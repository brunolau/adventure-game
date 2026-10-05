"""Paint a room background (style A) from real reference photos, the room's layout and a style reference.

Recipe (see art/tools/PAINTING.md for the why):
  model      = fal-ai/nano-banana-pro/edit, 16:9, 2K, png, one image per call
  image_urls = sketch mode (default when art/prompts/<room>.sketch.json exists):
                 [layout sketch (flat colour blocking in exact game geometry), reference photo(s), style reference]
               guide mode (fallback, NOT recommended - the model copies the boxes and ignores positions):
                 [reference photo(s), labelled layout guide art/layout/<room>.png, style reference]
  prompt     = generated image-role preamble + hand-written art/prompts/<room>.txt (placeholders expanded from
               game.json) + "do not draw the guide/sketch" + the canonical style-A sentence from ART_DIRECTION.md

Usage:
  python paint_room.py prompt S05                 # print the assembled prompt, render the sketch (free)
  python paint_room.py paint  S05 [--seed N] [--scope bg/pilot/ --budget 6]
                                                  # one paid generation -> art/masters/bg/S05_v<N>.png + .json,
                                                  # then art/review/S05_v<N>_overlay.png + _crops.png
  python paint_room.py export S05 3               # master v3 -> src/game/assets/bg/S05.webp (1920x1080, q90)

Prompt file art/prompts/<room>.txt:
  - lines starting with "#" are comments, except directives:
        #refs: path ; path        reference photos (default: the register's source_files)
        #style: path              style reference (default: art/backgrounds/entrance.png)
  - placeholders expanded from design-doc/game.json (so coordinates are never typed by hand):
        {rect:<hotspot id>}   -> "the block of the layout sketch at x 120-240, y 150-250 of the 1920x1080 frame
                                  (6-12 % from the left, 14-23 % from the top)"
        {exit:<exit id>}      -> same wording for an exit rect
        {walk}                -> the walk band's bounding box
        {npc_zones}           -> one sentence per NPC hotspot ("keep empty background, no person"), or a
                                 sentence that the room has none
        {anchors}             -> the camera family's landmark anchor points, or nothing
  - every hotspot id of the room must appear in a {rect:...} placeholder (NPC hotspots may be covered by
    {npc_zones} instead); the tool refuses to paint otherwise.

Sketch file art/prompts/<room>.sketch.json: {"background": "#rrggbb", "shapes": [...]} in 1920x1080 game
coordinates, drawn in order (later shapes on top):
  {"type": "rect",    "box": [x, y, w, h], "fill": "#rrggbb", "outline": "#rrggbb", "width": 3, "radius": 0}
  {"type": "ellipse", "box": [x, y, w, h], "fill": ..., "outline": ..., "width": ...}
  {"type": "poly",    "points": [[x, y], ...], "fill": ..., "outline": ..., "width": ...}
  {"type": "line",    "points": [[x, y], ...], "color": "#rrggbb", "width": 4}
  {"type": "bars",    "box": [x, y, w, h], "step": 30, "bar": 12, "fill": ..., "vertical": true}
  {"type": "grid",    "box": [x, y, w, h], "cols": 4, "rows": 6, "color": ..., "width": 2}
Any shape may carry a "note" (ignored). The rendered sketch is saved to art/layout/<room>_sketch.png.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import random
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fal_api  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "art"
GAME = ROOT / "design-doc" / "game.json"
REGISTER = ROOT / "design-doc" / "LOCATIONS_REGISTER.csv"
ART_DIRECTION = ROOT / "design-doc" / "ART_DIRECTION.md"
PROMPTS = ART / "prompts"
LAYOUT = ART / "layout"
MASTERS = ART / "masters" / "bg"
EXPORT = ROOT / "src" / "game" / "assets" / "bg"

MODEL = "fal-ai/nano-banana-pro/edit"
RESOLUTION = "2K"
ASPECT = "16:9"
FRAME = (1920, 1080)          # game coordinates (game.json rects, walk polygons)
MODEL_FRAME = (2752, 1536)    # what nano-banana-pro returns for 16:9 at 2K
DEFAULT_STYLE = ART / "backgrounds" / "entrance.png"
DEFAULT_SCOPE = "bg/"


# --------------------------------------------------------------------------- data

def load_room(room_id: str) -> tuple[dict, dict]:
    game = json.loads(GAME.read_text(encoding="utf-8"))
    rooms = {r["id"]: r for r in game["rooms"]}
    if room_id not in rooms:
        sys.exit(f"unknown room {room_id}")
    room = rooms[room_id]
    anchors = game.get("landmark_layouts", {}).get(room.get("camera_family")) or {}
    return room, anchors


def load_register_row(room_id: str) -> dict:
    with REGISTER.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["room_id"] == room_id:
                return row
    sys.exit(f"{room_id} has no row in {REGISTER.relative_to(ROOT)}")


def style_sentence() -> str:
    """The canonical style-A sentence, read verbatim from ART_DIRECTION.md (the blockquote after its heading)."""
    text = ART_DIRECTION.read_text(encoding="utf-8")
    after = text.split("Canonical style prompt", 1)[1]
    quote = []
    for line in after.splitlines()[1:]:
        if line.startswith(">"):
            quote.append(line[1:].strip())
        elif quote:
            break
    if not quote:
        sys.exit("canonical style sentence not found in ART_DIRECTION.md")
    return " ".join(quote)


# --------------------------------------------------------------------------- geometry

def fit_to_frame(img: Image.Image, frame: tuple[int, int] = FRAME) -> Image.Image:
    """Scale to cover the game frame and centre-crop (2752x1536 -> 1935x1080 -> crop 7 px left, 8 px right)."""
    fw, fh = frame
    scale = max(fw / img.width, fh / img.height)
    w, h = round(img.width * scale), round(img.height * scale)
    img = img.resize((w, h), Image.Resampling.LANCZOS)
    left, top = (w - fw) // 2, (h - fh) // 2
    return img.crop((left, top, left + fw, top + fh))


def to_model_geometry(img: Image.Image) -> Image.Image:
    """Place a 1920x1080 game-frame image on the model's output canvas so a master maps back with fit_to_frame()."""
    mw, mh = MODEL_FRAME
    cover_w = round(mw * FRAME[1] / mh)       # 1935: height drives the cover fit
    left = (cover_w - FRAME[0]) // 2
    right = cover_w - FRAME[0] - left
    canvas = Image.new("RGB", (cover_w, FRAME[1]))
    canvas.paste(img, (left, 0))
    # The few margin columns repeat the frame's border so they never read as a frame.
    canvas.paste(img.crop((0, 0, 1, FRAME[1])).resize((left, FRAME[1])), (0, 0))
    canvas.paste(img.crop((FRAME[0] - 1, 0, FRAME[0], FRAME[1])).resize((right, FRAME[1])), (left + FRAME[0], 0))
    return canvas.resize(MODEL_FRAME, Image.Resampling.LANCZOS)


