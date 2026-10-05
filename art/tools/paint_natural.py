"""Natural re-blocking room pipeline: design -> check -> paint -> review -> export -> in-engine screens, ONE ROOM per
command, writing only that room's files (art/tools/PAINTING.md "Natural mode", docs/reblock/README.md).

Same recipe and code as paint_room.py / review_room.py / refit_room.py, but every placeholder, overlay and crop uses
the room's effective natural geometry: game.json merged with src/game/data/blocking/<room>.json (merge in
tools/check_blocking.py, the same field-by-field rule as src/game/scripts/World/Room.cs). Nothing of the template
pipeline is overwritten. Per-room files:

  blocking          src/game/data/blocking/<room>.json               (you design it; `init` writes a draft)
  prompt + sketch   art/prompts/natural/<room>.txt, <room>.sketch.json (`init` writes drafts; `sketch` re-derives)
  layout guide      art/layout/natural/<room>.png, sketch render art/layout/natural/<room>_sketch.png
  masters           art/masters/bg_natural/<room>_v<N>.png + .json sidecar, notes art/masters/bg_natural/<room>.md
  foreground mask   art/prompts/natural/<room>.fg.json -> src/game/assets/fg_natural/<room>.webp (`mask`)
  state art         src/game/assets/variants_natural/<room>_<name>.webp (`patch`), referenced from the blocking's
                    state_patches / variant_layers
  review            art/review/natural/<room>_v<N>_overlay.png (rects, NPC staging + figure sizes, sill lines,
                    occluders, actor scale ruler, anchors), _crops.png
  export            src/game/assets/bg_natural/<room>.webp (the template bg/<room>.webp stays)
  screens           build/screens/m3/<room>/ (Godot, --blocking natural, needs a window)
  spend             art/spend-log.csv, default scope bg_natural/<room>/ (per-room budget)

Usage (from the repo root, PYTHONIOENCODING=utf-8 python -X utf8 art/tools/paint_natural.py ...):
  init    S12                         drafts of the blocking / prompt / sketch files that do not exist yet (free)
  sketch  S12 [--force]               starter sketch derived from the blocking (props as blocks, floor, exits) (free)
  check   S12 [--strict]              tools/check_blocking.py for the room (free)
  prompt  S12                         assembled prompt + sketch render + sketch review overlay (free)
  run     S12 --budget 0.45 [--seed N] [--no-export] [--max-attempts 3]
                                      ONE paid attempt (USD 0.15): check -> sketch -> paint -> review -> export
  paint   S12 --budget 0.45           paint only (one paid call) + review
  review  S12 2 [--grid x0 y0 x1 y1]  natural review overlay / measuring grid (free)
  export  S12 2                       master v2 -> bg_natural/S12.webp + sidecar "exported" (free)
  refit   fit|extend|fix S12 2 ...    refit_room.py on the natural masters (extend / fix: USD 0.15)
  mask    S12 [--preview-only]        foreground mask fg_natural/S12.webp cut from the exported painting along the
                                      polygons of art/prompts/natural/S12.fg.json (free)
  patch   S12 NAME --from V --box x y w h [--full] [--feather 6]
                                      state patch / variant overlay variants_natural/S12_NAME.webp cut from master vV
                                      (e.g. a `refit fix` version: outside its box it is pixel-identical) (free)
  import                              Godot --headless --import, serialised by a lock (free)
  screens S12 [--replay N] [--act ID ...] [--tag after_G04] [--frames 6]
                                      in-engine shots: <tag>_labels.png, <tag>_clean.png, <tag>_motion_NN.png (free)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layout_guide  # noqa: E402
import paint_room  # noqa: E402
import review_room  # noqa: E402

ROOT = paint_room.ROOT
sys.path.insert(0, str(ROOT / "tools"))
import check_blocking  # noqa: E402

ART = ROOT / "art"
GAME_DIR = ROOT / "src" / "game"
GODOT = ROOT / ".tools" / "godot" / "Godot_v4.7.2-stable_mono_win64" / "Godot_v4.7.2-stable_mono_win64_console.exe"
SCREENS = ROOT / "build" / "screens" / "m3"
IMPORT_LOCK = ROOT / "build" / ".godot_import.lock"
MAX_ATTEMPTS = 3
HERO_HEIGHT = 512
_template_load_room = paint_room.load_room
_template_expand = paint_room.expand
_template_review = review_room.review


# --------------------------------------------------------------------------- geometry

def blocking_of(room_id: str) -> dict:
    path = check_blocking.blocking_path(room_id)
    if not path.exists():
        sys.exit(f"no natural blocking {path.relative_to(ROOT)} (run: paint_natural.py init {room_id})")
    return json.loads(path.read_text(encoding="utf-8"))


def natural_room(room_id: str) -> tuple[dict, dict]:
    """Effective natural room and its camera-family anchors (the blocking's "anchors" override game.json's
    landmark_layouts positions; every room of one family must use the same values)."""
    room, anchors = _template_load_room(room_id)
    blocking = blocking_of(room_id)
    eff = check_blocking.effective_room(room, blocking)
    eff.pop("_blocking", None)
    return eff, dict(anchors, **(blocking.get("anchors") or {}))


def perspective_of(room_id: str) -> tuple[float, float, float, float]:
    room, _ = natural_room(room_id)
    b = blocking_of(room_id)
    ys = [p[1] for p in room["walk_polygon"]]
    band = b.get("walk_band") or [min(ys), max(ys)]
    scale = b.get("actor_scale") or [0.80, 1.00]
    return band[0], band[1], scale[0], scale[1]


def npc_figures(room_id: str) -> list[dict]:
    """Per NPC: feet, scale, resolved variant, sill, drawn figure box (canvas px) - what the game will draw."""
    room, _ = natural_room(room_id)
    b = blocking_of(room_id)
    persp = perspective_of(room_id)
    out = []
    for h in room["hotspots"]:
        if h["kind"] != "npc":
            continue
        st = (b.get("npcs") or {}).get(h["id"], {})
        x, y, w, hh = h["rect"]
        feet = st.get("feet") or [x + w / 2, y + hh]
        scale = st.get("scale") or check_blocking.scale_at(persp, feet[1])
        manifest = check_blocking.actor_manifest(h.get("character_id")) or {}
        ok, variant = check_blocking.resolve_staging(manifest, st.get("variant")) if manifest else (True, None)
        height = float(manifest.get("height_px", HERO_HEIGHT))
        sill = st.get("sill_y")
        chosen = variant or manifest.get("default_variant")
        if sill is not None and chosen:
            # bust: the cell above the pivot (= cut line) is drawn above the sill
            sheets = manifest.get("sheets") or {}
            anims = ((manifest.get("variants") or {}).get(chosen) or {}).get("animations") or {}
            sheet = sheets.get((anims.get("idle_still") or anims.get("idle") or {}).get("sheet", ""), {})
            above = float((sheet.get("pivot") or [0, height * 0.5])[1])
            top = sill - above * scale
            bottom = sill
        else:
            top = feet[1] - height * scale
            bottom = feet[1]
        half = 0.22 * height * scale
        out.append({"id": h["id"], "char": h.get("character_id"), "feet": feet, "scale": scale, "variant": chosen,
                    "staging": st.get("variant"), "ok": ok, "sill": sill, "box": [feet[0] - half + st.get("offset_x", 0),
                                                                                  top, 2 * half, bottom - top],
                    "z": st.get("z", "auto")})
    return out


# --------------------------------------------------------------------------- prompt: staging-aware NPC sentences

def staging_sentence(fig: dict, rect: list[int]) -> str:
    x, _, w, _ = rect
    span = f"x {x - 30}-{x + w + 30}"
    variant = fig["variant"] or ""
    if fig["sill"] is not None and variant in ("counter", "table"):
        what = "counter" if variant == "counter" else "table"
        return (f" The character stands behind a {what}: paint the {what}'s top edge as one straight horizontal line "
                f"exactly at y {fig['sill']:.0f} across {span}, with its front going down to the floor; above that "
                f"edge keep only plain background (wall, shelves), no person.")
    if fig["sill"] is not None and variant.startswith("window"):
        return (f" The character is seen through a window: paint the window sill exactly at y {fig['sill']:.0f} "
                f"across {span}; the opening above the sill shows a plain, dim interior, no person.")
    manifest = check_blocking.actor_manifest(fig["char"]) or {}
    pose = check_blocking.base_pose(manifest) if manifest else None
    if pose == "seated" and not fig["variant"]:
        return (f" The character's seat (chair, stool or bench) is part of the character sprite: paint only open "
                f"floor at y {fig['feet'][1]:.0f} in this zone - no chair, stool or bench there.")
    return f" The character's feet stand on the floor at y {fig['feet'][1]:.0f}."


def natural_expand(text: str, room: dict, anchors: dict, sketch: bool) -> str:
    result = _template_expand(text, room, anchors, sketch)
    figures = {f["id"]: f for f in npc_figures(room["id"])}
    for h in room["hotspots"]:
        if h["kind"] != "npc" or h["id"] not in figures:
            continue
        generic = (f"NPC zone at {paint_room.box_text(h['rect'])}: an animated character sprite will stand here later, "
                   f"so paint only plain, uncluttered background in it - no person, no figure, no silhouette, no "
                   f"clothes on hooks that read as a person.")
        result = result.replace(generic, generic + staging_sentence(figures[h["id"]], h["rect"]))
    return result


# --------------------------------------------------------------------------- review overlay (natural extras)

FIG = (120, 200, 255)
SILL = (0, 230, 255)
OCC = (255, 255, 255)
RULER = (60, 220, 90)


def natural_extras(img: Image.Image, room_id: str) -> Image.Image:
    img = img.convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    b = blocking_of(room_id)
    top, bottom, s0, s1 = perspective_of(room_id)
    # Actor scale ruler: the hero (512 px at scale 1) at the back, middle and front of the band.
    for i, y in enumerate((top, (top + bottom) / 2, bottom - 4)):
        s = check_blocking.scale_at((top, bottom, s0, s1), y)
        x = 1820 - i * 70
        hgt = HERO_HEIGHT * s
        d.rectangle([x - 0.11 * hgt, y - hgt, x + 0.11 * hgt, y], outline=RULER + (255,), width=2)
        d.ellipse([x - 0.06 * hgt, y - hgt, x + 0.06 * hgt, y - hgt + 0.12 * hgt], outline=RULER + (255,), width=2)
        review_room.label(d, (x, y - hgt - 4), f"hero {s:.2f}", RULER, 14, "mb")
    # NPC figures as the game draws them.
    for f in npc_figures(room_id):
        x0, y0, w, h = f["box"]
        d.rectangle([x0, y0, x0 + w, y0 + h], outline=FIG + (255,), width=3)
        fx, fy = f["feet"]
        d.line([(fx - 14, fy), (fx + 14, fy)], fill=FIG + (255,), width=3)
        d.line([(fx, fy - 14), (fx, fy + 14)], fill=FIG + (255,), width=3)
        if f["sill"] is not None:
            d.line([(x0 - 40, f["sill"]), (x0 + w + 40, f["sill"])], fill=SILL + (255,), width=3)
            review_room.label(d, (x0 + w + 44, f["sill"] - 10), f"sill {f['sill']:.0f}", SILL, 14)
        tag = f"{f['char']} {f['staging'] or 'default'}" + ("" if f["ok"] else " (UNKNOWN)")
        review_room.label(d, (x0, y0 - 22), f"{tag} s{f['scale']:.2f} z {f['z']}", FIG, 14)
    # Occluders: outline + baseline.
    for o in b.get("occluders") or []:
        pts = [tuple(p) for p in o.get("polygon", [])]
        if len(pts) >= 3:
            d.polygon(pts, outline=OCC + (255,), width=2)
            base = o.get("baseline", max(p[1] for p in pts))
            xs = [p[0] for p in pts]
            review_room.dashed_rect(d, (min(xs), base, max(xs), base), OCC + (255,), width=2)
            review_room.label(d, (min(xs), base + 4), f"occluder {o.get('id', '')} base {base}", OCC, 14)
    # Footer: this overlay shows the natural blocking, not game.json (cover the template footer first).
    ImageDraw.Draw(img).rectangle([0, img.height - 40, 1000, img.height], fill=(0, 0, 0, 255))
    review_room.label(d, (12, img.height - 12), f"{room_id} NATURAL review overlay - src/game/data/blocking/"
                                                f"{room_id}.json merged with game.json", (255, 255, 255), 18, "ld")
    return Image.alpha_composite(img, layer).convert("RGB")


def natural_review(room_id: str, version_or_path) -> tuple[Path, Path]:
    out_overlay, out_crops = _template_review(room_id, version_or_path)
    natural_extras(Image.open(out_overlay), room_id).save(out_overlay)
    return out_overlay, out_crops


# --------------------------------------------------------------------------- install

def natural_assemble(room_id: str, mode: str = "auto") -> dict:
    job = _template_assemble(room_id, mode)
    job["images"] = [(kind, item, name.replace(f"art/layout/{room_id}", f"art/layout/natural/{room_id}")
                      .replace(f"art/prompts/{room_id}", f"art/prompts/natural/{room_id}")) for kind, item, name in job["images"]]
    return job


_template_assemble = paint_room.assemble


def install() -> None:
    """Point paint_room / review_room / refit_room at the natural geometry and the separate output folders."""
    paint_room.load_room = natural_room
    paint_room.expand = natural_expand
    paint_room.assemble = natural_assemble
    paint_room.PROMPTS = ART / "prompts" / "natural"
    paint_room.LAYOUT = ART / "layout" / "natural"
    paint_room.MASTERS = ART / "masters" / "bg_natural"
    paint_room.EXPORT = ROOT / "src" / "game" / "assets" / "bg_natural"
    review_room.load_room = natural_room
    review_room.MASTERS = paint_room.MASTERS
    review_room.REVIEW = ART / "review" / "natural"
    review_room.load_nudges = lambda room_id: {}   # art_overrides nudges belong to the template painting
    review_room.review = natural_review


def write_guide(room_id: str) -> None:
    room, anchors = natural_room(room_id)
    paint_room.LAYOUT.mkdir(parents=True, exist_ok=True)
    layout_guide.draw_room(room, anchors).save(paint_room.LAYOUT / f"{room_id}.png")


def fix_sidecar(room_id: str, version: int | None = None) -> Path:
    """paint_room writes the template paths of the prompt and sketch into the sidecar; record the natural ones."""
    version = version or paint_room.next_version(room_id) - 1
    path = paint_room.MASTERS / f"{room_id}_v{version}.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["prompt_file"] = f"art/prompts/natural/{room_id}.txt"
    meta["blocking_file"] = f"src/game/data/blocking/{room_id}.json"
    meta["blocking"] = blocking_of(room_id)
    meta["kind"] = meta.get("kind", "paint")
    if meta.get("image_urls"):
        meta["image_urls"][0] = (f"art/layout/natural/{room_id}_sketch.png (rendered from "
                                 f"art/prompts/natural/{room_id}.sketch.json, model geometry)")
    path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- drafts

PALETTE = ["#c9a227", "#b5651d", "#7a9e3b", "#c0504d", "#4f81bd", "#8064a2", "#4bacc6", "#f79646", "#9bbb59", "#d4a5a5"]


def draft_blocking(room_id: str) -> dict:
    """A valid starting point: game.json geometry for every target, the background path and the staging keys."""
    room, _ = _template_load_room(room_id)
    ys = [p[1] for p in room["walk_polygon"]]
    npcs = {}
    for h in room["hotspots"]:
        if h["kind"] == "npc":
            x, y, w, hh = h["rect"]
            manifest = check_blocking.actor_manifest(h.get("character_id")) or {}
            expected = check_blocking.EXPECTED_STAGING.get(h["id"], "standing")
            candidates = {"bust": ["behind_counter", "window_bust", "window_bust_glass"]}.get(expected, [expected])
            variant = next((c for c in candidates if manifest and check_blocking.resolve_staging(manifest, c)[0]),
                           candidates[0])
            npcs[h["id"]] = {"variant": variant, "feet": [x + w / 2, max(y + hh, min(ys) + 10)],
                             "reason": "TODO: staging per docs/DECISIONS.md item 2; feet where the figure stands"}
            if expected == "bust":
                npcs[h["id"]]["sill_y"] = y + hh // 2
    return {
        "version": 1, "room": room_id,
        "status": "DRAFT - natural re-blocking; copied from game.json, redesign every value from the real photos "
                  "(art/tools/PAINTING.md Natural mode)",
        "note": "TODO: camera height, horizon y, foot line y, px per metre; where each prop really is.",
        "background": f"bg_natural/{room_id}.webp",
        "walk_polygon": room["walk_polygon"], "walk_band": [min(ys), max(ys)], "actor_scale": [0.8, 1.0],
        "spawn": room["spawn"],
        "hotspots": {h["id"]: {"rect": h["rect"], "interaction_point": h["interaction_point"],
                               "label_anchor": h.get("label_anchor") or [h["rect"][0] + h["rect"][2] // 2, h["rect"][1] - 10],
                               "reason": "TODO"} for h in room["hotspots"]},
        "npcs": npcs,
        "exits": {e["id"]: {"rect": e["rect"], "interaction_point": e["interaction_point"], "reason": "TODO"}
                  for e in room["exits"]},
        "state_patches": [],
    }


def draft_sketch(room_id: str) -> dict:
    """Flat-colour starter sketch from the blocking: sky/wall, the walk polygon as floor, every prop rect as its own
    coloured block, counters / sills under staged busts, exits as dark openings. Refine it into the real place."""
    room, _ = natural_room(room_id)
    b = blocking_of(room_id)
    ys = [p[1] for p in room["walk_polygon"]]
    floor_top = min(ys)
    shapes = [
        {"type": "rect", "box": [0, 0, 1920, floor_top], "fill": "#b8c4cc", "note": "TODO sky / back wall"},
        {"type": "rect", "box": [0, floor_top, 1920, 1080 - floor_top], "fill": "#9a8c76", "note": "floor / ground"},
        {"type": "poly", "points": room["walk_polygon"], "fill": "#a39478", "note": "walkable floor (one plain colour)"},
    ]
    for e in room["exits"]:
        x, y, w, h = e["rect"]
        if 0 < x and x + w < 1920:
            shapes.append({"type": "rect", "box": [x, y, w, h], "fill": "#3d3a36", "note": f"exit {e['id']} opening"})
    for f in npc_figures(room_id):
        if f["sill"] is not None:
            x0, _, w, _ = f["box"]
            shapes.append({"type": "rect", "box": [round(x0 - 40), round(f["sill"]), round(w + 80),
                                                   round(max(20, f["feet"][1] - f["sill"]))],
                           "fill": "#8b6a4a", "note": f"{f['id']} {f['variant']} top edge = sill_y {f['sill']}"})
    for i, h in enumerate(h for h in room["hotspots"] if h["kind"] != "npc"):
        shapes.append({"type": "rect", "box": h["rect"], "fill": PALETTE[i % len(PALETTE)], "note": h["id"]})
    return {"note": f"{room_id} natural STARTER sketch derived from src/game/data/blocking/{room_id}.json by "
                    f"paint_natural.py sketch - TODO: redraw walls, horizon, furniture of the real place.",
            "background": "#b8c4cc", "shapes": shapes}


PROMPT_DRAFT = """# {room} {name} ({era}) - NATURAL re-blocking prompt body for art/tools/paint_natural.py
# Geometry: src/game/data/blocking/{room}.json (placeholders expand from the merged natural geometry).
# Composition: art/prompts/natural/{room}.sketch.json
#refs: {refs}
#style: art/backgrounds/sokolikova-street.png
Place: TODO real place and area from the register row ({district}). Images 2-<n> are TODO what each photo shows.

