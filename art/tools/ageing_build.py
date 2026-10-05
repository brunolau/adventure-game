"""Local (free) build of the ageing-cast sprite sets (see ageing_cast.py for the paid steps).

Per character, inputs in art/characters/<ID>/ (raw outputs of ageing_cast.py):
  sheet_3q.png            Pro base sheet (the idle pose)
  edit_blink.png          NB2 1K blink edit            -> eye band transplanted onto the base
  edit_talk.png           NB2 1K 'ah' mouth edit       -> mouth band transplanted (eyes and brows stay the base's)
  edit_talk_oh.png        NB2 1K 'oh' mouth edit       -> idem
  edit_gesture.png        NB2 2K gesture key pose      -> keyed whole, aligned to the base by the lower body
  video_idle*.mp4         Hailuo idle loop (start = end) made from video_in.png (canvas transform in video_in.json)
  build.json              optional overrides: face boxes, target height, pivot, bust line, video, colour match ...
Optional prop variants (Q9C): edit_variant_q9c.png (+ edit_variant_q9c_gesture.png): the changed body region is
transplanted onto every still, so face frames stay pixel-identical; the variant idle is a breathing loop with a blink.

Commands (run from art/tools):
  canvas <ID>      write video_in.png (+ json) for the Hailuo idle (upper body for window busts)
  faces <ID>       detect eye / mouth boxes from the edits, write faces_debug.jpg (check it, override in build.json)
  build <ID>       stills, video idle, busts, variants -> art/characters/<ID>/sheets/ (PNG grids + JSON, GIF, contact)
  export <ID>      WebP grids + JSON + actor.json -> src/game/assets/actors/<ID>/
  likeness <PERSON> contact sheet of the shipped sprites (real relative size) + enlarged heads
"""
from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import ageing_cast as ac
import frames as fr
import glass

CHAR_ROOT = ac.CHAR_ROOT
GAME_ACTORS = ac.GAME_ACTORS
MAX_TEX = 4096
STILL_NAMES = ["idle", "blink", "talk_a", "talk_b", "gesture"]
DEFAULT_HEIGHT = 512
BG_PREVIEW = ac.REPO / "src" / "game" / "assets" / "bg" / "S01.webp"


# ----------------------------------------------------------------------------- small helpers

def cdir(char: str) -> Path:
    return CHAR_ROOT / char


