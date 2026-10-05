"""Free composite S66 v1 + raw of the v2 fix -> v4: the raw (block one storey lower) is used for everything above the
fence top rail (y 452) except the shed, whose roof silhouette from v1 stays in front; seams along the fence rail and the
shed roof outline (strong edges)."""
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(r"C:\Users\klatt\Desktop\adventura")
sys.path.insert(0, str(ROOT / "art" / "tools"))
import paint_room  # noqa: E402
import refit_room as rf  # noqa: E402

M = ROOT / "art/masters/bg_natural"
K = 1536 / 1080


def g(x, y):
    return ((x + 7) * K, y * K)


base = Image.open(M / "S66_v1.png").convert("RGB")
raw = Image.open(M / "_bg_natural_S66_S66_v2_fix_raw.png").convert("RGB").resize(base.size, Image.Resampling.LANCZOS)
outside = Image.new("L", base.size, 255)
ImageDraw.Draw(outside).rectangle((*g(0, 0), *g(1920, 460)), fill=0)
dx, dy = rf.align_shift(raw, base, outside)
if dx or dy:
    raw = ImageChops.offset(raw, -dx, -dy)
mask = Image.new("L", base.size, 0)
d = ImageDraw.Draw(mask)
d.rectangle((*g(0, 0), *g(1920, 450)), fill=255)
# keep the v1 shed (roof slab with snow, stovepipe, walls) in front
d.polygon([g(*p) for p in [(876, 302), (1640, 302), (1660, 340), (1660, 460), (876, 460)]], fill=0)
d.rectangle((*g(1470, 240), *g(1505, 310)), fill=0)
mask = mask.filter(ImageFilter.GaussianBlur(6))
out = Image.composite(raw, base, mask)
out.save(M / "S66_v4.png")
meta = json.loads((M / "S66_v1.json").read_text(encoding="utf-8"))
meta.update({"version": 4, "kind": "composite", "usd": 0, "from_version": 1, "drift_compensated_master_px": [dx, dy],
             "composite": "free composite (scratchpad composite_s66_block.py): raw of the v2 fix (Kudlakova 2 block one storey "
                          "lower) above the fence rail y 450, the v1 shed kept in front (mask along its roof outline)"})
meta.pop("exported", None)
(M / "S66_v4.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
paint_room.fit_to_frame(out).save(sys.argv[1])
print("ok", dx, dy)
