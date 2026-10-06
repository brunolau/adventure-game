"""S08 pump track on the far shore: one local edit of master v1 (paid) + a custom re-composite (free).

  python -X utf8 art/ambient/natural/S08_pumptrack/far_shore_fix.py call  --seed N            -> raw model output art/masters/bg_natural/_bg_natural_S08_pumptrack_S08_vN_fix_raw.png
  python -X utf8 art/ambient/natural/S08_pumptrack/far_shore_fix.py comp  --raw <path> [--top 70] [--bottom 302] [--feather-top 40] [--feather-bottom 10]
                                                   -> next master version S08_vN.png + sidecar + review overlay
The composite takes the model output only inside the far-shore band (full width, y top..bottom in game px) and
keeps the original everywhere else, including the round traffic sign and its pole, which stand in front of the band.
"""
from __future__ import annotations

import argparse
import datetime
import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "art" / "tools"))
import fal_api  # noqa: E402
import paint_natural  # noqa: E402
import paint_room as pr  # noqa: E402
import refit_room as rr  # noqa: E402

paint_natural.install()
SCOPE = "bg_natural/S08_pumptrack/"
BUDGET = 1.50
STYLE = "src/game/assets/bg_natural/S03.webp"
OWNER_PHOTO = "art/source/owner_refs/imgur_2tyAMxf.jpg"   # owner-permitted (feedback 2026-10-05 update)

INSTRUCTION = (
    "On the FAR side of the pond only - the band between the far reeds (about 25-29 % from the top of the image) "
    "and the distant hills - remove the flat yellow-green field and the row of five small red-roofed houses, and "
    "paint instead the real pump track of the village: a big, clearly RAISED, long earth hill (a man-made mound "
    "about four metres high) rising right behind the far reeds. Its hummocky top reaches about 13 % from the top of "
    "the image, clearly above the line of the distant hills, and it fills the far shore from the left edge to about "
    "70 % of the width, where it slopes down. A narrow winding packed light-brown dirt bike track runs over the "
    "hill: it snakes across the front face of the mound in long S-curves and one switchback, over a row of small "
    "rounded rollers (bumps in the track), with a banked turn (a raised curved berm) at its left end and another at "
    "its right end; between the track loops there are hummocks of dry autumn grass, ochre and olive tufts of weeds, "
    "a few thistles and two or three small bare bushes, and patches of bare earth. Behind the right part of the hill "
    "and to its right, further away near the horizon and therefore small: a long low white two-storey building with "
    "a row of windows and a flat roof, and a few small village houses with red-brown roofs among small trees; the "
    "blue-grey low hills stay on the horizon behind everything. No people, no bicycles, no animals, no text, no "
    "signs, no fence, no poles.")

PROMPT = (
    "You receive 3 images. Image 1 is one of our finished point-and-click adventure game backgrounds: a pond in "
    "autumn dry-grass scrubland at the edge of a village, seen from a dirt trail on a mound, late October "
    "afternoon. Make exactly this local change: {instruction} Change nothing else: the pond, its water and "
    "reflections, the reeds in the foreground, the bench, the wooden railing, the rusty ferns, the red ball, the "
    "duck, the round blue traffic sign on its pole at the right, the wide dirt trail in the foreground, the sky and "
    "clouds, the camera and the composition stay exactly as in image 1, same positions, sizes, colours and light. "
    "Image 2 is another background from the same game: keep the same painting technique. Image 3 is a real photo "
    "of this very pond and its pump track in spring: use it only for what the narrow dirt track winding over "
    "grassy hummocks looks like; do not copy its view, its season, its colours or the cyclists. {style}")


def call(args) -> None:
    master, meta = rr.load_master("S08", 1)
    seed = args.seed if args.seed is not None else random.randint(1, 2**31 - 1)
    version_hint = pr.next_version("S08")
    asset = f"{SCOPE}S08_v{version_hint}_fix"
    prompt = PROMPT.format(instruction=INSTRUCTION, style=pr.style_sentence())
    images = [fal_api.image_data_uri(master, fmt="PNG"),
              fal_api.image_data_uri(ROOT / STYLE, max_side=1376, fmt="JPEG"),
              fal_api.image_data_uri(ROOT / OWNER_PHOTO, max_side=1376, fmt="JPEG")]
    ns = argparse.Namespace(scope=SCOPE, budget=BUDGET)
    result, raw_path, raw = rr.call_edit(prompt, images, seed, asset, ns)
    side = raw_path.with_suffix(".json")
    side.write_text(json.dumps({"seed": raw.get("seed", seed), "asset": asset, "prompt": prompt,
                                "image_urls": ["art/masters/bg_natural/S08_v1.png", STYLE, OWNER_PHOTO],
                                "model": pr.MODEL, "usd": 0.15, "scope": SCOPE,
                                "started": datetime.datetime.now().isoformat(timespec="seconds"),
                                "model_description": raw.get("description")}, indent=2, ensure_ascii=False),
                    encoding="utf-8")
    print(raw_path, "seed", raw.get("seed", seed), "spent", fal_api.logged_spend(SCOPE))


