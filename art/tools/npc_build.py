"""Local (free) build of NPC sprite sets: milestone-2 batch (1960 Ivanka: BOZO, BERTA, POSTA, LIDA, RUDO, SKLAD,
VERA60; 1982 Dubravka: DOBRO, RUZENA, MARTA82, SIMON). Paid calls are made with npcs.py; this tool only processes.

Per character the settings live in art/characters/<ID>/build.json (written by `init`, edited by hand):
  base_source   raw approved sheet (default sheet_npc_3q.png)
  fix           optional local design fix applied to the base: bozo_text | sklad_blue | ruzena_boots
  eye_band / mouth_band   fractions of the figure height (from the top) that blink / talk edits may change
  posture       standing | seated (seated: scale from the head size of the standing sheet, pivot = head centre x)
  bust          {"visible": f, "glass": bool, "aliases": [...]}  counter / window bust variants (optional)

Subcommands (run from anywhere):
  init   ID [ID ...]   write build.json defaults (keeps existing values)
  base   ID            base.png (flat key, design fixes applied) + keyed/base_3q.png
  canvas ID            video_in_3q.png (Hailuo input: figure 80 % of 1024 px, feet at 90 %)
  bands  ID            propose eye / mouth bands from the NB2 face edits; review crop in review/
  stills ID            npc_set/: idle, blink, talk_a, talk_b, gesture on one pivot (face bands transplanted)
  idle   ID            idle_hailuo/: 36-frame loop from video_idle_hailuo_loop.mp4, aligned to the still idle
  bust   ID            window/: bust variants of the still set and the idle loop (clean + glass)
  export ID            src/game/assets/actors/ID/: WebP sheets as grids <= 4096 px, sheet JSON, actor.json
  review ID            review/: head crops, flicker numbers, idle strip, staging mock in the room's NPC rect
  all    ID            stills idle bust export review
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import export_actors
import frames
import glass

ART = frames.ART
REPO = ART.parent
CHAR_ROOT = ART / "characters"
GAME_ACTORS = REPO / "src" / "game" / "assets" / "actors"
GAME_JSON = REPO / "src" / "game" / "data" / "game.json"
MAX_SIDE = 4096
FIGURE_PX = 512
IDLE_FRAMES = 36

DEFAULTS = {
    "base_source": "sheet_npc_3q.png",
    "fix": None,
    "posture": "standing",
    "eye_band": None,
    "mouth_band": None,
    "head_frac": 0.2,
    "bust": None,
    "notes": "",
}


# ----------------------------------------------------------------------------- config

def char_dir(cid: str) -> Path:
    return CHAR_ROOT / cid


def load_cfg(cid: str) -> dict:
    path = char_dir(cid) / "build.json"
    cfg = dict(DEFAULTS)
    if path.exists():
        cfg.update(json.loads(path.read_text(encoding="utf-8")))
    return cfg


def save_cfg(cid: str, cfg: dict) -> None:
    (char_dir(cid) / "build.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
                                              encoding="utf-8", newline="\n")


def brief(cid: str) -> dict:
    return json.loads((CHAR_ROOT / "characters.json").read_text(encoding="utf-8"))[cid]


def key_rgb(cid: str) -> tuple[int, int, int]:
    return frames.KEY_COLOURS[brief(cid).get("key", "green")]


# ----------------------------------------------------------------------------- base fixes (local, free)

def fix_bozo_text(rgb: np.ndarray) -> np.ndarray:
    """The folded timetable came with large invented Latin letters; fade all print on the paper to faint grey marks."""
    key = frames.chroma_key(rgb)
    x0, y0, x1, y1 = frames.alpha_bbox(key)
    h, w = y1 - y0, x1 - x0
    ry0, ry1, rx0, rx1 = y0 + int(0.50 * h), y0 + int(0.66 * h), x0 + int(0.60 * w), x1
    sub = rgb[ry0:ry1, rx0:rx1].astype(np.float32)
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    sat = (sub.max(axis=2) - sub.min(axis=2)) / np.maximum(1, sub.max(axis=2))
    paper = (lum > 165) & (sat < 0.22)
    comps, sizes = frames.label_components(paper)
    biggest = int(np.argmax(sizes) + 1)
    region = comps == biggest
    ys, xs = np.nonzero(region)
    pb = (ys.min(), ys.max() + 1, xs.min(), xs.max() + 1)
    hull = np.zeros_like(region)
    hull[pb[0]:pb[1], pb[2]:pb[3]] = True
    skin = (r > g + 12) & (g > b) & (r - b > 40)
    skin = np.asarray(Image.fromarray((skin * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))) > 0
    # the sheet's interior (paper plus the print on it), eroded so the painted outline of the paper stays
    inner = Image.fromarray((paper * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(11)).filter(
        ImageFilter.MinFilter(9))
    inner = (np.asarray(inner) > 0) & hull & ~skin
    # normalized convolution: blur only the clean paper pixels, so the print disappears and the fold shading stays
    clean = (paper & inner).astype(np.float32)
    num = np.dstack([np.asarray(Image.fromarray((sub[..., c] * clean).clip(0, 255).astype(np.uint8))
                                .filter(ImageFilter.GaussianBlur(14)), np.float32) for c in range(3)])
    den = np.asarray(Image.fromarray((clean * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14)),
                     np.float32)[..., None] / 255
    smooth = num / np.maximum(den, 1e-3)
    out = sub.copy()
    out[inner] = smooth[inner]
    res = rgb.copy()
    res[ry0:ry1, rx0:rx1] = out.clip(0, 255).astype(np.uint8)
    return res


def fix_sklad_blue(rgb: np.ndarray) -> np.ndarray:
    """Design says blue work clothes; Pro painted them lilac-grey. Rotate violet hues to a faded workwear blue."""
    img = Image.fromarray(rgb).convert("HSV")
    hsv = np.asarray(img).astype(np.float32)
    hue, sat, val = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
    key = frames.chroma_key(rgb)[..., 3] > 0
    sel = key & (hue > 222) & (hue < 320) & (sat > 0.04)
    weight = np.clip((sat - 0.04) / 0.06, 0, 1) * sel
    new_h = 214.0
    new_s = np.clip(sat * 1.55 + 0.06, 0, 0.6)
    hsv2 = hsv.copy()
    hsv2[..., 0] = np.where(sel, new_h * 255 / 360, hsv[..., 0])
    hsv2[..., 1] = np.where(sel, (sat * (1 - weight) + new_s * weight) * 255, hsv[..., 1])
    out = np.asarray(Image.fromarray(hsv2.clip(0, 255).astype(np.uint8), "HSV").convert("RGB"))
    return np.where(sel[..., None], out, rgb)


def flat(rgba: np.ndarray, colour: tuple[int, int, int]) -> np.ndarray:
    a = rgba[..., 3:4].astype(np.float32) / 255
    return (rgba[..., :3] * a + np.array(colour, np.float32) * (1 - a)).clip(0, 255).astype(np.uint8)


def cmd_base(cid: str) -> None:
    cfg = load_cfg(cid)
    d = char_dir(cid)
    rgb = frames.load_rgb(d / cfg["base_source"])
    fix = cfg.get("fix")
    if fix == "bozo_text":
        rgb = fix_bozo_text(rgb)
    elif fix == "sklad_blue":
        rgb = fix_sklad_blue(rgb)
    elif fix == "ruzena_boots":
        # take the edit's feet wholesale below 0.82 of the figure height (soft 2 % transition), so no outline of
        # the old sheepskin boots survives at the edge of a change mask
        edit = frames.load_rgb(d / "pose_boots_fix.png")
        edit = np.asarray(Image.fromarray(edit).resize(rgb.shape[1::-1], Image.Resampling.LANCZOS))
        bk, ek = frames.chroma_key(rgb), frames.chroma_key(edit)
        dy, dx = frames.phase_shift(bk[..., 3].astype(np.float32), ek[..., 3].astype(np.float32))
        ek = np.roll(ek, (dy, dx), axis=(0, 1))
        x0, y0, x1, y1 = frames.alpha_bbox(bk)
        yy = (np.arange(rgb.shape[0]) - y0) / (y1 - y0)
        m = np.clip((yy - 0.80) / 0.02, 0, 1)[:, None, None]
        ab, ae = bk[..., 3:4] / 255.0, ek[..., 3:4] / 255.0
        alpha = ab * (1 - m) + ae * m
        prem = bk[..., :3] * ab * (1 - m) + ek[..., :3] * ae * m
        col = np.where(alpha > 1e-3, prem / np.maximum(alpha, 1e-3), 0)
        merged = np.dstack([col, alpha * 255]).clip(0, 255).astype(np.uint8)
        print("boots patch shift", dy, dx)
        rgb = flat(merged, key_rgb(cid))
    Image.fromarray(rgb).save(d / "base.png")
    keyed = frames.crop_to_figure(frames.chroma_key(rgb))
    frames.save_rgba(keyed, d / "keyed" / "base_3q.png")
    print(d / "base.png", frames.key_quality(keyed))


def cmd_canvas(cid: str) -> None:
    d = char_dir(cid)
    keyed = np.asarray(Image.open(d / "keyed" / "base_3q.png").convert("RGBA"))
    frames.figure_on_canvas(keyed, (1024, 1024), 0.80, 0.90, key_rgb(cid)).save(d / "video_in_3q.png")
    print(d / "video_in_3q.png")


# ----------------------------------------------------------------------------- face bands

def aligned_diff(base: np.ndarray, edit: np.ndarray) -> np.ndarray:
    if edit.shape != base.shape:
        edit = np.asarray(Image.fromarray(edit).resize(base.shape[1::-1], Image.Resampling.LANCZOS))
    bk, ek = frames.chroma_key(base), frames.chroma_key(edit)
    dy, dx = frames.phase_shift(bk[..., 3].astype(np.float32), ek[..., 3].astype(np.float32))
    edit = np.roll(edit, (dy, dx), axis=(0, 1))
    diff = np.abs(base.astype(np.float32) - edit.astype(np.float32)).mean(axis=2)
    return diff * ((bk[..., 3] > 128) | (np.roll(ek, (dy, dx), axis=(0, 1))[..., 3] > 128))


def runs(profile: np.ndarray, thr: float, gap: int) -> list[tuple[int, int, float]]:
    rows = np.flatnonzero(profile > thr)
    out: list[list[int]] = []
    for r in rows:
        if out and r - out[-1][1] <= gap:
            out[-1][1] = r
        else:
            out.append([r, r])
    return [(a, b, float(profile[a:b + 1].sum())) for a, b in out]


def cmd_bands(cid: str) -> None:
    cfg = load_cfg(cid)
    d = char_dir(cid)
    base = frames.load_rgb(d / "base.png")
    x0, y0, x1, y1 = frames.alpha_bbox(frames.chroma_key(base))
    h = y1 - y0
    head = int(cfg["head_frac"] * h)
    report = {}
    for name in ("pose_blink_nb2", "pose_talk_nb2", "pose_talk_oh_nb2"):
        p = d / f"{name}.png"
        if not p.exists():
            continue
        diff = aligned_diff(base, frames.load_rgb(p))
        prof = (diff[y0:y0 + head] > 18).sum(axis=1).astype(np.float32)
        rr = runs(prof, max(3.0, prof.max() * 0.12), max(3, h // 300))
        report[name] = [(round(a / h, 3), round(b / h, 3), int(s)) for a, b, s in rr if s > prof.sum() * 0.03]
    print(json.dumps(report, indent=1))
    # proposal: eye band = biggest blink run; mouth band = lowest talk run
    if "pose_blink_nb2" in report and report["pose_blink_nb2"]:
        a, b, _ = max(report["pose_blink_nb2"], key=lambda t: t[2])
        cfg.setdefault("proposed", {})["eye_band"] = [round(a - 0.008, 3), round(b + 0.008, 3)]
    talk = [t for k in ("pose_talk_nb2", "pose_talk_oh_nb2") for t in report.get(k, [])]
    if talk:
        a = min(t[0] for t in talk if t[0] >= max(t2[0] for t2 in talk) - 0.03)
        b = max(t[1] for t in talk)
        cfg.setdefault("proposed", {})["mouth_band"] = [round(a - 0.008, 3), round(b + 0.010, 3)]
    save_cfg(cid, cfg)
    print("proposed", cfg.get("proposed"))
    band_crop(cid)


def band_crop(cid: str) -> Path:
    """Head crops of base / edits at full resolution with the eye (blue) and mouth (red) bands drawn."""
    cfg = load_cfg(cid)
    d = char_dir(cid)
    base = frames.load_rgb(d / "base.png")
    x0, y0, x1, y1 = frames.alpha_bbox(frames.chroma_key(base))
    h = y1 - y0
    bands = {"eye": cfg.get("eye_band") or (cfg.get("proposed") or {}).get("eye_band"),
             "mouth": cfg.get("mouth_band") or (cfg.get("proposed") or {}).get("mouth_band")}
    head_cols = frames.chroma_key(base)[y0:y0 + int(0.18 * h), :, 3].any(axis=0)
    hx = np.flatnonzero(head_cols)
    box = (max(0, hx.min() - 30), y0, min(base.shape[1], hx.max() + 30), y0 + int(cfg["head_frac"] * h * 1.1))
    tiles = []
    for name in ("base", "pose_blink_nb2", "pose_talk_nb2", "pose_talk_oh_nb2"):
        p = d / f"{name}.png"
        if not p.exists():
            continue
        im = Image.open(p).convert("RGB")
        if im.size != (base.shape[1], base.shape[0]):
            im = im.resize((base.shape[1], base.shape[0]), Image.Resampling.LANCZOS)
        t = im.crop(box)
        dr = ImageDraw.Draw(t)
        for k in range(0, 40):  # ruler: a tick every 0.01 of the figure height, labels every 0.05
            yy = int(y0 + k * 0.01 * h) - box[1]
            if yy > t.height:
                break
            dr.line((0, yy, 14 if k % 5 else 30, yy), fill=(255, 255, 255), width=2)
            if k % 5 == 0:
                dr.text((34, yy - 6), f"{k / 100:.2f}", fill=(255, 255, 255))
        for label, col in (("eye", (0, 120, 255)), ("mouth", (255, 40, 40))):
            if bands[label]:
                for f in bands[label]:
                    yy = int(y0 + f * h) - box[1]
                    dr.line((0, yy, t.width, yy), fill=col, width=2)
        tiles.append(t)
    W = sum(t.width + 8 for t in tiles)
    sheet = Image.new("RGB", (W, tiles[0].height), (40, 40, 40))
    x = 0
    for t in tiles:
        sheet.paste(t, (x, 0))
        x += t.width + 8
    out = d / "review" / "bands.jpg"
    out.parent.mkdir(exist_ok=True)
    sheet.save(out, quality=90)
    print(out)
    return out


# ----------------------------------------------------------------------------- still set

def head_scale_ref(cid: str, base_rgb: np.ndarray) -> float:
    """Seated: source px height that maps to FIGURE_PX, from the head size in the standing sheet (template search)."""
    d = char_dir(cid)
    stand = frames.load_rgb(d / "sheet_npc_3q.png")
    sk = frames.chroma_key(stand)
    sx0, sy0, sx1, sy1 = frames.alpha_bbox(sk)
    sh = sy1 - sy0
    head = sk[sy0:sy0 + int(0.15 * sh)]
    cols = np.flatnonzero(head[..., 3].any(axis=0))
    tmpl = Image.fromarray(head[:, cols.min():cols.max() + 1]).convert("L")
    bk = frames.chroma_key(base_rgb)
    bx0, by0, bx1, by1 = frames.alpha_bbox(bk)
    region = Image.fromarray(flat(bk, (128, 128, 128))).convert("L").crop((bx0, by0, bx1, by0 + int(0.45 * (by1 - by0))))
    best = (-2.0, 1.0)
    reg = np.asarray(region, np.float32)
    for s in np.arange(0.80, 1.26, 0.02):
        t = np.asarray(tmpl.resize((max(4, round(tmpl.width * s)), max(4, round(tmpl.height * s)))), np.float32)
        if t.shape[0] >= reg.shape[0] or t.shape[1] >= reg.shape[1]:
            continue
        small = 4
        rs = reg[::small, ::small]
        ts = t[::small, ::small]
        tz = (ts - ts.mean()) / (ts.std() + 1e-6)
        score = -2.0
        for yy in range(0, rs.shape[0] - ts.shape[0], 2):
            for xx in range(0, rs.shape[1] - ts.shape[1], 2):
                win = rs[yy:yy + ts.shape[0], xx:xx + ts.shape[1]]
                v = float((tz * (win - win.mean()) / (win.std() + 1e-6)).mean())
                score = max(score, v)
        if score > best[0]:
            best = (score, float(s))
    print(f"head template match: scale {best[1]:.2f} (ncc {best[0]:.3f})")
    return sh * best[1]


def matched_edit(base: np.ndarray, edit: np.ndarray, band: tuple[float, float], head_frac: float) -> np.ndarray:
    """Align an NB2 face edit to the base and match its colours (per-channel gain + offset fitted on the head
    outside the band). NB2 often warms or cools the whole picture a little; without this the transplanted band
    would pop in colour on every blink / mouth frame."""
    if edit.shape != base.shape:
        edit = np.asarray(Image.fromarray(edit).resize(base.shape[1::-1], Image.Resampling.LANCZOS))
    bk, ek = frames.chroma_key(base), frames.chroma_key(edit)
    dy, dx = frames.phase_shift(bk[..., 3].astype(np.float32), ek[..., 3].astype(np.float32))
    edit = np.roll(edit, (dy, dx), axis=(0, 1))
    ek = np.roll(ek, (dy, dx), axis=(0, 1))
    x0, y0, x1, y1 = frames.alpha_bbox(bk)
    h = y1 - y0
    rows = np.zeros(base.shape[0], bool)
    rows[y0:y0 + int(head_frac * h)] = True
    rows[y0 + int((band[0] - 0.01) * h): y0 + int((band[1] + 0.01) * h)] = False
    sel = rows[:, None] & (bk[..., 3] > 250) & (ek[..., 3] > 250)
    out = edit.astype(np.float32)
    for c in range(3):
        xs, ys = out[..., c][sel], base[..., c][sel].astype(np.float32)
        a, b = np.polyfit(xs, ys, 1) if len(xs) > 500 else (1.0, 0.0)
        a = float(np.clip(a, 0.8, 1.25))
        out[..., c] = out[..., c] * a + b
    keyed = ek[..., 3] > 128
    res = np.where(keyed[..., None], out.clip(0, 255), edit.astype(np.float32)).astype(np.uint8)
    return res


def cmd_stills(cid: str) -> dict:
    cfg = load_cfg(cid)
    d = char_dir(cid)
    base = frames.load_rgb(d / "base.png")
    base_key = frames.chroma_key(base)
    bx0, by0, bx1, by1 = frames.alpha_bbox(base_key)
    eye, mouth = cfg["eye_band"], cfg["mouth_band"]
    if not eye or not mouth:
        sys.exit(f"{cid}: set eye_band and mouth_band in build.json (see `bands`)")
    layers, reports = [base_key], {}
    srcs = {"blink": "pose_blink_nb2.png", "talk_a": "pose_talk_nb2.png", "talk_b": "pose_talk_oh_nb2.png",
            "gesture": "pose_gesture_nb2.png", **cfg.get("frame_sources", {})}
    for label, band in (("blink", eye), ("talk_a", mouth), ("talk_b", mouth)):
        src = srcs[label]
        edit = matched_edit(base, frames.load_rgb(d / src), tuple(band), cfg["head_frac"])
        thr = cfg.get("patch_threshold", {}).get(label, 18.0)
        merged, rep = frames.patch_pose(base, edit, tuple(band), threshold=thr)
        rep["threshold"] = thr
        win = cfg.get("mouth_window_px") if label.startswith("talk") else None
        if win:
            # keep the transplant to a soft window around the mouth (NB2 also re-paints jaw stubble / beards,
            # which would flicker against the idle frame inside a talk sequence)
            diff = aligned_diff(base, edit)
            y_lo, y_hi = by0 + int(band[0] * (by1 - by0)), by0 + int(band[1] * (by1 - by0))
            strong = diff[y_lo:y_hi] > 60
            cols = strong.sum(axis=0).astype(np.float32)
            cx = float((cols * np.arange(len(cols))).sum() / max(1.0, cols.sum()))
            xx = np.arange(base.shape[1], dtype=np.float32)
            wx = np.clip(1.0 - (np.abs(xx - cx) - win) / (0.5 * win), 0, 1)[None, :, None]
            a_b, a_m = base_key[..., 3:4] / 255.0, merged[..., 3:4] / 255.0
            alpha = a_b * (1 - wx) + a_m * wx
            prem = base_key[..., :3] * a_b * (1 - wx) + merged[..., :3] * a_m * wx
            col = np.where(alpha > 1e-3, prem / np.maximum(alpha, 1e-3), 0)
            merged = np.dstack([col, alpha * 255]).clip(0, 255).astype(np.uint8)
            rep["mouth_window"] = [round(cx), win]
        reports[label] = rep
        layers.append(merged)
    gesture = frames.load_rgb(d / srcs["gesture"])
    if gesture.shape != base.shape:
        gesture = np.asarray(Image.fromarray(gesture).resize(base.shape[1::-1], Image.Resampling.LANCZOS))
    gk = frames.chroma_key(gesture)
    gbox = frames.alpha_bbox(gk)
    dy, dx = frames.phase_shift(base_key[..., 3].astype(np.float32), gk[..., 3].astype(np.float32))
    gk = np.roll(gk, (dy, dx), axis=(0, 1))
    reports["gesture"] = {"shift_dy_dx": [int(dy), int(dx)], "feet_line_delta_px": int(gbox[3] + dy - by1)}
    if cfg.get("gesture_band"):
        # take only the moving arm's band from the gesture edit; the rest stays the idle base (e.g. BOZO: the
        # edit re-painted the timetable hand with a lime smear)
        gk, rep = frames.patch_pose(base, np.roll(gesture, (dy, dx), axis=(0, 1)), tuple(cfg["gesture_band"]))
        reports["gesture"].update({"band": cfg["gesture_band"], "changed_px_in_region": rep["changed_px_in_region"]})
    layers.append(gk)
    if cfg["posture"] == "seated":
        ref_h = cfg.get("ref_height_src") or head_scale_ref(cid, base)
        cfg["ref_height_src"] = round(float(ref_h), 1)
        save_cfg(cid, cfg)
        head = base_key[by0:by0 + int(0.12 * (by1 - by0)), :, 3].astype(np.float32)
        cols = head.sum(axis=0)
        pivot_x = float((cols * np.arange(len(cols))).sum() / max(1.0, cols.sum()))
    else:
        ref_h = by1 - by0
        pivot_x = frames.torso_center_x(base_key)
    scale = FIGURE_PX / ref_h
    boxes = [frames.alpha_bbox(layer) for layer in layers]
    half = max(max(pivot_x - b[0] for b in boxes), max(b[2] - pivot_x for b in boxes))
    top = max(by1 - b[1] for b in boxes)
    cell_w, cell_h = 2 * int(np.ceil(half * scale)) + 8, int(np.ceil(top * scale)) + 8
    cells = []
    for layer in layers:
        img = Image.fromarray(layer, "RGBA")
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
        cell = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
        cell.paste(img, (round(cell_w / 2 - pivot_x * scale), round(cell_h - 4 - by1 * scale)), img)
        cells.append(cell)
    labels = ["idle", "blink", "talk_a", "talk_b", "gesture"]
    meta = {"name": "npc", "frames": labels, "cell": [cell_w, cell_h], "pivot": [cell_w // 2, cell_h - 4],
            "scale": round(scale, 4), "height_px": FIGURE_PX, "playback_fps": 8,
            "posture": cfg["posture"], "eye_band": eye, "mouth_band": mouth,
            "sources": ["key:base.png", "patch:" + srcs["blink"], "patch:" + srcs["talk_a"], "patch:" + srcs["talk_b"],
                        "key:" + srcs["gesture"]]}
    if cfg["posture"] == "seated":
        meta["seated_height_px"] = round((by1 - by0) * scale, 1)
        meta["height_note"] = ("height_px is the standing-equivalent figure height (scale from the head size of the "
                               "standing sheet); the seated sprite itself is seated_height_px tall")
    gif = [(0, 1600), (1, 110), (0, 900), (2, 130), (3, 130), (2, 130), (0, 130), (3, 130), (2, 130), (0, 600),
           (4, 1200), (0, 800)]
    frames.export_cells(cells, d / "npc_set", "npc", meta, labels, gif, names=labels)
    # flicker check: pixels that differ from idle outside the face bands (must be 0 for blink / talk)
    idle = np.asarray(cells[0]).astype(np.int16)
    for i, label in enumerate(labels[1:4], start=1):
        c = np.asarray(cells[i]).astype(np.int16)
        band = eye if label == "blink" else mouth
        ytop = cell_h - 4 - (by1 - by0) * scale
        lo, hi = int(ytop + band[0] * (by1 - by0) * scale) - 2, int(ytop + band[1] * (by1 - by0) * scale) + 2
        diff = np.abs(c - idle).max(axis=2) > 2
        diff[max(0, lo):hi] = False
        reports[label]["cells_differ_outside_band_px"] = int(diff.sum())
    (d / "npc_set" / "build_report.json").write_text(json.dumps(reports, indent=1), encoding="utf-8")
    print(json.dumps(reports))
    return meta


# ----------------------------------------------------------------------------- video idle

def shift_cells(cells: list[Image.Image], pivot: tuple[int, int], dx: int, dy: int, scale: float = 1.0
                ) -> tuple[list[Image.Image], tuple[int, int]]:
    """Move (and optionally scale about the pivot) cell content; the pivot stays horizontally centred."""
    cw, ch = cells[0].size
    px, py = pivot
    if abs(scale - 1.0) > 1e-3:
        out = []
        nw, nh = round(cw * scale), round(ch * scale)
        for c in cells:
            out.append(c.resize((nw, nh), Image.Resampling.LANCZOS))
        cells, cw, ch = out, nw, nh
        px, py = nw // 2, round(py * scale)
    ax, ay = abs(dx), abs(dy)
    W, H = cw + 2 * ax, ch + 2 * ay
    res = []
    for c in cells:
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.paste(c, (ax + dx, ay + dy), c)
        res.append(canvas)
    # trim empty rows at the top / bottom margin above the pivot band
    stack = np.max([np.asarray(r)[..., 3] for r in res], axis=0)
    rows = np.flatnonzero(stack.any(axis=1))
    top = int(max(0, rows.min() - 4))
    bottom = int(max(py + ay + 4, rows.max() + 2))
    res = [r.crop((0, top, W, bottom)) for r in res]
    return res, (int(px + ax), int(py + ay - top))


def cmd_idle(cid: str, video: str | None = None) -> dict:
    cfg = load_cfg(cid)
    d = char_dir(cid)
    video_path = Path(video) if video else d / "video_idle_hailuo_loop.mp4"
    out = d / "idle_hailuo"
    tmp = Path(tempfile.mkdtemp(prefix=f"idle_{cid}_"))
    try:
        info = frames.video_info(video_path)
        paths = frames.extract_frames(video_path, tmp)
        n = len(paths)
        base = frames.load_rgb(d / "base.png")
        bb = frames.alpha_bbox(frames.chroma_key(base))
        f0 = frames.alpha_bbox(frames.chroma_key(frames.load_rgb(paths[0]), choke=1))
        ref = f0[3] - f0[1]
        if cfg["posture"] == "seated":
            ref = ref * cfg["ref_height_src"] / (bb[3] - bb[1])
        meta = frames.build_loop(paths, out, info.get("fps", 24.0), IDLE_FRAMES, (1, 9), 0, 0, False, FIGURE_PX,
                                 None, None, "idle", cfg.get("video_choke", 1), (0, n - 1), False, None, ref)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    # align cell 0 to the still idle (same pivot convention, so switching to talk does not jump)
    still = Image.open(d / "npc_set" / "npc_idle.png").convert("RGBA")
    smeta = json.loads((d / "npc_set" / "npc_sheet.json").read_text(encoding="utf-8"))
    cells = [Image.open(out / f"idle_{i:02d}.png").convert("RGBA") for i in range(IDLE_FRAMES)]
    sa, va = np.asarray(still)[..., 3], np.asarray(cells[0])[..., 3]
    sbox, vbox = frames.alpha_bbox(np.asarray(still)), frames.alpha_bbox(np.asarray(cells[0]))
    height_ratio = (sbox[3] - sbox[1]) / max(1, (vbox[3] - vbox[1]))
    scale = height_ratio if abs(height_ratio - 1) > 0.012 else 1.0
    pivot = tuple(meta["pivot"])
    if scale != 1.0:
        cells, pivot = shift_cells(cells, pivot, 0, 0, scale)
        va = np.asarray(cells[0])[..., 3]
    S = 2 * max(sa.shape + va.shape)

    def on_canvas(alpha: np.ndarray, pv: tuple[int, int]) -> np.ndarray:
        c = np.zeros((S, S), np.float32)
        oy, ox = S // 2 - pv[1], S // 2 - pv[0]
        c[oy:oy + alpha.shape[0], ox:ox + alpha.shape[1]] = alpha
        return c

    dy, dx = frames.phase_shift(on_canvas(sa, tuple(smeta["pivot"])), on_canvas(va, pivot))
    cells, pivot = shift_cells(cells, pivot, dx, dy)
    meta.update({"cell": list(cells[0].size), "pivot": list(pivot), "aligned_to_still": [int(dx), int(dy)],
                 "scale_fix": round(scale, 4), "video": video_path.name, "posture": cfg["posture"]})
    for drop in ("source_frames",):
        meta.pop(drop, None)
    frames.export_cells(cells, out, "idle", meta, [str(i) for i in range(len(cells))])
    print(json.dumps({k: meta[k] for k in ("cell", "pivot", "aligned_to_still", "scale_fix", "playback_fps",
                                           "cycle_seconds")}))
    return meta


# ----------------------------------------------------------------------------- busts

def cmd_bust(cid: str) -> None:
    cfg = load_cfg(cid)
    if not cfg.get("bust"):
        print(cid, "no bust variant configured")
        return
    d = char_dir(cid)
    vis = cfg["bust"]["visible"]
    out = d / "window"
    for src, name in ((d / "npc_set" / "npc_sheet.png", "npc_bust"), (d / "idle_hailuo" / "idle_sheet.png", "idle_bust")):
        if not src.exists():
            continue
        glass.make_bust(src, out, name, vis, False, 0.16, 0.10, 1.08)
        if cfg["bust"].get("glass"):
            glass.make_bust(src, out, name + "_glass", vis, True, 0.16, 0.10, 1.08)
    print(sorted(p.name for p in out.glob("*_sheet.png")))


# ----------------------------------------------------------------------------- export

def grid(img: Image.Image, cell: tuple[int, int], count: int) -> tuple[Image.Image, int, int]:
    cw, ch = cell
    columns = max(1, min(count, MAX_SIDE // cw))
    rows = math.ceil(count / columns)
    columns = math.ceil(count / rows)
    if rows * ch > MAX_SIDE:
        raise SystemExit(f"{count} cells of {cell} do not fit {MAX_SIDE} px")
    out = Image.new("RGBA", (columns * cw, rows * ch), (0, 0, 0, 0))
    src_cols = max(1, img.width // cw)
    for i in range(count):
        sx, sy = (i % src_cols) * cw, (i // src_cols) * ch
        out.paste(img.crop((sx, sy, sx + cw, sy + ch)), ((i % columns) * cw, (i // columns) * ch))
    return out, columns, rows


SHEETS = {
    "npc": "npc_set/npc_sheet.png",
    "idle": "idle_hailuo/idle_sheet.png",
    "npc_bust": "window/npc_bust_sheet.png",
    "npc_bust_glass": "window/npc_bust_glass_sheet.png",
    "idle_bust": "window/idle_bust_sheet.png",
    "idle_bust_glass": "window/idle_bust_glass_sheet.png",
}


def cmd_export(cid: str) -> dict:
    cfg = load_cfg(cid)
    src_dir, dst_dir = char_dir(cid), GAME_ACTORS / cid
    dst_dir.mkdir(parents=True, exist_ok=True)
    sheets = {}
    for key, rel in SHEETS.items():
        src = src_dir / rel
        if not src.exists():
            continue
        meta = export_actors.sheet_json(src.with_suffix(".json"), key, f"{key}_sheet.webp")
        img = Image.open(src).convert("RGBA")
        packed, columns, rows = grid(img, tuple(meta["cell"]), meta["frames"])
        meta["columns"], meta["rows"] = columns, rows
        for drop in ("glass_params",):
            if meta.get(drop) is None:
                meta.pop(drop, None)
        dst = dst_dir / f"{key}_sheet.webp"
        packed.save(dst, "WEBP", quality=92, alpha_quality=100, method=6)
        check = Image.open(dst)
        assert check.size == packed.size and max(check.size) <= MAX_SIDE
        (dst_dir / f"{key}_sheet.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
                                                  encoding="utf-8", newline="\n")
        sheets[key] = {"file": dst.name, "json": f"{key}_sheet.json", "size": list(packed.size),
                       "cell": meta["cell"], "pivot": meta["pivot"], "frames": meta["frames"],
                       "grid": [columns, rows]}

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

    b = brief(cid)
    seated = cfg["posture"] == "seated"
    manifest = {
        "id": cid,
        "source": f"art/characters/{cid}",
        "view": "three-quarter, facing right (mirror for facing left)",
        "posture": cfg["posture"],
        "era": b.get("era"),
        "room": b.get("room"),
        "height_px": FIGURE_PX,
        "pivot": ("feet centre, 4 px above the cell bottom (seated: centre of her head above the ground line of "
                  "feet and bench legs; bust variants: centre of the cut edge)" if seated else
                  "feet centre, 4 px above the cell bottom (bust variants: centre of the cut edge)"),
        "sheets": sheets,
        "animations": anims("npc", "idle" if "idle" in sheets else None),
        "switching": ("Start talking only at a video idle loop boundary (cell 0 matches the still idle pose; aligned "
                      "to the still pivot) or cross-fade ~80 ms; video cells are slightly softer than the stills."),
        "notes": cfg.get("notes", ""),
    }
    if seated:
        npc_meta = json.loads((src_dir / "npc_set" / "npc_sheet.json").read_text(encoding="utf-8"))
        # Actor.HeadPosition = feet - height_px * scale: use the seated sprite's real height for labels / bubbles
        manifest["height_px"] = round(npc_meta["seated_height_px"])
        manifest["standing_equivalent_height_px"] = FIGURE_PX
    if "npc_bust" in sheets:
        variants = {
            "window": {"animations": anims("npc_bust", "idle_bust" if "idle_bust" in sheets else None),
                       "note": "bust cut at the sill / counter line, no glass treatment"},
        }
        if "npc_bust_glass" in sheets:
            variants["window_glass"] = {
                "animations": anims("npc_bust_glass", "idle_bust_glass" if "idle_bust_glass" in sheets else None),
                "note": "behind closed glass: bust cut at the sill line, pale veil + soft reflection"}
        for alias in cfg["bust"].get("aliases", []):
            variants[alias] = {"animations": variants["window"]["animations"],
                               "note": "same as 'window': bust standing behind a counter"}
        manifest["variants"] = variants
        manifest["default_variant"] = cfg["bust"].get("default")
        manifest["bust_visible_fraction"] = cfg["bust"]["visible"]
    (dst_dir / "actor.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
                                        newline="\n")
    print(cid, {k: (v["size"], v["frames"], v["grid"]) for k, v in sheets.items()})
    return manifest


# ----------------------------------------------------------------------------- review

def room_rect(cid: str) -> tuple[str, list[int]]:
    g = json.loads(GAME_JSON.read_text(encoding="utf-8"))
    for r in g["rooms"]:
        for hs in r.get("hotspots", []):
            if hs.get("character_id") == cid:
                return r["id"], hs["rect"]
    raise SystemExit(f"{cid}: no NPC hotspot")


def cmd_review(cid: str) -> None:
    cfg = load_cfg(cid)
    d = char_dir(cid)
    rv = d / "review"
    rv.mkdir(exist_ok=True)
    meta = json.loads((d / "npc_set" / "npc_sheet.json").read_text(encoding="utf-8"))
    labels = meta["frames"]
    cells = [Image.open(d / "npc_set" / f"npc_{n}.png").convert("RGBA") for n in labels]
    # 1. head crops x2 (expression stability between idle / blink / talk)
    a = np.asarray(cells[0])[..., 3]
    ys = np.flatnonzero(a.any(axis=1))
    top = ys.min()
    hh = int(FIGURE_PX * (0.22 if cfg["posture"] == "standing" else 0.24))
    cols = np.flatnonzero(a[top:top + hh].any(axis=0))
    box = (max(0, cols.min() - 10), max(0, top - 6), min(a.shape[1], cols.max() + 10), top + hh)
    heads = []
    for c in cells[:4]:
        t = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), (150, 160, 150, 255))
        t.alpha_composite(c.crop(box))
        heads.append(t.resize((t.width * 2, t.height * 2), Image.Resampling.LANCZOS))
    W = sum(h.width + 6 for h in heads)
    sheet = Image.new("RGB", (W, heads[0].height + 20), (40, 40, 40))
    x = 0
    for lab, h in zip(labels, heads):
        sheet.paste(h.convert("RGB"), (x, 20))
        ImageDraw.Draw(sheet).text((x + 4, 4), lab, fill=(255, 255, 255))
        x += h.width + 6
    sheet.save(rv / "heads.jpg", quality=90)
    # 2. idle strip: 8 cells of the video idle next to the still idle
    idle_dir = d / "idle_hailuo"
    if (idle_dir / "idle_00.png").exists():
        picks = [0, 4, 9, 13, 18, 22, 27, 31]
        ims = [cells[0]] + [Image.open(idle_dir / f"idle_{i:02d}.png").convert("RGBA") for i in picks]
        frames.contact_sheet(ims, rv / "idle_strip.jpg", cell_h=420, labels=["still idle"] + [f"video {i}" for i in picks])
    # 3. staging mock: sprite at the NPC rect (feet = rect bottom centre, scale 0.80) next to Adam
    room, rect = room_rect(cid)
    W, H = 1920, 1080
    bg = Image.open(ART / "backgrounds" / "tram-stop.png").convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    stage = bg.convert("RGBA")
    dr = ImageDraw.Draw(stage)
    dr.rectangle((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]), outline=(255, 220, 0), width=3)
    dr.rectangle((90, 790, 1830, 1015), outline=(0, 200, 255), width=2)
    fx, fy = rect[0] + rect[2] / 2, rect[1] + rect[3]

    def put(img: Image.Image, pivot: tuple[int, int], x: float, y: float, s: float, flip: bool = False) -> None:
        im = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else img
        im = im.resize((round(im.width * s), round(im.height * s)), Image.Resampling.LANCZOS)
        px = (img.width - pivot[0]) if flip else pivot[0]
        stage.alpha_composite(im, (round(x - px * s), round(y - pivot[1] * s)))

    adam = Image.open(ART / "characters" / "ADAM" / "keyed" / "side_right_3q.png").convert("RGBA")
    adam_s = FIGURE_PX / adam.height
    adam = adam.resize((round(adam.width * adam_s), FIGURE_PX), Image.Resampling.LANCZOS)
    ay = 880
    put(adam, (adam.width // 2, adam.height), rect[0] + rect[2] + 95 + 40, ay, 0.8 + 0.2 * (ay - 790) / 225, flip=True)
    put(cells[0], tuple(meta["pivot"]), fx, fy, 0.80)
    bust = d / "window" / "npc_bust_sheet.json"
    if bust.exists():
        bm = json.loads(bust.read_text(encoding="utf-8"))
        bimg = Image.open(d / "window" / "npc_bust_sheet.png").convert("RGBA").crop((0, 0, *bm["cell"]))
        sill = fy - (1 - bm["visible_fraction_of_figure"]) * FIGURE_PX * 0.80
        bx = 1300
        dr.rectangle((bx - 170, sill, bx + 170, fy + 40), fill=(150, 110, 80, 255), outline=(90, 60, 40), width=4)
        put(bimg, tuple(bm["pivot"]), bx, sill, 0.80)
        dr.text((bx - 160, fy + 50), f"bust variant, sill_y = {sill:.0f} (counter / window top)", fill=(255, 255, 255))
    dr.text((rect[0], rect[1] - 20), f"{room} {cid} rect {rect} (feet at rect bottom, scale 0.80)", fill=(255, 255, 0))
    stage.convert("RGB").save(rv / "staging.jpg", quality=88)
    print(rv / "heads.jpg", rv / "idle_strip.jpg", rv / "staging.jpg")


# ----------------------------------------------------------------------------- CLI

def cmd_init(cid: str) -> None:
    cfg = load_cfg(cid)
    save_cfg(cid, cfg)
    print(cid, cfg)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cmd", choices=["init", "base", "canvas", "bands", "stills", "idle", "bust", "export",
                                        "review", "all"])
    parser.add_argument("ids", nargs="+")
    parser.add_argument("--video")
    args = parser.parse_args()
    for cid in args.ids:
        if args.cmd == "all":
            cmd_stills(cid)
            if (char_dir(cid) / "video_idle_hailuo_loop.mp4").exists():
                cmd_idle(cid)
            cmd_bust(cid)
            cmd_export(cid)
            cmd_review(cid)
        elif args.cmd == "idle":
            cmd_idle(cid, args.video)
        else:
            globals()[f"cmd_{args.cmd}"](cid)


if __name__ == "__main__":
    main()
