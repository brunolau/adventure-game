"""State patches for the natural S05 painting (free, no paid calls; docs/reblock/README.md).

The template patches in src/game/assets/variants/ are cut for bg/S05.webp; the natural painting
bg_natural/S05.webp needs its own (same actions, new positions):
  variants_natural/S05_groceries_on_tray.webp  after G04: the grocery bag (items/GROCERIES.webp) on the table top
  variants_natural/S05_shed_unlocked.webp      after G06: padlock and hasp covered by door planks cloned from
                                               the rows just above and below on the same door
Positions are written to src/game/data/blocking/S05.json state_patches by hand (printed here).

Usage: PYTHONIOENCODING=utf-8 python -X utf8 art/tools/natural_patches.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "src" / "game" / "assets"
OUT = ASSETS / "variants_natural"


def groceries() -> None:
    bag = Image.open(ASSETS / "items" / "GROCERIES.webp").convert("RGBA")
    bag = bag.crop(bag.getbbox())
    h = 72
    bag = bag.resize((round(bag.width * h / bag.height), h), Image.Resampling.LANCZOS)
    pad = 10
    canvas = Image.new("RGBA", (bag.width + 2 * pad, bag.height + pad), (0, 0, 0, 0))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([pad - 4, bag.height - 6, pad + bag.width + 10, bag.height + 4], fill=(40, 25, 15, 110))
    canvas = Image.alpha_composite(canvas, shadow.filter(ImageFilter.GaussianBlur(3)))
    canvas.alpha_composite(bag, (pad, 0))
    OUT.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT / "S05_groceries_on_tray.webp", "WEBP", quality=92)
    # bag bottom on the table top (y ~600), centred at x ~240, left of the sanitiser bottle (x 290-306)
    pos = (240 - canvas.width // 2, 600 - bag.height)
    print(f"S05_groceries_on_tray.webp {canvas.size} pos {list(pos)}")


def shed_unlocked() -> None:
    bg = Image.open(ASSETS / "bg_natural" / "S05.webp").convert("RGBA")
    x0, y0, x1, y1 = 832, 522, 890, 596           # lock plate x 838-884 y 528-562, padlock hangs to y ~590
    mid = (y0 + y1) // 2
    upper = bg.crop((x0, y0 - (mid - y0), x1, y0))  # rows right above the plate (below the upper hinge)
    lower = bg.crop((x0, y1, x1, y1 + (y1 - mid)))  # rows right below the padlock (above the lower hinge)
    patch = Image.new("RGBA", (x1 - x0, y1 - y0))
    patch.paste(upper, (0, 0))
    patch.paste(lower, (0, mid - y0))
    # Feather the border so the cloned planks blend into the painting.
    mask = Image.new("L", patch.size, 0)
    ImageDraw.Draw(mask).rectangle([3, 3, patch.width - 4, patch.height - 4], fill=255)
    patch.putalpha(mask.filter(ImageFilter.GaussianBlur(2)))
    patch.save(OUT / "S05_shed_unlocked.webp", "WEBP", quality=95)
    preview = bg.copy()
    preview.alpha_composite(patch, (x0, y0))
    preview.crop((700, 380, 1000, 720)).save(ROOT / "art" / "review" / "natural" / "S05_shed_unlocked_preview.png")
    print(f"S05_shed_unlocked.webp {patch.size} pos {[x0, y0]}")


if __name__ == "__main__":
    groceries()
    shed_unlocked()
