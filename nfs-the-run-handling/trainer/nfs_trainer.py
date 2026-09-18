"""
NFS: The Run - Handling Trainer
================================
A tiny click-a-button app for single-player Need for Speed: The Run.

  * No Speed Loss  - keeps your speed through corners (anti-scrub)
  * Max Grip       - locks the car's grip float high

It only reads/writes the running game's memory while open. Close it and the
game is 100% back to normal - nothing on disk is ever changed.

------------------------------------------------------------------------
!!! FILL IN THE CONFIG BELOW ONCE (see README step 1 & 3) !!!
Until the Speed pointer is set, "No Speed Loss" has nothing to write to.
------------------------------------------------------------------------
"""

import threading
import time
import tkinter as tk
from tkinter import font as tkfont

try:
    import pymem
    import pymem.process
except ImportError:
    raise SystemExit(
        "The 'pymem' package is missing. Run:  pip install pymem\n"
        "(or use build_exe.bat which installs it for you)"
    )

# ======================================================================
# CONFIG  -  edit these once with the values you found in Cheat Engine
# ======================================================================

PROCESS_NAME = "Need For Speed The Run.exe"   # exact .exe name (CE > File > Open Process)

# --- Speed pointer (REQUIRED for No Speed Loss) -----------------------
# From your CE pointer scan. Example if CE shows:  "game.exe"+008ABCDE  ->  +1C  ->  +40
#   SPEED_BASE_OFFSET = 0x008ABCDE
#   SPEED_OFFSETS     = [0x1C, 0x40]      # outermost-to-value order; if speed reads wrong, reverse it
SPEED_BASE_OFFSET = None        # e.g. 0x008ABCDE
SPEED_OFFSETS     = []          # e.g. [0x1C, 0x40]  (empty = value is right at module+base offset)

# --- Grip pointer (OPTIONAL, for Max Grip) ----------------------------
GRIP_BASE_OFFSET = None         # e.g. 0x008AC120
GRIP_OFFSETS     = []
GRIP_TARGET      = 2.0          # value to lock grip to; raise for more stick

# --- Anti-scrub tuning ------------------------------------------------
RETAIN    = 1.00     # 1.00 = give back all corner scrub (no speed loss). Lower (0.85) if floaty.
BRAKE_CUT = 3.0      # per-tick speed drop bigger than this = braking (left alone). Tune live.
TICK_S    = 0.016    # ~60 checks/sec

# ======================================================================
#  Engine (you shouldn't need to touch anything below here)
# ======================================================================


class Trainer:
    def __init__(self):
        self.pm = None
        self.module_base = None
        self.connected = False
        self.speed_on = False
        self.grip_on = False
        self._prev_speed = None
        self._stop = threading.Event()

    # ---- process attach ------------------------------------------------
    def try_attach(self):
        if self.connected:
            # still alive?
            try:
                pymem.process.module_from_name(self.pm.process_handle, PROCESS_NAME)
                return True
            except Exception:
                self.connected = False
        try:
            self.pm = pymem.Pymem(PROCESS_NAME)
            mod = pymem.process.module_from_name(self.pm.process_handle, PROCESS_NAME)
            self.module_base = mod.lpBaseOfDll
            self.connected = True
            self._prev_speed = None
        except Exception:
            self.connected = False
        return self.connected

    # ---- pointer resolution (32-bit game) ------------------------------
    def _resolve(self, base_offset, offsets):
        if base_offset is None:
            return None
        addr = self.module_base + base_offset
        for off in offsets:
            ptr = self.pm.read_uint(addr)          # 4-byte pointer (32-bit process)
            addr = ptr + off
        return addr

    # ---- one work tick -------------------------------------------------
    def tick(self):
        if not self.connected:
            return
        try:
            if self.speed_on and SPEED_BASE_OFFSET is not None:
                a = self._resolve(SPEED_BASE_OFFSET, SPEED_OFFSETS)
                if a:
                    s = self.pm.read_float(a)
                    if self._prev_speed is not None:
                        drop = self._prev_speed - s
                        if 0 < drop < BRAKE_CUT:          # gentle drop = corner scrub -> restore
                            self.pm.write_float(a, s + drop * RETAIN)
                            s = self.pm.read_float(a)
                    self._prev_speed = s
            else:
                self._prev_speed = None

            if self.grip_on and GRIP_BASE_OFFSET is not None:
                g = self._resolve(GRIP_BASE_OFFSET, GRIP_OFFSETS)
                if g:
                    self.pm.write_float(g, GRIP_TARGET)
        except Exception:
            # game closed or address stale -> drop connection, we'll re-attach
            self.connected = False
            self._prev_speed = None

    def read_speed(self):
        """For the on-screen readout / verifying your pointer."""
        if not self.connected or SPEED_BASE_OFFSET is None:
            return None
        try:
            a = self._resolve(SPEED_BASE_OFFSET, SPEED_OFFSETS)
            return self.pm.read_float(a) if a else None
        except Exception:
            return None


