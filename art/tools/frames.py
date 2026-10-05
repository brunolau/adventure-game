"""Local (free) sprite processing for LastBell characters: chroma key (green/magenta/blue), view splitting, video frame extraction,
loop detection, feet-baseline alignment, spritesheets and GIF previews.

Subcommands:
  key      IN.png OUT.png                 key a flat-key image to transparent PNG (cropped to the figure)
  split    IN.png OUTDIR --names a,b,c    key a multi-view sheet and save each figure separately
  canvas   IN_KEYED.png OUT.png           place a keyed figure on a flat key-colour canvas (video model input);
                                          with --anchor RAW, src is a raw sheet placed with the anchor's transform
  extract  VIDEO.mp4 OUTDIR               dump all frames of a video (ffmpeg from imageio-ffmpeg)
  loop     FRAMEDIR OUTDIR                key frames, find the cleanest loop, align to the feet baseline,
                                          write frames, spritesheet (+ JSON) and a GIF preview
  preview  OUT.jpg IMG [IMG ...]         contact sheet of keyed sprites on a background, for review
  patch    BASE.png EDIT.png OUT.png      transplant only the changed head band of a pose edit onto the base
                                          (talk / blink frames without whole-body flicker)
  overlay  BASE.png EDIT.png FRAMES...    transplant a head edit (e.g. the 2020 face mask) onto animation frames
  stills   OUTDIR --base RAW --frame ...  edit-based pose set (idle/blink/talk/gesture) on one shared pivot
  sheet    OUTDIR FRAMES... --name --fps  spritesheet + GIF from already aligned cells (e.g. overlay output)

Keying model: 'keyness' (green: G - max(R, B); magenta: min(R, B) - G; blue: B - max(R, G)), with the key
colour taken from the image border. The flat background has keyness ~ 250, the character < 0 almost
everywhere. Alpha is linear in keyness, edge colours are un-mixed from the key colour, residual spill is
removed and specks are dropped by connected-component filtering. Use magenta for characters wearing green.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ART = Path(__file__).resolve().parent.parent
PREVIEW_BG = ART / "backgrounds" / "tram-stop.png"
KEY_RGB = (0, 255, 0)
KEY_COLOURS = {"green": KEY_RGB, "magenta": (255, 0, 255)}


# ----------------------------------------------------------------------------- keying

def keyness(rgbf: np.ndarray, kind: str) -> np.ndarray:
    """How strongly each pixel looks like the key: green G-max(R,B), magenta min(R,B)-G, blue B-max(R,G)."""
    r, g, b = rgbf[..., 0], rgbf[..., 1], rgbf[..., 2]
    if kind == "green":
        return g - np.maximum(r, b)
    if kind == "magenta":
        return np.minimum(r, b) - g
    return b - np.maximum(r, g)


def key_kind(key: np.ndarray) -> str:
    r, g, b = key
    if g > max(r, b):
        return "green"
    if min(r, b) > g + 64:  # a margin: video blue (2, 1, 249) has R > G and must not read as magenta
        return "magenta"
    return "blue"


def edge_despill(rgba: np.ndarray, width: int = 8) -> np.ndarray:
    """Remove the yellow-green cast that 4:2:0 video chroma leaves on thin parts near the matte edge (fingers).

    Plain despill clamps G to max(R, B), which turns green-tinted skin yellow. Within `width` px of transparency,
    pixels where G is (still) the top channel or that read olive (G > 0.88 R and G > B + 20) get G capped at
    (R + B) / 2 + 8. Skin (G ~0.73 R) and the mustard T-shirt (G ~0.8 R) are untouched; neutral greys are
    unchanged by the cap.
    """
    out = rgba.copy()
    clear = Image.fromarray(((rgba[..., 3] < 250) * 255).astype(np.uint8), "L")
    near = np.asarray(clear.filter(ImageFilter.MaxFilter(2 * width + 1))) > 0
    rgb = out[..., :3].astype(np.float32)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    olive = (g > 0.88 * r) & (g > b + 20)          # yellow-green / olive cast; skin ~0.73 R, mustard ~0.8 R
    zone = near & ((g >= np.maximum(r, b) - 3) | olive) & (rgba[..., 3] > 0)
    cap = (rgb[..., 0] + rgb[..., 2]) / 2 + 8
    g = np.where(zone, np.minimum(rgb[..., 1], cap), rgb[..., 1])
    out[..., 1] = g.clip(0, 255).astype(np.uint8)
    return out


def chroma_key(rgb: np.ndarray, lo: float | None = None, hi: float | None = None, despill: bool = True,
               min_island: int = 400, choke: int = 0, edge_fix: bool | None = None) -> np.ndarray:
    """Return an RGBA uint8 array with the flat key background (green, magenta or blue) made transparent.

    The key colour K is the median of the image border and decides the key kind. Alpha is linear in
    'keyness' between the foreground level (lo, default 0) and the background level (hi, default 85 % of K's
    keyness, which absorbs video compression noise). Edge pixels are un-mixed, F = (C - (1 - a) K) / a, so they
    keep the figure's own colour instead of a coloured fringe; residual spill is removed from the key channels.
    choke > 0 erodes the matte by that many pixels (video frames: 4:2:0 chroma bleeds the key into the edge).
    edge_fix (default: on when choke > 0, i.e. for video frames; green key only) applies edge_despill.
    """
    rgbf = rgb.astype(np.float32)
    h, w = rgbf.shape[:2]
    border = np.concatenate([rgbf[:4].reshape(-1, 3), rgbf[-4:].reshape(-1, 3),
                             rgbf[:, :4].reshape(-1, 3), rgbf[:, -4:].reshape(-1, 3)])
    key = np.median(border, axis=0)
    kind = key_kind(key)
    key_level = float(keyness(key[None, None, :], kind)[0, 0])
    lo = 0.0 if lo is None else lo
    hi = key_level * 0.85 if hi is None else hi
    level = keyness(rgbf, kind)
    alpha = np.clip((hi - level) / (hi - lo), 0.0, 1.0)
    alpha[alpha < 0.08] = 0.0
    # Interior protection: only pixels within `edge_px` of clear background may be semi-transparent.
    # Video models paint key-coloured bounce light onto occluded limbs; without this those turn see-through.
    edge_px = max(2, round(min(h, w) / 400))
    clear_bg = Image.fromarray(((level > key_level * 0.6) * 255).astype(np.uint8), "L")
    near_bg = np.asarray(clear_bg.filter(ImageFilter.MaxFilter(2 * edge_px + 1))) > 0
    alpha = np.where(near_bg, alpha, 1.0)
    a = alpha[..., None]
    with np.errstate(divide="ignore", invalid="ignore"):
        unmixed = np.where(a > 0.05, (rgbf - (1.0 - a) * key) / np.maximum(a, 0.05), rgbf)
    unmixed = unmixed.clip(0, 255)
    if despill:
        spill = np.maximum(keyness(unmixed, kind), 0)
        for channel in {"green": [1], "magenta": [0, 2], "blue": [2]}[kind]:
            unmixed[..., channel] -= spill
    r, g, b = unmixed[..., 0], unmixed[..., 1], unmixed[..., 2]
    if choke:
        # erode by `choke` px, then soften so the new edge stays anti-aliased
        matte = Image.fromarray((alpha * 255).astype(np.uint8), "L").filter(ImageFilter.MinFilter(2 * choke + 1))
        matte = matte.filter(ImageFilter.GaussianBlur(0.7))
        alpha = np.minimum(alpha, np.asarray(matte, dtype=np.float32) / 255)
    out = np.dstack([r, g, b, alpha * 255.0]).clip(0, 255).astype(np.uint8)
    if min_island:
        out[..., 3] = drop_islands(out[..., 3], min_island)
    if kind == "green" and (edge_fix or (edge_fix is None and choke > 0)):
        out = edge_despill(out)   # green key only: a magenta-keyed figure may wear green (ELA's vest)
    return out


def drop_islands(alpha: np.ndarray, min_pixels: int) -> np.ndarray:
    """Zero every connected opaque region smaller than min_pixels (noise, compression specks)."""
    mask = alpha > 24
    labels, sizes = label_components(mask)
    keep = np.zeros(len(sizes) + 1, dtype=bool)
    keep[1:] = sizes >= min_pixels
    return np.where(keep[labels], alpha, 0).astype(np.uint8)


def label_components(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """4-connected component labelling with a union-find over run lengths (numpy only, no scipy)."""
    height, width = mask.shape
    labels = np.zeros((height, width), dtype=np.int32)
    parent = [0]

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    prev_runs: list[tuple[int, int, int]] = []
    for y in range(height):
        row = mask[y]
        if not row.any():
            prev_runs = []
            continue
        padded = np.concatenate([[False], row, [False]])
        edges = np.flatnonzero(padded[1:] != padded[:-1])
        runs = []
        for start, end in zip(edges[::2], edges[1::2]):
            label = 0
            for p_start, p_end, p_label in prev_runs:
                if p_start < end and start < p_end:
                    if label == 0:
                        label = find(p_label)
                    else:
                        a, b = find(label), find(p_label)
                        if a != b:
                            parent[max(a, b)] = min(a, b)
                            label = min(a, b)
            if label == 0:
                label = len(parent)
                parent.append(label)
            labels[y, start:end] = label
            runs.append((start, end, label))
        prev_runs = runs
    roots = np.array([find(i) for i in range(len(parent))], dtype=np.int32)
    labels = roots[labels]
    sizes = np.bincount(labels.ravel(), minlength=len(parent))[1:]
    return labels, sizes


def alpha_bbox(rgba: np.ndarray, threshold: int = 24) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(rgba[..., 3] > threshold)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def crop_to_figure(rgba: np.ndarray, pad: int = 4) -> np.ndarray:
    box = alpha_bbox(rgba)
    if box is None:
        return rgba
    x0, y0, x1, y1 = box
    h, w = rgba.shape[:2]
    return rgba[max(0, y0 - pad):min(h, y1 + pad), max(0, x0 - pad):min(w, x1 + pad)]


def load_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"))


def save_rgba(rgba: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(path, optimize=True)


def key_quality(rgba: np.ndarray) -> dict:
    """Simple numbers for judging a key: share of semi-transparent pixels and residual green in the figure."""
    alpha = rgba[..., 3].astype(np.float32) / 255
    opaque = alpha > 0.9
    semi = (alpha > 0.05) & (alpha < 0.9)
    rgb = rgba[..., :3].astype(np.float32)
    greenish = (rgb[..., 1] - np.maximum(rgb[..., 0], rgb[..., 2])) > 20
    return {"opaque_px": int(opaque.sum()), "edge_px": int(semi.sum()),
            "edge_ratio": round(float(semi.sum() / max(1, opaque.sum())), 4),
            "green_in_figure_px": int((greenish & opaque).sum())}


# ----------------------------------------------------------------------------- multi-view sheets

def split_views(rgba: np.ndarray, count: int) -> list[np.ndarray]:
    """Split a keyed sheet into `count` figures at the widest empty column gaps."""
    occupied = (rgba[..., 3] > 24).any(axis=0)
    padded = np.concatenate([[False], occupied, [False]])
    edges = np.flatnonzero(padded[1:] != padded[:-1])
    spans = [(int(s), int(e)) for s, e in zip(edges[::2], edges[1::2])]
    # merge spans until `count` remain (merge across the narrowest gaps first)
    while len(spans) > count:
        gaps = [spans[i + 1][0] - spans[i][1] for i in range(len(spans) - 1)]
        i = int(np.argmin(gaps))
        spans[i:i + 2] = [(spans[i][0], spans[i + 1][1])]
    return [crop_to_figure(rgba[:, s:e]) for s, e in spans]


# ----------------------------------------------------------------------------- canvases and previews

def figure_on_canvas(rgba: np.ndarray, size: tuple[int, int], height_frac: float, feet_frac: float,
                     color: tuple[int, int, int] = KEY_RGB) -> Image.Image:
    """Scale a keyed figure to height_frac of the canvas and stand it with its feet at feet_frac."""
    fig = Image.fromarray(crop_to_figure(rgba, pad=0), "RGBA")
    width, height = size
    scale = height * height_frac / fig.height
    fig = fig.resize((round(fig.width * scale), round(fig.height * scale)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, color)
    x = (width - fig.width) // 2
    y = round(height * feet_frac) - fig.height
    canvas.paste(fig, (x, y), fig)
    return canvas


def pair_on_canvas(anchor_rgb: np.ndarray, src_rgb: np.ndarray, size: tuple[int, int], height_frac: float,
                   feet_frac: float, color: tuple[int, int, int] = KEY_RGB) -> Image.Image:
    """Place src on a key canvas with the transform that fits the anchor figure (same-size raw sheets).

    Used for first/last-frame videos: both frames must share scale and position or the body jumps.
    """
    anchor = chroma_key(anchor_rgb)
    src = chroma_key(src_rgb)
    x0, y0, x1, y1 = alpha_bbox(anchor)
    width, height = size
    scale = height * height_frac / (y1 - y0)
    img = Image.fromarray(src, "RGBA")
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
    ox = round(width / 2 - (x0 + x1) / 2 * scale)
    oy = round(height * feet_frac - y1 * scale)
    canvas = Image.new("RGB", size, color)
    canvas.paste(img, (ox, oy), img)
    return canvas


def background_crop(size: tuple[int, int]) -> Image.Image:
    """A crop of a real game background (platform area of the tram stop) for in-context previews."""
    bg = Image.open(PREVIEW_BG).convert("RGB")
    bw, bh = bg.size
    box_w = int(bh * 0.55 * size[0] / size[1])
    box = (int(bw * 0.30), int(bh * 0.40), int(bw * 0.30) + box_w, int(bh * 0.95))
    return bg.crop(box).resize(size, Image.Resampling.LANCZOS)


def contact_sheet(images: list[Image.Image], out: Path, cell_h: int = 640, labels: list[str] | None = None) -> None:
    cells = []
    for index, img in enumerate(images):
        scale = cell_h / img.height
        img = img.resize((max(1, round(img.width * scale)), cell_h), Image.Resampling.LANCZOS)
        cell_w = img.width + 40
        cell = background_crop((cell_w, cell_h + 40))
        cell.paste(img, (20, 20), img if img.mode == "RGBA" else None)
        if labels:
            ImageDraw.Draw(cell).text((8, 6), labels[index], fill=(255, 255, 255))
        cells.append(cell)
    sheet = Image.new("RGB", (sum(c.width for c in cells), cells[0].height), (40, 40, 40))
    x = 0
    for cell in cells:
        sheet.paste(cell, (x, 0))
        x += cell.width
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=88)


# ----------------------------------------------------------------------------- video frames and loops

def ffmpeg_exe() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def video_info(video: Path) -> dict:
    """fps and size via ffmpeg's stderr banner (ffprobe is not bundled with imageio-ffmpeg)."""
    proc = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(video)], capture_output=True, text=True)
    import re
    match = re.search(r"Video:.*?(\d{2,5})x(\d{2,5}).*?([\d.]+) fps", proc.stderr)
    duration = re.search(r"Duration: (\d+):(\d+):([\d.]+)", proc.stderr)
    info = {"raw": proc.stderr.strip().splitlines()[-3:]}
    if match:
        info.update(width=int(match.group(1)), height=int(match.group(2)), fps=float(match.group(3)))
    if duration:
        h, m, s = duration.groups()
        info["seconds"] = int(h) * 3600 + int(m) * 60 + float(s)
    return info


