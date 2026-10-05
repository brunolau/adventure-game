"""ROBOT 'snow' variant for the winter S41: a little fresh snow on the robot's lid (free, local).

For every cell of npc_sheet.webp and idle_sheet.webp: find the cream top face of the lid (light, low-saturation
pixels above the yellow rim, in the body columns), build a snow slab = that face lifted by a thickness that is
largest in the middle (a soft pile), shade its top white and its front edge pale blue, add a tiny painterly noise,
antialias, and composite it over the cell. The open-lid gesture frame gets a thin strip on the lid's top edge.
Writes npc_sheet_snow.webp/.json and idle_sheet_snow.webp/.json next to the originals (same cells and pivots).
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[4]   # repo root
ACT = ROOT / "src" / "game" / "assets" / "actors" / "ROBOT"
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


RNG = np.random.default_rng(41)
_n = Image.fromarray(((RNG.normal(0, 1, (400, 400)) * 40 + 128).clip(0, 255)).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5))
NOISE = (np.asarray(_n).astype(np.float32) - 128) / 12.0


def snow_cell(cell: Image.Image, open_lid: bool, thick: float) -> Image.Image:
    a = np.asarray(cell).astype(np.float32)
    rgb, alpha = a[..., :3], a[..., 3]
    h, s, v = hsv(rgb.astype(np.uint8))
    H, W = alpha.shape
    opaque = alpha > 160
    yellow = (h > 32) & (h < 58) & (s > 0.42) & (v > 0.55) & opaque
    cream = (v > 0.70) & (s < 0.32) & opaque
    face = np.zeros_like(opaque)
    cols = []
    for x in range(W):
        ys = np.where(opaque[:, x])[0]
        if len(ys) == 0:
            continue
        top = ys[0]
        if open_lid:
            ok = 0 <= top < 70 and cream[top:top + 6, x].any()
        else:
            ok = 70 <= top < 150
        if not ok:
            continue
        yl = np.where(yellow[top:, x])[0]
        bottom = top + (yl[0] if len(yl) else 0)
        if open_lid:
            bottom = top + 5
        seg = cream[top:bottom, x]
        if bottom - top < 3 or seg.mean() < 0.5:
            continue
        face[top:bottom, x] = True
        cols.append(x)
    if len(cols) < 20:
        return cell
    x0, x1 = min(cols), max(cols)
    # thickness: soft pile, thicker in the middle, a few gentle bumps (fixed pattern -> no shimmer)
    t = (np.arange(W) - x0) / max(1, x1 - x0)
    pile = np.clip(np.sin(np.pi * np.clip(t, 0, 1)), 0, 1) ** 0.45
    bumps = 1 + 0.18 * np.sin(t * 17.0) + 0.10 * np.sin(t * 41.0 + 1.3)
    T = (thick * pile * bumps).round().astype(int)
    slab = np.zeros_like(face)
    topface = np.zeros_like(face)
    for x in range(x0, x1 + 1):
        ys = np.where(face[:, x])[0]
        if len(ys) == 0 or T[x] <= 0:
            continue
        y_top, y_bot = ys[0], ys[-1]
        k = T[x]
        slab[max(0, y_top - k):y_bot + 1, x] = True
        topface[max(0, y_top - k):max(0, y_bot - k) + 1, x] = True
    # rounded edges: blur + threshold
    sm = Image.fromarray((slab * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6))
    sa = np.asarray(sm).astype(np.float32) / 255.0
    sa = np.clip((sa - 0.35) / 0.3, 0, 1)
    tf = np.asarray(Image.fromarray((topface * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.0))) / 255.0
    yy = np.arange(H)[:, None].astype(np.float32)
    n = NOISE[:H, :W]
    yrel = np.clip((yy - (np.where(slab.any(1))[0].min() if slab.any() else 0)) / 22.0, 0, 1)
    top_col = np.stack([250 - 14 * yrel + 2 * n, 252 - 10 * yrel + 2 * n, 255 - 4 * yrel + n], -1)
    side_col = np.stack([200 + 3 * n, 214 + 3 * n, 236 + 2 * n], -1)
    col = top_col * tf[..., None] + side_col * (1 - tf[..., None])
    # a soft warm highlight on the upper left of the pile, a little shade towards the right
    xx = np.arange(W)[None, :].astype(np.float32)
    shade = np.clip((xx - x0) / max(1, x1 - x0), 0, 1)
    col = col - np.stack([shade * 16, shade * 12, shade * 4], -1)
    col = np.clip(col, 0, 255)
    out = rgb * (1 - sa[..., None]) + col * sa[..., None]
    new_alpha = np.maximum(alpha, sa * 255)
    res = np.dstack([out, new_alpha]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(res, "RGBA")


def process(name: str, open_frames: set[int], thick: float):
    meta = json.loads((ACT / f"{name}.json").read_text(encoding="utf-8"))
    sheet = Image.open(ACT / meta["file"]).convert("RGBA")
    cw, ch = meta["cell"]
    cols = meta.get("columns") or sheet.width // cw
    out = sheet.copy()
    for i in range(meta["frames"]):
        bx, by = (i % cols) * cw, (i // cols) * ch
        cell = sheet.crop((bx, by, bx + cw, by + ch))
        out.paste(snow_cell(cell, i in open_frames, thick * (0.55 if i in open_frames else 1.0)), (bx, by))
    new_file = meta["file"].replace(".webp", "_snow.webp")
    out.save(ACT / new_file, "WEBP", lossless=True, quality=100, method=6)
    meta2 = dict(meta, file=new_file, name=meta["name"] + "_snow",
                 note=(meta.get("note", "") + " | snow variant for the winter S41: fresh snow on the lid, added "
                       "locally (scratch robot_snow.py), same cells and pivots").strip(" |"))
    (ACT / f"{name}_snow.json").write_text(json.dumps(meta2, indent=2, ensure_ascii=False), encoding="utf-8")
    prev = Image.new("RGBA", out.size, (90, 140, 90, 255))
    prev.alpha_composite(out)
    prev.convert("RGB").save(SCRATCH / f"{name}_snow_preview.png")
    print(ACT / new_file)


if __name__ == "__main__":
    thick = float(sys.argv[1]) if len(sys.argv) > 1 else 13
    process("npc_sheet", {4}, thick)
    process("idle_sheet", set(), thick)