# ======================================================================
#  GUI
# ======================================================================

BG    = "#12151c"
CARD  = "#1c2130"
GREEN = "#39d353"
RED   = "#e5534b"
GREY  = "#3a4152"
TEXT  = "#e6e9ef"
MUTE  = "#8b93a7"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.trainer = Trainer()
        self.title("NFS: The Run - Handling Trainer")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.geometry("360x300")

        big = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        med = tkfont.Font(family="Segoe UI", size=10)
        small = tkfont.Font(family="Segoe UI", size=9)

        tk.Label(self, text="NFS: The Run", bg=BG, fg=TEXT, font=big).pack(pady=(16, 0))
        tk.Label(self, text="Handling Trainer", bg=BG, fg=MUTE, font=small).pack()

        self.status = tk.Label(self, text="Waiting for game...", bg=BG, fg=MUTE, font=med)
        self.status.pack(pady=(10, 4))

        self.btn_speed = tk.Button(
            self, text="No Speed Loss:  OFF", font=med, width=26, height=2,
            bg=GREY, fg=TEXT, activebackground=GREY, relief="flat",
            command=self.toggle_speed,
        )
        self.btn_speed.pack(pady=6)

        self.btn_grip = tk.Button(
            self, text="Max Grip:  OFF", font=med, width=26, height=2,
            bg=GREY, fg=TEXT, activebackground=GREY, relief="flat",
            command=self.toggle_grip,
        )
        self.btn_grip.pack(pady=6)

        self.hint = tk.Label(self, text="", bg=BG, fg=MUTE, font=small)
        self.hint.pack(pady=(8, 0))

        # background worker
        self._worker = threading.Thread(target=self._loop, daemon=True)
        self._worker.start()
        self._refresh_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---- button handlers ----
    def toggle_speed(self):
        self.trainer.speed_on = not self.trainer.speed_on
        self._paint_buttons()

    def toggle_grip(self):
        self.trainer.grip_on = not self.trainer.grip_on
        self._paint_buttons()

    def _paint_buttons(self):
        s = self.trainer.speed_on
        self.btn_speed.config(
            text=f"No Speed Loss:  {'ON' if s else 'OFF'}",
            bg=GREEN if s else GREY, fg="#0b0e14" if s else TEXT,
        )
        g = self.trainer.grip_on
        self.btn_grip.config(
            text=f"Max Grip:  {'ON' if g else 'OFF'}",
            bg=GREEN if g else GREY, fg="#0b0e14" if g else TEXT,
        )

    # ---- worker thread: attach + tick ----
    def _loop(self):
        last_attach = 0.0
        while not self.trainer._stop.is_set():
            now = time.time()
            if not self.trainer.connected and now - last_attach > 1.0:
                last_attach = now
                self.trainer.try_attach()
            self.trainer.tick()
            time.sleep(TICK_S)

    # ---- UI refresh on main thread ----
    def _refresh_ui(self):
        if self.trainer.connected:
            spd = self.trainer.read_speed()
            extra = f"   (speed: {spd:.1f})" if spd is not None else ""
            self.status.config(text="Connected ✅" + extra, fg=GREEN)
        else:
            self.status.config(text="Waiting for game...", fg=MUTE)

        if SPEED_BASE_OFFSET is None:
            self.hint.config(text="⚠  Speed address not set - see README step 1")
        elif GRIP_BASE_OFFSET is None:
            self.hint.config(text="Tip: set the Grip address to enable Max Grip")
        else:
            self.hint.config(text="")
        self._paint_buttons()
        self.after(300, self._refresh_ui)

    def _on_close(self):
        self.trainer._stop.set()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
