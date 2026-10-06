"""In-engine screenshots of the content v2 art in the QA tree (qa_content_v2.py tree), through tools/qa_godot.py
(hidden window). Output: build/screens/content_v2/<room>/<tag>_*.png.

  python qa_screens.py [SHOT ...]      (default: all shots below)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
QA = ROOT / "build" / "qa_content_v2"
OUT = ROOT / "build" / "screens" / "content_v2"

# tag -> (room, state args, extra args)
SHOTS = {
    "S69_entry": ("S69", ["--replay", "11"], ["--labels"]),
    "S69_clean": ("S69", ["--replay", "11"], []),
    "S69_motion": ("S69", ["--replay", "11"], ["--frames", "6", "--interval", "700"]),
    "S69_life": ("S69", ["--replay", "11"], ["--frames", "36", "--interval", "500"]),
    "S69_after_Q11A": ("S69", ["--replay", "11", "--act", "Q11A"], []),
    "S69_after_Q11B": ("S69", ["--replay", "11", "--act", "Q11A", "--act", "Q11B"], []),
    "S69_after_Q11C": ("S69", ["--replay", "11", "--act", "Q11A", "--act", "Q11B", "--act", "Q11C"], []),
    "S69_B19": ("S69", ["--replay", "29", "--act", "B19"], []),
    "S18_exit": ("S18", ["--replay", "11"], ["--labels"]),
    "S17_sign": ("S17", ["--replay", "11"], ["--labels"]),
    "S37_1962": ("S37", ["--replay", "33"], ["--labels"]),
    "S37_clean": ("S37", ["--replay", "33"], []),
    "S37_after_Q10A": ("S37", ["--replay", "33", "--act", "Q10A"], []),
    "S37_after_Q10D": ("S37", ["--replay", "33", "--act", "Q10A", "--act", "Q10B", "--act", "Q10C", "--act", "Q10D"], []),
    "S32_1962": ("S32", ["--replay", "33"], ["--labels"]),
    "S38_1962": ("S38", ["--replay", "33"], ["--labels"]),
}


def run(tag: str) -> int:
    room, state, extra = SHOTS[tag]
    out = OUT / room
    out.mkdir(parents=True, exist_ok=True)
    shot = out / f"{tag}.png"
    wait = ["--wait", "1500"]
    args = [sys.executable, "-X", "utf8", str(ROOT / "tools" / "qa_godot.py"), "--qa-timeout", "420",
            "--path", str(QA / "game"), "--resolution", "1920x1080", "--",
            "--content-ext", str(QA / "content_ext"), "--blocking", "natural"] + state + \
        ["--room", room, "--fast-text", "--skip-lines"] + extra + wait + ["--screenshot", str(shot)]
    proc = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=480)
    keep = [line for line in proc.stdout.splitlines()
            if line.startswith("HARNESS") and ("state" in line or "screenshot" in line or "BLOCKER" in line
                                                or "FAIL" in line or "error" in line.lower())
            or "ERROR" in line or "SCRIPT ERROR" in line]
    print(f"{tag}: exit {proc.returncode}")
    for line in keep[-8:]:
        print("   " + line[:300])
    return proc.returncode


def main() -> None:
    tags = sys.argv[1:] or list(SHOTS)
    codes = {t: run(t) for t in tags}
    print({t: c for t, c in codes.items() if c})


if __name__ == "__main__":
    main()
