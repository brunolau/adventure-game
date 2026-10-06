"""S69 Sokolikovsky dvor (1995): minimal edits on the owner-loved style-test painting
art/backgrounds/sokolikova-yard.png (imported unchanged as art/masters/bg_natural/S69_v1.png).

Spec: docs/story/SOKOLIKOVA_YARD.md sections 1 and 6.1. Method of S18 (S18_scripts/edit_on_base.py, "guide" mode):
image 1 = the clean painting, image 2 = the painting with flat placeholder shapes; ONE nano-banana-pro edit paints
the new 3D objects (the green bench, Kubo's bike) and only the edit boxes are composited back, so the rest of the
painting stays pixel-identical. Flat things painted ON surfaces (the chalk hopscotch, the school club's painting on
three wall panels, Kubo's chalk tally) are drawn locally (`decals`): exact shapes and counts (three waves, two
strokes, six pieces: the P03 clue), the concrete / asphalt texture shows through the paint.

  canvas                     placeholder preview (free)
  paint --budget USD [--seed N]   one paid edit (USD 0.15) -> next master version + sidecar
  composite --base V --raw RAW    re-composite a raw output with the spec boxes (free)
  decals --base V            hopscotch + wall painting + tally on vV -> next version (free)
  review V                   grid crops of the edited areas (free)

Run from the repo root: PYTHONIOENCODING=utf-8 python -X utf8 art/masters/bg_natural/S69_scripts/s69_paint.py ...
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "art" / "tools"))
import content_v2_budget as budget  # noqa: E402
import fal_api  # noqa: E402
import paint_natural  # noqa: E402
import paint_room as pr  # noqa: E402
import refit_room  # noqa: E402

paint_natural.install()
ROOM = "S69"
SCOPE = "bg_natural/S69/"
REVIEW = ROOT / "art" / "review" / "natural"


def m(x: float, y: float) -> tuple[float, float]:
    return refit_room.to_master(x, y)


def poly(points):
    return [m(x, y) for x, y in points]


# --------------------------------------------------------------------------- camera (measured, see S69.md)
# Two-point perspective of the walled court: the right wall's top and foot meet at VP_L (-1146, ~478), the back
# wall's at VP_R (2836, ~470); horizon y ~475. With the principal point at x 960 the two orthogonal VPs give a focal
# length f = sqrt((960 + 1146) * (2836 - 960)) ~ 1988 px (a nearly level camera). The camera height follows from the
# objects the edit painted (bench seat 0.45 m, 16-inch bike wheels) and the walls: c ~ 2.45 m (right wall ~1.3 m,
# low back wall ~0.7 m, the near wall ~1.4 m, the passage ~1.1 m). Hero scale (y - 475) / 729.
VP_L = (-1146.0, 478.0)
VP_R = (2836.0, 470.0)
HORIZON = 475.0
CAM_H = 2.45
FOCAL = math.sqrt((960 + 1146) * (2836 - 960))
CX = 960.0


def px_per_m(y: float) -> float:
    return (y - HORIZON) / CAM_H


def ground_of(x: float, y: float) -> tuple[float, float]:
    """screen -> ground (X right, Z forward, metres)"""
    z = FOCAL * CAM_H / (y - HORIZON)
    return (x - CX) * z / FOCAL, z


def screen_of(gx: float, gz: float) -> tuple[float, float]:
    return CX + FOCAL * gx / gz, HORIZON + FOCAL * CAM_H / gz


def axis(vp) -> tuple[float, float]:
    """unit ground direction towards a vanishing point"""
    ang = math.atan2(vp[0] - CX, FOCAL)
    return math.sin(ang), math.cos(ang)


E_L, E_R = axis(VP_L), axis(VP_R)          # along the right wall (to VP_L), along the back wall (to VP_R)


def ground_rect(origin_screen, along, across, length_m, width_m):
    """screen quad (plane corners (0,0) (1,0) (1,1) (0,1)) of a ground rectangle that starts at origin_screen
    (the middle of its near short side), runs `length_m` along `along` and is `width_m` wide along `across`."""
    ox, oz = ground_of(*origin_screen)
    hx, hz = across[0] * width_m / 2, across[1] * width_m / 2
    fx, fz = along[0] * length_m, along[1] * length_m
    far_a = screen_of(ox + fx - hx, oz + fz - hz)
    far_b = screen_of(ox + fx + hx, oz + fz + hz)
    near_b = screen_of(ox + hx, oz + hz)
    near_a = screen_of(ox - hx, oz - hz)
    return [far_a, far_b, near_b, near_a]


def homography(src, dst) -> np.ndarray:
    a = []
    for (x, y), (u, v) in zip(src, dst):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        a.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, vt = np.linalg.svd(np.asarray(a, float))
    h = vt[-1].reshape(3, 3)
    return h / h[2, 2]


# --------------------------------------------------------------------------- placeholders for the paid edit

BENCH_GREEN, BENCH_DARK, LEG = "#3f7a3c", "#2c5a2c", "#5b5f62"
BIKE_RED, TYRE = "#c8322a", "#1e1e20"


def shapes(d: ImageDraw.ImageDraw) -> None:
    # Green wooden bench at the right edge of the court, backrest towards the grass bank, facing into the court.
    d.polygon(poly([(1716, 792), (1912, 786), (1912, 820), (1716, 826)]), fill=BENCH_GREEN)        # backrest slats
    d.polygon(poly([(1708, 846), (1914, 840), (1918, 862), (1704, 870)]), fill=BENCH_GREEN)        # seat
    d.polygon(poly([(1704, 870), (1918, 862), (1918, 866), (1704, 874)]), fill=BENCH_DARK)         # seat edge
    for x in (1722, 1896):
        d.polygon(poly([(x - 6, 786), (x + 6, 786), (x + 6, 880), (x - 6, 880)]), fill=LEG)        # side frames
    # Kubo's small bike with stabilisers, standing on the court left of the bench, front wheel to the left.
    for cx in (1502, 1598):
        d.ellipse([*m(cx - 27, 897), *m(cx + 27, 951)], outline=TYRE, width=6)
    d.ellipse([*m(1611, 932), *m(1629, 950)], outline=TYRE, width=4)                               # stabiliser
    d.line([m(1502, 924), m(1540, 890), m(1584, 892), m(1598, 924), m(1556, 926), m(1502, 924)], fill=BIKE_RED,
           width=7)
    d.line([m(1540, 890), m(1530, 866)], fill=BIKE_RED, width=6)                                   # fork / stem
    d.line([m(1516, 862), m(1546, 866)], fill="#3a3a3c", width=6)                                  # handlebar
    d.line([m(1584, 892), m(1588, 872)], fill=BIKE_RED, width=6)
    d.polygon(poly([(1574, 866), (1604, 866), (1600, 874), (1576, 874)]), fill="#2a2a2a")          # saddle


BOXES = [(1626, 744, 1920, 908), (1452, 836, 1664, 982)]   # composite boxes (game px): bench, bike (+ shadows)
FEATHER = 30

PROMPT = (
    "You receive 2 images. Image 1 is one of our finished point-and-click adventure game backgrounds: the walled "
    "courtyard playground between early-1970s panel housing blocks on Sokolikova street in Dubravka, Bratislava, on "
    "a June afternoon in 1995 - a worn asphalt court surrounded by walls of upright concrete panels, a birch and a "
    "blue spruce behind the low back wall, a grass bank at the bottom right. Image 2 is the same painting with flat "
    "colour placeholder shapes that ONLY show where two new objects must stand and how big they are. Edit image 1: "
    "add the two new objects exactly where and exactly as large as the placeholders in image 2, painted in the same "
    "loose painterly brushwork, palette and warm afternoon light as the rest of image 1 - not flat, not clean vector "
    "graphics. Keep everything else in image 1 exactly as it is: the walls, the panels, the trees, the blocks, the "
    "lamp, the court, the grass bank, the light and the shadows.\n\n"
    "1. At the right edge of the court, where the grass bank begins (from 89 % to 100 % of the width, the seat at "
    "about 79 % of the height): a plain park bench of a 1990s Slovak housing estate, freshly painted: green-painted "
    "wooden slats on the seat and the backrest, two simple dark grey steel side frames as legs, standing on the "
    "asphalt with its backrest towards the grass bank, facing into the court towards the left, empty. Its right end "
    "may touch the long grass of the bank.\n"
    "2. Left of the bench on the asphalt (from 76 % to 85 % of the width, wheels on the ground at 87 % of the "
    "height): a small child's bicycle with 16-inch wheels and two little stabiliser wheels at the back, seen from "
    "its side, standing upright on its stabilisers with the front wheel to the left; a plain red frame without any "
    "brand or lettering, black tyres, a black saddle, a plain silver handlebar with a small round bell on the left "
    "grip whose top cap is missing.\n\n"
    "Both objects stand firmly on the ground and cast soft shadows on the asphalt in the same direction and softness "
    "as the shadows already in image 1. No people, no animals, no text, no letters, no numbers, no logos and no brand "
    "names; do not add or remove anything else. Image 2 is a positioning aid only: do not copy its flat shapes. The "
    "result is image 1 edited, same 16:9 framing, no frames, borders or captions."
)


def base_image(version: int) -> Image.Image:
    img, _ = refit_room.load_master(ROOM, version)
    return img


def canvas_of(base: Image.Image) -> Image.Image:
    canvas = base.copy()
    shapes(ImageDraw.Draw(canvas))
    return canvas


def preview(canvas: Image.Image, name: str) -> Path:
    frame = pr.fit_to_frame(canvas).convert("RGB")
    d = ImageDraw.Draw(frame)
    for x0, y0, x1, y1 in BOXES:
        d.rectangle([x0, y0, x1, y1], outline=(255, 0, 255), width=2)
    out = REVIEW / f"{ROOM}_{name}_canvas_preview.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.save(out)
    return out


def mask_for(boxes) -> Image.Image:
    mask = Image.new("L", pr.MODEL_FRAME, 0)
    for x0, y0, x1, y1 in boxes:
        bx0, by0 = m(x0, y0)
        bx1, by1 = m(x1, y1)
        touch = (x0 <= 0, y0 <= 0, x1 >= pr.FRAME[0], y1 >= pr.FRAME[1])
        mbox = (0 if touch[0] else round(bx0), 0 if touch[1] else round(by0),
                pr.MODEL_FRAME[0] if touch[2] else round(bx1), pr.MODEL_FRAME[1] if touch[3] else round(by1))
        one = refit_room.soft_mask(pr.MODEL_FRAME, mbox, round(FEATHER / refit_room.K), tuple(not t for t in touch))
        mask = ImageChops.lighter(mask, one)
    return mask


def composite(base: Image.Image, result: Image.Image, boxes) -> tuple[Image.Image, tuple[int, int]]:
    mask = mask_for(boxes)
    outside = mask.point(lambda v: 255 if v == 0 else 0)
    dx, dy = refit_room.align_shift(result, base, outside)
    if dx or dy:
        result = ImageChops.offset(result, -dx, -dy)
        print(f"model output drifted by {dx:+d},{dy:+d} master px; compensated")
    return Image.composite(result, base, mask), (dx, dy)


def save(img: Image.Image, meta: dict) -> int:
    version = pr.next_version(ROOM)
    out = pr.MASTERS / f"{ROOM}_v{version}.png"
    img.save(out)
    meta = dict(meta, room=ROOM, version=version, output_size=list(img.size))
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{out.relative_to(ROOT)}")
    return version


def cmd_canvas(args) -> None:
    print(preview(canvas_of(base_image(args.base)), "bench_bike").relative_to(ROOT))


def cmd_paint(args) -> None:
    base = base_image(args.base)
    canvas = canvas_of(base)
    preview(canvas, "bench_bike")
    prompt = PROMPT + "\n\n" + pr.style_sentence()
    seed = args.seed if args.seed is not None else random.randint(1, 2 ** 31 - 1)
    version = pr.next_version(ROOM)
    asset = f"{SCOPE}{ROOM}_v{version}_bench_bike"
    images = [fal_api.image_data_uri(base, fmt="PNG"), fal_api.image_data_uri(canvas, max_side=2048, fmt="JPEG")]
    arguments = {"prompt": prompt, "image_urls": images, "aspect_ratio": pr.ASPECT, "resolution": pr.RESOLUTION,
                 "output_format": "png", "num_images": 1, "seed": seed}
    price = fal_api.IMAGE_PRICES[(pr.MODEL, pr.RESOLUTION)]
    started = datetime.datetime.now().isoformat(timespec="seconds")
    result = budget.run(pr.MODEL, arguments, asset, price, timeout_s=900)
    raw_path = pr.MASTERS / f"_{ROOM}_v{version}_bench_bike_raw.png"
    fal_api.download(result["images"][0]["url"], raw_path)
    raw = Image.open(raw_path).convert("RGB")
    if raw.size != pr.MODEL_FRAME:
        raw = raw.resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    final, drift = composite(base, raw, BOXES)
    save(final, {"kind": "edit", "from_version": args.base, "spec": "bench_bike (guide mode)",
                 "boxes_game_px": BOXES, "feather_game_px": FEATHER, "drift_compensated_master_px": list(drift),
                 "model": pr.MODEL, "seed": result.get("seed", seed), "usd": price, "scope": SCOPE,
                 "spend_log_asset": asset, "prompt": prompt,
                 "image_urls": [f"art/masters/bg_natural/{ROOM}_v{args.base}.png",
                                "the same + placeholder shapes (S69_scripts/s69_paint.py shapes, guide)"],
                 "raw_model_output": raw_path.relative_to(ROOT).as_posix(), "started": started,
                 "model_description": result.get("description")})


def cmd_composite(args) -> None:
    base = base_image(args.base)
    raw = Image.open(ROOT / args.raw).convert("RGB").resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    boxes = [tuple(b) for b in args.box] if args.box else BOXES
    final, drift = composite(base, raw, boxes)
    save(final, {"kind": "edit-recomposite", "from_version": args.base, "boxes_game_px": boxes, "usd": 0,
                 "raw_model_output": args.raw, "drift_compensated_master_px": list(drift),
                 "started": datetime.datetime.now().isoformat(timespec="seconds")})


# --------------------------------------------------------------------------- objects from the raw edit (free)
# The v2 guide-mode edit painted a convincing bench and bike, but at its own (larger, and in this painting more
# consistent) scale and place: bench x 1428-1790 y 738-1035 on the bank edge, bike x 1195-1420 y 735-945. The camera
# was re-measured with them (S69.md "Camera"). The bench stays where the model put it; the bike is moved into the
# left strip of the court (in front of the low back wall, left of centre) so that the centre stays free for the
# hopscotch and Zuzana can stand by the bench. Everything else stays the owner's painting.

BENCH_REGION = (1416, 726, 1812, 1052)      # game px: where the raw's changes belong to the bench (+ its shadow)
BIKE_REGION = (1176, 724, 1432, 1004)       # game px: the raw bike + its shadow
BIKE_CONTACT = (1320, 940)                  # game px in the raw: midpoint of the two wheel contacts
BIKE_TARGET = (1012, 836)                   # game px: where that midpoint goes (left strip, wheels on y ~836)
# The edit painted the bike ~1.5x too large for a 16-inch child's bike next to its own bench (handlebar ~1.06 m at
# the new place instead of ~0.7 m; seen in-engine next to Kubo, 1.18 m): extra size factor on top of the perspective.
BIKE_SIZE_FIX = 0.66


def to_master_arr(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("RGB"), np.float32)


def g2m_box(box):
    x0, y0 = m(box[0], box[1])
    x1, y1 = m(box[2], box[3])
    return round(x0), round(y0), round(x1), round(y1)


def change_masks(raw: np.ndarray, base: np.ndarray, box) -> tuple[np.ndarray, np.ndarray]:
    """(object mask, shadow factor map) of the raw's changes inside a master-px box."""
    x0, y0, x1, y1 = box
    r = raw[y0:y1, x0:x1]
    b = base[y0:y1, x0:x1]
    diff = np.abs(r - b).mean(axis=2)
    changed = diff > 14
    lum_r, lum_b = r.mean(axis=2) + 1, b.mean(axis=2) + 1
    ratio = lum_r / lum_b
    nr = r / lum_r[..., None]
    nb = b / lum_b[..., None]
    chroma = np.abs(nr - nb).max(axis=2)
    shadowish = changed & (ratio > 0.32) & (ratio < 0.95) & (chroma < 0.10)
    obj = changed & ~shadowish
    # clean the object mask: close small gaps, drop specks
    im = Image.fromarray((obj * 255).astype(np.uint8), "L")
    im = im.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MinFilter(3)) \
        .filter(ImageFilter.MaxFilter(3))
    obj = np.asarray(im) > 128
    factor = np.ones_like(r)
    sh = shadowish & ~obj
    factor[sh] = np.clip(r[sh] / np.maximum(b[sh], 1), 0.3, 1.0)
    fac_img = [Image.fromarray(((factor[..., c]) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(2))
               for c in range(3)]
    factor = np.stack([np.asarray(f, np.float32) / 255 for f in fac_img], axis=2)
    return obj, factor


# Generous envelope of the raw bike (game px): handlebar, saddle, frame, both wheels and the stabiliser, but not its
# cast shadow on the ground (that is re-drawn at the new place); wheel discs are filled so the spokes keep the raw's
# asphalt behind them.
BIKE_ENVELOPE = [(1276, 735), (1382, 730), (1386, 751), (1362, 768), (1356, 800), (1374, 828), (1398, 840),
                 (1418, 868), (1419, 926), (1402, 947), (1350, 947), (1331, 928), (1326, 893), (1306, 906),
                 (1272, 909), (1240, 911), (1222, 919), (1191, 919), (1189, 885), (1202, 874), (1204, 830),
                 (1224, 811), (1246, 800), (1244, 771), (1275, 767)]
BIKE_WHEELS = [(1331, 846, 1415, 944), (1206, 817, 1275, 909), (1193, 883, 1220, 917)]   # ellipses (game px)


def bike_alpha(raw: np.ndarray, base: np.ndarray) -> Image.Image:
    """Alpha of the raw bike in master px (full frame): the raw's changed pixels inside the envelope. Asphalt seen
    between the spokes and inside the frame is unchanged in the raw, so it stays transparent and the new place's
    own asphalt shows through (no halo of the old place's lighter ground)."""
    env = Image.new("L", pr.MODEL_FRAME, 0)
    ImageDraw.Draw(env).polygon(poly(BIKE_ENVELOPE), fill=255)
    diff = np.abs(raw - base).mean(axis=2) > 18
    changed = Image.fromarray((diff * 255).astype(np.uint8), "L").filter(ImageFilter.MinFilter(3))         .filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
    a = ImageChops.multiply(env, changed)
    return a.filter(ImageFilter.GaussianBlur(0.8))


def bike_placement(raw_img: Image.Image, base_img: Image.Image):
    """(sprite RGBA in master px, offset (ox, oy) in master px, scale) of the moved bike (shared by `objects` and the
    occluder texture of s69_build.py)."""
    base = to_master_arr(base_img)
    raw = to_master_arr(raw_img)
    f = (BIKE_TARGET[1] - HORIZON) / (BIKE_CONTACT[1] - HORIZON) * BIKE_SIZE_FIX
    alpha = bike_alpha(raw, base)
    bbox = alpha.getbbox()
    spr = raw_img.convert("RGBA")
    spr.putalpha(alpha)
    spr = spr.crop(bbox)
    nw, nh = max(1, round(spr.width * f)), max(1, round(spr.height * f))
    spr = spr.resize((nw, nh), Image.Resampling.LANCZOS)
    cmx, cmy = m(*BIKE_CONTACT)
    tmx, tmy = m(*BIKE_TARGET)
    ox = round(tmx - (cmx - bbox[0]) * f)
    oy = round(tmy - (cmy - bbox[1]) * f)
    return spr, (ox, oy), f, bbox


def cmd_objects(args) -> None:
    base_img = base_image(args.base)
    raw_img = Image.open(ROOT / args.raw).convert("RGB").resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    base = to_master_arr(base_img)
    raw = to_master_arr(raw_img)
    out = base.copy()
    # bench (in place): the raw inside the bench region where it changed (object + shadow), soft edge
    x0, y0, x1, y1 = g2m_box(BENCH_REGION)
    diff = np.abs(raw[y0:y1, x0:x1] - base[y0:y1, x0:x1]).mean(axis=2) > 10
    a = Image.fromarray((diff * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(7))         .filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(2.0))
    # fade the region border so nothing outside BENCH_REGION is touched
    border = refit_room.soft_mask((x1 - x0, y1 - y0), (0, 0, x1 - x0, y1 - y0), 16, (True, True, x1 < pr.MODEL_FRAME[0], True))
    a = np.asarray(ImageChops.multiply(a, border), np.float32)[..., None] / 255
    out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - a) + raw[y0:y1, x0:x1] * a
    # bike (moved and scaled by the perspective ratio and the size fix)
    spr, (ox, oy), f, bbox = bike_placement(raw_img, base_img)
    nw, nh = spr.size
    cmx, cmy = m(*BIKE_CONTACT)
    # cast shadow: the sun is behind the trees at the upper right, shadows fall to the lower left and are soft
    sa = np.asarray(spr, np.float32)[..., 3] / 255
    sh = Image.fromarray((sa * 255).astype(np.uint8), "L")
    contact_local = (cmy - bbox[1]) * f                    # contact line in sprite px
    sq = 0.30                                              # flattened onto the ground
    sh_h = max(1, round(nh * sq))
    sh = sh.resize((nw, sh_h), Image.Resampling.BILINEAR)
    shadow = Image.new("L", pr.MODEL_FRAME, 0)
    shear_px = round(nw * 0.18)
    sh = sh.transform((nw + shear_px, sh_h), Image.Transform.AFFINE, (1, -shear_px / sh_h, 0, 0, 1, 0),
                      Image.Resampling.BILINEAR)
    sy = round(oy + contact_local - sh_h * 0.92)
    shadow.paste(sh, (ox - shear_px + round(nw * 0.02), sy))
    shadow = shadow.filter(ImageFilter.GaussianBlur(5)).point(lambda v: round(v * 0.55))
    sh_arr = np.asarray(shadow, np.float32)[..., None] / 255
    tint = np.asarray([0.55, 0.56, 0.66], np.float32)[None, None, :]
    out = out * (1 - sh_arr) + out * tint * sh_arr
    final = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    final.alpha_composite(spr, (ox, oy))
    final = final.convert("RGB")
    save(final, {"kind": "objects from the raw edit (free)", "from_version": args.base, "raw": args.raw, "usd": 0,
                 "bench_region_game_px": BENCH_REGION, "bike_envelope_game_px": BIKE_ENVELOPE,
                 "bike_move_game_px": {"contact_from": BIKE_CONTACT, "contact_to": BIKE_TARGET,
                                       "scale": round(f, 4), "size_fix": BIKE_SIZE_FIX},
                 "note": "bench kept where the model painted it (raw pixels where they changed inside the bench "
                         "region); bike cut along its silhouette, scaled by the perspective ratio (y - 475) x the size fix and "
                         "moved into the left strip with a re-drawn soft cast shadow (sun at the upper right); "
                         "everything else is the base version pixel for pixel",
                 "started": datetime.datetime.now().isoformat(timespec="seconds")})


