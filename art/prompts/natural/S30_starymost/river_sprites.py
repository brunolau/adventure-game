"""S30 (old Stary most 1995) ambient sprites: Danube river traffic of 1995, style A, on a flat green key.

  python river_sprites.py image      ONE paid call (nano-banana-pro/edit 1K, USD 0.15, scope bg_natural/S30_starymost/)
                                     -> art/ambient/S30_river.png + .json
  python river_sprites.py key        free: key the sheet, split it into parts (art/ambient/S30_river_parts/NN.png)
  python river_sprites.py ship       free: copy the chosen parts as the shipped sprites
                                     src/game/assets/ambient/S30/natural/pusher.webp (+ .json sheet sidecar) etc.

Style reference: the accepted S30 painting itself (src/game/assets/bg_natural/S30.webp), so the sprites match its light.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "art" / "tools"))
import fal_api  # noqa: E402
import frames  # noqa: E402

OUT = ROOT / "art" / "ambient"
SHIP = ROOT / "src" / "game" / "assets" / "ambient" / "S30" / "natural"
SCOPE, CAP = "bg_natural/S30_starymost/", 0.75
STYLE_A = ("Style: classic 1990s hand-painted adventure game background. Rich painterly brushwork, slightly "
           "exaggerated cartoon proportions with gently curved lines, warm late-afternoon sunlight, saturated but "
           "harmonious colours, soft dappled shadows under the trees.")
PROMPT = (
    "Paint a sprite sheet of three separate river vessels on the Danube in Bratislava in 1995, for a point-and-click "
    "adventure game, arranged in three rows with wide empty space between them, every vessel in exact side view "
    "facing right, the whole vessel visible with empty margin on every side. Only the hulls down to the waterline "
    "are visible: the bottom of each vessel is a flat straight horizontal waterline cut, with no water, no wake and "
    "no reflection. Row 1 (the widest, filling about 90 % of the image width): a Danube pusher convoy - two long "
    "low empty cargo barges with dark rust-red and black steel hulls, joined one behind the other, pushed from "
    "behind (on the left) by a squat river pusher tug with a dark blue hull, a white two-storey wheelhouse with "
    "dark windows and a short black-topped funnel. Row 2: a white passenger hydrofoil of the 1990s (Soviet-built "
    "Raketa type) with a long row of windows and a raised bow, resting on its hull. Row 3: a small white and blue "
    "motor launch. No names, no numbers, no flags with emblems, no logos, no text, no people. "
    "Background: one perfectly flat, uniform, pure chroma-key green (#00FF00) filling the entire image, edge to "
    "edge, with no gradient, no texture, no ground, no cast shadow, no vignette and no text. Every object has crisp "
    "clean edges against the green, with no green tint, glow or reflection on it. Objects never touch each other or "
    "the image border. The reference image is a finished background painting from our game: use it only as the "
    "reference for the painting technique, the palette and the light; do not copy anything from its scene. "
    + STYLE_A)


def cmd_image() -> None:
    model = "fal-ai/nano-banana-pro/edit"
    price = fal_api.IMAGE_PRICES[(model, "1K")]
    style = Image.open(ROOT / "src" / "game" / "assets" / "bg_natural" / "S30.webp").convert("RGB")
    arguments = {"prompt": PROMPT, "image_urls": [fal_api.image_data_uri(style, max_side=1376, fmt="JPEG")],
                 "aspect_ratio": "16:9", "resolution": "1K", "output_format": "png", "num_images": 1}
    result = fal_api.run(model, arguments, f"{SCOPE}S30_river_sprites", price, budget=(SCOPE, CAP), timeout_s=600)
    path = fal_api.download(result["images"][0]["url"], OUT / "S30_river.png")
    meta = {"model": model, "usd": price, "prompt": PROMPT, "aspect_ratio": "16:9", "resolution": "1K",
            "style_reference": "src/game/assets/bg_natural/S30.webp", "seed": result.get("seed"),
            "spend_log_asset": f"{SCOPE}S30_river_sprites"}
    (OUT / "S30_river.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(path)


def cmd_key() -> None:
    rgb = np.asarray(Image.open(OUT / "S30_river.png").convert("RGB"))
    rgba = frames.chroma_key(rgb, min_island=300)
    labels, sizes = frames.label_components(rgba[..., 3] > 24)
    parts = OUT / "S30_river_parts"
    parts.mkdir(parents=True, exist_ok=True)
    for old in parts.glob("*.png"):
        old.unlink()
    boxes = []
    for index, size in enumerate(sizes, start=1):
        if size < 300:
            continue
        ys, xs = np.nonzero(labels == index)
        boxes.append((int(ys.min()), int(xs.min()), int(ys.max()), int(xs.max()), index))
    boxes.sort(key=lambda b: (round(b[0] / 120), b[1]))
    for n, (y0, x0, y1, x1, index) in enumerate(boxes):
        part = rgba[y0:y1 + 1, x0:x1 + 1].copy()
        own = labels[y0:y1 + 1, x0:x1 + 1]
        part[..., 3] = np.where((own == index) | (own == 0), part[..., 3], 0)
        Image.fromarray(part, "RGBA").save(parts / f"{n:02d}.png")
        print(f"{n:02d}: {x1 - x0 + 1}x{y1 - y0 + 1} at {x0},{y0}")


def cmd_ship(names: dict[str, int]) -> None:
    SHIP.mkdir(parents=True, exist_ok=True)
    for name, n in names.items():
        part = Image.open(OUT / "S30_river_parts" / f"{n:02d}.png").convert("RGBA")
        part = part.crop(part.getbbox())
        part.save(SHIP / f"{name}.webp", "WEBP", quality=92)
        sheet = {"frames": 1, "cell": [part.width, part.height], "pivot": [part.width // 2, part.height - 2],
                 "playback_fps": 1}
        (SHIP / f"{name}.json").write_text(json.dumps(sheet, indent=1), encoding="utf-8")
        print(f"{name}.webp {part.size}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "image":
        cmd_image()
    elif cmd == "key":
        cmd_key()
    elif cmd == "ship":
        cmd_ship({k: int(v) for k, v in (a.split("=") for a in sys.argv[2:])})
