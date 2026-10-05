"""S41 winter: local fix of one box of a winter master with the owner's photos as extra references (USD 0.15).

Like `paint_natural.py refit fix` (refit_room.cmd_fix: the model edits the whole master, only the box is composited
back with a soft seam, drift compensated), but the images are [master, aligned photo, closer photo, style] and the
output is the next art/masters/bg_natural/S41_winter_v<N>.png.
Usage: python fix_s41_winter.py FROM_N --box x y w h --instruction "..." [--seed N] [--feather 48]
"""
import argparse
import datetime
import json
import random
import re
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[4]   # repo root
sys.path.insert(0, str(ROOT / "art" / "tools"))
import paint_natural  # noqa: E402

paint_natural.install()
import paint_room as pr  # noqa: E402
import refit_room  # noqa: E402
import fal_api  # noqa: E402

ROOM = "S41"
SCOPE = "bg_natural/S41_winter/"
BUDGET = 4.0
DIR = ROOT / "art" / "masters" / "bg_natural"
REFS = [ROOT / "art/source/owner_refs/_S41_aligned_TXI6i3E.png", ROOT / "art/source/owner_refs/imgur_8l08ndF.jpg"]
STYLE = ROOT / "art/backgrounds/tram-stop.png"

PROMPT = (
    "Image 1 is one of our finished point-and-click adventure game backgrounds (a winter scene). Make exactly this "
    "local change: {instruction} Change nothing else: keep every other object, the camera, the composition, all "
    "positions, sizes, colours, the snow and the light exactly as in image 1. Images 2 and 3 are summer photos of the "
    "real place (image 2 from exactly the camera of image 1, image 3 from a little further along the road): use them "
    "only for the real shape of what you change, keep the winter of image 1. No people, no animals, no cars, no text, "
    "no logos, no frames. Image 4 is another background from the same game: keep the same painting technique.")


def next_number():
    nums = [int(m.group(1)) for p in DIR.glob(f"{ROOM}_winter_v*.png")
            if (m := re.fullmatch(rf"{ROOM}_winter_v(\d+)\.png", p.name))]
    return max(nums, default=0) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("from_n", type=int)
    ap.add_argument("--box", type=float, nargs=4, required=True)
    ap.add_argument("--instruction", required=True)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--feather", type=int, default=48)
    ap.add_argument("--from-raw", help="re-composite an earlier raw output (free)")
    ap.add_argument("--image1", help="send this master-geometry image as image 1 instead of the master (e.g. the "
                                     "master with flat-colour blocks painted into the box); compositing still "
                                     "uses the unmodified master outside the box")
    args = ap.parse_args()
    src = DIR / f"{ROOM}_winter_v{args.from_n}.png"
    master = Image.open(src).convert("RGB")
    if master.size != pr.MODEL_FRAME:
        master = master.resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    number = next_number()
    x, y, w, h = args.box
    mx0, my0 = refit_room.to_master(x, y)
    mx1, my1 = refit_room.to_master(x + w, y + h)
    prompt = PROMPT.format(instruction=args.instruction) + " " + pr.style_sentence()
    seed = args.seed if args.seed is not None else random.randint(1, 2**31 - 1)
    asset = f"{SCOPE}{ROOM}_winter_v{number}_fix"
    if args.from_raw:
        raw_path = Path(args.from_raw)
        result = Image.open(raw_path).convert("RGB").resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
        raw = {"seed": None}
        usd = 0.0
    else:
        first = Image.open(args.image1).convert("RGB") if args.image1 else master
        images = [fal_api.image_data_uri(first, fmt="PNG")]
        images += [fal_api.image_data_uri(r, max_side=2048, fmt="JPEG") for r in REFS]
        images.append(fal_api.image_data_uri(STYLE, max_side=1376, fmt="JPEG"))
        ns = argparse.Namespace(scope=SCOPE, budget=BUDGET)
        result, raw_path, raw = refit_room.call_edit(prompt, images, seed, asset, ns)
        usd = fal_api.IMAGE_PRICES[(pr.MODEL, pr.RESOLUTION)]
    outside = Image.new("L", pr.MODEL_FRAME, 255)
    ImageDraw.Draw(outside).rectangle((mx0, my0, mx1, my1), fill=0)
    dx, dy = refit_room.align_shift(result, master, outside)
    if dx or dy:
        result = ImageChops.offset(result, -dx, -dy)
        print(f"model output drifted by {dx:+d},{dy:+d} master px; compensated")
    touch = (x <= 0, y <= 0, x + w >= pr.FRAME[0], y + h >= pr.FRAME[1])
    mbox = (0 if touch[0] else round(mx0), 0 if touch[1] else round(my0),
            pr.MODEL_FRAME[0] if touch[2] else round(mx1), pr.MODEL_FRAME[1] if touch[3] else round(my1))
    mask = refit_room.soft_mask(pr.MODEL_FRAME, mbox, args.feather, open_sides=tuple(not t for t in touch))
    final = Image.composite(result, master, mask)
    out = DIR / f"{ROOM}_winter_v{number}.png"
    final.save(out)
    meta = {"room": ROOM, "version": f"winter_v{number}", "kind": "fix", "from_version": f"winter_v{args.from_n}",
            "box_game_px": [x, y, w, h], "instruction": args.instruction, "feather_master_px": args.feather,
            "drift_compensated_master_px": [dx, dy], "model": pr.MODEL, "seed": raw.get("seed", seed), "usd": usd,
            "scope": SCOPE, "spend_log_asset": asset if usd else None, "prompt": prompt,
            "image1_blocked": bool(args.image1),
            "image_urls": [src.relative_to(ROOT).as_posix() + (" + flat-colour blocks in the box" if args.image1 else "")] + [r.relative_to(ROOT).as_posix() for r in REFS]
            + [STYLE.relative_to(ROOT).as_posix()],
            "raw_model_output": Path(raw_path).relative_to(ROOT).as_posix(),
            "started": datetime.datetime.now().isoformat(timespec="seconds"),
            "model_description": raw.get("description"), "output_size": list(final.size)}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out, f"(scope {SCOPE} spent {fal_api.logged_spend(SCOPE):.2f})")
    paint_natural.natural_review(ROOM, out)


if __name__ == "__main__":
    main()
