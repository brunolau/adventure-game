"""Walk cycles for guest speakers (ISSUES PT-S18, DECISIONS "Guest speakers walk in briefly").

game.json actions[].staging.rule: Mira 60 walks into the S40 attic for I17, Tono 82 and Oto 82 walk to the S61
cache for E08, then leave again. Their NPC sets were made for standing still (no walk sheet; TONO82 is seated), so
this tool adds a three-quarter side walk loop (and for TONO82 a standing set) on top of the shipped sheets.

Paid (fal.ai, logged to art/spend-log.csv, refused above --budget for the scope characters/<ID>/guest_):
  stand  ID                  NB2 2K edit of the base sheet: the seated figure stands up (TONO82)
  fix    ID --base RAW         NB2 2K clean-up edit (remove left-over props / ghost limbs of the stand edit)
  face   ID blink|talk|talk_oh --base RAW   NB2 1K face edit of the standing sheet (TONO82 standing talk)
  video  ID [--image PNG]    Hailuo-02 Pro walk-in-place loop (start = end frame) from the walk canvas
Free (local):
  canvas ID [--sheet PNG]    key the (standing) sheet and write guest/video_in_walk.png (1080x1080)
  loop   ID                  guest/walk_right/: 12-cell loop scaled like the shipped idle (actor height_px)
  stills ID                  TONO82: guest/standing/ idle, blink, talk_a, talk_b from the standing edits
  export_standing TONO82     the standing set as actor.json variant "guest_standing" (after stills)
  export ID                  WebP sheets + the actor.json entries (walk sheet and "walk_right" animation, plus a
                             "standing" variant for TONO82) in src/game/assets/actors/<ID>/

Run from art/tools, e.g.:
  python guest_walks.py --budget 1.2 stand TONO82
  python guest_walks.py canvas MIRA60 && python guest_walks.py --budget 0.6 video MIRA60
  python guest_walks.py loop MIRA60 && python guest_walks.py export MIRA60
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

import chars
import export_actors
import fal_api
import frames

ART = fal_api.ART
REPO = ART.parent
CHAR_ROOT = ART / "characters"
GAME_ACTORS = REPO / "src" / "game" / "assets" / "actors"
VIDEO_ENDPOINT = "fal-ai/minimax/hailuo-02/pro/image-to-video"
NB2 = "fal-ai/nano-banana-2/edit"

PERSON = {
    "MIRA60": ("young woman", "She", "her", "keeps holding the pencil loosely in her right hand"),
    "OTO82": ("older man", "He", "his", "keeps holding the long metal file in his right hand"),
    "TONO82": ("boy", "He", "his", "keeps holding the folded paper swallow in front of him with both hands"),
}

WALK_PROMPT = (
    "The {person} walks in place, as if on a treadmill, with a natural relaxed walking cycle: legs stepping and arms "
    "swinging gently in alternation; {pron_l} {hold}. {Pron} stays in exactly the same spot in the centre of the frame "
    "and keeps exactly the same three-quarter view turned toward the right as in the first frame, at the same size. "
    "Seamless loop. The camera is completely static: no pan, no zoom, no camera shake. The background stays a "
    "perfectly flat uniform green the whole time, with no floor, no shadow and nothing else appearing. Same "
    "hand-painted style throughout."
)

STAND_PROMPT = (
    "Edit the first image: the same boy, with exactly the same face, hair, sweater, scarf, trousers and boots, now "
    "STANDS upright on both feet in the same three-quarter view turned toward the right, relaxed, holding the folded "
    "paper swallow in front of his chest with both hands. Remove the stool and the school briefcase completely. "
    "The complete body from the top of the hair to the soles of the boots is visible, with green margin on every "
    "side; both feet stand on the same invisible ground line. Keep his face, hair colour, skin tone and the soft even "
    "lighting exactly as in the first image: no dappled light spots or sun patches on him or his clothes."
)

FACE_PROMPTS = {
    "blink": ("Edit the first image: keep everything exactly the same (same boy, same pose, same position and size, "
              "same flat green background) and change ONLY his eyes: they are closed in a natural blink."),
    "talk": ("Edit the first image: keep everything exactly the same (same boy, same pose, same position and size, "
             "same flat green background) and change ONLY his mouth: it is open as if saying 'ah' in mid-sentence."),
    "talk_oh": ("Edit the first image: keep everything exactly the same (same boy, same pose, same position and "
                "size, same flat green background) and change ONLY his mouth: rounded as if saying 'oh'."),
}


def cdir(char: str) -> Path:
    return CHAR_ROOT / char / "guest"


def budget(args: argparse.Namespace, char: str) -> tuple[str, float]:
    return (f"characters/{char}/guest_", args.budget)


def save_result(result: dict, out_base: Path, meta: dict) -> list[Path]:
    """Download the outputs; retry, because a broken download loses an already billed result."""
    out_base.parent.mkdir(parents=True, exist_ok=True)
    (out_base.parent / (out_base.name + "_result.json")).write_text(json.dumps(result, indent=1), encoding="utf-8")
    for attempt in range(5):
        try:
            return chars.save_outputs(result, out_base, meta)
        except Exception as exc:  # network errors from requests
            print(f"download failed ({exc}); retry {attempt + 1}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"{out_base.name}: downloads failed; result URLs in {out_base.name}_result.json")


def cmd_stand(args: argparse.Namespace) -> None:
    base = CHAR_ROOT / args.char / "sheet_3q.png"
    prompt = " ".join([STAND_PROMPT, chars.key_background("green"), chars.STYLE_FOR_CHARACTER + chars.STYLE_A])
    price = fal_api.IMAGE_PRICES[(NB2, "2K")]
    arguments = {"prompt": prompt, "image_urls": chars.image_inputs([base], None), "aspect_ratio": "3:4",
                 "resolution": "2K", "output_format": "png", "num_images": 1, "seed": args.seed}
    name = args.out or "guest_stand_nb2"
    result = fal_api.run(NB2, arguments, f"characters/{args.char}/{name}", price, budget=budget(args, args.char))
    meta = {"model": NB2, "usd": price, "prompt": prompt, "references": [str(base.relative_to(ART))], "seed": args.seed}
    print("\n".join(str(p) for p in save_result(result, cdir(args.char) / name, meta)))


FIX_PROMPT = (
    "Edit the first image: keep the standing boy exactly as he is (same face, hair, sweater, scarf, trousers, boots, "
    "paper swallow, same pose, position and size). Remove everything else: the brown school briefcase on the left "
    "and the faint ghost-like extra leg and boot to the right of him must disappear completely, so only the one boy "
    "stands on the perfectly flat uniform green background."
)


def cmd_fix(args: argparse.Namespace) -> None:
    base = Path(args.base).resolve()
    prompt = " ".join([FIX_PROMPT, chars.key_background("green")])
    price = fal_api.IMAGE_PRICES[(NB2, "2K")]
    arguments = {"prompt": prompt, "image_urls": chars.image_inputs([base], None), "aspect_ratio": "3:4",
                 "resolution": "2K", "output_format": "png", "num_images": 1, "seed": args.seed}
    name = args.out or "guest_stand_fix_nb2"
    result = fal_api.run(NB2, arguments, f"characters/{args.char}/{name}", price, budget=budget(args, args.char))
    meta = {"model": NB2, "usd": price, "prompt": prompt, "references": [base.name], "seed": args.seed}
    print("\n".join(str(p) for p in save_result(result, cdir(args.char) / name, meta)))


def cmd_face(args: argparse.Namespace) -> None:
    base = Path(args.base).resolve()
    prompt = " ".join([FACE_PROMPTS[args.pose], chars.key_background("green"), chars.STYLE_FOR_CHARACTER + chars.STYLE_A])
    price = fal_api.IMAGE_PRICES[(NB2, "1K")]
    arguments = {"prompt": prompt, "image_urls": chars.image_inputs([base], None), "aspect_ratio": "3:4",
                 "resolution": "1K", "output_format": "png", "num_images": 1, "seed": args.seed}
    name = f"guest_face_{args.pose}_nb2"
    result = fal_api.run(NB2, arguments, f"characters/{args.char}/{name}", price, budget=budget(args, args.char))
    meta = {"model": NB2, "usd": price, "prompt": prompt, "references": [base.name], "seed": args.seed}
    print("\n".join(str(p) for p in save_result(result, cdir(args.char) / name, meta)))


def keyed_sheet(char: str, sheet: str | None) -> np.ndarray:
    path = Path(sheet) if sheet else CHAR_ROOT / char / "sheet_3q.png"
    img = Image.open(path)
    if img.mode == "RGBA" and np.asarray(img)[..., 3].min() < 255:  # already keyed (e.g. TONO82 keyed_stand.png)
        return frames.crop_to_figure(np.asarray(img).copy())
    return frames.crop_to_figure(frames.chroma_key(frames.load_rgb(path)))


def cmd_canvas(args: argparse.Namespace) -> None:
    keyed = keyed_sheet(args.char, args.sheet)
    frames.save_rgba(keyed, cdir(args.char) / "keyed_walk_base.png")
    canvas = frames.figure_on_canvas(keyed, (1080, 1080), args.height, 0.90)
    out = cdir(args.char) / "video_in_walk.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    print(out, frames.key_quality(keyed))


def cmd_video(args: argparse.Namespace) -> None:
    person, pron, pron_l, hold = PERSON[args.char]
    prompt = WALK_PROMPT.format(person=person, Pron=pron, pron_l=pron_l, hold=hold)
    image = Path(args.image) if args.image else cdir(args.char) / "video_in_walk.png"
    uri = fal_api.image_data_uri(image, fmt="PNG")
    arguments = {"prompt": prompt, "image_url": uri, "end_image_url": uri, "prompt_optimizer": False}
    price = fal_api.video_price(VIDEO_ENDPOINT, 6.0, "1080P")
    name = args.out or "guest_walk_hailuo_pro"
    result = fal_api.run(VIDEO_ENDPOINT, arguments, f"characters/{args.char}/{name}", price,
                         budget=budget(args, args.char), timeout_s=1800, poll_s=8)
    meta = {"model": VIDEO_ENDPOINT, "usd": round(price, 4), "prompt": prompt, "input": image.name, "tail_image": True,
            "seconds": 6.0, "resolution": "1080P"}
    print("\n".join(str(p) for p in save_result(result, cdir(args.char) / name, meta)))


def shipped_height(char: str, variant: str | None) -> float:
    manifest = json.loads((GAME_ACTORS / char / "actor.json").read_text(encoding="utf-8"))
    if char == "TONO82":
        return 512.0 * 152 / 175  # a 12-year-old standing: 152 cm on the 175 cm = 512 px scale
    return float(manifest.get("height_px", 512))


def cmd_loop(args: argparse.Namespace) -> None:
    d = cdir(args.char)
    video = d / (args.video or "guest_walk_hailuo_pro.mp4")
    fdir = d / "_frames"
    paths = frames.extract_frames(video, fdir)
    info = frames.video_info(video)
    fps = float(info.get("fps", 24))
    # scale: the standing first frame maps to the shipped figure height
    first = frames.chroma_key(frames.load_rgb(paths[0]))
    box = frames.alpha_bbox(first)
    ref = float(box[3] - box[1])
    meta = frames.build_loop(paths, d / "walk_right", fps, args.frames, (0.8, 1.6), 0.6, 0.2, True,
                             round(shipped_height(args.char, None)), None, None, "walk_right", ref_height=ref)
    print(json.dumps(meta, indent=1))


def clean_tono_stand(rgb: np.ndarray) -> np.ndarray:
    """Key a TONO82 stand edit and cut what NB2 left of the seated pose (briefcase, a faint ghost leg); boxes placed by
    eye on guest_stand_fix_nb2.png (448 px wide preview units); only the largest figure component is kept."""
    from PIL import ImageDraw, ImageFilter
    k = frames.chroma_key(rgb)
    h, w = k.shape[:2]
    s = w / 448
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.rectangle([0, int(395 * s), int(160 * s), h], fill=255)
    d.polygon([(int(282 * s), int(330 * s)), (w, int(330 * s)), (w, h), (int(303 * s), h), (int(303 * s), int(450 * s)),
               (int(282 * s), int(440 * s))], fill=255)
    k[np.array(mask) > 0, 3] = 0
    for x0, x1, y0, y1 in ((0, 172, 395, 472), (0, 162, 472, 600), (321, 448, 445, 512)):
        k[int(y0 * s):int(y1 * s), int(x0 * s):int(x1 * s), 3] = 0
    lab, sizes = frames.label_components(k[..., 3] > 24)
    keep = int(np.argmax(sizes)) + 1  # sizes[i] belongs to label i + 1
    grown = np.array(Image.fromarray(((lab == keep) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
    k[~grown, 3] = 0
    return k


def mouth_patch(base: np.ndarray, edit: np.ndarray, centre: tuple[int, int], radii: tuple[int, int]) -> np.ndarray:
    """Transplant only the mouth (soft ellipse) of an aligned face edit onto the base, so nothing else flickers."""
    from PIL import ImageDraw, ImageFilter
    h, w = base.shape[:2]
    m = Image.new("L", (w, h), 0)
    cx, cy = centre
    rx, ry = radii
    ImageDraw.Draw(m).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    m = np.asarray(m.filter(ImageFilter.GaussianBlur(10)), dtype=np.float32)[..., None] / 255.0
    return (base * (1 - m) + edit * m).astype(np.uint8)


def cmd_stills(args: argparse.Namespace) -> None:
    """TONO82 standing guest set: idle (= blink = gesture, no edit), talk_a ('ah') and talk_b ('oh') on one pivot."""
    d = cdir(args.char)
    base = frames.load_rgb(d / "guest_stand_fix_nb2.png")
    size = (base.shape[1], base.shape[0])
    edits = {name: np.asarray(Image.open(d / f"guest_face_{name}_nb2.png").convert("RGB").resize(size, Image.Resampling.LANCZOS))
             for name in ("talk", "talk_oh")}
    centre, radii = (935, 572), (78, 50)  # the mouth on the 1792x2400 stand edit
    layers = {"idle": clean_tono_stand(base),
              "talk_a": clean_tono_stand(mouth_patch(base, edits["talk"], centre, radii)),
              "talk_b": clean_tono_stand(mouth_patch(base, edits["talk_oh"], centre, radii))}
    box = frames.alpha_bbox(layers["idle"])
    x0, y0, x1, y1 = box
    height = round(shipped_height(args.char, None))
    scale = height / (y1 - y0)
    cw = int(np.ceil((x1 - x0) * scale)) + 8
    cw += cw % 2
    ch = height + 8
    names = ["idle", "blink", "talk_a", "talk_b", "gesture"]
    sheet = Image.new("RGBA", (cw * len(names), ch), (0, 0, 0, 0))
    for i, name in enumerate(names):
        src = layers["talk_a" if name == "talk_a" else "talk_b" if name == "talk_b" else "idle"]
        img = Image.fromarray(src[y0:y1, x0:x1], "RGBA").resize((cw - 8, height), Image.Resampling.LANCZOS)
        sheet.paste(img, (i * cw + 4, 4), img)
    out = d / "standing"
    out.mkdir(parents=True, exist_ok=True)
    sheet.save(out / "guest_standing_sheet.png")
    meta = {"frames": len(names), "cell": [cw, ch], "pivot": [cw // 2, ch - 4], "frame_names": names, "columns": len(names),
            "rows": 1, "playback_fps": 8, "source": "art/tools/guest_walks.py stills (NB2 stand edit + mouth transplants)"}
    (out / "guest_standing_sheet.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    preview = Image.new("RGBA", sheet.size, (110, 110, 110, 255))
    preview.alpha_composite(sheet)
    preview.convert("RGB").save(out / "guest_standing_review.jpg", quality=90)
    print(out, meta)


def cmd_export_standing(args: argparse.Namespace) -> None:
    """TONO82: the standing guest set as actor.json variant 'guest_standing' (the seated default stays for S64)."""
    d = cdir(args.char) / "standing"
    dst = GAME_ACTORS / args.char
    img = Image.open(d / "guest_standing_sheet.png").convert("RGBA")
    img.save(dst / "guest_standing_sheet.webp", "WEBP", lossless=True)
    meta = json.loads((d / "guest_standing_sheet.json").read_text(encoding="utf-8"))
    (dst / "guest_standing_sheet.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    manifest_path = dst / "actor.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sheets"]["guest_standing"] = {"file": "guest_standing_sheet.webp", "json": "guest_standing_sheet.json",
                                            "size": [img.width, img.height], "cell": meta["cell"], "pivot": meta["pivot"],
                                            "frames": meta["frames"], "columns": meta["columns"], "rows": 1}
    still = {"sheet": "guest_standing", "frames": ["idle"]}
    manifest.setdefault("variants", {})["guest_standing"] = {
        "height_px": round(shipped_height(args.char, None), 1),
        "note": "standing guest for E08 at S61 (ISSUES PT-S18): walks in with walk_right, stands, talks",
        "animations": {
            "idle": still, "idle_still": still,
            "blink": {"sheet": "guest_standing", "frames": ["blink"], "hold_ms": 110, "every_s": [2.5, 6.0]},
            "talk": {"sheet": "guest_standing", "frames": ["talk_a", "talk_b", "talk_a", "idle", "talk_b", "talk_a", "idle"],
                     "fps": 8, "loop": True},
            "gesture": {"sheet": "guest_standing", "frames": ["gesture"], "hold_ms": 1200, "oneshot": True},
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(dst / "guest_standing_sheet.webp", img.size)


def cmd_export(args: argparse.Namespace) -> None:
    d = cdir(args.char)
    dst = GAME_ACTORS / args.char
    src_png = d / "walk_right" / "walk_right_sheet.png"
    src_json = json.loads((d / "walk_right" / "walk_right_sheet.json").read_text(encoding="utf-8"))
    strip = Image.open(src_png).convert("RGBA")
    cell = src_json["cell"]
    n = src_json["frames"]
    # grids of at most 4096 px for mobile GPUs (ISSUES LIVING-04 / BUILD-01)
    columns = n
    while columns * cell[0] > 4096:
        columns = -(-n // (-(-n // columns) + 1))
    rows = -(-n // columns)
    img = Image.new("RGBA", (columns * cell[0], rows * cell[1]), (0, 0, 0, 0))
    for i in range(n):
        tile = strip.crop((i * cell[0], 0, (i + 1) * cell[0], cell[1]))
        img.paste(tile, ((i % columns) * cell[0], (i // columns) * cell[1]))
    out = dst / "walk_sheet.webp"
    img.save(out, "WEBP", lossless=True)
    sheet_meta = {
        "frames": n, "cell": cell, "pivot": src_json["pivot"],
        "columns": columns, "rows": rows, "playback_fps": src_json["playback_fps"],
        "stride_px_per_s": src_json.get("stride_px_per_s"), "source": "art/tools/guest_walks.py (Hailuo-02 Pro)",
    }
    (dst / "walk_sheet.json").write_text(json.dumps(sheet_meta, indent=2), encoding="utf-8")
    manifest_path = dst / "actor.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.setdefault("sheets", {})["walk"] = {"file": "walk_sheet.webp", "json": "walk_sheet.json",
                                                 "size": [img.width, img.height], "cell": cell,
                                                 "pivot": src_json["pivot"], "frames": n,
                                                 "columns": columns, "rows": rows}
    manifest.setdefault("animations", {})["walk_right"] = {
        "sheet": "walk", "loop": True, "fps": src_json["playback_fps"],
        "note": "guest walk-in (ISSUES PT-S18): three-quarter side walk, mirrored for left"}
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out, img.size, sheet_meta)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--budget", type=float, default=1.0, help="USD cap for characters/<ID>/guest_*")
    p.add_argument("--seed", type=int, default=1982)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stand"); s.add_argument("char"); s.add_argument("--out")
    s = sub.add_parser("fix"); s.add_argument("char"); s.add_argument("--base", required=True); s.add_argument("--out")
    s = sub.add_parser("face"); s.add_argument("char"); s.add_argument("pose", choices=FACE_PROMPTS)
    s.add_argument("--base", required=True)
    s = sub.add_parser("canvas"); s.add_argument("char"); s.add_argument("--sheet"); s.add_argument("--height", type=float, default=0.80)
    s = sub.add_parser("video"); s.add_argument("char"); s.add_argument("--image"); s.add_argument("--out")
    s = sub.add_parser("loop"); s.add_argument("char"); s.add_argument("--video"); s.add_argument("--frames", type=int, default=12)
    s = sub.add_parser("export"); s.add_argument("char")
    s = sub.add_parser("stills"); s.add_argument("char")
    s = sub.add_parser("export_standing"); s.add_argument("char")
    args = p.parse_args()
    {"stand": cmd_stand, "fix": cmd_fix, "face": cmd_face, "canvas": cmd_canvas, "video": cmd_video, "loop": cmd_loop,
     "export": cmd_export, "stills": cmd_stills, "export_standing": cmd_export_standing}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
