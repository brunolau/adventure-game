"""S18 ambient (free): "a neighbour shaking a rug from a balcony" as a small sprite sheet.

The rug is our own painted carpet from the S62 v1 natural master (saved as art/ambient/natural/sources/S62_v1_carpet.webp),
scaled to ~1.1 m at the first-floor loggia of the near block (x ~1355-1435, parapet rail y ~512, ~78 px per metre).
The neighbour is a dim figure in the shaded loggia behind the parapet (head, shoulders, arms holding the rug's top
corners). Frames (cell 150x176, pivot = the rug's top centre on the rail):
  0 empty (shown during the pause between loops)   1 rug draped, neighbour holding it
  2 / 4 rug flicked out (shorter, lower part swung towards the viewer), arms up
  3 / 5 rug snapped back with a wave and a little dust puff
Used by data/blocking/ambient/S18.json layer "rug_shake" (sprite_loop with pause_s).

Run: PYTHONIOENCODING=utf-8 python -X utf8 art/masters/bg_natural/S18_scripts/rug_sheet.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "art" / "ambient" / "natural" / "sources" / "S62_v1_carpet.webp"
OUT = ROOT / "src" / "game" / "assets" / "ambient" / "S18" / "natural"
CELL = (150, 176)
PIVOT = (75, 64)          # rug top centre = the parapet rail point
RUG_W = 82


def rug_base() -> Image.Image:
    im = Image.open(SRC).convert("RGBA")
    im = im.crop(im.split()[-1].getbbox())
    h = round(im.height * RUG_W / im.width)
    im = im.resize((RUG_W, h), Image.Resampling.LANCZOS)
    # in the shaded loggia at sunset: a bit darker and warmer
    rgb = ImageEnhance.Brightness(im.convert("RGB")).enhance(0.86)
    out = rgb.convert("RGBA")
    out.putalpha(im.split()[-1])
    return out


def warp(rug: Image.Image, length: float, wave: float, phase: float, flare: float) -> Image.Image:
    """Vertical scale `length` (0..1), horizontal sine wave of amplitude `wave` px growing towards the bottom,
    bottom edge widened by `flare` (the part swung towards the viewer looks wider)."""
    a = np.asarray(rug).astype(np.float32)
    h, w = a.shape[:2]
    nh = max(8, round(h * length))
    outw = w + 40
    out = np.zeros((nh, outw, 4), np.float32)
    for y in range(nh):
        t = y / max(1, nh - 1)
        sy = min(h - 1, int(t * (h - 1)))
        scale = 1.0 + flare * t * t
        shift = wave * t * math.sin(phase + t * 3.2)
        row = a[sy]
        for x in range(outw):
            cx = (x - outw / 2 - shift) / scale + w / 2
            if 0 <= cx < w - 1:
                i = int(cx)
                f = cx - i
                out[y, x] = row[i] * (1 - f) + row[i + 1] * f
    # the flicked-out part is lit differently: darken the lower part a little
    if length < 0.95:
        shade = np.linspace(1.0, 0.82, nh)[:, None, None]
        out[..., :3] *= shade
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def neighbour(img: Image.Image, arms_up: int) -> None:
    """A dim figure in the shaded loggia: soft painted shapes, a little blur, so it reads as a person in the shade
    rather than as a crisp cut-out."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    px, py = PIVOT
    body, skin, hair = (52, 56, 74, 225), (122, 92, 80, 225), (46, 36, 34, 230)
    d.rounded_rectangle([px - 19, py - 30, px + 19, py + 4], radius=9, fill=body)        # shoulders / housecoat
    d.ellipse([px - 9, py - 52, px + 9, py - 30], fill=skin)                            # head
    d.chord([px - 10, py - 54, px + 10, py - 34], 180, 360, fill=hair)                   # hair
    y_hand = py - 2 - arms_up
    for side in (-1, 1):
        d.line([(px + side * 15, py - 22), (px + side * 34, y_hand)], fill=body, width=6)
        d.ellipse([px + side * 34 - 3, y_hand - 3, px + side * 34 + 3, y_hand + 3], fill=skin)
    # soft light from the left on the face
    d.ellipse([px - 8, py - 47, px - 2, py - 38], fill=(150, 116, 96, 70))      # warm reflected light on the cheek
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.9)))