Brief: TODO art_brief in English: {brief}

Camera: TODO height and angle; horizon y; the line where the main wall / frontage meets the floor; px per metre.

What the sketch blocks are, left to right: TODO.

Interactive props - each painted clearly inside its block, the same size as its block, easy to recognise at a glance:
{props}
{exits}

Walkable floor: {{walk}} is TODO surface - one continuous flat surface with no kerb, step, edge or change of material
inside it, and nothing standing on it. Only light and shadows.
{{npc_zones}}
{{anchors}}

Fiction rules: TODO register fiction notes. No house numbers, no names, no shop signs, no logos, no brand lettering
(no TESLA etc.), no people, no animals. Any paper shows only illegible scribbles, no digits.
"""


def draft_prompt(room_id: str) -> str:
    room, _ = _template_load_room(room_id)
    reg = paint_room.load_register_row(room_id)
    props = "\n".join(f"{i}. {{rect:{h['id']}}}: TODO {h['name']}." for i, h in
                      enumerate((h for h in room["hotspots"] if h["kind"] != "npc"), 1))
    exits = " ".join(f"{{exit:{e['id']}}} is TODO ({e['label']})." for e in room["exits"])
    return PROMPT_DRAFT.format(room=room_id, name=room["name"], era=room["era"], district=room.get("district", ""),
                               refs=reg.get("source_files", ""), brief=room.get("art_brief", ""), props=props,
                               exits=exits)


def cmd_init(args) -> None:
    rid = args.room
    path = check_blocking.blocking_path(rid)
    if not path.exists():
        path.write_text(json.dumps(draft_blocking(rid), indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} (DRAFT: redesign from the photos)")
    else:
        print(f"kept  {path.relative_to(ROOT)}")
    prompt = paint_room.PROMPTS / f"{rid}.txt"
    paint_room.PROMPTS.mkdir(parents=True, exist_ok=True)
    if not prompt.exists():
        prompt.write_text(draft_prompt(rid), encoding="utf-8")
        print(f"wrote {prompt.relative_to(ROOT)} (DRAFT)")
    else:
        print(f"kept  {prompt.relative_to(ROOT)}")
    sketch = paint_room.sketch_path(rid)
    if not sketch.exists():
        sketch.write_text(json.dumps(draft_sketch(rid), indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {sketch.relative_to(ROOT)} (STARTER)")
    else:
        print(f"kept  {sketch.relative_to(ROOT)}")


def cmd_sketch(args) -> None:
    sketch = paint_room.sketch_path(args.room)
    if sketch.exists() and not args.force:
        print(f"kept {sketch.relative_to(ROOT)} (--force replaces it with a starter derived from the blocking)")
    else:
        paint_room.PROMPTS.mkdir(parents=True, exist_ok=True)
        sketch.write_text(json.dumps(draft_sketch(args.room), indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {sketch.relative_to(ROOT)}")
    write_guide(args.room)
    paint_room.render_sketch(args.room)
    natural_review(args.room, paint_room.LAYOUT / f"{args.room}_sketch.png")


def run_check(room_id: str, strict: bool = False) -> int:
    return check_blocking.main([room_id] + (["--strict"] if strict else []))


def masters_of(room_id: str) -> list[Path]:
    return sorted(paint_room.MASTERS.glob(f"{room_id}_v*.png"), key=lambda p: int(p.stem.rsplit("_v", 1)[1])
                  if p.stem.rsplit("_v", 1)[1].isdigit() else 0)


def paid_attempts(room_id: str) -> int:
    n = 0
    for png in masters_of(room_id):
        meta = png.with_suffix(".json")
        if not meta.exists():
            continue
        info = json.loads(meta.read_text(encoding="utf-8"))
        # Whole-picture attempts count (paint, derive_era); refit fix / extend repairs do not.
        if info.get("usd", 0) > 0 and info.get("kind", "paint") in ("paint", "derive"):
            n += 1
    return n


def cmd_run(args) -> None:
    rid = args.room
    if run_check(rid) != 0:
        sys.exit(f"{rid}: fix the blocking errors first (tools/check_blocking.py {rid})")
    for path in (check_blocking.blocking_path(rid), paint_room.PROMPTS / f"{rid}.txt", paint_room.sketch_path(rid)):
        if not path.exists():
            sys.exit(f"missing {path.relative_to(ROOT)} (paint_natural.py init {rid})")
        if "TODO" in path.read_text(encoding="utf-8"):
            sys.exit(f"{path.relative_to(ROOT)} still contains TODO - finish it before a paid call")
    done = paid_attempts(rid)
    if done >= args.max_attempts:
        sys.exit(f"{rid}: {done} paid attempt(s) already (limit {args.max_attempts}); repair with `refit` or raise "
                 f"--max-attempts with a reason in art/masters/bg_natural/{rid}.md")
    print(f"{rid}: paid attempt {done + 1} of max {args.max_attempts}, scope {args.scope}, budget USD {args.budget:.2f}")
    write_guide(rid)
    paint_room.render_sketch(rid)
    natural_review(rid, paint_room.LAYOUT / f"{rid}_sketch.png")
    paint_room.cmd_paint(args)
    version = paint_room.next_version(rid) - 1
    fix_sidecar(rid, version)
    if not args.no_export:
        args.version, args.quality = version, 90
        paint_room.cmd_export(args)
    print(f"\nLOOK at: art/masters/bg_natural/{rid}_v{version}.png\n"
          f"         art/review/natural/{rid}_v{version}_overlay.png and _crops.png\n"
          f"then: refit / fix if needed, foreground mask, overlays, ambient, `screens {rid}`, notes "
          f"art/masters/bg_natural/{rid}.md, `check {rid} --strict`.")


# --------------------------------------------------------------------------- foreground mask, state patches

FG_DIR = ROOT / "src" / "game" / "assets" / "fg_natural"
VARIANTS_DIR = ROOT / "src" / "game" / "assets" / "variants_natural"


def exported_painting(room_id: str) -> Image.Image:
    path = paint_room.EXPORT / f"{room_id}.webp"
    if not path.exists():
        sys.exit(f"missing {path.relative_to(ROOT)} (export the painting first)")
    return Image.open(path).convert("RGBA")


def cmd_mask(args) -> None:
    """Full-frame RGBA mask: the painting inside the spec polygons, transparent elsewhere. It is drawn above the
    actors, so use it only for things that are ALWAYS in front of every actor (a lamp post or railing at the front
    edge); things actors walk both behind and in front of are `occluders` in the blocking file (y-sorted)."""
    rid = args.room
    spec_path = paint_room.PROMPTS / f"{rid}.fg.json"
    if not spec_path.exists():
        spec_path.write_text(json.dumps({
            "note": f"{rid} foreground mask: polygons (canvas px) of painted things that are always in front of "
                    f"the actors. Run paint_natural.py mask {rid}.",
            "feather": 1.5, "polygons": [{"id": "TODO", "points": [[0, 1000], [100, 1000], [100, 1080], [0, 1080]]}]},
            indent=1), encoding="utf-8")
        sys.exit(f"wrote a template {spec_path.relative_to(ROOT)}; fill in the polygons and run again")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if "TODO" in json.dumps(spec):
        sys.exit(f"{spec_path.relative_to(ROOT)} still contains TODO")
    painting = exported_painting(rid)
    alpha = Image.new("L", painting.size, 0)
    d = ImageDraw.Draw(alpha)
    for poly in spec["polygons"]:
        d.polygon([tuple(p) for p in poly["points"]], fill=255)
    if spec.get("feather"):
        alpha = alpha.filter(ImageFilter.GaussianBlur(float(spec["feather"])))
    mask = painting.copy()
    mask.putalpha(alpha)
    dim = painting.convert("RGB").point(lambda v: v // 3).convert("RGBA")
    preview = Image.alpha_composite(dim, mask)
    review_dir = ART / "review" / "natural"
    review_dir.mkdir(parents=True, exist_ok=True)
    preview.convert("RGB").save(review_dir / f"{rid}_fg_preview.png")
    print(f"preview art/review/natural/{rid}_fg_preview.png (bright = drawn in front of every actor)")
    if args.preview_only:
        return
    FG_DIR.mkdir(parents=True, exist_ok=True)
    out = FG_DIR / f"{rid}.webp"
    mask.save(out, "WEBP", quality=95, alpha_quality=100, method=6)
    print(f"wrote {out.relative_to(ROOT)} (convention path: the blocking needs no foreground_mask key)")


def cmd_patch(args) -> None:
    """Cut a state patch (or a full-frame variant overlay with --full) from a master version of the room."""
    rid = args.room
    master = paint_room.MASTERS / f"{rid}_v{args.source}.png"
    if not master.exists():
        sys.exit(f"missing {master.relative_to(ROOT)}")
    frame = paint_room.fit_to_frame(Image.open(master).convert("RGB")).convert("RGBA")
    x, y, w, h = args.box
    alpha = Image.new("L", frame.size, 0)
    f = args.feather
    ImageDraw.Draw(alpha).rectangle([x + f, y + f, x + w - f, y + h - f], fill=255)
    if f:
        alpha = alpha.filter(ImageFilter.GaussianBlur(f / 2))
    frame.putalpha(alpha)
    VARIANTS_DIR.mkdir(parents=True, exist_ok=True)
    out = VARIANTS_DIR / f"{rid}_{args.name}.webp"
    if args.full:
        piece, at = frame, (0, 0)
        snippet = {"variant_layers": {"<game.json visual_variant_layers asset>": f"variants_natural/{out.name}"}}
    else:
        piece, at = frame.crop((x, y, x + w, y + h)), (x, y)
        snippet = {"state_patches": [{"texture": f"variants_natural/{out.name}", "pos": [x, y],
                                      "after": ["<action id>"], "until": []}]}
    piece.save(out, "WEBP", quality=95, alpha_quality=100, method=6)
    base = exported_painting(rid)
    preview = base.copy()
    preview.alpha_composite(piece, at)
    ImageDraw.Draw(preview).rectangle([x, y, x + w, y + h], outline=(255, 0, 255, 255), width=2)
    half = (base.width // 2, base.height // 2)
    side = Image.new("RGB", (base.width, base.height // 2))
    side.paste(base.convert("RGB").resize(half), (0, 0))
    side.paste(preview.convert("RGB").resize(half), (half[0], 0))
    review_dir = ART / "review" / "natural"
    review_dir.mkdir(parents=True, exist_ok=True)
    side.save(review_dir / f"{rid}_{args.name}_preview.png")
    print(f"wrote {out.relative_to(ROOT)}; preview art/review/natural/{rid}_{args.name}_preview.png "
          f"(left: exported painting, right: with the patch)")
    print(f"add to src/game/data/blocking/{rid}.json:\n{json.dumps(snippet, indent=1)}")


# --------------------------------------------------------------------------- Godot

class ImportLock:
    """Serialises Godot imports of parallel painters (one shared .godot/ cache). A stale lock (> 15 min) is broken."""

    def __enter__(self):
        IMPORT_LOCK.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + 1800
        while True:
            try:
                self.fd = os.open(IMPORT_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, f"{os.getpid()} {time.ctime()}".encode())
                return self
            except FileExistsError:
                try:
                    if time.time() - IMPORT_LOCK.stat().st_mtime > 900:
                        IMPORT_LOCK.unlink()
                        continue
                except OSError:
                    pass
                if time.time() > deadline:
                    sys.exit(f"{IMPORT_LOCK} held for 30 min - check for a hung Godot import")
                time.sleep(2)

    def __exit__(self, *exc):
        os.close(self.fd)
        try:
            IMPORT_LOCK.unlink()
        except OSError:
            pass


def godot(args: list[str], timeout: int = 600) -> int:
    cmd = [str(GODOT), "--path", str(GAME_DIR)] + args
    print("godot " + " ".join(args))
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout)
    for line in proc.stdout.splitlines():
        if line.startswith("HARNESS") or "ERROR" in line or "WARNING: Room" in line:
            print("  " + line)
    return proc.returncode


def cmd_import(args) -> None:
    with ImportLock():
        code = godot(["--headless", "--import"], timeout=1200)
    print(f"import exit {code}")


def cmd_screens(args) -> None:
    rid = args.room
    out = SCREENS / rid
    out.mkdir(parents=True, exist_ok=True)
    if not args.no_import:
        with ImportLock():
            godot(["--headless", "--import"], timeout=1200)
    state = []
    if args.replay:
        state += ["--replay", str(args.replay)]
    for act in args.act or []:
        state += ["--act", act]
    tag = args.tag or ("state" if state else "entry")
    base = ["--resolution", "1920x1080", "--", "--blocking", "natural"] + state + ["--room", rid, "--fast-text",
                                                                                 "--skip-lines"]
    shots = [
        (base + ["--labels", "--wait", "800", "--screenshot", str(out / f"{tag}_labels.png")]),
        (base + ["--wait", "800", "--screenshot", str(out / f"{tag}_clean.png")]),
        (base + ["--wait", "1500", "--frames", str(args.frames), "--interval", str(args.interval),
                 "--screenshot", str(out / f"{tag}_motion.png")]),
    ]
    codes = [godot(s, timeout=300) for s in shots]
    print(f"screens -> {out.relative_to(ROOT)} (exit codes {codes}); LOOK at every image")


# --------------------------------------------------------------------------- main

def main() -> None:
    install()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("init", "check", "prompt", "sketch"):
        p = sub.add_parser(name)
        p.add_argument("room")
        if name == "check":
            p.add_argument("--strict", action="store_true")
        if name == "prompt":
            p.add_argument("--mode", choices=["auto", "sketch", "guide"], default="auto")
        if name == "sketch":
            p.add_argument("--force", action="store_true")
    for name in ("run", "paint"):
        p = sub.add_parser(name)
        p.add_argument("room")
        p.add_argument("--mode", choices=["auto", "sketch", "guide"], default="sketch")
        p.add_argument("--seed", type=int)
        p.add_argument("--budget", type=float, required=True, help="USD cap of the scope (0.15 per call)")
        p.add_argument("--scope", help="spend-log prefix (default bg_natural/<room>/)")
        if name == "run":
            p.add_argument("--no-export", action="store_true")
            p.add_argument("--max-attempts", type=int, default=MAX_ATTEMPTS)
    p = sub.add_parser("review")
    p.add_argument("room")
    p.add_argument("version")
    p.add_argument("--grid", type=int, nargs=4)
    p = sub.add_parser("export")
    p.add_argument("room")
    p.add_argument("version", type=int)
    p.add_argument("--quality", type=int, default=90)
    p = sub.add_parser("refit", help="refit_room.py fit|extend|fix on the natural masters (pass its arguments)")
    p.add_argument("rest", nargs=argparse.REMAINDER)
    p = sub.add_parser("mask")
    p.add_argument("room")
    p.add_argument("--preview-only", action="store_true")
    p = sub.add_parser("patch")
    p.add_argument("room")
    p.add_argument("name", help="file name part: variants_natural/<room>_<name>.webp")
    p.add_argument("--from", dest="source", type=int, required=True, help="master version that shows the state")
    p.add_argument("--box", type=int, nargs=4, required=True, metavar=("X", "Y", "W", "H"))
    p.add_argument("--full", action="store_true", help="full-frame overlay (variant_layers) instead of a patch")
    p.add_argument("--feather", type=int, default=6)
    sub.add_parser("import")
    p = sub.add_parser("screens")
    p.add_argument("room")
    p.add_argument("--replay", type=int, help="walkthrough steps replayed before the jump (state)")
    p.add_argument("--act", action="append", help="action id performed before the shots (repeatable)")
    p.add_argument("--tag", help="file name prefix (default entry / state)")
    p.add_argument("--frames", type=int, default=6)
    p.add_argument("--interval", type=int, default=400)
    p.add_argument("--no-import", action="store_true")
    args = ap.parse_args()
    if getattr(args, "scope", "x") is None:
        args.scope = f"bg_natural/{args.room}/"
    if args.cmd == "init":
        cmd_init(args)
    elif args.cmd == "check":
        sys.exit(run_check(args.room, args.strict))
    elif args.cmd == "sketch":
        cmd_sketch(args)
    elif args.cmd == "prompt":
        write_guide(args.room)
        paint_room.cmd_prompt(args)
        natural_review(args.room, paint_room.LAYOUT / f"{args.room}_sketch.png")
    elif args.cmd == "run":
        cmd_run(args)
    elif args.cmd == "paint":
        write_guide(args.room)
        paint_room.cmd_paint(args)
        fix_sidecar(args.room)
    elif args.cmd == "review":
        if args.grid:
            review_room.grid_crop(args.room, args.version, tuple(args.grid))
        else:
            natural_review(args.room, args.version)
    elif args.cmd == "export":
        paint_room.cmd_export(args)
    elif args.cmd == "refit":
        import refit_room
        rest = list(args.rest)
        if len(rest) >= 2 and rest[0] in ("extend", "fix") and "--scope" not in rest:
            rest += ["--scope", f"bg_natural/{rest[1]}/"]   # per-room budget scope
        sys.argv = ["refit_room.py"] + rest
        refit_room.main()
    elif args.cmd == "mask":
        cmd_mask(args)
    elif args.cmd == "patch":
        cmd_patch(args)
    elif args.cmd == "import":
        cmd_import(args)
    elif args.cmd == "screens":
        cmd_screens(args)


if __name__ == "__main__":
    main()
