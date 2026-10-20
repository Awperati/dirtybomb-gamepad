"""Turns controller state into keyboard and mouse events. Pure logic, no Windows calls, so it is tested on its own.

Each tick, `Mapper.update(state, dt)` takes the controller's buttons and sticks and returns a list of events:
  ("down", input) / ("up", input)   a key or mouse button, e.g. ("down", "W"), ("up", "MOUSE_LEFT")
  ("wheel", +1 / -1)                one mouse-wheel click (+1 = up)
  ("move", dx, dy)                  relative mouse movement in whole pixels
Several controls may send the same key: the key stays down while any of them holds it.
"""
from .actions import ACTIONS, TOGGLE_ACTIONS


class Mapper:
    def __init__(self, settings):
        self.settings = settings
        self.held = {}            # input -> how many controls hold it
        self.prev = {}            # button -> was it down last tick
        self.down_for = {}        # button -> seconds held so far
        self.hold_fired = {}      # button -> its hold action has started
        self.toggled = set()      # toggle actions currently on
        self.frac = [0.0, 0.0]    # mouse movement left over (sub-pixel)

    # --- holding inputs -------------------------------------------------------------------------
    def _press(self, inp, out):
        if not inp:
            return
        if inp.startswith("WHEEL_"):
            out.append(("wheel", 1 if inp == "WHEEL_UP" else -1))
            return
        n = self.held.get(inp, 0)
        self.held[inp] = n + 1
        if n == 0:
            out.append(("down", inp))

    def _release(self, inp, out):
        if not inp or inp.startswith("WHEEL_"):
            return
        n = self.held.get(inp, 0)
        if n <= 0:
            return
        if n == 1:
            del self.held[inp]
            out.append(("up", inp))
        else:
            self.held[inp] = n - 1

    def _action_down(self, action, out):
        if action in TOGGLE_ACTIONS:
            if action in self.toggled:
                self.toggled.discard(action)
                self._release(ACTIONS[action], out)
            else:
                self.toggled.add(action)
                self._press(ACTIONS[action], out)
            return
        self._press(ACTIONS.get(action), out)

    def _action_up(self, action, out):
        if action in TOGGLE_ACTIONS:
            return                      # a toggle stays on until pressed again
        self._release(ACTIONS.get(action), out)

    def release_all(self):
        """Lets go of everything (when turned off, or the game loses focus)."""
        out = [("up", k) for k in list(self.held)]
        self.held.clear()
        self.toggled.clear()
        self.prev.clear()
        self.down_for.clear()
        self.hold_fired.clear()
        self.frac = [0.0, 0.0]
        return out

    # --- one tick -------------------------------------------------------------------------------
    def update(self, state, dt):
        """state: {"buttons": {name: bool}, "axes": {"leftx","lefty","rightx","righty","lefttrigger","righttrigger": -1..1 / 0..1}}"""
        s = self.settings
        out = []
        buttons = dict(state.get("buttons", {}))
        axes = state.get("axes", {})
        thr = s["trigger_threshold"]
        buttons["lefttrigger"] = axes.get("lefttrigger", 0.0) > thr
        buttons["righttrigger"] = axes.get("righttrigger", 0.0) > thr

        for name, bind in s["bindings"].items():
            now = bool(buttons.get(name, False))
            was = self.prev.get(name, False)
            press, hold = bind.get("press", "None"), bind.get("hold", "None")
            has_hold = hold not in (None, "None")
            if not has_hold:
                if now and not was:
                    self._action_down(press, out)
                elif was and not now:
                    self._action_up(press, out)
            else:
                # tap = the press action; held past hold_time = the hold action, kept until let go
                if now:
                    self.down_for[name] = self.down_for.get(name, 0.0) + (dt if was else 0.0)
                    if not self.hold_fired.get(name) and self.down_for[name] >= bind.get("hold_time", s["hold_time"]):
                        self.hold_fired[name] = True
                        self._action_down(hold, out)
                elif was:
                    if self.hold_fired.get(name):
                        self._action_up(hold, out)
                    else:
                        self._action_down(press, out)      # a quick tap: press and let go at once
                        self._action_up(press, out)
                    self.down_for[name] = 0.0
                    self.hold_fired[name] = False
            self.prev[name] = now

        # left stick: W/A/S/D
        dz = s["move_deadzone"]
        lx, ly = axes.get("leftx", 0.0), axes.get("lefty", 0.0)
        for key, on in (("W", ly < -dz), ("S", ly > dz), ("A", lx < -dz), ("D", lx > dz)):
            src = f"stick_{key}"
            if on and not self.prev.get(src):
                self._press(key, out)
            elif not on and self.prev.get(src):
                self._release(key, out)
            self.prev[src] = on

        # right stick: the mouse
        rx, ry = axes.get("rightx", 0.0), axes.get("righty", 0.0)
        mag = (rx * rx + ry * ry) ** 0.5
        ldz = s["look_deadzone"]
        if mag > ldz:
            scaled = min((mag - ldz) / (1.0 - ldz), 1.0) ** s["look_curve"]
            speed = s["look_speed"] * scaled * dt
            if buttons.get("lefttrigger"):
                speed *= s["aim_scale"]
            dx = rx / mag * speed
            dy = ry / mag * speed * s["vertical_scale"] * (-1 if s["invert_y"] else 1)
            self.frac[0] += dx
            self.frac[1] += dy
            mx, my = int(self.frac[0]), int(self.frac[1])
            self.frac[0] -= mx
            self.frac[1] -= my
            if mx or my:
                out.append(("move", mx, my))
        else:
            self.frac = [0.0, 0.0]
        return out
