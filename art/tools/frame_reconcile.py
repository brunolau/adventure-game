"""Reconcile cutscene frames with the rooms they show (art-reconcile wave, 2026-10-06).

1. CS09_1 (the gondola cabin leaving Biela Put) must show through its windows the NEW winter S41 painting
   (src/game/assets/bg_natural/S41.webp, log art/masters/bg_natural/S41.md): the valley station's curved dark-glass
   rope housing with the orange band, the low white hall, orange-red unbranded cabins with a dark window band and snow
   on the roof, the stone-clad wall with the card-reader pillar (green light) and the stainless turnstile in its gap,
   the arched wooden footbridge with the X-lattice railing over the dark stream, Hotel Posta (steep timber A-frame
   with balconies, lower cream wing with three chimneys), the light-grey steel tube pylon. The only lettering stays
   the plate BIELA PUT - PRIEHYBA. One Nano Banana Pro edit (USD 0.15) of the accepted winter master; the model
   output is used ONLY inside the window glass (hand-traced polygons below) and, around Adam, only where it changed
   the view behind him, so Adam, the coat, the cabin interior and the sign stay pixel-identical.
   Pass 1 (v4) paints the whole view; pass 2 (v5, cs09-detail) is a zoomed crop edit of the left half (the gate and
   the footbridge) plus a local snow cap on the descending cabin; pass 3 (v6, cs09-door) a tight crop edit of the left
   door window (the duplicate housing of pass 1 removed). Each pass only takes the window regions it names.
2. EPILOGUE_6: the wall calendar's weekday row in Slovak (Po Ut St Št Pi So Ne) and the grid of June 1962
   (1 June 1962 = Friday), free local repaint (Bahnschrift from Windows, ink and paper sampled from the painting).
3. S33: the wall calendar's month grid as June 1962 with the same weekday row (free local repaint; the year already
   read 1962).

Usage (repo root; PYTHONIOENCODING=utf-8 python -X utf8 art/tools/frame_reconcile.py ...):
  cs09 prompt | run --budget B | compose --version N             pass 1 (paid run: one Nano Banana Pro call)
  cs09-detail prompt | run --base-version 4 --budget B | compose --version N   pass 2
  cs09-door prompt | run --base-version 5 --budget B | compose --version N     pass 3
  calendar EPILOGUE_6 | S33 [--dry]                              free calendar repaint (new master version, review,
                                                                  export; --dry writes only the review sheet)
Reviews: art/review/reconcile/ (git-ignored). Spend scope: cutscenes/reconcile/CS09_1/ (art/spend-log.csv).
"""
from __future__ import annotations

import argparse
import calendar as pycal
import datetime
import json
import random
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive_era  # noqa: E402
import fal_api  # noqa: E402
import paint_room  # noqa: E402

ROOT = paint_room.ROOT
ART = ROOT / "art"
GAME = ROOT / "src" / "game"
FRAMES = ART / "cutscenes"
REVIEW = ART / "review" / "reconcile"
S41 = GAME / "assets" / "bg_natural" / "S41.webp"
CABIN = GAME / "assets" / "ambient" / "S41" / "natural" / "cabin_winter.webp"
SCOPE = "cutscenes/reconcile/CS09_1/"

# ------------------------------------------------------------------------------------------------ CS09_1

CS09_BASE_VERSION = 3          # the accepted winter master (art/cutscenes/CS09_1_v3.png)

# Window glass of the cabin in the 1920x1080 frame (traced on CS09_1_v3). Clockwise polygons; the frame bars, frost
# rims painted on the bars, benches, rails and the sign are outside them.
WINDOWS = {
    "far_left": [(0, 0), (196, 0), (182, 120), (160, 330), (152, 520), (150, 690), (0, 720)],
    "left_big": [(230, 0), (282, 0), (330, 20), (420, 60), (488, 100), (470, 200), (450, 330), (436, 470),
                 (430, 580), (296, 620), (226, 640), (226, 420), (228, 200)],
    "left_low": [(252, 860), (300, 836), (452, 760), (452, 790), (400, 830), (262, 916)],
    "far_left_low": [(0, 990), (160, 908), (172, 990), (110, 1040), (0, 1080)],
    "left_mid": [(570, 152), (640, 156), (652, 260), (662, 420), (664, 600), (664, 740), (660, 868), (634, 868),
                 (640, 760), (620, 745), (552, 748), (530, 650), (522, 520), (528, 380), (545, 250)],
    "door_left": [(722, 186), (908, 186), (910, 612), (738, 612), (730, 400)],
    "door_right": [(1012, 186), (1200, 186), (1192, 400), (1186, 612), (1012, 612)],
    "right_mid": [(1270, 152), (1346, 152), (1372, 230), (1372, 650), (1290, 660), (1262, 650), (1264, 400)],
    "right_big": [(1445, 100), (1590, 0), (1700, 0), (1735, 120), (1755, 300), (1765, 500), (1770, 640),
                  (1700, 640), (1570, 600), (1500, 560), (1480, 400), (1462, 250)],
    "far_right": [(1760, 0), (1920, 0), (1920, 720), (1830, 690), (1790, 600), (1782, 400), (1772, 200)],
    "right_low": [(1600, 800), (1640, 830), (1670, 880), (1675, 925), (1600, 870)],
    "far_right_low": [(1750, 905), (1920, 1000), (1920, 1080), (1830, 1080), (1760, 1000)],
}
# Adam (head, scarf, coat, bag) overlaps right_mid / right_big: inside this generous silhouette (~15 px margin) the
# model output is taken only where it really changed the picture (the view behind him), so his own pixels stay the
# base's; elsewhere in the glass the model output is used fully (no thin remnants of the old view).
ADAM_POLY = [(1330, 300), (1380, 272), (1455, 272), (1492, 305), (1500, 400), (1505, 420), (1535, 450), (1572, 490),
             (1585, 560), (1600, 720), (1240, 720), (1240, 680), (1295, 640), (1328, 560), (1338, 480), (1345, 450),
             (1325, 400), (1322, 340)]
SIGN = [730, 36, 460, 88]

