"""Winter-coat variant of the hero set (ADAM, December 1982 exteriors; ISSUES PT-S20).

The default set (hero_set.py, PIPELINE.md section 11) is re-dressed, not re-animated by hand:
  * the three facing bases and the six key poses get one NB2 2K "same man, same pose, winter coat + scarf" edit each;
  * the HEAD of every facing base is transplanted back from the default master (rows above the scarf), so the
    default blink and mouth frames apply unchanged and the face stays pixel-identical to the jacket set;
  * walks and pose transitions are new Hailuo-02 Pro clips from the coat stills (same prompts as the default set,
    jacket wording replaced), cut by the unchanged hero_set.py stages.
Everything lives in art/characters/ADAM/coat1982/ (same layout as art/characters/ADAM/), so hero_set.py stages run on
it with --char ADAM/coat1982. Shipped as `<name>_coat1982` sheets next to the default ones (variant "coat1982").

Stages (run from art/tools):
  edit NAME [NAME ...]   paid: NB2 2K coat edit of a facing base (side, front, back) or key pose (reach_low, ...)
  masters                free: key, align, head transplant, face caches, video input canvases
  video NAME [NAME ...]  paid: Hailuo-02 Pro clip (walk_right, walk_toward, walk_away or a pose name)
  build                  free: idle / talk / walk / one-shot sheets via hero_set.py (char ADAM/coat1982)
  export                 free: WebP sheets + JSON into src/game/assets/actors/ADAM/ and the animations.json entries
  review                 free: default vs coat comparison sheets (build/screens/fixes/art/)

Every paid call goes through task_guard (spend-log prefixes TASK_PREFIXES since --since, cap --budget).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

import chars
import fal_api
import frames as fr
import hero_set as hs

ART = fal_api.ART
REPO = ART.parent
ADAM = ART / "characters" / "ADAM"
CHAR = "ADAM/coat1982"
COAT = ART / "characters" / CHAR
VARIANT = "coat1982"
GAME_DIR = REPO / "src" / "game" / "assets" / "actors" / "ADAM"
REVIEW = REPO / "build" / "screens" / "fixes" / "art"

# Task budget (art fixes 2026-10-05, USD 8 for the coat, CS07 ports, TOOLS icon and other open art items).
TASK_PREFIXES = ("characters/ADAM/coat1982/", "cutscenes/fix/", "items/TOOLS/fix/", "bg_natural/fix/")
TASK_SINCE = "2026-10-05T21:50"
TASK_BUDGET = 8.00

COAT_LOOK = (
    "a plain hip-length winter coat of thick dark charcoal-grey wool, closed all the way up the front with a row "
    "of dark buttons, a small turned-down collar, long sleeves that reach down to his wrists, two plain flap "
    "pockets at the hips; around his neck a thick knitted mustard-yellow wool scarf, wrapped once and snug around "
    "the neck below the chin, its ends tucked inside the closed coat"
)

FACING_NOTE = {
    "side": "He is still in the same side view facing right.",
    "front": "He is still in the same front view facing the viewer.",
    "back": "He is still seen from behind, his back to the viewer: we see the back of the coat, the scarf around "
            "the back of his neck and the bag strap across his back.",
}

POSE_NOTE = {
    "reach_low": "He is still crouching in exactly the same pose, reaching down toward the floor; his hand is empty.",
    "reach_mid": "He still reaches forward at chest height in exactly the same pose; his hand is empty.",
    "reach_high": "He still stretches his arm up above his head in exactly the same pose; his hand is empty.",
    "use_tool": "He still works with the same small screwdriver in his right hand in exactly the same pose; the "
                "screwdriver stays exactly as it is and is the only object in his hands.",
    "show_item": "He still holds his right hand out palm up in exactly the same pose; the hand is empty.",
    "inventory_combine": "He still faces the viewer with both hands in front of his stomach in exactly the same "
                         "pose, fingertips pinched together; his hands are empty. The scarf is wrapped snugly around his neck and its "
                         "ends are tucked inside the closed coat: nothing hangs down in front of his hands. He keeps "
                         "exactly the same size in the frame: the top of his hair and his shoes stay where they are.",
}

FACINGS = ("side", "front", "back")


def coat_prompt(name: str) -> str:
    note = FACING_NOTE.get(name) or POSE_NOTE[name]
    return " ".join([
        "Edit the first image: the same man with the same face, the same hair, the same pose, the same position "
        "and size in the frame, the same dark jeans, the same brown shoes and the same brown leather messenger bag, "
        "on the same flat green background. " + note + " Change ONLY his clothes on the upper body for a cold "
        "snowy December day: instead of the open blue work jacket and the mustard T-shirt he now wears " + COAT_LOOK
        + ". The strap of the messenger bag now runs over the coat from his right shoulder across his chest, and "
        "the bag rests on his left hip exactly where it was. No hat, no gloves. His face, hair, hands, jeans, shoes "
        "and the bag stay exactly as they are. Do not move, turn or rescale him.",
        chars.POSE_GUARD, chars.key_background("green"), chars.STYLE_FOR_CHARACTER + chars.STYLE_A])


# ----------------------------------------------------------------------------- robust result saving

def robust_download(url: str, dest: Path, attempts: int = 6) -> Path:
    """fal_api.download with retries and a streamed body (a v3b.fal.media read once timed out and lost a result)."""
    import shutil
    import subprocess
    import time
    import requests
    dest.parent.mkdir(parents=True, exist_ok=True)
    curl = shutil.which("curl")
    if curl:   # curl got through where requests' reads stalled on v3b.fal.media
        tmp = dest.with_suffix(dest.suffix + ".part")
        done = subprocess.run([curl, "-s", "-L", "--retry", "6", "--retry-delay", "4", "--retry-all-errors",
                               "--max-time", "900", "-A", fal_api.USER_AGENT, "-o", str(tmp), url])
        if done.returncode == 0 and tmp.exists() and tmp.stat().st_size > 1000:
            tmp.replace(dest)
            return dest
        print(f"[download] curl failed ({done.returncode}) for {dest.name}; trying requests", file=sys.stderr)
    for attempt in range(attempts):
        try:
            with requests.get(url, timeout=(20, 60), stream=True, headers={"User-Agent": fal_api.USER_AGENT}) as r:
                r.raise_for_status()
                tmp = dest.with_suffix(dest.suffix + ".part")
                with tmp.open("wb") as handle:
                    for chunk in r.iter_content(1 << 16):
                        handle.write(chunk)
                tmp.replace(dest)
                return dest
        except Exception as error:  # network hiccup: retry
            print(f"[download] {dest.name}: attempt {attempt + 1} failed: {error}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"download failed: {url}")


def save_result(result: dict, out_base: Path, meta: dict) -> list[Path]:
    """Keep the raw result (URLs) first, then download every output; `fetch` can redo the download later."""
    out_base.parent.mkdir(parents=True, exist_ok=True)
    out_base.with_suffix(".result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    paths: list[Path] = []
    if "video" in result:
        paths.append(robust_download(result["video"]["url"], out_base.with_suffix(".mp4")))
    for index, image in enumerate(result.get("images", [])):
        suffix = "" if index == 0 else f"_{index}"
        paths.append(robust_download(image["url"], out_base.with_name(out_base.name + suffix).with_suffix(".png")))
    meta = dict(meta, outputs=[p.name for p in paths], seed=result.get("seed", meta.get("seed")),
                description=result.get("description"))
    out_base.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return paths


# ----------------------------------------------------------------------------- budget guard

def task_spent() -> float:
    with fal_api.SPEND_LOG.open(encoding="utf-8") as handle:
        return sum(float(r["usd"]) for r in csv.DictReader(handle)
                   if r["asset"].startswith(TASK_PREFIXES) and r["timestamp"] >= TASK_SINCE)


def task_guard(asset: str, usd: float, reserved: float = 0.0) -> None:
    spent = task_spent()
    if spent + reserved + usd > TASK_BUDGET + 1e-9:
        sys.exit(f"BUDGET: {asset}: {spent:.3f} (+{reserved:.3f} in flight) + {usd:.3f} USD would exceed "
                 f"the {TASK_BUDGET:.2f} USD task cap")
    print(f"[budget] {spent:.3f} spent of {TASK_BUDGET:.2f}; this call {usd:.3f}", file=sys.stderr)


# ----------------------------------------------------------------------------- paid: edits

def source_image(name: str) -> Path:
    """The image the coat edit starts from: the green pose base of a facing, or the aligned key pose on green."""
    if name in FACINGS:
        return ADAM / "prod" / f"pose_base_{name}.png"
    out = COAT / "prod" / f"src_{name}.png"
    if not out.exists():
        key = Image.open(ADAM / "masters" / f"{name}_aligned.png").convert("RGBA")
        canvas = Image.new("RGBA", key.size, hs.GREEN + (255,))
        canvas.alpha_composite(key)
        hs.save(canvas.convert("RGB"), out)
    return out


def edit_one(name: str, tag: str, seed: int) -> list[Path]:
    model = "fal-ai/nano-banana-2/edit"
    price = fal_api.IMAGE_PRICES[(model, "2K")]
    out_name = f"coat_{name}{tag}"
    asset = f"characters/{CHAR}/{out_name}"
    task_guard(asset, price)
    prompt = coat_prompt(name)
    src = source_image(name)
    arguments = {"prompt": prompt, "image_urls": [fal_api.image_data_uri(src, max_side=2048)], "aspect_ratio": "3:4",
                 "resolution": "2K", "output_format": "png", "num_images": 1, "seed": seed}
    result = fal_api.run(model, arguments, asset, price, budget=None, timeout_s=600)
    meta = {"model": model, "usd": price, "prompt": prompt, "aspect_ratio": "3:4", "resolution": "2K",
            "references": [str(src.relative_to(ART))], "seed": seed}
    return save_result(result, COAT / "prod" / out_name, meta)


def cmd_edit(args: argparse.Namespace) -> None:
    names = args.names
    for n in names:
        if n not in FACINGS and n not in POSE_NOTE:
            sys.exit(f"unknown edit {n}")
    price = fal_api.IMAGE_PRICES[("fal-ai/nano-banana-2/edit", "2K")]
    task_guard("batch", 0.0, reserved=price * len(names))
    with ThreadPoolExecutor(max_workers=min(4, len(names))) as pool:
        for paths in pool.map(lambda n: edit_one(n, args.tag, args.seed), names):
            print("\n".join(str(p) for p in paths))


# ----------------------------------------------------------------------------- free: masters

# Which coat edit file is the approved one per name (retakes get a tag).
EDIT_FILES = {n: f"coat_{n}.png" for n in (*FACINGS, *POSE_NOTE)}
EDIT_FILES_PATH = COAT / "edits.json"


def edit_file(name: str) -> Path:
    files = dict(EDIT_FILES)
    if EDIT_FILES_PATH.exists():
        files.update(json.loads(EDIT_FILES_PATH.read_text(encoding="utf-8")))
    return COAT / "prod" / files[name]


def load_edit_key(name: str, shape: tuple[int, int]) -> np.ndarray:
    rgb = fr.load_rgb(edit_file(name))
    if rgb.shape[:2] != shape:
        rgb = np.asarray(Image.fromarray(rgb).resize((shape[1], shape[0]), Image.Resampling.LANCZOS))
    return main_figure(fr.chroma_key(rgb))


def main_figure(key: np.ndarray) -> np.ndarray:
    """Drop stray painted parts outside the figure (the front edit painted a second, small head above him):
    keep the largest opaque component and the components whose box lies inside its box."""
    labels, sizes = fr.label_components(key[..., 3] > 24)
    if len(sizes) <= 1:
        return key
    main = int(np.argmax(sizes)) + 1
    ys, xs = np.nonzero(labels == main)
    box = (xs.min(), ys.min(), xs.max(), ys.max())
    keep = np.zeros(len(sizes) + 1, dtype=bool)
    keep[main] = True
    for index in range(1, len(sizes) + 1):
        if index == main:
            continue
        yy, xx = np.nonzero(labels == index)
        if len(xx) == 0:
            continue
        if xx.min() >= box[0] and xx.max() <= box[2] and yy.min() >= box[1] and yy.max() <= box[3]:
            keep[index] = True
    out = key.copy()
    # semi-transparent edge pixels below the component threshold follow the nearest kept component
    grown = np.asarray(Image.fromarray((keep[labels] * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
    out[..., 3] = np.where(grown, out[..., 3], 0)
    return out


def figure_rows(key: np.ndarray) -> tuple[int, int]:
    x0, y0, x1, y1 = fr.alpha_bbox(key)
    return y0, y1


def scarf_top(orig: np.ndarray, coat: np.ndarray, facing: str) -> float:
    """Highest figure-height fraction (below the eyes) where the coat edit's neck differs from the default figure:
    the top edge of the scarf / collar. Measured on a blurred difference so a one-pixel outline shift of the
    re-rendered face does not count."""
    y0, y1 = figure_rows(orig)
    h = y1 - y0
    c0, c1 = hs.head_columns(orig, pad=0.0)
    c0, c1 = int(c0), int(c1)
    a = Image.fromarray(np.ascontiguousarray(hs.premul(orig)[..., :3].clip(0, 255).astype(np.uint8)))
    b = Image.fromarray(np.ascontiguousarray(hs.premul(coat)[..., :3].clip(0, 255).astype(np.uint8)))
    a = np.asarray(a.filter(ImageFilter.GaussianBlur(4)), np.float32)
    b = np.asarray(b.filter(ImageFilter.GaussianBlur(4)), np.float32)
    diff = np.abs(a - b).mean(axis=2)
    for y in range(int(y0 + 0.10 * h), int(y0 + 0.30 * h)):
        row = diff[y, c0:c1]
        inside = orig[y, c0:c1, 3] > 128
        if inside.sum() and ((row > 40) & inside).sum() > 0.35 * inside.sum():
            return (y - y0) / h
    return 0.20


def hsv_of(rgba: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    hsv = np.asarray(Image.fromarray(np.ascontiguousarray(rgba[..., :3])).convert("HSV")).astype(np.float32)
    return hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255


def grow(mask: np.ndarray, px: int) -> np.ndarray:
    return np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * px + 1))) > 0


def fill_holes(mask: np.ndarray) -> np.ndarray:
    """mask plus every background component that does not touch the image border."""
    labels, sizes = fr.label_components(~mask)
    border = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    hole = np.ones(len(sizes) + 1, dtype=bool)
    hole[border] = False
    hole[0] = False
    return mask | hole[labels]


def shrink(mask: np.ndarray, px: int) -> np.ndarray:
    return np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(2 * px + 1))) > 0


def head_weight(orig: np.ndarray, coat: np.ndarray, top: float, soft: float = 0.010) -> np.ndarray:
    """1 where the default head is taken over, feathered: inside the head box down to below the chin, every pixel
    that the coat edit painted as face, ear or hair. Pixels the edit painted as scarf (mustard knit) or coat
    (charcoal wool), and pixels where the default shows its blue jacket collar, stay the edit's, so the scarf
    keeps its own painted contour in front of the default chin and neck."""
    y0, y1 = figure_rows(orig)
    h = y1 - y0
    ys = (np.arange(orig.shape[0], dtype=np.float32) - y0) / h
    bottom = 0.21
    wy = 1 - hs.smoothstep(bottom - soft, bottom + soft, ys)
    c0, c1 = hs.head_columns(orig, pad=0.03)
    xs = np.arange(orig.shape[1], dtype=np.float32)
    wx = hs.smoothstep(c0 - 10, c0 + 10, xs) * (1 - hs.smoothstep(c1 - 10, c1 + 10, xs))
    eh, es, ev = hsv_of(coat)
    oh, os_, ov = hsv_of(orig)
    scarf = (eh > 27) & (eh < 65) & (es > 0.33) & (ev > 0.14) & (coat[..., 3] > 60) & (ys[:, None] > 0.10)
    wool = (es < 0.16) & (ev > 0.12) & (ev < 0.62) & (coat[..., 3] > 60)
    jacket = (oh > 190) & (oh < 245) & (os_ > 0.22) & (orig[..., 3] > 60)
    # hair and the eyes' dark pupils are also low-saturation; above the mouth line nothing is wool
    wool &= (ys[:, None] > 0.125)
    # the painted outline of the face reads as olive after the despill: keep only solid scarf / wool areas
    scarf = grow(shrink(scarf, 2), 2)
    # the dark ribs between the knit rows fall outside the colour rule: close the scarf and fill its holes
    scarf = fill_holes(shrink(grow(scarf, 7), 7)) & (coat[..., 3] > 0)
    wool = grow(shrink(wool, 3), 3)
    # below the eyes, where the edit is opaque and the default is not (the scarf stands out behind the neck),
    # the default would punch a hole: keep the edit there too
    beyond = (coat[..., 3].astype(np.int16) > orig[..., 3].astype(np.int16) + 40) & (ys[:, None] > 0.12)
    keep_edit = grow(scarf, 5) | grow(wool, 3) | grow(jacket, 3) | grow(beyond, 2)
    m = Image.fromarray(((~keep_edit) * 255).astype(np.uint8), "L").filter(ImageFilter.MinFilter(3)).filter(
        ImageFilter.GaussianBlur(2.5))
    return wy[:, None] * wx[None, :] * (np.asarray(m, np.float32) / 255)


def wool_mask(key: np.ndarray) -> np.ndarray:
    """Soft mask of the charcoal coat: solid low-saturation areas (big components only, so jeans highlights and
    outline specks are left alone)."""
    _h, sat, val = hsv_of(key)
    wool = shrink((sat < 0.16) & (val > 0.12) & (val < 0.75) & (key[..., 3] > 200), 2)
    labels, sizes = fr.label_components(wool)
    keep = np.zeros(len(sizes) + 1, dtype=bool)
    keep[1:] = sizes >= 5000
    m = Image.fromarray((grow(keep[labels], 2) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(2))
    return np.asarray(m, np.float32) / 255 * (key[..., 3] > 0)


def match_coat_tone(key: np.ndarray, reference: np.ndarray) -> tuple[np.ndarray, list[float]]:
    """Per-channel gain on the coat so its mean colour matches the facing base (NB2 painted the reach_low coat
    ~24 % lighter, which would brighten the coat during the crouch)."""
    wk, wr = wool_mask(key), wool_mask(reference)
    mk = (key[..., :3].astype(np.float32) * wk[..., None]).sum((0, 1)) / wk.sum()
    mr = (reference[..., :3].astype(np.float32) * wr[..., None]).sum((0, 1)) / wr.sum()
    gain = mr / mk
    if np.all(np.abs(gain - 1) < 0.06):
        return key, [1.0, 1.0, 1.0]
    out = key.copy()
    rgb = key[..., :3].astype(np.float32)
    out[..., :3] = (rgb * (1 - wk[..., None]) + rgb * gain * wk[..., None]).clip(0, 255).astype(np.uint8)
    return out, [round(float(g), 3) for g in gain]


def rescale_about_feet(key: np.ndarray, target_height: float) -> tuple[np.ndarray, float]:
    """Scale an edit about its feet centre so its figure height matches the default (NB2 re-framed the front
    views ~6-9 % larger)."""
    x0, y0, x1, y1 = fr.alpha_bbox(key)
    scale = target_height / (y1 - y0)
    if abs(scale - 1) < 0.004:
        return key, 1.0
    fx = hs.feet_center_x(key)
    img = Image.fromarray(key, "RGBA")
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", (key.shape[1], key.shape[0]), (0, 0, 0, 0))
    out.alpha_composite(img, (round(fx - fx * scale), round(y1 - y1 * scale)))
    return np.asarray(out), scale


def stage_masters() -> None:
    report = {}
    for facing in FACINGS:
        orig_dir = ADAM / "masters" / f"face_{facing}"
        orig = {p.stem: hs.load_rgba(p) for p in orig_dir.glob("*.png")}
        base = orig["base"]
        edit = load_edit_key(facing, base.shape[:2])
        bx0, by0, bx1, by1 = fr.alpha_bbox(base)
        edit, scale = rescale_about_feet(edit, by1 - by0)
        dy, dx = hs.head_align(base, edit)
        edit = np.roll(edit, (dy, dx), axis=(0, 1))
        top = scarf_top(base, edit, facing)
        w = head_weight(base, edit, top)
        coat_base = hs.blend(edit, base, w)
        out_dir = COAT / "masters" / f"face_{facing}"
        out = {"base": coat_base}
        for n in ("blink", "talk_a", "talk_o", "talk_e"):
            if n in orig:
                out[n] = hs.blend(coat_base, orig[n], w)
        out["mask"] = coat_base                              # no face mask in 1982; hero_set expects the files
        if "blink" in out:
            out["mask_blink"] = out["blink"]
        out["mask_layer"] = np.zeros_like(coat_base)
        for n, img in out.items():
            hs.save(img, out_dir / f"{n}.png")
        bx = fr.alpha_bbox(base)
        ex = fr.alpha_bbox(coat_base)
        report[facing] = {"rescale": round(scale, 4), "head_shift": [int(dy), int(dx)], "scarf_top": round(top, 3), "bbox_default": bx,
                          "bbox_coat": ex, "feet_shift_after_head_align": list(hs.feet_shift(base, coat_base))}
        green = Image.new("RGBA", hs.CANVAS, hs.GREEN + (255,))
        green.alpha_composite(Image.fromarray(coat_base, "RGBA"))
        hs.save(green.convert("RGB"), COAT / "prod" / f"pose_base_{facing}.png")
        # walk video input: same placement rule as hero_set.stage_prep
        hs.save(hs.place(coat_base, hs.VIDEO, hs.VIDEO[1] * hs.WALK_FIG, hs.VIDEO[1] * hs.WALK_FEET, hs.VIDEO[0] / 2),
                COAT / "prod" / f"video_in_walk_{facing}.png")
    for pose, (facing, _src, _scale, align) in hs.KEY_POSES.items():
        if not edit_file(pose).exists():
            print(pose, "no edit yet")
            continue
        orig_pose = hs.load_rgba(ADAM / "masters" / f"{pose}_aligned.png")
        edit = load_edit_key(pose, orig_pose.shape[:2])
        scale = 1.0
        if pose != "reach_low":   # the crouch has no standing height; its bbox is compared below
            px0, py0, px1, py1 = fr.alpha_bbox(orig_pose)
            ex0, ey0, ex1, ey1 = fr.alpha_bbox(edit)
            # the head-to-feet span of a key pose: measured from the head top, hands above it (reach_high) aside
            edit, scale = rescale_about_feet(edit, (py1 - py0) * 1.0) if abs((ey1 - ey0) / (py1 - py0) - 1) > 0.02 else (edit, 1.0)
        # feet onto the feet of the COAT base of the facing (as hero_set aligns key poses to the pose base), so a
        # one-shot starts and ends on the same feet even where the coat base stands a few px off the default
        coat_base = hs.load_rgba(COAT / "masters" / f"face_{facing}" / "base.png")
        if align == "boots":
            bx, _bw, bb = hs.boots_box(coat_base)
            ex, _ew, eb = hs.boots_box(edit)
            dy, dx = round(bb - eb), round(bx - ex)
        else:
            _dy, dx = hs.feet_shift(coat_base, edit)
            dy = fr.alpha_bbox(coat_base)[3] - fr.alpha_bbox(edit)[3]   # soles on the same line
        edit = np.roll(edit, (dy, dx), axis=(0, 1))
        edit, gain = match_coat_tone(edit, coat_base)
        hs.save(edit, COAT / "masters" / f"{pose}_aligned.png")
        report[pose] = {"rescale": round(scale, 4), "coat_gain": gain, "feet_shift": [int(dy), int(dx)], "bbox_default": fr.alpha_bbox(orig_pose),
                        "bbox_coat": fr.alpha_bbox(edit)}
        # transition video canvases: same rule as hero_set.stage_canvases (start = coat base of the facing)
        base = hs.load_rgba(COAT / "masters" / f"face_{facing}" / "base.png")
        x0, y0, x1, y1 = fr.alpha_bbox(base)
        scale = hs.VIDEO[1] * hs.POSE_FIG / (y1 - y0)
        px = fr.torso_center_x(base)
        for tag, rgba in (("start", base), ("end", edit)):
            img = Image.fromarray(rgba, "RGBA").resize((round(rgba.shape[1] * scale), round(rgba.shape[0] * scale)),
                                                        Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", hs.VIDEO, hs.GREEN + (255,))
            canvas.alpha_composite(img, (round(hs.VIDEO[0] / 2 - px * scale), round(hs.VIDEO[1] * hs.POSE_FEET - y1 * scale)))
            hs.save(canvas.convert("RGB"), COAT / "prod" / f"video_in_{pose}_{tag}.png")
    (COAT / "masters" / "report.json").write_text(json.dumps(report, indent=2, default=int), encoding="utf-8")
    print(json.dumps(report, default=int))


# ----------------------------------------------------------------------------- paid: videos

WALKS = {"walk_right": ("side", "video_walk_right_pro.json"), "walk_toward": ("front", "video_walk_toward_pro.json"),
         "walk_away": ("back", "video_walk_away_pro.json")}
# approved clips and their cycle search windows (s): the first toward / away clips walked stop-and-go (both feet
# planted ~0.4 s at every step; leg-motion minima 1-3 against 11-19 for the jacket clips), the brisk retakes (_b)
# walk continuously: cycles of 33 and 24 video frames
WALK_VIDEOS = {"walk_right": "video_walk_right_pro.mp4", "walk_toward": "video_walk_toward_pro_b.mp4",
               "walk_away": "video_walk_away_pro_b.mp4"}
WALK_PERIODS = {"walk_right": (1.3, 1.8), "walk_toward": (1.2, 1.6), "walk_away": (0.8, 1.3)}
POSE_VIDEO_SIDECAR = {"reach_high": "video_reach_high_pro_b.json"}


def motion_prompt(name: str, brisk: bool = False) -> str:
    sidecar = WALKS[name][1] if name in WALKS else POSE_VIDEO_SIDECAR.get(name, f"video_{name}_pro.json")
    prompt = json.loads((ADAM / "prod" / sidecar).read_text(encoding="utf-8"))["prompt"]
    prompt = prompt.replace("his open blue jacket swinging a little, so the mustard-yellow T-shirt under it stays "
                            "visible the whole time", "the hem of his closed grey winter coat swinging a little, the "
                            "mustard-yellow scarf staying snug around his neck")
    prompt += " He wears the same closed grey winter coat and mustard-yellow scarf the whole time."
    if brisk:
        # the first coat clips toward / away walked stop-and-go (both feet planted for ~0.4 s at every step)
        prompt = prompt.replace("with a natural relaxed walking cycle:", "with a brisk, steady, continuous walking "
                                "rhythm at a normal city pace, like a man who is cold and wants to get somewhere: no "
                                "pause between the steps, one foot is always moving;")
    return prompt


def video_one(name: str, tag: str) -> list[Path]:
    endpoint = "fal-ai/minimax/hailuo-02/pro/image-to-video"
    price = fal_api.video_price(endpoint, 6.0, "1080P")
    if name in WALKS:
        start = COAT / "prod" / f"video_in_walk_{WALKS[name][0]}.png"
        end = start
        out_name = f"video_{name}_pro{tag}"
    else:
        start = COAT / "prod" / f"video_in_{name}_start.png"
        end = COAT / "prod" / f"video_in_{name}_end.png"
        out_name = f"video_{name}_pro{tag}"
    asset = f"characters/{CHAR}/{out_name}"
    task_guard(asset, price)
    prompt = motion_prompt(name, brisk=bool(tag))
    arguments = {"prompt": prompt, "image_url": fal_api.image_data_uri(start, fmt="PNG"), "prompt_optimizer": False,
                 "end_image_url": fal_api.image_data_uri(end, fmt="PNG")}
    result = fal_api.run(endpoint, arguments, asset, price, budget=None, timeout_s=1500, poll_s=8)
    meta = {"model": endpoint, "usd": round(price, 4), "prompt": prompt, "input": start.name,
            "tail_image": start == end, "end_image": end.name, "seconds": 6.0, "resolution": "1080P",
            "arguments": {k: v for k, v in arguments.items() if not str(v).startswith("data:")}}
    return save_result(result, COAT / "prod" / out_name, meta)


def cmd_video(args: argparse.Namespace) -> None:
    price = fal_api.video_price("fal-ai/minimax/hailuo-02/pro/image-to-video", 6.0, "1080P")
    task_guard("batch", 0.0, reserved=price * len(args.names))
    with ThreadPoolExecutor(max_workers=min(3, len(args.names))) as pool:
        for paths in pool.map(lambda n: video_one(n, args.tag), args.names):
            print("\n".join(str(p) for p in paths))


# ----------------------------------------------------------------------------- free: build, export, review

def stage_build(only: list[str] | None) -> None:
    jobs = only or ["idle", "talk", "walk", "oneshot"]
    if "idle" in jobs:
        for facing in FACINGS:
            hs.stage_idle(CHAR, facing, False)
    if "talk" in jobs:
        for facing in ("side", "front"):
            hs.stage_talk(CHAR, facing, False)
    if "walk" in jobs:
        for name, (facing, _sidecar) in WALKS.items():
            video = WALK_VIDEOS[name]
            if not (COAT / "prod" / video).exists():
                print(name, "no video yet")
                continue
            # the coat side clip walks slower than the jacket clip (one cycle = 37-38 video frames against 23), so
            # its search window is moved up; 20 cells per cycle; export retimes it to the jacket's ground speed
            hs.stage_walk(CHAR, name, video, 20, WALK_PERIODS[name], name != "walk_right")
            hs.review_strip(COAT / "anim" / name, name)
    if "oneshot" in jobs:
        for pose in hs.KEY_POSES:
            if not (COAT / "prod" / f"video_{pose}_pro.mp4").exists():
                print(pose, "no video yet")
                continue
            hs.stage_oneshot(CHAR, pose)


def _default_meta(name: str) -> dict:
    return json.loads((ADAM / "anim" / name / f"{name}_sheet.json").read_text(encoding="utf-8"))


def _retime_side(meta: dict) -> tuple[float, float, float]:
    """Play the coat side walk faster until its measured stride equals the jacket walk's (272 px/s), so Adam walks at
    the same ground speed in every era without foot sliding (the coat clip walks slower: 235 px/s)."""
    target = _default_meta("walk_right")["stride_px_per_s"]
    k = target / meta["stride_px_per_s"]
    return round(meta["playback_fps"] * k, 2), round(meta["cycle_seconds"] / k, 3), round(target, 1)


def _retime_to_side_cadence(meta: dict) -> tuple[float, float, None]:
    """Depth walks move at a fixed share of the side stride; give them the side walk's cadence."""
    side = json.loads((COAT / "anim" / "walk_right" / "walk_right_sheet.json").read_text(encoding="utf-8"))
    cycle = _retime_side(side)[1]
    return round(meta["frames"] / cycle, 2), cycle, None


