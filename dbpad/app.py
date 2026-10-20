"""The window: turn it on/off, tune the look speed, remap buttons (PlayStation labels), and see the controller live.

A worker thread reads the controller ~250 times a second, runs the Mapper and sends the input; the window
only reads its status and edits the settings. Settings are saved next to the app (dbpad_settings.json).
"""
import copy
import json
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

from .actions import ACTIONS, BUTTONS, DEFAULT_SETTINGS
from .mapper import Mapper
from . import gameconfig, sendinput

APP_NAME = "Dirty Bomb Gamepad"
VERSION = "1.0.1"
TICK = 1 / 250

BG, PANEL, FG, MUTED, ACCENT, ON, OFF = "#10161f", "#18212d", "#e6edf5", "#8a9bb0", "#3aa0ff", "#46d17c", "#e05d5d"


def settings_path():
    base = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(sys.argv[0]))
    return os.path.join(base, "dbpad_settings.json")


def load_settings():
    s = copy.deepcopy(DEFAULT_SETTINGS)
    try:
        with open(settings_path(), "r", encoding="utf-8") as f:
            saved = json.load(f)
        binds = s["bindings"]
        binds.update({k: v for k, v in saved.pop("bindings", {}).items() if k in binds})
        s.update({k: v for k, v in saved.items() if k in s})
    except (OSError, ValueError):
        pass
    return s


