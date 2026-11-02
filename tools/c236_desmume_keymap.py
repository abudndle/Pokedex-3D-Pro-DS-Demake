#!/usr/bin/env python3
"""Write an isolated SDL2 DeSmuME CLI keymap for asset-free CI.

DeSmuME CLI loads [SDLKEYS] from $XDG_CONFIG_HOME/desmume/config. SDL2
keycodes are NOT X11 keysyms or SDL1.2 arrow constants. Prefer printable\nkeys for headless input injection. Never touch the
user's existing DeSmuME config.
"""
import argparse
import os
from pathlib import Path

SDL_SCANCODE_MASK = 1 << 30
KEYS = {
    # Use distinct printable keys for direction/B. This avoids SDL/X11
    # arrow-scancode translation on headless CI and is NOT a user keymap.
    "A": ord("x"), "B": ord("b"),
    "Select": SDL_SCANCODE_MASK | 229, "Start": 13,
    "Right": ord("d"), "Left": ord("f"),
    "Up": ord("i"), "Down": ord("k"),
    "R": ord("w"), "L": ord("q"),
    "X": ord("s"), "Y": ord("a"),
    "Debug": ord("p"), "Boost": ord("o"), "Lid": 8,
}


def write_config(xdg_config_home):
    """Create exactly one new config; fail closed on existing/symlink paths."""
    root = Path(xdg_config_home)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("XDG config root must be an existing real directory")
    folder = root / "desmume"
    if folder.exists() or folder.is_symlink():
        raise FileExistsError("isolated DeSmuME config directory already exists")
    folder.mkdir(mode=0o700)
    content = "[SDLKEYS]\n" + "".join(
        f"{name}={code}\n" for name, code in KEYS.items())
    target = folder / "config"
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="ascii", newline="\n") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xdg-config-home", type=Path, required=True)
    args = parser.parse_args()
    path = write_config(args.xdg_config_home)
    print("Isolated DeSmuME SDL2 CLI keymap installed at", path)
    print("Expected SDL2 keycodes: A=%d B=%d Right=%d" %
          (KEYS["A"], KEYS["B"], KEYS["Right"]))


if __name__ == "__main__":
    main()
