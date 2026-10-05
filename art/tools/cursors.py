"""Mouse cursors and Space markers for LastBell (style A) via fal.ai nano-banana-2 edit on a flat key canvas.

  python art/tools/cursors.py generate [--take N] [--seed S]   one paid call (USD 0.12, 2K 16:9; scope ui/cursors, cap USD 1.50)
  python art/tools/cursors.py cut art/ui/cursors/raw/sheet_vN.png   free: key the 4 x 2 grid, write the masters
  python art/tools/cursors.py export                            free: game files (64/96/128 px + hotspots.json)

The sheet has eight painted figures (left to right, top row first):
  pointer (default / walk), hand (use / take), talk (speech bubble), look (magnifying glass, look-only targets),
  exit (arrow pointing right; left / up / down are mirrored / rotated locally), busy (hourglass, cutscenes and lines),
  marker (round badge for the Space markers), marker_exit (the same badge with an arrow).

Masters: art/ui/cursors/<name>.png (keyed, cropped, square, 512 px). Game files: src/game/assets/ui/cursors/
<name>_<size>.png for 64, 96 and 128 px and hotspots.json ({name: [x, y]} as fractions of the square), read by
scripts/UI/Hud/CursorSet.cs. The hotspot of a pointer-like cursor is its tip pixel; symbol cursors use the centre.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chars  # noqa: E402
import fal_api  # noqa: E402
import frames  # noqa: E402

ART = fal_api.ART
REPO = ART.parent
OUT = ART / "ui" / "cursors"
RAW = OUT / "raw"
GAME = REPO / "src" / "game" / "assets" / "ui" / "cursors"
STYLE_REF = ART / "items" / "raw" / "style_ref_m2.png"
MODEL = "fal-ai/nano-banana-2/edit"
BUDGET = ("ui/cursors", 1.50)
SIZES = (64, 96, 128)
MASTER = 512

NAMES = ["pointer", "hand", "talk", "look", "exit", "busy", "marker", "marker_exit"]

FIGURES = [
    "(1) a classic slanted mouse-pointer arrow, its sharp tip pointing exactly to the upper-left corner of its cell, "
    "body of warm ivory cream with a thick dark brown ink outline and a thin polished brass rim just inside the "
    "outline, a short tail at the lower right",
    "(2) a friendly cartoon hand in a cream cotton glove seen from the back, the index finger stretched out and "
    "pointing diagonally to the upper-left corner of its cell, the other fingers curled, a brass cuff ring at the wrist, "
    "thick dark brown ink outline",
    "(3) a round speech bubble of cream paper with a thick dark brown ink outline and a small pointed tail at its "
    "lower left, three round brass dots in a row inside",
    "(4) a magnifying glass with a round polished brass rim, a milky pale-blue lens with a bright white highlight, "
    "and a short dark wooden handle pointing to the lower right, thick dark brown ink outline",
    "(5) a bold, thick, chunky arrow pointing straight to the right (horizontal), painted polished brass gold with a "
    "thick dark brown ink outline and a lighter highlight along its upper edge",
    "(6) a small upright hourglass with a dark wooden top and bottom and two turned wooden posts, pale glass bulbs "
    "with warm golden sand running from the upper bulb into the lower one, thick dark brown ink outline",
    "(7) a small round badge like an enamel button: a polished brass ring rim around a deep teal enamel disc with a "
    "small cream dot in the middle, thick dark brown ink outline, seen straight from the front",
    "(8) exactly the same round badge as figure 7 (same brass rim, same teal enamel), but with a short cream arrow "
    "pointing to the right inside it instead of the dot, seen straight from the front",
]

PROMPT = (
    "Edit the first image, a flat chroma-key green canvas: paint a sheet of eight separate mouse-cursor icons for a "
    "classic 1990s hand-painted point-and-click adventure game, in a grid of 4 columns and 2 rows, each figure centred "
    "in its own cell, filling about 55 % of the cell, with generous green margin around it; no figure touches or "
    "overlaps another. Top row, left to right: " + "; ".join(FIGURES[:4]) + ". Bottom row, left to right: "
    + "; ".join(FIGURES[4:]) + ". "
    "The second image shows finished inventory icons from our game on the same green: match their rendering exactly "
    "(rich painterly brushwork, warm key light from the upper left, a darker painted edge around every silhouette, "
    "saturated but harmonious colours), but make these cursor shapes bold, simple and flat-on so they stay readable "
    "at 48 pixels. Every figure is a solid, fully opaque shape with crisp edges. No green parts on any figure. "
    "No text, no letters, no numbers, no logos, no cast shadows on the background, no frames, no grid lines. "
    + chars.key_background("green").replace("The character must", "Every figure must").replace(
        "on the character", "on any figure")
)


def key_canvas(size: tuple[int, int]) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"key_canvas_{size[0]}x{size[1]}.png"
    if not path.exists():
        Image.new("RGB", size, (0, 255, 0)).save(path)
    return path


def cmd_generate(args: argparse.Namespace) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    take = args.take or 1 + len(list(RAW.glob("sheet_v*.json")))
    res = "2K"
    price = fal_api.IMAGE_PRICES[(MODEL, res)]
    refs = [key_canvas((1600, 900)), STYLE_REF]
    arguments = {"prompt": PROMPT, "image_urls": [fal_api.image_data_uri(r, max_side=2048) for r in refs],
                 "aspect_ratio": "16:9", "resolution": res, "output_format": "png", "num_images": 1}
    if args.seed is not None:
        arguments["seed"] = args.seed
    result = fal_api.run(MODEL, arguments, f"ui/cursors/sheet_v{take}", price, budget=BUDGET, timeout_s=600)
    meta = {"model": MODEL, "usd": price, "prompt": PROMPT, "aspect_ratio": "16:9", "resolution": res,
            "references": [str(r.relative_to(ART)) for r in refs], "seed": args.seed}
    for path in chars.save_outputs(result, RAW / f"sheet_v{take}", meta):
        print(path)


def square_master(rgba: np.ndarray) -> Image.Image:
    crop = frames.crop_to_figure(rgba, pad=2)
    img = Image.fromarray(crop, "RGBA")
    side = max(img.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    return canvas.resize((MASTER, MASTER), Image.Resampling.LANCZOS)


def cmd_cut(args: argparse.Namespace) -> None:
    rgb = frames.load_rgb(Path(args.raw))
    rgba = frames.chroma_key(rgb, min_island=60)
    h, w = rgba.shape[:2]
    labels, sizes = frames.label_components(rgba[..., 3] > 24)
    cols, rows = 4, 2
    cells: dict[int, np.ndarray] = {}
    for index, size in enumerate(sizes, start=1):
        if size < 60:
            continue
        ys, xs = np.nonzero(labels == index)
        cell = int(ys.mean() // (h / rows)) * cols + int(xs.mean() // (w / cols))
        cells.setdefault(cell, np.zeros((h, w), bool))
        cells[cell] |= labels == index
    OUT.mkdir(parents=True, exist_ok=True)
    for cell, name in enumerate(NAMES):
        if cell not in cells:
            print(name, "MISSING")
            continue
        part = rgba.copy()
        part[..., 3] = np.where(cells[cell], part[..., 3], 0)
        square_master(part).save(OUT / f"{name}.png")
        print(name, frames.key_quality(frames.crop_to_figure(part)))
    (OUT / "source.json").write_text(json.dumps({"sheet": str(Path(args.raw).resolve().relative_to(ART)),
                                                 "cells": NAMES}, indent=2), encoding="utf-8")


def tip(img: Image.Image, direction: tuple[float, float]) -> tuple[float, float]:
    """The opaque pixel furthest along a direction (e.g. (-1, -1) = upper-left tip), as fractions of the square."""
    a = np.asarray(img)[..., 3] > 128
    ys, xs = np.nonzero(a)
    score = xs * direction[0] + ys * direction[1]
    i = int(np.argmax(score))
    return (float(xs[i]) / img.width, float(ys[i]) / img.height)


def lens_centre(img: Image.Image) -> tuple[float, float]:
    """Centre of the magnifier's lens: the centroid of the pale, bluish pixels."""
    rgba = np.asarray(img).astype(np.int32)
    pale = (rgba[..., 3] > 200) & (rgba[..., 2] > 170) & (rgba[..., 2] >= rgba[..., 0])
    ys, xs = np.nonzero(pale)
    if len(xs) == 0:
        return (0.5, 0.5)
    return (float(xs.mean()) / img.width, float(ys.mean()) / img.height)


