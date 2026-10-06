#!/usr/bin/env python3
"""Content-extension overlays (src/game/data/content_ext/): Python mirror of LastBell.Core's OverlayApplier.

game.json is never edited. Two overlays are applied on top of it when content loads (Core:
GameContent.Load(json, ContentOverlays); schema in src/LastBell.Core/README.md section 13):

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

Lines an overlay sequence drops and the texts of removed exits / connections are "retired": no
table key any more (Core still resolves dropped lines for old saves); an sk override row for a
retired key is kept and ignored, so a revert needs no edit.

Usage:
    python tools/content_ext.py check [--dialogue PATH] [--travel PATH]
        validate the overlays against game.json (exit 1 on errors), print a summary
    python tools/content_ext.py merge DRAFT_ext.json [...] [--out PATH] [--dry-run]
        merge writing drafts (docs/writing/out*/<chunk>_ext.json) into dialogue_ext.json losslessly:
        their sequences, topic_extensions and topics are copied verbatim (plus a "chunk" field);
        entries of the same chunk already in the overlay are replaced, other chunks are kept.
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

DIALOGUE_FORMAT = "lastbell.dialogue_ext"
TRAVEL_FORMAT = "lastbell.travel_ext"
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
    used_dialogue: Path | None = None
    used_travel: Path | None = None

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
                        travel: Path | None = TRAVEL_EXT, use_overlays: bool = True) -> Overlay:
    game = json.loads(game_path.read_bytes().decode("utf-8"))
    if not use_overlays:
        return Overlay(game=game)
    errors: list[str] = []
    try:
        d = read_overlay(dialogue)
    except json.JSONDecodeError as error:
        d, _ = None, errors.append(f"$dialogue_ext: invalid JSON ({error})")
    try:
        t = read_overlay(travel)
    except json.JSONDecodeError as error:
        t, _ = None, errors.append(f"$travel_ext: invalid JSON ({error})")
    result = apply_overlays(game, d, t)
    result.errors[:0] = errors
    result.used_dialogue = dialogue if d is not None else None
    result.used_travel = travel if t is not None else None
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

def apply_overlays(game: dict, dialogue: dict | None, travel: dict | None) -> Overlay:
    """Return the effective game (a deep copy) and the overlay bookkeeping; errors mirror Core's messages."""
    eff = copy.deepcopy(game)
    result = Overlay(game=eff)
    base_ids = _all_line_ids(game)
    new_ids: set[str] = set()
    if dialogue is not None:
        _apply_dialogue(eff, dialogue, base_ids, new_ids, result)
    if travel is not None:
        _apply_travel(eff, travel, base_ids, new_ids, result)
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
    for i, ex in enumerate(root.get("exits", [])):
        path = f"{rp}.exits[{i}]"
        if not isinstance(ex, dict) or not isinstance(ex.get("id"), str):
            errors.append(f"{path}: must be an object with an id")
            continue
        eid = ex["id"]
        path += f"({eid})"
        _check_keys(ex, path, EXIT_KEYS, errors)
        missing = [k for k in ("room", "to", "label", "locked_look", "travel", "rect", "interaction_point") if k not in ex]
        if missing:
            errors.append(f"{path}: missing {', '.join(missing)}")
            continue
        room_id, to = ex["room"], ex["to"]
        if room_id not in rooms or to not in rooms:
            errors.append(f"{path}: unknown room {room_id if room_id not in rooms else to!r}")
            continue
        if to == room_id:
            errors.append(f"{path}.to: an exit cannot lead into its own room")
        if rooms[to]["era"] != rooms[room_id]["era"]:
            errors.append(f"{path}.to: {to!r} is in another era; eras are changed only by the chronometer")
        if eid != f"{room_id}.to_{to}":
            errors.append(f"{path}.id: expected '{room_id}.to_{to}'")
        if eid in all_exit_ids and eid not in res.removed_exits:
            errors.append(f"{path}.id: exit {eid!r} already exists")
        if any(e["to"] == to for e in rooms[room_id]["exits"]):
            errors.append(f"{path}: room {room_id!r} already has an exit to {to!r}")
        if ex["travel"] not in TRAVEL_KINDS:
            errors.append(f"{path}.travel: unknown travel style {ex['travel']!r}")
        requires = _str_list(ex, "requires_done", path, errors)
        for n, a in enumerate(requires):
            if a not in action_ids:
                errors.append(f"{path}.requires_done[{n}]: unknown action {a!r}")
        if not (isinstance(ex["rect"], list) and len(ex["rect"]) == 4 and all(isinstance(v, int) for v in ex["rect"])):
            errors.append(f"{path}.rect: must have 4 integers")
        if not (isinstance(ex["interaction_point"], list) and len(ex["interaction_point"]) == 2):
            errors.append(f"{path}.interaction_point: must have 2 integers")
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
                                     _speakers(eff), base_ids, new_ids, False, errors)
                if lines is not None:
                    new_exit["first_ride"] = lines
        rooms[room_id]["exits"].append(new_exit)
        added_exits.append((room_id, new_exit))
        res.added_exits.append(eid)
        res.added_keys |= {f"exit.{eid}.label", f"exit.{eid}.locked"}

    for i, c in enumerate(root.get("connections", [])):
        path = f"{rp}.connections[{i}]"
        if not isinstance(c, dict):
            errors.append(f"{path}: must be an object")
            continue
        _check_keys(c, path, CONNECTION_KEYS, errors)
        a, b = c.get("from"), c.get("to")
        path += f"({a}->{b})"
        if a not in rooms or b not in rooms:
            errors.append(f"{path}: unknown room")
            continue
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
        connections.append({"from": a, "to": b, "requires_done": requires, "bidirectional": c.get("bidirectional", True),
                            "travel": c.get("travel"), "label": c.get("label", ""), "locked_look": c.get("locked_look", "")})
        res.added_connections.append((a, b))
        res.added_keys |= {f"conn.{a}.{b}.label", f"conn.{a}.{b}.locked"}
    if len(errors) > start:
        return

    def linked(x: str, y: str) -> bool:
        return any((c["from"] == x and c["to"] == y) or (c.get("bidirectional") and c["from"] == y and c["to"] == x)
                   for c in connections)

    for a, b in res.added_connections:
        c = next(x for x in connections if x["from"] == a and x["to"] == b)
        for x, y in ((a, b), (b, a)) if c.get("bidirectional") else ((a, b),):
            e = next((e for e in rooms[x]["exits"] if e["to"] == y), None)
            if e is None:
                errors.append(f"{rp}.connections({a}->{b}): room {x!r} needs an exit to {y!r} in exits")
            elif e["travel"] != c["travel"] or e.get("requires_done", []) != c["requires_done"]:
                errors.append(f"{rp}.exits({e['id']}): travel and requires_done must equal those of connection {a}->{b}")
    for room_id, e in added_exits:
        if not linked(room_id, e["to"]):
            errors.append(f"{rp}.exits({e['id']}): no connection leads from {room_id!r} to {e['to']!r}")
    for a, b in res.removed_connections:
        for x, y in ((a, b), (b, a)):
            stale = next((e for e in rooms[x]["exits"] if e["to"] == y), None)
            if stale is not None and not linked(x, y):
                errors.append(f"{rp}.remove_connections({a}->{b}): exit {stale['id']!r} still leads there; add it to remove_exits")
    for exit_id in res.removed_exits:
        room_id, e = original_exits[exit_id]
        if linked(room_id, e["to"]):
            errors.append(f"{rp}.remove_exits({exit_id}): connection {room_id}<->{e['to']} still exists")

    for era in eff["eras"]:
        seen, todo = {era["anchor"]}, [era["anchor"]]
        while todo:
            r = todo.pop()
            for c in connections:
                for x, y in ((c["from"], c["to"]), (c["to"], c["from"]) if c.get("bidirectional") else (None, None)):
                    if x == r and y not in seen:
                        seen.add(y)
                        todo.append(y)
        for r in eff["rooms"]:
            if r["era"] == era["year"] and r["id"] not in seen:
                errors.append(f"{rp}: room {r['id']!r} can no longer be reached from the {era['year']} time node {era['anchor']!r}")

    _apply_regions(eff, root, res)