# --------------------------------------------------------------------------- local decals (free)

def chalk_layer(size, draw_fn, seed: int, width_px: float) -> np.ndarray:
    """Alpha (0..1) of rough chalk strokes drawn at 4x on a canvas of `size` (game px)."""
    sc = 4
    big = Image.new("L", (size[0] * sc, size[1] * sc), 0)
    draw_fn(ImageDraw.Draw(big), sc)
    a = np.asarray(big, np.float32) / 255
    rng = np.random.default_rng(seed)
    grain = rng.random(a.shape).astype(np.float32)
    a = a * (0.55 + 0.45 * grain)                 # chalk is grainy, the asphalt shows through
    img = Image.fromarray((a * 255).astype(np.uint8), "L").resize(size, Image.Resampling.LANCZOS)
    img = img.filter(ImageFilter.GaussianBlur(0.35))
    return np.asarray(img, np.float32) / 255


def apply_chalk(frame: np.ndarray, alpha: np.ndarray, colour=(236, 234, 226), strength=0.82) -> None:
    """Chalk on asphalt / concrete: lighten towards chalk white, keep the local light (shadows stay darker)."""
    lum = frame.mean(axis=2, keepdims=True) / 255
    light = np.clip(0.45 + lum * 0.9, 0.5, 1.1)
    target = np.asarray(colour, np.float32)[None, None, :] * light
    a = (alpha * strength)[..., None]
    frame[:] = frame * (1 - a) + np.minimum(target, 255) * a


