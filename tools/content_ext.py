#!/usr/bin/env python3
"""Content-extension overlays (src/game/data/content_ext/): Python mirror of LastBell.Core's OverlayApplier.

game.json is never edited. Three overlays are applied on top of it when content loads, in this order (Core:
GameContent.Load(json, ContentOverlays); schema in src/LastBell.Core/README.md section 13):

  world_ext.json     new rooms, hotspots (also in existing rooms), characters, items, actions, side quests with
                     hints and step texts, epilogue shots, variant layers, exits and connections, and relocations
                     of existing actions to a hotspot in another room of the same era (tools/content_world.py)
  dialogue_ext.json  longer sequences for existing exchanges (action lines, ambient topic lines,
                     first-entry lines: the full play order, a plain string = an existing line id of
                     that exchange, an object {key, speaker, sk} = a new line) and new optional NPC
                     topics (id "ext.<...>" or "<CHAR>.extra <n>", label, lines, repeatable,
                     requires_done / excluded_done on existing action ids). Nothing else may be set.
  travel_ext.json    removed / added exits and connections (e.g. the 2020 bus S07 <-> S51), first-ride
                     lines of transport exits, and the map regions with their hubs.

The localization tools build their tables from the EFFECTIVE game (game.json with the overlays
applied), so every overlay text gets its key in dialogue.csv / world.csv like any other text:

    new line                     its key (e.g. action.G02.x01, topic.ELA.extra 1.001)
    new topic label              topic.<topicId>.label
    new exit / connection        exit.<exitId>.label|locked, conn.<from>.<to>.label|locked
    first-ride line              travel.<exitId>.first.<n>  (effective game: rooms[].exits[].first_ride[])
    map region                   region.<regionId>.name (ui.csv)
    world overlay                room / hotspot / item / character / action / quest / epilogue keys of the
                                 usual scheme, plus action.<id>.hint_step (tools/content_world.py)

Lines an overlay sequence drops and the texts of removed exits / connections are "retired": no
table key any more (Core still resolves dropped lines for old saves); an sk override row for a
retired key is kept and ignored, so a revert needs no edit.

Usage:
    python tools/content_ext.py check [--dialogue PATH] [--travel PATH] [--world PATH]
        validate the overlays against game.json (exit 1 on errors), print a summary. Core is the authority: it
        also plays the whole game in several orders (no softlock); run `dotnet test src/LastBell.sln` after a change
    python tools/content_ext.py merge-world DRAFT.json [--out PATH] [--dry-run]
        write a draft's world overlay (the file itself, or its "world_ext" object, e.g.
        docs/writing/out/content_v2_draft.json) to world_ext.json, validated against game.json and the live
        dialogue / travel overlays; it replaces the whole world overlay (prints what is added or dropped)
    python tools/content_ext.py merge DRAFT_ext.json [...] [--out PATH] [--dry-run]
        merge writing drafts (docs/writing/out*/<chunk>_ext.json) into dialogue_ext.json losslessly:
        their sequences, topic_extensions and topics are copied verbatim (plus a "chunk" field);
        entries of the same chunk already in the overlay are replaced, other chunks are kept. A combined draft
        merges its "dialogue_ext" object (run merge-world first when it also has a "world_ext").
        A draft's "travel" proposal is not merged (travel_ext.json is edited by the Core owner).
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_GAME_JSON = REPO_ROOT / "design-doc" / "game.json"
OVERLAY_DIR = REPO_ROOT / "src" / "game" / "data" / "content_ext"
DIALOGUE_EXT = OVERLAY_DIR / "dialogue_ext.json"
TRAVEL_EXT = OVERLAY_DIR / "travel_ext.json"
WORLD_EXT = OVERLAY_DIR / "world_ext.json"

DIALOGUE_FORMAT = "lastbell.dialogue_ext"
TRAVEL_FORMAT = "lastbell.travel_ext"
WORLD_FORMAT = "lastbell.world_ext"
TRAVEL_KINDS = {"walk", "map_transition", "car_transition", "bus", "tram", "cable_A6", "board_funitel", "arrive_funitel"}

DIALOGUE_ROOT_KEYS = {"format", "version", "about", "schema", "chunk", "note", "sources", "sequences", "topic_extensions", "topics"}
SEQUENCE_KEYS = {"id", "action", "topic", "room", "character", "kind", "lines", "note", "chunk"}
TOPIC_KEYS = {"id", "character", "label", "label_key", "speaks_first", "repeatable", "requires_done", "excluded_done",
              "lines", "note", "kind", "chunk"}
LINE_KEYS = {"key", "speaker", "sk", "note"}
TRAVEL_ROOT_KEYS = {"format", "version", "about", "note", "remove_exits", "remove_connections", "exits", "connections", "regions"}
EXIT_KEYS = {"room", "id", "to", "label", "locked_look", "travel", "requires_done", "rect", "interaction_point", "first_ride", "note"}
CONNECTION_KEYS = {"from", "to", "bidirectional", "travel", "label", "locked_look", "requires_done", "note"}
REGION_KEYS = {"id", "era", "rooms", "hubs", "note"}

LINE_SUFFIX = re.compile(r"^[A-Za-z]{0,3}\d{1,4}$")
DRAFT_TOPIC_ID = re.compile(r"^(?P<char>[A-Z][A-Z0-9_]*)\.extra \d{1,3}$")


@dataclass
class Overlay:
    """The effective game and what the overlays changed."""

    game: dict
    errors: list[str] = field(default_factory=list)
    added_line_keys: set[str] = field(default_factory=set)       # new lines incl. first-ride lines
    added_keys: set[str] = field(default_factory=set)            # every table key that only the overlays produce
    retired_keys: set[str] = field(default_factory=set)          # handoff keys the overlays removed (dropped lines,
                                                                 # labels / locked looks of removed exits and connections)
    sequences: dict[str, list[str]] = field(default_factory=dict)  # block ("action.G02", "topic.X", "entry.S07") -> play order
    dropped: dict[str, list[str]] = field(default_factory=dict)  # block -> dropped handoff line ids
    new_topics: list[str] = field(default_factory=list)
    regions: list[dict] = field(default_factory=list)
    removed_exits: list[str] = field(default_factory=list)
    added_exits: list[str] = field(default_factory=list)
    removed_connections: list[tuple[str, str]] = field(default_factory=list)
    added_connections: list[tuple[str, str]] = field(default_factory=list)
    # world overlay
    added_rooms: list[str] = field(default_factory=list)
    added_hotspots: list[str] = field(default_factory=list)
    added_characters: list[str] = field(default_factory=list)
    added_items: list[str] = field(default_factory=list)
    added_actions: list[str] = field(default_factory=list)
    added_quests: list[str] = field(default_factory=list)
    relocations: list[dict] = field(default_factory=list)
    retired_hotspots: list[str] = field(default_factory=list)
    region_hints: dict[str, tuple[str, bool]] = field(default_factory=dict)  # new room -> (region id, hub)
    used_dialogue: Path | None = None
    used_travel: Path | None = None
    used_world: Path | None = None
    consumed_region_hints: set[str] = field(default_factory=set)

    @property
    def ok(self) -> bool:
        return not self.errors


# --------------------------------------------------------------------------- loading

def read_overlay(path: Path | None) -> dict | None:
    """Parse an overlay file; a missing or blank file means no overlay."""
    if path is None or not path.exists():
        return None
    text = path.read_bytes().decode("utf-8-sig")
    if not text.strip():
        return None
    return json.loads(text)


def load_effective_game(game_path: Path = CANONICAL_GAME_JSON, dialogue: Path | None = DIALOGUE_EXT,
                        travel: Path | None = TRAVEL_EXT, use_overlays: bool = True,
                        world: Path | None = WORLD_EXT) -> Overlay:
    game = json.loads(game_path.read_bytes().decode("utf-8"))
    if not use_overlays:
        return Overlay(game=game)
    errors: list[str] = []
    parsed = {}
    for name, path in (("dialogue", dialogue), ("travel", travel), ("world", world)):
        try:
            parsed[name] = read_overlay(path)
        except json.JSONDecodeError as error:
            parsed[name] = None
            errors.append(f"${name}_ext: invalid JSON ({error})")
    result = apply_overlays(game, parsed["dialogue"], parsed["travel"], parsed["world"])
    result.errors[:0] = errors
    result.used_dialogue = dialogue if parsed["dialogue"] is not None else None
    result.used_travel = travel if parsed["travel"] is not None else None
    result.used_world = world if parsed["world"] is not None else None
    return result


# --------------------------------------------------------------------------- helpers

def _speakers(game: dict) -> set[str]:
    return {c["id"] for c in game.get("characters", [])} | set(game.get("non_actor_speakers", {}))


def _all_line_ids(game: dict) -> set[str]:
    ids: set[str] = set()

    def add(lines):
        ids.update(l["line_id"] for l in lines if l.get("line_id"))
    for a in game.get("actions", []):
        add(a.get("lines", []))
    for c in game.get("characters", []):
        for t in c.get("ambient_topics", []):
            add(t.get("lines", []))
    for r in game.get("rooms", []):
        add(r.get("first_entry", []))
    for c in game.get("cutscenes", []):
        for b in c.get("beats", []):
            add(b.get("lines", []))
    return ids


def _check_keys(obj: dict, path: str, allowed: set[str], errors: list[str], hint: str = "") -> None:
    for key in obj:
        if key not in allowed:
            errors.append(f"{path}.{key}: field not allowed in a content overlay{f' ({hint})' if hint else ''}; "
                          f"allowed: {', '.join(sorted(allowed))}")


def _str_list(obj: dict, key: str, path: str, errors: list[str]) -> list[str]:
    value = obj.get(key, [])
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        errors.append(f"{path}.{key}: must be a list of strings")
        return []
    return value


def _header(root: dict, path: str, fmt: str, errors: list[str]) -> None:
    if "format" in root and root["format"] != fmt:
        errors.append(f"{path}.format: expected {fmt!r}, got {root['format']!r}")
    if "version" in root and root["version"] != 1:
        errors.append(f"{path}.version: only version 1 is supported")


def _parse_lines(seq: dict, path: str, kind: str, owner_id: str, prefix: str, existing: list[dict],
                 allowed_speakers: set[str], speakers: set[str], base_ids: set[str], new_ids: set[str],
                 allow_existing: bool, errors: list[str]) -> list[dict] | None:
    lines_in = seq.get("lines")
    if not isinstance(lines_in, list):
        errors.append(f"{path}.lines: missing or not a list")
        return None
    if not lines_in:
        errors.append(f"{path}.lines: empty (remove the entry to keep the handoff lines)")
        return None
    by_id = {l["line_id"]: l for l in existing if l.get("line_id")}
    used: set[str] = set()
    out: list[dict] = []
    ok = True
    for i, item in enumerate(lines_in):
        lp = f"{path}.lines[{i}]"
        if isinstance(item, str):
            if not allow_existing:
                errors.append(f"{lp}: {item!r}: a new topic has no existing lines; write {{key, speaker, sk}}")
                ok = False
            elif item not in by_id:
                extra = " (lines may only be reordered within their own exchange)" if item in base_ids else ""
                errors.append(f"{lp}: {item!r} is not a line of {kind} {owner_id!r}{extra}")
                ok = False
            elif item in used:
                errors.append(f"{lp}: {item!r} is listed twice")
                ok = False
            else:
                used.add(item)
                out.append(copy.deepcopy(by_id[item]))
            continue
        if not isinstance(item, dict):
            errors.append(f"{lp}: must be an existing line id or an object {{key, speaker, sk}}")
            ok = False
            continue
        _check_keys(item, lp, LINE_KEYS, errors, "a line has only key, speaker and sk")
        key, speaker, text = item.get("key"), item.get("speaker"), item.get("sk")
        if not all(isinstance(v, str) for v in (key, speaker, text)):
            errors.append(f"{lp}: key, speaker and sk are required strings")
            ok = False
            continue
        if not key.startswith(prefix) or not LINE_SUFFIX.match(key[len(prefix):]):
            errors.append(f"{lp}.key: {key!r} must be '{prefix}<n>' (e.g. {prefix}x01)")
            ok = False
        if key in base_ids or key in new_ids:
            errors.append(f"{lp}.key: {key!r} already exists; new lines need new stable keys")
            ok = False
        new_ids.add(key)
        if speaker not in speakers:
            errors.append(f"{lp}.speaker: unknown speaker {speaker!r}")
            ok = False
        elif speaker not in allowed_speakers:
            errors.append(f"{lp}.speaker: {speaker!r} does not take part in {kind} {owner_id!r} "
                          f"(allowed: {', '.join(sorted(allowed_speakers))})")
            ok = False
        if not text.strip():
            errors.append(f"{lp}.sk: empty text")
            ok = False
        elif "\n" in text or "\r" in text:
            errors.append(f"{lp}.sk: one line is one subtitle; no line breaks")
            ok = False
        out.append({"speaker": speaker, "text": text, "line_id": key})
    return out if ok else None


# --------------------------------------------------------------------------- apply

class _Helpers:
    """The shared parsers handed to tools/content_world.py (the same rules as the travel overlay)."""

    header = staticmethod(lambda root, path, fmt, errors: _header(root, path, fmt, errors))
    check_keys = staticmethod(lambda obj, path, allowed, errors, hint="": _check_keys(obj, path, allowed, errors, hint))

    @staticmethod
    def parse_lines(seq, path, kind, owner_id, prefix, existing, allowed, speakers, base_ids, new_ids, allow_existing, errors):
        return _parse_lines(seq, path, kind, owner_id, prefix, existing, allowed, speakers, base_ids, new_ids,
                            allow_existing, errors)

    parse_exit = staticmethod(lambda *a: _parse_exit(*a))
    parse_connection = staticmethod(lambda *a: _parse_connection(*a))
    check_edges = staticmethod(lambda *a: _check_edges(*a))
    check_reachable = staticmethod(lambda *a: _check_reachable(*a))


def apply_overlays(game: dict, dialogue: dict | None, travel: dict | None, world: dict | None = None) -> Overlay:
    """Return the effective game (a deep copy) and the overlay bookkeeping; errors mirror Core's messages.
    Order as in Core: world, dialogue, travel."""
    import content_world  # noqa: E402  (same folder)

    eff = copy.deepcopy(game)
    result = Overlay(game=eff)
    new_ids: set[str] = set()
    if world is not None:
        content_world.apply_world(eff, world, _all_line_ids(game), new_ids, result, _Helpers)
        if result.errors:
            result.added_line_keys |= new_ids
            result.added_keys |= new_ids
            return result
    # Lines the world overlay added count as existing lines for the dialogue overlay (it may extend them).
    base_ids = _all_line_ids(eff)
    if dialogue is not None:
        _apply_dialogue(eff, dialogue, base_ids, new_ids, result)
    if travel is not None:
        _apply_travel(eff, travel, base_ids, new_ids, result)
    for room_id, (region, _hub) in result.region_hints.items():
        if room_id in result.consumed_region_hints or any(f"rooms({room_id}).region" in e for e in result.errors):
            continue
        era = next((r["era"] for r in eff["rooms"] if r["id"] == room_id), None)
        result.errors.append(f"$world_ext.rooms({room_id}).region: {era} has no map regions in travel_ext.json; leave 'region' "
                             "out (the room joins the region of its district) or define the regions of that era")
    result.added_line_keys |= new_ids
    result.added_keys |= new_ids
    return result


def _apply_dialogue(eff: dict, root: dict, base_ids: set[str], new_ids: set[str], res: Overlay) -> None:
    errors = res.errors
    rp = "$dialogue_ext"
    if not isinstance(root, dict):
        errors.append(f"{rp}: the overlay must be a JSON object")
        return
    _header(root, rp, DIALOGUE_FORMAT, errors)
    _check_keys(root, rp, DIALOGUE_ROOT_KEYS, errors,
                "exits and connections belong in travel_ext.json" if "travel" in root else "")
    speakers = _speakers(eff)
    action_ids = {a["id"] for a in eff["actions"]}
    actions = {a["id"]: a for a in eff["actions"]}
    hotspots = {h["id"]: h for r in eff["rooms"] for h in r.get("hotspots", [])}
    topics = {t["id"]: (c, t) for c in eff["characters"] for t in c.get("ambient_topics", [])}
    rooms = {r["id"]: r for r in eff["rooms"]}
    replacements: dict[tuple[str, str], list[dict]] = {}
    party_cache: dict[str, set[str]] = {}

    def party(cid: str) -> set[str]:
        """Adam, the character, and everyone speaking in its handoff topics and in actions on its NPC hotspots."""
        if cid not in party_cache:
            people = {"ADAM", cid}
            for c in eff["characters"]:
                if c["id"] == cid:
                    for t in c.get("ambient_topics", []):
                        people |= {l["speaker"] for l in t.get("lines", [])}
            for a in eff["actions"]:
                h = hotspots.get(a.get("target", ""))
                if h and h.get("kind") == "npc" and h.get("character_id") == cid:
                    people |= {l["speaker"] for l in a.get("lines", [])}
            party_cache[cid] = people
        return party_cache[cid]

    for list_key in ("sequences", "topic_extensions"):
        entries = root.get(list_key, [])
        if not isinstance(entries, list):
            errors.append(f"{rp}.{list_key}: must be a list")
            continue
        for i, seq in enumerate(entries):
            path = f"{rp}.{list_key}[{i}]"
            if not isinstance(seq, dict):
                errors.append(f"{path}: must be an object")
                continue
            _check_keys(seq, path, SEQUENCE_KEYS, errors, "a sequence may only set lines")
            anchors = [k for k in ("action", "topic", "room") if k in seq]
            if len(anchors) != 1:
                errors.append(f"{path}: give exactly one of 'action', 'topic' or 'room' (first-entry lines)")
                continue
            anchor = anchors[0]
            oid = seq[anchor]
            path += f"({oid})"
            if anchor == "action":
                if oid not in actions:
                    errors.append(f"{path}.action: unknown action {oid!r}")
                    continue
                a = actions[oid]
                allowed = {l["speaker"] for l in a.get("lines", [])} | {"ADAM"}
                target = hotspots.get(a.get("target", ""))
                if target and target.get("kind") == "npc" and target.get("character_id"):
                    allowed |= party(target["character_id"])
                allowed |= set((a.get("staging") or {}).get("guest_speakers", []))
                # people standing in the action's (effective) room may join in
                allowed |= set(rooms.get(a.get("room"), {}).get("npc_ids", []))
                kind, block, prefix, existing = "action", f"action.{oid}", f"action.{oid}.", a.get("lines", [])
                expected_kind = "action_lines"
            elif anchor == "topic":
                if oid not in topics:
                    errors.append(f"{path}.topic: unknown ambient topic {oid!r}")
                    continue
                c, t = topics[oid]
                if "character" in seq and seq["character"] != c["id"]:
                    errors.append(f"{path}.character: topic {oid!r} belongs to {c['id']!r}, not {seq['character']!r}")
                allowed = party(c["id"])
                kind, block, prefix, existing = "topic", f"topic.{oid}", f"topic.{oid}.", t.get("lines", [])
                expected_kind = "topic_lines"
            else:
                if oid not in rooms:
                    errors.append(f"{path}.room: unknown room {oid!r}")
                    continue
                r = rooms[oid]
                allowed = {l["speaker"] for l in r.get("first_entry", [])} | {"ADAM"}
                kind, block, prefix, existing = "room", f"entry.{oid}", f"entry.{oid}.", r.get("first_entry", [])
                expected_kind = "first_entry_lines"
            if (anchor, oid) in replacements:
                errors.append(f"{path}: {kind} {oid!r} is extended twice")
                continue
            if "kind" in seq and seq["kind"] != expected_kind:
                errors.append(f"{path}.kind: expected {expected_kind!r}, got {seq['kind']!r}")
            if "id" in seq and seq["id"] != block:
                errors.append(f"{path}.id: expected {block!r}, got {seq['id']!r}")
            lines = _parse_lines(seq, path, kind, oid, prefix, existing, allowed, speakers, base_ids, new_ids, True, errors)
            if lines is None:
                continue
            kept = {l["line_id"] for l in lines if l.get("line_id") in base_ids}
            dropped = [l["line_id"] for l in existing if l.get("line_id") and l["line_id"] not in kept]
            res.retired_keys.update(dropped)
            res.dropped[block] = dropped
            res.sequences[block] = [l["line_id"] for l in lines]
            replacements[(anchor, oid)] = lines

    topic_entries = root.get("topics", [])
    added_topics: dict[str, list[dict]] = {}
    if not isinstance(topic_entries, list):
        errors.append(f"{rp}.topics: must be a list")
        topic_entries = []
    npc_chars = {h.get("character_id") for h in hotspots.values() if h.get("kind") == "npc"}
    chars = {c["id"]: c for c in eff["characters"]}
    seen_topic_ids = set(topics)
    for i, t in enumerate(topic_entries):
        path = f"{rp}.topics[{i}]"
        if not isinstance(t, dict) or not isinstance(t.get("id"), str):
            errors.append(f"{path}: must be an object with an id")
            continue
        tid = t["id"]
        path += f"({tid})"
        _check_keys(t, path, TOPIC_KEYS, errors,
                    "a new topic may only set label, lines, repeatable, requires_done and excluded_done")
        cid = t.get("character")
        if cid not in chars:
            errors.append(f"{path}.character: unknown character {cid!r}")
            continue
        if cid not in npc_chars:
            errors.append(f"{path}.character: {cid!r} has no NPC hotspot to talk to")
            continue
        m = DRAFT_TOPIC_ID.match(tid)
        if not tid.startswith("ext.") and not (m and m.group("char") == cid):
            errors.append(f"{path}.id: a new topic id must start with 'ext.' or be '<character>.extra <n>'")
        if tid in seen_topic_ids:
            errors.append(f"{path}.id: topic id {tid!r} already exists")
            continue
        seen_topic_ids.add(tid)
        if "kind" in t and t["kind"] != "new_topic":
            errors.append(f"{path}.kind: expected 'new_topic', got {t['kind']!r}")
        label = t.get("label")
        if not isinstance(label, str) or not label.strip():
            errors.append(f"{path}.label: missing or empty")
            continue
        if "label_key" in t and t["label_key"] != f"topic.{tid}.label":
            errors.append(f"{path}.label_key: expected 'topic.{tid}.label', got {t['label_key']!r}")
        requires = _str_list(t, "requires_done", path, errors)
        excluded = _str_list(t, "excluded_done", path, errors)
        for n, a in enumerate(requires):
            if a not in action_ids:
                errors.append(f"{path}.requires_done[{n}]: unknown action {a!r}")
        for n, a in enumerate(excluded):
            if a not in action_ids:
                errors.append(f"{path}.excluded_done[{n}]: unknown action {a!r}")
        for a in set(requires) & set(excluded):
            errors.append(f"{path}: action {a!r} is both required and excluded; the topic could never be offered")
        repeatable = t.get("repeatable", True)
        if not isinstance(repeatable, bool):
            errors.append(f"{path}.repeatable: must be true or false")
            repeatable = True
        lines = _parse_lines(t, path, "topic", tid, f"topic.{tid}.", [], party(cid), _speakers(eff), base_ids,
                             new_ids, False, errors)
        if lines is None:
            continue
        if "speaks_first" in t and lines and lines[0]["speaker"] != t["speaks_first"]:
            errors.append(f"{path}.speaks_first: {t['speaks_first']!r} but the first line is spoken by {lines[0]['speaker']!r}")
        topic = {"id": tid, "label": label, "requires_done": requires, "lines": lines, "repeatable": repeatable}
        if excluded:
            topic["excluded_done"] = excluded
        added_topics.setdefault(cid, []).append(topic)
        res.new_topics.append(tid)
        res.added_keys.add(f"topic.{tid}.label")
        res.sequences[f"topic.{tid}"] = [l["line_id"] for l in lines]

    for (anchor, oid), lines in replacements.items():
        if anchor == "action":
            actions[oid]["lines"] = lines
        elif anchor == "topic":
            topics[oid][1]["lines"] = lines
        else:
            rooms[oid]["first_entry"] = lines
    for cid, new in added_topics.items():
        chars[cid].setdefault("ambient_topics", []).extend(new)


def _apply_travel(eff: dict, root: dict, base_ids: set[str], new_ids: set[str], res: Overlay) -> None:
    errors = res.errors
    rp = "$travel_ext"
    if not isinstance(root, dict):
        errors.append(f"{rp}: the overlay must be a JSON object")
        return
    start = len(errors)
    _header(root, rp, TRAVEL_FORMAT, errors)
    _check_keys(root, rp, TRAVEL_ROOT_KEYS, errors)
    rooms = {r["id"]: r for r in eff["rooms"]}
    action_ids = {a["id"] for a in eff["actions"]}
    connections = eff["connections"]
    all_exit_ids = {e["id"] for r in eff["rooms"] for e in r.get("exits", [])}
    original_exits = {e["id"]: (r["id"], e) for r in eff["rooms"] for e in r.get("exits", [])}

    for i, item in enumerate(root.get("remove_exits", [])):
        path = f"{rp}.remove_exits[{i}]"
        exit_id = item if isinstance(item, str) else item.get("exit") if isinstance(item, dict) else None
        if isinstance(item, dict):
            _check_keys(item, path, {"exit", "reason"}, errors)
        if exit_id not in original_exits:
            errors.append(f"{path}: unknown exit {exit_id!r}")
            continue
        room_id, _ = original_exits[exit_id]
        rooms[room_id]["exits"] = [e for e in rooms[room_id]["exits"] if e["id"] != exit_id]
        res.removed_exits.append(exit_id)
        res.retired_keys |= {f"exit.{exit_id}.label", f"exit.{exit_id}.locked"}
    for i, item in enumerate(root.get("remove_connections", [])):
        path = f"{rp}.remove_connections[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{path}: must be {{from, to, reason}}")
            continue
        _check_keys(item, path, {"from", "to", "reason"}, errors)
        found = next((c for c in connections if c["from"] == item.get("from") and c["to"] == item.get("to")), None)
        if found is None:
            errors.append(f"{path}: no connection {item.get('from')}->{item.get('to')} in game.json")
            continue
        connections.remove(found)
        res.removed_connections.append((found["from"], found["to"]))
        res.retired_keys |= {f"conn.{found['from']}.{found['to']}.label", f"conn.{found['from']}.{found['to']}.locked"}

    added_exits = []
    exits_by_room = {rid: r["exits"] for rid, r in rooms.items()}
    for i, ex in enumerate(root.get("exits", [])):
        path = f"{rp}.exits[{i}]"
        if not isinstance(ex, dict):
            errors.append(f"{path}: must be an object with an id")
            continue
        new_exit, room_id = _parse_exit(ex, path, None, rooms, exits_by_room, all_exit_ids, res.removed_exits,
                                        action_ids, _speakers(eff), base_ids, new_ids, res)
        if new_exit is not None:
            added_exits.append((room_id, new_exit))

    added_connections = []
    for i, c in enumerate(root.get("connections", [])):
        path = f"{rp}.connections[{i}]"
        if not isinstance(c, dict):
            errors.append(f"{path}: must be an object")
            continue
        new_c = _parse_connection(c, path, rooms, connections, action_ids, errors)
        if new_c is None:
            continue
        connections.append(new_c)
        added_connections.append((new_c["from"], new_c["to"]))
        res.added_connections.append((new_c["from"], new_c["to"]))
        res.added_keys |= {f"conn.{new_c['from']}.{new_c['to']}.label", f"conn.{new_c['from']}.{new_c['to']}.locked"}
    if len(errors) > start:
        return

    def linked(x: str, y: str) -> bool:
        return any((c["from"] == x and c["to"] == y) or (c.get("bidirectional") and c["from"] == y and c["to"] == x)
                   for c in connections)

    _check_edges(rp, connections, exits_by_room, added_connections, added_exits, errors)
    for a, b in res.removed_connections:
        for x, y in ((a, b), (b, a)):
            stale = next((e for e in rooms[x]["exits"] if e["to"] == y), None)
            if stale is not None and not linked(x, y):
                errors.append(f"{rp}.remove_connections({a}->{b}): exit {stale['id']!r} still leads there; add it to remove_exits")
    for exit_id in res.removed_exits:
        room_id, e = original_exits[exit_id]
        if linked(room_id, e["to"]):
            errors.append(f"{rp}.remove_exits({exit_id}): connection {room_id}<->{e['to']} still exists")

    _check_reachable(rp, eff, "can no longer be reached", errors)
    _apply_regions(eff, root, res)


def _parse_exit(ex: dict, path: str, own_room: str | None, rooms: dict, exits_by_room: dict, all_exit_ids: set,
                removed: list, action_ids: set, speakers: set, base_ids: set, new_ids: set, res: Overlay):
    """One added exit (travel_ext exits[], world_ext exits[] and rooms[].exits[]); returns (exit, room id) or (None, None)."""
    errors = res.errors
    if not isinstance(ex.get("id"), str):
        errors.append(f"{path}: must be an object with an id")
        return None, None
    eid = ex["id"]
    path += f"({eid})"
    _check_keys(ex, path, EXIT_KEYS - {"room"} if own_room else EXIT_KEYS, errors)
    required = ("to", "label", "locked_look", "travel", "rect", "interaction_point") + (() if own_room else ("room",))
    missing = [k for k in required if k not in ex]
    if missing:
        errors.append(f"{path}: missing {', '.join(missing)}")
        return None, None
    room_id, to = own_room or ex["room"], ex["to"]
    if room_id not in rooms or to not in rooms:
        errors.append(f"{path}: unknown room {room_id if room_id not in rooms else to!r}")
        return None, None
    if to == room_id:
        errors.append(f"{path}.to: an exit cannot lead into its own room")
    if rooms[to]["era"] != rooms[room_id]["era"]:
        errors.append(f"{path}.to: {to!r} is in another era; eras are changed only by the chronometer")
    if eid != f"{room_id}.to_{to}":
        errors.append(f"{path}.id: expected '{room_id}.to_{to}'")
    if eid in all_exit_ids and eid not in removed:
        errors.append(f"{path}.id: exit {eid!r} already exists")
    all_exit_ids.add(eid)
    if any(e["to"] == to for e in exits_by_room[room_id]):
        errors.append(f"{path}: room {room_id!r} already has an exit to {to!r}")
    if ex["travel"] not in TRAVEL_KINDS:
        errors.append(f"{path}.travel: unknown travel style {ex['travel']!r}")
    requires = _str_list(ex, "requires_done", path, errors)
    for n, a in enumerate(requires):
        if a not in action_ids:
            errors.append(f"{path}.requires_done[{n}]: unknown action {a!r}")
    ok = True
    if not (isinstance(ex["rect"], list) and len(ex["rect"]) == 4 and all(isinstance(v, int) for v in ex["rect"])):
        errors.append(f"{path}.rect: must have 4 integers")
        ok = False
    if not (isinstance(ex["interaction_point"], list) and len(ex["interaction_point"]) == 2):
        errors.append(f"{path}.interaction_point: must have 2 integers")
        ok = False
    for k in ("label", "locked_look"):
        if not isinstance(ex[k], str) or not ex[k].strip():
            errors.append(f"{path}.{k}: empty")
    new_exit = {"id": eid, "to": to, "label": ex["label"], "requires_done": requires, "travel": ex["travel"],
                "locked_look": ex["locked_look"], "rect": ex["rect"], "interaction_point": ex["interaction_point"]}
    ride = ex.get("first_ride")
    if ride is not None:
        rpth = path + ".first_ride"
        if not isinstance(ride, dict):
            errors.append(f"{rpth}: must be {{lines: [...]}}")
        else:
            _check_keys(ride, rpth, {"id", "lines", "note"}, errors)
            if "id" in ride and ride["id"] != f"travel.{eid}.first":
                errors.append(f"{rpth}.id: expected 'travel.{eid}.first'")
            lines = _parse_lines(ride, rpth, "first ride", eid, f"travel.{eid}.first.", [], {"ADAM"},
                                 speakers, base_ids, new_ids, False, errors)
            if lines is not None:
                new_exit["first_ride"] = lines
    exits_by_room[room_id].append(new_exit)
    res.added_exits.append(eid)
    res.added_keys |= {f"exit.{eid}.label", f"exit.{eid}.locked"}
    return (new_exit, room_id) if ok else (None, None)


def _parse_connection(c: dict, path: str, rooms: dict, connections: list, action_ids: set, errors: list[str]):
    """One added connection (travel_ext and world_ext connections[]); None on an unusable entry."""
    _check_keys(c, path, CONNECTION_KEYS, errors)
    a, b = c.get("from"), c.get("to")
    path += f"({a}->{b})"
    if a not in rooms or b not in rooms:
        errors.append(f"{path}: unknown room")
        return None
    if rooms[a]["era"] != rooms[b]["era"]:
        errors.append(f"{path}: connections stay inside one era")
    if any({x["from"], x["to"]} == {a, b} for x in connections):
        errors.append(f"{path}: a connection between {a!r} and {b!r} already exists")
    if c.get("travel") not in TRAVEL_KINDS:
        errors.append(f"{path}.travel: unknown travel style {c.get('travel')!r}")
    requires = _str_list(c, "requires_done", path, errors)
    for n, x in enumerate(requires):
        if x not in action_ids:
            errors.append(f"{path}.requires_done[{n}]: unknown action {x!r}")
    for k in ("label", "locked_look"):
        if not isinstance(c.get(k), str) or not c[k].strip():
            errors.append(f"{path}.{k}: missing or empty")
    return {"from": a, "to": b, "requires_done": requires, "bidirectional": c.get("bidirectional", True),
            "travel": c.get("travel"), "label": c.get("label", ""), "locked_look": c.get("locked_look", "")}


def _check_edges(rp: str, connections: list, exits_by_room: dict, added_connections, added_exits, errors: list[str]) -> None:
    """Exits and connections describe the same edges (Core CheckEdges)."""
    def linked(x: str, y: str) -> bool:
        return any((c["from"] == x and c["to"] == y) or (c.get("bidirectional") and c["from"] == y and c["to"] == x)
                   for c in connections)

    for a, b in added_connections:
        c = next(x for x in connections if x["from"] == a and x["to"] == b)
        for x, y in ((a, b), (b, a)) if c.get("bidirectional") else ((a, b),):
            e = next((e for e in exits_by_room[x] if e["to"] == y), None)
            if e is None:
                errors.append(f"{rp}.connections({a}->{b}): room {x!r} needs an exit to {y!r} in exits")
            elif e["travel"] != c["travel"] or e.get("requires_done", []) != c["requires_done"]:
                errors.append(f"{rp}.exits({e['id']}): travel and requires_done must equal those of connection {a}->{b}")
    for room_id, e in added_exits:
        if not linked(room_id, e["to"]):
            errors.append(f"{rp}.exits({e['id']}): no connection leads from {room_id!r} to {e['to']!r}; add one in connections")


def _check_reachable(rp: str, eff: dict, what: str, errors: list[str]) -> None:
    """Every room stays reachable from its era's time node over the (ungated) graph."""
    for era in eff["eras"]:
        seen, todo = {era["anchor"]}, [era["anchor"]]
        while todo:
            r = todo.pop()
            for c in eff["connections"]:
                for x, y in ((c["from"], c["to"]), (c["to"], c["from"]) if c.get("bidirectional") else (None, None)):
                    if x == r and y not in seen:
                        seen.add(y)
                        todo.append(y)
        for r in eff["rooms"]:
            if r["era"] == era["year"] and r["id"] not in seen:
                errors.append(f"{rp}: room {r['id']!r} {what} from the {era['year']} time node {era['anchor']!r}")


