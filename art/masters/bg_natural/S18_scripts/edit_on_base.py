"""S18 / S62 painter "sokolikova-street" (owner feedback 2026-10-06): minimal edits on the owner-loved style-test
painting art/backgrounds/sokolikova-street.png (imported unchanged as art/masters/bg_natural/S18_v2.png).

Method ("placeholders on the painting"): flat colour shapes for the new objects are pasted onto the base painting
(game coordinates, converted to master pixels) and ONE nano-banana-pro edit repaints only those shapes; the model
output is then composited back onto the base ONLY inside the edit boxes (soft seam, drift compensated), so the rest
of the painting stays pixel-identical to the owner's picture.

  canvas  ROOM [--spec NAME]           build the placeholder canvas + preview (free)
  paint   ROOM --base V [--spec NAME] --budget USD [--seed N]
                                       one paid edit (USD 0.15) -> next master version + sidecar + review
  composite ROOM --base V --raw RAW [--spec NAME]
                                       re-composite an earlier raw output with the spec's boxes (free)
  revert  ROOM --base V --from-version R --box x0 y0 x1 y1 [...]
                                       copy vV and put back vR's pixels inside the boxes (free)

Specs live in this file (SPECS). Scope bg_natural/sokolikova_street/ (task budget USD 3 for S18 + S62).
Run from the repo root: PYTHONIOENCODING=utf-8 python -X utf8 art/masters/bg_natural/S18_scripts/edit_on_base.py ...
"""
from __future__ import annotations

import argparse
import datetime
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "art" / "tools"))
import fal_api  # noqa: E402
import paint_natural  # noqa: E402
import paint_room as pr  # noqa: E402
import refit_room  # noqa: E402

paint_natural.install()
SCOPE = "bg_natural/sokolikova_street/"
SCRATCH = ROOT / "art" / "review" / "natural"


def m(x: float, y: float) -> tuple[float, float]:
    """game px -> master px"""
    return refit_room.to_master(x, y)


def poly(points):
    return [m(x, y) for x, y in points]


def rect(x0, y0, x1, y1):
    return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


# --------------------------------------------------------------------------- specs

def s18_shapes(d: ImageDraw.ImageDraw) -> None:
    cream, cream_lit, shade, trim, roof = "#e6d6b4", "#f0e4c8", "#9c8c78", "#7a3328", "#4a2a22"
    # Kiosk (front plane y 880, ~122 px/m there; 2.5 m wide, 2.6 m tall, sill 1.05 m = y 752)
    d.polygon(poly([(316, 576), (398, 582), (398, 858), (316, 880)]), fill=shade)           # right side wall (shade)
    d.polygon(poly([(2, 556), (326, 556), (404, 570), (404, 580), (326, 578), (2, 578)]), fill=roof)  # roof slab
    d.polygon(rect(10, 578, 316, 880), fill=cream)                                           # front wall
    d.polygon(rect(10, 584, 316, 630), fill=cream_lit)                                       # blank fascia
    d.polygon(rect(10, 630, 316, 637), fill=trim)
    d.polygon(rect(10, 764, 316, 771), fill=trim)
    # left pane: newspapers on clips (grey columns on off-white sheets)
    d.polygon(rect(20, 642, 97, 764), fill="#d8d8d0")
    for i, (x0, y0) in enumerate([(24, 648), (60, 650), (24, 706), (60, 704)]):
        d.polygon(rect(x0, y0, x0 + 32, y0 + 52), fill="#f4f2ea")
        for k in range(4):
            d.polygon(rect(x0 + 4, y0 + 8 + 10 * k, x0 + 28, y0 + 12 + 10 * k), fill="#8a8a84")
    # centre: open sales hatch (dark interior) with a light counter ledge
    d.polygon(rect(105, 642, 221, 752), fill="#3a2c26")
    d.polygon(rect(98, 748, 228, 758), fill="#d9cbb0")
    # right pane: colourful sweets / chewing gum packets
    d.polygon(rect(229, 650, 306, 764), fill="#d8d8d0")
    colours = ["#e8402a", "#f2c12e", "#3aa655", "#2f7fd8", "#e86fb0", "#f08a24", "#8c4fd0", "#26b8c0"]
    for row in range(5):
        for col in range(3):
            x0, y0 = 234 + col * 24, 655 + row * 21
            d.polygon(rect(x0, y0, x0 + 20, y0 + 16), fill=colours[(row * 3 + col) % len(colours)])
    # Bench on the lawn strip in front of the near block, parallel to the strip
    wood, steel = "#8a5a34", "#4c4c50"
    d.polygon(poly([(1398, 772), (1606, 792), (1606, 822), (1398, 802)]), fill=wood)         # backrest
    d.polygon(poly([(1390, 818), (1612, 840), (1618, 852), (1384, 830)]), fill=wood)         # seat
    for x, y in [(1396, 830), (1600, 851)]:
        d.polygon(rect(x - 6, y, x + 6, y + 56), fill=steel)                                 # legs
    # Low green wire fence along the strip, and drying racks with laundry behind it
    green, pole = "#3e7a3a", "#5a5e62"
    d.polygon(poly([(1630, 806), (1780, 822), (1780, 966), (1630, 941)]), fill=green)
    for x in (1640, 1762):
        d.polygon(rect(x - 4, 661, x + 4, 868), fill=pole)                                   # rack poles
        d.polygon(rect(x - 34, 660, x + 34, 667), fill=pole)                                 # cross bars
    d.line([m(1640, 668), m(1762, 670)], fill=pole, width=3)
    for (x0, x1, y1, c) in [(1648, 1676, 742, "#f4f4ee"), (1680, 1702, 730, "#3d78c8"), (1706, 1732, 748, "#e8c43a"),
                            (1736, 1756, 728, "#d8483a")]:
        d.polygon(rect(x0, 668, x1, y1), fill=c)


