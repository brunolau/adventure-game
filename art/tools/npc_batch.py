"""Batch production of NPC sprite sets (style A), built on chars.py / npcs.py / frames.py / glass.py.

One run produces, per character id, everything PIPELINE.md asks for an NPC (house view: three-quarter facing
right, ADAM's approved keyed 3/4 sprite as the cast style anchor, briefs in art/characters/characters.json):

  paid (fal.ai, logged to art/spend-log.csv, refused beyond the task budget):
    sheet    Nano Banana Pro 2K 3:4 base sheet
    faces    Nano Banana 2 1K edits: blink, talk_a ('ah'), talk_o ('oh')
    gesture  Nano Banana 2 2K edit (the brief's 'gesture')
    video    Hailuo-02 standard 768p 6 s idle loop (start = end frame) from a 1024 px key canvas
  free (local):
    build    keyed base, still set (idle | blink | talk_a | talk_b | gesture on one pivot; blink = eye band,
             talk = mouth band of the edits composited on the base body, so nothing else flickers), the idle
             loop from the video, bust variants (window / window_glass / counter) and review sheets
    export   WebP sheets + JSON (+ actor.json) into src/game/assets/actors/<ID>/; sheets wider than 4096 px
             are packed as row-major grids ('columns' / 'rows' in the JSON) for mobile GPUs

Paid calls run in a small thread pool; spend logging is serialised (thread lock + lock file), and the budget is
reserved before each submit, so parallel calls cannot overshoot it.

Brief keys used beyond npcs.py: key (green|magenta), height_px (children: e.g. 420), child (bool),
wears_glasses (bool), variants (list of 'window', 'window_glass', 'counter'), bust_visible, counter_visible.

Run from art/tools, for example:
  python npc_batch.py --budget 20 --since 2026-10-05T04:29:00 sheet LEA95 SONA
  python npc_batch.py --budget 20 --since 2026-10-05T04:29:00 faces LEA95
  python npc_batch.py build LEA95
  python npc_batch.py export LEA95
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import chars
import fal_api
import frames as fr
import glass

ART = fal_api.ART
REPO = ART.parent
CHAR_ROOT = ART / "characters"
GAME_ACTORS = REPO / "src" / "game" / "assets" / "actors"
CAST_ANCHOR = CHAR_ROOT / "ADAM" / "keyed" / "side_right_3q.png"
MAX_TEX = 4096

PRONOUNS = {"he": {"subj": "he", "pos": "his", "obj": "him"}, "she": {"subj": "she", "pos": "her", "obj": "her"}}

VIEW_NPC_3Q = (
    "Paint a single full-body character for a point-and-click adventure game: {desc} "
    "Pose: standing relaxed in a three-quarter view turned toward the right, exactly like the approved character in "
    "the first reference image: body and face turned about 45 degrees toward the right edge of the image, both eyes "
    "visible, the near side of the body toward the viewer, both feet flat on the ground, weight evenly balanced, "
    "calm neutral expression with the mouth closed, eyes open. Hands and props exactly as described in the brief. "
    "Clothing, hair and shoes are period-correct for Bratislava in the mid-1990s, with no brand names, no logos and "
    "no readable text anywhere. Same framing and scale as the first reference image: the figure is centred and fills "
    "about 80% of the image height."
)

CHILD_RULES = chars.SPRITE_RULES.replace(
    "(head a little large, about 1/6.5 of the height), but still a believable adult.",
    "(head a little large), but clearly a believable 11-year-old child with a child's body proportions: the head "
    "is about 1/5.5 of her height, short legs and narrow shoulders, a soft round child's face.")

KEEP = ("Edit the first image: keep everything exactly the same (same character, same pose, same position and size "
        "in the frame, same clothes, same colours, same flat green background)")

FACE_PROMPTS = {
    "blink": KEEP + " and change ONLY {pos} eyes: they are closed in a natural blink{glasses}, the eyelids relaxed. "
                    "{Pos} eyebrows, mouth, nose, hair and head position stay exactly as they are. Do not move or "
                    "redraw anything else.",
    "talk_a": KEEP + " and change ONLY {pos} mouth and jaw: {subj} is in the middle of speaking, mouth open as if "
                     "saying 'ah', the jaw lowered a little. {Pos} eyes, eyebrows, nose, hair and head position stay "
                     "exactly as they are. Do not move or redraw anything else.",
    "talk_o": KEEP + " and change ONLY {pos} mouth: the lips form a small rounded 'oh' shape, as in mid-speech. {Pos} "
                     "eyes, eyebrows, nose, hair and head position stay exactly as they are. Do not move or redraw "
                     "anything else.",
}

GESTURE_PROMPT = (
    "Edit the first image: the same character, same face, same clothes, same colours, same scale, same flat green "
    "background, the same three-quarter view facing right, standing on the same spot with the feet in exactly the "
    "same place. Change only the pose of the arms and hands: {gesture} Keep the head, the face, the hair, the body, "
    "the legs and the feet unchanged, and keep the whole figure inside the frame. Keep the face, hair colour, skin "
    "tone and the soft even lighting exactly as in the first image: no dappled light spots or sun patches on the "
    "character or the clothes."
)

IDLE_SUFFIX = (
    " The character keeps the same position, facing and scale. Seamless loop. The camera is completely static. The "
    "background stays a perfectly flat uniform green, nothing else appears. Same hand-painted style throughout."
)

HAILUO = "fal-ai/minimax/hailuo-02/standard/image-to-video"
NB2 = "fal-ai/nano-banana-2/edit"
PRO = "fal-ai/nano-banana-pro/edit"
VIDEO_CANVAS = (1024, 1024)
VIDEO_FIG, VIDEO_FEET = 0.80, 0.90
IDLE_FRAMES = 36

# ----------------------------------------------------------------------------- spend log and budget

_LOG_LOCK = threading.Lock()
_ORIGINAL_LOG = fal_api.log_spend


def _locked_log(model: str, asset: str, usd: float) -> None:
    """Serialise spend-log appends (threads of this process + other processes that use this tool)."""
    lock_path = fal_api.SPEND_LOG.with_suffix(".lock")
    with _LOG_LOCK:
        for _ in range(200):
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError:
                if time.time() - lock_path.stat().st_mtime > 30:  # stale lock
                    lock_path.unlink(missing_ok=True)
                time.sleep(0.05)
        else:
            fd = None
        try:
            _ORIGINAL_LOG(model, asset, usd)
        finally:
            if fd is not None:
                os.close(fd)
                lock_path.unlink(missing_ok=True)


fal_api.log_spend = _locked_log


class Budget:
    """Task budget over the spend log (asset prefixes characters/<ID>/ of the batch, rows since a timestamp)."""

    def __init__(self, cap: float, ids: list[str], since: str | None):
        self.cap, self.since = cap, since
        self.prefixes = tuple(f"characters/{i}/" for i in ids)
        self.reserved = 0.0
        self.lock = threading.Lock()

    def spent(self) -> float:
        if not fal_api.SPEND_LOG.exists():
            return 0.0
        with fal_api.SPEND_LOG.open(encoding="utf-8") as handle:
            return sum(float(r["usd"]) for r in csv.DictReader(handle)
                       if r["asset"].startswith(self.prefixes) and (self.since is None or r["timestamp"] >= self.since))

    def reserve(self, asset: str, usd: float) -> None:
        with self.lock:
            spent = self.spent()
            if spent + self.reserved + usd > self.cap + 1e-9:
                raise fal_api.BudgetExceeded(f"{asset}: {spent:.3f} + {self.reserved:.3f} in flight + {usd:.3f} "
                                             f"would exceed {self.cap:.2f}")
            self.reserved += usd
            print(f"[budget] {spent:.3f} spent, {self.reserved:.3f} in flight, cap {self.cap:.2f}", flush=True)

    def release(self, usd: float) -> None:
        with self.lock:
            self.reserved -= usd


BUDGET: Budget | None = None

# ----------------------------------------------------------------------------- briefs and prompts


def briefs() -> dict:
    return json.loads((CHAR_ROOT / "characters.json").read_text(encoding="utf-8"))


def brief_of(cid: str) -> dict:
    data = briefs()
    if cid not in data:
        sys.exit(f"{cid} has no brief in art/characters/characters.json")
    return data[cid]


def key_of(brief: dict) -> str:
    return brief.get("key", "green")


def words(brief: dict) -> dict:
    p = PRONOUNS[brief.get("pronoun", "he")]
    return dict(p, Pos=p["pos"].capitalize(), Subj=p["subj"].capitalize(),
                glasses=" behind the glasses" if brief.get("wears_glasses") else "",
                gesture=brief.get("gesture", ""))


def finish(prompt: str, key: str) -> str:
    prompt = " ".join([prompt, chars.key_background(key), chars.STYLE_FOR_CHARACTER + chars.STYLE_A])
    return chars.recolour_key_words(prompt, key).replace("with green margin", f"with {key} margin")


def sheet_prompt(brief: dict) -> str:
    rules = CHILD_RULES if brief.get("child") else chars.SPRITE_RULES
    return finish(" ".join([chars.CAST_REF_NOTE, VIEW_NPC_3Q.format(desc=brief["description"]), rules]),
                  key_of(brief))


def cdir(cid: str) -> Path:
    return CHAR_ROOT / cid


# ----------------------------------------------------------------------------- paid calls

def edit_call(cid: str, model: str, prompt: str, refs: list[Path], resolution: str, name: str,
              seed: int | None) -> list[Path]:
    price = fal_api.IMAGE_PRICES[(model, resolution)]
    asset = f"characters/{cid}/{name}"
    BUDGET.reserve(asset, price)
    try:
        arguments = {"prompt": prompt, "image_urls": chars.image_inputs(refs, None), "aspect_ratio": "3:4",
                     "resolution": resolution, "output_format": "png", "num_images": 1}
        if seed is not None:
            arguments["seed"] = seed
        result = fal_api.run(model, arguments, asset, price, budget=None, timeout_s=900)
    finally:
        BUDGET.release(price)
    meta = {"model": model, "usd": price, "prompt": prompt, "aspect_ratio": "3:4", "resolution": resolution,
            "references": [str(r.relative_to(ART)) for r in refs], "style_reference": None, "seed": seed}
    return chars.save_outputs(result, cdir(cid) / name, meta)


def do_sheet(cid: str, name: str, seed: int | None) -> list[Path]:
    brief = brief_of(cid)
    cast = chars.cast_reference(CAST_ANCHOR, key_of(brief), cdir(cid))
    return edit_call(cid, PRO, sheet_prompt(brief), [cast], "2K", name, seed)


def base_path(cid: str) -> Path:
    return cdir(cid) / "sheet_npc_3q.png"


def do_face(cid: str, kind: str, seed: int | None, suffix: str = "") -> list[Path]:
    brief = brief_of(cid)
    prompt = finish(FACE_PROMPTS[kind].format(**words(brief)), key_of(brief))
    return edit_call(cid, NB2, prompt, [base_path(cid)], "1K", f"pose_{kind}_nb2{suffix}", seed)


def do_gesture(cid: str, seed: int | None, suffix: str = "") -> list[Path]:
    brief = brief_of(cid)
    prompt = finish(GESTURE_PROMPT.format(**words(brief)), key_of(brief))
    return edit_call(cid, NB2, prompt, [base_path(cid)], "2K", f"pose_gesture_nb2{suffix}", seed)


def video_canvas(cid: str) -> Path:
    """Keyed base on a flat key canvas, torso centre on the canvas centre (= the still set's pivot x)."""
    brief = brief_of(cid)
    colour = fr.KEY_COLOURS[key_of(brief)]
    keyed = fr.chroma_key(fr.load_rgb(base_path(cid)))
    x0, y0, x1, y1 = fr.alpha_bbox(keyed)
    cx = fr.torso_center_x(keyed)
    w, h = VIDEO_CANVAS
    scale = h * VIDEO_FIG / (y1 - y0)
    img = Image.fromarray(keyed, "RGBA").resize((round(keyed.shape[1] * scale), round(keyed.shape[0] * scale)),
                                                Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", VIDEO_CANVAS, colour)
    canvas.paste(img, (round(w / 2 - cx * scale), round(h * VIDEO_FEET - y1 * scale)), img)
    out = cdir(cid) / "video_in_3q.png"
    canvas.save(out)
    return out


def do_video(cid: str, suffix: str = "", motion: str | None = None) -> list[Path]:
    brief = brief_of(cid)
    image = video_canvas(cid)
    prompt = chars.recolour_key_words((motion or brief["idle_motion"]) + IDLE_SUFFIX, key_of(brief))
    uri = fal_api.image_data_uri(image, fmt="PNG")
    arguments = {"prompt": prompt, "image_url": uri, "end_image_url": uri, "duration": "6", "resolution": "768P",
                 "prompt_optimizer": False}
    price = fal_api.video_price(HAILUO, 6.0, "768P")
    name = f"video_idle_hailuo_loop{suffix}"
    asset = f"characters/{cid}/{name}"
    BUDGET.reserve(asset, price)
    try:
        result = fal_api.run(HAILUO, arguments, asset, price, budget=None, timeout_s=1800, poll_s=8)
    finally:
        BUDGET.release(price)
    meta = {"model": HAILUO, "usd": round(price, 4), "prompt": prompt, "input": image.name, "tail_image": True,
            "seconds": 6.0, "resolution": "768P",
            "arguments": {k: v for k, v in arguments.items() if not str(v).startswith("data:")}}
    return chars.save_outputs(result, cdir(cid) / name, meta)


def run_jobs(jobs: list[tuple[str, callable]], workers: int) -> None:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fn): label for label, fn in jobs}
        for future in as_completed(futures):
            label = futures[future]
            try:
                print(f"OK   {label}: {[p.name for p in future.result()]}", flush=True)
            except Exception as exc:  # report and continue with the other jobs
                print(f"FAIL {label}: {exc}", flush=True)


