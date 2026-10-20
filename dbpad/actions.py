"""What a controller button can do in Dirty Bomb, and the keys/mouse buttons behind each action.

The keys are Dirty Bomb's default binds (ShooterInput.ini). If you have rebound something in the game,
change the key here or pick a different action in the app.
"""

# action name -> input it sends. Keys are scan-code names (see sendinput.py), plus mouse buttons and the wheel.
ACTIONS = {
    "None": None,
    "Fire": "MOUSE_LEFT",
    "Aim (ironsights)": "MOUSE_RIGHT",
    "Jump": "SPACE",
    "Long jump (Alt)": "LALT",          # Left Alt bound to "Duck | Jump" in Dirty Bomb (see README)
    "Crouch": "LCTRL",
    "Sprint (hold)": "LSHIFT",
    "Sprint (toggle)": "LSHIFT",          # special: press once to sprint, again to stop
    "Reload": "R",
    "Use / revive / plant": "F",
    "Ability 1 (Q)": "Q",
    "Ability 2 (E)": "E",
    "Quick melee": "MOUSE_MIDDLE",
    "Heavy melee": "MOUSE_X1",
    "Primary weapon (1)": "1",
    "Secondary weapon (2)": "2",
    "Melee weapon (3)": "3",
    "Item slot 4": "4",
    "Item slot 5": "5",
    "Next weapon": "WHEEL_DOWN",
    "Previous weapon": "WHEEL_UP",
    "Scoreboard": "TAB",
    "Menu (Esc)": "ESC",
    "Quick chat (V)": "V",
    "Push to talk (X)": "X",
    "Show ally names (Z)": "Z",
    "Chat: all (Y)": "Y",
    "Chat: team (U)": "U",
    "Enter": "ENTER",
}

TOGGLE_ACTIONS = {"Sprint (toggle)"}

# Controller buttons in SDL's names, shown with PlayStation labels (Xbox / Switch labels in brackets).
BUTTONS = [
    ("a", "Cross ✕", "A"),
    ("b", "Circle ○", "B"),
    ("x", "Square □", "X"),
    ("y", "Triangle △", "Y"),
    ("leftshoulder", "L1", "LB"),
    ("rightshoulder", "R1", "RB"),
    ("lefttrigger", "L2", "LT"),
    ("righttrigger", "R2", "RT"),
    ("leftstick", "L3", "LS"),
    ("rightstick", "R3", "RS"),
    ("dpup", "D-pad ↑", "D-pad ↑"),
    ("dpdown", "D-pad ↓", "D-pad ↓"),
    ("dpleft", "D-pad ←", "D-pad ←"),
    ("dpright", "D-pad →", "D-pad →"),
    ("start", "Options", "Menu"),
    ("back", "Create / Share", "View"),
    ("touchpad", "Touchpad click", "—"),
    ("misc1", "Mute", "Share"),
    ("guide", "PS button", "Xbox button"),
]

# Default layout, modelled on PlayStation shooters.
DEFAULT_BINDINGS = {
    "a": {"press": "Jump", "hold": "Long jump (Alt)", "hold_time": 0.18},   # tap jumps, hold a moment for a long jump
    "b": {"press": "Crouch", "hold": "None"},
    "x": {"press": "Reload", "hold": "Use / revive / plant"},     # tap reloads, hold uses / revives / plants
    "y": {"press": "Next weapon", "hold": "None"},
    "leftshoulder": {"press": "Ability 1 (Q)", "hold": "None"},
    "rightshoulder": {"press": "Ability 2 (E)", "hold": "None"},
    "lefttrigger": {"press": "Aim (ironsights)", "hold": "None"},
    "righttrigger": {"press": "Fire", "hold": "None"},
    "leftstick": {"press": "Sprint (toggle)", "hold": "None"},
    "rightstick": {"press": "Quick melee", "hold": "None"},
    "dpup": {"press": "Primary weapon (1)", "hold": "None"},
    "dpdown": {"press": "Secondary weapon (2)", "hold": "None"},
    "dpleft": {"press": "Melee weapon (3)", "hold": "None"},
    "dpright": {"press": "Use / revive / plant", "hold": "None"},
    "start": {"press": "Menu (Esc)", "hold": "None"},
    "back": {"press": "Scoreboard", "hold": "None"},
    "touchpad": {"press": "Quick chat (V)", "hold": "None"},
    "misc1": {"press": "Push to talk (X)", "hold": "None"},
    "guide": {"press": "None", "hold": "None"},
}

SETTINGS_VERSION = 2

DEFAULT_SETTINGS = {
    "version": SETTINGS_VERSION,
    "enabled": True,
    "only_when_game_focused": True,
    "look_speed": 1400,        # mouse pixels a second with the right stick pushed all the way
    "look_curve": 1.8,         # 1 = straight line; higher = finer aim near the centre
    "look_deadzone": 0.12,
    "vertical_scale": 0.8,     # up/down speed compared with left/right
    "aim_scale": 0.6,          # look speed while aiming (L2)
    "invert_y": False,
    "move_deadzone": 0.35,     # how far the left stick goes before W/A/S/D press
    "trigger_threshold": 0.3,
    "hold_time": 0.30,         # seconds a button must be held for its "hold" action (a button can set its own)
    "bindings": DEFAULT_BINDINGS,
}
