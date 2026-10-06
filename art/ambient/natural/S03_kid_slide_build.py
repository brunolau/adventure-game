"""Free rebuild of the S03 ambient sprite src/game/assets/ambient/S03/natural/kid_slide.webp (2026-10-06).

Source: art/ambient/natural/S03_kid_slide.png (+ .json: prompt, model, USD 0.15), one nano-banana-pro call on flat
green. This keys it (art/tools/frames.chroma_key), takes pose (b) (the child leaning back, hands beside the hips),
scales it to 132 px, rotates it 32 degrees clockwise so the legs lie along the slide of the log playground and saves
it. The ambient layer kid_slide (src/game/data/blocking/ambient/S03.json) draws it at scale 0.42 with the pivot printed
here (the seat on the slide) and hides it behind the standing stone and the front left post (mask slide_occluders).
Run from the repo root: PYTHONIOENCODING=utf-8 python -X utf8 art/ambient/natural/S03_kid_slide_build.py
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "art" / "tools"))
import frames  # noqa: E402

ANGLE = 32.0      # clockwise
TARGET_H = 132    # texture px before rotation
rgb = np.asarray(Image.open(ROOT / "art/ambient/natural/S03_kid_slide.png").convert("RGB"))
rgba = frames.chroma_key(rgb, min_island=300)
labels, sizes = frames.label_components(rgba[..., 3] > 24)
parts = sorted((int(np.nonzero(labels == i)[1].min()), i) for i, s in enumerate(sizes, start=1) if s >= 2000)
idx = parts[1][1]                                   # pose (b), the right-hand figure
ys, xs = np.nonzero(labels == idx)
x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
part = rgba[y0:y1 + 1, x0:x1 + 1].copy()
own = labels[y0:y1 + 1, x0:x1 + 1]
part[..., 3] = np.where((own == idx) | (own == 0), part[..., 3], 0)
im = Image.fromarray(part, "RGBA")
alpha = np.asarray(im)[..., 3]
cx = int(im.width * 0.42)
seat = (cx, int(np.nonzero(alpha[:, cx] > 128)[0].max()))
k = TARGET_H / im.height
im = im.resize((round(im.width * k), TARGET_H), Image.LANCZOS)
seat = (seat[0] * k, seat[1] * k)
w, h = im.size
rot = im.rotate(-ANGLE, resample=Image.BICUBIC, expand=True)
dx, dy = seat[0] - w / 2, seat[1] - h / 2
t = math.radians(ANGLE)
pivot = [round(rot.width / 2 + dx * math.cos(t) - dy * math.sin(t)),
         round(rot.height / 2 + dx * math.sin(t) + dy * math.cos(t))]
out = ROOT / "src/game/assets/ambient/S03/natural/kid_slide.webp"
rot.save(out, "WEBP", quality=95, alpha_quality=100, method=6)
print(f"{out.relative_to(ROOT)} {rot.size} pivot {pivot} (S03.json kid_slide uses [56, 138])")