def hopscotch_alpha(frame_size, quad) -> np.ndarray:
    """Classic Slovak 'skolka': 1, 2, 3, 4-5 (pair), 6, 7-8 (pair) and a half circle at the top: 8 squares in
    total plus the half circle (look.S69.court). Drawn on a ground plane 1.0 m x 4.6 m, warped into `quad`."""
    W, H = 80, 300                                 # plane units = cm (squares of 40 cm, Slovak 'skolka')
    sc = 4
    plane = Image.new("L", (W * sc, H * sc), 0)
    d = ImageDraw.Draw(plane)
    lw = 4 * sc
    rng = random.Random(1995)

    def wob(v):
        return v + rng.uniform(-1.2, 1.2) * sc

    def rect(x0, y0, x1, y1):
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        d.line([(wob(x * sc), wob(y * sc)) for x, y in pts], fill=255, width=lw, joint="curve")
    y = H
    cells = [("single",), ("single",), ("single",), ("pair",), ("single",), ("pair",)]
    s = 40
    for cell in cells:
        if cell[0] == "single":
            rect(20, y - s, 60, y)
        else:
            rect(0, y - s, 40, y)
            rect(40, y - s, 80, y)
        y -= s
    # half circle at the top ("nebo")
    d.arc([0 * sc, (y - 40) * sc, 80 * sc, (y + 40) * sc], 180, 360, fill=255, width=lw)
    # numbers are left out on purpose (no lettering in backgrounds; the look describes the squares)
    a_plane = np.asarray(plane, np.float32) / 255
    rng2 = np.random.default_rng(7)
    a_plane = a_plane * (0.5 + 0.5 * rng2.random(a_plane.shape).astype(np.float32))
    plane_img = Image.fromarray((a_plane * 255).astype(np.uint8), "L")
    # map plane (u right, v down = towards the viewer) to the screen quad
    src = [(0, 0), (W * sc, 0), (W * sc, H * sc), (0, H * sc)]
    h = homography(quad, src)                      # screen -> plane (PIL wants the inverse mapping)
    coeffs = (h / h[2, 2]).flatten()[:8]
    warped = plane_img.transform(frame_size, Image.Transform.PERSPECTIVE, tuple(coeffs), Image.Resampling.BICUBIC)
    warped = warped.filter(ImageFilter.GaussianBlur(0.45))
    return np.asarray(warped, np.float32) / 255


