"""Free pixel retouch S61 SRC -> DST (relayout 2026-10-06): the E08 state "niche closed".

The stone of row 2 / column 3 of the 3 x 4 panel (game x 1158-1193, y 610-643) goes back into its cavity: the stone
of row 1 / column 3 (same column, so the same light; game y 575-608) is cloned 35 px down into the cavity through a
2 px feathered mask; a thin fresh mortar line (slightly lighter grey) frames it.

    python art/masters/bg_natural/S61_scripts/retouch_s61_closed.py SRC DST <preview.png>
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(r"C:\Users\klatt\Desktop\adventura")
M = ROOT / "art/masters/bg_natural"
K = 1536 / 1080


def g2m(x, y):
    return int(round((x + 7) * K)), int(round(y * K))


src_v, dst_v = int(sys.argv[1]), int(sys.argv[2])
im = Image.open(M / f"S61_v{src_v}.png").convert("RGB")
arr = np.asarray(im, dtype=np.float32).copy()
x0, y0 = g2m(1156, 573)
x1, y1 = g2m(1195, 609)
dy = int(round(36 * K))
stone = arr[y0:y1, x0:x1].copy()
h, w = stone.shape[:2]
mask = np.zeros((h, w), np.uint8)
mask[2:-2, 2:-2] = 255
mask = np.asarray(Image.fromarray(mask).filter(ImageFilter.GaussianBlur(1.4)), dtype=np.float32)[..., None] / 255
region = arr[y0 + dy:y1 + dy, x0:x1]
arr[y0 + dy:y1 + dy, x0:x1] = region * (1 - mask) + stone * mask
# fresh mortar: lighten the 2-3 px joint ring around the replaced stone a little
ring = np.zeros((h + 8, w + 8), np.float32)
ring[1:-1, 1:-1] = 1
ring[5:-5, 5:-5] = 0
ring = np.asarray(Image.fromarray((ring * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)), dtype=np.float32)[..., None] / 255 * 0.35
reg = arr[y0 + dy - 4:y1 + dy + 4, x0 - 4:x1 + 4]
arr[y0 + dy - 4:y1 + dy + 4, x0 - 4:x1 + 4] = reg * (1 - ring) + np.array([168, 164, 156], dtype=np.float32) * ring
out = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
out.save(M / f"S61_v{dst_v}.png")
meta = json.loads((M / f"S61_v{src_v}.json").read_text(encoding="utf-8"))
meta.update({"version": dst_v, "kind": "retouch", "usd": 0, "from_version": src_v,
             "retouch": "free pixel retouch (art/masters/bg_natural/S61_scripts/retouch_s61_closed.py): E08 state - the "
                        "cavity of row 2 / column 3 closed with the stone of row 1 / column 3 cloned 36 px down, fresh mortar ring"})
meta.pop("exported", None)
(M / f"S61_v{dst_v}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
sys.path.insert(0, str(ROOT / "art" / "tools"))
import paint_room  # noqa: E402
c = paint_room.fit_to_frame(out).crop((1060, 540, 1260, 700))
c.resize((c.width * 3, c.height * 3), Image.Resampling.LANCZOS).save(Path(sys.argv[3]))
print("wrote", M / f"S61_v{dst_v}.png")
