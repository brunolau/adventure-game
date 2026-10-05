"""Fix the blocking of a painted master without repainting the room (art/tools/PAINTING.md, steps 5-6).

nano-banana-pro composes at its own "natural" scale: it keeps the left-to-right order of a sketch but often draws
the scene larger/closer, so every prop lands too low and too wide apart. Two repair paths, both keep the accepted
painting pixel-exact where it is not changed:

  fit     (free)  measure each prop's bounding box in the master (game coordinates, e.g. with a gridded crop) and
                  find the uniform scale + offset that puts every prop into its hotspot rect.
                    python refit_room.py fit S05 3 --box "S05.tray=250,410,420,490" --box "S05.shed_door=625,380,780,480" ...
  extend  (paid)  scale the master by that transform, put it on the 16:9 canvas and let the model paint ONLY the
                  uncovered margins (outpainting); the original pixels are composited back on top with a soft seam.
                    python refit_room.py extend S05 3 --scale 0.840 --offset -92 -168 --note "..." [--dry-run]
                  --keep X Y W H limits where the original is pasted back (put the seam on a strong edge such as a
                  kerb; a seam through a texture like paving shows doubled joints); --from-raw re-composites an
                  earlier paid output for free.
  fix     (paid)  local edit of one region with a hand-written instruction (e.g. "make the bag smaller and move it
                  left"); only the given box (game coordinates) is taken from the model's output, with a soft seam.
                    python refit_room.py fix S01 2 --box 100 95 330 175 --instruction "..."
Measure prop boxes with: python review_room.py S05 3 --grid x0 y0 x1 y1
Each paid command writes the next master version art/masters/bg/<room>_v<N>.png + .json and its review overlay.
Coordinates are game-frame (1920x1080) coordinates: x' = scale * x + offset_x, y' = scale * y + offset_y.
"""
from __future__ import annotations

import argparse
import datetime
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fal_api  # noqa: E402
import paint_room as pr  # noqa: E402

K = pr.FRAME[1] / pr.MODEL_FRAME[1]                       # game px per master px (0.703125)
CROP_X = (round(pr.MODEL_FRAME[0] * K) - pr.FRAME[0]) // 2  # 7 px cropped on the left by fit_to_frame
GREY = (128, 128, 128)


def to_master(x: float, y: float) -> tuple[float, float]:
    return (x + CROP_X) / K, y / K


def load_master(room: str, version: int) -> tuple[Image.Image, dict]:
    path = pr.MASTERS / f"{room}_v{version}.png"
    if not path.exists():
        sys.exit(f"missing {path}")
    side = path.with_suffix(".json")
    meta = json.loads(side.read_text(encoding="utf-8")) if side.exists() else {}
    img = Image.open(path).convert("RGB")
    if img.size != pr.MODEL_FRAME:
        img = img.resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    return img, meta


# --------------------------------------------------------------------------- fit

def parse_boxes(items: list[str]) -> dict[str, tuple[float, float, float, float]]:
    boxes = {}
    for item in items:
        ident, coords = item.split("=", 1)
        x0, y0, x1, y1 = (float(v) for v in coords.split(","))
        boxes[ident.strip()] = (x0, y0, x1, y1)
    return boxes


def prop_score(box, rect) -> float:
    """max(share of the prop inside the rect, share of the rect covered by the prop)."""
    bx0, by0, bx1, by1 = box
    rx, ry, rw, rh = rect
    ix = max(0.0, min(bx1, rx + rw) - max(bx0, rx))
    iy = max(0.0, min(by1, ry + rh) - max(by0, ry))
    inter = ix * iy
    return max(inter / max(1.0, (bx1 - bx0) * (by1 - by0)), inter / (rw * rh))


def best_fit(boxes: dict, rects: dict, s_range=(0.5, 1.0)) -> tuple[float, float, float, float]:
    def score(s, tx, ty):
        return min(prop_score((s * b[0] + tx, s * b[1] + ty, s * b[2] + tx, s * b[3] + ty), rects[i])
                   for i, b in boxes.items())

    best = (-1.0, 1.0, 0.0, 0.0)
    for step_s, step_t, span in ((0.01, 8, None), (0.002, 2, 24)):
        if span is None:
            s_values = [s_range[0] + k * step_s for k in range(int((s_range[1] - s_range[0]) / step_s) + 1)]
            t_values = [(tx, ty) for tx in range(-600, 601, step_t) for ty in range(-600, 601, step_t)]
        else:
            _, s0, tx0, ty0 = best
            s_values = [s0 + k * step_s for k in range(-5, 6)]
            t_values = [(tx0 + dx, ty0 + dy) for dx in range(-span, span + 1, step_t)
                        for dy in range(-span, span + 1, step_t)]
        for s in s_values:
            for tx, ty in t_values:
                value = score(s, tx, ty)
                if value > best[0]:
                    best = (value, s, tx, ty)
    return best


