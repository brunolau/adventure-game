"""Winter life for the Jasna 2035 rooms (owner 2026-10-06: "Jasna 2035 is in winter", 6 February 2035).

Adds the winter layers to the per-room ambient files (src/game/data/blocking/ambient/<room>.json): skiers sliding on
the far pistes, a snowcat grooming a slope, gondola / Funitel cabins riding their ropes (the painted cabins are lifted
off a clean plate and become the first cabins of the conveyor), snow blown off roofs and ridges, light snowfall varied
per room, breath steam of the people outdoors (NPC mouths and the hero, ParticleLayer follow "hero"), chimney steam.
Every layer this tool owns has an id starting with "w_"; `layers` drops those and appends the current set, so it can
be re-run. Sprites live in src/game/assets/ambient/<room>/winter/ (one folder per room, nothing shared).

Commands (run from the repo root: PYTHONIOENCODING=utf-8 python -X utf8 art/tools/winter_ambient.py ...):
  sprites                 free: draw the skier and snowcat sprites (supersampled, style-A colours) into the room
                          folders whose w_* layers use them (run after `cut`), preview in art/ambient/winter/
  plate ROOM --budget U   paid (NB2 2K, USD 0.12): the room painting without the painted cabins (ropes kept);
                          art/ambient/winter/<room>_plate_raw.png
  cut ROOM                free: from the plate: clean patches over the painted cabins + the cabin sprites
  layers [ROOM ...]       free: write the w_* layers into the ambient files
  screens [ROOM ...]      free: Godot import, then a clean shot and motion frames per room (hidden QA window,
                          tools/qa_godot.py) in build/screens/jasna_winter/<room>/winter_life_*.png
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

TOOLS = Path(__file__).resolve().parent
ART = TOOLS.parent
REPO = ART.parent
GAME = REPO / "src" / "game"
AMBIENT_ASSETS = GAME / "assets" / "ambient"
AMBIENT_DATA = GAME / "data" / "blocking" / "ambient"
WORK = ART / "ambient" / "winter"
sys.path.insert(0, str(TOOLS))

ROOMS = ["S42", "S43", "S44", "S45", "S46", "S47", "S48", "S49", "S50", "S67", "S68"]
PREFIX = "w_"

# ----------------------------------------------------------------------------- sprites (drawn locally)

SS = 8  # supersampling

JACKETS = {
    "red": ((200, 52, 42), (36, 38, 46), (240, 240, 236)),
    "blue": ((42, 98, 200), (34, 36, 44), (214, 58, 46)),
    "yellow": ((232, 184, 40), (38, 40, 48), (40, 42, 50)),
    "teal": ((32, 150, 140), (40, 44, 56), (236, 236, 232)),
    "purple": ((122, 64, 160), (30, 32, 40), (240, 240, 236)),
    "orange": ((228, 110, 34), (44, 50, 70), (36, 38, 44)),
}


def _poly(d: ImageDraw.ImageDraw, pts, fill, k: float = SS) -> None:
    d.polygon([(x * k, y * k) for x, y in pts], fill=fill)


def _line(d: ImageDraw.ImageDraw, a, b, fill, w: float, k: float = SS) -> None:
    d.line([(a[0] * k, a[1] * k), (b[0] * k, b[1] * k)], fill=fill, width=max(1, round(w * k)))


def _ellipse(d: ImageDraw.ImageDraw, box, fill, k: float = SS) -> None:
    d.ellipse([box[0] * k, box[1] * k, box[2] * k, box[3] * k], fill=fill)


def shade(c, f):
    return tuple(max(0, min(255, round(v * f))) for v in c[:3]) + (255,)


def skier(colour: str, pose: str = "carve") -> Image.Image:
    """A small downhill skier facing right (48 x 48, pivot at the ski centre (24, 43)): crouched, skis angled down
    to the right, poles back. pose 'carve' leans into the slope, 'straight' stands taller."""
    jacket, trousers, helmet = JACKETS[colour]
    W = 48
    img = Image.new("RGBA", (W * SS, W * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lean = 3.0 if pose == "carve" else 1.0
    tall = 0.0 if pose == "carve" else -2.0
    # skis (two dark lines, slightly apart, tips up at the right)
    for off in (0.0, 1.6):
        _line(d, (9, 41.5 + off), (38, 44.5 + off), (34, 34, 40, 255), 1.5)
        _line(d, (38, 44.5 + off), (40.5, 43.2 + off), (34, 34, 40, 255), 1.4)
    # legs: bent knees forward (to the right)
    knee = (26 + lean * 0.4, 33 + tall)
    hip = (21 + lean * 0.2, 27 + tall)
    _poly(d, [(hip[0] - 3, hip[1]), (hip[0] + 3, hip[1] + 1), (knee[0] + 2.4, knee[1]), (knee[0] - 1.8, knee[1] + 0.6)],
          trousers + (255,))
    _poly(d, [(knee[0] - 2.2, knee[1] - 0.4), (knee[0] + 2.4, knee[1]), (23.5, 42.5), (19.5, 42.0)], trousers + (255,))
    _poly(d, [(hip[0] - 1, hip[1] + 1), (hip[0] + 4, hip[1] + 2), (knee[0] + 4.4, knee[1] + 1.4),
              (knee[0] + 0.6, knee[1] + 2)], shade(trousers, 1.25))
    _poly(d, [(knee[0] + 0.6, knee[1] + 1.6), (knee[0] + 4.2, knee[1] + 1.8), (27.5, 43.5), (24, 43.2)],
          shade(trousers, 1.25))
    # boots
    _poly(d, [(19, 41.6), (24.4, 42.2), (24.6, 44.0), (18.6, 43.4)], (52, 54, 62, 255))
    _poly(d, [(23.6, 42.8), (28.6, 43.4), (28.8, 45.2), (23.2, 44.6)], (60, 62, 70, 255))
    # torso: leaning forward
    sh = (25 + lean, 17 + tall)       # shoulder
    _poly(d, [(hip[0] - 4, hip[1] + 1), (hip[0] + 4, hip[1] + 2), (sh[0] + 4, sh[1] + 1), (sh[0] - 3, sh[1] - 1)],
          jacket + (255,))
    _poly(d, [(hip[0] + 1, hip[1] + 1.5), (hip[0] + 4, hip[1] + 2), (sh[0] + 4, sh[1] + 1), (sh[0] + 1, sh[1])],
          shade(jacket, 0.78))
    # arms forward with poles trailing back
    hand_f = (sh[0] + 6, sh[1] + 7)
    hand_b = (sh[0] + 3, sh[1] + 8)
    _line(d, (sh[0] + 1, sh[1] + 1), hand_f, shade(jacket, 0.9), 2.2)
    _line(d, (sh[0] - 1, sh[1] + 1.5), hand_b, shade(jacket, 0.7), 2.0)
    for hand in (hand_f, hand_b):
        _line(d, hand, (hand[0] - 13, hand[1] + 12), (70, 72, 80, 255), 0.9)
        _ellipse(d, (hand[0] - 1.1, hand[1] - 1.1, hand[0] + 1.1, hand[1] + 1.1), (30, 30, 34, 255))
    # head: helmet + goggles + a bit of face
    hc = (sh[0] + 2.5, sh[1] - 4.5)
    _ellipse(d, (hc[0] - 3.4, hc[1] - 3.4, hc[0] + 3.4, hc[1] + 3.4), (230, 186, 156, 255))
    _poly(d, [(hc[0] - 3.8, hc[1] + 0.6), (hc[0] - 3.4, hc[1] - 2.6), (hc[0] - 0.5, hc[1] - 4.2), (hc[0] + 2.8, hc[1] - 3.4),
              (hc[0] + 3.8, hc[1] - 0.8), (hc[0] + 1.0, hc[1] - 0.6)], helmet + (255,))
    _poly(d, [(hc[0] + 0.6, hc[1] - 1.0), (hc[0] + 3.9, hc[1] - 1.0), (hc[0] + 3.7, hc[1] + 0.9), (hc[0] + 0.8, hc[1] + 0.8)],
          (40, 44, 60, 255))
    img = img.resize((W, W), Image.Resampling.LANCZOS)
    return soften(img)


def snowcat() -> Image.Image:
    """A piste groomer facing right (96 x 56, pivot at the track bottom centre (48, 52)): red body and cabin, wide
    dark rubber tracks, the grey front blade on the right, the comb/tiller at the back, an amber beacon."""
    W, H = 96, 56
    img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    red, dark = (198, 46, 36), (36, 36, 42)
    # tracks
    _poly(d, [(18, 40), (74, 40), (79, 46), (74, 52), (18, 52), (13, 46)], dark + (255,))
    for x in range(20, 74, 9):
        _ellipse(d, (x, 42.5, x + 6, 48.5), (92, 94, 100, 255))
    _line(d, (16, 51.5), (76, 51.5), (60, 60, 66, 255), 1.0)
    # tiller at the back (left)
    _poly(d, [(5, 41), (16, 38), (16, 47), (6, 50), (3, 47)], (120, 122, 128, 255))
    _poly(d, [(2, 48), (8, 47), (9, 51), (2, 52)], (230, 232, 236, 255))
    # body
    _poly(d, [(18, 40), (78, 40), (80, 33), (60, 30), (20, 31)], red + (255,))
    _poly(d, [(20, 37), (78, 37), (78, 40), (18, 40)], shade(red, 0.72))
    # cabin
    _poly(d, [(46, 31), (66, 31), (64, 18), (52, 17), (47, 22)], red + (255,))
    _poly(d, [(49, 29), (63, 29), (62, 20), (53, 19.5), (49.5, 23)], (52, 66, 88, 255))
    _poly(d, [(54, 20), (61, 20.5), (61.5, 27), (56, 27)], (110, 136, 168, 255))
    _ellipse(d, (55, 13.5, 59, 17.5), (250, 170, 40, 255))
    # front blade (right)
    _poly(d, [(80, 30), (90, 31), (92, 44), (86, 50), (80, 48)], (170, 172, 178, 255))
    _poly(d, [(86, 32), (90, 31), (92, 44), (88, 47)], (128, 130, 138, 255))
    # snow on the roof and the blade
    _poly(d, [(51, 17.4), (64.4, 17.6), (64.6, 19.2), (51, 18.8)], (246, 248, 252, 255))
    _poly(d, [(80, 46), (92, 43.5), (93, 50), (80, 52)], (240, 244, 250, 255))
    img = img.resize((W, H), Image.Resampling.LANCZOS)
    return soften(img)


def soften(img: Image.Image) -> Image.Image:
    """A touch of painterly softness: blur the colour a little inside the shape, keep the matte."""
    rgb = img.convert("RGB").filter(ImageFilter.GaussianBlur(0.35))
    out = Image.merge("RGBA", (*rgb.split(), img.getchannel("A")))
    return out




def cmd_sprites(args: argparse.Namespace) -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    sprites = {}
    for i, colour in enumerate(JACKETS):
        sprites[f"skier_{colour}"] = skier(colour, "carve" if i % 2 == 0 else "straight")
    sprites["snowcat"] = snowcat()
    # only the sprites a room's w_* layers use (room_layers) go into its folder
    for room in ROOMS:
        _first, last, _tweaks, _note = room_layers(room)
        wanted = {Path(l["texture"]).stem for l in last if str(l.get("texture", "")).startswith(f"{room}/winter/")}
        for n in sorted(wanted & set(sprites)):
            out = AMBIENT_ASSETS / room / "winter"
            out.mkdir(parents=True, exist_ok=True)
            sprites[n].save(out / f"{n}.webp", lossless=True)
    # preview: every sprite x4 and at game size on a snowy slope colour
    bg = Image.new("RGBA", (900, 260), (232, 238, 248, 255))
    x = 10
    for n, s in sprites.items():
        big = s.resize((s.width * 3, s.height * 3), Image.Resampling.NEAREST)
        bg.alpha_composite(big, (x, 10))
        small = s.resize((max(1, round(s.width * 0.25)), max(1, round(s.height * 0.25))), Image.Resampling.LANCZOS)
        bg.alpha_composite(small, (x + 20, 220))
        x += big.width + 8
    bg.convert("RGB").save(WORK / "sprites_preview.png")
    print(WORK / "sprites_preview.png")


# ----------------------------------------------------------------------------- clean plates (painted cabins)

# Painted cabins that become moving ones: box (x0, y0, x1, y1) around cabin + hanger in game px, grip = the point on
# the rope the hanger clamps (the sprite pivot).
CABINS = {
    "S42": {"what": "the three small grey gondola cabins (with their hangers) that hang on the cables of the gondola "
                    "station at the left edge: one high up at the top left and two small ones behind the station on "
                    "the right",
            "cabins": {"a": {"box": [6, 180, 76, 276], "grip": [50, 192]},
                       "b": {"box": [226, 350, 266, 412], "grip": [241, 359]},
                       "c": {"box": [261, 340, 302, 404], "grip": [285, 350]}}},
    "S48": {"what": "the small grey gondola cabin (with its hanger) that hangs on the cable at the pylon on the left edge",
            "cabins": {"a": {"box": [0, 376, 68, 482], "grip": [42, 389]}}},
    "S50": {"what": "the grey cable-car cabin (with its hanger) that hangs on the cable below the pylon at the left",
            "cabins": {"a": {"box": [118, 388, 198, 504], "grip": [166, 399]}}},
}

PLATE_PROMPT = (
    "Edit the first image: keep everything exactly the same - the same painting, the same camera and framing, the "
    "same colours, snow, light and brushwork - and remove ONLY {what}. The cables themselves stay exactly where they "
    "are and continue unbroken through the places where the cabins hung; behind the removed cabins continue the sky, "
    "the clouds, the mountains, the forest or the building exactly as they look around them. Do not change, move, add "
    "or redraw anything else. No people, no text.")


def task_spent(prefixes: tuple[str, ...], since: str) -> float:
    with (ART / "spend-log.csv").open(encoding="utf-8") as handle:
        return sum(float(r["usd"]) for r in csv.DictReader(handle) if r["asset"].startswith(prefixes)
                   and r["timestamp"] >= since)


def cmd_plate(args: argparse.Namespace) -> None:
    import fal_api
    import hero_coat
    import npc_winter
    from concurrent.futures import ThreadPoolExecutor
    model = "fal-ai/nano-banana-2/edit"
    price = fal_api.IMAGE_PRICES[(model, "2K")]
    spent = task_spent(npc_winter.TASK_PREFIXES, npc_winter.TASK_SINCE)
    if spent + price * len(args.rooms) > args.budget + 1e-9:
        sys.exit(f"BUDGET: {spent:.3f} + {price * len(args.rooms):.3f} would exceed {args.budget:.2f}")
    WORK.mkdir(parents=True, exist_ok=True)

    def one(room: str) -> list[Path]:
        src = GAME / "assets" / "bg_natural" / f"{room}.webp"
        prompt = PLATE_PROMPT.format(what=CABINS[room]["what"])
        arguments = {"prompt": prompt, "image_urls": [fal_api.image_data_uri(src)], "aspect_ratio": "16:9",
                     "resolution": "2K", "output_format": "png", "num_images": 1, "seed": args.seed}
        asset = f"ambient/jasna_winter/{room}_plate"
        result = fal_api.run(model, arguments, asset, price, budget=None, timeout_s=600)
        meta = {"model": model, "usd": price, "prompt": prompt, "references": [str(src.relative_to(REPO))],
                "seed": args.seed}
        return hero_coat.save_result(result, WORK / f"{room}_plate_raw", meta)
    with ThreadPoolExecutor(max_workers=3) as pool:
        for room, paths in zip(args.rooms, pool.map(one, args.rooms)):
            print(room, [str(p) for p in paths])


def fit_to_frame(img: Image.Image) -> Image.Image:
    """The pipeline's cover-fit of a 2K 16:9 output onto the 1920 x 1080 frame."""
    w, h = img.size
    scale = 1080 / h
    nw = round(w * scale)
    img = img.resize((nw, 1080), Image.Resampling.LANCZOS)
    left = (nw - 1920) // 2
    return img.crop((left, 0, left + 1920, 1080))


