# AP Tutor Bot 🎓

A Discord bot that tutors you through **AP Seminar** and **AP European History**,
powered by Claude. It's built for *learning*, not shortcuts: it explains concepts,
walks you through problems with hints first, helps you understand the scoring
rubrics, and coaches your own writing — but it won't do graded work for you.

## What it does

- **Ask by mentioning it or DMing it.** `@AP Tutor explain HIPP with an example`
- **Socratic tutoring.** It nudges you toward answers before spelling everything out,
  and gives full walkthroughs when you're stuck.
- **Rubric-aware.** It knows the AP Seminar (IRR/IWA, source evaluation, end-of-course
  exam) and AP Euro (DBQ/LEQ, HIPP, the reasoning skills) scoring criteria.
- **Per-channel memory** so a back-and-forth stays coherent.

### Commands

| Command | What it does |
|---|---|
| `/subject` | Switch between **AP Seminar** and **AP European History** for the channel |
| `/reset` | Clear the conversation history in the channel |
| `/help` | Show what the bot can do |

## Setup

### 1. Create the Discord bot
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) → **New Application**.
2. Open the **Bot** tab → **Reset Token** → copy the token (this is your `DISCORD_TOKEN`).
3. Under **Privileged Gateway Intents**, enable **Message Content Intent** (the bot needs
   this to read your questions).
4. Open **OAuth2 → URL Generator**, check **bot** and **applications.commands** scopes,
   give it **Send Messages** + **Read Message History** permissions, and use the generated
   URL to invite the bot to your server.

### 2. Get an Anthropic API key
From the [Anthropic Console](https://console.anthropic.com/settings/keys) → this is your
`ANTHROPIC_API_KEY`.

### 3. Install and run
```bash
pip install -r requirements.txt

cp .env.example .env      # then edit .env with your real tokens
export $(grep -v '^#' .env | xargs)   # load them (macOS/Linux)

python bot.py
```

The bot syncs its slash commands on startup and prints a "Logged in as…" line
when it's ready.

## Cost note

It defaults to `claude-opus-5` for the best explanations. If you're sending a lot
of messages and want to spend less, set `TUTOR_MODEL=claude-sonnet-5` in your
environment — roughly half the cost, still a strong tutor.

## Files

- `bot.py` — the Discord bot (events, commands, Claude calls, message splitting)
- `prompts.py` — the tutoring personas and rubric knowledge for each subject
- `requirements.txt` — dependencies
- `.env.example` — the environment variables you need to set

## A note on academic integrity

This bot is designed to help you *learn* the material and *improve your own work*.
It deliberately won't write essays, IRRs, IWAs, or full DBQ/LEQ responses for you
to submit — that's both against AP rules and bad for actually getting a good score.
Use it to understand, practice, and revise.
