"""Free retouch S61 v4 -> v6: remove the loose stone that the closed-niche fix left lying on the coping (it is back in
the panel). Clone the coping top + lawn/track background from the right (master x 1786-1874, y 742-775) over it."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
ROOT = Path(r"C:\Users\klatt\Desktop\adventura")
M = ROOT / "art/masters/bg_natural"
im = Image.open(M / "S61_v4.png").convert("RGB")
src = im.crop((1588, 744, 1694, 775))
mask = Image.new("L", src.size, 0)
ImageDraw.Draw(mask).rectangle((5, 3, src.width - 6, src.height - 4), fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(2))
out = im.copy()
out.paste(src, (1690, 744), mask)
out.save(M / "S61_v6.png")
meta = json.loads((M / "S61_v4.json").read_text(encoding="utf-8"))
meta.update({"version": 6, "kind": "retouch", "usd": 0, "from_version": 4,
             "retouch": "free pixel retouch: the loose stone left on the wall coping by the v4 closed-niche fix is covered "
                        "with coping/lawn/track pixels cloned from master x 1588-1694, y 744-775 (pasted at 1690,744, soft "
                        "mask) - closed-niche state: all 12 stones in the panel, nothing on the coping"})
(M / "S61_v6.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
c = out.crop((1517, 718, 1922, 796))
c.resize((c.width * 3, c.height * 3), Image.NEAREST).save(r"C:\Users\klatt\AppData\Local\Temp\claude\C--Users-klatt\9df75bbe-8a3f-41a0-b478-5b6746711c17\scratchpad\S61_coping_v6.png")
print("ok")
