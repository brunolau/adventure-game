"""Winter S41 ambient sprites (free, local):
  cabin_winter.webp  the parked gondola cabin cut at master resolution from art/masters/bg_natural/S41_winter_v6.png
                     (body outline from its orange frame row by row, the painted hanger arm, plus a straight hanger
                     extension and grip so it can ride on the rope; pivot = top of the grip)
  skier_a/b/c.webp   tiny distant skiers (drawn at 8x and downsampled; they are 10-26 px tall in the game)
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[4]   # repo root
OUT = ROOT / "src" / "game" / "assets" / "ambient" / "S41" / "natural"
SCRATCH = ROOT / "art" / "review" / "natural" / "s41_winter"   # git-ignored previews
SCRATCH.mkdir(parents=True, exist_ok=True)


def hsv(rgb):
    f = rgb.astype(np.float32) / 255.0
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    mx, mn = f.max(-1), f.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    nz = d > 1e-6
    rm = nz & (mx == r)
    gm = nz & (mx == g) & ~rm
    bm = nz & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6
    h[gm] = ((b - r)[gm] / d[gm]) + 2
    h[bm] = ((r - g)[bm] / d[bm]) + 4
    return h * 60, np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0), mx


def cabin():
    master = Image.open(ROOT / "art/masters/bg_natural/S41_winter_v6.png").convert("RGB")
    ox, oy = 1930, 440
    crop = master.crop((ox, oy, ox + 130, oy + 140))
    a = np.asarray(crop).copy()
    h, s, v = hsv(a)
    orange = ((h < 32) | (h > 345)) & (s > 0.45) & (v > 0.45)
    mask = np.zeros(a.shape[:2], dtype=bool)
    for y in range(44, 119):
        xs = np.where(orange[y, 15:112])[0] + 15
        if len(xs) >= 2:
            mask[y, xs.min():xs.max() + 1] = True
    # the fence post with its snow cap covers the cabin's lower right: rebuild those rows from the row above
    for y in range(108, 119):
        row = mask[y]
        if row.any():
            a[y, 70:92] = a[106, 70:92]
    # painted hanger arm (dark) between the cabin roof and the station
    dark = (v < 0.32)
    hang = np.zeros_like(mask)
    hang[34:49, 54:82] = dark[34:49, 54:82]
    mask |= hang
    mask[:44, :55] = False          # station structure bits left of the hanger
    # snow on the cabin roof (white) inside the body columns
    white = (v > 0.85) & (s < 0.2)
    cols = np.where(mask.any(0))[0]
    roof = np.zeros_like(mask)
    roof[40:50, cols.min():cols.max() + 1] = white[40:50, cols.min():cols.max() + 1]
    mask |= roof
    img = Image.fromarray(a).convert("RGBA")
    alpha = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
    img.putalpha(alpha)
    # hanger extension and grip up to the rope (pivot = grip top)
    canvas = Image.new("RGBA", (130, 140), (0, 0, 0, 0))
    canvas.alpha_composite(img)
    d = ImageDraw.Draw(canvas)
    d.line([(77, 37), (77, 14)], fill=(52, 57, 66, 255), width=4)
    d.rounded_rectangle([71, 6, 84, 16], radius=2, fill=(60, 66, 76, 255))
    d.line([(73, 8), (82, 8)], fill=(120, 128, 138, 255), width=1)
    bbox = canvas.getbbox()
    sprite = canvas.crop(bbox)
    pivot = [77 - bbox[0], 6 - bbox[1]]
    OUT.mkdir(parents=True, exist_ok=True)
    sprite.save(OUT / "cabin_winter.webp", "WEBP", lossless=True, quality=100, method=6)
    prev = Image.new("RGBA", sprite.size, (120, 170, 230, 255))
    prev.alpha_composite(sprite)
    prev.convert("RGB").resize((sprite.width * 4, sprite.height * 4), Image.NEAREST).save(SCRATCH / "cabin_sprite_preview.png")
    print("cabin_winter.webp", sprite.size, "pivot", pivot)
    return pivot


def skier(name, jacket, pants, helmet):
    S = 8
    W, H = 22, 22
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = lambda pts: [(x * S, y * S) for x, y in pts]
    # skis (dark, slightly tilted downhill to the right)
    d.line(k([(3, 19.5), (19, 20.5)]), fill=(40, 42, 48, 255), width=int(1.1 * S))
    # legs, bent (crouched skier facing right)
    d.polygon(k([(8, 19.5), (10, 13), (13, 13), (12.5, 16), (14.5, 19.8), (12.6, 19.8), (11, 16.5), (10, 19.5)]),
              fill=pants)
    # body leaning forward
    d.polygon(k([(9, 13.5), (10.5, 7.5), (14, 7), (15, 10), (13.5, 13.5)]), fill=jacket)
    # arm and pole
    d.line(k([(13.5, 9), (16.5, 12)]), fill=jacket, width=int(1.4 * S))
    d.line(k([(16.5, 11), (19, 19.5)]), fill=(70, 70, 76, 255), width=int(0.5 * S))
    # head + helmet
    d.ellipse(k([(11.6, 3.6), (15.2, 7.4)]), fill=(232, 196, 170, 255))
    d.pieslice(k([(11.3, 3.2), (15.5, 7.4)]), 180, 360, fill=helmet)
    sprite = im.resize((W * 2, H * 2), Image.LANCZOS)
    sprite.save(OUT / f"{name}.webp", "WEBP", lossless=True, quality=100, method=6)
    return sprite.size


if __name__ == "__main__":
    pivot = cabin()
    sizes = {n: skier(n, j, p, hc) for n, j, p, hc in (
        ("skier_a", (214, 58, 52, 255), (40, 46, 60, 255), (240, 240, 244, 255)),
        ("skier_b", (52, 112, 196, 255), (34, 36, 44, 255), (230, 70, 50, 255)),
        ("skier_c", (238, 186, 52, 255), (60, 60, 70, 255), (30, 32, 38, 255)))}
    print(sizes)
    (SCRATCH / "sprites.json").write_text(json.dumps({"cabin_pivot": pivot, "skiers": sizes}), encoding="utf-8")
