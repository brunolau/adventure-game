"""Text-key scheme shared by the LastBell localization tools.

This module is the Python mirror of the key table in design-doc/ARCHITECTURE.md
("Text keys and localization") and of the C# `TextKeys` helper in LastBell.Core.
Both sides must build identical keys, so change them together.

Keys are derived from ids in game.json; spaces inside ids are kept as-is
(for example "topic.ELA.ambient 1.label").

Scheme extensions (strings that are player-visible but have no row in the
ARCHITECTURE.md table) are marked with `extension=True` on their entries:

    game.title                          game.json "title" (title screen)
    puzzle.<id>.left.<n> / .right.<n>   matching-puzzle option labels, n from 1
    journal.clue.<puzzleId>             journal_contract.clues (prefix "Pxx: " removed)

Speaker prefixes: epilogue lines and puzzle wrong/success lines are stored in
game.json as "SPEAKER: text". When SPEAKER is a known speaker id (a character
or a non-actor speaker), the prefix is split off: the table holds only the text,
and the presentation shows the speaker name via char.<SPEAKER>.name. Core must
apply the same split (see `split_speaker_prefix`).

Era cards (era.<year>.card / era.<year>.date / era.<year>.year) and the journal tab names are
hand-written in ui.csv; check_strings.py verifies them against game.json. era.<year>.year is the
year shown to the player; it may differ from the era id (Ivanka: id 1960, shown 1962,
docs/DECISIONS.md "Ivanka is shown as June 1962").

Content overlays (src/game/data/content_ext/, tools/content_ext.py): the tools read the
EFFECTIVE game, i.e. game.json with dialogue_ext.json / travel_ext.json applied
(`effective_game()`), so overlay lines, new topic labels and new exits get their keys like any
other text. Two extra fields exist only in the effective game:

    travel.<exitId>.first.<n>           rooms[].exits[].first_ride[] (first-ride lines, dialogue.csv)
    action.<id>.hint_step               actions[].hint_step (world_ext.json: the exact step hint of a new or
                                        relocated action; game.json's step texts are ui.hint_step.<id> in ui.csv)
"""
from __future__ import annotations

import csv
import io
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_GAME_JSON = REPO_ROOT / "design-doc" / "game.json"
SYNCED_GAME_JSON = REPO_ROOT / "src" / "game" / "data" / "game.json"
DIALOGUES_CSV = REPO_ROOT / "design-doc" / "dialogues.csv"
LOCALIZATION_DIR = REPO_ROOT / "src" / "game" / "localization"

TABLE_DIALOGUE = "dialogue"
TABLE_WORLD = "world"
TABLE_UI = "ui"
TABLE_FILE_NAMES = {TABLE_DIALOGUE: "dialogue.csv", TABLE_WORLD: "world.csv", TABLE_UI: "ui.csv"}
GENERATED_TABLES = (TABLE_DIALOGUE, TABLE_WORLD)

SOURCE_LOCALE = "sk"
HEADER = ("keys", SOURCE_LOCALE, "en")

SPEAKER_PREFIX_PATTERN = re.compile(r"^([A-Z][A-Z0-9_]*): (.+)$", re.DOTALL)
PUZZLE_ID_PREFIX_PATTERN = re.compile(r"^(P\d+): (.+)$", re.DOTALL)
PLACEHOLDER_PATTERN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
# ui.<area>.<name>; the name may contain data enums such as "cable_A6".
UI_KEY_PATTERN = re.compile(r"^ui\.[a-z0-9_]+\.[A-Za-z0-9_]+$")

PUZZLE_OPTION_SIDES = ("left", "right")

# Journal tabs in journal_contract.tabs order -> ui.csv keys.
JOURNAL_TAB_KEYS = (
    "ui.journal.tab_goals",
    "ui.journal.tab_findings",
    "ui.journal.tab_people",
    "ui.journal.tab_time_map",
    "ui.journal.tab_album",
)

