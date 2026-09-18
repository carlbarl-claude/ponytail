"""Local test mode for the AP tutor — chat in your terminal, no Discord needed.

Only requires ANTHROPIC_API_KEY. Great for trying the bot, testing the study
library, or studying offline from Discord.

Run:
    python chat.py            # starts in the default subject
    python chat.py euro       # start in AP European History
    python chat.py seminar    # start in AP Seminar

In-chat commands:
    :subject euro | seminar   switch subject (clears history)
    :grade <your writing>     score your writing on the rubric
    :quiz [topic]             get a practice question
    :sources                  show what's in the study library
    :reset                    clear the conversation
    :quit                     exit
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import anthropic

import prompts
import rag
import tutor

MODEL = os.environ.get("TUTOR_MODEL", tutor.MODEL_DEFAULT)


def call(client, system_prompt, messages, max_tokens=2200):
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            thinking={"type": "adaptive"},
            messages=messages,
        )
    except anthropic.APIError as e:
        return f"[error talking to Claude: {e}]"
    return tutor.extract_text(resp)


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit(
            "Set ANTHROPIC_API_KEY (in a .env file or your environment) to use chat mode."
        )

    subject = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in prompts.SUBJECTS \
        else prompts.DEFAULT_SUBJECT
    client = anthropic.Anthropic()
    history: list[dict] = []

    name = prompts.SUBJECTS[subject][0]
    print(f"AP Tutor (local mode) — tutoring {name}.")
    print("Type your question, or :help for commands, :quit to exit.\n")

    while True:
        try:
            line = input("you › ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye! 👋")
            return
        if not line:
            continue

        # --- commands ---
        if line in (":quit", ":q", ":exit"):
            print("bye! 👋")
            return
        if line == ":help":
            print(__doc__)
            continue
        if line == ":reset":
            history.clear()
            print("(history cleared)\n")
            continue
        if line == ":sources":
            print(rag.library_summary(subject) + "\n")
            continue
        if line.startswith(":subject"):
            arg = line.split(maxsplit=1)
            if len(arg) == 2 and arg[1] in prompts.SUBJECTS:
                subject = arg[1]
                history.clear()
                print(f"(switched to {prompts.SUBJECTS[subject][0]}, history cleared)\n")
            else:
                print("usage: :subject euro | seminar\n")
            continue
        if line.startswith(":grade"):
            work = line[len(":grade"):].strip()
            if not work:
                print("usage: :grade <paste your thesis/paragraph>\n")
                continue
            reply = call(client, tutor.grade_system(subject, work),
                         [{"role": "user", "content": work}])
            print(f"\ntutor › {reply}\n")
            continue
        if line.startswith(":quiz"):
            topic = line[len(":quiz"):].strip()
            reply = call(client, tutor.quiz_system(subject, topic),
                         [{"role": "user", "content": topic or "Give me a practice question."}],
                         max_tokens=2000)
            print(f"\ntutor › {reply}\n")
            continue

        # --- normal tutoring turn ---
        system_prompt = tutor.tutor_system(subject, line)
        messages = history + [{"role": "user", "content": line}]
        reply = call(client, system_prompt, messages)
        history.append({"role": "user", "content": line})
        history.append({"role": "assistant", "content": reply})
        print(f"\ntutor › {reply}\n")


if __name__ == "__main__":
    main()
