"""Free pixel retouch S61 SRC -> DST (relayout 2026-10-06): the hand cart's wheel ruts past the sapling.

The brief needs the cart's track right at the sapling ("Stopa rucneho vozika vedie rovno pri kmeni"). The paid edits
that place the cart correctly (derive v11, fix v12, rut fixes v13 / v15) painted no visible ruts, while the first
derive (v9, rejected: cart in the foreground) painted convincing muddy ruts across the foreground. This transfers that
painted rut TEXTURE: a strip of v9 along its two ruts (game x 1010-1810, sloping ~0.11 px/px) is de-sheared, shrunk to
the depth of the new path (~0.62x: v9 ruts at ~5 m, the new path at ~7.5 m), turned into a high-pass (strip minus
its blur, x1.7) so only the ruts' mud and the slush specks move, and added onto SRC along the path from the cart's
wheel (game ~392, 708) along the front kerb of the sapling's grass bed to ~860 (fading out in front of the bench).

    python art/masters/bg_natural/S61_scripts/retouch_s61_ruts.py SRC DST <preview.png>
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
dst = np.asarray(Image.open(M / f"S61_v{src_v}.png").convert("RGB"), dtype=np.float32).copy()
v9 = np.asarray(Image.open(M / "S61_v9.png").convert("RGB"), dtype=np.float32)

# 1. de-sheared strip of the v9 ruts (game: x 1010-1810, top line y 812 at x 1010 sloping to y 900 at x 1810, 150 high)
gx0, gx1, gy0, slope, gh = 1010, 1810, 812, (900 - 812) / 800, 150
mx0, _ = g2m(gx0, 0)
mx1, _ = g2m(gx1, 0)
cols = []
for mx in range(mx0, mx1):
    gx = mx / K - 7
    top = int(round((gy0 + slope * (gx - gx0)) * K))
    cols.append(v9[top:top + int(gh * K), mx])
strip = np.stack(cols, axis=1)                              # (h, w, 3)
S = Image.fromarray(strip.clip(0, 255).astype(np.uint8))

# 2. shrink to the new depth and to the path length (game 392 -> 862 = 470 px)
tw = int(470 * K)
th = int(gh * K * 0.62 * 0.8)                               # rut spacing shrinks a bit more than the length (depth)
S = S.resize((tw, th), Image.Resampling.LANCZOS)
s = np.asarray(S, dtype=np.float32)
blur = np.asarray(S.filter(ImageFilter.GaussianBlur(14)), dtype=np.float32)
delta = (s - blur) * 1.7                                    # high-pass: mud darker and browner, slush specks lighter
luma_r = 1 + delta.mean(-1, keepdims=True) / 100.0

# 3. masks: only where the strip deviates (ruts, specks), faded at both ends, soft top/bottom
dev = np.abs(luma_r[..., 0] - 1)
m = np.clip((dev - 0.03) / 0.08, 0, 1)
m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float32) / 255
xx = np.linspace(0, 1, tw)[None, :]
ends = np.clip(xx / 0.05, 0, 1) * np.clip((1 - xx) / 0.35, 0, 1)
yy = np.linspace(0, 1, th)[:, None]
edge = np.clip(yy / 0.12, 0, 1) * np.clip((1 - yy) / 0.12, 0, 1)
m = (m * ends * edge)[..., None]

# 4. paste along the path: top-left at game (392, 698), slight downward slope (~10 px over the length)
px0, py0 = g2m(392, 698)
for i in range(tw):
    y = py0 + int(round(10 * K * i / tw))
    region = dst[y:y + th, px0 + i]
    a = m[:, i]
    dst[y:y + th, px0 + i] = region + delta[:, i] * a

out = Image.fromarray(dst.clip(0, 255).astype(np.uint8))
out.save(M / f"S61_v{dst_v}.png")
meta = json.loads((M / f"S61_v{src_v}.json").read_text(encoding="utf-8"))
meta.update({"version": dst_v, "kind": "retouch", "usd": 0, "from_version": src_v,
             "retouch": "free pixel retouch (art/masters/bg_natural/S61_scripts/retouch_s61_ruts.py): the painted rut texture "
                        "of S61 v9 (game x 1010-1810 along its ruts, de-sheared, shrunk 0.62x, high-pass x1.7) added "
                        "onto the path from the hand cart's wheel (game ~392,708) along the front kerb of the sapling's bed, "
                        "fading out in front of the bench"})
meta.pop("exported", None)
(M / f"S61_v{dst_v}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
sys.path.insert(0, str(ROOT / "art" / "tools"))
import paint_room  # noqa: E402
fr = paint_room.fit_to_frame(out).crop((150, 520, 980, 840))
fr.save(Path(sys.argv[3]))
print("wrote", M / f"S61_v{dst_v}.png", "strip", strip.shape, "->", (th, tw))
