# Setup — the easy way 🎓

**What is this?** A Discord bot that tutors you through **AP Seminar** and **AP
European History**. You talk to it in Discord like a person; it explains concepts,
walks you through practice questions, and scores your writing against the real AP
rubrics. This guide gets it running on a Discord server.

It's written so a friend can walk you through it on a call. You'll copy two "tokens"
(think: long passwords) and click a link. That's basically it.

**Total time:** about 10 minutes. **No coding, no file editing required.**

### Contents
- [What you need first](#what-you-need-first)
- [The whole thing in one line](#the-whole-thing-in-one-line)
- [Part A — get your Anthropic key](#part-a--get-your-anthropic-key-the-bots-brain)
- [Part B — make the Discord bot](#part-b--make-the-discord-bot-the-bots-body)
- [Part C — run the wizard](#part-c--run-the-wizard)
- [Using it in Discord](#using-it-in-discord)
- [If something goes wrong](#if-something-goes-wrong)
- [Frequently asked](#frequently-asked)

---

## What you need first
- A computer (Windows or Mac).
- **Python** installed. Check by opening a terminal and typing `python --version`.
  - Don't have it? Get it at <https://www.python.org/downloads/>.
  - **Windows:** during install, tick the box **"Add Python to PATH"**.
- This project's folder downloaded onto the computer.

---

## The whole thing in one line
Once Python is installed and you have the folder:

- **Mac:** double-click **`run.sh`** (or in Terminal: `./run.sh`)
- **Windows:** double-click **`run.bat`**

The first time, it launches a **setup wizard** that asks you for two tokens and
checks them for you. Get those two tokens using Parts A and B below, then come back.

---

## Part A — get your Anthropic key (the bot's "brain")
1. Go to <https://console.anthropic.com/settings/keys> and sign in (or make an account).
2. Click **Create Key**, give it any name, and click create.
3. **Copy the key** — it starts with `sk-ant-`. Keep it somewhere for a minute.
   - You'll need a small amount of paid credit on the account for the bot to answer.

---

## Part B — make the Discord bot (the bot's "body")
1. Go to <https://discord.com/developers/applications> and sign in.
2. Click **New Application** (top right). Name it (e.g. "AP Tutor"). Click **Create**.
3. On the left, click **Bot**.
4. Find **Privileged Gateway Intents** and turn **ON** the switch labeled
   **MESSAGE CONTENT INTENT**. ⬅️ *This one is important — the bot can't read
   questions without it.* Save if it asks.
5. Near the top of the Bot page, click **Reset Token**, confirm, then **Copy** the
   token it shows. This is your Discord token. (It's shown only once — if you lose
   it, just Reset again.)

---

## Part C — run the wizard
1. Start the project (`run.sh` on Mac, `run.bat` on Windows — or `python setup.py`).
2. When it asks for your **Anthropic key**, paste the `sk-ant-...` key and press Enter.
   It'll say ✅ if it works.
3. When it asks for your **Discord token**, paste it and press Enter. It'll say ✅ and
   tell you your bot's name.
4. The wizard prints an **invite link**. Open it in your browser, choose the server
   you want the bot in, and click **Authorize**.
   - You need "Manage Server" permission on that server to add a bot. If it's your
     friend's server, they can either give you that or open the link themselves.
5. Back in the wizard, choose **Y** to start the bot. Done! 🎉

---

## Using it in Discord
- In any channel the bot can see, **@mention it** with your question, or **DM it**.
- Handy commands (type `/` and they pop up):
  - `/grade` — paste your writing, get it scored on the rubric.
  - `/quiz` — get a practice question.
  - `/subject` — switch between AP Seminar and AP European History.
  - `/help` — see everything.
- Want it smarter about your class? **Attach a PDF/TXT/MD** (notes, a study guide,
  official released samples) and it'll start using them.

---

## If something goes wrong
The bot tries to tell you exactly what's up, but here are the usual ones:

| What you see | What to do |
|---|---|
| "MESSAGE CONTENT INTENT is off" | Do **Part B, step 4** and restart the bot. |
| "Discord rejected the token" | Reset the token again (Part B, step 5) and rerun `python setup.py`. |
| "Anthropic key was rejected" | Recopy the whole `sk-ant-...` key; rerun `python setup.py`. |
| Bot is online but silent | Make sure you **@mentioned it** (or DM'd it), and that it can see the channel. |
| "Python isn't installed" | Install Python (see "What you need first"), then rerun. |

To change a token later, just run `python setup.py` again — it updates everything.

---

## Frequently asked

**Does it cost money?** The Discord side is free. The "brain" (Anthropic) charges a
small amount per question — usually a fraction of a cent. You add credit on the
Anthropic Console. To spend less, you can switch to a cheaper model (ask your friend,
or set `TUTOR_MODEL=claude-sonnet-5` in the `.env`).

**Is it going to do my homework for me?** No — on purpose. It won't write essays or
full graded responses for you to submit. It explains, quizzes, and coaches your own
work, which is what actually raises your score (and stays within AP rules).

**Can lots of people in the server use it at once?** Yes. It keeps each channel's
conversation separate.

**Where do the tokens live? Is it safe?** They're saved in a file called `.env` on
the computer running the bot, and nowhere else. Don't share that file. It's set to
never be uploaded to GitHub.

**Do I have to keep my computer on?** Yes, while you want the bot online — keep the
terminal window open. Closing it stops the bot. Want it online 24/7 without your
computer? That's optional hosting — ask your friend, it can be added later.

**I closed the window / restarted. How do I start it again?** Double-click `run.sh`
(Mac) or `run.bat` (Windows) again — after the first setup it goes straight to
running. It even remembers which subject each channel was set to.
