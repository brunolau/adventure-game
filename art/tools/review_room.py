"""Overlay a room's blocking (hotspot rects, NPC zones, exits, walk band, anchors) onto a painted master.

The master is first fitted to the 1920x1080 game frame exactly like the export (paint_room.fit_to_frame), so
what you see is what the game will show. Visual-only nudges from src/game/data/art_overrides.json
(rooms.<id>.targets.<hotspot>.rect_nudge = [dx, dy, dw, dh]) are drawn as dashed cyan boxes next to the original rect.

Usage: python review_room.py S05 3          (master art/masters/bg/S05_v3.png)
       python review_room.py S05 path/to/any_1920x1080_or_2752x1536.png
       python review_room.py S05 3 --grid 200 300 820 640   (x2 crop with a 20 px grid, game coordinates, for
                                                              measuring prop boxes for refit_room.py fit)
Output: art/review/<room>_v<N>_overlay.png  - full frame with the blocking drawn on top
        art/review/<room>_v<N>_crops.png    - every hotspot rect enlarged x2 with 60 px context, for checking
                                              that each prop sits inside its rect and is recognisable
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paint_room import FRAME, MASTERS, ROOT, fit_to_frame, load_room  # noqa: E402

REVIEW = ROOT / "art" / "review"
OVERRIDES = ROOT / "src" / "game" / "data" / "art_overrides.json"

PROP = (255, 190, 40)
NPC = (80, 160, 255)
EXIT = (255, 70, 70)
WALK = (60, 220, 90)
ANCHOR = (255, 0, 255)
NUDGE = (0, 230, 255)


def font(size: int) -> ImageFont.ImageFont:
    for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def label(draw: ImageDraw.ImageDraw, xy, text: str, colour, size: int = 20, anchor: str = "la") -> None:
    f = font(size)
    box = draw.textbbox(xy, text, font=f, anchor=anchor)
    draw.rectangle([box[0] - 3, box[1] - 2, box[2] + 3, box[3] + 2], fill=(0, 0, 0, 170))
    draw.text(xy, text, font=f, fill=colour + (255,), anchor=anchor)


def dashed_rect(draw: ImageDraw.ImageDraw, box, colour, width: int = 3, dash: int = 12) -> None:
    x0, y0, x1, y1 = box
    for x in range(int(x0), int(x1), dash * 2):
        draw.line([(x, y0), (min(x + dash, x1), y0)], fill=colour, width=width)
        draw.line([(x, y1), (min(x + dash, x1), y1)], fill=colour, width=width)
    for y in range(int(y0), int(y1), dash * 2):
        draw.line([(x0, y), (x0, min(y + dash, y1))], fill=colour, width=width)
        draw.line([(x1, y), (x1, min(y + dash, y1))], fill=colour, width=width)


def load_nudges(room_id: str) -> dict:
    """Per-target visual overrides (schema of src/game/scripts/World/ArtOverrides.cs: targets.<id>.rect_nudge)."""
    if not OVERRIDES.exists():
        return {}
    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    return data.get("rooms", {}).get(room_id, {}).get("targets", {})


def overlay(base: Image.Image, room: dict, anchors: dict) -> Image.Image:
    img = base.convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    walk = [tuple(p) for p in room["walk_polygon"]]
    d.polygon(walk, fill=WALK + (55,), outline=WALK + (255,), width=4)
    label(d, (walk[0][0] + 8, walk[0][1] + 6), "walk band", WALK)

    nudges = load_nudges(room["id"])
    for h in room["hotspots"]:
        x, y, w, hh = h["rect"]
        colour = NPC if h["kind"] == "npc" else PROP
        if h["kind"] == "npc":
            d.rectangle([x, y, x + w, y + hh], fill=NPC + (45,))
        d.rectangle([x, y, x + w, y + hh], outline=colour + (255,), width=4)
        label(d, (x, y + hh + 4), h["id"] + ("  (keep clear)" if h["kind"] == "npc" else ""), colour, 18)
        ix, iy = h["interaction_point"]
        d.ellipse([ix - 7, iy - 7, ix + 7, iy + 7], fill=colour + (255,), outline=(0, 0, 0, 255))
        if h.get("label_anchor"):
            ax, ay = h["label_anchor"]
            d.line([(ax - 8, ay), (ax + 8, ay)], fill=colour + (255,), width=2)
        if h["id"] in nudges:
            dx, dy, dw, dh = (list(nudges[h["id"]].get("rect_nudge", [0, 0, 0, 0])) + [0, 0, 0, 0])[:4]
            dashed_rect(d, (x + dx, y + dy, x + w + dx + dw, y + hh + dy + dh), NUDGE + (255,))
            label(d, (x + dx, y + dy - 24), f"nudge {dx:+.0f},{dy:+.0f},{dw:+.0f},{dh:+.0f}", NUDGE, 16)

    for e in room["exits"]:
        x, y, w, hh = e["rect"]
        d.rectangle([x, y, x + w, y + hh], fill=EXIT + (70,), outline=EXIT + (255,), width=4)
        label(d, (min(max(x + w / 2, 120), FRAME[0] - 120), y - 6), f"exit -> {e['to']}", EXIT, 18, "mb")

    for name, (ax, ay) in anchors.items():
        d.line([(ax - 18, ay), (ax + 18, ay)], fill=ANCHOR + (255,), width=4)
        d.line([(ax, ay - 18), (ax, ay + 18)], fill=ANCHOR + (255,), width=4)
        label(d, (ax + 22, ay - 12), name, ANCHOR, 18)

    label(d, (12, FRAME[1] - 12), f"{room['id']} review overlay - rects from design-doc/game.json", (255, 255, 255),
          18, "ld")
    return Image.alpha_composite(img, layer).convert("RGB")


def crops(base: Image.Image, room: dict, margin: int = 60, zoom: int = 2) -> Image.Image:
    tiles = []
    for h in room["hotspots"] + [dict(e, kind="exit", name=e["label"]) for e in room["exits"]]:
        x, y, w, hh = h["rect"]
        box = (max(0, x - margin), max(0, y - margin), min(FRAME[0], x + w + margin), min(FRAME[1], y + hh + margin))
        tile = base.crop(box).resize(((box[2] - box[0]) * zoom, (box[3] - box[1]) * zoom), Image.Resampling.LANCZOS)
        d = ImageDraw.Draw(tile)
        colour = {"npc": NPC, "exit": EXIT}.get(h["kind"], PROP)
        d.rectangle([(x - box[0]) * zoom, (y - box[1]) * zoom, (x + w - box[0]) * zoom, (y + hh - box[1]) * zoom],
                    outline=colour, width=3)
        tiles.append((h["id"], tile))
    cell_w = max(t.width for _, t in tiles)
    cell_h = max(t.height for _, t in tiles) + 34
    cols = min(4, len(tiles))
    rows = -(-len(tiles) // cols)
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    for i, (name, tile) in enumerate(tiles):
        cx, cy = (i % cols) * cell_w, (i // cols) * cell_h
        sheet.paste(tile, (cx, cy + 34))
        d.text((cx + 6, cy + 6), name, font=font(20), fill=(255, 255, 255))
    return sheet


def review(room_id: str, version_or_path) -> tuple[Path, Path]:
    room, anchors = load_room(room_id)
    path = Path(str(version_or_path))
    if str(version_or_path).isdigit():
        path = MASTERS / f"{room_id}_v{version_or_path}.png"
        tag = f"{room_id}_v{version_or_path}"
    else:
        tag = path.stem
    base = Image.open(path).convert("RGB")
    if base.size != FRAME:
        base = fit_to_frame(base)
    REVIEW.mkdir(parents=True, exist_ok=True)
    out_overlay = REVIEW / f"{tag}_overlay.png"
    out_crops = REVIEW / f"{tag}_crops.png"
    overlay(base, room, anchors).save(out_overlay)
    crops(base, room).save(out_crops)
    print(f"review: {out_overlay.relative_to(ROOT)} , {out_crops.relative_to(ROOT)}")
    return out_overlay, out_crops


def grid_crop(room_id: str, version_or_path, box: tuple[int, int, int, int]) -> Path:
    """Enlarged crop (x2) with a 20 px grid labelled every 100 px, for measuring prop bounding boxes."""
    path = MASTERS / f"{room_id}_v{version_or_path}.png" if str(version_or_path).isdigit() else Path(version_or_path)
    base = Image.open(path).convert("RGB")
    if base.size != FRAME:
        base = fit_to_frame(base)
    x0, y0, x1, y1 = box
    tile = base.crop(box).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.Resampling.LANCZOS)
    d = ImageDraw.Draw(tile)
    f = font(16)
    for x in range((x0 // 20 + 1) * 20, x1, 20):
        major = x % 100 == 0
        d.line([((x - x0) * 2, 0), ((x - x0) * 2, tile.height)], fill=(255, 0, 255) if major else (0, 255, 255))
        if major:
            d.text(((x - x0) * 2 + 2, 2), str(x), fill=(255, 0, 255), font=f)
    for y in range((y0 // 20 + 1) * 20, y1, 20):
        major = y % 100 == 0
        d.line([(0, (y - y0) * 2), (tile.width, (y - y0) * 2)], fill=(255, 0, 255) if major else (0, 255, 255))
        if major:
            d.text((2, (y - y0) * 2 + 2), str(y), fill=(255, 0, 255), font=f)
    REVIEW.mkdir(parents=True, exist_ok=True)
    out = REVIEW / f"{Path(str(path)).stem}_grid_{x0}_{y0}.png"
    tile.save(out)
    print(f"grid crop: {out.relative_to(ROOT)}")
    return out


if __name__ == "__main__":
    if len(sys.argv) == 8 and sys.argv[3] == "--grid":
        grid_crop(sys.argv[1], sys.argv[2], tuple(int(v) for v in sys.argv[4:8]))
    elif len(sys.argv) == 3:
        review(sys.argv[1], sys.argv[2])
    else:
        sys.exit(__doc__)
