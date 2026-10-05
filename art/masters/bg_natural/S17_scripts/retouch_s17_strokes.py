"""Free pixel retouch of S17 v1: the art panel shows 4 black strokes, the clue (look text: TRI VLNY, DVA UDERY,
SEST DIELIKOV) needs exactly two. Cover strokes 3 and 4 with plywood cloned from the blank area to their right.
Writes art/masters/bg_natural/S17_v2.png + sidecar (kind "retouch", usd 0)."""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(r"C:\Users\klatt\Desktop\adventura")
src_v, dst_v = int(sys.argv[1]), int(sys.argv[2])
master = ROOT / f"art/masters/bg_natural/S17_v{src_v}.png"
im = Image.open(master).convert("RGB")
# master px: strokes 3+4 occupy x 479-529, y 718-760; blank plywood right of them x 530-565
src = im.crop((528, 708, 566, 770)).resize((64, 62), Image.Resampling.LANCZOS)
mask = Image.new("L", src.size, 0)
# parallelogram: the left edge follows the gap between stroke 2 and stroke 3 (master (488,712) -> (476,766))
ImageDraw.Draw(mask).polygon([(488 - 474, 4), (src.width - 4, 4), (src.width - 4, src.height - 4), (476 - 474, src.height - 4)], fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(1.6))
out = im.copy()
out.paste(src, (474, 708), mask)
dst = ROOT / f"art/masters/bg_natural/S17_v{dst_v}.png"
out.save(dst)
meta = json.loads(master.with_suffix(".json").read_text(encoding="utf-8"))
meta.update({"version": dst_v, "kind": "retouch", "usd": 0, "from_version": src_v,
             "retouch": "free pixel retouch (scratchpad retouch_s17_strokes.py): art panel strokes 3 and 4 covered with "
                        "plywood cloned from master x 528-566, y 708-770 (stretched to 64x62) pasted at 474,708 through a parallelogram mask along the gap between strokes 2 and 3 - the "
                        "panel now shows exactly three waves, TWO strokes and six pieces (clue 3-2-6)"})
meta.pop("exported", None)
dst.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
c = out.crop((422, 696, 571, 796))
c.resize((c.width * 4, c.height * 4), Image.Resampling.NEAREST).save(Path(sys.argv[3]))
print("wrote", dst)
