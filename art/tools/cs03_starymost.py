"""CS03_1 on the Starý most (owner decision 2026-10-06, docs/DECISIONS.md "Owner answers (2026-10-06, afternoon)").

The cutscene shot CS03_1 plays in S30 right after B22. It was painted on 2026-10-05 at the retired Tyršovo nábrežie
shelter (wooden hut, stone embankment path, castle with white walls and red roofs). S30 is now the measuring booth on
the old Starý most (src/game/assets/bg_natural/S30.webp, log art/masters/bg_natural/S30.md), so the background of the
frame is repainted to that place: the grey-green sheet-metal booth on the plank footway, the riveted truss, the
Danube, Most SNP and the castle in its 1990s colours. Adam's hand and the brass chronometer (counter 1962, four
lights) stay pixel-identical to the accepted master v1: the traced hand + chronometer silhouette HAND (dilated 3 px)
is always the base; everything else comes from the edit.

Pass 1 (run, paid): one Nano Banana Pro edit of the whole frame. References: image 1 the master CS03_1_v1, image 2 the
S30 painting in the state after B22 (coil in the ring, the metronome on the table, the wheels at 3-2-6: the moment the
cutscene plays), image 3 a close-up crop of that booth. -> v2. The model re-composed the scene with a smaller hand, so
its own hand edge showed left of the real one, and it kept v1's pale castle.
Pass 2 (left, paid): a crop edit of the left part to remove that edge -> v3, rejected (the model repainted a new S30).
Pass 3 (retouch, free): the duplicate edge painted over from the footway beside it, the castle recoloured to the
S30 colours, the pseudo-letters in the map circles blanked -> v4 (accepted, exported).

Usage (repo root; PYTHONIOENCODING=utf-8 python -X utf8 art/tools/cs03_starymost.py ...):
  prompt                         prompt + the reference images and the silhouette preview into the review folder (free)
  run --budget B [--seed N]      pass 1 (USD 0.15) -> art/cutscenes/CS03_1_v<N>.png + sidecar + review sheet
  compose --version N            re-composite a pass-1 version from its raw model output (free)
  left prompt|run|compose        pass 2 (run: USD 0.15)
  retouch --base-version N       pass 3 (free) -> next version + review crops
  export --version N             accepted master -> src/game/assets/cutscenes/CS03_1.webp (1920x1080, WebP q90)
Reviews: art/review/reconcile/ (git-ignored). Spend scope: cutscenes/reconcile/CS03_1/ (art/spend-log.csv).
"""
from __future__ import annotations

import argparse
import datetime
import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive_era  # noqa: E402
import fal_api  # noqa: E402
import frame_reconcile  # noqa: E402
import paint_room  # noqa: E402

ROOT = paint_room.ROOT
GAME = ROOT / "src" / "game"
FRAMES = ROOT / "art" / "cutscenes"
REVIEW = ROOT / "art" / "review" / "reconcile"
S30 = GAME / "assets" / "bg_natural" / "S30.webp"
S30_PATCHES = [("variants_natural/S30_coil_in.webp", (158, 466)),          # B20
               ("variants_natural/S30_metronome_placed.webp", (656, 574)),  # B21
               ("variants_natural/S30_dial_326.webp", (406, 518))]          # B22
BOOTH_CROP = (60, 300, 860, 830)   # the booth, the counter and the round table in the S30 frame
BASE_VERSION = 1
SCOPE = "cutscenes/reconcile/CS03_1/"

# Adam's hand + the open chronometer in the 1920x1080 frame (traced on CS03_1_v1 with 25 px grids), clockwise from the
# wrist at the bottom-left edge: the palm's left edge, the raised index finger, the lid, the top finger behind the
# bow ring, the three curled fingers on the right, the palm's lower-right edge.
HAND = [(159, 1080), (180, 1053), (200, 1027), (220, 1000), (238, 973), (251, 940), (255, 890), (249, 853), (246, 803),
        (243, 770), (234, 737), (232, 703), (238, 680), (248, 637), (255, 605), (257, 570), (265, 540), (280, 510),
        (300, 480), (302, 420), (315, 412), (332, 415), (350, 435), (356, 434), (394, 390), (456, 362), (512, 356), (556, 371), (572, 409), (569, 465), (562, 500),
        (550, 527), (575, 552), (600, 548), (640, 527), (673, 493), (720, 470), (773, 457), (800, 460), (813, 477),
        (813, 500), (800, 517), (790, 530), (795, 545), (785, 575), (800, 580), (833, 583), (852, 600), (853, 623),
        (837, 643), (800, 650), (772, 665), (780, 680), (813, 680), (837, 700), (840, 727), (823, 743), (793, 753),
        (770, 765), (753, 790), (780, 788), (807, 800), (817, 823), (810, 847), (790, 860), (760, 867), (725, 894),
        (678, 932), (640, 971), (609, 1009), (578, 1055), (567, 1080)]