def config(char: str) -> dict:
    path = cdir(char) / "build.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_config(char: str, data: dict) -> None:
    (cdir(char) / "build.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def load_raw(path: Path, size: tuple[int, int] | None = None) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    if size and img.size != size:
        img = img.resize(size, Image.Resampling.LANCZOS)
    return np.asarray(img)


def premul(rgba: np.ndarray) -> np.ndarray:
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255
    return np.concatenate([f[..., :3] * a, a * 255], axis=2)


def unpremul(p: np.ndarray) -> np.ndarray:
    a = p[..., 3:4] / 255
    with np.errstate(divide="ignore", invalid="ignore"):
        rgb = np.where(a > 1e-4, p[..., :3] / np.maximum(a, 1e-4), 0)
    return np.dstack([rgb, p[..., 3]]).clip(0, 255).astype(np.uint8)


def blend(under: np.ndarray, over: np.ndarray, weight: np.ndarray) -> np.ndarray:
    w = weight[..., None].astype(np.float32)
    return unpremul(premul(under) * (1 - w) + premul(over) * w)


def phase_shift_band(a: np.ndarray, b: np.ndarray, rows: tuple[int, int]) -> tuple[int, int]:
    """(dy, dx) aligning b onto a, using only the given row band of both alpha maps."""
    ma = np.zeros_like(a, dtype=np.float32)
    mb = np.zeros_like(b, dtype=np.float32)
    ma[rows[0]:rows[1]] = a[rows[0]:rows[1]]
    mb[rows[0]:rows[1]] = b[rows[0]:rows[1]]
    return fr.phase_shift(ma, mb)


def shift(arr: np.ndarray, dy: int, dx: int) -> np.ndarray:
    out = np.zeros_like(arr)
    h, w = arr.shape[:2]
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = arr[ys, xs]
    return out


def bbox(rgba: np.ndarray) -> tuple[int, int, int, int]:
    return fr.alpha_bbox(rgba)


def components(mask: np.ndarray, min_share: float = 0.08) -> np.ndarray:
    labels, sizes = fr.label_components(mask)
    if len(sizes) == 0:
        return mask
    keep = np.flatnonzero(sizes >= sizes.max() * min_share) + 1
    return np.isin(labels, keep)


# ----------------------------------------------------------------------------- base geometry

class Base:
    """The keyed base sheet and its sprite geometry (pivot, figure height, target scale)."""

    def __init__(self, char: str):
        self.char = char
        self.brief = ac.BRIEFS[char]
        self.cfg = config(char)
        name = self.cfg.get("base", "portrait.png" if self.brief["staging"] == "screen" else "sheet_3q.png")
        self.path = cdir(char) / name
        self.rgb = load_raw(self.path)
        self.size = (self.rgb.shape[1], self.rgb.shape[0])
        self.key = drop_specks(fr.chroma_key(self.rgb))
        x0, y0, x1, y1 = bbox(self.key)
        self.box = (x0, y0, x1, y1)
        self.fig_h = y1 - y0
        px = self.cfg.get("pivot_x")
        self.pivot = (float(px) if px is not None else float(fr.torso_center_x(self.key)), float(y1))
        target = self.cfg.get("target_height", DEFAULT_HEIGHT)
        self.target_h = float(target)
        self.scale = self.target_h / self.fig_h

    def frac_row(self, f: float) -> int:
        return int(self.box[1] + f * self.fig_h)


def drop_specks(rgba: np.ndarray, min_share: float = 0.003) -> np.ndarray:
    """Remove small detached islands (stray paint specks the editors leave on the key background)."""
    labels, sizes = fr.label_components(rgba[..., 3] > 24)
    if len(sizes) <= 1:
        return rgba
    small = np.flatnonzero(sizes < sizes.max() * min_share) + 1
    out = rgba.copy()
    out[np.isin(labels, small), 3] = 0
    return out


def aligned_edit(base: Base, path: Path, band: tuple[float, float] | None = None) -> tuple[np.ndarray, np.ndarray, dict]:
    """Load an edit at base size, key it and align it to the base (by a row band of the figure)."""
    rgb = load_raw(path, base.size)
    key = drop_specks(fr.chroma_key(rgb))
    if band is None:
        band = tuple(base.cfg.get("align_band", [0.62, 1.0]))
    rows = (base.frac_row(band[0]), min(base.size[1], base.frac_row(band[1]) + 4))
    dy, dx = phase_shift_band(base.key[..., 3].astype(np.float32), key[..., 3].astype(np.float32), rows)
    rgb, key = shift(rgb, dy, dx), shift(key, dy, dx)
    eb = bbox(key)
    report = {"shift_dy_dx": [int(dy), int(dx)], "bottom_delta": int(eb[3] - base.box[3]),
              "height_ratio": round((eb[3] - eb[1]) / base.fig_h, 4)}
    return rgb, key, report


# ----------------------------------------------------------------------------- face boxes and transplants

def soft(rgb: np.ndarray, radius: float = 2.5) -> np.ndarray:
    return np.asarray(Image.fromarray(rgb).filter(ImageFilter.GaussianBlur(radius)), np.float32)


def changed(base: Base, rgb: np.ndarray, key: np.ndarray, thr: float) -> np.ndarray:
    """Pixels the edit really changed: blurred difference (the 1K edits are softer and a pixel off at edges)."""
    if not hasattr(base, "_soft"):
        base._soft = soft(base.rgb)
    diff = np.abs(base._soft - soft(rgb)).mean(axis=2)
    fig = (base.key[..., 3] > 128) | (key[..., 3] > 128)
    m = (diff > thr) & fig
    img = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    return np.asarray(img) > 0


def head_band(base: Base) -> tuple[int, int]:
    default = {"screen": [0.0, 0.75], "seated": [0.0, 0.32]}.get(base.brief["staging"], [0.0, 0.2])
    if base.brief.get("child") and base.brief["staging"] != "seated":
        default = [0.0, 0.22]
    lo, hi = base.cfg.get("head_band", default)
    return base.frac_row(lo), base.frac_row(hi)


def auto_faces(base: Base) -> dict:
    """Eye box from the blink edit, mouth box from the 'ah' edit (blurred differences, head band only)."""
    top, bottom = head_band(base)
    blink_rgb, blink_key, _ = aligned_edit(base, cdir(base.char) / "edit_blink.png", band=(0.0, 1.0))
    m = changed(base, blink_rgb, blink_key, 40)
    m[:top] = False
    m[bottom:] = False
    m = components(m, 0.2)
    ys, xs = np.nonzero(m)
    if len(ys) == 0:
        raise SystemExit(f"{base.char}: no blink change found in the head band")
    ex0, ey0, ex1, ey1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    ew = max(20, ex1 - ex0)
    eye = [ex0 - int(0.12 * ew), ey0 - int(0.22 * ew), ex1 + int(0.12 * ew), ey1 + int(0.14 * ew)]
    mouth = None
    talk = cdir(base.char) / "edit_talk.png"
    if talk.exists():
        t_rgb, t_key, _ = aligned_edit(base, talk, band=(0.0, 1.0))
        mt = changed(base, t_rgb, t_key, 40)
        lo, hi = ey1 + int(0.25 * ew), ey1 + int(1.25 * ew)
        mt[:lo] = False
        mt[hi:] = False
        mt[:, :max(0, ex0 - int(0.4 * ew))] = False
        mt[:, ex1 + int(0.4 * ew):] = False
        mt = components(mt, 0.15)
        ys, xs = np.nonzero(mt)
        if len(ys):
            mx0, my0, mx1, my1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            mw = max(20, mx1 - mx0)
            mouth = [mx0 - int(0.25 * mw), my0 - int(0.2 * mw), mx1 + int(0.25 * mw), my1 + int(0.25 * mw)]
    return {"eye_box": eye, "mouth_box": mouth}


def transplant(base: Base, under: np.ndarray, rgb: np.ndarray, key: np.ndarray, box: list[int], thr: float = 12,
               feather: int = 6) -> np.ndarray:
    """Blend the changed pixels of an aligned edit inside a box onto `under` (keyed RGBA)."""
    m = changed(base, rgb, key, thr)
    win = np.zeros(m.shape, bool)
    x0, y0, x1, y1 = [int(v) for v in box]
    win[max(0, y0):y1, max(0, x0):x1] = True
    m &= win
    img = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * feather + 1))
    img = img.filter(ImageFilter.GaussianBlur(feather))
    w = np.asarray(img, np.float32) / 255
    soft = np.asarray(Image.fromarray((win * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(feather)),
                      np.float32) / 255
    w = np.minimum(w, soft)
    return blend(under, key, w)


def faces_debug(base: Base, faces: dict, out: Path) -> None:
    eb, mb = faces["eye_box"], faces.get("mouth_box") or faces["eye_box"]
    cx = (eb[0] + eb[2]) // 2
    w = int(2.4 * (eb[2] - eb[0]))
    y0 = eb[1] - int(0.8 * (eb[2] - eb[0]))
    crop = (cx - w // 2, y0, cx + w // 2, y0 + w)

    def tile(rgba: np.ndarray, boxes: bool = False) -> Image.Image:
        t = Image.fromarray(rgba).crop(crop)
        bg = Image.new("RGBA", t.size, (90, 90, 90, 255))
        bg.alpha_composite(t)
        if boxes:
            d = ImageDraw.Draw(bg)
            for b, col in ((eb, (255, 60, 60, 255)), (faces.get("mouth_box"), (60, 160, 255, 255))):
                if b:
                    d.rectangle((b[0] - crop[0], b[1] - crop[1], b[2] - crop[0], b[3] - crop[1]), outline=col, width=2)
        return bg.convert("RGB").resize((400, 400), Image.Resampling.LANCZOS)

    tiles = [tile(base.key, True)]
    for kind in ("blink", "talk", "talk_oh"):
        p = cdir(base.char) / f"edit_{kind}.png"
        box = faces["eye_box"] if kind == "blink" else faces.get("mouth_box")
        if p.exists() and box:
            rgb, key, _ = aligned_edit(base, p, band=(0.0, 1.0))
            tiles.append(tile(transplant(base, base.key, rgb, key, box)))
    sheet = Image.new("RGB", (410 * len(tiles), 400), (30, 30, 30))
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * 410, 0))
    sheet.save(out, quality=90)


# ----------------------------------------------------------------------------- cells, grids, previews

def cell_geometry(frames_src: list[np.ndarray], base: Base, margin: int = 6) -> tuple[int, int]:
    s = base.scale
    px, py = base.pivot
    half, top, below = 0.0, 0.0, 0.0
    for rgba in frames_src:
        x0, y0, x1, y1 = bbox(rgba)
        half = max(half, (px - x0) * s, (x1 - px) * s)
        top = max(top, (py - y0) * s)
        below = max(below, (y1 - py) * s)
    return 2 * int(math.ceil(half + margin)), int(math.ceil(top + margin + 4 + below))


def to_cell(rgba: np.ndarray, scale: float, pivot_src: tuple[float, float], cell: tuple[int, int],
            pivot_cell: tuple[float, float]) -> Image.Image:
    img = Image.fromarray(rgba, "RGBA")
    # crop to content first (fast resize)
    x0, y0, x1, y1 = bbox(rgba)
    x0, y0 = max(0, x0 - 4), max(0, y0 - 4)
    x1, y1 = min(rgba.shape[1], x1 + 4), min(rgba.shape[0], y1 + 4)
    img = img.crop((x0, y0, x1, y1))
    img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", cell, (0, 0, 0, 0))
    out.alpha_composite(img, (round(pivot_cell[0] - (pivot_src[0] - x0) * scale),
                              round(pivot_cell[1] - (pivot_src[1] - y0) * scale)))
    return out


