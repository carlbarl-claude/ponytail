# NFS: The Run — Handling Trainer (standalone app)

A real window with buttons. No Cheat Engine needed to *use* it.
Open the app → click **No Speed Loss** / **Max Grip** → play.

```
trainer/
  nfs_trainer.py      the app
  build_exe.bat       double-click to build NFS_Run_Trainer.exe
  requirements.txt
```

---

## You (once): make the .exe

**1. Fill in the addresses.** Open `nfs_trainer.py` in Notepad and edit the `CONFIG`
block near the top with what you found in Cheat Engine:
- `PROCESS_NAME` — exact game .exe name.
- `SPEED_BASE_OFFSET` + `SPEED_OFFSETS` — your Speed pointer (required).
- `GRIP_BASE_OFFSET` + `GRIP_OFFSETS` — optional, for Max Grip.

> **Pointer format:** if CE shows `"game.exe"+008ABCDE` then `+1C` then `+40`, use
> `SPEED_BASE_OFFSET = 0x008ABCDE` and `SPEED_OFFSETS = [0x1C, 0x40]`.
> The app shows the live speed value when connected — if it reads wrong, reverse the offset list.

**2. Build it.** Double-click **`build_exe.bat`**. It installs what it needs and produces
**`dist\NFS_Run_Trainer.exe`**. (Needs Python from https://www.python.org/downloads/ —
tick *"Add to PATH"* when installing.)

**3. Test it.** Right-click `NFS_Run_Trainer.exe` → **Run as administrator** (needed to touch
game memory), launch the game, click a button. When it says *Connected ✅* with a live speed
number, your pointer is good.

Then just give your brother the single `NFS_Run_Trainer.exe` file. That's all he needs.

---

## Your brother: use it

1. Double-click **`NFS_Run_Trainer.exe`** (Run as administrator if Windows asks).
2. Start Need for Speed: The Run.
3. When the window says **Connected ✅**, click **No Speed Loss** (and **Max Grip**).
4. Play. Close the window to turn everything off.

---

## Notes / gotchas

- **Run as administrator** — writing to another program's memory needs it. Without it the app
  opens but can't connect.
- **Antivirus / SmartScreen** may warn because the app edits game memory and isn't signed.
  It's your own code. On the "Windows protected your PC" box: *More info → Run anyway*, and if
  needed add an exclusion. (This is normal for every game trainer.)
- **32-bit game:** the app follows 4-byte pointers, correct for The Run. If you ever point it at
  a 64-bit game, pointer reads would need to be 8-byte.
- **Nothing is permanent.** The app only writes memory while it's open. Close it → game normal.
- Tuning (`RETAIN`, `BRAKE_CUT`, `GRIP_TARGET`) lives in the same `CONFIG` block; rebuild after changes.

Send me your **Speed pointer**, **Grip offset**, and the **exact .exe name** and I'll drop them
straight into `nfs_trainer.py` for you so the build is truly plug-and-play.