def fit(img: Image.Image, fill: float) -> Image.Image:
    """Scales the figure inside the square so its larger side is `fill` of the square (centred)."""
    box = img.getbbox()
    if box is None:
        return img
    fig = img.crop(box)
    scale = fill * img.width / max(fig.size)
    fig = fig.resize((max(1, round(fig.width * scale)), max(1, round(fig.height * scale))), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(fig, ((img.width - fig.width) // 2, (img.height - fig.height) // 2))
    return out


def cmd_export(args: argparse.Namespace) -> None:
    masters = {name: Image.open(OUT / f"{name}.png").convert("RGBA") for name in NAMES}
    shapes: dict[str, Image.Image] = {}
    hotspots: dict[str, list[float]] = {}
    # Pointer-like cursors: the tip is the hotspot, the figure sits in the upper-left part of the square so the
    # hover label beside it has room. Symbol cursors: centred, hotspot in the centre.
    shapes["pointer"] = fit(masters["pointer"], 0.80)
    shapes["hand"] = fit(masters["hand"], 0.86)
    shapes["talk"] = fit(masters["talk"], 0.80)
    shapes["look"] = fit(masters["look"], 0.80)
    shapes["busy"] = fit(masters["busy"], 0.72)
    exit_right = fit(masters["exit"], 0.82)
    shapes["exit_right"] = exit_right
    shapes["exit_left"] = exit_right.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    shapes["exit_up"] = exit_right.rotate(90, resample=Image.Resampling.BICUBIC)
    shapes["exit_down"] = exit_right.rotate(-90, resample=Image.Resampling.BICUBIC)
    shapes["marker"] = fit(masters["marker"], 0.92)
    shapes["marker_exit"] = fit(masters["marker_exit"], 0.92)
    for name, img in shapes.items():
        if name in ("pointer", "hand"):
            hotspots[name] = list(tip(img, (-1, -1)))
        elif name.startswith("exit_"):
            d = {"exit_right": (1, 0), "exit_left": (-1, 0), "exit_up": (0, -1), "exit_down": (0, 1)}[name]
            hotspots[name] = list(tip(img, d))
        elif name == "look":
            hotspots[name] = list(lens_centre(img))
        else:
            hotspots[name] = [0.5, 0.5]
    GAME.mkdir(parents=True, exist_ok=True)
    for name, img in shapes.items():
        sizes = SIZES if not name.startswith("marker") else (48, 64, 96)
        for size in sizes:
            img.resize((size, size), Image.Resampling.LANCZOS).save(GAME / f"{name}_{size}.png", optimize=True)
    (GAME / "hotspots.json").write_text(json.dumps(
        {"sizes": list(SIZES), "marker_sizes": [48, 64, 96],
         "hotspots": {k: [round(v[0], 4), round(v[1], 4)] for k, v in hotspots.items()}}, indent=2), encoding="utf-8")
    # Contact sheet for review (dark and light backgrounds).
    cell = 140
    sheet = Image.new("RGBA", (cell * len(shapes), cell * 2), (0, 0, 0, 255))
    for i, (name, img) in enumerate(shapes.items()):
        for row, bg in enumerate([(40, 34, 28, 255), (236, 226, 204, 255)]):
            tile = Image.new("RGBA", (cell, cell), bg)
            small = img.resize((128, 128), Image.Resampling.LANCZOS)
            tile.alpha_composite(small, (6, 6))
            hx, hy = hotspots[name]
            for dx in range(-3, 4):
                tile.putpixel((min(cell - 1, 6 + int(hx * 128) + dx), min(cell - 1, 6 + int(hy * 128))), (255, 0, 0, 255))
                tile.putpixel((min(cell - 1, 6 + int(hx * 128)), min(cell - 1, 6 + int(hy * 128) + dx)), (255, 0, 0, 255))
            sheet.paste(tile, (i * cell, row * cell))
    sheet.convert("RGB").save(OUT / "contact.png")
    print("exported", len(shapes), "cursors to", GAME, "contact", OUT / "contact.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--take", type=int)
    g.add_argument("--seed", type=int)
    g.set_defaults(func=cmd_generate)
    c = sub.add_parser("cut")
    c.add_argument("raw")
    c.set_defaults(func=cmd_cut)
    e = sub.add_parser("export")
    e.set_defaults(func=cmd_export)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