KEEP_DILATE = 3      # px outside the traced outline still taken from the base (the painted contour line)
FEATHER = 2          # px soft edge outward

PROMPT = """You receive 3 images. Image 1 is a finished cutscene frame of our point-and-click adventure game, June 1995 in Bratislava: a close-up of Adam's hand holding the open brass ZVON chronometer; its mechanical digit counter has just clicked over to 1962 and its four small lights glow. The background of image 1 still shows an old riverside place that is no longer in the game. Image 2 is our finished background painting of the room where this moment really happens: the wooden plank footway of the old Starý most, the riveted grey steel truss bridge over the Danube, in 1995, with a small grey-green sheet-metal measuring booth. Image 3 is a close-up of that booth from image 2.

Edit image 1. Keep Adam's hand and the brass chronometer exactly as they are, pixel for pixel: the same size, position and pose, every finger, the open lid with the bell engraving, the bow ring and the crown, the counter window reading exactly 1962, the four lights (amber, red, blue, white), the brass reflections.
Change ONLY everything behind the hand and the chronometer into the place of image 2, seen from close up, as if Adam stands on the bridge footway right in front of the booth and holds the chronometer up at chest height:
- behind the hand, on the left and in the centre, slightly out of focus: the measuring booth of images 2 and 3 - faded grey-green riveted sheet-metal walls, a corrugated metal roof with a small plain red pennant, the propped-open hatch with its wooden counter. On the counter: the ring holder with the copper measuring coil sitting in it, a faint warm glow fading out of its windings as it comes to rest; the small wooden demo circuit board with red and blue wires; the grey box with its three number wheels (too small and soft to read). Inside the booth, pinned on its back wall, a sheet of paper map with two places circled in red (lines only, no lettering);
- right of the booth at the railing: the small round wooden table with a wooden metronome standing on its white mark, as in image 2;
- on the right: the grey footway railing with thin vertical bars, and beyond it the turquoise Danube with sun glitter, the green Petrzalka bank with trees on the left, Most SNP with its slanted pylon, the cables and the round saucer on top, Bratislava Castle on its hill with ochre-yellow walls, dark slate roofs and four dark corner towers (its 1990s colours: not white walls, not red roofs), the green-copper spire of St Martin's Cathedral and the red-roofed houses of the Old Town, a white riverboat at the far quay - the same panorama as in image 2;
- at the right edge of the frame: a riveted grey steel truss member of the bridge with an X brace and a large riveted gusset plate, as in image 2; at the very left edge a riveted grey vertical truss member;
- at the bottom, around the wrist: the weathered wooden planks of the footway in sunlight.
Remove completely: the wooden hut, the stone embankment path and its paving, the old iron railing along the embankment, the tree at the top left, the old pale castle with red roofs.

Light: the warm late-afternoon sun of image 2, glints on the water and on the brass. No people, no animals, no text, no lettering and no numbers in the background; the only digits in the whole picture stay the 1962 on the chronometer. The result is image 1 edited, in the same 16:9 framing and camera: no frames, no borders, no letterbox bars, no captions, no watermark. Keep the painting technique, brushwork, palette handling and level of detail of image 1; the new background is painted like image 2, a little softer because it is behind the focus."""


def base_master() -> Image.Image:
    return Image.open(FRAMES / f"CS03_1_v{BASE_VERSION}.png").convert("RGB")


def base_frame() -> Image.Image:
    return paint_room.fit_to_frame(base_master()).convert("RGB")


def s30_state() -> Image.Image:
    img = Image.open(S30).convert("RGBA")
    for rel, pos in S30_PATCHES:
        img.alpha_composite(Image.open(GAME / "assets" / rel).convert("RGBA"), pos)
    return img.convert("RGB")


def booth_closeup(s30: Image.Image) -> Image.Image:
    crop = s30.crop(BOOTH_CROP)
    return crop.resize((crop.width * 2, crop.height * 2), Image.Resampling.LANCZOS)


