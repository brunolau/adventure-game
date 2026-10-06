"""S62 painter "sokolikova-street" (2026-10-06): step A of the two-step S62 = ONE derive_era edit of the S18 master that
changes only season, light and vehicles (December 1982 dusk, snow, bare tree, lit windows, a period car) and KEEPS the
kiosk as it is. The positioning guide (image 2) therefore shows the S18 blocking (the kiosk's panes and hatch), not the
S62 one; the era text is art/prompts/natural/S62.winter.era.txt (placeholders refer to S18 ids). Step B turns the kiosk
into the 1982 shop with a local `refit fix` on the result.

Why not one derive: v2 painted the shop over the near block on the right, v3 re-composed the whole scene (shop 1.8x too
big, car moved, red parapets gone). This is the 4th whole-picture attempt for S62 (cap raised with this reason in
art/masters/bg_natural/S62.md). Output: art/masters/bg_natural/S62_v<N>.png + sidecar (kind "derive", counted),
art/review/natural/S62_v<N>_derive.png (camera measure against the S18 base), no export.

Run: PYTHONIOENCODING=utf-8 python -X utf8 art/masters/bg_natural/S62_scripts/winter_derive.py --from 6 --budget 3.0 [--seed N]
"""
from __future__ import annotations

import argparse
import datetime
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "art" / "tools"))
import derive_era  # noqa: E402
import fal_api  # noqa: E402
import paint_natural  # noqa: E402
import paint_room  # noqa: E402

SCOPE = "bg_natural/sokolikova_street/"
ERA_FILE = ROOT / "art" / "prompts" / "natural" / "S62.winter.era.txt"
CAP = 4   # raised from 3, reason in art/masters/bg_natural/S62.md


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="source", type=int, required=True)
    ap.add_argument("--budget", type=float, required=True)
    ap.add_argument("--seed", type=int)
    args = ap.parse_args()
    if paint_natural.paid_attempts("S62") >= CAP:
        sys.exit(f"S62: {CAP} whole-picture attempts already")
    derive_era.check_pair = lambda base, target, test: None
    derive_era.ERA_FILE_OVERRIDE = ERA_FILE
    # guide + placeholders from the S18 blocking (the kiosk stays), era text from the S62 winter file
    job = derive_era.assemble("S18", "S18", args.source, False)
    job["prompt"] = job["prompt"].replace("Sídliskový dvor s kioskom in 1995", "a street of the Dubravka housing estate in "
                                          "Bratislava in 1995").replace("the SAME PLACE in 1995", "the SAME PLACE in December 1982")
    version = paint_room.next_version("S62")
    stem = f"S62_v{version}"
    seed = args.seed if args.seed is not None else random.randint(1, 2 ** 31 - 1)
    arguments = {"prompt": job["prompt"],
                 "image_urls": [fal_api.image_data_uri(job["base_img"], fmt="PNG"),
                                fal_api.image_data_uri(job["guide"], max_side=2048, fmt="JPEG")],
                 "aspect_ratio": paint_room.ASPECT, "resolution": paint_room.RESOLUTION, "output_format": "png",
                 "num_images": 1, "seed": seed}
    price = fal_api.IMAGE_PRICES[(paint_room.MODEL, paint_room.RESOLUTION)]
    asset = f"{SCOPE}{stem}_derive"
    started = datetime.datetime.now().isoformat(timespec="seconds")
    result = fal_api.run(paint_room.MODEL, arguments, asset, price, budget=(SCOPE, args.budget), timeout_s=900)
    raw = paint_room.MASTERS / f"_{stem}_raw.png"
    fal_api.download(result["images"][0]["url"], raw)
    derived = derive_era.as_model(Image.open(raw))
    report = derive_era.measure(derived, job["base_img"], job["room"], job["anchors"])
    gx, gy = report["global_shift_master_px"]
    if (gx or gy) and max(abs(gx), abs(gy)) <= derive_era.GLOBAL_COMPENSATE:
        derived = ImageChops.offset(derived, -gx, -gy)
        report = dict(derive_era.measure(derived, job["base_img"], job["room"], job["anchors"]),
                      compensated_master_px=[gx, gy])
    out = paint_room.MASTERS / f"{stem}.png"
    derived.save(out)
    meta = {"room": "S62", "version": version, "kind": "derive", "step": "A (winter only, kiosk kept)",
            "from_room": "S18", "from_version": args.source,
            "from_master": job["base_path"].relative_to(ROOT).as_posix(), "model": paint_room.MODEL,
            "resolution": paint_room.RESOLUTION, "aspect_ratio": paint_room.ASPECT, "seed": result.get("seed", seed),
            "usd": price, "scope": SCOPE, "spend_log_asset": asset, "started": started,
            "prompt_file": ERA_FILE.relative_to(ROOT).as_posix(), "prompt": job["prompt"],
            "image_urls": [job["base_path"].relative_to(ROOT).as_posix() + " (model geometry)",
                           f"{job['base_path'].name} + S18 blocking boxes (guide: the kiosk stays)"],
            "camera": report, "model_description": result.get("description"),
            "raw_model_output": raw.relative_to(ROOT).as_posix(), "output_size": list(derived.size),
            "script": "art/masters/bg_natural/S62_scripts/winter_derive.py"}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    review = derive_era.derive_review(derived, job["base_img"], job["room"], job["anchors"], report,
                                      ROOT / "art" / "review" / "natural" / f"{stem}_derive.png")
    print(f"{out.relative_to(ROOT)} ${price:.2f} (scope {SCOPE} spent {fal_api.logged_spend(SCOPE):.2f})")
    derive_era.print_report(report)
    print(f"review: {review.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
