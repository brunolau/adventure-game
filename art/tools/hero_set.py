"""Production animation set for the hero (ADAM): local, free processing on top of chars.py outputs.

Notes and results: art/characters/PIPELINE.md section 11; shipped set: src/game/assets/actors/<ID>/README.md.
Stages (run from art/tools, roughly in this order; every stage reads/writes art/characters/<ID>/):
  prep                pose bases (one shared 1792x2400 canvas per facing) and 1080 px walk video canvases
  canvases POSE       start/end canvases for a pose-transition video (key pose aligned to the base by the feet)
  walk NAME VIDEO     walk loop from a Hailuo video (scale from the standing first frame; --fixed-baseline for
                      toward/away walks)
  idle FACING [--mask]  breathing + blink loop from the still masters (no video, so no texture boil)
  talk FACING [--mask]  mouth-shape loop composited onto the still body (mouth band only, so no flicker)
  oneshot POSE        reach / use_tool / show_item / inventory_combine: crisp first and last frame from the
                      stills, in-betweens sampled at equal pose progress from the transition video
  oneshot POSE --mask 2020 face-mask variant of a one-shot (tracked mask layer, NB2 frame edits where needed)
  walkmask NAME FACING  2020 face-mask variant of a walk (tracked mask layer)
  export              lossless WebP sheets + JSON + animations.json into src/game/assets/actors/<ID>/

Geometry contract (all animations of one facing): the standing figure is HEIGHT px tall (hair to soles);
pivot = feet centre at x = cell_w / 2 (y = cell_h - 4 except toward/away walks, see the JSON); cells are
symmetric around the pivot so the engine can mirror any right-facing sheet for the left direction with a plain
horizontal flip. Raw video frames are cached in art/characters/<ID>/_frames/ (regenerable, not kept).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

import frames as fr

ART = fr.ART
REPO = ART.parent
HEIGHT = 512                      # standing figure height in the shipped sheets
CANVAS = (1792, 2400)             # pose-base canvas (= NB2/Pro 3:4 2K output size)
BASE_FIG_H = 1700                 # standing figure height on the pose-base canvas
BASE_FEET_Y = 2256                # feet baseline on the pose-base canvas
VIDEO = (1080, 1080)
WALK_FIG, WALK_FEET = 0.80, 0.90  # walk video inputs: figure height and feet line as fractions of the canvas
POSE_FIG, POSE_FEET = 0.66, 0.94  # transition video inputs: room above the head for reach_high
GREEN = (0, 255, 0)


def char_dir(char: str) -> Path:
    return ART / "characters" / char


def load_rgba(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))


def save(img: Image.Image | np.ndarray, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(img, np.ndarray):
        img = Image.fromarray(img)
    img.save(path, optimize=True)
    return path


# ----------------------------------------------------------------------------- geometry helpers

def feet_center_x(rgba: np.ndarray, band: float = 0.06) -> float:
    """x centre of the lowest `band` of the figure (both shoes)."""
    x0, y0, x1, y1 = fr.alpha_bbox(rgba)
    rows = rgba[y1 - max(3, int((y1 - y0) * band)):y1, :, 3] > 128
    cols = np.flatnonzero(rows.any(axis=0))
    return float(cols.mean()) if len(cols) else (x0 + x1) / 2


def place(rgba: np.ndarray, canvas: tuple[int, int], fig_h: float, feet_y: float, anchor_x: float,
          anchor_src_x: float | None = None, color=GREEN, mirror: bool = False) -> Image.Image:
    """Scale a keyed (cropped or not) figure to fig_h and put its feet on feet_y with anchor_src_x at anchor_x."""
    if mirror:
        rgba = rgba[:, ::-1].copy()
    x0, y0, x1, y1 = fr.alpha_bbox(rgba)
    scale = fig_h / (y1 - y0)
    src_x = fr.torso_center_x(rgba) if anchor_src_x is None else anchor_src_x
    img = Image.fromarray(rgba, "RGBA")
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", canvas, color + (255,) if color else (0, 0, 0, 0))
    out.alpha_composite(img, (round(anchor_x - src_x * scale), round(feet_y - y1 * scale)))
    return out.convert("RGB") if color else out


def feet_shift(base_key: np.ndarray, edit_key: np.ndarray, band: float = 0.12) -> tuple[int, int]:
    """(dy, dx) aligning the edit's feet onto the base's feet (phase correlation on the lowest band only)."""
    x0, y0, x1, y1 = fr.alpha_bbox(base_key)
    top = y1 - int((y1 - y0) * band) - 20
    a = base_key[..., 3].astype(np.float32).copy()
    b = edit_key[..., 3].astype(np.float32).copy()
    a[:top] = 0
    b[:top] = 0
    return fr.phase_shift(a, b)


def boots_box(rgba: np.ndarray, band: float = 0.18) -> tuple[float, float, float]:
    """(centre x, width, bottom y) of the dark brown shoes in the lowest `band` of the figure.

    Used where the lowest band also holds a hand (reach_low), which confuses a plain alpha correlation; skin is
    excluded by its brightness, the bag by its height.
    """
    x0, y0, x1, y1 = fr.alpha_bbox(rgba)
    top = y1 - int((y1 - y0) * band)
    hsv = np.asarray(Image.fromarray(np.ascontiguousarray(rgba[..., :3])).convert("HSV")).astype(np.float32)
    h, s, v = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
    m = (h > 5) & (h < 40) & (s > 0.3) & (v < 0.6) & (rgba[..., 3] > 200)
    m[:top] = False
    labels, sizes = fr.label_components(m)
    keep = np.zeros(len(sizes) + 1, dtype=bool)
    keep[1:] = sizes >= 0.25 * sizes.max()       # the two shoes; drops finger outlines and specks
    ys, xs = np.nonzero(keep[labels])
    return float((xs.min() + xs.max()) / 2), float(xs.max() - xs.min()), float(ys.max())


# ----------------------------------------------------------------------------- warping (breathing, jaw)

def warp_rows(rgba: np.ndarray, src_y: np.ndarray) -> np.ndarray:
    """out[y] = in[src_y[y]] (fractional rows), premultiplied bilinear sampling. src_y has one value per row."""
    h = rgba.shape[0]
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255
    pre = np.concatenate([f[..., :3] * a, a * 255], axis=2)
    y0 = np.clip(np.floor(src_y).astype(int), 0, h - 1)
    y1 = np.clip(y0 + 1, 0, h - 1)
    t = (src_y - np.floor(src_y))[:, None, None]
    out = pre[y0] * (1 - t) + pre[y1] * t
    alpha = out[..., 3:4] / 255
    with np.errstate(divide="ignore", invalid="ignore"):
        rgb = np.where(alpha > 1e-4, out[..., :3] / np.maximum(alpha, 1e-4), 0)
    return np.dstack([rgb, out[..., 3]]).clip(0, 255).astype(np.uint8)


def warp_field(rgba: np.ndarray, dy: np.ndarray) -> np.ndarray:
    """General vertical displacement: out(x, y) = in(x, y + dy(x, y)), premultiplied bilinear."""
    h, w = rgba.shape[:2]
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255
    pre = np.concatenate([f[..., :3] * a, a * 255], axis=2)
    ys = np.arange(h, dtype=np.float32)[:, None] + dy
    y0 = np.clip(np.floor(ys).astype(int), 0, h - 1)
    y1 = np.clip(y0 + 1, 0, h - 1)
    t = (ys - np.floor(ys))[..., None]
    xs = np.broadcast_to(np.arange(w)[None, :], (h, w))
    out = pre[y0, xs] * (1 - t) + pre[y1, xs] * t
    alpha = out[..., 3:4] / 255
    with np.errstate(divide="ignore", invalid="ignore"):
        rgb = np.where(alpha > 1e-4, out[..., :3] / np.maximum(alpha, 1e-4), 0)
    return np.dstack([rgb, out[..., 3]]).clip(0, 255).astype(np.uint8)


def smoothstep(e0: float, e1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def breathe(rgba: np.ndarray, amount: float, top: float, chest: float, hips: float) -> np.ndarray:
    """Lift everything above the hips by `amount` px (shoulders and head fully, fading to 0 at the hips).

    top/chest/hips are figure-height fractions of the base figure (0 = hair top). Output row y samples input
    row y + amount * s(y), so content moves up by ~amount where s = 1.
    """
    x0, y0, x1, y1 = fr.alpha_bbox(rgba)
    h = y1 - y0
    ys = (np.arange(rgba.shape[0], dtype=np.float32) - y0) / h
    s = 1 - smoothstep(chest, hips, ys)   # 1 above the chest line, 0 below the hips
    if amount == 0:
        return rgba
    warped = warp_rows(rgba, np.arange(rgba.shape[0], dtype=np.float32) + amount * s)
    return np.where((amount * s > 1e-6)[:, None, None], warped, rgba)   # rows that do not move stay exact


# ----------------------------------------------------------------------------- cells

def to_cell(rgba: np.ndarray, scale: float, pivot_src: tuple[float, float], cell: tuple[int, int]) -> Image.Image:
    """Scale a source frame and place its pivot (x, feet y) at the cell pivot (w/2, h-4)."""
    img = Image.fromarray(rgba, "RGBA")
    img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", cell, (0, 0, 0, 0))
    out.alpha_composite(img, (round(cell[0] / 2 - pivot_src[0] * scale), round(cell[1] - 4 - pivot_src[1] * scale)))
    return out


def cell_size(frames: list[np.ndarray], scale: float, pivots: list[tuple[float, float]], margin: int = 6) -> tuple[int, int]:
    half, top = 0.0, 0.0
    for rgba, (px, py) in zip(frames, pivots):
        x0, y0, x1, y1 = fr.alpha_bbox(rgba)
        half = max(half, (px - x0) * scale, (x1 - px) * scale)
        top = max(top, (py - y0) * scale)
    w = 2 * int(math.ceil(half + margin))
    return w, int(math.ceil(top + margin + 4))


def sheet_meta(name: str, cells: list[Image.Image], fps: float, oneshot: bool, **extra) -> dict:
    w, h = cells[0].size
    meta = {"name": name, "frames": len(cells), "cell": [w, h], "pivot": [w // 2, h - 4],
            "playback_fps": round(fps, 2), "oneshot": oneshot, "stride_px_per_s": None,
            "standing_height_px": HEIGHT}
    meta.update(extra)
    return meta


def export(cells: list[Image.Image], out_dir: Path, name: str, meta: dict, labels: list[str] | None = None,
           gif_sequence=None) -> None:
    """Sheet PNG + JSON, GIF preview and contact sheet; the per-frame PNGs are dropped (the sheet is the master)."""
    fr.export_cells(cells, out_dir, name, meta, labels or [f"{i}" for i in range(len(cells))], gif_sequence)
    for frame_png in out_dir.glob(f"{name}_[0-9][0-9].png"):
        frame_png.unlink()


# ----------------------------------------------------------------------------- stage: prep

def stage_prep(char: str) -> None:
    d = char_dir(char)
    prod, masters = d / "prod", d / "masters"
    side_raw = fr.load_rgb(prod / "sheet_profile_open_solo_nb2.png")
    side_key = fr.crop_to_figure(fr.chroma_key(side_raw))
    save(side_key, masters / "side_keyed.png")
    # front / back: approved prototype turnaround views, mirrored so the bag hangs on his LEFT hip (brief)
    front_key = load_rgba(d / "keyed" / "turn_front.png")[:, ::-1].copy()
    back_key = load_rgba(d / "keyed" / "turn_back.png")[:, ::-1].copy()
    save(front_key, masters / "front_keyed.png")
    save(back_key, masters / "back_keyed.png")
    # pose bases: one canvas per facing; the side figure stands a bit left of centre (reaches go right)
    for facing, key, ax in (("side", side_key, CANVAS[0] * 0.44), ("front", front_key, CANVAS[0] / 2),
                            ("back", back_key, CANVAS[0] / 2)):
        save(place(key, CANVAS, BASE_FIG_H, BASE_FEET_Y, ax), prod / f"pose_base_{facing}.png")
        save(place(key, VIDEO, VIDEO[1] * WALK_FIG, VIDEO[1] * WALK_FEET, VIDEO[0] / 2), prod / f"video_in_walk_{facing}.png")
        print(facing, key.shape[1::-1])


# ----------------------------------------------------------------------------- stage: canvases (transition videos)

# Key-pose edits: source file (under prod/) and a scale correction where the editor re-framed the figure.
# reach_low: NB2 enlarged the crouching figure ~1.6x (head and boots measured against the base), so it is
# scaled back about its feet; every pose is then shifted so its feet sit on the base's feet.
KEY_POSES = {  # pose: (facing, edit file, scale correction, feet alignment)
    "reach_low": ("side", "pose_reach_low.png", 0.62, "boots"),
    "reach_mid": ("side", "pose_reach_mid.png", 1.0, "alpha"),
    "reach_high": ("side", "pose_reach_high_b.png", 1.0, "alpha"),
    "use_tool": ("side", "pose_use_tool_b.png", 1.0, "alpha"),
    "show_item": ("side", "pose_show_item.png", 1.0, "alpha"),
    "inventory_combine": ("front", "pose_inventory_combine.png", 1.0, "alpha"),
}


def keyed_aligned_pose(char: str, pose: str) -> np.ndarray:
    """Key pose edit keyed, scale-corrected and shifted so its feet sit exactly on the pose base's feet."""
    facing, source, scale, align = KEY_POSES[pose]
    prod = char_dir(char) / "prod"
    base = fr.chroma_key(fr.load_rgb(prod / f"pose_base_{facing}.png"))
    edit_rgb = fr.load_rgb(prod / source)
    if edit_rgb.shape[:2] != base.shape[:2]:
        edit_rgb = np.asarray(Image.fromarray(edit_rgb).resize(base.shape[1::-1], Image.Resampling.LANCZOS))
    edit = fr.chroma_key(edit_rgb)
    if scale != 1.0:
        x0, y0, x1, y1 = fr.alpha_bbox(edit)
        fx = feet_center_x(edit)
        img = Image.fromarray(edit, "RGBA")
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
        out = Image.new("RGBA", (edit.shape[1], edit.shape[0]), (0, 0, 0, 0))
        out.alpha_composite(img, (round(fx - fx * scale), round(y1 - y1 * scale)))  # scale about the feet
        edit = np.asarray(out)
    if align == "boots":
        bx, _bw, bb = boots_box(base)
        ex, _ew, eb = boots_box(edit)
        dy, dx = round(bb - eb), round(bx - ex)
    else:
        dy, dx = feet_shift(base, edit)
    return np.roll(edit, (dy, dx), axis=(0, 1))


