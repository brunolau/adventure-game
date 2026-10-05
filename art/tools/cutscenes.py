"""Cutscene beat and epilogue frames for LastBell (style A) via fal.ai nano-banana-pro/edit.

One 1920x1080 frame per cutscene beat (game.json cutscenes[].beats[], shipped as
src/game/assets/cutscenes/<CS>_<n>.webp, n from 1) and per epilogue shot (epilogue[], shipped as
src/game/assets/cutscenes/EPILOGUE_<n>.webp). Shot briefs, references and the camera moves live in
art/tools/cutscene_shots.py. Masters (2752x1536 PNG + JSON sidecar) go to art/cutscenes/.

References are what keeps a frame on model: the approved character sheets (keyed and put on a neutral grey card,
so no chroma green leaks into the scene), the room's painted background (src/game/assets/bg/<room>.webp) or,
while a room is not painted yet, its reference photos from art/source/rooms/<room>/ plus a painted background
of the game as the style reference, and item icons for props.

Usage (from the repo root, PYTHONIOENCODING=utf-8 python -X utf8 art/tools/cutscenes.py ...):
  list                                   shots, their status and the latest master
  prompt <shot>                          print the assembled prompt and save the reference images (free)
  paint <shot> [<shot> ...] [--seed N]   one paid call per shot (USD 0.15), in parallel; refused beyond --budget
  export <shot> <version>                master -> src/game/assets/cutscenes/<shot>.webp (1920x1080, WebP q90)
  camera                                 write src/game/data/cutscene_camera.json from the shot specs (free)
  contact [<shot> ...]                   contact sheet of the exported frames with the letterbox and camera rects
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fal_api  # noqa: E402
import frames  # noqa: E402
from paint_room import fit_to_frame, style_sentence  # noqa: E402
import cutscene_shots  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "art"
MASTERS = ART / "cutscenes"
REFS = MASTERS / "refs"
EXPORT = ROOT / "src" / "game" / "assets" / "cutscenes"
CAMERA_JSON = ROOT / "src" / "game" / "data" / "cutscene_camera.json"
CHARS = json.loads((ART / "characters" / "characters.json").read_text(encoding="utf-8"))

MODEL = "fal-ai/nano-banana-pro/edit"
RESOLUTION = "2K"
PRICE = fal_api.IMAGE_PRICES[(MODEL, RESOLUTION)]
SCOPE = "cutscenes/"
DEFAULT_BUDGET = 15.0
GREY = (128, 128, 128)

# Which approved image stands for a character (keyed sheet or a sheet on a flat key).
CHAR_SOURCES = {
    "ADAM": ["characters/ADAM/masters/front_keyed.png", "characters/ADAM/masters/side_keyed.png"],
    "MIRA60": ["characters/MIRA60/sheet_3q.png"],
    "MIRA95": ["characters/MIRA95/sheet_3q.png"],
    "JANA82": ["characters/JANA82/edit_gesture.png"],
    "JANA20": ["characters/JANA20/edit_gesture.png"],
    "JANA35": ["characters/JANA35/edit_gesture.png"],
    "TAMARA": ["characters/TAMARA/keyed/base_3q.png", "characters/TAMARA/pose_gesture_nb2_v2.png"],
}

PREAMBLE = (
    "Paint ONE finished frame of a film-like cutscene of our hand-painted point-and-click adventure game "
    "'Posledny zvonec' (Slovakia; eras 1960, 1982, 1995, 2020, 2035). The reference images are numbered in the order "
    "they are given:"
)

COMPOSITION = {
    "cutscene": ("Composition: a cinematic 16:9 film frame with a clear focal point and depth (foreground, subject, "
                 "background), painted full-bleed to all four edges (never paint black letterbox bars or a border: the game "
                 "adds its own bars later and they cover the top tenth and the bottom fifth of the image, with the "
                 "subtitles), so keep faces, hands and the key object inside the middle band."),
    "epilogue": ("Composition: a calm 16:9 picture like a still from the last minutes of a film, with a clear focal point "
                 "and depth; it is shown whole with a caption below it, so keep the subject well inside the frame."),
}

RULES = (
    "Character references show approved characters of the game on a plain grey card: copy each person's face, age, "
    "hair, body proportions, clothes and colours exactly, but pose and light them for this scene; never copy the grey "
    "card, the sheet layout or a duplicate of the same person. Place references show the real location and its "
    "painted version in our game: keep its architecture, materials and era. Photos are only references: repaint "
    "everything in our style, paint any real people in them out, and do not copy brand logos or shop names. "
    "{composition} One single image: no panels, no split screen, no border, "
    "no frame, no captions, no subtitles, no speech bubbles, no watermark, no UI, unless the shot asks for it. "
    "No text or lettering anywhere unless the shot quotes it exactly."
)


def char_ref(char_id: str) -> Path:
    """The character's approved look, keyed, on a neutral grey card (cached in art/cutscenes/refs/)."""
    out = REFS / f"char_{char_id}.png"
    if out.exists():
        return out
    sources = CHAR_SOURCES.get(char_id) or [f"characters/{char_id}/keyed/base_3q.png"]
    figures = []
    for rel in sources:
        path = ART / rel
        img = Image.open(path)
        if img.mode == "RGBA" and np.asarray(img)[..., 3].min() < 10:
            rgba = np.asarray(img.convert("RGBA"))
        else:
            rgba = frames.chroma_key(frames.load_rgb(path))
        rgba = frames.crop_to_figure(rgba, pad=8)
        figures.append(Image.fromarray(rgba, "RGBA"))
    height = 1400
    figures = [f.resize((max(1, round(f.width * height / f.height)), height), Image.Resampling.LANCZOS) for f in figures]
    pad = 60
    card = Image.new("RGB", (sum(f.width for f in figures) + pad * (len(figures) + 1), height + 2 * pad), GREY)
    x = pad
    for f in figures:
        card.paste(f, (x, pad), f)
        x += f.width + pad
    REFS.mkdir(parents=True, exist_ok=True)
    card.save(out)
    return out