# ----------------------------------------------------------------------------- local build

def align(base_key: np.ndarray, edit_rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    if edit_rgb.shape != base_key.shape[:2] + (3,):
        edit_rgb = np.asarray(Image.fromarray(edit_rgb).resize(base_key.shape[1::-1], Image.Resampling.LANCZOS))
    edit_key = fr.chroma_key(edit_rgb)
    dy, dx = fr.phase_shift(base_key[..., 3].astype(np.float32), edit_key[..., 3].astype(np.float32))
    return np.roll(edit_rgb, (dy, dx), axis=(0, 1)), np.roll(edit_key, (dy, dx), axis=(0, 1)), (int(dy), int(dx))


def changed_rows(base_rgb: np.ndarray, base_key: np.ndarray, edit_rgb: np.ndarray, top: int, bottom: int,
                 cols: tuple[int, int], threshold: float = 22.0) -> np.ndarray:
    edit_rgb, edit_key, _ = align(base_key, edit_rgb)
    diff = np.abs(base_rgb.astype(np.float32) - edit_rgb.astype(np.float32)).mean(axis=2)
    changed = (diff > threshold) & ((base_key[..., 3] > 128) | (edit_key[..., 3] > 128))
    counts = changed[top:bottom, cols[0]:cols[1]].sum(axis=1).astype(np.float32)
    return counts


def centroid_of_peak(counts: np.ndarray, offset: int) -> float | None:
    if counts.max() <= 0:
        return None
    smooth = np.convolve(counts, np.ones(9) / 9, mode="same")
    peak = int(np.argmax(smooth))
    lo, hi = peak, peak
    while lo > 0 and smooth[lo - 1] > smooth[peak] * 0.35:
        lo -= 1
    while hi < len(smooth) - 1 and smooth[hi + 1] > smooth[peak] * 0.35:
        hi += 1
    w = smooth[lo:hi + 1]
    return offset + float((np.arange(lo, hi + 1) * w).sum() / w.sum())


def face_landmarks(cid: str) -> dict:
    """Eye line from the blink edit, mouth line from the 'ah' edit (rows of the base sheet)."""
    d = cdir(cid)
    base_rgb = fr.load_rgb(base_path(cid))
    base_key = fr.chroma_key(base_rgb)
    x0, y0, x1, y1 = fr.alpha_bbox(base_key)
    h = y1 - y0
    child = bool(brief_of(cid).get("child"))
    head = h / (5.5 if child else 6.5)
    # search window: the head only (rows from the hair top to below the chin, columns of the hair/skull band)
    head_bottom = y0 + int(head * 1.25)
    skull = base_key[y0:y0 + int(head * 0.6), :, 3] > 128
    hc = np.flatnonzero(skull.any(axis=0))
    pad = int(head * 0.15)
    cols = (max(0, int(hc.min()) - pad), int(hc.max()) + pad)
    blink = changed_rows(base_rgb, base_key, fr.load_rgb(d / "pose_blink_nb2.png"), y0, head_bottom, cols)
    blink[: int(head * 0.3)] = 0           # hair
    blink[int(head * 0.85):] = 0           # below the nose
    eye = centroid_of_peak(blink, y0)
    talk = changed_rows(base_rgb, base_key, fr.load_rgb(d / "pose_talk_a_nb2.png"), y0, head_bottom, cols)
    if eye is not None:
        talk[: max(0, int(eye - y0 + head * 0.18))] = 0
    mouth = centroid_of_peak(talk, y0)
    if eye is None or not (0.35 * head <= eye - y0 <= 0.8 * head):
        eye = y0 + 0.58 * head
    if mouth is None or not (eye + 0.18 * head <= mouth <= eye + 0.6 * head):
        mouth = eye + 0.36 * head
    gap = mouth - eye
    bands = {
        "eyes": [eye - 0.6 * gap, eye + 0.4 * gap],
        "mouth": [eye + 0.45 * gap, mouth + 1.05 * gap],
    }
    frac = {k: [round((a - y0) / h, 4), round((b - y0) / h, 4)] for k, (a, b) in bands.items()}
    return {"figure_box": [x0, y0, x1, y1], "eye_y": round(eye, 1), "mouth_y": round(mouth, 1),
            "bands_px": {k: [round(a), round(b)] for k, (a, b) in bands.items()}, "bands_frac": frac}


def patch_face(base_rgb: np.ndarray, edit_rgb: np.ndarray, band: tuple[float, float], feather: int = 8,
               threshold: float = 16.0) -> tuple[np.ndarray, dict]:
    """Transplant the changed pixels of a face edit inside a horizontal band onto the keyed base.

    Unlike frames.patch_pose this (1) colour-matches the edit to the base first (per-channel gain/offset fitted on
    head pixels outside the band, which should not have changed: NB2 sometimes re-renders a face warmer or
    brighter), (2) keeps the base silhouette and alpha (no key-colour fringe from the softer 1K edit) and
    (3) fades the band edges, so a blink or a mouth frame changes nothing but the eyes or the mouth.
    """
    base_key = fr.chroma_key(base_rgb)
    edit_rgb, edit_key, shift = align(base_key, edit_rgb)
    x0, y0, x1, y1 = fr.alpha_bbox(base_key)
    h = y1 - y0
    top, bottom = y0 + band[0] * h, y0 + band[1] * h
    rows = np.arange(base_rgb.shape[0], dtype=np.float32)[:, None]
    ramp = max(2.0, feather * 1.5)
    band_w = np.clip((rows - top) / ramp, 0, 1) * np.clip((bottom - rows) / ramp, 0, 1)
    band_w = band_w * band_w * (3 - 2 * band_w)
    solid = (base_key[..., 3] > 250) & (edit_key[..., 3] > 250)
    head = np.zeros(solid.shape, bool)
    head[y0:y0 + int(h * 0.30)] = True
    ref = solid & head & (band_w[:, :1].repeat(solid.shape[1], 1) < 0.01)
    b = base_key[..., :3].astype(np.float32)
    e = edit_key[..., :3].astype(np.float32)          # un-mixed and despilled edit colours
    border = np.concatenate([base_rgb[:4].reshape(-1, 3), base_rgb[-4:].reshape(-1, 3)]).astype(np.float32)
    kind = fr.key_kind(np.median(border, axis=0))
    keyish = fr.keyness(edit_rgb.astype(np.float32), kind) > 12   # key colour painted into the edit (e.g. lenses)
    gains = []
    if ref.sum() > 500:
        for ch in range(3):
            xs, ys = e[..., ch][ref], b[..., ch][ref]
            # moment matching (a regression slope would flatten the contrast: the 1K edit is softer)
            a = float(np.clip(ys.std() / max(1e-3, xs.std()), 0.9, 1.1))
            off = float(ys.mean() - a * xs.mean())
            e[..., ch] = e[..., ch] * a + off
            gains.append([round(a, 3), round(off, 1)])
    e = e.clip(0, 255)
    good = (base_key[..., 3] > 250) & (edit_key[..., 3] > 250) & ~keyish
    interior = np.asarray(Image.fromarray((good * 255).astype(np.uint8), "L")
                          .filter(ImageFilter.MinFilter(5)), np.float32) / 255
    diff = np.abs(b - e).mean(axis=2)
    changed = (diff > threshold) & (band_w[:, 0:1] > 0.0) & (interior > 0)
    mask = Image.fromarray((changed * 255).astype(np.uint8), "L")
    mask = mask.filter(ImageFilter.MaxFilter(2 * (feather // 2) + 1)).filter(ImageFilter.GaussianBlur(feather))
    m = (np.asarray(mask, np.float32) / 255) * band_w
    m = m * np.asarray(Image.fromarray((interior * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)),
                       np.float32) / 255
    out = base_key.copy()
    rgb = base_key[..., :3].astype(np.float32) * (1 - m[..., None]) + e * m[..., None]
    out[..., :3] = rgb.clip(0, 255).astype(np.uint8)
    outside = (base_key[..., 3] > 128) & (band_w[:, 0:1].repeat(solid.shape[1], 1) <= 0)
    report = {"shift_dy_dx": list(shift), "colour_fit": gains, "changed_px": int(changed.sum()),
              "mean_abs_diff_outside_band_after_fit": round(float(diff[outside].mean()), 2)}
    return out, report


def build_cells(base_rgb: np.ndarray, layers: list[np.ndarray], target_h: int) -> tuple[list[Image.Image], dict]:
    base_key = fr.chroma_key(base_rgb)
    _x0, by0, _x1, by1 = fr.alpha_bbox(base_key)
    scale = target_h / (by1 - by0)
    pivot_x = fr.torso_center_x(base_key)
    boxes = [fr.alpha_bbox(layer) for layer in layers]
    half = max(max(pivot_x - b[0] for b in boxes), max(b[2] - pivot_x for b in boxes))
    top = max(by1 - b[1] for b in boxes)
    below = max(0, max(b[3] - by1 for b in boxes))
    cell_w = 2 * int(np.ceil(half * scale)) + 8
    cell_h = int(np.ceil(top * scale)) + 8 + int(np.ceil(below * scale))
    pivot_y = cell_h - 4 - int(np.ceil(below * scale))
    cells = []
    for layer in layers:
        img = Image.fromarray(layer, "RGBA")
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
        cell = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
        cell.paste(img, (round(cell_w / 2 - pivot_x * scale), round(pivot_y - by1 * scale)), img)
        cells.append(cell)
    return cells, {"cell": [cell_w, cell_h], "pivot": [cell_w // 2, pivot_y], "scale": round(scale, 4)}


def build_stills(cid: str, gesture_mode: str = "patch") -> dict:
    d = cdir(cid)
    brief = brief_of(cid)
    target_h = int(brief.get("height_px", 512))
    lm = face_landmarks(cid)
    base_rgb = fr.load_rgb(base_path(cid))
    base_key = fr.chroma_key(base_rgb)
    layers, reports = [base_key], {}
    sources = ["key:sheet_npc_3q.png"]
    for label, src, band in (("blink", "pose_blink_nb2.png", "eyes"), ("talk_a", "pose_talk_a_nb2.png", "mouth"),
                             ("talk_b", "pose_talk_o_nb2.png", "mouth")):
        rgba, rep = patch_face(base_rgb, fr.load_rgb(d / src), tuple(lm["bands_frac"][band]))
        layers.append(rgba)
        reports[label] = rep
        sources.append(f"patch[{band} {lm['bands_frac'][band]}]:{src}")
    g_rgb = fr.load_rgb(d / "pose_gesture_nb2.png")
    if gesture_mode == "patch":
        rgba, rep = fr.patch_pose(base_rgb, g_rgb, (0.0, 1.0), feather=10)
        reports["gesture"] = rep
    else:
        g_rgb, rgba, shift = align(base_key, g_rgb)
        reports["gesture"] = {"shift_dy_dx": list(shift)}
    layers.append(rgba)
    sources.append(f"{gesture_mode}:pose_gesture_nb2.png")
    cells, geo = build_cells(base_rgb, layers, target_h)
    names = ["idle", "blink", "talk_a", "talk_b", "gesture"]
    meta = {"name": "npc", "frames": names, **geo, "height_px": target_h, "playback_fps": 8, "sources": sources,
            "face_landmarks": lm, "edit_reports": reports}
    gif = [(0, 1400), (1, 110), (0, 900), (2, 125), (3, 125), (2, 125), (0, 125), (3, 125), (2, 125), (0, 700),
           (4, 1200), (0, 600)]
    fr.export_cells(cells, d / "npc_set", "npc", meta, names, gif, names=names)
    fr.save_rgba(fr.crop_to_figure(base_key), d / "keyed" / "base_3q.png")
    return meta


_CHROMA_KEY = fr.chroma_key


def _video_key(rgb: np.ndarray, *args, **kwargs) -> np.ndarray:
    """chroma_key for video frames (choke > 0) that also clears key colour enclosed by the figure.

    Video models paint the key colour into small enclosed gaps (between an arm and the body); frames.chroma_key
    keeps pixels away from the open background opaque (interior protection) and despills them to olive. None of
    these characters wears the key colour, so clearly key-dominant raw pixels are made transparent.
    """
    out = _CHROMA_KEY(rgb, *args, **kwargs)
    if kwargs.get("choke", 0) > 0:
        rgbf = rgb.astype(np.int16)
        border = np.concatenate([rgbf[:4].reshape(-1, 3), rgbf[-4:].reshape(-1, 3)])
        kind = fr.key_kind(np.median(border, axis=0))
        r, g, b = rgbf[..., 0], rgbf[..., 1], rgbf[..., 2]
        keyish = (g - np.maximum(r, b) > 30) if kind == "green" else (np.minimum(r, b) - g > 40)
        if keyish.any():
            # the open background: transparent components that touch the image border
            labels, _sizes = fr.label_components(out[..., 3] < 128)
            edge_labels = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
            outside = np.isin(labels, edge_labels[edge_labels > 0])
            near_out = np.asarray(Image.fromarray((outside * 255).astype(np.uint8), "L")
                                  .filter(ImageFilter.MaxFilter(5))) > 0
            enclosed = keyish & ~near_out          # key colour inside the figure, not on its outer edge
            if enclosed.any():
                grow = np.asarray(Image.fromarray((enclosed * 255).astype(np.uint8), "L")
                                  .filter(ImageFilter.MaxFilter(3))) > 0
                out = out.copy()
                out[..., 3] = np.where(grow & ~near_out, 0, out[..., 3])
    return out


fr.chroma_key = _video_key


def closure_frame(paths: list[Path], search: int = 12) -> int:
    """Index near the end of a start=end clip that matches frame 0 best (the loop length)."""
    first = np.asarray(Image.open(paths[0]).convert("RGB").resize((128, 128)), np.float32)
    best, best_i = 1e9, len(paths) - 1
    for i in range(max(1, len(paths) - search), len(paths)):
        err = float(np.abs(np.asarray(Image.open(paths[i]).convert("RGB").resize((128, 128)), np.float32)
                           - first).mean())
        if err < best:
            best, best_i = err, i
    return best_i


def build_idle(cid: str, video_name: str = "video_idle_hailuo_loop.mp4", out_name: str = "idle_hailuo",
               frame_range: tuple[int, int] | None = None, pingpong: bool = False) -> dict:
    d = cdir(cid)
    brief = brief_of(cid)
    target_h = int(brief.get("height_px", 512))
    raw = d / "_frames" / Path(video_name).stem
    info = fr.video_info(d / video_name)
    paths = fr.extract_frames(d / video_name, raw)
    end = closure_frame(paths) if frame_range is None else frame_range[1]
    start = 0 if frame_range is None else frame_range[0]
    first = fr.chroma_key(fr.load_rgb(paths[0]))
    fb = fr.alpha_bbox(first)
    ref_h = fb[3] - fb[1]
    if pingpong:
        # calm half of a clip played forward and back (the far end of the clip is not used)
        half = IDLE_FRAMES // 2
        picks = [start + round(i * (end - start) / half) for i in range(half + 1)]
        seq = picks + picks[-2:0:-1]
        tmp = d / "_frames" / (Path(video_name).stem + "_pp")
        tmp.mkdir(parents=True, exist_ok=True)
        for old in tmp.glob("f_*.png"):
            old.unlink()
        for j, src in enumerate(seq):
            shutil.copy(paths[src], tmp / f"f_{j:04d}.png")
        seq_paths = sorted(tmp.glob("f_*.png"))
        meta = fr.build_loop(seq_paths, d / out_name, info.get("fps", 24.0), len(seq_paths), (1, 2), 0, 0, False,
                             target_h, None, None, "idle", choke=1, frame_range=(0, len(seq_paths)),
                             ref_height=ref_h)
        meta["pingpong_source_frames"] = seq
    else:
        # key only the sampled frames (plus the closing one): 37 instead of ~142 keyings
        fps = info.get("fps", 24.0)
        picks = [start + round(i * (end - start) / IDLE_FRAMES) for i in range(IDLE_FRAMES)] + [end]
        tmp = d / "_frames" / (Path(video_name).stem + "_picks")
        tmp.mkdir(parents=True, exist_ok=True)
        for old in tmp.glob("f_*.png"):
            old.unlink()
        for j, src in enumerate(picks):
            shutil.copy(paths[src], tmp / f"f_{j:04d}.png")
        meta = fr.build_loop(sorted(tmp.glob("f_*.png")), d / out_name, fps, IDLE_FRAMES, (1, 2), 0, 0, False,
                             target_h, None, None, "idle", choke=1, frame_range=(0, IDLE_FRAMES), ref_height=ref_h,
                             playback_fps=IDLE_FRAMES / ((end - start) / fps))
        meta.update(source_frames=picks[:-1], cycle_frames=end - start, cycle_seconds=round((end - start) / fps, 3))
    meta["video"] = video_name
    (d / out_name / "idle_sheet.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def build_busts(cid: str) -> list[str]:
    d = cdir(cid)
    brief = brief_of(cid)
    made = []
    variants = brief.get("variants", [])
    sources = [("npc", d / "npc_set" / "npc_sheet.png")]
    if (d / "idle_hailuo" / "idle_sheet.png").exists():
        sources.append(("idle", d / "idle_hailuo" / "idle_sheet.png"))
    for prefix, sheet in sources:
        if "window" in variants or "window_glass" in variants:
            vis = float(brief.get("bust_visible", 0.5))
            glass.make_bust(sheet, d / "window", f"{prefix}_bust", vis, False, 0.16, 0.10, 1.08)
            made.append(f"window/{prefix}_bust")
            if "window_glass" in variants:
                glass.make_bust(sheet, d / "window", f"{prefix}_bust_glass", vis, True, 0.16, 0.10, 1.08)
                made.append(f"window/{prefix}_bust_glass")
        if "counter" in variants:
            vis = float(brief.get("counter_visible", 0.55))
            glass.make_bust(sheet, d / "counter", f"{prefix}_counter", vis, False, 0.16, 0.10, 1.08)
            made.append(f"counter/{prefix}_counter")
    return made


# ----------------------------------------------------------------------------- review sheets

def face_crop_strip(cells: list[Image.Image], names: list[str], lm_frac: dict, height_px: int, zoom: int = 3
                    ) -> Image.Image:
    """Heads of the still cells, enlarged, for checking blink / mouth / flicker."""
    c0 = cells[0]
    pivot_y = c0.height - 4
    top = int(pivot_y - height_px) - 4
    bottom = int(pivot_y - height_px * (1 - 0.30))
    a = np.asarray(c0.getchannel("A"))
    cols = np.flatnonzero((a[top:bottom] > 100).any(axis=0))
    left, right = int(cols.min()) - 4, int(cols.max()) + 4
    crops = []
    for cell, name in zip(cells, names):
        crop = cell.crop((left, top, right, bottom))
        bg = Image.new("RGBA", crop.size, (120, 130, 140, 255))
        bg.alpha_composite(crop)
        bg = bg.resize((crop.width * zoom, crop.height * zoom), Image.Resampling.LANCZOS)
        ImageDraw.Draw(bg).text((6, 4), name, fill=(255, 255, 255))
        crops.append(bg)
    strip = Image.new("RGB", (sum(c.width for c in crops) + 6 * len(crops), crops[0].height), (30, 30, 30))
    x = 0
    for c in crops:
        strip.paste(c.convert("RGB"), (x, 0))
        x += c.width + 6
    return strip


def review(cid: str) -> Path:
    d = cdir(cid)
    out_dir = d / "review"
    out_dir.mkdir(exist_ok=True)
    meta = json.loads((d / "npc_set" / "npc_sheet.json").read_text(encoding="utf-8"))
    names = meta["frames"]
    cells = [Image.open(d / "npc_set" / f"npc_{n}.png").convert("RGBA") for n in names]
    faces = face_crop_strip(cells, names, meta["face_landmarks"]["bands_frac"], meta["height_px"])
    faces.save(out_dir / "faces.jpg", quality=90)
    # body difference of every still against idle (should be ~0 outside the head, except the gesture)
    base = np.asarray(cells[0], np.float32)
    diffs = {}
    for cell, n in zip(cells[1:], names[1:]):
        arr = np.asarray(cell, np.float32)
        hmask = np.zeros(arr.shape[:2], bool)
        hmask[: int(arr.shape[0] - 4 - meta["height_px"] * 0.72)] = True
        body = ~hmask
        diffs[n] = round(float(np.abs(arr[body] - base[body]).mean()), 3)
    (out_dir / "still_body_diff.json").write_text(json.dumps(diffs, indent=2), encoding="utf-8")
    return out_dir


def idle_strip(cid: str) -> Path | None:
    d = cdir(cid)
    sheet_json = d / "idle_hailuo" / "idle_sheet.json"
    if not sheet_json.exists():
        return None
    meta = json.loads(sheet_json.read_text(encoding="utf-8"))
    sheet = Image.open(d / "idle_hailuo" / "idle_sheet.png").convert("RGBA")
    cw, ch = meta["cell"]
    picks = list(range(0, meta["frames"], 3))
    still = Image.open(d / "npc_set" / "npc_idle.png").convert("RGBA")
    cells = [still] + [sheet.crop((i * cw, 0, (i + 1) * cw, ch)) for i in picks]
    labels = ["still"] + [f"idle {i}" for i in picks]
    out = d / "review" / "idle_strip.jpg"
    fr.contact_sheet(cells, out, cell_h=360, labels=labels)
    return out


# ----------------------------------------------------------------------------- export

def grid_pack(strip: Image.Image, cell: tuple[int, int], frames: int) -> tuple[Image.Image, int, int]:
    cw, ch = cell
    if strip.width <= MAX_TEX:
        return strip, frames, 1
    rows = int(np.ceil(frames * cw / MAX_TEX))
    while True:
        cols = int(np.ceil(frames / rows))
        if cols * cw <= MAX_TEX:
            break
        rows += 1
    if rows * ch > MAX_TEX:
        raise SystemExit(f"{frames} cells of {cell} do not fit in {MAX_TEX} px")
    grid = Image.new("RGBA", (cols * cw, rows * ch), (0, 0, 0, 0))
    for i in range(frames):
        grid.paste(strip.crop((i * cw, 0, (i + 1) * cw, ch)), ((i % cols) * cw, (i // cols) * ch))
    return grid, cols, rows


SHEET_SOURCES = {
    "npc": "npc_set/npc_sheet.png",
    "idle": "idle_hailuo/idle_sheet.png",
    "npc_bust": "window/npc_bust_sheet.png",
    "npc_bust_glass": "window/npc_bust_glass_sheet.png",
    "idle_bust": "window/idle_bust_sheet.png",
    "idle_bust_glass": "window/idle_bust_glass_sheet.png",
    "npc_counter": "counter/npc_counter_sheet.png",
    "idle_counter": "counter/idle_counter_sheet.png",
}


def anims(still: str, video: str | None) -> dict:
    return {
        "idle": ({"sheet": video, "loop": True} if video else {"sheet": still, "frames": ["idle"]}),
        "idle_still": {"sheet": still, "frames": ["idle"]},
        "blink": {"sheet": still, "frames": ["blink"], "hold_ms": 110, "every_s": [2.5, 6.0],
                  "note": "only while the still idle is shown (the video idle blinks by itself)"},
        "talk": {"sheet": still, "frames": ["talk_a", "talk_b", "talk_a", "idle", "talk_b", "talk_a", "idle"],
                 "fps": 8, "loop": True},
        "gesture": {"sheet": still, "frames": ["gesture"], "hold_ms": 1200, "oneshot": True,
                    "note": "PlayGesture: hold, then return to idle (no in-betweens)"},
    }


def export(cid: str) -> dict:
    src_dir, dst_dir = cdir(cid), GAME_ACTORS / cid
    brief = brief_of(cid)
    dst_dir.mkdir(parents=True, exist_ok=True)
    sheets = {}
    for key, rel in SHEET_SOURCES.items():
        src = src_dir / rel
        if not src.exists():
            continue
        meta = json.loads(src.with_suffix(".json").read_text(encoding="utf-8"))
        out = dict(meta)
        if isinstance(meta.get("frames"), list):
            out["frame_names"] = meta["frames"]
            out["frames"] = len(meta["frames"])
        for drop in ("source_frames", "sources", "face_landmarks", "edit_reports", "pingpong_source_frames"):
            out.pop(drop, None)
        out.setdefault("oneshot", False)
        out.setdefault("stride_px_per_s", None)
        out["loop"] = key.startswith("idle") and not out["oneshot"]
        out.setdefault("pivot_is_sill_line", False)
        strip = Image.open(src).convert("RGBA")
        packed, cols, rows = grid_pack(strip, tuple(out["cell"]), out["frames"])
        name = f"{key}_sheet.webp"
        out["file"] = name
        out["columns"], out["rows"] = cols, rows
        lossless = not key.startswith("idle")
        if lossless:
            packed.save(dst_dir / name, "WEBP", lossless=True, quality=100, method=6)
        else:
            packed.save(dst_dir / name, "WEBP", quality=92, alpha_quality=100, method=6)
        check = Image.open(dst_dir / name)
        assert check.size == packed.size and max(check.size) <= MAX_TEX, (name, check.size)
        (dst_dir / f"{key}_sheet.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n",
                                                  encoding="utf-8", newline="\n")
        sheets[key] = {"file": name, "json": f"{key}_sheet.json", "size": list(packed.size), "cell": out["cell"],
                       "pivot": out["pivot"], "frames": out["frames"], "columns": cols, "rows": rows}
    manifest = {
        "id": cid,
        "source": f"art/characters/{cid}",
        "view": "three-quarter, facing right (mirror for facing left)",
        "height_px": int(brief.get("height_px", 512)),
        "pivot": "feet centre, 4 px above the cell bottom (window / counter variants: centre of the cut edge)",
        "staging": "standing" + ("; variants: " + ", ".join(brief["variants"]) if brief.get("variants") else ""),
        "sheets": sheets,
        "animations": anims("npc", "idle" if "idle" in sheets else None),
        "switching": ("Start talking only at a video idle loop boundary (cell 0 matches the still idle pose) or "
                      "cross-fade ~80 ms; video cells are slightly softer than the edit-based stills."),
        "notes": brief.get("notes", ""),
    }
    variants = {}
    if "npc_bust_glass" in sheets:
        variants["window_glass"] = {"animations": anims("npc_bust_glass", "idle_bust_glass" if "idle_bust_glass"
                                                        in sheets else None),
                                    "note": "behind closed glass: bust cut at the sill line, pale veil + soft "
                                            "reflection"}
    if "npc_bust" in sheets:
        variants["window"] = {"animations": anims("npc_bust", "idle_bust" if "idle_bust" in sheets else None),
                              "note": "bust cut at the sill line, without the glass treatment (open hatch, or if "
                                      "the engine adds its own glass layer)"}
    if "npc_counter" in sheets:
        variants["counter"] = {"animations": anims("npc_counter", "idle_counter" if "idle_counter" in sheets
                                                   else None),
                               "note": "standing behind a table or counter: cut at the counter-top line (sill_y = "
                                       "canvas y of the painted counter top)"}
    if variants:
        manifest["variants"] = variants
        manifest["default_variant"] = None
    (dst_dir / "actor.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
                                        newline="\n")
    return manifest


# ----------------------------------------------------------------------------- CLI

def main() -> None:
    global BUDGET
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--budget", type=float, default=0.0, help="USD cap of the task (paid commands)")
    parser.add_argument("--budget-ids", help="comma-separated ids whose spend counts (default: the ids given)")
    parser.add_argument("--since", help="ISO timestamp: only spend logged from then on counts")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=1995)
    parser.add_argument("--suffix", default="", help="output name suffix for retakes (e.g. _r2)")
    parser.add_argument("cmd", choices=["sheet", "faces", "face", "gesture", "video", "build", "idle", "busts",
                                        "review", "export"])
    parser.add_argument("ids", nargs="+")
    parser.add_argument("--kind", help="face: blink|talk_a|talk_o")
    parser.add_argument("--gesture-mode", default="patch", choices=["patch", "key"])
    parser.add_argument("--range", help="idle: a,b source frame range")
    parser.add_argument("--pingpong", action="store_true")
    parser.add_argument("--video", default="video_idle_hailuo_loop.mp4")
    args = parser.parse_args()
    ids = args.ids
    budget_ids = args.budget_ids.split(",") if args.budget_ids else ids
    BUDGET = Budget(args.budget, budget_ids, args.since)
    seed = args.seed
    if args.cmd == "sheet":
        run_jobs([(f"{c} sheet", lambda c=c: do_sheet(c, "sheet_npc_3q" + args.suffix, seed)) for c in ids],
                 args.workers)
    elif args.cmd == "faces":
        jobs = []
        for c in ids:
            for kind in ("blink", "talk_a", "talk_o"):
                jobs.append((f"{c} {kind}", lambda c=c, k=kind: do_face(c, k, seed, args.suffix)))
            jobs.append((f"{c} gesture", lambda c=c: do_gesture(c, seed, args.suffix)))
        run_jobs(jobs, args.workers)
    elif args.cmd == "face":
        run_jobs([(f"{c} {args.kind}", lambda c=c: do_face(c, args.kind, seed, args.suffix)) for c in ids],
                 args.workers)
    elif args.cmd == "gesture":
        run_jobs([(f"{c} gesture", lambda c=c: do_gesture(c, seed, args.suffix)) for c in ids], args.workers)
    elif args.cmd == "video":
        run_jobs([(f"{c} video", lambda c=c: do_video(c, args.suffix)) for c in ids], args.workers)
    elif args.cmd == "build":
        for c in ids:
            meta = build_stills(c, args.gesture_mode)
            print(c, json.dumps({k: meta[k] for k in ("cell", "pivot", "scale")}),
                  json.dumps(meta["face_landmarks"]["bands_frac"]),
                  json.dumps({k: (v.get("colour_fit"), v.get("mean_abs_diff_outside_band_after_fit")) for k, v in meta["edit_reports"].items()}))
            review(c)
    elif args.cmd == "idle":
        rng = tuple(int(v) for v in args.range.split(",")) if args.range else None
        for c in ids:
            meta = build_idle(c, args.video, frame_range=rng, pingpong=args.pingpong)
            print(c, json.dumps({k: meta.get(k) for k in ("frames", "cell", "pivot", "cycle_frames",
                                                          "playback_fps", "height_px_range")}))
            idle_strip(c)
    elif args.cmd == "busts":
        for c in ids:
            print(c, build_busts(c))
    elif args.cmd == "review":
        for c in ids:
            print(review(c), idle_strip(c))
    elif args.cmd == "export":
        for c in ids:
            m = export(c)
            print(c, {k: (v["size"], v["frames"], v["columns"]) for k, v in m["sheets"].items()})


if __name__ == "__main__":
    main()
