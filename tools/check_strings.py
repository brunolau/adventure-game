#!/usr/bin/env python3
"""Validate the Godot CSV translation tables in src/game/localization/.

Checks (errors make the exit code 1):
  * src/game/data/game.json exists and matches design-doc/game.json
  * every table is UTF-8 without BOM, parses as CSV, has the header "keys,sk,en"
    and exactly three fields per row
  * keys are non-empty, trimmed, single-line and unique within and across tables
  * every "sk" text is non-empty
  * placeholders such as {item} are identical in "sk" and a filled-in "en"
  * every key the scheme derives from game.json (tools/text_keys.py) exists in
    its table with the current game.json text (or with its accepted rewrite from
    localization/overrides/sk_overrides.csv while game.json still has the text
    the rewrite replaces, ISSUES.md TEXT-01), and no stale keys remain
  * no accepted rewrite contains an internal id (room, hotspot, item, action ...)
  * ui.csv contains the era cards for every era (era.<year>.card, .date with the
    game.json day and the shown year, .year = the shown four-digit year), a region.<district>.name key
    for every rooms[].district (map regions), the journal tabs from
    journal_contract (same texts) and every key in REQUIRED_UI_KEYS; other ui
    keys follow ui.<area>.<name>
  * every speaker id used by a line has a char.<id>.name key
  * no game.json string field is left unclassified (visible but unkeyed)
  * the content overlays (src/game/data/content_ext/, tools/content_ext.py) are valid; the scheme
    keys are those of the EFFECTIVE game (game.json + overlays), so every overlay text (new lines,
    new topic labels, new exits and connections, first-ride lines) must be in its table, every
    map region (travel_ext.json regions, else the districts) needs region.<id>.name and every
    exit travel style ui.travel.<style> in ui.csv

Warnings (reported, exit code unaffected): backslashes (Godot unescapes them),
leading/trailing whitespace in texts, generated tables not in canonical format.

Placeholder convention for ui.csv: {name} with an ASCII identifier, replaced by
the presentation layer after Tr().

Usage:
    python tools/check_strings.py [--game PATH] [--dir PATH] [--verbose]
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import text_keys as tk  # noqa: E402

MAX_LISTED = 25
ERA_KEY_PATTERN = re.compile(r"^era\.(\d{4})\.(card|date|year)$")
SHOWN_YEAR_PATTERN = re.compile(r"^\d{4}$")
# Map region names (ISSUES.md TEXT-02): region.<rooms[].district>.name, hand-written in ui.csv.
REGION_KEY_PATTERN = re.compile(r"^region\.([^.]+)\.name$")
CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


class Findings:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def check_data_sync(game_path: Path, findings: Findings) -> None:
    if not tk.SYNCED_GAME_JSON.exists():
        findings.error("src/game/data/game.json is missing; run tools/sync_data.py")
        return
    canonical = game_path.read_bytes().replace(b"\r\n", b"\n")
    synced = tk.SYNCED_GAME_JSON.read_bytes().replace(b"\r\n", b"\n")
    if canonical != synced:
        findings.error("src/game/data/game.json differs from design-doc/game.json; run tools/sync_data.py")


def load_table(path: Path, findings: Findings) -> dict[str, list[str]] | None:
    """Parse and structurally check one table; return {key: [sk, en]} or None when unreadable."""
    name = path.name
    if not path.exists():
        findings.error(f"{name}: file is missing")
        return None
    try:
        header, rows = tk.read_table(path)
    except ValueError as error:
        findings.error(str(error))
        return None
    if tuple(header) != tk.HEADER:
        findings.error(f"{name}: header must be exactly {','.join(tk.HEADER)!r}, got {','.join(header)!r}")
    table: dict[str, list[str]] = {}
    for line_no, row in enumerate(rows, start=2):
        if len(row) != len(tk.HEADER):
            findings.error(f"{name}:{line_no}: expected {len(tk.HEADER)} fields, got {len(row)}: {row[:1]}")
            continue
        key, sk, en = row
        if not key:
            findings.error(f"{name}:{line_no}: empty key")
            continue
        if key != key.strip() or CONTROL_CHARS.search(key):
            findings.error(f"{name}:{line_no}: key has surrounding whitespace or control characters: {key!r}")
        if key in table:
            findings.error(f"{name}:{line_no}: duplicate key {key!r}")
            continue
        if not sk.strip():
            findings.error(f"{name}:{line_no}: empty sk text for {key!r}")
        for locale, text in (("sk", sk), ("en", en)):
            if text != text.strip():
                findings.warn(f"{name}:{line_no}: {locale} text of {key!r} has leading/trailing whitespace")
            if "\\" in text:
                findings.warn(f"{name}:{line_no}: {locale} text of {key!r} contains a backslash "
                              "(Godot unescapes sequences such as \\n)")
            for placeholder in tk.placeholders(text):
                if not placeholder.isascii():
                    findings.error(f"{name}:{line_no}: non-ASCII placeholder {{{placeholder}}} in {key!r}")
        if en and tk.placeholders(sk) != tk.placeholders(en):
            findings.error(f"{name}:{line_no}: placeholders differ between sk and en for {key!r}: "
                           f"{sorted(tk.placeholders(sk))} vs {sorted(tk.placeholders(en))}")
        table[key] = [sk, en]
    if path.name in (tk.TABLE_FILE_NAMES[t] for t in tk.GENERATED_TABLES):
        canonical = tk.format_table(header, rows)
        if path.read_bytes().decode("utf-8").replace("\r\n", "\n") != canonical:
            findings.warn(f"{name}: not in canonical format; re-run tools/extract_strings.py")
    return table


def check_scheme(game: dict, tables: dict[str, dict[str, list[str]]], findings: Findings,
                 overrides_path: Path = tk.SK_OVERRIDES, overlay=None) -> None:
    overrides, problems = tk.load_sk_overrides(overrides_path)
    retired = overlay.retired_keys if overlay is not None else ()
    overlay_keys = overlay.added_keys if overlay is not None else ()
    effective, applied, stale = tk.apply_sk_overrides(tk.iter_text_entries(game), overrides, retired, overlay_keys)
    for problem in problems + stale:
        findings.error(problem)
    if applied:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from extract_strings import internal_id_pattern  # noqa: E402
        pattern = internal_id_pattern(game)
        for entry in effective:
            if entry.key in applied and pattern.search(entry.text):
                findings.error(f"sk override {entry.key!r} still contains an internal id: {pattern.findall(entry.text)}")
    entries: dict[str, tk.TextEntry] = {}
    for entry in effective:
        first = entries.setdefault(entry.key, entry)
        if first.text != entry.text:
            findings.error(f"scheme: key {entry.key!r} is produced twice with different texts "
                           f"({first.source} vs {entry.source})")

    key_owner = {}
    for table_name, table in tables.items():
        for key in table:
            if key in key_owner:
                findings.error(f"key {key!r} exists in both {key_owner[key]} and {tk.TABLE_FILE_NAMES[table_name]}")
            else:
                key_owner[key] = tk.TABLE_FILE_NAMES[table_name]

    missing, stale_text, wrong_table = [], [], []
    unreadable = Counter(entry.table for entry in entries.values() if entry.table not in tables)
    for table_name, count in unreadable.items():
        findings.error(f"{tk.TABLE_FILE_NAMES[table_name]}: unreadable, {count} scheme keys not checked")
    for key, entry in entries.items():
        if entry.table not in tables:
            continue
        table = tables[entry.table]
        if key not in table:
            owner = key_owner.get(key)
            (wrong_table if owner else missing).append(
                f"{key} (expected in {tk.TABLE_FILE_NAMES[entry.table]}{', found in ' + owner if owner else ''})")
        elif table[key][0] != entry.text:
            stale_text.append(f"{key}: table {table[key][0][:60]!r} vs expected {entry.text[:60]!r}")
    for label, items in (("missing scheme key", missing), ("key in the wrong table", wrong_table),
                         ("sk text differs from game.json", stale_text)):
        for item in items:
            findings.error(f"{label}: {item}")

    for table_name in tk.GENERATED_TABLES:
        for key in tables.get(table_name, {}):
            if key not in entries:
                findings.error(f"{tk.TABLE_FILE_NAMES[table_name]}: stale key not produced by the scheme: {key!r}")

    known = set(entries)
    for entry in entries.values():
        if entry.speaker and tk.character_name(entry.speaker) not in known:
            findings.error(f"speaker {entry.speaker!r} of {entry.key!r} has no {tk.character_name(entry.speaker)} key")

    for problem in tk.audit_fields(game, list(tk.iter_text_entries(game))):
        findings.error(f"game.json audit: {problem}")


def check_ui(game: dict, ui: dict[str, list[str]], findings: Findings, overlay=None) -> None:
    eras = {era["year"]: era for era in game.get("eras", [])}
    for key in tk.expected_ui_scheme_keys(game):
        if key not in ui:
            findings.error(f"ui.csv: missing required key {key!r}")

    # Room captions use the district (region.<district>.name); the map's regions use their ids.
    districts = {room.get("district", "") for room in game.get("rooms", [])} - {""}
    import content_ext  # noqa: E402
    regions = content_ext.region_ids(overlay) if overlay is not None else set()
    for district in sorted(districts | regions):
        if f"region.{district}.name" not in ui:
            findings.error(f"ui.csv: missing region key 'region.{district}.name'")
    for kind in sorted({e.get("travel") for r in game.get("rooms", []) for e in r.get("exits", [])} - {None}):
        if f"ui.travel.{kind}" not in ui:
            findings.error(f"ui.csv: missing travel style key 'ui.travel.{kind}'")

    for key, (sk, _en) in ui.items():
        region_match = REGION_KEY_PATTERN.match(key)
        if region_match:
            if region_match.group(1) not in districts | regions:
                findings.error(f"ui.csv: {key!r} refers to a district or map region that does not exist")
            continue
        era_match = ERA_KEY_PATTERN.match(key)
        if era_match:
            year = int(era_match.group(1))
            if year not in eras:
                findings.error(f"ui.csv: {key!r} refers to a year that is not an era in game.json")
            elif era_match.group(2) == "year":
                # The year shown for the era (presentation override; the era id stays the game.json year).
                if not SHOWN_YEAR_PATTERN.match(sk):
                    findings.error(f"ui.csv: {key!r} = {sk!r} is not a four-digit year")
            elif era_match.group(2) == "date":
                iso_year, _month, iso_day = eras[year]["date"].split("-")
                # The date shows the presented year (era.<year>.year, e.g. Ivanka 1960 shown as 1962) and the game.json day.
                shown_year = ui.get(f"era.{year}.year", (iso_year, ""))[0]
                if shown_year not in sk or not re.search(rf"(?<!\d){int(iso_day)}\.", sk):
                    findings.error(f"ui.csv: {key!r} = {sk!r} does not match game.json date {eras[year]['date']} "
                                   f"(shown year {shown_year})")
        elif not tk.UI_KEY_PATTERN.match(key):
            findings.error(f"ui.csv: key {key!r} does not follow ui.<area>.<name>")

    # Step hints (Core Hints.StepText): every quest action has its exact step text, ui.hint_step.<id> in ui.csv for
    # game.json's actions, actions[].hint_step (key action.<id>.hint_step, world.csv) for the world overlay's new and
    # relocated ones; a ui.csv row that a relocation shadows is never shown again.
    actions = {a["id"]: a for a in game.get("actions", [])}
    for quest in game.get("quests", []):
        for aid in quest.get("actions", []):
            action = actions.get(aid, {})
            if not action.get("hint_step") and f"ui.hint_step.{aid}" not in ui:
                findings.error(f"ui.csv: missing step hint 'ui.hint_step.{aid}' (quest {quest['id']})")
    for aid, action in actions.items():
        key = f"ui.hint_step.{aid}"
        if action.get("hint_step") and key in ui and ui[key][0] != action["hint_step"]:
            findings.warn(f"ui.csv: {key!r} is shadowed by the world overlay's hint_step of {aid} "
                          f"({action['hint_step'][:60]!r}); it is never shown, keep it equal or remove it")

    tabs = game.get("journal_contract", {}).get("tabs", [])
    if len(tabs) != len(tk.JOURNAL_TAB_KEYS):
        findings.error(f"journal_contract.tabs has {len(tabs)} tabs but JOURNAL_TAB_KEYS has "
                       f"{len(tk.JOURNAL_TAB_KEYS)}; update tools/text_keys.py and ui.csv")
    for key, tab in zip(tk.JOURNAL_TAB_KEYS, tabs):
        if key in ui and ui[key][0] != tab:
            findings.error(f"ui.csv: {key!r} = {ui[key][0]!r} but journal_contract.tabs says {tab!r}")


def print_block(title: str, items: list[str], verbose: bool) -> None:
    print(f"{title}: {len(items)}")
    shown = items if verbose else items[:MAX_LISTED]
    for item in shown:
        print(f"  - {item}")
    if len(items) > len(shown):
        print(f"  ... {len(items) - len(shown)} more (use --verbose)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--game", type=Path, default=tk.CANONICAL_GAME_JSON)
    parser.add_argument("--dir", type=Path, default=tk.LOCALIZATION_DIR)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--overrides", type=Path, default=tk.SK_OVERRIDES)
    args = parser.parse_args()

    findings = Findings()
    try:
        game, overlay = tk.effective_game(args.game)
    except (OSError, ValueError) as error:
        print(f"ERROR: cannot load {args.game}: {error}", file=sys.stderr)
        return 2
    for error in overlay.errors:
        findings.error(f"content overlay: {error}")

    check_data_sync(args.game, findings)
    tables: dict[str, dict[str, list[str]]] = {}
    for table_name, file_name in tk.TABLE_FILE_NAMES.items():
        table = load_table(args.dir / file_name, findings)
        if table is not None:
            tables[table_name] = table
    check_scheme(game, tables, findings, args.overrides, overlay)
    if tk.TABLE_UI in tables:
        check_ui(game, tables[tk.TABLE_UI], findings, overlay)

    for table_name, table in tables.items():
        translated = sum(1 for sk, en in table.values() if en)
        print(f"{tk.TABLE_FILE_NAMES[table_name]}: {len(table)} keys, en filled {translated}")
    print(f"total: {sum(len(t) for t in tables.values())} keys")
    print_block("errors", findings.errors, args.verbose)
    print_block("warnings", findings.warnings, args.verbose)
    print("RESULT: " + ("FAILED" if findings.errors else "OK"))
    return 1 if findings.errors else 0


if __name__ == "__main__":
    sys.exit(main())