def paint_on_wall(frame: np.ndarray, alpha: np.ndarray, colour, strength=0.9) -> None:
    """Emulsion paint on weathered concrete: the colour takes the panel's light and texture (darker where the
    concrete is darker), slightly matt."""
    lum = frame.mean(axis=2, keepdims=True)
    ref = np.median(lum[alpha > 0.5]) if (alpha > 0.5).any() else 128.0
    shade = np.clip(lum / max(ref, 1.0), 0.6, 1.25) ** 0.7
    col = np.asarray(colour, np.float32)[None, None, :] * shade
    a = (alpha * strength)[..., None]
    frame[:] = frame * (1 - a) + np.clip(col, 0, 255) * a


def shape_alpha(size, draw_fn, seed: int, rough: float = 0.6) -> np.ndarray:
    sc = 4
    big = Image.new("L", (size[0] * sc, size[1] * sc), 0)
    draw_fn(ImageDraw.Draw(big), sc)
    big = big.filter(ImageFilter.GaussianBlur(sc * 0.6))
    a = np.asarray(big, np.float32) / 255
    rng = np.random.default_rng(seed)
    noise = Image.fromarray((rng.random((size[1] // 2 + 1, size[0] // 2 + 1)) * 255).astype(np.uint8), "L") \
        .resize((size[0] * sc, size[1] * sc), Image.Resampling.BICUBIC)
    n = np.asarray(noise, np.float32) / 255
    a = np.clip((a - 0.5) * 3.0 + 0.5 + (n - 0.5) * rough, 0, 1)      # brushy edge
    wear = np.asarray(Image.fromarray((rng.random((size[1] * sc // 6 + 1, size[0] * sc // 6 + 1)) * 255)
                                      .astype(np.uint8), "L").resize((size[0] * sc, size[1] * sc),
                                                                     Image.Resampling.BICUBIC), np.float32) / 255
    a = a * np.clip(0.78 + wear * 0.35, 0, 1)                           # weathered, a little patchy
    img = Image.fromarray((a * 255).astype(np.uint8), "L").resize(size, Image.Resampling.LANCZOS)
    return np.asarray(img, np.float32) / 255


# The three right-wall panels next to the passage (measured on the painting, game px): left edge, right edge, top
# and foot of each panel face.
PANELS = [(1381, 1440, 586, 700), (1447, 1497, 590, 703), (1502, 1549, 594, 706)]


def wall_painting(frame: np.ndarray) -> list[tuple[str, tuple[int, int, int, int]]]:
    """The school club's painting (the S17 sign's content): panel 1 the four shapes (red circle, blue triangle,
    yellow square, purple V); panel 2 THREE WAVES (one green zigzag with three peaks) over TWO black STROKES;
    panel 3 SIX red PIECES in a column. Returns the boxes it painted (for the review)."""
    H, W = frame.shape[:2]
    red, blue, yellow, purple, green, black = (196, 62, 48), (52, 102, 196), (226, 178, 52), (132, 70, 164), \
        (52, 138, 82), (36, 34, 36)
    painted = []

    def on_panel(i, fn, colour, seed):
        x0, x1, top, foot = PANELS[i]
        box = (x0, top, x1, foot)
        w, h = x1 - x0, foot - top
        a = shape_alpha((w, h), lambda d, sc: fn(d, sc, w, h), seed)
        full = np.zeros((H, W), np.float32)
        full[top:foot, x0:x1] = a
        paint_on_wall(frame, full, colour)
        painted.append((f"panel{i + 1}", box))

    # panel 1: four shapes stacked (circle, triangle, square, V)
    def circle(d, sc, w, h):
        cx, cy, r = w * 0.5, h * 0.17, w * 0.24
        d.ellipse([(cx - r) * sc, (cy - r) * sc, (cx + r) * sc, (cy + r) * sc], fill=255)

    def triangle(d, sc, w, h):
        cx, cy, r = w * 0.5, h * 0.40, w * 0.27
        d.polygon([(cx * sc, (cy - r) * sc), ((cx + r) * sc, (cy + r * 0.8) * sc), ((cx - r) * sc, (cy + r * 0.8) * sc)],
                  fill=255)

    def square(d, sc, w, h):
        cx, cy, r = w * 0.5, h * 0.62, w * 0.21
        d.rectangle([(cx - r) * sc, (cy - r) * sc, (cx + r) * sc, (cy + r) * sc], fill=255)

    def vee(d, sc, w, h):
        cx, cy, r = w * 0.5, h * 0.84, w * 0.22
        d.polygon([((cx - r) * sc, (cy - r) * sc), ((cx - r * 0.35) * sc, (cy - r) * sc), (cx * sc, (cy + r * 0.1) * sc),
                   ((cx + r * 0.35) * sc, (cy - r) * sc), ((cx + r) * sc, (cy - r) * sc),
                   ((cx + r * 0.2) * sc, (cy + r) * sc), ((cx - r * 0.2) * sc, (cy + r) * sc)], fill=255)
    on_panel(0, circle, red, 11)
    on_panel(0, triangle, blue, 12)
    on_panel(0, square, yellow, 13)
    on_panel(0, vee, purple, 14)

    # panel 2: three waves (a zigzag with three peaks) and below it two vertical strokes
    def waves(d, sc, w, h):
        pts = []
        y_lo, y_hi = h * 0.36, h * 0.18
        for k in range(7):
            pts.append((w * (0.1 + 0.8 * k / 6) * sc, (y_lo if k % 2 == 0 else y_hi) * sc))
        d.line(pts, fill=255, width=round(w * 0.11 * sc), joint="curve")

    def strokes(d, sc, w, h):
        for cx in (w * 0.36, w * 0.64):
            d.rectangle([(cx - w * 0.06) * sc, h * 0.52 * sc, (cx + w * 0.06) * sc, h * 0.82 * sc], fill=255)
    on_panel(1, waves, green, 21)
    on_panel(1, strokes, black, 22)

    # panel 3: six red pieces in two columns of three (like puzzle pieces: squares and bent bits)
    def pieces(d, sc, w, h):
        cells = [(0.3, 0.16), (0.7, 0.16), (0.3, 0.44), (0.7, 0.44), (0.3, 0.72), (0.7, 0.72)]
        for k, (fx, fy) in enumerate(cells):
            cx, cy, r = w * fx, h * fy, w * 0.14
            if k in (1, 4):      # bent pieces
                d.polygon([((cx - r) * sc, (cy - r) * sc), ((cx + r * 0.2) * sc, (cy - r) * sc),
                           ((cx + r * 0.2) * sc, (cy - r * 0.1) * sc), ((cx + r) * sc, (cy - r * 0.1) * sc),
                           ((cx + r) * sc, (cy + r) * sc), ((cx - r * 0.2) * sc, (cy + r) * sc),
                           ((cx - r * 0.2) * sc, (cy + r * 0.2) * sc), ((cx - r) * sc, (cy + r * 0.2) * sc)],
                          fill=255)
            elif k == 3:         # a curved piece
                d.pieslice([(cx - r * 1.3) * sc, (cy - r * 1.1) * sc, (cx + r * 1.3) * sc, (cy + r * 1.5) * sc],
                           200, 340, fill=255)
            else:
                d.rectangle([(cx - r) * sc, (cy - r * 0.8) * sc, (cx + r) * sc, (cy + r * 0.8) * sc], fill=255)
    on_panel(2, pieces, red, 31)
    return painted


TALLY_PANEL = (1612, 1672, 600, 712)   # a panel further right (Kubo's days to the holidays, chalk)


def tally(frame: np.ndarray) -> None:
    x0, x1, top, foot = TALLY_PANEL
    w, h = x1 - x0, foot - top
    rng = random.Random(15)

    def draw(d, sc):
        # a column of chalk tally groups (four strokes + a cross stroke), some crossed off, low on the panel where a
        # first-grader reaches; 3 rows
        for row in range(3):
            y0 = h * (0.42 + row * 0.16)
            for k in range(4):
                x = w * (0.30 + k * 0.08) + rng.uniform(-0.6, 0.6)
                d.line([(x * sc, y0 * sc), ((x + rng.uniform(-0.8, 0.8)) * sc, (y0 + h * 0.11) * sc)], fill=255,
                       width=round(1.3 * sc))
            d.line([(w * 0.24 * sc, (y0 + h * 0.09) * sc), (w * 0.62 * sc, (y0 + h * 0.02) * sc)], fill=255,
                   width=round(1.2 * sc))
    a = chalk_layer((w, h), draw, 5, 1.2)
    full = np.zeros(frame.shape[:2], np.float32)
    full[top:foot, x0:x1] = a
    apply_chalk(frame, full, strength=0.7)


HOPSCOTCH_START = (1150, 884)     # screen point of the middle of the first square's near edge


def hopscotch_quad():
    """Ground quad of the 0.8 x 3.0 m hopscotch: from its first square near the middle of the court it runs along
    the back wall's direction (towards VP_R, to the upper right) with the half circle at the far end; corners in the
    order of the plane's (0,0) (1,0) (1,1) (0,1) (plane y = 0 is the far end)."""
    return ground_rect(HOPSCOTCH_START, E_R, (E_L[0], E_L[1]), 3.0, 0.8)


def cmd_decals(args) -> None:
    base = base_image(args.base)                         # master px (2752 x 1536)
    frame_img = pr.fit_to_frame(base).convert("RGB")     # game px
    frame = np.asarray(frame_img, np.float32).copy()
    painted = wall_painting(frame)
    tally(frame)
    quad = hopscotch_quad()
    a = hopscotch_alpha((1920, 1080), quad)
    apply_chalk(frame, a, strength=0.85)
    out_frame = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8), "RGB")
    # write back into master resolution only where the decals changed pixels (the rest stays pixel-identical)
    diff = np.abs(np.asarray(out_frame, np.float32) - np.asarray(frame_img, np.float32)).max(axis=2) > 0.5
    mask_game = Image.fromarray((diff * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(3))
    up = out_frame.resize((round(pr.MODEL_FRAME[0] * refit_room.K), pr.FRAME[1]), Image.Resampling.LANCZOS)
    # game frame -> master: undo the crop (CROP_X) and the scale
    canvas_game = Image.new("RGB", (round(pr.MODEL_FRAME[0] * refit_room.K), pr.FRAME[1]))
    canvas_game.paste(pr.fit_to_frame(base).convert("RGB"), (refit_room.CROP_X, 0))
    canvas_game.paste(out_frame, (refit_room.CROP_X, 0))
    mask_full = Image.new("L", canvas_game.size, 0)
    mask_full.paste(mask_game, (refit_room.CROP_X, 0))
    master_new = canvas_game.resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    master_mask = mask_full.resize(pr.MODEL_FRAME, Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(1.2))
    final = Image.composite(master_new, base, master_mask)
    del up
    save(final, {"kind": "decals (local, free)", "from_version": args.base, "usd": 0,
                 "decals": {"wall_painting_panels_game_px": PANELS, "tally_panel_game_px": TALLY_PANEL,
                            "hopscotch_quad_game_px": [[round(x, 1), round(y, 1)] for x, y in quad]},
                 "note": "S69_scripts/s69_paint.py decals: club painting (4 shapes / 3 waves + 2 strokes / 6 pieces), "
                         "Kubo's chalk tally, chalk hopscotch (8 squares + half circle); outside the changed pixels "
                         "the master is identical to the base version",
                 "started": datetime.datetime.now().isoformat(timespec="seconds")})


def cmd_review(args) -> None:
    img = pr.fit_to_frame(base_image(args.version)).convert("RGB")
    crops = [(1360, 560, 1700, 730, 4), (1150, 740, 1920, 1000, 2), (900, 640, 1200, 780, 3)]
    for i, (x0, y0, x1, y1, s) in enumerate(crops):
        c = img.crop((x0, y0, x1, y1)).resize(((x1 - x0) * s, (y1 - y0) * s), Image.Resampling.LANCZOS)
        out = REVIEW / f"{ROOM}_v{args.version}_crop{i}.png"
        c.save(out)
        print(out.relative_to(ROOT))
    img.save(REVIEW / f"{ROOM}_v{args.version}_frame.png")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("canvas")
    p.add_argument("--base", type=int, default=1)
    p = sub.add_parser("paint")
    p.add_argument("--base", type=int, default=1)
    p.add_argument("--seed", type=int)
    p = sub.add_parser("composite")
    p.add_argument("--base", type=int, required=True)
    p.add_argument("--raw", required=True)
    p.add_argument("--box", type=float, nargs=4, action="append")
    p = sub.add_parser("objects")
    p.add_argument("--base", type=int, default=1)
    p.add_argument("--raw", default="art/masters/bg_natural/_S69_v2_bench_bike_raw.png")
    p = sub.add_parser("decals")
    p.add_argument("--base", type=int, required=True)
    p = sub.add_parser("review")
    p.add_argument("version", type=int)
    args = ap.parse_args()
    {"canvas": cmd_canvas, "paint": cmd_paint, "composite": cmd_composite, "decals": cmd_decals,
     "objects": cmd_objects,
     "review": cmd_review}[args.cmd](args)


if __name__ == "__main__":
    main()
