"""Validate natural re-blocking files (src/game/data/blocking/<room>.json, docs/reblock/README.md,
art/tools/PAINTING.md "Natural mode").

A blocking file replaces the presentation of a room (hotspot / exit rects, interaction points, label anchors, walk
polygon, NPC staging, perspective range, painting, foreground mask, occluders, state overlays, ambient layers, audio);
ids and conditions stay in game.json. The game applies it per room when natural blocking is enabled (project setting
last_bell/presentation/blocking = "natural" or --blocking natural); rooms without a file keep the template.

Checks on the EFFECTIVE room (game.json merged with the blocking file, exactly as src/game/scripts/World/Room.cs does):
  errors   - unknown room / hotspot / exit / NPC / action ids, unknown keys' malformed values
           - every hotspot and exit rect at least 44x44 px and at least 44x44 px of it on screen
           - walk polygon: >= 3 points, simple (no self-intersection), inside the 1920x1080 frame
           - exit "side" one of left / right / up / down, exit "arrival" (where the hero appears when he comes in through
             it, World/ExitSides.cs) inside the walk polygon
           - every hotspot and exit interaction point inside the walk polygon (exits reachable; the polygon is one
             connected area, so every inside point is reachable from the spawn), spawn inside
           - label anchors on screen
           - NPC feet on walkable floor (12 px tolerance) unless the staging gives an explicit scale or a sill variant
           - no rect fully hidden behind others in the game's hit order (NPCs, props later-on-top, exits)
           - NPC staging: the variant resolves in the actor's actor.json (standing / seated / behind_counter /
             window_bust / window_bust_glass or a variant name) and its sheets exist; bust variants have a sill_y
           - files: background, foreground mask, occluder textures and variant overlays exist and are 1920x1080
             (patches: inside the frame); state patch textures exist; the ambient file parses, its layer types are
             known and every texture / sheet / mask it names exists with a valid Godot .import (not valid=false); audio
             sounds exist in data/audio/ambience.json
  warnings - label boxes overlapping each other or pushed by the screen clamp, label far from its rect,
             two exits to different places on the same edge closer than 360 px (two doors / paths into the picture: 200 px), an edge exit whose
             return exit in the target sits on the same edge (walking continuity, docs/navigation/EXITS.md),
             exit rect far from its interaction point, NPC approach point not walkable, NPC scale far from the
             room perspective at its feet, rect mostly hidden, staging that differs from docs/DECISIONS.md item 2,
             ambient sprites cut from the template painting, camera-family rooms with a different perspective or
             different natural "anchors" (optional {name: [x, y]} override of game.json landmark_layouts)
  --strict - the room is finished: these become errors (unless "waive": {"<key>": "reason"} in the file says why):
             painting missing (key "background"), ambient file missing or < 3 layers ("ambient"), a visual_variant_layers
             asset of the room without a natural overlay ("variant:<asset>"), a hotspot with visible_after / hide_after
             without a state patch for that action ("patch:<hotspot id>"), an NPC without staging ("staging:<npc id>")

Usage: python tools/check_blocking.py                 (all files in src/game/data/blocking/)
       python tools/check_blocking.py S03 S05         (these rooms' blocking files)
       python tools/check_blocking.py --strict S05    (the room is done: missing art becomes an error)
       python tools/check_blocking.py --template S03  (check game.json's template geometry instead, for comparison)
Exit code 1 when any error is found.
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "src" / "game" / "data" / "game.json"
BLOCKING = ROOT / "src" / "game" / "data" / "blocking"
ASSETS = ROOT / "src" / "game" / "assets"
OVERRIDES = ROOT / "src" / "game" / "data" / "art_overrides.json"

FRAME = (1920, 1080)
MIN_RECT = 44
NPC_APPROACH_GAP = 95          # Room.NpcApproachGap
LABEL_FONT_PX = 22             # HotspotLabelLayer (normal contrast)
LABEL_CHAR_PX = 12.0           # average glyph width of the fallback font at 22 px (estimate)
FEET_TOLERANCE = 12
TOP_LEVEL_KEYS = {"version", "room", "status", "note", "notes", "background", "walk_polygon", "walk_band", "actor_scale",
                  "spawn", "hotspots", "exits", "npcs", "foreground_mask", "ambient", "state_patches", "reasons",
                  "occluders", "variant_layers", "audio", "waive", "family_base", "anchors", "guests", "time_node"}
TARGET_KEYS = {"rect", "interaction_point", "label_anchor", "reason", "note", "side", "arrival"}
# Exit directions (World/ExitSides.cs, docs/navigation/EXITS.md): named in a blocking or derived from the zone.
EXIT_SIDES = {"left", "right", "up", "down"}
EXIT_CROWD_PX = 360           # two exits to different places on the same edge closer than this: warning
EXIT_CROWD_UP_PX = 200        # the same for two doors / paths into the picture
NPC_KEYS = {"feet", "scale", "variant", "sill_y", "offset_x", "facing", "z", "reason", "note", "approach_gap"}
GUEST_KEYS = {"character", "enter", "stand", "variant", "facing", "delay", "reason", "note"}
TIME_NODE_KEYS = {"rect", "interaction_point", "hotspot", "reason", "note"}
DATA = ROOT / "src" / "game" / "data"
AMBIENT_ASSETS = ASSETS / "ambient"
AMBIENCE = DATA / "audio" / "ambience.json"
MUSIC = DATA / "audio" / "music.json"
ACTORS = ASSETS / "actors"
# src/game/scripts/Living/Ambient/AmbientBuilder.cs Types
AMBIENT_TYPES = {"particles", "sway", "water", "sprite_loop", "cutout", "tween_path", "flicker", "clouds", "rotor", "critters"}
MIN_AMBIENT_LAYERS = 3        # design-doc/ART_DIRECTION.md section 5
GENERIC_STAGING = ("standing", "seated", "behind_counter", "window_bust", "window_bust_glass")
# docs/DECISIONS.md item 2 (accepted 2026-10-05) plus the existing window busts and decision 7:
# hotspot id -> expected staging class ("standing", "seated", "bust" = counter / table / window cut, or a variant name)
EXPECTED_STAGING = {
    "S03.ELA": "standing", "S13.TONO": "seated", "S64.TONO82": "seated", "S37.VERA60": "seated",
    "S18.ZITA": "bust", "S25.TRH": "bust", "S26.MILADA": "bust", "S33.POSTA": "bust", "S35.SKLAD": "bust",
    "S62.RUZENA": "bust", "S65.MARTA82": "bust", "S43.TAMARA": "bust", "S44.BORIS": "bust", "S49.VIKTOR": "bust",
    "S46.SARA": "bust", "S56.TONO20": "bust", "S64.OTO82": "bust", "S04.DANA": "bust", "S06.MIRA20": "bust",
    "S54.JANA20": "laptop",
}


# --------------------------------------------------------------------------- data

def load_game() -> dict:
    """game.json with the content overlays (src/game/data/content_ext, tools/content_ext.py) applied, as the game
    loads it: the travel overlay adds and removes exits (e.g. the 2020 bus S07 <-> S51)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import content_ext  # noqa: E402
    overlay = content_ext.load_effective_game(GAME)
    if overlay.errors:
        raise SystemExit("content overlay invalid: " + "; ".join(overlay.errors[:5]))
    return overlay.game