# UI keys the handoff mandates explicitly (menu entries, verbatim system messages,
# controls named in PRIBEH_A_PRAVIDLA.txt). check_strings.py requires them in ui.csv.
REQUIRED_UI_KEYS = (
    "ui.menu.new_game",
    "ui.menu.continue",
    "ui.menu.load",
    "ui.menu.save",
    "ui.menu.settings",
    "ui.menu.album",
    "ui.menu.credits",
    "ui.menu.help",
    "ui.menu.quit",
    "ui.pause.title",
    "ui.save.slot",
    "ui.save.slot_empty",
    "ui.save.autosave",
    "ui.save.checkpoint_finale",
    "ui.save.overwrite_confirm",
    "ui.save.corrupted",
    "ui.settings.language",
    "ui.settings.volume_master",
    "ui.settings.volume_music",
    "ui.settings.volume_ambience",
    "ui.settings.volume_sfx",
    "ui.settings.volume_voice",
    "ui.settings.text_speed",
    "ui.settings.subtitles",
    "ui.settings.subtitle_size",
    "ui.settings.fullscreen",
    "ui.settings.windowed",
    "ui.settings.reduced_motion",
    "ui.settings.high_contrast_labels",
    "ui.settings.hotspot_key_hint",
    "ui.inventory.title",
    "ui.inventory.tab_archived",
    "ui.journal.title",
    "ui.journal.state_open",
    "ui.journal.state_in_progress",
    "ui.journal.state_done",
    "ui.map.title",
    "ui.map.node",
    "ui.hint.title",
    "ui.hint.level_1",
    "ui.hint.level_2",
    "ui.hint.level_3",
    "ui.puzzle.confirm",
    "ui.puzzle.reset",
    "ui.puzzle.close",
    "ui.puzzle.hint_fill",
    "ui.cutscene.skip_prompt",
    "ui.cutscene.the_end",
    "ui.travel.finish_ride",
    "ui.tutorial.left_click",
    "ui.tutorial.right_click",
    "ui.tutorial.space",
    "ui.system.path_blocked",
) + JOURNAL_TAB_KEYS


# --------------------------------------------------------------------------- key builders
# Keep these in sync with LastBell.Core TextKeys and ARCHITECTURE.md.

def room_name(room_id: str) -> str:
    return f"room.{room_id}.name"


def hotspot_name(hotspot_id: str) -> str:
    return f"hotspot.{hotspot_id}.name"


def hotspot_look(hotspot_id: str) -> str:
    """Fallback key; a hotspot look normally uses its look_line_id."""
    return f"hotspot.{hotspot_id}.look"


def hotspot_look_variant(hotspot_id: str, n: int) -> str:
    """Fallback key for look_variants[n-1]; normally the variant's line_id is used."""
    return f"hotspot.{hotspot_id}.look.{n}"


def exit_label(exit_id: str) -> str:
    return f"exit.{exit_id}.label"


def exit_locked(exit_id: str) -> str:
    return f"exit.{exit_id}.locked"


def connection_label(from_room: str, to_room: str) -> str:
    return f"conn.{from_room}.{to_room}.label"


def connection_locked(from_room: str, to_room: str) -> str:
    return f"conn.{from_room}.{to_room}.locked"


def item_name(item_id: str) -> str:
    return f"item.{item_id}.name"


def item_look(item_id: str) -> str:
    """Fallback key; an item look normally uses its look_line_id (e.g. "item.PHONE")."""
    return f"item.{item_id}.look"


def item_purpose(item_id: str) -> str:
    return f"item.{item_id}.purpose"


def action_label(action_id: str) -> str:
    return f"action.{action_id}.label"


def action_journal(action_id: str) -> str:
    return f"action.{action_id}.journal"


def action_objective(action_id: str) -> str:
    return f"action.{action_id}.objective"


def action_hint_step(action_id: str) -> str:
    """Exact step hint of a world-overlay action (Core TextKeys.ActionHintStep / Hints.StepText)."""
    return f"action.{action_id}.hint_step"


def character_name(character_id: str) -> str:
    return f"char.{character_id}.name"


def topic_label(topic_id: str) -> str:
    return f"topic.{topic_id}.label"


def quest_title(quest_id: str) -> str:
    return f"quest.{quest_id}.title"


def quest_goal(quest_id: str) -> str:
    return f"quest.{quest_id}.goal"


def quest_reward(quest_id: str) -> str:
    return f"quest.{quest_id}.reward"


def quest_hint(quest_id: str, n: int) -> str:
    return f"quest.{quest_id}.hint.{n}"


def puzzle_title(puzzle_id: str) -> str:
    return f"puzzle.{puzzle_id}.title"


def puzzle_clue(puzzle_id: str) -> str:
    return f"puzzle.{puzzle_id}.clue"


def puzzle_wrong(puzzle_id: str) -> str:
    return f"puzzle.{puzzle_id}.wrong"


def puzzle_success(puzzle_id: str) -> str:
    return f"puzzle.{puzzle_id}.success"


def puzzle_confirm(puzzle_id: str) -> str:
    return f"puzzle.{puzzle_id}.confirm"


def era_card(year: int) -> str:
    return f"era.{year}.card"


def era_date(year: int) -> str:
    return f"era.{year}.date"


