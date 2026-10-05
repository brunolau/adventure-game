"""Paint / review / export a room for its NATURAL re-blocking (docs/reblock/README.md).

Same recipe and code as paint_room.py and review_room.py (art/tools/PAINTING.md), but every placeholder, overlay and
crop uses the room's effective natural geometry: game.json merged with src/game/data/blocking/<room>.json (merge in
tools/check_blocking.py, the same field-by-field rule as src/game/scripts/World/Room.cs). Nothing of the template
pipeline is overwritten:

  prompt + sketch   art/prompts/natural/<room>.txt, art/prompts/natural/<room>.sketch.json
  layout guide      art/layout/natural/<room>.png, sketch render art/layout/natural/<room>_sketch.png
  masters           art/masters/bg_natural/<room>_v<N>.png (+ .json sidecar)
  review            art/review/natural/<room>_v<N>_overlay.png, _crops.png (no art_overrides nudges)
  export            src/game/assets/bg_natural/<room>.webp (the template bg/<room>.webp stays)

Usage (from the repo root, PYTHONIOENCODING=utf-8 python -X utf8 ...):
  art/tools/paint_natural.py prompt S05
  art/tools/paint_natural.py paint  S05 --scope bg_natural/ --budget 4 [--seed N]     (USD 0.15 per call)
  art/tools/paint_natural.py review S05 2 [--grid x0 y0 x1 y1]
  art/tools/paint_natural.py export S05 2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layout_guide  # noqa: E402
import paint_room  # noqa: E402
import review_room  # noqa: E402

ROOT = paint_room.ROOT
sys.path.insert(0, str(ROOT / "tools"))
import check_blocking  # noqa: E402

ART = ROOT / "art"
_template_load_room = paint_room.load_room


def natural_room(room_id: str) -> tuple[dict, dict]:
    room, anchors = _template_load_room(room_id)
    path = check_blocking.blocking_path(room_id)
    if not path.exists():
        sys.exit(f"no natural blocking {path.relative_to(ROOT)}")
    eff = check_blocking.effective_room(room, json.loads(path.read_text(encoding="utf-8")))
    eff.pop("_blocking", None)
    return eff, anchors


def install() -> None:
    """Point paint_room / review_room at the natural geometry and the separate output folders."""
    paint_room.load_room = natural_room
    paint_room.PROMPTS = ART / "prompts" / "natural"
    paint_room.LAYOUT = ART / "layout" / "natural"
    paint_room.MASTERS = ART / "masters" / "bg_natural"
    paint_room.EXPORT = ROOT / "src" / "game" / "assets" / "bg_natural"
    review_room.load_room = natural_room
    review_room.MASTERS = paint_room.MASTERS
    review_room.REVIEW = ART / "review" / "natural"
    review_room.load_nudges = lambda room_id: {}   # art_overrides nudges belong to the template painting


def write_guide(room_id: str) -> None:
    room, anchors = natural_room(room_id)
    paint_room.LAYOUT.mkdir(parents=True, exist_ok=True)
    layout_guide.draw_room(room, anchors).save(paint_room.LAYOUT / f"{room_id}.png")


def fix_sidecar(room_id: str) -> None:
    """paint_room writes the template paths of the prompt and sketch into the sidecar; record the natural ones."""
    version = paint_room.next_version(room_id) - 1
    path = paint_room.MASTERS / f"{room_id}_v{version}.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["prompt_file"] = f"art/prompts/natural/{room_id}.txt"
    meta["blocking_file"] = f"src/game/data/blocking/{room_id}.json"
    if meta.get("image_urls"):
        meta["image_urls"][0] = (f"art/layout/natural/{room_id}_sketch.png (rendered from "
                                 f"art/prompts/natural/{room_id}.sketch.json, model geometry)")
    path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    install()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prompt")
    p.add_argument("room")
    p.add_argument("--mode", choices=["auto", "sketch", "guide"], default="auto")
    p = sub.add_parser("paint")
    p.add_argument("room")
    p.add_argument("--mode", choices=["auto", "sketch", "guide"], default="auto")
    p.add_argument("--seed", type=int)
    p.add_argument("--budget", type=float, required=True)
    p.add_argument("--scope", default="bg_natural/")
    p = sub.add_parser("review")
    p.add_argument("room")
    p.add_argument("version")
    p.add_argument("--grid", type=int, nargs=4)
    p = sub.add_parser("export")
    p.add_argument("room")
    p.add_argument("version", type=int)
    p.add_argument("--quality", type=int, default=90)
    args = ap.parse_args()
    if args.cmd in ("prompt", "paint"):
        write_guide(args.room)
    if args.cmd == "prompt":
        paint_room.cmd_prompt(args)
    elif args.cmd == "paint":
        paint_room.cmd_paint(args)
        fix_sidecar(args.room)
    elif args.cmd == "review":
        if args.grid:
            review_room.grid_crop(args.room, args.version, tuple(args.grid))
        else:
            review_room.review(args.room, args.version)
    else:
        paint_room.cmd_export(args)


if __name__ == "__main__":
    main()