def blocking_path(room_id: str) -> Path:
    return BLOCKING / f"{room_id}.json"


def effective_room(room: dict, blocking: dict | None) -> dict:
    """game.json room with the blocking's geometry applied (Room.cs ApplyBlocking: field by field)."""
    eff = copy.deepcopy(room)
    if not blocking:
        return eff
    hs = blocking.get("hotspots", {})
    for h in eff["hotspots"]:
        b = hs.get(h["id"])
        if not b:
            continue
        if "rect" in b:
            h["rect"] = b["rect"]
            if "label_anchor" not in b:     # a moved rect without its own anchor: default above the rect
                x, y, w, _ = b["rect"]
                h["label_anchor"] = [x + w / 2, y - 10]
        for key in ("interaction_point", "label_anchor"):
            if key in b:
                h[key] = b[key]
    ex = blocking.get("exits", {})
    for e in eff["exits"]:
        b = ex.get(e["id"])
        if not b:
            continue
        for key in ("rect", "interaction_point", "label_anchor", "side", "arrival"):
            if key in b:
                e[key] = b[key]
    if "walk_polygon" in blocking:
        eff["walk_polygon"] = blocking["walk_polygon"]
    if "spawn" in blocking:
        eff["spawn"] = blocking["spawn"]
    eff["_blocking"] = blocking
    return eff


def exit_label_anchor(e: dict) -> list[float]:
    """Room.cs: exits without an explicit anchor get one 12 px above the rect, x clamped to 80..1840."""
    if e.get("label_anchor"):
        return e["label_anchor"]
    x, y, w, _ = e["rect"]
    return [min(max(x + w / 2, 80), FRAME[0] - 80), y - 12]


def hotspot_label_anchor(h: dict) -> list[float]:
    if h.get("label_anchor"):
        return h["label_anchor"]
    x, y, w, _ = h["rect"]
    return [x + w / 2, y - 10]


def perspective(eff: dict, art_room: dict) -> tuple[float, float, float, float]:
    b = eff.get("_blocking") or {}
    ys = [p[1] for p in eff["walk_polygon"]]
    band = b.get("walk_band") or (art_room.get("walk_band") if not b else None) or [min(ys), max(ys)]
    scale = b.get("actor_scale") or (art_room.get("actor_scale") if not b else None) or [0.80, 1.00]
    return band[0], band[1], scale[0], scale[1]


def scale_at(p: tuple[float, float, float, float], y: float) -> float:
    top, bottom, s0, s1 = p
    if bottom - top < 1:
        return s1
    t = min(max((y - top) / (bottom - top), 0.0), 1.0)
    return s0 + (s1 - s0) * t


# --------------------------------------------------------------------------- geometry

def point_on_segment(p, a, b, eps=0.01) -> bool:
    (px, py), (ax, ay), (bx, by) = p, a, b
    cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
    if abs(cross) > eps * max(1.0, abs(bx - ax) + abs(by - ay)):
        return False
    return min(ax, bx) - eps <= px <= max(ax, bx) + eps and min(ay, by) - eps <= py <= max(ay, by) + eps


def inside(poly, p) -> bool:
    if len(poly) < 3:
        return False
    if any(point_on_segment(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))):
        return True
    x, y = p
    result = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            result = not result
        j = i
    return result


def distance_to_polygon(poly, p) -> float:
    best = float("inf")
    px, py = p
    for i in range(len(poly)):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % len(poly)]
        dx, dy = bx - ax, by - ay
        t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        cx, cy = ax + t * dx, ay + t * dy
        best = min(best, ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5)
    return best


def segments_cross(a, b, c, d) -> bool:
    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if o1 != o2 and o3 != o4:
        return True
    return (o1 == 0 and point_on_segment(c, a, b)) or (o2 == 0 and point_on_segment(d, a, b)) or \
           (o3 == 0 and point_on_segment(a, c, d)) or (o4 == 0 and point_on_segment(b, c, d))


def is_simple(poly) -> bool:
    n = len(poly)
    for i in range(n):
        for j in range(i + 1, n):
            if abs(i - j) <= 1 or (i == 0 and j == n - 1):
                continue
            if segments_cross(poly[i], poly[(i + 1) % n], poly[j], poly[(j + 1) % n]):
                return False
    return True


def rect_box(r):
    x, y, w, h = r
    return x, y, x + w, y + h


def overlap(a, b) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def visible_fraction(rect, covers, step: int = 2) -> float:
    """Share of the rect's on-screen area not covered by the rects earlier in the hit order."""
    x0, y0, x1, y1 = rect_box(rect)
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(FRAME[0], x1), min(FRAME[1], y1)
    boxes = [rect_box(c) for c in covers]
    total = free = 0
    y = y0 + step / 2
    while y < y1:
        x = x0 + step / 2
        while x < x1:
            total += 1
            if not any(b[0] <= x < b[2] and b[1] <= y < b[3] for b in boxes):
                free += 1
            x += step
        y += step
    return free / total if total else 0.0


# --------------------------------------------------------------------------- checks

