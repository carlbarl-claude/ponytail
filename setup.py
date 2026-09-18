"""Friendly first-time setup wizard for the AP Tutor bot.

Designed to be run by a non-technical person, ideally with someone on a call:
- installs the Python dependencies,
- asks for the two tokens right here in the terminal (no file editing),
- checks each token immediately so you know if you pasted it wrong,
- writes the .env file for you,
- prints the exact link to add the bot to a Discord server,
- offers to start the bot.

Just run:  python setup.py
"""

import os
import re
import sys
import json
import subprocess
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(HERE, ".env")

# Permissions the invite link grants: View Channels + Send Messages +
# Embed Links + Read Message History (84992). Enough to tutor, nothing scary.
INVITE_PERMISSIONS = 84992


def hr():
    print("-" * 60)


def ensure_dependencies():
    """Install requirements if the key packages aren't importable yet."""
    try:
        import anthropic  # noqa: F401
        import discord  # noqa: F401
        return
    except ImportError:
        pass
    print("Installing the pieces the bot needs (this can take a minute)...")
    req = os.path.join(HERE, "requirements.txt")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", req],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("\nCouldn't install the requirements automatically. Details:")
        print(result.stderr[-1500:])
        print("\nTry running this yourself, then rerun setup:")
        print(f"    {sys.executable} -m pip install -r requirements.txt")
        sys.exit(1)
    print("Done installing. ✅\n")


def check_anthropic_key(key: str):
    """Return (ok, message). Verifies the key by listing models (free, no charge)."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        client.models.list(limit=1)
        return True, "Anthropic key works. ✅"
    except anthropic.AuthenticationError:
        return False, "That Anthropic key was rejected — double-check you copied the whole thing."
    except anthropic.APIConnectionError:
        return False, "Couldn't reach Anthropic (network?). Check your connection and try again."
    except Exception as e:  # anything unexpected — show it rather than hang
        return False, f"Couldn't verify the Anthropic key: {e}"


def check_discord_token(token: str):
    """Return (ok, message, bot_info). Verifies via Discord's REST API."""
    req = urllib.request.Request(
        "https://discord.com/api/v10/users/@me",
        headers={"Authorization": f"Bot {token}", "User-Agent": "AP-Tutor-Setup"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        name = data.get("username", "your bot")
        return True, f"Discord token works — it belongs to **{name}**. ✅", data
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "That Discord token was rejected — make sure you copied the whole Bot token.", None
        return False, f"Discord returned an error ({e.code}). Try again in a moment.", None
    except urllib.error.URLError:
        return False, "Couldn't reach Discord (network?). Check your connection and try again.", None


def ask_token(label: str, hint: str, checker):
    """Prompt for a token, validate it, and keep asking until it's good (or skipped)."""
    print(f"\n{label}")
    print(hint)
    print("(It's fine that you can see it on screen — this is your own computer.)")
    while True:
        value = input("Paste it here and press Enter: ").strip().strip('"').strip("'")
        if not value:
            print("Nothing entered. Type 'skip' if you want to fill this in later.")
            continue
        if value.lower() == "skip":
            return None, None
        result = checker(value)
        ok, msg = result[0], result[1]
        print(msg)
        if ok:
            extra = result[2] if len(result) > 2 else None
            return value, extra
        print("Let's try that again (or type 'skip' to do it later).")


def read_existing_env() -> dict:
    values = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    values[k.strip()] = v.strip()
    return values


def write_env(anthropic_key: str, discord_token: str):
    existing = read_existing_env()
    anthropic_key = anthropic_key or existing.get("ANTHROPIC_API_KEY", "")
    discord_token = discord_token or existing.get("DISCORD_TOKEN", "")
    lines = [
        "# Written by setup.py — keep this file private, never share or commit it.",
        f"DISCORD_TOKEN={discord_token}",
        f"ANTHROPIC_API_KEY={anthropic_key}",
    ]
    model = existing.get("TUTOR_MODEL")
    if model:
        lines.append(f"TUTOR_MODEL={model}")
    else:
        lines.append("# Optional: TUTOR_MODEL=claude-sonnet-5  (cheaper, still a strong tutor)")
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nSaved your settings to {ENV_PATH} 🔒")


def invite_url(bot_id: str) -> str:
    return (
        f"https://discord.com/oauth2/authorize?client_id={bot_id}"
        f"&permissions={INVITE_PERMISSIONS}&scope=bot+applications.commands"
    )


def main():
    hr()
    print("  AP Tutor Bot — Setup Wizard  🎓")
    hr()
    print("This will get the bot ready in a few short steps.")
    print("If you get stuck, the SETUP.md file has pictures-and-words directions.\n")

    ensure_dependencies()
    existing = read_existing_env()

    # 1) Anthropic key
    anthropic_key, _ = ask_token(
        "Step 1 of 2 — your Anthropic API key",
        "Get it at https://console.anthropic.com/settings/keys (starts with 'sk-ant-').",
        check_anthropic_key,
    )

    # 2) Discord bot token
    discord_token, bot_info = ask_token(
        "Step 2 of 2 — your Discord bot token",
        "Get it at https://discord.com/developers/applications → your app → Bot → Reset Token.",
        check_discord_token,
    )

    write_env(anthropic_key, discord_token)

    hr()
    if bot_info and bot_info.get("id"):
        print("Add the bot to the Discord server with this link:\n")
        print("   " + invite_url(bot_info["id"]))
        print("\nOpen it in a browser, pick the server, and click Authorize.")
    else:
        print("Once your Discord token is set, run the bot and it will print the")
        print("invite link for you.")
    hr()

    print("\n⚠️  One thing to double-check in the Developer Portal:")
    print("   Bot → Privileged Gateway Intents → turn ON 'MESSAGE CONTENT INTENT'.")
    print("   (Without it the bot can't read questions. Setup can't toggle this for you.)\n")

    have_both = anthropic_key and discord_token
    if have_both:
        answer = input("Start the bot now? [Y/n] ").strip().lower()
        if answer in ("", "y", "yes"):
            print("\nStarting the bot... (press Ctrl+C to stop it)\n")
            os.execv(sys.executable, [sys.executable, os.path.join(HERE, "bot.py")])
    print("All set. When you're ready, start it any time with:")
    print(f"    {sys.executable} bot.py")
    print("Or just double-click run.sh (Mac/Linux) or run.bat (Windows).")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled. Run 'python setup.py' again whenever you like.")