def item_ref(item_id: str) -> Path:
    out = REFS / f"item_{item_id}.png"
    if not out.exists():
        icon = Image.open(ART / "items" / f"{item_id}.png").convert("RGBA")
        card = Image.new("RGB", (icon.width + 80, icon.height + 80), GREY)
        card.paste(icon, (40, 40), icon)
        REFS.mkdir(parents=True, exist_ok=True)
        card.save(out)
    return out


def crop_ref(spec: str) -> Path:
    """'crop:<path>@x0,y0,x1,y1' -> an upscaled crop of a game image (e.g. the family photo inside S06)."""
    path, box = spec[5:].split("@")
    x0, y0, x1, y1 = (int(v) for v in box.split(","))
    out = REFS / f"crop_{Path(path).stem}_{x0}_{y0}_{x1}_{y1}.png"
    if not out.exists():
        img = Image.open(ROOT / path).convert("RGB").crop((x0, y0, x1, y1))
        scale = max(1, round(768 / max(img.size)))
        img = img.resize((img.width * scale, img.height * scale), Image.Resampling.LANCZOS)
        REFS.mkdir(parents=True, exist_ok=True)
        img.save(out)
    return out


def resolve_ref(spec: str) -> Path:
    """Reference spec -> local file. char:ID | item:ID | bg:ROOM | photo:ROOM/file | frame:SHOT | crop:... | path."""
    kind, _, value = spec.partition(":")
    if kind == "char":
        return char_ref(value)
    if kind == "item":
        return item_ref(value)
    if kind == "bg":
        return ROOT / "src" / "game" / "assets" / "bg" / f"{value}.webp"
    if kind == "photo":
        return ART / "source" / "rooms" / value
    if kind == "frame":
        return EXPORT / f"{value}.webp"
    if kind == "crop":
        return crop_ref(spec)
    if kind == "style":
        return ART / "backgrounds" / f"{value}.png"
    return ROOT / spec


