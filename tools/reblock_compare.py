"""Side-by-side comparison of a room's template and natural blocking (docs/reblock/README.md).

Input:  build/screens/reblock/<room>_template.png and <room>_natural.png, in-game screenshots with Space labels on:
          <console exe> --path src/game --resolution 1920x1080 -- --blocking template --room S05 --labels --skip-lines \
                        --wait 1500 --screenshot build/screens/reblock/S05_template.png
          (same with --blocking natural)
Output: docs/reblock/<room>_compare.png (two screenshots at 1200x675 side by side, captions, a thin outline of the
        walk polygon of each blocking so the change of the walkable floor is visible).

Usage: PYTHONIOENCODING=utf-8 python -X utf8 tools/reblock_compare.py S03 S05
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_blocking  # noqa: E402

SHOTS = ROOT / "build" / "screens" / "reblock"
OUT = ROOT / "docs" / "reblock"
SCALE = 1200 / 1920
GAP, HEAD, FOOT = 24, 70, 44


def font(size: int):
    for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def panel(path: Path, polygon) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).line([tuple(p) for p in polygon] + [tuple(polygon[0])], fill=(70, 230, 110, 200), width=4)
    img = Image.alpha_composite(img, layer).convert("RGB")
    return img.resize((round(img.width * SCALE), round(img.height * SCALE)), Image.Resampling.LANCZOS)


def compose(room_id: str) -> Path:
    game = check_blocking.load_game()
    room = {r["id"]: r for r in game["rooms"]}[room_id]
    blocking = json.loads(check_blocking.blocking_path(room_id).read_text(encoding="utf-8"))
    natural = check_blocking.effective_room(room, blocking)
    left = panel(SHOTS / f"{room_id}_template.png", room["walk_polygon"])
    right = panel(SHOTS / f"{room_id}_natural.png", natural["walk_polygon"])
    w = left.width + right.width + 3 * GAP
    h = left.height + HEAD + FOOT
    sheet = Image.new("RGB", (w, h), (28, 28, 32))
    sheet.paste(left, (GAP, HEAD))
    sheet.paste(right, (2 * GAP + left.width, HEAD))
    d = ImageDraw.Draw(sheet)
    title = f"{room_id} {room['name']} ({room['era']})"
    d.text((GAP, 14), title, font=font(30), fill=(240, 240, 240))
    d.text((GAP, HEAD - 26), "TEMPLATE blocking (game.json) - current bg/" + room_id + ".webp",
           font=font(20), fill=(255, 200, 120))
    d.text((2 * GAP + left.width, HEAD - 26), "NATURAL blocking (data/blocking/" + room_id + ".json) - bg_natural/"
           + room_id + ".webp", font=font(20), fill=(140, 230, 160))
    d.text((GAP, h - FOOT + 10), "In-game screenshots, Space labels on, hero at the room spawn; green line = walk polygon. "
           "Logic ids and conditions are identical in both.", font=font(18), fill=(200, 200, 200))
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{room_id}_compare.png"
    sheet.save(out, optimize=True)
    print(f"{out.relative_to(ROOT)} {sheet.size}")
    return out


if __name__ == "__main__":
    for rid in sys.argv[1:] or ["S03", "S05"]:
        compose(rid)