def save_settings(s):
    try:
        with open(settings_path(), "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2)
    except OSError:
        pass


class Worker(threading.Thread):
    """Reads the pad and sends input. Talks to the window only through `status` and `settings`."""

    def __init__(self, settings):
        super().__init__(daemon=True)
        self.settings = settings
        self.mapper = Mapper(settings)
        self.status = {"pad": None, "state": None, "active": False, "error": ""}
        self.stop_flag = threading.Event()

    def run(self):
        try:
            from .pad import Pads
            pads = Pads()
        except Exception as e:  # SDL missing or failed to start
            self.status["error"] = f"Could not start controller support: {e}"
            return
        last = time.perf_counter()
        focus_checked, in_front = 0.0, False
        while not self.stop_flag.is_set():
            now = time.perf_counter()
            dt, last = now - last, now
            state = pads.poll()
            self.status["state"] = state
            self.status["pad"] = (state["name"], state["kind"]) if state else None
            s = self.settings
            if now - focus_checked > 0.25:
                in_front = sendinput.game_in_front()
                focus_checked = now
            active = bool(state) and s["enabled"] and (in_front or not s["only_when_game_focused"])
            if active:
                sendinput.send(self.mapper.update(state, min(dt, 0.05)))
            elif self.status["active"] or self.mapper.held:
                sendinput.send(self.mapper.release_all())
            self.status["active"] = active
            self.status["in_front"] = in_front
            time.sleep(TICK)
        sendinput.send(self.mapper.release_all())
        pads.close()


class App:
    def __init__(self):
        self.settings = load_settings()
        self.worker = Worker(self.settings)
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} {VERSION}")
        self.root.configure(bg=BG)
        self.root.minsize(980, 600)
        try:
            self.root.iconbitmap(default=resource("icon.ico"))
        except tk.TclError:
            pass
        self._style()
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.worker.start()
        self._refresh()

    # --- look ------------------------------------------------------------------------------------
    def _style(self):
        st = ttk.Style(self.root)
        st.theme_use("clam")
        st.configure(".", background=BG, foreground=FG, fieldbackground=PANEL, bordercolor="#2a3646", font=("Segoe UI", 10))
        st.configure("Panel.TFrame", background=PANEL)
        st.configure("Panel.TLabel", background=PANEL, foreground=FG)
        st.configure("Muted.TLabel", background=PANEL, foreground=MUTED, font=("Segoe UI", 9))
        st.configure("Title.TLabel", background=BG, foreground=FG, font=("Segoe UI Semibold", 16))
        st.configure("Sub.TLabel", background=BG, foreground=MUTED)
        st.configure("TCheckbutton", background=PANEL, foreground=FG)
        st.map("TCheckbutton", background=[("active", PANEL)])
        st.configure("TCombobox", fieldbackground=BG, background=PANEL, foreground=FG, arrowcolor=FG)
        st.map("TCombobox", fieldbackground=[("readonly", BG)], foreground=[("readonly", FG)])
        st.configure("Big.TButton", font=("Segoe UI Semibold", 11), padding=(14, 6))
        st.configure("Horizontal.TScale", background=PANEL, troughcolor=BG)
        self.root.option_add("*TCombobox*Listbox.background", PANEL)
        self.root.option_add("*TCombobox*Listbox.foreground", FG)
        self.root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)

    def _panel(self, parent, title, side=None):
        f = ttk.Frame(parent, style="Panel.TFrame", padding=12)
        if side:
            f.pack(side=side, fill="both", expand=True, padx=(0, 10) if side == "left" else 0)
        else:
            f.pack(fill="x", padx=14, pady=(0, 10))
        ttk.Label(f, text=title, style="Panel.TLabel", font=("Segoe UI Semibold", 11)).pack(anchor="w", pady=(0, 6))
        return f

    def _build(self):
        head = ttk.Frame(self.root, padding=(14, 12, 14, 8))
        head.pack(fill="x")
        ttk.Label(head, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(head, text="Play Dirty Bomb with a PlayStation, Xbox or other controller", style="Sub.TLabel").pack(anchor="w")

        # status and aiming side by side
        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=14, pady=(0, 10))
        p = self._panel(top, "Status", side="left")
        row = ttk.Frame(p, style="Panel.TFrame")
        row.pack(fill="x")
        self.dot = tk.Canvas(row, width=14, height=14, bg=PANEL, highlightthickness=0)
        self.dot.pack(side="left", padx=(0, 8))
        self.dot_id = self.dot.create_oval(2, 2, 12, 12, fill=OFF, outline="")
        self.status_lbl = ttk.Label(row, text="Starting…", style="Panel.TLabel")
        self.status_lbl.pack(side="left")
        self.toggle_btn = ttk.Button(row, style="Big.TButton", command=self.toggle)
        self.toggle_btn.pack(side="right")
        self.pad_lbl = ttk.Label(p, text="", style="Muted.TLabel")
        self.pad_lbl.pack(anchor="w", pady=(6, 0))
        self.live = tk.Canvas(p, height=26, bg=PANEL, highlightthickness=0)
        self.live.pack(fill="x", pady=(6, 0))
        self.focus_var = tk.BooleanVar(value=self.settings["only_when_game_focused"])
        ttk.Checkbutton(p, text="Only while Dirty Bomb is in front (recommended)", variable=self.focus_var,
                        command=lambda: self._set("only_when_game_focused", self.focus_var.get())).pack(anchor="w", pady=(8, 0))
        # the game's own (Xbox) controller bindings: off stops double input, e.g. holding R2 making the game aim
        nat = ttk.Frame(p, style="Panel.TFrame")
        nat.pack(fill="x", pady=(8, 0))
        self.native_lbl = ttk.Label(nat, text="", style="Muted.TLabel")
        self.native_lbl.pack(side="left")
        self.native_btn = ttk.Button(nat, command=self.toggle_native)
        self.native_btn.pack(side="right")
        self._show_native()

        # aiming
        p = self._panel(top, "Aiming (right stick)", side="right")
        self._slider(p, "Look speed", "look_speed", 300, 4000, lambda v: f"{v:.0f}")
        self._slider(p, "Precision curve", "look_curve", 1.0, 3.0, lambda v: f"{v:.2f}")
        self._slider(p, "Dead zone", "look_deadzone", 0.0, 0.4, lambda v: f"{v:.2f}")
        self._slider(p, "Up/down speed", "vertical_scale", 0.3, 1.5, lambda v: f"×{v:.2f}")
        self._slider(p, "Speed while aiming (L2)", "aim_scale", 0.2, 1.0, lambda v: f"×{v:.2f}")
        self.inv_var = tk.BooleanVar(value=self.settings["invert_y"])
        ttk.Checkbutton(p, text="Invert up/down", variable=self.inv_var,
                        command=lambda: self._set("invert_y", self.inv_var.get())).pack(anchor="w", pady=(4, 0))

        # buttons
        p = self._panel(self.root, "Buttons")
        ttk.Label(p, text="Tap does the first action. If a hold action is set, holding the button does that instead.",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 6))
        grid = ttk.Frame(p, style="Panel.TFrame")
        grid.pack(fill="x")
        names = list(ACTIONS)
        half = (len(BUTTONS) + 1) // 2             # two columns of buttons, so the window fits a 1080p screen
        for side in (0, 1):
            base = side * 4
            ttk.Label(grid, text="Button", style="Muted.TLabel").grid(row=0, column=base, sticky="w", padx=(24 if side else 0, 0))
            ttk.Label(grid, text="Tap / press", style="Muted.TLabel").grid(row=0, column=base + 1, sticky="w", padx=6)
            ttk.Label(grid, text="Hold", style="Muted.TLabel").grid(row=0, column=base + 2, sticky="w")
        for i, (key, ps, other) in enumerate(BUTTONS):
            side, r = divmod(i, half)
            base, r = side * 4, r + 1
            label = ps if other in ("—", ps) else f"{ps}  ({other})"
            ttk.Label(grid, text=label, style="Panel.TLabel").grid(row=r, column=base, sticky="w", pady=1, padx=(24 if side else 0, 0))
            for c, slot in ((1, "press"), (2, "hold")):
                var = tk.StringVar(value=self.settings["bindings"][key].get(slot, "None"))
                box = ttk.Combobox(grid, values=names, textvariable=var, state="readonly", width=20)
                box.grid(row=r, column=base + c, sticky="w", padx=(6 if c == 1 else 0, 0), pady=1)
                box.bind("<<ComboboxSelected>>", lambda e, k=key, sl=slot, v=var: self._bind(k, sl, v.get()))
        bottom = ttk.Frame(p, style="Panel.TFrame")
        bottom.pack(fill="x", pady=(8, 0))
        ttk.Button(bottom, text="Reset to defaults", command=self.reset).pack(side="left")
        ttk.Label(bottom, text="Left stick = W A S D (move).", style="Muted.TLabel").pack(side="right")

    def _slider(self, parent, text, key, lo, hi, fmt):
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=text, style="Panel.TLabel", width=22).pack(side="left")
        val = ttk.Label(row, text=fmt(self.settings[key]), style="Panel.TLabel", width=7)
        val.pack(side="right")
        var = tk.DoubleVar(value=self.settings[key])

        def changed(_=None):
            v = var.get()
            val.config(text=fmt(v))
            self._set(key, v)
        ttk.Scale(row, from_=lo, to=hi, variable=var, command=changed).pack(side="left", fill="x", expand=True, padx=8)

    # --- changes ---------------------------------------------------------------------------------
    def _set(self, key, value):
        self.settings[key] = value
        save_settings(self.settings)

    def _bind(self, key, slot, action):
        self.settings["bindings"][key][slot] = action
        save_settings(self.settings)

    def toggle(self):
        self._set("enabled", not self.settings["enabled"])

    def _show_native(self):
        st = gameconfig.status(gameconfig.input_ini())
        if st == "missing":
            self.native_lbl.config(text="Dirty Bomb's settings file wasn't found (run the game once).")
            self.native_btn.config(text="Check again")
        elif st == "on":
            self.native_lbl.config(text="Dirty Bomb's own controller bindings: ON (can double up inputs)")
            self.native_btn.config(text="Turn them off")
        else:
            self.native_lbl.config(text="Dirty Bomb's own controller bindings: OFF (only this app drives the game)")
            self.native_btn.config(text="Turn them back on")

    def toggle_native(self):
        path = gameconfig.input_ini()
        st = gameconfig.status(path)
        if st == "missing":
            return self._show_native()
        if gameconfig.game_running():
            messagebox.showwarning(APP_NAME, "Close Dirty Bomb first.\n\nThe game saves its settings file when it exits, which would undo this.")
            return
        try:
            if st == "on":
                n = gameconfig.disable(path)
                messagebox.showinfo(APP_NAME, f"Turned off {n} of Dirty Bomb's own controller bindings.\n\n"
                                              f"A backup was saved as\n{path + gameconfig.BACKUP_SUFFIX}\n\n"
                                              "Now only this app drives the game, so holding R2 just fires.")
            else:
                n = gameconfig.enable(path)
                messagebox.showinfo(APP_NAME, f"Turned {n} of Dirty Bomb's own controller bindings back on.")
        except OSError as e:
            messagebox.showerror(APP_NAME, f"Couldn't change the settings file:\n{e}")
        self._show_native()

    def reset(self):
        defaults = copy.deepcopy(DEFAULT_SETTINGS)
        self.settings.clear()
        self.settings.update(defaults)
        save_settings(self.settings)
        self.root.destroy()          # rebuild the window with the defaults
        App.__init__(self)

    # --- live view -------------------------------------------------------------------------------
    def _refresh(self):
        st = self.worker.status
        on = self.settings["enabled"]
        self.toggle_btn.config(text="Turn off" if on else "Turn on")
        if st.get("error"):
            text, colour = st["error"], OFF
        elif not st.get("pad"):
            text, colour = "No controller found. Plug one in or pair it over Bluetooth.", OFF
        elif not on:
            text, colour = "Off", OFF
        elif st.get("active"):
            text, colour = "Active: playing Dirty Bomb with the controller", ON
        else:
            text, colour = "Ready: waiting for Dirty Bomb to be in front", "#e8b54a"
        self.status_lbl.config(text=text)
        self.dot.itemconfig(self.dot_id, fill=colour)
        self.pad_lbl.config(text=f"{st['pad'][0]}  ·  {st['pad'][1]} layout" if st.get("pad") else "")
        self._draw_live(st.get("state"))
        self.root.after(50, self._refresh)

    def _draw_live(self, state):
        c = self.live
        c.delete("all")
        if not state:
            return
        x = 2
        pressed = [ps for key, ps, _ in BUTTONS if state["buttons"].get(key)]
        ax = state["axes"]
        if ax.get("lefttrigger", 0) > self.settings["trigger_threshold"]:
            pressed.append("L2")
        if ax.get("righttrigger", 0) > self.settings["trigger_threshold"]:
            pressed.append("R2")
        if not pressed:
            c.create_text(x, 13, text="Press a button to see it here", fill=MUTED, anchor="w", font=("Segoe UI", 9))
            return
        for name in pressed:
            w = 10 + 7 * len(name)
            c.create_rectangle(x, 3, x + w, 23, fill=ACCENT, outline="")
            c.create_text(x + w / 2, 13, text=name, fill="white", font=("Segoe UI Semibold", 9))
            x += w + 6

    def close(self):
        self.worker.stop_flag.set()
        self.worker.join(timeout=1.0)
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def resource(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, name)
