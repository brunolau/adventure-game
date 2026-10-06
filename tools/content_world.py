"""World overlay (src/game/data/content_ext/world_ext.json): Python mirror of LastBell.Core's ContentOverlay.World.cs.

Used by tools/content_ext.py (apply_overlays) so the localization and writing tools see the EFFECTIVE game:
new rooms, hotspots, characters, items, actions, side quests, epilogue shots, variant layers and connections,
and relocations of existing actions to a hotspot in another room of the same era. The effective entries have the
game.json shape (plus actions[].hint_step), so every new text gets its key from the usual scheme:

    room.<id>.name, hotspot.<id>.name, look.<hotspotId> (look), look.<hotspotId>.variant<n>, item.<id>.name,
    item.<id> (look), item.<id>.purpose, char.<id>.name, action.<id>.label|journal|objective, action.<id>.hint_step,
    action.<id>.<n> (lines), entry.<room>.<n> (first entry), quest.<id>.title|goal|reward|hint.<n>,
    epilogue.<n>.shot|line (n continues after game.json's 9), exit.<id>.label|locked, conn.<from>.<to>.label|locked

Core (GameContent.Load) is the authority: it runs every check here and, on top, the playability check (the whole game
played through the real rules in several orders, no softlock). `python tools/content_ext.py check` runs the checks of
this mirror (ids, references, geometry, item flow, default-click ambiguity, reachability); `dotnet test src/LastBell.sln`
loads the live overlays through Core.
"""
from __future__ import annotations

import copy
import re

WORLD_FORMAT = "lastbell.world_ext"
ATOMIC = "atomic_after_validation_and_puzzle_before_lines"
DEFAULT_LAYERS = ["background", "prop_state_variants", "npc_shadows", "npcs_and_adam_sorted_by_feet_y",
                  "foreground_mask", "hotspot_labels", "hud"]
ANIMATIONS = {"talk", "show_item", "inventory_combine", "use_tool", "reach_low", "reach_mid", "reach_high"}
CANVAS = (1920, 1080)
MIN_TARGET = 44

ROOM_ID = re.compile(r"^S\d{2,3}$")
CODE_ID = re.compile(r"^[A-Z][A-Z0-9_]*$")
QUEST_ID = re.compile(r"^Q\d{1,3}$")
HOTSPOT_SUFFIX = re.compile(r"^[A-Za-z0-9_]+$")
ASSET = re.compile(r"^[a-z_]+(/[A-Za-z0-9_\-]+)+\.(webp|png|jpg|ogg)$")
SFX = re.compile(r"^[a-z0-9_]+$")

ROOT_KEYS = {"format", "version", "about", "note", "schema", "sources", "characters", "items", "rooms", "hotspots",
             "exits", "connections", "quests", "actions", "epilogue", "visual_variant_layers", "relocations"}
CHARACTER_KEYS = {"id", "name", "age", "role", "voice", "design", "rooms", "note"}
ITEM_KEYS = {"id", "name", "look", "purpose", "icon", "origin", "disposition", "note"}
ROOM_KEYS = {"id", "name", "era", "district", "region", "hub", "art_brief", "ambience", "background_asset", "music",
             "walk_polygon", "spawn", "camera_family", "layer_order", "npc_ids", "first_entry", "hotspots", "exits",
             "blocking_note", "note"}
HOTSPOT_KEYS = {"room", "id", "name", "kind", "character_id", "look", "rect", "interaction_point", "label_anchor",
                "visible_after", "hide_after", "look_variants", "note"}
QUEST_KEYS = {"id", "type", "title", "goal", "reward", "hints", "actions", "completion", "missable", "note"}
ACTION_KEYS = {"id", "room", "target", "kind", "label", "requires_done", "requires_items", "selected_item", "gives",
               "consumes", "excluded_done", "lines", "quest", "once", "objective", "journal_text", "animation", "sfx",
               "staging", "commit_policy", "symmetric", "hint_step", "puzzle", "cutscene", "note"}
EPILOGUE_KEYS = {"quest", "after", "shot", "line", "note"}
LAYER_KEYS = {"room", "after", "asset", "change", "note"}
RELOCATION_KEYS = {"action", "to_hotspot", "hint_step", "retire_hotspot", "reason", "note"}
VARIANT_KEYS = {"after", "sk", "note"}


def inside(poly: list, x: float, y: float) -> bool:
    """Point in polygon (even-odd); a point on the outline counts as inside (Core OverlayApplier.InsidePolygon)."""
    result = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        cross = (x - xi) * (yj - yi) - (y - yi) * (xj - xi)
        if abs(cross) < 1e-9 and min(xi, xj) - 1e-9 <= x <= max(xi, xj) + 1e-9 and min(yi, yj) - 1e-9 <= y <= max(yi, yj) + 1e-9:
            return True
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            result = not result
        j = i
    return result


def _ints(value, count: int) -> bool:
    return isinstance(value, list) and len(value) == count and all(isinstance(v, int) and not isinstance(v, bool) for v in value)


def _needs(a: dict) -> list[str]:
    out = list(a.get("requires_items", []))
    if a.get("selected_item"):
        out.append(a["selected_item"])
    if a.get("kind") == "combine":
        out.append(a["target"])
    return out


def dependency_closure(actions: list[dict]) -> dict[str, set[str]]:
    """Every action's transitive 'happens after' set: requires_done plus the one giver of each needed item."""
    by_id = {a["id"]: a for a in actions}
    givers: dict[str, list[str]] = {}
    for a in actions:
        for item in a.get("gives", []):
            givers.setdefault(item, []).append(a["id"])
    giver = {item: ids[0] for item, ids in givers.items() if len(ids) == 1}

    def direct(aid: str) -> list[str]:
        a = by_id.get(aid)
        if a is None:
            return []
        return list(a.get("requires_done", [])) + [giver[i] for i in _needs(a) if i in giver]

    closure: dict[str, set[str]] = {}
    for a in actions:
        seen: set[str] = set()
        todo = direct(a["id"])
        while todo:
            n = todo.pop()
            if n in seen:
                continue
            seen.add(n)
            todo.extend(direct(n))
        closure[a["id"]] = seen
    return closure


