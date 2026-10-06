"""Free pixel retouch of the relayout S17 painting (2026-10-06): SRC -> DST.

1. Art panel: the painting shows the two straight black strokes plus two extra curved black strokes; the clue (look
   text: TRI VLNY, DVA UDERY, SEST DIELIKOV) needs exactly two. The curved strokes (master x 478-575, y 712-770,
   game ~330-397 x 500-541) are removed: their dark pixels (grown by 3 px) are filled by harmonic (diffusion)
   inpainting from the surrounding plywood, plus a little plywood grain noise.
2. Service wall: the painting shows the inset panel as ONE grey slab; the story needs a 3 x 4 grid of stones (S61 niche
   row 2 / column 3, S55 cache). The wall stands at the same game position as in the first S17 painting (S17 v2), so
   the 12-stone panel of S17 v2 (inside its frame, game 1080-1233 x 574-680) is pasted in, tone-matched to the new
   painting (per-channel gain = new slab mean / old panel mean), feathered 2 px.

    python art/masters/bg_natural/S17_scripts/retouch_s17_relayout.py SRC DST <preview.png>
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
im = Image.open(M / f"S17_v{src_v}.png").convert("RGB")
arr = np.asarray(im, dtype=np.float32).copy()

# 1. curved strokes on the art panel
x0, y0, x1, y1 = 478, 712, 575, 770
reg = arr[y0:y1, x0:x1]
luma = reg @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
dark = luma < 120
m = Image.fromarray((dark * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))
hole = np.asarray(m) > 0
fill = reg.copy()
known = ~hole
mean = reg[known].mean(0)
fill[hole] = mean
for _ in range(1500):
    p = np.pad(fill, ((1, 1), (1, 1), (0, 0)), mode="edge")
    avg = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]) / 4
    fill[hole] = avg[hole]
rng = np.random.default_rng(17)
grain = rng.normal(0, 2.2, fill.shape).astype(np.float32)
fill[hole] += grain[hole]
soft = np.asarray(Image.fromarray((hole * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)),
                  dtype=np.float32)[..., None] / 255
arr[y0:y1, x0:x1] = reg * (1 - soft) + fill * soft

# 2. 12-stone panel from S17 v2
old = np.asarray(Image.open(M / "S17_v2.png").convert("RGB"), dtype=np.float32)
px0, py0 = g2m(1080, 574)
px1, py1 = g2m(1233, 680)
o = old[py0:py1, px0:px1]
n = arr[py0:py1, px0:px1]
gain = n.reshape(-1, 3).mean(0) / o.reshape(-1, 3).mean(0)
o = o * gain[None, None, :]
h, w = o.shape[:2]
mask = np.zeros((h, w), np.uint8)
mask[2:-2, 2:-2] = 255
mask = np.asarray(Image.fromarray(mask).filter(ImageFilter.GaussianBlur(1.5)), dtype=np.float32)[..., None] / 255
arr[py0:py1, px0:px1] = n * (1 - mask) + o * mask

out = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
out.save(M / f"S17_v{dst_v}.png")
meta = json.loads((M / f"S17_v{src_v}.json").read_text(encoding="utf-8"))
meta.update({"version": dst_v, "kind": "retouch", "usd": 0, "from_version": src_v,
             "retouch": "free pixel retouch (art/masters/bg_natural/S17_scripts/retouch_s17_relayout.py): the two extra "
                        "curved black strokes on the art panel inpainted (panel = 3 waves, 2 strokes, 6 pieces); the "
                        "12-stone panel of S17 v2 (same wall position, game 1080-1233 x 574-680) pasted into the plain "
                        f"slab of the service wall, tone gain {', '.join(f'{g:.3f}' for g in gain)}"})
meta.pop("exported", None)
(M / f"S17_v{dst_v}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
sys.path.insert(0, str(ROOT / "art" / "tools"))
import paint_room  # noqa: E402
fr = paint_room.fit_to_frame(out)
a = fr.crop((190, 430, 410, 640)).resize((440, 420))
b = fr.crop((1040, 530, 1440, 720)).resize((800, 380))
prev = Image.new("RGB", (1250, 420), "white")
prev.paste(a, (0, 0))
prev.paste(b, (450, 20))
prev.save(Path(sys.argv[3]))
print("wrote", M / f"S17_v{dst_v}.png", "gain", gain)