class Report:
    def __init__(self, name: str):
        self.name, self.errors, self.warnings = name, [], []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def check_schema(rep: Report, room: dict, blocking: dict) -> None:
    hotspots = {h["id"]: h for h in room["hotspots"]}
    exits = {e["id"] for e in room["exits"]}
    if blocking.get("room") != room["id"]:
        rep.error(f"'room' is {blocking.get('room')!r}, expected {room['id']!r}")
    for key in blocking:
        if key not in TOP_LEVEL_KEYS:
            rep.warn(f"unknown top-level key {key!r} (ignored by the game)")
    for hid, b in blocking.get("hotspots", {}).items():
        if hid not in hotspots:
            rep.error(f"hotspot {hid!r} is not in game.json room {room['id']}")
        check_target_values(rep, hid, b)
    for eid, b in blocking.get("exits", {}).items():
        if eid not in exits:
            rep.error(f"exit {eid!r} is not in game.json room {room['id']}")
        check_target_values(rep, eid, b)
    for nid, b in blocking.get("npcs", {}).items():
        if nid not in hotspots or hotspots[nid]["kind"] != "npc":
            rep.error(f"npcs.{nid}: not an NPC hotspot of room {room['id']}")
            continue
        for key in b:
            if key not in NPC_KEYS:
                rep.warn(f"npcs.{nid}: unknown key {key!r}")
        if "feet" in b and not is_vec(b["feet"]):
            rep.error(f"npcs.{nid}.feet must be [x, y]")
        if "scale" in b and not (isinstance(b["scale"], (int, float)) and 0.1 <= b["scale"] <= 1.5):
            rep.error(f"npcs.{nid}.scale must be a number in 0.1..1.5")
        for key in ("sill_y", "offset_x"):
            if key in b and not isinstance(b[key], (int, float)):
                rep.error(f"npcs.{nid}.{key} must be a number")
        if "sill_y" in b and isinstance(b["sill_y"], (int, float)) and not 0 <= b["sill_y"] <= FRAME[1]:
            rep.error(f"npcs.{nid}.sill_y {b['sill_y']} is off screen")
        if b.get("facing") not in (None, "left", "right"):
            rep.error(f"npcs.{nid}.facing must be 'left' or 'right'")
        if b.get("z", "auto") not in ("auto", "back", "behind", "front"):
            rep.error(f"npcs.{nid}.z must be 'auto', 'back' or 'front'")
        check_staging(rep, nid, hotspots[nid].get("character_id"), b)
    anchors = blocking.get("anchors")
    if anchors is not None:
        fam = room.get("camera_family")
        known = load_game().get("landmark_layouts", {}).get(fam) or {}
        if not isinstance(anchors, dict) or not all(is_vec(v) for v in anchors.values()):
            rep.error("anchors must be {name: [x, y]} (natural positions of the landmark_layouts anchors)")
        else:
            for name in anchors:
                if name not in known:
                    rep.error(f"anchors.{name}: not a landmark_layouts anchor of {fam} ({', '.join(known) or 'none'})")
            for name in known:
                if name not in anchors:
                    rep.warn(f"anchors: {fam} anchor {name!r} keeps its template position {known[name]}")
    for key in ("walk_band", "actor_scale", "spawn"):
        if key in blocking and not is_vec(blocking[key]):
            rep.error(f"{key} must be [a, b]")
    if "actor_scale" in blocking and is_vec(blocking["actor_scale"]):
        s0, s1 = blocking["actor_scale"]
        if not (0.2 <= s0 <= 1.3 and 0.2 <= s1 <= 1.3):
            rep.error(f"actor_scale {blocking['actor_scale']} outside 0.2..1.3")
        elif s0 > s1:
            rep.warn(f"actor_scale {blocking['actor_scale']}: actors get smaller towards the front")
    actions = ACTION_IDS()
    for patch in blocking.get("state_patches", []):
        tex = patch.get("texture")
        if not tex or not (ASSETS / tex).exists():
            rep.error(f"state patch texture {tex!r} does not exist")
        elif is_vec(patch.get("pos")):
            check_image(rep, f"state patch {tex}", ASSETS / tex, patch_at=patch["pos"])
        if not is_vec(patch.get("pos")):
            rep.error(f"state patch {tex!r}: pos must be [x, y]")
        for key in ("after", "until"):
            for aid in patch.get(key, []):
                if aid not in actions:
                    rep.error(f"state patch {tex!r}: {key} action {aid!r} is not in game.json")


def check_guests_and_node(rep: Report, room: dict, blocking: dict, eff: dict) -> None:
    """Guest speakers (ISSUES PT-S18) and the painted time-node clock (PT-F10), World/GuestStage.cs and Room.cs."""
    poly = [tuple(p) for p in eff["walk_polygon"]]
    actions = {a["id"]: a for a in load_game().get("actions", [])}
    chars = {c["id"] for c in load_game().get("characters", [])}
    npc_chars = {h.get("character_id") for h in room["hotspots"] if h["kind"] == "npc"}
    for aid, guests in (blocking.get("guests") or {}).items():
        action = actions.get(aid)
        if action is None or action["room"] != room["id"]:
            rep.error(f"guests.{aid}: not an action of room {room['id']}")
            continue
        speakers = {line["speaker"] for line in action.get("lines", [])}
        if not isinstance(guests, list) or not guests:
            rep.error(f"guests.{aid} must be a non-empty list")
            continue
        for i, g in enumerate(guests):
            ident = f"guests.{aid}[{i}]"
            for key in g:
                if key not in GUEST_KEYS:
                    rep.warn(f"{ident}: unknown key {key!r}")
            cid = g.get("character")
            if cid not in chars:
                rep.error(f"{ident}: character {cid!r} is not in game.json characters")
                continue
            if cid not in speakers:
                rep.error(f"{ident}: {cid} speaks no line of {aid}")
            if cid in npc_chars:
                rep.error(f"{ident}: {cid} is a permanent NPC of {room['id']} (never moved; it speaks from its place)")
            for key in ("enter", "stand"):
                if not is_vec(g.get(key)):
                    rep.error(f"{ident}.{key} must be [x, y]")
            if is_vec(g.get("stand")) and not (inside(poly, tuple(g["stand"])) or distance_to_polygon(poly, tuple(g["stand"])) <= FEET_TOLERANCE):
                rep.error(f"{ident}.stand {g['stand']} is not on walkable floor")
            if is_vec(g.get("enter")) and not (-200 <= g["enter"][0] <= FRAME[0] + 200 and 0 <= g["enter"][1] <= FRAME[1] + 200):
                rep.error(f"{ident}.enter {g['enter']} is too far off screen")
            if g.get("facing") not in (None, "left", "right"):
                rep.error(f"{ident}.facing must be 'left' or 'right'")
            manifest = actor_manifest(cid)
            if manifest is None:
                rep.warn(f"{ident}: no sprite data for {cid} (placeholder figure)")
                continue
            ok, variant = resolve_staging(manifest, g.get("variant"))
            if not ok:
                rep.error(f"{ident}.variant {g.get('variant')!r} does not exist for {cid}")
                continue
            anims = dict(manifest.get("animations") or {})
            if variant:
                anims.update((manifest.get("variants") or {}).get(variant, {}).get("animations") or {})
            if "walk_right" not in anims:
                rep.warn(f"{ident}: {cid} has no walk_right animation (the guest glides in)")
            for name in variant_sheets(manifest, variant):
                sheet = (manifest.get("sheets") or {}).get(name)
                if not sheet or not (ACTORS / cid / sheet.get("file", "")).exists():
                    rep.error(f"{ident}: {cid} sheet {name!r} is missing")
    node = blocking.get("time_node")
    if node is not None:
        for key in node:
            if key not in TIME_NODE_KEYS:
                rep.warn(f"time_node: unknown key {key!r}")
        anchors = {n["room"] for n in load_game().get("anchor_nodes", [])}
        if room["id"] not in anchors:
            rep.error(f"time_node: {room['id']} is not an anchor node (game.json anchor_nodes)")
        hid = node.get("hotspot")
        if hid is not None:
            if hid not in {h["id"] for h in room["hotspots"]}:
                rep.error(f"time_node.hotspot {hid!r} is not a hotspot of {room['id']}")
        else:
            r = node.get("rect")
            if not (isinstance(r, list) and len(r) == 4):
                rep.error("time_node needs a rect [x, y, w, h] or a hotspot id")
            else:
                if r[2] < MIN_RECT or r[3] < MIN_RECT:
                    rep.error(f"time_node rect {r} smaller than {MIN_RECT}x{MIN_RECT}")
                if r[0] < 0 or r[1] < 0 or r[0] + r[2] > FRAME[0] or r[1] + r[3] > FRAME[1]:
                    rep.error(f"time_node rect {r} is not on screen")
        ip = node.get("interaction_point")
        if ip is not None and (not is_vec(ip) or not (inside(poly, tuple(ip)) or distance_to_polygon(poly, tuple(ip)) <= 1)):
            rep.error(f"time_node.interaction_point {ip} is not on walkable floor")


