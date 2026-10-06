"""Winter versions of the Jasna 2035 paintings and cutscene frames (owner decision 2026-10-06: "Jasna 2035 is in
winter"; docs/DECISIONS.md). The same idea as derive_era.py, for a SEASON change of the same room: one Nano Banana
Pro edit (USD 0.15) of the accepted summer painting keeps the camera, the architecture, every prop and every
blocking rect, and only adds winter. derive_era.py refuses base == target (outside --test), so this tool wraps its
camera measurement and review for the same-room case.

Inputs per target (English):
  rooms   art/prompts/natural/<ROOM>.winter.txt   prompt body ({rect:ID} {exit:ID} {walk} {npc_zones} expand from
                                                  the room's natural blocking, as in derive_era.py)
          art/prompts/natural/<ROOM>.winter.json  {"mode": "full" | "regions", "edit_regions": [[x, y, w, h], ...],
                                                  "protect": [[x, y, w, h], ...], "feather": 12, "place": "..."}
  frames  art/prompts/winter/<SHOT>.txt / .json   same keys; "refs": extra reference images (repo paths, optional
                                                  "#<frame index>" to cut one cell of a sprite sheet)
"full": the model output is used everywhere except the `protect` boxes (base pixels pasted back, feathered).
"regions": the model output is used only inside `edit_regions` (windows, added winter details); everything else stays
pixel-identical to the summer painting, so state patches, occluders and lettering stay valid.

The summer painting is kept ONLY in art/: the first run copies the shipped export to
art/masters/bg_natural/<ROOM>_summer.webp (frames: art/cutscenes/<SHOT>_summer.webp) and always edits that copy.

Usage (repo root; PYTHONIOENCODING=utf-8 python -X utf8 art/tools/winter_jasna.py ...):
  prompt  S42                      assembled prompt + guide image (free)
  run     S42 --budget 0.30        ONE paid edit -> raw, composite master (1920x1080), reviews, export
  compose S42 --version 2          free re-composite of an existing raw with the current .winter.json
  patches S43                      re-fit the room's state patches / variant patches onto the winter painting
  screens S42 [--replay N] [--tag T] [--act ID]   in-engine screenshots via tools/qa_godot.py (hidden window)
                                   -> build/screens/jasna_winter/<ROOM>/
Spend scopes: bg_natural/winter/<ROOM>/ and cutscenes/winter/<SHOT>/ (art/spend-log.csv).
"""
from __future__ import annotations

import argparse
import datetime
import json
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive_era  # noqa: E402  (installs the natural geometry into paint_room / review_room)
import fal_api  # noqa: E402
import paint_natural  # noqa: E402
import paint_room  # noqa: E402
import review_room  # noqa: E402

ROOT = paint_room.ROOT
ART = ROOT / "art"
GAME_DIR = ROOT / "src" / "game"
ROOMS = ["S42", "S43", "S44", "S45", "S46", "S47", "S48", "S49", "S50", "S67", "S68"]
FRAME_DIR = ART / "cutscenes"
FRAME_EXPORT = GAME_DIR / "assets" / "cutscenes"
FRAME_PROMPTS = ART / "prompts" / "winter"
ROOM_MASTERS = ART / "masters" / "bg_natural"
ROOM_EXPORT = GAME_DIR / "assets" / "bg_natural"
REVIEW = ART / "review" / "natural" / "winter"
SCREENS = ROOT / "build" / "screens" / "jasna_winter"
DATE_TEXT = "6 February 2035"

LIGHT = ("Lighting: a clear, cold, sunny winter day in the Low Tatras mountains: deep clean blue sky, low winter sun, "
         "crisp blue-violet shadows on the snow, sparkle on fresh snow, cold bright air. The brushwork, line quality "
         "and palette harmony stay exactly those of image 1 (style A).")


def is_room(target: str) -> bool:
    return bool(re.fullmatch(r"S\d\d", target))


# --------------------------------------------------------------------------- files

def summer_copy(target: str) -> Path:
    return (ROOM_MASTERS / f"{target}_summer.webp") if is_room(target) else (FRAME_DIR / f"{target}_summer.webp")