def _apply_regions(eff: dict, root: dict, res: Overlay) -> None:
    errors = res.errors
    rp = "$travel_ext"
    rooms = {r["id"]: r for r in eff["rooms"]}
    years = {e["year"] for e in eff["eras"]}
    region_of: dict[str, dict] = {}
    regions: list[dict] = []
    hinted = {r: h for r, h in res.region_hints.items() if r in rooms}
    for i, g in enumerate(root.get("regions", [])):
        path = f"{rp}.regions[{i}]"
        if not isinstance(g, dict) or not isinstance(g.get("id"), str):
            errors.append(f"{path}: must be an object with an id")
            continue
        path += f"({g['id']})"
        _check_keys(g, path, REGION_KEYS, errors)
        era = g.get("era")
        if era not in years:
            errors.append(f"{path}.era: unknown era {era!r}")
            continue
        if not g["id"].strip() or "." in g["id"]:
            errors.append(f"{path}.id: a region id is a plain name without dots")
        if any(r["era"] == era and r["id"] == g["id"] for r in regions):
            errors.append(f"{path}.id: region {g['id']!r} is defined twice in {era}")
        members = list(_str_list(g, "rooms", path, errors))
        hubs = list(_str_list(g, "hubs", path, errors))
        for room_id, (region, hub) in hinted.items():
            if rooms[room_id]["era"] != era:
                continue
            if region == g["id"]:
                if room_id not in members:
                    members.append(room_id)
                if hub and room_id not in hubs:
                    hubs.append(room_id)
                elif not hub and room_id in hubs:
                    errors.append(f"{path}.hubs: {room_id!r} is a hub here but $world_ext.rooms({room_id}).hub is false")
            elif room_id in members:
                errors.append(f"{path}.rooms: {room_id!r} is listed here but $world_ext.rooms({room_id}).region is {region!r}")
        if not members:
            errors.append(f"{path}.rooms: empty")
        if not hubs:
            errors.append(f"{path}.hubs: a region needs at least one hub")
        region = {"id": g["id"], "era": era, "rooms": members, "hubs": hubs}
        for r in members:
            if r not in rooms:
                errors.append(f"{path}.rooms: unknown room {r!r}")
            elif rooms[r]["era"] != era:
                errors.append(f"{path}.rooms: {r!r} is in {rooms[r]['era']}, not {era}")
            elif r in region_of:
                errors.append(f"{path}.rooms: {r!r} already belongs to region {region_of[r]['id']!r}")
            else:
                region_of[r] = region
        for h in hubs:
            if h not in members:
                errors.append(f"{path}.hubs: hub {h!r} is not one of the region's rooms")
        regions.append(region)
    for era in {r["era"] for r in regions}:
        for room in eff["rooms"]:
            if room["era"] == era and room["id"] not in region_of:
                if room["id"] in hinted:
                    names = ", ".join(r["id"] for r in regions if r["era"] == era)
                    errors.append(f"$world_ext.rooms({room['id']}).region: {hinted[room['id']][0]!r} is not a region of {era} "
                                  f"in travel_ext.json (regions: {names})")
                else:
                    errors.append(f"{rp}.regions: room {room['id']!r} of {era} belongs to no region")
    res.consumed_region_hints |= {r for r in hinted if r in region_of}
    for c in eff["connections"]:
        a, b = region_of.get(c["from"]), region_of.get(c["to"])
        if a is None or b is None or a is b:
            continue
        if c["from"] not in a["hubs"] or c["to"] not in b["hubs"]:
            errors.append(f"{rp}.regions: connection {c['from']}->{c['to']} joins region {a['id']!r} and {b['id']!r} "
                          "but not hub to hub; far places are reached through their transport hub")
    res.regions = regions