def is_vec(v) -> bool:
    return isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v)


def check_target_values(rep: Report, ident: str, b: dict) -> None:
    for key in b:
        if key not in TARGET_KEYS:
            rep.warn(f"{ident}: unknown key {key!r}")
    if "rect" in b and not (isinstance(b["rect"], list) and len(b["rect"]) == 4
                            and all(isinstance(x, (int, float)) for x in b["rect"])):
        rep.error(f"{ident}: rect must be [x, y, w, h]")
    for key in ("interaction_point", "label_anchor", "arrival"):
        if key in b and not is_vec(b[key]):
            rep.error(f"{ident}: {key} must be [x, y]")
    if "side" in b and b["side"] not in EXIT_SIDES:
        rep.error(f"{ident}: side must be one of {sorted(EXIT_SIDES)}")


def exit_side(e: dict) -> str:
    """ExitSides.FromRect / the blocking's named side: left / right edge zones, else up (into the picture) or down."""
    if e.get("side") in EXIT_SIDES:
        return e["side"]
    x, y, w, h = e["rect"]
    cx, cy = x + w / 2, y + h / 2
    if cx < FRAME[0] * 0.16:
        return "left"
    if cx > FRAME[0] * 0.84:
        return "right"
    return "down" if cy > FRAME[1] * 0.80 else "up"