def export_path(target: str) -> Path:
    return (ROOM_EXPORT / f"{target}.webp") if is_room(target) else (FRAME_EXPORT / f"{target}.webp")


def masters_dir(target: str) -> Path:
    return ROOM_MASTERS if is_room(target) else FRAME_DIR


VARIANT = "winter"      # --variant: "winter" (summer -> winter) or e.g. "winterfix" (a local fix of a winter master)


def prompt_paths(target: str) -> tuple[Path, Path]:
    if is_room(target):
        stem = paint_room.PROMPTS / f"{target}.{VARIANT}"
    else:
        stem = FRAME_PROMPTS / (target if VARIANT == "winter" else f"{target}.{VARIANT}")
    return Path(str(stem) + ".txt"), Path(str(stem) + ".json")


def ensure_summer(target: str) -> Path:
    """Copy the shipped (summer) export into art/ once; the summer painting is never shipped next to the winter one."""
    keep = summer_copy(target)
    if not keep.exists():
        src = export_path(target)
        if not src.exists():
            sys.exit(f"missing {src.relative_to(ROOT)}")
        keep.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, keep)
        print(f"kept the summer painting: {keep.relative_to(ROOT)}")
    return keep


def base_frame(target: str) -> Image.Image:
    img = Image.open(ensure_summer(target)).convert("RGB")
    if img.size != paint_room.FRAME:
        img = paint_room.fit_to_frame(img)
    return img


def read_config(target: str) -> dict:
    _, cfg = prompt_paths(target)
    if not cfg.exists():
        return {"mode": "full", "protect": [], "edit_regions": [], "feather": 12}
    data = json.loads(cfg.read_text(encoding="utf-8"))
    data.setdefault("mode", "full")
    data.setdefault("feather", 12)
    return data


def read_body(target: str) -> str:
    txt, _ = prompt_paths(target)
    if not txt.exists():
        sys.exit(f"write {txt.relative_to(ROOT)} first")
    text = txt.read_text(encoding="utf-8")
    if "TODO" in text:
        sys.exit(f"{txt.relative_to(ROOT)} still contains TODO")
    return "\n".join(line for line in text.splitlines() if not line.startswith("#")).strip()


def next_version(target: str) -> int:
    folder = masters_dir(target)
    versions = [int(m.group(1)) for p in folder.glob(f"{target}_v*.png")
                if (m := re.fullmatch(rf"{re.escape(target)}_v(\d+)\.png", p.name))]
    return max(versions, default=0) + 1


def ref_image(spec: str) -> Image.Image:
    path, _, cell = spec.partition("#")
    img = Image.open(ROOT / path).convert("RGBA")
    meta = (ROOT / path).with_suffix(".json")
    if cell and meta.exists():
        w, h = json.loads(meta.read_text(encoding="utf-8"))["cell"]
        i = int(cell)
        img = img.crop((i * w, 0, (i + 1) * w, h))
    card = Image.new("RGBA", img.size, (128, 128, 128, 255))
    card.alpha_composite(img)
    return card.convert("RGB")


# --------------------------------------------------------------------------- prompt

