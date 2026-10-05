"""Validate natural re-blocking files (src/game/data/blocking/<room>.json, docs/reblock/README.md).

A blocking file replaces the presentation geometry of a room (hotspot / exit rects, interaction points, label anchors,
walk polygon, NPC feet and scale, perspective range); ids and conditions stay in game.json. The game applies it only
when natural blocking is enabled (project setting last_bell/presentation/blocking = "natural" or --blocking natural).

Checks on the EFFECTIVE room (game.json merged with the blocking file, exactly as src/game/scripts/World/Room.cs does):
  errors   - unknown room / hotspot / exit / NPC ids, malformed values
           - every hotspot and exit rect at least 44x44 px and at least 44x44 px of it on screen
           - walk polygon: >= 3 points, simple (no self-intersection), inside the 1920x1080 frame
           - every hotspot and exit interaction point inside the walk polygon (exits reachable; the polygon is one
             connected area, so every inside point is reachable from the spawn), spawn inside
           - label anchors on screen
           - NPC feet on walkable floor (inside the walk polygon, 12 px tolerance)
           - no rect fully hidden behind others in the game's hit order (NPCs, props later-on-top, exits)
  warnings - label boxes overlapping each other or pushed by the screen clamp, label far from its rect,
             exit rect far from its interaction point, NPC approach point not walkable, NPC scale far from the
             room perspective at its feet, rect mostly hidden, background painting missing

Usage: python tools/check_blocking.py                 (all files in src/game/data/blocking/)
       python tools/check_blocking.py S03 S05         (these rooms' blocking files)
       python tools/check_blocking.py --template S03  (check game.json's template geometry instead, for comparison)
Exit code 1 when any error is found.
"""
from __future__ import annotations

import copy
import json
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
                  "spawn", "hotspots", "exits", "npcs", "foreground_mask", "ambient", "state_patches", "reasons"}
TARGET_KEYS = {"rect", "interaction_point", "label_anchor", "reason", "note"}


# --------------------------------------------------------------------------- data

def load_game() -> dict:
    return json.loads(GAME.read_text(encoding="utf-8"))


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
        for key in ("rect", "interaction_point", "label_anchor"):
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
        if "feet" in b and not is_vec(b["feet"]):
            rep.error(f"npcs.{nid}.feet must be [x, y]")
        if "scale" in b and not (isinstance(b["scale"], (int, float)) and 0.1 <= b["scale"] <= 1.5):
            rep.error(f"npcs.{nid}.scale must be a number in 0.1..1.5")
    for key in ("walk_band", "actor_scale", "spawn"):
        if key in blocking and not is_vec(blocking[key]):
            rep.error(f"{key} must be [a, b]")
    if "actor_scale" in blocking and is_vec(blocking["actor_scale"]):
        s0, s1 = blocking["actor_scale"]
        if not (0.2 <= s0 <= 1.3 and 0.2 <= s1 <= 1.3):
            rep.error(f"actor_scale {blocking['actor_scale']} outside 0.2..1.3")
        elif s0 > s1:
            rep.warn(f"actor_scale {blocking['actor_scale']}: actors get smaller towards the front")
    for patch in blocking.get("state_patches", []):
        tex = patch.get("texture")
        if not tex or not (ASSETS / tex).exists():
            rep.error(f"state patch texture {tex!r} does not exist")
        if not is_vec(patch.get("pos")):
            rep.error(f"state patch {tex!r}: pos must be [x, y]")
    bg = blocking.get("background")
    if bg and not (ASSETS / bg).exists():
        rep.warn(f"background {bg} does not exist yet (the game falls back to the blockout)")


def is_vec(v) -> bool:
    return isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v)


def check_target_values(rep: Report, ident: str, b: dict) -> None:
    for key in b:
        if key not in TARGET_KEYS:
            rep.warn(f"{ident}: unknown key {key!r}")
    if "rect" in b and not (isinstance(b["rect"], list) and len(b["rect"]) == 4
                            and all(isinstance(x, (int, float)) for x in b["rect"])):
        rep.error(f"{ident}: rect must be [x, y, w, h]")
    for key in ("interaction_point", "label_anchor"):
        if key in b and not is_vec(b[key]):
            rep.error(f"{ident}: {key} must be [x, y]")


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
            if x0 - NPC_APPROACH_GAP / 2 <= ip[0] <= x1 + NPC_APPROACH_GAP / 2:
                sides = [(x0 - NPC_APPROACH_GAP, ip[1]), (x1 + NPC_APPROACH_GAP, ip[1])]
                if not any(inside(poly, s) for s in sides):
                    rep.warn(f"{ident}: neither approach point {[list(s) for s in sides]} is walkable; the hero "
                             f"stands on the interaction point in front of the NPC")

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
        if not inside(poly, feet):
            d = distance_to_polygon(poly, feet)
            (rep.warn if d <= FEET_TOLERANCE else rep.error)(
                f"{h['id']}: NPC feet {feet} are {d:.0f} px off the walkable floor")
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


def main(argv: list[str]) -> int:
    template = "--template" in argv
    ids = [a for a in argv if not a.startswith("--")]
    game = load_game()
    rooms = {r["id"]: r for r in game["rooms"]}
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8")).get("rooms", {}) if OVERRIDES.exists() else {}
    if not ids:
        ids = sorted(p.stem for p in BLOCKING.glob("*.json")) if not template else sorted(rooms)
    errors = warnings = 0
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
                print(f"{rid}: ERROR no blocking file {path.relative_to(ROOT)}")
                errors += 1
                continue
            try:
                blocking = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as ex:
                print(f"{rid}: ERROR {path.name}: {ex}")
                errors += 1
                continue
            check_schema(rep, rooms[rid], blocking)
        check_room(rep, effective_room(rooms[rid], blocking), overrides.get(rid, {}))
        mode = "template (game.json)" if template else f"natural ({blocking_path(rid).relative_to(ROOT).as_posix()})"
        status = "OK" if not rep.errors else "FAIL"
        print(f"{rid} {mode}: {status} - {len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
        for e in rep.errors:
            print(f"  ERROR {e}")
        for w in rep.warnings:
            print(f"  warn  {w}")
        errors += len(rep.errors)
        warnings += len(rep.warnings)
    print(f"check_blocking: {len(ids)} room(s), {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
