"""Shared helpers for cutting vehicles out of a painting with the help of an edited copy (free, local)."""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

MASTER_SCALE = 1080 / 1536          # master 2752x1536 -> 1935x1080, then 7 px cropped on the left
MASTER_CROP_X = 7


def m2g(x: float, y: float) -> tuple[float, float]:
    """Master px -> game px."""
    return x * MASTER_SCALE - MASTER_CROP_X, y * MASTER_SCALE


def g2m(x: float, y: float) -> tuple[float, float]:
    return (x + MASTER_CROP_X) / MASTER_SCALE, y / MASTER_SCALE


def poly_mask(shape: tuple[int, int], polys: list, offset=(0, 0)) -> np.ndarray:
    img = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(img)
    for poly in polys:
        d.polygon([(x - offset[0], y - offset[1]) for x, y in poly], fill=255)
    return np.asarray(img) > 0


def morph(mask: np.ndarray, grow: int = 0, shrink: int = 0, close: int = 0, open_: int = 0) -> np.ndarray:
    img = Image.fromarray((mask * 255).astype(np.uint8), "L")
    if open_:
        k = 2 * open_ + 1
        img = img.filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k))
    if close:
        k = 2 * close + 1
        img = img.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.MinFilter(k))
    if grow:
        img = img.filter(ImageFilter.MaxFilter(2 * grow + 1))
    if shrink:
        img = img.filter(ImageFilter.MinFilter(2 * shrink + 1))
    return np.asarray(img) > 127


def fill_holes(mask: np.ndarray) -> np.ndarray:
    """Fill background regions that are not connected to the border."""
    h, w = mask.shape
    pad = Image.new("L", (w + 2, h + 2), 0)
    pad.paste(Image.fromarray((mask * 255).astype(np.uint8), "L"), (1, 1))
    ImageDraw.floodfill(pad, (0, 0), 128)
    a = np.asarray(pad)[1:-1, 1:-1]
    return a != 128


def soft(mask: np.ndarray, blur: float) -> np.ndarray:
    img = Image.fromarray((mask * 255).astype(np.uint8), "L")
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(img, dtype=np.float32) / 255.0


def shadow_fit(o: np.ndarray, e: np.ndarray, tint: np.ndarray, amax: float = 0.8):
    """Per pixel alpha a so that (1-a)*e + a*tint ~= o; returns (alpha, residual)."""
    den = e - tint[None, None, :]
    num = e - o
    a = (num * den).sum(-1) / np.maximum((den * den).sum(-1), 1e-3)
    a = np.clip(a, 0, amax)
    rec = (1 - a[..., None]) * e + a[..., None] * tint[None, None, :]
    res = np.abs(rec - o).max(-1)
    return a, res


def save_webp(img: Image.Image, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "WEBP", lossless=True, quality=100, method=6)


def preview(rgba: Image.Image, path, bg=(255, 0, 255)) -> None:
    c = Image.new("RGBA", rgba.size, bg + (255,))
    c.alpha_composite(rgba)
    c.convert("RGB").save(path)


def keep_connected(mask: np.ndarray, seeds: list, offset=(0, 0), bridge: int = 0) -> np.ndarray:
    """Only the parts of mask connected (8-neighbourhood after an optional `bridge` px dilation) to one of the seed
    points (full-image px; the nearest mask pixel within 40 px is used). Drops stray specks, e.g. bits of overhead wire
    the edit repainted next to a pantograph."""
    probe = morph(mask, grow=bridge) if bridge else mask
    img = Image.fromarray((probe * 255).astype(np.uint8), "L").copy()   # a fromarray image may share the buffer
    ys, xs = np.nonzero(probe)
    for sx, sy in seeds:
        sx, sy = sx - offset[0], sy - offset[1]
        if not len(xs):
            break
        k = int(np.argmin((xs - sx) ** 2 + (ys - sy) ** 2))
        if (xs[k] - sx) ** 2 + (ys[k] - sy) ** 2 > 1600:
            continue
        ImageDraw.floodfill(img, (int(xs[k]), int(ys[k])), 128, thresh=0)
    return (np.asarray(img) == 128) & mask
