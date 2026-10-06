"""In-engine screenshots of the S30 on the old Stary most (1995) into build/screens/s30_stary_most/ (background QA window via
tools/qa_godot.py, exactly like `paint_natural.py screens`, only another output folder and extra tags).
Usage: python screens_s30.py [--no-import] [--tag entry] [--act ID ...] [--replay N] [--frames 8] [--interval 500]
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]   # repo root
sys.path.insert(0, str(ROOT / "art" / "tools"))
import paint_natural  # noqa: E402

OUT = ROOT / "build" / "screens" / "s30_stary_most"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-import", action="store_true")
    ap.add_argument("--tag", default="entry")
    ap.add_argument("--act", action="append")
    ap.add_argument("--replay", type=int)
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--interval", type=int, default=500)
    ap.add_argument("--extra", nargs="*", default=[], help="extra harness args after --")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.no_import:
        with paint_natural.ImportLock():
            paint_natural.godot(["--headless", "--import"], timeout=1200)
    state = []
    if args.replay:
        state += ["--replay", str(args.replay)]
    for act in args.act or []:
        state += ["--act", act]
    base = ["--resolution", "1920x1080", "--", "--blocking", "natural"] + state + ["--room", "S30", "--fast-text",
                                                                                 "--skip-lines"] + args.extra
    t = args.tag
    shots = [
        base + ["--labels", "--wait", "800", "--screenshot", str(OUT / f"{t}_labels.png")],
        base + ["--wait", "800", "--screenshot", str(OUT / f"{t}_clean.png")],
        base + ["--wait", "1500", "--frames", str(args.frames), "--interval", str(args.interval),
                "--screenshot", str(OUT / f"{t}_motion.png")],
    ]
    codes = [paint_natural.godot(s, timeout=300) for s in shots]
    print("exit codes", codes, "->", OUT)


if __name__ == "__main__":
    main()
