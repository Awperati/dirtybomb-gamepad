"""Reads controllers through SDL2's game controller API: PlayStation 4/5, Xbox, Switch Pro, 8BitDo and the
many other pads SDL knows all come out in the same layout (SDL's database maps them).

Call `Pads.poll()` from one thread only (SDL wants that); it returns the first connected controller's state.
"""
import ctypes
import os

import sdl2

BUTTON_IDS = {
    "a": sdl2.SDL_CONTROLLER_BUTTON_A, "b": sdl2.SDL_CONTROLLER_BUTTON_B,
    "x": sdl2.SDL_CONTROLLER_BUTTON_X, "y": sdl2.SDL_CONTROLLER_BUTTON_Y,
    "back": sdl2.SDL_CONTROLLER_BUTTON_BACK, "guide": sdl2.SDL_CONTROLLER_BUTTON_GUIDE,
    "start": sdl2.SDL_CONTROLLER_BUTTON_START,
    "leftstick": sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK, "rightstick": sdl2.SDL_CONTROLLER_BUTTON_RIGHTSTICK,
    "leftshoulder": sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER, "rightshoulder": sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER,
    "dpup": sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP, "dpdown": sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN,
    "dpleft": sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT, "dpright": sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT,
    "misc1": sdl2.SDL_CONTROLLER_BUTTON_MISC1, "touchpad": sdl2.SDL_CONTROLLER_BUTTON_TOUCHPAD,
}
AXIS_IDS = {
    "leftx": sdl2.SDL_CONTROLLER_AXIS_LEFTX, "lefty": sdl2.SDL_CONTROLLER_AXIS_LEFTY,
    "rightx": sdl2.SDL_CONTROLLER_AXIS_RIGHTX, "righty": sdl2.SDL_CONTROLLER_AXIS_RIGHTY,
    "lefttrigger": sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT, "righttrigger": sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT,
}


class Pads:
    def __init__(self):
        # keep reading the pad while the game, not this window, is in front
        sdl2.SDL_SetHint(sdl2.SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, b"1")
        for hint in (b"SDL_JOYSTICK_HIDAPI_PS4", b"SDL_JOYSTICK_HIDAPI_PS5", b"SDL_JOYSTICK_HIDAPI_SWITCH"):
            sdl2.SDL_SetHint(hint, b"1")
        if sdl2.SDL_Init(sdl2.SDL_INIT_GAMECONTROLLER | sdl2.SDL_INIT_EVENTS) != 0:
            raise RuntimeError(sdl2.SDL_GetError().decode(errors="replace"))
        self.pad = None
        self.name = ""
        self.kind = ""

    def _open_first(self):
        for i in range(sdl2.SDL_NumJoysticks()):
            if sdl2.SDL_IsGameController(i):
                pad = sdl2.SDL_GameControllerOpen(i)
                if pad:
                    self.pad = pad
                    self.name = (sdl2.SDL_GameControllerName(pad) or b"Controller").decode(errors="replace")
                    try:
                        t = sdl2.SDL_GameControllerGetType(pad)
                        self.kind = {sdl2.SDL_CONTROLLER_TYPE_PS4: "PlayStation", sdl2.SDL_CONTROLLER_TYPE_PS5: "PlayStation",
                                     sdl2.SDL_CONTROLLER_TYPE_XBOX360: "Xbox", sdl2.SDL_CONTROLLER_TYPE_XBOXONE: "Xbox",
                                     sdl2.SDL_CONTROLLER_TYPE_NINTENDO_SWITCH_PRO: "Switch"}.get(t, "Other")
                    except Exception:
                        self.kind = "Other"
                    return

    def poll(self):
        """Handles plug/unplug, then returns {"name", "kind", "buttons", "axes"} or None with no controller."""
        ev = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(ctypes.byref(ev)):
            if ev.type == sdl2.SDL_CONTROLLERDEVICEREMOVED and self.pad is not None:
                if not sdl2.SDL_GameControllerGetAttached(self.pad):
                    sdl2.SDL_GameControllerClose(self.pad)
                    self.pad = None
        if self.pad is None:
            self._open_first()
        if self.pad is None:
            return None
        sdl2.SDL_GameControllerUpdate()
        buttons = {name: bool(sdl2.SDL_GameControllerGetButton(self.pad, bid)) for name, bid in BUTTON_IDS.items()}
        axes = {}
        for name, aid in AXIS_IDS.items():
            v = sdl2.SDL_GameControllerGetAxis(self.pad, aid)
            axes[name] = max(-1.0, v / 32767.0) if "trigger" not in name else max(0.0, v / 32767.0)
        return {"name": self.name, "kind": self.kind, "buttons": buttons, "axes": axes}

    def close(self):
        if self.pad is not None:
            sdl2.SDL_GameControllerClose(self.pad)
        sdl2.SDL_Quit()