CS09_PROMPT = """You receive 3 images. Image 1 is a finished cutscene frame of our point-and-click adventure game: inside a small eight-seat gondola cabin of the Biela Put - Priehyba cable car at Jasna on 6 February 2035, a clear cold winter day; Adam sits by the window holding his lift ticket, a moment after the cabin has left the valley station. Image 2 is our finished background painting of that valley station at Biela Put, seen from the access road in front of Hotel Posta: this is exactly the place the cabin has just left. Image 3 is one of the line's cabins as painted in image 2: rounded, orange-red, unbranded, with a dark window band and snow on its roof.

Edit image 1: change ONLY the view seen through the cabin's windows and the two door windows. Everything inside the cabin stays exactly as in image 1: Adam (face, hair, dark charcoal winter coat, mustard knitted scarf, pose, hands, ticket card, jeans, boots, brown leather messenger bag), the benches, the door, the window frames and the frost rims on them, the grab rails, the snow on the floor, the sunlight on the floor and the plate above the door with its lettering.

The new view through the glass: the cabin hangs a few metres above the valley station of image 2 and rises away from it, so through the windows we look down and back onto the very same place, painted from above in the same winter light, with the same buildings, colours and details as in image 2:
- through the big window on the left and the narrow window at the far left: Hotel Posta as in image 2 - a steep-gabled timber A-frame chalet with two wooden balconies, warm brown timber and a thick snowy roof, and beside it its lower cream-coloured wing with a snowy roof, small dormers and three small chimneys; in front of it the ploughed grey access road between snow banks with the grey stone-clad retaining wall along its side; snow-laden spruces and white mountains behind.
- through the narrow window left of the door: the arched wooden footbridge with its brown X-lattice railing over the dark stream with snowy stones, two snow-capped benches on the white verge.
- through the two door windows, just below the cabin: the valley station of image 2 - the curved dark-glass rope housing with its bright orange band on grey pillars, the low white boarding hall with an orange stripe, an orange-red cabin parked in the station, the brown wooden fence; and on the road side, in the gap of the stone-clad wall, the dark card-reader pillar with its small green light next to the stainless turnstile with glass wings.
- through the windows on the right, behind Adam: the light-grey steel tube pylon with its ladder close outside, the two haul ropes, one more orange-red cabin like image 3 coming down on the other rope, and the snowy slope with spruces.
No lettering anywhere in the view: no signposts, no hotel name, no signs or boards with text on any building, no logos, no liveries on the cabins. The only lettering in the whole picture stays the plate above the door from image 1. No people in the view except at most two tiny distant skiers on the slope.

The result is image 1 edited, in the same 16:9 framing: the same camera, cabin, people and light; no frames, no borders, no letterbox bars, no captions, no watermark, no new text. Keep the painting technique, brushwork, palette handling and level of detail of image 1 (style A); the view outside is painted in the same style as image 2."""


def cs09_base() -> Image.Image:
    return Image.open(FRAMES / f"CS09_1_v{CS09_BASE_VERSION}.png").convert("RGB")


