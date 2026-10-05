"""S21 (1995): key the generated side-view Tatra T3 (T3_side_v1_raw.png, one paid call, see edit.py) into a sprite.

Free and local. Keeps the largest connected part of the keyed image (the tram with its pantograph; a stray painted
streak in the sky is dropped), scales it so the tram is ~560 px long (15 m at the distance of the tram street at the
right edge of S21) and writes src/game/assets/ambient/S21/natural/tram_t3_side.webp + .json (pivot = the bottom of
the wheels, centred).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "art" / "tools"))
import cutlib  # noqa: E402
import frames  # noqa: E402

OUT = ROOT / "src" / "game" / "assets" / "ambient" / "S21" / "natural"
LENGTH_PX = 560


def main() -> None:
    rgb = np.asarray(Image.open(HERE / "T3_side_v1_raw.png").convert("RGB"))
    rgba = frames.chroma_key(rgb, min_island=400)
    labels, sizes = frames.label_components(rgba[..., 3] > 24)
    keep = 1 + int(np.argmax(sizes))
    rgba[..., 3] = np.where(labels == keep, rgba[..., 3], 0)
    img = Image.fromarray(rgba, "RGBA")
    img = img.crop(img.getbbox())
    # wheel bottoms: the lowest opaque rows in the middle third (the couplers stick out lower at the ends? no: higher)
    a = np.asarray(img)[..., 3] > 128
    cols = slice(img.width // 6, img.width * 5 // 6)
    bottom = int(np.nonzero(a[:, cols].any(1))[0].max())
    f = LENGTH_PX / img.width
    small = img.resize((LENGTH_PX, max(1, round(img.height * f))), Image.Resampling.LANCZOS)
    cutlib.save_webp(small, OUT / "tram_t3_side.webp")
    meta = {"frames": 1, "cell": list(small.size), "pivot": [small.width // 2, round(bottom * f)], "playback_fps": 1}
    (OUT / "tram_t3_side.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    cutlib.preview(small, HERE / "S21_tram_side_preview.png")
    print(meta)


if __name__ == "__main__":
    main()
