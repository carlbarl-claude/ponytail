# NFS: The Run — Handling Mod (Cheat Engine)

Single-player handling tweaks: **No Speed Loss** in corners + **Max Grip**.
Fully reversible — Cheat Engine reads/writes memory while the game runs; nothing on disk changes.

**Files**
- `NFSTheRun_CornerSpeed.CT` — the table (core engine + two toggles + placeholder addresses).

**Toggles**
| Feature | Hotkey | Needs |
|---|---|---|
| **No Speed Loss** (anti-scrub, full retain) | **F1** | Speed address (Step 1) |
| **Max Grip** (locks grip float high) | **F2** | Grip address (Step 3) |

---

## How it works

- **No Speed Loss** watches your speed float. A *small* frame-to-frame drop = cornering
  scrub → it's given straight back (`retain = 1.00`). A *large* drop = you braking →
  left alone (`brakeCut`). So corners hold speed but **brakes still work**.
- **Max Grip** just writes a high value to the car's grip/traction float every tick.

---

## Step 1 — Find your Speed value (one-time)

1. Get into a race, attach CE to the game.
2. Float, **Unknown initial value**. Accelerate → `Increased`; coast/brake → `Decreased`.
   Repeat until a few addresses remain. Confirm: freeze it → constant speed.
3. **Pointer-scan** it (right-click → *Pointer scan for this address*), restart, re-find,
   rescan until stable (level 5–6). Paste the pointer into the **`Speed`** entry.

> The scripts match entries **by description prefix** (`Speed`, `Grip`), so you can rename
> the tail freely — just keep the first word.

## Step 2 — Turn it on

1. Load the `.CT`. Tick **`[ Enable ] Core`** first (starts the engine + registers F1/F2).
2. Tick **`No Speed Loss`** (or press **F1** in-game). Drive — corners should hold speed.

**Tuning** (double-click `[ Enable ] Core`, edit the `TUNABLES` block, re-tick to reload):

| Setting | Does | Try |
|---|---|---|
| `retain` | Fraction of scrubbed speed returned. | `1.00` = no loss. Feels floaty/twitchy? drop to `0.85`. |
| `brakeCut` | Per-tick drop above this = braking, ignored. | `3.0`. Braking weak? lower it. Corners still scrub? raise it. |
| `gripTarget` | Value Max Grip locks to (Step 3). | `2.0`. Raise for more stick. |

> `brakeCut` is in the game's raw speed unit, so tune it live for a minute: find the value
> where hard braking still slows you but gentle cornering doesn't bleed speed.

## Step 3 — Find Grip for Max Grip (optional but that's the "real" fix)

1. Right-click **Speed** → *Find out what accesses this address*. Drive; double-click a
   listed instruction → note its **base register/pointer**.
2. Right-click → *Dissect data/structures* on that base. You'll see the vehicle floats:
   mass, downforce, steering, **grip/traction**, drag…
3. Change candidates one at a time while driving to spot grip (usually ~0.5–2.0; higher =
   sticks to the road, less understeer). Paste it into the **`Grip`** entry.
4. Set `gripTarget` in the TUNABLES to how sticky you want it, then tick **`Max Grip`** / **F2**.

Send me your **speed unit / pointer path** or the **grip offset** and I'll pin exact defaults.

---

## Troubleshooting

- **F1/F2 do nothing** → `[ Enable ] Core` isn't ticked, or the address is still `0`.
- **Toggle says "Enable Core first"** → tick `[ Enable ] Core` before the sub-toggles.
- **Car's on ice / won't slow** → `retain` too high or `brakeCut` too low.
- **Still scrubs** → `brakeCut` too low (raise it).
- **Max Grip snaps back** → Grip address `0`/wrong, or it's not the grip float — redo Step 3.
