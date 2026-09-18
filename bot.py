"""AP coursework tutor — a Discord bot powered by Claude.

Focus: tutoring & explanations for AP Seminar and AP European History.

How to use it in Discord:
- Mention the bot (@BotName your question) or DM it directly to ask anything.
- /subject seminar | euro  — switch which AP class the bot tutors for (per channel).
- /reset                   — clear the conversation history for the channel.
- /help                    — show what the bot can do.

Conversation memory is kept per channel so a back-and-forth stays coherent,
and trimmed so requests stay affordable.
"""

import os
import collections

import anthropic
import discord
from discord import app_commands

import prompts
import rag

# --- Configuration ---------------------------------------------------------

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
# Default to Opus 5 for the best tutoring quality. Set TUTOR_MODEL=claude-sonnet-5
# in the environment to cut cost roughly in half if you're sending lots of messages.
MODEL = os.environ.get("TUTOR_MODEL", "claude-opus-5")
MAX_TOKENS = 1600  # Roughly fits a Discord message; long answers get split.
# How many prior turns (user+assistant pairs) to remember per channel.
HISTORY_TURNS = 10

DISCORD_LIMIT = 2000  # Discord's hard per-message character cap.

# --- State -----------------------------------------------------------------

claude = anthropic.AsyncAnthropic()  # reads ANTHROPIC_API_KEY from the environment

# Per-channel conversation history: channel_id -> deque of message dicts.
_histories: dict[int, collections.deque] = collections.defaultdict(
    lambda: collections.deque(maxlen=HISTORY_TURNS * 2)
)
# Per-channel chosen subject: channel_id -> subject key.
_subjects: dict[int, str] = {}

intents = discord.Intents.default()
intents.message_content = True  # required to read message text for mention/DM handling
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# --- Helpers ---------------------------------------------------------------

def subject_for(channel_id: int) -> str:
    return _subjects.get(channel_id, prompts.DEFAULT_SUBJECT)


def split_message(text: str, limit: int = DISCORD_LIMIT) -> list[str]:
    """Split a long reply into Discord-sized chunks, preferring paragraph breaks."""
    chunks: list[str] = []
    remaining = text.strip()
    while len(remaining) > limit:
        # Try to break at the last paragraph or newline before the limit.
        split_at = remaining.rfind("\n\n", 0, limit)
        if split_at == -1:
            split_at = remaining.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = remaining.rfind(" ", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


# Appended to the subject system prompt to tell Claude how to use retrieved material.
_GROUNDING_INSTRUCTIONS = """
--- Using the study library ---
Below you may be given a STUDY LIBRARY CONTEXT block: excerpts retrieved from a
library of AP rubrics, scored sample responses, and the student's own uploaded notes.
When it's relevant to the question:
- Cite the specific rubric criterion by name (e.g., "DBQ · Complexity (1 pt)").
- When a scored sample is relevant, reference it and explain *why* it earned (or lost)
  its score — connect the student's situation to that example.
- Prefer the retrieved material over generic advice for anything about scoring.
- Samples labeled "scored sample" in the built-in library are illustrative/synthetic
  teaching examples, not official College Board samples — you may say so if asked.
  Material labeled "your upload" is the student's own file.
If the context doesn't cover something, use your general AP knowledge and say the
library didn't have specifics on it. Never invent a rubric point value or a fake
"official sample" — only cite what's actually provided or well-established.
"""


async def ask_claude(channel_id: int, user_text: str) -> str:
    """Send the channel's history plus the new message to Claude and return the reply."""
    subject_key = subject_for(channel_id)
    subject_name, system_prompt = prompts.SUBJECTS[subject_key]
    history = _histories[channel_id]

    # Retrieve relevant rubric/sample/upload excerpts and ground the answer in them.
    system_prompt = system_prompt + _GROUNDING_INSTRUCTIONS
    context_block = rag.build_context(subject_key, user_text)
    if context_block:
        system_prompt = system_prompt + "\n\n" + context_block

    messages = list(history) + [{"role": "user", "content": user_text}]

    try:
        response = await claude.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            thinking={"type": "adaptive"},
            messages=messages,
        )
    except anthropic.RateLimitError:
        return "I'm getting a lot of questions right now — give me a few seconds and ask again. 🙏"
    except anthropic.APIStatusError as e:
        return f"Something went wrong reaching my brain (error {e.status_code}). Try again in a moment."
    except anthropic.APIConnectionError:
        return "I couldn't connect just now. Please try again in a moment."

    reply = "".join(b.text for b in response.content if b.type == "text").strip()
    if not reply:
        reply = "Hmm, I didn't have a good answer for that — can you rephrase or add a bit more detail?"

    # Persist this turn so follow-ups have context.
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": reply})
    return reply


async def respond(channel, channel_id: int, user_text: str) -> None:
    """Generate a reply and send it back, split across messages if needed."""
    async with channel.typing():
        reply = await ask_claude(channel_id, user_text)
    for chunk in split_message(reply):
        await channel.send(chunk)


# --- Discord events --------------------------------------------------------

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user} — tutoring {len(prompts.SUBJECTS)} AP subjects.")