def character_brief(char_id: str) -> str:
    brief = CHARS.get(char_id, {})
    return brief.get("description", "")


def build_prompt(shot: dict) -> tuple[str, list[Path]]:
    paths, lines = [], [PREAMBLE]
    for n, (spec, role) in enumerate(shot["refs"], start=1):
        path = resolve_ref(spec)
        if not path.exists():
            sys.exit(f"{shot['id']}: missing reference {spec} -> {path}")
        paths.append(path)
        lines.append(f"Image {n}: {role}")
    text = " ".join(lines) + "\n\n" + "Shot: " + shot["shot"].strip()
    chars = shot.get("characters") or []
    if chars:
        text += "\n\nCharacters in this frame (briefs of the approved designs): " + " ".join(
            character_brief(c) for c in chars if character_brief(c))
    if shot.get("light"):
        text += "\n\nLight and time: " + shot["light"].strip()
    rules = RULES.format(composition=COMPOSITION[shot.get("kind", "cutscene")])
    text += "\n\n" + rules + "\n\n" + style_sentence()
    return text, paths


def next_version(shot_id: str) -> int:
    existing = [int(p.stem.rsplit("_v", 1)[1]) for p in MASTERS.glob(f"{shot_id}_v*.png") if p.stem.rsplit("_v", 1)[1].isdigit()]
    return max(existing, default=0) + 1


def paint(shot_id: str, seed: int | None, budget: float) -> Path:
    shot = cutscene_shots.SHOTS[shot_id]
    prompt, paths = build_prompt(shot)
    version = next_version(shot_id)
    asset = f"{SCOPE}{shot_id}_v{version}"
    arguments = {
        "prompt": prompt,
        "image_urls": [fal_api.image_data_uri(p, max_side=1536, fmt="JPEG" if p.suffix.lower() in (".jpg", ".jpeg", ".webp") else "PNG")
                       for p in paths],
        "aspect_ratio": "16:9",
        "resolution": RESOLUTION,
        "output_format": "png",
        "num_images": 1,
    }
    if seed is not None:
        arguments["seed"] = seed
    MASTERS.mkdir(parents=True, exist_ok=True)
    out = MASTERS / f"{shot_id}_v{version}.png"
    out.touch()  # reserve the version number for parallel calls
    try:
        result = fal_api.run(MODEL, arguments, asset, PRICE, budget=(SCOPE, budget), timeout_s=600)
    except Exception:
        out.unlink(missing_ok=True)
        raise
    url = result["images"][0]["url"]
    fal_api.download(url, out)
    meta = {"shot": shot_id, "model": MODEL, "resolution": RESOLUTION, "usd": PRICE, "seed": result.get("seed", seed),
            "prompt": prompt, "references": [str(p.relative_to(ROOT)).replace("\\", "/") for p in paths],
            "at": datetime.datetime.now().isoformat(timespec="seconds")}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def cmd_paint(args) -> None:
    for s in args.shots:  # validate every shot (references exist) before any paid call
        build_prompt(cutscene_shots.SHOTS[s])
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(args.shots))) as pool:
        futures = {pool.submit(paint, s, args.seed, args.budget): s for s in args.shots}
        for future in concurrent.futures.as_completed(futures):
            shot = futures[future]
            try:
                print(f"{shot}: {future.result().relative_to(ROOT)}", flush=True)
            except Exception as error:  # report and go on with the others
                print(f"{shot}: FAILED {error}", flush=True)
    print(f"cutscenes/ spend so far: USD {fal_api.logged_spend(SCOPE):.2f}")