def s18_shapes_kiosk_racks(d: ImageDraw.ImageDraw) -> None:
    """Spec 2: the kiosk as in spec 1; fence + drying racks with laundry shapes (the bench is already painted)."""
    cream, cream_lit, shade, trim, roof = "#e2cfa6", "#ecdcb8", "#9c8c78", "#7a3328", "#4a2a22"
    d.polygon(poly([(316, 576), (398, 582), (398, 858), (316, 880)]), fill=shade)
    d.polygon(poly([(2, 556), (326, 556), (404, 570), (404, 580), (326, 578), (2, 578)]), fill=roof)
    d.polygon(rect(10, 578, 316, 880), fill=cream)
    d.polygon(rect(10, 584, 316, 630), fill=cream_lit)
    d.polygon(rect(10, 630, 316, 637), fill=trim)
    d.polygon(rect(10, 764, 316, 771), fill=trim)
    d.polygon(rect(20, 642, 97, 764), fill="#d8d8d0")
    for x0, y0 in [(24, 648), (60, 650), (24, 706), (60, 704)]:
        d.polygon(rect(x0, y0, x0 + 32, y0 + 52), fill="#f4f2ea")
        for k in range(4):
            d.polygon(rect(x0 + 4, y0 + 8 + 10 * k, x0 + 28, y0 + 12 + 10 * k), fill="#8a8a84")
    d.polygon(rect(105, 642, 221, 752), fill="#3a2c26")
    d.polygon(rect(98, 748, 228, 758), fill="#d9cbb0")
    d.polygon(rect(229, 650, 306, 764), fill="#d8d8d0")
    colours = ["#e8402a", "#f2c12e", "#3aa655", "#2f7fd8", "#e86fb0", "#f08a24", "#8c4fd0", "#26b8c0"]
    for row in range(5):
        for col in range(3):
            x0, y0 = 234 + col * 24, 655 + row * 21
            d.polygon(rect(x0, y0, x0 + 20, y0 + 16), fill=colours[(row * 3 + col) % len(colours)])
    green, pole = "#3e7a3a", "#5a5e62"
    d.polygon(poly([(1630, 806), (1776, 822), (1776, 966), (1630, 941)]), fill=green)
    for x in (1642, 1760):
        d.polygon(rect(x - 4, 661, x + 4, 868), fill=pole)
        d.polygon(rect(x - 34, 660, x + 34, 667), fill=pole)
    for k in range(3):
        d.line([m(1610, 664 + 2 * k), m(1792, 666 + 2 * k)], fill=pole, width=2)
    for (x0, x1, y1, c) in [(1650, 1690, 760, "#f4f4ee"), (1694, 1714, 726, "#3d78c8"), (1718, 1740, 740, "#e8c43a"),
                            (1744, 1756, 722, "#d8483a")]:
        d.polygon(rect(x0, 668, x1, y1), fill=c)