def assemble(target: str) -> dict:
    cfg = read_config(target)
    body = read_body(target)
    fix = VARIANT != "winter"
    if fix:
        src = masters_dir(target) / f"{target}_v{cfg['base_version']}.png"
        base = Image.open(src).convert("RGB")
        base_name = f"{src.relative_to(ROOT).as_posix()} (winter master)"
    else:
        base = base_frame(target)
        base_name = f"{summer_copy(target).relative_to(ROOT).as_posix()} (summer, model geometry)"
    model_base = paint_room.to_model_geometry(base)
    images = [("base", model_base, base_name)]
    if is_room(target) and fix:
        room, anchors = paint_natural.natural_room(target)
        body = derive_era.expand_era(body, room, anchors)
        guide = derive_era.guide_image(model_base, room)
        images.append(("guide", guide, f"{target} winter master + natural blocking boxes (guide)"))
        preamble = (
            f"You receive 2 images. Image 1 is a finished winter background painting of our point-and-click adventure "
            f"game: {cfg.get('place') or room['name']} on {DATE_TEXT}. Image 2 is the same painting with coloured "
            f"boxes that only mark the interactive objects, the exits and the walkable floor. Make ONLY the change "
            f"described below and keep everything else in image 1 exactly as it is: the same camera, framing, "
            f"buildings, trees, snow, light, colours, brushwork and level of detail.")
        warning = (
            "Image 2 is a positioning aid only: do NOT draw any of its boxes, outlines, labels or captions. The result "
            "is image 1 edited, in the same 16:9 framing: no frames, no borders, no UI, no captions, no watermark, no "
            "new text, no people or animals.")
        parts = [preamble, body, warning, paint_room.style_sentence()]
        room_info = {"room": room, "anchors": anchors}
    elif is_room(target):
        room, anchors = paint_natural.natural_room(target)
        place = cfg.get("place") or room["name"]
        body = derive_era.expand_era(body, room, anchors)
        guide = derive_era.guide_image(model_base, room)
        images.append(("guide", guide, f"{target} summer painting + natural blocking boxes (guide)"))
        preamble = (
            f"You receive 2 images. Image 1 is a finished background painting of our point-and-click adventure game: "
            f"{place}, painted in summer 2035. Image 2 is the same painting with coloured boxes that only mark the "
            f"interactive objects, the exits and the walkable floor, which must all stay exactly where they are. Edit "
            f"image 1 into the SAME PLACE on {DATE_TEXT}, a clear cold day in deep winter, seen by the SAME CAMERA: "
            f"keep the exact viewpoint, lens, horizon, perspective and framing, and keep the position, size and outline "
            f"of every building, wall, door, window, pole, rail, sign, piece of furniture, object and tree trunk. "
            f"Change only what winter changes, as described below. Keep the painting technique, brushwork, palette "
            f"handling and level of detail of image 1.")
        warning = (
            "Image 2 is a positioning aid only: do NOT draw any of its boxes, outlines, labels or captions. The result "
            "is image 1 edited, in the same 16:9 framing: no frames, no borders, no UI, no captions, no watermark, no "
            "text except the lettering already in image 1, and no people or animals unless stated above.")
        parts = [preamble, body, warning, LIGHT, paint_room.style_sentence()]
        room_info = {"room": room, "anchors": anchors}
    else:
        refs = cfg.get("refs") or []
        for i, spec in enumerate(refs, 2):
            images.append(("ref", ref_image(spec), spec))
        ref_text = " ".join(f"Image {i} is {desc}." for i, desc in enumerate(cfg.get("ref_roles") or [], 2))
        preamble = (
            f"You receive {len(images)} image{'s' if len(images) > 1 else ''}. Image 1 is a finished cutscene frame of "
            f"our point-and-click adventure game: {cfg.get('place', 'a scene at Jasna in 2035')}, painted in summer. "
            f"{ref_text} Edit image 1 into the SAME SCENE on {DATE_TEXT}, a clear cold day in deep winter: keep the "
            f"exact framing, camera, composition, every person (face, hair, pose, hands, expression), every object and "
            f"every piece of lettering exactly as in image 1, unless the text below says otherwise. Change only what "
            f"winter changes, as described below. Keep the painting technique, brushwork, palette handling and level "
            f"of detail of image 1.")
        warning = ("The result is image 1 edited, in the same 16:9 framing: no frames, no borders, no letterbox bars, "
                   "no captions, no watermark, no new text.")
        parts = [preamble, body, warning, LIGHT, paint_room.style_sentence()]
        room_info = {}
    return {"prompt": "\n\n".join(parts), "images": images, "base": base, "model_base": model_base, "cfg": cfg,
            **room_info}


def cmd_prompt(args) -> None:
    job = assemble(args.target)
    print(job["prompt"])
    print(f"\n{len(job['prompt'])} characters; images:")
    for i, (_, _, name) in enumerate(job["images"], 1):
        print(f"  {i}: {name}")
    REVIEW.mkdir(parents=True, exist_ok=True)
    if len(job["images"]) > 1:
        out = REVIEW / f"{args.target}_guide.jpg"
        paint_room.fit_to_frame(job["images"][1][1]).convert("RGB").save(out, quality=88)
        print(f"guide: {out.relative_to(ROOT)}")