def era_year(year: int) -> str:
    """The year shown to the player for the era with this id (presentation; Core TextKeys.EraYear)."""
    return f"era.{year}.year"


def epilogue_shot(n: int) -> str:
    return f"epilogue.{n}.shot"


def epilogue_line(n: int) -> str:
    return f"epilogue.{n}.line"


# Scheme extensions (see module docstring).

def game_title() -> str:
    return "game.title"


def puzzle_option(puzzle_id: str, side: str, n: int) -> str:
    if side not in PUZZLE_OPTION_SIDES:
        raise ValueError(f"unknown puzzle option side: {side}")
    return f"puzzle.{puzzle_id}.{side}.{n}"


def journal_clue(puzzle_id: str) -> str:
    return f"journal.clue.{puzzle_id}"


# --------------------------------------------------------------------------- helpers

def speaker_ids(game: dict) -> set[str]:
    """All ids that may appear as a line speaker."""
    ids = {character["id"] for character in game.get("characters", [])}
    ids.update(game.get("non_actor_speakers", {}).keys())
    return ids


def split_speaker_prefix(text: str, known_speakers: set[str]) -> tuple[str | None, str]:
    """Split "SPEAKER: text" when SPEAKER is a known speaker id; otherwise return (None, text)."""
    match = SPEAKER_PREFIX_PATTERN.match(text)
    if match and match.group(1) in known_speakers:
        return match.group(1), match.group(2)
    return None, text


def placeholders(text: str) -> Counter:
    return Counter(PLACEHOLDER_PATTERN.findall(text))


def load_json(path: Path) -> dict:
    return json.loads(path.read_bytes().decode("utf-8"))


# --------------------------------------------------------------------------- entries

@dataclass(frozen=True)
class TextEntry:
    """One player-visible string with its stable key."""

    key: str
    text: str
    table: str
    field: str  # normalized JSON path of the source field, e.g. "rooms[].hotspots[].look"
    source: str  # concrete JSON path for diagnostics, e.g. "rooms[S01].hotspots[S01.tools].look"
    speaker: str | None = None
    line_id: str | None = None  # set when the key is a line_id from the data
    extension: bool = False  # key not covered by the ARCHITECTURE.md table