@client.event
async def on_message(message: discord.Message):
    # Never respond to ourselves or other bots.
    if message.author.bot:
        return

    is_dm = message.guild is None
    is_mention = client.user in message.mentions

    if not (is_dm or is_mention):
        return  # Only engage when spoken to.

    # Ingest any attached study materials (PDF/TXT/MD) into the channel's subject.
    subject_key = subject_for(message.channel.id)
    ingestible = [
        a for a in message.attachments
        if os.path.splitext(a.filename)[1].lower() in {".pdf", ".txt", ".md"}
    ]
    if ingestible:
        async with message.channel.typing():
            for att in ingestible:
                data = await att.read()
                ok, note = rag.ingest_upload(subject_key, att.filename, data)
                await message.channel.send(note)

    # Strip the bot mention out of the text so it doesn't confuse Claude.
    content = message.content
    if is_mention:
        content = content.replace(f"<@{client.user.id}>", "").replace(
            f"<@!{client.user.id}>", ""
        ).strip()

    if not content:
        subject_name = prompts.SUBJECTS[subject_for(message.channel.id)][0]
        await message.channel.send(
            f"Hi! 👋 I'm your **{subject_name}** tutor. Ask me anything — "
            "a concept, a practice question, help outlining an argument. "
            "Use `/subject` to switch classes or `/help` to see what I can do."
        )
        return

    await respond(message.channel, message.channel.id, content)


# --- Slash commands --------------------------------------------------------

@tree.command(name="subject", description="Choose which AP class I tutor for in this channel.")
@app_commands.describe(subject="Which AP class?")
@app_commands.choices(
    subject=[
        app_commands.Choice(name="AP Seminar", value="seminar"),
        app_commands.Choice(name="AP European History", value="euro"),
    ]
)
async def subject_cmd(interaction: discord.Interaction, subject: app_commands.Choice[str]):
    _subjects[interaction.channel_id] = subject.value
    # A subject switch starts a fresh conversation so context doesn't bleed across classes.
    _histories.pop(interaction.channel_id, None)
    await interaction.response.send_message(
        f"Switched to **{subject.name}** for this channel. Fresh start — what are we working on? 📚"
    )


@tree.command(name="sources", description="Show what's in the study library for this channel.")
async def sources_cmd(interaction: discord.Interaction):
    subject_key = subject_for(interaction.channel_id)
    subject_name = prompts.SUBJECTS[subject_key][0]
    summary = rag.library_summary(subject_key)
    await interaction.response.send_message(
        f"**{subject_name} study library**\n{summary}\n\n"
        "Attach a **PDF, TXT, or MD** file in a message to me to add your own notes, "
        "study guides, or official released samples — I'll cite them when relevant. "
        "See `knowledge/sources.md` in the repo for where to download official materials.",
        ephemeral=True,
    )


@tree.command(name="reindex", description="Rebuild the study library index for this channel's subject.")
async def reindex_cmd(interaction: discord.Interaction):
    subject_key = subject_for(interaction.channel_id)
    count = rag.reindex(subject_key)
    await interaction.response.send_message(
        f"Rebuilt the library index — {count} sections indexed. ✅", ephemeral=True
    )


@tree.command(name="reset", description="Clear our conversation history in this channel.")
async def reset_cmd(interaction: discord.Interaction):
    _histories.pop(interaction.channel_id, None)
    await interaction.response.send_message("Cleared! We're starting fresh. 🧹")


@tree.command(name="help", description="Show what the AP tutor bot can do.")
async def help_cmd(interaction: discord.Interaction):
    subject_name = prompts.SUBJECTS[subject_for(interaction.channel_id)][0]
    await interaction.response.send_message(
        f"**AP Tutor Bot** — currently tutoring **{subject_name}** here.\n\n"
        "**How to talk to me**\n"
        "• Mention me (`@me your question`) or DM me directly.\n"
        "• I focus on *understanding*: I'll explain concepts, walk through problems, "
        "and coach your writing — but I won't do graded work for you.\n\n"
        "• I ground my scoring advice in a **study library** of rubrics and scored "
        "samples, and I'll cite the exact rubric line and a sample when it helps.\n"
        "• **Upload your own** notes/readings/PDFs — just attach a PDF, TXT, or MD "
        "file and I'll start using it.\n\n"
        "**Commands**\n"
        "• `/subject` — switch between AP Seminar and AP European History.\n"
        "• `/sources` — see what's in the study library here.\n"
        "• `/reindex` — rebuild the library index after adding files.\n"
        "• `/reset` — clear our conversation history in this channel.\n"
        "• `/help` — show this message.\n\n"
        "Try: *\"Explain HIPP with an example\"* or *\"Grade this thesis against the DBQ rubric.\"*",
        ephemeral=True,
    )


# --- Entry point -----------------------------------------------------------

def main():
    if not DISCORD_TOKEN:
        raise SystemExit("Set the DISCORD_TOKEN environment variable (see .env.example).")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set the ANTHROPIC_API_KEY environment variable (see .env.example).")
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
