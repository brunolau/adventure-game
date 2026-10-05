"""Run the Godot project for QA without disturbing the person at the computer (owner request 2026-10-06).

Use this instead of calling the Godot console exe for every QA run that opens a window (screenshots, --shots,
--frames, --acceptance, --perf, --play-all with a window). Headless runs may use it too.

    python tools/qa_godot.py --path src/game --resolution 1920x1080 -- --room S05 --screenshot build/screens/S05.png
    python tools/qa_godot.py --headless --path src/game --time-scale 6 -- --fast-text --play-all

What it does (Windows):
- starts the GUI exe (not the console wrapper, so no console window) with STARTUPINFO SW_HIDE: the game window is
  created hidden, never appears on a screen or in the taskbar and never takes the foreground. Godot keeps
  rendering a hidden window, so screenshots, frame captures and settle waits work (a MINIMIZED Godot window
  stops drawing and screenshot runs hang, measured 2026-10-06; that is why the window is hidden, not minimized);
- the game's own QA background mode (scripts/Diagnostics/QaWindow.cs) adds no-focus, off-screen position and a
  muted Master bus (game argument --audible keeps the sound);
- caps a windowed run at --max-fps 60 (a hidden window would otherwise render at the monitor rate) and runs the
  process at below-normal CPU priority, so the computer stays responsive while several QA runs work;
- streams the engine output to stdout and returns the engine's exit code (124 after --qa-timeout).

Launcher options (before the first "--"; all other arguments go to Godot unchanged):
  --qa-show             create the window normally (only for runs the product owner asked to watch; add the game
                        argument --visible to keep it on screen)
  --qa-max-fps N        frame cap for windowed runs (default 60, 0 = engine default)
  --qa-priority P       below (default), idle or normal
  --qa-timeout S        stop the run after S seconds (exit code 124)
Environment: GODOT_EXE overrides the engine executable.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXE = ROOT / ".tools" / "godot" / "Godot_v4.7.2-stable_mono_win64" / "Godot_v4.7.2-stable_mono_win64.exe"

SW_HIDE = 0
CREATE_NO_WINDOW = 0x08000000
PRIORITY = {"normal": 0x00000020, "below": 0x00004000, "idle": 0x00000040}


def parse(argv: list[str]) -> tuple[dict, list[str]]:
    opts = {"show": False, "max_fps": 60, "priority": "below", "timeout": None}
    godot: list[str] = []
    i = 0
    engine_part = True
    while i < len(argv):
        a = argv[i]
        if a == "--":
            engine_part = False
        if engine_part and a.startswith("--qa-"):
            if a == "--qa-show":
                opts["show"] = True
            elif a in ("--qa-max-fps", "--qa-priority", "--qa-timeout") and i + 1 < len(argv):
                value = argv[i + 1]
                i += 1
                if a == "--qa-max-fps":
                    opts["max_fps"] = int(value)
                elif a == "--qa-priority":
                    if value not in PRIORITY:
                        raise SystemExit(f"qa_godot: --qa-priority must be one of {', '.join(PRIORITY)}")
                    opts["priority"] = value
                else:
                    opts["timeout"] = float(value)
            else:
                raise SystemExit(f"qa_godot: unknown or incomplete launcher option {a}")
        else:
            godot.append(a)
        i += 1
    return opts, godot


def main(argv: list[str]) -> int:
    opts, args = parse(argv)
    exe = Path(os.environ.get("GODOT_EXE") or DEFAULT_EXE)
    if exe.name.endswith("_console.exe"):
        exe = exe.with_name(exe.name.replace("_console.exe", ".exe"))  # the wrapper would open a console window
    if not exe.exists():
        raise SystemExit(f"qa_godot: Godot executable not found: {exe}")
    engine = args[: args.index("--")] if "--" in args else args
    if opts["max_fps"] > 0 and "--headless" not in engine and "--max-fps" not in engine:
        args = ["--max-fps", str(opts["max_fps"])] + args

    env = dict(os.environ, LASTBELL_QA_LAUNCHER="1")  # QaWindow warns about windowed QA runs launched without it
    kwargs: dict = {"env": env}
    if os.name == "nt":
        flags = CREATE_NO_WINDOW | PRIORITY[opts["priority"]]
        kwargs["creationflags"] = flags
        if not opts["show"]:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = SW_HIDE
            kwargs["startupinfo"] = si
    proc = subprocess.Popen([str(exe), *args], cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, **kwargs)

    def pump() -> None:
        assert proc.stdout is not None
        out = sys.stdout.buffer
        for line in iter(proc.stdout.readline, b""):
            out.write(line)
            out.flush()

    reader = threading.Thread(target=pump, daemon=True)
    reader.start()
    try:
        code = proc.wait(timeout=opts["timeout"])
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        reader.join(timeout=5)
        print(f"qa_godot: stopped after --qa-timeout {opts['timeout']:g} s", flush=True)
        return 124
    except KeyboardInterrupt:
        proc.kill()
        proc.wait()
        return 130
    reader.join(timeout=5)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