def iter_text_entries(game: dict) -> Iterator[TextEntry]:
    """Yield every keyed, player-visible string of game.json in a stable order."""
    known_speakers = speaker_ids(game)
    world = TABLE_WORLD
    dialogue = TABLE_DIALOGUE

    def line_entries(lines: Iterable[dict], field: str, source: str) -> Iterator[TextEntry]:
        # A spoken line without line_id has no key in the scheme; it is skipped here and
        # reported by audit_fields() as a visible string without a key.
        for index, line in enumerate(lines):
            line_id = line.get("line_id")
            if line_id:
                yield TextEntry(line_id, line["text"], dialogue, field, f"{source}[{index}]",
                                speaker=line.get("speaker"), line_id=line_id)

    if isinstance(game.get("title"), str):
        yield TextEntry(game_title(), game["title"], world, "title", "title", extension=True)

    # Speaker display names: characters and non-actor speakers share the char.<id>.name key.
    for character in game.get("characters", []):
        yield TextEntry(character_name(character["id"]), character["name"], world,
                        "characters[].name", f"characters[{character['id']}].name")
    for speaker_id, name in game.get("non_actor_speakers", {}).items():
        yield TextEntry(character_name(speaker_id), name, world,
                        "non_actor_speakers.*", f"non_actor_speakers.{speaker_id}")

    for room in game.get("rooms", []):
        room_id = room["id"]
        room_src = f"rooms[{room_id}]"
        yield TextEntry(room_name(room_id), room["name"], world, "rooms[].name", f"{room_src}.name")
        yield from line_entries(room.get("first_entry", []), "rooms[].first_entry[].text", f"{room_src}.first_entry")
        for hotspot in room.get("hotspots", []):
            hotspot_id = hotspot["id"]
            src = f"{room_src}.hotspots[{hotspot_id}]"
            yield TextEntry(hotspot_name(hotspot_id), hotspot["name"], world,
                            "rooms[].hotspots[].name", f"{src}.name")
            look_line_id = hotspot.get("look_line_id")
            yield TextEntry(look_line_id or hotspot_look(hotspot_id), hotspot["look"], world,
                            "rooms[].hotspots[].look", f"{src}.look", line_id=look_line_id)
            for n, variant in enumerate(hotspot.get("look_variants", []), start=1):
                variant_line_id = variant.get("line_id")
                yield TextEntry(variant_line_id or hotspot_look_variant(hotspot_id, n), variant["text"], world,
                                "rooms[].hotspots[].look_variants[].text", f"{src}.look_variants[{n - 1}]",
                                line_id=variant_line_id)
        for room_exit in room.get("exits", []):
            exit_id = room_exit["id"]
            src = f"{room_src}.exits[{exit_id}]"
            yield TextEntry(exit_label(exit_id), room_exit["label"], world, "rooms[].exits[].label", f"{src}.label")
            yield TextEntry(exit_locked(exit_id), room_exit["locked_look"], world,
                            "rooms[].exits[].locked_look", f"{src}.locked_look")
            # travel overlay only: lines played the first time this transport exit is used
            yield from line_entries(room_exit.get("first_ride", []), "rooms[].exits[].first_ride[].text",
                                    f"{src}.first_ride")

    for connection in game.get("connections", []):
        a, b = connection["from"], connection["to"]
        src = f"connections[{a}->{b}]"
        yield TextEntry(connection_label(a, b), connection["label"], world, "connections[].label", f"{src}.label")
        yield TextEntry(connection_locked(a, b), connection["locked_look"], world,
                        "connections[].locked_look", f"{src}.locked_look")

    for item in game.get("items", []):
        item_id = item["id"]
        src = f"items[{item_id}]"
        yield TextEntry(item_name(item_id), item["name"], world, "items[].name", f"{src}.name")
        look_line_id = item.get("look_line_id")
        yield TextEntry(look_line_id or item_look(item_id), item["look"], world, "items[].look", f"{src}.look",
                        line_id=look_line_id)
        yield TextEntry(item_purpose(item_id), item["purpose"], world, "items[].purpose", f"{src}.purpose")

    for action in game.get("actions", []):
        action_id = action["id"]
        src = f"actions[{action_id}]"
        yield TextEntry(action_label(action_id), action["label"], world, "actions[].label", f"{src}.label")
        yield TextEntry(action_journal(action_id), action["journal_text"], world,
                        "actions[].journal_text", f"{src}.journal_text")
        if action.get("objective"):
            yield TextEntry(action_objective(action_id), action["objective"], world,
                            "actions[].objective", f"{src}.objective")
        if action.get("hint_step"):  # world overlay only
            yield TextEntry(action_hint_step(action_id), action["hint_step"], world,
                            "actions[].hint_step", f"{src}.hint_step")
        yield from line_entries(action.get("lines", []), "actions[].lines[].text", f"{src}.lines")

    for character in game.get("characters", []):
        for topic in character.get("ambient_topics", []):
            topic_id = topic["id"]
            src = f"characters[{character['id']}].ambient_topics[{topic_id}]"
            yield TextEntry(topic_label(topic_id), topic["label"], world,
                            "characters[].ambient_topics[].label", f"{src}.label")
            yield from line_entries(topic.get("lines", []), "characters[].ambient_topics[].lines[].text",
                                    f"{src}.lines")

    for cutscene in game.get("cutscenes", []):
        for index, beat in enumerate(cutscene.get("beats", [])):
            yield from line_entries(beat.get("lines", []), "cutscenes[].beats[].lines[].text",
                                    f"cutscenes[{cutscene['id']}].beats[{index}].lines")

    for quest in game.get("quests", []):
        quest_id = quest["id"]
        src = f"quests[{quest_id}]"
        yield TextEntry(quest_title(quest_id), quest["title"], world, "quests[].title", f"{src}.title")
        yield TextEntry(quest_goal(quest_id), quest["goal"], world, "quests[].goal", f"{src}.goal")
        if quest.get("reward"):
            yield TextEntry(quest_reward(quest_id), quest["reward"], world, "quests[].reward", f"{src}.reward")
        for n, hint in enumerate(quest.get("hints", []), start=1):
            yield TextEntry(quest_hint(quest_id, n), hint, world, "quests[].hints[]", f"{src}.hints[{n - 1}]")

    for puzzle in game.get("puzzles", []):
        puzzle_id = puzzle["id"]
        src = f"puzzles[{puzzle_id}]"
        yield TextEntry(puzzle_title(puzzle_id), puzzle["title"], world, "puzzles[].title", f"{src}.title")
        yield TextEntry(puzzle_clue(puzzle_id), puzzle["clue"], world, "puzzles[].clue", f"{src}.clue")
        speaker, text = split_speaker_prefix(puzzle["wrong_line"], known_speakers)
        yield TextEntry(puzzle_wrong(puzzle_id), text, world, "puzzles[].wrong_line", f"{src}.wrong_line",
                        speaker=speaker)
        speaker, text = split_speaker_prefix(puzzle["success_line"], known_speakers)
        yield TextEntry(puzzle_success(puzzle_id), text, world, "puzzles[].success_line", f"{src}.success_line",
                        speaker=speaker)
        controls = puzzle.get("controls", {})
        if controls.get("confirm_label"):
            yield TextEntry(puzzle_confirm(puzzle_id), controls["confirm_label"], world,
                            "puzzles[].controls.confirm_label", f"{src}.controls.confirm_label")
        for side in PUZZLE_OPTION_SIDES:
            for n, option in enumerate(controls.get(side, []), start=1):
                yield TextEntry(puzzle_option(puzzle_id, side, n), str(option), world,
                                f"puzzles[].controls.{side}[]", f"{src}.controls.{side}[{n - 1}]", extension=True)

    puzzle_ids = {puzzle["id"] for puzzle in game.get("puzzles", [])}
    for index, clue in enumerate(game.get("journal_contract", {}).get("clues", [])):
        match = PUZZLE_ID_PREFIX_PATTERN.match(clue)
        if match and match.group(1) in puzzle_ids:  # otherwise reported by audit_fields()
            yield TextEntry(journal_clue(match.group(1)), match.group(2), world, "journal_contract.clues[]",
                            f"journal_contract.clues[{index}]", extension=True)

    for n, shot in enumerate(game.get("epilogue", []), start=1):
        src = f"epilogue[{n - 1}]"
        yield TextEntry(epilogue_shot(n), shot["shot"], world, "epilogue[].shot", f"{src}.shot")
        speaker, text = split_speaker_prefix(shot["line"], known_speakers)
        yield TextEntry(epilogue_line(n), text, world, "epilogue[].line", f"{src}.line", speaker=speaker)