SPECS = {
    "s18_kiosk": {
        "room": "S18",
        "shapes": s18_shapes,
        # composite boxes (game px): kiosk + its shadow; bench + fence + racks + their shadows
        "boxes": [(0, 536, 480, 940), (1366, 640, 1792, 990)],
        "feather": 40,
        "prompt": (
            "Image 1 is one of our finished point-and-click adventure game backgrounds: a street between early-1970s "
            "panel housing blocks in Dubravka, Bratislava, on a summer evening in 1995 at sunset. Flat, untextured "
            "colour shapes have been pasted onto it as placeholders. Repaint ONLY those placeholder shapes as real "
            "painted objects, at exactly the same position, size and outline, in the same painting technique and in "
            "the same warm low evening sunlight as the rest of image 1. Everything that is not a placeholder must stay "
            "exactly as it is: the sky, every building, balcony, staircase, the pine trees, the big tree at the right, "
            "the road, the kerbs, the little red car and the light do not change.\n\n"
            "The placeholders:\n"
            "1. The cream box with the dark brown roof at the far left (from 0 % to 21 % of the width, from 51 % to "
            "81 % of the height): a small prefabricated NEWSPAPER KIOSK of 1995 standing on a small concrete apron at "
            "the corner of the lawn, in front of the pine trunks. Cream wall panels with thin dark maroon trim, a flat "
            "roof with a thin overhanging dark edge, a plain blank fascia board with NO lettering at all. Its front "
            "faces the camera; its right side wall, in shadow, recedes towards the street. Above a plain lower panel "
            "the front has three openings side by side: on the left a glass display pane with newspapers and "
            "magazines hung on clips behind the glass (only illegible grey scribble columns, no readable words, no "
            "digits); in the middle an OPEN sales hatch, an empty dim opening into the kiosk with a narrow light "
            "counter ledge whose top edge is one straight horizontal line at the bottom of the opening (70 % of the "
            "height); nobody is inside, the opening only shows dim shelves with stacked papers at the back; on the "
            "right a glass display pane with rows of colourful little packets of chewing gum and sweets in bright "
            "wrappers with NO brand names and no letters.\n"
            "2. The brown shape on the lawn strip in front of the near block at the right (73 % to 84 % of the width): "
            "a plain park bench of the housing estate with wooden slats on grey steel legs, standing on the grass "
            "parallel to the strip, empty.\n"
            "3. The green shape and the grey poles with coloured rectangles right of the bench (85 % to 93 % of the "
            "width): a low green wire-mesh fence along the lawn strip and, behind it on the lawn, the residents' steel "
            "drying racks (two T-shaped poles with clothes lines) with a few pieces of laundry - a white sheet, a blue "
            "towel, a yellow towel, a red shirt - hanging still in the evening air.\n\n"
            "Each new object casts a soft long evening shadow on the ground like the other objects in image 1. "
            "No people, no animals, no text, no letters, no numbers, no logos and no brand names anywhere; do not add "
            "or remove anything else. No frames, borders or captions. Image 2 is another background from the same "
            "game: keep the same painting technique."),
    },
    "s18_kiosk2": {
        "room": "S18",
        "mode": "guide",            # image 1 = the clean base, image 2 = base + placeholders (positioning aid)
        "shapes": s18_shapes_kiosk_racks,
        "boxes": [(0, 470, 482, 945), (1590, 600, 1795, 995)],
        "feather": 40,
        "prompt": (
            "You receive 2 images. Image 1 is one of our finished point-and-click adventure game backgrounds: a street "
            "between early-1970s panel housing blocks in Dubravka, Bratislava, on a summer evening in 1995 at sunset. "
            "Image 2 is the same painting with flat colour placeholder shapes that ONLY show where two new objects "
            "must stand and how big they are. Edit image 1: add the two new objects exactly where and exactly as "
            "large as the placeholders in image 2, painted in the same loose painterly brushwork, palette and warm "
            "low evening sunlight as the rest of image 1 - not flat, not clean vector graphics: slightly weathered "
            "surfaces with soft brush texture, warm sunset light and dappled pine shadows on the sunlit front, cool "
            "shade on the side, soft long evening shadows on the ground. Keep everything else in image 1 exactly as "
            "it is: the sky, every building, balcony and staircase, the pine trees, the big tree at the right, the "
            "wooden bench on the lawn strip, the road, the kerbs, the little red car and the light.\n\n"
            "1. Far left (0 % to 21 % of the width, from 51 % to 81 % of the height, on the ground at 81 %): a small "
            "prefabricated NEWSPAPER KIOSK of 1995 standing on a small concrete apron at the corner of the lawn, in "
            "front of the pine trunks (the pine crowns stay visible above its roof). Cream-ochre wall panels with "
            "thin rust-brown trim, a little grime and a few rust streaks near the bottom, a flat roof with a dark "
            "overhanging edge, a plain blank fascia board with NO lettering. Its front faces the camera; its right "
            "side wall, in cool shadow, recedes towards the street. Above a plain lower panel the front has three "
            "openings side by side: on the left a glass display pane with newspapers and magazines hung on clips "
            "behind the glass; in the middle an OPEN sales hatch, an empty dim opening into the kiosk with a narrow "
            "light counter ledge whose top edge is one straight horizontal line at the bottom of the opening (70 % "
            "of the height); nobody is inside, the opening shows only dim shelves with stacked papers at the back; "
            "on the right a glass display pane with rows of colourful little packets of chewing gum and sweets.\n"
            "2. Right, between the bench and the big tree (83 % to 93 % of the width): a low green wire-mesh fence "
            "along the lawn strip that ends left of the big tree's trunk (the trunk stays fully visible), and behind "
            "it on the lawn the residents' steel drying racks: two thin grey T-shaped poles with three clothes lines "
            "between them, with real painted laundry hanging still in the evening air - a white bed sheet, a blue "
            "towel, a yellow towel and a small red shirt, with soft folds, the warm evening light on them.\n\n"
            "NO letters, words, digits, logos or brand names anywhere: the newspaper pages show only grey lines and "
            "small grey photo squares, the sweets packets only plain colour fields. No people, no animals; do not add "
            "or remove anything else. Image 2 is a positioning aid only: do not copy its flat shapes. The result is "
            "image 1 edited, same 16:9 framing, no frames, borders or captions."),
    },
}


