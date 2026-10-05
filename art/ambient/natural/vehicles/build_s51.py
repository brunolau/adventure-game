"""S51 (2020): cut the modern tram that the paid edit S51_tram_v2_raw.png painted into the S51 master (free, local).

The edit is the S51 painting with an unbranded modern low-floor tram standing at the platform (same place as the
T3 in S11). The tram (with its pantograph and the shadow it casts) is the difference between the edit and the
untouched master. Output: src/game/assets/ambient/S51/natural/tram_2020*.webp (+ smaller copies for far away),
previews in this folder and S51_build.json (pivot = the vanishing point the sprite is scaled about).
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
import cutlib  # noqa: E402

OUT = ROOT / "src" / "game" / "assets" / "ambient" / "S51" / "natural"
VP_GAME = (1050.0, 390.0)            # near-track scaling point (between the rails' fit and the tram's own lines)
REGION = (1430, 80, 2380, 1080)      # master px
BODY_POLY = [(1618, 528), (1700, 488), (1880, 386), (1925, 352), (2205, 340), (2285, 398), (2312, 470), (2316, 700),
             (2318, 800), (2318, 965), (2255, 995), (2000, 1005), (1900, 965), (1760, 862), (1620, 742), (1612, 560)]
PANTO_BOX = [(1860, 85), (2130, 85), (2130, 372), (1860, 372)]
SHADOW_POLY = [(1436, 690), (1600, 660), (1760, 862), (1900, 965), (2000, 1012), (2200, 1012), (2200, 1040),
               (1436, 1040)]
TINT = np.array([22, 49, 98], dtype=np.float32)
SHADE = np.array([40, 40, 58], dtype=np.float32)


def main() -> None:
    clean_full = Image.open(ROOT / "art/masters/bg_natural/S51_v1.png").convert("RGB")
    veh_full = Image.open(HERE / "S51_tram_v2_raw.png").convert("RGB")
    x0, y0, x1, y1 = REGION
    c = np.asarray(clean_full, dtype=np.float32)[y0:y1, x0:x1]
    v = np.asarray(veh_full, dtype=np.float32)[y0:y1, x0:x1]
    shape = c.shape[:2]
    diff = np.abs(c - v).max(-1)
    _, res = cutlib.shadow_fit(v, c, TINT)
    body_zone = cutlib.poly_mask(shape, [BODY_POLY], (x0, y0))
    panto_zone = cutlib.poly_mask(shape, [PANTO_BOX], (x0, y0)) & ~body_zone
    body = (res > 30) & body_zone
    body = cutlib.morph(body, close=7)
    body = cutlib.fill_holes(body) & body_zone
    body = cutlib.morph(body, open_=2)
    lum = np.array([0.299, 0.587, 0.114], dtype=np.float32)
    lum_v = v @ lum
    panto = (diff > 36) & panto_zone
    panto = cutlib.morph(panto, close=3) & ((lum_v < 140) | (diff > 36)) & panto_zone
    sky = (v[..., 2] > v[..., 0] + 12) & (lum_v > 135)
    panto = cutlib.morph(panto & ~sky, close=1, open_=1)
    obj = body | panto
    obj_a = np.maximum(cutlib.soft(body, 0.8), cutlib.soft(panto, 0.6))
    obj_a = np.where(obj, 1.0, obj_a)
    shadow_zone = cutlib.poly_mask(shape, [SHADOW_POLY], (x0, y0)) | body_zone
    lv, lc, ls = lum_v, c @ lum, float(SHADE @ lum)
    a_lum = np.clip((lc - lv) / np.maximum(lc - ls, 1.0), 0, 0.5)
    sh = np.where(shadow_zone & (diff < 90), a_lum, 0.0)
    sh = np.asarray(Image.fromarray((sh * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7.0)),
                    dtype=np.float32) / 255           # a smooth shadow, not the re-rendered paving texture
    sh = np.where(sh > 0.1, sh, 0.0) * cutlib.soft(shadow_zone, 6)
    alpha = obj_a + (1 - obj_a) * sh
    col = (obj_a[..., None] * v + ((1 - obj_a) * sh)[..., None] * SHADE[None, None, :]) / np.maximum(alpha, 1e-4)[..., None]
    rgba = np.dstack([np.clip(col, 0, 255), np.clip(alpha * 255, 0, 255)]).astype(np.uint8)
    sprite = Image.fromarray(rgba, "RGBA")
    bbox = sprite.getbbox()
    sprite = sprite.crop(bbox)
    # split copies for the close-up part of the departure: the body is drawn above the hero, its cast shadow below
    body_only = np.dstack([np.clip(v, 0, 255), np.clip(obj_a * 255, 0, 255)]).astype(np.uint8)
    shadow_only = np.dstack([np.broadcast_to(SHADE, v.shape), np.clip((1 - obj_a) * sh * 255, 0, 255)]).astype(np.uint8)
    split = {"body": Image.fromarray(body_only, "RGBA").crop(bbox), "shadow": Image.fromarray(shadow_only, "RGBA").crop(bbox)}
    origin_m = (x0 + bbox[0], y0 + bbox[1])
    vp_m = cutlib.g2m(*VP_GAME)
    pivot = [round(vp_m[0] - origin_m[0], 2), round(vp_m[1] - origin_m[1], 2)]
    cutlib.save_webp(sprite, OUT / "tram_2020.webp")
    for part, img in split.items():
        cutlib.save_webp(img, OUT / f"tram_2020_{part}.webp")
    for name, f in (("tram_2020_mid", 0.4), ("tram_2020_small", 0.16), ("tram_2020_far", 0.07)):
        small = sprite.resize((max(1, round(sprite.width * f)), max(1, round(sprite.height * f))),
                              Image.Resampling.LANCZOS)
        cutlib.save_webp(small, OUT / f"{name}.webp")
    cutlib.preview(sprite, HERE / "S51_tram_preview.png")
    info = {"tram_2020": {"origin_master": list(map(int, origin_m)), "size": list(sprite.size), "pivot": pivot,
                          "vp_game": list(VP_GAME), "draw_scale_at_stop": cutlib.MASTER_SCALE}}
    (HERE / "S51_build.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(json.dumps(info))


if __name__ == "__main__":
    main()