def check_room(rep: Report, eff: dict, art_room: dict) -> None:
    poly = [tuple(p) for p in eff["walk_polygon"]]
    fw, fh = FRAME

    # Walk polygon.
    if len(poly) < 3:
        rep.error("walk polygon has fewer than 3 points")
        return
    if not is_simple(poly):
        rep.error("walk polygon intersects itself")
    for p in poly:
        if not (0 <= p[0] <= fw and 0 <= p[1] <= fh):
            rep.error(f"walk polygon point {list(p)} is off screen")
    spawn = eff.get("spawn")
    if spawn and not inside(poly, spawn):
        rep.error(f"spawn {spawn} is outside the walk polygon")

    targets = []   # (id, kind, rect, ip, label anchor, name)
    for h in eff["hotspots"]:
        targets.append((h["id"], "npc" if h["kind"] == "npc" else "prop", h["rect"], h.get("interaction_point"),
                        hotspot_label_anchor(h), h.get("name", "")))
    for e in eff["exits"]:
        targets.append((e["id"], "exit", e["rect"], e.get("interaction_point"), exit_label_anchor(e), e.get("label", "")))

    # Rects: size and on-screen part.
    for ident, kind, rect, ip, anchor, name in targets:
        x, y, w, h = rect
        vw = min(x + w, fw) - max(x, 0)
        vh = min(y + h, fh) - max(y, 0)
        if w < MIN_RECT or h < MIN_RECT:
            rep.error(f"{ident}: rect {w}x{h} is smaller than {MIN_RECT}x{MIN_RECT}")
        elif vw < MIN_RECT or vh < MIN_RECT:
            rep.error(f"{ident}: only {max(vw, 0)}x{max(vh, 0)} px of the rect are on screen")

    # Interaction points (exits reachable: the polygon is one connected area, so inside = reachable from the spawn).
    for ident, kind, rect, ip, anchor, name in targets:
        if not ip:
            rep.warn(f"{ident}: no interaction point (the game walks to the rect centre)")
            ip = [rect[0] + rect[2] / 2, rect[1] + rect[3] / 2]
        if not inside(poly, ip):
            rep.error(f"{ident}: interaction point {ip} is outside the walk polygon "
                      f"({distance_to_polygon(poly, ip):.0f} px away)")
        if kind == "exit":
            x0, y0, x1, y1 = rect_box(rect)
            dx = max(x0 - ip[0], 0, ip[0] - x1)
            dy = max(y0 - ip[1], 0, ip[1] - y1)
            if (dx * dx + dy * dy) ** 0.5 > 120:
                rep.warn(f"{ident}: interaction point {ip} is {(dx * dx + dy * dy) ** 0.5:.0f} px from its rect")
        if kind == "npc":
            x0, _, x1, _ = rect_box(rect)
            gap = ((eff.get("_blocking") or {}).get("npcs", {}).get(ident) or {}).get("approach_gap", NPC_APPROACH_GAP)
            if x0 - gap / 2 <= ip[0] <= x1 + gap / 2:
                sides = [(x0 - gap, ip[1]), (x1 + gap, ip[1])]
                if not any(inside(poly, s) for s in sides):
                    rep.warn(f"{ident}: neither approach point {[list(s) for s in sides]} is walkable; the hero "
                             f"stands on the interaction point in front of the NPC")

    # Exit layout (docs/navigation/EXITS.md): the arrival point is walkable; two exits to different places do not crowd
    # on the same side of the picture.
    exits_eff = eff["exits"]
    for e in exits_eff:
        if e.get("arrival") and is_vec(e["arrival"]) and not inside(poly, e["arrival"]):
            rep.error(f"{e['id']}: arrival {e['arrival']} is outside the walk polygon")
    for i, a in enumerate(exits_eff):
        for b in exits_eff[i + 1:]:
            if a["to"] == b["to"] or exit_side(a) != exit_side(b):
                continue
            ca = (a["rect"][0] + a["rect"][2] / 2, a["rect"][1] + a["rect"][3] / 2)
            cb = (b["rect"][0] + b["rect"][2] / 2, b["rect"][1] + b["rect"][3] / 2)
            d = ((ca[0] - cb[0]) ** 2 + (ca[1] - cb[1]) ** 2) ** 0.5
            # Doors, gates and paths into the picture are separate painted ways; edge exits only read as one place.
            if d < (EXIT_CROWD_UP_PX if exit_side(a) == "up" else EXIT_CROWD_PX):
                rep.warn(f"exits {a['id']} and {b['id']} both lead {exit_side(a)} and their zones are only {d:.0f} px "
                         f"apart (separate them or name a side)")

    # Labels on screen, not overlapping, near their rect.
    boxes = []
    for ident, kind, rect, ip, anchor, name in targets:
        ax, ay = anchor
        if not (0 <= ax <= fw and 0 <= ay <= fh):
            rep.error(f"{ident}: label anchor {anchor} is off screen")
            continue
        tw = len(name) * LABEL_CHAR_PX
        th = LABEL_FONT_PX * 1.15
        px = min(max(ax - tw / 2, 8), fw - tw - 8)
        py = min(max(ay, th + 8), fh - 8)
        if abs(px - (ax - tw / 2)) > 1 or abs(py - ay) > 1:
            rep.warn(f"{ident}: label '{name}' at {anchor} is pushed back on screen by the clamp")
        box = (px - 10 - (14 if kind == "exit" else 0), py - th - 2, px + tw + 10 + (14 if kind == "exit" else 0), py + 10)
        boxes.append((ident, box))
        x0, y0, x1, y1 = rect_box(rect)
        dx = max(x0 - ax, 0, ax - x1)
        dy = max(y0 - ay, 0, ay - y1)
        if (dx * dx + dy * dy) ** 0.5 > 150:
            rep.warn(f"{ident}: label anchor {anchor} is {(dx * dx + dy * dy) ** 0.5:.0f} px from its rect")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if overlap(boxes[i][1], boxes[j][1]):
                rep.warn(f"labels of {boxes[i][0]} and {boxes[j][0]} overlap")

    # NPC feet on walkable floor, scale vs perspective.
    blocking = eff.get("_blocking") or {}
    persp = perspective(eff, art_room)
    nudges = {} if blocking else art_room.get("npc_feet", {})
    for h in eff["hotspots"]:
        if h["kind"] != "npc":
            continue
        x, y, w, hh = h["rect"]
        staging = blocking.get("npcs", {}).get(h["id"], {})
        feet = staging.get("feet") or [x + w / 2 + nudges.get(h["id"], [0, 0])[0], y + hh + nudges.get(h["id"], [0, 0])[1]]
        if not (0 <= feet[0] <= fw and 0 <= feet[1] <= fh):
            rep.error(f"{h['id']}: NPC feet {feet} are off screen")
        elif not inside(poly, feet):
            d = distance_to_polygon(poly, feet)
            # A natural staging may put an NPC off the hero's floor (behind a counter, on a bench, inside a window)
            # when it fixes the scale or stands the bust on a sill: the perspective is not extrapolated then.
            staged = blocking and ("scale" in staging or "sill_y" in staging)
            if d > FEET_TOLERANCE and not staged:
                rep.error(f"{h['id']}: NPC feet {feet} are {d:.0f} px off the walkable floor "
                          f"(move them onto the floor, or stage the NPC with an explicit scale / sill_y)")
            elif d <= FEET_TOLERANCE:
                rep.warn(f"{h['id']}: NPC feet {feet} are {d:.0f} px off the walkable floor")
        if "sill_y" in staging and isinstance(staging["sill_y"], (int, float)) and staging["sill_y"] > feet[1] + 1:
            rep.warn(f"{h['id']}: sill_y {staging['sill_y']} is below the feet y {feet[1]} (feet = the floor point "
                     f"under the bust, used for depth sorting)")
        if "scale" in staging and abs(staging["scale"] - scale_at(persp, feet[1])) > 0.1:
            rep.warn(f"{h['id']}: NPC scale {staging['scale']} vs room perspective {scale_at(persp, feet[1]):.2f} "
                     f"at feet y {feet[1]}")

    # Hidden rects in the game's hit order: NPCs, props (later data entries on top), exits.
    npcs = [t for t in targets if t[1] == "npc"]
    props = [t for t in targets if t[1] == "prop"][::-1]
    exits = [t for t in targets if t[1] == "exit"]
    order = npcs + props + exits
    for i, t in enumerate(order):
        covers = [o[2] for o in order[:i] if overlap(rect_box(o[2]), rect_box(t[2]))]
        if not covers:
            continue
        frac = visible_fraction(t[2], covers)
        if frac <= 0.0:
            rep.error(f"{t[0]}: rect is fully hidden behind {', '.join(o[0] for o in order[:i] if o[2] in covers)}")
        elif frac < 0.4:
            rep.warn(f"{t[0]}: only {frac:.0%} of the rect is clickable (rest hidden behind earlier targets)")


# --------------------------------------------------------------------------- staging, files, ambient, audio

_cache: dict = {}


def ACTION_IDS() -> set[str]:   # noqa: N802 - cached constant
    if "actions" not in _cache:
        _cache["actions"] = {a["id"] for a in load_game().get("actions", [])}
    return _cache["actions"]


def actor_manifest(char_id: str | None) -> dict | None:
    if not char_id:
        return None
    key = "actor:" + char_id
    if key not in _cache:
        path = ACTORS / char_id / "actor.json"
        _cache[key] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return _cache[key]


def base_pose(manifest: dict) -> str:
    """The actor's base pose; "posture" may carry a note after a semicolon ("standing; variants: counter")."""
    return str(manifest.get("posture") or manifest.get("staging") or "standing").split(";")[0].strip()


def resolve_staging(manifest: dict, staging: str | None) -> tuple[bool, str | None]:
    """Same rule as ActorAnimationSet.TryResolveStaging (C#): (ok, actor.json variant or None = default sheets)."""
    if not staging or staging == "default":
        return True, None
    variants = manifest.get("variants") or {}
    pose = base_pose(manifest)
    plain = manifest.get("default_variant") is None
    pick = {
        "standing": "full" if "full" in variants else ("" if plain and pose == "standing" else None),
        "seated": "seated" if "seated" in variants else ("" if plain and pose == "seated" else None),
        "behind_counter": "counter" if "counter" in variants else ("table" if "table" in variants else None),
        "window_bust": "window" if "window" in variants else None,
        "window_bust_glass": "window_glass" if "window_glass" in variants else None,
    }.get(staging, staging if staging in variants else None)
    if pick is None:
        return False, None
    return True, (pick or None)


