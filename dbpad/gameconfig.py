"""Switches Dirty Bomb's own (leftover Unreal Engine 3 Xbox) controller bindings off and on.

If the game can see the controller itself (an Xbox pad, or a PlayStation pad through Steam Input or
DS4Windows), those bindings fire as well as this app: holding R2, for example, makes the game aim. Turning
them off comments out every `Bindings=(Name="XboxTypeS_...")` line in the player's ShooterInput.ini
(a `;` at the start, which the game ignores), after saving a backup next to it. Turning them back on
removes exactly those markers. Keyboard and mouse bindings are never touched.

Dirty Bomb writes this file when it exits, so the game must be closed while switching.
"""
import ctypes
import os
import shutil
import uuid
from ctypes import wintypes

MARK = ";dbpad-off "
BACKUP_SUFFIX = ".dbpad-backup"


def documents_dir():
    """The user's Documents folder (follows OneDrive or a moved Documents folder)."""
    try:
        class GUID(ctypes.Structure):
            _fields_ = [("d1", wintypes.DWORD), ("d2", wintypes.WORD), ("d3", wintypes.WORD), ("d4", ctypes.c_ubyte * 8)]
        u = uuid.UUID("{FDD39AD0-238F-46AF-ADB4-6C85480369C7}")   # FOLDERID_Documents
        g = GUID(u.fields[0], u.fields[1], u.fields[2], (ctypes.c_ubyte * 8)(*u.bytes[8:]))
        p = ctypes.c_wchar_p()
        if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(g), 0, None, ctypes.byref(p)) == 0:
            path = p.value
            ctypes.windll.ole32.CoTaskMemFree(p)
            return path
    except Exception:
        pass
    return os.path.join(os.path.expanduser("~"), "Documents")


def input_ini():
    return os.path.join(documents_dir(), "My Games", "UnrealEngine3", "ShooterGame", "Config", "ShooterInput.ini")


def _is_pad_binding(line):
    return line.lstrip().startswith('Bindings=(Name="XboxTypeS_')


def status(path):
    """'on' (the game's controller bindings work), 'off' (switched off by this app), or 'missing'."""
    if not os.path.isfile(path):
        return "missing"
    with open(path, "r", encoding="utf-8-sig", errors="surrogateescape") as f:
        lines = f.read().splitlines()
    return "on" if any(_is_pad_binding(l) for l in lines) else "off"


def _rewrite(path, fn):
    with open(path, "r", encoding="utf-8-sig", errors="surrogateescape", newline="") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    changed = 0
    out = []
    for l in lines:
        new = fn(l)
        changed += new != l
        out.append(new)
    if changed:
        with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
            f.write(nl.join(out))
    return changed


def disable(path):
    """Comments out the game's controller bindings. Returns how many lines changed. Backs the file up first."""
    backup = path + BACKUP_SUFFIX
    if not os.path.exists(backup):
        shutil.copy2(path, backup)
    return _rewrite(path, lambda l: MARK + l if _is_pad_binding(l) else l)


def enable(path):
    """Puts back exactly the lines this app commented out. Returns how many lines changed."""
    return _rewrite(path, lambda l: l[len(MARK):] if l.startswith(MARK) else l)


def game_running():
    """Is Dirty Bomb running? (It rewrites ShooterInput.ini when it exits, so switch only while it's closed.)"""
    TH32CS_SNAPPROCESS = 0x2

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD),
                    ("szExeFile", ctypes.c_wchar * 260)]
    k32 = ctypes.windll.kernel32
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if not snap or snap == wintypes.HANDLE(-1).value:
        return False
    try:
        e = PROCESSENTRY32W()
        e.dwSize = ctypes.sizeof(e)
        ok = k32.Process32FirstW(snap, ctypes.byref(e))
        while ok:
            if e.szExeFile.lower().startswith("shootergame"):
                return True
            ok = k32.Process32NextW(snap, ctypes.byref(e))
        return False
    finally:
        k32.CloseHandle(snap)
