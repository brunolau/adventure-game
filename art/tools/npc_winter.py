"""Winter variants of the Jasna 2035 outdoor NPCs (owner 2026-10-06: "Jasna 2035 is in winter").

NINA (S42, forecourt), IVAN (S67, the open Priehyba station hall) and TURISTA (S68, the unheated Funitel cabin) were
painted for alpine June. This tool re-dresses their accepted sets for 6 February 2035 without re-posing them and ships
the result as an actor.json variant `winter` (sheets `npc_winter`, `idle_winter`, `idle_fidget_winter` next to the
default sheets), selected per room in the natural blocking (`npcs.<id>.variant = "winter"`).

Paid (fal.ai, logged to art/spend-log.csv under characters/<ID>/winter/; refused beyond --budget for this task):
  redress ID [--seed N]     NB2 2K edit of the accepted base sheet: same person, pose, size; winter clothes only
  gesture ID                NB2 2K edit of the winter base with the brief's gesture (the clothes come from image 1)
  video   ID                Hailuo-02 Pro 6 s idle loop (start = end) from the winter canvas (NINA: blue canvas)
Free (local):
  build   ID                winter/npc_set: idle, blink, talk_a, talk_b, gesture. The winter base is aligned to the
                            default base by the feet; inside the head the default face is taken over wherever the
                            edit painted (nearly) the same pixels, so the default blink and mouth frames apply
                            unchanged (no new face edits, no flicker); also writes the video canvas
  idle    ID / calm ID      npc_prod.py idle / calm on the winter folder (same scale and pivot as the stills)
  export  ID                WebP grids into src/game/assets/actors/<ID>/ (*_winter) + the `winter` variant in
                            actor.json (the default sheets and animations are left untouched)
  review  ID                art/characters/<ID>/winter/review.jpg: default | winter stills, face zoom

Run from art/tools with PYTHONIOENCODING=utf-8 python -X utf8 npc_winter.py ...
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

import chars
import fal_api
import frames
import hero_coat
import npc_prod
import npcs

ART = fal_api.ART
CHAR_ROOT = ART / "characters"
GAME_ACTORS = ART.parent / "src" / "game" / "assets" / "actors"
TASK_SINCE = "2026-10-06T01:40"
TASK_PREFIXES = ("characters/NINA/winter/", "characters/IVAN/winter/", "characters/TURISTA/winter/",
                 "ambient/jasna_winter/")
CAST = ("NINA", "IVAN", "TURISTA")

WINTER = {
    "NINA": {
        "keep": "the same woman with the same face, the same dark brown hair worn loose with the side part, the same "
                "pose with the arms hanging relaxed, the same position and size in the frame, on the same flat "
                "magenta background",
        "clothes": "Change ONLY her clothes for a clear, freezing February day in the snowy mountains: her coat is "
                   "now a warm, thick knee-length winter wool coat in the same dark bottle-green, buttoned closed up "
                   "to the collar; a soft charcoal-grey knitted scarf is wrapped once around her neck with its short "
                   "ends tucked into the coat; thin black knitted gloves on both hands; the same slim black "
                   "trousers; black waterproof winter ankle boots with a little snow on the toes instead of the "
                   "white trainers. The service identification card (white card, small photo square, simple blue "
                   "circle emblem, no readable text) on its plain dark grey lanyard now hangs on the outside of the "
                   "closed coat in front of her chest. No hat, no earmuffs, no bag.",
        "who": "her",
    },
    "IVAN": {
        "keep": "the same man with the same face, the same short dark brown hair line, the same pose with the arms "
                "hanging relaxed, the same position and size in the frame, on the same flat green background",
        "clothes": "Change ONLY his clothes for a freezing February day at a high mountain cable-car station: he now "
                   "wears a thick padded insulated winter work parka in the same dark slate-blue with the same "
                   "signal-orange shoulder panels, zipped up to the chin with a high collar, the same small round "
                   "neutral patch with only a simple white cable-car cabin pictogram on the chest (no letters, no "
                   "logo) and the same small black two-way radio clipped beside it; a plain dark grey knitted beanie "
                   "covering the top of his head and his ears; black insulated work gloves; dark grey insulated "
                   "winter work trousers; the same brown boots with a little snow on the toes. No text, no logo, no "
                   "goggles, no face mask.",
        "who": "him",
    },
    "TURISTA": {
        "keep": "the same man with the same face, the same neatly trimmed grey moustache, the same pose, the same "
                "position and size in the frame, on the same flat green background",
        "clothes": "Change ONLY his clothes for a freezing February day trip to the snowy mountains: instead of the "
                   "beige bucket sun hat he wears a warm knitted dark-blue beanie with a small grey bobble, his "
                   "salt-and-pepper hair showing a little at the temples; instead of the light hiking jacket a "
                   "padded brick-red ski jacket, zipped up, with a high collar; dark grey padded ski trousers; "
                   "grey-brown winter hiking boots with a little snow on the toes; thin black gloves. The same small "
                   "dark blue daypack on both shoulders and the same small black compact camera on its wrist strap "
                   "in his near hand at waist height. Ordinary winter clothes, no brand logos, no text, no goggles.",
        "who": "him",
    },
}


def task_spent() -> float:
    with fal_api.SPEND_LOG.open(encoding="utf-8") as handle:
        return sum(float(r["usd"]) for r in csv.DictReader(handle)
                   if r["asset"].startswith(TASK_PREFIXES) and r["timestamp"] >= TASK_SINCE)


def guard(args: argparse.Namespace, asset: str, usd: float, reserved: float = 0.0) -> None:
    spent = task_spent()
    if spent + reserved + usd > args.budget + 1e-9:
        sys.exit(f"BUDGET: {asset}: {spent:.3f} (+{reserved:.3f} in flight) + {usd:.3f} USD would exceed the "
                 f"{args.budget:.2f} USD task cap")
    print(f"[budget] {spent:.3f} spent of {args.budget:.2f}; this call {usd:.3f}", file=sys.stderr)


def wdir(char_id: str) -> Path:
    return CHAR_ROOT / char_id / "winter"


def key_word(char_id: str) -> str:
    return npcs.key_of(npcs.load_brief(char_id))


def nb2_edit(args: argparse.Namespace, char_id: str, prompt: str, src: Path, out_name: str) -> list[Path]:
    model = "fal-ai/nano-banana-2/edit"
    price = fal_api.IMAGE_PRICES[(model, "2K")]
    asset = f"characters/{char_id}/winter/{out_name}"
    guard(args, asset, price)
    arguments = {"prompt": prompt, "image_urls": [fal_api.image_data_uri(src, max_side=2400)], "aspect_ratio": "3:4",
                 "resolution": "2K", "output_format": "png", "num_images": 1, "seed": args.seed}
    result = fal_api.run(model, arguments, asset, price, budget=None, timeout_s=600)
    meta = {"model": model, "usd": price, "prompt": prompt, "aspect_ratio": "3:4", "resolution": "2K",
            "references": [str(src.relative_to(ART))], "seed": args.seed}
    return hero_coat.save_result(result, wdir(char_id) / out_name, meta)


def redress_prompt(char_id: str) -> str:
    w = WINTER[char_id]
    key = key_word(char_id)
    return " ".join([
        f"Edit the first image: {w['keep']}. {w['clothes']} {w['who'].capitalize()} face, eyes, mouth, expression "
        f"and skin tone stay exactly as they are. Do not move, turn or rescale {w['who']}; the feet stay exactly "
        "where they are.",
        npc_prod.HUMAN_GUARD.format(**npcs.words_of(npcs.load_brief(char_id))),
        chars.key_background(key), chars.recolour_key_words(chars.STYLE_FOR_CHARACTER, key) + chars.STYLE_A])


def cmd_redress(args: argparse.Namespace) -> None:
    ids = args.ids or list(CAST)
    price = fal_api.IMAGE_PRICES[("fal-ai/nano-banana-2/edit", "2K")]
    guard(args, "batch", 0.0, reserved=price * len(ids))
    tag = args.tag or ""

    def one(char_id: str) -> list[Path]:
        return nb2_edit(args, char_id, redress_prompt(char_id), CHAR_ROOT / char_id / "sheet_npc_3q.png",
                        f"sheet_winter{tag}")
    with ThreadPoolExecutor(max_workers=3) as pool:
        for char_id, paths in zip(ids, pool.map(one, ids)):
            print(char_id, [str(p) for p in paths])


def cmd_gesture(args: argparse.Namespace) -> None:
    ids = args.ids or list(CAST)
    price = fal_api.IMAGE_PRICES[("fal-ai/nano-banana-2/edit", "2K")]
    guard(args, "batch", 0.0, reserved=price * len(ids))
    tag = args.tag or ""

    def one(char_id: str) -> list[Path]:
        brief = npcs.load_brief(char_id)
        key = npcs.key_of(brief)
        words = npcs.words_of(brief)
        prompt = " ".join([npcs.GESTURE_PROMPT.format(**words), npc_prod.HUMAN_GUARD.format(**words),
                           "The winter clothes (coat or jacket, scarf, hat, gloves, boots) stay exactly as they are.",
                           args.extra or "", chars.key_background(key),
                           chars.recolour_key_words(chars.STYLE_FOR_CHARACTER, key) + chars.STYLE_A])
        prompt = chars.recolour_key_words(prompt, key)
        return nb2_edit(args, char_id, prompt, wdir(char_id) / "sheet_npc_3q.png", f"pose_gesture_winter{tag}")
    with ThreadPoolExecutor(max_workers=3) as pool:
        for char_id, paths in zip(ids, pool.map(one, ids)):
            print(char_id, [str(p) for p in paths])


def cmd_video(args: argparse.Namespace) -> None:
    ids = args.ids or list(CAST)
    endpoint, resolution = npc_prod.VIDEO_ENGINES["hailuo_pro"]
    price = fal_api.video_price(endpoint, 6.0, resolution)
    guard(args, "batch", 0.0, reserved=price * len(ids))
    tag = args.tag or ""

    def one(char_id: str) -> list[Path]:
        brief = npcs.load_brief(char_id)
        key = npcs.key_of(brief)
        bg = brief.get("video_canvas") or key
        prompt = chars.recolour_key_words(brief["idle_motion"] + npcs.IDLE_SUFFIX, bg)
        if args.extra:
            prompt = args.extra + " " + prompt
        image = wdir(char_id) / "video_in_3q.png"
        uri = fal_api.image_data_uri(image, fmt="PNG")
        arguments = {"prompt": prompt, "image_url": uri, "end_image_url": uri, "prompt_optimizer": False}
        name = f"video_idle_winter{tag}"
        asset = f"characters/{char_id}/winter/{name}"
        guard(args, asset, price)
        result = fal_api.run(endpoint, arguments, asset, price, budget=None, timeout_s=1800, poll_s=8)
        meta = {"model": endpoint, "usd": round(price, 4), "prompt": prompt, "input": image.name, "tail_image": True,
                "seconds": 6.0, "resolution": resolution,
                "arguments": {k: v for k, v in arguments.items() if not str(v).startswith("data:")}}
        return hero_coat.save_result(result, wdir(char_id) / name, meta)
    with ThreadPoolExecutor(max_workers=3) as pool:
        for char_id, paths in zip(ids, pool.map(one, ids)):
            print(char_id, [str(p) for p in paths])


# ----------------------------------------------------------------------------- local build

def hsv(rgba: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return hero_coat.hsv_of(np.ascontiguousarray(rgba[..., :3]))


def skin(rgba: np.ndarray) -> np.ndarray:
    h, s, v = hsv(rgba)
    return (h < 50) & (s > 0.12) & (s < 0.72) & (v > 0.30) & (rgba[..., 3] > 200)


def blend(a: np.ndarray, b: np.ndarray, m: np.ndarray) -> np.ndarray:
    """Premultiplied blend of two keyed layers: m = 0 -> a, 1 -> b."""
    mm = m[..., None].astype(np.float32)
    aa, ab = a[..., 3:4].astype(np.float32) / 255, b[..., 3:4].astype(np.float32) / 255
    alpha = aa * (1 - mm) + ab * mm
    premul = a[..., :3].astype(np.float32) * aa * (1 - mm) + b[..., :3].astype(np.float32) * ab * mm
    with np.errstate(divide="ignore", invalid="ignore"):
        rgb = np.where(alpha > 1e-3, premul / np.maximum(alpha, 1e-3), 0)
    return np.dstack([rgb, alpha * 255]).clip(0, 255).astype(np.uint8)


def on_key(rgba: np.ndarray, colour: tuple[int, int, int]) -> np.ndarray:
    a = rgba[..., 3:4].astype(np.float32) / 255
    return (rgba[..., :3].astype(np.float32) * a + np.array(colour, np.float32) * (1 - a)).clip(0, 255).astype(np.uint8)


def largest(mask: np.ndarray) -> np.ndarray:
    labels, sizes = frames.label_components(mask)
    if len(sizes) == 0:
        return mask
    return labels == (int(np.argmax(sizes)) + 1)


def face_weight(dk: np.ndarray, wk: np.ndarray) -> tuple[np.ndarray, dict]:
    """Where the winter base takes the default face: skin (holes filled: eyes, brows, lips) of BOTH figures in the
    head rows, i.e. face pixels that the edit did not cover with a hat brim, a scarf or a collar."""
    x0, y0, x1, y1 = frames.alpha_bbox(dk)
    h = y1 - y0
    rows = np.zeros(dk.shape[:2], bool)
    rows[y0:y0 + int(0.205 * h)] = True
    # closing (radius 14 canvas px) bridges the eyes and brows where they touch the hair, then the holes are filled
    close = lambda m: hero_coat.fill_holes(hero_coat.shrink(hero_coat.grow(m, 14), 14))
    face_d = close(hero_coat.grow(hero_coat.shrink(skin(dk) & rows, 1), 1)) & (dk[..., 3] > 200)
    face_w = close(hero_coat.grow(hero_coat.shrink(skin(wk) & rows, 1), 1)) & (wk[..., 3] > 200)
    face = largest(face_d & face_w & rows)
    face = hero_coat.fill_holes(face)
    core = hero_coat.shrink(face, 2)
    m = Image.fromarray((core * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(2.0))
    weight = np.asarray(m, np.float32) / 255
    ys, xs = np.nonzero(core)
    return weight, {"face_px": int(core.sum()), "face_box": [int(xs.min()), int(ys.min()), int(xs.max()),
                                                             int(ys.max())] if len(xs) else None}


def cmd_build(args: argparse.Namespace) -> None:
    char_id = args.id
    brief = npcs.load_brief(char_id)
    key = npcs.key_of(brief)
    colour = tuple(frames.KEY_COLOURS[key])
    src = CHAR_ROOT / char_id
    out = wdir(char_id)
    d_rgb = frames.load_rgb(src / "sheet_npc_3q.png")
    dk = frames.chroma_key(d_rgb)
    w_rgb = npc_prod.load_rgb_like(out / (args.sheet or "sheet_winter.png"), d_rgb)
    wk = hero_coat.main_figure(frames.chroma_key(w_rgb))
    # align by the figure (alpha), then check the face separately
    dy, dx = frames.phase_shift(dk[..., 3].astype(np.float32), wk[..., 3].astype(np.float32))
    wk = np.roll(wk, (dy, dx), axis=(0, 1))
    bd, bw = frames.alpha_bbox(dk), frames.alpha_bbox(wk)
    x0, y0, x1, y1 = bd
    h = y1 - y0
    head = (slice(y0, y0 + int(0.2 * h)), slice(max(0, x0 - 20), x1 + 20))
    lum = lambda im: (im[..., :3].astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)) * (im[..., 3] / 255)
    hdy, hdx = frames.phase_shift(lum(dk)[head], lum(wk)[head])
    if abs(hdy) <= 6 and abs(hdx) <= 6 and (hdy or hdx):
        # the head drifted against the body: follow the head (the face must sit where the default face sits)
        print(f"head offset {hdy},{hdx} after the body alignment: following the head")
        wk = np.roll(wk, (hdy, hdx), axis=(0, 1))
    weight, freport = face_weight(dk, wk)
    base = blend(wk, dk, weight)
    report = {"body_shift_dy_dx": [int(dy), int(dx)], "head_shift_after_body": [int(hdy), int(hdx)],
              "default_box": list(bd), "winter_box": list(frames.alpha_bbox(base)),
              "feet_bottom_delta_px": int(bw[3] - bd[3]) if bw else None, **freport}
    frames.save_rgba(base, out / "keyed" / "base_winter.png")
    Image.fromarray(on_key(base, colour)).save(out / "sheet_npc_3q.png")
    # face frames: the default construction (npc_prod.py stills) on the default base, then the same face weight
    meta_d = json.loads((src / "npc_set" / "npc_sheet.json").read_text(encoding="utf-8"))
    bands = meta_d["face_bands"]
    layers = [base]
    for label, edit, band in (("blink", "pose_blink_nb2.png", bands["blink_band"]),
                              ("talk_a", "pose_talk_nb2.png", bands["talk_band"]),
                              ("talk_b", "pose_talk_oh_nb2.png", bands["talk_band"])):
        dx_full, _ = frames.patch_pose(d_rgb, npc_prod.load_rgb_like(src / edit, d_rgb), tuple(band), feather=8)
        layers.append(blend(wk, dx_full, weight))
    gesture_src = out / (args.gesture or "pose_gesture_winter.png")
    if gesture_src.exists():
        g_rgb = npc_prod.load_rgb_like(gesture_src, d_rgb)
        gesture, grep = frames.patch_pose(on_key(base, colour), g_rgb, (0.0, 1.0), feather=6, threshold=20.0)
        gesture = hero_coat.main_figure(gesture)
        report["gesture"] = grep
    else:
        print("no winter gesture yet: the gesture cell repeats the idle")
        gesture = base
    layers.append(gesture)
    scale = meta_d["height_px"] / (y1 - y0)
    pivot_x = frames.torso_center_x(dk)
    cells, cell, pivot = npc_prod.place_cells(layers, pivot_x, y1, scale)
    labels = ["idle", "blink", "talk_a", "talk_b", "gesture"]
    bw2 = frames.alpha_bbox(base)
    height_px = int(round((bw2[3] - bw2[1]) * scale))
    meta = {"name": "npc", "frames": labels, "cell": list(cell), "pivot": list(pivot), "scale": round(scale, 4),
            "height_px": height_px, "playback_fps": 8, "face_bands": bands,
            "default_height_px": meta_d["height_px"],
            "sources": ["winter base: " + (args.sheet or "sheet_winter.png") + " + default face",
                        "default face frames (npc_prod stills) blended with the face weight",
                        "patch:" + gesture_src.name], "reports": report}
    frames.export_cells(cells, out / "npc_set", "npc", meta, labels, npc_prod.GIF_SEQUENCE, names=labels)
    idle = np.asarray(cells[0], dtype=np.int16)
    for label, cell_img in zip(labels[1:4], cells[1:4]):
        delta = np.abs(np.asarray(cell_img, dtype=np.int16) - idle).max(axis=2) > 2
        rows = np.flatnonzero(delta.any(axis=1))
        print(f"{label}: changed rows {(int(rows.min()), int(rows.max())) if len(rows) else None} of {cell[1]}")
    # the video canvas (NINA: blue, see PIPELINE.md section 12)
    canvas_colour = (0, 0, 255) if brief.get("video_canvas") == "blue" else colour
    keyed = frames.crop_to_figure(base)
    frames.figure_on_canvas(keyed, (1080, 1080), 0.80, 0.90, canvas_colour).save(out / "video_in_3q.png")
    print(json.dumps(report, indent=1))


def winter_npc_prod() -> None:
    """Point npc_prod.py's folder helper at the winter folder (its idle / calm stages then run unchanged)."""
    npc_prod.char_dir = lambda char_id: wdir(char_id)