def variant_sheets(manifest: dict, variant: str | None) -> list[str]:
    """Sheet names the drawn animations use (variant overrides on top of the base animations)."""
    anims = dict(manifest.get("animations") or {})
    chosen = variant or manifest.get("default_variant")
    if chosen:
        anims.update((manifest.get("variants") or {}).get(chosen, {}).get("animations") or {})
    return sorted({a.get("sheet") for a in anims.values() if isinstance(a, dict) and a.get("sheet")})


def staging_class(manifest: dict, variant: str | None, char_id: str) -> str:
    """'standing', 'seated', 'bust' or the variant name, for the DECISIONS comparison."""
    chosen = variant or manifest.get("default_variant")
    if chosen in ("counter", "table", "window", "window_glass"):
        return "bust"
    if chosen == "full":
        return "standing"
    if chosen:
        return chosen
    return base_pose(manifest)


def check_staging(rep: Report, nid: str, char_id: str | None, b: dict) -> None:
    manifest = actor_manifest(char_id)
    if manifest is None:
        rep.warn(f"npcs.{nid}: no sprite data assets/actors/{char_id}/actor.json (placeholder figure)")
        return
    ok, variant = resolve_staging(manifest, b.get("variant"))
    if not ok:
        names = ", ".join(sorted((manifest.get("variants") or {}).keys())) or "none"
        rep.error(f"npcs.{nid}.variant {b.get('variant')!r} does not exist for {char_id} "
                  f"(generic: {', '.join(GENERIC_STAGING)}; actor.json variants: {names}; base pose "
                  f"{base_pose(manifest)})")
        return
    sheets = manifest.get("sheets") or {}
    sill_line = False
    for name in variant_sheets(manifest, variant):
        sheet = sheets.get(name)
        if not sheet:
            rep.error(f"npcs.{nid}: {char_id} animation sheet {name!r} is not in actor.json sheets")
            continue
        for key in ("file", "json"):
            if sheet.get(key) and not (ACTORS / char_id / sheet[key]).exists():
                rep.error(f"npcs.{nid}: {char_id} sheet file {sheet[key]} is missing")
        meta = ACTORS / char_id / sheet.get("json", "")
        if sheet.get("json") and meta.exists():
            try:
                sill_line |= bool(json.loads(meta.read_text(encoding="utf-8")).get("pivot_is_sill_line"))
            except json.JSONDecodeError:
                rep.error(f"npcs.{nid}: {char_id} {sheet['json']} is not valid JSON")
    if sill_line and "sill_y" not in b:
        rep.error(f"npcs.{nid}: {char_id} variant {variant or manifest.get('default_variant')!r} is cut at a sill line; "
                  f"give sill_y (canvas y of the painted sill / counter / table top)")
    if not sill_line and "sill_y" in b:
        rep.warn(f"npcs.{nid}: sill_y is ignored by a full-figure variant ({variant or 'default'})")
    expected = EXPECTED_STAGING.get(nid)
    actual = staging_class(manifest, variant, char_id)
    if expected and actual != expected:
        rep.warn(f"npcs.{nid}: staged {actual!r} ({b.get('variant') or 'default'}), docs/DECISIONS.md item 2 asks for "
                 f"{expected!r}")


def image_size(path: Path):
    try:
        from PIL import Image
    except ImportError:
        return None
    with Image.open(path) as img:
        return img.size, img.mode


def check_image(rep: Report, what: str, path: Path, full_frame: bool = False, patch_at=None, alpha: bool = False) -> None:
    info = image_size(path)
    if info is None:
        return
    (w, h), mode = info
    if full_frame and (w, h) != FRAME:
        rep.error(f"{what}: {rel(path)} is {w}x{h}, must be 1920x1080")
    if patch_at is not None:
        x, y = patch_at
        if x < 0 or y < 0 or x + w > FRAME[0] or y + h > FRAME[1]:
            rep.warn(f"{what}: {w}x{h} at {list(patch_at)} reaches out of the frame")
    if alpha and "A" not in mode and mode != "P":
        rep.error(f"{what}: {rel(path)} has no alpha channel")


def rel(path: Path) -> str:
    """Repo-relative posix path (absolute when outside the repo, e.g. a test copy)."""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def res_path(path: str) -> Path:
    return ROOT / "src" / "game" / path[len("res://"):] if path.startswith("res://") else ASSETS / path


def strict_or_warn(rep: Report, strict: bool, waive: dict, key: str, msg: str) -> None:
    if key in waive:
        return
    (rep.error if strict else rep.warn)(f"{msg} [waive key {key!r}]")