def region_ids(overlay: Overlay) -> set[str]:
    """Region ids the map uses: travel_ext regions plus the districts of eras without regions."""
    eras_with = {r["era"] for r in overlay.regions}
    ids = {r["id"] for r in overlay.regions}
    ids |= {room.get("district", "") for room in overlay.game["rooms"] if room["era"] not in eras_with} - {""}
    return ids


# --------------------------------------------------------------------------- CLI

def _shown(path: Path | None) -> str:
    if path is None:
        return "-"
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _summary(o: Overlay) -> None:
    print(f"dialogue overlay: {_shown(o.used_dialogue)}; travel overlay: {_shown(o.used_travel)}")
    blocks = [b for b in o.sequences if not any(b == f"topic.{t}" for t in o.new_topics)]
    print(f"extended exchanges: {len(blocks)} ({sum(1 for b in blocks if b.startswith('action.'))} actions, "
          f"{sum(1 for b in blocks if b.startswith('topic.'))} topics, {sum(1 for b in blocks if b.startswith('entry.'))} first entries); "
          f"new topics: {len(o.new_topics)}; new lines: {len(o.added_line_keys)}; retired handoff lines: {len(o.retired_keys)}")
    print(f"exits removed {o.removed_exits}, added {o.added_exits}; connections removed {o.removed_connections}, "
          f"added {o.added_connections}; regions: {len(o.regions)}")
    print(f"world overlay: {_shown(o.used_world)}; rooms +{o.added_rooms}, "
          f"hotspots +{len(o.added_hotspots)}, characters +{o.added_characters}, items +{o.added_items}, "
          f"actions +{o.added_actions}, quests +{o.added_quests}, relocations "
          f"{[r['action'] + ' ' + r['from_room'] + '->' + r['to_room'] for r in o.relocations]}, retired hotspots {o.retired_hotspots}")