def stage_canvases(char: str, pose: str) -> None:
    facing = KEY_POSES[pose][0]
    prod = char_dir(char) / "prod"
    base = fr.chroma_key(fr.load_rgb(prod / f"pose_base_{facing}.png"))
    edit = keyed_aligned_pose(char, pose)
    save(edit, char_dir(char) / "masters" / f"{pose}_aligned.png")
    x0, y0, x1, y1 = fr.alpha_bbox(base)
    scale = VIDEO[1] * POSE_FIG / (y1 - y0)
    px = fr.torso_center_x(base)
    for tag, rgba in (("start", base), ("end", edit)):
        img = Image.fromarray(rgba, "RGBA").resize((round(rgba.shape[1] * scale), round(rgba.shape[0] * scale)),
                                                    Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", VIDEO, GREEN + (255,))
        canvas.alpha_composite(img, (round(VIDEO[0] / 2 - px * scale), round(VIDEO[1] * POSE_FEET - y1 * scale)))
        save(canvas.convert("RGB"), prod / f"video_in_{pose}_{tag}.png")
    print(pose, "canvases written")


# ----------------------------------------------------------------------------- stage: walk

def scratch_frames(char: str, video: Path) -> list[Path]:
    """Extract (once) all frames of a video into art/characters/<ID>/_frames/<video stem>/ (not kept in git)."""
    out = char_dir(char) / "_frames" / video.stem
    frames = sorted(out.glob("f_*.png"))
    if not frames:
        frames = fr.extract_frames(video, out)
    return frames


def stage_walk(char: str, name: str, video: str, frames_out: int, period: tuple[float, float],
               fixed_baseline: bool) -> dict:
    """Walk loop on the standing scale (first video frame = the input still). Side walks align each frame's
    lowest foot to the baseline; toward/away walks keep the video's vertical positions (fixed_baseline)."""
    d = char_dir(char)
    paths = scratch_frames(char, d / "prod" / video)
    first = fr.chroma_key(fr.load_rgb(paths[0]))
    x0, y0, x1, y1 = fr.alpha_bbox(first)
    meta = fr.build_loop(paths, d / "anim" / name, 24.0, frames_out, period, 0.6, 0.2, True, HEIGHT, None, None,
                         name, choke=1, ref_height=float(y1 - y0),
                         fixed_baseline=float(y1) if fixed_baseline else None)
    meta.update(standing_height_px=HEIGHT, source_video=video)
    (d / "anim" / name / f"{name}_sheet.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(name, {k: meta[k] for k in ("cell", "cycle_seconds", "playback_fps", "loop_error", "stride_px_per_s",
                                       "height_px_range")})
    return meta