def check_assets(rep: Report, room: dict, blocking: dict, game: dict, strict: bool) -> None:
    rid = room["id"]
    waive = blocking.get("waive") or {}
    if not isinstance(waive, dict):
        rep.error("waive must be an object {key: reason}")
        waive = {}
    # Painting.
    bg = blocking.get("background") or f"bg_natural/{rid}.webp"   # RoomBlocking.cs: same convention
    if not (ASSETS / bg).exists():
        strict_or_warn(rep, strict, waive, "background",
                       f"background {bg} does not exist yet (the game shows the blockout)")
    else:
        check_image(rep, "background", ASSETS / bg, full_frame=True)
    # Foreground mask (explicit path must exist; the convention path is optional).
    fg = blocking.get("foreground_mask")
    if fg:
        if not (ASSETS / fg).exists():
            rep.error(f"foreground_mask {fg} does not exist")
        else:
            check_image(rep, "foreground_mask", ASSETS / fg, full_frame=True, alpha=True)
    elif (ASSETS / "fg_natural" / f"{rid}.webp").exists():
        check_image(rep, "foreground mask", ASSETS / "fg_natural" / f"{rid}.webp", full_frame=True, alpha=True)
    # Occluders.
    occ = blocking.get("occluders", [])
    if not isinstance(occ, list):
        rep.error("occluders must be a list")
        occ = []
    ys = [p[1] for p in blocking.get("walk_polygon") or room["walk_polygon"]]
    for i, o in enumerate(occ):
        name = o.get("id", f"#{i + 1}")
        poly = o.get("polygon")
        if not (isinstance(poly, list) and len(poly) >= 3 and all(is_vec(p) for p in poly)):
            rep.error(f"occluder {name}: polygon must be >= 3 [x, y] points")
            continue
        if any(not (0 <= p[0] <= FRAME[0] and 0 <= p[1] <= FRAME[1]) for p in poly):
            rep.error(f"occluder {name}: polygon leaves the frame")
        if not is_simple([tuple(p) for p in poly]):
            rep.error(f"occluder {name}: polygon intersects itself")
        base = o.get("baseline", max(p[1] for p in poly))
        if not isinstance(base, (int, float)):
            rep.error(f"occluder {name}: baseline must be a number")
        elif base <= min(ys):
            rep.warn(f"occluder {name}: baseline {base} is above the walk area (y >= {min(ys)}): every actor is in "
                     f"front of it, so it hides nothing")
        elif base >= max(ys):
            rep.warn(f"occluder {name}: baseline {base} is below the walk area: it is always in front (use the "
                     f"foreground mask for that)")
        tex = o.get("texture")
        if tex:
            if not (ASSETS / tex).exists():
                rep.error(f"occluder {name}: texture {tex} does not exist")
            else:
                check_image(rep, f"occluder {name}", ASSETS / tex, full_frame=True)
    # Variant overlays for the room's visual_variant_layers.
    room_layers = [v["asset"] for v in game.get("visual_variant_layers", []) if v.get("room") == rid]
    mapping = blocking.get("variant_layers", {})
    if not isinstance(mapping, dict):
        rep.error("variant_layers must be an object {template asset: natural overlay}")
        mapping = {}
    for asset, value in mapping.items():
        if asset not in room_layers:
            rep.error(f"variant_layers: {asset!r} is not a visual_variant_layers asset of {rid} "
                      f"(the room has: {', '.join(room_layers) or 'none'})")
        if value is None or value == "none":
            continue
        tex, pos = (value.get("texture"), value.get("pos")) if isinstance(value, dict) else (value, None)
        if not isinstance(tex, str) or not (ASSETS / tex).exists():
            rep.error(f"variant_layers[{asset}]: overlay {tex!r} does not exist")
            continue
        if pos is not None and not is_vec(pos):
            rep.error(f"variant_layers[{asset}]: pos must be [x, y]")
        elif pos is None:
            check_image(rep, f"variant overlay {tex}", ASSETS / tex, full_frame=True, alpha=True)
        else:
            check_image(rep, f"variant patch {tex}", ASSETS / tex, patch_at=pos)
    for asset in room_layers:
        if asset not in mapping:
            strict_or_warn(rep, strict, waive, f"variant:{asset}",
                           f"visual_variant_layers asset {asset} has no natural overlay in variant_layers "
                           f"(the game shows a dev marker)")
    # Hotspots that appear / disappear need a picture of the changed state.
    patches = blocking.get("state_patches", [])
    for h in room["hotspots"]:
        for key in ("hide_after", "visible_after"):
            for aid in h.get(key) or []:
                if not any(aid in (p.get("after") or []) or aid in (p.get("until") or []) for p in patches):
                    strict_or_warn(rep, strict, waive, f"patch:{h['id']}",
                                   f"{h['id']} {key} {aid}: no state patch with {aid} in after/until shows the change")
    # NPC staging present.
    for h in room["hotspots"]:
        if h["kind"] == "npc" and "variant" not in (blocking.get("npcs", {}).get(h["id"]) or {}):
            strict_or_warn(rep, strict, waive, f"staging:{h['id']}",
                           f"{h['id']}: no staging variant in npcs (default sheets; actors.json placements are not "
                           f"used in natural rooms)")
    check_ambient(rep, rid, blocking, strict, waive)
    check_audio(rep, blocking.get("audio"))


def import_problem(image: Path) -> str | None:
    """Why Godot cannot load an existing image, or None. The game loads ambient sprites through ResourceLoader, which
    needs the image's .import sidecar; one written while the file was missing or half-written says valid=false and the
    sprite is "not found" in the game even though the file is there (S51 tram_2020_mid, 2026-10-06). Godot does not
    retry such an import on its own: rewrite the sidecar (or delete it) and run the headless --import."""
    sidecar = image.with_name(image.name + ".import")
    if not sidecar.exists():
        return f"has no Godot import file {rel(sidecar)} (run the headless --import, then keep the .import with the file)"
    text = sidecar.read_text(encoding="utf-8", errors="replace")
    if re.search(r"^valid\s*=\s*false\s*$", text, re.MULTILINE) or not re.search(r"^path(\.\w+)?\s*=", text, re.MULTILINE):
        return f"failed its Godot import ({rel(sidecar)} says valid=false / has no imported path): the game cannot load it"
    return None


def check_ambient(rep: Report, rid: str, blocking: dict, strict: bool, waive: dict) -> None:
    path = res_path(blocking["ambient"]) if blocking.get("ambient") else BLOCKING / "ambient" / f"{rid}.json"
    if not path.exists():
        strict_or_warn(rep, strict, waive, "ambient", f"ambient file {rel(path)} does not "
                                                      f"exist (no ambient animation in natural mode)")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        rep.error(f"ambient {path.name}: invalid JSON ({ex})")
        return
    if data.get("room") not in (None, rid):
        rep.error(f"ambient {path.name}: 'room' is {data.get('room')!r}")
    layers = [layer for layer in data.get("layers", []) if isinstance(layer, dict) and not layer.get("disabled")]
    if len(layers) < MIN_AMBIENT_LAYERS:
        strict_or_warn(rep, strict, waive, "ambient", f"ambient {path.name}: {len(layers)} layer(s), a living scene "
                                                      f"needs >= {MIN_AMBIENT_LAYERS} (ART_DIRECTION.md section 5)")
    template_cuts = set()
    for i, layer in enumerate(layers):
        lid = layer.get("id", f"#{i + 1}")
        if layer.get("type") not in AMBIENT_TYPES:
            rep.error(f"ambient {lid}: unknown type {layer.get('type')!r} ({', '.join(sorted(AMBIENT_TYPES))})")
        refs = []
        for key in ("texture", "textures", "mask"):
            value = layer.get(key)
            refs += [value] if isinstance(value, str) else [v for v in value or [] if isinstance(v, str)]
        sheet = layer.get("sheet")
        for ref in refs + ([sheet] if isinstance(sheet, str) else []):
            if ref.startswith("builtin:"):
                continue
            full = ROOT / "src" / "game" / ref[len("res://"):] if ref.startswith("res://") else AMBIENT_ASSETS / ref
            image = full if full.suffix in (".webp", ".png") else full.with_name(full.name + ".webp")
            if not image.exists():
                rep.error(f"ambient {lid}: {ref} does not exist ({rel(image)})")
            elif problem := import_problem(image):
                rep.error(f"ambient {lid}: {ref} {problem}")
            if ref == sheet and not image.with_suffix(".json").exists() and not ref.endswith((".webp", ".png")):
                rep.error(f"ambient {lid}: sheet {ref} has no .json")
            parts = ref.split("/")
            if parts[0] == rid and len(parts) == 2:
                template_cuts.add(ref)
    for ref in sorted(template_cuts):
        rep.warn(f"ambient: {ref} is cut from the template painting bg/{rid}.webp; cut natural sprites into "
                 f"assets/ambient/{rid}/natural/ (art/tools/ambient_cut.py --natural {rid})")


