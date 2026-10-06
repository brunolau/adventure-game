"""S08 pump-track riders: one style-A sprite sheet on a flat green key (nano-banana-pro, USD 0.15).

  PYTHONIOENCODING=utf-8 python -X utf8 art/ambient/natural/S08_pumptrack/riders_gen.py [seed]   (shipped: seed 2020833)
Image 1 is a flat #00FF00 canvas (a first try that sent only the S08 painting made the model paint the children INTO
the scene: art/ambient/rejected/s08_riders_a1.png); image 2 is a crop of the S08 painting for the technique.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "art" / "tools"))
import ambient_art  # noqa: E402
import fal_api  # noqa: E402

OUT = ROOT / "art" / "ambient" / "s08_riders.png"
SCOPE = ("ambient/S08_pumptrack/", 0.45)
STYLE = ROOT / "src" / "game" / "assets" / "bg_natural" / "S08.webp"

PROMPT = (
    "Paint a sprite sheet of three children riding on a dirt pump track, for a point-and-click adventure game, every "
    "figure in exact side view facing RIGHT, all at the same scale (as if the same distance from the camera), "
    "arranged in three rows with wide empty space between all figures. Each child wears a bicycle helmet; the faces "
    "are tiny, simple and turned forward along the ride (no detailed faces). Autumn clothes, late October. "
    "Row 1: a small girl about four years old on a small red wooden balance bike (no pedals), dark-blue jacket, "
    "light-blue helmet, grey trousers, little boots - two poses: (a) pushing off with one foot on the ground, "
    "(b) gliding with both feet lifted forward. "
    "Row 2: a small boy about five years old on a small blue balance bike (no pedals), orange-red jacket, white "
    "helmet, dark trousers - two poses: (a) pushing off with one foot down, (b) gliding with both feet lifted. "
    "Row 3: a boy about ten years old on a small black BMX bike, yellow jacket, dark jeans, black helmet, standing "
    "on the pedals - three poses: (a) pedals level, knees bent, (b) pedals vertical, (c) crouched low pumping over a "
    "bump with his arms bent. "
    "Whole figures and bikes visible, both wheels complete, wheels resting on an invisible flat ground line, no "
    "ground, no shadow, no dust, no motion lines, no text. No green in the clothes or bikes.")


def main() -> None:
    model = "fal-ai/nano-banana-pro/edit"
    prompt = ("Image 1 is an empty flat chroma-key green canvas: paint the sprites on it and keep the rest of it "
              "perfectly flat green. " + f"{PROMPT} {ambient_art.GREEN} {ambient_art.STYLE_NOTE} {ambient_art.STYLE_A}")
    style = Image.open(STYLE).convert("RGB").crop((0, 560, 900, 1080))   # foreground grass + trail only
    canvas = Image.new("RGB", (1376, 768), (0, 255, 0))
    arguments = {"prompt": prompt, "image_urls": [fal_api.image_data_uri(canvas, fmt="PNG"),
                                                  fal_api.image_data_uri(style, max_side=1376, fmt="JPEG")],
                 "aspect_ratio": "16:9", "resolution": "2K", "output_format": "png", "num_images": 1,
                 "seed": int(sys.argv[1]) if len(sys.argv) > 1 else 2020832}
    price = fal_api.IMAGE_PRICES[(model, "2K")]
    result = fal_api.run(model, arguments, f"ambient/S08_pumptrack/s08_riders_seed{arguments['seed']}", price, budget=SCOPE, timeout_s=900)
    fal_api.download(result["images"][0]["url"], OUT)
    meta = {"model": model, "usd": price, "prompt": prompt, "aspect_ratio": "16:9", "resolution": "2K",
            "image_urls": ["flat #00FF00 canvas 1376x768", "src/game/assets/bg_natural/S08.webp (v3) crop 0,560-900,1080"], "seed": arguments["seed"],
            "scope": SCOPE[0], "use": "S08 pump-track riders ambient (art/masters/bg_natural/S08.md)"}
    OUT.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(OUT, "spent", fal_api.logged_spend(SCOPE[0]))


if __name__ == "__main__":
    main()