def extract_frames(video: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("f_*.png"):
        old.unlink()
    subprocess.run([ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-i", str(video), "-vsync", "0",
                    str(out_dir / "f_%04d.png")], check=True)
    return sorted(out_dir.glob("f_*.png"))


def silhouette(rgba: np.ndarray, size: int = 96) -> np.ndarray:
    """Downscaled alpha * luminance signature used to compare poses between frames."""
    img = Image.fromarray(rgba, "RGBA")
    lum = np.asarray(img.convert("L").resize((size, size), Image.Resampling.BILINEAR), dtype=np.float32) / 255
    alpha = np.asarray(img.getchannel("A").resize((size, size), Image.Resampling.BILINEAR), dtype=np.float32) / 255
    return np.concatenate([alpha.ravel(), (lum * alpha).ravel() * 0.5])


def torso_center_x(rgba: np.ndarray) -> float:
    """x centroid of the head+torso band (top 15-45 % of the figure), stable while the legs swing."""
    box = alpha_bbox(rgba)
    x0, y0, x1, y1 = box
    height = y1 - y0
    band = rgba[y0 + int(height * 0.15): y0 + int(height * 0.45), :, 3].astype(np.float32)
    cols = band.sum(axis=0)
    return float((cols * np.arange(len(cols))).sum() / max(1.0, cols.sum()))


def find_loop(signatures: list[np.ndarray], min_period: int, max_period: int, skip_start: int,
              skip_end: int) -> tuple[int, int, float]:
    """Return (start, period, error) of the most self-similar cycle inside the usable frame range."""
    n = len(signatures)
    sig = np.stack(signatures)
    best = (0, min_period, float("inf"))
    for period in range(min_period, max_period + 1):
        for start in range(skip_start, n - skip_end - period):
            # closure error: frame start vs frame start+period, plus neighbours for robustness
            err = float(np.mean([np.abs(sig[start + k] - sig[start + period + k]).mean()
                                 for k in (0, 1) if start + period + k < n]))
            # mild preference for the dominant cycle rather than tiny partial periods
            if err < best[2]:
                best = (start, period, err)
    return best


def build_loop(frame_paths: list[Path], out_dir: Path, fps: float, frames_out: int, period_s: tuple[float, float],
               skip_start_s: float, skip_end_s: float, recenter: bool, target_height: int, lo: float, hi: float,
               name: str, choke: int = 1, frame_range: tuple[int, int] | None = None, oneshot: bool = False,
               playback_fps: float | None = None, ref_height: float | None = None,
               fixed_baseline: float | None = None) -> dict:
    """Key, select, align and export one animation.

    Loop mode (default): find the most self-similar cycle and sample `frames_out` frames over it.
    frame_range=(a, b): use source frames a..b instead of searching (e.g. a whole start=end idle clip).
    oneshot: include both ends of the range (non-looping actions such as reach; play reversed to return).
    ref_height: source-pixel height that maps to target_height (e.g. the standing first frame), so every
    animation of a character shares one scale; default is the median height of the chosen frames.
    fixed_baseline: source y of the feet line used for every frame instead of each frame's lowest pixel. Use it
    for toward/away walks: in perspective the near foot reaches below the standing feet line, and per-frame
    alignment of the lowest pixel would bob the whole body. The cell then extends below the pivot.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    if frame_range:
        start, period, err = frame_range[0], frame_range[1] - frame_range[0], 0.0
        frame_paths = frame_paths[:frame_range[1] + 1]
    keyed = [chroma_key(load_rgb(p), lo=lo, hi=hi, choke=choke) for p in frame_paths]
    if not frame_range:
        sigs = [silhouette(crop_to_figure(k, pad=0)) for k in keyed]
        start, period, err = find_loop(sigs, max(4, int(period_s[0] * fps)), int(period_s[1] * fps),
                                       int(skip_start_s * fps), int(skip_end_s * fps))
    if oneshot:
        picks = [start + round(i * period / (frames_out - 1)) for i in range(frames_out)]
    else:  # loop: the frame at start + period equals the first one, so it is not repeated
        picks = [start + round(i * period / frames_out) for i in range(frames_out)]
    chosen = [keyed[i] for i in picks]

    # common geometry: feet baseline = lowest opaque row; horizontal anchor = torso centre (walk in place)
    boxes = [alpha_bbox(k) for k in chosen]
    bottoms = [fixed_baseline if fixed_baseline is not None else b[3] for b in boxes]
    centers = [torso_center_x(k) if recenter else (chosen[0].shape[1] / 2) for k in chosen]
    heights = [b[3] - b[1] for b in boxes]
    ref_height = float(ref_height or np.median(heights))
    scale = target_height / ref_height if target_height else 1.0
    # the anchor sits at cell_w / 2, so the cell must be symmetric around it (left + right clipped one side)
    half = max(max(c - b[0] for c, b in zip(centers, boxes)), max(b[2] - c for c, b in zip(centers, boxes)))
    top = max(bot - b[1] for bot, b in zip(bottoms, boxes))
    below = int(np.ceil(max(0.0, max(b[3] - bot for bot, b in zip(bottoms, boxes))) * scale))
    cell_w, cell_h = 2 * int(np.ceil(half * scale)) + 8, int(np.ceil(top * scale)) + 8 + below
    pivot_y = cell_h - 4 - below
    cells: list[Image.Image] = []
    for k, cx, bot in zip(chosen, centers, bottoms):
        img = Image.fromarray(k, "RGBA")
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
        cell = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
        ox = round(cell_w / 2 - cx * scale)
        oy = round(pivot_y - bot * scale)
        cell.paste(img, (ox, oy), img)
        cells.append(cell)

    # stride estimate: lowest-foot x travel per frame (for the engine's walk speed, avoids foot sliding)
    playback_fps = playback_fps or frames_out / (period / fps)
    meta = {"name": name, "frames": len(cells), "cell": [cell_w, cell_h], "pivot": [cell_w // 2, pivot_y],
            "source_frames": picks, "source_fps": fps, "cycle_frames": period, "cycle_seconds": round(period / fps, 3),
            "playback_fps": round(playback_fps, 2), "loop_error": round(err, 4), "scale": round(scale, 4),
            "recentered": recenter, "oneshot": oneshot, "height_px_median": round(ref_height * scale, 1),
            "height_px_range": [round(min(heights) * scale, 1), round(max(heights) * scale, 1)],
            "baseline_from_feet": fixed_baseline is None}
    meta["stride_px_per_s"] = stride_speed(chosen, centers, scale, playback_fps)
    export_cells(cells, out_dir, name, meta, [f"{i} (src {p})" for i, p in enumerate(picks)])
    return meta


def export_cells(cells: list[Image.Image], out_dir: Path, name: str, meta: dict, labels: list[str],
                 gif_sequence: list[tuple[int, int]] | None = None, names: list[str] | None = None) -> None:
    """Write numbered (or named) frame PNGs, a horizontal spritesheet + JSON, a GIF preview on a real game
    background and a contact sheet. gif_sequence = [(cell index, milliseconds), ...] overrides plain playback."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cell_w, cell_h = cells[0].size
    for old in out_dir.glob(f"{name}_*.png"):
        old.unlink()
    for i, cell in enumerate(cells):
        suffix = names[i] if names else f"{i:02d}"
        cell.save(out_dir / f"{name}_{suffix}.png", optimize=True)
    sheet = Image.new("RGBA", (cell_w * len(cells), cell_h), (0, 0, 0, 0))
    for i, cell in enumerate(cells):
        sheet.paste(cell, (i * cell_w, 0))
    sheet.save(out_dir / f"{name}_sheet.png", optimize=True)
    (out_dir / f"{name}_sheet.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    # GIF preview on a real game background (GIF has 1-bit alpha, so composite instead)
    sequence = gif_sequence or [(i, round(1000 / meta["playback_fps"])) for i in range(len(cells))]
    bg = background_crop((cell_w, cell_h))
    gif_frames, durations = [], []
    for index, ms in sequence:
        frame = bg.copy().convert("RGBA")
        frame.alpha_composite(cells[index])
        gif_frames.append(frame.convert("RGB").quantize(colors=255, method=Image.Quantize.MEDIANCUT))
        durations.append(ms)
    gif_frames[0].save(out_dir / f"{name}_preview.gif", save_all=True, append_images=gif_frames[1:],
                       duration=durations, loop=0, disposal=2)
    contact_sheet(cells, out_dir / f"{name}_contact.jpg", cell_h=min(cell_h, 480), labels=labels)


def build_stills(entries: list[tuple[str, str, Path]], base: Path, out_dir: Path, name: str, target_height: int,
                 region: tuple[float, float], gif_sequence: list[tuple[int, int]] | None) -> dict:
    """Edit-based pose set (idle / blink / talk / gesture ...) on one shared pivot.

    entries = [(label, mode, raw sheet)]: mode 'key' keys the edited sheet as is (body poses), 'patch'
    transplants only its changed head band onto the base (blink, mouth shapes, face mask).
    All sheets share the base's canvas; each is aligned to the base by phase correlation.
    """
    base_rgb = load_rgb(base)
    base_key = chroma_key(base_rgb)
    layers = []
    for _label, mode, path in entries:
        rgb = load_rgb(path)
        if rgb.shape != base_rgb.shape:
            rgb = np.asarray(Image.fromarray(rgb).resize(base_rgb.shape[1::-1], Image.Resampling.LANCZOS))
        if mode == "patch":
            rgba, _ = patch_pose(base_rgb, rgb, region)
        else:
            rgba = chroma_key(rgb)
            dy, dx = phase_shift(base_key[..., 3].astype(np.float32), rgba[..., 3].astype(np.float32))
            rgba = np.roll(rgba, (dy, dx), axis=(0, 1))
        layers.append(rgba)
    _bx0, by0, _bx1, by1 = alpha_bbox(base_key)
    scale = target_height / (by1 - by0)
    pivot_x = torso_center_x(base_key)
    boxes = [alpha_bbox(layer) for layer in layers]
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
    labels = [label for label, _, _ in entries]
    meta = {"name": name, "frames": labels, "cell": [cell_w, cell_h], "pivot": [cell_w // 2, cell_h - 4],
            "scale": round(scale, 4), "height_px": target_height, "playback_fps": 8,
            "sources": [f"{mode}:{path.name}" for _, mode, path in entries]}
    export_cells(cells, out_dir, name, meta, labels, gif_sequence, names=labels)
    return meta


def stride_speed(frames: list[np.ndarray], centers: list[float], scale: float, playback_fps: float) -> float | None:
    """Median horizontal speed (px/s, after scaling) of the lowest foot relative to the torso."""
    xs = []
    for k, c in zip(frames, centers):
        box = alpha_bbox(k)
        rows = k[box[3] - max(3, (box[3] - box[1]) // 40): box[3], :, 3] > 128
        cols = np.flatnonzero(rows.any(axis=0))
        if len(cols) == 0:
            return None
        xs.append((cols.mean() - c) * scale)
    deltas = np.abs(np.diff(xs))
    deltas = deltas[deltas < np.percentile(deltas, 75) * 1.5] if len(deltas) > 3 else deltas
    return round(float(np.median(deltas) * playback_fps), 1) if len(deltas) else None


# ----------------------------------------------------------------------------- pose patches (talk / blink)

def phase_shift(a: np.ndarray, b: np.ndarray) -> tuple[int, int]:
    """Integer (dy, dx) that best aligns b onto a, by phase correlation."""
    fa, fb = np.fft.fft2(a), np.fft.fft2(b)
    cross = fa * np.conj(fb)
    cross /= np.abs(cross) + 1e-9
    corr = np.fft.ifft2(cross).real
    dy, dx = np.unravel_index(int(np.argmax(corr)), corr.shape)
    h, w = a.shape
    return (dy - h if dy > h // 2 else dy), (dx - w if dx > w // 2 else dx)


def patch_pose(base_rgb: np.ndarray, edit_rgb: np.ndarray, region: tuple[float, float], feather: int = 12,
               threshold: float = 18.0) -> tuple[np.ndarray, dict]:
    """Transplant the changed pixels of `edit` inside a vertical band of the figure onto `base`.

    region = (top, bottom) as fractions of the base figure's height (e.g. (0.0, 0.17) for the head).
    Returns the keyed RGBA result and a report: alignment shift, scale ratio and how much the editor changed
    outside the region (a proxy for the flicker a whole-frame swap would cause).
    """
    if edit_rgb.shape != base_rgb.shape:  # cheaper low-res edit (e.g. 1K) of a 2K base
        edit_rgb = np.asarray(Image.fromarray(edit_rgb).resize(base_rgb.shape[1::-1], Image.Resampling.LANCZOS))
    base_key = chroma_key(base_rgb)
    edit_key = chroma_key(edit_rgb)
    dy, dx = phase_shift(base_key[..., 3].astype(np.float32), edit_key[..., 3].astype(np.float32))
    edit_rgb = np.roll(edit_rgb, (dy, dx), axis=(0, 1))
    edit_key = np.roll(edit_key, (dy, dx), axis=(0, 1))
    bx0, by0, bx1, by1 = alpha_bbox(base_key)
    ex0, ey0, ex1, ey1 = alpha_bbox(edit_key)
    height = by1 - by0
    band = np.zeros(base_rgb.shape[:2], dtype=bool)
    band[by0 + int(region[0] * height): by0 + int(region[1] * height), :] = True
    diff = np.abs(base_rgb.astype(np.float32) - edit_rgb.astype(np.float32)).mean(axis=2)
    figure = (base_key[..., 3] > 128) | (edit_key[..., 3] > 128)
    changed = (diff > threshold) & band & figure
    mask = Image.fromarray((changed * 255).astype(np.uint8), "L")
    mask = mask.filter(ImageFilter.MaxFilter(4 * (feather // 2) + 1)).filter(ImageFilter.GaussianBlur(feather))
    m = (np.asarray(mask, dtype=np.float32) / 255.0) * band
    # blend keyed layers in premultiplied space so background green never mixes into the figure
    ab = base_key[..., 3:4].astype(np.float32) / 255
    ae = edit_key[..., 3:4].astype(np.float32) / 255
    mm = m[..., None]
    alpha = ab * (1 - mm) + ae * mm
    premul = base_key[..., :3] * ab * (1 - mm) + edit_key[..., :3] * ae * mm
    with np.errstate(divide="ignore", invalid="ignore"):
        rgb = np.where(alpha > 1e-3, premul / np.maximum(alpha, 1e-3), 0)
    merged = np.dstack([rgb, alpha * 255]).clip(0, 255).astype(np.uint8)
    outside = figure & ~band
    report = {"shift_dy_dx": [int(dy), int(dx)], "height_ratio": round((ey1 - ey0) / height, 4),
              "changed_px_in_region": int(changed.sum()),
              "mean_abs_diff_outside_region": round(float(diff[outside].mean()), 2) if outside.any() else None,
              "share_changed_outside_region": round(float((diff[outside] > threshold).mean()), 4)
              if outside.any() else None}
    return merged, report


def head_overlay(base_rgb: np.ndarray, edit_rgb: np.ndarray, region: tuple[float, float],
                 threshold: float = 18.0, feather: int = 8) -> tuple[np.ndarray, np.ndarray]:
    """Cut the changed part of a head edit (face mask, glasses, ...) as an RGBA layer, plus the base head crop.

    Both are cropped to the head band of the base figure; the base crop is used to align the layer onto frames.
    """
    base_key = chroma_key(base_rgb)
    edit_key = chroma_key(edit_rgb)
    dy, dx = phase_shift(base_key[..., 3].astype(np.float32), edit_key[..., 3].astype(np.float32))
    edit_rgb = np.roll(edit_rgb, (dy, dx), axis=(0, 1))
    edit_key = np.roll(edit_key, (dy, dx), axis=(0, 1))
    x0, y0, x1, y1 = alpha_bbox(base_key)
    height = y1 - y0
    top, bottom = y0 + int(region[0] * height), y0 + int(region[1] * height)
    diff = np.abs(base_rgb.astype(np.float32) - edit_rgb.astype(np.float32)).mean(axis=2)
    changed = (diff > threshold) & ((base_key[..., 3] > 128) | (edit_key[..., 3] > 128))
    changed[:top] = False
    changed[bottom:] = False
    mask = Image.fromarray((changed * 255).astype(np.uint8), "L")
    mask = mask.filter(ImageFilter.MaxFilter(2 * feather + 1)).filter(ImageFilter.GaussianBlur(feather / 2))
    m = np.asarray(mask, dtype=np.float32) / 255
    layer = edit_key.copy()
    layer[..., 3] = (layer[..., 3].astype(np.float32) * m).astype(np.uint8)
    box = (slice(top, bottom), slice(x0, x1))
    return layer[box], base_key[box]


def apply_head_overlay(frame: np.ndarray, layer: np.ndarray, base_head: np.ndarray, base_height: float,
                       frame_height: float, search: int = 8) -> tuple[np.ndarray, tuple[int, int]]:
    """Scale the layer to the frame, align base_head to the frame's head (top + front-most point), composite."""
    scale = frame_height / base_height
    size = (max(1, round(layer.shape[1] * scale)), max(1, round(layer.shape[0] * scale)))
    layer_img = Image.fromarray(layer, "RGBA").resize(size, Image.Resampling.LANCZOS)
    head_a = np.asarray(Image.fromarray(base_head[..., 3]).resize(size, Image.Resampling.BILINEAR), np.float32)
    fa = frame[..., 3].astype(np.float32)
    fx0, fy0, fx1, fy1 = alpha_bbox(frame)
    band = fa[fy0:fy0 + size[1]] > 128
    hb = head_a > 128
    # initial guess: same head top, same front-most (right-most) x in the head band
    front_frame = int(np.flatnonzero(band.any(axis=0)).max())
    front_head = int(np.flatnonzero(hb.any(axis=0)).max())
    gx, gy = front_frame - front_head, fy0
    best, best_xy = -1.0, (gx, gy)
    for oy in range(-search, search + 1):
        for ox in range(-search, search + 1):
            x, y = gx + ox, gy + oy
            if x < 0 or y < 0 or x + size[0] > fa.shape[1] or y + size[1] > fa.shape[0]:
                continue
            region = fa[y:y + size[1], x:x + size[0]] > 128
            score = float((region & hb).sum()) / max(1, float((region | hb).sum()))  # IoU
            if score > best:
                best, best_xy = score, (x, y)
    out = Image.fromarray(frame, "RGBA")
    out.alpha_composite(layer_img, best_xy)
    return np.asarray(out), best_xy


# ----------------------------------------------------------------------------- CLI

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("key")
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--lo", type=float, default=None)
    p.add_argument("--hi", type=float, default=None)

    p = sub.add_parser("split")
    p.add_argument("src")
    p.add_argument("out_dir")
    p.add_argument("--names", required=True, help="comma-separated view names, left to right")
    p.add_argument("--prefix", default="view_")

    p = sub.add_parser("canvas")
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--size", default="1024x1024")
    p.add_argument("--height", type=float, default=0.80)
    p.add_argument("--feet", type=float, default=0.90)
    p.add_argument("--anchor", help="raw sheet whose figure defines the transform (src must be a raw sheet too)")
    p.add_argument("--key", choices=KEY_COLOURS, default="green", help="canvas colour (magenta for green clothes)")

    p = sub.add_parser("extract")
    p.add_argument("video")
    p.add_argument("out_dir")

    p = sub.add_parser("loop")
    p.add_argument("frame_dir")
    p.add_argument("out_dir")
    p.add_argument("--name", default="walk_right")
    p.add_argument("--fps", type=float, required=True)
    p.add_argument("--frames", type=int, default=10)
    p.add_argument("--period", default="0.8,1.5", help="min,max cycle length in seconds")
    p.add_argument("--skip-start", type=float, default=0.5)
    p.add_argument("--skip-end", type=float, default=0.2)
    p.add_argument("--no-recenter", action="store_true")
    p.add_argument("--height", type=int, default=512, help="target figure height in px (0 = keep)")
    p.add_argument("--choke", type=int, default=1, help="matte erosion in source px (video chroma bleed)")
    p.add_argument("--range", help="a,b: use source frames a..b instead of searching for a loop")
    p.add_argument("--oneshot", action="store_true", help="non-looping action: include both range ends")
    p.add_argument("--playback-fps", type=float, help="override the playback rate (default: real time)")
    p.add_argument("--lo", type=float, default=None)
    p.add_argument("--hi", type=float, default=None)

    p = sub.add_parser("patch")
    p.add_argument("base")
    p.add_argument("edit")
    p.add_argument("dst")
    p.add_argument("--region", default="0.0,0.17", help="top,bottom band as fractions of the figure height")
    p.add_argument("--crop-like", help="crop to the same box as this keyed base crop (keeps frames aligned)")

    p = sub.add_parser("overlay")
    p.add_argument("base")
    p.add_argument("edit")
    p.add_argument("frames", nargs="+", help="keyed frames (e.g. walk_right_??.png)")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--suffix", default="_mask2020")
    p.add_argument("--region", default="0.0,0.17")

    p = sub.add_parser("stills")
    p.add_argument("out_dir")
    p.add_argument("--name", default="npc_set")
    p.add_argument("--base", required=True, help="raw base sheet (the idle pose)")
    p.add_argument("--frame", action="append", required=True,
                   help="label=[patch:]raw_sheet.png, in order; list the base itself as e.g. idle=BASE")
    p.add_argument("--height", type=int, default=512)
    p.add_argument("--region", default="0.0,0.17")
    p.add_argument("--gif", help="preview sequence 'index:ms,index:ms,...'")

    p = sub.add_parser("sheet")
    p.add_argument("out_dir")
    p.add_argument("frames", nargs="+", help="already aligned cells of equal size")
    p.add_argument("--name", required=True)
    p.add_argument("--fps", type=float, required=True)

    p = sub.add_parser("preview")
    p.add_argument("dst")
    p.add_argument("images", nargs="+")
    p.add_argument("--cell-height", type=int, default=640)

    args = parser.parse_args()
    if args.cmd == "key":
        rgba = crop_to_figure(chroma_key(load_rgb(Path(args.src)), lo=args.lo, hi=args.hi))
        save_rgba(rgba, Path(args.dst))
        print(args.dst, rgba.shape[1::-1], key_quality(rgba))
    elif args.cmd == "split":
        names = args.names.split(",")
        views = split_views(chroma_key(load_rgb(Path(args.src))), len(names))
        for view_name, rgba in zip(names, views):
            dst = Path(args.out_dir) / f"{args.prefix}{view_name}.png"
            save_rgba(rgba, dst)
            print(dst, rgba.shape[1::-1], key_quality(rgba))
    elif args.cmd == "canvas":
        size = tuple(int(v) for v in args.size.split("x"))
        color = KEY_COLOURS[args.key]
        if args.anchor:
            pair_on_canvas(load_rgb(Path(args.anchor)), load_rgb(Path(args.src)), size, args.height,
                           args.feet, color).save(args.dst)
        else:
            rgba = np.asarray(Image.open(args.src).convert("RGBA"))
            figure_on_canvas(rgba, size, args.height, args.feet, color).save(args.dst)
        print(args.dst, size)
    elif args.cmd == "extract":
        info = video_info(Path(args.video))
        frames = extract_frames(Path(args.video), Path(args.out_dir))
        print(json.dumps({k: v for k, v in info.items() if k != "raw"}), len(frames), "frames")
    elif args.cmd == "loop":
        frames = sorted(Path(args.frame_dir).glob("f_*.png"))
        lo_s, hi_s = (float(v) for v in args.period.split(","))
        meta = build_loop(frames, Path(args.out_dir), args.fps, args.frames, (lo_s, hi_s), args.skip_start,
                          args.skip_end, not args.no_recenter, args.height, args.lo, args.hi, args.name,
                          args.choke, tuple(int(v) for v in args.range.split(",")) if args.range else None,
                          args.oneshot, args.playback_fps)
        print(json.dumps(meta, indent=1))
    elif args.cmd == "patch":
        top, bottom = (float(v) for v in args.region.split(","))
        rgba, report = patch_pose(load_rgb(Path(args.base)), load_rgb(Path(args.edit)), (top, bottom))
        box = alpha_bbox(chroma_key(load_rgb(Path(args.base))))
        pad = 4
        rgba = rgba[max(0, box[1] - pad):box[3] + pad, max(0, box[0] - pad):box[2] + pad]
        save_rgba(rgba, Path(args.dst))
        print(args.dst, json.dumps(report))
    elif args.cmd == "overlay":
        top, bottom = (float(v) for v in args.region.split(","))
        layer, base_head = head_overlay(load_rgb(Path(args.base)), load_rgb(Path(args.edit)), (top, bottom))
        bx0, by0, bx1, by1 = alpha_bbox(chroma_key(load_rgb(Path(args.base))))
        frames = [np.asarray(Image.open(f).convert("RGBA")) for f in args.frames]
        heights = [alpha_bbox(f)[3] - alpha_bbox(f)[1] for f in frames]
        frame_height = float(np.median(heights))
        out_dir = Path(args.out_dir)
        for path, frame in zip(args.frames, frames):
            result, xy = apply_head_overlay(frame, layer, base_head, by1 - by0, frame_height)
            dst = out_dir / (Path(path).stem + args.suffix + ".png")
            save_rgba(result, dst)
            print(dst.name, xy)
    elif args.cmd == "stills":
        entries = []
        for spec in args.frame:
            label, source = spec.split("=", 1)
            mode, path = ("patch", source[len("patch:"):]) if source.startswith("patch:") else ("key", source)
            entries.append((label, mode, Path(path)))
        top, bottom = (float(v) for v in args.region.split(","))
        sequence = [tuple(int(v) for v in item.split(":")) for item in args.gif.split(",")] if args.gif else None
        meta = build_stills(entries, Path(args.base), Path(args.out_dir), args.name, args.height, (top, bottom),
                            sequence)
        print(json.dumps(meta, indent=1))
    elif args.cmd == "sheet":
        cells = [Image.open(f).convert("RGBA") for f in args.frames]
        meta = {"name": args.name, "frames": len(cells), "cell": list(cells[0].size),
                "pivot": [cells[0].width // 2, cells[0].height - 4], "playback_fps": args.fps,
                "sources": [Path(f).name for f in args.frames]}
        export_cells(cells, Path(args.out_dir), args.name, meta, [Path(f).stem for f in args.frames])
        print(json.dumps(meta))
    elif args.cmd == "preview":
        imgs = [Image.open(p).convert("RGBA") for p in args.images]
        contact_sheet(imgs, Path(args.dst), cell_h=args.cell_height, labels=[Path(p).stem for p in args.images])
        print(args.dst)


if __name__ == "__main__":
    main()
