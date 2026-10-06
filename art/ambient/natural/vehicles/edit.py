"""Paid edits for the living-scene vehicles (S11 tramless base, S51 modern tram, S21 / S57 vehicles).

One nano-banana-pro/edit call per job (USD 0.15 at 2K), logged to art/spend-log.csv with scope
'ambient/vehicles/' (cap 6 USD for the living-scene polish, 2026-10-05). Outputs land in
art/ambient/natural/vehicles/<job>_raw.png (model frame 2752x1536) + <job>.json (prompt, seed, cost).

  python art/ambient/natural/vehicles/edit.py <job> [--seed N]
"""
from __future__ import annotations

import argparse
import datetime
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "art" / "tools"))
import fal_api  # noqa: E402

MODEL = "fal-ai/nano-banana-pro/edit"
SCOPE = ("ambient/vehicles/", 6.00)
MASTERS = ROOT / "art" / "masters" / "bg_natural"

KEEP = ("Keep everything else in the picture exactly as it is, pixel for pixel where possible: the same camera, "
        "framing, horizon and perspective, the same brushwork, palette, lighting and shadows, and every other object "
        "at exactly the same place and size. Do not add anything that is not asked for: no people, no animals, no "
        "text, no logos, no signs, no number plates.")

JOBS: dict[str, dict] = {
    "S11_notram": {
        # 2026-10-06: the redesigned S11 (owner Dubravka corrections, master v3); v1 of this job used S11_v1.
        "images": [MASTERS / "S11_v3.png"],
        "prompt": (
            "This is a finished hand-painted adventure-game background of a tram stop in a 1980s housing estate. "
            "Remove the red-and-cream tram that stands on the near track at the right of the platform: remove the "
            "whole tram body, its roof pantograph, its mirror and coupler and the shadow it casts. Paint what is "
            "behind it so the place reads as an empty tram stop with no vehicle: the double tram track with its "
            "grooved rails set into big grey concrete panels (grass in the joints) continuing straight ahead and "
            "then gently uphill in the same perspective as the visible near part of the track, the light edge strip "
            "of the platform continuing along the track, the red steel-tube railing beyond the tracks, the east "
            "carriageway, the long low bluish two-storey medical centre with its white ribbon windows and its "
            "blue-grey mosaic tiles continuing to the left behind where the tram was, the long panel block with "
            "red-orange balconies above it, the tall rust-red lamp posts, the overhead contact wires continuing at "
            "the same height and angle as the wires that are already visible, the trees, and the blue morning sky. "
            + KEEP),
    },
    "S51_tram": {
        # 2026-10-06: the redesigned S51 (master v3). v3 of this job (with the S11 v3 tram painting as image 2) copied
        # the 1995 concrete-panel track bed around the tram, so v4 sends only the S51 painting and gives the place in
        # coordinates (the T3's place in S11 v3: front x 1111-1398, y 304-628).
        "images": [MASTERS / "S51_v3.png"],
        "prompt": (
            "This is a finished hand-painted adventure-game background of a tram stop in Bratislava in late October "
            "2020, afternoon sun low at the right behind the camera. Add ONE modern low-floor city tram standing on "
            "the near track (the track right next to the platform, on the right of the tactile strip), doors closed, "
            "its front facing the camera: its front face covers x 1110-1400 and y 300-630 of the 1920x1080 frame, "
            "the bottom of its front stands on the near track between its two rails, and its left side runs along "
            "the platform edge, receding along the rails towards the far end of the platform. It stands ON the "
            "existing track: keep the grey ballast, the concrete sleepers, the rails, the green steel mesh fence "
            "between the tracks (hidden only where the tram stands in front of it) and the far track exactly as "
            "they are painted; do not change the track bed anywhere. The new tram is a long articulated modern "
            "tram of the kind Bratislava runs today: a large curved one-piece windscreen, slim LED headlights, a "
            "red front and red lower body, light silver-grey upper sides with long dark tinted side windows, and a "
            "single-arm pantograph on the roof raised against the overhead contact wire. Completely unbranded: no "
            "emblem, badge or logo on the front or anywhere, no fleet numbers, no route number, no destination "
            "text (the destination display is dark and blank), no advertising; no driver or passengers visible "
            "(the windows reflect the sky). It casts a soft shadow onto the platform at its left. " + KEEP),
    },
    "T3_side": {
        "images": ["S11_tram_crop"],
        "aspect": "21:9",
        "prompt": (
            "Image 1 is a red-cream Tatra T3 tram cut from a finished painting of our hand-painted adventure game "
            "(seen in three-quarter front view). Paint ONE single Tatra T3 tram car of the same kind, livery and "
            "painting style as a game sprite, in an exact side view (the camera perfectly perpendicular to the side, "
            "no perspective), facing right, the whole tram visible with a wide empty margin on every side: the long "
            "boxy body with rounded front and rear ends, cream roof and cream band around the windows, red lower body "
            "below the windows, a long row of passenger windows with dark glass softly reflecting the sky, three "
            "pairs of folding doors in the side, a small round headlight at the front end, the diamond (scissor) "
            "pantograph raised high above the roof, the two bogies with their wheels at the bottom, the bottom edge "
            "of the wheels perfectly level. Soft warm morning light from the upper left, painterly brushwork, a thin "
            "darker outline. The route box is blank. No text, no numbers, no logos, no advertising, no people, no "
            "rails, no ground, no shadow. Background: one perfectly flat, uniform, pure chroma-key green (#00FF00) "
            "filling the entire image, edge to edge, with no gradient, no texture, no ground, no cast shadow and no "
            "vignette; the tram has crisp clean edges against the green, with no green tint, glow or reflection on "
            "it."),
    },
}


