"""Draw a blocking/layout guide for a room from game.json.

The guide is passed to the image model as a second reference image so that painted props land inside
their hotspot rects and the walk band stays open. It is never shipped.

Usage: python layout_guide.py S17 [S18 ...]   (or "all")
Output: art/layout/<room>.png (1920x1080)
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT / "design-doc" / "game.json"
OUT = ROOT / "art" / "layout"

W, H = 1920, 1080
WALK = (60, 200, 90, 90)
PROP = (255, 190, 40, 255)
NPC = (80, 160, 255, 255)
EXIT = (255, 70, 70, 255)
ANCHOR = (255, 0, 255, 255)


def font(size):
    for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_room(room, landmarks):
    img = Image.new("RGBA", (W, H), (235, 235, 230, 255))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    small, big = font(22), font(30)

    # Horizon-ish grid so the model reads the canvas as a scene, not a diagram.
    for x in range(0, W, 160):
        d.line([(x, 0), (x, H)], fill=(0, 0, 0, 25))
    for y in range(0, H, 90):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, 25))

    d.polygon([tuple(p) for p in room["walk_polygon"]], fill=WALK, outline=(30, 120, 50, 255))
    wx = sum(p[0] for p in room["walk_polygon"]) / len(room["walk_polygon"])
    wy = sum(p[1] for p in room["walk_polygon"]) / len(room["walk_polygon"])
    d.text((wx, wy), "OPEN WALKABLE FLOOR", font=big, fill=(20, 90, 40, 255), anchor="mm")

    for h in room["hotspots"]:
        x, y, w, hh = h["rect"]
        color = NPC if h["kind"] == "npc" else PROP
        d.rectangle([x, y, x + w, y + hh], outline=color, width=5)
        # NPCs are separate animated sprites: their area must stay empty background, no painted person.
        label = h["name"] if h["kind"] != "npc" else "keep clear (no person)"
        d.text((x + 6, y + 4), label, font=small, fill=(0, 0, 0, 255))
        ix, iy = h["interaction_point"]
        d.ellipse([ix - 6, iy - 6, ix + 6, iy + 6], fill=color)

    for e in room["exits"]:
        x, y, w, hh = e["rect"]
        d.rectangle([x, y, x + w, y + hh], fill=(255, 70, 70, 90), outline=EXIT, width=4)
        d.text((x + w / 2, y - 14), f'exit: {e["label"]}', font=small, fill=EXIT, anchor="mm")

    for name, (ax, ay) in (landmarks or {}).items():
        d.line([(ax - 18, ay), (ax + 18, ay)], fill=ANCHOR, width=4)
        d.line([(ax, ay - 18), (ax, ay + 18)], fill=ANCHOR, width=4)
        d.text((ax + 22, ay - 12), name, font=small, fill=ANCHOR)

    d.text((16, 12), f'{room["id"]} {room["name"]} ({room["era"]})', font=big, fill=(0, 0, 0, 255))
    return Image.alpha_composite(img, overlay).convert("RGB")


def main(args):
    game = json.loads(GAME.read_text(encoding="utf-8"))
    rooms = {r["id"]: r for r in game["rooms"]}
    ids = list(rooms) if args == ["all"] else args
    OUT.mkdir(parents=True, exist_ok=True)
    for rid in ids:
        room = rooms[rid]
        landmarks = game["landmark_layouts"].get(room.get("camera_family"))
        draw_room(room, landmarks).save(OUT / f"{rid}.png")
        print(f"{rid}: {len(room['hotspots'])} hotspots, {len(room['exits'])} exits -> art/layout/{rid}.png")


if __name__ == "__main__":
    main(sys.argv[1:] or ["S17"])