class _World:
    def __init__(self, eff: dict, root: dict, base_ids: set[str], new_ids: set[str], res, helpers):
        self.eff, self.root, self.base_ids, self.new_ids, self.res, self.h = eff, root, base_ids, new_ids, res, helpers
        self.errors: list[str] = res.errors
        self.rp = "$world_ext"

    # -- small helpers mirroring Core's Str / Text / StrList
    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def str_(self, o: dict, key: str, path: str, required: bool = False):
        if key not in o or o[key] is None:
            if required:
                self.err(f"{path}.{key}: missing")
            return None
        if not isinstance(o[key], str):
            self.err(f"{path}.{key}: must be a string")
            return None
        return o[key]

    def text(self, o: dict, key: str, path: str, required: bool = True):
        t = self.str_(o, key, path, required)
        if t is None:
            return None
        if not t.strip():
            self.err(f"{path}.{key}: empty text")
            return None
        if "\n" in t or "\r" in t:
            self.err(f"{path}.{key}: one text is one line; no line breaks")
            return None
        if t != t.strip():
            self.err(f"{path}.{key}: leading or trailing spaces")
        return t

    def strs(self, o: dict, key: str, path: str) -> list[str]:
        value = o.get(key, [])
        if value is None:
            return []
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            self.err(f"{path}.{key}: must be a list of strings")
            return []
        return list(value)

    def boolean(self, o: dict, key: str, path: str):
        if key not in o or o[key] is None:
            return None
        if not isinstance(o[key], bool):
            self.err(f"{path}.{key}: must be true or false")
            return None
        return o[key]

    def entries(self, parent: dict, key: str, path: str):
        value = parent.get(key)
        if value is None:
            return
        if not isinstance(value, list):
            self.err(f"{path}.{key}: must be a list")
            return
        for i, o in enumerate(value):
            p = f"{path}.{key}[{i}]"
            if isinstance(o, dict):
                yield o, p
            else:
                self.err(f"{p}: must be an object")

    def rect_ok(self, r: list, path: str) -> None:
        if r[2] < MIN_TARGET or r[3] < MIN_TARGET:
            self.err(f"{path}: at least {MIN_TARGET}x{MIN_TARGET} px (got {r[2]}x{r[3]})")
            return
        w = min(r[0] + r[2], CANVAS[0]) - max(r[0], 0)
        h = min(r[1] + r[3], CANVAS[1]) - max(r[1], 0)
        if w < MIN_TARGET or h < MIN_TARGET:
            self.err(f"{path}: at least {MIN_TARGET}x{MIN_TARGET} px of it on screen")

    # -- the overlay
    def apply(self) -> None:
        rp, root, eff, res = self.rp, self.root, self.eff, self.res
        start = len(self.errors)
        self.h.header(root, rp, WORLD_FORMAT, self.errors)
        hint = "lines of existing exchanges and optional topics belong in dialogue_ext.json" if (
            "topics" in root or "sequences" in root) else ""
        self.h.check_keys(root, rp, ROOT_KEYS, self.errors, hint)

        rooms = {r["id"]: r for r in eff["rooms"]}
        hotspot_room = {h["id"]: r["id"] for r in eff["rooms"] for h in r.get("hotspots", [])}
        hotspots = {h["id"]: h for r in eff["rooms"] for h in r.get("hotspots", [])}
        characters = {c["id"]: c for c in eff["characters"]}
        items = {i["id"]: i for i in eff["items"]}
        actions = {a["id"]: a for a in eff["actions"]}
        quests = {q["id"]: q for q in eff["quests"]}
        years = {e["year"] for e in eff["eras"]}
        used = set(self.base_ids)
        for h in hotspots.values():
            if h.get("look_line_id"):
                used.add(h["look_line_id"])
            used |= {v["line_id"] for v in h.get("look_variants", []) if v.get("line_id")}
        used |= {i["look_line_id"] for i in eff["items"] if i.get("look_line_id")}

        def prescan(key: str) -> set[str]:
            return {o["id"] for o in root.get(key, []) or [] if isinstance(o, dict) and isinstance(o.get("id"), str)}

        new_action_ids, new_quest_ids = prescan("actions"), prescan("quests")
        action_ids = set(actions) | new_action_ids
        all_ids: set[str] = set()

        def new_id(i: str, path: str, pattern, what: str, example: str, exists: bool) -> bool:
            if not pattern.match(i):
                self.err(f"{path}.id: '{i}' is not a valid {what} id (e.g. {example})")
                return False
            if exists:
                self.err(f"{path}.id: {what} '{i}' already exists; the world overlay adds new ids only (to move an action use relocations)")
                return False
            if f"{what}:{i}" in all_ids:
                self.err(f"{path}.id: {what} '{i}' is defined twice")
                return False
            all_ids.add(f"{what}:{i}")
            return True

        def new_key(key: str, path: str) -> bool:
            if key not in self.new_ids and key not in used:
                used.add(key)
                return True
            self.err(f"{path}: text key '{key}' already exists")
            return False

        # characters
        new_chars = []
        for o, path in self.entries(root, "characters", rp):
            cid = self.str_(o, "id", path, True)
            if cid is None:
                continue
            p = f"{path}({cid})"
            self.h.check_keys(o, p, CHARACTER_KEYS, self.errors,
                              "a character's optional topics belong in dialogue_ext.json topics (id 'ext.<...>' or '<CHARACTER>.extra <n>')"
                              if "ambient_topics" in o else "")
            if not new_id(cid, p, CODE_ID, "character", "ZUZANA, SAMPLE95", cid in characters or cid in eff.get("non_actor_speakers", {})):
                continue
            name = self.text(o, "name", p)
            age = o.get("age")
            if age is not None and not (isinstance(age, (int, str)) and not isinstance(age, bool)):
                self.err(f"{p}.age: must be a number or a text")
                age = None
            role, voice, design = (self.str_(o, k, p) or "" for k in ("role", "voice", "design"))
            self.str_(o, "note", p)
            listed = self.strs(o, "rooms", p) if "rooms" in o else None
            if name is None:
                continue
            new_chars.append(({"id": cid, "name": name, "age": age, "role": role, "voice": voice, "design": design,
                               "rooms": [], "ambient_topics": [], "greeting_first": None, "greeting_repeat": None}, listed, p))
        for c, _, _ in new_chars:
            characters[c["id"]] = c
        speakers = set(characters) | set(eff.get("non_actor_speakers", {}))

        # items
        new_items = []
        for o, path in self.entries(root, "items", rp):
            iid = self.str_(o, "id", path, True)
            if iid is None:
                continue
            p = f"{path}({iid})"
            self.h.check_keys(o, p, ITEM_KEYS, self.errors)
            if not new_id(iid, p, CODE_ID, "item", "BELL_MUTE", iid in items):
                continue
            name, look, purpose = self.text(o, "name", p), self.text(o, "look", p), self.text(o, "purpose", p)
            icon = self.str_(o, "icon", p) or f"items/{iid}.webp"
            if not icon.startswith("items/") or not ASSET.match(icon):
                self.err(f"{p}.icon: '{icon}' must be an asset path under items/ (e.g. items/{iid}.webp)")
            origin = self.str_(o, "origin", p)
            disposition = self.str_(o, "disposition", p) or "retain"
            if disposition != "retain":
                self.err(f"{p}.disposition: every item is 'retain' (kept in the bag; archived when it has no use left)")
            self.str_(o, "note", p)
            if None in (name, look, purpose) or not new_key(f"item.{iid}", p + ".look"):
                continue
            new_items.append(({"id": iid, "name": name, "look": look, "origin": "", "purpose": purpose,
                               "disposition": "retain", "icon": icon, "look_line_id": f"item.{iid}"}, origin, p))
        for item, _, _ in new_items:
            items[item["id"]] = item

        # rooms
        new_rooms = []
        for o, path in self.entries(root, "rooms", rp):
            rid = self.str_(o, "id", path, True)
            if rid is None:
                continue
            p = f"{path}({rid})"
            self.h.check_keys(o, p, ROOM_KEYS, self.errors)
            if not new_id(rid, p, ROOM_ID, "room", "S69", rid in rooms):
                continue
            name = self.text(o, "name", p)
            era = o.get("era")
            if not isinstance(era, int) or isinstance(era, bool):
                self.err(f"{p}.era: missing year")
                continue
            if era not in years:
                self.err(f"{p}.era: unknown era {era}")
                continue
            district = self.text(o, "district", p)
            region = self.str_(o, "region", p)
            hub = self.boolean(o, "hub", p) or False
            if region is not None and (not region.strip() or "." in region):
                self.err(f"{p}.region: a region id is a plain name without dots")
            if hub and region is None:
                self.err(f"{p}.hub: only a room with a 'region' can be its hub")
            bg = self.str_(o, "background_asset", p, True)
            if bg is not None and (not (bg.startswith("bg/") or bg.startswith("bg_natural/")) or not ASSET.match(bg)):
                self.err(f"{p}.background_asset: '{bg}' must be an asset path under bg/ or bg_natural/ (e.g. bg/{rid}.webp)")
            music = self.str_(o, "music", p, True)
            if music is not None and (not music.startswith("music/") or not music.endswith(".ogg") or not ASSET.match(music)):
                self.err(f"{p}.music: '{music}' must be an .ogg path under music/ (e.g. music/{era}.ogg)")
            poly = o.get("walk_polygon")
            if poly is None:
                self.err(f"{p}.walk_polygon: missing")
            elif not isinstance(poly, list) or not all(_ints(pt, 2) for pt in poly):
                self.err(f"{p}.walk_polygon: must be a list of [x, y] integer points")
                poly = None
            elif len(poly) < 3:
                self.err(f"{p}.walk_polygon: at least 3 points")
                poly = None
            elif not all(0 <= x <= CANVAS[0] and 0 <= y <= CANVAS[1] for x, y in poly):
                self.err(f"{p}.walk_polygon: every point lies inside the {CANVAS[0]}x{CANVAS[1]} frame")
                poly = None
            spawn = o.get("spawn")
            if not _ints(spawn, 2):
                self.err(f"{p}.spawn: must have 2 integers")
                spawn = None
            elif poly is not None and not inside(poly, *spawn):
                self.err(f"{p}.spawn: [{spawn[0]}, {spawn[1]}] is not inside the walk polygon")
            layers = self.strs(o, "layer_order", p) if "layer_order" in o else list(DEFAULT_LAYERS)
            for layer in layers:
                if layer not in DEFAULT_LAYERS:
                    self.err(f"{p}.layer_order: unknown layer '{layer}' (known: {', '.join(DEFAULT_LAYERS)})")
            for layer in ("background", "npcs_and_adam_sorted_by_feet_y"):
                if layer not in layers:
                    self.err(f"{p}.layer_order: '{layer}' is missing")
            npc_ids = self.strs(o, "npc_ids", p) if "npc_ids" in o else None
            art, amb, blocking = (self.str_(o, k, p) or "" for k in ("art_brief", "ambience", "blocking_note"))
            camera = self.str_(o, "camera_family", p) or rid
            self.str_(o, "note", p)
            if None in (name, district, bg, music, poly, spawn):
                continue
            if region is not None:
                res.region_hints[rid] = (region, hub)
            room = {"id": rid, "name": name, "era": era, "district": district, "art_brief": art, "ambience": amb,
                    "first_entry": [], "hotspots": [], "npc_ids": [], "background_asset": bg, "music": music,
                    "walk_polygon": copy.deepcopy(poly), "spawn": list(spawn), "camera_family": camera, "exits": [],
                    "layer_order": layers, "blocking_note": blocking}
            rooms[rid] = room
            new_rooms.append((room, o, p, npc_ids))

        # hotspots
        added: dict[str, list[dict]] = {}
        new_hotspot_ids: set[str] = set()

        def add_hotspot(o: dict, path: str, rid: str, nested: bool) -> None:
            hid = self.str_(o, "id", path, True)
            if hid is None:
                return
            p = f"{path}({hid})"
            self.h.check_keys(o, p, HOTSPOT_KEYS - {"room"} if nested else HOTSPOT_KEYS, self.errors)
            room = rooms[rid]
            if not hid.startswith(rid + ".") or not HOTSPOT_SUFFIX.match(hid[len(rid) + 1:]):
                self.err(f"{p}.id: a hotspot id is '<room>.<name>' with letters, digits or '_' (e.g. {rid}.board)")
                return
            if hid in hotspots:
                self.err(f"{p}.id: hotspot '{hid}' already exists")
                return
            name = self.text(o, "name", p)
            kind = self.str_(o, "kind", p) or "prop"
            char = self.str_(o, "character_id", p)
            if kind not in ("prop", "npc"):
                self.err(f"{p}.kind: '{kind}' (a hotspot is 'prop' or 'npc')")
            if kind == "npc":
                present = [h for h in room.get("hotspots", []) + added.get(rid, []) if h.get("kind") == "npc"]
                if char is None:
                    self.err(f"{p}.character_id: an NPC hotspot names its character")
                elif char not in characters:
                    self.err(f"{p}.character_id: unknown character '{char}'")
                elif hid != f"{rid}.{char}":
                    self.err(f"{p}.id: an NPC hotspot is '<room>.<character>' (here '{rid}.{char}')")
                elif any(h.get("character_id") == char for h in present):
                    self.err(f"{p}.character_id: '{char}' already stands in room '{rid}'")
            elif char is not None:
                self.err(f"{p}.character_id: only an NPC hotspot has a character")
            look = self.text(o, "look", p)
            rect, point = o.get("rect"), o.get("interaction_point")
            if not _ints(rect, 4):
                self.err(f"{p}.rect: must have 4 integers")
                rect = None
            if not _ints(point, 2):
                self.err(f"{p}.interaction_point: must have 2 integers")
                point = None
            anchor = o.get("label_anchor")
            if anchor is None and rect is not None:
                anchor = [rect[0] + rect[2] // 2, max(0, rect[1] - 10)]
            elif anchor is not None and not _ints(anchor, 2):
                self.err(f"{p}.label_anchor: must have 2 integers")
                anchor = None
            if rect is not None:
                self.rect_ok(rect, p + ".rect")
            if point is not None and not inside(room["walk_polygon"], *point):
                self.err(f"{p}.interaction_point: [{point[0]}, {point[1]}] is not inside the walk polygon of '{rid}'")
            if anchor is not None and not (0 <= anchor[0] <= CANVAS[0] and 0 <= anchor[1] <= CANVAS[1]):
                self.err(f"{p}.label_anchor: [{anchor[0]}, {anchor[1]}] is off screen")
            visible, hide = self.strs(o, "visible_after", p), self.strs(o, "hide_after", p)
            for key, ids in (("visible_after", visible), ("hide_after", hide)):
                for i, a in enumerate(ids):
                    if a not in action_ids:
                        self.err(f"{p}.{key}[{i}]: unknown action '{a}'")
            variants = []
            for n, (v, vp) in enumerate(self.entries(o, "look_variants", p), start=1):
                self.h.check_keys(v, vp, VARIANT_KEYS, self.errors)
                after = self.str_(v, "after", vp, True)
                text = self.text(v, "sk", vp)
                self.str_(v, "note", vp)
                if after is not None and after not in action_ids:
                    self.err(f"{vp}.after: unknown action '{after}'")
                key = f"look.{hid}.variant{n}"
                if after is None or text is None or not new_key(key, vp):
                    continue
                variants.append({"after": after, "text": text, "line_id": key})
            self.str_(o, "note", p)
            if None in (name, look, rect, point, anchor) or not new_key(f"look.{hid}", p + ".look"):
                return
            h = {"id": hid, "name": name, "kind": kind, "look": look, "rect": list(rect),
                 "interaction_point": list(point), "visible_after": visible, "hide_after": hide,
                 "look_variants": variants, "label_anchor": list(anchor), "look_line_id": f"look.{hid}"}
            if char is not None:
                h["character_id"] = char
            hotspots[hid] = h
            hotspot_room[hid] = rid
            new_hotspot_ids.add(hid)
            added.setdefault(rid, []).append(h)
            res.added_hotspots.append(hid)

        for room, o, p, _ in new_rooms:
            for ho, hp in self.entries(o, "hotspots", p):
                add_hotspot(ho, hp, room["id"], True)
        new_room_ids = {r["id"] for r, _, _, _ in new_rooms}
        for o, path in self.entries(root, "hotspots", rp):
            rid = self.str_(o, "room", path, True)
            if rid is None:
                continue
            if rid not in rooms:
                self.err(f"{path}.room: unknown room '{rid}'")
                continue
            if rid in new_room_ids:
                self.err(f"{path}.room: '{rid}' is a new room; list its hotspots in rooms[].hotspots")
                continue
            add_hotspot(o, path, rid, False)

        def npc_chars(rid: str) -> set[str]:
            return {h["character_id"] for h in rooms[rid].get("hotspots", []) + added.get(rid, [])
                    if h.get("kind") == "npc" and h.get("character_id")}

        # first entries of new rooms
        for room, o, p, _ in new_rooms:
            if "first_entry" not in o:
                continue
            allowed = npc_chars(room["id"]) | {"ADAM"}
            lines = self.h.parse_lines({"lines": o["first_entry"]}, p + ".first_entry", "room", room["id"],
                                       f"entry.{room['id']}.", [], allowed, speakers, self.base_ids, self.new_ids,
                                       False, self.errors)
            if lines is not None:
                room["first_entry"] = lines
                used.update(l["line_id"] for l in lines)

        # exits and connections
        exits_by_room = {rid: list(r.get("exits", [])) for rid, r in rooms.items()}
        all_exit_ids = {e["id"] for r in eff["rooms"] for e in r.get("exits", [])}
        added_exits = []

        def exit_added(e, rid, path):
            if e is None:
                return
            added_exits.append((rid, e))
            if not inside(rooms[rid]["walk_polygon"], *e["interaction_point"]):
                self.err(f"{path}({e['id']}).interaction_point: [{e['interaction_point'][0]}, {e['interaction_point'][1]}] "
                         f"is not inside the walk polygon of '{rid}'")
            self.rect_ok(e["rect"], f"{path}({e['id']}).rect")

        for room, o, p, _ in new_rooms:
            for eo, ep in self.entries(o, "exits", p):
                e, rid = self.h.parse_exit(eo, ep, room["id"], rooms, exits_by_room, all_exit_ids, [], action_ids,
                                           speakers, self.base_ids, self.new_ids, res)
                exit_added(e, rid, ep)
        for eo, ep in self.entries(root, "exits", rp):
            e, rid = self.h.parse_exit(eo, ep, None, rooms, exits_by_room, all_exit_ids, [], action_ids, speakers,
                                       self.base_ids, self.new_ids, res)
            exit_added(e, rid, ep)
        connections = eff["connections"]
        added_connections = []
        for co, cp in self.entries(root, "connections", rp):
            c = self.h.parse_connection(co, cp, rooms, connections, action_ids, self.errors)
            if c is None:
                continue
            connections.append(c)
            added_connections.append((c["from"], c["to"]))
            res.added_connections.append((c["from"], c["to"]))
            res.added_keys |= {f"conn.{c['from']}.{c['to']}.label", f"conn.{c['from']}.{c['to']}.locked"}
        for room, _, p, _ in new_rooms:
            if not exits_by_room[room["id"]]:
                self.err(f"{p}.exits: a room needs at least one exit")

        # quests
        new_quests = []
        for o, path in self.entries(root, "quests", rp):
            qid = self.str_(o, "id", path, True)
            if qid is None:
                continue
            p = f"{path}({qid})"
            self.h.check_keys(o, p, QUEST_KEYS, self.errors)
            if not new_id(qid, p, QUEST_ID, "quest", "Q10", qid in quests):
                continue
            if (self.str_(o, "type", p) or "side") != "side":
                self.err(f"{p}.type: the world overlay adds side quests only (main quests are the handoff's)")
            title, goal = self.text(o, "title", p), self.text(o, "goal", p)
            reward = (self.text(o, "reward", p) or "") if "reward" in o else ""
            hints = self.strs(o, "hints", p)
            if len(hints) != 3:
                self.err(f"{p}.hints: exactly three hints (direction, place, the whole chain), got {len(hints)}")
            for i, hint_text in enumerate(hints):
                if not hint_text.strip() or "\n" in hint_text or "\r" in hint_text:
                    self.err(f"{p}.hints[{i}]: empty or a line break")
            qa = self.strs(o, "actions", p)
            if not qa:
                self.err(f"{p}.actions: empty")
            for a in qa:
                if a not in new_action_ids:
                    self.err(f"{p}.actions: '{a}' is not an action of this overlay (a new quest consists of new actions)")
            for a in sorted({a for a in qa if qa.count(a) > 1}):
                self.err(f"{p}.actions: '{a}' is listed twice")
            completion = self.str_(o, "completion", p, True)
            if completion is not None and completion not in qa:
                self.err(f"{p}.completion: '{completion}' is not one of the quest's actions")
            if self.boolean(o, "missable", p):
                self.err(f"{p}.missable: side quests are never missable")
            self.str_(o, "note", p)
            if None in (title, goal, completion):
                continue
            new_quests.append(({"id": qid, "title": title, "type": "side", "actions": qa, "goal": goal,
                                "completion": completion, "reward": reward, "hints": hints, "missable": False}, p))

        def party_of(cid: str) -> set[str]:
            """The character and everyone speaking in its handoff topics and in actions on its NPC hotspots."""
            people = {cid}
            for t in characters.get(cid, {}).get("ambient_topics", []):
                people |= {l["speaker"] for l in t.get("lines", [])}
            for a in eff["actions"]:
                h = hotspots.get(a.get("target", ""))
                if h and h.get("kind") == "npc" and h.get("character_id") == cid:
                    people |= {l["speaker"] for l in a.get("lines", [])}
            return people

        # actions
        new_item_ids = {i["id"] for i, _, _ in new_items}
        new_actions = []
        for o, path in self.entries(root, "actions", rp):
            aid = self.str_(o, "id", path, True)
            if aid is None:
                continue
            p = f"{path}({aid})"
            self.h.check_keys(o, p, ACTION_KEYS, self.errors)
            if not new_id(aid, p, CODE_ID, "action", "Q10A", aid in actions):
                continue
            room_id, target, kind = (self.str_(o, k, p, True) for k in ("room", "target", "kind"))
            label = self.text(o, "label", p)
            requires, excluded = self.strs(o, "requires_done", p), self.strs(o, "excluded_done", p)
            needs, gives, consumes = (self.strs(o, k, p) for k in ("requires_items", "gives", "consumes"))
            selected = self.str_(o, "selected_item", p)
            quest = self.str_(o, "quest", p, True)
            objective = self.text(o, "objective", p) if o.get("objective") is not None else None
            journal = self.text(o, "journal_text", p)
            hint_step = self.text(o, "hint_step", p)
            sfx = self.str_(o, "sfx", p)
            if sfx is not None and not SFX.match(sfx):
                self.err(f"{p}.sfx: '{sfx}' is not an sfx id (lower case, digits, '_')")
            if self.boolean(o, "once", p) is False:
                self.err(f"{p}.once: every action happens at most once")
            policy = self.str_(o, "commit_policy", p)
            if policy is not None and policy != ATOMIC:
                self.err(f"{p}.commit_policy: only '{ATOMIC}'")
            symmetric = self.boolean(o, "symmetric", p) or False
            for f in ("puzzle", "cutscene"):
                if o.get(f) is not None:
                    self.err(f"{p}.{f}: new actions cannot have a {f} (puzzles and cutscenes have their art and data in "
                             "game.json); relocate an existing puzzle action instead")
            self.str_(o, "note", p)
            if None in (room_id, target, kind, label, quest, journal, hint_step):
                continue
            for key, ids in (("requires_done", requires), ("excluded_done", excluded)):
                for i, a in enumerate(ids):
                    if a not in action_ids:
                        self.err(f"{p}.{key}[{i}]: unknown action '{a}'")
            for a in set(requires) & set(excluded):
                self.err(f"{p}: '{a}' is both required and excluded; the action could never happen")
            if aid in requires:
                self.err(f"{p}.requires_done: the action requires itself")
            for key, ids in (("requires_items", needs), ("gives", gives), ("consumes", consumes)):
                for i, it in enumerate(ids):
                    if it not in items:
                        self.err(f"{p}.{key}[{i}]: unknown item '{it}'")
            for g in gives:
                if g in items and g not in new_item_ids:
                    self.err(f"{p}.gives: '{g}' is a game.json item; it already has its one origin (a new action gives new items only)")
            for c in consumes:
                if c in items and c not in new_item_ids:
                    self.err(f"{p}.consumes: '{c}' is a game.json item; consuming it could block the story (a new action consumes new items only)")
                if c not in needs:
                    self.err(f"{p}.consumes: consumed item '{c}' is not declared in requires_items")
            for g in gives:
                if g in needs:
                    self.err(f"{p}.gives: '{g}' is also required; an action cannot need what it gives")
            if selected is not None and selected not in items:
                self.err(f"{p}.selected_item: unknown item '{selected}'")
            elif selected is not None and selected not in needs:
                self.err(f"{p}.selected_item: selected item '{selected}' is not declared in requires_items")
            if quest not in new_quest_ids:
                self.err(f"{p}.quest: '{quest}' is not a quest of this overlay (new actions belong to new side quests)")
            allowed = {"ADAM"}
            staging = {"guest_speakers": [], "rule": ""}
            if o.get("staging") is not None:
                so = o["staging"]
                if not isinstance(so, dict):
                    self.err(f"{p}.staging: must be {{guest_speakers, rule}}")
                else:
                    self.h.check_keys(so, p + ".staging", {"guest_speakers", "rule"}, self.errors)
                    guests = self.strs(so, "guest_speakers", p + ".staging")
                    for g in guests:
                        if g not in speakers:
                            self.err(f"{p}.staging.guest_speakers: unknown speaker '{g}'")
                    allowed |= set(guests)
                    staging = {"guest_speakers": guests, "rule": self.str_(so, "rule", p + ".staging") or ""}
            if kind == "combine":
                default_animation = "inventory_combine"
                if room_id != "inventory":
                    self.err(f"{p}.room: combine actions use room 'inventory'")
                if target not in items:
                    self.err(f"{p}.target: unknown item '{target}' (a combine action targets an item)")
                elif target not in needs:
                    self.err(f"{p}.requires_items: the target item '{target}' is not declared")
                if selected is None:
                    self.err(f"{p}.selected_item: a combine action names the item put on the target")
                elif selected == target:
                    self.err(f"{p}.selected_item: an item cannot be combined with itself")
            elif kind in ("click", "topic"):
                default_animation = "talk" if kind == "topic" else ("reach_mid" if selected is None else "show_item")
                if symmetric:
                    self.err(f"{p}.symmetric: only combine actions are symmetric")
                if room_id not in rooms:
                    self.err(f"{p}.room: unknown room '{room_id}'")
                elif target not in hotspots:
                    self.err(f"{p}.target: unknown hotspot '{target}'")
                elif hotspot_room[target] != room_id:
                    self.err(f"{p}.target: hotspot '{target}' is not in room '{room_id}'")
                else:
                    h = hotspots[target]
                    is_npc = h.get("kind") == "npc"
                    if kind == "topic" and (not is_npc or selected is not None):
                        self.err(f"{p}.kind: a topic is chosen in the conversation with an NPC and takes no item")
                    if kind == "click" and is_npc and selected is None:
                        self.err(f"{p}.selected_item: a left click on an NPC opens the conversation; an action on an NPC is a topic or uses an item")
                    if is_npc and h.get("character_id"):
                        allowed |= party_of(h["character_id"])
                    allowed |= npc_chars(room_id)
            else:
                self.err(f"{p}.kind: unknown action kind '{kind}' (click, topic, combine)")
                continue
            animation = self.str_(o, "animation", p) or default_animation
            if animation not in ANIMATIONS:
                self.err(f"{p}.animation: unknown animation '{animation}' (known: {', '.join(sorted(ANIMATIONS))})")
            lines = self.h.parse_lines(o, p, "action", aid, f"action.{aid}.", [], allowed, speakers, self.base_ids,
                                       self.new_ids, False, self.errors)
            if lines is None:
                continue
            used.update(l["line_id"] for l in lines)
            a = {"id": aid, "room": room_id, "target": target, "label": label, "kind": kind, "requires_done": requires,
                 "requires_items": needs, "selected_item": selected, "gives": gives, "consumes": consumes,
                 "lines": lines, "quest": quest, "puzzle": None, "cutscene": None, "once": True, "objective": objective,
                 "animation": animation, "sfx": sfx, "excluded_done": excluded, "commit_policy": ATOMIC,
                 "journal_text": journal, "staging": staging, "hint_step": hint_step}
            if kind == "combine":
                a["symmetric"] = symmetric
            new_actions.append((a, p))
        for a, _ in new_actions:
            actions[a["id"]] = a

        # relocations
        relocated: dict[str, dict] = {}
        retire = []
        base_action_ids = {a["id"] for a in eff["actions"]}
        for o, path in self.entries(root, "relocations", rp):
            aid = self.str_(o, "action", path, True)
            if aid is None:
                continue
            p = f"{path}({aid})"
            self.h.check_keys(o, p, RELOCATION_KEYS, self.errors,
                              "a relocation moves the action only; its guards, items, quest, puzzle and lines stay as they are")
            to = self.str_(o, "to_hotspot", p, True)
            hint = self.text(o, "hint_step", p)
            retire_old = self.boolean(o, "retire_hotspot", p) or False
            self.str_(o, "reason", p)
            self.str_(o, "note", p)
            if to is None or hint is None:
                continue
            if aid not in base_action_ids:
                self.err(f"{p}.action: '{aid}' is a new action; put it into its room directly" if aid in new_action_ids
                         else f"{p}.action: unknown action '{aid}'")
                continue
            if aid in relocated:
                self.err(f"{p}.action: '{aid}' is relocated twice")
                continue
            a = actions[aid]
            if a["room"] == "inventory":
                self.err(f"{p}.action: '{aid}' is a combination in the bag; it happens in no room")
                continue
            if to not in hotspots:
                self.err(f"{p}.to_hotspot: unknown hotspot '{to}'")
                continue
            to_room, from_room = rooms[hotspot_room[to]], rooms[a["room"]]
            if to_room["id"] == from_room["id"]:
                self.err(f"{p}.to_hotspot: '{to}' is in the action's own room '{from_room['id']}'; a relocation moves it to another room")
                continue
            if to_room["era"] != from_room["era"]:
                self.err(f"{p}.to_hotspot: '{to}' is in {to_room['era']}, '{aid}' happens in {from_room['era']}; a relocation stays in the same era")
                continue
            old, new = hotspots[a["target"]], hotspots[to]
            old_npc, new_npc = old.get("kind") == "npc", new.get("kind") == "npc"
            if old_npc != new_npc or (old_npc and old.get("character_id") != new.get("character_id")):
                describe = lambda h, npc: f"the NPC {h.get('character_id')}" if npc else "a prop"  # noqa: E731
                self.err(f"{p}.to_hotspot: '{a['target']}' is {describe(old, old_npc)}, '{to}' is {describe(new, new_npc)}; "
                         "the action keeps its kind of target (and its speakers)")
                continue
            moved = dict(a, room=to_room["id"], target=to, hint_step=hint)
            relocated[aid] = moved
            res.relocations.append({"action": aid, "from_room": from_room["id"], "from_hotspot": a["target"],
                                    "to_room": to_room["id"], "to_hotspot": to, "retired": retire_old})
            if retire_old:
                retire.append((a["target"], p + ".retire_hotspot"))
        for aid, a in relocated.items():
            actions[aid] = a
        effective_actions = [actions[a["id"]] for a in eff["actions"]] + [a for a, _ in new_actions]
        retired: set[str] = set()
        for hid, path in retire:
            if hid in new_hotspot_ids:
                continue
            still = [a["id"] for a in effective_actions if a["target"] == hid and a["room"] != "inventory"]
            if still:
                self.err(f"{path}: '{hid}' is still the target of {', '.join(still)}; it cannot be retired")
            elif hotspots[hid].get("kind") == "npc":
                self.err(f"{path}: '{hid}' is an NPC; people are not retired by a relocation")
            elif hid not in retired:
                retired.add(hid)
                res.retired_hotspots.append(hid)

        # epilogue, layers
        new_epilogue, new_layers = [], []
        for o, path in self.entries(root, "epilogue", rp):
            self.h.check_keys(o, path, EPILOGUE_KEYS, self.errors)
            quest, after = self.str_(o, "quest", path, True), self.str_(o, "after", path, True)
            shot, line = self.text(o, "shot", path), self.text(o, "line", path)
            self.str_(o, "note", path)
            if None in (quest, after, shot, line):
                continue
            q = next((q for q, _ in new_quests if q["id"] == quest), None)
            if q is None:
                self.err(f"{path}.quest: '{quest}' is not a quest of this overlay (game.json quests keep their own shot)")
                continue
            if after not in q["actions"]:
                self.err(f"{path}.after: '{after}' is not an action of quest '{quest}'")
            if any(e["quest"] == quest for e in new_epilogue):
                self.err(f"{path}.quest: quest '{quest}' has a second epilogue shot")
            m = re.match(r"^([A-Z][A-Z0-9_]*): ", line)
            if m and m.group(1) not in speakers:
                self.err(f"{path}.line: unknown speaker '{m.group(1)}' (write \"SPEAKER: text\")")
            new_epilogue.append({"quest": quest, "after": after, "shot": shot, "line": line})
        for o, path in self.entries(root, "visual_variant_layers", rp):
            self.h.check_keys(o, path, LAYER_KEYS, self.errors)
            rid, after, asset = (self.str_(o, k, path, True) for k in ("room", "after", "asset"))
            change = self.str_(o, "change", path) or ""
            self.str_(o, "note", path)
            if None in (rid, after, asset):
                continue
            if rid not in rooms:
                self.err(f"{path}.room: unknown room '{rid}'")
            if after not in action_ids:
                self.err(f"{path}.after: unknown action '{after}'")
            if not asset.startswith("variants/") or not ASSET.match(asset):
                self.err(f"{path}.asset: '{asset}' must be an asset path under variants/")
            if any(l["room"] == rid and l["after"] == after and l["asset"] == asset for l in eff.get("visual_variant_layers", []) + new_layers):
                self.err(f"{path}: this layer already exists")
            new_layers.append({"room": rid, "after": after, "asset": asset, "change": change})
        if len(self.errors) > start:
            return

        # assemble
        def with_npcs(room: dict, extra: list[dict]) -> list[str]:
            ids = list(room.get("npc_ids", []))
            for h in extra:
                if h.get("kind") == "npc" and h.get("character_id") and h["character_id"] not in ids:
                    ids.append(h["character_id"])
            return ids

        for room in eff["rooms"]:
            extra = added.get(room["id"], [])
            room["hotspots"] = [h for h in room.get("hotspots", []) if h["id"] not in retired] + extra
            room["exits"] = exits_by_room[room["id"]]
            room["npc_ids"] = with_npcs(room, extra)
        for room, _, p, listed in new_rooms:
            room["hotspots"] = added.get(room["id"], [])
            room["exits"] = exits_by_room[room["id"]]
            room["npc_ids"] = with_npcs(room, room["hotspots"])
            if listed is not None and sorted(listed) != sorted(room["npc_ids"]):
                self.err(f"{p}.npc_ids: [{', '.join(listed)}] but the room's NPC hotspots are [{', '.join(room['npc_ids'])}] "
                         "(leave npc_ids out: it is derived)")
            eff["rooms"].append(room)
            res.added_rooms.append(room["id"])
        where: dict[str, list[str]] = {}
        for room in eff["rooms"]:
            for h in room["hotspots"]:
                if h.get("kind") == "npc" and h.get("character_id"):
                    where.setdefault(h["character_id"], []).append(room["id"])
        for c in eff["characters"]:
            c["rooms"] = list(c.get("rooms", [])) + [r for r in where.get(c["id"], []) if r not in c.get("rooms", [])]
        for c, listed, p in new_chars:
            c["rooms"] = where.get(c["id"], [])
            if listed is not None and sorted(listed) != sorted(c["rooms"]):
                self.err(f"{p}.rooms: [{', '.join(listed)}] but the character stands in [{', '.join(c['rooms'])}] (leave rooms out: it is derived)")
            eff["characters"].append(c)
            res.added_characters.append(c["id"])
        for item, origin, p in new_items:
            givers = [a["id"] for a, _ in new_actions if item["id"] in a["gives"]]
            if not givers:
                self.err(f"{p}: no action gives item '{item['id']}'")
                continue
            if len(givers) > 1:
                self.err(f"{p}: item '{item['id']}' is given by {' and '.join(givers)}; an item has exactly one origin")
            if origin is not None and origin != givers[0]:
                self.err(f"{p}.origin: '{origin}' but '{givers[0]}' gives the item")
            item["origin"] = givers[0]
            eff["items"].append(item)
            res.added_items.append(item["id"])
        for q, p in new_quests:
            mine = [a["id"] for a, _ in new_actions if a["quest"] == q["id"]]
            for m in mine:
                if m not in q["actions"]:
                    self.err(f"{p}.actions: '{m}' has quest '{q['id']}' but is not listed")
            for a in q["actions"]:
                other = next((x for x, _ in new_actions if x["id"] == a and x["quest"] != q["id"]), None)
                if other is not None:
                    self.err(f"{p}.actions: '{a}' belongs to quest '{other['quest']}'")
            eff["quests"].append(q)
            res.added_quests.append(q["id"])
        eff["actions"] = effective_actions
        res.added_actions.extend(a["id"] for a, _ in new_actions)
        base_epilogue = len(eff.get("epilogue", []))
        eff.setdefault("epilogue", []).extend(new_epilogue)
        eff.setdefault("visual_variant_layers", []).extend(new_layers)
        if len(self.errors) > start:
            return

        # keys: every new text, and the retired hotspots' keys
        keys = res.added_keys
        keys |= {f"room.{r['id']}.name" for r, _, _, _ in new_rooms}
        for rid, hs in added.items():
            for h in hs:
                keys |= {f"hotspot.{h['id']}.name", h["look_line_id"]} | {v["line_id"] for v in h["look_variants"]}
        keys |= {f"char.{c['id']}.name" for c, _, _ in new_chars}
        for item, _, _ in new_items:
            keys |= {f"item.{item['id']}.name", item["look_line_id"], f"item.{item['id']}.purpose"}
        for a, _ in new_actions:
            keys |= {f"action.{a['id']}.label", f"action.{a['id']}.journal", f"action.{a['id']}.hint_step"}
            if a["objective"]:
                keys.add(f"action.{a['id']}.objective")
        keys |= {f"action.{aid}.hint_step" for aid in relocated}
        for q, _ in new_quests:
            keys |= {f"quest.{q['id']}.title", f"quest.{q['id']}.goal"} | {f"quest.{q['id']}.hint.{n}" for n in range(1, len(q["hints"]) + 1)}
            if q["reward"]:
                keys.add(f"quest.{q['id']}.reward")
        for n in range(base_epilogue + 1, base_epilogue + len(new_epilogue) + 1):
            keys |= {f"epilogue.{n}.shot", f"epilogue.{n}.line"}
        for hid in retired:
            h = hotspots[hid]
            res.retired_keys |= {f"hotspot.{hid}.name", h.get("look_line_id") or f"hotspot.{hid}.look"}
            res.retired_keys |= {v.get("line_id") or f"hotspot.{hid}.look.{n}" for n, v in enumerate(h.get("look_variants", []), start=1)}

        # whole-content checks
        self.h.check_edges(rp, connections, exits_by_room, added_connections, added_exits, self.errors)
        self.h.check_reachable(rp, eff, "cannot be reached", self.errors)
        touched = {a["id"] for a, _ in new_actions} | set(relocated)
        check_item_flow(rp, eff, touched, new_item_ids, self.errors)
        check_default_actions(rp, eff, touched, self.errors)


def check_item_flow(rp: str, eff: dict, touched: set[str], new_items: set[str], errors: list[str]) -> None:
    """Core CheckItemFlow: every needed item obtainable before, consumed at most once, no consumption conflict."""
    actions = {a["id"]: a for a in eff["actions"]}
    initial = set(eff.get("initial_state", {}).get("inventory", []))
    closure = dependency_closure(eff["actions"])
    postgame = eff.get("postgame", {})
    returned, unlock = set(postgame.get("return_items", [])), postgame.get("unlock")
    for a in eff["actions"]:
        if a["id"] not in touched:
            continue
        for item in dict.fromkeys(_needs(a)):
            if item in initial:
                continue
            givers = [g for g in eff["actions"] if item in g.get("gives", [])]
            if item in returned and unlock in actions:
                givers.append(actions[unlock])
            if not givers:
                errors.append(f"{rp}.actions({a['id']}): item '{item}' can never be obtained (no action gives it)")
                continue
            if all(g["id"] == a["id"] or a["id"] in closure[g["id"]] for g in givers):
                errors.append(f"{rp}.actions({a['id']}): item '{item}' comes only from {', '.join(g['id'] for g in givers)}, "
                              f"which needs '{a['id']}' first (a cycle)")
    for item in new_items:
        consumers = [c["id"] for c in eff["actions"] if item in c.get("consumes", [])]
        if len(consumers) > 1:
            errors.append(f"{rp}.items({item}): consumed by {' and '.join(consumers)}; an item that exists once is consumed once")
    for c in eff["actions"]:
        for item in c.get("consumes", []):
            for b in eff["actions"]:
                if b["id"] == c["id"] or not (b["id"] in touched or c["id"] in touched) or item not in _needs(b):
                    continue
                if b["id"] in closure[c["id"]] or c["id"] in b.get("excluded_done", []) or b["id"] in c.get("excluded_done", []):
                    continue
                if item in returned and unlock in closure[b["id"]]:
                    continue
                errors.append(f"{rp}.actions({b['id']}): needs '{item}', which '{c['id']}' consumes; done first, '{c['id']}' would make "
                              f"'{b['id']}' impossible (let '{c['id']}' require '{b['id']}', or give '{b['id']}' its own item)")


def check_default_actions(rp: str, eff: dict, touched: set[str], errors: list[str]) -> None:
    """Core CheckDefaultActions: two actions with the same trigger must never be possible at once."""
    closure = dependency_closure(eff["actions"])
    groups: dict[str, list[dict]] = {}
    for a in eff["actions"]:
        if a["kind"] == "topic":
            continue
        if a["kind"] == "combine":
            triggers = [f"combine:{a['target']}+{a.get('selected_item')}"]
            if a.get("symmetric"):
                triggers.append(f"combine:{a.get('selected_item')}+{a['target']}")
        else:
            triggers = [f"click:{a['target']}+{a.get('selected_item') or '-'}"]
        for t in triggers:
            if a not in groups.setdefault(t, []):
                groups[t].append(a)
    reported: set[tuple[str, str]] = set()
    for trigger, members in groups.items():
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                if a["id"] not in touched and b["id"] not in touched:
                    continue
                if a["id"] in closure[b["id"]] or b["id"] in closure[a["id"]] or b["id"] in a.get("excluded_done", []) or a["id"] in b.get("excluded_done", []):
                    continue
                pair = tuple(sorted((a["id"], b["id"])))
                if pair in reported:
                    continue
                reported.add(pair)
                who = b["id"] if b["id"] in touched else a["id"]
                errors.append(f"{rp}.actions({who}): '{a['id']}' and '{b['id']}' have the same trigger ({trigger}) and could both be "
                              "possible at once; one must require the other, or use another item / target")


def apply_world(eff: dict, root, base_ids: set[str], new_ids: set[str], res, helpers) -> None:
    """Apply world_ext.json to the effective game in place (errors in res.errors, bookkeeping on res)."""
    if not isinstance(root, dict):
        res.errors.append("$world_ext: the overlay must be a JSON object")
        return
    _World(eff, root, base_ids, new_ids, res, helpers).apply()
