"""S41 winter v5 (free): re-composite the raw output of the paid hotel fix (v4) onto v1.

The fix model drew the steep A-frame of Hotel Posta taller than its box (gable tip at y ~150), so the paid v4
composite cut the roof. v5 takes the same raw output with a taller box (x 540-1090, y 110-440) and a 48 master px
feather, but only 10 px on the lower-left edges (x < 800, y > 330) so v1's old deck on stilts does not ghost through
the new hedge. Then deflake.py 5 6 removes the painted static snowflakes from the sky -> v6 (final).
Usage: python recomposite_v5.py
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "art" / "tools"))
import paint_natural  # noqa: E402

paint_natural.install()
import paint_room as pr  # noqa: E402
import refit_room  # noqa: E402

DIR = ROOT / "art" / "masters" / "bg_natural"


def main():
    v1 = Image.open(DIR / "S41_winter_v1.png").convert("RGB")
    raw = Image.open(DIR / "_bg_natural_S41_winter_S41_winter_v4_fix_raw.png").convert("RGB").resize(
        pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    x, y, w, h = 540, 110, 550, 330
    mx0, my0 = refit_room.to_master(x, y)
    mx1, my1 = refit_room.to_master(x + w, y + h)
    box = (round(mx0), round(my0), round(mx1), round(my1))
    a48 = np.asarray(refit_room.soft_mask(pr.MODEL_FRAME, box, 48)).astype(np.float32)
    a10 = np.asarray(refit_room.soft_mask(pr.MODEL_FRAME, box, 10)).astype(np.float32)
    y330 = int(refit_room.to_master(0, 330)[1])
    x800 = int(refit_room.to_master(800, 0)[0])
    sel = np.zeros_like(a48, dtype=bool)
    sel[y330:, :x800] = True
    mask = Image.fromarray(np.where(sel, a10, a48).clip(0, 255).astype(np.uint8))
    Image.composite(raw, v1, mask).save(DIR / "S41_winter_v5.png")
    print(DIR / "S41_winter_v5.png")


if __name__ == "__main__":
    main()