# --------------------------------------------------------------------------- commands

def base_image(room: str, version: int) -> Image.Image:
    img, _ = refit_room.load_master(room, version)
    return img


def build_canvas(spec: dict, base: Image.Image) -> Image.Image:
    canvas = base.copy()
    spec["shapes"](ImageDraw.Draw(canvas))
    return canvas


def preview(canvas: Image.Image, spec: dict, name: str) -> Path:
    frame = pr.fit_to_frame(canvas).convert("RGB")
    d = ImageDraw.Draw(frame)
    for x0, y0, x1, y1 in spec["boxes"]:
        d.rectangle([x0, y0, x1, y1], outline=(255, 0, 255), width=2)
    out = SCRATCH / f"{spec['room']}_{name}_canvas_preview.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.save(out)
    return out


def mask_for(spec: dict) -> Image.Image:
    mask = Image.new("L", pr.MODEL_FRAME, 0)
    for x0, y0, x1, y1 in spec["boxes"]:
        bx0, by0 = m(x0, y0)
        bx1, by1 = m(x1, y1)
        touch = (x0 <= 0, y0 <= 0, x1 >= pr.FRAME[0], y1 >= pr.FRAME[1])
        mbox = (0 if touch[0] else round(bx0), 0 if touch[1] else round(by0),
                pr.MODEL_FRAME[0] if touch[2] else round(bx1), pr.MODEL_FRAME[1] if touch[3] else round(by1))
        one = refit_room.soft_mask(pr.MODEL_FRAME, mbox, spec.get("feather", 40), tuple(not t for t in touch))
        mask = ImageChops.lighter(mask, one)
    return mask


def composite(base: Image.Image, result: Image.Image, spec: dict) -> tuple[Image.Image, tuple[int, int]]:
    mask = mask_for(spec)
    outside = mask.point(lambda v: 255 if v == 0 else 0)
    dx, dy = refit_room.align_shift(result, base, outside)
    if dx or dy:
        result = ImageChops.offset(result, -dx, -dy)
        print(f"model output drifted by {dx:+d},{dy:+d} master px; compensated")
    return Image.composite(result, base, mask), (dx, dy)


def cmd_canvas(args) -> None:
    spec = SPECS[args.spec]
    canvas = build_canvas(spec, base_image(spec["room"], args.base))
    print(preview(canvas, spec, args.spec).relative_to(ROOT))