def cmd_idle(args: argparse.Namespace) -> None:
    winter_npc_prod()
    ns = argparse.Namespace(char=args.id, video=args.video or "video_idle_winter.mp4", work=None, first=0, last=None)
    npc_prod.cmd_idle(ns)


def cmd_calm(args: argparse.Namespace) -> None:
    winter_npc_prod()
    ns = argparse.Namespace(char=args.id, work=None, threshold=args.threshold, step=args.step, fps=None)
    npc_prod.cmd_calm(ns)


def cmd_export(args: argparse.Namespace) -> None:
    char_id = args.id
    d = wdir(char_id)
    dst = GAME_ACTORS / char_id
    actor_path = dst / "actor.json"
    actor = json.loads(actor_path.read_text(encoding="utf-8"))
    sources = npc_prod.sheet_sources(d)
    keys = {}
    for key, png in sources.items():
        name = f"{key}_winter"
        actor["sheets"][name] = npc_prod.write_sheet(png, name, dst)
        keys[key] = name
    idle_meta = json.loads(sources["idle"].with_suffix(".json").read_text(encoding="utf-8")) if "idle" in sources \
        else None
    actor.setdefault("variants", {})["winter"] = {
        "animations": npc_prod.anims(keys["npc"], keys.get("idle"), keys.get("idle_fidget"), idle_meta),
        "note": "Jasna 2035 is winter (6 February 2035, owner 2026-10-06): the same set re-dressed for snow and "
                "frost (art/tools/npc_winter.py; default face pixels, so the default blink and mouth frames apply); "
                "selected in the natural blocking (npcs.<id>.variant = \"winter\")."}
    actor_path.write_text(json.dumps(actor, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    for key, name in keys.items():
        entry = actor["sheets"][name]
        assert max(entry["size"]) <= 4096, (name, entry["size"])
        print(name, entry["size"], f"{entry['frames']} cells, {entry['columns']} columns, cell {entry['cell']}")


def cmd_review(args: argparse.Namespace) -> None:
    char_id = args.id
    rows = []
    for folder in (CHAR_ROOT / char_id, wdir(char_id)):
        meta = json.loads((folder / "npc_set" / "npc_sheet.json").read_text(encoding="utf-8"))
        cells = npc_prod.strip_cells(folder / "npc_set" / "npc_sheet.png", meta)
        rows.append((cells, meta))
    width = sum(c.width + 4 for c in rows[0][0] + rows[1][0]) + 40
    zooms = []
    for cells, meta in rows:
        px, py = meta["pivot"]
        hgt = meta.get("default_height_px", meta["height_px"])
        top = int(py - hgt) - 30
        box = (int(px - 0.20 * hgt), max(0, top), int(px + 0.22 * hgt), int(top + 0.28 * hgt))
        zooms.append([c.crop(box).resize(((box[2] - box[0]) * 2, (box[3] - box[1]) * 2), Image.Resampling.LANCZOS)
                      for c in cells[:4]])
    zw, zh = zooms[0][0].size
    height = max(c.height for c in rows[0][0] + rows[1][0]) + 30 + 2 * (zh + 6)
    bg = frames.background_crop((max(width, 4 * (zw + 6) + 20), height)).convert("RGBA")
    x = 10
    for cells, _meta in rows:
        for c in cells:
            bg.alpha_composite(c, (x, 10))
            x += c.width + 4
        x += 20
    zy = max(c.height for c in rows[0][0] + rows[1][0]) + 30
    for r, zrow in enumerate(zooms):
        for i, z in enumerate(zrow):
            bg.alpha_composite(z, (10 + i * (zw + 6), zy + r * (zh + 6)))
    out = wdir(char_id) / "review.jpg"
    bg.convert("RGB").save(out, quality=90)
    print(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--budget", type=float, default=0.0, help="USD cap of the task (paid commands)")
    parser.add_argument("--seed", type=int, default=2035)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("redress")
    p.add_argument("ids", nargs="*")
    p.add_argument("--tag", help="suffix of the output name (retakes)")
    p.set_defaults(func=cmd_redress)
    p = sub.add_parser("gesture")
    p.add_argument("ids", nargs="*")
    p.add_argument("--tag")
    p.add_argument("--extra", help="extra sentence (retakes)")
    p.set_defaults(func=cmd_gesture)
    p = sub.add_parser("video")
    p.add_argument("ids", nargs="*")
    p.add_argument("--tag")
    p.add_argument("--extra", help="sentence put before the brief's idle motion (retakes)")
    p.set_defaults(func=cmd_video)
    p = sub.add_parser("build")
    p.add_argument("id")
    p.add_argument("--sheet")
    p.add_argument("--gesture")
    p.set_defaults(func=cmd_build)
    p = sub.add_parser("idle")
    p.add_argument("id")
    p.add_argument("--video")
    p.set_defaults(func=cmd_idle)
    p = sub.add_parser("calm")
    p.add_argument("id")
    p.add_argument("--threshold", type=float, default=4.0)
    p.add_argument("--step", type=int, default=3)
    p.set_defaults(func=cmd_calm)
    p = sub.add_parser("export")
    p.add_argument("id")
    p.set_defaults(func=cmd_export)
    p = sub.add_parser("review")
    p.add_argument("id")
    p.set_defaults(func=cmd_review)
    args = parser.parse_args()
    if args.cmd in ("redress", "gesture", "video") and args.budget <= 0:
        sys.exit("paid command: pass --budget")
    args.func(args)


if __name__ == "__main__":
    main()
