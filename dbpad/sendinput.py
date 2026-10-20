"""Sends keyboard and mouse input to Windows (SendInput), and tells whether Dirty Bomb is the window in front.

Keys go as hardware scan codes, which games that read DirectInput or raw input (like Dirty Bomb, Unreal
Engine 3) pick up; mouse movement goes as relative motion, the same as a real mouse.
"""
import ctypes
import os
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

INPUT_MOUSE, INPUT_KEYBOARD = 0, 1
KEYEVENTF_KEYUP, KEYEVENTF_SCANCODE = 0x0002, 0x0008
MOUSEEVENTF_MOVE = 0x0001
MOUSE_FLAGS = {
    "MOUSE_LEFT": (0x0002, 0x0004, 0),
    "MOUSE_RIGHT": (0x0008, 0x0010, 0),
    "MOUSE_MIDDLE": (0x0020, 0x0040, 0),
    "MOUSE_X1": (0x0080, 0x0100, 1),
    "MOUSE_X2": (0x0080, 0x0100, 2),
}
MOUSEEVENTF_WHEEL = 0x0800

# Set-1 scan codes (the keys Dirty Bomb's defaults use, and a few more)
SCAN = {
    "ESC": 0x01, "1": 0x02, "2": 0x03, "3": 0x04, "4": 0x05, "5": 0x06, "6": 0x07, "7": 0x08, "8": 0x09,
    "9": 0x0A, "0": 0x0B, "TAB": 0x0F, "Q": 0x10, "W": 0x11, "E": 0x12, "R": 0x13, "T": 0x14, "Y": 0x15,
    "U": 0x16, "I": 0x17, "O": 0x18, "P": 0x19, "ENTER": 0x1C, "LCTRL": 0x1D, "A": 0x1E, "S": 0x1F,
    "D": 0x20, "F": 0x21, "G": 0x22, "H": 0x23, "J": 0x24, "K": 0x25, "L": 0x26, "LSHIFT": 0x2A,
    "Z": 0x2C, "X": 0x2D, "C": 0x2E, "V": 0x2F, "B": 0x30, "N": 0x31, "M": 0x32, "SPACE": 0x39,
    "LALT": 0x38, "F1": 0x3B, "F2": 0x3C, "F3": 0x3D, "F4": 0x3E,
}

ULONG_PTR = ctypes.c_size_t


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]


class _U(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
user32.SendInput.restype = wintypes.UINT


def _key(scan, up):
    i = INPUT(type=INPUT_KEYBOARD)
    i.ki = KEYBDINPUT(0, scan, KEYEVENTF_SCANCODE | (KEYEVENTF_KEYUP if up else 0), 0, 0)
    return i


def _mouse(flags, data=0, dx=0, dy=0):
    i = INPUT(type=INPUT_MOUSE)
    i.mi = MOUSEINPUT(dx, dy, data & 0xFFFFFFFF, flags, 0, 0)
    return i


def build(events):
    """Mapper events -> INPUT records."""
    out = []
    for ev in events:
        kind = ev[0]
        if kind in ("down", "up"):
            name, up = ev[1], kind == "up"
            if name in MOUSE_FLAGS:
                down_flag, up_flag, data = MOUSE_FLAGS[name]
                out.append(_mouse(up_flag if up else down_flag, data))
            elif name in SCAN:
                out.append(_key(SCAN[name], up))
        elif kind == "wheel":
            out.append(_mouse(MOUSEEVENTF_WHEEL, 120 * ev[1]))
        elif kind == "move":
            out.append(_mouse(MOUSEEVENTF_MOVE, 0, ev[1], ev[2]))
    return out


def send(events):
    records = build(events)
    if not records:
        return 0
    arr = (INPUT * len(records))(*records)
    return user32.SendInput(len(records), arr, ctypes.sizeof(INPUT))


# --- is Dirty Bomb in front? ---------------------------------------------------------------------
GAME_EXES = ("shootergame-win32-shipping.exe", "shootergame-win64-shipping.exe", "shootergame.exe")
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.QueryFullProcessImageNameW.argtypes = (wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD))


def foreground_exe():
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(len(buf))
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return os.path.basename(buf.value).lower()
        return ""
    finally:
        kernel32.CloseHandle(h)


def game_in_front():
    return foreground_exe() in GAME_EXES