def expected_ui_scheme_keys(game: dict) -> list[str]:
    """Keys that game.json implies but that live in the hand-written ui.csv."""
    keys: list[str] = []
    for era in game.get("eras", []):
        keys += [era_card(era["year"]), era_date(era["year"]), era_year(era["year"])]
    keys += list(REQUIRED_UI_KEYS)
    return keys


# --------------------------------------------------------------------------- field audit
# Every string leaf in game.json is classified so that a new or renamed field
# cannot silently become a visible string without a key.

KEYED_FIELDS = frozenset({
    "title",
    "rooms[].name",
    "rooms[].first_entry[].text",
    "rooms[].hotspots[].name",
    "rooms[].hotspots[].look",
    "rooms[].hotspots[].look_variants[].text",
    "rooms[].exits[].label",
    "rooms[].exits[].locked_look",
    "rooms[].exits[].first_ride[].text",
    "characters[].name",
    "characters[].ambient_topics[].label",
    "characters[].ambient_topics[].lines[].text",
    "non_actor_speakers.*",
    "items[].name",
    "items[].look",
    "items[].purpose",
    "actions[].label",
    "actions[].objective",
    "actions[].journal_text",
    "actions[].hint_step",
    "actions[].lines[].text",
    "puzzles[].title",
    "puzzles[].clue",
    "puzzles[].wrong_line",
    "puzzles[].success_line",
    "puzzles[].controls.confirm_label",
    "puzzles[].controls.left[]",
    "puzzles[].controls.right[]",
    "quests[].title",
    "quests[].goal",
    "quests[].reward",
    "quests[].hints[]",
    "cutscenes[].beats[].lines[].text",
    "connections[].label",
    "connections[].locked_look",
    "journal_contract.clues[]",
    "epilogue[].shot",
    "epilogue[].line",
})

# Shown to the player through hand-written ui.csv keys (verified by check_strings.py).
UI_TABLE_FIELDS = frozenset({
    "eras[].date",  # era.<year>.date
    "journal_contract.tabs[]",  # JOURNAL_TAB_KEYS
})

