"""Local paid edit of a natural master with extra reference images and polygon masks (L_YARD podlubie + lawn).

Owner feedback 2026-10-06 ("S17 family refinements"): the concrete footpath left of the court fence becomes lawn,
and right of the yard entrance the ground floor is an open covered underpass ("podlubie") to the blocks behind.
`refit_room.py fix` takes one rectangle and only the style image; this variant passes reference images (the owner's
own imgur photo `imgur_fNEtUPs.jpg`, owner permission 2026-10-05 -> may be a generator input; the accepted S17 result
for the other eras) and composites the model output only inside the spec's regions, minus tight "protect" polygons
(story props that must stay pixel-identical).

  python -X utf8 podlubie_fix.py run <room> <from_version> --spec <spec.json> [--seed N] [--budget 3.0]
  python -X utf8 podlubie_fix.py recomposite <room> <from_version> --spec <spec.json> --raw <raw.png>   (free)
  python -X utf8 podlubie_fix.py mask <room> --spec <spec.json>            (free: mask preview over the master)

spec.json (game coordinates 1920x1080):
  {"instruction_file": "....txt", "refs": ["art/source/owner_refs/imgur_fNEtUPs.jpg", ...],
   "style": "art/backgrounds/sokolikova-yard.png", "feather": 14,
   "regions": [{"rect": [x, y, w, h]} | {"poly": [[x, y], ...]}],
   "protect": [{"rect": [...]} | {"poly": [...]} | {"hue_rect": [x, y, w, h], "hue": [h0, h1], "sat": s, "grow": px}],
   "keep_from": null}
`keep_from` (optional) = a master version whose pixels are pasted back inside `protect` instead of the from-version.
"""
from __future__ import annotations

import argparse
import colorsys
import datetime
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(r"C:\Users\klatt\Desktop\adventura")
sys.path.insert(0, str(ROOT / "art" / "tools"))
import paint_natural  # noqa: E402

paint_natural.install()
import fal_api  # noqa: E402
import paint_room as pr  # noqa: E402
import refit_room as rr  # noqa: E402

PROMPT_HEAD = (
    "Image 1 is one of our finished point-and-click adventure game backgrounds (painted, style A). "
    "Make exactly the local changes described below and change nothing else: keep every other object, the camera, "
    "the composition, all positions, sizes, colours and the light exactly as in image 1. No people, no animals, "
    "no cars, no text, no letters, no logos, no frames. ")


def to_m(x: float, y: float) -> tuple[float, float]:
    return rr.to_master(x, y)


def poly_of(item: dict) -> list[tuple[float, float]]:
    if "rect" in item:
        x, y, w, h = item["rect"]
        pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    else:
        pts = [tuple(p) for p in item["poly"]]
    return [to_m(*p) for p in pts]


def build_mask(spec: dict, master: Image.Image) -> tuple[Image.Image, Image.Image]:
    """(take, protect): take = where the model output is used (soft), protect = pasted back from the original."""
    size = pr.MODEL_FRAME
    take = Image.new("L", size, 0)
    d = ImageDraw.Draw(take)
    for item in spec["regions"]:
        d.polygon(poly_of(item), fill=255)
    feather = round(spec.get("feather", 14) / rr.K)
    if feather:
        take = take.filter(ImageFilter.GaussianBlur(feather / 2))
    protect = Image.new("L", size, 0)
    for item in spec.get("protect", []):
        layer = Image.new("L", size, 0)
        if "hue_rect" in item:
            x, y, w, h = item["hue_rect"]
            (mx0, my0), (mx1, my1) = to_m(x, y), to_m(x + w, y + h)
            box = tuple(round(v) for v in (mx0, my0, mx1, my1))
            crop = master.crop(box).convert("RGB")
            hm = Image.new("L", crop.size, 0)
            px, hp = crop.load(), hm.load()
            h0, h1 = item["hue"]
            for j in range(crop.height):
                for i in range(crop.width):
                    r, g, b = px[i, j]
                    hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                    hue = hh * 360
                    inside = (h0 <= hue <= h1) if h0 <= h1 else (hue >= h0 or hue <= h1)
                    if (inside and item.get("sat", 0.4) <= ss <= item.get("sat_max", 1.0)
                            and vv >= item.get("val", 0.15)):
                        hp[i, j] = 255
            layer.paste(hm, box[:2])
        else:
            ImageDraw.Draw(layer).polygon(poly_of(item), fill=255)
        # grow (> 0) / erode (< 0) in master px: an eroded protect lets the model's own (near-identical) object
        # outline over the new background replace the old outline, so no rim of the old background stays.
        grow = item.get("grow", 0)
        if grow > 0:
            layer = layer.filter(ImageFilter.MaxFilter(2 * grow + 1))
        elif grow < 0:
            layer = layer.filter(ImageFilter.MinFilter(2 * -grow + 1))
        protect = ImageChops.lighter(protect, layer)
    pf = spec.get("protect_feather", 1.5)
    if pf:
        protect = protect.filter(ImageFilter.GaussianBlur(pf))
    return take, protect


