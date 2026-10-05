"""Behind-the-window variants of NPC spritesheets (free, local): MIRA20 in S06, optionally DANA in S04.

A character seen through a closed window shows only the part above the window sill, and the glass in front of
her adds a pale reflection veil. This tool takes a horizontal spritesheet (+ JSON with cell and feet pivot, as
written by frames.py) and writes, for every cell:
  * a bust crop: everything below the sill line is cut with a hard horizontal edge; the new pivot is the centre
    of that edge, so the engine places the pivot on the painted sill's top edge;
  * optionally a glass treatment: contrast lifted slightly, then a cool pale veil and one soft diagonal
    reflection streak, the same on every cell (the figure does not walk, so the streak stays put).

Usage:
  python glass.py SHEET.png OUT_DIR --name bust_glass --visible 0.45 [--glass] [--veil 0.16] [--streak 0.10]
  python glass.py preview OUT.png BUST_SHEET.png [BUST_SHEET2.png ...]   mock window for a readability check

--visible: fraction of the figure height (feet-to-top, 512 px sheets) that shows above the sill.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

VEIL_RGB = np.array([206, 218, 228], np.float32)  # pale overcast-sky reflection


def load_sheet(path: Path) -> tuple[list[Image.Image], dict]:
    meta = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    sheet = Image.open(path).convert("RGBA")
    cw, ch = meta["cell"]
    count = sheet.width // cw
    return [sheet.crop((i * cw, 0, (i + 1) * cw, ch)) for i in range(count)], meta


def figure_height(meta: dict, cells: list[Image.Image]) -> float:
    if meta.get("height_px"):
        return float(meta["height_px"])
    if meta.get("height_px_median"):
        return float(meta["height_px_median"])
    tops = [c.getchannel("A").getbbox()[1] for c in cells]
    return float(meta["pivot"][1] - np.median(tops))


def treat(cell: np.ndarray, veil: float, streak: float, contrast: float) -> np.ndarray:
    rgb = cell[..., :3].astype(np.float32)
    a = cell[..., 3:4]
    h, w = rgb.shape[:2]
    mean = (rgb * (a / 255)).sum(axis=(0, 1)) / max(1.0, float((a / 255).sum()))
    rgb = (rgb - mean) * contrast + mean  # pre-compensate a little of the contrast the veil takes away
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # one broad soft diagonal streak (upper left to lower right), plus the uniform veil
    d = (xx - w * 0.15) * 0.8 - (yy - h * 0.10) * 0.6
    band = np.exp(-((d - w * 0.18) / (w * 0.16)) ** 2)
    rgb = rgb * (1 - veil) + VEIL_RGB * veil
    rgb = rgb + (255 - rgb) * (streak * band)[..., None]
    return np.dstack([rgb.clip(0, 255), a]).astype(np.uint8)


def make_bust(sheet_path: Path, out_dir: Path, name: str, visible: float, glass: bool, veil: float,
              streak: float, contrast: float) -> dict:
    cells, meta = load_sheet(sheet_path)
    cw, ch = meta["cell"]
    px, py = meta["pivot"]
    fig_h = figure_height(meta, cells)
    sill_y = int(round(py - fig_h * (1 - visible)))
    tops = [c.getchannel("A").getbbox()[1] for c in cells]
    top = max(0, min(tops) - 4)
    out_cells = []
    for cell in cells:
        arr = np.asarray(cell).copy()
        arr[sill_y:, :, 3] = 0
        arr = arr[top:sill_y]
        if glass:
            arr = treat(arr, veil, streak, contrast)
        out_cells.append(Image.fromarray(arr, "RGBA"))
    bw, bh = out_cells[0].size
    out_dir.mkdir(parents=True, exist_ok=True)
    strip = Image.new("RGBA", (bw * len(out_cells), bh), (0, 0, 0, 0))
    for i, c in enumerate(out_cells):
        strip.paste(c, (i * bw, 0))
    strip.save(out_dir / f"{name}_sheet.png", optimize=True)
    new_meta = dict(meta)
    new_meta.update({
        "name": name, "cell": [bw, bh], "pivot": [px, bh], "pivot_is_sill_line": True,
        "visible_fraction_of_figure": visible, "figure_height_px": round(fig_h, 1),
        "source_sheet": sheet_path.name, "glass": glass,
        "glass_params": {"veil": veil, "streak": streak, "contrast": contrast} if glass else None,
        "placement": ("Place the pivot (bottom centre, the cut edge) exactly on the top edge of the painted window "
                      "sill; scale like the full figure (figure_height_px is the full standing height the bust "
                      "belongs to). Draw above the background, below the window frame overlay if there is one."),
    })
    (out_dir / f"{name}_sheet.json").write_text(json.dumps(new_meta, indent=2), encoding="utf-8", newline="\n")
    return new_meta


def mock_window(size: tuple[int, int], sill_y: int) -> tuple[Image.Image, Image.Image]:
    """A mock window (dim warm interior behind glass, white frame, sill) as background and frame overlay."""
    w, h = size
    yy = np.linspace(0, 1, h)[:, None]
    interior = np.dstack([(70 + 40 * yy) * np.ones((1, w)), (52 + 30 * yy) * np.ones((1, w)),
                          (40 + 20 * yy) * np.ones((1, w))])
    bg = Image.fromarray(interior.clip(0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(bg)
    d.rectangle((w * 0.62, h * 0.12, w * 0.8, h * 0.32), fill=(150, 120, 90, 255))  # a picture on the wall
    d.rectangle((w * 0.64, h * 0.14, w * 0.78, h * 0.30), fill=(190, 175, 150, 255))
    # reflections on the glass of the background
    glass = Image.new("RGBA", size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glass)
    gd.polygon([(w * 0.05, 0), (w * 0.25, 0), (w * 0.0, h * 0.55), (w * -0.2, h * 0.55)], fill=(220, 230, 240, 50))
    gd.polygon([(w * 0.7, 0), (w * 0.78, 0), (w * 0.4, h), (w * 0.32, h)], fill=(220, 230, 240, 30))
    glass = glass.filter(ImageFilter.GaussianBlur(8))
    bg.alpha_composite(glass)
    frame = Image.new("RGBA", size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(frame)
    fw = max(6, w // 40)
    fd.rectangle((0, 0, w - 1, fw), fill=(236, 232, 222, 255))
    fd.rectangle((0, 0, fw, h), fill=(236, 232, 222, 255))
    fd.rectangle((w - fw, 0, w, h), fill=(236, 232, 222, 255))
    fd.rectangle((w // 2 - fw // 2, 0, w // 2 + fw // 2, sill_y), fill=(236, 232, 222, 255))  # mullion
    fd.rectangle((0, sill_y, w, h), fill=(178, 160, 140, 255))  # wall below
    fd.rectangle((0, sill_y - fw // 2, w, sill_y + fw), fill=(225, 220, 210, 255))  # sill
    return bg, frame


def cmd_preview(out: Path, sheets: list[Path]) -> None:
    panels = []
    for sheet in sheets:
        cells, meta = load_sheet(sheet)
        cell = cells[0]
        w, h = cell.width * 3, int(cell.height * 1.35)
        sill_y = h - int(cell.height * 0.12)
        bg, frame = mock_window((w, h), sill_y)
        x = w // 4 - cell.width // 2
        bg.alpha_composite(cell, (x, sill_y - cell.height))
        if len(cells) > 2:
            bg.alpha_composite(cells[2], (x + w // 2, sill_y - cell.height))
        bg.alpha_composite(frame)
        panels.append(bg)
    W, H = sum(p.width for p in panels) + 10 * len(panels), max(p.height for p in panels)
    sheet = Image.new("RGB", (W, H), (90, 110, 80))
    x = 0
    for p in panels:
        sheet.paste(p.convert("RGB"), (x, 0))
        x += p.width + 10
    sheet.save(out)
    print(out, sheet.size)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        cmd_preview(Path(sys.argv[2]), [Path(p) for p in sys.argv[3:]])
        return
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sheet")
    parser.add_argument("out_dir")
    parser.add_argument("--name", required=True)
    parser.add_argument("--visible", type=float, default=0.45)
    parser.add_argument("--glass", action="store_true")
    parser.add_argument("--veil", type=float, default=0.16)
    parser.add_argument("--streak", type=float, default=0.10)
    parser.add_argument("--contrast", type=float, default=1.08)
    args = parser.parse_args()
    meta = make_bust(Path(args.sheet), Path(args.out_dir), args.name, args.visible, args.glass, args.veil,
                     args.streak, args.contrast)
    print(json.dumps({k: meta[k] for k in ("name", "cell", "pivot", "figure_height_px")}))


if __name__ == "__main__":
    main()