def g2m(v: float) -> float:
    return v / rr.K


def band_mask(top: float, bottom: float, f_top: float, f_bottom: float) -> Image.Image:
    """Full-width band in master px with separate soft edges at the top and the bottom, sign and pole cut out."""
    W, H = pr.MODEL_FRAME
    ys = np.arange(H, dtype=np.float32)
    t0, b0 = g2m(top), g2m(bottom)
    ft, fb = max(1.0, g2m(f_top)), max(1.0, g2m(f_bottom))
    up = np.clip((ys - t0) / ft, 0, 1)                   # 0 at top, 1 at top + feather
    down = np.clip((b0 - ys) / fb, 0, 1)                 # 1 above bottom - feather, 0 at bottom
    col = np.minimum(up, down)
    col = col * col * (3 - 2 * col)
    a = np.repeat(col[:, None], W, axis=1)
    # the round sign (centre 1814,262 game px, edge radius ~65) and its pole (x 1805-1822) stay original
    xs = (np.arange(W, dtype=np.float32) * rr.K) - rr.CROP_X  # master x -> game x
    gy = ys * rr.K
    X, Y = np.meshgrid(xs, gy)
    r = np.sqrt((X - 1814) ** 2 + (Y - 262) ** 2)
    sign = np.clip((66.5 - r) / 2.0, 0, 1)
    pole = ((X >= 1804) & (X <= 1823) & (Y >= 300)).astype(np.float32)
    keep = np.maximum(sign, pole)
    a = a * (1 - keep)
    return Image.fromarray((a * 255).round().astype(np.uint8), "L")


def comp(args) -> None:
    master, meta = rr.load_master("S08", 1)
    raw_path = ROOT / args.raw
    result = Image.open(raw_path).convert("RGB")
    if result.size != pr.MODEL_FRAME:
        result = result.resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    outside = Image.new("L", pr.MODEL_FRAME, 255)
    ImageDraw.Draw(outside).rectangle((0, round(g2m(args.top - 20)), pr.MODEL_FRAME[0], round(g2m(args.bottom + 10))),
                                      fill=0)
    dx, dy = rr.align_shift(result, master, outside)
    if dx or dy:
        result = ImageChops.offset(result, -dx, -dy)
        print(f"model output drifted by {dx:+d},{dy:+d} master px; compensated")
    mask = band_mask(args.top, args.bottom, args.feather_top, args.feather_bottom)
    final = Image.composite(result, master, mask)
    rawmeta = {}
    side = raw_path.with_suffix(".json")
    if side.exists():
        rawmeta = json.loads(side.read_text(encoding="utf-8"))
    rr.save_version("S08", final, {
        "kind": "fix", "from_version": 1,
        "box_game_px": [0, args.top, 1920, args.bottom - args.top],
        "composite": (f"model output only in the full-width far-shore band y {args.top}-{args.bottom} game px (soft "
                      f"top {args.feather_top} px, bottom {args.feather_bottom} px), the round traffic sign (centre "
                      "1814,262, r 66) and its pole x 1804-1823 kept original; everything else = v1"),
        "instruction": INSTRUCTION, "drift_compensated_master_px": [dx, dy], "model": pr.MODEL,
        "seed": rawmeta.get("seed"), "usd": rawmeta.get("usd", 0.0) if not args.recomposite else 0.0,
        "scope": SCOPE, "spend_log_asset": rawmeta.get("asset"), "prompt": rawmeta.get("prompt"),
        "image_urls": rawmeta.get("image_urls"), "raw_model_output": raw_path.relative_to(ROOT).as_posix(),
        "started": datetime.datetime.now().isoformat(timespec="seconds"),
        "model_description": rawmeta.get("model_description"), "parent_prompt": meta.get("prompt")})


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("call")
    p.add_argument("--seed", type=int)
    p.set_defaults(func=call)
    p = sub.add_parser("comp")
    p.add_argument("--raw", required=True)
    p.add_argument("--top", type=float, default=70)
    p.add_argument("--bottom", type=float, default=302)
    p.add_argument("--feather-top", type=float, default=40)
    p.add_argument("--feather-bottom", type=float, default=10)
    p.add_argument("--recomposite", action="store_true", help="the raw was already counted in an earlier version")
    p.set_defaults(func=comp)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