RETIME = {"walk_right": _retime_side, "walk_away": _retime_to_side_cadence}


def stage_export() -> None:
    manifest_path = GAME_DIR / "animations.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for base_name, facing, mirror in hs.ANIMATIONS:
        src = COAT / "anim" / base_name
        if not (src / f"{base_name}_sheet.json").exists():
            print(base_name, "MISSING (not exported)")
            continue
        name = f"{base_name}_{VARIANT}"
        meta = json.loads((src / f"{base_name}_sheet.json").read_text(encoding="utf-8"))
        img = Image.open(src / f"{base_name}_sheet.png").convert("RGBA")
        img.save(GAME_DIR / f"{name}.webp", "WEBP", lossless=True, quality=100, method=6, exact=False)
        ship = {k: meta[k] for k in ("frames", "cell", "pivot", "playback_fps", "oneshot", "stride_px_per_s") if k in meta}
        ship = {"name": name, **ship}
        if base_name in RETIME:
            ship["playback_fps"], ship["cycle_seconds"], stride = RETIME[base_name](meta)
            if stride is not None:
                ship["stride_px_per_s"] = stride
            meta = dict(meta, cycle_seconds=ship["cycle_seconds"])
        ship.update(image=f"{name}.webp", facing=facing, mirror_for_left=mirror, variant=VARIANT,
                    standing_height_px=hs.HEIGHT)
        for k in ("mouth_sequence", "blink_frames", "cycle_seconds", "note"):
            if k in meta:
                ship[k] = meta[k]
        if base_name in hs.ITEM_ANCHORS:
            # same palm position relative to the feet (measured: +1 px), so shift by the pivot difference
            dflt = json.loads((GAME_DIR / f"{base_name}.json").read_text(encoding="utf-8"))
            ax, ay = hs.ITEM_ANCHORS[base_name]
            ship["item_anchor_last_frame"] = [ax + ship["pivot"][0] - dflt["pivot"][0], ay + ship["pivot"][1] - dflt["pivot"][1]]
        if base_name in ("walk_toward", "walk_away"):
            ship["stride_px_per_s"] = None
            ship["note"] = ("depth walk: move the actor along y at a per-room speed tuned by eye (start with ~0.25 x "
                            "the walk_right stride, scaled by the actor scale); feet may reach below the pivot")
        (GAME_DIR / f"{name}.json").write_text(json.dumps(ship, indent=2), encoding="utf-8")
        manifest["animations"][name] = {k: ship[k] for k in ("image", "facing", "frames", "cell", "pivot",
                                                             "playback_fps", "oneshot", "mirror_for_left", "variant",
                                                             "stride_px_per_s")}
        print(f"{name:34s} {img.size[0]:5d}x{img.size[1]:<4d} {(GAME_DIR / (name + '.webp')).stat().st_size // 1024:5d} KB")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def stage_review() -> None:
    """One sheet per animation pair: default (top) and coat (bottom) cells on a 1982 background, plus an overview."""
    REVIEW.mkdir(parents=True, exist_ok=True)
    bg = Image.open(REPO / "src" / "game" / "assets" / "bg_natural" / "S57.webp").convert("RGB")
    rows = []
    for base_name, _facing, _mirror in hs.ANIMATIONS:
        pair = []
        for d in (ADAM / "anim" / base_name, COAT / "anim" / base_name):
            sheet = d / f"{base_name}_sheet.png"
            if not sheet.exists():
                pair = []
                break
            meta = json.loads((d / f"{base_name}_sheet.json").read_text(encoding="utf-8"))
            pair.append((Image.open(sheet).convert("RGBA"), meta))
        if not pair:
            continue
        cw = max(m["cell"][0] for _s, m in pair)
        ch = max(m["cell"][1] for _s, m in pair)
        n = max(m["frames"] for _s, m in pair)
        step = max(1, n // 8)
        idx = list(range(0, n, step))[:8] + ([n - 1] if (n - 1) % step else [])
        strip = Image.new("RGB", (cw * len(idx), ch * 2), (0, 0, 0))
        crop = bg.crop((800, 380, 800 + strip.width // 2, 380 + strip.height // 2)).resize(strip.size)
        strip.paste(crop)
        strip = strip.convert("RGBA")
        for r, (sheet, meta) in enumerate(pair):
            w, h = meta["cell"]
            for i, f in enumerate(idx):
                if f >= meta["frames"]:
                    continue
                cell = sheet.crop((f * w, 0, (f + 1) * w, h))
                strip.alpha_composite(cell, (i * cw + (cw - w) // 2, r * ch + (ch - h)))
        strip = strip.convert("RGB")
        strip.save(REVIEW / f"coat_{base_name}.jpg", quality=88)
        rows.append(strip)
    if rows:
        width = max(r.width for r in rows)
        scale = 0.5
        over = Image.new("RGB", (int(width * scale), int(sum(r.height for r in rows) * scale)), (30, 30, 30))
        y = 0
        for r in rows:
            rr = r.resize((int(r.width * scale), int(r.height * scale)), Image.Resampling.LANCZOS)
            over.paste(rr, (0, y))
            y += rr.height
        over.save(REVIEW / "coat_overview.jpg", quality=85)
        print(REVIEW / "coat_overview.jpg")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("edit")
    p.add_argument("names", nargs="+")
    p.add_argument("--tag", default="")
    p.add_argument("--seed", type=int, default=1985)
    sub.add_parser("masters")
    p = sub.add_parser("video")
    p.add_argument("names", nargs="+")
    p.add_argument("--tag", default="")
    p = sub.add_parser("build")
    p.add_argument("--only", nargs="*")
    sub.add_parser("export")
    sub.add_parser("review")
    sub.add_parser("spent")
    args = parser.parse_args()
    if args.cmd == "edit":
        cmd_edit(args)
    elif args.cmd == "masters":
        stage_masters()
    elif args.cmd == "video":
        cmd_video(args)
    elif args.cmd == "build":
        stage_build(args.only)
    elif args.cmd == "export":
        stage_export()
    elif args.cmd == "review":
        stage_review()
    elif args.cmd == "spent":
        print(f"{task_spent():.3f} of {TASK_BUDGET:.2f}")


if __name__ == "__main__":
    main()
