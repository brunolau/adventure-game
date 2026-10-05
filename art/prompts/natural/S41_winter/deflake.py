"""Free retouch: remove the static snowflakes the model painted into the SKY of a winter master (the ambient
snowfall layer provides moving flakes). Small bright dots on blue sky are replaced by the local median.
Usage: python deflake.py SRC_N DST_N [--preview]
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[4]   # repo root
DIR = ROOT / "art" / "masters" / "bg_natural"
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


def main():
    src_n, dst_n = int(sys.argv[1]), int(sys.argv[2])
    src = DIR / f"S41_winter_v{src_n}.png"
    img = Image.open(src).convert("RGB")
    rows = 560                     # master rows ~ game y 0-394 (sky down to the treeline and the station roofs)
    top = img.crop((0, 0, img.width, rows))
    med = top.filter(ImageFilter.MedianFilter(17))
    a = np.asarray(top).astype(np.float32)
    m = np.asarray(med).astype(np.float32)
    luma = lambda x: 0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2]
    diff = luma(a) - luma(m)
    h, s, v = hsv(m.astype(np.uint8))
    strict = (h > 195) & (h < 235) & (s > 0.28) & (v > 0.3)
    relaxed = (h > 190) & (h < 240) & (s > 0.10) & (v > 0.3)
    relaxed[135:, :] = False          # the pale sun glow top left: only above every tree, peak and roof
    relaxed[:, 2380:] = False         # not near the pylon
    sky = strict | relaxed
    # the sky must be sky all around (no flake removal at roof / tree / rope edges)
    sky_img = Image.fromarray((sky * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(9))
    sky = np.asarray(sky_img) > 0
    flake = (diff > 18) & sky
    mask = Image.fromarray((flake * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
    mk = np.asarray(mask).astype(np.float32)[..., None] / 255.0
    out_top = (a * (1 - mk) + m * mk).clip(0, 255).astype(np.uint8)
    out = img.copy()
    out.paste(Image.fromarray(out_top), (0, 0))
    dst = DIR / f"S41_winter_v{dst_n}.png"
    out.save(dst)
    meta = {"room": "S41", "version": f"winter_v{dst_n}", "kind": "retouch", "from_version": f"winter_v{src_n}", "usd": 0,
            "note": "free retouch (scratch deflake.py): static snowflakes painted into the blue sky removed (small bright "
                    "dots on sky blue replaced by a 17 px median; master rows 0-560 only), so only the ambient "
                    "snowfall moves", "pixels_changed": int((mk[..., 0] > 0.05).sum())}
    dst.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    Image.fromarray((np.asarray(mask))).save(SCRATCH / "deflake_mask.png")
    print(dst, meta["pixels_changed"])


if __name__ == "__main__":
    main()
