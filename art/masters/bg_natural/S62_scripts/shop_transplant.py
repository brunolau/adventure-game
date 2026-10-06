"""S62 (free): compose the final December-1982 picture from the paid steps (art/masters/bg_natural/S62.md).

  base     v4  step A: the S18 picture in December 1982 at dusk (camera kept, red parapets, bench, fence, bare tree,
               lit windows); the 1995 kiosk is still there and an unrequested second pale-blue car stands next to it
  road     v5  step B fix: removed that car (and, unasked, the kiosk); only its road / island-end area is used
  shop     v3  the derive attempt that painted exactly the right 1982 mixed-goods shop at the left (one large serving
               window, jar crate on the outer ledge, old radio, bottle crates at the corner) but ~1.6x too large
The shop is cut out of v3 along its silhouette, scaled by SCALE (offset TX, TY: walls from beyond the left edge to
x ~359, base on y ~882 = the kiosk's ground line) and pasted over the kiosk, with a soft contact shadow.
Run: PYTHONIOENCODING=utf-8 python -X utf8 art/masters/bg_natural/S62_scripts/shop_transplant.py
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "art" / "tools"))
import paint_natural  # noqa: E402
import paint_room as pr  # noqa: E402
import refit_room  # noqa: E402

paint_natural.install()
K, CROP_X = refit_room.K, refit_room.CROP_X
BASE, ROAD, SHOP = 4, 5, 3
ROAD_BOX = (356, 700, 624, 912)      # game px, taken from v5 (the extra car removed)
SCALE, TX, TY = 0.63, 0.0, 261.4
# v3 shop silhouette (game px): roof slab x 0-606 y 466-565, walls x 0-572 down to the base y 990; bottle crates
WALLS = [(-8, 466), (606, 466), (606, 566), (573, 566), (573, 990), (-8, 990)]
CRATES = [(456, 782), (613, 782), (613, 1019), (456, 1019)]


def g2m(x: float, y: float) -> tuple[float, float]:
    return (x + CROP_X) / K, y / K


def soft_box(box, feather):
    m = Image.new("L", pr.MODEL_FRAME, 0)
    x0, y0 = g2m(box[0], box[1])
    x1, y1 = g2m(box[2], box[3])
    ImageDraw.Draw(m).rectangle([x0 + feather, y0 + feather, x1 - feather, y1 - feather], fill=255)
    return m.filter(ImageFilter.GaussianBlur(feather / 2))


def main() -> None:
    base, _ = refit_room.load_master("S62", BASE)
    road, _ = refit_room.load_master("S62", ROAD)
    shop_src, _ = refit_room.load_master("S62", SHOP)
    img = Image.composite(road, base, soft_box(ROAD_BOX, 14))

    alpha = Image.new("L", pr.MODEL_FRAME, 0)
    d = ImageDraw.Draw(alpha)
    d.polygon([g2m(x, y) for x, y in WALLS], fill=255)
    d.polygon([g2m(x, y) for x, y in CRATES], fill=255)
    alpha = alpha.filter(ImageFilter.GaussianBlur(1.5))
    sprite = shop_src.convert("RGBA")
    sprite.putalpha(alpha)
    box = alpha.getbbox()
    sprite = sprite.crop(box)
    sprite = sprite.resize((round(sprite.width * SCALE), round(sprite.height * SCALE)), Image.Resampling.LANCZOS)
    ox = SCALE * box[0] + (TX + CROP_X * (SCALE - 1)) / K
    oy = SCALE * box[1] + TY / K

    def gx(x):
        return SCALE * x + TX

    def gy(y):
        return SCALE * y + TY
    right, base_y = gx(573), gy(990)
    shadow = Image.new("L", pr.MODEL_FRAME, 0)
    sd = ImageDraw.Draw(shadow)
    sd.polygon([g2m(-10, base_y - 6), g2m(right + 4, base_y - 6), g2m(right + 8, base_y + 8), g2m(-10, base_y + 8)],
               fill=110)
    crate_bottom = gy(1019)
    sd.polygon([g2m(gx(452), crate_bottom - 5), g2m(gx(618), crate_bottom - 5), g2m(gx(622), crate_bottom + 6),
                g2m(gx(448), crate_bottom + 6)], fill=120)
    shadow = shadow.filter(ImageFilter.GaussianBlur(7))
    dark = ImageChops.multiply(img, Image.new("RGB", img.size, (120, 124, 140)))
    img = Image.composite(dark, img, shadow).convert("RGBA")
    img.alpha_composite(sprite, (round(ox), round(oy)))
    final = img.convert("RGB")
    version = pr.next_version("S62")
    out = pr.MASTERS / f"S62_v{version}.png"
    final.save(out)
    meta = {"room": "S62", "version": version, "kind": "transplant", "usd": 0,
            "from_versions": {"base": BASE, "road_without_extra_car": ROAD, "shop": SHOP}, "road_box_game_px": ROAD_BOX,
            "transform_game_px": {"scale": SCALE, "offset": [TX, TY]},
            "shop_walls_game_px": [round(gx(0)), round(gy(566)), round(gx(573)), round(gy(990))],
            "window_game_px": [round(gx(60)), round(gy(577)), round(gx(502)), round(gy(800))],
            "ledge_top_game_y": round(gy(797)), "crates_game_px": [round(gx(456)), round(gy(782)), round(gx(613)),
                                                                   round(gy(1019))],
            "script": "art/masters/bg_natural/S62_scripts/shop_transplant.py",
            "started": datetime.datetime.now().isoformat(timespec="seconds"), "output_size": list(final.size)}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(out.relative_to(ROOT), {k: meta[k] for k in ("shop_walls_game_px", "window_game_px", "ledge_top_game_y",
                                                      "crates_game_px")})


if __name__ == "__main__":
    main()