def guide_in_model_geometry(room_id: str) -> Image.Image:
    """The labelled layout guide on the model canvas (guide mode only), half size."""
    img = to_model_geometry(Image.open(LAYOUT / f"{room_id}.png").convert("RGB"))
    return img.resize((MODEL_FRAME[0] // 2, MODEL_FRAME[1] // 2), Image.Resampling.LANCZOS)


def sketch_path(room_id: str) -> Path:
    return PROMPTS / f"{room_id}.sketch.json"


def render_sketch(room_id: str) -> Image.Image:
    """Draw the flat colour blocking sketch in game coordinates (1920x1080) and save it for review."""
    spec = json.loads(sketch_path(room_id).read_text(encoding="utf-8"))
    img = Image.new("RGB", FRAME, spec.get("background", "#808080"))
    d = ImageDraw.Draw(img)
    for shape in spec["shapes"]:
        kind = shape["type"]
        fill, outline, width = shape.get("fill"), shape.get("outline"), shape.get("width", 0)
        if kind in ("rect", "ellipse", "bars", "grid"):
            x, y, w, h = shape["box"]
            box = [x, y, x + w, y + h]
        if kind == "rect":
            if shape.get("radius"):
                d.rounded_rectangle(box, radius=shape["radius"], fill=fill, outline=outline, width=width)
            else:
                d.rectangle(box, fill=fill, outline=outline, width=width)
        elif kind == "ellipse":
            d.ellipse(box, fill=fill, outline=outline, width=width)
        elif kind == "poly":
            d.polygon([tuple(p) for p in shape["points"]], fill=fill, outline=outline, width=width or 1)
        elif kind == "line":
            d.line([tuple(p) for p in shape["points"]], fill=shape["color"], width=shape.get("width", 4),
                   joint="curve")
        elif kind == "bars":
            step, bar = shape["step"], shape["bar"]
            if shape.get("vertical", True):
                for bx in range(x, x + w, step):
                    d.rectangle([bx, y, min(bx + bar, x + w), y + h], fill=fill)
            else:
                for by in range(y, y + h, step):
                    d.rectangle([x, by, x + w, min(by + bar, y + h)], fill=fill)
        elif kind == "grid":
            cols, rows, colour, lw = shape.get("cols", 1), shape.get("rows", 1), shape["color"], shape.get("width", 2)
            for c in range(cols + 1):
                gx = x + round(c * w / cols)
                d.line([(gx, y), (gx, y + h)], fill=colour, width=lw)
            for r in range(rows + 1):
                gy = y + round(r * h / rows)
                d.line([(x, gy), (x + w, gy)], fill=colour, width=lw)
        else:
            sys.exit(f"unknown sketch shape {kind!r}")
    LAYOUT.mkdir(parents=True, exist_ok=True)
    img.save(LAYOUT / f"{room_id}_sketch.png")
    return img


def box_text(rect: list[int]) -> str:
    x, y, w, h = rect
    fw, fh = FRAME
    return (f"x {x}-{x + w}, y {y}-{y + h} of the 1920x1080 frame "
            f"({100 * x / fw:.0f}-{100 * (x + w) / fw:.0f} % from the left, "
            f"{100 * y / fh:.0f}-{100 * (y + h) / fh:.0f} % from the top)")


def walk_text(room: dict) -> str:
    xs = [p[0] for p in room["walk_polygon"]]
    ys = [p[1] for p in room["walk_polygon"]]
    return "the band at " + box_text([min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)])


# --------------------------------------------------------------------------- prompt

def read_prompt_file(room_id: str) -> tuple[str, list[Path] | None, Path | None]:
    path = PROMPTS / f"{room_id}.txt"
    if not path.exists():
        sys.exit(f"write {path.relative_to(ROOT)} first (see art/tools/PAINTING.md for the template)")
    body, refs, style = [], None, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#refs:"):
            refs = [ROOT / p.strip() for p in line[6:].split(";") if p.strip()]
        elif line.startswith("#style:"):
            style = ROOT / line[7:].strip()
        elif line.startswith("#"):
            continue
        else:
            body.append(line)
    text = "\n".join(body).strip()
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text, refs, style


def expand(text: str, room: dict, anchors: dict, sketch: bool) -> str:
    hotspots = {h["id"]: h for h in room["hotspots"]}
    exits = {e["id"]: e for e in room["exits"]}
    used: set[str] = set()

    def rect(match: re.Match) -> str:
        kind, ident = match.group(1), match.group(2)
        table = hotspots if kind == "rect" else exits
        if ident not in table:
            sys.exit(f"prompt references unknown {kind} id {ident!r}")
        used.add(ident)
        item = table[ident]
        if sketch:
            return f"the {'area' if kind == 'exit' else 'block'} of the layout sketch at {box_text(item['rect'])}"
        # Name the guide's label so the model can match the prose to the drawn box.
        guide_label = (f"exit: {item['label']}" if kind == "exit"
                       else "keep clear (no person)" if item["kind"] == "npc" else item["name"])
        return f"the box labelled '{guide_label}' in the layout guide, i.e. {box_text(item['rect'])}"

    text = re.sub(r"\{(rect|exit):([^}]+)\}", rect, text)
    text = text.replace("{walk}", walk_text(room))
    npcs = [h for h in room["hotspots"] if h["kind"] == "npc"]
    if npcs:
        npc_text = " ".join(
            f"NPC zone at {box_text(h['rect'])}: an animated character sprite will stand here later, so paint "
            f"only plain, uncluttered background in it - no person, no figure, no silhouette, no clothes on hooks "
            f"that read as a person." for h in npcs)
        used.update(h["id"] for h in npcs)
    else:
        npc_text = "This room has no NPC zones."
    text = text.replace("{npc_zones}", npc_text)
    anchor_text = " ".join(f"Fixed architectural anchor '{name}' at x {x}, y {y}." for name, (x, y) in anchors.items())
    text = text.replace("{anchors}", anchor_text)
    missing = [h for h in hotspots if h not in used]
    if missing:
        sys.exit(f"prompt does not place hotspot(s): {', '.join(missing)}")
    return text


def roles_preamble(refs: list[Path], sketch: bool) -> str:
    n = len(refs)
    style_role = (
        f"Image {n + 2} is a finished background painting from our game: use it ONLY as the reference for the "
        f"painting technique (brushwork, palette, edge softness, level of detail, line quality); do not copy "
        f"anything from its scene.")
    if sketch:
        photos = "Image 2 is a photo of the real place" if n == 1 else f"Images 2-{n + 1} are photos of the real place"
        return (
            f"You receive {n + 2} images. Image 1 is the LAYOUT SKETCH of the finished 1920x1080 game screen: a "
            f"crude flat-colour blocking that fixes the exact composition - camera, horizon, wall and floor lines, "
            f"and the position, size and outline of every object. Repaint image 1 into a finished painting: keep "
            f"every line and every block exactly where it is and exactly as large as it is, paint each block as the "
            f"object described below, do not move, enlarge, shrink, add or remove anything, and leave no flat "
            f"colour areas or hard geometric edges. {photos} (geography, architecture, materials and real details "
            f"to paint from; they are references only, do not copy their camera, cars, people, signs or weather). "
            f"{style_role}")
    photos = "Image 1 is a photo of the real place" if n == 1 else f"Images 1-{n} are photos of the real place"
    return (
        f"You receive {n + 2} images. {photos} (geography, architecture, materials and real details to paint from; "
        f"they are references, do not copy their camera, cars, people, signs or weather). "
        f"Image {n + 1} is a LAYOUT GUIDE for the 1920x1080 game screen: its coloured boxes mark where each "
        f"interactive prop must be painted, the green band marks the open walkable floor, red boxes mark exits, "
        f"the faint grid and all labels are only measurement aids. {style_role} "
        f"Paint ONE new 16:9 background screen for a point-and-click adventure game.")


GUIDE_WARNING = (
    "The layout guide is a positioning aid only: do NOT draw any of its boxes, outlines, dots, grid lines, green "
    "band, colour fills, labels, captions or any other text from it. The finished picture contains no UI, no "
    "frames, no captions, no watermark and no people or animals unless stated above.")
SKETCH_WARNING = (
    "The layout sketch is a blocking aid only: paint over all of it. Do NOT draw frames, borders, outlines or "
    "boxes around objects, and keep no flat colour block. The finished picture contains no UI, no captions, no "
    "text except what is asked for above, no watermark and no people or animals unless stated above.")


def assemble(room_id: str, mode: str = "auto") -> dict:
    room, anchors = load_room(room_id)
    register = load_register_row(room_id)
    body, refs, style = read_prompt_file(room_id)
    if refs is None:
        refs = [ROOT / p.strip() for p in register["source_files"].split(";") if p.strip()]
    style = style or DEFAULT_STYLE
    sketch = sketch_path(room_id).exists() if mode == "auto" else mode == "sketch"
    for path in [*refs, style, LAYOUT / f"{room_id}.png"] + ([sketch_path(room_id)] if sketch else []):
        if not path.exists():
            sys.exit(f"missing input {path}")
    prompt = "\n\n".join([roles_preamble(refs, sketch), expand(body, room, anchors, sketch),
                          SKETCH_WARNING if sketch else GUIDE_WARNING, style_sentence()])
    if sketch:
        layout = ("layout", to_model_geometry(render_sketch(room_id)),
                  f"art/layout/{room_id}_sketch.png (rendered from art/prompts/{room_id}.sketch.json, model geometry)")
        photos = [("photo", r, r.relative_to(ROOT).as_posix()) for r in refs]
        images = [layout, *photos]
    else:
        layout = ("layout", guide_in_model_geometry(room_id), f"art/layout/{room_id}.png (model geometry)")
        images = [*[("photo", r, r.relative_to(ROOT).as_posix()) for r in refs], layout]
    images.append(("style", style, style.relative_to(ROOT).as_posix()))
    return {"prompt": prompt, "images": images, "mode": "sketch" if sketch else "guide"}


# --------------------------------------------------------------------------- commands

def next_version(room_id: str) -> int:
    versions = [int(m.group(1)) for p in MASTERS.glob(f"{room_id}_v*.png")
                if (m := re.fullmatch(rf"{room_id}_v(\d+)\.png", p.name))]
    return max(versions, default=0) + 1


def encode(kind: str, item) -> str:
    if kind == "layout":
        return fal_api.image_data_uri(item, fmt="PNG")
    if kind == "style":
        return fal_api.image_data_uri(item, max_side=1376, fmt="JPEG")
    return fal_api.image_data_uri(item, max_side=2048, fmt="JPEG")


def cmd_prompt(args) -> None:
    job = assemble(args.room, args.mode)
    print(job["prompt"])
    print(f"\n--- image_urls ({job['mode']} mode) ---")
    for i, (_, _, name) in enumerate(job["images"], 1):
        print(f"{i}: {name}")
    print(f"\n{len(job['prompt'])} characters")


def cmd_paint(args) -> None:
    job = assemble(args.room, args.mode)
    MASTERS.mkdir(parents=True, exist_ok=True)
    version = next_version(args.room)
    seed = args.seed if args.seed is not None else random.randint(1, 2**31 - 1)
    arguments = {"prompt": job["prompt"], "image_urls": [encode(kind, item) for kind, item, _ in job["images"]],
                 "aspect_ratio": ASPECT, "resolution": RESOLUTION, "output_format": "png", "num_images": 1,
                 "seed": seed}
    price = fal_api.IMAGE_PRICES[(MODEL, RESOLUTION)]
    asset = f"{args.scope}{args.room}_v{version}"
    started = datetime.datetime.now().isoformat(timespec="seconds")
    result = fal_api.run(MODEL, arguments, asset, price, budget=(args.scope, args.budget), timeout_s=900)
    out = MASTERS / f"{args.room}_v{version}.png"
    fal_api.download(result["images"][0]["url"], out)
    size = Image.open(out).size
    sidecar = {
        "room": args.room, "version": version, "model": MODEL, "resolution": RESOLUTION, "aspect_ratio": ASPECT,
        "seed": result.get("seed", seed), "usd": price, "started": started, "spend_log_asset": asset,
        "mode": job["mode"], "prompt_file": f"art/prompts/{args.room}.txt", "prompt": job["prompt"],
        "image_urls": [name for _, _, name in job["images"]], "output_size": list(size),
        "model_description": result.get("description"),
    }
    if job["mode"] == "sketch":
        sidecar["sketch"] = json.loads(sketch_path(args.room).read_text(encoding="utf-8"))
    out.with_suffix(".json").write_text(json.dumps(sidecar, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{out.relative_to(ROOT)} {size} seed {sidecar['seed']} ${price:.2f} "
          f"(scope {args.scope} spent {fal_api.logged_spend(args.scope):.2f} of {args.budget:.2f})")
    import review_room
    review_room.review(args.room, version)


def cmd_export(args) -> None:
    master = MASTERS / f"{args.room}_v{args.version}.png"
    if not master.exists():
        sys.exit(f"missing {master}")
    EXPORT.mkdir(parents=True, exist_ok=True)
    out = EXPORT / f"{args.room}.webp"
    fit_to_frame(Image.open(master).convert("RGB")).save(out, "WEBP", quality=args.quality, method=6)
    sidecar = master.with_suffix(".json")
    if sidecar.exists():
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
        meta["exported"] = {"path": out.relative_to(ROOT).as_posix(), "size": list(FRAME), "quality": args.quality,
                            "at": datetime.datetime.now().isoformat(timespec="seconds")}
        sidecar.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{master.relative_to(ROOT)} -> {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KiB)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prompt")
    p.add_argument("room")
    p.add_argument("--mode", choices=["auto", "sketch", "guide"], default="auto")
    p.set_defaults(func=cmd_prompt)
    p = sub.add_parser("paint")
    p.add_argument("room")
    p.add_argument("--mode", choices=["auto", "sketch", "guide"], default="auto")
    p.add_argument("--seed", type=int)
    p.add_argument("--budget", type=float, default=6.0, help="USD cap for the spend scope (default 6)")
    p.add_argument("--scope", default=DEFAULT_SCOPE,
                   help="spend-log asset prefix the budget applies to (default 'bg/'; use a per-task prefix "
                        "such as 'bg/batch2/')")
    p.set_defaults(func=cmd_paint)
    p = sub.add_parser("export")
    p.add_argument("room")
    p.add_argument("version", type=int)
    p.add_argument("--quality", type=int, default=90)
    p.set_defaults(func=cmd_export)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