def _apply_regions(eff: dict, root: dict, res: Overlay) -> None:
    errors = res.errors
    rp = "$travel_ext"
    rooms = {r["id"]: r for r in eff["rooms"]}
    years = {e["year"] for e in eff["eras"]}
    region_of: dict[str, dict] = {}
    regions: list[dict] = []
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
        members = _str_list(g, "rooms", path, errors)
        hubs = _str_list(g, "hubs", path, errors)
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
                errors.append(f"{rp}.regions: room {room['id']!r} of {era} belongs to no region")
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

def _summary(o: Overlay) -> None:
    print(f"dialogue overlay: {o.used_dialogue.relative_to(REPO_ROOT).as_posix() if o.used_dialogue else '-'}; "
          f"travel overlay: {o.used_travel.relative_to(REPO_ROOT).as_posix() if o.used_travel else '-'}")
    blocks = [b for b in o.sequences if not any(b == f"topic.{t}" for t in o.new_topics)]
    print(f"extended exchanges: {len(blocks)} ({sum(1 for b in blocks if b.startswith('action.'))} actions, "
          f"{sum(1 for b in blocks if b.startswith('topic.'))} topics, {sum(1 for b in blocks if b.startswith('entry.'))} first entries); "
          f"new topics: {len(o.new_topics)}; new lines: {len(o.added_line_keys)}; retired handoff lines: {len(o.retired_keys)}")
    print(f"exits removed {o.removed_exits}, added {o.added_exits}; connections removed {o.removed_connections}, "
          f"added {o.added_connections}; regions: {len(o.regions)}")