def cmd_fit(args) -> None:
    room, _ = pr.load_room(args.room)
    rects = {h["id"]: h["rect"] for h in room["hotspots"]}
    boxes = parse_boxes(args.box)
    unknown = set(boxes) - set(rects)
    if unknown:
        sys.exit(f"unknown hotspot ids: {', '.join(sorted(unknown))}")
    value, s, tx, ty = best_fit(boxes, rects, (args.min_scale, 1.0))
    print(f"scale {s:.3f} offset {tx:+.0f} {ty:+.0f}  (worst prop score {value:.2f}; 1.0 = prop fully inside or "
          f"rect fully covered)")
    for ident, b in boxes.items():
        nb = (s * b[0] + tx, s * b[1] + ty, s * b[2] + tx, s * b[3] + ty)
        print(f"  {ident:16} -> x {nb[0]:.0f}-{nb[2]:.0f}, y {nb[1]:.0f}-{nb[3]:.0f}   rect {rects[ident]}   "
              f"score {prop_score(nb, rects[ident]):.2f}")
    print(f"uncovered after scaling: x {s * pr.FRAME[0] + tx:.0f}-1920 (right), y {s * pr.FRAME[1] + ty:.0f}-1080 "
          f"(bottom), x 0-{max(0, tx):.0f} (left), y 0-{max(0, ty):.0f} (top)")
    print(f"next: python refit_room.py extend {args.room} {args.version} --scale {s:.3f} --offset {tx:.0f} {ty:.0f}")


# --------------------------------------------------------------------------- compositing helpers