def cmd_check(args) -> int:
    o = load_effective_game(dialogue=args.dialogue, travel=args.travel, world=args.world)
    _summary(o)
    for e in o.errors:
        print(f"  ERROR {e}")
    print("RESULT: " + ("OK" if o.ok else "FAILED"))
    return 0 if o.ok else 1


def cmd_merge(args) -> int:
    out: Path = args.out
    current = read_overlay(out) or {}
    merged = {
        "format": DIALOGUE_FORMAT,
        "version": 1,
        "about": current.get("about", "Dialogue overlay on top of game.json (never edited): longer sequences and extra "
                                      "optional NPC topics, written per design-doc/WRITING_METHOD.md. Schema: "
                                      "src/LastBell.Core/README.md section 13. Built by tools/content_ext.py merge."),
        "sources": list(current.get("sources", [])),
        "sequences": list(current.get("sequences", [])),
        "topic_extensions": list(current.get("topic_extensions", [])),
        "topics": list(current.get("topics", [])),
    }
    for draft_path in args.drafts:
        whole = json.loads(draft_path.read_text(encoding="utf-8"))
        # A combined content draft carries its dialogue part as "dialogue_ext" (the "world_ext" part: merge-world).
        draft = whole["dialogue_ext"] if isinstance(whole.get("dialogue_ext"), dict) else whole
        chunk = draft.get("chunk") or whole.get("chunk") or draft_path.stem.replace("_ext", "")
        rel = _shown(draft_path)
        for key in ("sequences", "topic_extensions", "topics"):
            merged[key] = [e for e in merged[key] if e.get("chunk") != chunk]
            for entry in draft.get(key, []):
                e = {"chunk": chunk}
                e.update(entry)
                merged[key].append(e)
        merged["sources"] = [s for s in merged["sources"] if s.get("chunk") != chunk] + [{"chunk": chunk, "file": rel}]
        skipped = [k for k in draft if k not in DIALOGUE_ROOT_KEYS]
        if draft is not whole:
            skipped += [k for k in whole if k not in ("dialogue_ext", "chunk")]
        print(f"{rel}: chunk {chunk}: {len(draft.get('sequences', []))} sequences, "
              f"{len(draft.get('topic_extensions', []))} topic extensions, {len(draft.get('topics', []))} topics"
              + (f"; not merged: {skipped} (world_ext: merge-world; travel texts go to travel_ext.json)" if skipped else ""))
    # Validate the result before writing.
    game = json.loads(CANONICAL_GAME_JSON.read_text(encoding="utf-8"))
    check = apply_overlays(game, merged, read_overlay(TRAVEL_EXT), read_overlay(WORLD_EXT))
    for e in check.errors:
        print(f"  ERROR {e}")
    if check.errors:
        if any(isinstance(json.loads(p.read_text(encoding="utf-8")).get("world_ext"), dict) for p in args.drafts):
            print("  hint: the draft has a world_ext part; run `python tools/content_ext.py merge-world <draft>` first")
        print("RESULT: FAILED (nothing written)")
        return 1
    text = json.dumps(merged, ensure_ascii=False, indent=1) + "\n"
    if args.dry_run:
        print(f"would write {out} ({len(text)} bytes)")
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(text.encode("utf-8"))
        print(f"wrote {out.relative_to(REPO_ROOT).as_posix()}")
    print("RESULT: OK")
    return 0


