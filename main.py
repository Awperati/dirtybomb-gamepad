"""Dirty Bomb Gamepad: play Dirty Bomb with a PlayStation, Xbox or other controller."""
import sys


def selftest(path):
    """Builds without a window: starts SDL, lists controllers, writes the result to `path` (used by the build check)."""
    lines = []
    try:
        from dbpad.pad import Pads
        p = Pads()
        st = p.poll()
        lines.append("sdl ok")
        lines.append(f"controller: {st['name']} ({st['kind']})" if st else "controller: none")
        p.close()
    except Exception as e:  # pragma: no cover
        lines.append(f"error: {e}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--selftest":
        selftest(sys.argv[2])
    else:
        from dbpad.app import App
        App().run()
