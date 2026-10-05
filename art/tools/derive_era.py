"""Derive another era of the SAME camera from an accepted natural base painting (art/tools/PAINTING.md "Natural mode",
step "camera families").

game.json `location_families` lists the rooms that show one place in several eras (L_STOP: S57 1982, S11 1995,
S51 2020; L_SCHOOL_FRONT, L_HALL, L_CLASS, L_CABINET, L_YARD, L_WINDOW). They share one camera: the
`landmark_layouts` anchors must stay pixel-identical, and so must everything built (walls, doors, kerbs, windows).
Painting each era from scratch drifts the camera; this tool instead EDITS the accepted base painting with one Nano
Banana Pro call (USD 0.15): image 1 = the base master, image 2 = the same master with the target room's natural
blocking drawn on it (where the new era's props go). The prompt says: same camera, keep every built structure and
the anchors, change only what the era changes (art/prompts/natural/<TARGET>.era.txt).

After the call it measures the camera: a global shift (phase correlation, compensated when small) and the local shift
at every anchor and exit (normalised cross-correlation of the base and derived edges), and writes a review image
with the anchors, the target rects and the base edges over the derived painting.

Per-room files (TARGET only; the base is read-only):
  blocking   src/game/data/blocking/<TARGET>.json   (`init` drafts it from the base: same walk polygon, band, scale,
                                                     anchors; hotspots / exits copied where they match - verify!)
  prompt     art/prompts/natural/<TARGET>.era.txt   (`init` drafts it with TODOs; English)
  master     art/masters/bg_natural/<TARGET>_v<N>.png + .json (kind "derive", from_room, from_version, drift)
  review     art/review/natural/<TARGET>_v<N>_derive.png (anchors + edges + rects), _overlay.png, _crops.png
  export     src/game/assets/bg_natural/<TARGET>.webp (unless --no-export)
  spend      art/spend-log.csv scope bg_natural/<TARGET>/ (per-room budget)

Usage (repo root; PYTHONIOENCODING=utf-8 python -X utf8 art/tools/derive_era.py ...):
  init    S11 S51                    draft the target blocking + era prompt (free; keeps existing files)
  prompt  S11 S51 --from 2           assembled prompt, guide image and a pre-review of the target rects on the base
                                     painting: art/review/natural/S51_from_S11_v2_prereview.png (free)
  run     S11 S51 --from 2 --budget 0.30 [--seed N] [--no-export]
                                     ONE paid edit (USD 0.15) -> master, drift report, review, export
  review  S11 S51 --from 2 --version 1
                                     re-measure / re-draw the review of an existing derived master (free)
  --test  allows a base and target outside one family (or the same room); writes into art/review/natural/derive_test/
          only (no master, no export, scope bg_natural/derive_test/) - for testing the tool itself.
"""
from __future__ import annotations

import argparse
import datetime
import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fal_api  # noqa: E402
import paint_natural  # noqa: E402
import paint_room  # noqa: E402
import review_room  # noqa: E402

paint_natural.install()
check_blocking = paint_natural.check_blocking
ROOT = paint_room.ROOT
ART = ROOT / "art"
TEST_DIR = ART / "review" / "natural" / "derive_test"
ANCHOR_TOLERANCE = 8        # game px: an anchor that moved more than this means the camera drifted
GLOBAL_COMPENSATE = 48      # master px: a global shift up to this is compensated (translated back)
PROP, NPC, EXIT, WALK, ANCHOR, EDGE = (255, 190, 40), (80, 160, 255), (255, 70, 70), (60, 220, 90), (255, 0, 255), \
    (0, 230, 255)


# --------------------------------------------------------------------------- data

def game() -> dict:
    return check_blocking.load_game()


def family_of(room_id: str) -> tuple[dict | None, str | None]:
    """(location family, era) of a room."""
    for fam in game().get("location_families", []):
        for era, rid in (fam.get("versions") or {}).items():
            if rid == room_id:
                return fam, era
    return None, None


def room_era(room_id: str) -> str:
    return str(next(r for r in game()["rooms"] if r["id"] == room_id).get("era", ""))


