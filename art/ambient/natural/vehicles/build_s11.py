"""S11 (1995): cut the painted Tatra T3 out of the painting as a moving sprite and build the tramless patch.

Free and local. Inputs: the S11 master art/masters/bg_natural/S11_v1.png and the paid edit
S11_notram_v1_raw.png (the same painting with the tram removed, see edit.py). Outputs:
  src/game/assets/ambient/S11/natural/tram_t3.webp     the tram + its cast shadow (master resolution, RGBA)
  src/game/assets/ambient/S11/natural/track_empty.webp the empty track where the tram stands (game px, RGBA)
  art/ambient/natural/vehicles/S11_*.png               previews
The tram sprite is scaled about the track's vanishing point (pivot = VP) by the ambient layers in
data/blocking/ambient/S11.json, which is exact perspective for something moving along the track.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "art" / "tools"))
import cutlib  # noqa: E402
import paint_room  # noqa: E402

OUT = ROOT / "src" / "game" / "assets" / "ambient" / "S11" / "natural"
VP_GAME = (1035.0, 378.0)             # where the near track's rails converge (fitted to the painted rails)
REGION = (1440, 90, 2330, 1000)       # master px: tram, pantograph, cast shadow
BODY_POLY = [(1640, 520), (1690, 470), (1820, 425), (1835, 392), (2255, 388), (2302, 450), (2300, 600), (2294, 880),
             (2240, 912), (2120, 915), (2085, 975), (1975, 975), (1940, 925), (1850, 880), (1700, 770), (1640, 720)]
PANTO_BOX = [(1770, 100), (2100, 100), (2100, 400), (1770, 400)]
SHADOW_POLY = [(1470, 680), (1660, 680), (1700, 770), (1850, 880), (1950, 940), (2330, 940), (2330, 1000),
               (1460, 1000)]
TINT = np.array([22, 49, 98], dtype=np.float32)        # separates body (badly fitted) from shadow
SHADE = np.array([34, 42, 66], dtype=np.float32)       # colour of the moving cast shadow


def main() -> None:
    o_full = Image.open(ROOT / "art/masters/bg_natural/S11_v1.png").convert("RGB")
    e_full = Image.open(HERE / "S11_notram_v1_raw.png").convert("RGB")
    x0, y0, x1, y1 = REGION
    o = np.asarray(o_full, dtype=np.float32)[y0:y1, x0:x1]
    e = np.asarray(e_full, dtype=np.float32)[y0:y1, x0:x1]
    shape = o.shape[:2]
    diff = np.abs(o - e).max(-1)
    a, res = cutlib.shadow_fit(o, e, TINT)
    body_zone = cutlib.poly_mask(shape, [BODY_POLY], (x0, y0))
    panto_zone = cutlib.poly_mask(shape, [PANTO_BOX], (x0, y0)) & ~body_zone
    body = (res > 34) & body_zone
    body = cutlib.morph(body, close=7)
    body = cutlib.fill_holes(body) & body_zone
    body = cutlib.morph(body, open_=2)
    panto = (diff > 38) & panto_zone
    lum_o = o @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    panto = cutlib.morph(panto, close=4) & ((lum_o < 140) | (diff > 38)) & panto_zone   # bridge the wire crossings
    rows = np.arange(shape[0])[:, None] + y0
    rust = o[..., 0] > o[..., 2] + 10
    panto &= rust | (rows < 172)        # below the grey collector bars the frame is rusty: drop the dark wire bits
    sky = (o[..., 2] > o[..., 0] + 12) & (lum_o > 135)
    panto = cutlib.morph(panto & ~sky, close=2, open_=1)
    obj = body | panto
    obj_a = np.maximum(cutlib.soft(body, 0.8), cutlib.soft(panto, 0.6))
    obj_a = np.where(obj | (obj_a > 0.5), np.maximum(obj_a, obj.astype(np.float32)), obj_a)
    shadow_zone = cutlib.poly_mask(shape, [SHADOW_POLY], (x0, y0)) | body_zone
    lum = np.array([0.299, 0.587, 0.114], dtype=np.float32)
    lo, le, lc = o @ lum, e @ lum, float(SHADE @ lum)
    a_lum = np.clip((le - lo) / np.maximum(le - lc, 1.0), 0, 0.62)   # darkening that matches the painted luminance
    sh = np.where(shadow_zone, a_lum, 0.0)
    sh = np.where(sh > 0.08, sh, 0.0)
    sh = np.asarray(Image.fromarray((sh * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.0)),
                    dtype=np.float32) / 255
    alpha = obj_a + (1 - obj_a) * sh
    col = (obj_a[..., None] * o + ((1 - obj_a) * sh)[..., None] * SHADE[None, None, :]) / np.maximum(alpha, 1e-4)[..., None]
    rgba = np.dstack([np.clip(col, 0, 255), np.clip(alpha * 255, 0, 255)]).astype(np.uint8)
    sprite = Image.fromarray(rgba, "RGBA")
    bbox = sprite.getbbox()
    sprite = sprite.crop(bbox)
    # split copies for the close-up part of the departure: the body is drawn above the hero, its cast shadow below
    body_only = np.dstack([np.clip(o, 0, 255), np.clip(obj_a * 255, 0, 255)]).astype(np.uint8)
    shadow_only = np.dstack([np.broadcast_to(SHADE, o.shape), np.clip((1 - obj_a) * sh * 255, 0, 255)]).astype(np.uint8)
    split = {"body": Image.fromarray(body_only, "RGBA").crop(bbox), "shadow": Image.fromarray(shadow_only, "RGBA").crop(bbox)}
    origin_m = (x0 + bbox[0], y0 + bbox[1])
    vp_m = cutlib.g2m(*VP_GAME)
    pivot = [round(vp_m[0] - origin_m[0], 2), round(vp_m[1] - origin_m[1], 2)]
    cutlib.save_webp(sprite, OUT / "tram_t3.webp")
    for part, img in split.items():
        cutlib.save_webp(img, OUT / f"tram_t3_{part}.webp")
    for name, f in (("tram_t3_mid", 0.4), ("tram_t3_small", 0.16), ("tram_t3_far", 0.07)):   # smaller copies: 2D draws without mipmaps
        small = sprite.resize((max(1, round(sprite.width * f)), max(1, round(sprite.height * f))),
                              Image.Resampling.LANCZOS)
        cutlib.save_webp(small, OUT / f"{name}.webp")
    cutlib.preview(sprite, HERE / "S11_tram_preview.png")
    # patch in game px: the edit's pixels wherever the tram, its pantograph or its shadow changed the painting
    o_g = np.asarray(paint_room.fit_to_frame(o_full), dtype=np.float32)
    e_g = np.asarray(paint_room.fit_to_frame(e_full), dtype=np.float32)
    full_obj = np.zeros((1536, 2752), dtype=np.uint8)
    full_obj[y0:y1, x0:x1] = (np.maximum(obj_a, (sh > 0.05).astype(np.float32)) > 0.3) * 255
    mask_g = np.asarray(paint_room.fit_to_frame(Image.fromarray(full_obj, "L").convert("RGB")).convert("L")) > 60
    mask_g = cutlib.morph(mask_g, grow=10)
    pa = cutlib.soft(mask_g, 5)
    ys, xs = np.nonzero(pa > 0.003)
    gx0, gy0, gx1, gy1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    patch = np.dstack([e_g[gy0:gy1, gx0:gx1], pa[gy0:gy1, gx0:gx1] * 255]).clip(0, 255).astype(np.uint8)
    patch_img = Image.fromarray(patch, "RGBA")
    cutlib.save_webp(patch_img, OUT / "track_empty.webp")
    check = Image.fromarray(o_g.astype(np.uint8)).convert("RGBA")
    check.alpha_composite(patch_img, (int(gx0), int(gy0)))
    check.convert("RGB").save(HERE / "S11_patched_preview.png")
    info = {"tram_t3": {"origin_master": list(map(int, origin_m)), "size": list(sprite.size), "pivot": pivot,
                        "vp_game": list(VP_GAME), "draw_scale_at_stop": cutlib.MASTER_SCALE},
            "track_empty": {"pos": [int(gx0), int(gy0)], "size": list(patch_img.size)}}
    (HERE / "S11_build.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