def cmd_export(args) -> None:
    master = MASTERS / f"{args.shot}_v{args.version}.png"
    EXPORT.mkdir(parents=True, exist_ok=True)
    out = EXPORT / f"{args.shot}.webp"
    img = Image.open(master).convert("RGB")
    if args.crop:  # x0,y0,x1,y1 in master pixels, e.g. to drop black bars the model painted itself
        img = img.crop(tuple(int(v) for v in args.crop.split(",")))
    fit_to_frame(img).save(out, "WEBP", quality=90, method=6)
    sidecar = master.with_suffix(".json")
    meta = json.loads(sidecar.read_text(encoding="utf-8"))
    meta["exported"] = {"path": out.relative_to(ROOT).as_posix(), "crop": args.crop,
                        "at": datetime.datetime.now().isoformat(timespec="seconds")}
    sidecar.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{master.relative_to(ROOT)} -> {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KiB)")


def fill_box(arr: np.ndarray, box: tuple[int, int, int, int], feather: int = 5, tone: str = "light") -> None:
    """Free local retouch: paint a box over with its ground colour (median of its lighter pixels for paper, of its
    darker pixels for a chalkboard: tone="dark"), feathered at the edges, with a little noise so it does not look
    flat; used to blank stray lettering."""
    x0, y0, x1, y1 = box
    region = arr[y0:y1, x0:x1].astype(np.float32)
    lum = region.mean(axis=2)
    paper = np.median(region[lum >= np.percentile(lum, 55)] if tone == "light" else region[lum <= np.percentile(lum, 45)], axis=0)
    h, w = y1 - y0, x1 - x0
    ys, xs = np.mgrid[0:h, 0:w]
    edge = np.minimum.reduce([xs + 1, w - xs, ys + 1, h - ys]).astype(np.float32)
    alpha = np.clip(edge / feather, 0, 1)[..., None]
    rng = np.random.default_rng(1)
    fill = paper + rng.normal(0, 1.5, region.shape)
    arr[y0:y1, x0:x1] = (alpha * fill + (1 - alpha) * region).clip(0, 255).astype(np.uint8)


def cmd_retouch(args) -> None:
    src = MASTERS / f"{args.shot}_v{args.version}.png"
    arr = np.asarray(Image.open(src).convert("RGB")).copy()
    boxes = [tuple(int(v) for v in b.split(",")) for b in args.box]
    for box in boxes:
        fill_box(arr, box, tone=args.tone)
    version = next_version(args.shot)
    out = MASTERS / f"{args.shot}_v{version}.png"
    Image.fromarray(arr).save(out)
    meta = json.loads(src.with_suffix(".json").read_text(encoding="utf-8"))
    meta.update({"retouch_of": src.name, "retouch_boxes": boxes, "retouch_note": args.note, "usd": 0,
                 "at": datetime.datetime.now().isoformat(timespec="seconds")})
    meta.pop("exported", None)
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{src.name} -> {out.relative_to(ROOT)} (free local retouch, {len(boxes)} box(es))")


def cmd_prompt(args) -> None:
    prompt, paths = build_prompt(cutscene_shots.SHOTS[args.shot])
    print(prompt)
    print("\nimages:", *[p.relative_to(ROOT) for p in paths], sep="\n  ")


def cmd_list(_args) -> None:
    for shot_id, shot in cutscene_shots.SHOTS.items():
        versions = sorted(MASTERS.glob(f"{shot_id}_v*.png"))
        exported = (EXPORT / f"{shot_id}.webp").exists()
        print(f"{shot_id:12s} masters={len(versions)} exported={'yes' if exported else 'no '} camera={'yes' if shot.get('camera') else 'no'}")
    print(f"spend cutscenes/: USD {fal_api.logged_spend(SCOPE):.2f}")