# Ids, references, enums, asset paths and design-only notes: never shown to the player.
INTERNAL_FIELDS = frozenset({
    "version", "language", "source_note", "revision_note", "epilogue_rules",
    "rooms[].id", "rooms[].district", "rooms[].art_brief", "rooms[].ambience", "rooms[].blocking_note",
    "rooms[].background_asset", "rooms[].music", "rooms[].camera_family", "rooms[].layer_order[]",
    "rooms[].npc_ids[]", "rooms[].first_entry[].speaker", "rooms[].first_entry[].line_id",
    "rooms[].hotspots[].id", "rooms[].hotspots[].kind", "rooms[].hotspots[].hide_after[]",
    "rooms[].hotspots[].visible_after[]", "rooms[].hotspots[].look_line_id", "rooms[].hotspots[].character_id",
    "rooms[].hotspots[].look_variants[].after", "rooms[].hotspots[].look_variants[].line_id",
    "rooms[].exits[].id", "rooms[].exits[].to", "rooms[].exits[].travel", "rooms[].exits[].requires_done[]",
    "rooms[].exits[].first_ride[].speaker", "rooms[].exits[].first_ride[].line_id",
    "characters[].ambient_topics[].excluded_done[]",
    "characters[].id", "characters[].age", "characters[].role", "characters[].voice", "characters[].design",
    "characters[].rooms[]", "characters[].ambient_topics[].id", "characters[].ambient_topics[].requires_done[]",
    "characters[].ambient_topics[].lines[].speaker", "characters[].ambient_topics[].lines[].line_id",
    "items[].id", "items[].origin", "items[].disposition", "items[].icon", "items[].look_line_id",
    "actions[].id", "actions[].room", "actions[].target", "actions[].kind", "actions[].selected_item",
    "actions[].gives[]", "actions[].requires_done[]", "actions[].requires_items[]", "actions[].consumes[]",
    "actions[].excluded_done[]", "actions[].quest", "actions[].puzzle", "actions[].cutscene",
    "actions[].animation", "actions[].sfx", "actions[].commit_policy", "actions[].staging.rule",
    "actions[].staging.guest_speakers[]", "actions[].lines[].speaker", "actions[].lines[].line_id",
    "puzzles[].id", "puzzles[].controls.type", "puzzles[].controls.row_origin",
    "puzzles[].controls.column_origin", "puzzles[].solution[]", "puzzles[].initial[]",
    "quests[].id", "quests[].type", "quests[].actions[]", "quests[].completion", "quests[].optional_followups[]",
    "cutscenes[].id", "cutscenes[].beats[].shot", "cutscenes[].beats[].lines[].speaker",
    "cutscenes[].beats[].lines[].line_id",
    "connections[].from", "connections[].to", "connections[].travel", "connections[].requires_done[]",
    "initial_state.room", "initial_state.inventory[]", "initial_state.visited[]", "initial_state.selected_item",
    "initial_state.mode",
    "eras[].anchor", "eras[].unlocked_by",
    "epilogue[].quest", "epilogue[].after",
    "journal_contract.auto_entries", "journal_contract.pinning",
})

INTERNAL_SUBTREES = (
    "special_transitions", "postgame", "creative_lock", "bible_sections", "causal_effects", "sources",
    "acceptance", "anchor_nodes", "location_families", "cache_contract", "butterfly_effects",
    "landmark_layouts", "visual_variant_layers", "travel_contract", "stats",
)

# Objects whose keys are data (ids), normalized to "*".
DYNAMIC_KEY_OBJECTS = frozenset({"non_actor_speakers"})


def iter_string_leaves(game: dict) -> Iterator[tuple[str, str]]:
    """Yield (normalized_path, value) for every string leaf of game.json."""

    def walk(value, path: str):
        if isinstance(value, dict):
            for key, child in value.items():
                segment = "*" if path in DYNAMIC_KEY_OBJECTS else key
                yield from walk(child, f"{path}.{segment}" if path else segment)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child, f"{path}[]")
        elif isinstance(value, str):
            yield path, value

    yield from walk(game, "")


def classify_field(path: str) -> str:
    """Return "keyed", "ui", "internal" or "unclassified" for a normalized path."""
    if path in KEYED_FIELDS:
        return "keyed"
    if path in UI_TABLE_FIELDS:
        return "ui"
    if path in INTERNAL_FIELDS:
        return "internal"
    root = re.split(r"[.\[]", path, maxsplit=1)[0]
    if root in INTERNAL_SUBTREES:
        return "internal"
    return "unclassified"


def audit_fields(game: dict, entries: Iterable[TextEntry]) -> list[str]:
    """Report string fields that are neither keyed nor known to be internal, and
    keyed fields where some strings did not receive a key."""
    problems: list[str] = []
    leaf_counts: Counter = Counter()
    examples: dict[str, str] = {}
    for path, value in iter_string_leaves(game):
        kind = classify_field(path)
        if kind == "keyed":
            leaf_counts[path] += 1
        elif kind == "unclassified":
            leaf_counts[f"?{path}"] += 1
            examples.setdefault(path, value)
    entry_counts = Counter(entry.field for entry in entries)
    for path in sorted(p for p in leaf_counts if p.startswith("?")):
        field = path[1:]
        problems.append(f"unclassified string field '{field}' ({leaf_counts[path]}x), "
                        f"e.g. {examples[field][:80]!r}: add it to KEYED_FIELDS or INTERNAL_FIELDS")
    for path in sorted(p for p in leaf_counts if not p.startswith("?")):
        if leaf_counts[path] != entry_counts.get(path, 0):
            problems.append(f"field '{path}': {leaf_counts[path]} strings but {entry_counts.get(path, 0)} keyed")
    return problems