# ----------------------------------------------------------------------------- review

def review_strip(anim_dir: Path, name: str, out: Path | None = None, every: int = 1) -> Path:
    """Frames side by side on a flat background with guide lines: red = pivot (feet) line, blue = standing head
    height (pivot y - HEIGHT), grey = pivot x. Drift, bob and size pops show against the lines."""
    from PIL import ImageDraw
    meta = json.loads((anim_dir / f"{name}_sheet.json").read_text(encoding="utf-8"))
    sheet = Image.open(anim_dir / f"{name}_sheet.png").convert("RGBA")
    cw, ch = meta["cell"]
    px, py = meta["pivot"]
    n = sheet.width // cw
    cells = [sheet.crop((i * cw, 0, (i + 1) * cw, ch)) for i in range(0, n, every)]
    strip = Image.new("RGBA", (cw * len(cells), ch), (196, 186, 160, 255))
    for i, c in enumerate(cells):
        strip.alpha_composite(c, (i * cw, 0))
    draw = ImageDraw.Draw(strip)
    draw.line([(0, py), (strip.width, py)], fill=(220, 0, 0, 255), width=1)
    draw.line([(0, py - HEIGHT), (strip.width, py - HEIGHT)], fill=(0, 60, 220, 255), width=1)
    for i in range(len(cells)):
        draw.line([(i * cw + px, 0), (i * cw + px, ch)], fill=(90, 90, 90, 255), width=1)
        draw.line([(i * cw, 0), (i * cw, ch)], fill=(255, 255, 255, 255), width=1)
    out = out or anim_dir / f"{name}_review.jpg"
    strip.convert("RGB").save(out, quality=90)
    return out


# ----------------------------------------------------------------------------- face patches (blink, mouth, mask)

# Soft horizontal bands (figure-height fractions, 0 = hair top) that a face edit may change. Restricting a
# patch to its band keeps everything else pixel-identical to the base: the talk edits also raised the eyebrows,
# which would twitch at lip-sync speed, so mouth frames take only the mouth/jaw band.
FACE_BANDS = {"blink": (0.045, 0.100), "mouth": (0.098, 0.178), "mask": (0.030, 0.205)}
BAND_SOFT = 0.008


def head_columns(base_key: np.ndarray, pad: float = 0.03) -> tuple[float, float]:
    """x range of the head (alpha in the top 13 % of the figure), padded by `pad` figure heights."""
    x0, y0, x1, y1 = fr.alpha_bbox(base_key)
    h = y1 - y0
    band = base_key[y0:y0 + int(0.13 * h), :, 3] > 128
    cols = np.flatnonzero(band.any(axis=0))
    return float(cols.min() - pad * h), float(cols.max() + pad * h)


def head_align(base_key: np.ndarray, edit_key: np.ndarray) -> tuple[int, int]:
    """(dy, dx) aligning the edit's head on the base's head (phase correlation on the head region only)."""
    x0, y0, x1, y1 = fr.alpha_bbox(base_key)
    h = y1 - y0
    c0, c1 = head_columns(base_key, pad=0.06)
    r0, r1 = max(0, int(y0 - 0.03 * h)), int(y0 + 0.21 * h)
    c0, c1 = max(0, int(c0)), int(c1)

    def signature(k: np.ndarray) -> np.ndarray:
        crop = k[r0:r1, c0:c1].astype(np.float32)
        return crop[..., 3] / 255 * (40 + crop[..., :3].mean(axis=2))

    win = np.outer(np.hanning(r1 - r0), np.hanning(c1 - c0)).astype(np.float32)
    return fr.phase_shift(signature(base_key) * win, signature(edit_key) * win)


def premul(rgba: np.ndarray) -> np.ndarray:
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255
    return np.concatenate([f[..., :3] * a, f[..., 3:4]], axis=2)


def unpremul(p: np.ndarray) -> np.ndarray:
    a = p[..., 3:4] / 255
    with np.errstate(divide="ignore", invalid="ignore"):
        rgb = np.where(a > 1e-4, p[..., :3] / np.maximum(a, 1e-4), 0)
    return np.dstack([rgb, p[..., 3]]).clip(0, 255).astype(np.uint8)


def mask_coloured(rgba: np.ndarray) -> np.ndarray:
    """Light blue fabric or white elastic of a disposable face mask."""
    hsv = np.asarray(Image.fromarray(np.ascontiguousarray(rgba[..., :3])).convert("HSV")).astype(np.float32)
    hue, sat, val = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
    # fabric ~189 deg / value 0.82; the jacket (incl. collar highlights) is ~219 deg / value <= 0.6
    blue = (hue > 172) & (hue < 212) & (sat > 0.10) & (sat < 0.65) & (val > 0.62)
    white = (sat < 0.28) & (val > 0.62)          # elastic loops, antialiased over skin or hair
    return (blue | white) & (rgba[..., 3] > 128)


