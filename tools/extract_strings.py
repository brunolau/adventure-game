#!/usr/bin/env python3
"""Generate the Godot CSV translation tables from game.json and dialogues.csv.

Writes src/game/localization/dialogue.csv (spoken lines: room entries, action
lines, topic lines, cutscene lines) and src/game/localization/world.csv (names,
looks, labels, journal texts, objectives, quests, hints, puzzles, epilogue).
ui.csv is hand-written and is not touched.

Keys follow the scheme in design-doc/ARCHITECTURE.md, implemented in
tools/text_keys.py. game.json is canonical: when dialogues.csv disagrees with
it, the game.json text is used and the difference is reported.

Existing translations (every column after "sk") are preserved for keys that
still exist; keys whose Slovak text changed are listed so the translation can
be reviewed.

The tables are built from the EFFECTIVE game: game.json with the content overlays of
src/game/data/content_ext/ applied (world_ext.json: new rooms, hotspots, characters, items, actions,
side quests, relocations; dialogue_ext.json: longer sequences and extra topics; travel_ext.json:
exits, connections, first-ride lines; tools/content_ext.py). An invalid overlay fails the run.
--no-overlays builds the handoff tables alone (comparison only).

Accepted Slovak rewrites (ISSUES.md TEXT-01) live in
src/game/localization/overrides/sk_overrides.csv (keys,game_json,sk,note): the
generated sk text of such a key is the override's sk while game.json still has
the override's game_json text. A stale override (game.json changed) keeps the
game.json text and fails the run until the rewrite is reviewed.

Usage:
    python tools/extract_strings.py [--game PATH] [--dialogues PATH] [--out-dir PATH]
                                    [--dry-run] [--strict] [--verbose] [--no-overlays]

Exit codes: 0 ok, 1 duplicate-key conflicts or visible strings without a key
(with --strict also dialogues.csv mismatches and content warnings), 2 input error.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import text_keys as tk  # noqa: E402

MAX_LISTED = 12


def load_dialogues(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"line_id", "speaker", "text"}
    if rows and not required.issubset(rows[0].keys()):
        raise ValueError(f"{path.name}: expected columns {sorted(required)}, got {list(rows[0].keys())}")
    return rows


def deduplicate(entries: list[tk.TextEntry]) -> tuple[list[tk.TextEntry], list[tuple], list[tuple]]:
    """Keep the first entry per key; return (unique, conflicts, same_text_duplicates)."""
    by_key: dict[str, tk.TextEntry] = {}
    conflicts, same_text = [], []
    for entry in entries:
        first = by_key.get(entry.key)
        if first is None:
            by_key[entry.key] = entry
        elif first.text != entry.text:
            conflicts.append((entry.key, first, entry))
        else:
            same_text.append((entry.key, first, entry))
    return list(by_key.values()), conflicts, same_text


def cross_check_dialogues(entries: list[tk.TextEntry], rows: list[dict]) -> dict[str, list]:
    """Compare dialogues.csv with the line_id-keyed strings of game.json."""
    by_line_id = {entry.line_id: entry for entry in entries if entry.line_id}
    report: dict[str, list] = defaultdict(list)
    counts = Counter(row["line_id"] for row in rows)
    report["duplicate_line_ids_in_csv"] = sorted(line_id for line_id, n in counts.items() if n > 1)
    seen = set()
    for row in rows:
        line_id = row["line_id"]
        seen.add(line_id)
        entry = by_line_id.get(line_id)
        if entry is None:
            report["only_in_dialogues_csv"].append(line_id)
            continue
        if row["text"] != entry.text:
            report["text_mismatches"].append((line_id, entry.text, row["text"]))
        if entry.speaker is not None and row["speaker"] != entry.speaker:
            report["speaker_mismatches"].append((line_id, entry.speaker, row["speaker"]))
    report["missing_from_dialogues_csv"] = [line_id for line_id in by_line_id if line_id not in seen]
    return report


def internal_id_pattern(game: dict) -> re.Pattern:
    """Ids that should never be visible to the player (rooms, hotspots, actions, items, puzzles, quests).
    Character ids are left out: they double as names on in-world signs."""
    ids: set[str] = set()
    for room in game.get("rooms", []):
        ids.add(room["id"])
        ids.update(hotspot["id"] for hotspot in room.get("hotspots", []))
    for collection in ("items", "actions", "puzzles", "quests", "cutscenes"):
        ids.update(entry["id"] for entry in game.get(collection, []))
    alternatives = "|".join(sorted((re.escape(i) for i in ids), key=len, reverse=True))
    return re.compile(rf"(?<![\w.])({alternatives})(?![\w])")


def find_internal_ids(entries: list[tk.TextEntry], game: dict) -> list[tuple[str, list[str], str]]:
    pattern = internal_id_pattern(game)
    hits = []
    for entry in entries:
        found = pattern.findall(entry.text)
        if found:
            hits.append((entry.key, sorted(set(found)), entry.text))
    return hits


def read_existing_translations(path: Path) -> tuple[list[str], dict[str, list[str]]]:
    """Return (extra_locale_columns, {key: [sk, extra...]}) of an existing table."""
    if not path.exists():
        return [], {}
    header, rows = tk.read_table(path)
    if len(header) < 2 or header[0] != tk.HEADER[0] or header[1] != tk.SOURCE_LOCALE:
        raise ValueError(f"{path.name}: unexpected header {header}")
    extra = header[2:]
    existing = {}
    for row in rows:
        if row:
            existing[row[0]] = (row + [""] * len(header))[1:len(header)]
    return extra, existing


def build_rows(entries: list[tk.TextEntry], path: Path) -> tuple[list[str], list[list[str]], list[str]]:
    """Rows for one table, keeping existing translations. Returns (header, rows, keys_with_changed_sk)."""
    extra, existing = read_existing_translations(path)
    locales = list(tk.HEADER[2:]) + [locale for locale in extra if locale not in tk.HEADER]
    header = [tk.HEADER[0], tk.SOURCE_LOCALE] + locales
    rows, changed = [], []
    for entry in entries:
        old = existing.get(entry.key)
        translations = [""] * len(locales)
        if old is not None:
            old_by_locale = dict(zip(extra, old[1:]))
            translations = [old_by_locale.get(locale, "") for locale in locales]
            if old[0] != entry.text and any(translations):
                changed.append(entry.key)
        rows.append([entry.key, entry.text] + translations)
    return header, rows, changed


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(tk.REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def print_list(title: str, items: list, formatter=str, verbose: bool = False) -> None:
    print(f"{title}: {len(items)}")
    shown = items if verbose else items[:MAX_LISTED]
    for item in shown:
        print(f"  - {formatter(item)}")
    if len(items) > len(shown):
        print(f"  ... {len(items) - len(shown)} more (use --verbose)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--game", type=Path, default=tk.CANONICAL_GAME_JSON)
    parser.add_argument("--dialogues", type=Path, default=tk.DIALOGUES_CSV)
    parser.add_argument("--out-dir", type=Path, default=tk.LOCALIZATION_DIR)
    parser.add_argument("--dry-run", action="store_true", help="report only, do not write tables")
    parser.add_argument("--strict", action="store_true", help="also fail on mismatches and content warnings")
    parser.add_argument("--verbose", action="store_true", help="list every finding")
    parser.add_argument("--overrides", type=Path, default=tk.SK_OVERRIDES, help="accepted sk rewrites (TEXT-01)")
    parser.add_argument("--no-overlays", action="store_true", help="ignore src/game/data/content_ext (handoff only)")
    args = parser.parse_args()

    try:
        game, overlay = tk.effective_game(args.game, use_overlays=not args.no_overlays)
        dialogue_rows = load_dialogues(args.dialogues)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if overlay.errors:
        for error in overlay.errors[:40]:
            print(f"ERROR: {error}", file=sys.stderr)
        print("RESULT: FAILED (content overlay invalid; tables not written)")
        return 1

    all_entries = list(tk.iter_text_entries(game))
    entries, conflicts, same_text = deduplicate(all_entries)
    audit_problems = tk.audit_fields(game, all_entries)
    # dialogues.csv is the handoff's line list: compare it with the handoff lines only.
    dialogue_report = cross_check_dialogues([e for e in entries if e.key not in overlay.added_keys], dialogue_rows)
    for line_id in overlay.retired_keys:  # dropped by an overlay sequence: not missing from the game
        if line_id in dialogue_report.get("only_in_dialogues_csv", []):
            dialogue_report["only_in_dialogues_csv"].remove(line_id)
    overrides, override_problems = tk.load_sk_overrides(args.overrides)
    entries, overridden, stale = tk.apply_sk_overrides(entries, overrides, overlay.retired_keys, overlay.added_keys)
    override_problems += stale
    variants, variant_problems = tk.load_guidance_variants()
    entries, variant_keys, variant_add_problems = tk.add_guidance_variants(entries, variants)
    override_problems += variant_problems + variant_add_problems
    id_hits = find_internal_ids(entries, game)

    tables = {table: [e for e in entries if e.table == table] for table in tk.GENERATED_TABLES}
    changed_translations: dict[str, list[str]] = {}
    if not args.dry_run:
        args.out_dir.mkdir(parents=True, exist_ok=True)
    for table, table_entries in tables.items():
        path = args.out_dir / tk.TABLE_FILE_NAMES[table]
        try:
            header, rows, changed = build_rows(table_entries, path)
        except ValueError as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 2
        changed_translations[table] = changed
        if not args.dry_run:
            path.write_bytes(tk.format_table(header, rows).encode("utf-8"))

    # ------------------------------------------------------------------ report
    verb = "would write" if args.dry_run else "wrote"
    print(f"source: {display_path(args.game)} + {display_path(args.dialogues)} ({len(dialogue_rows)} rows)")
    if overlay.used_dialogue or overlay.used_travel or overlay.used_world:
        print(f"content overlays: {len(overlay.sequences) - len(overlay.new_topics)} extended exchanges, "
              f"{len(overlay.new_topics)} new topics, {len(overlay.added_keys)} overlay keys, "
              f"{len(overlay.retired_keys)} retired keys; exits -{len(overlay.removed_exits)} +{len(overlay.added_exits)}, "
              f"connections -{len(overlay.removed_connections)} +{len(overlay.added_connections)}, regions {len(overlay.regions)}; "
              f"world: rooms +{len(overlay.added_rooms)}, hotspots +{len(overlay.added_hotspots)}, "
              f"characters +{len(overlay.added_characters)}, items +{len(overlay.added_items)}, "
              f"actions +{len(overlay.added_actions)}, quests +{len(overlay.added_quests)}, "
              f"relocations {len(overlay.relocations)}, retired hotspots {len(overlay.retired_hotspots)}")
    for table, table_entries in tables.items():
        print(f"{verb} {tk.TABLE_FILE_NAMES[table]}: {len(table_entries)} keys")
    by_prefix = Counter(e.key.split(".", 1)[0] for e in entries)
    print("keys by prefix: " + ", ".join(f"{prefix} {n}" for prefix, n in sorted(by_prefix.items())))
    line_id_keys = sum(1 for e in entries if e.line_id)
    print(f"line_id keys: {line_id_keys}; generated keys: {len(entries) - line_id_keys}")
    print()

    extensions = [e for e in entries if e.extension]
    ext_fields = Counter(e.field for e in extensions)
    print("texts without a key in the ARCHITECTURE.md table (scheme extensions):")
    for field, n in sorted(ext_fields.items()):
        sample = next(e for e in extensions if e.field == field)
        print(f"  - {field}: {n} keys, e.g. {sample.key} = {sample.text!r}")
    split = [e for e in entries if e.speaker and not e.line_id]
    print(f"speaker prefixes split off (\"SPEAKER: text\" -> text, speaker via char.<id>.name): {len(split)}")
    for field, n in sorted(Counter(e.field for e in split).items()):
        print(f"  - {field}: {n}")
    print()

    print_list("duplicate keys with different texts (first kept)", conflicts,
               lambda c: f"{c[0]}: {c[1].source} {c[1].text!r} vs {c[2].source} {c[2].text!r}", args.verbose)
    print_list("duplicate keys with identical texts (merged)", same_text,
               lambda c: f"{c[0]}: {c[1].source} and {c[2].source}", args.verbose)
    print_list("visible strings without a key / unclassified fields", audit_problems, str, args.verbose)
    print()
    print("dialogues.csv vs game.json (game.json wins):")
    for name in ("text_mismatches", "speaker_mismatches", "only_in_dialogues_csv",
                 "missing_from_dialogues_csv", "duplicate_line_ids_in_csv"):
        items = dialogue_report.get(name, [])
        fmt = (lambda m: f"{m[0]}: game.json {m[1]!r} / csv {m[2]!r}") if "mismatch" in name else str
        print_list(f"  {name}", items, fmt, args.verbose)
    print()
    print(f"sk overrides applied (TEXT-01, {display_path(args.overrides)}): {len(overridden)}")
    print(f"Standard/Hard guidance variants ({display_path(tk.GUIDANCE_VARIANTS)}): {len(variant_keys)}")
    print_list("sk override problems", override_problems, str, args.verbose)
    print_list("content warning: internal ids inside player-visible texts", id_hits,
               lambda h: f"{h[0]} {h[1]}: {h[2][:90]!r}", args.verbose)
    if id_hits:
        print("  by key prefix: " + ", ".join(
            f"{p} {n}" for p, n in sorted(Counter(h[0].split(".", 1)[0] for h in id_hits).items())))
    for table, changed in changed_translations.items():
        if changed:
            print_list(f"{tk.TABLE_FILE_NAMES[table]}: Slovak text changed, review translations", changed,
                       str, args.verbose)

    mismatches = sum(len(dialogue_report.get(n, [])) for n in
                     ("text_mismatches", "speaker_mismatches", "only_in_dialogues_csv",
                      "missing_from_dialogues_csv", "duplicate_line_ids_in_csv"))
    failed = bool(conflicts or audit_problems or override_problems)
    if args.strict:
        failed = failed or bool(mismatches or id_hits)
    print()
    print("RESULT: " + ("FAILED" if failed else "OK"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