def cmd_check(args) -> int:
    o = load_effective_game(dialogue=args.dialogue, travel=args.travel)
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
        draft = json.loads(draft_path.read_text(encoding="utf-8"))
        chunk = draft.get("chunk") or draft_path.stem.replace("_ext", "")
        rel = draft_path.resolve().relative_to(REPO_ROOT).as_posix()
        for key in ("sequences", "topic_extensions", "topics"):
            merged[key] = [e for e in merged[key] if e.get("chunk") != chunk]
            for entry in draft.get(key, []):
                e = {"chunk": chunk}
                e.update(entry)
                merged[key].append(e)
        merged["sources"] = [s for s in merged["sources"] if s.get("chunk") != chunk] + [{"chunk": chunk, "file": rel}]
        skipped = [k for k in draft if k not in DIALOGUE_ROOT_KEYS]
        print(f"{rel}: chunk {chunk}: {len(draft.get('sequences', []))} sequences, "
              f"{len(draft.get('topic_extensions', []))} topic extensions, {len(draft.get('topics', []))} topics"
              + (f"; not merged: {skipped} (travel texts go to travel_ext.json)" if skipped else ""))
    # Validate the result before writing.
    game = json.loads(CANONICAL_GAME_JSON.read_text(encoding="utf-8"))
    check = apply_overlays(game, merged, read_overlay(TRAVEL_EXT))
    for e in check.errors:
        print(f"  ERROR {e}")
    if check.errors:
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check", help="validate the overlays")
    p.add_argument("--dialogue", type=Path, default=DIALOGUE_EXT)
    p.add_argument("--travel", type=Path, default=TRAVEL_EXT)
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("merge", help="merge writing drafts into dialogue_ext.json")
    p.add_argument("drafts", nargs="+", type=Path)
    p.add_argument("--out", type=Path, default=DIALOGUE_EXT)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_merge)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