def dust(img: Image.Image, y: int, strength: float) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rng = np.random.default_rng(int(strength * 100) + y)
    for _ in range(9):
        x = PIVOT[0] + rng.uniform(-48, 48)
        yy = y + rng.uniform(-10, 14)
        r = rng.uniform(5, 11)
        d.ellipse([x - r, yy - r * 0.7, x + r, yy + r * 0.7], fill=(226, 206, 170, int(48 * strength)))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(3)))


def frame(rug: Image.Image, kind: str) -> Image.Image:
    img = Image.new("RGBA", CELL, (0, 0, 0, 0))
    if kind == "empty":
        return img
    params = {"draped": (1.0, 0.0, 0.0, 0.0, 0), "flick_a": (0.56, 4.0, 0.4, 0.28, 8),
              "snap_a": (1.0, 7.0, 1.2, 0.02, 2), "flick_b": (0.64, -5.0, 2.2, 0.22, 7),
              "snap_b": (1.0, -6.0, 3.0, 0.02, 1)}[kind]
    length, wave, phase, flare, arms_up = params
    neighbour(img, arms_up)
    r = warp(rug, length, wave, phase, flare)
    top = PIVOT[1] - 3 - (arms_up // 2)
    img.alpha_composite(r, (PIVOT[0] - r.width // 2, top))
    # the top fold over the rail (darker band) and the hands in front of it
    d = ImageDraw.Draw(img)
    d.rectangle([PIVOT[0] - RUG_W // 2, top, PIVOT[0] + RUG_W // 2, top + 4], fill=(70, 30, 26, 200))
    for side in (-1, 1):
        hx = PIVOT[0] + side * 34
        d.ellipse([hx - 3, top - 2, hx + 3, top + 4], fill=(122, 92, 80, 230))
    if kind.startswith("snap"):
        dust(img, top + r.height, 1.0 if kind == "snap_a" else 0.8)
    if kind.startswith("flick"):
        dust(img, top + r.height + 6, 0.5)
    return img


def main() -> None:
    rug = rug_base()
    kinds = ["empty", "draped", "flick_a", "snap_a", "flick_b", "snap_b"]
    sheet = Image.new("RGBA", (CELL[0] * len(kinds), CELL[1]), (0, 0, 0, 0))
    for i, k in enumerate(kinds):
        sheet.alpha_composite(frame(rug, k), (i * CELL[0], 0))
    OUT.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT / "rug_shake_sheet.webp", "WEBP", quality=95, alpha_quality=100, method=6)
    (OUT / "rug_shake_sheet.json").write_text(json.dumps({
        "name": "rug_shake_sheet", "frames": len(kinds), "cell": list(CELL), "pivot": list(PIVOT),
        "playback_fps": 6, "frame_names": kinds, "oneshot": False,
        "note": "S18 neighbour shaking a rug from the first-floor loggia (art/masters/bg_natural/S18_scripts/rug_sheet.py)"},
        indent=2), encoding="utf-8")
    preview = Image.new("RGBA", sheet.size, (92, 104, 130, 255))
    preview.alpha_composite(sheet)
    preview.convert("RGB").resize((sheet.width * 2, sheet.height * 2), Image.Resampling.NEAREST).save(
        ROOT / "art" / "ambient" / "preview" / "S18_natural_rug_shake_sheet.png")
    print(f"wrote {(OUT / 'rug_shake_sheet.webp').relative_to(ROOT)} {sheet.size}")


if __name__ == "__main__":
    main()
