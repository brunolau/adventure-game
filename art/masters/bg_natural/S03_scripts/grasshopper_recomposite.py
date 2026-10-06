"""Free re-composite of the S03 grasshopper from the raw output of the paid v4 edit (owner answer 2026-10-06).

v4 (podlubie_fix.py run with grasshopper.json) painted a good wooden grasshopper, but larger than the gap it was asked
for: it stands on the meadow behind the play tower's slide and the shelter's left bay, its body passing behind the
front-left post and its rear behind the left table's paper bags. The rectangular region of v4 cut it in half. Here the
figure is taken from the same raw output by its own outline instead: pixels where the raw differs strongly from the
accepted master v3 (the new figure), inside a loose box around it, minus the objects that stand in front of it in v3
(slide, standing stone, shelter post, left table with its bags, roof), which are pasted back from v3. Everything else
is v3, pixel-identical.

  python -X utf8 grasshopper_recomposite.py <raw.png> [--preview out.png]     -> next S03 master version (free)
"""
from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(r"C:\Users\klatt\Desktop\adventura")
sys.path.insert(0, str(ROOT / "art" / "tools"))
sys.path.insert(0, str(ROOT / "art" / "masters" / "bg_natural" / "S17_scripts"))
import paint_natural  # noqa: E402

paint_natural.install()
import paint_room as pr  # noqa: E402
import refit_room as rr  # noqa: E402
import podlubie_fix as pf  # noqa: E402

BASE = 3
THRESH = 40            # max-channel difference (0-255) that counts as "new figure"
# loose area around the figure (game px): the gap right of the tower and the shelter's left bay above the bags
AREA = [[150, 336], [268, 336], [268, 372], [440, 372], [440, 600], [150, 600]]
# objects in front of the figure in v3 (game px), pasted back from v3
FRONT = {
    "front-left post": [[257, 360], [299, 360], [299, 700], [257, 700]],
    "post brace": [[296, 372], [345, 372], [300, 432]],
    "left table and bags": [[338, 492], [470, 486], [470, 640], [338, 640]],
    "back post": [[422, 372], [446, 372], [446, 640], [422, 640]],
    "roof": [[150, 300], [700, 300], [700, 373], [205, 373]],
    "standing stone": [[150, 690], [138, 600], [140, 560], [158, 543], [182, 540], [198, 556], [204, 610], [200, 690]],
}


def poly_mask(size, pts_game):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon([rr.to_master(*p) for p in pts_game], fill=255)
    return m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw")
    ap.add_argument("--preview")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    master, meta = rr.load_master("S03", BASE)
    raw = Image.open(ROOT / args.raw).convert("RGB").resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    size = pr.MODEL_FRAME
    a = np.asarray(raw, dtype=np.int16)
    b = np.asarray(master, dtype=np.int16)
    diff = Image.fromarray(np.abs(a - b).max(axis=2).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))
    fig = (np.asarray(diff) > THRESH) & (np.asarray(poly_mask(size, AREA)) > 0)
    m = Image.fromarray((fig * 255).astype(np.uint8))
    # close small gaps inside the figure (wood grain close to the field colours), then drop specks
    m = m.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7))
    m = m.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    import frames  # noqa: E402  (art/tools)
    labels, sizes = frames.label_components(np.asarray(m) > 0)
    keep = np.zeros_like(labels, dtype=bool)
    for i, s in enumerate(sizes, start=1):
        if s >= 1500:
            keep |= labels == i
    m = Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
    front = Image.new("L", size, 0)
    for pts in FRONT.values():
        front = Image.fromarray(np.maximum(np.asarray(front), np.asarray(poly_mask(size, pts))))
    # the green slide by its own pixels (as in grasshopper.json)
    spec = pf.load_spec("art/masters/bg_natural/S03_scripts/grasshopper.json")
    _, slide = pf.build_mask({"regions": [], "protect": [spec["protect"][0]], "protect_feather": 0}, master)
    front = Image.fromarray(np.maximum(np.asarray(front), np.asarray(slide)))
    take = Image.fromarray(np.where(np.asarray(front) > 0, 0, np.asarray(m)).astype(np.uint8))
    take = take.filter(ImageFilter.GaussianBlur(1.2))
    hard_front = front.filter(ImageFilter.GaussianBlur(0.8))
    final = Image.composite(raw, master, take)
    final = Image.composite(master, final, hard_front)
    if args.preview:
        (x0, y0), (x1, y1) = rr.to_master(120, 330), rr.to_master(660, 660)
        box = tuple(round(v) for v in (x0, y0, x1, y1))
        tint = Image.composite(Image.new("RGB", size, (255, 0, 255)), final, take.point(lambda v: v // 2))
        out = Image.new("RGB", (box[2] - box[0], 2 * (box[3] - box[1])))
        out.paste(final.crop(box), (0, 0))
        out.paste(tint.crop(box), (0, box[3] - box[1]))
        out.save(args.preview)
        print(args.preview)
    if args.dry_run:
        return
    rr.save_version("S03", final, {
        "kind": "recomposite", "tool": "S03_scripts/grasshopper_recomposite.py", "from_version": BASE,
        "raw_model_output": args.raw, "threshold": THRESH, "area_game_px": AREA, "front_game_px": FRONT,
        "usd": 0.0, "scope": "", "seed": None,
        "note": "figure taken from the v4 raw by its difference outline; objects in front pasted back from v3",
        "started": datetime.datetime.now().isoformat(timespec="seconds"), "parent_prompt": meta.get("prompt")})


if __name__ == "__main__":
    main()