def hand_mask(size=(1920, 1080)) -> Image.Image:
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(HAND, fill=255)
    return m


def composite(base: Image.Image, edit: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Mask = where the model output is used (255): everywhere except the hand + chronometer silhouette (dilated by
    KEEP_DILATE px so the painted outline stays the base's, feathered outward by FEATHER px)."""
    poly = hand_mask(base.size).filter(ImageFilter.MaxFilter(2 * KEEP_DILATE + 1))
    keep = poly.filter(ImageFilter.MaxFilter(2 * FEATHER + 1)).filter(ImageFilter.GaussianBlur(FEATHER))
    k = np.maximum(np.asarray(keep, dtype=np.float32), np.asarray(poly, dtype=np.float32))
    mask = Image.fromarray((255 - k).clip(0, 255).astype(np.uint8), "L")
    return Image.composite(edit, base, mask), mask


def build(version: int, raw_path: Path, meta: dict) -> Path:
    base = base_frame()
    raw = derive_era.as_model(Image.open(raw_path))
    small = (paint_room.MODEL_FRAME[0] // 4, paint_room.MODEL_FRAME[1] // 4)
    gx, gy = derive_era.phase_shift(derive_era.gray(raw, small), derive_era.gray(base_master(), small))
    gx, gy = gx * 4, gy * 4
    if (gx or gy) and max(abs(gx), abs(gy)) <= derive_era.GLOBAL_COMPENSATE:
        raw = ImageChops.offset(raw, -gx, -gy)
        meta["compensated_master_px"] = [gx, gy]
        print(f"model output drifted by {gx:+d},{gy:+d} master px; compensated")
    edit = paint_room.fit_to_frame(raw).convert("RGB")
    result, mask = composite(base, edit)
    out = FRAMES / f"CS03_1_v{version}.png"
    result.save(out)
    REVIEW.mkdir(parents=True, exist_ok=True)
    edit.save(REVIEW / f"CS03_1_v{version}_model.jpg", quality=90)
    side = frame_reconcile.review_sheet(f"CS03_1_v{version}", base, result, mask,
                                        f"CS03_1 v{version} (Stary most background)")
    meta.update({"compose": {"base_version": BASE_VERSION, "hand": HAND, "keep_dilate": KEEP_DILATE,
                             "feather": FEATHER},
                 "output_size": list(result.size), "composed": datetime.datetime.now().isoformat(timespec="seconds"),
                 "review": side.relative_to(ROOT).as_posix()})
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{out.relative_to(ROOT)}; LOOK at {side.relative_to(ROOT)} and "
          f"{(REVIEW / f'CS03_1_v{version}_model.jpg').relative_to(ROOT)}")
    return out


def job() -> dict:
    s30 = s30_state()
    images = [("base", base_master(), f"art/cutscenes/CS03_1_v{BASE_VERSION}.png (accepted master, counter 1962)"),
              ("ref", s30, "src/game/assets/bg_natural/S30.webp + the B20/B21/B22 state patches"),
              ("ref", booth_closeup(s30), f"crop {list(BOOTH_CROP)} of image 2, 2x")]
    return {"images": images, "prompt": PROMPT + "\n\n" + paint_room.style_sentence()}


def cmd_prompt(_args) -> None:
    j = job()
    print(j["prompt"])
    REVIEW.mkdir(parents=True, exist_ok=True)
    for i, (_, img, name) in enumerate(j["images"], 1):
        img.convert("RGB").save(REVIEW / f"CS03_1_ref{i}.jpg", quality=88)
        print(f"image {i}: {name}")
    base = base_frame()
    tint = Image.new("RGB", base.size, (0, 255, 120))
    Image.composite(Image.blend(base, tint, 0.45), base, hand_mask()).save(REVIEW / "CS03_1_hand.jpg", quality=88)
    print(f"hand silhouette: {(REVIEW / 'CS03_1_hand.jpg').relative_to(ROOT)}")


def cmd_run(args) -> None:
    j = job()
    version = frame_reconcile.next_version("CS03_1")
    seed = args.seed if args.seed is not None else random.randint(1, 2 ** 31 - 1)
    urls = [fal_api.image_data_uri(j["images"][0][1], fmt="PNG")]
    urls += [fal_api.image_data_uri(img, max_side=2048, fmt="JPEG") for _, img, _ in j["images"][1:]]
    arguments = {"prompt": j["prompt"], "image_urls": urls, "aspect_ratio": paint_room.ASPECT,
                 "resolution": paint_room.RESOLUTION, "output_format": "png", "num_images": 1, "seed": seed}
    price = fal_api.IMAGE_PRICES[(paint_room.MODEL, paint_room.RESOLUTION)]
    asset = f"{SCOPE}CS03_1_v{version}_starymost"
    started = datetime.datetime.now().isoformat(timespec="seconds")
    result = fal_api.run(paint_room.MODEL, arguments, asset, price, budget=(SCOPE, args.budget), timeout_s=900)
    raw = FRAMES / f"_CS03_1_v{version}_starymost_raw.png"
    fal_api.download(result["images"][0]["url"], raw)
    meta = {"target": "CS03_1", "version": version, "kind": "reconcile with the Stary most S30 painting",
            "model": paint_room.MODEL, "resolution": paint_room.RESOLUTION, "seed": result.get("seed", seed),
            "usd": price, "scope": SCOPE, "spend_log_asset": asset, "started": started, "prompt": j["prompt"],
            "image_urls": [name for _, _, name in j["images"]], "model_description": result.get("description"),
            "raw_model_output": raw.relative_to(ROOT).as_posix()}
    build(version, raw, meta)
    print(f"scope {SCOPE} spent {fal_api.logged_spend(SCOPE):.2f} of {args.budget:.2f}")


def cmd_compose(args) -> None:
    side = FRAMES / f"CS03_1_v{args.version}.json"
    meta = json.loads(side.read_text(encoding="utf-8"))
    meta["recomposed"] = True
    build(args.version, ROOT / meta["raw_model_output"], meta)


def cmd_export(args) -> None:
    src = FRAMES / f"CS03_1_v{args.version}.png"
    img = Image.open(src).convert("RGB")
    assert img.size == (1920, 1080), img.size
    dest = GAME / "assets" / "cutscenes" / "CS03_1.webp"
    img.save(dest, "WEBP", quality=90, method=6)
    side = src.with_suffix(".json")
    meta = json.loads(side.read_text(encoding="utf-8"))
    meta["exported"] = {"path": dest.relative_to(ROOT).as_posix(), "at": datetime.datetime.now().isoformat(timespec="seconds")}
    side.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")


# --- pass 2 (paid): a crop edit of the left part. Pass 1 re-composed the scene with a smaller hand; its own hand shows
# left of the real one (a paler thumb, palm edge and a sliver of the lid between the truss member and the hand). The
# crop is edited and only LEFT_REGION outside the hand silhouette is taken.

LEFT_CROP = (0, 330, 1333, 1080)          # 16:9 crop of the frame: x0, y0, x1, y1
LEFT_REGION = [(110, 470), (340, 470), (340, 1080), (110, 1080)]
LEFT_FEATHER_Y = (470, 500)               # soft top edge, inside the footway below the railing
LEFT_PROMPT = """You receive 2 images. Image 1 is a crop of a finished cutscene frame of our point-and-click adventure game: on the wooden footway of the old Starý most in Bratislava (June 1995), Adam's hand holds the open brass chronometer in front of the grey-green sheet-metal measuring booth. Image 2 is our background painting of this bridge footway.

Image 1 has one painting mistake: directly LEFT of Adam's hand there is a second, paler copy of a hand - a thumb, the edge of a palm and a thin sliver of brass - standing between the riveted grey steel member at the left edge and the real hand. Remove that duplicate hand completely and paint what is behind it: the weathered wooden planks of the bridge footway in warm late-afternoon sun, as in image 2, with the soft long shadows of the railing bars falling across them; continue the planks right up to the outline of the real hand. In the same area, replace the pale stone-like surface with round dappled leaf shadows (there are no trees on the bridge) by these sunlit planks.

Keep everything else exactly as it is in image 1: Adam's real hand (the large hand holding the chronometer) and its outline, the chronometer, the riveted grey steel member and its rivets at the left edge, the railing, the booth, the copper coil, the counter and the planks on the right. No people, no animals, no text. The result is image 1 edited, in the same 16:9 framing: no frames, no borders, no captions. Keep the painting technique, brushwork and palette of image 1."""


def left_mask(size=(1920, 1080)) -> Image.Image:
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(LEFT_REGION, fill=255)
    a = np.asarray(m.filter(ImageFilter.GaussianBlur(2)), dtype=np.float32)
    y0, y1 = LEFT_FEATHER_Y
    a = a * np.clip((np.arange(size[1]) - y0) / (y1 - y0), 0, 1)[:, None]
    hand = np.asarray(hand_mask(size).filter(ImageFilter.MaxFilter(2 * KEEP_DILATE + 1))
                      .filter(ImageFilter.MaxFilter(2 * FEATHER + 1)).filter(ImageFilter.GaussianBlur(FEATHER)),
                      dtype=np.float32)
    a = a * (1 - hand / 255)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "L")


def left_build(base_version: int, version: int, raw_path: Path, meta: dict) -> Path:
    base = Image.open(FRAMES / f"CS03_1_v{base_version}.png").convert("RGB")
    crop = base.crop(LEFT_CROP)
    raw = derive_era.as_model(Image.open(raw_path))
    model_in = frame_reconcile.crop_to_model(crop)
    small = (paint_room.MODEL_FRAME[0] // 4, paint_room.MODEL_FRAME[1] // 4)
    gx, gy = derive_era.phase_shift(derive_era.gray(raw, small), derive_era.gray(model_in, small))
    gx, gy = gx * 4, gy * 4
    if (gx or gy) and max(abs(gx), abs(gy)) <= derive_era.GLOBAL_COMPENSATE:
        raw = ImageChops.offset(raw, -gx, -gy)
        meta["compensated_model_px"] = [gx, gy]
        print(f"model output drifted by {gx:+d},{gy:+d} model px; compensated")
    edit = base.copy()
    edit.paste(frame_reconcile.model_to_crop(raw, crop.size), LEFT_CROP[:2])
    mask = left_mask(base.size)
    result = Image.composite(edit, base, mask)
    out = FRAMES / f"CS03_1_v{version}.png"
    result.save(out)
    REVIEW.mkdir(parents=True, exist_ok=True)
    edit.save(REVIEW / f"CS03_1_v{version}_model.jpg", quality=90)
    side = frame_reconcile.review_sheet(f"CS03_1_v{version}", base, result, mask, f"CS03_1 v{version} (left strip)")
    meta.update({"compose": {"base_version": base_version, "crop": LEFT_CROP, "region": LEFT_REGION,
                             "feather_y": LEFT_FEATHER_Y, "hand_excluded": True},
                 "output_size": list(result.size), "composed": datetime.datetime.now().isoformat(timespec="seconds"),
                 "review": side.relative_to(ROOT).as_posix()})
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{out.relative_to(ROOT)}; LOOK at {side.relative_to(ROOT)}")
    return out


def cmd_left(args) -> None:
    if args.action == "compose":
        meta = json.loads((FRAMES / f"CS03_1_v{args.version}.json").read_text(encoding="utf-8"))
        meta["recomposed"] = True
        left_build(meta["compose"]["base_version"], args.version, ROOT / meta["raw_model_output"], meta)
        return
    base = Image.open(FRAMES / f"CS03_1_v{args.base_version}.png").convert("RGB")
    model_in = frame_reconcile.crop_to_model(base.crop(LEFT_CROP))
    ref = s30_state()
    prompt = LEFT_PROMPT + "\n\n" + paint_room.style_sentence()
    REVIEW.mkdir(parents=True, exist_ok=True)
    model_in.save(REVIEW / "CS03_1_left_in.jpg", quality=88)
    if args.action == "prompt":
        print(prompt)
        tint = Image.new("RGB", base.size, (255, 0, 160))
        Image.composite(Image.blend(base, tint, 0.45), base, left_mask(base.size)).save(
            REVIEW / "CS03_1_left_region.jpg", quality=88)
        print("image 1: art/review/reconcile/CS03_1_left_in.jpg; region: art/review/reconcile/CS03_1_left_region.jpg")
        return
    version = frame_reconcile.next_version("CS03_1")
    seed = args.seed if args.seed is not None else random.randint(1, 2 ** 31 - 1)
    urls = [fal_api.image_data_uri(model_in, fmt="PNG"), fal_api.image_data_uri(ref, max_side=2048, fmt="JPEG")]
    arguments = {"prompt": prompt, "image_urls": urls, "aspect_ratio": paint_room.ASPECT,
                 "resolution": paint_room.RESOLUTION, "output_format": "png", "num_images": 1, "seed": seed}
    price = fal_api.IMAGE_PRICES[(paint_room.MODEL, paint_room.RESOLUTION)]
    asset = f"{SCOPE}CS03_1_v{version}_left"
    started = datetime.datetime.now().isoformat(timespec="seconds")
    result = fal_api.run(paint_room.MODEL, arguments, asset, price, budget=(SCOPE, args.budget), timeout_s=900)
    raw = FRAMES / f"_CS03_1_v{version}_left_raw.png"
    fal_api.download(result["images"][0]["url"], raw)
    meta = {"target": "CS03_1", "version": version, "kind": "crop edit: remove the duplicate hand edge left of the hand",
            "model": paint_room.MODEL, "resolution": paint_room.RESOLUTION, "seed": result.get("seed", seed),
            "usd": price, "scope": SCOPE, "spend_log_asset": asset, "started": started, "prompt": prompt,
            "image_urls": [f"crop {list(LEFT_CROP)} of art/cutscenes/CS03_1_v{args.base_version}.png",
                           "src/game/assets/bg_natural/S30.webp + state patches"],
            "model_description": result.get("description"), "raw_model_output": raw.relative_to(ROOT).as_posix()}
    left_build(args.base_version, version, raw, meta)
    print(f"scope {SCOPE} spent {fal_api.logged_spend(SCOPE):.2f} of {args.budget:.2f}")


# --- pass 3 (free): local retouch of the accepted composite.
# a) the duplicate hand edge of pass 1 left of the real hand is painted over from the footway beside it: below y 780
#    each pixel continues the plank joints (they run up-right towards the booth, direction (-1, +0.5) back to the
#    clean band), above y 740 the soft sun-and-shadow surface is mirrored from the clean band at the ghost's edge;
#    the base hand is pasted back on top.
# b) the castle keeps the base's silhouette but gets its 1990s colours from bg_natural/S30 (ochre-yellow walls, dark
#    slate roofs and tower caps): pixels classed by colour inside traced polygons, sky, trees and windows untouched.

GHOST_EDGE = [(203, 536), (203, 541), (178, 587), (175, 637), (168, 675), (162, 725), (153, 769), (150, 820),
              (161, 870), (167, 920), (169, 953), (164, 980), (151, 1007), (134, 1033), (118, 1060),
              (118, 1080)]   # 6 px left of the ghost's outline (it reaches the riveted member below y 1060)
GHOST_RIGHT_X = 420          # the fill polygon reaches into the hand; the hand is restored from the base afterwards
CLEAN_X0 = 112               # inner edge of the riveted member at the left frame edge
PLANK_DIR = (-1.0, 0.5)
MIRROR_Y, PLANK_Y = 740, 780
MIRROR_SHEAR = 0.6
BOARD_PX = 70                # vertical repeat of the boards for the rows under the letterbox bar

CASTLE_BODY = [(1156, 112), (1185, 112), (1236, 102), (1236, 96), (1256, 96), (1256, 110), (1334, 110), (1352, 106),
               (1354, 182), (1156, 182)]
CASTLE_ROOFS = [[(1170, 93), (1158, 116), (1183, 116)],                      # left tower cap
                [(1246, 85), (1236, 103), (1256, 103)],                      # middle tower cap
                [(1343, 92), (1333, 110), (1353, 110)],                      # right tower cap
                [(1173, 141), (1181, 122), (1238, 113), (1239, 128)],        # left palace roof
                [(1255, 113), (1335, 114), (1342, 132), (1255, 129)]]        # right palace roof
OCHRE = ((150, 112, 82), (250, 196, 122))      # shade, lit (sampled from bg_natural/S30)
SLATE = ((52, 56, 72), (112, 114, 130))


def ghost_edge_x(ys: np.ndarray) -> np.ndarray:
    gy = np.array([p[1] for p in GHOST_EDGE], dtype=np.float32)
    gx = np.array([p[0] for p in GHOST_EDGE], dtype=np.float32)
    return np.interp(ys, gy, gx)


def fill_ghost(img: Image.Image) -> tuple[Image.Image, Image.Image]:
    a = np.asarray(img, dtype=np.float32)
    h, w = a.shape[:2]
    poly = Image.new("L", (w, h), 0)
    ImageDraw.Draw(poly).polygon(GHOST_EDGE + [(GHOST_RIGHT_X, 1080), (GHOST_RIGHT_X, GHOST_EDGE[0][1])], fill=255)
    region = np.asarray(poly) > 0
    ys, xs = np.nonzero(region)
    out = a.copy()
    # plank continuation: step back along the joint direction until the point lies in the clean band
    px, py = xs.astype(np.float32), ys.astype(np.float32)
    for _ in range(400):
        inside = px >= ghost_edge_x(np.clip(py, 0, h - 1)) - 1
        if not inside.any():
            break
        px = np.where(inside, px + PLANK_DIR[0], px)
        py = np.where(inside, py + PLANK_DIR[1], py)
    off_frame = (py > h - 1)[:, None]
    plank = a[np.clip(py, 0, h - 1).astype(int), np.clip(px, CLEAN_X0, w - 1).astype(int)]
    # mirror about the ghost edge (ping-pong inside the clean band)
    edge = ghost_edge_x(ys.astype(np.float32))
    span = np.maximum(edge - CLEAN_X0, 8)
    d = (xs - edge) % (2 * span)
    mx = np.where(d <= span, edge - d, edge - (2 * span - d))
    my = ys + MIRROR_SHEAR * np.abs(xs - edge)       # sheared, so the mirrored shadows do not read as symmetric
    mirror = a[np.clip(my, 0, h - 1).astype(int), np.clip(mx, CLEAN_X0, w - 1).astype(int)]
    plank = np.where(off_frame, mirror, plank)       # bottom rows (under the letterbox bar): no joint source left
    t = np.clip((ys - MIRROR_Y) / max(PLANK_Y - MIRROR_Y, 1), 0, 1)[:, None]
    out[ys, xs] = mirror * (1 - t) + plank * t
    # rows whose joints leave the frame (y > ~1000, under the letterbox bar): repeat the planks one board higher up
    off = off_frame[:, 0]
    for y in np.unique(ys[off]):
        sel = off & (ys == y)
        out[y, xs[sel]] = out[max(y - BOARD_PX, 0), xs[sel]]
    filled = Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(0.6))
    soft = poly.filter(ImageFilter.GaussianBlur(2))
    return Image.composite(filled, img, soft), soft


def recolour_castle(img: Image.Image) -> tuple[Image.Image, Image.Image]:
    a = np.asarray(img, dtype=np.float32)
    h, w = a.shape[:2]
    body = Image.new("L", (w, h), 0)
    ImageDraw.Draw(body).polygon(CASTLE_BODY, fill=255)
    roofs = Image.new("L", (w, h), 0)
    for poly in CASTLE_ROOFS:
        ImageDraw.Draw(roofs).polygon(poly, fill=255)
    body_m, roof_m = np.asarray(body) > 0, np.asarray(roofs) > 0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    # soft classes (no stair-stepping between roof and wall); trees, windows and sky keep their pixels
    roof_w = roof_m * np.clip((r - g - 15) / 20, 0, 1)
    tree = (g - b > 12) & (r - g < 32) & (lum < 195)
    window = (r - g > 35) & (g - b > 25) & (lum < 175) & ~roof_m
    sky = (lum > 200) & (r - b < 32)
    region = (body_m | roof_m) & ~tree & ~window & ~sky
    # the greyish anti-aliased fringe between the shaded wall and the tree tops belongs to the wall
    near = np.asarray(Image.fromarray((region * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(5))) > 0
    fringe = tree & near & (a.max(-1) - a.min(-1) < 40) & body_m
    region = region | fringe
    out = a.copy()
    tw = np.clip((lum - 150) / (235 - 150), 0, 1)[..., None]
    wall = np.array(OCHRE[0]) * (1 - tw) + np.array(OCHRE[1]) * tw
    tr = np.clip((lum - 95) / (175 - 95), 0, 1)[..., None]
    roof = np.array(SLATE[0]) * (1 - tr) + np.array(SLATE[1]) * tr
    new = roof * roof_w[..., None] + wall * (1 - roof_w[..., None])
    out[region] = new[region]
    mask = Image.fromarray((region * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.8))
    result = Image.composite(Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGB"), img, mask)
    return result, mask


MAP_SCRIBBLES = [(800, 260, 820, 278), (862, 302, 895, 321)]   # pseudo-letters the model wrote inside the two circles


def blank_scribbles(img: Image.Image) -> Image.Image:
    """The pinned map keeps its lines and red circles; the tiny pseudo-letters inside the circles become paper."""
    out = img.copy()
    for box in MAP_SCRIBBLES:
        c = np.asarray(img.crop(box), dtype=np.float32)
        lum = c @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        red = (c[..., 0] - c[..., 1]) > 60
        paper_lum = np.percentile(lum[~red], 70)
        paper = np.median(c[(lum >= paper_lum - 6) & ~red], axis=0)
        ink = (lum < paper_lum - 18) & ~red
        m = Image.fromarray((ink * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(3))
        fill = Image.new("RGB", m.size, tuple(int(v) for v in paper))
        patch = Image.composite(fill, img.crop(box), m.filter(ImageFilter.GaussianBlur(0.8)))
        out.paste(patch, box[:2])
    return out


def cmd_retouch(args) -> None:
    global MIRROR_Y, PLANK_Y
    if args.mirror_y is not None:
        MIRROR_Y, PLANK_Y = args.mirror_y, args.plank_y
    src = Image.open(FRAMES / f"CS03_1_v{args.base_version}.png").convert("RGB")
    step1, ghost_mask = fill_ghost(src)
    base = base_frame()
    hand = hand_mask(base.size).filter(ImageFilter.MaxFilter(2 * KEEP_DILATE + 1))
    hand = hand.filter(ImageFilter.MaxFilter(2 * FEATHER + 1)).filter(ImageFilter.GaussianBlur(FEATHER))
    step1 = Image.composite(base, step1, hand)
    result, castle_mask = recolour_castle(blank_scribbles(step1))
    version = frame_reconcile.next_version("CS03_1")
    out = FRAMES / f"CS03_1_v{version}.png"
    result.save(out)
    shown = ImageChops.lighter(ghost_mask, castle_mask)
    side = frame_reconcile.review_sheet(f"CS03_1_v{version}", src, result, Image.eval(shown, lambda v: 255 - v),
                                        f"CS03_1 v{version} (free retouch of v{args.base_version})")
    REVIEW.mkdir(parents=True, exist_ok=True)
    for name, box, s in (("left", (40, 480, 360, 1080), 2), ("castle", (1120, 70, 1380, 200), 4)):
        pair = Image.new("RGB", ((box[2] - box[0]) * s * 2 + 10, (box[3] - box[1]) * s), (20, 20, 20))
        pair.paste(src.crop(box).resize(((box[2] - box[0]) * s, (box[3] - box[1]) * s)), (0, 0))
        pair.paste(result.crop(box).resize(((box[2] - box[0]) * s, (box[3] - box[1]) * s)),
                   ((box[2] - box[0]) * s + 10, 0))
        pair.save(REVIEW / f"CS03_1_v{version}_{name}.jpg", quality=90)
    meta = {"target": "CS03_1", "version": version, "kind": "free local retouch", "usd": 0, "base_version": args.base_version,
            "retouch": {"ghost_edge": GHOST_EDGE, "clean_x0": CLEAN_X0, "plank_dir": PLANK_DIR,
                        "mirror_y": MIRROR_Y, "plank_y": PLANK_Y, "mirror_shear": MIRROR_SHEAR, "castle_body": CASTLE_BODY,
                        "castle_roofs": CASTLE_ROOFS, "ochre": OCHRE, "slate": SLATE,
                        "map_scribbles_blanked": MAP_SCRIBBLES,
                        "hand_restored_from": f"CS03_1_v{BASE_VERSION}"},
            "output_size": list(result.size), "composed": datetime.datetime.now().isoformat(timespec="seconds"),
            "review": side.relative_to(ROOT).as_posix()}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{out.relative_to(ROOT)}; LOOK at {side.relative_to(ROOT)}, art/review/reconcile/CS03_1_v{version}_left.jpg, "
          f"_castle.jpg")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prompt")
    r = sub.add_parser("run")
    r.add_argument("--budget", type=float, required=True)
    r.add_argument("--seed", type=int)
    c = sub.add_parser("compose")
    c.add_argument("--version", type=int, required=True)
    e = sub.add_parser("export")
    e.add_argument("--version", type=int, required=True)
    lf = sub.add_parser("left")
    lf.add_argument("action", choices=["prompt", "run", "compose"])
    lf.add_argument("--base-version", type=int, default=2)
    lf.add_argument("--version", type=int)
    lf.add_argument("--budget", type=float, default=0.30)
    lf.add_argument("--seed", type=int)
    rt = sub.add_parser("retouch")
    rt.add_argument("--base-version", type=int, default=2)
    rt.add_argument("--mirror-y", type=int, help="above this row the clean band is mirrored (default MIRROR_Y)")
    rt.add_argument("--plank-y", type=int, help="below this row the plank joints are continued (default PLANK_Y)")
    args = ap.parse_args()
    {"prompt": cmd_prompt, "run": cmd_run, "compose": cmd_compose, "export": cmd_export,
     "left": cmd_left, "retouch": cmd_retouch}[args.cmd](args)


if __name__ == "__main__":
    main()
