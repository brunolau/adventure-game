"""Free retouch S55 v6 -> v8 (D05 state): open the cache in row 2 / column 3 of the stone panel (game x 1158-1193,
y 612-643): a dark recess with an inner shadow and crumbled mortar edge, and the pulled stone lying flat on the asphalt
at the foot of the wall. (The paid fix v7 removed four stones and changed the panel; rejected.)"""
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


im = Image.open(M / "S55_v6.png").convert("RGB")
arr = np.asarray(im, dtype=np.float32).copy()
x0, y0 = g2m(1156, 610)
x1, y1 = g2m(1195, 645)
stone = im.crop((x0, y0, x1, y1))
h, w = y1 - y0, x1 - x0
yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
# recess colour: dark earthy grey, darker at the top and left (inner shadow from the overhang), lighter at the floor
base = np.array([62, 54, 48], dtype=np.float32)
shade = 0.45 + 0.55 * np.clip(yy / (h * 0.85), 0, 1) * (0.75 + 0.25 * np.clip(xx / (w * 0.6), 0, 1))
rec = base[None, None, :] * shade[..., None]
floor = yy > h * 0.78
rec[floor] = rec[floor] * 0.6 + np.array([120, 110, 98], dtype=np.float32) * 0.4   # dusty floor of the cavity
rng = np.random.default_rng(55)
rec += rng.normal(0, 4, rec.shape)
# ragged mortar edge: keep 2-4 px of the original border, irregular
edge = np.minimum.reduce([xx, yy, w - 1 - xx, h - 1 - yy])
rag = 0.8 + 1.4 * rng.random((h, w))
alpha = np.clip((edge - rag) / 2.0, 0, 1)
alpha = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float32) / 255
region = arr[y0:y1, x0:x1]
arr[y0:y1, x0:x1] = region * (1 - alpha[..., None]) + rec * alpha[..., None]
out = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
# the pulled stone lying flat on the asphalt at the foot of the wall (squashed, darker underside shadow)
sx0, sy0 = g2m(1166, 703)
flat = stone.resize((w, int(h * 0.42)), Image.Resampling.LANCZOS)
shadow = Image.new("L", (w + 10, int(h * 0.42) + 8), 0)
sh = np.zeros((shadow.height, shadow.width), np.uint8)
sh[4:-1, 3:-3] = 110
shadow = Image.fromarray(sh).filter(ImageFilter.GaussianBlur(3))
dark = Image.new("RGB", shadow.size, (40, 36, 34))
out.paste(dark, (sx0 - 5, sy0 + 2), shadow)
m = Image.new("L", flat.size, 255).filter(ImageFilter.GaussianBlur(0.6))
out.paste(flat, (sx0, sy0), m)
out.save(M / "S55_v8.png")
meta = json.loads((M / "S55_v6.json").read_text(encoding="utf-8"))
meta.update({"version": 8, "kind": "retouch", "usd": 0, "from_version": 6,
             "retouch": "free pixel retouch (scratchpad retouch_s55_open.py): D05 state - cavity painted into stone row 2 / "
                        "column 3 (game x 1158-1193, y 612-643), the pulled stone lying flat at the wall foot (game ~1166,703)"})
meta.pop("exported", None)
(M / "S55_v8.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
sys.path.insert(0, str(ROOT / "art" / "tools"))
import paint_room  # noqa: E402
paint_room.fit_to_frame(out).crop((1000, 500, 1320, 740)).resize((640, 480)).save(Path(sys.argv[1]))
print("ok")
