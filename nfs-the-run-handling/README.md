# NFS: The Run — Corner Speed Assist (Cheat Engine)

Single-player handling tweak: stop scrubbing so much speed in corners.
Fully reversible — it's just Cheat Engine reading/writing memory while the game runs.
Nothing on disk is modified.

**Files**
- `NFSTheRun_CornerSpeed.CT` — the table (anti-scrub script + placeholder entries).

---

## How it works

Cornering speed loss is just your **speed value dropping** frame-to-frame while you
turn. The `Anti-Scrub` script watches that value and, when it drops a *small* amount
(a corner scrubbing speed) it gives most of it back — but ignores *large* drops so
your **brakes still work normally**. One threshold (`brakeCut`) separates the two.

The cleaner alternative — editing the actual grip float — is Step 3 (optional).

---

## Step 1 — Find your Speed value (one-time)

You've done pointer scans before, so quick version:

1. Launch The Run, get into a race, open CE, attach to the game process.
2. Value type **Float**, scan type **Unknown initial value**.
3. **Accelerate** on a straight → `Increased value`. Coast/brake → `Decreased value`.
   Repeat 4–6 times until you're down to a handful of addresses. Speed sits in a
   sensible range (often ~0–100 or ~0–300 depending on the unit — doesn't matter which).
4. Add the winner to the list. Confirm it: freeze it and you should glide at constant speed.

**Make it stick across restarts (pointer scan):**
5. Right-click the address → **Pointer scan for this address**. Play a bit, restart
   the game, re-find speed, then **rescan** the pointermap with the new address until
   you've got a stable pointer path (max level 5–6 is plenty).
6. Copy that stable pointer into the table's **`Speed`** entry (base module + offsets).

> ⚠️ Keep the `Speed` entry's description **exactly** as it ships
> (`Speed  (SET THIS - see README step 1)`). The Lua finds the address *by that
> description*. If you rename it, update the string inside `corner.speedRec()` to match.

---

## Step 2 — Turn on Anti-Scrub

1. Load `NFSTheRun_CornerSpeed.CT` (File → Open, or drag onto CE).
2. Tick the box on **`[ Enable ] Anti-Scrub`**.
3. Drive. Corners should hold speed; braking should still slow you.

**Tuning** — double-click the script to edit the `TUNABLES` block:

| Setting | What it does | Try |
|---|---|---|
| `retain` | How much scrubbed speed to give back (0–1). | Start `0.90`. Feels sluggish/floaty? lower to `0.7`. Want almost no loss? `0.98`. |
| `brakeCut` | Per-tick drop above this = "braking", left alone. | Start `3.0`. If **braking feels weak** → lower it. If corners **still scrub** → raise it. |
| `interval` | ms between checks. | Leave at `16` (~60fps). |

Re-tick the box after editing to reload the script.

> The right `brakeCut` depends on the game's speed unit, so it's trial-and-error for a
> minute. Find the value where hard braking still works but gentle cornering doesn't bleed speed.

---

## Step 3 — (Optional) Edit the real grip value

Cleaner than anti-scrub, but more digging. Once you trust your Speed pointer, the
vehicle's physics floats usually live in the **same struct** nearby.

1. Right-click Speed → **Find out what accesses this address**. Drive around; CE lists
   instructions touching the car struct. Double-click one → note the **base register**.
2. Right-click that instruction → **Dissect data/structures** on the base pointer.
   You'll see a block of floats: mass, downforce, steering, grip/traction, drag, etc.
3. Change candidates *one at a time* while driving to identify grip/lateral friction.
   (Grip usually 0.5–2.0-ish; bumping it up = sticks to the road, less understeer.)
4. Put the winner in the **`Grip / Traction`** entry, freeze it at a higher value, done.

If you find it, paste the offset here and I'll wire it into the table with a hotkey +
multiplier so you're not just hard-freezing a raw value.

---

## Troubleshooting

- **Nothing happens** → the `Speed` address is `0`/stale. Redo Step 1 or fix the pointer.
- **Car feels like it's on ice / won't slow** → `retain` too high or `brakeCut` too low.
- **Still scrubs in corners** → `brakeCut` too low (raise it) or `retain` too low.
- **Script won't enable** → check the `Speed` entry description matches `corner.speedRec()`.

Send me the numbers you land on (or your speed unit / pointer path) and I'll tighten it up.