def check_audio(rep: Report, audio) -> None:
    if audio is None:
        return
    if not isinstance(audio, dict):
        rep.error("audio must be an object")
        return
    for key in audio:
        if key not in ("ambience", "ambience_mode", "music", "note", "reason"):
            rep.warn(f"audio: unknown key {key!r}")
    if audio.get("ambience_mode", "replace") not in ("replace", "add"):
        rep.error("audio.ambience_mode must be 'replace' or 'add'")
    library = json.loads(AMBIENCE.read_text(encoding="utf-8")).get("library", {}) if AMBIENCE.exists() else {}
    for i, layer in enumerate(audio.get("ambience") or []):
        sound = layer.get("sound") if isinstance(layer, dict) else None
        if sound not in library:
            rep.error(f"audio.ambience[{i}]: sound {sound!r} is not in data/audio/ambience.json library")
        for key in ("every", "x"):
            if key in layer and not is_vec(layer[key]):
                rep.error(f"audio.ambience[{i}].{key} must be [min, max]")
    music = audio.get("music")
    if music:
        cues = json.loads(MUSIC.read_text(encoding="utf-8")).get("cues", {}) if MUSIC.exists() else {}
        if music not in cues and not (ASSETS / music).exists():
            rep.error(f"audio.music {music!r} is neither a music.json cue nor an asset")


def check_families(blockings: dict[str, dict], rooms: dict) -> list[str]:
    """Rooms of one camera family (game.json location_families / camera_family) must share the perspective."""
    notes = []
    families: dict[str, list[str]] = {}
    for rid in blockings:
        fam = rooms[rid].get("camera_family")
        if fam and fam != rid:
            families.setdefault(fam, []).append(rid)
    for fam, members in sorted(families.items()):
        if len(members) < 2:
            continue
        base = blockings[members[0]]
        for rid in members[1:]:
            for key in ("walk_band", "actor_scale", "anchors"):
                if blockings[rid].get(key) != base.get(key):
                    notes.append(f"{fam}: {rid}.{key} {blockings[rid].get(key)} differs from {members[0]}.{key} "
                                 f"{base.get(key)} (one camera = one perspective)")
    return notes


def check_continuity(loaded: dict[str, dict], rooms: dict[str, dict]) -> list[str]:
    """Walking continuity (docs/navigation/EXITS.md): leaving A out of its left (right) edge arrives at B's right (left)
    edge, so an edge exit whose return exit sits on the SAME edge of the target makes Adam turn round on arrival."""
    notes = []
    for rid, blocking in sorted(loaded.items()):
        a = effective_room(rooms[rid], blocking)
        for e in a["exits"]:
            target = rooms.get(e["to"])
            if target is None or e["to"] not in loaded or e.get("travel", "walk") != "walk":
                continue
            b = effective_room(target, loaded[e["to"]])
            back = next((x for x in b["exits"] if x["to"] == rid), None)
            if back is None:
                continue
            sa, sb = exit_side(e), exit_side(back)
            # Only walkways out of the frame edge on both sides: a door in a side wall is passed through and turned
            # away from, so the same side in both rooms is natural there.
            def at_edge(x: dict, side: str) -> bool:
                return x["rect"][0] <= 5 if side == "left" else x["rect"][0] + x["rect"][2] >= FRAME[0] - 5
            if sa in ("left", "right") and sa == sb and rid < e["to"] and at_edge(e, sa) and at_edge(back, sb):
                notes.append(f"continuity: {e['id']} leads {sa} and its return {back['id']} is on the {sb} edge too "
                             f"(walking out of the {sa} edge should arrive from the {'right' if sa == 'left' else 'left'})")
    return notes


def main(argv: list[str]) -> int:
    template = "--template" in argv
    strict = "--strict" in argv
    ids = [a for a in argv if not a.startswith("--")]
    game = load_game()
    rooms = {r["id"]: r for r in game["rooms"]}
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8")).get("rooms", {}) if OVERRIDES.exists() else {}
    if not ids:
        ids = sorted(p.stem for p in BLOCKING.glob("*.json")) if not template else sorted(rooms)
    errors = warnings = 0
    loaded: dict[str, dict] = {}
    for rid in ids:
        if rid not in rooms:
            print(f"{rid}: ERROR unknown room")
            errors += 1
            continue
        rep = Report(rid)
        blocking = None
        if not template:
            path = blocking_path(rid)
            if not path.exists():
                print(f"{rid}: ERROR no blocking file {rel(path)}")
                errors += 1
                continue
            try:
                blocking = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as ex:
                print(f"{rid}: ERROR {path.name}: {ex}")
                errors += 1
                continue
            check_schema(rep, rooms[rid], blocking)
            check_assets(rep, rooms[rid], blocking, game, strict)
            loaded[rid] = blocking
        check_room(rep, effective_room(rooms[rid], blocking), overrides.get(rid, {}))
        if blocking is not None:
            check_guests_and_node(rep, rooms[rid], blocking, effective_room(rooms[rid], blocking))
        mode = "template (game.json)" if template else f"natural ({rel(blocking_path(rid))})"
        status = "OK" if not rep.errors else "FAIL"
        print(f"{rid} {mode}: {status} - {len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
        for e in rep.errors:
            print(f"  ERROR {e}")
        for w in rep.warnings:
            print(f"  warn  {w}")
        errors += len(rep.errors)
        warnings += len(rep.warnings)
    if not template:
        # Family members not named on the command line still count for the comparison.
        for path in BLOCKING.glob("*.json"):
            if path.stem in rooms and path.stem not in loaded:
                try:
                    loaded[path.stem] = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    pass
        for note in check_families(loaded, rooms):
            if any(rid in note for rid in ids):
                print(f"  warn  {note}")
                warnings += 1
        for note in check_continuity(loaded, rooms):
            if any(rid in note for rid in ids):
                print(f"  warn  {note}")
                warnings += 1
    print(f"check_blocking: {len(ids)} room(s), {errors} error(s), {warnings} warning(s)"
          + (" [strict]" if strict else ""))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
