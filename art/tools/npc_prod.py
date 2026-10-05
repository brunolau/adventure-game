"""Production NPC sprite sets (first used for the 2035 batch): paid edits, local build and game export.

Built on npcs.py (prompts, budget guard), frames.py (keying, patches, previews), export_actors.py (WebP encoding,
sheet JSON) and regrid_sheets.py (grids of at most 4096 px for mobile GPUs). Briefs: art/characters/characters.json.

Paid (fal.ai, logged to art/spend-log.csv; refused once the task budget would be exceeded):
  sheet  ID                                 Pro 2K 3:4 base sheet, cast anchor = ADAM's keyed 3/4 sprite
                                            (brief 'pronoun': 'it' = a machine: robot prompts, no human rules)
  pose   ID blink|talk|talk_oh|gesture --base RAW
                                            NB2 edits (face frames 1K, gesture 2K)
  video  ID [--engine hailuo_pro|hailuo]    idle loop from video_in_3q.png (start = end frame)
Free (local):
  prep   ID [--canvas-height 0.80]          key the base sheet (keyed/base_3q.png) and write the video canvas
  stills ID                                 npc_set/: idle, blink, talk_a, talk_b, gesture on one pivot; blink and
                                            mouth frames are transplanted in bands found from the edits themselves
                                            (eyes / mouth only, so the body and the other facial features stay
                                            pixel-identical: no flicker); the gesture keeps every unchanged pixel
  idle   ID                                 idle_hailuo/: 36 cells of the whole start=end clip, same scale and
                                            pivot as the stills (cell 0 = the still idle pose)
  calm   ID [--threshold 4 --step 3]        idle_calm/: default idle = ping-pong of the clip's calm frames around
                                            its loop point + one blink cell; the whole clip ships as idle_fidget
  cut    ID --name counter --visible 0.42   bust variants cut at a counter / table top (pivot = centre of the cut)
  export ID                                 WebP grids + JSON + actor.json into src/game/assets/actors/ID
  review ID                                 review images (stills on a background, face zoom, idle strip)

Run from art/tools, e.g.:
  python npc_prod.py --budget 15 --budget-since 2026-10-05T04:30 sheet NINA
  python npc_prod.py prep NINA && python npc_prod.py stills NINA && python npc_prod.py export NINA
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import chars
import export_actors
import fal_api
import frames
import npcs
import regrid_sheets

ART = fal_api.ART
REPO = ART.parent
CHAR_ROOT = ART / "characters"
GAME_ACTORS = REPO / "src" / "game" / "assets" / "actors"
BATCH_2035 = ["NINA", "TAMARA", "BORIS", "SARA", "ROBOT", "VIKTOR", "IVAN", "TURISTA"]
HUMAN_HEIGHT_PX = 512
HUMAN_HEIGHT_CM = 175.0
IDLE_CELLS = 36

# ----------------------------------------------------------------------------- prompts

HUMAN_GUARD = ("Keep {pos} face, hair colour, skin tone and the soft even lighting exactly as in the first image: no "
               "dappled light spots or sun patches on {obj} or {pos} clothes.")

MACHINE_CAST_NOTE = (
    "The FIRST reference image shows an already approved character from our game. Use it only as the reference for "
    "how things are drawn and painted in this game: painting technique, soft outlines, level of detail, lighting and "
    "colour palette. Do not copy the man, his face or anything he wears.")
MACHINE_VIEW = (
    "Paint a single full-body sprite of a small robot character for a point-and-click adventure game: {desc} "
    "Pose: standing still on its two wheels in a three-quarter view turned toward the right, the same viewing angle "
    "as the approved character in the first reference image: its front face with the light eyes is turned about 45 "
    "degrees toward the right edge of the image, the near side of its body faces the viewer, both wheels stand on "
    "the ground. The robot is centred and fills about 75% of the image height, antenna included.")
MACHINE_RULES = (
    "The robot is a game sprite: completely visible from the tip of the antenna pennant to the bottom of the wheels, "
    "with green margin on every side; both wheels stand on the same invisible ground line. Even, soft, warm daylight "
    "from the front-left, no strong cast shadows, so the sprite fits many scenes. Gently curved, slightly exaggerated "
    "cartoon shapes as in classic 1990s adventure games, painted with the same brushwork as the people.")
MACHINE_KEEP = ("Edit the first image: keep everything exactly the same (the same robot, same angle, same position "
                "and size in the frame, same colours, same flat green background)")
MACHINE_FACE = {
    "blink": MACHINE_KEEP + " and change ONLY its two round light eyes: they dim and squeeze into two short, soft, "
                            "horizontal glowing lines, like closed eyes in a blink. Do not move or redraw anything "
                            "else.",
    "talk": MACHINE_KEEP + " and change ONLY the small curved row of light dots below its eyes: it glows a little "
                           "brighter and opens into a wider, rounder curve, like a smiling mouth in mid-speech. The "
                           "eyes stay exactly the same. Do not move or redraw anything else.",
    "talk_oh": MACHINE_KEEP + " and change ONLY the small row of light dots below its eyes: the dots form a small "
                              "round ring, like a mouth saying 'oh'. The eyes stay exactly the same. Do not move or "
                              "redraw anything else.",
}
MACHINE_GESTURE = (
    "Edit the first image: the same robot, same colours, same scale, same flat green background, the same "
    "three-quarter view facing right, standing on the same spot with both wheels in exactly the same place. Change "
    "only this: {gesture} Keep the body shell, the wheels and the antenna unchanged, and keep the whole robot inside "
    "the frame.")
MACHINE_IDLE_SUFFIX = (
    " The robot keeps the same position, facing and scale. Seamless loop. The camera is completely static. The "
    "background stays a perfectly flat uniform green, nothing else appears. Same hand-painted style throughout.")

VIDEO_ENGINES = {
    "hailuo_pro": ("fal-ai/minimax/hailuo-02/pro/image-to-video", "1080P"),
    "hailuo": ("fal-ai/minimax/hailuo-02/standard/image-to-video", "768P"),
}


# ----------------------------------------------------------------------------- helpers

def is_machine(brief: dict) -> bool:
    return brief.get("pronoun") == "it"


def char_dir(char_id: str) -> Path:
    return CHAR_ROOT / char_id


def key_colour(brief: dict) -> tuple[int, int, int]:
    return frames.KEY_COLOURS[npcs.key_of(brief)]


def target_height(brief: dict) -> int:
    """Sprite height at scale 1: adults 512 px; machines by real size (brief real_height_cm), see stills --height."""
    if brief.get("sprite_height_px"):
        return int(brief["sprite_height_px"])
    return HUMAN_HEIGHT_PX


def load_rgb_like(path: Path, like: np.ndarray) -> np.ndarray:
    rgb = frames.load_rgb(path)
    if rgb.shape != like.shape:
        rgb = np.asarray(Image.fromarray(rgb).resize(like.shape[1::-1], Image.Resampling.LANCZOS))
    return rgb


def aligned_diff(base_rgb: np.ndarray, edit_rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    base_key = frames.chroma_key(base_rgb)
    edit_key = frames.chroma_key(edit_rgb)
    dy, dx = frames.phase_shift(base_key[..., 3].astype(np.float32), edit_key[..., 3].astype(np.float32))
    edit_rgb = np.roll(edit_rgb, (dy, dx), axis=(0, 1))
    edit_key = np.roll(edit_key, (dy, dx), axis=(0, 1))
    diff = np.abs(base_rgb.astype(np.float32) - edit_rgb.astype(np.float32)).mean(axis=2)
    figure = (base_key[..., 3] > 128) & (edit_key[..., 3] > 128)
    return diff * figure, base_key, (int(dy), int(dx))


def changed_rows_peak(diff: np.ndarray, y0: int, y1: int, smooth: int, threshold: float = 22.0) -> float | None:
    """Row with the most changed pixels inside [y0, y1) (profile smoothed over `smooth` rows)."""
    rows = (diff[y0:y1] > threshold).sum(axis=1).astype(np.float64)
    if rows.sum() < 30:
        return None
    kernel = np.ones(max(1, smooth)) / max(1, smooth)
    return float(y0 + int(np.argmax(np.convolve(rows, kernel, mode="same"))))


def face_bands(base_rgb: np.ndarray, blink_rgb: np.ndarray, talk_rgb: np.ndarray) -> dict:
    """Eye and mouth rows from what the blink and talk edits changed; bands as fractions of the figure height.

    Eyes: the peak of the blink edit's changes 3-14 % below the top of the figure; mouth: the peak of the talk
    edit's changes 3-10 % of the height below the eyes (NB2 also re-renders collars and hair, which a plain
    centroid would pick up)."""
    diff_b, base_key, shift_b = aligned_diff(base_rgb, blink_rgb)
    diff_t, _, shift_t = aligned_diff(base_rgb, talk_rgb)
    x0, y0, x1, y1 = frames.alpha_bbox(base_key)
    height = y1 - y0
    smooth = max(3, int(0.01 * height))
    eye_y = changed_rows_peak(diff_b, y0 + int(0.03 * height), y0 + int(0.14 * height), smooth)
    if eye_y is None:
        raise SystemExit("blink edit changed nothing in the eye zone")
    mouth_y = changed_rows_peak(diff_t, int(eye_y + 0.03 * height), int(eye_y + 0.10 * height), smooth)
    if mouth_y is None:
        raise SystemExit("talk edit changed nothing below the eyes")
    d = mouth_y - eye_y
    blink = ((eye_y - 0.55 * d - y0) / height, (eye_y + 0.40 * d - y0) / height)
    talk = ((mouth_y - 0.50 * d - y0) / height, (mouth_y + 0.80 * d - y0) / height)
    return {"eye_y_frac": round((eye_y - y0) / height, 4), "mouth_y_frac": round((mouth_y - y0) / height, 4),
            "blink_band": [round(v, 4) for v in blink], "talk_band": [round(v, 4) for v in talk],
            "shift_blink": shift_b, "shift_talk": shift_t}


def panel_patch(base_rgb: np.ndarray, edit_rgb: np.ndarray, part: str, feather: int = 4) -> tuple[np.ndarray, dict]:
    """Machines: transplant only the inside of the dark face panel (light eyes / light-dot mouth) of an edit.

    NB2 re-renders the whole shell of a machine (diff > 40 on most rows), so a row band would carry that over. The
    panel = the largest dark region of the figure (luminance < 80), holes filled, eroded a little so the panel's
    rim stays the base's. part: 'eyes' = panel rows above the midpoint between the eye and mouth lights,
    'mouth' = below it, 'all' = the whole panel."""
    from PIL import ImageFilter
    base_key = frames.chroma_key(base_rgb)
    edit_key = frames.chroma_key(edit_rgb)
    dy, dx = frames.phase_shift(base_key[..., 3].astype(np.float32), edit_key[..., 3].astype(np.float32))
    edit_key = np.roll(edit_key, (dy, dx), axis=(0, 1))
    lum = base_rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    dark = (lum < 80) & (base_key[..., 3] > 200)
    labels, sizes = frames.label_components(dark)
    panel = labels == (int(np.argmax(sizes)) + 1)
    # fill the light eyes and dots: the panel is a convex rounded rectangle, so take its convex hull
    ys0, xs0 = np.nonzero(panel)
    pts = sorted(set(zip(xs0[::7].tolist(), ys0[::7].tolist())))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    img = Image.new("L", panel.shape[::-1], 0)
    ImageDraw.Draw(img).polygon(hull, fill=255)
    img = img.filter(ImageFilter.MinFilter(2 * 8 + 1))                               # keep the rim
    mask = np.asarray(img, dtype=np.float32) / 255
    ys = np.flatnonzero(mask.max(axis=1) > 0.5)
    glow = (base_rgb[..., 2] > 200) & (lum > 170) & (mask > 0.5)
    split = None
    glow_labels, glow_sizes = frames.label_components(glow)
    if len(glow_sizes) >= 3:
        # the two largest glowing blobs are the eyes; the light dots of the mouth sit below them
        eyes = np.argsort(glow_sizes)[-2:] + 1
        eye_rows = np.flatnonzero(np.isin(glow_labels, eyes).any(axis=1))
        eye_bottom = int(eye_rows.max())
        below = glow & ~np.isin(glow_labels, eyes)
        below[:eye_bottom + 1] = False
        mouth_rows = np.flatnonzero(below.any(axis=1))
        if len(mouth_rows):
            split = (eye_bottom + int(mouth_rows.min())) // 2
    if part != "all" and split is not None:
        rows = np.arange(mask.shape[0])[:, None]
        mask = mask * ((rows < split) if part == "eyes" else (rows >= split))
    mask = np.asarray(Image.fromarray((mask * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(feather)),
                      dtype=np.float32)[..., None] / 255
    ab = base_key[..., 3:4].astype(np.float32) / 255
    ae = edit_key[..., 3:4].astype(np.float32) / 255
    alpha = ab * (1 - mask) + ae * mask
    premul = base_key[..., :3] * ab * (1 - mask) + edit_key[..., :3] * ae * mask
    with np.errstate(divide="ignore", invalid="ignore"):
        rgb = np.where(alpha > 1e-3, premul / np.maximum(alpha, 1e-3), 0)
    report = {"shift_dy_dx": [int(dy), int(dx)], "panel_rows": [int(ys.min()), int(ys.max())] if len(ys) else None,
              "eye_mouth_split_row": split, "part": part}
    return np.dstack([rgb, alpha * 255]).clip(0, 255).astype(np.uint8), report


def leg_iou(a: np.ndarray, b: np.ndarray, frac: float = 0.30) -> float:
    """IoU of the bottom `frac` of two keyed figures on the same canvas (are the feet/legs where they were?)."""
    x0, y0, x1, y1 = frames.alpha_bbox(a)
    top = y1 - int(frac * (y1 - y0))
    ma, mb = a[top:y1, :, 3] > 128, b[top:y1, :, 3] > 128
    return float((ma & mb).sum() / max(1, (ma | mb).sum()))


def place_cells(layers: list[np.ndarray], pivot_x: float, feet_y: float, scale: float,
                pad: int = 4) -> tuple[list[Image.Image], tuple[int, int], tuple[int, int]]:
    """Scale full-canvas keyed layers and place them on cells that share one pivot (feet centre)."""
    boxes = [frames.alpha_bbox(layer) for layer in layers]
    half = max(max(pivot_x - b[0] for b in boxes), max(b[2] - pivot_x for b in boxes))
    top = max(feet_y - b[1] for b in boxes)
    below = max(0.0, max(b[3] - feet_y for b in boxes))
    cell_w = 2 * int(math.ceil(half * scale)) + 2 * pad
    below_px = int(math.ceil(below * scale))
    cell_h = int(math.ceil(top * scale)) + 2 * pad + below_px
    pivot = (cell_w // 2, cell_h - pad - below_px)
    cells = []
    for layer in layers:
        img = Image.fromarray(layer, "RGBA")
        img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))),
                         Image.Resampling.LANCZOS)
        cell = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
        cell.paste(img, (round(pivot[0] - pivot_x * scale), round(pivot[1] - feet_y * scale)), img)
        cells.append(cell)
    return cells, (cell_w, cell_h), pivot


def strip_cells(sheet: Path, meta: dict) -> list[Image.Image]:
    img = Image.open(sheet).convert("RGBA")
    cw, ch = meta["cell"]
    count = len(meta["frames"]) if isinstance(meta["frames"], list) else int(meta["frames"])
    cols = max(1, img.width // cw)
    return [img.crop(((i % cols) * cw, (i // cols) * ch, (i % cols + 1) * cw, (i // cols + 1) * ch))
            for i in range(count)]


# ----------------------------------------------------------------------------- paid commands

def budget_args(args: argparse.Namespace) -> argparse.Namespace:
    if not args.budget_scope:
        args.budget_scope = ",".join(f"characters/{c}/" for c in BATCH_2035)
    return args


def cmd_sheet(args: argparse.Namespace) -> None:
    budget_args(args)
    brief = npcs.load_brief(args.char)
    key = npcs.key_of(brief)
    cast = chars.cast_reference(npcs.CAST_ANCHOR, key, char_dir(args.char))
    if is_machine(brief):
        parts = [MACHINE_CAST_NOTE, MACHINE_VIEW.format(desc=brief["description"]), MACHINE_RULES]
    else:
        parts = [chars.CAST_REF_NOTE, npcs.VIEW_NPC_3Q.format(desc=brief["description"]), chars.SPRITE_RULES]
    prompt = " ".join(parts + [chars.key_background(key), chars.STYLE_FOR_CHARACTER + chars.STYLE_A])
    prompt = chars.recolour_key_words(prompt, key).replace("with green margin", f"with {key} margin")
    name = args.out or "sheet_npc_3q"
    paths = npcs.edit(args, "pro", prompt, [cast], "3:4", "2K", f"characters/{args.char}/{name}",
                      char_dir(args.char) / name)
    print("\n".join(str(p) for p in paths))


def cmd_pose(args: argparse.Namespace) -> None:
    budget_args(args)
    brief = npcs.load_brief(args.char)
    key = npcs.key_of(brief)
    if is_machine(brief):
        if args.pose == "gesture":
            template, res = MACHINE_GESTURE.format(gesture=brief["gesture"]), args.res or "2K"
        else:
            template, res = MACHINE_FACE[args.pose], args.res or "1K"
        prompt = template
    else:
        words = npcs.words_of(brief)
        if args.pose == "gesture":
            template, res = npcs.GESTURE_PROMPT, args.res or "2K"
        else:
            template, res = npcs.FACE_PROMPTS[args.pose], args.res or "1K"
        prompt = template.format(**words) + " " + HUMAN_GUARD.format(**words)
        if args.extra:
            prompt += " " + args.extra
    prompt = prompt + " " + chars.key_background(key) + " " + chars.STYLE_FOR_CHARACTER + chars.STYLE_A
    prompt = chars.recolour_key_words(prompt, key)
    out = args.out or f"pose_{args.pose}_nb2"
    paths = npcs.edit(args, "nb2", prompt, [Path(args.base).resolve()], "3:4", res,
                      f"characters/{args.char}/{out}", char_dir(args.char) / out)
    print("\n".join(str(p) for p in paths))


def cmd_video(args: argparse.Namespace) -> None:
    budget_args(args)
    brief = npcs.load_brief(args.char)
    key = npcs.key_of(brief)
    endpoint, resolution = VIDEO_ENGINES[args.engine]
    suffix = MACHINE_IDLE_SUFFIX if is_machine(brief) else npcs.IDLE_SUFFIX
    prompt = chars.recolour_key_words(brief["idle_motion"] + suffix, args.bg or key)
    if args.bg:  # e.g. a blue canvas for a magenta-keyed character (magenta idles spun round, PIPELINE.md)
        prompt = prompt.replace(f"uniform {key}", f"uniform {args.bg}")
    image = Path(args.image) if args.image else char_dir(args.char) / "video_in_3q.png"
    uri = fal_api.image_data_uri(image, fmt="PNG")
    arguments = {"prompt": prompt, "image_url": uri, "end_image_url": uri, "prompt_optimizer": False}
    if args.engine == "hailuo":
        arguments.update(duration="6", resolution=resolution)
    price = fal_api.video_price(endpoint, 6.0, resolution)
    name = args.out or f"video_idle_{args.engine}_loop"
    asset = f"characters/{args.char}/{name}"
    npcs.guard(args, asset, price)
    result = fal_api.run(endpoint, arguments, asset, price, budget=None, timeout_s=1800, poll_s=8)
    meta = {"model": endpoint, "usd": round(price, 4), "prompt": prompt, "input": image.name, "tail_image": True,
            "seconds": 6.0, "resolution": resolution,
            "arguments": {k: v for k, v in arguments.items() if not str(v).startswith("data:")}}
    paths = chars.save_outputs(result, char_dir(args.char) / name, meta)
    print("\n".join(str(p) for p in paths))


# ----------------------------------------------------------------------------- local commands

def cmd_prep(args: argparse.Namespace) -> None:
    brief = npcs.load_brief(args.char)
    d = char_dir(args.char)
    raw = d / (args.sheet or "sheet_npc_3q.png")
    rgba = frames.chroma_key(frames.load_rgb(raw))
    keyed = frames.crop_to_figure(rgba)
    frames.save_rgba(keyed, d / "keyed" / "base_3q.png")
    print("keyed", keyed.shape[1::-1], frames.key_quality(keyed))
    canvas = frames.figure_on_canvas(keyed, (1080, 1080), args.canvas_height, 0.90, key_colour(brief))
    canvas.save(d / "video_in_3q.png")
    print("canvas", d / "video_in_3q.png")


GIF_SEQUENCE = [(0, 1400), (1, 110), (0, 700), (2, 125), (3, 125), (2, 125), (0, 125), (3, 125), (2, 125), (0, 500),
                (4, 1200), (0, 600)]


def cmd_stills(args: argparse.Namespace) -> None:
    brief = npcs.load_brief(args.char)
    d = char_dir(args.char)
    base_path = d / "sheet_npc_3q.png"
    base_rgb = frames.load_rgb(base_path)
    srcs = {k: d / getattr(args, k) for k in ("blink", "talk", "talk_oh", "gesture")}
    edits = {k: load_rgb_like(p, base_rgb) for k, p in srcs.items()}
    base_key = frames.chroma_key(base_rgb)
    layers = [base_key]
    reports = {}
    if is_machine(brief):
        bands = {"mode": "face panel (machine)"}
        for label, src, part in (("blink", "blink", "eyes"), ("talk_a", "talk", "mouth"),
                                 ("talk_b", "talk_oh", "mouth")):
            rgba, report = panel_patch(base_rgb, edits[src], part)
            layers.append(rgba)
            reports[label] = report
    else:
        bands = face_bands(base_rgb, edits["blink"], edits["talk"])
        if args.blink_band:
            bands["blink_band"] = [float(v) for v in args.blink_band.split(",")]
        if args.talk_band:
            bands["talk_band"] = [float(v) for v in args.talk_band.split(",")]
        for label, src, band in (("blink", "blink", bands["blink_band"]), ("talk_a", "talk", bands["talk_band"]),
                                 ("talk_b", "talk_oh", bands["talk_band"])):
            rgba, report = frames.patch_pose(base_rgb, edits[src], tuple(band), feather=args.feather)
            layers.append(rgba)
            reports[label] = report
    if args.gesture_mode == "patch":
        gesture, report = frames.patch_pose(base_rgb, edits["gesture"], (0.0, 1.0), feather=6, threshold=20.0)
    else:
        gesture = frames.chroma_key(edits["gesture"])
        dy, dx = frames.phase_shift(base_key[..., 3].astype(np.float32), gesture[..., 3].astype(np.float32))
        gesture = np.roll(gesture, (dy, dx), axis=(0, 1))
        report = {"shift_dy_dx": [int(dy), int(dx)]}
    report["leg_iou"] = round(leg_iou(base_key, frames.chroma_key(np.roll(
        edits["gesture"], tuple(report["shift_dy_dx"]), axis=(0, 1)))), 4)
    reports["gesture"] = report
    layers.append(gesture)
    _x0, by0, _x1, by1 = frames.alpha_bbox(base_key)
    height_px = args.height or target_height(brief)
    scale = height_px / (by1 - by0)
    pivot_x = frames.torso_center_x(base_key) if not is_machine(brief) else (_x0 + _x1) / 2
    cells, cell, pivot = place_cells(layers, pivot_x, by1, scale)
    labels = ["idle", "blink", "talk_a", "talk_b", "gesture"]
    meta = {"name": "npc", "frames": labels, "cell": list(cell), "pivot": list(pivot), "scale": round(scale, 4),
            "height_px": height_px, "playback_fps": 8, "face_bands": bands,
            "sources": ["key:sheet_npc_3q.png", f"patch:{srcs['blink'].name}", f"patch:{srcs['talk'].name}",
                        f"patch:{srcs['talk_oh'].name}", f"{args.gesture_mode}:{srcs['gesture'].name}"],
            "reports": reports}
    out = d / "npc_set"
    frames.export_cells(cells, out, "npc", meta, labels, GIF_SEQUENCE, names=labels)
    # pixel-identity check: outside the transplanted bands the face frames must equal the idle cell
    idle = np.asarray(cells[0], dtype=np.int16)
    for label, cell_img in zip(labels[1:4], cells[1:4]):
        delta = np.abs(np.asarray(cell_img, dtype=np.int16) - idle).max(axis=2) > 2
        rows = np.flatnonzero(delta.any(axis=1))
        span = (int(rows.min()), int(rows.max())) if len(rows) else None
        print(f"{label}: changed rows {span} of {cell[1]} (pivot {pivot[1]})")
    print(json.dumps({k: v for k, v in meta.items() if k not in ('sources',)}, indent=1))


def cmd_idle(args: argparse.Namespace) -> None:
    brief = npcs.load_brief(args.char)
    d = char_dir(args.char)
    video = d / (args.video or "video_idle_hailuo_pro_loop.mp4")
    work = Path(args.work) / args.char if args.work else d / "_frames"
    paths = frames.extract_frames(video, work)
    fps = frames.video_info(video).get("fps", 24.0)
    n = len(paths)
    last = args.last if args.last is not None else n - 1
    first = args.first
    period = last - first
    picks = [first + round(i * period / IDLE_CELLS) for i in range(IDLE_CELLS)]
    keyed = {i: frames.chroma_key(frames.load_rgb(paths[i]), choke=1) for i in sorted(set(picks + [first, last]))}
    k0 = keyed[first]
    x0, y0, x1, y1 = frames.alpha_bbox(k0)
    still_meta = json.loads((d / "npc_set" / "npc_sheet.json").read_text(encoding="utf-8"))
    height_px = still_meta["height_px"]
    scale = height_px / (y1 - y0)
    pivot_x = frames.torso_center_x(k0) if not is_machine(brief) else (x0 + x1) / 2
    layers = [keyed[i] for i in picks]
    cells, cell, pivot = place_cells(layers, pivot_x, y1, scale)
    # numbers for review: loop closure, how much the feet/legs move, drift of the figure box
    def band_diff(a: np.ndarray, b: np.ndarray, top: float, bottom: float) -> float:
        ya, yb = y0 + int(top * (y1 - y0)), y0 + int(bottom * (y1 - y0))
        return float(np.abs(a[ya:yb].astype(np.float32) - b[ya:yb].astype(np.float32)).mean())
    legs = [round(band_diff(k0, layer, 0.75, 1.0), 2) for layer in layers]
    heads = [round(band_diff(k0, layer, 0.0, 0.18), 2) for layer in layers]
    boxes = [frames.alpha_bbox(layer) for layer in layers]
    meta = {"name": "idle", "frames": IDLE_CELLS, "cell": list(cell), "pivot": list(pivot), "source_fps": fps,
            "cycle_frames": period, "cycle_seconds": round(period / fps, 3),
            "playback_fps": round(IDLE_CELLS / (period / fps), 2),
            "loop_error": round(float(np.abs(k0.astype(np.float32) - keyed[last].astype(np.float32)).mean()) / 255, 4),
            "scale": round(scale, 4), "recentered": False, "oneshot": False, "height_px_median": height_px,
            "height_px_range": [round(min(b[3] - b[1] for b in boxes) * scale, 1),
                                round(max(b[3] - b[1] for b in boxes) * scale, 1)],
            "baseline_from_feet": True, "stride_px_per_s": None, "source_frames": picks,
            "source_video": video.name}
    out = d / "idle_hailuo"
    frames.export_cells(cells, out, "idle", meta, [f"{i} (src {p})" for i, p in enumerate(picks)])
    print(json.dumps({k: v for k, v in meta.items() if k != "source_frames"}, indent=1))
    print("leg band mean abs diff vs frame 0:", legs)
    print("head band mean abs diff vs frame 0:", heads)
    print("feet bottom (src px):", sorted(set(b[3] for b in boxes)), "box x:", min(b[0] for b in boxes),
          max(b[2] for b in boxes))
    # compare the first idle cell with the still idle cell at the shared pivot
    still = Image.open(d / "npc_set" / "npc_idle.png").convert("RGBA")
    a = np.asarray(still)[..., 3].astype(np.float32)
    b_img = Image.new("RGBA", still.size, (0, 0, 0, 0))
    b_img.paste(cells[0], (still_meta["pivot"][0] - pivot[0], still_meta["pivot"][1] - pivot[1]))
    b = np.asarray(b_img)[..., 3].astype(np.float32)
    print("still idle vs video cell 0: alpha shift", frames.phase_shift(a, b),
          "alpha IoU", round(float(((a > 128) & (b > 128)).sum() / max(1, ((a > 128) | (b > 128)).sum())), 4))


def cmd_calm(args: argparse.Namespace) -> None:
    """Default idle from the calm stretch of the start=end clip around its loop point, played as a ping-pong.

    Hailuo idles glance or bow down for 2-3 s of each 6 s clip although the prompt forbids it; looping that every
    6 s looks mechanical. The frames whose head band stays within --threshold (mean abs diff, 0-255) of frame 0
    on both sides of the loop point (the clip ends where it starts) are sampled every --step frames and played
    forward and back, rotated to start at source frame 0, so the full clip can follow as idle_fidget (its cell 0
    is the same frame). One blink cell (the still set's blink transplanted onto the frame-0 cell) is listed in
    blink_frames: the engine shows it in most loops and falls back to the previous cell (frame 0) otherwise.
    """
    brief = npcs.load_brief(args.char)
    d = char_dir(args.char)
    work = Path(args.work) / args.char if args.work else d / "_frames"
    paths = sorted(work.glob("f_*.png"))
    if not paths:
        raise SystemExit(f"no extracted frames in {work} (run idle first)")
    n = len(paths)
    f0 = frames.load_rgb(paths[0])
    k0 = frames.chroma_key(f0, choke=1)
    x0, y0, x1, y1 = frames.alpha_bbox(k0)
    head = (slice(y0, y0 + int(0.20 * (y1 - y0))), slice(x0, x1))
    ref = f0[head].astype(np.float32)
    motion = [float(np.abs(frames.load_rgb(p)[head].astype(np.float32) - ref).mean()) for p in paths]
    period = n - 1                      # frame n-1 equals frame 0 (start = end)
    b = 0
    while b + 1 < period and motion[b + 1] <= args.threshold:
        b += 1
    a = period
    while a - 1 > b and motion[a - 1] <= args.threshold:
        a -= 1
    back = [period - k * args.step for k in range(1, (period - a) // args.step + 1)]
    fwd = list(range(0, b + 1, args.step))
    picks = sorted(back) + fwd           # time order across the loop point; source 0 at index len(back)
    j = len(back)
    still_meta = json.loads((d / "npc_set" / "npc_sheet.json").read_text(encoding="utf-8"))
    height_px = still_meta["height_px"]
    scale = height_px / (y1 - y0)
    pivot_x = frames.torso_center_x(k0) if not is_machine(brief) else (x0 + x1) / 2
    layers = [frames.chroma_key(frames.load_rgb(paths[i % period]), choke=1) for i in picks]
    cells, cell, pivot = place_cells(layers, pivot_x, y1, scale)
    # blink cell: the still blink's changed pixels, aligned onto the frame-0 cell by the head region
    still_idle = np.asarray(Image.open(d / "npc_set" / "npc_idle.png").convert("RGBA"), np.float32)
    still_blink = np.asarray(Image.open(d / "npc_set" / "npc_blink.png").convert("RGBA"), np.float32)
    base = np.asarray(cells[j], np.float32)
    canvas = np.zeros_like(base)
    ox, oy = pivot[0] - still_meta["pivot"][0], pivot[1] - still_meta["pivot"][1]
    sh, sw = still_idle.shape[:2]
    def paste(src: np.ndarray) -> np.ndarray:
        out = np.zeros_like(base)
        ys, xs = max(0, oy), max(0, ox)
        ye, xe = min(base.shape[0], oy + sh), min(base.shape[1], ox + sw)
        out[ys:ye, xs:xe] = src[ys - oy:ye - oy, xs - ox:xe - ox]
        return out
    idle_on, blink_on = paste(still_idle), paste(still_blink)
    rows = slice(0, pivot[1] - int(0.80 * height_px)) if not is_machine(brief) else slice(0, base.shape[0])
    lum = lambda im: (im[..., :3] @ np.array([0.299, 0.587, 0.114], np.float32)) * (im[..., 3] / 255)
    dy, dx = frames.phase_shift(lum(base)[rows], lum(idle_on)[rows])
    idle_on, blink_on = (np.roll(im, (dy, dx), axis=(0, 1)) for im in (idle_on, blink_on))
    changed = np.abs(blink_on - idle_on).max(axis=2) > 12
    from PIL import ImageFilter
    m = Image.fromarray((changed * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(5)) \
        .filter(ImageFilter.GaussianBlur(1.5))
    m = (np.asarray(m, np.float32) / 255)[..., None] * (blink_on[..., 3:4] / 255)
    blink_cell = base * (1 - m) + blink_on * m
    blink_cell[..., 3] = np.maximum(base[..., 3], (blink_on[..., 3] * m[..., 0]))
    names = [f"c{i:02d}" for i in range(len(cells))]
    sheet_cells = cells[:j + 1] + [Image.fromarray(blink_cell.clip(0, 255).astype(np.uint8), "RGBA")] + cells[j + 1:]
    sheet_names = names[:j + 1] + ["blink"] + names[j + 1:]
    order = list(range(len(cells))) + list(range(len(cells) - 2, 0, -1))
    order = order[order.index(j):] + order[:order.index(j)]
    sequence = [names[i] for i in order]
    spots = [k for k, name in enumerate(sequence) if name == names[j]]
    sequence[spots[-1] if len(spots) > 1 else spots[0]] = "blink"
    fps = args.fps or json.loads((d / "idle_hailuo" / "idle_sheet.json").read_text(encoding="utf-8")).get("source_fps", 24.0)
    meta = {"name": "idle", "frames": sheet_names, "cell": list(cell), "pivot": list(pivot),
            "playback_fps": round(fps / args.step, 2), "blink_frames": [j + 1], "sequence": sequence,
            "loop_seconds": round(len(sequence) * args.step / fps, 2), "scale": round(scale, 4),
            "height_px": height_px, "source_frames": [i % period for i in picks],
            "calm_window": {"from": a, "to": b, "of": period, "threshold": args.threshold, "step": args.step,
                            "blink_alignment_dy_dx": [int(dy), int(dx)]},
            "note": "ping-pong of the calm frames around the clip's loop point; play 'sequence' (names)"}
    gif = [(sheet_names.index(name), round(1000 * args.step / fps)) for name in sequence] * 2
    frames.export_cells(sheet_cells, d / "idle_calm", "idle", meta, sheet_names, gif, names=sheet_names)
    print(f"calm window: source {a}..{period} + 0..{b} of {period} ({len(picks)} cells + blink, loop "
          f"{meta['loop_seconds']} s at {meta['playback_fps']} fps); blink alignment {dy},{dx}")
    print("motion around 0:", [round(v, 1) for v in motion[:b + 3]], "...", [round(v, 1) for v in motion[a - 2:]])


def cut_sheet(src_png: Path, src_json: Path, out_png: Path, visible: float, height_px: float) -> dict:
    meta = json.loads(src_json.read_text(encoding="utf-8"))
    cells = strip_cells(src_png, meta)
    cw, ch = meta["cell"]
    px, py = meta["pivot"]
    cut_y = int(round(py - (1.0 - visible) * height_px))
    out_cells = [c.crop((0, 0, cw, cut_y)) for c in cells]
    sheet = Image.new("RGBA", (cw * len(out_cells), cut_y), (0, 0, 0, 0))
    for i, c in enumerate(out_cells):
        sheet.paste(c, (i * cw, 0))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_png, optimize=True)
    out = dict(meta)
    out.update(cell=[cw, cut_y], pivot=[px, cut_y], pivot_is_sill_line=True, visible_fraction=visible,
               cut_from=src_png.name)
    out_png.with_suffix(".json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def cmd_cut(args: argparse.Namespace) -> None:
    d = char_dir(args.char)
    still_meta = json.loads((d / "npc_set" / "npc_sheet.json").read_text(encoding="utf-8"))
    height_px = still_meta["height_px"]
    out_dir = d / args.name
    for key, png in sheet_sources(d).items():
        meta = cut_sheet(png, png.with_suffix(".json"), out_dir / f"{key}_{args.name}_sheet.png", args.visible,
                         height_px)
        print(key, args.name, meta["cell"], meta["pivot"])
    # preview: the bust standing on a painted counter line
    sheet = Image.open(out_dir / f"npc_{args.name}_sheet.png").convert("RGBA")
    meta = json.loads((out_dir / f"npc_{args.name}_sheet.json").read_text(encoding="utf-8"))
    cw, ch = meta["cell"]
    bg = frames.background_crop((cw * 5 + 40, ch + 160)).convert("RGBA")
    draw = ImageDraw.Draw(bg)
    draw.rectangle((0, ch + 20, bg.width, bg.height), fill=(120, 86, 60, 255))
    draw.rectangle((0, ch + 20, bg.width, ch + 30), fill=(160, 120, 84, 255))
    for i in range(5):
        bg.alpha_composite(sheet.crop((i * cw, 0, (i + 1) * cw, ch)), (20 + i * cw, 20))
    bg.convert("RGB").save(out_dir / f"{args.name}_preview.jpg", quality=88)


def sheet_sources(d: Path) -> dict[str, Path]:
    """Master strips per shipped sheet key: 'npc' stills; 'idle' = the calm ping-pong when built (else the whole
    clip); 'idle_fidget' = the whole clip when the calm idle exists."""
    out = {"npc": d / "npc_set" / "npc_sheet.png"}
    calm, full = d / "idle_calm" / "idle_sheet.png", d / "idle_hailuo" / "idle_sheet.png"
    if calm.exists():
        out["idle"] = calm
        if full.exists():
            out["idle_fidget"] = full
    elif full.exists():
        out["idle"] = full
    return out


def anims(still: str, video: str | None, fidget: str | None = None, video_meta: dict | None = None) -> dict:
    idle = {"sheet": still, "frames": ["idle"]}
    if video:
        idle = {"sheet": video, "loop": True}
        if video_meta and video_meta.get("sequence"):
            idle.update(frames=video_meta["sequence"], fps=video_meta["playback_fps"],
                        note="calm ping-pong of the video idle; its blink cell is in the sheet's blink_frames")
    a = {
        "idle": idle,
        "idle_still": {"sheet": still, "frames": ["idle"]},
        "blink": {"sheet": still, "frames": ["blink"], "hold_ms": 110, "every_s": [2.5, 6.0],
                  "note": "only while the still idle is shown (the video idle blinks by itself)"},
        "talk": {"sheet": still, "frames": ["talk_a", "talk_b", "talk_a", "idle", "talk_b", "talk_a", "idle"],
                 "fps": 8, "loop": True},
        "gesture": {"sheet": still, "frames": ["gesture"], "hold_ms": 1200, "oneshot": True,
                    "note": "PlayGesture: hold, then return to idle (no in-betweens)"},
    }
    if fidget:
        a["idle_fidget"] = {"sheet": fidget, "loop": False, "every_s": [10, 20],
                            "note": "the whole 6 s video idle (a glance down and back); starts and ends on the idle "
                                    "loop's first cell"}
    return a


VARIANT_NOTES = {
    "counter": "behind a service counter: bust cut at the counter top (pivot = centre of the cut edge); place the "
               "pivot on the painted counter's top edge (data/ambient/actors.json sill_y)",
    "table": "behind a table: figure cut at the table top (pivot = centre of the cut edge); place the pivot on the "
             "painted table's top edge (data/ambient/actors.json sill_y)",
}


def write_sheet(src_png: Path, key: str, dst_dir: Path) -> dict:
    meta_src = src_png.with_suffix(".json")
    meta = export_actors.sheet_json(meta_src, key, f"{key}_sheet.webp")
    for drop in ("reports", "face_bands", "source_frames"):
        meta.pop(drop, None)
    if key.startswith("idle_fidget"):
        meta["loop"] = False
    img = Image.open(src_png).convert("RGBA")
    cw, ch = meta["cell"]
    count = meta["frames"]
    columns, rows = regrid_sheets.grid_layout(cw, ch, count)
    packed = regrid_sheets.grid_pack(img, cw, ch, count, columns)
    dst_dir.mkdir(parents=True, exist_ok=True)
    tmp = dst_dir / f"_{key}_grid.png"
    packed.save(tmp)
    size = export_actors.to_webp(tmp, dst_dir / f"{key}_sheet.webp")
    tmp.unlink()
    meta["columns"], meta["rows"] = columns, rows
    (dst_dir / f"{key}_sheet.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
                                              encoding="utf-8", newline="\n")
    # lossy RGB, lossless alpha: same geometry and an identical matte
    check = np.asarray(Image.open(dst_dir / f"{key}_sheet.webp").convert("RGBA"), dtype=np.int16)
    ref = np.asarray(packed, dtype=np.int16)
    assert check.shape == ref.shape and np.array_equal(check[..., 3], ref[..., 3]), key
    return {"file": f"{key}_sheet.webp", "json": f"{key}_sheet.json", "size": list(size), "cell": meta["cell"],
            "pivot": meta["pivot"], "frames": count, "columns": columns}


def cmd_export(args: argparse.Namespace) -> None:
    brief = npcs.load_brief(args.char)
    d = char_dir(args.char)
    dst = GAME_ACTORS / args.char
    sources = sheet_sources(d)
    sheets = {key: write_sheet(png, key, dst) for key, png in sources.items()}
    metas = {key: json.loads(png.with_suffix(".json").read_text(encoding="utf-8")) for key, png in sources.items()}
    variants = {}
    for name in VARIANT_NOTES:
        if not (d / name / f"npc_{name}_sheet.png").exists():
            continue
        keys = {}
        for key in sources:
            png = d / name / f"{key}_{name}_sheet.png"
            if png.exists():
                sheets[f"{key}_{name}"] = write_sheet(png, f"{key}_{name}", dst)
                keys[key] = f"{key}_{name}"
        variants[name] = {"animations": anims(keys["npc"], keys.get("idle"), keys.get("idle_fidget"),
                                              metas.get("idle")),
                          "note": VARIANT_NOTES[name]}
    still = metas["npc"]
    manifest = {
        "id": args.char,
        "source": f"art/characters/{args.char}",
        "view": "three-quarter, facing right (mirror for facing left)",
        "height_px": still["height_px"],
        "pivot": ("feet centre, 4 px above the cell bottom (counter/table variants: centre of the cut edge)"
                  if not is_machine(brief) else "centre of the wheels' ground contact, 4 px above the cell bottom"),
        "sheets": sheets,
        "animations": anims("npc", "idle" if "idle" in sheets else None,
                            "idle_fidget" if "idle_fidget" in sheets else None, metas.get("idle")),
        "switching": ("Start talking only at a video idle loop boundary (cell 0 matches the still idle pose) or "
                      "cross-fade ~80 ms; video cells are slightly softer than the edit-based stills."),
        "notes": brief.get("notes", ""),
    }
    if variants:
        manifest["variants"] = variants
        manifest["default_variant"] = None
    (dst / "actor.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
                                    newline="\n")
    for key, entry in sheets.items():
        assert max(entry["size"]) <= 4096, (key, entry["size"])
        print(key, entry["size"], f"{entry['frames']} cells, {entry['columns']} columns, cell {entry['cell']}")


def cmd_review(args: argparse.Namespace) -> None:
    d = char_dir(args.char)
    meta = json.loads((d / "npc_set" / "npc_sheet.json").read_text(encoding="utf-8"))
    cells = strip_cells(d / "npc_set" / "npc_sheet.png", meta)
    # face zoom: head of idle / blink / talk_a / talk_b at 2x
    px, py = meta["pivot"]
    h = meta["height_px"]
    top = int(py - h) - 4
    head = (int(px - 0.20 * h), max(0, top), int(px + 0.22 * h), int(top + 0.24 * h))
    zooms = [c.crop(head).resize(((head[2] - head[0]) * 3, (head[3] - head[1]) * 3), Image.Resampling.LANCZOS)
             for c in cells[:4]]
    frames.contact_sheet(zooms, d / "npc_set" / "face_zoom.jpg", cell_h=zooms[0].height,
                         labels=["idle", "blink", "talk_a", "talk_b"])
    idle_dir = d / "idle_hailuo"
    if (idle_dir / "idle_sheet.json").exists():
        imeta = json.loads((idle_dir / "idle_sheet.json").read_text(encoding="utf-8"))
        icells = strip_cells(idle_dir / "idle_sheet.png", imeta)
        picks = icells[::3]
        frames.contact_sheet(picks, idle_dir / "idle_strip.jpg", cell_h=min(480, imeta["cell"][1]),
                             labels=[str(i) for i in range(0, len(icells), 3)])
        # head zoom over the loop: is the face stable (no drift, no off-model frames)?
        ipx, ipy = imeta["pivot"]
        ihead = (int(ipx - 0.20 * h), max(0, int(ipy - h) - 4), int(ipx + 0.22 * h), int(ipy - h + 0.24 * h))
        izooms = [c.crop(ihead).resize(((ihead[2] - ihead[0]) * 2, (ihead[3] - ihead[1]) * 2),
                                       Image.Resampling.LANCZOS) for c in icells[::4]]
        frames.contact_sheet(izooms, idle_dir / "idle_face_strip.jpg", cell_h=izooms[0].height,
                             labels=[str(i) for i in range(0, len(icells), 4)])
    print(d / "npc_set" / "face_zoom.jpg")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--budget", type=float, default=0.0, help="USD cap of the task (paid commands)")
    parser.add_argument("--budget-scope", default="", help="comma-separated spend-log asset prefixes "
                                                           "(default: characters/<ID>/ of the 2035 batch)")
    parser.add_argument("--budget-since", help="ISO timestamp: only spend logged from then on counts")
    parser.add_argument("--seed", type=int, default=1985)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("sheet")
    p.add_argument("char")
    p.add_argument("--out")
    p.set_defaults(func=cmd_sheet)

    p = sub.add_parser("pose")
    p.add_argument("char")
    p.add_argument("pose", choices=["blink", "talk", "talk_oh", "gesture"])
    p.add_argument("--base", required=True)
    p.add_argument("--res")
    p.add_argument("--out")
    p.add_argument("--extra", help="extra sentence appended to a human pose prompt (retakes)")
    p.set_defaults(func=cmd_pose)

    p = sub.add_parser("video")
    p.add_argument("char")
    p.add_argument("--image")
    p.add_argument("--engine", choices=VIDEO_ENGINES, default="hailuo_pro")
    p.add_argument("--bg", help="background colour word of the canvas if it is not the brief's key (blue)")
    p.add_argument("--out")
    p.set_defaults(func=cmd_video)

    p = sub.add_parser("prep")
    p.add_argument("char")
    p.add_argument("--sheet")
    p.add_argument("--canvas-height", type=float, default=0.80)
    p.set_defaults(func=cmd_prep)

    p = sub.add_parser("stills")
    p.add_argument("char")
    p.add_argument("--blink", default="pose_blink_nb2.png")
    p.add_argument("--talk", default="pose_talk_nb2.png")
    p.add_argument("--talk-oh", dest="talk_oh", default="pose_talk_oh_nb2.png")
    p.add_argument("--gesture", default="pose_gesture_nb2.png")
    p.add_argument("--gesture-mode", choices=["patch", "key"], default="patch")
    p.add_argument("--blink-band", help="override top,bottom (fractions of the figure height)")
    p.add_argument("--talk-band", help="override top,bottom (fractions of the figure height)")
    p.add_argument("--feather", type=int, default=8)
    p.add_argument("--height", type=int, help="sprite height px at scale 1 (default: brief or 512)")
    p.set_defaults(func=cmd_stills)

    p = sub.add_parser("idle")
    p.add_argument("char")
    p.add_argument("--video")
    p.add_argument("--work", help="folder for extracted frames (default: <char>/_frames)")
    p.add_argument("--first", type=int, default=0)
    p.add_argument("--last", type=int)
    p.set_defaults(func=cmd_idle)

    p = sub.add_parser("calm")
    p.add_argument("char")
    p.add_argument("--work", help="folder with the extracted frames (default: <char>/_frames)")
    p.add_argument("--threshold", type=float, default=4.0, help="max head-band mean abs diff vs frame 0")
    p.add_argument("--step", type=int, default=3, help="source frames per cell")
    p.add_argument("--fps", type=float, help="source fps (default: from the video)")
    p.set_defaults(func=cmd_calm)

    p = sub.add_parser("cut")
    p.add_argument("char")
    p.add_argument("--name", choices=list(VARIANT_NOTES), required=True)
    p.add_argument("--visible", type=float, required=True, help="fraction of the figure height above the cut")
    p.set_defaults(func=cmd_cut)

    p = sub.add_parser("export")
    p.add_argument("char")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("review")
    p.add_argument("char")
    p.set_defaults(func=cmd_review)

    args = parser.parse_args()
    if args.cmd in ("sheet", "pose", "video") and args.budget <= 0:
        sys.exit("paid command: pass --budget")
    args.func(args)


if __name__ == "__main__":
    main()