def load_image(ref):
    """A path, or a named crop of our own paintings (never the owner's reference photos)."""
    from PIL import Image
    if ref == "S11_tram_crop":
        return Image.open(MASTERS / "S11_v1.png").convert("RGB").crop((1640, 110, 2310, 920))
    return Image.open(ref).convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("job", choices=sorted(JOBS))
    ap.add_argument("--seed", type=int)
    args = ap.parse_args()
    job = JOBS[args.job]
    seed = args.seed if args.seed is not None else random.randint(1, 2 ** 31 - 1)
    images = [load_image(p) for p in job["images"]]
    arguments = {"prompt": job["prompt"],
                 "image_urls": [fal_api.image_data_uri(p, fmt="PNG") for p in images],
                 "aspect_ratio": job.get("aspect", "16:9"), "resolution": "2K", "output_format": "png", "num_images": 1, "seed": seed}
    price = fal_api.IMAGE_PRICES[(MODEL, "2K")]
    asset = f"{SCOPE[0]}{args.job}"
    started = datetime.datetime.now().isoformat(timespec="seconds")
    result = fal_api.run(MODEL, arguments, asset, price, budget=SCOPE, timeout_s=900)
    n = 1
    while (HERE / f"{args.job}_v{n}_raw.png").exists():
        n += 1
    raw = HERE / f"{args.job}_v{n}_raw.png"
    fal_api.download(result["images"][0]["url"], raw)
    meta = {"job": args.job, "version": n, "model": MODEL, "resolution": "2K", "seed": result.get("seed", seed),
            "usd": price, "started": started, "spend_log_asset": asset,
            "images": [str(p) if isinstance(p, str) else p.relative_to(ROOT).as_posix() for p in job["images"]],
            "prompt": job["prompt"],
            "description": result.get("description")}
    raw.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{raw.relative_to(ROOT)} USD {price:.2f}; scope spent {fal_api.logged_spend(SCOPE[0]):.2f} of {SCOPE[1]:.2f}")


if __name__ == "__main__":
    main()
