"""Free pixel retouch S55 SRC -> DST (relayout 2026-10-06): the distance markings of the pickup point.

The derive (v9) painted the markings as one long diagonal dashed yellow line running across the walk band towards the
camera. 1) Remove it: every yellow-paint pixel (dilated 4 px) in game x 1240-1800, y 630-1080 is replaced by the S17 v8
asphalt (same camera, the derive kept the asphalt texture: NCC 0.83), tone-matched by the ratio of the two paintings'
blurred colours (computed without the dashes). 2) Paint the markings the blocking describes: five short transverse
yellow bars, 0.6 m long (in depth) and 0.12 m wide, 1.4 m apart, centred on y ~765 (6.65 m ahead), at X = -2.6 ..
+3.0 m - perspective-correct (each stripe points at the vanishing point), lit by the asphalt underneath (paint colour x
local relative luminance), worn (alpha noise), soft edges.

    python art/masters/bg_natural/S55_scripts/retouch_s55_markings.py SRC DST <preview.png>
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(r"C:\Users\klatt\Desktop\adventura")
M = ROOT / "art/masters/bg_natural"
K = 1536 / 1080
F, CX, HOR, EYE = 1220.0, 960.0, 380.0, 2.1


def g2m(x, y):
    return (x + 7) * K, y * K


def P(X, Z):
    return CX + F * X / Z, HOR + F * EYE / Z


src_v, dst_v = int(sys.argv[1]), int(sys.argv[2])
img = Image.open(M / f"S55_v{src_v}.png").convert("RGB")
W, H = img.size
b = np.asarray(img, dtype=np.float32).copy()
a = np.asarray(Image.open(M / "S17_v8.png").convert("RGB"), dtype=np.float32)

# 1. remove the diagonal dashes
r, g, bl = b[..., 0], b[..., 1], b[..., 2]
yellow = (r > 105) & (g > 90) & (bl < 110) & ((r - bl) > 55) & ((g - bl) > 40) & ((r - g) < 70)
win = np.zeros_like(yellow)
x0, y0 = g2m(1240, 630)
x1, y1 = g2m(1800, 1080)
win[int(y0):int(y1), int(x0):int(x1)] = True
yellow &= win
hole = np.asarray(Image.fromarray((yellow * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)), dtype=np.float32) / 255
# the last dash fragment at the pipe foot lies in the dark patch and is too dark for the colour test: add its box
fx0, fy0 = g2m(1312, 690)
fx1, fy1 = g2m(1360, 718)
hole[int(fy0):int(fy1), int(fx0):int(fx1)] = 1.0
known = 1 - hole


def masked_blur(img_arr, w, radius):
    num = np.asarray(Image.fromarray(np.clip(img_arr * w[..., None], 0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(radius)), dtype=np.float32)
    den = np.asarray(Image.fromarray((w * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius)),
                     dtype=np.float32)[..., None] / 255
    return num / np.maximum(den, 1e-3)


gain = (masked_blur(b, known, 18) + 2) / (masked_blur(a, known, 18) + 2)
fillv = np.clip(a * gain, 0, 255)
soft = np.asarray(Image.fromarray((hole * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)),
                  dtype=np.float32)[..., None] / 255
# where S17 v8 shows the brick wall (game x < 1362, y < 718) its pixels are no asphalt: those hole pixels are filled
# by harmonic (diffusion) inpainting instead, AFTER the clone has replaced the dashes around them (clean boundary)
wx, wy = g2m(1362, 718)
zone = np.zeros(hole.shape, dtype=bool)
zone[:int(wy), :int(wx)] = True
zh = (hole > 0.02) & zone
soft_out = soft * (~zh)[..., None]
b = b * (1 - soft_out) + fillv * soft_out
if zh.any():
    ys, xs = np.where(zh)
    yy0, yy1, xx0, xx1 = ys.min() - 6, ys.max() + 7, xs.min() - 6, xs.max() + 7
    sub = b[yy0:yy1, xx0:xx1].copy()
    hm = zh[yy0:yy1, xx0:xx1]
    for _ in range(1500):
        q = np.pad(sub, ((1, 1), (1, 1), (0, 0)), mode="edge")
        avg = (q[:-2, 1:-1] + q[2:, 1:-1] + q[1:-1, :-2] + q[1:-1, 2:]) / 4
        sub[hm] = avg[hm]
    sub[hm] += np.random.default_rng(5).normal(0, 3, sub[hm].shape)
    b[yy0:yy1, xx0:xx1] = sub

# 2. paint five transverse stripes
lum = b.mean(-1)
ref = np.asarray(Image.fromarray(lum.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(40)), dtype=np.float32)
rel = np.clip(lum / np.maximum(ref, 1), 0.55, 1.35)[..., None]
paint = np.array([238, 204, 52], dtype=np.float32)
mask = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(mask)
stripes = []
for X in (-2.6, -1.2, 0.2, 1.6, 3.0):
    z0, z1, hw = 6.35, 6.95, 0.06
    quad = [P(X - hw, z1), P(X + hw, z1), P(X + hw, z0), P(X - hw, z0)]
    stripes.append([tuple(round(v) for v in q) for q in quad])
    d.polygon([g2m(*q) for q in quad], fill=255)
mask = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.1)), dtype=np.float32) / 255
rng = np.random.default_rng(55)
noise = np.asarray(Image.fromarray((rng.random((H // 4, W // 4)) * 255).astype(np.uint8)).resize((W, H), Image.Resampling.BILINEAR),
                   dtype=np.float32) / 255
wear = np.clip(0.55 + 0.6 * noise, 0, 1) * 0.88
alpha = (mask * wear)[..., None]
b = b * (1 - alpha) + np.clip(paint * rel, 0, 255) * alpha

out = Image.fromarray(b.clip(0, 255).astype(np.uint8))
out.save(M / f"S55_v{dst_v}.png")
meta = json.loads((M / f"S55_v{src_v}.json").read_text(encoding="utf-8"))
meta.update({"version": dst_v, "kind": "retouch", "usd": 0, "from_version": src_v,
             "retouch": "free pixel retouch (art/masters/bg_natural/S55_scripts/retouch_s55_markings.py): the derive's "
                        "diagonal dashed line removed (S17 v8 asphalt, same camera, tone-matched) and five short transverse "
                        f"yellow distance stripes painted at y ~738-790 (game quads {stripes})"})
meta.pop("exported", None)
(M / f"S55_v{dst_v}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
sys.path.insert(0, str(ROOT / "art" / "tools"))
import paint_room  # noqa: E402
paint_room.fit_to_frame(out).crop((300, 600, 1920, 1080)).save(Path(sys.argv[3]))
print("wrote", M / f"S55_v{dst_v}.png", "stripes", stripes)
