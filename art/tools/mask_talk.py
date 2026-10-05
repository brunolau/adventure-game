"""Local (free) talk frames for characters who wear a 2020 face mask.

Image editors asked for "speaking behind the mask" pull the mask off the mouth or paint an open mouth through
it (tested on five NPCs with NB2, 2026-10-05). This tool instead moves the mask the way a jaw moves it: the
light-blue mask is found in the head band of a raw key-background sheet, and its lower part is stretched
downwards around a jaw hinge (no movement at the ear side, full movement at the chin). Eyes and eyebrows stay
those of the base, so alternating talk frames does not flicker the expression.

Usage (outputs are raw sheets of the same size as the base, to be used as `patch:` frames in frames.py stills):
  python mask_talk.py BASE.png OUT_A.png --drop 0.14 [--fold]
  python mask_talk.py BASE.png OUT_B.png --drop 0.07
  --facing right|left  side of the image the face points to (default right: the chin is the right end)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

import frames


def find_mask(rgb: np.ndarray, head_band: float = 0.24) -> np.ndarray:
    """Boolean matte of the light-blue surgical mask (largest light-blue component in the head band)."""
    key = frames.chroma_key(rgb)
    x0, y0, x1, y1 = frames.alpha_bbox(key)
    top, bottom = y0, y0 + int((y1 - y0) * head_band)
    rgbf = rgb.astype(np.float32)
    r, g, b = rgbf[..., 0], rgbf[..., 1], rgbf[..., 2]
    mx, mn = rgbf.max(axis=2), rgbf.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1)
    blue = (b > r + 18) & (b >= g - 6) & (mx > 120) & (sat > 0.08) & (sat < 0.7) & (key[..., 3] > 128)
    blue[:top] = False
    blue[bottom:] = False
    labels, sizes = frames.label_components(blue)
    if len(sizes) == 0:
        raise SystemExit("no light-blue mask found in the head band")
    mask = labels == (int(np.argmax(sizes)) + 1)
    # close pleat shadows and stitching inside the mask
    img = Image.fromarray((mask * 255).astype(np.uint8), "L")
    img = img.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))
    return np.asarray(img) > 128


def jaw_drop(rgb: np.ndarray, mask: np.ndarray, drop: float, hinge: float = 0.42, facing: str = "right",
             fold: bool = False, outline_px: int = 4) -> tuple[np.ndarray, dict]:
    ys, xs = np.nonzero(mask)
    mx0, mx1, my0, my1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    mh = my1 - my0
    d_max = drop * mh
    y_hinge = my0 + hinge * mh
    # sample region: the mask plus its painted outline just below it
    region = np.asarray(Image.fromarray((mask * 255).astype(np.uint8), "L")
                        .filter(ImageFilter.MaxFilter(2 * outline_px + 1))) > 128
    soft = np.asarray(Image.fromarray((region * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(1.2)),
                      dtype=np.float32) / 255
    out = rgb.astype(np.float32).copy()
    src_all = rgb.astype(np.float32)
    h = rgb.shape[0]
    for x in range(mx0 - outline_px, mx1 + outline_px + 1):
        col = np.flatnonzero(region[:, x])
        if len(col) == 0:
            continue
        bottom = int(col.max())
        if bottom <= y_hinge + 2:
            continue
        t = (x - mx0) / max(1, mx1 - mx0)
        t = t if facing == "right" else 1 - t
        weight = float(np.clip((t - 0.05) / 0.6, 0, 1))
        weight = weight * weight * (3 - 2 * weight)  # smoothstep: hinge near the ear, full drop at the chin
        new_bottom = bottom + d_max * weight
        if new_bottom - bottom < 0.5:
            continue
        y_start = int(np.floor(y_hinge))
        y_end = min(h - 1, int(np.ceil(new_bottom)) + 1)
        dst = np.arange(y_start, y_end + 1, dtype=np.float32)
        src = y_hinge + (dst - y_hinge) * (bottom - y_hinge) / (new_bottom - y_hinge)
        src = np.clip(src, 0, h - 1)
        lo = np.floor(src).astype(int)
        hi = np.minimum(lo + 1, h - 1)
        f = (src - lo)[:, None]
        pix = src_all[lo, x] * (1 - f) + src_all[hi, x] * f
        alpha = (soft[lo, x] * (1 - f[:, 0]) + soft[hi, x] * f[:, 0])[:, None]
        if fold:
            # a soft horizontal fold where the stretched fabric creases (about 60 % down the moving part)
            rel = (dst - y_hinge) / max(1.0, new_bottom - y_hinge)
            shade = 1 - 0.07 * weight * np.exp(-((rel - 0.6) / 0.08) ** 2)
            pix = pix * shade[:, None]
        out[y_start:y_end + 1, x] = out[y_start:y_end + 1, x] * (1 - alpha) + pix * alpha
    report = {"mask_box": [mx0, my0, mx1, my1], "mask_height_px": mh, "drop_px": round(d_max, 1),
              "hinge_y": round(y_hinge, 1)}
    return out.clip(0, 255).astype(np.uint8), report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("base")
    parser.add_argument("out")
    parser.add_argument("--drop", type=float, default=0.14, help="chin drop as a fraction of the mask height")
    parser.add_argument("--hinge", type=float, default=0.42, help="hinge line as a fraction of the mask height")
    parser.add_argument("--facing", choices=["right", "left"], default="right")
    parser.add_argument("--fold", action="store_true")
    args = parser.parse_args()
    rgb = np.asarray(Image.open(args.base).convert("RGB"))
    mask = find_mask(rgb)
    out, report = jaw_drop(rgb, mask, args.drop, args.hinge, args.facing, args.fold)
    Image.fromarray(out).save(args.out)
    sidecar = Path(args.out).with_suffix(".json")
    sidecar.write_text(json.dumps(dict(report, tool="mask_talk.py (local, free)", base=Path(args.base).name,
                                       drop=args.drop, hinge=args.hinge, fold=args.fold), indent=2),
                       encoding="utf-8", newline="\n")
    print(args.out, json.dumps(report))


if __name__ == "__main__":
    main()
