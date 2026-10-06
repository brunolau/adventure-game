"""S01: recolour the painted service bag on the chair from olive canvas to the brown leather of the TOOLS icon and of
the bag Adam carries (ISSUES M5-04). Local, free: a hand-drawn polygon around the bag, limited to its khaki hues (the
red / silver tools in it and the green chair seat stay), hue moved to the icon's leather brown, a little more
saturation. Writes src/game/assets/bg_natural/S01.webp; the previous file is kept in art/masters/bg_natural/.

Run from the repository root: python art/tools/s01_bag_recolor.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src" / "game" / "assets" / "bg_natural" / "S01.webp"
BACKUP = REPO / "art" / "masters" / "bg_natural" / "S01_before_bag_recolor.webp"
ORIGIN = (592, 668)  # crop origin of the polygon below (canvas px)
BAG = [(75, 72), (115, 60), (150, 66), (182, 76), (197, 88), (207, 100), (220, 130), (224, 170), (217, 184), (214, 200),
       (218, 230), (200, 240), (183, 234), (178, 206), (150, 194), (100, 190), (68, 182), (62, 150), (68, 110)]


def rgb_to_hsv(a: np.ndarray) -> np.ndarray:
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    rc = np.where(m, (mx - r) / np.where(m, d, 1), 0)
    gc = np.where(m, (mx - g) / np.where(m, d, 1), 0)
    bc = np.where(m, (mx - b) / np.where(m, d, 1), 0)
    h = np.where(r == mx, bc - gc, np.where(g == mx, 2.0 + rc - bc, 4.0 + gc - rc))
    h = np.where(m, (h / 6.0) % 1.0, 0)
    s = np.where(mx > 1e-6, d / np.where(mx > 1e-6, mx, 1), 0)
    return np.stack([h, s, mx], -1)


def hsv_to_rgb(a: np.ndarray) -> np.ndarray:
    h, s, v = a[..., 0], a[..., 1], a[..., 2]
    i = np.floor(h * 6).astype(int) % 6
    f = h * 6 - np.floor(h * 6)
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    out = np.choose(i, [np.stack(c, -1) for c in ((v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q))]
                    ) if False else None
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], -1)


def main() -> None:
    if not BACKUP.exists():
        BACKUP.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SRC, BACKUP)
    img = Image.open(BACKUP).convert("RGB")
    a = np.asarray(img).astype(np.float32) / 255
    poly = Image.new("L", img.size, 0)
    ImageDraw.Draw(poly).polygon([(x + ORIGIN[0], y + ORIGIN[1]) for x, y in BAG], fill=255)
    poly = np.asarray(poly.filter(ImageFilter.GaussianBlur(1.5)), dtype=np.float32) / 255
    hsv = rgb_to_hsv(a)
    hue_ok = ((hsv[..., 0] > 0.04) & (hsv[..., 0] < 0.21) & (hsv[..., 1] > 0.12) & (hsv[..., 2] < 0.68)).astype(np.float32)
    hue_ok = np.asarray(Image.fromarray((hue_ok * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)),
                        dtype=np.float32) / 255
    w = (poly * hue_ok)[..., None]
    new = hsv.copy()
    new[..., 0] = 0.068
    new[..., 1] = np.clip(hsv[..., 1] * 1.3 + 0.06, 0, 1)
    new[..., 2] = hsv[..., 2] * 0.93
    out = a * (1 - w) + hsv_to_rgb(new) * w
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(SRC, "WEBP", lossless=True)
    print(SRC, "recoloured; original kept in", BACKUP)


if __name__ == "__main__":
    main()
