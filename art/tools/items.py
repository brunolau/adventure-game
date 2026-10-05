"""Inventory icons for LastBell (style A) via fal.ai nano-banana-2 edit on a flat key canvas, keyed locally.

All icons of a batch are painted in ONE image (a 4 x 2 grid), so camera angle, light and brushwork match; single
retakes reuse the approved batch as a style reference. Every paid call is logged to art/spend-log.csv.

Subcommands:
  sheet  --ids A,B,...           paid: NB2 2K 16:9 grid of up to 8 icons (order = grid order, row by row)
  single ID --style-ref IMG      paid: NB2 1K 1:1 retake of one icon, matching the style reference
  cut    RAW.png --ids A,B,...    free: key the grid, assign figures to cells, write masters + 256 px icons
  key1   RAW.png ID               free: key a single-icon image and write the master + 256 px icon
  export ID ...                   free: copy 256 px icons to src/game/assets/items/<ID>.webp
  board  OUT.png ID ...           free: review board (256 px on light, dark and slot backgrounds, plus 64 px)
  fix    RAW.png --changes TEXT    paid: NB2 edit of a raw sheet (2K 16:9) or cell (--aspect 1:1, 1K) keeping the rest
  cropcell RAW.png CELL OUT.png   free: one grid cell on a square green canvas (input for fix --aspect 1:1)
  stylegrid OUT.png [ID ...]      free: approved icons on green in a 4 x 2 grid (style reference for `sheet --style-ref`)
  contact OUT.png                 free: contact sheet of every game.json item icon (256 px + 64 px strip)

Masters: art/items/<ID>.png (512 px, transparent) and art/items/raw/*.png (generator output + sidecar JSON).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import chars
import fal_api
import frames
import item_briefs

ART = fal_api.ART
REPO = ART.parent
ITEMS = ART / "items"
RAW = ITEMS / "raw"
GAME_ITEMS = REPO / "src" / "game" / "assets" / "items"
ADAM_SHEET = ART / "characters" / "ADAM" / "sheet_side_right.png"

ICON_BRIEFS = {
    "PHONE": ("Adam's smartphone from 2020: a plain dark graphite modern smartphone with rounded corners, seen at a "
              "slight angle, in a thin dark bumper case; its screen is lit with a simple deep-blue wallpaper and a "
              "small white battery symbol that is full. No brand, no logo, no readable text."),
    "TOOLS": ("Adam's service bag: exactly the brown leather messenger bag from the second reference image, flap "
              "open, with his tools sticking out of it: a screwdriver with a red-and-yellow handle, a small pair of "
              "pliers with red grips and a compact yellow tape measure."),
    "ORDER": ("Mira's shopping list: a small, slightly crumpled sheet of cream lined notepad paper with one corner "
              "folded over; on it exactly three short lines handwritten in blue ink in neat old-fashioned "
              "handwriting, the Slovak words 'čaj', 'zemiaky' and 'ovsené vločky', one per line. Nothing else is "
              "written on it: no title, no other words, no tick marks."),
    "GROCERIES": ("Mira's closed shopping bag: a sturdy natural-beige canvas tote bag with two cloth handles, its top "
                  "folded shut and tied with a string so the contents are hidden, gently bulging with the round "
                  "shapes of potatoes; a small blank paper tag hangs from one handle."),
    "SHEDKEY": ("The key to the garden workshop: an old-fashioned warded brass key with a round bow and a simple bit, "
                "worn shiny brass, on a short loop of brown string with a small blank cardboard tag."),
    "CHRONO": ("The portable ZVON chronometer: a palm-sized round brass instrument like a thick pocket watch, its "
               "hinged lid open; a small engraved bell emblem (the logo of a school technology club) on the lid, a "
               "mechanical year-counter window showing the four digits 2020, a row of four small round indicator "
               "lamps (amber, red, blue and white) glowing softly, a little winding crown on top and a finely "
               "engraved rim. Sturdy, hand-made 1960s engineering, no other text."),
    "FUSE_OLD": ("A blown glass cartridge fuse, shown large and diagonally: a small glass tube with two silver metal "
                 "end caps; the thin wire inside is broken in the middle and the inside of the glass is smoky grey "
                 "and blackened from the burn-out; one end cap is stamped '2A'."),
    "FUSE": ("A new glass cartridge fuse of exactly the same type and size as the blown one, shown large and "
             "diagonally: a clean glass tube with two shiny silver end caps and an intact thin straight wire through "
             "the middle; one end cap is stamped '2A'."),
}

ICON_BRIEFS.update(item_briefs.BRIEFS)  # the 70 icons after the prologue (milestone 2 batch)
PROLOGUE_IDS = ["PHONE", "TOOLS", "ORDER", "GROCERIES", "SHEDKEY", "CHRONO", "FUSE_OLD", "FUSE"]

ICON_RULES = (
    "Consistent rendering for every icon: the same slightly elevated three-quarter camera angle looking a little "
    "down onto the object, the same soft warm key light from the upper left with gentle shading toward the lower "
    "right, a subtle darker painted edge around each silhouette so it stays readable at 64 pixels, saturated but "
    "harmonious colours, rich painterly brushwork. Glass is painted as slightly milky with bright white highlights, "
    "so the background never shows through it. No green parts on any object. No text labels, no logos, no brand "
    "names, no cast shadows on the background, no frames, no slots, no grid lines."
)


def task_guard(args: argparse.Namespace, asset: str, usd: float) -> None:
    prefixes = tuple(p for p in args.budget_scope.split(",") if p)
    with fal_api.SPEND_LOG.open(encoding="utf-8") as handle:
        spent = sum(float(r["usd"]) for r in csv.DictReader(handle)
                    if r["asset"].startswith(prefixes) and (not args.budget_since or r["timestamp"] >= args.budget_since))
    if spent + usd > args.budget + 1e-9:
        sys.exit(f"BUDGET: {asset}: {spent:.3f} + {usd:.3f} USD would exceed the {args.budget:.2f} USD task cap")
    print(f"[budget] {spent:.3f} spent of {args.budget:.2f}; this call {usd:.3f}", file=sys.stderr)


def key_canvas(size: tuple[int, int]) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"key_canvas_{size[0]}x{size[1]}.png"
    if not path.exists():
        Image.new("RGB", size, (0, 255, 0)).save(path)
    return path


def bag_reference() -> Path:
    """Crop of the approved ADAM sheet around his messenger bag (TOOLS is this bag)."""
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / "ref_adam_bag.png"
    if not path.exists():
        Image.open(ADAM_SHEET).convert("RGB").crop((560, 980, 1010, 1420)).save(path)
    return path


def run_edit(args: argparse.Namespace, prompt: str, refs: list[Path], aspect: str, res: str, asset: str,
             out_base: Path) -> list[Path]:
    model = "fal-ai/nano-banana-2/edit"
    price = fal_api.IMAGE_PRICES[(model, res)]
    task_guard(args, asset, price)
    arguments = {"prompt": prompt, "image_urls": [fal_api.image_data_uri(r, max_side=2048) for r in refs],
                 "aspect_ratio": aspect, "resolution": res, "output_format": "png", "num_images": 1,
                 "seed": args.seed}
    result = fal_api.run(model, arguments, asset, price, budget=None, timeout_s=600)
    meta = {"model": model, "usd": price, "prompt": prompt, "aspect_ratio": aspect, "resolution": res,
            "references": [str(r.relative_to(ART)) for r in refs], "seed": args.seed}
    return chars.save_outputs(result, out_base, meta)


def cmd_sheet(args: argparse.Namespace) -> None:
    ids = args.ids.split(",")
    rows = [ids[:4], ids[4:8]]
    listing = []
    for r, row in enumerate(rows):
        if not row:
            continue
        where = "Top row" if r == 0 else "Bottom row"
        listing.append(where + ", left to right: " + " ".join(f"({i + 1 + 4 * r}) {ICON_BRIEFS[i_id]}"
                                                               for i, i_id in enumerate(row)))
    if len(ids) < 8:
        listing.append(f"Only these {len(ids)} icons: the remaining cells of the bottom row stay empty green.")
    if args.style_ref:
        ref_note = (" The SECOND reference image shows eight finished inventory icons of the same game on the same "
                    "green: match their camera angle, light direction, darker painted outline, brushwork, level of "
                    "detail, colour palette and visual size exactly, but do not copy any of their objects; paint "
                    "only the objects described here. ")
        refs = [key_canvas((1600, 900)), Path(args.style_ref).resolve()]
    else:
        ref_note = (" The SECOND reference image shows our hero's bag as painted in our game; use it for the "
                    "painting technique of all icons and paint the service bag (icon 2) as exactly this bag. ")
        refs = [key_canvas((1600, 900)), bag_reference()]
    prompt = (
        "Edit the first image, a flat chroma-key green canvas: paint separate inventory icons for a classic 1990s "
        "point-and-click adventure game on it, arranged in a neat grid of 4 columns and 2 rows, evenly spaced, each "
        "object centred in its own cell with generous green margin around it, no object touching or overlapping "
        "another, all at a similar visual size (each object fills about 70% of its cell). " + " ".join(listing) +
        ref_note + ICON_RULES + " " +
        chars.key_background("green").replace("The character must", "Every object must").replace(
            "on the character", "on the objects") + " " + chars.STYLE_A)
    name = args.out or "items_sheet"
    paths = run_edit(args, prompt, refs, "16:9", "2K", f"items/{name}", RAW / name)
    print("\n".join(str(p) for p in paths))


def cmd_single(args: argparse.Namespace) -> None:
    prompt = (
        "Edit the first image, a flat chroma-key green canvas: paint ONE inventory icon for a classic 1990s "
        "point-and-click adventure game, centred, filling about 70% of the image, with green margin on every side: "
        + ICON_BRIEFS[args.id] + " The SECOND reference image shows other finished icons of the same game; match "
        "their camera angle, light direction, outline, brushwork and colour palette exactly, but do not copy any "
        "of their objects. " + ICON_RULES + " " + chars.key_background("green").replace(
            "The character must", "The object must").replace("on the character", "on the object") + " " + chars.STYLE_A)
    name = args.out or f"{args.id}_single"
    paths = run_edit(args, prompt, [key_canvas((1024, 1024)), Path(args.style_ref).resolve()], "1:1", "1K",
                     f"items/{args.id}/{name}", RAW / name)
    print("\n".join(str(p) for p in paths))


def fit_icon(rgba: np.ndarray, size: int, pad_frac: float = 0.06) -> Image.Image:
    fig = Image.fromarray(frames.crop_to_figure(rgba, pad=0), "RGBA")
    inner = size * (1 - 2 * pad_frac)
    scale = inner / max(fig.width, fig.height)
    fig = fig.resize((max(1, round(fig.width * scale)), max(1, round(fig.height * scale))), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(fig, ((size - fig.width) // 2, (size - fig.height) // 2))
    return canvas


def write_icon(rgba: np.ndarray, item_id: str, source: str) -> None:
    ITEMS.mkdir(parents=True, exist_ok=True)
    fit_icon(rgba, 512).save(ITEMS / f"{item_id}.png", optimize=True)
    fit_icon(rgba, 256).save(ITEMS / f"{item_id}_256.png", optimize=True)
    (ITEMS / f"{item_id}.json").write_text(json.dumps({"id": item_id, "source": source, "brief": ICON_BRIEFS[item_id],
                                                       "key": frames.key_quality(rgba)}, indent=2),
                                           encoding="utf-8", newline="\n")


def cmd_cut(args: argparse.Namespace) -> None:
    ids = args.ids.split(",")
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
        cx, cy = xs.mean(), ys.mean()
        cell = int(cy // (h / rows)) * cols + int(cx // (w / cols))
        cells.setdefault(cell, np.zeros((h, w), bool))
        cells[cell] |= labels == index
    for cell, item_id in enumerate(ids):
        if item_id == "_":  # cell taken from another source
            continue
        if cell not in cells:
            print(item_id, "MISSING")
            continue
        part = rgba.copy()
        part[..., 3] = np.where(cells[cell], part[..., 3], 0)
        write_icon(part, item_id, Path(args.raw).name + f" cell {cell}")
        print(item_id, frames.key_quality(frames.crop_to_figure(part)))


def cmd_key1(args: argparse.Namespace) -> None:
    rgba = frames.chroma_key(frames.load_rgb(Path(args.raw)), min_island=60)
    write_icon(rgba, args.id, Path(args.raw).name)
    print(args.id, frames.key_quality(frames.crop_to_figure(rgba)))


def cmd_export(args: argparse.Namespace) -> None:
    GAME_ITEMS.mkdir(parents=True, exist_ok=True)
    for item_id in args.ids:
        img = Image.open(ITEMS / f"{item_id}_256.png").convert("RGBA")
        assert img.size == (256, 256)
        img.save(GAME_ITEMS / f"{item_id}.webp", "WEBP", quality=95, alpha_quality=100, method=6)
        print(GAME_ITEMS / f"{item_id}.webp")


def cmd_board(args: argparse.Namespace) -> None:
    icons = [Image.open(ITEMS / f"{i}_256.png").convert("RGBA") for i in args.ids]
    backs = [(236, 228, 210), (40, 36, 44), (92, 70, 50)]
    board = Image.new("RGB", (len(icons) * 266 + 10, 3 * 266 + 90), (120, 120, 120))
    for r, colour in enumerate(backs):
        for c, icon in enumerate(icons):
            tile = Image.new("RGBA", (256, 256), colour + (255,))
            if r == 2:  # an inventory-slot look: rounded darker frame
                ImageDraw.Draw(tile).rounded_rectangle((4, 4, 251, 251), radius=18, outline=(160, 130, 90, 255),
                                                       width=6)
            tile.alpha_composite(icon)
            board.paste(tile.convert("RGB"), (10 + c * 266, 10 + r * 266))
    for c, icon in enumerate(icons):
        small = icon.resize((64, 64), Image.Resampling.LANCZOS)
        tile = Image.new("RGBA", (64, 64), backs[2] + (255,))
        tile.alpha_composite(small)
        board.paste(tile.convert("RGB"), (10 + c * 266 + 96, 10 + 3 * 266 + 6))
    board.save(args.out)
    print(args.out, board.size)


def cmd_fix(args: argparse.Namespace) -> None:
    """Paid: edit an existing raw sheet (or cell) in place - fix text, details or chain consistency, keep the rest."""
    grid = ("a sheet of finished inventory icons for our game on a flat chroma-key green background, in a grid of "
            "4 columns and 2 rows (icons 1-4 in the top row and 5-8 in the bottom row, left to right)"
            if args.aspect == "16:9" else "one finished inventory icon for our game on a flat chroma-key green "
            "background")
    ref_note = ""
    if args.ref:
        ref_note = (" The SECOND reference image shows another finished icon of the same game; use it only for "
                    "the object it shows, as described in the changes. ")
    prompt = (f"Edit this image: it is {grid}. Keep every icon, its position, size, angle, painting style, darker "
              "painted outline, lighting and colours and the flat green background exactly as they are, except for "
              "these changes: " + args.changes + ref_note + " Any lettering that remains must be either exactly the "
              "words given here or tiny and illegible; do not add any other words, no English words. " +
              chars.STYLE_A)
    refs = [Path(args.raw).resolve()] + ([Path(args.ref).resolve()] if args.ref else [])
    res = "2K" if args.aspect == "16:9" else "1K"
    paths = run_edit(args, prompt, refs, args.aspect, res, f"items/{args.out}", RAW / args.out)
    print("\n".join(str(p) for p in paths))


def cmd_cropcell(args: argparse.Namespace) -> None:
    """Free: crop one cell (0-7) of a 4 x 2 raw sheet onto a square flat-green canvas (input for `fix --aspect 1:1`)."""
    img = Image.open(args.raw).convert("RGB")
    w, h = img.size
    c, r = args.cell % 4, args.cell // 4
    cell = img.crop((c * w // 4, r * h // 2, (c + 1) * w // 4, (r + 1) * h // 2))
    side = max(cell.size) + 80
    canvas = Image.new("RGB", (side, side), (0, 255, 0))
    canvas.paste(cell, ((side - cell.width) // 2, (side - cell.height) // 2))
    canvas.resize((1024, 1024), Image.Resampling.LANCZOS).save(args.out)
    print(args.out)


def cmd_stylegrid(args: argparse.Namespace) -> None:
    """Free: the approved icons on the key green in a 4 x 2 grid (style reference for later sheets)."""
    ids = args.ids or PROLOGUE_IDS
    canvas = Image.new("RGB", (1600, 900), (0, 255, 0))
    cw, ch = 400, 450
    for n, item_id in enumerate(ids[:8]):
        icon = Image.open(ITEMS / f"{item_id}.png").convert("RGBA").resize((300, 300), Image.Resampling.LANCZOS)
        x = (n % 4) * cw + (cw - 300) // 2
        y = (n // 4) * ch + (ch - 300) // 2
        canvas.paste(icon, (x, y), icon)
    canvas.save(args.out)
    print(args.out)


def cmd_contact(args: argparse.Namespace) -> None:
    """Free: every icon of game.json items[] at 256 px on the slot colour with its id, plus a 64 px strip."""
    game = json.loads((REPO / "src" / "game" / "data" / "game.json").read_text(encoding="utf-8"))
    ids = [item["id"] for item in game["items"]]
    cols = 13
    rows = (len(ids) + cols - 1) // cols
    cell_w, cell_h = 270, 292
    per_small = 40
    small_rows = (len(ids) + per_small - 1) // per_small
    sheet = Image.new("RGB", (cols * cell_w + 10, rows * cell_h + 10 + small_rows * 74 + 10), (64, 58, 54))
    draw = ImageDraw.Draw(sheet)
    slot = (92, 70, 50)
    missing = []
    for n, item_id in enumerate(ids):
        x, y = 10 + (n % cols) * cell_w, 10 + (n // cols) * cell_h
        tile = Image.new("RGBA", (256, 256), slot + (255,))
        path = GAME_ITEMS / f"{item_id}.webp"
        if path.exists():
            icon = Image.open(path).convert("RGBA")
            tile.alpha_composite(icon)
            small = icon.resize((64, 64), Image.Resampling.LANCZOS)
        else:
            missing.append(item_id)
            ImageDraw.Draw(tile).line((0, 0, 255, 255), fill=(200, 40, 40, 255), width=6)
            small = None
        sheet.paste(tile.convert("RGB"), (x, y))
        draw.text((x + 4, y + 260), f"{n + 1:02d} {item_id}", fill=(240, 232, 214))
        sx, sy = 10 + (n % per_small) * 87, 10 + rows * cell_h + (n // per_small) * 74
        stile = Image.new("RGBA", (64, 64), slot + (255,))
        if small is not None:
            stile.alpha_composite(small)
        sheet.paste(stile.convert("RGB"), (sx, sy))
    sheet.save(args.out, optimize=True)
    print(args.out, sheet.size, "missing:", missing or "none")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--budget", type=float, default=0.0)
    parser.add_argument("--budget-scope", default="items/")
    parser.add_argument("--budget-since")
    parser.add_argument("--seed", type=int, default=2020)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("sheet")
    p.add_argument("--ids", required=True)
    p.add_argument("--out")
    p.add_argument("--style-ref", help="finished icons on green (stylegrid); default: the ADAM bag crop")
    p.set_defaults(func=cmd_sheet)
    p = sub.add_parser("single")
    p.add_argument("id", choices=ICON_BRIEFS)
    p.add_argument("--style-ref", required=True)
    p.add_argument("--out")
    p.set_defaults(func=cmd_single)
    p = sub.add_parser("cut")
    p.add_argument("raw")
    p.add_argument("--ids", required=True)
    p.set_defaults(func=cmd_cut)
    p = sub.add_parser("key1")
    p.add_argument("raw")
    p.add_argument("id", choices=ICON_BRIEFS)
    p.set_defaults(func=cmd_key1)
    p = sub.add_parser("export")
    p.add_argument("ids", nargs="+")
    p.set_defaults(func=cmd_export)
    p = sub.add_parser("board")
    p.add_argument("out")
    p.add_argument("ids", nargs="+")
    p.set_defaults(func=cmd_board)
    p = sub.add_parser("fix")
    p.add_argument("raw")
    p.add_argument("--changes", required=True)
    p.add_argument("--ref")
    p.add_argument("--aspect", default="16:9", choices=["16:9", "1:1"])
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_fix)
    p = sub.add_parser("cropcell")
    p.add_argument("raw")
    p.add_argument("cell", type=int)
    p.add_argument("out")
    p.set_defaults(func=cmd_cropcell)
    p = sub.add_parser("stylegrid")
    p.add_argument("out")
    p.add_argument("ids", nargs="*")
    p.set_defaults(func=cmd_stylegrid)
    p = sub.add_parser("contact")
    p.add_argument("out")
    p.set_defaults(func=cmd_contact)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