def grid(cells: list[Image.Image]) -> tuple[Image.Image, int, int]:
    cw, ch = cells[0].size
    cols = max(1, min(len(cells), MAX_TEX // cw))
    rows = math.ceil(len(cells) / cols)
    if rows * ch > MAX_TEX:
        raise SystemExit(f"grid {cols}x{rows} of {cw}x{ch} exceeds {MAX_TEX} px")
    sheet = Image.new("RGBA", (cols * cw, rows * ch), (0, 0, 0, 0))
    for i, c in enumerate(cells):
        sheet.paste(c, ((i % cols) * cw, (i // cols) * ch))
    return sheet, cols, rows


def preview_bg(size: tuple[int, int]) -> Image.Image:
    bg = Image.open(BG_PREVIEW).convert("RGB")
    bw, bh = bg.size
    box_w = int(bh * 0.6 * size[0] / size[1])
    box = (int(bw * 0.42), int(bh * 0.3), int(bw * 0.42) + box_w, int(bh * 0.9))
    return bg.crop(box).resize(size, Image.Resampling.LANCZOS)


def write_sheet(out_dir: Path, name: str, cells: list[Image.Image], meta: dict,
                gif_sequence: list[tuple[int, int]] | None = None, labels: list[str] | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet, cols, rows = grid(cells)
    sheet.save(out_dir / f"{name}_sheet.png", optimize=True)
    cw, ch = cells[0].size
    meta = dict(meta, name=name, frames=len(cells), cell=[cw, ch], columns=cols, rows=rows,
                file=f"{name}_sheet.png")
    (out_dir / f"{name}_sheet.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
                                                 encoding="utf-8", newline="\n")
    seq = gif_sequence or [(i, round(1000 / meta.get("playback_fps", 8))) for i in range(len(cells))]
    bg = preview_bg((cw, ch))
    gif = []
    for i, _ms in seq:
        f = bg.copy().convert("RGBA")
        f.alpha_composite(cells[i])
        gif.append(f.convert("RGB").quantize(colors=255, method=Image.Quantize.MEDIANCUT))
    gif[0].save(out_dir / f"{name}_preview.gif", save_all=True, append_images=gif[1:],
                duration=[ms for _, ms in seq], loop=0, disposal=2)
    fr.contact_sheet(cells[:24], out_dir / f"{name}_contact.jpg", cell_h=min(ch, 420),
                     labels=labels[:24] if labels else [str(i) for i in range(min(24, len(cells)))])
    return meta


# ----------------------------------------------------------------------------- breathing (variant idles)

def warp_rows(rgba: np.ndarray, src_y: np.ndarray) -> np.ndarray:
    h = rgba.shape[0]
    pre = premul(rgba)
    y0 = np.clip(np.floor(src_y).astype(int), 0, h - 1)
    y1 = np.clip(y0 + 1, 0, h - 1)
    t = (src_y - np.floor(src_y))[:, None, None]
    return unpremul(pre[y0] * (1 - t) + pre[y1] * t)


def breathe(rgba: np.ndarray, amount: float, chest: float, hips: float) -> np.ndarray:
    """Lift everything above the hips by `amount` px (full above the chest line, fading to 0 at the hips)."""
    if amount == 0:
        return rgba
    x0, y0, x1, y1 = bbox(rgba)
    ys = (np.arange(rgba.shape[0], dtype=np.float32) - y0) / (y1 - y0)
    t = np.clip((ys - chest) / (hips - chest), 0, 1)
    s = 1 - t * t * (3 - 2 * t)
    warped = warp_rows(rgba, np.arange(rgba.shape[0], dtype=np.float32) + amount * s)
    return np.where((amount * s > 1e-6)[:, None, None], warped, rgba)


# ----------------------------------------------------------------------------- video

def ffmpeg_frames(video: Path) -> list[Path]:
    tmp = Path(tempfile.gettempdir()) / "lastbell_ageing" / video.parent.name / video.stem
    if tmp.exists():
        shutil.rmtree(tmp)
    return fr.extract_frames(video, tmp)


def canvas_for_video(base: Base) -> None:
    """video_in.png: the base on a square key canvas; window busts are framed on the upper body (sharper bust)."""
    cfgv = base.cfg.get("video_canvas", {})
    size = cfgv.get("size", 1024)
    if base.brief["staging"] == "screen":
        img = Image.fromarray(base.rgb)
        w, h = img.size
        out_w = size if w >= h else round(size * w / h)
        scale = out_w / w
        img = img.resize((out_w, round(h * scale)), Image.Resampling.LANCZOS)
        img.save(cdir(base.char) / "video_in.png")
        meta = {"canvas": list(img.size), "scale": scale, "offset": [0, 0]}
    else:
        x0, y0, x1, y1 = base.box
        if base.brief["staging"] in ("window", "window_glass"):
            show = cfgv.get("show_fraction", 0.62)  # head to hips fills the frame, cut at the bottom edge
            fit_h = base.fig_h * show
            scale = size * 0.94 / fit_h
            oy = size * 0.06 - y0 * scale
        else:
            scale = size * cfgv.get("height", 0.80) / base.fig_h
            oy = size * cfgv.get("feet", 0.90) - y1 * scale
        ox = size / 2 - base.pivot[0] * scale
        img = Image.fromarray(base.key, "RGBA").resize((round(base.size[0] * scale), round(base.size[1] * scale)),
                                                        Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (size, size), (0, 255, 0))
        canvas.paste(img, (round(ox), round(oy)), img)
        canvas.save(cdir(base.char) / "video_in.png")
        meta = {"canvas": [size, size], "scale": scale, "offset": [round(ox), round(oy)]}
    (cdir(base.char) / "video_in.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(cdir(base.char) / "video_in.png", meta)


def video_src_frames(base: Base, video: Path, count: int) -> tuple[list[np.ndarray], dict]:
    """Key `count` evenly spaced frames of a start=end idle clip and map them back into base pixel space."""
    meta = json.loads((cdir(base.char) / "video_in.json").read_text(encoding="utf-8"))
    paths = ffmpeg_frames(video)
    first = Image.open(paths[0])
    k = first.width / meta["canvas"][0]
    n = len(paths) - 1  # the last frame equals the first one (start = end)
    picks = [round(i * n / count) for i in range(count)]
    s_c, (ox, oy) = meta["scale"], meta["offset"]
    out = []
    for i in picks:
        rgb = np.asarray(Image.open(paths[i]).convert("RGB"))
        key = fr.chroma_key(rgb, choke=1)
        key = fr.edge_despill(key)
        # video px -> base px: base = (v / k - offset) / s_c
        f = 1 / (k * s_c)
        img = Image.fromarray(key, "RGBA").resize((round(key.shape[1] * f), round(key.shape[0] * f)),
                                                    Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", base.size, (0, 0, 0, 0))
        canvas.paste(img, (round(-ox / s_c), round(-oy / s_c)), img)
        out.append(np.asarray(canvas))
    return out, {"source_frames": picks, "video_frames": len(paths), "video_size": [first.width, first.height]}


def match_to_still(frames_src: list[np.ndarray], still: np.ndarray, rows: tuple[int, int]) -> tuple[list, dict]:
    """Global shift (head-band phase correlation of frame 0) + per-channel gain so video frame 0 meets the still."""
    f0 = frames_src[0]
    dy, dx = phase_shift_band(still[..., 3].astype(np.float32), f0[..., 3].astype(np.float32), rows)
    shifted = [shift(f, dy, dx) for f in frames_src]
    a = (still[..., 3] > 200) & (shifted[0][..., 3] > 200)
    gain = []
    for c in range(3):
        ms = still[..., c][a].astype(np.float32).mean()
        mv = shifted[0][..., c][a].astype(np.float32).mean()
        gain.append(float(np.clip(ms / max(mv, 1), 0.85, 1.15)))
    out = []
    for f in shifted:
        g = f.astype(np.float32)
        g[..., :3] *= np.array(gain, np.float32)
        out.append(g.clip(0, 255).astype(np.uint8))
    diff = np.abs(out[0].astype(np.float32) - still.astype(np.float32))[a].mean() if a.any() else None
    return out, {"shift_dy_dx": [int(dy), int(dx)], "gain_rgb": [round(v, 3) for v in gain],
                 "frame0_mean_abs_diff": round(float(diff), 2) if diff is not None else None}


def sharpen(img: Image.Image, amount: int) -> Image.Image:
    if amount <= 0:
        return img
    rgb = img.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.2, percent=amount, threshold=2))
    out = rgb.convert("RGBA")
    out.putalpha(img.getchannel("A"))
    return out


# ----------------------------------------------------------------------------- busts

def bust_cells(cells: list[Image.Image], pivot: tuple[int, int], height: float, visible: float,
               glass_on: bool) -> tuple[list[Image.Image], tuple[int, int]]:
    sill = int(round(pivot[1] - height * (1 - visible)))
    tops = [c.getchannel("A").getbbox()[1] for c in cells if c.getchannel("A").getbbox()]
    top = max(0, min(tops) - 4)
    out = []
    for c in cells:
        arr = np.asarray(c).copy()
        arr = arr[top:sill]
        if glass_on:
            arr = glass.treat(arr, 0.16, 0.10, 1.08)
        out.append(Image.fromarray(arr, "RGBA"))
    return out, (pivot[0], sill - top)


# ----------------------------------------------------------------------------- build

def build_stills(base: Base, faces: dict) -> tuple[dict[str, np.ndarray], dict]:
    report = {}
    frames_src = {"idle": base.key}
    d = cdir(base.char)
    rgb, key, rep = aligned_edit(base, d / "edit_blink.png", band=(0.0, 1.0))
    frames_src["blink"] = transplant(base, base.key, rgb, key, faces["eye_box"])
    report["blink"] = rep
    for label, name in (("talk_a", "edit_talk.png"), ("talk_b", "edit_talk_oh.png")):
        rgb, key, rep = aligned_edit(base, d / name, band=(0.0, 1.0))
        frames_src[label] = transplant(base, base.key, rgb, key, faces["mouth_box"])
        report[label] = rep
    rgb, key, rep = aligned_edit(base, d / "edit_gesture.png")
    frames_src["gesture"] = key
    report["gesture"] = rep
    return frames_src, report


def variant_frames(base: Base, stills: dict[str, np.ndarray], faces: dict) -> tuple[dict[str, np.ndarray], dict] | None:
    d = cdir(base.char)
    vpath = d / "edit_variant_q9c.png"
    if not vpath.exists():
        return None
    rgb, key, rep = aligned_edit(base, vpath)
    # body region = everything below the face (the face frames stay the base's)
    top = int(faces["mouth_box"][3]) + 6 if faces.get("mouth_box") else base.frac_row(0.2)
    m = changed(base, rgb, key, 14)
    m[:top] = False
    m = components(m, 0.05)
    img = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(5))
    w = np.asarray(img, np.float32) / 255
    w[:top] = 0
    out = {name: blend(arr, key, w) for name, arr in stills.items() if name != "gesture"}
    g = d / "edit_variant_q9c_gesture.png"
    if g.exists():
        _rgb, gkey, grep_ = aligned_edit(base, g)
        out["gesture"] = gkey
        rep["gesture"] = grep_
    else:
        out["gesture"] = stills["gesture"]
    return out, rep


def build(char: str) -> None:
    base = Base(char)
    cfg = base.cfg
    faces = cfg.get("faces") or auto_faces(base)
    hs = cfg.get("head_scale")
    if hs:  # seated figures: scale so the head matches the standing figure of the lineup (top-to-eye distance)
        eye_y = (faces["eye_box"][1] + faces["eye_box"][3]) / 2
        base.scale = hs["frac"] * hs["standing"] / (eye_y - base.box[1])
        base.target_h = base.fig_h * base.scale
    out_dir = cdir(char) / "sheets"
    out_dir.mkdir(parents=True, exist_ok=True)
    stills, report = build_stills(base, faces)
    var = variant_frames(base, stills, faces)
    all_src = list(stills.values()) + (list(var[0].values()) if var else [])

    staging = base.brief["staging"]
    if staging == "screen":
        return build_screen(base, stills, var, faces, report)

    cell = cell_geometry(all_src, base)
    pivot_cell = (cell[0] // 2, cell[1] - 4 - math.ceil(max((bbox(f)[3] - base.pivot[1]) * base.scale
                                                              for f in all_src)))
    sharp = cfg.get("still_sharpen", 0)
    still_cells = [sharpen(to_cell(stills[n], base.scale, base.pivot, cell, pivot_cell), sharp) for n in STILL_NAMES]
    common = {"pivot": list(pivot_cell), "scale": round(base.scale, 4), "height_px": round(base.target_h, 1),
              "playback_fps": 8, "oneshot": False, "stride_px_per_s": None, "pivot_is_sill_line": False}
    seq = [(0, 900), (1, 110), (0, 600), (2, 125), (3, 125), (2, 125), (0, 125), (3, 125), (2, 125), (0, 500),
           (4, 1200)]
    sheets = {"npc": write_sheet(out_dir, "npc", still_cells, dict(common, frame_names=STILL_NAMES), seq,
                                 STILL_NAMES)}
    if var:
        vcells = [sharpen(to_cell(var[0][n], base.scale, base.pivot, cell, pivot_cell), sharp) for n in STILL_NAMES]
        sheets["npc_q9c"] = write_sheet(out_dir, "npc_q9c", vcells, dict(common, frame_names=STILL_NAMES), seq,
                                        STILL_NAMES)
        # breathing idle with one blink (no video for the variant)
        n, blink_at = 24, 10
        amount = 0.0035 * base.fig_h
        bframes = []
        for i in range(n):
            src = var[0]["blink"] if i == blink_at else var[0]["idle"]
            bframes.append(breathe(src, amount * (0.5 - 0.5 * math.cos(2 * math.pi * i / n)), 0.30, 0.55))
        bcells = [sharpen(to_cell(f, base.scale, base.pivot, cell, pivot_cell), sharp) for f in bframes]
        sheets["idle_q9c"] = write_sheet(out_dir, "idle_q9c", bcells,
                                         dict(common, playback_fps=6, blink_frames=[blink_at],
                                              note="procedural breathing warp + blink (edit-based, no video)"))

    video = cdir(char) / cfg.get("video", "video_idle_pro.mp4")
    if not video.exists():
        video = cdir(char) / "video_idle.mp4"
    idle_cells = None
    if video.exists():
        count = cfg.get("idle_frames", 48)
        vsrc, vrep = video_src_frames(base, video, count)
        top, bottom = head_band(base)
        vsrc, mrep = match_to_still(vsrc, base.key, (top, base.frac_row(0.5)))
        vrep.update(mrep)
        vsharp = cfg.get("video_sharpen", 60)
        vcell = cell_geometry(vsrc + [base.key], base)
        vpivot = (vcell[0] // 2, vcell[1] - 4 - math.ceil(max(0.0, max((bbox(f)[3] - base.pivot[1]) * base.scale
                                                                         for f in vsrc + [base.key]))))
        if staging in ("window", "window_glass"):
            vcell, vpivot = cell, pivot_cell  # busts are cut later; keep the still geometry
        idle_cells = [sharpen(to_cell(f, base.scale, base.pivot, vcell, vpivot), vsharp) for f in vsrc]
        fps = round(count / 6.0 * cfg.get("idle_speed", 1.0), 2)
        idle_meta = dict(common, pivot=list(vpivot), playback_fps=fps, loop=True, source=video.name, **vrep)
        if staging in ("window", "window_glass"):
            for old in out_dir.glob("idle_sheet.*"):
                old.unlink()
            sheets["idle"] = dict(idle_meta, cell=list(vcell), columns=0, rows=0, frames=len(idle_cells))
        else:
            sheets["idle"] = write_sheet(out_dir, "idle", idle_cells, idle_meta)
        report["video"] = vrep
    if staging in ("window", "window_glass"):
        visible = cfg.get("bust_visible", 0.45)
        for glass_on, suffix in ((False, "bust"), (True, "bust_glass")):
            bc, bp = bust_cells(still_cells, pivot_cell, base.target_h, visible, glass_on)
            meta = dict(common, pivot=list(bp), pivot_is_sill_line=True, visible_fraction_of_figure=visible,
                        figure_height_px=base.target_h, frame_names=STILL_NAMES, glass=glass_on)
            sheets[f"npc_{suffix}"] = write_sheet(out_dir, f"npc_{suffix}", bc, meta, seq, STILL_NAMES)
            if idle_cells:
                ic, ip = bust_cells(idle_cells, pivot_cell, base.target_h, visible, glass_on)
                meta = dict(sheets["idle"], pivot=list(ip), pivot_is_sill_line=True,
                            visible_fraction_of_figure=visible, figure_height_px=base.target_h, glass=glass_on)
                for k in ("name", "frames", "cell", "columns", "rows", "file"):
                    meta.pop(k, None)
                sheets[f"idle_{suffix}"] = write_sheet(out_dir, f"idle_{suffix}", ic, meta)
    report["faces"] = faces
    report["sheets"] = {k: {"cell": v["cell"], "frames": v["frames"], "grid": [v["columns"], v["rows"]]}
                        for k, v in sheets.items()}
    (out_dir / "build_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    review(char, out_dir, sheets)
    print(json.dumps(report["sheets"]))


def review(char: str, out_dir: Path, sheets: dict) -> None:
    """One review image: still cells, then every 4th idle cell, on a neutral background with a feet guide."""
    tiles = []
    for name in ("npc", "npc_q9c", "npc_bust_glass", "npc_bust", "idle", "idle_q9c", "idle_bust_glass"):
        if name not in sheets or not (out_dir / f"{name}_sheet.png").exists():
            continue
        meta = sheets[name]
        img = Image.open(out_dir / f"{name}_sheet.png").convert("RGBA")
        cw, ch = meta["cell"]
        cols = meta["columns"]
        step = 1 if name.startswith("npc") else max(1, meta["frames"] // 8)
        row = []
        for i in range(0, meta["frames"], step):
            c = img.crop(((i % cols) * cw, (i // cols) * ch, (i % cols + 1) * cw, (i // cols + 1) * ch))
            bg = Image.new("RGBA", c.size, (128, 132, 140, 255))
            bg.alpha_composite(c)
            ImageDraw.Draw(bg).line((0, meta["pivot"][1], cw, meta["pivot"][1]), fill=(255, 0, 0, 255))
            row.append(bg)
        strip = Image.new("RGB", (sum(r.width for r in row) + 4 * len(row), max(r.height for r in row)), (20, 20, 20))
        x = 0
        for r in row:
            strip.paste(r.convert("RGB"), (x, 0))
            x += r.width + 4
        tiles.append((name, strip))
    W = max(t.width for _, t in tiles)
    H = sum(t.height + 24 for _, t in tiles)
    sheet = Image.new("RGB", (W, H), (20, 20, 20))
    y = 0
    d = ImageDraw.Draw(sheet)
    for name, t in tiles:
        d.text((4, y + 4), f"{char} {name}", fill=(255, 255, 255))
        sheet.paste(t, (0, y + 24))
        y += t.height + 24
    sheet.save(cdir(char) / f"{char}_review.jpg", quality=88)


# ----------------------------------------------------------------------------- JANA20 (video portrait)

def screen_plate(name: str, size: tuple[int, int]) -> Image.Image:
    p = cdir("JANA20") / name
    return Image.open(p).convert("RGB").resize(size, Image.Resampling.LANCZOS)


def find_quad(rgb: np.ndarray) -> np.ndarray:
    """Corners (tl, tr, br, bl) of the magenta screen area of the laptop sheet."""
    f = rgb.astype(np.int16)
    m = (f[..., 0] > 170) & (f[..., 2] > 170) & (f[..., 1] < 110)
    m = components(m, 0.5)
    ys, xs = np.nonzero(m)
    pts = np.stack([xs, ys], 1).astype(np.float64)
    s, dd = pts.sum(1), pts[:, 0] - pts[:, 1]
    return np.array([pts[s.argmin()], pts[dd.argmax()], pts[s.argmax()], pts[dd.argmin()]]), m


def perspective_coeffs(dst: np.ndarray, src: np.ndarray) -> list[float]:
    """PIL PERSPECTIVE coefficients mapping output (dst) points to input (src) points."""
    a = []
    for (x, y), (u, v) in zip(dst, src):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        a.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    A = np.array(a, np.float64)
    b = src.reshape(8)
    return list(np.linalg.solve(A, b))


def build_screen(base: Base, stills: dict, var, faces: dict, report: dict) -> None:
    char = base.char
    cfg = base.cfg
    out_dir = cdir(char) / "sheets"
    screen_w = cfg.get("screen_width", 480)
    sw, sh = screen_w, round(screen_w * base.size[1] / base.size[0])
    plates = {"": screen_plate("plate_room.png", base.size)}
    if (cdir(char) / "plate_room_q9c.png").exists():
        plates["_q9c"] = screen_plate("plate_room_q9c.png", base.size)

    def frame_on(plate: Image.Image, rgba: np.ndarray, sharp: int = 0) -> Image.Image:
        img = plate.copy().convert("RGBA")
        img.alpha_composite(Image.fromarray(rgba, "RGBA"))
        img = img.convert("RGB").resize((sw, sh), Image.Resampling.LANCZOS)
        if sharp:
            img = img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=sharp, threshold=2))
        # webcam look: a hint of vignette
        return img.convert("RGBA")

    common = {"pivot": [sw // 2, sh], "playback_fps": 8, "oneshot": False, "stride_px_per_s": None,
              "pivot_is_sill_line": True, "height_px": sh}
    seq = [(0, 900), (1, 110), (0, 600), (2, 125), (3, 125), (2, 125), (0, 125), (3, 125), (2, 125), (0, 500),
           (4, 1200)]
    sheets = {}
    video = cdir(char) / cfg.get("video", "video_idle_pro.mp4")
    if not video.exists():
        video = cdir(char) / "video_idle.mp4"
    vsrc = None
    if video.exists():
        count = cfg.get("idle_frames", 48)
        vsrc, vrep = video_src_frames(base, video, count)
        top, bottom = head_band(base)
        vsrc, mrep = match_to_still(vsrc, base.key, (top, bottom))
        vrep.update(mrep)
        report["video"] = vrep
    for suffix, plate in plates.items():
        src = stills if suffix == "" or not var else var[0]
        cells = [frame_on(plate, src[n]) for n in STILL_NAMES]
        sheets[f"screen{suffix}"] = write_sheet(out_dir, f"screen{suffix}", cells,
                                                dict(common, frame_names=STILL_NAMES), seq, STILL_NAMES)
        if vsrc is not None:
            icells = [frame_on(plate, f, cfg.get("video_sharpen", 40)) for f in vsrc]
            sheets[f"idle_screen{suffix}"] = write_sheet(out_dir, f"idle_screen{suffix}", icells,
                                                         dict(common, playback_fps=round(len(icells) / 6.0, 2),
                                                              loop=True))
    # laptop variant: every screen cell warped into the laptop's magenta screen
    lap_path = cdir(char) / "laptop.png"
    if lap_path.exists():
        lap_rgb = np.asarray(Image.open(lap_path).convert("RGB"))
        lap_key = fr.chroma_key(lap_rgb)
        quad, screen_mask = find_quad(lap_rgb)
        x0, y0, x1, y1 = bbox(lap_key)
        lap_w = cfg.get("laptop_width", 300)
        s = lap_w / (x1 - x0)
        lap = Image.fromarray(lap_key, "RGBA").crop((x0, y0, x1, y1))
        lap = lap.resize((round(lap.width * s), round(lap.height * s)), Image.Resampling.LANCZOS)
        quad_c = (quad - [x0, y0]) * s
        smask = Image.fromarray((screen_mask * 255).astype(np.uint8)).crop((x0, y0, x1, y1)).resize(lap.size)
        smask = smask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))  # anti-aliased edge
        cw, ch = lap.width + 8, lap.height + 8
        report["laptop"] = {"quad": quad.round(1).tolist(), "scale": round(s, 4)}

        def on_laptop(screen: Image.Image) -> Image.Image:
            src = np.array([[0, 0], [screen.width, 0], [screen.width, screen.height], [0, screen.height]], np.float64)
            coeffs = perspective_coeffs(quad_c, src)
            warped = screen.convert("RGB").transform(lap.size, Image.Transform.PERSPECTIVE, coeffs,
                                                     Image.Resampling.BICUBIC)
            # screen glow: slightly lifted blacks, soft reflection streak
            arr = np.asarray(warped, np.float32) * 0.92 + 14
            out = lap.copy()
            out.paste(Image.fromarray(arr.clip(0, 255).astype(np.uint8)), (0, 0), smask)
            cell = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            cell.alpha_composite(out, (4, 4))
            return cell

        lcommon = dict(common, pivot=[cw // 2, ch - 4], pivot_is_sill_line=True, height_px=ch - 8)
        for name in list(sheets):
            meta = sheets[name]
            img = Image.open(out_dir / f"{name}_sheet.png").convert("RGBA")
            cwi, chi = meta["cell"]
            cols = meta["columns"]
            cells = [on_laptop(img.crop(((i % cols) * cwi, (i // cols) * chi, (i % cols + 1) * cwi,
                                         (i // cols + 1) * chi))) for i in range(meta["frames"])]
            lname = name.replace("screen", "laptop")
            extra = {k: meta[k] for k in ("frame_names", "loop") if k in meta}
            sheets[lname] = write_sheet(out_dir, lname, cells,
                                        dict(lcommon, playback_fps=meta["playback_fps"], **extra),
                                        seq if "frame_names" in meta else None, meta.get("frame_names"))
    report["faces"] = faces
    report["sheets"] = {k: {"cell": v["cell"], "frames": v["frames"], "grid": [v["columns"], v["rows"]]}
                        for k, v in sheets.items()}
    (out_dir / "build_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    review_screen(char, out_dir, sheets)
    print(json.dumps(report["sheets"]))


def review_screen(char: str, out_dir: Path, sheets: dict) -> None:
    rows = []
    for name, meta in sheets.items():
        img = Image.open(out_dir / f"{name}_sheet.png").convert("RGBA")
        cw, ch = meta["cell"]
        cols = meta["columns"]
        step = 1 if meta["frames"] <= 5 else max(1, meta["frames"] // 6)
        cells = []
        for i in range(0, meta["frames"], step):
            c = img.crop(((i % cols) * cw, (i // cols) * ch, (i % cols + 1) * cw, (i // cols + 1) * ch))
            bg = Image.new("RGBA", c.size, (128, 132, 140, 255))
            bg.alpha_composite(c)
            cells.append(bg.convert("RGB"))
        strip = Image.new("RGB", (sum(c.width + 4 for c in cells), ch + 20), (20, 20, 20))
        ImageDraw.Draw(strip).text((4, 2), name, fill=(255, 255, 255))
        x = 0
        for c in cells:
            strip.paste(c, (x, 20))
            x += c.width + 4
        rows.append(strip)
    W = max(r.width for r in rows)
    sheet = Image.new("RGB", (W, sum(r.height for r in rows)), (20, 20, 20))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height
    sheet.save(cdir(char) / f"{char}_review.jpg", quality=88)


# ----------------------------------------------------------------------------- export

def to_webp(src: Path, dst: Path, lossless: bool) -> tuple[int, int]:
    """Edit-based sheets are lossless (their bodies are pixel-identical between cells; lossy blocks would shimmer
    when the cells alternate), video sheets are lossy RGB q92 with lossless alpha."""
    img = Image.open(src).convert("RGBA")
    if max(img.size) > MAX_TEX:
        raise SystemExit(f"{src} is {img.size}, beyond {MAX_TEX} px")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if lossless:
        img.save(dst, "WEBP", lossless=True, quality=100, method=6, exact=False)
        assert np.array_equal(np.asarray(Image.open(dst).convert("RGBA"))[..., 3], np.asarray(img)[..., 3])
    else:
        img.save(dst, "WEBP", quality=92, alpha_quality=100, method=6)
    return img.size


def still_anims(sheet: str, idle: str | None, blink_inside: bool = False) -> dict:
    a = {
        "idle": ({"sheet": idle, "loop": True} if idle else {"sheet": sheet, "frames": ["idle"]}),
        "idle_still": {"sheet": sheet, "frames": ["idle"]},
        "blink": {"sheet": sheet, "frames": ["blink"], "hold_ms": 110, "every_s": [2.5, 6.0],
                  "note": "only while the still idle is shown (the idle loop blinks by itself)"},
        "talk": {"sheet": sheet, "frames": ["talk_a", "talk_b", "talk_a", "idle", "talk_b", "talk_a", "idle"],
                 "fps": 8, "loop": True},
        "gesture": {"sheet": sheet, "frames": ["gesture"], "hold_ms": 1200, "oneshot": True,
                    "note": "PlayGesture: hold, then return to idle (no in-betweens)"},
    }
    return a


def export(char: str) -> None:
    brief = ac.BRIEFS[char]
    src_dir = cdir(char) / "sheets"
    dst_dir = GAME_ACTORS / char
    dst_dir.mkdir(parents=True, exist_ok=True)
    sheets = {}
    for js in sorted(src_dir.glob("*_sheet.json")):
        key = js.name[:-len("_sheet.json")]
        meta = json.loads(js.read_text(encoding="utf-8"))
        name = f"{key}_sheet.webp"
        video = key.startswith("idle") and key != "idle_q9c"
        size = to_webp(src_dir / f"{key}_sheet.png", dst_dir / name, lossless=not video)
        meta["webp"] = "lossy q92, lossless alpha" if video else "lossless"
        meta["file"] = name
        meta.setdefault("loop", key.startswith("idle"))
        (dst_dir / f"{key}_sheet.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
                                                  encoding="utf-8", newline="\n")
        sheets[key] = {"file": name, "json": f"{key}_sheet.json", "size": list(size), "cell": meta["cell"],
                       "pivot": meta["pivot"], "frames": meta["frames"], "columns": meta["columns"],
                       "rows": meta["rows"]}
    staging = brief["staging"]
    variants: dict = {}
    default_variant = None
    if staging == "screen":
        main, idle = "laptop", "idle_laptop" if "idle_laptop" in sheets else None
        animations = still_anims(main, idle)
        variants["laptop"] = {"animations": still_anims("laptop", idle),
                              "note": "an open laptop on the bench showing Jana's video call; pivot = bottom centre "
                                      "of the laptop, place it on the painted bench top (placement sill_y)"}
        variants["screen"] = {"animations": still_anims("screen", "idle_screen" if "idle_screen" in sheets else None),
                              "note": "the flat 16:9 video frame only, to composite into a painted screen "
                                      "(placement sill_y = screen bottom, scale = screen width / cell width)"}
        if "laptop_q9c" in sheets:
            variants["laptop_q9c"] = {"animations": still_anims("laptop_q9c", "idle_laptop_q9c"
                                                                if "idle_laptop_q9c" in sheets else None),
                                      "note": "after Q9C (BF_JANA): refurbished laptops with labels behind her"}
            variants["screen_q9c"] = {"animations": still_anims("screen_q9c", "idle_screen_q9c"
                                                                if "idle_screen_q9c" in sheets else None),
                                      "note": "after Q9C, flat video frame"}
        default_variant = "laptop"
    else:
        idle = "idle" if "idle" in sheets else None
        animations = still_anims("npc", idle)
        if staging in ("window", "window_glass"):
            variants["window_glass"] = {"animations": still_anims("npc_bust_glass", "idle_bust_glass"
                                                                  if "idle_bust_glass" in sheets else None),
                                        "note": "behind closed glass: bust cut at the sill line, pale veil + soft "
                                                "reflection; pivot = sill line (placement sill_y)"}
            variants["window"] = {"animations": still_anims("npc_bust", "idle_bust" if "idle_bust" in sheets
                                                            else None),
                                  "note": "bust cut at the sill line without glass (open window); pivot = sill line"}
            variants["full"] = {"animations": still_anims("npc", None),
                                "note": "full figure stills (no video idle; the video was framed on the upper body)"}
            animations = still_anims("npc", None)
            default_variant = staging
        if "npc_q9c" in sheets:
            variants["q9c"] = {"animations": still_anims("npc_q9c", "idle_q9c"),
                               "note": "after Q9C (BF_JANA): prop variant; idle = breathing loop with a built-in "
                                       "blink (no video)"}
    npc_meta = json.loads((dst_dir / (("laptop" if staging == "screen" else "npc") + "_sheet.json")).read_text(
        encoding="utf-8"))
    manifest = {
        "id": char,
        "source": f"art/characters/{char}",
        "person": brief["person"],
        "view": ("front, webcam portrait inside a laptop screen" if staging == "screen"
                 else "three-quarter, facing right (mirror for facing left)"),
        "height_px": npc_meta.get("height_px", DEFAULT_HEIGHT),
        "pivot": ("feet centre (seated: lowest point of the seat / feet), 4 px above the cell bottom; window and "
                  "laptop variants: centre of the sill / laptop bottom edge"),
        "staging": staging,
        "sheets": sheets,
        "animations": animations,
        "switching": ("Start talking only at a video idle loop boundary (cell 0 matches the still idle pose) or "
                      "cross-fade ~80 ms; video cells are slightly softer than the edit-based stills."),
        "notes": brief.get("notes", ""),
    }
    if variants:
        manifest["variants"] = variants
        manifest["default_variant"] = default_variant
    (dst_dir / "actor.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
                                        newline="\n")
    # verify decode
    for key, s in sheets.items():
        im = Image.open(dst_dir / s["file"])
        assert tuple(im.size) == tuple(s["size"]) and max(im.size) <= MAX_TEX, key
    print(char, {k: (v["size"], v["frames"]) for k, v in sheets.items()})


# ----------------------------------------------------------------------------- likeness contact sheet

def likeness(person: str) -> None:
    ages = ac.PEOPLE[person]["ages"]
    figures, heads, labels = [], [], []
    for char in ages:
        d = GAME_ACTORS / char
        man = json.loads((d / "actor.json").read_text(encoding="utf-8"))
        key = "npc" if "npc" in man["sheets"] else "laptop"
        if char == "JANA20":
            key = "screen"
        s = man["sheets"][key]
        img = Image.open(d / s["file"]).convert("RGBA")
        cw, ch = s["cell"]
        cell = img.crop((0, 0, cw, ch))
        figures.append(cell)
        labels.append(f"{char} ({ac.BRIEFS[char]['age'] if char in ac.BRIEFS else 80})")
        # head: top of the figure, square crop of ~0.22 of the standing height
        bb = cell.getchannel("A").getbbox() or (0, 0, cw, ch)
        size = int(0.24 * DEFAULT_HEIGHT) if key != "screen" else int(ch * 0.8)
        cx = (bb[0] + bb[2]) // 2 if key == "screen" else None
        if key == "screen":
            box = (cw // 2 - size // 2, ch // 2 - size // 2 - ch // 10, cw // 2 + size // 2, ch // 2 + size // 2 - ch // 10)
        else:
            alpha = np.asarray(cell.getchannel("A")) > 128
            top = bb[1]
            rows = alpha[top:top + size]
            cols = np.flatnonzero(rows.any(axis=0))
            cx = int((cols.min() + cols.max()) / 2) if len(cols) else cw // 2
            box = (cx - size // 2, top - 6, cx + size // 2, top - 6 + size)
        head = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), (0, 0, 0, 0))
        head.alpha_composite(cell.crop(box))
        heads.append(head.resize((300, 300), Image.Resampling.LANCZOS))
    if person == "MIRA":
        d = GAME_ACTORS / "MIRA20"
        man = json.loads((d / "actor.json").read_text(encoding="utf-8"))
    pad = 30
    W = sum(f.width for f in figures) + pad * (len(figures) + 1)
    W = max(W, len(heads) * 320 + pad)
    Hf = max(f.height for f in figures)
    H = Hf + 300 + pad * 4 + 40
    sheet = Image.new("RGB", (W, H), (126, 130, 138))
    floor = pad + Hf
    d = ImageDraw.Draw(sheet)
    x = pad
    for f, lab in zip(figures, labels):
        sheet.paste(f, (x, floor - f.height), f)
        d.text((x, floor + 6), lab, fill=(255, 255, 255))
        x += f.width + pad
    d.line((pad, floor, W - pad, floor), fill=(200, 60, 60))
    x = pad
    y = floor + 40
    for h in heads:
        bg = Image.new("RGBA", h.size, (110, 114, 122, 255))
        bg.alpha_composite(h)
        sheet.paste(bg.convert("RGB"), (x, y))
        x += 320
    out = ac.LIKE_ROOT / person / f"{person}_likeness_final.jpg"
    sheet.save(out, quality=90)
    print(out)


# ----------------------------------------------------------------------------- head proportion fix (seated TONO)

def sample_bilinear(img: np.ndarray, sx: np.ndarray, sy: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    x0 = np.clip(np.floor(sx).astype(int), 0, w - 1)
    y0 = np.clip(np.floor(sy).astype(int), 0, h - 1)
    x1, y1 = np.clip(x0 + 1, 0, w - 1), np.clip(y0 + 1, 0, h - 1)
    fx, fy = (sx - np.floor(sx))[..., None], (sy - np.floor(sy))[..., None]
    f = img.astype(np.float32)
    top = f[y0, x0] * (1 - fx) + f[y0, x1] * fx
    bot = f[y1, x0] * (1 - fx) + f[y1, x1] * fx
    return (top * (1 - fy) + bot * fy).clip(0, 255).astype(np.uint8)


def head_warp(rgb: np.ndarray, cx: float, chin_y: float, collar_y: float, k: float) -> np.ndarray:
    """Magnify everything above the chin by k about the chin point; identity below the collar line, smooth between.

    Seated figures from the image models get realistic (small) heads on long bodies; the cast draws heads ~1/6.5 of
    the standing height. Applied identically to the base and every edit (raw images on the key colour).
    """
    h, w = rgb.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    t = np.clip((ys - chin_y) / (collar_y - chin_y), 0, 1)
    sc = k - (k - 1) * (t * t * (3 - 2 * t))
    return sample_bilinear(rgb, cx + (xs - cx) / sc, chin_y + (ys - chin_y) / sc)


def cmd_headwarp(char: str) -> None:
    d = cdir(char)
    cfg = config(char)
    hw = cfg["head_warp"]
    raw = load_raw(d / hw.get("raw", "sheet_raw.png"))
    base_key = fr.chroma_key(raw)
    x0, y0, x1, y1 = bbox(base_key)
    eb, mb = hw["eye_box"], hw["mouth_box"]
    cx = (eb[0] + eb[2]) / 2
    chin = float(mb[3])
    collar = chin + hw.get("collar", 0.7) * (chin - y0)
    k = hw["k"]
    out = head_warp(raw, cx, chin, collar, k)
    Image.fromarray(out).save(d / "sheet_3q.png")
    for kind in ("blink", "talk", "talk_oh", "gesture"):
        src = d / f"raw_{kind}.png"
        if not src.exists():
            continue
        rgb = load_raw(src, (raw.shape[1], raw.shape[0]))
        key = fr.chroma_key(rgb)
        band = (0.0, 1.0) if kind != "gesture" else (0.62, 1.0)
        rows = (int(y0 + band[0] * (y1 - y0)), int(y0 + band[1] * (y1 - y0)) + 4)
        dy, dx = phase_shift_band(base_key[..., 3].astype(np.float32), key[..., 3].astype(np.float32), rows)
        rgb = shift(rgb, dy, dx)
        rgb[(rgb == 0).all(axis=2)] = (0, 255, 0)  # shifted-in border: key colour
        Image.fromarray(head_warp(rgb, cx, chin, collar, k)).save(d / f"edit_{kind}.png")
        print(kind, "shift", dy, dx)
    print("warp", {"cx": cx, "chin": chin, "collar": collar, "k": k})


# ----------------------------------------------------------------------------- CLI

def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, target = sys.argv[1], sys.argv[2]
    if cmd == "canvas":
        canvas_for_video(Base(target))
    elif cmd == "faces":
        base = Base(target)
        faces = auto_faces(base)
        cfg = config(target)
        if "--save" in sys.argv:
            cfg["faces"] = faces
            save_config(target, cfg)
        faces = cfg.get("faces", faces) if "--use-saved" in sys.argv else faces
        faces_debug(base, faces, cdir(target) / "faces_debug.jpg")
        print(json.dumps(faces))
    elif cmd == "build":
        build(target)
    elif cmd == "headwarp":
        cmd_headwarp(target)
    elif cmd == "export":
        export(target)
    elif cmd == "likeness":
        likeness(target)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
