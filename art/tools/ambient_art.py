"""Ambient sprite generation for the LastBell living world (style A) via fal.ai, plus local keying.

Paid subcommands (logged to art/spend-log.csv, budget scope 'ambient/', hard cap 10 USD):
  image <name>                 one sprite sheet on a flat chroma-key background (nano-banana-pro, 1K)
  video <name> --image IMG     image-to-video on the flat key background (Hailuo-02 standard, 6 s)
Free subcommands:
  key <name>                   key a generated sheet and split it into separate sprites (connected components)
  list                         show the asset briefs and the logged ambient spend

Outputs: art/ambient/<name>.png (+ .json sidecar), keyed parts in art/ambient/<name>_parts/.
The shipped sprites are assembled by art/tools/ambient_cut.py into src/game/assets/ambient/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

import fal_api
import frames

ART = fal_api.ART
OUT = ART / "ambient"
BUDGET = ("ambient/", 10.00)
STYLE_REF = ART.parent / "src" / "game" / "assets" / "bg" / "S02.webp"

STYLE_A = (
    "Style: classic 1990s hand-painted adventure game background. Rich painterly brushwork, slightly "
    "exaggerated cartoon proportions with gently curved lines, warm late-afternoon sunlight, saturated but "
    "harmonious colours, soft dappled shadows under the trees."
)
STYLE_NOTE = (
    "The LAST reference image is a finished background painting from our game. Use it only as the reference for "
    "the painting technique: brushwork, colour palette, edge softness, level of detail and line quality. Do not "
    "copy anything from its scene into the new image."
)


def key_bg(word: str, hex_code: str) -> str:
    return (f"Background: one perfectly flat, uniform, pure chroma-key {word} ({hex_code}) filling the entire image, "
            "edge to edge, with no gradient, no texture, no ground, no cast shadow, no vignette and no text. Every "
            f"object has crisp clean edges against the {word}, with no {word} tint, glow or reflection on it. "
            "Objects never touch each other or the image border.")


GREEN = key_bg("green", "#00FF00")
MAGENTA = key_bg("magenta", "#FF00FF")

BRIEFS: dict[str, dict] = {
    "leaves": {
        "aspect": "1:1", "key": MAGENTA,
        "prompt": (
            "Paint a sprite sheet of 16 separate single autumn leaves for a point-and-click adventure game, arranged "
            "in a loose 4 by 4 grid with wide empty space between them. A mix of golden-yellow birch leaves, orange "
            "and red maple leaves, ochre linden leaves and brown oak leaves; most seen flat from above, a few curled "
            "or tilted. All leaves about the same size, each one complete with its little stem, softly lit, with "
            "visible painted brush strokes and a soft darker outline."),
    },
    "pigeon": {
        "aspect": "16:9", "key": GREEN,
        "prompt": (
            "Paint a sprite sheet of ONE and the same small city pigeon in 8 poses for a point-and-click adventure "
            "game, arranged in two rows of four, every pose at exactly the same scale, with wide empty space between "
            "the poses. The pigeon has soft grey and slate-blue plumage with a pinkish-violet neck sheen and two dark "
            "wing bars (no green anywhere on the bird), orange eye, dark beak, coral-red feet. Top row: flying, exact "
            "side view facing right: 1 wings raised high above the back, 2 wings half up, 3 wings swept fully down "
            "below the body, 4 gliding with the wings spread level. Bottom row: on the ground, exact side view facing "
            "right: 5 standing upright, 6 head lowered to the ground pecking, 7 head raised looking around, 8 walking "
            "mid-step. Both feet visible in the ground poses."),
    },
    "car2020": {
        "aspect": "16:9", "key": GREEN,
        "prompt": (
            "Paint one small modern five-door hatchback car in silver-blue, exact side view facing right, as a game "
            "sprite for a point-and-click adventure game. The whole car is visible with empty margin on every side; "
            "the windows are dark tinted glass with soft sky reflections (not see-through); black tyres with simple "
            "grey wheel rims. No logo, no badge, no brand, no number plate, no text, no driver visible. The car fills "
            "about 80 % of the image width."),
    },
    "car1995": {
        "aspect": "16:9", "key": GREEN,
        "prompt": (
            "Paint one boxy early-1990s Central European five-door hatchback car in faded tomato red, exact side view "
            "facing right, as a game sprite for a point-and-click adventure game set in Bratislava in 1995: square "
            "lines, black plastic bumpers, narrow chrome-free trim, small steel wheels with plain hub caps. The whole "
            "car is visible with empty margin on every side; the windows are dark glass with soft sky reflections "
            "(not see-through). No logo, no badge, no brand, no number plate, no text, no driver visible. The car "
            "fills about 80 % of the image width."),
    },
    "cat": {
        "aspect": "16:9", "key": MAGENTA,
        "prompt": (
            "Paint one slim grey tabby cat with darker stripes and a white chest, walking calmly, exact side view "
            "facing right, mid-stride with the near front leg and the far hind leg forward, tail held up in a gentle "
            "curve, as a game sprite for a point-and-click adventure game. The whole cat is visible with empty margin "
            "on every side and fills about 55 % of the image width, centred."),
    },
    "clouds": {
        "aspect": "16:9", "key": GREEN,
        "prompt": (
            "Paint four separate soft fair-weather cumulus clouds for the sky of a point-and-click adventure game, "
            "arranged with wide empty space between them: two long flat ones and two rounder small ones. Warm "
            "late-afternoon light: white and cream tops, peach and soft blue-grey undersides, painterly soft edges."),
    },
    "ducks": {
        "aspect": "16:9", "key": GREEN,
        "prompt": (
            "Paint a sprite sheet of two brown female mallard ducks swimming, exact side view facing right, for a "
            "point-and-click adventure game: four poses in one row at exactly the same scale with wide empty space "
            "between them: 1 swimming with the head up, 2 swimming with the head turned slightly, 3 dipping the beak "
            "into the water, 4 swimming with the head up. Only the bird bodies down to the waterline are visible; the "
            "bottom of each body is a flat straight horizontal waterline cut. Mottled brown plumage, a small blue "
            "wing patch, orange-brown beak."),
    },
}

VIDEO_PROMPTS = {
    "cat": (
        "The cat walks in place, as if on a treadmill, with a calm natural four-legged walking cycle, tail swaying "
        "slightly. It stays in exactly the same spot in the centre of the frame and keeps facing right in side view. "
        "The camera is completely static: no pan, no zoom. The background stays a perfectly flat uniform magenta the "
        "whole time, with no floor, no shadow and nothing else appearing. Same hand-painted style throughout."),
}


def cmd_image(args: argparse.Namespace) -> None:
    brief = BRIEFS[args.name]
    model = "fal-ai/nano-banana-pro/edit"
    price = fal_api.IMAGE_PRICES[(model, "1K")]
    prompt = f"{brief['prompt']} {brief['key']} {STYLE_NOTE} {STYLE_A}"
    style = Image.open(STYLE_REF).convert("RGB")
    arguments = {
        "prompt": prompt,
        "image_urls": [fal_api.image_data_uri(style, max_side=1376, fmt="JPEG")],
        "aspect_ratio": brief["aspect"],
        "resolution": "1K",
        "output_format": "png",
        "num_images": 1,
    }
    name = args.out or args.name
    result = fal_api.run(model, arguments, f"ambient/{name}", price, budget=BUDGET, timeout_s=600)
    OUT.mkdir(parents=True, exist_ok=True)
    url = result["images"][0]["url"]
    path = fal_api.download(url, OUT / f"{name}.png")
    meta = {"model": model, "usd": price, "prompt": prompt, "aspect_ratio": brief["aspect"], "resolution": "1K",
            "style_reference": "src/game/assets/bg/S02.webp", "seed": result.get("seed")}
    (OUT / f"{name}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(path)


def cmd_video(args: argparse.Namespace) -> None:
    endpoint = "fal-ai/minimax/hailuo-02/standard/image-to-video"
    seconds = 6.0
    price = fal_api.video_price(endpoint, seconds, "768P")
    prompt = VIDEO_PROMPTS[args.name]
    arguments = {"prompt": prompt, "image_url": fal_api.image_data_uri(Path(args.image), fmt="PNG"),
                 "duration": "6", "resolution": "768P", "prompt_optimizer": False}
    name = args.out or f"{args.name}_video"
    result = fal_api.run(endpoint, arguments, f"ambient/{name}", price, budget=BUDGET, timeout_s=1500, poll_s=8)
    path = fal_api.download(result["video"]["url"], OUT / f"{name}.mp4")
    meta = {"model": endpoint, "usd": price, "prompt": prompt, "input": Path(args.image).name, "seconds": seconds}
    (OUT / f"{name}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(path)


def cmd_key(args: argparse.Namespace) -> None:
    src = OUT / f"{args.name}.png"
    rgb = np.asarray(Image.open(src).convert("RGB"))
    rgba = frames.chroma_key(rgb, min_island=args.min_island)
    out_dir = OUT / f"{args.name}_parts"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()
    labels, sizes = frames.label_components(rgba[..., 3] > 24)
    boxes = []
    for index, size in enumerate(sizes, start=1):
        if size < args.min_island:
            continue
        ys, xs = np.nonzero(labels == index)
        boxes.append((int(ys.min()), int(xs.min()), int(ys.max()), int(xs.max()), index))
    # reading order: rows (by top y within a tolerance), then x
    boxes.sort(key=lambda b: (round(b[0] / args.row_tolerance), b[1]))
    for n, (y0, x0, y1, x1, index) in enumerate(boxes):
        pad = 3
        y0, x0 = max(0, y0 - pad), max(0, x0 - pad)
        y1, x1 = min(rgba.shape[0] - 1, y1 + pad), min(rgba.shape[1] - 1, x1 + pad)
        part = rgba[y0:y1 + 1, x0:x1 + 1].copy()
        own = labels[y0:y1 + 1, x0:x1 + 1]
        # drop pixels of neighbouring components that intrude into the bounding box
        part[..., 3] = np.where((own == index) | (own == 0), part[..., 3], 0)
        Image.fromarray(part, "RGBA").save(out_dir / f"{n:02d}.png")
        print(f"{n:02d}: {x1 - x0 + 1}x{y1 - y0 + 1} at {x0},{y0}")


def cmd_list(_: argparse.Namespace) -> None:
    for name, brief in BRIEFS.items():
        print(f"{name}: {brief['prompt'][:90]}...")
    print(f"logged ambient spend: {fal_api.logged_spend('ambient/'):.3f} USD of {BUDGET[1]:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(required=True)
    image = sub.add_parser("image")
    image.add_argument("name", choices=BRIEFS)
    image.add_argument("--out")
    image.set_defaults(func=cmd_image)
    video = sub.add_parser("video")
    video.add_argument("name", choices=VIDEO_PROMPTS)
    video.add_argument("--image", required=True)
    video.add_argument("--out")
    video.set_defaults(func=cmd_video)
    key = sub.add_parser("key")
    key.add_argument("name")
    key.add_argument("--min-island", type=int, default=150)
    key.add_argument("--row-tolerance", type=int, default=120)
    key.set_defaults(func=cmd_key)
    listing = sub.add_parser("list")
    listing.set_defaults(func=cmd_list)
    args = parser.parse_args()
    try:
        args.func(args)
    except fal_api.BudgetExceeded as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