def patch_weights(base_key: np.ndarray, edit_rgb: np.ndarray, band: tuple[float, float], threshold: float = 16.0,
                  feather: int = 6, columns: tuple[float, float] | None = None,
                  face_mask_rule: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """Edit keyed and head-aligned onto the base, plus the per-pixel blend weight of its changed face region.

    face_mask_rule: above the eye line only new mask-coloured pixels (ear loops over hair or skin) count as a
    change, so a re-rendered eye from the mask edit never replaces the base (or blink) eyes.
    """
    if edit_rgb.shape[:2] != base_key.shape[:2]:
        edit_rgb = np.asarray(Image.fromarray(edit_rgb).resize(base_key.shape[1::-1], Image.Resampling.LANCZOS))
    edit_key = fr.chroma_key(edit_rgb)
    dy, dx = head_align(base_key, edit_key)
    edit_key = np.roll(edit_key, (dy, dx), axis=(0, 1))
    x0, y0, x1, y1 = fr.alpha_bbox(base_key)
    h = y1 - y0
    ys = (np.arange(base_key.shape[0], dtype=np.float32) - y0) / h
    wy = smoothstep(band[0] - BAND_SOFT, band[0] + BAND_SOFT, ys) * (1 - smoothstep(band[1] - BAND_SOFT,
                                                                                       band[1] + BAND_SOFT, ys))
    hx0, hx1 = columns or head_columns(base_key)
    xs = np.arange(base_key.shape[1], dtype=np.float32)
    wx = smoothstep(hx0 - 12, hx0 + 12, xs) * (1 - smoothstep(hx1 - 12, hx1 + 12, xs))
    weight = wy[:, None] * wx[None, :]
    diff = np.abs(premul(base_key) - premul(edit_key)).mean(axis=2)
    changed = (diff > threshold) & (weight > 0.01)
    if face_mask_rule:
        new_mask = mask_coloured(edit_key) & ~mask_coloured(base_key)
        new_mask = np.asarray(Image.fromarray((new_mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        above_eyes = (ys < 0.098)[:, None]
        changed &= ~above_eyes | new_mask
    mask = Image.fromarray((changed * 255).astype(np.uint8), "L")
    mask = mask.filter(ImageFilter.MaxFilter(2 * feather + 1)).filter(ImageFilter.GaussianBlur(feather))
    return edit_key, (np.asarray(mask, dtype=np.float32) / 255) * weight


def blend(under: np.ndarray, over: np.ndarray, weight: np.ndarray) -> np.ndarray:
    """Premultiplied blend: over where weight = 1, under where weight = 0."""
    w = weight[..., None]
    mixed = unpremul(premul(under) * (1 - w) + premul(over) * w)
    return np.where(w > 0, mixed, under)       # untouched pixels stay bit-identical (no edge rounding)


def face_masters(char: str, facing: str) -> dict[str, np.ndarray]:
    """Full-canvas keyed masters of one facing: base, blink, talk_a/o/e, mask, mask_blink (+ the mask layer)."""
    cache = char_dir(char) / "masters" / f"face_{facing}"
    names = ["base", "blink", "talk_a", "talk_o", "talk_e", "mask", "mask_blink", "mask_layer"]
    if facing == "back":
        names = ["base", "mask", "mask_layer"]
    if all((cache / f"{n}.png").exists() for n in names):
        return {n: load_rgba(cache / f"{n}.png") for n in names}
    prod = char_dir(char) / "prod"
    base = fr.chroma_key(fr.load_rgb(prod / f"pose_base_{facing}.png"))
    out = {"base": base}
    if facing == "back":
        # the back edit drew one strap across the back of the head; keep only the ear zones (ear loops)
        hx0, hx1 = head_columns(base, pad=0.0)
        width = hx1 - hx0
        mask_key, w = patch_weights(base, fr.load_rgb(prod / "pose_back_mask2020.png"), FACE_BANDS["mask"],
                                    columns=(hx0 - 0.02 * width, hx1 + 0.02 * width), face_mask_rule=True)
        xs = np.arange(base.shape[1], dtype=np.float32)
        ears = 1 - smoothstep(hx0 + 0.16 * width, hx0 + 0.24 * width, xs) * (
            1 - smoothstep(hx1 - 0.24 * width, hx1 - 0.16 * width, xs))
        w = w * ears[None, :]
    else:
        blink_key, wb = patch_weights(base, fr.load_rgb(prod / f"pose_{facing}_blink.png"), FACE_BANDS["blink"])
        out["blink"] = blend(base, blink_key, wb)
        for m in "aoe":
            k, wm = patch_weights(base, fr.load_rgb(prod / f"pose_{facing}_talk_{m}.png"), FACE_BANDS["mouth"])
            out[f"talk_{m}"] = blend(base, k, wm)
        mask_key, w = patch_weights(base, fr.load_rgb(prod / f"pose_{facing}_mask2020.png"), FACE_BANDS["mask"],
                                    face_mask_rule=True)
        out["mask_blink"] = blend(out["blink"], mask_key, w)
    out["mask"] = blend(base, mask_key, w)
    out["mask_layer"] = overlay_layer(mask_key, w)
    for n, img in out.items():
        save(img, cache / f"{n}.png")
    return out


def overlay_layer(mask_key: np.ndarray, weight: np.ndarray) -> np.ndarray:
    """The face mask alone (fabric + ear loops) as an RGBA layer for compositing onto other bodies.

    The patch weight also covers re-rendered skin and collar pixels near the mask; on the same body that is
    harmless, on a walk frame it would paste a ghost collar line, so the layer keeps only mask-coloured pixels
    (closed to fill the darker folds).
    """
    hsv = np.asarray(Image.fromarray(np.ascontiguousarray(mask_key[..., :3])).convert("HSV")).astype(np.float32)
    fabric = ((hsv[..., 0] * 360 / 255 > 172) & (hsv[..., 0] * 360 / 255 < 212) & (hsv[..., 2] > 158)
              & (weight > 0.01))
    m = Image.fromarray(((mask_coloured(mask_key) & (weight > 0.01)) * 255).astype(np.uint8), "L")
    m = m.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(7))
    # keep only pieces that hold mask fabric (the fabric itself, loops attached to it, the back view's slivers);
    # skin highlights on the neck, eye whites and jacket specks are separate pieces and are dropped
    labels, sizes = fr.label_components(np.asarray(m) > 0)
    blue_count = np.bincount(labels[fabric], minlength=len(sizes) + 1)
    keep = blue_count >= 150
    keep[0] = False
    m = Image.fromarray((keep[labels] * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(1.2))
    layer = mask_key.copy()
    layer[..., 3] = (layer[..., 3].astype(np.float32) * weight * np.asarray(m, np.float32) / 255).astype(np.uint8)
    return layer


def pose_mask_master(char: str, pose: str) -> tuple[np.ndarray, np.ndarray] | None:
    """(masked end key pose, mask layer) from a dedicated NB2 mask edit of the key pose, if one exists."""
    prod = char_dir(char) / "prod"
    edit = prod / f"pose_{pose}_mask2020.png"
    if not edit.exists():
        return None
    end = load_rgba(char_dir(char) / "masters" / f"{pose}_aligned.png")
    k, w = patch_weights(end, fr.load_rgb(edit), (-0.5, 1.5), columns=mask_columns(end, k_rgb=fr.load_rgb(edit)))
    return blend(end, k, w), overlay_layer(k, w)


def mask_columns(end: np.ndarray, k_rgb: np.ndarray) -> tuple[float, float]:
    """x range where a mask edit of a key pose differs (the head can be anywhere, e.g. bent down)."""
    if k_rgb.shape[:2] != end.shape[:2]:
        k_rgb = np.asarray(Image.fromarray(k_rgb).resize(end.shape[1::-1], Image.Resampling.LANCZOS))
    k = fr.chroma_key(k_rgb)
    diff = np.abs(premul(end) - premul(k)).mean(axis=2)
    hsv = np.asarray(Image.fromarray(np.ascontiguousarray(k[..., :3])).convert("HSV")).astype(np.float32)
    bluish = (hsv[..., 0] * 360 / 255 > 170) & (hsv[..., 0] * 360 / 255 < 225) & (hsv[..., 2] > 150)
    ys, xs = np.nonzero((diff > 30) & bluish)          # the light blue mask itself
    if len(xs) == 0:
        return 0.0, float(end.shape[1])
    pad = 0.6 * (xs.max() - xs.min())
    return float(xs.min() - pad), float(xs.max() + pad)


# ----------------------------------------------------------------------------- stages: idle and talk

IDLE_FRAMES, IDLE_FPS, IDLE_BLINK = 32, 8.0, (22,)
BREATH = 0.0035          # shoulder lift as a fraction of the figure height (~1.8 px at 512)
TALK_SEQUENCE = ["a", "e", "rest", "o", "a", "e", "rest", "a", "o", "e", "a", "rest"]
TALK_FPS = 10.0
JAW_OPEN = {"a": 1.0, "o": 0.7, "e": 0.45, "rest": 0.0}
JAW = 0.006              # jaw drop under the face mask for 'a', fraction of the figure height


def master_geometry(base_key: np.ndarray) -> tuple[float, tuple[float, float]]:
    x0, y0, x1, y1 = fr.alpha_bbox(base_key)
    return HEIGHT / (y1 - y0), (fr.torso_center_x(base_key), float(y1))


def cells_from_masters(frames: list[np.ndarray], base_key: np.ndarray) -> list[Image.Image]:
    scale, pivot = master_geometry(base_key)
    cell = cell_size(frames, scale, [pivot] * len(frames))
    return [to_cell(f, scale, pivot, cell) for f in frames]


def jaw_warp(rgba: np.ndarray, base_key: np.ndarray, facing: str, amount: float) -> np.ndarray:
    """Move the lower face (nose line to chin) down by up to `amount` px, the neck below absorbs it."""
    if amount <= 0:
        return rgba
    x0, y0, x1, y1 = fr.alpha_bbox(base_key)
    h = y1 - y0
    ys = (np.arange(rgba.shape[0], dtype=np.float32) - y0) / h
    nose, chin, below = 0.105, 0.155, 0.195
    d = np.where(ys < nose, 0, np.where(ys < chin, (ys - nose) / (chin - nose),
                                        np.where(ys < below, 1 - (ys - chin) / (below - chin), 0)))
    hx0, hx1 = head_columns(base_key, pad=0.0)
    if facing == "side":
        cx0, cx1 = (hx0 + hx1) / 2, hx1 + 0.03 * h       # face = front half of the head in profile
    else:
        w = hx1 - hx0
        cx0, cx1 = hx0 + 0.12 * w, hx1 - 0.12 * w
    xs = np.arange(rgba.shape[1], dtype=np.float32)
    wx = smoothstep(cx0 - 10, cx0 + 10, xs) * (1 - smoothstep(cx1 - 10, cx1 + 10, xs))
    dy = -(amount * d[:, None] * wx[None, :]).astype(np.float32)
    return np.where((np.abs(dy) > 1e-6)[..., None], warp_field(rgba, dy), rgba)  # untouched pixels stay exact


def stage_idle(char: str, facing: str, mask: bool) -> None:
    M = face_masters(char, facing)
    base = M["mask"] if mask else M["base"]
    blink = M.get("mask_blink" if mask else "blink")
    _x0, y0, _x1, y1 = fr.alpha_bbox(M["base"])
    amount = BREATH * (y1 - y0)
    frames = []
    for t in range(IDLE_FRAMES):
        src = blink if (blink is not None and t in IDLE_BLINK) else base
        frames.append(breathe(src, amount * (0.5 - 0.5 * math.cos(2 * math.pi * t / IDLE_FRAMES)), 0, 0.30, 0.55))
    cells = cells_from_masters(frames, M["base"])
    name = f"idle_{FACING_NAME[facing]}" + ("_mask2020" if mask else "")
    meta = sheet_meta(name, cells, IDLE_FPS, False, facing=FACING_NAME[facing], source="still masters, "
                      "procedural breathing warp + blink frame", blink_frames=list(IDLE_BLINK) if blink is not None
                      else [], breath_px=round(amount * HEIGHT / (y1 - y0), 2))
    export(cells, char_dir(char) / "anim" / name, name, meta)
    review_strip(char_dir(char) / "anim" / name, name, every=2)
    print(name, meta["cell"])


def stage_talk(char: str, facing: str, mask: bool) -> None:
    M = face_masters(char, facing)
    frames = []
    for shape in TALK_SEQUENCE:
        if mask:
            _x0, y0, _x1, y1 = fr.alpha_bbox(M["base"])
            frames.append(jaw_warp(M["mask"], M["base"], facing, JAW * (y1 - y0) * JAW_OPEN[shape]))
        else:
            frames.append(M["base"] if shape == "rest" else M[f"talk_{shape}"])
    cells = cells_from_masters(frames, M["base"])
    name = f"talk_{FACING_NAME[facing]}" + ("_mask2020" if mask else "")
    meta = sheet_meta(name, cells, TALK_FPS, False, facing=FACING_NAME[facing], mouth_sequence=TALK_SEQUENCE,
                      source="still body; " + ("jaw warp under the face mask" if mask else
                                               "mouth/jaw band of NB2 mouth edits composited onto the body"))
    export(cells, char_dir(char) / "anim" / name, name, meta)
    print(name, meta["cell"])


FACING_NAME = {"side": "right", "front": "front", "back": "back"}


# ----------------------------------------------------------------------------- head tracking for mask overlays

def fft_corr(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Valid-mode cross-correlation sum_x a(p + x) b(x) for every p where b fits inside a (2-D)."""
    ha, wa = a.shape
    hb, wb = b.shape
    fa = np.fft.rfft2(a, s=(ha, wa))
    fb = np.fft.rfft2(b[::-1, ::-1], s=(ha, wa))
    full = np.fft.irfft2(fa * fb, s=(ha, wa))
    return full[hb - 1:ha, wb - 1:wa]


class HeadTemplate:
    """A head crop (and the matching mask layer crop) at cell scale, matched by weighted SSD over rotations and
    scales; the layer is composited with the winning transform."""

    def __init__(self, head: np.ndarray, layer: np.ndarray, angles: list[float], scales: list[float]):
        self.variants = []
        for ang in angles:
            for sc in scales:
                size = (max(1, round(head.shape[1] * sc)), max(1, round(head.shape[0] * sc)))
                h_img = Image.fromarray(head, "RGBA").resize(size, Image.Resampling.LANCZOS)
                l_img = Image.fromarray(layer, "RGBA").resize(size, Image.Resampling.LANCZOS)
                if ang:
                    h_img = h_img.rotate(ang, Image.Resampling.BICUBIC, expand=True)
                    l_img = l_img.rotate(ang, Image.Resampling.BICUBIC, expand=True)
                t = premul(np.asarray(h_img)) / 255
                wmask = Image.fromarray(((t[..., 3] > 0.1) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))
                w = np.asarray(wmask, dtype=np.float32) / 255
                self.variants.append((ang, sc, t, w, np.asarray(l_img), float((w[..., None] * t * t).sum()),
                                      float(w.sum())))

    def match(self, frame: np.ndarray, guess: tuple[int, int], search: int) -> tuple[float, tuple[int, int], int]:
        """Best (mse, top-left position, variant index) with the variant's top-left within `search` of guess.

        guess is the top-left position for the unrotated, unscaled template; rotated/scaled variants are
        compared by their centres.
        """
        f = premul(frame) / 255
        best = (float("inf"), guess, 0)
        h0, w0 = self.variants[0][2].shape[:2]
        for index, (_ang, _sc, t, w, _layer, tt, ws) in enumerate(self.variants):
            th, tw = t.shape[:2]
            gx = guess[0] + w0 / 2 - tw / 2
            gy = guess[1] + h0 / 2 - th / 2
            rx0, ry0 = int(max(0, gx - search)), int(max(0, gy - search))
            rx1 = int(min(f.shape[1], gx + search + tw))
            ry1 = int(min(f.shape[0], gy + search + th))
            if rx1 - rx0 < tw or ry1 - ry0 < th:
                continue
            region = f[ry0:ry1, rx0:rx1]
            ff = fft_corr((region * region).sum(axis=2), w)
            ft = sum(fft_corr(region[..., c], w * t[..., c]) for c in range(4))
            ssd = (ff - 2 * ft + tt) / max(ws, 1.0)
            iy, ix = np.unravel_index(int(np.argmin(ssd)), ssd.shape)
            if ssd[iy, ix] < best[0]:
                best = (float(ssd[iy, ix]), (rx0 + int(ix), ry0 + int(iy)), index)
        return best

    def apply(self, frame: np.ndarray, pos: tuple[int, int], index: int) -> np.ndarray:
        out = Image.fromarray(frame, "RGBA")
        layer = Image.fromarray(self.variants[index][4], "RGBA")
        out.alpha_composite(layer, (max(0, pos[0]), max(0, pos[1])))
        return np.asarray(out)


def head_crop_box(master: np.ndarray, layer: np.ndarray) -> tuple[int, int, int, int]:
    """Box around the head: the mask layer's bounding box grown to include hair, ears and chin."""
    ys, xs = np.nonzero(layer[..., 3] > 40)
    lx0, lx1, ly0, ly1 = xs.min(), xs.max(), ys.min(), ys.max()
    w, h = lx1 - lx0, ly1 - ly0
    x0, y0, x1, y1 = fr.alpha_bbox(master)
    fig_h = y1 - y0
    size = 0.20 * fig_h   # a head is ~1/6.5 of the standing height
    cx, cy = (lx0 + lx1) / 2, (ly0 + ly1) / 2
    return (int(cx - size * 0.62), int(cy - size * 0.78), int(cx + size * 0.62), int(cy + size * 0.45))


def make_template(master: np.ndarray, layer: np.ndarray, scale: float, pivot: tuple[float, float],
                  cell: tuple[int, int], angles: list[float], scales: list[float]) -> tuple[HeadTemplate, tuple[int, int]]:
    """Template at cell scale plus the template's top-left position in a cell rendered from this master."""
    bx0, by0, bx1, by1 = head_crop_box(master, layer)
    head_cell = np.asarray(to_cell(master, scale, pivot, cell))
    layer_cell = np.asarray(to_cell(layer, scale, pivot, cell))
    ox, oy = cell[0] / 2 - pivot[0] * scale, cell[1] - 4 - pivot[1] * scale
    cx0, cy0 = int(max(0, bx0 * scale + ox)), int(max(0, by0 * scale + oy))
    cx1, cy1 = int(min(cell[0], bx1 * scale + ox)), int(min(cell[1], by1 * scale + oy))
    head = head_cell[cy0:cy1, cx0:cx1].copy()
    lay = layer_cell[cy0:cy1, cx0:cx1].copy()
    return HeadTemplate(head, lay, angles, scales), (cx0, cy0)


def overlay_masks(cells: list[Image.Image], templates: list[tuple[HeadTemplate, tuple[int, int]]],
                  search: int, start_centre: tuple[float, float] | None = None) -> tuple[list[Image.Image], list[dict]]:
    """Composite the mask layer of the best-matching template onto every cell, tracking one head centre.

    Every template searches around the head centre found in the previous cell (initially start_centre or the
    first template's own position), so a template can never jump to a far-away look-alike (the chest).
    """
    out, report = [], []

    def centre_of(tmpl: HeadTemplate, pos: tuple[int, int], vi: int) -> tuple[float, float]:
        th, tw = tmpl.variants[vi][2].shape[:2]
        return pos[0] + tw / 2, pos[1] + th / 2

    if start_centre is None:
        t0, p0 = templates[0]
        start_centre = centre_of(t0, p0, 0)
    centre = start_centre
    for i, cell in enumerate(cells):
        frame = np.asarray(cell.convert("RGBA"))
        best = None
        for ti, (tmpl, _pos) in enumerate(templates):
            h0, w0 = tmpl.variants[0][2].shape[:2]
            guess = (round(centre[0] - w0 / 2), round(centre[1] - h0 / 2))
            mse, pos, vi = tmpl.match(frame, guess, search)
            if best is None or mse < best[0]:
                best = (mse, pos, vi, ti)
        mse, pos, vi, ti = best
        tmpl = templates[ti][0]
        out.append(Image.fromarray(tmpl.apply(frame, pos, vi), "RGBA"))
        report.append({"frame": i, "template": ti, "angle": tmpl.variants[vi][0], "scale": tmpl.variants[vi][1],
                       "mse": round(mse, 5)})
        centre = centre_of(tmpl, pos, vi)
    return out, report


# ----------------------------------------------------------------------------- stage: one-shots

ONESHOT_VIDEOS = {"reach_high": "video_reach_high_pro_b.mp4"}  # retakes
ONESHOTS = {  # pose: (frames out, playback fps)
    "reach_low": (12, 12.0), "reach_mid": (10, 12.0), "reach_high": (10, 12.0),
    "use_tool": (16, 12.0), "show_item": (10, 12.0), "inventory_combine": (14, 12.0),
}


def progress_picks(keyed: list[np.ndarray], count: int, span: tuple[int, int] | None = None) -> tuple[list[int], list[float]]:
    """Source frames at equal steps of pose progress p = d0 / (d0 + d1) (distance to start and end signature).

    Hailuo moves quickly and then drifts slowly into the end frame; equal time steps would spend most frames on
    the drift and still jump at the end, equal progress steps put the frames where the pose actually changes.
    """
    lo, hi = span or (0, len(keyed) - 1)
    sigs = [silhouette_fixed(k) for k in keyed[lo:hi + 1]]
    d0 = np.array([np.abs(x - sigs[0]).mean() for x in sigs])
    d1 = np.array([np.abs(x - sigs[-1]).mean() for x in sigs])
    prog = np.maximum.accumulate(d0 / np.maximum(d0 + d1, 1e-9))
    prog = (prog - prog[0]) / max(prog[-1] - prog[0], 1e-9)
    picks = [lo + int(np.searchsorted(prog, (i + 1) / (count + 1))) for i in range(count)]
    return picks, [round(float(prog[q - lo]), 3) for q in picks]


def silhouette_fixed(rgba: np.ndarray, size: int = 128) -> np.ndarray:
    """Alpha+luminance signature on the full (uncropped) frame, so pose changes are not normalised away."""
    img = Image.fromarray(rgba, "RGBA")
    a = np.asarray(img.getchannel("A").resize((size, size), Image.Resampling.BILINEAR), np.float32) / 255
    lum = np.asarray(img.convert("L").resize((size, size), Image.Resampling.BILINEAR), np.float32) / 255
    return np.concatenate([a.ravel(), (lum * a).ravel() * 0.5])


# Poses whose video in-betweens put a hand above the head: Hailuo smears the raised fingers into a khaki/olive
# cast (chroma bleed plus a soft render). Above the standing head line there is only arm and hand, so khaki and
# olive pixels there are pulled back to skin tone; the T-shirt (same hue ratio) is never in that zone.
SKIN_ABOVE_HEAD = {"reach_high"}


def skin_fix_above(cell: Image.Image, top_rows: int) -> Image.Image:
    a = np.asarray(cell.convert("RGBA")).copy()
    zone = a[:max(0, top_rows)].astype(np.float32)
    r, g, b = zone[..., 0], zone[..., 1], zone[..., 2]
    khaki = (g > 0.74 * r) & (g > b + 18) & (zone[..., 3] > 0)
    zone[..., 1] = np.where(khaki, np.minimum(g, 0.72 * r), g)
    zone[..., 2] = np.where(khaki, np.maximum(b, 0.56 * r), b)
    a[:max(0, top_rows)] = zone.clip(0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def stage_oneshot(char: str, pose: str, span: tuple[int, int] | None = None) -> None:
    facing = KEY_POSES[pose][0]
    d = char_dir(char)
    M = face_masters(char, facing)
    base = M["base"]
    end = load_rgba(d / "masters" / f"{pose}_aligned.png")
    video = ONESHOT_VIDEOS.get(pose, f"video_{pose}_pro.mp4")
    paths = scratch_frames(char, d / "prod" / video)
    keyed = [fr.chroma_key(fr.load_rgb(p), choke=1) for p in paths]
    frames_out, fps = ONESHOTS[pose]
    picks, progress = progress_picks(keyed, frames_out - 2, span)
    first, settle = picks[0], picks[-1]
    # geometry: masters on the master transform, video frames on the transform of their standing first frame
    m_scale, m_pivot = master_geometry(base)
    v0 = keyed[0]
    _x0, vy0, _x1, vy1 = fr.alpha_bbox(v0)
    v_scale, v_pivot = HEIGHT / (vy1 - vy0), (fr.torso_center_x(v0), float(vy1))
    srcs = [(base, m_scale, m_pivot)] + [(keyed[i], v_scale, v_pivot) for i in picks] + [(end, m_scale, m_pivot)]
    half, top = 0.0, 0.0
    for rgba, sc, (px, py) in srcs:
        x0, y0, x1, y1 = fr.alpha_bbox(rgba)
        half = max(half, (px - x0) * sc, (x1 - px) * sc)
        top = max(top, (py - y0) * sc)
    cell = (2 * int(math.ceil(half + 6)), int(math.ceil(top + 10)))
    cells = [to_cell(rgba, sc, pv, cell) for rgba, sc, pv in srcs]
    if pose in SKIN_ABOVE_HEAD:
        cells = [cells[0]] + [skin_fix_above(c, cell[1] - 4 - HEIGHT + 6) for c in cells[1:-1]] + [cells[-1]]
    name = f"{pose}_{FACING_NAME[facing]}"
    meta = sheet_meta(name, cells, fps, True, facing=FACING_NAME[facing], source_video=video,
                      source_frames=["still:base"] + picks + ["still:key_pose"], progress=progress,
                      note="play forward to act, hold the last frame, play reversed to return to idle")
    out_dir = d / "anim" / name
    export(cells, out_dir, name, meta)
    review_strip(out_dir, name)
    print(name, meta["cell"], "picks", picks, "progress", progress)


# In-between video frames where head tracking cannot place a profile mask (head pitched down toward the floor):
# NB2 painted the mask onto the source video frame itself; only its mask pixels are transplanted.
MASK_FRAME_EDITS = {"reach_low": {33: "frame_reach_low_f0034_mask2020.png", 44: "frame_reach_low_f0045_mask2020.png",
                                  49: "frame_reach_low_f0050_mask2020.png"}}


def frame_mask_layer(frame_key: np.ndarray, edit_rgb: np.ndarray) -> np.ndarray:
    """Mask-only layer from an NB2 mask edit of one keyed video frame (aligned by phase correlation)."""
    if edit_rgb.shape[:2] != frame_key.shape[:2]:
        edit_rgb = np.asarray(Image.fromarray(edit_rgb).resize(frame_key.shape[1::-1], Image.Resampling.LANCZOS))
    edit_key = fr.chroma_key(edit_rgb)
    dy, dx = fr.phase_shift(frame_key[..., 3].astype(np.float32), edit_key[..., 3].astype(np.float32))
    edit_key = np.roll(edit_key, (dy, dx), axis=(0, 1))
    diff = np.abs(premul(frame_key) - premul(edit_key)).mean(axis=2)
    mask = Image.fromarray(((diff > 16) * 255).astype(np.uint8), "L")
    mask = mask.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(3))
    return overlay_layer(edit_key, np.asarray(mask, np.float32) / 255)


def stage_oneshot_mask(char: str, pose: str) -> None:
    facing = KEY_POSES[pose][0]
    d = char_dir(char)
    name = f"{pose}_{FACING_NAME[facing]}"
    src_dir = d / "anim" / name
    meta = json.loads((src_dir / f"{name}_sheet.json").read_text(encoding="utf-8"))
    sheet = Image.open(src_dir / f"{name}_sheet.png").convert("RGBA")
    cw, ch = meta["cell"]
    cells = [sheet.crop((i * cw, 0, (i + 1) * cw, ch)) for i in range(meta["frames"])]
    M = face_masters(char, facing)
    m_scale, m_pivot = master_geometry(M["base"])
    # heads pitch down a lot while crouching (reach_low) or looking at the hands; PIL angles are counter-clockwise,
    # a right-facing head looking down is a clockwise (negative) rotation
    angles = [float(a) for a in range(-60, 36, 5)]
    scales = [0.94, 1.0, 1.06]
    templates = [make_template(M["base"], M["mask_layer"], m_scale, m_pivot, (cw, ch), angles, scales)]
    end_mask = pose_mask_master(char, pose)
    if end_mask is not None:
        templates.append(make_template(load_rgba(d / "masters" / f"{pose}_aligned.png"), end_mask[1], m_scale,
                                       m_pivot, (cw, ch), angles, scales))
    out, report = overlay_masks(cells[1:-1], templates, search=40)
    edits = MASK_FRAME_EDITS.get(pose, {})
    if edits:
        video = ONESHOT_VIDEOS.get(pose, f"video_{pose}_pro.mp4")
        paths = scratch_frames(char, d / "prod" / video)
        v0 = fr.chroma_key(fr.load_rgb(paths[0]), choke=1)
        _x0, vy0, _x1, vy1 = fr.alpha_bbox(v0)
        v_scale, v_pivot = HEIGHT / (vy1 - vy0), (fr.torso_center_x(v0), float(vy1))
        for i, src in enumerate(meta["source_frames"][1:-1]):
            if src in edits:
                k = fr.chroma_key(fr.load_rgb(paths[src]), choke=1)
                layer = frame_mask_layer(k, fr.load_rgb(d / "prod" / edits[src]))
                merged = Image.fromarray(k, "RGBA")
                merged.alpha_composite(Image.fromarray(layer, "RGBA"))
                out[i] = to_cell(np.asarray(merged), v_scale, v_pivot, (cw, ch))
                report[i] = {"frame": i, "template": "nb2_frame_edit", "source": edits[src]}
    first = Image.fromarray(np.asarray(to_cell(M["mask"], m_scale, m_pivot, (cw, ch))), "RGBA")
    if end_mask is not None:
        last = to_cell(end_mask[0], m_scale, m_pivot, (cw, ch))
    else:
        last, rep = overlay_masks([cells[-1]], templates[:1], search=40)
        last = last[0]
    cells_m = [first] + out + [last]
    mname = name + "_mask2020"
    meta_m = dict(meta, name=mname, mask_overlay=report, source="mask layer tracked onto " + name)
    export(cells_m, d / "anim" / mname, mname, meta_m)
    review_strip(d / "anim" / mname, mname)
    print(mname, [(r["template"], r.get("angle"), r.get("scale")) for r in report])


def stage_walk_mask(char: str, name: str, facing: str) -> None:
    d = char_dir(char)
    src_dir = d / "anim" / name
    meta = json.loads((src_dir / f"{name}_sheet.json").read_text(encoding="utf-8"))
    sheet = Image.open(src_dir / f"{name}_sheet.png").convert("RGBA")
    cw, ch = meta["cell"]
    cells = [sheet.crop((i * cw, 0, (i + 1) * cw, ch)) for i in range(meta["frames"])]
    M = face_masters(char, facing)
    m_scale, _ = master_geometry(M["base"])
    x0, y0, x1, y1 = fr.alpha_bbox(M["base"])
    tmpl, pos = make_template(M["base"], M["mask_layer"], m_scale, (fr.torso_center_x(M["base"]), float(y1)),
                              (cw, ch), [float(a) for a in range(-10, 11, 2)], [0.95, 1.0, 1.05])
    # initial guess: the template sits where the standing head would be relative to the pivot; walk heads bob,
    # so start from the head top of the first cell
    a = np.asarray(cells[0])[..., 3]
    top = int(np.flatnonzero((a > 128).any(axis=1)).min())
    h0, w0 = tmpl.variants[0][2].shape[:2]
    centre = (pos[0] + w0 / 2, pos[1] + h0 / 2 + (top - (meta["pivot"][1] - HEIGHT)))
    out, report = overlay_masks(cells, [(tmpl, pos)], search=24, start_centre=centre)
    mname = name + "_mask2020"
    meta_m = dict(meta, name=mname, mask_overlay=report, source="mask layer tracked onto " + name)
    export(out, d / "anim" / mname, mname, meta_m)
    review_strip(d / "anim" / mname, mname)
    print(mname, [(r["angle"], r["scale"], r["mse"]) for r in report][:6])


# ----------------------------------------------------------------------------- stage: export to the game

ANIMATIONS = [  # (name, facing, mirror_for_left)
    ("idle_right", "right", True), ("idle_front", "front", False), ("idle_back", "back", False),
    ("walk_right", "right", True), ("walk_toward", "front", False), ("walk_away", "back", False),
    ("talk_right", "right", True), ("talk_front", "front", False),
    ("reach_low_right", "right", True), ("reach_mid_right", "right", True), ("reach_high_right", "right", True),
    ("use_tool_right", "right", True), ("show_item_right", "right", True),
    ("inventory_combine_front", "front", False),
]


ITEM_ANCHORS = {"show_item_right": [336, 116]}   # palm of the held-out hand, last frame, cell coordinates


def stage_export(char: str) -> None:
    d = char_dir(char)
    out_dir = REPO / "src" / "game" / "assets" / "actors" / char
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"character": char, "standing_height_px": HEIGHT, "format": "horizontal strip of equal cells",
                "left_facing": "mirror the *_right sheets horizontally (pivot x = cell_w / 2 stays put)",
                "animations": {}}
    for base_name, facing, mirror in ANIMATIONS:
        for name in (base_name, base_name + "_mask2020"):
            src = d / "anim" / name
            meta = json.loads((src / f"{name}_sheet.json").read_text(encoding="utf-8"))
            img = Image.open(src / f"{name}_sheet.png").convert("RGBA")
            img.save(out_dir / f"{name}.webp", "WEBP", lossless=True, quality=100, method=6, exact=False)
            ship = {k: meta[k] for k in ("name", "frames", "cell", "pivot", "playback_fps", "oneshot",
                                         "stride_px_per_s") if k in meta}
            ship.update(image=f"{name}.webp", facing=facing, mirror_for_left=mirror,
                        variant="mask2020" if name.endswith("_mask2020") else "default",
                        standing_height_px=HEIGHT)
            for k in ("mouth_sequence", "blink_frames", "cycle_seconds", "note"):
                if k in meta:
                    ship[k] = meta[k]
            if base_name in ITEM_ANCHORS:
                ship["item_anchor_last_frame"] = ITEM_ANCHORS[base_name]
                ship["item_anchor_note"] = ("cell px where the bottom centre of the shown item sits on the open palm "
                                            "in the last frame (approximate, measured by eye); mirror x for left")
            if base_name in ("walk_toward", "walk_away"):
                # the measured value is sideways foot travel; ground speed in depth depends on the room's perspective
                ship["stride_px_per_s"] = None
                ship["note"] = ("depth walk: move the actor along y at a per-room speed tuned by eye (start with "
                                "~0.25 x the walk_right stride, scaled by the actor scale); feet may reach below the "
                                "pivot (perspective)")
            (out_dir / f"{name}.json").write_text(json.dumps(ship, indent=2), encoding="utf-8")
            manifest["animations"][name] = {k: ship[k] for k in ("image", "facing", "frames", "cell", "pivot",
                                                                  "playback_fps", "oneshot", "mirror_for_left",
                                                                  "variant", "stride_px_per_s")}
            print(f"{name:34s} {img.size[0]:5d}x{img.size[1]:<4d} {(out_dir / (name + '.webp')).stat().st_size // 1024:5d} KB")
    (out_dir / "animations.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--char", default="ADAM")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prep")
    p = sub.add_parser("canvases")
    p.add_argument("pose")
    p = sub.add_parser("walk")
    p.add_argument("name")
    p.add_argument("video")
    p.add_argument("--frames", type=int, default=16)
    p.add_argument("--period", default="0.8,1.6")
    p.add_argument("--fixed-baseline", action="store_true", help="toward/away walks (perspective feet)")
    for cmd in ("idle", "talk"):
        p = sub.add_parser(cmd)
        p.add_argument("facing", choices=["side", "front", "back"])
        p.add_argument("--mask", action="store_true", help="2020 face-mask variant")
    p = sub.add_parser("oneshot")
    p.add_argument("pose", choices=list(KEY_POSES))
    p.add_argument("--span", help="first,last source frames to sample from (default: whole video)")
    p.add_argument("--mask", action="store_true", help="build the 2020 mask variant of an existing one-shot")
    p = sub.add_parser("walkmask")
    p.add_argument("name")
    p.add_argument("facing", choices=["side", "front", "back"])
    sub.add_parser("export")
    args = parser.parse_args()
    if args.cmd == "idle":
        stage_idle(args.char, args.facing, args.mask)
    elif args.cmd == "talk":
        stage_talk(args.char, args.facing, args.mask)
    elif args.cmd == "oneshot":
        if args.mask:
            stage_oneshot_mask(args.char, args.pose)
        else:
            stage_oneshot(args.char, args.pose, tuple(int(v) for v in args.span.split(",")) if args.span else None)
    elif args.cmd == "walkmask":
        stage_walk_mask(args.char, args.name, args.facing)
    elif args.cmd == "export":
        stage_export(args.char)
    elif args.cmd == "prep":
        stage_prep(args.char)
    elif args.cmd == "canvases":
        stage_canvases(args.char, args.pose)
    elif args.cmd == "walk":
        lo, hi = (float(v) for v in args.period.split(","))
        stage_walk(args.char, args.name, args.video, args.frames, (lo, hi), args.fixed_baseline)


if __name__ == "__main__":
    main()
