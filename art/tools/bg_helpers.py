"""Helpers for painting room backgrounds that complement paint_room.py / refit_room.py (art/tools/PAINTING.md).

Found while painting S02 S03 S04 S06 S07 (batch "prologue2020", 2026-10-05; logs in art/masters/bg/<room>.md).
Only `prezoom-paint` is paid (one nano-banana-pro call through fal_api.run: budget guard + art/spend-log.csv);
the other commands are free pixel operations that write a normal master version (+ sidecar + review overlay).

  prezoom-paint ROOM --plan S TX TY --scope bg/x/ --budget USD [--seed N] [--dry-run]
        Paint with a PRE-ZOOMED sketch: art/prompts/<room>.sketch.json is drawn at the eye-level scale the model
        prefers (it re-composes frontage sketches 1.3-2x larger), and a later `refit_room.py extend --scale S
        --offset TX TY` brings the props into their rects. Identical to `paint_room.py paint` except that
        {rect:...} placeholders expand to the PLANNED sketch coordinates ((game - offset) / scale). Do not use
        {walk}, {exit:...} or {npc_zones} in such a prompt (they would map outside the frame).
  trim ROOM VERSION CUT_Y --note "..."
        Grey out everything below game y CUT_Y, so that a following `refit_room.py extend` repaints it instead of
        keeping it (e.g. a kerb that would land above the walk band after scaling). Pass --keep to the extend so the
        grey strip is not pasted back.
  remap ROOM VERSION TOP OLD NEW --note "..."
        Vertical row remap: rows above TOP stay identical, input rows TOP..OLD are stretched smoothly onto
        TOP..NEW (slope ramps in over the first quarter, the kink lands on the strong edge at NEW), rows below shift
        by NEW-OLD. Used to push a kerb out of the walk band when everything between is empty paving.
  recomposite ROOM BASE_VERSION RAW X Y W H [--feather 30] --note "..."
        Re-composite the raw output of an earlier paid `refit_room.py fix` onto BASE_VERSION with another box
        (game px). Lesson: the fix box must exceed the object by more than the feather (fix uses 48 master px ~
        34 game px, capped at a third of the box); a tight box leaves a half-transparent ghost (S02 v3).

All coordinates are game-frame (1920x1080) coordinates, as in review_room.py --grid.
Run from the repo root: PYTHONIOENCODING=utf-8 python -X utf8 art/tools/bg_helpers.py <command> ...
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paint_room as pr  # noqa: E402
import refit_room as rf  # noqa: E402


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def cmd_prezoom_paint(args) -> None:
    s, tx, ty = args.plan
    original_box_text = pr.box_text

    def planned_box_text(rect):
        x, y, w, h = rect
        return original_box_text([round((x - tx) / s), round((y - ty) / s), round(w / s), round(h / s)])

    pr.box_text = planned_box_text
    if args.dry_run:
        print(pr.assemble(args.room)["prompt"])
        return
    args.mode = "auto"
    version = pr.next_version(args.room)
    pr.cmd_paint(args)
    side = pr.MASTERS / f"{args.room}_v{version}.json"
    meta = json.loads(side.read_text(encoding="utf-8"))
    meta["prezoom_plan"] = {"scale": s, "offset_game_px": [tx, ty],
                            "note": "sketch drawn pre-zoomed; {rect:} expanded to planned sketch coordinates; "
                                    "refit with refit_room.py extend at about this transform"}
    side.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def cmd_trim(args) -> None:
    master, meta = rf.load_master(args.room, args.version)
    _, my = rf.to_master(0, args.cut_y)
    img = master.copy()
    ImageDraw.Draw(img).rectangle((0, round(my), pr.MODEL_FRAME[0], pr.MODEL_FRAME[1]), fill=rf.GREY)
    rf.save_version(args.room, img, {
        "kind": "trim (free)", "from_version": args.version, "cut_game_y": args.cut_y, "usd": 0.0, "scope": "",
        "note": args.note, "started": _now(), "parent_prompt": meta.get("prompt")})


def cmd_remap(args) -> None:
    master, meta = rf.load_master(args.room, args.version)
    top, old, new = args.top, args.old, args.new
    arr = np.asarray(master).astype(np.float32)
    height = arr.shape[0]
    yo = np.arange(height) * rf.K                       # output rows in game px
    ramp = 0.25
    span_out, span_in = new - top, old - top
    s_c = (span_in / span_out - ramp / 2) / (1 - ramp / 2)
    t = np.clip((yo - top) / span_out, 0, 1)
    fine = np.linspace(0, 1, 4001)
    u = np.clip(fine / ramp, 0, 1)
    slope = np.where(fine < ramp, 1 + (s_c - 1) * (3 * u ** 2 - 2 * u ** 3), s_c)
    cum = np.concatenate([[0], np.cumsum((slope[1:] + slope[:-1]) / 2 * np.diff(fine))])
    cum *= (span_in / span_out) / cum[-1]
    yi = np.where(yo <= top, yo, np.where(yo >= new, yo - (new - old), top + span_out * np.interp(t, fine, cum)))
    src = np.clip(yi / rf.K, 0, height - 1)
    lo = np.floor(src).astype(int)
    hi = np.minimum(lo + 1, height - 1)
    w = (src - lo)[:, None, None]
    out = arr[lo] * (1 - w) + arr[hi] * w
    img = Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), "RGB")
    print(f"constant stretch {1 / s_c:.3f}x; input row {old:g} -> output row {new:g}")
    rf.save_version(args.room, img, {
        "kind": "row remap (free)", "from_version": args.version, "top_game_y": top, "old_game_y": old,
        "new_game_y": new, "usd": 0.0, "scope": "", "note": args.note, "started": _now(),
        "parent_prompt": meta.get("prompt")})


def cmd_recomposite(args) -> None:
    master, meta = rf.load_master(args.room, args.base_version)
    result = Image.open(pr.ROOT / args.raw).convert("RGB").resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    x, y, w, h = args.box
    mx0, my0 = rf.to_master(x, y)
    mx1, my1 = rf.to_master(x + w, y + h)
    outside = Image.new("L", pr.MODEL_FRAME, 255)
    ImageDraw.Draw(outside).rectangle((mx0, my0, mx1, my1), fill=0)
    dx, dy = rf.align_shift(result, master, outside)
    if dx or dy:
        result = ImageChops.offset(result, -dx, -dy)
        print(f"model output drifted by {dx:+d},{dy:+d} master px; compensated")
    mask = rf.soft_mask(pr.MODEL_FRAME, (round(mx0), round(my0), round(mx1), round(my1)), args.feather)
    final = Image.composite(result, master, mask)
    rf.save_version(args.room, final, {
        "kind": "fix-recomposite (free)", "from_version": args.base_version, "box_game_px": [x, y, w, h],
        "feather_master_px": args.feather, "drift_compensated_master_px": [dx, dy], "usd": 0.0, "scope": "",
        "raw_model_output": args.raw, "note": args.note, "started": _now(), "parent_prompt": meta.get("prompt")})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prezoom-paint")
    p.add_argument("room")
    p.add_argument("--plan", type=float, nargs=3, required=True, metavar=("S", "TX", "TY"))
    p.add_argument("--seed", type=int)
    p.add_argument("--scope", required=True)
    p.add_argument("--budget", type=float, required=True)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_prezoom_paint)
    p = sub.add_parser("trim")
    p.add_argument("room")
    p.add_argument("version", type=int)
    p.add_argument("cut_y", type=float)
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_trim)
    p = sub.add_parser("remap")
    p.add_argument("room")
    p.add_argument("version", type=int)
    p.add_argument("top", type=float)
    p.add_argument("old", type=float)
    p.add_argument("new", type=float)
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_remap)
    p = sub.add_parser("recomposite")
    p.add_argument("room")
    p.add_argument("base_version", type=int)
    p.add_argument("raw", help="raw model output, repo-relative (art/masters/bg/_<asset>_raw.png)")
    p.add_argument("box", type=float, nargs=4, metavar=("X", "Y", "W", "H"))
    p.add_argument("--feather", type=int, default=30, help="soft seam width in master px")
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_recomposite)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