def cmd_paint(args) -> None:
    spec = SPECS[args.spec]
    room = spec["room"]
    base = base_image(room, args.base)
    canvas = build_canvas(spec, base)
    preview(canvas, spec, args.spec)
    style = ROOT / args.style
    prompt = spec["prompt"] + "\n\n" + pr.style_sentence()
    seed = args.seed if args.seed is not None else random.randint(1, 2 ** 31 - 1)
    version = pr.next_version(room)
    asset = f"{SCOPE}{room}_v{version}_edit"
    if spec.get("mode") == "guide":
        images = [fal_api.image_data_uri(base, fmt="PNG"), fal_api.image_data_uri(canvas, max_side=2048, fmt="JPEG")]
    else:
        images = [fal_api.image_data_uri(canvas, fmt="PNG"),
                  fal_api.image_data_uri(style, max_side=1376, fmt="JPEG")]
    arguments = {"prompt": prompt, "image_urls": images, "aspect_ratio": pr.ASPECT, "resolution": pr.RESOLUTION,
                 "output_format": "png", "num_images": 1, "seed": seed}
    price = fal_api.IMAGE_PRICES[(pr.MODEL, pr.RESOLUTION)]
    started = datetime.datetime.now().isoformat(timespec="seconds")
    result = fal_api.run(pr.MODEL, arguments, asset, price, budget=(SCOPE, args.budget), timeout_s=900)
    raw_path = pr.MASTERS / f"_{room}_v{version}_edit_raw.png"
    fal_api.download(result["images"][0]["url"], raw_path)
    raw = Image.open(raw_path).convert("RGB")
    if raw.size != pr.MODEL_FRAME:
        raw = raw.resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    final, drift = composite(base, raw, spec)
    save(room, final, {
        "kind": "edit", "from_version": args.base, "spec": args.spec, "boxes_game_px": spec["boxes"],
        "feather_master_px": spec.get("feather", 40), "drift_compensated_master_px": list(drift), "model": pr.MODEL,
        "seed": result.get("seed", seed), "usd": price, "scope": SCOPE, "spend_log_asset": asset, "prompt": prompt,
        "image_urls": ([f"art/masters/bg_natural/{room}_v{args.base}.png",
                        f"the same + placeholder shapes (S18_scripts/edit_on_base.py spec {args.spec}, guide)"]
                       if spec.get("mode") == "guide" else
                       [f"art/masters/bg_natural/{room}_v{args.base}.png + placeholder shapes "
                        f"(art/masters/bg_natural/S18_scripts/edit_on_base.py spec {args.spec})", args.style]),
        "raw_model_output": raw_path.relative_to(ROOT).as_posix(), "started": started,
        "model_description": result.get("description")})


def cmd_composite(args) -> None:
    spec = SPECS[args.spec]
    room = spec["room"]
    base = base_image(room, args.base)
    raw = Image.open(ROOT / args.raw).convert("RGB").resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    final, drift = composite(base, raw, spec)
    save(room, final, {"kind": "edit-recomposite", "from_version": args.base, "spec": args.spec,
                       "boxes_game_px": spec["boxes"], "usd": 0, "raw_model_output": args.raw,
                       "drift_compensated_master_px": list(drift),
                       "started": datetime.datetime.now().isoformat(timespec="seconds")})


def cmd_revert(args) -> None:
    """Free: copy version --base, then put back the pixels of version --from-version inside the given game boxes
    (hard copy; use boxes that cover a whole earlier composite box, or end where a later edit's seam will cover)."""
    room = args.room
    img = base_image(room, args.base)
    src = base_image(room, args.from_version)
    for box in args.box:
        x0, y0, x1, y1 = box
        mx0, my0 = m(x0, y0)
        mx1, my1 = m(x1, y1)
        b = (max(0, round(mx0)), max(0, round(my0)), min(pr.MODEL_FRAME[0], round(mx1)),
             min(pr.MODEL_FRAME[1], round(my1)))
        img.paste(src.crop(b), b[:2])
    save(room, img, {"kind": "revert", "from_version": args.base, "reverted_from": args.from_version,
                     "boxes_game_px": args.box, "usd": 0, "note": args.note,
                     "started": datetime.datetime.now().isoformat(timespec="seconds")})


def save(room: str, img: Image.Image, meta: dict) -> None:
    version = pr.next_version(room)
    out = pr.MASTERS / f"{room}_v{version}.png"
    img.save(out)
    meta = dict(meta, room=room, version=version, output_size=list(img.size))
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{out.relative_to(ROOT)} (scope {SCOPE} spent {fal_api.logged_spend(SCOPE):.2f})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("canvas", "paint", "composite"):
        p = sub.add_parser(name)
        p.add_argument("--spec", default="s18_kiosk", choices=sorted(SPECS))
        p.add_argument("--base", type=int, required=True)
        if name == "paint":
            p.add_argument("--budget", type=float, required=True)
            p.add_argument("--seed", type=int)
            p.add_argument("--style", default="art/backgrounds/sokolikova-yard.png")
        if name == "composite":
            p.add_argument("--raw", required=True)
    p = sub.add_parser("revert")
    p.add_argument("room")
    p.add_argument("--base", type=int, required=True)
    p.add_argument("--from-version", type=int, required=True)
    p.add_argument("--box", type=float, nargs=4, action="append", required=True)
    p.add_argument("--note", default="")
    args = ap.parse_args()
    {"canvas": cmd_canvas, "paint": cmd_paint, "composite": cmd_composite, "revert": cmd_revert}[args.cmd](args)


if __name__ == "__main__":
    main()
