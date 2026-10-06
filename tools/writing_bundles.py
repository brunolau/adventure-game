#!/usr/bin/env python3
"""Write the context bundles for the Slovak text rewrite (docs/writing/).

Every player-visible text key of the three localization tables is assigned to exactly one
writing chunk:

    C1  2020: rooms S01-S10 and S51-S56 and everything that happens there
    C2  1995: rooms S11-S30
    C3  1960 + 1982: rooms S31-S40 and S57-S66
    C4  2035: rooms S41-S50, S67, S68, plus all cutscenes, the epilogue, speaker names that
        belong to no room, the game title and every ui.csv string (menus, HUD, system texts)

For each chunk the tool writes docs/writing/context/<chunk>.md (story order: the actions in
walkthrough order with all their texts, then the rooms in first-visit order, conversations,
items, quests, puzzles and names) and docs/writing/context/<chunk>_keys.csv (keys,sk_current,
kind: the template a chunk writer copies; the writer returns keys,sk_new,note).

The texts shown are the current tables (src/game/localization/*.csv, i.e. game.json plus the
accepted overrides). The game is the EFFECTIVE game: game.json with the content overlays of
src/game/data/content_ext/ applied (tools/content_ext.py), so extended conversations appear in
their full play order and overlay texts (new lines, new topics, new exits, first-ride lines) are
indexed too (KeyInfo.overlay = True: their text lives in the overlay, not in sk_overrides.csv).
game.json, walkthrough.json, the overlays and the tables are only read.

The key index built here is also used by tools/check_rewrite.py.

Usage:
    python tools/writing_bundles.py [--out-dir docs/writing/context] [--chunk C1] [--stats]

Exit codes: 0 ok, 1 a table key could not be assigned to a chunk, 2 input error.
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import text_keys as tk  # noqa: E402

WALKTHROUGH_JSON = tk.REPO_ROOT / "design-doc" / "walkthrough.json"
WRITING_DIR = tk.REPO_ROOT / "docs" / "writing"
CONTEXT_DIR = WRITING_DIR / "context"


def _rooms(*ranges: tuple[int, int]) -> list[str]:
    return [f"S{n:02d}" for start, end in ranges for n in range(start, end + 1)]


CHUNKS: "OrderedDict[str, dict]" = OrderedDict(
    C1={"title": "2020 – Chorvátsky Grob, Čierna Voda a Dúbravka 2020", "rooms": _rooms((1, 10), (51, 56))},
    C2={"title": "1995 – Bratislava (Dúbravka, Karlova Ves, Staré Mesto, Ružinov, Petržalka)",
        "rooms": _rooms((11, 30))},
    C3={"title": "1960 Ivanka pri Dunaji + 1982 Dúbravka", "rooms": _rooms((31, 40), (57, 66))},
    C4={"title": "2035 Jasná + cutscény, epilóg, systémové a UI texty",
        "rooms": _rooms((41, 50), (67, 68))},
)
GENERIC_CHUNK = "C4"
ROOM_CHUNK = {room: chunk for chunk, spec in CHUNKS.items() for room in spec["rooms"]}
# Rooms added by the world overlay (content_ext/world_ext.json) join the chunk of their era.
ERA_CHUNK = {2020: "C1", 1995: "C2", 1960: "C3", 1982: "C3", 2035: "C4"}

# Default locked look of exits/connections that have no condition: the text is never shown.
NEVER_SHOWN = "never_shown"

# Kinds drive the rules in check_rewrite.py (length limits, speaker rules).
KIND_LINE = "line"            # spoken subtitle line (has a speaker)
KIND_LOOK = "look"            # Adam's observation (hotspot/item look, look variant, locked look)
KIND_NAME = "name"            # names and titles (rooms, hotspots, items, characters, exits, quests, puzzles)
KIND_LABEL = "label"          # action labels (hover sentence / dialogue choice)
KIND_TOPIC = "topic_label"    # ambient topic choice
KIND_GOAL = "goal"            # objectives, journal texts, quest goals, item purposes, rewards
KIND_HINT = "hint"            # quest hints
KIND_CLUE = "clue"            # puzzle clue, journal clue
KIND_OPTION = "option"        # puzzle option / confirm button
KIND_CAPTION = "caption"      # epilogue shot caption
KIND_UI = "ui"                # ui.csv


@dataclass
class KeyInfo:
    key: str
    table: str
    text: str                      # current sk text in the table
    original: str | None           # game.json text (None for ui.csv)
    chunk: str
    section: str
    kind: str
    speaker: str | None = None
    order: tuple = ()
    role: str = ""                 # where the player sees it, in plain words
    notes: list[str] = field(default_factory=list)
    never_shown: bool = False
    source: str = ""               # concrete game.json path (diagnostics, era lookup)
    era: int | None = None         # year of the scene the text belongs to (None: generic)
    overlay: bool = False          # the text comes from a content overlay (edit it there)


# --------------------------------------------------------------------------- loading

def read_tables() -> dict[str, dict[str, str]]:
    tables = {}
    for table, name in tk.TABLE_FILE_NAMES.items():
        header, rows = tk.read_table(tk.LOCALIZATION_DIR / name)
        tables[table] = {row[0]: row[1] for row in rows if row}
    return tables


def load_walkthrough() -> dict:
    return tk.load_json(WALKTHROUGH_JSON)


# --------------------------------------------------------------------------- the model

class Model:
    """game.json with lookups and the chunk assignment of every object."""

    def __init__(self, game: dict, walkthrough: dict, tables: dict[str, dict[str, str]]):
        self.game = game
        self.tables = tables
        self.walkthrough = walkthrough
        self.rooms = {room["id"]: room for room in game["rooms"]}
        self.hotspots = {h["id"]: (room["id"], h) for room in game["rooms"] for h in room.get("hotspots", [])}
        self.actions = {a["id"]: a for a in game["actions"]}
        self.items = {i["id"]: i for i in game["items"]}
        self.characters = {c["id"]: c for c in game["characters"]}
        self.quests = {q["id"]: q for q in game["quests"]}
        self.puzzles = {p["id"]: p for p in game["puzzles"]}
        self.cutscenes = {c["id"]: c for c in game["cutscenes"]}
        self.non_actor = game.get("non_actor_speakers", {})
        self.action_quest = {a: q["id"] for q in game["quests"] for a in q.get("actions", [])}
        self.puzzle_action = {a["puzzle"]: a["id"] for a in game["actions"] if a.get("puzzle")}
        self.cutscene_actions = defaultdict(list)
        for a in game["actions"]:
            if a.get("cutscene"):
                self.cutscene_actions[a["cutscene"]].append(a["id"])
        self._order_actions()
        self._order_rooms()
        self.action_room = {aid: self._resolve_action_room(a) for aid, a in self.actions.items()}

    # ---- order
    def _order_actions(self) -> None:
        order = [step["action"] for step in self.walkthrough.get("main_route", [])]
        order += [a for a in self.walkthrough.get("postgame_optional_route", []) if a not in order]
        order += [a["id"] for a in self.game["actions"] if a["id"] not in order]
        self.action_order = {aid: n for n, aid in enumerate(order)}
        self.step_room = {step["action"]: step.get("room_after") for step in self.walkthrough.get("main_route", [])}

    def _order_rooms(self) -> None:
        seen: list[str] = [self.game.get("initial_state", {}).get("room", "S01")]
        for step in self.walkthrough.get("main_route", []):
            for room in list(step.get("travel_path", [])) + [step.get("room_after")]:
                if room and room not in seen:
                    seen.append(room)
        for aid in self.walkthrough.get("postgame_optional_route", []):
            room = self.actions.get(aid, {}).get("room")
            if room in self.rooms and room not in seen:
                seen.append(room)
        seen += [r for r in self.rooms if r not in seen]
        self.room_order = {room: n for n, room in enumerate(seen)}

    def _resolve_action_room(self, action: dict) -> str | None:
        if action["room"] in self.rooms:
            return action["room"]
        room = self.step_room.get(action["id"])
        if room in self.rooms:
            return room
        quest = self.quests.get(self.action_quest.get(action["id"], ""))
        if quest:
            rooms = [self.actions[a]["room"] for a in quest["actions"] if self.actions[a]["room"] in self.rooms]
            if rooms:
                return Counter(rooms).most_common(1)[0][0]
        return None

    # ---- chunks
    def room_chunk(self, room: str | None) -> str:
        """The chunk of a room: the fixed lists above, else (rooms of the world overlay) the chunk of its era."""
        if room in ROOM_CHUNK:
            return ROOM_CHUNK[room]
        era = self.rooms.get(room or "", {}).get("era")
        return ERA_CHUNK.get(era, GENERIC_CHUNK)

    def action_chunk(self, aid: str) -> str:
        return self.room_chunk(self.action_room.get(aid))

    def item_chunk(self, iid: str) -> str:
        origin = self.items[iid].get("origin")
        if origin in self.actions:
            return self.action_chunk(origin)
        if origin == "initial":
            return self.room_chunk(self.game.get("initial_state", {}).get("room"))
        return GENERIC_CHUNK

    def character_chunk(self, cid: str) -> str:
        rooms = self.characters.get(cid, {}).get("rooms") or []
        return self.room_chunk(rooms[0]) if rooms else GENERIC_CHUNK

    def quest_chunk(self, qid: str) -> str:
        actions = self.quests[qid].get("actions", [])
        return self.action_chunk(actions[0]) if actions else GENERIC_CHUNK

    def puzzle_chunk(self, pid: str) -> str:
        aid = self.puzzle_action.get(pid)
        return self.action_chunk(aid) if aid else GENERIC_CHUNK

    def room_era(self, room: str | None) -> int | None:
        return self.rooms[room].get("era") if room in self.rooms else None

    def era_of_source(self, source: str) -> int | None:
        """Era of the scene a game.json path belongs to (None for generic texts)."""
        match = re.match(r"^(\w+)\[([^\]]+)\]", source)
        if not match:
            return None
        collection, oid = match.groups()
        if collection == "rooms":
            return self.room_era(oid)
        if collection == "connections":
            return self.room_era(oid.split("->")[0])
        if collection == "actions":
            return self.room_era(self.action_room.get(oid))
        if collection == "characters":
            rooms = self.characters.get(oid, {}).get("rooms") or []
            return self.room_era(rooms[0]) if rooms else None
        if collection == "items":
            origin = self.items.get(oid, {}).get("origin")
            return self.room_era(self.action_room.get(origin)) if origin in self.actions else 2020
        if collection == "quests":
            actions = self.quests.get(oid, {}).get("actions") or []
            return self.room_era(self.action_room.get(actions[0])) if actions else None
        if collection == "puzzles":
            return self.room_era(self.action_room.get(self.puzzle_action.get(oid, "")))
        if collection == "cutscenes":
            triggers = self.cutscene_actions.get(oid) or []
            return self.room_era(self.action_room.get(triggers[0])) if triggers else None
        return None

    # ---- plain words
    def speaker_name(self, sid: str | None) -> str:
        if not sid:
            return ""
        if sid in self.characters:
            return self.characters[sid]["name"]
        return self.non_actor.get(sid, sid)

    def action_ref(self, aid: str) -> str:
        action = self.actions.get(aid)
        if not action:
            return aid
        label = self.tables[tk.TABLE_WORLD].get(tk.action_label(aid), action["label"])
        return f"„{label}“ ({aid})"

    def item_ref(self, iid: str) -> str:
        item = self.items.get(iid)
        if not item:
            return iid
        name = self.tables[tk.TABLE_WORLD].get(tk.item_name(iid), item["name"])
        return f"„{name}“ ({iid})"

    def target_ref(self, target: str) -> str:
        if target in self.hotspots:
            room, hotspot = self.hotspots[target]
            name = self.tables[tk.TABLE_WORLD].get(tk.hotspot_name(target), hotspot["name"])
            return f"„{name}“ ({target})"
        if target in self.items:
            return self.item_ref(target)
        return target

    def room_ref(self, room: str | None) -> str:
        if room not in self.rooms:
            return "—"
        name = self.tables[tk.TABLE_WORLD].get(tk.room_name(room), self.rooms[room]["name"])
        return f"{room} {name} ({self.rooms[room].get('era')})"

    def conditions(self, requires_done=(), requires_items=(), excluded_done=()) -> str:
        parts = []
        if requires_done:
            parts.append("after " + ", ".join(self.action_ref(a) for a in requires_done))
        if requires_items:
            parts.append("holding " + ", ".join(self.item_ref(i) for i in requires_items))
        if excluded_done:
            parts.append("not after " + ", ".join(self.action_ref(a) for a in excluded_done))
        return "; ".join(parts) if parts else "always"

    def how(self, action: dict) -> str:
        kind = action["kind"]
        target = self.target_ref(action["target"])
        selected = action.get("selected_item")
        if kind == "topic":
            return f"dialogue choice when talking to {target}"
        if kind == "combine":
            return f"in the bag: combine {self.item_ref(selected)} with {target}"
        if selected:
            return f"use {self.item_ref(selected)} on {target}"
        return f"left click on {target}"

    def label_role(self, action: dict) -> str:
        kind = action["kind"]
        if kind == "topic":
            return "dialogue choice the player picks (also the heading of this exchange in the conversation log)"
        if kind == "combine":
            return "action sentence shown while combining the two items (hover line)"
        if action.get("selected_item"):
            return "action sentence shown when the selected item hovers over the target"
        return "action name (journal/transcript; the click itself shows the hotspot name)"


# --------------------------------------------------------------------------- key index

def build_key_index(game: dict | None = None, walkthrough: dict | None = None,
                    tables: dict[str, dict[str, str]] | None = None) -> tuple[dict[str, KeyInfo], Model]:
    """Assign every key of the three tables to a chunk, section and kind."""
    overlay_keys: set[str] = set()
    if game is None:
        game, overlay = tk.effective_game()
        if overlay.errors:
            raise ValueError("content overlay invalid: " + "; ".join(overlay.errors[:3]))
        overlay_keys = overlay.added_keys
    walkthrough = walkthrough if walkthrough is not None else load_walkthrough()
    tables = tables if tables is not None else read_tables()
    model = Model(game, walkthrough, tables)
    index: dict[str, KeyInfo] = {}
    sk = {key: text for table in tables.values() for key, text in table.items()}

    def add(entry: tk.TextEntry, chunk: str, section: str, kind: str, order: tuple, role: str,
            notes: list[str] | None = None, never_shown: bool = False) -> None:
        if entry.key in index:
            return
        index[entry.key] = KeyInfo(entry.key, entry.table, sk.get(entry.key, entry.text), entry.text, chunk,
                                   section, kind, entry.speaker, order, role, notes or [], never_shown,
                                   entry.source, model.era_of_source(entry.source), entry.key in overlay_keys)

    room_src = re.compile(r"^rooms\[([^\]]+)\]")
    for entry in tk.iter_text_entries(game):
        src, fld = entry.source, entry.field
        if fld == "title":
            add(entry, GENERIC_CHUNK, "general", KIND_NAME, (0,), "game title (title screen)")
        elif fld == "characters[].name":
            cid = re.search(r"characters\[([^\]]+)\]", src).group(1)
            add(entry, model.character_chunk(cid), "names", KIND_NAME, (cid,), "speaker name above subtitles; NPC name")
        elif fld == "non_actor_speakers.*":
            add(entry, GENERIC_CHUNK, "general", KIND_NAME, (1, entry.key), "speaker name above subtitles")
        elif fld.startswith("rooms[]"):
            room = room_src.match(src).group(1)
            chunk = model.room_chunk(room)
            ro = model.room_order.get(room, 999)
            if fld == "rooms[].name":
                add(entry, chunk, "rooms", KIND_NAME, (ro, 0), "room name (map, exit labels elsewhere)")
            elif fld == "rooms[].first_entry[].text":
                add(entry, chunk, "rooms", KIND_LINE, (ro, 1, entry.key), "first entry line (Adam, once)")
            elif fld.startswith("rooms[].hotspots[]"):
                hid = re.search(r"hotspots\[([^\]]+)\]", src).group(1)
                kind = KIND_NAME if fld.endswith(".name") else KIND_LOOK
                role = {"rooms[].hotspots[].name": "hotspot name (hover / Space label)",
                        "rooms[].hotspots[].look": "right-click look (Adam's observation)",
                        "rooms[].hotspots[].look_variants[].text": "look variant (replaces the look later)"}[fld]
                add(entry, chunk, "rooms", kind, (ro, 2, hid, entry.key), role)
            elif fld == "rooms[].exits[].first_ride[].text":
                eid = re.search(r"exits\[([^\]]+)\]", src).group(1)
                add(entry, chunk, "rooms", KIND_LINE, (ro, 3, eid, 2, entry.key),
                    "first-ride line (Adam, once, before the bus leaves)")
            elif fld.startswith("rooms[].exits[]"):
                eid = re.search(r"exits\[([^\]]+)\]", src).group(1)
                room_exit = next(e for e in model.rooms[room]["exits"] if e["id"] == eid)
                if fld.endswith(".label"):
                    add(entry, chunk, "rooms", KIND_NAME, (ro, 3, eid, 0), "exit label (hover / Space)")
                else:
                    never = not room_exit.get("requires_done")
                    add(entry, chunk, "rooms", KIND_LOOK, (ro, 3, eid, 1),
                        "locked exit look (left click while locked)", never_shown=never)
        elif fld.startswith("connections[]"):
            a, b = re.search(r"connections\[([^\]]+)->([^\]]+)\]", src).groups()
            conn = next(c for c in game["connections"] if c["from"] == a and c["to"] == b)
            ro = model.room_order.get(a, 999)
            if fld.endswith(".label"):
                add(entry, model.room_chunk(a), "rooms", KIND_NAME, (ro, 4, a, b, 0), "map connection label")
            else:
                add(entry, model.room_chunk(a), "rooms", KIND_LOOK, (ro, 4, a, b, 1),
                    "map connection locked look", never_shown=not conn.get("requires_done"))
        elif fld.startswith("items[]"):
            iid = re.search(r"items\[([^\]]+)\]", src).group(1)
            origin = model.items[iid].get("origin")
            io_ = model.action_order.get(origin, -1)
            kind, role = {"items[].name": (KIND_NAME, "inventory name (hover in the bag, action sentences)"),
                          "items[].look": (KIND_LOOK, "right-click look in the bag (Adam)"),
                          "items[].purpose": (KIND_GOAL, "inventory tooltip: what the item is for")}[fld]
            add(entry, model.item_chunk(iid), "items", kind, (io_, iid, fld), role)
        elif fld.startswith("actions[]"):
            aid = re.search(r"actions\[([^\]]+)\]", src).group(1)
            action = model.actions[aid]
            ao = model.action_order.get(aid, 999)
            if fld == "actions[].label":
                add(entry, model.action_chunk(aid), "story", KIND_LABEL, (ao, 0), model.label_role(action))
            elif fld == "actions[].lines[].text":
                add(entry, model.action_chunk(aid), "story", KIND_LINE, (ao, 1, entry.key), "spoken line")
            elif fld == "actions[].objective":
                add(entry, model.action_chunk(aid), "story", KIND_GOAL, (ao, 2),
                    "objective: the pinned 'current goal' sentence after this action")
            elif fld == "actions[].journal_text":
                add(entry, model.action_chunk(aid), "story", KIND_GOAL, (ao, 3), "journal entry recorded by this action")
            elif fld == "actions[].hint_step":
                add(entry, model.action_chunk(aid), "story", KIND_HINT, (ao, 4),
                    "exact step hint (hint level 3, H key; world overlay)")
        elif fld.startswith("characters[].ambient_topics[]"):
            cid = re.search(r"characters\[([^\]]+)\]", src).group(1)
            tid = re.search(r"ambient_topics\[([^\]]+)\]", src).group(1)
            kind = KIND_TOPIC if fld.endswith(".label") else KIND_LINE
            role = "topic choice (what Adam asks / brings up)" if kind == KIND_TOPIC else "spoken line"
            add(entry, model.character_chunk(cid), "conversations", kind, (cid, tid, entry.key), role)
        elif fld == "cutscenes[].beats[].lines[].text":
            cid = re.search(r"cutscenes\[([^\]]+)\]", src).group(1)
            add(entry, GENERIC_CHUNK, "cutscenes", KIND_LINE, (cid, entry.key), "cutscene subtitle")
        elif fld.startswith("quests[]"):
            qid = re.search(r"quests\[([^\]]+)\]", src).group(1)
            kind = {"quests[].title": KIND_NAME, "quests[].hints[]": KIND_HINT}.get(fld, KIND_GOAL)
            role = {"quests[].title": "quest title (journal)",
                    "quests[].goal": "quest goal (journal + pinned goal card)",
                    "quests[].reward": "reward line (journal / album)",
                    "quests[].hints[]": "hint (H key)"}[fld]
            if fld == "quests[].hints[]":
                level = int(entry.key.rsplit(".", 1)[1])
                role = {1: "hint level 1: direction", 2: "hint level 2: concrete steps",
                        3: "hint level 3: exact solution"}.get(level, "hint")
            add(entry, model.quest_chunk(qid), "quests", kind,
                (model.action_order.get(model.quests[qid]["actions"][0], 999), qid, entry.key), role)
        elif fld.startswith("puzzles[]"):
            pid = re.search(r"puzzles\[([^\]]+)\]", src).group(1)
            kind = {"puzzles[].title": KIND_NAME, "puzzles[].clue": KIND_CLUE,
                    "puzzles[].wrong_line": KIND_LINE, "puzzles[].success_line": KIND_LINE}.get(fld, KIND_OPTION)
            role = {"puzzles[].title": "puzzle window title", "puzzles[].clue": "clue shown in the puzzle window",
                    "puzzles[].wrong_line": "line after a wrong answer", "puzzles[].success_line": "line after solving",
                    "puzzles[].controls.confirm_label": "confirm button"}.get(fld, "puzzle option label")
            add(entry, model.puzzle_chunk(pid), "puzzles", kind, (pid, entry.key), role)
        elif fld == "journal_contract.clues[]":
            pid = entry.key.rsplit(".", 1)[1]
            add(entry, model.puzzle_chunk(pid), "puzzles", KIND_CLUE, (pid, "~journal"),
                "journal 'Findings' line for the puzzle clue")
        elif fld.startswith("epilogue[]"):
            n = int(entry.key.split(".")[1])
            kind = KIND_CAPTION if fld.endswith(".shot") else KIND_LINE
            role = "credits shot caption" if kind == KIND_CAPTION else "credits line"
            add(entry, GENERIC_CHUNK, "epilogue", kind, (n, entry.key), role)
        else:
            add(entry, GENERIC_CHUNK, "general", KIND_GOAL, (9, entry.key), fld)

    ui_order = list(tables[tk.TABLE_UI].keys())
    for n, key in enumerate(ui_order):
        index[key] = KeyInfo(key, tk.TABLE_UI, tables[tk.TABLE_UI][key], None, GENERIC_CHUNK, "ui", KIND_UI,
                             None, (n,), "user interface (ui.csv, edited directly, not via overrides)")
    return index, model


# --------------------------------------------------------------------------- markdown

def esc(text: str) -> str:
    return text.replace("\n", " ")


def fmt_key(info: KeyInfo, model: Model, tag: str | None = None) -> str:
    who = ""
    if info.speaker:
        who = f"**{info.speaker}** ({model.speaker_name(info.speaker)}): "
    tag = tag or info.role
    flag = " _(never shown in play: this exit has no lock — leave unchanged)_" if info.never_shown else ""
    return f"- `{info.key}` [{tag}]{flag} {who}{esc(info.text)}"


def write_bundle(chunk: str, index: dict[str, KeyInfo], model: Model) -> str:
    keys = {k: v for k, v in index.items() if v.chunk == chunk}
    shown = [v for v in keys.values() if not v.never_shown]
    out = io.StringIO()
    w = out.write
    spec = CHUNKS[chunk]
    by_table = Counter(v.table for v in shown)
    w(f"# {chunk} – {spec['title']}\n\n")
    w("Generated by `tools/writing_bundles.py` from design-doc/game.json, walkthrough.json and the current "
      "tables in src/game/localization/. Do not edit by hand; re-run the tool.\n\n")
    w(f"Keys to write: **{len(shown)}** (dialogue {by_table.get('dialogue', 0)}, world {by_table.get('world', 0)}, "
      f"ui {by_table.get('ui', 0)}). Never shown (default locked looks of open exits): {len(keys) - len(shown)}.\n\n")
    w("Rules: docs/writing/STYLE_GUIDE.md, voices and ty/vy table: docs/writing/VOICES.md, terms and protected "
      "facts: docs/writing/GLOSSARY.md (checker rules: docs/writing/glossary.json). Return `docs/writing/out/" + chunk + ".csv` with the header `keys,sk_new,note` "
      "(only changed keys; note in English) and run `python tools/check_rewrite.py docs/writing/out/"
      f"{chunk}.csv --chunk {chunk}`.\n\n")
    w("Ids in brackets (S01, G01, ITEM…) are context for you. They must never appear in the Slovak text.\n\n")

    # ---- story
    actions = sorted({v.order[0] for v in keys.values() if v.section == "story"})
    order_to_action = {model.action_order[a]: a for a in model.actions}
    if actions:
        w("## 1. Story actions in play order\n\n")
        w("Each block is one player action: where it happens, how the player triggers it, what it needs and "
          "gives, then every text it shows in the order the player sees it (label, spoken lines, new objective, "
          "journal entry). Lines inside a block play one after another.\n\n")
    for ao in actions:
        aid = order_to_action[ao]
        action = model.actions[aid]
        qid = model.action_quest.get(aid)
        quest = model.quests.get(qid or "")
        qtitle = model.tables[tk.TABLE_WORLD].get(tk.quest_title(qid), quest["title"]) if quest else ""
        w(f"### {aid} · {quest['type'] + ' quest ' + qid + ' „' + qtitle + '“' if quest else 'no quest'}\n\n")
        w(f"- Where: {model.room_ref(model.action_room.get(aid))}\n")
        w(f"- How: {model.how(action)}\n")
        w(f"- Available: {model.conditions(action.get('requires_done', []), action.get('requires_items', []), action.get('excluded_done', []))}\n")
        if action.get("gives"):
            w(f"- Player gets: {', '.join(model.item_ref(i) for i in action['gives'])}\n")
        if action.get("consumes"):
            w(f"- Used up: {', '.join(model.item_ref(i) for i in action['consumes'])}\n")
        if action.get("puzzle"):
            p = model.puzzles[action["puzzle"]]
            w(f"- Puzzle {p['id']} opens first (solution: {p['solution']}); see section Puzzles.\n")
        if action.get("cutscene"):
            cs_lines = [line for beat in model.cutscenes[action["cutscene"]].get("beats", [])
                        for line in beat.get("lines", [])]
            w(f"- Afterwards cutscene {action['cutscene']} plays (written in C4; context only): "
              + " / ".join(f"{line.get('speaker')}: "
                           f"{model.tables[tk.TABLE_DIALOGUE].get(line.get('line_id'), line['text'])}"
                           for line in cs_lines) + "\n")
        for t in model.game.get("special_transitions", []):
            if t.get("after") == aid:
                w(f"- Afterwards the player is moved to {model.room_ref(t['to'])}.\n")
        staged = action.get("staging", {}).get("guest_speakers") or []
        if staged:
            w(f"- Guest speakers: {', '.join(staged)}\n")
        w("\n")
        for info in sorted((v for v in keys.values() if v.section == "story" and v.order[0] == ao),
                           key=lambda v: v.order):
            tag = info.role
            if info.key.endswith(".journal") and info.original == model.actions[aid].get("objective"):
                tag = "journal entry (same text as the objective in game.json)"
            w(fmt_key(info, model, tag) + "\n")
        w("\n")

    # ---- rooms
    rooms = sorted({v.order[0] for v in keys.values() if v.section == "rooms"})
    order_to_room = {n: r for r, n in model.room_order.items()}
    if rooms:
        w("## 2. Rooms in first-visit order\n\n")
        w("Room name, Adam's first-entry line, hotspot names and looks (right click), exits. A look is what Adam "
          "says when the player right-clicks; on props without an action the left click shows it too.\n\n")
    for ro in rooms:
        rid = order_to_room[ro]
        room = model.rooms[rid]
        w(f"### {rid} · {model.tables[tk.TABLE_WORLD].get(tk.room_name(rid), room['name'])} "
          f"({room.get('era')}, {room.get('district')})\n\n")
        w(f"Picture: {room.get('art_brief', '')}\n\n")
        if room.get("npc_ids"):
            w(f"People here: {', '.join(c + ' ' + model.speaker_name(c) for c in room['npc_ids'])}\n\n")
        infos = sorted((v for v in keys.values() if v.section == "rooms" and v.order[0] == ro and not v.never_shown),
                       key=lambda v: v.order)
        hotspot_done = set()
        for info in infos:
            if info.order[1] == 2:
                hid = info.order[2]
                if hid not in hotspot_done:
                    hotspot_done.add(hid)
                    _, h = model.hotspots[hid]
                    extra = [f"kind {h['kind']}"]
                    if h.get("visible_after"):
                        extra.append("appears " + model.conditions(h["visible_after"]))
                    if h.get("hide_after"):
                        extra.append("disappears after " + ", ".join(model.action_ref(a) for a in h["hide_after"]))
                    used = [a for a in model.actions.values() if a["target"] == hid]
                    if used:
                        extra.append("actions here: " + ", ".join(model.action_ref(a["id"]) for a in used))
                    w(f"- Hotspot {hid}: {'; '.join(extra)}\n")
                tag = info.role
                variant = re.search(r"variant(\d+)$|\.look\.(\d+)$", info.key)
                if variant:
                    n = int(variant.group(1) or variant.group(2))
                    after = h["look_variants"][n - 1].get("after")
                    tag = f"look variant, shown after {model.action_ref(after)}"
                w("  " + fmt_key(info, model, tag) + "\n")
            elif info.order[1] == 3:
                eid = info.order[2]
                room_exit = next(e for e in room["exits"] if e["id"] == eid)
                tag = info.role
                if info.key.endswith(".label"):
                    tag = f"exit label → {room_exit['to']}"
                elif not info.never_shown:
                    tag = f"locked exit look, shown until {model.conditions(room_exit['requires_done'])[6:]}"
                w(fmt_key(info, model, tag) + "\n")
            elif info.order[1] == 4:
                tag = info.role
                if not info.never_shown and info.key.endswith(".locked"):
                    a, b = info.order[2], info.order[3]
                    conn = next(c for c in model.game["connections"] if c["from"] == a and c["to"] == b)
                    tag = f"map connection locked look, until {model.conditions(conn['requires_done'])[6:]}"
                w(fmt_key(info, model, tag) + "\n")
            else:
                w(fmt_key(info, model) + "\n")
        w("\n")

    # ---- conversations
    convo = [v for v in keys.values() if v.section == "conversations"]
    if convo:
        w("## 3. Conversations (ambient topics)\n\n")
        w("A topic appears in the NPC's menu as its label; the lines below it play when the player picks it. "
          "Usually Adam speaks first: then the label is the topic and Adam's first line is the real question "
          "(they must not repeat each other). When the NPC speaks first, the label IS Adam's question and the "
          "NPC's first line must answer it.\n\n")
        chars = []
        for v in sorted(convo, key=lambda v: v.order):
            if v.order[0] not in chars:
                chars.append(v.order[0])
        for cid in chars:
            c = model.characters[cid]
            w(f"### {cid} · {c['name']} ({c.get('age')}) — {', '.join(c.get('rooms', []))}\n\n")
            w(f"Role: {c.get('role', '')}  \nVoice: {c.get('voice', '')}\n\n")
            story = [a["id"] for a in model.game["actions"]
                     if a["target"] in model.hotspots and model.hotspots[a["target"]][1].get("character_id") == cid]
            if story:
                w(f"Story actions with this character (texts in section 1): {', '.join(story)}\n\n")
            for t in c.get("ambient_topics", []):
                cond = model.conditions(t.get("requires_done", []))
                first = (t.get("lines") or [{}])[0].get("speaker")
                who = ("Adam speaks first: label = topic, his line = the question" if first == "ADAM"
                       else f"{first} answers first: the label must work as Adam's question")
                w(f"- Topic `{t['id']}` (available: {cond}; "
                  f"{'repeatable' if t.get('repeatable') else 'once'}; {who})\n")
                for v in sorted((v for v in convo if v.order[0] == cid and v.order[1] == t["id"]),
                                key=lambda v: (0 if v.key.endswith(".label") else 1, v.key)):
                    w("  " + fmt_key(v, model) + "\n")
            w("\n")

    # ---- items
    items = sorted((v for v in keys.values() if v.section == "items"), key=lambda v: v.order)
    if items:
        w("## 4. Items first obtained in this chunk\n\n")
        last = None
        for v in items:
            iid = v.order[1]
            if iid != last:
                last = iid
                item = model.items[iid]
                uses = [a["id"] for a in model.game["actions"]
                        if iid in (a.get("requires_items") or []) or a.get("selected_item") == iid or a["target"] == iid]
                consumed = [a["id"] for a in model.game["actions"] if iid in (a.get("consumes") or [])]
                origin = item.get("origin")
                w(f"- Item {iid}: from {model.action_ref(origin) if origin in model.actions else origin}; "
                  f"used in {', '.join(uses) or '—'}; used up by {', '.join(consumed) or '— (stays)'}\n")
            w("  " + fmt_key(v, model) + "\n")
        w("\n")

    # ---- quests
    quests = sorted((v for v in keys.values() if v.section == "quests"), key=lambda v: v.order)
    if quests:
        w("## 5. Quests (journal, goal card, hints)\n\n")
        w("Hint level 1 gives a direction, level 2 the concrete steps, level 3 the exact solution. "
          "Level 3 must name every step in order with in-game names (no ids).\n\n")
        last = None
        for v in quests:
            qid = v.order[1]
            if qid != last:
                last = qid
                q = model.quests[qid]
                w(f"\n### {qid} ({q['type']}) — actions {', '.join(q['actions'])}\n\n")
            w(fmt_key(v, model) + "\n")
        w("\n")

    # ---- puzzles
    puzzles = sorted((v for v in keys.values() if v.section == "puzzles"), key=lambda v: v.order)
    if puzzles:
        w("## 6. Puzzles\n\n")
        last = None
        for v in puzzles:
            pid = v.order[0]
            if pid != last:
                last = pid
                p = model.puzzles[pid]
                w(f"\n### {pid} — controls {p['controls'].get('type')}, solution {p['solution']} "
                  f"(action {model.puzzle_action.get(pid)})\n\n")
            w(fmt_key(v, model) + "\n")
        w("\n")

    # ---- cutscenes
    cuts = sorted((v for v in keys.values() if v.section == "cutscenes"), key=lambda v: v.order)
    if cuts:
        w("## 7. Cutscenes\n\n")
        for cid, cs in model.cutscenes.items():
            trig = model.cutscene_actions.get(cid, [])
            w(f"### {cid} — after {', '.join(model.action_ref(a) + ' in ' + model.room_ref(model.action_room.get(a)) for a in trig)}\n\n")
            for a in trig:
                before = model.actions[a].get("lines", [])[-2:]
                if before:
                    w(f"Just before (context, chunk {model.action_chunk(a)}): " + " / ".join(
                        f"{line.get('speaker')}: "
                        f"{model.tables[tk.TABLE_DIALOGUE].get(line.get('line_id'), line['text'])}"
                        for line in before) + "\n\n")
            for n, beat in enumerate(cs.get("beats", []), start=1):
                w(f"Shot {n}: {beat.get('shot', '')}\n\n")
                for line in beat.get("lines", []):
                    info = keys.get(line.get("line_id", ""))
                    if info:
                        w(fmt_key(info, model) + "\n")
                w("\n")

    # ---- epilogue
    epi = sorted((v for v in keys.values() if v.section == "epilogue"), key=lambda v: v.order)
    if epi:
        w("## 8. Epilogue (credits shots after side quests)\n\n")
        for n, shot in enumerate(model.game.get("epilogue", []), start=1):
            w(f"- Shot {n}: shown when side quest {shot.get('quest')} is done (after {model.action_ref(shot.get('after'))})\n")
            for v in epi:
                if v.order[0] == n:
                    w("  " + fmt_key(v, model) + "\n")
        w("\n")

    # ---- names
    names = sorted((v for v in keys.values() if v.section == "names"), key=lambda v: v.order)
    if names:
        w("## 9. Character names (speaker labels)\n\n")
        for v in names:
            w(fmt_key(v, model) + "\n")
        w("\n")

    general = sorted((v for v in keys.values() if v.section == "general"), key=lambda v: v.order)
    if general:
        w("## 10. General texts\n\n")
        for v in general:
            w(fmt_key(v, model) + "\n")
        w("\n")

    ui = sorted((v for v in keys.values() if v.section == "ui"), key=lambda v: v.order)
    if ui:
        w("## 11. User interface (ui.csv)\n\n")
        w("Hand-written table: rewrites are applied by editing ui.csv directly (not via overrides). Keep "
          "{placeholders} exactly; keep buttons short; the tone addresses the player with 'ty'.\n\n")
        area = None
        for v in ui:
            a = v.key.split(".")[1] if v.key.startswith("ui.") else v.key.split(".")[0]
            if a != area:
                area = a
                w(f"\n### {a}\n\n")
            w(fmt_key(v, model, "ui") + "\n")
        w("\n")

    never = [v for v in keys.values() if v.never_shown]
    if never:
        w("## Appendix: never shown\n\n")
        w(f"{len(never)} locked looks of exits and map connections without a condition carry the default text "
          f"„{never[0].text}“. They are never displayed; leave them unchanged.\n")
    return out.getvalue()


def write_keys_csv(chunk: str, index: dict[str, KeyInfo]) -> str:
    rows = [["keys", "sk_current", "kind", "speaker"]]
    order = {"story": 1, "rooms": 2, "conversations": 3, "items": 4, "quests": 5, "puzzles": 6,
             "cutscenes": 7, "epilogue": 8, "names": 9, "general": 10, "ui": 11}
    infos = [v for v in index.values() if v.chunk == chunk and not v.never_shown]
    infos.sort(key=lambda v: (order.get(v.section, 99),
                              tuple(f"{x:06d}" if isinstance(x, int) else str(x) for x in v.order)))
    for v in infos:
        rows.append([v.key, v.text, v.kind, v.speaker or ""])
    return tk.format_table(rows[0], rows[1:])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out-dir", type=Path, default=CONTEXT_DIR)
    parser.add_argument("--chunk", choices=list(CHUNKS), help="write only this chunk")
    parser.add_argument("--stats", action="store_true", help="print chunk sizes only")
    args = parser.parse_args()
    try:
        index, model = build_key_index()
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    tables = model.tables
    all_keys = {k for t in tables.values() for k in t}
    missing = sorted(all_keys - set(index))
    extra = sorted(set(index) - all_keys)
    for chunk in CHUNKS:
        infos = [v for v in index.values() if v.chunk == chunk]
        shown = [v for v in infos if not v.never_shown]
        kinds = Counter(v.kind for v in shown)
        print(f"{chunk}: {len(shown)} keys to write (+{len(infos) - len(shown)} never shown); "
              + ", ".join(f"{k} {n}" for k, n in sorted(kinds.items())))
    print(f"total: {len(index)} keys in the index, {len(all_keys)} in the tables")
    if missing:
        print(f"ERROR: {len(missing)} table keys without a chunk, e.g. {missing[:5]}")
    if extra:
        print(f"note: {len(extra)} scheme keys not in the tables (run tools/extract_strings.py), e.g. {extra[:5]}")
    if args.stats:
        return 1 if missing else 0

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for chunk in CHUNKS:
        if args.chunk and chunk != args.chunk:
            continue
        (args.out_dir / f"{chunk}.md").write_bytes(write_bundle(chunk, index, model).encode("utf-8"))
        (args.out_dir / f"{chunk}_keys.csv").write_bytes(write_keys_csv(chunk, index).encode("utf-8"))
        print(f"wrote {(args.out_dir / f'{chunk}.md').relative_to(tk.REPO_ROOT).as_posix()} and {chunk}_keys.csv")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
