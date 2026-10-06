"""S03 wooden grasshopper (owner answer 2026-10-06): one paid local edit guided by a flat placeholder silhouette.

The first try (v4, plain instruction) painted a grasshopper ~220 px long that ran behind the shelter post into the left
bay, so the region cut it in half. Here image 1 is the accepted master with a flat-colour placeholder silhouette drawn
into the gap between the play tower and the shelter's front-left post (the sketch-mode trick that fixed S03 v2); the
model output is composited onto the CLEAN master with the spec's region / protect masks (podlubie_fix.composite), so
everything outside the gap (and the slide, stone, post and roof inside it) stays pixel-identical.

  python -X utf8 grasshopper_placeholder.py preview 3          (free: writes the placeholder image + a zoom)
  python -X utf8 grasshopper_placeholder.py run 3 [--seed N]   (USD 0.15)
  python -X utf8 grasshopper_placeholder.py recomposite 3 --raw <raw.png>   (free)
"""
from __future__ import annotations

import argparse
import datetime
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(r"C:\Users\klatt\Desktop\adventura")
sys.path.insert(0, str(ROOT / "art" / "tools"))
sys.path.insert(0, str(ROOT / "art" / "masters" / "bg_natural" / "S17_scripts"))
import paint_natural  # noqa: E402

paint_natural.install()
import fal_api  # noqa: E402
import paint_room as pr  # noqa: E402
import refit_room as rr  # noqa: E402
import podlubie_fix as pf  # noqa: E402

SPEC = "art/masters/bg_natural/S03_scripts/grasshopper.json"
INSTR = ROOT / "art/masters/bg_natural/S03_scripts/grasshopper_placeholder.txt"
WOOD, GREEN, DARK, WHITE = (196, 136, 66), (112, 164, 58), (40, 30, 20), (250, 248, 240)


def M(x, y):
    return rr.to_master(x, y)


def draw_placeholder(master: Image.Image) -> Image.Image:
    """Side-on grasshopper facing left, knee of the hind leg above its back; game x 166-258, y 384-590 (inside the gap)."""
    img = master.copy()
    d = ImageDraw.Draw(img)

    def line(pts, col, w):
        d.line([M(*p) for p in pts], fill=col, width=round(w / rr.K), joint="curve")

    def poly(pts, col):
        d.polygon([M(*p) for p in pts], fill=col)

    def disc(x, y, r, col):
        (cx, cy), rr_ = M(x, y), r / rr.K
        d.ellipse((cx - rr_, cy - rr_, cx + rr_, cy + rr_), fill=col)

    line([(214, 498), (210, 588)], WOOD, 7)                     # middle leg (its foot behind the slide)
    line([(198, 486), (182, 532), (184, 586)], WOOD, 7)         # front leg (behind the slide and the stone)
    poly([(198, 462), (210, 458), (256, 494), (254, 512), (246, 514)], WOOD)  # body beam, rising to the head
    poly([(220, 506), (232, 494), (254, 446), (258, 452), (246, 500), (236, 514)], GREEN)  # thick hind thigh, knee up
    line([(254, 450), (240, 590)], WOOD, 6)                     # hind shin down to the ground
    poly([(166, 452), (202, 444), (208, 484), (172, 494)], GREEN)  # box head
    disc(180, 456, 8, WHITE); disc(197, 452, 8, WHITE)          # big eyes
    disc(177, 458, 3.5, DARK); disc(194, 454, 3.5, DARK)
    line([(180, 446), (174, 418), (168, 386)], DARK, 2.5)       # antennae
    line([(194, 444), (200, 414), (206, 384)], DARK, 2.5)
    # the slide, the standing stone, the post and the roof stay in front: paste the original back over them
    _, protect = pf.build_mask(pf.load_spec(SPEC), master)
    img = Image.composite(master, img, protect)
    return img


def zoom(img: Image.Image, path: Path) -> None:
    (x0, y0), (x1, y1) = M(110, 340), M(320, 640)
    img.crop((round(x0), round(y0), round(x1), round(y1))).resize((round((x1 - x0) * 1.6), round((y1 - y0) * 1.6))).save(path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["preview", "run", "recomposite"])
    ap.add_argument("version", type=int)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--raw")
    ap.add_argument("--budget", type=float, default=0.45)
    ap.add_argument("--scope", default="bg_natural/S03_grasshopper/")
    args = ap.parse_args()
    spec = pf.load_spec(SPEC)
    master, meta = rr.load_master("S03", args.version)
    guide = draw_placeholder(master)
    guide_path = pr.MASTERS / f"S03_v{args.version}_grasshopper_placeholder.png"
    guide.save(guide_path)
    if args.cmd == "preview":
        zoom(guide, ROOT / "art/review/natural/S03_grasshopper_placeholder_zoom.png")
        print(guide_path)
        return
    instruction = INSTR.read_text(encoding="utf-8").strip()
    prompt = pf.PROMPT_HEAD + instruction + " " + pr.style_sentence()
    seed = args.seed if args.seed is not None else random.randint(1, 2**31 - 1)
    hint = pr.next_version("S03")
    if args.cmd == "run":
        asset = f"{args.scope}S03_v{hint}_grasshopper"
        images = [fal_api.image_data_uri(guide, fmt="PNG"),
                  fal_api.image_data_uri(ROOT / spec["style"], max_side=1376, fmt="JPEG")]
        result, raw_path, raw = rr.call_edit(prompt, images, seed, asset, args)
        usd = fal_api.IMAGE_PRICES[(pr.MODEL, pr.RESOLUTION)]
    else:
        raw_path = ROOT / args.raw
        result = Image.open(raw_path).convert("RGB").resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
        raw, asset, usd = {"seed": None}, "", 0.0
    final, drift, _, _ = pf.composite(spec, master, result, None)
    rr.save_version("S03", final, {
        "kind": "fix" if usd else "recomposite", "tool": "S03_scripts/grasshopper_placeholder.py",
        "from_version": args.version, "spec": SPEC, "regions_game_px": spec["regions"],
        "protect_game_px": spec.get("protect", []), "instruction": instruction,
        "drift_compensated_master_px": list(drift), "model": pr.MODEL,
        "seed": raw.get("seed", seed) if usd else None, "usd": usd, "scope": args.scope if usd else "",
        "spend_log_asset": asset, "prompt": prompt,
        "image_urls": [guide_path.relative_to(ROOT).as_posix(), spec["style"]],
        "raw_model_output": Path(raw_path).resolve().relative_to(ROOT).as_posix(),
        "started": datetime.datetime.now().isoformat(timespec="seconds"), "parent_prompt": meta.get("prompt")})


if __name__ == "__main__":
    main()