def phase_shift(a: np.ndarray, b: np.ndarray) -> tuple[int, int]:
    import frames
    return frames.phase_shift(a, b)


def _grow(mask: np.ndarray, px: int) -> np.ndarray:
    return np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * px + 1))) > 0


def _shrink(mask: np.ndarray, px: int) -> np.ndarray:
    return np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(2 * px + 1))) > 0


def _soft(mask: np.ndarray, radius: float) -> np.ndarray:
    img = Image.fromarray((mask * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(radius))
    return np.asarray(img, np.float32) / 255


def cabin_mask(diff: np.ndarray, box: tuple[int, int, int, int], grip: tuple[int, int]) -> np.ndarray:
    """The painted cabin inside its box: the body (largest blob of the plate difference after an opening that drops
    the thin ropes, holes filled, plus what hangs from it: icicles, the roof edge), the hanger (changed pixels within
    12 px of the line from the grip to the body top, as hangers are curved) and the grip clamp."""
    import frames
    x0, y0, x1, y1 = box
    changed = np.zeros_like(diff, bool)
    changed[y0:y1, x0:x1] = diff[y0:y1, x0:x1] > 14
    body = _grow(_shrink(changed, 3), 3)
    labels, sizes = frames.label_components(body)
    body = labels == (int(np.argmax(sizes)) + 1) if len(sizes) else body
    filled = _shrink(_grow(body, 6), 6)
    lab2, _ = frames.label_components(~filled)
    border = set(np.unique(np.concatenate([lab2[0], lab2[-1], lab2[:, 0], lab2[:, -1]])).tolist())
    holes = ~filled & ~np.isin(lab2, list(border))
    body = filled | holes
    # cabins are convex: take the hull of the body (its dark bottom edge can match a dark forest in the plate)
    ys, xs = np.nonzero(body)
    pts = sorted(set(zip(xs.tolist(), ys.tolist())))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for q in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    for q in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    hull_img = Image.new("L", diff.shape[::-1], 0)
    ImageDraw.Draw(hull_img).polygon(lower[:-1] + upper[:-1], fill=255)
    body = (np.asarray(hull_img) > 0) | body
    body = _grow(body, 1) | (_grow(body, 4) & changed)
    ys, xs = np.nonzero(body)
    top = int(ys.min())
    cx = float(xs[ys < top + 6].mean())
    gx, gy = grip
    yy, xx = np.mgrid[0:diff.shape[0], 0:diff.shape[1]]
    t = np.clip((yy - gy) / max(1, top + 4 - gy), 0, 1)
    line_x = gx + (cx - gx) * t
    hanger = (np.abs(xx - line_x) <= 12) & (yy >= gy - 8) & (yy <= top + 8) & changed
    labels, sizes = frames.label_components(hanger | body)
    keep = np.unique(labels[body])
    hanger = np.isin(labels, keep[keep > 0]) & hanger
    clamp = ((xx - gx) ** 2 + (yy - gy) ** 2 <= 9 ** 2) & changed
    # the painted bottom edge of the body can match a dark forest in the plate: extend the body 8 px down within
    # its columns (only cabin-like pixels of that strip go into the sprite, see cmd_cut)
    ys, xs = np.nonzero(body)
    ext = np.zeros_like(body)
    bottom = int(ys.max())
    ext[max(y0, bottom - 2):min(y1, bottom + 9), int(xs.min()):int(xs.max()) + 1] = True
    return body, _grow(hanger | clamp, 1) & _grow(changed, 1), ext & ~body


def cmd_cut(args: argparse.Namespace) -> None:
    room = args.room
    conf = CABINS[room]
    paint = np.asarray(Image.open(GAME / "assets" / "bg_natural" / f"{room}.webp").convert("RGB"), np.float32)
    plate_img = fit_to_frame(Image.open(WORK / f"{room}_plate_raw.png").convert("RGB"))
    plate = np.asarray(plate_img, np.float32)
    out = AMBIENT_ASSETS / room / "winter"
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    lum = lambda a: a @ np.array([0.299, 0.587, 0.114], np.float32)
    for name, c in conf["cabins"].items():
        x0, y0, x1, y1 = c["box"]
        pad = 40
        wx0, wy0, wx1, wy1 = max(0, x0 - pad), max(0, y0 - pad), min(1920, x1 + pad), min(1080, y1 + pad)
        ring = np.ones((wy1 - wy0, wx1 - wx0), bool)
        ring[y0 - wy0:y1 - wy0, x0 - wx0:x1 - wx0] = False
        dy, dx = phase_shift(lum(paint[wy0:wy1, wx0:wx1]) * ring, lum(plate[wy0:wy1, wx0:wx1]) * ring)
        win_p = paint[wy0:wy1, wx0:wx1]
        win_q = np.roll(plate, (dy, dx), axis=(0, 1))[wy0:wy1, wx0:wx1]
        lbox = (x0 - wx0, y0 - wy0, x1 - wx0, y1 - wy0)
        lgrip = (c["grip"][0] - wx0, c["grip"][1] - wy0)
        diff = np.abs(win_p - win_q).mean(axis=2)
        body, hanger, ext = cabin_mask(diff, lbox, lgrip)
        mask = body | hanger | (ext & (diff > 8))
        # hanger: replace only where the painting is darker than the plate (the dark hanger on sky); elsewhere the
        # plate may carry stray rope strokes the painting does not have
        darker = lum(win_p) < lum(win_q) - 8
        patch_area = body | ext | (hanger & _grow(darker, 1))
        # colour-match the plate to the painting on the pixels around the cabin (NB2 shifts the tones a little)
        around = _grow(mask, 14) & ~_grow(mask, 4)
        matched = win_q.copy()
        gains = []
        for ch in range(3):
            a = np.vstack([win_q[..., ch][around], np.ones(int(around.sum()))]).T
            g, o = np.linalg.lstsq(a, win_p[..., ch][around], rcond=None)[0]
            matched[..., ch] = win_q[..., ch] * g + o
            gains.append([round(float(g), 3), round(float(o), 1)])
        err_before = float(np.abs(win_p - win_q).mean(axis=2)[around].mean())
        err_after = float(np.abs(win_p - matched).mean(axis=2)[around].mean())
        # sprite: the painted cabin, matte from the mask (soft 0.7 px)
        alpha = _soft(mask, 0.7)
        sprite = np.dstack([win_p, alpha * 255]).clip(0, 255).astype(np.uint8)
        ys, xs = np.nonzero(alpha > 0.03)
        sx0, sy0, sx1, sy1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
        Image.fromarray(sprite[sy0:sy1, sx0:sx1], "RGBA").save(out / f"cabin_{name}.webp", lossless=True)
        pivot = [int(c["grip"][0] - (wx0 + sx0)), int(c["grip"][1] - (wy0 + sy0))]
        # clean patch: the matched plate where the cabin was (grown 4 px), feathered
        fa = _soft(_grow(body | ext, 4) | _grow(patch_area & ~body, 1), 1.5)
        patch = np.dstack([matched, fa * 255]).clip(0, 255).astype(np.uint8)
        ys, xs = np.nonzero(fa > 0.01)
        px0, py0, px1, py1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
        Image.fromarray(patch[py0:py1, px0:px1], "RGBA").save(out / f"plate_{name}.webp", lossless=True)
        report[name] = {"plate_shift_dy_dx": [int(dy), int(dx)], "tone_err_before_after": [round(err_before, 2),
                        round(err_after, 2)], "gain_offset_rgb": gains,
                        "cabin_sprite": f"{room}/winter/cabin_{name}.webp", "cabin_size": [int(sx1 - sx0), int(sy1 - sy0)],
                        "cabin_pivot": pivot, "cabin_top_left": [int(wx0 + sx0), int(wy0 + sy0)],
                        "plate": f"{room}/winter/plate_{name}.webp", "plate_pos": [int(wx0 + px0), int(wy0 + py0)]}
        k = 3
        size = ((wx1 - wx0) * k, (wy1 - wy0) * k)
        rv = Image.new("RGB", (size[0] * 3 + 20, size[1]), (0, 0, 0))
        rv.paste(Image.fromarray(win_p.astype(np.uint8)).resize(size), (0, 0))
        comp = win_p * (1 - fa[..., None]) + matched * fa[..., None]
        rv.paste(Image.fromarray(comp.clip(0, 255).astype(np.uint8)).resize(size), (size[0] + 10, 0))
        spr = Image.fromarray(sprite[sy0:sy1, sx0:sx1], "RGBA")
        chk = Image.new("RGBA", spr.size, (255, 0, 255, 255))
        chk.alpha_composite(spr)
        rv.paste(chk.convert("RGB").resize((spr.width * k, spr.height * k)), (size[0] * 2 + 20, 0))
        rv.save(WORK / f"{room}_cabin_{name}_review.png")
    (WORK / f"{room}_cabins.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))


# ----------------------------------------------------------------------------- layers

SKIER_PIVOT = [24, 44]
SNOWCAT_PIVOT = [48, 52]


def skier_layer(room: str, lid: str, colour: str, path, scale, speed: float, every, start, mask=None, clip=None,
                fade: float = 6) -> dict:
    layer = {"id": PREFIX + lid, "type": "tween_path", "texture": f"{room}/winter/skier_{colour}.webp",
             "pivot": SKIER_PIVOT, "path": path, "speed_px_s": speed, "scale": scale, "faces": "right",
             "direction": "forward", "every_s": every, "start_s": start, "fade_px": fade}
    if mask:
        layer["mask"] = mask
    if clip:
        layer["clip"] = clip
    return layer


def snowcat_layer(room: str, path, scale, speed: float, mask=None) -> dict:
    layer = {"id": PREFIX + "snowcat", "type": "tween_path", "texture": f"{room}/winter/snowcat.webp",
             "pivot": SNOWCAT_PIVOT, "path": path, "speed_px_s": speed, "scale": scale, "faces": "right",
             "direction": "alternate", "every_s": [3, 6], "start_s": [0.01, 0.01], "prewarm_s": 12,
             "speed_jitter": [1, 1], "fade_px": 14, "bob_px": 0.3, "bob_hz": 0.8}
    if mask:
        layer["mask"] = mask
    return layer


def cabin_layer(room: str, lid: str, sprite: str, path, scale, speed: float, every, clip=None, mask=None,
                prewarm: float = 0.0, start=(0.01, 0.01)) -> dict:
    """A gondola cabin riding a rope: the sprite pivot is the grip, so the path is the rope itself."""
    info = json.loads((WORK / f"{room}_cabins.json").read_text(encoding="utf-8"))[sprite]
    layer = {"id": PREFIX + lid, "type": "tween_path", "texture": info["cabin_sprite"], "pivot": info["cabin_pivot"],
             "path": path, "speed_px_s": speed, "speed_jitter": [1, 1], "scale": scale, "faces": "right",
             "direction": "forward", "every_s": every, "start_s": list(start), "bob_px": 0.5, "bob_hz": 0.35,
             "reduced_motion": "freeze"}
    if prewarm:
        layer["prewarm_s"] = prewarm
    if clip:
        layer["clip"] = clip
    if mask:
        layer["mask"] = mask
    return layer


def plate_layer(room: str, name: str) -> dict:
    info = json.loads((WORK / f"{room}_cabins.json").read_text(encoding="utf-8"))[name]
    return {"id": PREFIX + f"plate_{name}", "type": "cutout", "texture": info["plate"], "pos": info["plate_pos"]}


BREATH = {"preset": "steam", "emit_jitter": [2, 1], "pulse_on_s": 0.5, "rate": 8, "size": [9, 14],
          "speed_y": [-10, -4], "grow": 2.4, "lifetime": [1.3, 2.0], "color": "#f6f9ff", "fade_in": 0.15,
          "fade_out": 0.9, "max": 24, "reduced_motion": "hide"}


def hero_breath(alpha: float = 1.0) -> dict:
    """Adam's breath: emitted at his mouth (ParticleLayer follow 'hero'), in front of everything."""
    return {"id": PREFIX + "hero_breath", "type": "particles", "plane": "front", "follow": "hero",
            "follow_offset": [0.068, 0.118], "follow_push": 7, "pulse_s": [3.0, 4.2], "speed_x": [-2, 2],
            "alpha_range": [round(0.36 * alpha, 3), round(0.56 * alpha, 3)], "prewarm_s": 0, **BREATH}


def npc_breath_fields(npc: str, feet_y: float, alpha: float = 1.0) -> dict:
    """An NPC's breath at its mouth (ParticleLayer follow 'npc:<id>': the side it faces, its scale), y-sorted just
    in front of the speaker (plane actors), pulsed like breathing."""
    return {"plane": "actors", "sort_y": feet_y + 2, "follow": f"npc:{npc}", "follow_offset": [0.065, 0.118],
            "follow_push": 4, "pulse_s": [3.2, 4.6], "speed_x": [-2, 2],
            "alpha_range": [round(0.32 * alpha, 3), round(0.5 * alpha, 3)], **BREATH}


def npc_breath(lid: str, npc: str, feet_y: float, alpha: float = 1.0) -> dict:
    return {"id": PREFIX + lid, "type": "particles", **npc_breath_fields(npc, feet_y, alpha)}


def flurry(lid: str, rect, count: int, size, speed_y, wind: float, mask=None, plane=None, alpha=(0.5, 0.9),
           speed_x=(-8, 8), lifetime=(14, 24)) -> dict:
    layer = {"id": PREFIX + lid, "type": "particles", "preset": "snow", "emit_rect": rect, "count": count,
             "size": list(size), "speed_y": list(speed_y), "speed_x": list(speed_x), "wind": wind,
             "alpha_range": list(alpha), "lifetime": list(lifetime)}
    if mask:
        layer["mask"] = mask
    if plane:
        layer["plane"] = plane
    return layer


def powder(lid: str, rect, rate: float, speed_x, mask=None, clip=None, size=(10, 22), alpha=(0.1, 0.22)) -> dict:
    """Wind-blown snow off a roof edge or a ridge: soft white puffs that drift sideways and thin out."""
    layer = {"id": PREFIX + lid, "type": "particles", "preset": "steam", "emit_rect": rect, "rate": rate,
             "size": list(size), "speed_x": list(speed_x), "speed_y": [-4, 4], "wind": 4, "grow": 2.6,
             "spin": [-10, 10], "lifetime": [2.6, 4.6], "alpha_range": list(alpha), "color": "#ffffff",
             "fade_in": 0.5, "fade_out": 2.0, "max": 40}
    if mask:
        layer["mask"] = mask
    if clip:
        layer["clip"] = clip
    return layer


def sifting(lid: str, rect, rate: float, mask=None, plane=None) -> dict:
    """Fine powder sifting off laden branches / eaves now and then."""
    layer = {"id": PREFIX + lid, "type": "particles", "preset": "snow", "emit_rect": rect, "rate": rate,
             "size": [1.4, 3.2], "speed_y": [26, 60], "speed_x": [2, 12], "wind": 4, "lifetime": [1.6, 3.2],
             "alpha_range": [0.5, 0.9], "color": "#ffffff", "max": 40}
    if mask:
        layer["mask"] = mask
    if plane:
        layer["plane"] = plane
    return layer


def room_layers(room: str) -> tuple[list[dict], list[dict], dict, str]:
    """(layers inserted first = clean plates, layers appended, tweaks of existing layers by id, note)."""
    first: list[dict] = []
    last: list[dict] = []
    tweaks: dict = {}
    note = ""
    if room == "S42":
        first = [plate_layer("S42", n) for n in ("a", "b", "c")]
        left = [0, 0, 246, 279]
        right = [226, 0, 104, 1080]
        last = [
            # left: cabins come down the upper rope into the station and leave on the lower one
            cabin_layer("S42", "cabin_in_left", "a", [[-75, 94], [0, 152], [50, 192], [100, 235], [162, 279]],
                        [1.06, 0.95], 42, [5, 9], clip=left, prewarm=3.45),
            cabin_layer("S42", "cabin_out_left", "a", [[88, 281], [40, 255], [0, 232], [-80, 190]], [0.93, 1.05],
                        42, [6, 10], clip=left, start=(4, 6)),
            # right: out of the station on the upper rope (behind the spruce), back in on the lower one
            cabin_layer("S42", "cabin_out_right", "c", [[222, 319], [250, 336], [285, 350], [322, 368], [356, 382]],
                        [1.0, 0.92], 22, [6, 11], clip=right, prewarm=3.0),
            cabin_layer("S42", "cabin_in_right", "b", [[356, 388], [320, 383], [280, 374], [241, 359], [222, 352]],
                        [1.04, 0.98], 22, [6, 11], clip=right, prewarm=5.0),
            skier_layer("S42", "skier_summit", "red", [[978, 268], [942, 288], [966, 306], [926, 326], [950, 344],
                        [906, 364], [926, 382], [884, 400]], [0.14, 0.17], 13, [8, 16], [1, 4]),
            skier_layer("S42", "skier_mid", "blue", [[912, 334], [885, 350], [903, 368], [876, 386], [858, 404]],
                        [0.15, 0.17], 11, [10, 20], [5, 9]),
            skier_layer("S42", "skier_low", "yellow", [[835, 398], [800, 409], [765, 419], [736, 431], [748, 447],
                        [776, 461]], [0.16, 0.18], 12, [9, 18], [3, 7]),
            skier_layer("S42", "skier_low_b", "teal", [[830, 402], [796, 414], [760, 426], [742, 440], [764, 455]],
                        [0.16, 0.18], 14, [14, 26], [12, 16]),
            snowcat_layer("S42", [[1008, 322], [1052, 306], [1098, 296]], [0.11, 0.11], 3.0),
            powder("roof_hotel", [1110, 296, 460, 10], 0.9, [14, 34]),
            powder("roof_gable", [1640, 40, 160, 30], 0.5, [12, 30], size=(8, 18)),
            powder("summit_ridge", [580, 238, 400, 22], 0.8, [16, 36], size=(14, 30), alpha=(0.06, 0.15)),
            sifting("eaves_station", [0, 279, 245, 4], 0.6),
            hero_breath(),
        ]
        tweaks = {"nina_breath": npc_breath_fields("S42.NINA", 770)}
        note = ("Winter life (art/tools/winter_ambient.py, w_* layers): the gondola runs - the painted cabins are "
                "lifted off clean plates (w_plate_*) and ride the ropes into and out of the station (clipped by the "
                "station roof and the spruce), four skiers carve down the Chopok pistes, a snowcat grooms the slope "
                "under the summit, snow blows off the hotel roof, the gable and the summit ridge, powder sifts off "
                "the station eaves, Nina and Adam breathe steam (pulsed).")
    elif room == "S45":
        last = [
            skier_layer("S45", "skier_a", "red", [[1338, 232], [1305, 250], [1325, 268], [1290, 288], [1310, 306],
                        [1270, 324], [1290, 340]], [0.19, 0.22], 13, [8, 16], [1, 4]),
            skier_layer("S45", "skier_b", "blue", [[1482, 252], [1500, 268], [1470, 286], [1495, 304], [1455, 322]],
                        [0.2, 0.22], 11, [10, 20], [5, 9]),
            skier_layer("S45", "skier_c", "orange", [[1640, 264], [1606, 281], [1626, 298], [1590, 315],
                        [1600, 330]], [0.2, 0.22], 12, [9, 18], [3, 7]),
            skier_layer("S45", "skier_d", "purple", [[1340, 236], [1312, 258], [1296, 280], [1270, 304],
                        [1248, 326]], [0.19, 0.22], 16, [14, 28], [12, 18]),
            snowcat_layer("S45", [[1540, 292], [1620, 278], [1700, 264]], [0.13, 0.13], 3.5),
            powder("summit", [740, 132, 290, 26], 1.2, [18, 40], size=(16, 34), alpha=(0.08, 0.18)),
            powder("ridge_right", [1000, 170, 300, 30], 0.6, [16, 34], size=(12, 26), alpha=(0.06, 0.14)),
            sifting("rowan", [60, 40, 300, 160], 0.35),
            sifting("spruce_right", [1770, 40, 140, 480], 0.45),
            hero_breath(),
        ]
        note = ("Winter life (w_* layers): skiers carve down the pistes under the lift, a snowcat crawls across the "
                "broad slope, snow plumes blow off the Chopok summit and the right ridge, powder sifts off the rowan "
                "twigs and the laden spruce, Adam's breath steams.")
    elif room == "S48":
        first = [plate_layer("S48", "a")]
        clip = [0, 0, 72, 1080]
        last = [
            cabin_layer("S48", "cabin_in", "a", [[-80, 411], [0, 397], [42, 389], [80, 381]], [1.0, 0.97], 30,
                        [6, 11], clip=clip, prewarm=2.85),
            cabin_layer("S48", "cabin_out", "a", [[78, 368], [40, 372], [0, 377], [-80, 388]], [0.97, 1.0], 30,
                        [7, 12], clip=clip, start=(4, 7)),
            powder("rotunda_roof", [140, 356, 1030, 14], 1.6, [20, 46]),
            powder("pavilion_roof", [1170, 160, 750, 26], 1.0, [16, 36]),
            flurry("flurry", [-60, -30, 2040, 30], 26, (2.0, 4.2), (28, 52), 18, speed_x=(10, 30)),
            hero_breath(),
        ]
        note = ("Winter life (w_* layers): the gondola runs at the pylon (painted cabin on a clean plate, cabins "
                "pass behind the pylon), snow blows off the Rotunda ring roof and the pavilion roof, a light wind-"
                "driven flurry, Adam's breath steams.")
    elif room == "S50":
        first = [plate_layer("S50", "a")]
        clip = [96, 0, 1300, 532]
        last = [
            cabin_layer("S50", "cabin_down", "a", [[96, 350], [118, 366], [166, 399], [250, 456], [330, 512],
                        [420, 574]], [1.0, 1.08], 34, [8, 14], clip=clip, prewarm=1.7),
            cabin_layer("S50", "cabin_up", "a", [[340, 548], [250, 488], [160, 428], [80, 372]], [1.06, 0.97], 34,
                        [9, 15], clip=clip, start=(6, 9)),
            flurry("flurry_front", [-60, -40, 2040, 30], 9, (6, 10), (50, 80), 26, plane="front",
                   speed_x=(30, 60), alpha=(0.5, 0.8), lifetime=(10, 16)),
            powder("letters", [640, 455, 380, 10], 0.5, [24, 44], size=(8, 16)),
            hero_breath(),
        ]
        note = ("Winter life (w_* layers): the near gondola runs past the pylon (painted cabin on a clean plate, "
                "clipped at the pylon and the pavilion roof), wind-driven flakes in front, snow blows off the CHOPOK "
                "letters, Adam's breath steams.")
    elif room == "S67":
        last = [hero_breath()]
        tweaks = {"ivan_breath": npc_breath_fields("S67.IVAN", 790)}
        note = "Winter life (w_* layers): Adam's breath steams in the open station hall; Ivan's breath is pulsed."
    elif room == "S68":
        mask = "S68/natural/window_glass_mask.webp"
        last = [
            skier_layer("S68", "skier_field", "red", [[468, 500], [500, 512], [530, 526], [556, 540]], [0.2, 0.22],
                        9, [9, 16], [1, 4], mask=mask),
            skier_layer("S68", "skier_field_b", "blue", [[600, 516], [640, 528], [680, 540], [720, 552]],
                        [0.2, 0.22], 10, [12, 20], [6, 10], mask=mask),
            skier_layer("S68", "skier_forest", "yellow", [[1250, 462], [1215, 474], [1170, 488], [1120, 500]],
                        [0.2, 0.22], 11, [10, 18], [3, 6], mask=mask),
            snowcat_layer("S68", [[430, 552], [500, 544], [560, 536]], [0.11, 0.11], 2.5, mask=mask),
            flurry("flakes_window", [100, 200, 1400, 40], 24, (2.5, 5), (24, 46), 10, mask=mask, speed_x=(-60, -30),
                   lifetime=(8, 14)),
            npc_breath("turista_breath", "S68.TURISTA", 815, alpha=0.8),
            hero_breath(alpha=0.75),
        ]
        note = ("Winter life (w_* layers): skiers on the snowfields and the forest piste below, a snowcat far "
                "down, snowflakes streaming past the panes as the cabin climbs, Milos's and Adam's breath (the "
                "cabin is unheated).")
    elif room == "S43":
        last = [
            skier_layer("S43", "skier_door", "red", [[250, 450], [216, 466], [186, 480]], [0.24, 0.26], 9, [12, 24],
                        [2, 6], mask="S43/natural/door_glass_mask.webp"),
            flurry("flurry_door", [40, 380, 260, 20], 10, (2.2, 4.4), (24, 44), 10,
                   mask="S43/natural/door_glass_mask.webp", lifetime=(8, 14)),
            flurry("flurry_window", [1760, 250, 160, 20], 7, (2.2, 4.4), (24, 44), 10,
                   mask="S43/natural/window_glass_mask.webp", lifetime=(8, 14)),
        ]
        note = "Winter life (w_* layers): a skier on the slope behind the entrance, a light flurry outside the glass."
    elif room == "S44":
        mask = "S44/natural/window_glass_mask.webp"
        last = [
            skier_layer("S44", "skier_a", "red", [[372, 425], [395, 445], [410, 462], [400, 480], [388, 500]],
                        [0.15, 0.17], 6, [10, 18], [1, 4], mask=mask),
            skier_layer("S44", "skier_b", "teal", [[300, 440], [282, 452], [270, 464]], [0.15, 0.16], 5, [14, 24],
                        [6, 10], mask=mask),
            flurry("flurry_window", [90, 260, 340, 20], 14, (2.2, 4.4), (22, 40), 10, mask=mask, lifetime=(12, 20)),
        ]
        note = "Winter life (w_* layers): skiers on the slope behind the window, a light flurry outside."
    elif room == "S46":
        mask = "S46/natural/window_glass_mask.webp"
        last = [
            skier_layer("S46", "skier_a", "yellow", [[1600, 362], [1585, 375], [1560, 388], [1540, 400],
                        [1515, 410]], [0.17, 0.19], 8, [9, 16], [1, 4], mask=mask),
            skier_layer("S46", "skier_b", "blue", [[1700, 370], [1672, 381], [1690, 392], [1648, 404]],
                        [0.17, 0.19], 8, [12, 20], [5, 9], mask=mask),
            flurry("flurry_window", [1445, 270, 450, 20], 16, (2.2, 4.6), (22, 42), 10, mask=mask,
                   lifetime=(12, 20)),
            flurry("flurry_door", [50, 400, 220, 20], 8, (2.2, 4.4), (22, 42), 10,
                   mask="S46/natural/door_glass_mask.webp", lifetime=(10, 16)),
            powder("chalet_roof", [1490, 455, 300, 12], 0.5, [10, 24], mask=mask, size=(8, 16)),
        ]
        note = ("Winter life (w_* layers): skiers under the chairlift behind the window, snow blowing off the chalet "
                "roof, a light flurry outside the window wall and the entrance.")
    elif room == "S47":
        last = [
            flurry("flurry_window", [-40, 170, 1320, 20], 18, (2.0, 4.2), (24, 44), 16,
                   mask="S47/natural/window_glass_mask.webp", speed_x=(20, 50), lifetime=(10, 16)),
        ]
        note = "Winter life (w_* layers): a light wind-driven flurry outside the window wall."
    elif room == "S49":
        mask = "S49/natural/window_glass_mask.webp"
        last = [
            powder("rotunda_roof", [740, 300, 760, 14], 1.2, [18, 40], mask=mask, size=(8, 18)),
            flurry("flurry_window", [690, 240, 840, 20], 12, (2.0, 4.0), (24, 44), 14, mask=mask,
                   speed_x=(14, 40), lifetime=(10, 16)),
        ]
        note = "Winter life (w_* layers): snow blowing off the Rotunda roofs and a light flurry outside the window."
    return first, last, tweaks, note


def cmd_layers(args: argparse.Namespace) -> None:
    for room in args.rooms or ROOMS:
        path = AMBIENT_DATA / f"{room}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        first, last, tweaks, note = room_layers(room)
        layers = [l for l in data["layers"] if not str(l.get("id", "")).startswith(PREFIX)]
        for layer in layers:
            if layer.get("id") in tweaks:
                layer.update(tweaks[layer["id"]])
        data["layers"] = first + layers + last
        notes = data.get("notes", "")
        if " Winter life (" in notes:
            notes = notes[:notes.index(" Winter life (")]
        if note:
            notes = notes.rstrip() + " " + note.replace("Winter life (w_* layers)",
                                                        "Winter life (art/tools/winter_ambient.py, w_* layers)")
        data["notes"] = notes
        ids = [l["id"] for l in data["layers"]]
        assert len(ids) == len(set(ids)), (room, ids)
        for layer in first + last:
            for key in ("texture", "mask"):
                if key in layer:
                    f = AMBIENT_ASSETS / layer[key]
                    assert f.exists(), (room, layer["id"], f)
        path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(room, f"{len(first)} plates + {len(last)} winter layers; total {len(data['layers'])}")


def cmd_screens(args: argparse.Namespace) -> None:
    """In-engine evidence (hidden QA window via tools/qa_godot.py): a clean shot and motion frames per room in
    build/screens/jasna_winter/<room>/winter_life_*.png."""
    import paint_natural
    if not args.no_import:
        with paint_natural.ImportLock():
            paint_natural.godot(["--headless", "--import"], timeout=1200)
    for room in args.rooms or ROOMS:
        out = REPO / "build" / "screens" / "jasna_winter" / room
        out.mkdir(parents=True, exist_ok=True)
        base = ["--resolution", "1920x1080", "--", "--blocking", "natural"] + (args.state or []) + [
            "--room", room, "--fast-text", "--skip-lines"]
        tag = args.tag
        codes = [paint_natural.godot(base + ["--wait", "900", "--screenshot", str(out / f"{tag}_clean.png")], 300),
                 paint_natural.godot(base + ["--wait", "1200", "--frames", str(args.frames), "--interval",
                                             str(args.interval), "--screenshot", str(out / f"{tag}_motion.png")], 400)]
        print(room, "exit codes", codes, "->", out.relative_to(REPO))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--budget", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=2035)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("sprites")
    p.set_defaults(func=cmd_sprites)
    p = sub.add_parser("plate")
    p.add_argument("rooms", nargs="+")
    p.set_defaults(func=cmd_plate)
    p = sub.add_parser("cut")
    p.add_argument("room")
    p.set_defaults(func=cmd_cut)
    p = sub.add_parser("screens")
    p.add_argument("rooms", nargs="*")
    p.add_argument("--tag", default="winter_life")
    p.add_argument("--frames", type=int, default=10)
    p.add_argument("--interval", type=int, default=450)
    p.add_argument("--state", nargs="*", help="extra harness arguments before --room (e.g. --replay 60)")
    p.add_argument("--no-import", action="store_true")
    p.set_defaults(func=cmd_screens)
    p = sub.add_parser("layers")
    p.add_argument("rooms", nargs="*")
    p.set_defaults(func=cmd_layers)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
