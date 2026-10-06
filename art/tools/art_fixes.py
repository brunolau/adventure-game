"""Small art fixes after the playtests (2026-10-05): CS06/CS07 port symbols, item icons matching the paintings.

Subcommands (run from art/tools):
  ports                  free: turn the X port symbol into + (the room S49 and the journal read circle, plus,
                         square, triangle; ISSUES PT-S21) in CS06_1, CS06_2, CS07_1 (plate and the ORIGIN folder)
                         and CS07_2: the X's own painted strokes are lifted off an in-painted plate, turned by the
                         angle that makes them upright and put back, so brushwork and engraving stay the painting's
  origin_icon            free: the same fix on the ORIGIN item icon (the folder shows the four symbols)
  tools_icon [--tag T]   paid: TOOLS icon re-painted from the S01 painting (olive canvas tool bag on the chair,
                         ISSUES M5-04) on a magenta key canvas, NB2 1K 1:1
  tools_cut RAW          free: key the TOOLS raw image and write the master + 256 px icon + game WebP
  sign_s43 [--tag T]     paid: S43 reception lettering RECEPTION -> RECEPCIA (local crop edit, ISSUES PT-S27)
Paid calls use hero_coat.task_guard (one USD 8 task budget for all art fixes).
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

import fal_api
import frames as fr
import hero_coat

ART = fal_api.ART
REPO = ART.parent
MASTERS = ART / "cutscenes"
EXPORT = REPO / "src" / "game" / "assets" / "cutscenes"
REVIEW = REPO / "build" / "screens" / "fixes" / "art"

# X symbol boxes in master pixels (2752x1536), measured on the v2 masters.
PORT_X = {
    "CS06_1": [(222, 580, 322, 682)],
    "CS06_2": [(214, 580, 316, 682)],
    "CS07_2": [(215, 580, 317, 682)],
    "CS07_1": [(812, 492, 975, 668, 0.8)],   # the ORIGIN folder in the tray already shows a + (perspective)
}


# ----------------------------------------------------------------------------- symbol rotation (free)

def box_blur(a: np.ndarray, r: int) -> np.ndarray:
    """Mean over a (2r+1)^2 window (edge-clamped), any number of trailing channels."""
    pad = np.pad(a, ((r + 1, r), (r + 1, r)) + ((0, 0),) * (a.ndim - 2), mode="edge")
    c = pad.cumsum(0).cumsum(1)
    k = 2 * r + 1
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def inpaint(rgb: np.ndarray, hole: np.ndarray) -> np.ndarray:
    """Fill `hole` from its surroundings by coarse-to-fine repeated averaging (harmonic fill: stable, smooth)."""
    out = rgb.astype(np.float32).copy()
    ring = np.asarray(Image.fromarray((hole * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))) > 0
    ring &= ~hole
    out[hole] = out[ring].mean(axis=0) if ring.any() else out[~hole].mean(axis=0)
    for r, n in ((16, 30), (8, 30), (4, 40), (2, 60), (1, 60)):
        for _ in range(n):
            out[hole] = box_blur(out, r)[hole]
    return out


def symbol_mask(rgb: np.ndarray, thr: float, radius: int | None = None, dark_only: bool = False,
                grow_px: int = 2) -> np.ndarray:
    """Painted symbol strokes: pixels that differ from a local mean (engraving: darker or lighter; ink: darker)."""
    lum = rgb.astype(np.float32).mean(axis=2)
    bg = box_blur(lum, radius or max(6, min(rgb.shape[:2]) // 6))
    m = (bg - lum > thr) if dark_only else (np.abs(lum - bg) > thr)
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * grow_px + 1))) > 0
    return m


def rotate_layer(layer: np.ndarray, angle: float, centre: tuple[float, float], scale: float = 1.0) -> np.ndarray:
    """Rotate (PIL convention, counter-clockwise) and scale a float layer (H, W, C) about centre (x, y)."""
    a = math.radians(angle)
    cos, sin = math.cos(a), math.sin(a)
    cx, cy = centre
    # inverse map: source = R(-angle) * (dest - c) / scale + c   (image y points down)
    m = (cos / scale, -sin / scale, cx - (cos * cx - sin * cy) / scale,
         sin / scale, cos / scale, cy - (sin * cx + cos * cy) / scale)
    chans = []
    for c in range(layer.shape[2]):
        ch = Image.fromarray(layer[..., c].astype(np.float32), "F")
        chans.append(np.asarray(ch.transform(ch.size, Image.Transform.AFFINE, m, Image.Resampling.BICUBIC)))
    return np.dstack(chans)


def upright_angle(energy: np.ndarray, centre: tuple[float, float]) -> float:
    """Rotation (degrees) that puts the X's arms on the vertical and horizontal through the centre."""
    h, w = energy.shape
    ys, xs = np.mgrid[0:h, 0:w]
    best = (-1.0, 45.0)
    band = max(2.0, min(h, w) * 0.06)
    for ang in np.arange(30.0, 60.5, 0.5):
        rot = np.asarray(Image.fromarray(energy.astype(np.float32), "F").rotate(ang, Image.Resampling.BILINEAR,
                                                                                center=centre))
        score = rot[(np.abs(xs - centre[0]) < band) | (np.abs(ys - centre[1]) < band)].sum()
        if score > best[0]:
            best = (score, float(ang))
    return best[1]


