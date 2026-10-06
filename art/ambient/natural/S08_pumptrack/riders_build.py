"""Key art/ambient/s08_riders.png and build the three S08 rider sheets (free).

  PYTHONIOENCODING=utf-8 python -X utf8 art/ambient/natural/S08_pumptrack/riders_build.py

Outputs (src/game/assets/ambient/S08/natural/): rider_girl_sheet, rider_boy_sheet (balance bikes, 2 frames: push,
glide), rider_bmx_sheet (3 frames: pedal_0, pedal_1, pump). Cells are already at their on-screen size (draw at scale
1.0): the BMX boy ~46 px tall, the balance-bike children ~32 px, i.e. ~27 px per metre on the far pump-track hill.
Pivot = where the wheels touch the track (cell bottom centre of the bike). A soft contact shadow is painted under the
wheels, offset to the right (the low sun is on the left). Parts also saved to art/ambient/s08_riders_parts/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "art" / "tools"))
import frames  # noqa: E402

SRC = ROOT / "art" / "ambient" / "s08_riders.png"
PARTS = ROOT / "art" / "ambient" / "s08_riders_parts"
OUT = ROOT / "src" / "game" / "assets" / "ambient" / "S08" / "natural"
FACTOR = 46 / 518          # source px -> screen px (BMX boy 518 px tall in the source -> 46 px)
HAZE = (176, 140, 96)      # far-hill colour the riders are pulled towards (aerial perspective)
HAZE_MIX = 0.14

GROUPS = {
    "rider_girl_sheet": {"boxes": [(165, 92, 484, 453), (718, 72, 1036, 444)], "names": ["push", "glide"], "fps": 2},
    "rider_boy_sheet": {"boxes": [(175, 534, 501, 898), (768, 530, 1094, 895)], "names": ["push", "glide"], "fps": 2},
    "rider_bmx_sheet": {"boxes": [(110, 964, 565, 1471), (716, 953, 1170, 1471), (1286, 1025, 1739, 1471)],
                        "names": ["pedal_0", "pedal_1", "pump"], "fps": 3},
}


def component(rgba: np.ndarray, labels: np.ndarray, box) -> np.ndarray:
    x0, y0, x1, y1 = box
    sub_l = labels[y0:y1 + 1, x0:x1 + 1]
    ids, counts = np.unique(sub_l[sub_l > 0], return_counts=True)
    main = ids[np.argmax(counts)]
    part = rgba[y0:y1 + 1, x0:x1 + 1].copy()
    part[..., 3] = np.where(sub_l == main, part[..., 3], 0)
    return part


def wheel_frame(part: np.ndarray) -> tuple[float, int]:
    """(bike centre x, wheel bottom y) of a part: from the alpha of its lowest 22 % (the wheels)."""
    a = part[..., 3] > 60
    rows = np.nonzero(a.any(axis=1))[0]
    bottom = int(rows.max())
    top_w = bottom - int(0.22 * (bottom - rows.min()))
    cols = np.nonzero(a[top_w:bottom + 1].any(axis=0))[0]
    return (cols.min() + cols.max()) / 2.0, bottom


def grade(img: Image.Image) -> Image.Image:
    arr = np.asarray(img).astype(np.float32)
    rgb = arr[..., :3] * (1 - HAZE_MIX) + np.array(HAZE, np.float32) * HAZE_MIX
    return Image.fromarray(np.dstack([rgb, arr[..., 3]]).clip(0, 255).astype(np.uint8), "RGBA")


def main() -> None:
    rgb = np.asarray(Image.open(SRC).convert("RGB"))
    rgba = frames.chroma_key(rgb, min_island=400)
    labels, _ = frames.label_components(rgba[..., 3] > 24)
    PARTS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, g in GROUPS.items():
        parts = [component(rgba, labels, b) for b in g["boxes"]]
        for i, p in enumerate(parts):
            Image.fromarray(p, "RGBA").save(PARTS / f"{name}_{g['names'][i]}.png")
        refs = [wheel_frame(p) for p in parts]
        # common canvas in source px: every part placed so its bike centre / wheel bottom meet at the pivot
        lefts = [cx for cx, _ in refs]
        rights = [p.shape[1] - cx for p, (cx, _) in zip(parts, refs)]
        ups = [b for _, b in refs]
        downs = [p.shape[0] - b for p, (_, b) in zip(parts, refs)]
        margin = 40
        L, R = max(lefts) + margin, max(rights) + margin
        U, D = max(ups) + margin, max(downs) + margin + 30
        W, H = int(L + R), int(U + D)
        cells = []
        for p, (cx, b) in zip(parts, refs):
            canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            # contact shadow: soft ellipse under the wheels, shifted right
            bike_len = float(np.ptp(np.nonzero((p[..., 3] > 60).any(axis=0))[0]))
            sh = Image.new("L", (W, H), 0)
            ImageDraw.Draw(sh).ellipse((L - bike_len * 0.42 + 26, U - 12, L + bike_len * 0.5 + 26, U + 20), fill=120)
            sh = sh.filter(ImageFilter.GaussianBlur(9))
            shadow = Image.new("RGBA", (W, H), (60, 40, 25, 0))
            shadow.putalpha(sh)
            canvas.alpha_composite(shadow)
            canvas.alpha_composite(Image.fromarray(p, "RGBA"), (int(round(L - cx)), int(round(U - b))))
            cells.append(canvas)
        cw, ch = max(1, round(W * FACTOR)), max(1, round(H * FACTOR))
        small = [grade(c.resize((cw, ch), Image.Resampling.LANCZOS)) for c in cells]
        sheet = Image.new("RGBA", (cw * len(small), ch), (0, 0, 0, 0))
        for i, c in enumerate(small):
            sheet.paste(c, (i * cw, 0))
        sheet.save(OUT / f"{name}.webp", lossless=True, quality=100, method=6)
        pivot = [round(L * FACTOR), round(U * FACTOR)]
        meta = {"name": name, "frames": len(small), "cell": [cw, ch], "pivot": pivot, "playback_fps": g["fps"],
                "frame_names": g["names"], "oneshot": False}
        (OUT / f"{name}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        fig_h = max(int(np.ptp(np.nonzero((np.asarray(s)[..., 3] > 100).any(axis=1))[0])) for s in small)
        print(name, "cell", cw, ch, "pivot", pivot, "figure height px", fig_h)


if __name__ == "__main__":
    main()