def composite(spec: dict, master: Image.Image, result: Image.Image, keep: Image.Image | None):
    take, protect = build_mask(spec, master)
    outside = take.point(lambda v: 255 if v < 8 else 0)
    dx, dy = rr.align_shift(result, master, outside)
    if dx or dy:
        result = ImageChops.offset(result, -dx, -dy)
        print(f"model output drifted by {dx:+d},{dy:+d} master px; compensated")
    final = Image.composite(result, master, take)
    final = Image.composite(keep if keep is not None else master, final, protect)
    return final, (dx, dy), take, protect


def load_spec(path: str) -> dict:
    spec = json.loads((ROOT / path).read_text(encoding="utf-8"))
    spec["instruction"] = (ROOT / spec["instruction_file"]).read_text(encoding="utf-8").strip()
    return spec


def cmd_mask(args) -> None:
    spec = load_spec(args.spec)
    master, _ = rr.load_master(args.room, args.version)
    take, protect = build_mask(spec, master)
    tint = Image.new("RGB", master.size, (255, 0, 255))
    prev = Image.composite(tint, master, take.point(lambda v: v // 2))
    prev = Image.composite(Image.new("RGB", master.size, (0, 255, 255)), prev, protect.point(lambda v: v // 2))
    out = ROOT / "art" / "review" / "natural" / f"{args.room}_podlubie_mask.png"
    prev.resize((1376, 768)).save(out)
    print(out)


def cmd_run(args, raw_path: Path | None = None) -> None:
    spec = load_spec(args.spec)
    master, meta = rr.load_master(args.room, args.version)
    keep = rr.load_master(args.room, spec["keep_from"])[0] if spec.get("keep_from") else None
    prompt = PROMPT_HEAD + spec["instruction"] + " " + pr.style_sentence()
    seed = args.seed if args.seed is not None else random.randint(1, 2**31 - 1)
    hint = pr.next_version(args.room)
    if raw_path is None:
        asset = f"{args.scope}{args.room}_v{hint}_podlubie"
        images = [fal_api.image_data_uri(master, fmt="PNG")]
        images += [fal_api.image_data_uri(ROOT / r, max_side=1600, fmt="JPEG") for r in spec.get("refs", [])]
        images.append(fal_api.image_data_uri(ROOT / spec["style"], max_side=1376, fmt="JPEG"))
        result, raw_path, raw = rr.call_edit(prompt, images, seed, asset, args)
        usd = fal_api.IMAGE_PRICES[(pr.MODEL, pr.RESOLUTION)]
    else:
        result = Image.open(raw_path).convert("RGB").resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
        raw, asset, usd = {"seed": None}, "", 0.0
    final, drift, _, _ = composite(spec, master, result, keep)
    rr.save_version(args.room, final, {
        "kind": "fix" if usd else "recomposite", "tool": "S17_scripts/podlubie_fix.py", "from_version": args.version,
        "spec": args.spec, "regions_game_px": spec["regions"], "protect_game_px": spec.get("protect", []),
        "instruction": spec["instruction"], "drift_compensated_master_px": list(drift), "model": pr.MODEL,
        "seed": raw.get("seed", seed) if usd else None, "usd": usd, "scope": args.scope if usd else "",
        "spend_log_asset": asset, "prompt": prompt,
        "image_urls": [f"art/masters/bg_natural/{args.room}_v{args.version}.png"] + spec.get("refs", [])
        + [spec["style"]],
        "raw_model_output": Path(raw_path).resolve().relative_to(ROOT).as_posix(),
        "started": datetime.datetime.now().isoformat(timespec="seconds"), "parent_prompt": meta.get("prompt")})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "recomposite", "mask"):
        p = sub.add_parser(name)
        p.add_argument("room")
        if name != "mask":
            p.add_argument("version", type=int)
        else:
            p.add_argument("version", type=int)
        p.add_argument("--spec", required=True)
        p.add_argument("--seed", type=int)
        p.add_argument("--budget", type=float, default=3.0)
        p.add_argument("--scope", default="bg_natural/L_YARD_podlubie/")
        if name == "recomposite":
            p.add_argument("--raw", required=True)
    args = ap.parse_args()
    if args.cmd == "mask":
        cmd_mask(args)
    elif args.cmd == "run":
        cmd_run(args)
    else:
        cmd_run(args, raw_path=ROOT / args.raw)


if __name__ == "__main__":
    main()