def soft_mask(size, box, feather: int, open_sides=(True, True, True, True)) -> Image.Image:
    """White box with soft edges on the sides flagged in open_sides (left, top, right, bottom)."""
    x0, y0, x1, y1 = box
    feather = max(0, min(feather, int((x1 - x0) // 3), int((y1 - y0) // 3)))  # thin boxes get a thinner seam
    l, t, r, b = open_sides
    inner = (x0 + (feather if l else 0), y0 + (feather if t else 0),
             x1 - (feather if r else 0), y1 - (feather if b else 0))
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rectangle(inner, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(feather / 2)) if feather else mask


def align_shift(result: Image.Image, reference: Image.Image, mask: Image.Image, radius: int = 16) -> tuple[int, int]:
    """Integer shift of `result` that best matches `reference` inside `mask` (the model may drift a few px)."""
    scale = 4
    small = (result.width // scale, result.height // scale)
    a = result.convert("L").resize(small)
    b = reference.convert("L").resize(small)
    m = mask.resize(small).point(lambda v: 255 if v > 250 else 0)
    best = (float("inf"), 0, 0)
    for dy in range(-radius // scale, radius // scale + 1):
        for dx in range(-radius // scale, radius // scale + 1):
            shifted = ImageChops.offset(a, dx, dy)
            diff = ImageChops.difference(shifted, b)
            black = Image.new("L", small, 0)
            stat = sum(Image.composite(diff, black, m).histogram()[k] * k for k in range(256))
            if stat < best[0]:
                best = (stat, dx, dy)
    return best[1] * scale, best[2] * scale


def call_edit(prompt: str, images: list[str], seed: int, asset: str, args) -> Image.Image:
    arguments = {"prompt": prompt, "image_urls": images, "aspect_ratio": pr.ASPECT, "resolution": pr.RESOLUTION,
                 "output_format": "png", "num_images": 1, "seed": seed}
    price = fal_api.IMAGE_PRICES[(pr.MODEL, pr.RESOLUTION)]
    result = fal_api.run(pr.MODEL, arguments, asset, price, budget=(args.scope, args.budget), timeout_s=900)
    tmp = pr.MASTERS / f"_{asset.replace('/', '_')}_raw.png"
    fal_api.download(result["images"][0]["url"], tmp)
    img = Image.open(tmp).convert("RGB")
    if img.size != pr.MODEL_FRAME:
        img = img.resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    return img, tmp, result


def save_version(room: str, img: Image.Image, meta: dict) -> int:
    version = pr.next_version(room)
    out = pr.MASTERS / f"{room}_v{version}.png"
    img.save(out)
    meta = dict(meta, room=room, version=version, output_size=list(img.size))
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    spent = f"scope {meta['scope']} spent {fal_api.logged_spend(meta['scope']):.2f}" if meta.get("scope") else "free"
    print(f"{out.relative_to(pr.ROOT)}  ({spent})")
    import review_room
    review_room.review(room, version)
    return version


# --------------------------------------------------------------------------- extend

EXTEND_PROMPT = (
    "Image 1 is one of our finished point-and-click adventure game backgrounds, placed on a larger 16:9 canvas; "
    "the flat grey areas ({areas}) are empty canvas. Paint ONLY those grey areas so the picture continues "
    "seamlessly: {note} Keep the painted part of image 1 exactly as it is - same positions, sizes, colours and "
    "details; do not move, rescale, redraw or crop anything that is already painted. No people, no animals, no "
    "cars, no text, no logos, no frames or borders. Image 2 is another background from the same game: match its "
    "painting technique and keep the brushwork, palette and light of image 1.")


def cmd_extend(args) -> None:
    master, meta = load_master(args.room, args.version)
    s, (tx, ty) = args.scale, args.offset
    mx, my = (tx + CROP_X * (1 - s)) / K, ty / K           # offset in master pixels
    scaled = master.resize((round(master.width * s), round(master.height * s)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", pr.MODEL_FRAME, GREY)
    canvas.paste(scaled, (round(mx), round(my)))
    x0, y0 = max(0, round(mx)), max(0, round(my))
    x1, y1 = min(pr.MODEL_FRAME[0], round(mx) + scaled.width), min(pr.MODEL_FRAME[1], round(my) + scaled.height)
    open_sides = (x0 > 0, y0 > 0, x1 < pr.MODEL_FRAME[0], y1 < pr.MODEL_FRAME[1])
    names = ["left", "top", "right", "bottom"]
    areas = " and ".join(f"along the {n} edge" for n, o in zip(names, open_sides) if o) or "none"
    canvas_path = pr.MASTERS / f"{args.room}_v{args.version}_extend_canvas.png"
    canvas.save(canvas_path)
    print(f"canvas {canvas_path.relative_to(pr.ROOT)}: painting covers master px x {x0}-{x1}, y {y0}-{y1}; "
          f"grey {areas}")
    if args.dry_run:
        return
    style = pr.ROOT / args.style
    prompt = EXTEND_PROMPT.format(areas=areas, note=args.note) + " " + pr.style_sentence()
    seed = args.seed if args.seed is not None else random.randint(1, 2**31 - 1)
    version_hint = pr.next_version(args.room)
    if args.from_raw:
        # Re-composite an earlier paid result with a different seam (free).
        raw_path = pr.ROOT / args.from_raw
        result = Image.open(raw_path).convert("RGB").resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
        raw, asset, usd = {"seed": None, "description": f"re-composite of {args.from_raw}"}, "", 0.0
    else:
        asset = f"{args.scope}{args.room}_v{version_hint}_extend"
        images = [fal_api.image_data_uri(canvas, fmt="PNG"),
                  fal_api.image_data_uri(style, max_side=1376, fmt="JPEG")]
        result, raw_path, raw = call_edit(prompt, images, seed, asset, args)
        usd = fal_api.IMAGE_PRICES[(pr.MODEL, pr.RESOLUTION)]
    if args.keep:
        # Paste the original back only inside this box (game px), e.g. down to a kerb line, so the seam runs
        # along a strong edge instead of through a texture (a seam through paving shows doubled joints).
        kx0, ky0 = to_master(args.keep[0], args.keep[1])
        kx1, ky1 = to_master(args.keep[0] + args.keep[2], args.keep[1] + args.keep[3])
        nx0, ny0, nx1, ny1 = max(x0, round(kx0)), max(y0, round(ky0)), min(x1, round(kx1)), min(y1, round(ky1))
        open_sides = (nx0 > 0, ny0 > 0, nx1 < pr.MODEL_FRAME[0], ny1 < pr.MODEL_FRAME[1])
        x0, y0, x1, y1 = nx0, ny0, nx1, ny1
    mask = soft_mask(pr.MODEL_FRAME, (x0, y0, x1, y1), args.feather, open_sides)
    dx, dy = align_shift(result, canvas, mask)
    if dx or dy:
        result = ImageChops.offset(result, -dx, -dy)
        print(f"model output drifted by {dx:+d},{dy:+d} master px; compensated")
    final = Image.composite(canvas, result, mask)
    save_version(args.room, final, {
        "kind": "extend", "from_version": args.version, "scale": s, "offset_game_px": [tx, ty],
        "feather_master_px": args.feather, "drift_compensated_master_px": [dx, dy], "model": pr.MODEL,
        "seed": raw.get("seed", seed), "usd": usd, "scope": args.scope if usd else "",
        "spend_log_asset": asset, "prompt": prompt, "keep_game_px": args.keep,
        "image_urls": [canvas_path.relative_to(pr.ROOT).as_posix(), args.style],
        "raw_model_output": raw_path.relative_to(pr.ROOT).as_posix(),
        "started": datetime.datetime.now().isoformat(timespec="seconds"),
        "model_description": raw.get("description"), "parent_prompt": meta.get("prompt")})


# --------------------------------------------------------------------------- fix

FIX_PROMPT = (
    "Image 1 is one of our finished point-and-click adventure game backgrounds. Make exactly this local change: "
    "{instruction} Change nothing else: keep every other object, the camera, the composition, all positions, "
    "sizes, colours and the light exactly as in image 1. No people, no animals, no text, no logos, no frames. "
    "Image 2 is another background from the same game: keep the same painting technique.")


def cmd_fix(args) -> None:
    master, meta = load_master(args.room, args.version)
    x, y, w, h = args.box
    mx0, my0 = to_master(x, y)
    mx1, my1 = to_master(x + w, y + h)
    style = pr.ROOT / args.style
    prompt = FIX_PROMPT.format(instruction=args.instruction) + " " + pr.style_sentence()
    seed = args.seed if args.seed is not None else random.randint(1, 2**31 - 1)
    version_hint = pr.next_version(args.room)
    asset = f"{args.scope}{args.room}_v{version_hint}_fix"
    images = [fal_api.image_data_uri(master, fmt="PNG"), fal_api.image_data_uri(style, max_side=1376, fmt="JPEG")]
    result, raw_path, raw = call_edit(prompt, images, seed, asset, args)
    outside = Image.new("L", pr.MODEL_FRAME, 255)
    ImageDraw.Draw(outside).rectangle((mx0, my0, mx1, my1), fill=0)
    dx, dy = align_shift(result, master, outside)
    if dx or dy:
        result = ImageChops.offset(result, -dx, -dy)
        print(f"model output drifted by {dx:+d},{dy:+d} master px; compensated")
    # A side that touches the game frame's edge runs to the canvas edge with no feather: feathering it would blend the
    # old pixels back in along the frame border (S09 v4: a half-transparent ghost of the replaced object).
    touch = (x <= 0, y <= 0, x + w >= pr.FRAME[0], y + h >= pr.FRAME[1])
    mbox = (0 if touch[0] else round(mx0), 0 if touch[1] else round(my0),
            pr.MODEL_FRAME[0] if touch[2] else round(mx1), pr.MODEL_FRAME[1] if touch[3] else round(my1))
    mask = soft_mask(pr.MODEL_FRAME, mbox, args.feather, open_sides=tuple(not t for t in touch))
    final = Image.composite(result, master, mask)
    save_version(args.room, final, {
        "kind": "fix", "from_version": args.version, "box_game_px": [x, y, w, h], "instruction": args.instruction,
        "feather_master_px": args.feather, "drift_compensated_master_px": [dx, dy], "model": pr.MODEL,
        "seed": raw.get("seed", seed), "usd": fal_api.IMAGE_PRICES[(pr.MODEL, pr.RESOLUTION)], "scope": args.scope,
        "spend_log_asset": asset, "prompt": prompt,
        "image_urls": [f"art/masters/bg/{args.room}_v{args.version}.png", args.style],
        "raw_model_output": raw_path.relative_to(pr.ROOT).as_posix(),
        "started": datetime.datetime.now().isoformat(timespec="seconds"),
        "model_description": raw.get("description"), "parent_prompt": meta.get("prompt")})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("fit")
    p.add_argument("room")
    p.add_argument("version", type=int)
    p.add_argument("--box", action="append", required=True, help="hotspot_id=x0,y0,x1,y1 (prop bbox, game px)")
    p.add_argument("--min-scale", type=float, default=0.5)
    p.set_defaults(func=cmd_fit)

    for name, func in (("extend", cmd_extend), ("fix", cmd_fix)):
        p = sub.add_parser(name)
        p.add_argument("room")
        p.add_argument("version", type=int)
        p.add_argument("--style", default="art/backgrounds/sokolikova-street.png")
        p.add_argument("--seed", type=int)
        p.add_argument("--budget", type=float, default=6.0)
        p.add_argument("--scope", default=pr.DEFAULT_SCOPE)
        p.add_argument("--feather", type=int, default=48, help="soft seam width in master px")
        p.set_defaults(func=func)
        if name == "extend":
            p.add_argument("--scale", type=float, required=True)
            p.add_argument("--offset", type=float, nargs=2, required=True, metavar=("TX", "TY"))
            p.add_argument("--note", default="", help="what the new areas contain, e.g. 'continue the pavement'")
            p.add_argument("--dry-run", action="store_true", help="only build and save the canvas (free)")
            p.add_argument("--keep", type=float, nargs=4, metavar=("X", "Y", "W", "H"),
                           help="paste the original back only inside this box (game px after scaling)")
            p.add_argument("--from-raw", help="re-use an earlier raw model output instead of a new paid call")
        else:
            p.add_argument("--box", type=float, nargs=4, required=True, metavar=("X", "Y", "W", "H"),
                           help="region (game px) that may change; everything outside stays pixel-exact")
            p.add_argument("--instruction", required=True)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