# --------------------------------------------------------------------------- CSV I/O

def format_csv_field(value: str) -> str:
    """Quote a field when needed (comma, quote, CR/LF, or leading/trailing whitespace)."""
    if value == "" or not (any(c in value for c in ',"\r\n') or value != value.strip()):
        return value
    return '"' + value.replace('"', '""') + '"'


def format_table(header: Iterable[str], rows: Iterable[Iterable[str]]) -> str:
    """Serialize a translation table: comma-delimited, LF line ends, minimal quoting."""
    lines = [",".join(format_csv_field(field) for field in header)]
    lines += [",".join(format_csv_field(field) for field in row) for row in rows]
    return "\n".join(lines) + "\n"


def read_table(path: Path) -> tuple[list[str], list[list[str]]]:
    """Read a translation table as (header, rows). Raises ValueError on encoding problems."""
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"{path.name}: starts with a UTF-8 BOM")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{path.name}: not valid UTF-8 ({error})") from error
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",", quotechar='"', strict=True)
    try:
        table = list(reader)
    except csv.Error as error:
        raise ValueError(f"{path.name}: CSV parse error at line {reader.line_num}: {error}") from error
    if not table:
        raise ValueError(f"{path.name}: empty file")
    return table[0], table[1:]


# --------------------------------------------------------------------------- Slovak text overrides

# Accepted rewrites of game.json texts in the sk column (ISSUES.md TEXT-01 / M2QA-08): game.json stays
# canonical and untouched; a row here replaces the generated sk text of one key while the game.json text
# still equals the row's "game_json" column. If game.json changes that text, the override is stale and
# both tools report it (review the rewrite). The folder carries a .gdignore, so Godot does not import it.
SK_OVERRIDES = LOCALIZATION_DIR / "overrides" / "sk_overrides.csv"
# Less revealing texts for Standard and Hard difficulty (owner 2026-10-08: "the game is hinting way too much in the
# texts and dialogues"): <base key>.std rows; the game shows them unless the difficulty is Easy (TextService.VariantKey).
GUIDANCE_VARIANTS = LOCALIZATION_DIR / "overrides" / "guidance_std.csv"
# The English source (keys,en), written by tools/en_batches.py merge; extract_strings puts it into the en column.
EN_SOURCE = LOCALIZATION_DIR / "overrides" / "en.csv"
VARIANT_SUFFIX = ".std"
VARIANT_HEADER = ("keys", "sk", "note")
OVERRIDE_HEADER = ("keys", "game_json", "sk", "note")


@dataclass(frozen=True)
class SkOverride:
    """One accepted Slovak rewrite of a generated table text."""

    key: str
    game_json: str  # the game.json text the rewrite replaces (must still match)
    sk: str  # the text shown to players
    note: str  # why (English)


def load_sk_overrides(path: Path = SK_OVERRIDES) -> tuple[dict[str, SkOverride], list[str]]:
    """Read the override table. Returns ({key: override}, problems); a missing file means no overrides."""
    if not path.exists():
        return {}, []
    problems: list[str] = []
    try:
        header, rows = read_table(path)
    except ValueError as error:
        return {}, [str(error)]
    if tuple(header) != OVERRIDE_HEADER:
        return {}, [f"{path.name}: header must be exactly {','.join(OVERRIDE_HEADER)!r}, got {','.join(header)!r}"]
    overrides: dict[str, SkOverride] = {}
    for line_no, row in enumerate(rows, start=2):
        if len(row) != len(OVERRIDE_HEADER):
            problems.append(f"{path.name}:{line_no}: expected {len(OVERRIDE_HEADER)} fields, got {len(row)}")
            continue
        key, game_json, sk, note = row
        if key in overrides:
            problems.append(f"{path.name}:{line_no}: duplicate key {key!r}")
            continue
        if not sk.strip() or sk == game_json:
            problems.append(f"{path.name}:{line_no}: {key!r}: the sk text must be non-empty and differ from game_json")
        overrides[key] = SkOverride(key, game_json, sk, note)
    return overrides, problems