def s41_reference() -> Image.Image:
    """S41 with its signpost boards painted plain brown (no lettering), so the model has no text to copy."""
    img = Image.open(S41).convert("RGB")
    box = (1098, 282, 1280, 392)
    a = np.asarray(img.crop(box), dtype=np.float32)
    warm = (a[..., 0] - a[..., 2]) > 12                     # board wood and its cream letters; sky / snow are cool
    wood = a[warm & (a.max(-1) < 120)]
    fill = np.median(wood, axis=0) if len(wood) else np.array([92, 62, 40], dtype=np.float32)
    m = Image.fromarray((warm * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(3))
    plain = Image.new("RGB", m.size, tuple(int(v) for v in fill))
    patch = Image.composite(plain, img.crop(box), m)
    img.paste(patch, box[:2])
    return img


def cabin_reference() -> Image.Image:
    sprite = Image.open(CABIN).convert("RGBA")
    big = sprite.resize((sprite.width * 6, sprite.height * 6), Image.Resampling.LANCZOS)
    card = Image.new("RGBA", (big.width + 120, big.height + 120), (128, 128, 128, 255))
    card.alpha_composite(big, (60, 60))
    return card.convert("RGB")


def window_mask(size: tuple[int, int], feather: float = 2.0) -> Image.Image:
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    for poly in WINDOWS.values():
        d.polygon(poly, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(feather)) if feather else mask


def cs09_composite(base: Image.Image, edit: Image.Image, lo: float = 16, hi: float = 36) -> tuple[Image.Image, Image.Image]:
    glass = np.asarray(window_mask(base.size), dtype=np.float32) / 255
    b = np.asarray(base.filter(ImageFilter.GaussianBlur(2)), dtype=np.float32)
    e = np.asarray(edit.filter(ImageFilter.GaussianBlur(2)), dtype=np.float32)
    changed = np.clip((np.abs(e - b).max(-1) - lo) / (hi - lo), 0, 1)
    changed = np.asarray(Image.fromarray((changed * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(5))
                         .filter(ImageFilter.GaussianBlur(2)), dtype=np.float32) / 255
    zone_img = Image.new("L", base.size, 0)
    ImageDraw.Draw(zone_img).polygon(ADAM_POLY, fill=255)
    zone = np.asarray(zone_img.filter(ImageFilter.GaussianBlur(4)), dtype=np.float32) / 255
    m = glass * (1 - zone) + glass * zone * changed
    sx, sy, sw, sh = SIGN
    m[sy:sy + sh, sx:sx + sw] = 0
    mask = Image.fromarray((m * 255).clip(0, 255).astype(np.uint8), "L")
    return Image.composite(edit, base, mask), mask


def cs09_job() -> dict:
    base = cs09_base()
    images = [("base", paint_room.to_model_geometry(base), f"art/cutscenes/CS09_1_v{CS09_BASE_VERSION}.png (winter master)"),
              ("ref", s41_reference(), "src/game/assets/bg_natural/S41.webp (signpost lettering blurred)"),
              ("ref", cabin_reference(), "src/game/assets/ambient/S41/natural/cabin_winter.webp (6x, on grey)")]
    return {"base": base, "images": images, "prompt": CS09_PROMPT + "\n\n" + paint_room.style_sentence()}


def next_version(stem: str) -> int:
    nums = []
    for p in FRAMES.glob(f"{stem}_v*.png"):
        tail = p.stem[len(stem) + 2:]
        if tail.isdigit():
            nums.append(int(tail))
    for p in (FRAMES / "rejected").glob(f"{stem}_v*.png"):
        tail = p.stem[len(stem) + 2:]
        if tail.isdigit():
            nums.append(int(tail))
    return max(nums, default=0) + 1


def review_sheet(name: str, base: Image.Image, result: Image.Image, mask: Image.Image, title: str) -> Path:
    REVIEW.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (1920, 1080 + 540), (20, 20, 20))
    sheet.paste(base.resize((960, 540), Image.Resampling.LANCZOS), (0, 0))
    sheet.paste(result.resize((960, 540), Image.Resampling.LANCZOS), (960, 0))
    tint = Image.new("RGB", result.size, (255, 0, 160))
    shown = Image.composite(result, Image.blend(result, tint, 0.35), mask.point(lambda v: 255 if v > 8 else 0))
    sheet.paste(shown, (0, 540))
    d = ImageDraw.Draw(sheet)
    d.text((12, 12), "before", fill=(255, 255, 255))
    d.text((972, 12), title, fill=(255, 255, 255))
    d.text((12, 552), "result; magenta tint = kept from the base", fill=(255, 255, 255))
    out = REVIEW / f"{name}.jpg"
    sheet.save(out, quality=88)
    return out


def cs09_build(version: int, raw_path: Path, meta: dict) -> Path:
    job = cs09_job()
    base = job["base"]
    raw = derive_era.as_model(Image.open(raw_path))
    small = (paint_room.MODEL_FRAME[0] // 4, paint_room.MODEL_FRAME[1] // 4)
    gx, gy = derive_era.phase_shift(derive_era.gray(raw, small), derive_era.gray(job["images"][0][1], small))
    gx, gy = gx * 4, gy * 4
    if (gx or gy) and max(abs(gx), abs(gy)) <= derive_era.GLOBAL_COMPENSATE:
        raw = ImageChops.offset(raw, -gx, -gy)
        meta["compensated_master_px"] = [gx, gy]
        print(f"model output drifted by {gx:+d},{gy:+d} master px; compensated")
    edit = paint_room.fit_to_frame(raw).convert("RGB")
    result, mask = cs09_composite(base, edit)
    out = FRAMES / f"CS09_1_v{version}.png"
    result.save(out)
    side = review_sheet(f"CS09_1_v{version}", base, result, mask, f"CS09_1 v{version} (S41 view)")
    meta.update({"compose": {"windows": WINDOWS, "adam_poly": ADAM_POLY, "sign": SIGN, "diff_ramp": [16, 36]},
                 "output_size": list(result.size), "composed": datetime.datetime.now().isoformat(timespec="seconds"),
                 "review": side.relative_to(ROOT).as_posix()})
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    dest = GAME / "assets" / "cutscenes" / "CS09_1.webp"
    result.save(dest, "WEBP", quality=90, method=6)
    print(f"{out.relative_to(ROOT)} -> {dest.relative_to(ROOT)}; LOOK at {side.relative_to(ROOT)}")
    return out


def cmd_cs09(args) -> None:
    job = cs09_job()
    if args.action == "prompt":
        print(job["prompt"])
        REVIEW.mkdir(parents=True, exist_ok=True)
        for i, (_, img, name) in enumerate(job["images"], 1):
            img.convert("RGB").save(REVIEW / f"CS09_1_ref{i}.jpg", quality=88)
            print(f"image {i}: {name}")
        mask = window_mask(job["base"].size, 0)
        tint = Image.new("RGB", job["base"].size, (0, 255, 120))
        Image.composite(Image.blend(job["base"], tint, 0.45), job["base"], mask).save(REVIEW / "CS09_1_windows.jpg",
                                                                                     quality=88)
        print(f"window polygons: {(REVIEW / 'CS09_1_windows.jpg').relative_to(ROOT)}")
        return
    if args.action == "compose":
        side = FRAMES / f"CS09_1_v{args.version}.json"
        meta = json.loads(side.read_text(encoding="utf-8"))
        meta["recomposed"] = True
        cs09_build(args.version, ROOT / meta["raw_model_output"], meta)
        return
    version = next_version("CS09_1")
    seed = args.seed if args.seed is not None else random.randint(1, 2 ** 31 - 1)
    urls = [fal_api.image_data_uri(job["images"][0][1], fmt="PNG")]
    urls += [fal_api.image_data_uri(img, max_side=2048, fmt="JPEG") for _, img, _ in job["images"][1:]]
    arguments = {"prompt": job["prompt"], "image_urls": urls, "aspect_ratio": paint_room.ASPECT,
                 "resolution": paint_room.RESOLUTION, "output_format": "png", "num_images": 1, "seed": seed}
    price = fal_api.IMAGE_PRICES[(paint_room.MODEL, paint_room.RESOLUTION)]
    asset = f"{SCOPE}CS09_1_v{version}_s41"
    started = datetime.datetime.now().isoformat(timespec="seconds")
    result = fal_api.run(paint_room.MODEL, arguments, asset, price, budget=(SCOPE, args.budget), timeout_s=900)
    raw = FRAMES / f"_CS09_1_v{version}_s41_raw.png"
    fal_api.download(result["images"][0]["url"], raw)
    meta = {"target": "CS09_1", "version": version, "kind": "reconcile with the winter S41 painting",
            "model": paint_room.MODEL, "resolution": paint_room.RESOLUTION, "seed": result.get("seed", seed),
            "usd": price, "scope": SCOPE, "spend_log_asset": asset, "started": started, "prompt": job["prompt"],
            "image_urls": [name for _, _, name in job["images"]], "model_description": result.get("description"),
            "raw_model_output": raw.relative_to(ROOT).as_posix()}
    cs09_build(version, raw, meta)
    print(f"scope {SCOPE} spent {fal_api.logged_spend(SCOPE):.2f} of {args.budget:.2f}")


# --- pass 2: a zoomed edit of the left half (the gate in the left door window, the footbridge at the far left)

DETAIL_CROP = (0, 140, 1244, 840)          # 16:9 crop of the frame, x0, y0, x1, y1
DETAIL_PROMPT = """Image 1 is a crop of a finished cutscene frame of our point-and-click adventure game: inside a small gondola cabin that has just left the valley station at Biela Put (Jasna, 6 February 2035, a clear cold winter day); through the cabin windows we look down onto the station area. Image 2 is our finished background painting of that place, seen from the access road.

Make ONLY these two changes inside the window glass and keep everything else in image 1 exactly as it is: the cabin's frames, door, benches, grab rails, frost rims and light, and the rest of the view (Hotel Posta and its cream wing, the road, the stone wall in the narrow window, and the station housing with the orange band and the parked orange-red cabin in the RIGHT door window):
1. Through the LEFT of the two door windows (the tall window in the left door leaf, right of the centre of image 1): remove the dark-glass housing with the orange band and the small white hut. Instead we look down onto the road side of the station, as in image 2 right of its road: the ploughed grey road with a low snow bank, the grey stone-clad retaining wall topped with snow running along the road, and in a gap in that wall a slim dark card-reader pillar with a small glowing green light, standing next to a stainless-steel turnstile with two glass wings; behind the wall the white snow field with ski tracks and the brown wooden fence of the station.
2. Through the lower part of the narrow window at the far left edge: the arched wooden footbridge with its brown X-lattice railing crossing the dark mountain stream between snow-capped stones, as in image 2 left of its road; keep the light-wood pillar with the round turquoise clock face standing at the bridge head.
No lettering, no signs, no numbers, no people, no animals. Keep the painting technique, brushwork, palette handling and level of detail of image 1; the result is image 1 edited, in the same 16:9 framing, no frames, no borders, no captions."""
# The model put the gate (reader pillar + turnstile in the wall gap) into the narrow window left of the door and the
# footbridge over the stream into the lower far-left window (it ignored "left door window"); those two are taken.
DETAIL_REGIONS = {
    "left_mid": WINDOWS["left_mid"],
    "far_left_low": [(0, 440), (164, 440), (152, 520), (150, 690), (0, 720)],
}
DETAIL_RAMP_Y = (470, 505)       # soft top edge of the far-left part (in the snow bank above the bridge)
SNOW_CAP = {"roof_y": 181, "x0": 1772, "x1": 1890, "height": 6}     # the descending cabin in the right big window


def crop_to_model(img: Image.Image) -> Image.Image:
    """Pad a 16:9 crop to the model's 2752x1536 aspect (repeating the border columns) and scale it there."""
    mw, mh = paint_room.MODEL_FRAME
    w, h = img.size
    cover_w = round(h * mw / mh)
    left = (cover_w - w) // 2
    right = cover_w - w - left
    canvas = Image.new("RGB", (cover_w, h))
    canvas.paste(img, (left, 0))
    canvas.paste(img.crop((0, 0, 1, h)).resize((max(left, 1), h)), (0, 0))
    canvas.paste(img.crop((w - 1, 0, w, h)).resize((max(right, 1), h)), (left + w, 0))
    return canvas.resize((mw, mh), Image.Resampling.LANCZOS)


def model_to_crop(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    return paint_room.fit_to_frame(img.convert("RGB"), size)


def roof_profile(img: Image.Image) -> dict[int, int]:
    """Top edge of the descending cabin's orange-red shell per column (the first red pixel from above)."""
    a = np.asarray(img.convert("RGB"), dtype=np.int32)
    c = SNOW_CAP
    prof = {}
    for x in range(c["x0"] - 6, c["x1"] + 6):
        col = a[c["roof_y"] - 25:c["roof_y"] + 60, x]
        hits = np.nonzero((col[:, 0] > 95) & (col[:, 0] - col[:, 1] > 40) & (col[:, 0] - col[:, 2] > 35))[0]
        if len(hits):
            prof[x] = int(hits[0]) + c["roof_y"] - 25
    return prof


def snow_cap(img: Image.Image, seed: int = 41) -> Image.Image:
    """Paint a soft snow cap on the roof of the descending cabin (free, local): a low lumpy dome that follows the
    shell's real top edge (measured per column), thickest in the middle, thinning out over the rounded shoulder;
    sunlit top, cool body, a thin shadow line where it sits on the shell. Supersampled 4x. The hanger arm stays on
    top (its dark pixels are not covered)."""
    rnd = random.Random(seed)
    c = SNOW_CAP
    prof = roof_profile(img)
    xs, xe = min(prof), c["x1"] - 16           # dome span on the flat top; the shoulder gets a thin coat
    ss = 4
    x0, y0 = c["x0"] - 10, c["roof_y"] - 20
    w, h = c["x1"] - c["x0"] + 20, 80
    layer = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    phase = [rnd.uniform(0, 6.28) for _ in range(3)]
    for x in range(xs, c["x1"] + 1):
        if x not in prof:
            continue
        roof = prof[x]
        if x <= xe:
            u = (x - xs) / (xe - xs)
            lump = 1 + 0.18 * np.sin(x / 7 + phase[0]) + 0.1 * np.sin(x / 3.1 + phase[1])
            thick = 1.5 + c["height"] * (np.sin(np.pi * u) ** 0.55) * lump
        else:
            thick = max(0.0, 2.2 - (roof - prof.get(xe, roof)) / 18)   # thin coat on the shoulder
        if thick <= 0.3:
            continue
        top, bottom = roof - thick, roof + 1.2
        for sx in range(ss):
            px = (x - x0) * ss + sx
            d.line([(px, (top - y0) * ss), (px, (bottom - y0) * ss)], fill=(214, 224, 240, 255))
            d.line([(px, (top - y0) * ss), (px, (top + min(2.0, thick * 0.45) - y0) * ss)], fill=(246, 248, 252, 255))
            d.line([(px, (bottom - 1.0 - y0) * ss), (px, (bottom - y0) * ss)], fill=(176, 190, 216, 255))
    layer = layer.resize((w, h), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(0.5))
    full = Image.new("RGBA", img.size, (0, 0, 0, 0))
    full.paste(layer, (x0, y0))
    a = np.asarray(full, dtype=np.float32)
    base = np.asarray(img.convert("RGB"), dtype=np.float32)
    dark = base.max(-1) < 70                                                # the hanger arm / grip
    alpha = a[..., 3:4] / 255 * (~dark)[..., None]
    rgb = base * (1 - alpha) + a[..., :3] * alpha
    return Image.fromarray(rgb.clip(0, 255).astype(np.uint8), "RGB")


def detail_compose(base_version: int, version: int, raw_path: Path, meta: dict) -> Path:
    base = Image.open(FRAMES / f"CS09_1_v{base_version}.png").convert("RGB")
    x0, y0, x1, y1 = DETAIL_CROP
    crop = base.crop(DETAIL_CROP)
    raw = derive_era.as_model(Image.open(raw_path))
    model_in = crop_to_model(crop)
    small = (paint_room.MODEL_FRAME[0] // 4, paint_room.MODEL_FRAME[1] // 4)
    gx, gy = derive_era.phase_shift(derive_era.gray(raw, small), derive_era.gray(model_in, small))
    gx, gy = gx * 4, gy * 4
    if (gx or gy) and max(abs(gx), abs(gy)) <= derive_era.GLOBAL_COMPENSATE:
        raw = ImageChops.offset(raw, -gx, -gy)
        meta["compensated_model_px"] = [gx, gy]
        print(f"model output drifted by {gx:+d},{gy:+d} model px; compensated")
    edit_crop = model_to_crop(raw, crop.size)
    edit = base.copy()
    edit.paste(edit_crop, (x0, y0))
    mask = Image.new("L", base.size, 0)
    d = ImageDraw.Draw(mask)
    for poly in DETAIL_REGIONS.values():
        d.polygon(poly, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(2))
    m = np.asarray(mask, dtype=np.float32)
    r0, r1 = DETAIL_RAMP_Y
    ramp = np.clip((np.arange(base.height) - r0) / (r1 - r0), 0, 1)[:, None]  # soft top edge of the far-left part
    left = np.zeros_like(m)
    left[:, :200] = 1
    m = m * (1 - left) + m * left * ramp
    mask = Image.fromarray(m.clip(0, 255).astype(np.uint8), "L")
    result = Image.composite(edit, base, mask)
    result = snow_cap(result)
    out = FRAMES / f"CS09_1_v{version}.png"
    result.save(out)
    shown = mask.copy()
    ImageDraw.Draw(shown).rectangle([SNOW_CAP["x0"], SNOW_CAP["roof_y"] - 14, SNOW_CAP["x1"], SNOW_CAP["roof_y"] + 6],
                                    fill=255)
    side = review_sheet(f"CS09_1_v{version}", base, result, shown, f"CS09_1 v{version} (detail pass + snow cap)")
    meta.update({"compose": {"base_version": base_version, "crop": DETAIL_CROP, "regions": DETAIL_REGIONS,
                             "ramp_y": DETAIL_RAMP_Y, "snow_cap": SNOW_CAP}, "output_size": list(result.size),
                 "composed": datetime.datetime.now().isoformat(timespec="seconds"),
                 "review": side.relative_to(ROOT).as_posix()})
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    dest = GAME / "assets" / "cutscenes" / "CS09_1.webp"
    result.save(dest, "WEBP", quality=90, method=6)
    print(f"{out.relative_to(ROOT)} -> {dest.relative_to(ROOT)}; LOOK at {side.relative_to(ROOT)}")
    return out


def cmd_cs09_detail(args) -> None:
    if args.action == "compose":
        side = FRAMES / f"CS09_1_v{args.version}.json"
        meta = json.loads(side.read_text(encoding="utf-8"))
        meta["recomposed"] = True
        detail_compose(meta["compose"]["base_version"], args.version, ROOT / meta["raw_model_output"], meta)
        return
    base = Image.open(FRAMES / f"CS09_1_v{args.base_version}.png").convert("RGB")
    crop = base.crop(DETAIL_CROP)
    model_in = crop_to_model(crop)
    s41 = s41_reference()
    REVIEW.mkdir(parents=True, exist_ok=True)
    model_in.save(REVIEW / "CS09_1_detail_in.jpg", quality=88)
    prompt = DETAIL_PROMPT + "\n\n" + paint_room.style_sentence()
    if args.action == "prompt":
        print(prompt)
        print(f"image 1: {(REVIEW / 'CS09_1_detail_in.jpg').relative_to(ROOT)}")
        return
    version = next_version("CS09_1")
    seed = args.seed if args.seed is not None else random.randint(1, 2 ** 31 - 1)
    urls = [fal_api.image_data_uri(model_in, fmt="PNG"), fal_api.image_data_uri(s41, max_side=2048, fmt="JPEG")]
    arguments = {"prompt": prompt, "image_urls": urls, "aspect_ratio": paint_room.ASPECT,
                 "resolution": paint_room.RESOLUTION, "output_format": "png", "num_images": 1, "seed": seed}
    price = fal_api.IMAGE_PRICES[(paint_room.MODEL, paint_room.RESOLUTION)]
    asset = f"{SCOPE}CS09_1_v{version}_detail"
    started = datetime.datetime.now().isoformat(timespec="seconds")
    result = fal_api.run(paint_room.MODEL, arguments, asset, price, budget=(SCOPE, args.budget), timeout_s=900)
    raw = FRAMES / f"_CS09_1_v{version}_detail_raw.png"
    fal_api.download(result["images"][0]["url"], raw)
    meta = {"target": "CS09_1", "version": version, "kind": "detail pass (zoomed crop edit) + local snow cap",
            "model": paint_room.MODEL, "resolution": paint_room.RESOLUTION, "seed": result.get("seed", seed),
            "usd": price, "scope": SCOPE, "spend_log_asset": asset, "started": started, "prompt": prompt,
            "image_urls": [f"art/cutscenes/CS09_1_v{args.base_version}.png crop {DETAIL_CROP}",
                           "src/game/assets/bg_natural/S41.webp (signpost boards plain)"],
            "model_description": result.get("description"), "raw_model_output": raw.relative_to(ROOT).as_posix()}
    detail_compose(args.base_version, version, raw, meta)
    print(f"scope {SCOPE} spent {fal_api.logged_spend(SCOPE):.2f} of {args.budget:.2f}")


# --- pass 3: the left door window still showed a second station housing above a small white hut (a duplicate of
# the right door window); a tight crop edit replaces it with the open snow field and the station fence.

DOOR_CROP = (560, 160, 1396, 630)          # 16:9 crop around the two door windows
DOOR_PROMPT = """Image 1 is a crop of a finished cutscene frame of our point-and-click adventure game: inside a small gondola cabin that has just left the valley station at Biela Put (Jasna, 6 February 2035, a clear cold winter day). In the middle of image 1 is the closed cabin door with two tall windows. Through the RIGHT door window we see the valley station: a curved dark-glass rope housing with an orange band on grey pillars and a parked orange-red cabin. Through the LEFT door window we see a second, duplicate dark-glass housing with an orange band standing on a small white hut.

Make ONLY this change: in the LEFT door window, remove the duplicate dark-glass housing and the small white hut completely, and paint in their place what lies behind them: the open white snow field sloping gently down, with a few soft ski tracks, the brown wooden fence of the station running across it with snow on its rails, and behind it the same snowy slope, spruces and white mountain that are already painted at the top of that window. Nothing built is seen in the left door window. Keep everything else in image 1 exactly as it is: the right door window with the station and the parked cabin, the narrow window at the left edge with the stone wall and the turnstile, the door, all frames and frost rims, the person at the right edge and the light.
No lettering, no signs, no numbers, no people. Keep the painting technique, brushwork, palette handling and level of detail of image 1; the result is image 1 edited, in the same 16:9 framing, no frames, no borders, no captions."""


def door_compose(base_version: int, version: int, raw_path: Path, meta: dict) -> Path:
    base = Image.open(FRAMES / f"CS09_1_v{base_version}.png").convert("RGB")
    x0, y0, x1, y1 = DOOR_CROP
    crop = base.crop(DOOR_CROP)
    raw = derive_era.as_model(Image.open(raw_path))
    model_in = crop_to_model(crop)
    small = (paint_room.MODEL_FRAME[0] // 4, paint_room.MODEL_FRAME[1] // 4)
    gx, gy = derive_era.phase_shift(derive_era.gray(raw, small), derive_era.gray(model_in, small))
    gx, gy = gx * 4, gy * 4
    if (gx or gy) and max(abs(gx), abs(gy)) <= derive_era.GLOBAL_COMPENSATE:
        raw = ImageChops.offset(raw, -gx, -gy)
        meta["compensated_model_px"] = [gx, gy]
        print(f"model output drifted by {gx:+d},{gy:+d} model px; compensated")
    edit = base.copy()
    edit.paste(model_to_crop(raw, crop.size), (x0, y0))
    mask = Image.new("L", base.size, 0)
    ImageDraw.Draw(mask).polygon(WINDOWS["door_left"], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(2))
    result = Image.composite(edit, base, mask)
    out = FRAMES / f"CS09_1_v{version}.png"
    result.save(out)
    side = review_sheet(f"CS09_1_v{version}", base, result, mask, f"CS09_1 v{version} (left door window)")
    meta.update({"compose": {"base_version": base_version, "crop": DOOR_CROP, "region": WINDOWS["door_left"]},
                 "output_size": list(result.size), "composed": datetime.datetime.now().isoformat(timespec="seconds"),
                 "review": side.relative_to(ROOT).as_posix()})
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    dest = GAME / "assets" / "cutscenes" / "CS09_1.webp"
    result.save(dest, "WEBP", quality=90, method=6)
    print(f"{out.relative_to(ROOT)} -> {dest.relative_to(ROOT)}; LOOK at {side.relative_to(ROOT)}")
    return out


def cmd_cs09_door(args) -> None:
    if args.action == "compose":
        side = FRAMES / f"CS09_1_v{args.version}.json"
        meta = json.loads(side.read_text(encoding="utf-8"))
        meta["recomposed"] = True
        door_compose(meta["compose"]["base_version"], args.version, ROOT / meta["raw_model_output"], meta)
        return
    base = Image.open(FRAMES / f"CS09_1_v{args.base_version}.png").convert("RGB")
    model_in = crop_to_model(base.crop(DOOR_CROP))
    REVIEW.mkdir(parents=True, exist_ok=True)
    model_in.save(REVIEW / "CS09_1_door_in.jpg", quality=88)
    prompt = DOOR_PROMPT + "\n\n" + paint_room.style_sentence()
    if args.action == "prompt":
        print(prompt)
        return
    version = next_version("CS09_1")
    seed = args.seed if args.seed is not None else random.randint(1, 2 ** 31 - 1)
    arguments = {"prompt": prompt, "image_urls": [fal_api.image_data_uri(model_in, fmt="PNG")],
                 "aspect_ratio": paint_room.ASPECT, "resolution": paint_room.RESOLUTION, "output_format": "png",
                 "num_images": 1, "seed": seed}
    price = fal_api.IMAGE_PRICES[(paint_room.MODEL, paint_room.RESOLUTION)]
    asset = f"{SCOPE}CS09_1_v{version}_door"
    started = datetime.datetime.now().isoformat(timespec="seconds")
    result = fal_api.run(paint_room.MODEL, arguments, asset, price, budget=(SCOPE, args.budget), timeout_s=900)
    raw = FRAMES / f"_CS09_1_v{version}_door_raw.png"
    fal_api.download(result["images"][0]["url"], raw)
    meta = {"target": "CS09_1", "version": version, "kind": "left door window (zoomed crop edit)",
            "model": paint_room.MODEL, "resolution": paint_room.RESOLUTION, "seed": result.get("seed", seed),
            "usd": price, "scope": SCOPE, "spend_log_asset": asset, "started": started, "prompt": prompt,
            "image_urls": [f"art/cutscenes/CS09_1_v{args.base_version}.png crop {DOOR_CROP}"],
            "model_description": result.get("description"), "raw_model_output": raw.relative_to(ROOT).as_posix()}
    door_compose(args.base_version, version, raw, meta)
    print(f"scope {SCOPE} spent {fal_api.logged_spend(SCOPE):.2f} of {args.budget:.2f}")


# ------------------------------------------------------------------------------------------------ calendars
# June 1962 with Monday first: 1 June 1962 was a Friday (calendar.weekday(1962, 6, 1) == 4).
WEEKDAYS_SK = ["Po", "Ut", "St", "Št", "Pi", "So", "Ne"]
FONT = "C:/Windows/Fonts/bahnschrift.ttf"       # DIN-like, close to the painted calendar digits

# Geometry in the coordinates of the edited master. Column centres x, a straight sheared baseline per row:
# y(row, col) = row0 + row * row_step + col * col_slope (the painted calendars hang slightly skewed).
CALENDARS = {
    "EPILOGUE_6": {
        "master": FRAMES / "EPILOGUE_6_v1.png", "frame_export": GAME / "assets" / "cutscenes" / "EPILOGUE_6.webp",
        "fit": "model",                          # 2752x1536 master -> fit_to_frame on export
        # ruled lines measured on the master (ink projections): column lines x at y 400 and their tilt per px of y;
        # horizontal lines y = y_at(x_ref) + slope * (x - x_ref)
        "vlines": [1115, 1139, 1163, 1186.5, 1210, 1233, 1254, 1277], "vtilt": 0.03, "x_ref": 1128,
        "header_top": (308.0, 0.200), "header_bottom": (331.0, 0.188), "bottom": (461.5, 0.109),
        "inset": 3.0,
        "cols": [1127, 1151, 1174.5, 1198, 1221.5, 1243.5, 1265.5],
        "header": {"size": 14.0, "variation": "SemiBold SemiCondensed", "rotate": -3},
        "body": {"row0": 366.0, "row_step": 20.4, "slope": 3.5, "size": 16.0, "variation": "SemiBold SemiCondensed",
                 "rotate": -2},
        "red_sunday": True,
    },
    "S33": {
        # the post office wall calendar (no ruled lines): tiny weekday words and a month grid that started on a
        # Thursday with painted slips ("29 29", no 30); the year already reads 1962 (free edit 2026-10-06)
        "master": ART / "masters" / "bg_natural" / "S33_v2.png",
        "frame_export": GAME / "assets" / "bg_natural" / "S33.webp",
        "fit": "model",
        "rects": {"header": (419, 662, 549, 671), "body": (419, 671, 549, 731)},
        "cols": [426, 444.5, 463.5, 482, 500.5, 518.5, 537],
        "header": {"y": 666.5, "size": 6.6, "variation": "SemiBold SemiCondensed", "rotate": 0},
        "body": {"row0": 677.2, "row_step": 11.6, "slope": 0.0, "size": 10.2, "variation": "Bold SemiCondensed",
                 "rotate": 0},
        "red_sunday": True, "ink_quantile": 0.12, "blur": 0, "alpha": 1.1, "paper_only": True,
    },
}


def inpaint(rgb: np.ndarray, hole: np.ndarray) -> np.ndarray:
    """Normalized-convolution fill of the hole from the surrounding paper, coarse to fine, plus a little grain."""
    out = rgb.copy()
    known = (~hole).astype(np.float32)
    for i, sigma in enumerate((24, 12, 6, 3, 1.5)):
        img = Image.fromarray((out * known[..., None]).clip(0, 255).astype(np.uint8), "RGB")
        num = np.asarray(img.filter(ImageFilter.GaussianBlur(sigma)), dtype=np.float32)
        den = np.asarray(Image.fromarray((known * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(sigma)),
                         dtype=np.float32)[..., None] / 255
        fill = num / np.maximum(den, 1e-3)
        # the coarsest pass fills every hole pixel (wide holes), finer passes refine near the known paper
        out = np.where(hole[..., None] & (den > (1e-4 if i == 0 else 0.05)), fill, out)
    smooth = np.asarray(Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(3)),
                        dtype=np.float32)
    out = np.where(hole[..., None], smooth, out)          # paper is smooth: no streaks from the narrow side strips
    rnd = np.random.default_rng(1962)
    grain = np.asarray(Image.fromarray((128 + rnd.normal(0, 5, out.shape[:2])).clip(0, 255).astype(np.uint8), "L")
                       .filter(ImageFilter.GaussianBlur(0.7)), dtype=np.float32)[..., None] - 128
    out = np.where(hole[..., None], out + grain, out)
    return out


def june_1962() -> list[list[int | None]]:
    weeks = pycal.Calendar(firstweekday=0).monthdayscalendar(1962, 6)
    return [[d or None for d in week] for week in weeks]


def draw_label(layer: Image.Image, text: str, centre: tuple[float, float], size: float, variation: str,
               colour: tuple[int, int, int], rotate: float, ss: int = 4) -> None:
    font = ImageFont.truetype(FONT, round(size * ss))
    font.set_variation_by_name(variation)
    box = font.getbbox(text)
    w, h = box[2] - box[0] + 8 * ss, box[3] - box[1] + 8 * ss
    tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((4 * ss - box[0], 4 * ss - box[1]), text, font=font, fill=colour + (255,))
    tile = tile.rotate(rotate, resample=Image.Resampling.BICUBIC, expand=True)
    cx, cy = centre
    layer.alpha_composite(tile, (round(cx * ss - tile.width / 2), round(cy * ss - tile.height / 2)))


def cell_masks(cfg: dict, size: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    """(header interiors, body interiors) as boolean masks: the cells between the ruled lines, inset from them."""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    xr, ins = cfg["x_ref"], cfg["inset"]
    hline = lambda key: cfg[key][0] + cfg[key][1] * (xx - xr)  # noqa: E731
    v = [x + cfg["vtilt"] * (yy - 400) for x in cfg["vlines"]]
    inside_cols = np.zeros((h, w), dtype=bool)
    for a, b in zip(v[:-1], v[1:]):
        inside_cols |= (xx > a + ins) & (xx < b - ins)
    header = inside_cols & (yy > hline("header_top") + ins) & (yy < hline("header_bottom") - ins)
    body = inside_cols & (yy > hline("header_bottom") + ins) & (yy < hline("bottom") - ins)
    return header, body


def repaint_calendar(img: Image.Image, cfg: dict) -> tuple[Image.Image, Image.Image, dict]:
    """Empty every cell of the weekday row and of the month grid (the ruled lines stay untouched), refill the
    cells from their own paper, then letter the Slovak weekday row and June 1962 in the painting's ink."""
    rgb = np.asarray(img.convert("RGB"), dtype=np.float32)
    if "vlines" in cfg:
        header, body = cell_masks(cfg, img.size)
    else:
        header, body = (np.zeros((img.height, img.width), dtype=bool) for _ in range(2))
        for m, key in ((header, "header"), (body, "body")):
            bx0, by0, bx1, by1 = cfg["rects"][key]
            m[by0:by1, bx0:bx1] = True
    hole = header | body
    lum = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    ys, xs = np.nonzero(hole)
    y0, y1, x0, x1 = ys.min() - 12, ys.max() + 13, xs.min() - 12, xs.max() + 13
    sub, sub_lum, sub_hole = rgb[y0:y1, x0:x1], lum[y0:y1, x0:x1], hole[y0:y1, x0:x1]
    paper = np.asarray(Image.fromarray(sub_lum.clip(0, 255).astype(np.uint8), "L").filter(ImageFilter.MedianFilter(15)),
                       dtype=np.float32)
    ink = sub_lum < paper - 22
    glyph_px = sub[ink & sub_hole]
    order = np.argsort(glyph_px @ np.array([0.299, 0.587, 0.114], dtype=np.float32))
    quant = cfg.get("ink_quantile", 0.3)
    ink_rgb = tuple(int(v) for v in np.median(glyph_px[order[: max(1, int(len(order) * quant))]], axis=0))
    # known paper = outside the cells and not ink (the ruled lines must not bleed into the fill)
    ring = ~sub_hole & ~ink
    paper_ref = float(np.median(sub_lum[ring]))
    not_paper = (sub_lum < paper_ref - 14) | (sub_lum > paper_ref + 30)     # wall, frame edge, shadows, highlights
    if not cfg.get("paper_only"):                     # EPILOGUE_6: the paper itself has a strong light gradient
        not_paper = np.zeros_like(not_paper)
    fill_hole = sub_hole | ink | not_paper
    filled = inpaint(sub, fill_hole)
    keep_lines = (ink | not_paper) & ~sub_hole
    filled = np.where(keep_lines[..., None], sub, filled)
    out = rgb.copy()
    out[y0:y1, x0:x1] = np.where(sub_hole[..., None], filled, sub)
    base = Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGB")
    ss = 4
    layer = Image.new("RGBA", (base.width * ss, base.height * ss), (0, 0, 0, 0))
    red = (min(255, ink_rgb[0] + 70), max(0, ink_rgb[1] - 12), max(0, ink_rgb[2] - 12))   # muted brick red
    hd, bd = cfg["header"], cfg["body"]
    xr = cfg.get("x_ref", 0)
    for c, (x, label) in enumerate(zip(cfg["cols"], WEEKDAYS_SK)):
        colour = red if cfg.get("red_sunday") and c == 6 else ink_rgb
        if "header_top" in cfg:
            top = cfg["header_top"][0] + cfg["header_top"][1] * (x - xr)
            bottom = cfg["header_bottom"][0] + cfg["header_bottom"][1] * (x - xr)
            y = (top + bottom) / 2 + 0.5
        else:
            y = hd["y"]
        draw_label(layer, label, (x, y), hd["size"], hd["variation"], colour, hd["rotate"])
    for r, week in enumerate(june_1962()):
        for c, day in enumerate(week):
            if day is None:
                continue
            colour = red if cfg.get("red_sunday") and c == 6 else ink_rgb
            y = bd["row0"] + r * bd["row_step"] + c * bd["slope"]
            draw_label(layer, str(day), (cfg["cols"][c], y), bd["size"], bd["variation"], colour, bd["rotate"])
    small = layer.resize(base.size, Image.Resampling.LANCZOS)
    if cfg.get("blur", 0.35):
        small = small.filter(ImageFilter.GaussianBlur(cfg.get("blur", 0.35)))
    a = np.asarray(small, dtype=np.float32)
    alpha = np.clip(a[..., 3:4] / 255 * cfg.get("alpha", 0.95), 0, 1)
    res = np.asarray(base, dtype=np.float32) * (1 - alpha) + a[..., :3] * alpha
    result = Image.fromarray(res.clip(0, 255).astype(np.uint8), "RGB")
    mask = (np.maximum(hole, a[..., 3] > 10) * 255).astype(np.uint8)
    info = {"ink_rgb": list(ink_rgb), "red_rgb": list(red)}
    return result, Image.fromarray(mask, "L"), info


def cmd_calendar(args) -> None:
    target = args.target
    cfg = CALENDARS[target]
    master = Image.open(cfg["master"]).convert("RGB")
    result, mask, info = repaint_calendar(master, cfg)
    ys, xs = np.nonzero(np.asarray(mask) > 0)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    REVIEW.mkdir(parents=True, exist_ok=True)
    pad = 30
    box = (x0 - pad, y0 - 80, x1 + pad, y1 + pad)
    before, after = master.crop(box), result.crop(box)
    k = 3
    sheet = Image.new("RGB", (before.width * k * 2 + 10, before.height * k), (20, 20, 20))
    sheet.paste(before.resize((before.width * k, before.height * k), Image.Resampling.LANCZOS), (0, 0))
    sheet.paste(after.resize((after.width * k, after.height * k), Image.Resampling.LANCZOS), (before.width * k + 10, 0))
    side = REVIEW / f"{target}_calendar.png"
    sheet.save(side)
    if args.dry:
        print(f"dry run; LOOK at {side.relative_to(ROOT)}  {info}")
        return
    stem = cfg["master"].stem.rsplit("_v", 1)[0]
    folder = cfg["master"].parent
    version = max(int(q.stem.rsplit("_v", 1)[1]) for q in folder.glob(f"{stem}_v*.png")
                  if q.stem.rsplit("_v", 1)[1].isdigit()) + 1
    out = folder / f"{stem}_v{version}.png"
    result.save(out)
    frame = paint_room.fit_to_frame(result) if cfg["fit"] == "model" else result
    frame.save(cfg["frame_export"], "WEBP", quality=90, method=6)
    meta = {"target": target, "version": version, "kind": "free local calendar repaint (Slovak weekday row, June 1962)",
            "from_master": cfg["master"].relative_to(ROOT).as_posix(), "usd": 0,
            "weekdays": WEEKDAYS_SK, "month": "June 1962 (1 June = Friday), Monday first",
            "geometry": {k2: v for k2, v in cfg.items() if k2 not in ("master", "frame_export")}, **info,
            "review": side.relative_to(ROOT).as_posix(),
            "composed": datetime.datetime.now().isoformat(timespec="seconds")}
    if True:
        src_meta = cfg["master"].with_suffix(".json")
        if src_meta.exists():
            meta["previous_sidecar"] = json.loads(src_meta.read_text(encoding="utf-8"))
        out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=str),
                                            encoding="utf-8")
    print(f"{out.relative_to(ROOT)} -> {cfg['frame_export'].relative_to(ROOT)}; LOOK at {side.relative_to(ROOT)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("cs09")
    p.add_argument("action", choices=["prompt", "run", "compose"])
    p.add_argument("--budget", type=float, default=0.0)
    p.add_argument("--seed", type=int)
    p.add_argument("--version", type=int)
    p = sub.add_parser("cs09-detail")
    p.add_argument("action", choices=["prompt", "run", "compose"])
    p.add_argument("--base-version", type=int, default=4)
    p.add_argument("--budget", type=float, default=0.0)
    p.add_argument("--seed", type=int)
    p.add_argument("--version", type=int)
    p = sub.add_parser("cs09-door")
    p.add_argument("action", choices=["prompt", "run", "compose"])
    p.add_argument("--base-version", type=int, default=5)
    p.add_argument("--budget", type=float, default=0.0)
    p.add_argument("--seed", type=int)
    p.add_argument("--version", type=int)
    p = sub.add_parser("calendar")
    p.add_argument("target", choices=sorted(CALENDARS))
    p.add_argument("--dry", action="store_true", help="review sheet only, write nothing")
    args = ap.parse_args()
    {"cs09": cmd_cs09, "cs09-detail": cmd_cs09_detail, "cs09-door": cmd_cs09_door,
     "calendar": cmd_calendar}[args.cmd](args)


if __name__ == "__main__":
    main()