def cmd_camera(_args) -> None:
    """Camera moves for the cutscene player: visible source rect at the start and the end of the beat."""
    data = {"_comment": ("Cutscene beat camera moves (presentation only, written by "
                         "art/tools/cutscenes.py camera from art/tools/cutscene_shots.py). Rects are [x, y, w, h] in "
                         "the 1920x1080 frame: the part of the picture that fills the view at the start ('from') and "
                         "at the end ('to') of the move, cover-fitted to the screen; a rect may reach up to 10 % of "
                         "its height above or below the picture (shown black, under the letterbox bars). 'seconds' "
                         "(default: the beat's duration_min_s) and 'ease' (in_out | out | linear, default in_out). "
                         "Reduced motion shows the 'to' rect without moving.")}
    for shot_id, shot in cutscene_shots.SHOTS.items():
        cam = shot.get("camera")
        if not cam:
            continue
        entry = {"from": cam["from"], "to": cam["to"]}
        for key in ("seconds", "ease"):
            if key in cam:
                entry[key] = cam[key]
        for rect in (entry["from"], entry["to"]):
            x, y, w, h = rect
            margin = 0.1 * h  # the letterbox bar height in rect units: a rect may reach under the bars
            if (x < 0 or x + w > 1920 or y < -margin - 0.5 or y + h > 1080 + margin + 0.5 or w < 1440
                    or abs(w / h - 16 / 9) > 0.02):
                sys.exit(f"{shot_id}: camera rect {rect} must be 16:9, at most 1.33x zoom and inside 1920x1080 "
                         "(vertically up to the letterbox margin)")
        data[shot_id] = entry
    lines = [f"  {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in data.items()]
    CAMERA_JSON.write_text("{\n" + ",\n".join(lines) + "\n}\n", encoding="utf-8")
    print(f"{CAMERA_JSON.relative_to(ROOT)}: {len(data) - 1} camera moves")


def cmd_contact(args) -> None:
    shots = args.shots or [s for s in cutscene_shots.SHOTS if (EXPORT / f"{s}.webp").exists()]
    cells = []
    for s in shots:
        path = EXPORT / f"{s}.webp" if not args.master else sorted(MASTERS.glob(f"{s}_v*.png"))[-1]
        img = Image.open(path).convert("RGB")
        img = fit_to_frame(img) if img.size != (1920, 1080) else img
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle((0, 0, 1920, 108), fill=(0, 0, 0, 150))
        d.rectangle((0, 972, 1920, 1080), fill=(0, 0, 0, 150))
        cam = cutscene_shots.SHOTS[s].get("camera")
        if cam:
            for rect, colour in ((cam["from"], (255, 220, 0, 255)), (cam["to"], (0, 220, 255, 255))):
                x, y, w, h = rect
                d.rectangle((x, y, x + w, y + h), outline=colour, width=6)
        d.text((20, 20), s, fill=(255, 255, 255, 255), font_size=48)
        cells.append(img.resize((960, 540)))
    cols = 2
    sheet = Image.new("RGB", (cols * 960, ((len(cells) + cols - 1) // cols) * 540), (30, 30, 30))
    for i, c in enumerate(cells):
        sheet.paste(c, ((i % cols) * 960, (i // cols) * 540))
    out = Path(args.out) if args.out else MASTERS / "contact.jpg"
    sheet.save(out, quality=85)
    print(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("prompt")
    p.add_argument("shot")
    p = sub.add_parser("paint")
    p.add_argument("shots", nargs="+")
    p.add_argument("--seed", type=int)
    p.add_argument("--budget", type=float, default=DEFAULT_BUDGET)
    p = sub.add_parser("export")
    p.add_argument("shot")
    p.add_argument("version", type=int)
    p.add_argument("--crop", help="x0,y0,x1,y1 crop of the master before the cover fit")
    p = sub.add_parser("retouch")
    p.add_argument("shot")
    p.add_argument("version", type=int)
    p.add_argument("--box", action="append", required=True, help="x0,y0,x1,y1 in master pixels")
    p.add_argument("--note", default="")
    p.add_argument("--tone", choices=["light", "dark"], default="light", help="ground: paper (light) or chalkboard (dark)")
    sub.add_parser("camera")
    p = sub.add_parser("contact")
    p.add_argument("shots", nargs="*")
    p.add_argument("--master", action="store_true")
    p.add_argument("--out")
    args = ap.parse_args()
    {"list": cmd_list, "prompt": cmd_prompt, "paint": cmd_paint, "export": cmd_export, "camera": cmd_camera,
     "contact": cmd_contact, "retouch": cmd_retouch}[args.cmd](args)


if __name__ == "__main__":
    main()