def apply_sk_overrides(entries: Iterable[TextEntry], overrides: dict[str, SkOverride],
                       retired: Iterable[str] = (), overlay_keys: Iterable[str] = ()
                       ) -> tuple[list[TextEntry], list[str], list[str]]:
    """Entries with the accepted rewrites applied. Returns (entries, applied_keys, problems).

    A problem is an override whose key the scheme does not produce or whose game_json column no longer
    equals the game.json text (stale: the game.json text is kept until the override is reviewed).
    Overrides of `retired` keys (handoff lines an overlay sequence dropped) are kept and ignored, so a
    revert of the overlay needs no edit here; an override of an `overlay_keys` text is a problem (the
    overlay holds that text: edit it there).
    """
    from dataclasses import replace

    retired, overlay_keys = set(retired), set(overlay_keys)
    result, applied, problems = [], [], []
    produced = set(retired)
    for entry in entries:
        produced.add(entry.key)
        override = overrides.get(entry.key)
        if override is not None and entry.key in overlay_keys:
            problems.append(f"sk override {entry.key!r}: this text comes from a content overlay; edit it in "
                            "src/game/data/content_ext/ instead")
            result.append(entry)
        elif override is None:
            result.append(entry)
        elif override.game_json != entry.text:
            problems.append(f"stale sk override {entry.key!r}: game.json now says {entry.text[:60]!r}, "
                            f"the override replaces {override.game_json[:60]!r}")
            result.append(entry)
        else:
            result.append(replace(entry, text=override.sk))
            applied.append(entry.key)
    for key in overrides:
        if key not in produced:
            problems.append(f"sk override {key!r}: the key scheme does not produce this key")
    return result, applied, problems


# --------------------------------------------------------------------------- content overlays

def effective_game(game_path: Path = CANONICAL_GAME_JSON, use_overlays: bool = True):
    """(effective game dict, content_ext.Overlay): game.json with the content overlays applied."""
    import content_ext  # noqa: E402  (same folder)
    overlay = content_ext.load_effective_game(game_path, use_overlays=use_overlays)
    return overlay.game, overlay


def load_guidance_variants(path: Path = GUIDANCE_VARIANTS) -> tuple[dict[str, str], list[str]]:
    """Read the Standard/Hard variants ({key}.std -> sk). A missing file means no variants."""
    if not path.exists():
        return {}, []
    try:
        header, rows = read_table(path)
    except ValueError as error:
        return {}, [str(error)]
    if tuple(header) != VARIANT_HEADER:
        return {}, [f"{path.name}: header must be exactly {','.join(VARIANT_HEADER)!r}, got {','.join(header)!r}"]
    variants: dict[str, str] = {}
    problems: list[str] = []
    for line_no, row in enumerate(rows, start=2):
        if len(row) != len(VARIANT_HEADER):
            problems.append(f"{path.name}:{line_no}: expected {len(VARIANT_HEADER)} fields, got {len(row)}")
            continue
        key, sk, _note = row
        if not key.endswith(VARIANT_SUFFIX):
            problems.append(f"{path.name}:{line_no}: {key!r} must end with {VARIANT_SUFFIX!r}")
        elif key in variants:
            problems.append(f"{path.name}:{line_no}: duplicate key {key!r}")
        elif not sk.strip():
            problems.append(f"{path.name}:{line_no}: {key!r}: empty text")
        else:
            variants[key] = sk
    return variants, problems


def add_guidance_variants(entries: Iterable[TextEntry], variants: dict[str, str]
                          ) -> tuple[list[TextEntry], list[str], list[str]]:
    """Entries with each <base>.std variant inserted right after its base key (same table and speaker)."""
    from dataclasses import replace

    entries = list(entries)
    base_keys = {e.key for e in entries}
    by_base: dict[str, str] = {}
    problems: list[str] = []
    for key, sk in variants.items():
        base = key[: -len(VARIANT_SUFFIX)]
        if base not in base_keys:
            problems.append(f"guidance variant {key!r}: base key {base!r} does not exist")
        else:
            by_base[base] = key
    result, added = [], []
    for entry in entries:
        result.append(entry)
        vkey = by_base.get(entry.key)
        if vkey is None:
            continue
        if variants[vkey] == entry.text:
            problems.append(f"guidance variant {vkey!r}: same text as the base key")
            continue
        result.append(replace(entry, key=vkey, text=variants[vkey], field=entry.field + VARIANT_SUFFIX,
                              source=entry.source + VARIANT_SUFFIX, line_id=None, extension=True))
        added.append(vkey)
    return result, added, problems


def load_en_source(path: Path = EN_SOURCE) -> dict[str, str]:
    """{key: english} from the English source file (empty when it does not exist)."""
    if not path.exists():
        return {}
    header, rows = read_table(path)
    if tuple(header[:2]) != ("keys", "en"):
        raise ValueError(f"{path.name}: header must start with keys,en")
    return {r[0]: r[1] for r in rows if len(r) >= 2 and r[1].strip()}
