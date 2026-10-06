"""S18 (free): transplant the kiosk painted in the raw output of the v5 guide-mode edit, scaled to the planned size.

The v5 edit (S18_scripts/edit_on_base.py spec s18_kiosk2) painted a convincing weathered kiosk, but ~1.35x larger than
the placeholder (x 90-571, y 466-879): it would hide the little red car and most of the left lawn. This script cuts
the kiosk out of that raw output along its silhouette, scales it by SCALE about the game-frame origin with offset
(TX, TY) so that its walls stand at x 12-339 with the base on y 880, adds a soft contact and cast shadow (low sun from
the left: the shadow falls to the right of the kiosk), and pastes it onto the base version (v5 with the kiosk
composite box put back to v4 = the owner's painting there). Result: the next master version.

Run: PYTHONIOENCODING=utf-8 python -X utf8 art/masters/bg_natural/S18_scripts/kiosk_transplant.py
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
K = refit_room.K
CROP_X = refit_room.CROP_X

RAW = ROOT / "art" / "masters" / "bg_natural" / "_S18_v5_edit_raw.png"
WITH_RIGHT = 5          # v5: bench (v3) + fence and laundry (v5 edit)
CLEAN_LEFT = 4          # v4: the owner's painting in the kiosk area
LEFT_BOX = (0, 460, 492, 952)   # covers the whole v5 kiosk composite box (0, 470, 482, 945)
SCALE, TX, TY = 0.75, -72.0, 223.75
# kiosk silhouette in the raw (game px): roof slab x 90-571 y 466-508, walls x 111-549 down to the base y 879
SILHOUETTE = [(89, 465), (572, 465), (572, 509), (550, 509), (550, 880), (110, 880), (110, 509), (89, 509)]


def g2m(x: float, y: float) -> tuple[float, float]:
    return (x + CROP_X) / K, y / K


def main() -> None:
    raw = Image.open(RAW).convert("RGB").resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    right, _ = refit_room.load_master("S18", WITH_RIGHT)
    clean, _ = refit_room.load_master("S18", CLEAN_LEFT)
    base = right.copy()
    b = [round(v) for v in (*g2m(LEFT_BOX[0], LEFT_BOX[1]), *g2m(LEFT_BOX[2], LEFT_BOX[3]))]
    b[0] = 0
    base.paste(clean.crop(tuple(b)), (b[0], b[1]))

    # Kiosk sprite (master px) with a 1.5 px soft edge.
    alpha = Image.new("L", pr.MODEL_FRAME, 0)
    ImageDraw.Draw(alpha).polygon([g2m(x, y) for x, y in SILHOUETTE], fill=255)
    alpha = alpha.filter(ImageFilter.GaussianBlur(1.5))
    sprite = raw.convert("RGBA")
    sprite.putalpha(alpha)
    box = alpha.getbbox()
    sprite = sprite.crop(box)
    sprite = sprite.resize((round(sprite.width * SCALE), round(sprite.height * SCALE)), Image.Resampling.LANCZOS)
    # game transform x' = S x + TX  ->  master X' = S X + (TX + CROP_X (S - 1)) / K
    ox = SCALE * box[0] + (TX + CROP_X * (SCALE - 1)) / K
    oy = SCALE * box[1] + TY / K

    # Shadows on the ground: contact band under the base, cast shadow to the right (sun low from the left).
    def gx(x):
        return SCALE * x + TX

    def gy(y):
        return SCALE * y + TY
    left, right_x, base_y = gx(110), gx(550), gy(880)
    shadow = Image.new("L", pr.MODEL_FRAME, 0)
    d = ImageDraw.Draw(shadow)
    d.polygon([g2m(left - 4, base_y - 6), g2m(right_x + 6, base_y - 6), g2m(right_x + 10, base_y + 7),
               g2m(left - 6, base_y + 7)], fill=120)
    d.polygon([g2m(right_x - 2, base_y + 4), g2m(right_x - 2, base_y - 30), g2m(right_x + 120, base_y - 26),
               g2m(right_x + 150, base_y - 8)], fill=90)
    shadow = shadow.filter(ImageFilter.GaussianBlur(9))
    dark = ImageChops.multiply(base, Image.new("RGB", base.size, (150, 128, 125)))
    base = Image.composite(dark, base, shadow)

    base = base.convert("RGBA")
    base.alpha_composite(sprite, (round(ox), round(oy)))
    final = base.convert("RGB")
    version = pr.next_version("S18")
    out = pr.MASTERS / f"S18_v{version}.png"
    final.save(out)
    meta = {"room": "S18", "version": version, "kind": "transplant", "usd": 0,
            "from_versions": {"right_side": WITH_RIGHT, "left_side": CLEAN_LEFT},
            "kiosk_source": RAW.relative_to(ROOT).as_posix(), "silhouette_game_px": SILHOUETTE,
            "transform_game_px": {"scale": SCALE, "offset": [TX, TY]},
            "kiosk_walls_game_px": [round(gx(110)), round(gy(509)), round(gx(550)), round(gy(880))],
            "script": "art/masters/bg_natural/S18_scripts/kiosk_transplant.py",
            "started": datetime.datetime.now().isoformat(timespec="seconds"), "output_size": list(final.size)}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(out.relative_to(ROOT), meta["kiosk_walls_game_px"])


if __name__ == "__main__":
    main()