def x_to_plus(rgb: np.ndarray, box: tuple[int, int, int, int], thr: float = 14.0, scale: float = 1.0,
              main_only: bool = False, ink: bool = False) -> tuple[np.ndarray, dict]:
    """Turn the X symbol inside box into a + made of the same painted strokes."""
    x0, y0, x1, y1 = box
    pad = (x1 - x0) // 3
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(rgb.shape[1], x1 + pad), min(rgb.shape[0], y1 + pad)
    region = rgb[Y0:Y1, X0:X1].astype(np.float32)
    inner = np.zeros(region.shape[:2], bool)
    inner[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
    sym = (symbol_mask(region, thr, radius=6, dark_only=True, grow_px=1) if ink else symbol_mask(region, thr)) & inner
    # only the X itself: the largest component and the pieces close to it (other symbols, a switch edge or a
    # lamp halo inside the box would otherwise be rotated along)
    labels, sizes = fr.label_components(sym)
    if len(sizes):
        main = int(np.argmax(sizes)) + 1
        near = np.asarray(Image.fromarray(((labels == main) * 255).astype(np.uint8)).filter(
            ImageFilter.MaxFilter(9))) > 0
        keep = np.zeros(len(sizes) + 1, dtype=bool)
        keep[np.unique(labels[near])] = True
        keep[0] = False
        if main_only:
            keep[:] = False
            keep[main] = True
        sym = keep[labels]
    # the rotated strokes land where the plate shows now: clear the whole disc the X sweeps through
    ys, xs = np.nonzero(sym)
    weights = np.abs(region.mean(axis=2) - box_blur(region.mean(axis=2), max(6, min(region.shape[:2]) // 6)))[sym]
    cx, cy = float((xs * weights).sum() / weights.sum()), float((ys * weights).sum() / weights.sum())
    radius = max(np.hypot(xs - cx, ys - cy).max() + 3, 4)
    yy, xx = np.mgrid[0:region.shape[0], 0:region.shape[1]]
    disc = np.hypot(xx - cx, yy - cy) <= radius
    background = inpaint(region, sym)
    layer = (region - background) * sym[..., None]
    energy = np.abs(layer).mean(axis=2)
    angle = upright_angle(energy, (cx, cy))
    soft = np.asarray(Image.fromarray((sym * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)),
                      np.float32) / 255
    layer = (region - background) * soft[..., None]
    rotated = rotate_layer(layer, angle, (cx, cy), scale)
    out_region = background + rotated
    # keep the original outside the swept disc (feathered), so nothing but the symbol changes
    feather = np.clip((radius + 4 - np.hypot(xx - cx, yy - cy)) / 4, 0, 1)[..., None]
    out_region = out_region * feather + region * (1 - feather)
    out = rgb.copy()
    out[Y0:Y1, X0:X1] = out_region.clip(0, 255).astype(np.uint8)
    return out, {"box": list(box), "centre": [round(cx + X0, 1), round(cy + Y0, 1)], "angle": angle, "scale": scale,
                 "radius": round(float(radius), 1)}


def next_version(shot: str) -> int:
    versions = [int(p.stem.rsplit("_v", 1)[1]) for p in MASTERS.glob(f"{shot}_v*.png")]
    return max(versions) + 1 if versions else 1


def cmd_ports(_args: argparse.Namespace) -> None:
    import cutscenes
    REVIEW.mkdir(parents=True, exist_ok=True)
    for shot, boxes in PORT_X.items():
        src = MASTERS / f"{shot}_v2.png"
        rgb = np.asarray(Image.open(src).convert("RGB"))
        out = rgb
        report = []
        for box in boxes:
            out, info = x_to_plus(out, box[:4], scale=box[4] if len(box) > 4 else 1.0)
            report.append(info)
        version = next_version(shot)
        dst = MASTERS / f"{shot}_v{version}.png"
        Image.fromarray(out).save(dst)
        meta = json.loads(src.with_suffix(".json").read_text(encoding="utf-8"))
        meta.update({"retouch_of": src.name, "usd": 0, "at": datetime.datetime.now().isoformat(timespec="seconds"),
                     "retouch_note": "port symbol X turned into + (room S49 / journal: circle, plus, square, "
                                     "triangle; ISSUES PT-S21): the X's own strokes rotated upright on an "
                                     "in-painted plate", "retouch_symbols": report})
        meta.pop("exported", None)
        dst.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        img = Image.open(dst).convert("RGB")
        cutscenes.fit_to_frame(img).save(EXPORT / f"{shot}.webp", "WEBP", quality=90, method=6)
        meta["exported"] = {"path": f"src/game/assets/cutscenes/{shot}.webp", "crop": None,
                            "at": datetime.datetime.now().isoformat(timespec="seconds")}
        dst.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        # before / after crop for review
        x0 = min(b[0] for b in boxes) - 120
        y0 = min(b[1] for b in boxes) - 120
        x1 = max(b[2] for b in boxes) + 120
        y1 = max(b[3] for b in boxes) + 120
        before = Image.fromarray(rgb[y0:y1, x0:x1])
        after = Image.fromarray(out[y0:y1, x0:x1])
        pair = Image.new("RGB", (before.width * 2 + 10, before.height), (20, 20, 20))
        pair.paste(before, (0, 0))
        pair.paste(after, (before.width + 10, 0))
        pair.save(REVIEW / f"ports_{shot}.png")
        print(shot, f"v{version}", report)


def cmd_origin_icon(_args: argparse.Namespace) -> None:
    import items
    master = ART / "items" / "ORIGIN.png"
    rgba = np.asarray(Image.open(master).convert("RGBA"))
    box = tuple(int(v) for v in _args.box.split(","))
    rgb, info = x_to_plus(rgba[..., :3].copy(), box, thr=_args.thr, scale=_args.scale, main_only=True,
                          ink=True)
    out = np.dstack([rgb, rgba[..., 3]])
    backup = ART / "items" / "rejected_ORIGIN_x_symbol.png"
    if not backup.exists():
        Image.open(master).save(backup)
    Image.fromarray(out, "RGBA").save(master, optimize=True)
    small = Image.fromarray(out, "RGBA").resize((256, 256), Image.Resampling.LANCZOS)
    small.save(ART / "items" / "ORIGIN_256.png", optimize=True)
    small.save(REPO / "src" / "game" / "assets" / "items" / "ORIGIN.webp", "WEBP", quality=95, alpha_quality=100, method=6)
    pair = Image.new("RGBA", (1034, 512), (140, 140, 140, 255))
    pair.alpha_composite(Image.open(backup).convert("RGBA"), (0, 0))
    pair.alpha_composite(Image.fromarray(out, "RGBA"), (522, 0))
    pair.convert("RGB").save(REVIEW / "icon_ORIGIN_before_after.png")
    print("ORIGIN", info)


# ----------------------------------------------------------------------------- TOOLS icon (paid)

TOOLS_BRIEF = (
    "Adam's service tool bag, exactly the bag that stands on the chair in the second reference image: a soft "
    "olive-green canvas tool bag with a wide open top, rounded ends, brown leather trim, two front pockets, a long "
    "olive canvas shoulder strap with a metal buckle; tools stick out of the open top and the front pockets: a "
    "screwdriver with a red handle, pliers with orange grips and an adjustable steel wrench."
)


def s01_bag_reference() -> Path:
    out = ART / "items" / "raw" / "ref_S01_tool_bag.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    bg = Image.open(REPO / "src" / "game" / "assets" / "bg_natural" / "S01.webp").convert("RGB")
    bg.crop((610, 680, 880, 920)).resize((810, 720), Image.Resampling.LANCZOS).save(out)
    return out


def icon_style_reference() -> Path:
    """Four finished prologue icons on magenta (camera, light and outline reference)."""
    out = ART / "items" / "raw" / "ref_icons_magenta.png"
    canvas = Image.new("RGBA", (1024, 512), (255, 0, 255, 255))
    for i, item in enumerate(["PHONE", "GROCERIES", "SHEDKEY", "CHRONO"]):
        icon = Image.open(ART / "items" / f"{item}_256.png").convert("RGBA").resize((240, 240))
        canvas.alpha_composite(icon, (16 + i * 252, 136))
    canvas.convert("RGB").save(out)
    return out


def magenta_canvas() -> Path:
    out = ART / "items" / "raw" / "key_canvas_magenta_1024.png"
    if not out.exists():
        Image.new("RGB", (1024, 1024), (255, 0, 255)).save(out)
    return out


def cmd_tools_icon(args: argparse.Namespace) -> None:
    import chars
    import items
    model = "fal-ai/nano-banana-2/edit"
    price = fal_api.IMAGE_PRICES[(model, "1K")]
    name = f"TOOLS_s01{args.tag}"
    asset = f"items/TOOLS/fix/{name}"
    hero_coat.task_guard(asset, price)
    rules = items.ICON_RULES.replace("No green parts on any object. ", "")
    key = chars.key_background("magenta").replace("The character must", "The object must").replace(
        "on the character", "on the object")
    prompt = (
        "Edit the first image, a flat chroma-key magenta canvas: paint ONE inventory icon for a classic 1990s "
        "point-and-click adventure game, centred, filling about 70% of the image, with magenta margin on every side: "
        + TOOLS_BRIEF + " The SECOND reference image is a crop of the game's room painting: copy the bag's shape, "
        "olive-green canvas colour, brown trim, pockets, strap and tools from it, but paint the bag alone, without "
        "the chair, the table or the room. The THIRD reference image shows other finished icons of the same game: "
        "match their camera angle, light direction, darker painted outline, brushwork and visual size exactly, but do "
        "not copy their objects. " + rules + " " + key + " " + chars.STYLE_A)
    refs = [magenta_canvas(), s01_bag_reference(), icon_style_reference()]
    arguments = {"prompt": prompt, "image_urls": [fal_api.image_data_uri(r, max_side=1536) for r in refs],
                 "aspect_ratio": "1:1", "resolution": "1K", "output_format": "png", "num_images": 1, "seed": 2020}
    result = fal_api.run(model, arguments, asset, price, budget=None, timeout_s=600)
    meta = {"model": model, "usd": price, "prompt": prompt, "aspect_ratio": "1:1", "resolution": "1K",
            "references": [str(r.relative_to(ART)) for r in refs], "seed": 2020}
    paths = hero_coat.save_result(result, ART / "items" / "raw" / name, meta)
    print("\n".join(str(p) for p in paths))


def recolor_to_leather(rgb: np.ndarray) -> np.ndarray:
    """Olive canvas -> the brown leather of the S01 painting after its M5-04 recolour: the same HSV transform as
    art/tools/s01_bag_recolor.py (hue 0.068, saturation x1.3 + 0.06, value x0.93), applied to the olive / khaki
    hues only, so the red screwdriver, the orange pliers, the steel wrench and the brown trim stay as painted."""
    import s01_bag_recolor as rc
    a = rgb.astype(np.float32) / 255
    hsv = rc.rgb_to_hsv(a)
    olive = ((hsv[..., 0] > 0.105) & (hsv[..., 0] < 0.25) & (hsv[..., 1] > 0.10)).astype(np.float32)
    w = np.asarray(Image.fromarray((olive * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)),
                   np.float32)[..., None] / 255
    new = hsv.copy()
    new[..., 0] = 0.068
    new[..., 1] = np.clip(hsv[..., 1] * 1.3 + 0.06, 0, 1)
    new[..., 2] = hsv[..., 2] * 0.93
    out = a * (1 - w) + rc.hsv_to_rgb(new) * w
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


def cmd_tools_cut(args: argparse.Namespace) -> None:
    import items
    raw = Path(args.raw)
    rgb = fr.load_rgb(raw)
    if args.leather:
        rgb = recolor_to_leather(rgb)
        Image.fromarray(rgb).save(raw.with_name(raw.stem + "_leather.png"))
    rgba = fr.chroma_key(rgb, min_island=60)
    items.ICON_BRIEFS["TOOLS"] = TOOLS_BRIEF + (" Recoloured locally to the brown leather of the S01 bag (M5-04)."
                                                if args.leather else "")
    items.write_icon(rgba, "TOOLS", raw.name)
    img = Image.open(ART / "items" / "TOOLS_256.png").convert("RGBA")
    img.save(REPO / "src" / "game" / "assets" / "items" / "TOOLS.webp", "WEBP", quality=95, alpha_quality=100, method=6)
    print("TOOLS", fr.key_quality(fr.crop_to_figure(rgba)))


# ----------------------------------------------------------------------------- S43 lettering (paid)

def cmd_sign_s43(args: argparse.Namespace) -> None:
    import chars
    model = "fal-ai/nano-banana-2/edit"
    price = fal_api.IMAGE_PRICES[(model, "1K")]
    box = tuple(int(v) for v in args.box.split(","))
    bg_path = REPO / "src" / "game" / "assets" / "bg_natural" / "S43.webp"
    crop = Image.open(bg_path).convert("RGB").crop(box)
    src = ART / "backgrounds" / "fixes" / "S43_reception_crop.png"
    src.parent.mkdir(parents=True, exist_ok=True)
    side = 1024
    crop.resize((side, round(side * crop.height / crop.width)), Image.Resampling.LANCZOS).save(src)
    name = f"S43_recepcia{args.tag}"
    asset = f"bg_natural/fix/{name}"
    hero_coat.task_guard(asset, price)
    prompt = ("Edit this crop of a hand-painted adventure game background: the wall lettering that reads "
              "'RECEPTION' must read 'RECEPCIA' instead (the Slovak word): exactly eight letters, R-E-C-E-P-C-I-A, "
              "with no letter T and no letter O or N. Same 3D metal letter style, size, colour and spacing, the word "
              "centred where the old word was. Change nothing else: same wall, same light, same brushwork, same "
              "framing. " + chars.STYLE_A)
    if args.tag == "":
        prompt = prompt.replace(": exactly eight letters, R-E-C-E-P-C-I-A, with no letter T and no letter O or N", "")
    aspect = args.aspect
    arguments = {"prompt": prompt, "image_urls": [fal_api.image_data_uri(src)], "aspect_ratio": aspect,
                 "resolution": "1K", "output_format": "png", "num_images": 1, "seed": args.seed}
    result = fal_api.run(model, arguments, asset, price, budget=None, timeout_s=600)
    meta = {"model": model, "usd": price, "prompt": prompt, "aspect_ratio": aspect, "resolution": "1K",
            "references": [str(src.relative_to(ART))], "box": list(box), "seed": args.seed}
    paths = hero_coat.save_result(result, ART / "backgrounds" / "fixes" / name, meta)
    print("\n".join(str(p) for p in paths))


def slide_glyph(edit: np.ndarray, args: argparse.Namespace, y0: int, y1: int) -> np.ndarray:
    """Drop one stray glyph (--cut) and slide the glyph after it (--tail) left over it, on a marble fill from
    below the lettering. Kept for reference: the accepted S43 edit spells the word right and needs no slide."""
    cut0, cut1 = (int(v) for v in args.cut.split(","))      # glyph to drop, crop px at 1024 wide
    a0, a1 = (int(v) for v in args.tail.split(","))          # the glyph(s) that move left over the dropped one
    shift = cut1 - cut0
    merged = edit.copy()
    # 1. wall where the dropped glyph and the moving glyph stand: marble texture from just below the lettering,
    #    colour-matched per channel to the wall right above and below the band
    zx0, zx1 = cut0 - 4, a1 + 6
    hgt = y1 - y0
    texture = edit[y1 + 8:y1 + 8 + hgt, zx0:zx1].copy()
    ring = np.concatenate([edit[y0 - 14:y0 - 4, zx0:zx1].reshape(-1, 3), edit[y1 + 2:y1 + 8, zx0:zx1].reshape(-1, 3)])
    texture = (texture - texture.reshape(-1, 3).mean(0)) * (ring.std(0) / np.maximum(texture.reshape(-1, 3).std(0), 1))         + ring.mean(0)
    # vertical brightness ramp of the wall (lighter toward the top-right light spot): blend the band's own top and
    # bottom wall rows into the texture
    ys = np.linspace(0, 1, hgt)[:, None, None]
    top_row = edit[y0 - 6:y0 - 2, zx0:zx1].mean(0)[None]
    bottom_row = edit[y1 + 2:y1 + 6, zx0:zx1].mean(0)[None]
    ramp = top_row * (1 - ys) + bottom_row * ys
    texture = texture - texture.mean((0, 1), keepdims=True) + ramp
    # 2. the moving glyph: pixels that stand out from a smooth wall estimate inside its box
    glyph_box = edit[y0:y1, a0:a1]
    hole = np.ones(glyph_box.shape[:2], bool)
    hole[:, :3] = hole[:, -3:] = False
    hole[:3, :] = hole[-3:, :] = False
    wall_est = inpaint(glyph_box, hole)
    diff = np.abs(glyph_box - wall_est).mean(axis=2)
    gm = Image.fromarray(((diff > 14) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(
        ImageFilter.GaussianBlur(1.5))
    gmask = (np.asarray(gm, np.float32) / 255)[..., None]
    # 3. compose: wall over both glyphs (feathered box), then the glyph at its new place
    fx = np.clip(np.minimum(np.arange(zx1 - zx0) + 1, zx1 - zx0 - np.arange(zx1 - zx0)) / 6, 0, 1)[None, :, None]
    fy = np.clip(np.minimum(np.arange(hgt) + 1, hgt - np.arange(hgt)) / 6, 0, 1)[:, None, None]
    fw = fx * fy
    merged[y0:y1, zx0:zx1] = merged[y0:y1, zx0:zx1] * (1 - fw) + texture * fw
    nx0 = a0 - shift
    merged[y0:y1, nx0:nx0 + (a1 - a0)] = merged[y0:y1, nx0:nx0 + (a1 - a0)] * (1 - gmask) + glyph_box * gmask
    return merged


def cmd_s43_compose(args: argparse.Namespace) -> None:
    """Free: put only the lettering band of an NB2 crop edit back into the painting (feathered, everything else stays
    the original pixels); optionally drop a stray glyph first (--cut / --tail, see slide_glyph)."""
    box = tuple(int(v) for v in args.box.split(","))
    bg_path = REPO / "src" / "game" / "assets" / "bg_natural" / "S43.webp"
    backup = ART / "masters" / "bg_natural" / "S43_before_recepcia.webp"
    if not backup.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        Image.open(bg_path).save(backup, "WEBP", lossless=True)
    bg = np.asarray(Image.open(backup).convert("RGB")).astype(np.float32)
    w, h = box[2] - box[0], box[3] - box[1]
    edit = np.asarray(Image.open(Path(args.edit)).convert("RGB").resize((1024, round(1024 * h / w)),
                                                                          Image.Resampling.LANCZOS)).astype(np.float32)
    y0, y1 = (int(v) for v in args.band.split(","))          # lettering band, crop px
    merged = slide_glyph(edit, args, y0, y1) if args.cut else edit
    # back into the painting at the crop scale: only the lettering band, feathered, everything else original
    small = np.asarray(Image.fromarray(merged.clip(0, 255).astype(np.uint8)).resize((w, h), Image.Resampling.LANCZOS),
                       np.float32)
    sy0, sy1 = int((y0 - 16) * h / edit.shape[0]), int((y1 + 16) * h / edit.shape[0])
    sx0, sx1 = int(float(args.x_range.split(",")[0]) * w / 1024), int(float(args.x_range.split(",")[1]) * w / 1024)
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]
    m = (np.clip((yy - sy0) / 8, 0, 1) * np.clip((sy1 - yy) / 8, 0, 1) *
         np.clip((xx - sx0) / 10, 0, 1) * np.clip((sx1 - xx) / 10, 0, 1))[..., None]
    region = bg[box[1]:box[3], box[0]:box[2]]
    bg[box[1]:box[3], box[0]:box[2]] = region * (1 - m) + small * m
    for spec in args.clean or []:
        # a faint stroke NB2 left after the word (the old N's diagonal): darker-than-wall pixels in-painted
        cx0, cy0, cx1, cy1 = (int(v) for v in spec.split(","))
        reg = bg[cy0:cy1, cx0:cx1]
        dark = symbol_mask(reg.astype(np.uint8), 6, radius=8, dark_only=True, grow_px=2)
        bg[cy0:cy1, cx0:cx1] = inpaint(reg, dark)
    result = Image.fromarray(bg.clip(0, 255).astype(np.uint8))
    result.save(bg_path, "WEBP", quality=90, method=6)   # like the other shipped paintings (lossy, ~150-200 KB)
    REVIEW.mkdir(parents=True, exist_ok=True)
    before = Image.open(backup).convert("RGB").crop((box[0] - 40, box[1] + 60, box[2] + 40, box[3] - 120))
    after = result.crop((box[0] - 40, box[1] + 60, box[2] + 40, box[3] - 120))
    pair = Image.new("RGB", (before.width, before.height * 2 + 6), (20, 20, 20))
    pair.paste(before, (0, 0))
    pair.paste(after, (0, before.height + 6))
    pair.save(REVIEW / "S43_recepcia_before_after.png")
    print(bg_path, "written; original kept in", backup)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ports")
    p = sub.add_parser("origin_icon")
    p.add_argument("--box", required=True, help="x0,y0,x1,y1 of the X on the 512 px master")
    p.add_argument("--thr", type=float, default=14.0)
    p.add_argument("--scale", type=float, default=0.8)
    p = sub.add_parser("tools_icon")
    p.add_argument("--tag", default="")
    p = sub.add_parser("tools_cut")
    p.add_argument("raw")
    p.add_argument("--leather", action="store_true", help="recolour the olive canvas to the S01 leather brown")
    p = sub.add_parser("sign_s43")
    p.add_argument("--box", required=True, help="x0,y0,x1,y1 crop of bg_natural/S43.webp around the lettering")
    p.add_argument("--aspect", default="16:9")
    p.add_argument("--tag", default="")
    p.add_argument("--seed", type=int, default=43)
    p = sub.add_parser("s43_compose")
    p.add_argument("--box", required=True)
    p.add_argument("--edit", required=True)
    p.add_argument("--cut", help="x0,x1 of a stray glyph to drop (crop px at 1024 wide)")
    p.add_argument("--band", required=True, help="y0,y1 of the lettering (crop px at 1024 wide)")
    p.add_argument("--tail", help="x0,x1 of the glyph that slides left over it (crop px at 1024 wide)")
    p.add_argument("--x-range", required=True, help="x0,x1 of the lettering area that goes back (crop px at 1024 wide)")
    p.add_argument("--clean", action="append", help="x0,y0,x1,y1 (painting px): in-paint faint dark strokes there")
    args = parser.parse_args()
    {"s43_compose": cmd_s43_compose, "ports": cmd_ports, "origin_icon": cmd_origin_icon, "tools_icon": cmd_tools_icon, "tools_cut": cmd_tools_cut,
     "sign_s43": cmd_sign_s43}[args.cmd](args)


if __name__ == "__main__":
    main()
