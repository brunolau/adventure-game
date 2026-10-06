"""Free composite for the S55 after-E10 state (relayout 2026-10-06): S55 BASE (2020) + the linden (crown + trunk), its
grass bed, the bench and the low wall with the 12-stone panel from S17 LINDEN (1995 healthy-linden state, same camera).
Writes S55 v<DST> (kind "composite", usd 0) as the base for one paid fix that ages them to 2020.

    python art/masters/bg_natural/S55_scripts/composite_s55_e10.py BASE LINDEN DST <preview.png>
    (relayout: BASE 10 = S55 v10, LINDEN 9 = S17 v9, DST 11)
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(r"C:\Users\klatt\Desktop\adventura")
sys.path.insert(0, str(ROOT / "art" / "tools"))
import paint_room  # noqa: E402

M = ROOT / "art/masters/bg_natural"
K = 1536 / 1080          # master px per game px
CROP = 7                 # fit_to_frame crops 7 game px on the left


def g2m(x, y):
    return ((x + CROP) * K, y * K)


base_v, linden_v, dst_v = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
s55 = Image.open(M / f"S55_v{base_v}.png").convert("RGB")
s17 = Image.open(M / f"S17_v{linden_v}.png").convert("RGB")
W, H = s55.size
mask = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(mask)
# crown: green leaves of the S17 healthy crown inside its fix box, above the lawn line
arr = np.asarray(s17, dtype=np.float32) / 255
r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
mx, mn = arr.max(-1), arr.min(-1)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
greenish = (g >= r * 0.95) & (g > b * 1.15) & (sat > 0.25)
x0, y0 = g2m(410, 0)
x1, y1 = g2m(970, 452)
crown = np.zeros((H, W), dtype=bool)
crown[int(y0):int(y1), int(x0):int(x1)] = greenish[int(y0):int(y1), int(x0):int(x1)]
crown_img = Image.fromarray((crown * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
mask.paste(255, (0, 0), crown_img)
# trunk and main limbs below the crown
d.polygon([g2m(*p) for p in [(598, 300), (648, 300), (646, 700), (596, 700)]], fill=255)
# grass bed with kerb, bench, wall with coping and panel (+ their shadows on the asphalt)
d.polygon([g2m(*p) for p in [(432, 652), (812, 652), (830, 722), (424, 722)]], fill=255)
d.rectangle([g2m(680, 572), g2m(944, 720)], fill=255)
d.rectangle([g2m(944, 530), g2m(1342, 722)], fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(3))
out = Image.composite(s17, s55, mask)
out.save(M / f"S55_v{dst_v}.png")
meta = json.loads((M / f"S55_v{base_v}.json").read_text(encoding="utf-8"))
meta.update({"version": dst_v, "kind": "composite", "usd": 0, "from_version": base_v,
             "composite": f"free composite (art/masters/bg_natural/S55_scripts/composite_s55_e10.py): S55 v{base_v} + linden "
                          f"crown (hue mask), trunk, grass bed, bench and low wall cut from S17 v{linden_v} (same L_YARD "
                          "camera) - base for the E10 ageing fix"})
meta.pop("exported", None)
(M / f"S55_v{dst_v}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
paint_room.fit_to_frame(out).save(Path(sys.argv[4]))
print("ok")