# --------------------------------------------------------------------------- composite

def rect_mask(size: tuple[int, int], rects: list, feather: int, invert: bool = False) -> Image.Image:
    """White inside the rects (black with invert), feathered; sides that touch the frame edge are not feathered."""
    w, h = size
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    pad = 3 * feather + 4
    for r in rects:
        if len(r) == 4 and not isinstance(r[0], list):
            x, y, rw, rh = r
            x0, y0, x1, y1 = x, y, x + rw, y + rh
            x0 = -pad if x0 <= 2 else x0
            y0 = -pad if y0 <= 2 else y0
            x1 = w + pad if x1 >= w - 2 else x1
            y1 = h + pad if y1 >= h - 2 else y1
            d.rectangle([x0, y0, x1, y1], fill=255)
        else:   # polygon [[x, y], ...]
            d.polygon([tuple(p) for p in r], fill=255)
    if feather:
        mask = mask.filter(ImageFilter.GaussianBlur(feather / 2))
    return ImageChops.invert(mask) if invert else mask


def composite(base: Image.Image, winter: Image.Image, cfg: dict) -> tuple[Image.Image, Image.Image]:
    """(result, mask) in game frame space; mask = where the model output is used."""
    feather = int(cfg.get("feather", 12))
    if cfg["mode"] == "regions":
        mask = rect_mask(base.size, cfg.get("edit_regions") or [], feather)
    else:
        mask = rect_mask(base.size, cfg.get("protect") or [], feather, invert=True)
    if cfg.get("snow_regions"):
        # only the snow the model added (much brighter than the base, low saturation), e.g. snow tracked onto a floor
        b = np.asarray(base, dtype=np.float32)
        w = np.asarray(winter, dtype=np.float32)
        luma = lambda a: 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]  # noqa: E731
        sat = (w.max(-1) - w.min(-1)) / np.maximum(w.max(-1), 1)
        snow = np.clip((luma(w) - luma(b) - 28) / 30, 0, 1) * np.clip((0.28 - sat) / 0.12, 0, 1)
        area = np.asarray(rect_mask(base.size, cfg["snow_regions"], 24), dtype=np.float32) / 255
        snow_img = Image.fromarray((snow * area * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(3))             .filter(ImageFilter.GaussianBlur(1.2))
        mask = ImageChops.lighter(mask, snow_img)
    if cfg.get("diff_regions"):
        # windows with people / objects in front of them: take the model output only where it really changed the
        # picture (the view behind), keep the base where the model left it alone (unchanged areas differ by < ~14)
        b = np.asarray(base.filter(ImageFilter.GaussianBlur(2)), dtype=np.float32)
        w = np.asarray(winter.filter(ImageFilter.GaussianBlur(2)), dtype=np.float32)
        lo, hi = cfg.get("diff_ramp", [18, 40])
        changed = np.clip((np.abs(w - b).max(-1) - lo) / (hi - lo), 0, 1)
        area = np.asarray(rect_mask(base.size, cfg["diff_regions"], feather), dtype=np.float32) / 255
        diff_img = Image.fromarray((changed * area * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(5))             .filter(ImageFilter.GaussianBlur(2.5))
        mask = ImageChops.lighter(mask, diff_img)
    return Image.composite(winter, base, mask), mask


def measure_frames(winter: Image.Image, base: Image.Image, job: dict) -> dict:
    """Camera check: derive_era.measure for rooms (exits, anchors); global shift + NCC of edges for frames."""
    w_model, b_model = paint_room.to_model_geometry(winter), paint_room.to_model_geometry(base)
    if "room" in job:
        return derive_era.measure(w_model, b_model, job["room"], job["anchors"])
    small = (paint_room.MODEL_FRAME[0] // 4, paint_room.MODEL_FRAME[1] // 4)
    gx, gy = derive_era.phase_shift(derive_era.gray(w_model, small), derive_era.gray(b_model, small))
    return {"global_shift_master_px": [gx * 4, gy * 4], "points": {}, "camera_ok": max(abs(gx), abs(gy)) <= 2}


def build(target: str, version: int, raw_path: Path, job: dict, meta: dict) -> Path:
    """raw model output -> drift compensation -> composite -> master vN (1920x1080 PNG) -> reviews -> export."""
    raw = derive_era.as_model(Image.open(raw_path))
    report = derive_era.measure(raw, job["model_base"], job["room"], job["anchors"]) if "room" in job else \
        measure_frames(paint_room.fit_to_frame(raw), job["base"], job)
    gx, gy = report["global_shift_master_px"]
    if (gx or gy) and max(abs(gx), abs(gy)) <= derive_era.GLOBAL_COMPENSATE:
        raw = ImageChops.offset(raw, -gx, -gy)
        print(f"model output drifted by {gx:+d},{gy:+d} master px; compensated")
        meta["compensated_master_px"] = [gx, gy]
    winter = paint_room.fit_to_frame(raw).convert("RGB")
    result, mask = composite(job["base"], winter, job["cfg"])
    report = measure_frames(result, job["base"], job)
    folder = masters_dir(target)
    out = folder / f"{target}_v{version}.png"
    result.save(out)
    meta.update({"camera": report, "compose": job["cfg"], "output_size": list(result.size),
                 "composed": datetime.datetime.now().isoformat(timespec="seconds")})
    REVIEW.mkdir(parents=True, exist_ok=True)
    # side by side + mask
    sheet = Image.new("RGB", (1920, 1080 + 540), (20, 20, 20))
    sheet.paste(job["base"].resize((960, 540), Image.Resampling.LANCZOS), (0, 0))
    sheet.paste(result.resize((960, 540), Image.Resampling.LANCZOS), (960, 0))
    tint = Image.new("RGB", result.size, (255, 0, 160))
    shown = Image.composite(Image.blend(result, tint, 0.0), Image.blend(result, tint, 0.35),
                            mask.point(lambda v: 255 if v > 8 else 0))
    sheet.paste(shown, (0, 540))
    d = ImageDraw.Draw(sheet)
    review_room.label(d, (12, 12), f"{target} summer (shipped base)", (255, 255, 255), 20)
    review_room.label(d, (972, 12), f"{target} winter v{version}", (255, 255, 255), 20)
    review_room.label(d, (12, 552), "winter master; magenta tint = kept from the summer painting", (255, 255, 255),
                      20)
    side = REVIEW / f"{target}_v{version}_winter.jpg"
    sheet.save(side, quality=88)
    meta["review"] = side.relative_to(ROOT).as_posix()
    if "room" in job:
        derive = derive_era.derive_review(paint_room.to_model_geometry(result), job["model_base"], job["room"],
                                          job["anchors"], report, REVIEW / f"{target}_v{version}_derive.png")
        paint_natural.natural_review(target, version)
        meta["derive_review"] = derive.relative_to(ROOT).as_posix()
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    dest = export_path(target)
    result.save(dest, "WEBP", quality=90, method=6)
    print(f"{out.relative_to(ROOT)} -> {dest.relative_to(ROOT)} ({dest.stat().st_size // 1024} KiB); camera "
          f"{'KEPT' if report['camera_ok'] else 'DRIFTED'}")
    derive_era.print_report(report)
    print(f"LOOK at {side.relative_to(ROOT)}")
    return out


def cmd_run(args) -> None:
    target = args.target
    job = assemble(target)
    scope = f"{'bg_natural' if is_room(target) else 'cutscenes'}/winter/{target}/"
    version = next_version(target)
    seed = args.seed if args.seed is not None else random.randint(1, 2 ** 31 - 1)
    urls = []
    for kind, img, _ in job["images"]:
        if kind == "base":
            urls.append(fal_api.image_data_uri(img, fmt="PNG"))
        else:
            urls.append(fal_api.image_data_uri(img, max_side=2048, fmt="JPEG"))
    arguments = {"prompt": job["prompt"], "image_urls": urls, "aspect_ratio": paint_room.ASPECT,
                 "resolution": paint_room.RESOLUTION, "output_format": "png", "num_images": 1, "seed": seed}
    price = fal_api.IMAGE_PRICES[(paint_room.MODEL, paint_room.RESOLUTION)]
    asset = f"{scope}{target}_v{version}_{VARIANT}"
    started = datetime.datetime.now().isoformat(timespec="seconds")
    print(f"{target}: winter edit, scope {scope}, budget USD {args.budget:.2f}")
    result = fal_api.run(paint_room.MODEL, arguments, asset, price, budget=(scope, args.budget), timeout_s=900)
    raw = masters_dir(target) / f"_{target}_v{version}_{VARIANT}_raw.png"
    fal_api.download(result["images"][0]["url"], raw)
    txt, cfg = prompt_paths(target)
    meta = {"target": target, "version": version, "kind": "winter" if VARIANT == "winter" else f"winter {VARIANT}", "model": paint_room.MODEL,
            "resolution": paint_room.RESOLUTION, "aspect_ratio": paint_room.ASPECT, "seed": result.get("seed", seed),
            "usd": price, "scope": scope, "spend_log_asset": asset, "started": started,
            "base": job["images"][0][2],
            "prompt_file": txt.relative_to(ROOT).as_posix(), "config_file": cfg.relative_to(ROOT).as_posix(),
            "prompt": job["prompt"], "image_urls": [name for _, _, name in job["images"]],
            "model_description": result.get("description"), "raw_model_output": raw.relative_to(ROOT).as_posix()}
    if is_room(target):
        meta["blocking"] = paint_natural.blocking_of(target)
    build(target, version, raw, job, meta)
    print(f"scope {scope} spent {fal_api.logged_spend(scope):.2f} of {args.budget:.2f}; total winter "
          f"{fal_api.logged_spend('bg_natural/winter/') + fal_api.logged_spend('cutscenes/winter/'):.2f}")


def cmd_compose(args) -> None:
    target = args.target
    folder = masters_dir(target)
    side = folder / f"{target}_v{args.version}.json"
    meta = json.loads(side.read_text(encoding="utf-8")) if side.exists() else {"target": target}
    raw = ROOT / (args.raw or meta.get("raw_model_output") or "")
    if not raw.exists():
        sys.exit(f"missing raw output {raw}")
    job = assemble(target)
    meta["recomposed"] = True
    build(target, args.version, raw, job, meta)


# --------------------------------------------------------------------------- state patches

def refit_patch(texture: Path, pos: tuple[int, int], summer: Image.Image, winter: Image.Image) -> dict:
    """Keep the patch's own change (where it differs from the summer painting), take everything else from the
    winter painting, so the patch sits seamlessly on the winter background. Returns stats."""
    art_keep = ART / "masters" / "bg_natural" / "patches_summer" / texture.name
    art_keep.parent.mkdir(parents=True, exist_ok=True)
    if not art_keep.exists():
        shutil.copy2(texture, art_keep)
    patch = Image.open(art_keep).convert("RGBA")
    x, y = pos
    box = (x, y, x + patch.width, y + patch.height)
    s = np.asarray(summer.crop(box), dtype=np.float32)
    w = np.asarray(winter.crop(box), dtype=np.float32)
    p = np.asarray(patch, dtype=np.float32)
    bg_changed = float(np.abs(s - w).max())
    diff = np.abs(p[..., :3] - s).max(-1)
    m = np.clip((diff - 10) / 25, 0, 1)
    m_img = Image.fromarray((m * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(5)) \
        .filter(ImageFilter.GaussianBlur(2))
    m = np.asarray(m_img, dtype=np.float32)[..., None] / 255
    rgb = p[..., :3] * m + w * (1 - m)
    out = np.dstack([rgb, p[..., 3]]).clip(0, 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(texture, "WEBP", quality=95, alpha_quality=100, method=6)
    return {"texture": texture.relative_to(ROOT).as_posix(), "summer_copy": art_keep.relative_to(ROOT).as_posix(),
            "background_max_change": round(bg_changed, 1)}


def cmd_patches(args) -> None:
    rid = args.target
    blocking = paint_natural.blocking_of(rid)
    summer = base_frame(rid)
    winter = Image.open(export_path(rid)).convert("RGB")
    items = [(p["texture"], p["pos"]) for p in blocking.get("state_patches") or []]
    for v in (blocking.get("variant_layers") or {}).values():
        if isinstance(v, dict):
            items.append((v["texture"], v["pos"]))
    if not items:
        print(f"{rid}: no state patches / variant patches")
        return
    preview = winter.convert("RGBA")
    for tex, pos in items:
        path = GAME_DIR / "assets" / tex
        stats = refit_patch(path, tuple(pos), summer, winter)
        preview.alpha_composite(Image.open(path).convert("RGBA"), tuple(pos))
        print(f"{rid}: {stats}")
    REVIEW.mkdir(parents=True, exist_ok=True)
    out = REVIEW / f"{rid}_patches_winter.jpg"
    preview.convert("RGB").save(out, quality=90)
    print(f"preview (winter painting with every patch applied): {out.relative_to(ROOT)}")


# --------------------------------------------------------------------------- screenshots

def qa(args: list[str], timeout: int = 400) -> int:
    cmd = [sys.executable, str(ROOT / "tools" / "qa_godot.py"), "--qa-timeout", str(timeout), "--path",
           str(GAME_DIR)] + args
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in proc.stdout.splitlines():
        if line.startswith("HARNESS ERROR") or "WARNING: Room" in line or "SCRIPT ERROR" in line:
            print("  " + line)
    return proc.returncode


def cmd_import(args) -> None:
    with paint_natural.ImportLock():
        code = qa(["--headless", "--import"], timeout=1500)
    print(f"import exit {code}")


def cmd_screens(args) -> None:
    rid = args.target
    out = SCREENS / rid
    out.mkdir(parents=True, exist_ok=True)
    state = []
    if args.replay:
        state += ["--replay", str(args.replay)]
    for act in args.act or []:
        state += ["--act", act]
    tag = args.tag or ("state" if state else "entry")
    base = ["--resolution", "1920x1080", "--", "--blocking", "natural"] + state + ["--room", rid, "--fast-text",
                                                                                 "--skip-lines"]
    shots = [base + ["--labels", "--wait", "900", "--screenshot", str(out / f"{tag}_labels.png")],
             base + ["--wait", "900", "--screenshot", str(out / f"{tag}_clean.png")]]
    if not args.no_motion:
        shots.append(base + ["--wait", "1500", "--frames", "4", "--interval", "700",
                             "--screenshot", str(out / f"{tag}_motion.png")])
    codes = [qa(s) for s in shots]
    print(f"{rid}: screens -> {out.relative_to(ROOT)} (exit codes {codes})")


# --------------------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("prompt", "run", "compose", "patches", "screens", "import"):
        p = sub.add_parser(name)
        if name != "import":
            p.add_argument("target", help="room (S42) or cutscene frame (CS09_1, EPILOGUE_9)")
            p.add_argument("--variant", default="winter", help="prompt/config variant (default winter; e.g. winterfix "
                                                               "= a local fix of the winter master cfg base_version)")
        if name == "run":
            p.add_argument("--budget", type=float, required=True, help="USD cap of the target's scope")
            p.add_argument("--seed", type=int)
        if name == "compose":
            p.add_argument("--version", type=int, required=True)
            p.add_argument("--raw", help="repo path of a raw model output (default: the sidecar's)")
        if name == "screens":
            p.add_argument("--replay", type=int)
            p.add_argument("--act", action="append")
            p.add_argument("--tag")
            p.add_argument("--no-motion", action="store_true")
    args = ap.parse_args()
    global VARIANT
    VARIANT = getattr(args, "variant", "winter") or "winter"
    {"prompt": cmd_prompt, "run": cmd_run, "compose": cmd_compose, "patches": cmd_patches, "screens": cmd_screens,
     "import": cmd_import}[args.cmd](args)


if __name__ == "__main__":
    main()