def cmd_merge_world(args) -> int:
    """Write a draft's world overlay (the whole file, or its "world_ext" part) to world_ext.json after validation."""
    whole = json.loads(args.draft.read_text(encoding="utf-8"))
    draft = whole["world_ext"] if isinstance(whole.get("world_ext"), dict) else whole
    draft = {"format": WORLD_FORMAT, "version": 1, **{k: v for k, v in draft.items() if k not in ("format", "version")}}
    current = read_overlay(args.out) or {}
    game = json.loads(CANONICAL_GAME_JSON.read_text(encoding="utf-8"))
    check = apply_overlays(game, read_overlay(DIALOGUE_EXT), read_overlay(TRAVEL_EXT), draft)
    for e in check.errors:
        print(f"  ERROR {e}")
    before = apply_overlays(game, None, None, current) if current else Overlay(game=game)
    for what in ("added_rooms", "added_characters", "added_items", "added_actions", "added_quests"):
        old, new = set(getattr(before, what)), set(getattr(check, what))
        if old != new:
            print(f"{what[6:]}: +{sorted(new - old)} -{sorted(old - new)}")
    print(f"relocations: {[r['action'] + ' ' + r['from_room'] + '->' + r['to_room'] for r in check.relocations]}")
    if check.errors:
        print("RESULT: FAILED (nothing written)")
        return 1
    text = json.dumps(draft, ensure_ascii=False, indent=1) + "\n"
    if args.dry_run:
        print(f"would write {_shown(args.out)} ({len(text)} bytes)")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(text.encode("utf-8"))
        print(f"wrote {_shown(args.out)} (replaces the whole world overlay)")
    print("RESULT: OK (Core also checks playability: run dotnet test src/LastBell.sln, then tools/extract_strings.py)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check", help="validate the overlays")
    p.add_argument("--dialogue", type=Path, default=DIALOGUE_EXT)
    p.add_argument("--travel", type=Path, default=TRAVEL_EXT)
    p.add_argument("--world", type=Path, default=WORLD_EXT)
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("merge", help="merge writing drafts into dialogue_ext.json")
    p.add_argument("drafts", nargs="+", type=Path)
    p.add_argument("--out", type=Path, default=DIALOGUE_EXT)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_merge)
    p = sub.add_parser("merge-world", help="write a draft's world overlay to world_ext.json (validated)")
    p.add_argument("draft", type=Path)
    p.add_argument("--out", type=Path, default=WORLD_EXT)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_merge_world)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