def check_pair(base: str, target: str, test: bool) -> dict | None:
    fam_b, _ = family_of(base)
    fam_t, _ = family_of(target)
    if test:
        return fam_t or fam_b
    if fam_b is None or fam_t is None or fam_b["id"] != fam_t["id"]:
        sys.exit(f"{base} and {target} are not one game.json location family (use --test to try the tool anyway)")
    if base == target:
        sys.exit("base and target are the same room")
    return fam_t


def base_master(base: str, version: int) -> Path:
    path = paint_room.MASTERS / f"{base}_v{version}.png"
    if not path.exists():
        sys.exit(f"missing base master {path.relative_to(ROOT)}")
    return path


def as_model(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    return img if img.size == paint_room.MODEL_FRAME else img.resize(paint_room.MODEL_FRAME, Image.Resampling.LANCZOS)


# --------------------------------------------------------------------------- init (drafts)

def draft_target_blocking(base: str, target: str) -> dict:
    """Same camera: copy the base's walk polygon, band, scale, spawn, anchors; hotspots whose id suffix matches and
    exits at the same template position (game.json rect x) take the base geometry; the rest keeps game.json's."""
    base_b = paint_natural.blocking_of(base)
    base_room, _ = paint_natural._template_load_room(base)
    room, _ = paint_natural._template_load_room(target)
    draft = paint_natural.draft_blocking(target)
    for key in ("walk_polygon", "walk_band", "actor_scale", "spawn", "anchors", "occluders"):
        if key in base_b:
            draft[key] = base_b[key]
    draft["family_base"] = base
    draft["status"] = (f"DRAFT derived from the {base} blocking (same camera). Verify every hotspot / exit against the "
                       f"derived painting; anchors, walk_band and actor_scale must stay identical to {base}.")
    base_targets = {**(base_b.get("hotspots") or {}), **(base_b.get("exits") or {})}
    for h in room["hotspots"]:
        suffix = h["id"].split(".", 1)[1]
        src = f"{base}.{suffix}"
        if src in base_targets and h["id"] in draft["hotspots"]:
            draft["hotspots"][h["id"]] = dict(base_targets[src], reason=f"copied from {src} (same camera) - verify")
    base_exits = {e["id"]: e for e in base_room["exits"]}
    for e in room["exits"]:
        near = min(base_exits.values(), key=lambda b: abs(b["rect"][0] - e["rect"][0]), default=None)
        if near and abs(near["rect"][0] - e["rect"][0]) < 100 and near["id"] in base_targets:
            draft["exits"][e["id"]] = dict(base_targets[near["id"]],
                                           reason=f"copied from {near['id']} (same template position) - verify")
    return draft


ERA_PROMPT = """# {target} {name} ({era}) - ERA DERIVATION prompt body for art/tools/derive_era.py (base {base}, {base_era})
# Image 1 = the accepted {base} natural master, image 2 = the same with the {target} blocking drawn on it.
# Write ENGLISH. Placeholders: {{rect:ID}} {{exit:ID}} {{walk}} {{anchors}} {{npc_zones}} expand from the {target} blocking.
# location_families text for {era} (Slovak, translate): {family_text}
# art_brief (Slovak, translate): {brief}
Era changes: TODO what is different in {era} compared with {base_era}: season, weather and light; which objects of the
time replace which (shelter, signs, posters, vehicles, cars, street furniture); what is newer, older or not built yet.
Everything built that exists in both eras stays exactly where it is.

Interactive props of {era}:
{props}
{exits}

Walkable floor: {{walk}} stays open ground with nothing standing on it.
{{npc_zones}}

Fiction rules: no house numbers, no names, no shop signs, no logos, no brand lettering, no people, no animals. Any paper
shows only illegible scribbles, no digits.
"""


def draft_era_prompt(base: str, target: str) -> str:
    room, _ = paint_natural._template_load_room(target)
    fam, era = family_of(target)
    props = "\n".join(f"{i}. {{rect:{h['id']}}}: TODO {h['name']}." for i, h in
                      enumerate((h for h in room["hotspots"] if h["kind"] != "npc"), 1))
    exits = " ".join(f"{{exit:{e['id']}}} is TODO ({e['label']})." for e in room["exits"])
    return ERA_PROMPT.format(target=target, name=room["name"], era=room.get("era", era), base=base,
                             base_era=room_era(base), family_text=(fam or {}).get(era or "", "-"),
                             brief=room.get("art_brief", ""), props=props, exits=exits)


ERA_FILE_OVERRIDE: Path | None = None   # --era-file


def era_prompt_path(target: str) -> Path:
    return ERA_FILE_OVERRIDE or paint_room.PROMPTS / f"{target}.era.txt"


def cmd_init(args) -> None:
    check_pair(args.base, args.target, args.test)
    path = check_blocking.blocking_path(args.target)
    if path.exists():
        print(f"kept  {path.relative_to(ROOT)}")
    else:
        path.write_text(json.dumps(draft_target_blocking(args.base, args.target), indent=2, ensure_ascii=False),
                        encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} (DRAFT from {args.base}: verify)")
    prompt = era_prompt_path(args.target)
    if prompt.exists():
        print(f"kept  {prompt.relative_to(ROOT)}")
    else:
        prompt.parent.mkdir(parents=True, exist_ok=True)
        prompt.write_text(draft_era_prompt(args.base, args.target), encoding="utf-8")
        print(f"wrote {prompt.relative_to(ROOT)} (DRAFT: replace every TODO)")


# --------------------------------------------------------------------------- prompt

def expand_era(text: str, room: dict, anchors: dict) -> str:
    import re
    hotspots = {h["id"]: h for h in room["hotspots"]}
    exits = {e["id"]: e for e in room["exits"]}
    used: set[str] = set()

    def rect(match) -> str:
        kind, ident = match.group(1), match.group(2)
        table = hotspots if kind == "rect" else exits
        if ident not in table:
            sys.exit(f"era prompt references unknown {kind} id {ident!r}")
        used.add(ident)
        item = table[ident]
        label = f"exit: {item['label']}" if kind == "exit" else item["name"]
        return f"the box labelled '{label}' in image 2 ({paint_room.box_text(item['rect'])})"

    text = re.sub(r"\{(rect|exit):([^}]+)\}", rect, text)
    text = text.replace("{walk}", paint_room.walk_text(room))
    figures = {f["id"]: f for f in paint_natural.npc_figures(room["id"])}
    npc_text = " ".join(
        f"NPC zone at {paint_room.box_text(h['rect'])}: an animated character sprite will be drawn here later, so "
        f"paint no person, figure or silhouette in it." + paint_natural.staging_sentence(figures[h["id"]], h["rect"])
        for h in room["hotspots"] if h["kind"] == "npc" and h["id"] in figures) or "This room has no NPC zones."
    used.update(h["id"] for h in room["hotspots"] if h["kind"] == "npc")
    text = text.replace("{npc_zones}", npc_text)
    text = text.replace("{anchors}", anchor_sentence(anchors))
    missing = [h for h in hotspots if h not in used]
    if missing:
        sys.exit(f"era prompt does not place hotspot(s): {', '.join(missing)}")
    return text


def anchor_sentence(anchors: dict) -> str:
    return " ".join(f"The fixed landmark '{name}' stays exactly at x {x}, y {y} "
                    f"({100 * x / 1920:.0f} % from the left, {100 * y / 1080:.0f} % from the top)."
                    for name, (x, y) in anchors.items())


def read_era_prompt(target: str) -> str:
    path = era_prompt_path(target)
    if not path.exists():
        sys.exit(f"write {path.relative_to(ROOT)} first (derive_era.py init BASE {target})")
    body = "\n".join(line for line in path.read_text(encoding="utf-8").splitlines() if not line.startswith("#"))
    return body.strip()


def guide_image(base_img: Image.Image, room: dict) -> Image.Image:
    """The base painting (game frame) with the target's blocking drawn on it, in model geometry."""
    frame = paint_room.fit_to_frame(base_img).convert("RGBA")
    layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.polygon([tuple(p) for p in room["walk_polygon"]], outline=WALK + (255,), width=3)
    for h in room["hotspots"]:
        x, y, w, hh = h["rect"]
        colour = NPC if h["kind"] == "npc" else PROP
        d.rectangle([x, y, x + w, y + hh], outline=colour + (255,), width=4)
        review_room.label(d, (x, y - 24), "keep clear" if h["kind"] == "npc" else h["name"], colour, 18)
    for e in room["exits"]:
        x, y, w, hh = e["rect"]
        d.rectangle([x, y, x + w, y + hh], outline=EXIT + (255,), width=4)
        review_room.label(d, (min(max(x, 10), 1700), y - 24), f"exit: {e['label']}", EXIT, 18)
    return paint_room.to_model_geometry(Image.alpha_composite(frame, layer).convert("RGB"))


def assemble(base: str, target: str, version: int, test: bool) -> dict:
    fam = check_pair(base, target, test)
    room, anchors = paint_natural.natural_room(target)
    _, base_anchors = paint_natural.natural_room(base)
    if anchors != base_anchors:
        print(f"WARNING: anchors of {target} {anchors} differ from {base} {base_anchors}: one camera needs identical "
              f"anchors (set 'anchors' in the blocking files)")
    master_path = base_master(base, version)
    base_img = as_model(Image.open(master_path))
    era_b, era_t = room_era(base), room_era(target)
    place = (fam or {}).get("place") or room["name"]
    preamble = (
        f"You receive 2 images. Image 1 is a finished background painting of our point-and-click adventure game: "
        f"{place} in {era_b}. Image 2 is the same painting with coloured boxes that only mark where the interactive "
        f"objects of the new version must be. Edit image 1 into the SAME PLACE in {era_t}, seen by the SAME CAMERA: "
        f"keep the exact viewpoint, lens, horizon, perspective and framing, and keep the position, size and outline "
        f"of every building, wall, kerb, step, door, window, pole, rail and tree trunk that exists in both eras. "
        f"Change only what the time changes, as described below. Keep the painting technique, brushwork, palette "
        f"handling and level of detail of image 1.")
    body = expand_era(read_era_prompt(target), room, anchors)
    warning = (
        "Image 2 is a positioning aid only: do NOT draw any of its boxes, outlines, labels or captions. The result is "
        "image 1 edited, in the same 16:9 framing: no frames, no borders, no UI, no captions, no watermark, no text "
        "except what is asked for above, and no people or animals unless stated above.")
    prompt = "\n\n".join([preamble, anchor_sentence(anchors), body, warning, paint_room.style_sentence()])
    return {"prompt": prompt, "base_img": base_img, "guide": guide_image(base_img, room), "room": room,
            "anchors": anchors, "base_path": master_path}


def out_dir(test: bool) -> Path:
    return TEST_DIR if test else ART / "review" / "natural"


def cmd_prompt(args) -> None:
    job = assemble(args.base, args.target, args.source, args.test)
    print(job["prompt"])
    print(f"\n{len(job['prompt'])} characters")
    folder = out_dir(args.test)
    folder.mkdir(parents=True, exist_ok=True)
    pre = folder / f"{args.target}_from_{args.base}_v{args.source}_prereview.png"
    paint_room.fit_to_frame(job["guide"]).save(pre)
    print(f"pre-review (target blocking on the base painting): {pre.relative_to(ROOT)}")


# --------------------------------------------------------------------------- camera measurement

def gray(img: Image.Image, size: tuple[int, int]) -> np.ndarray:
    return np.asarray(img.convert("L").resize(size, Image.Resampling.LANCZOS), dtype=np.float32)


def edges(img: Image.Image, size: tuple[int, int]) -> np.ndarray:
    g = img.convert("L").resize(size, Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(1))
    return np.asarray(g.filter(ImageFilter.FIND_EDGES), dtype=np.float32)


def phase_shift(moved: np.ndarray, ref: np.ndarray) -> tuple[int, int]:
    """(dx, dy) such that moved ~= ref shifted by (dx, dy)."""
    win = np.outer(np.hanning(ref.shape[0]), np.hanning(ref.shape[1]))
    a, b = np.fft.fft2(moved * win), np.fft.fft2(ref * win)
    r = a * np.conj(b)
    r /= np.abs(r) + 1e-9
    corr = np.fft.ifft2(r).real
    dy, dx = np.unravel_index(np.argmax(corr), corr.shape)
    if dy > ref.shape[0] // 2:
        dy -= ref.shape[0]
    if dx > ref.shape[1] // 2:
        dx -= ref.shape[1]
    return int(dx), int(dy)


def local_shift(moved: np.ndarray, ref: np.ndarray, x: float, y: float, half: int = 48, search: int = 24):
    """Best (dx, dy, ncc) of the ref window around (x, y) found in `moved` (arrays in game px / 2)."""
    h, w = ref.shape
    x0, y0 = int(max(half, min(w - half, x))), int(max(half, min(h - half, y)))
    tpl = ref[y0 - half:y0 + half, x0 - half:x0 + half]
    tpl = tpl - tpl.mean()
    tn = np.sqrt((tpl ** 2).sum()) + 1e-6
    best = (0, 0, -1.0)
    for dy in range(-search, search + 1):
        for dx in range(-search, search + 1):
            ya, xa = y0 - half + dy, x0 - half + dx
            if ya < 0 or xa < 0 or ya + 2 * half > h or xa + 2 * half > w:
                continue
            win = moved[ya:ya + 2 * half, xa:xa + 2 * half]
            win = win - win.mean()
            ncc = float((win * tpl).sum() / (np.sqrt((win ** 2).sum()) * tn + 1e-6))
            if ncc > best[2]:
                best = (dx, dy, ncc)
    return best


def measure(derived: Image.Image, base: Image.Image, room: dict, anchors: dict) -> dict:
    """Global shift (master px) and per-anchor / per-exit local shifts (game px) of derived vs base."""
    small = (paint_room.MODEL_FRAME[0] // 4, paint_room.MODEL_FRAME[1] // 4)
    gx, gy = phase_shift(gray(derived, small), gray(base, small))
    shift = [gx * 4, gy * 4]
    half_frame = (960, 540)
    e_der = edges(paint_room.fit_to_frame(derived), half_frame)
    e_base = edges(paint_room.fit_to_frame(base), half_frame)
    points = {f"anchor {k}": v for k, v in anchors.items()}
    for e in room["exits"]:
        x, y, w, h = e["rect"]
        points[f"exit {e['id']}"] = [x + w / 2, y + h / 2]
    local = {}
    for name, (x, y) in points.items():
        dx, dy, ncc = local_shift(e_der, e_base, x / 2, y / 2)
        local[name] = {"at": [x, y], "shift_px": [dx * 2, dy * 2], "ncc": round(ncc, 3),
                       "ok": max(abs(dx * 2), abs(dy * 2)) <= ANCHOR_TOLERANCE and ncc > 0.25}
    return {"global_shift_master_px": shift, "points": local,
            "camera_ok": all(v["ok"] for k, v in local.items() if k.startswith("anchor"))}


def derive_review(derived: Image.Image, base: Image.Image, room: dict, anchors: dict, report: dict,
                  out: Path) -> Path:
    """Top: base | derived (half size) with anchors. Bottom: derived + base edges (cyan) + target rects + shifts."""
    base_f = paint_room.fit_to_frame(base).convert("RGB")
    der_f = paint_room.fit_to_frame(derived).convert("RGB")
    sheet = Image.new("RGB", (1920, 540 + 1080), (20, 20, 20))
    for i, img in enumerate((base_f, der_f)):
        tile = img.copy()
        d = ImageDraw.Draw(tile)
        for name, (ax, ay) in anchors.items():
            d.line([(ax - 22, ay), (ax + 22, ay)], fill=ANCHOR, width=5)
            d.line([(ax, ay - 22), (ax, ay + 22)], fill=ANCHOR, width=5)
        sheet.paste(tile.resize((960, 540), Image.Resampling.LANCZOS), (i * 960, 0))
    big = der_f.convert("RGBA")
    edge = np.asarray(base_f.convert("L").filter(ImageFilter.GaussianBlur(1)).filter(ImageFilter.FIND_EDGES))
    alpha = np.clip((edge.astype(np.float32) - 18) * 6, 0, 200).astype(np.uint8)
    cyan = Image.new("RGBA", big.size, EDGE + (0,))
    cyan.putalpha(Image.fromarray(alpha, "L"))
    big = Image.alpha_composite(big, cyan)
    layer = Image.new("RGBA", big.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.polygon([tuple(p) for p in room["walk_polygon"]], outline=WALK + (255,), width=3)
    for h in room["hotspots"]:
        x, y, w, hh = h["rect"]
        colour = NPC if h["kind"] == "npc" else PROP
        d.rectangle([x, y, x + w, y + hh], outline=colour + (255,), width=3)
        review_room.label(d, (x, y + hh + 4), h["id"], colour, 16)
    for e in room["exits"]:
        x, y, w, hh = e["rect"]
        d.rectangle([x, y, x + w, y + hh], outline=EXIT + (255,), width=3)
    for name, info in report["points"].items():
        x, y = info["at"]
        colour = ANCHOR if name.startswith("anchor") else EXIT
        d.line([(x - 18, y), (x + 18, y)], fill=colour + (255,), width=4)
        d.line([(x, y - 18), (x, y + 18)], fill=colour + (255,), width=4)
        sx, sy = info["shift_px"]
        tag = "ok" if info["ok"] else "MOVED"
        review_room.label(d, (min(x + 22, 1600), y - 12), f"{name} {sx:+d},{sy:+d} px ncc {info['ncc']:.2f} {tag}",
                          colour, 16)
    g = report["global_shift_master_px"]
    verdict = "CAMERA KEPT" if report["camera_ok"] else "CAMERA DRIFT - check the anchors"
    review_room.label(d, (12, 1080 - 12), f"{room['id']} derived: cyan = edges of the base painting; global shift "
                                          f"{g[0]:+d},{g[1]:+d} master px; {verdict}", (255, 255, 255), 20, "ld")
    sheet.paste(Image.alpha_composite(big, layer).convert("RGB"), (0, 540))
    sheet.save(out)
    return out


# --------------------------------------------------------------------------- run / review

def cmd_run(args) -> None:
    target = args.target
    if not args.test and paint_natural.run_check(target) != 0:
        sys.exit(f"{target}: fix the blocking errors first")
    era_file = era_prompt_path(target)
    if era_file.exists() and "TODO" in era_file.read_text(encoding="utf-8"):
        sys.exit(f"{era_file.relative_to(ROOT)} still contains TODO - finish it before a paid call")
    if not args.test and paint_natural.paid_attempts(target) >= paint_natural.MAX_ATTEMPTS:
        sys.exit(f"{target}: {paint_natural.MAX_ATTEMPTS} paid paint/derive attempts already; repair with "
                 f"`paint_natural.py refit fix` or explain a new attempt in art/masters/bg_natural/{target}.md")
    job = assemble(args.base, target, args.source, args.test)
    scope = args.scope or ("bg_natural/derive_test/" if args.test else f"bg_natural/{target}/")
    version = paint_room.next_version(target)
    folder = TEST_DIR if args.test else paint_room.MASTERS
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"{target}_from_{args.base}_v{args.source}_test{version}" if args.test else f"{target}_v{version}"
    seed = args.seed if args.seed is not None else random.randint(1, 2 ** 31 - 1)
    arguments = {"prompt": job["prompt"],
                 "image_urls": [fal_api.image_data_uri(job["base_img"], fmt="PNG"),
                                fal_api.image_data_uri(job["guide"], max_side=2048, fmt="JPEG")],
                 "aspect_ratio": paint_room.ASPECT, "resolution": paint_room.RESOLUTION, "output_format": "png",
                 "num_images": 1, "seed": seed}
    price = fal_api.IMAGE_PRICES[(paint_room.MODEL, paint_room.RESOLUTION)]
    asset = f"{scope}{stem}_derive"
    started = datetime.datetime.now().isoformat(timespec="seconds")
    print(f"{target}: derive from {args.base} v{args.source}, scope {scope}, budget USD {args.budget:.2f}")
    result = fal_api.run(paint_room.MODEL, arguments, asset, price, budget=(scope, args.budget), timeout_s=900)
    raw = folder / f"_{stem}_raw.png"
    fal_api.download(result["images"][0]["url"], raw)
    derived = as_model(Image.open(raw))
    report = measure(derived, job["base_img"], job["room"], job["anchors"])
    gx, gy = report["global_shift_master_px"]
    if (gx or gy) and max(abs(gx), abs(gy)) <= GLOBAL_COMPENSATE:
        from PIL import ImageChops
        derived = ImageChops.offset(derived, -gx, -gy)
        report = dict(measure(derived, job["base_img"], job["room"], job["anchors"]), compensated_master_px=[gx, gy])
        print(f"model output drifted by {gx:+d},{gy:+d} master px; compensated")
    out = folder / f"{stem}.png"
    derived.save(out)
    meta = {"room": target, "version": None if args.test else version, "kind": "derive", "from_room": args.base,
            "from_version": args.source, "from_master": job["base_path"].relative_to(ROOT).as_posix(),
            "model": paint_room.MODEL, "resolution": paint_room.RESOLUTION, "aspect_ratio": paint_room.ASPECT,
            "seed": result.get("seed", seed), "usd": price, "scope": scope, "spend_log_asset": asset,
            "started": started, "prompt_file": era_prompt_path(target).relative_to(ROOT).as_posix(),
            "blocking_file": f"src/game/data/blocking/{target}.json", "prompt": job["prompt"],
            "image_urls": [job["base_path"].relative_to(ROOT).as_posix() + " (model geometry)",
                           f"{job['base_path'].name} + {target} blocking boxes (guide)"],
            "camera": report, "model_description": result.get("description"),
            "raw_model_output": raw.relative_to(ROOT).as_posix(), "output_size": list(derived.size)}
    if not args.test:
        meta["blocking"] = paint_natural.blocking_of(target)
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    review = derive_review(derived, job["base_img"], job["room"], job["anchors"], report,
                           (folder if args.test else out_dir(False)) / f"{stem}_derive.png")
    print(f"{out.relative_to(ROOT)} ${price:.2f} (scope {scope} spent {fal_api.logged_spend(scope):.2f} of "
          f"{args.budget:.2f}); camera {'KEPT' if report['camera_ok'] else 'DRIFTED'}")
    print_report(report)
    print(f"review: {review.relative_to(ROOT)}")
    if args.test:
        return
    paint_natural.natural_review(target, version)
    if not args.no_export:
        args.room, args.version, args.quality = target, version, 90
        paint_room.cmd_export(args)
    print(f"LOOK at {out.relative_to(ROOT)} and the review images before you accept it")


def print_report(report: dict) -> None:
    for name, info in report["points"].items():
        sx, sy = info["shift_px"]
        print(f"  {name:40s} shift {sx:+3d},{sy:+3d} px  ncc {info['ncc']:.2f}  {'ok' if info['ok'] else 'MOVED'}")


def cmd_review(args) -> None:
    job = assemble(args.base, args.target, args.source, args.test)
    if args.test:
        path = TEST_DIR / f"{args.target}_from_{args.base}_v{args.source}_test{args.version}.png"
        out = TEST_DIR / f"{path.stem}_derive.png"
    else:
        path = paint_room.MASTERS / f"{args.target}_v{args.version}.png"
        out = out_dir(False) / f"{args.target}_v{args.version}_derive.png"
    derived = as_model(Image.open(path))
    report = measure(derived, job["base_img"], job["room"], job["anchors"])
    derive_review(derived, job["base_img"], job["room"], job["anchors"], report, out)
    print_report(report)
    print(f"camera {'KEPT' if report['camera_ok'] else 'DRIFTED'}; review: {out.relative_to(ROOT)}")
    if not args.test:
        paint_natural.natural_review(args.target, args.version)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("init", "prompt", "run", "review"):
        p = sub.add_parser(name)
        p.add_argument("base", help="room with the accepted natural painting")
        p.add_argument("target", help="room of the same location family to derive")
        p.add_argument("--test", action="store_true")
        p.add_argument("--era-file", help="era prompt instead of art/prompts/natural/<TARGET>.era.txt (repo path)")
        if name != "init":
            p.add_argument("--from", dest="source", type=int, required=True, help="base master version")
        if name == "run":
            p.add_argument("--budget", type=float, required=True, help="USD cap of the scope (0.15 per call)")
            p.add_argument("--scope", help="spend-log prefix (default bg_natural/<TARGET>/)")
            p.add_argument("--seed", type=int)
            p.add_argument("--no-export", action="store_true")
        if name == "review":
            p.add_argument("--version", type=int, required=True, help="derived master version (test: the testN)")
    args = ap.parse_args()
    global ERA_FILE_OVERRIDE
    if args.era_file:
        ERA_FILE_OVERRIDE = (ROOT / args.era_file).resolve()
    {"init": cmd_init, "prompt": cmd_prompt, "run": cmd_run, "review": cmd_review}[args.cmd](args)


if __name__ == "__main__":
    main()
