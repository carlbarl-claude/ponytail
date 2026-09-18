# AP Tutor Bot 🎓

A Discord bot that tutors you through **AP Seminar** and **AP European History**,
powered by Claude. It's built for *learning*, not shortcuts: it explains concepts,
walks you through problems with hints first, helps you understand the scoring
rubrics, and coaches your own writing — but it won't do graded work for you.

## What it does

- **Ask by mentioning it or DMing it.** `@AP Tutor explain HIPP with an example`
- **Socratic tutoring.** It nudges you toward answers before spelling everything out,
  and gives full walkthroughs when you're stuck.
- **Grounded in real rubrics + scored samples.** It searches a **study library** of
  AP rubrics and scored sample responses, and cites the exact rubric line and a sample
  (with the "why it earned that score" reasoning) when it's relevant.
- **Upload your own materials.** Attach a **PDF, TXT, or MD** file in Discord — notes,
  a study guide, a reading, or official released samples you've downloaded — and the
  bot indexes it and starts citing it.
- **Per-channel memory** so a back-and-forth stays coherent.

### Commands

| Command | What it does |
|---|---|
| `/subject` | Switch between **AP Seminar** and **AP European History** for the channel |
| `/sources` | Show what's in the study library for the channel |
| `/reindex` | Rebuild the library index after adding files on disk |
| `/reset` | Clear the conversation history in the channel |
| `/help` | Show what the bot can do |

## How the grounding works (RAG)

The `knowledge/` folder is a per-subject **study library**:

```
knowledge/
  ap_euro/     rubrics.md  samples.md  uploads/
  ap_seminar/  rubrics.md  samples.md  uploads/
  sources.md   # where to download official College Board materials
```

`rag.py` indexes those files with **BM25 keyword search** (lightweight, free, no extra
API key). On each question, the bot retrieves the most relevant rubric criteria and
scored samples and feeds them to Claude, instructing it to cite them.

- The built-in `samples.md` files are **original, clearly-labeled illustrative
  examples** — not College Board's copyrighted student samples.
- To ground the bot in the *real* released exams and scored samples, download them
  yourself (`knowledge/sources.md` has the official links) and add them via the upload
  feature. Uploaded files stay local and are **git-ignored** on purpose.
- Want semantic search instead of keyword search later? Swap the BM25 retrieval in
  `rag.py` for an embeddings index — the rest of the pipeline stays the same.

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

- `bot.py` — the Discord bot (events, commands, Claude calls, uploads, message splitting)
- `prompts.py` — the tutoring personas and rubric knowledge for each subject
- `rag.py` — the study-library retrieval engine (indexing, BM25 search, upload ingest)
- `knowledge/` — the study library (rubric summaries, illustrative samples, uploads)
- `requirements.txt` — dependencies
- `.env.example` — the environment variables you need to set

## A note on academic integrity

This bot is designed to help you *learn* the material and *improve your own work*.
It deliberately won't write essays, IRRs, IWAs, or full DBQ/LEQ responses for you
to submit — that's both against AP rules and bad for actually getting a good score.
Use it to understand, practice, and revise.
