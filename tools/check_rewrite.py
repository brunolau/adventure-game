#!/usr/bin/env python3
"""Validate a chunk rewrite of the Slovak game texts before it becomes an override.

Input: a CSV with the header exactly "keys,sk_new,note" (UTF-8, comma-delimited, quoted as
needed), one row per rewritten key. Rows whose sk_new equals the current text are ignored.

Errors (exit code 1):
  * malformed CSV, wrong header, duplicate keys, unknown keys (not in dialogue/world/ui.csv)
  * key outside the chunk given with --chunk
  * empty text, line breaks or control characters, a speaker prefix ("ADAM: ...", "Mira: ...")
  * internal ids (S17, G01, Q9C, P03, M11B, CS04, hotspot/item/action ids) that the current
    text does not already contain
  * text longer than the hard limit of its kind (docs/writing/glossary.json "limits")
  * a protected fact or verbatim text from docs/writing/glossary.json missing
  * a code or number from the current text missing (K-17, Z-17, 3–2–6, 1982, 38 ...) in a
    strict kind (objectives, journal, goals, hints, clues, labels, puzzle options)
  * a person or place named in the current text missing in a strict kind
  * a glossary term (item, device, concept) of the current text missing in a strict kind
    (write "drop: <name, term or number>" in the note to acknowledge an intended drop, e.g. a
    decided rename; it then becomes a warning. Protected facts and verbatim texts cannot be dropped)
  * ui.csv placeholders ({item}, {n}) changed
  * journal text that game.json keeps identical to the objective no longer identical

Warnings (exit code 0 unless --strict):
  * length above the soft limit, ui text much longer than before
  * numbers, names or terms missing in spoken lines and looks (a joke may drop them), or a
    protected token that moved to another line of the same exchange
  * deprecated words (glossary "deprecated"), design jargon (glossary "jargon"), modern words
    in 1960/1982 dialogue (glossary "anachronisms")
  * a topic label that repeats Adam's first line, an exit label that no longer equals the
    room name it used to equal, a key that is never shown in play

Content overlays (src/game/data/content_ext/, tools/content_ext.py) are checked too (the live
overlays, or the drafts given with --overlay / --world, restricted to --chunk; the texts of the world
overlay - new rooms, hotspots, items, characters, actions, quests, epilogue shots, step hints - are
overlay texts like the new lines):
  * every new overlay text (new lines, new topic labels, new exit / connection texts, first-ride
    lines) gets the same per-text checks as a rewrite (length, internal ids, speaker prefix,
    deprecated words, jargon, anachronisms)
  * protected facts and verbatim lines of an extended exchange: a dropped handoff line that carries
    a protected fact is an error unless the fact is still stated in another line of the same
    exchange (action / topic / first entry); a dropped verbatim line is always an error. A rewrite
    of a kept key may move a fact into a new overlay line of its exchange (a warning, as before)
  * a CSV row for an overlay key is an error: overlay texts are edited in the overlay

With --overrides-out PATH the tool writes the complete merged override table (the current
src/game/localization/overrides/sk_overrides.csv plus the rows of this file, game_json =
the game.json text) to PATH, and ui.csv rows to PATH.ui.csv; it never edits the live files.

Usage:
    python tools/check_rewrite.py OUT.csv [--chunk C1] [--strict] [--verbose]
                                  [--overrides-out PATH] [--overlay DRAFT_ext.json]
    python tools/check_rewrite.py --overlay-only [--overlay DRAFT_ext.json] [--world WORLD.json] [--chunk C1]
    python tools/check_rewrite.py --self-test     (glossary rules must hold for the current texts,
                                                   the live overlay included)

Exit codes: 0 ok, 1 errors found, 2 input error.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import text_keys as tk  # noqa: E402
import writing_bundles as wb  # noqa: E402

GLOSSARY_JSON = wb.WRITING_DIR / "glossary.json"
INPUT_HEADER = ("keys", "sk_new", "note")
MAX_LISTED = 40

# Slovak number words (cardinals and ordinal stems) -> value, for the "numbers kept" check.
_UNITS = {"jeden": 1, "jedna": 1, "jedno": 1, "dva": 2, "dve": 2, "tri": 3, "štyri": 4, "päť": 5, "šesť": 6,
          "sedem": 7, "osem": 8, "deväť": 9}
_TEENS = {"desať": 10, "jedenásť": 11, "dvanásť": 12, "trinásť": 13, "štrnásť": 14, "pätnásť": 15,
          "šestnásť": 16, "sedemnásť": 17, "osemnásť": 18, "devätnásť": 19}
_TENS = {"dvadsať": 20, "tridsať": 30, "štyridsať": 40, "päťdesiat": 50, "šesťdesiat": 60,
         "sedemdesiat": 70, "osemdesiat": 80, "deväťdesiat": 90}
_ORDINALS = {"druh": 2, "tret": 3, "treť": 3, "štvrt": 4, "štvrť": 4, "piat": 5, "šiest": 6, "siedm": 7, "ôsm": 8, "deviat": 9,
             "desiat": 10, "dvanást": 12, "trinást": 13, "dvadsiat": 20, "tridsiat": 30}
_NUMBER_WORDS: dict[str, int] = {}
for _w, _v in {**_UNITS, **_TEENS, **_TENS}.items():
    _NUMBER_WORDS[_w] = _v
for _t, _tv in _TENS.items():
    for _u, _uv in _UNITS.items():
        if _uv > 1 or _u == "jeden":
            _NUMBER_WORDS[_t + _u] = _tv + _uv
_NUMBER_WORDS.update({"dvoch": 2, "troch": 3, "štyroch": 4, "piatich": 5, "šiestich": 6, "dvadsiatich": 20,
                      "dvadsiatichpiatich": 25, "tridsiatichôsmich": 38})
# Small counts are too common in jokes to be tracked as words ("jeden", "dva").
_TRACKED_MIN = 3

WORD_RE = re.compile(r"[A-Za-zÀ-žÁ-ž]+")
DIGITS_RE = re.compile(r"\d+")
CODE_RE = re.compile(r"\b[A-ZÁ-Ž]-\d+\b|\d+\s*[–—-]\s*\d+(?:\s*[–—-]\s*\d+)*|\d+\s*×\s*\d+|\d+°")
PREFIX_RE = re.compile(r"^\s*([A-ZÁ-Ža-zá-ž0-9_ ]{2,30}):\s")
GENERIC_ID_RE = re.compile(r"(?<![\w.-])(S\d{2}(?:\.\w+)?|[GBICDEFJ]\d{2}|Q\d[A-F]|P0\d|M\d{2}[A-D]?|M1[1-5][A-D]?|CS\d{2}|Q\d)(?![\w-])")


def norm_dash(text: str) -> str:
    return re.sub(r"\s*[–—-]\s*", "–", re.sub(r"\s*×\s*", "×", text))


def number_values(text: str) -> set[int]:
    values = {int(d) for d in DIGITS_RE.findall(text)}
    for word in WORD_RE.findall(text.lower()):
        if word in _NUMBER_WORDS and _NUMBER_WORDS[word] >= _TRACKED_MIN:
            values.add(_NUMBER_WORDS[word])
            continue
        for stem, value in _ORDINALS.items():
            if word.startswith(stem) and len(word) <= len(stem) + 3 and value >= _TRACKED_MIN:
                if stem == "druh" and word not in ("druhý", "druhá", "druhé", "druhom", "druhého", "druhej", "druhú"):
                    continue
                values.add(value)
    return values


def codes(text: str) -> set[str]:
    return {norm_dash(c) for c in CODE_RE.findall(text)}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, key: str, message: str) -> None:
        self.errors.append(f"{key}: {message}")

    def warn(self, key: str, message: str) -> None:
        self.warnings.append(f"{key}: {message}")


# --------------------------------------------------------------------------- loading

def load_glossary(path: Path = GLOSSARY_JSON) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_names"] = {name: re.compile(rx) for name, rx in {**data["names"], **data["places"]}.items()}
    data["_terms"] = {name: re.compile(rx, re.IGNORECASE) for name, rx in data["terms"].items()}
    data["_deprecated"] = [(re.compile(d["pattern"], re.IGNORECASE), d["use"]) for d in data["deprecated"]]
    data["_jargon"] = [re.compile(rx, re.IGNORECASE) for rx in data["jargon"]]
    ana = data["anachronisms"]
    data["_anachronisms"] = [re.compile(rx, re.IGNORECASE) for rx in ana["patterns"]]
    data["_protected"] = defaultdict(list)
    for rule in data["protected"]:
        compiled = [re.compile(rx) for rx in rule["require"]]
        for key in rule["keys"]:
            data["_protected"][key].append((rule["id"], rule["why"], rule["require"], compiled))
    data["_verbatim"] = defaultdict(list)
    for rule in data["verbatim"]:
        for key in rule["keys"]:
            data["_verbatim"][key].append(rule)
    return data


def read_rewrite(path: Path, report: Report) -> list[tuple[int, str, str, str]]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        report.error(path.name, "file starts with a UTF-8 BOM; save as UTF-8 without BOM")
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{path.name}: not valid UTF-8 ({error})") from error
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        table = list(reader)
    except csv.Error as error:
        raise ValueError(f"{path.name}: CSV parse error at line {reader.line_num}: {error}") from error
    if not table:
        raise ValueError(f"{path.name}: empty file")
    if tuple(table[0]) != INPUT_HEADER:
        raise ValueError(f"{path.name}: header must be exactly {','.join(INPUT_HEADER)!r}, got {','.join(table[0])!r}")
    rows = []
    for line_no, row in enumerate(table[1:], start=2):
        if not row or (len(row) == 1 and not row[0].strip()):
            continue
        if len(row) != 3:
            report.error(f"{path.name}:{line_no}", f"expected 3 fields (keys,sk_new,note), got {len(row)}")
            continue
        rows.append((line_no, row[0], row[1], row[2]))
    return rows


def internal_ids(game: dict) -> re.Pattern:
    from extract_strings import internal_id_pattern
    return internal_id_pattern(game)


def speaker_prefixes(game: dict) -> set[str]:
    names = set(tk.speaker_ids(game))
    for character in game.get("characters", []):
        full = character["name"]
        names.add(full)
        names.add(full.split()[0])
    names.update(game.get("non_actor_speakers", {}).values())
    names.update({"Tóno", "Mira", "Oto", "Babka", "Adam", "Systém", "Rozprávač"})
    return {n.lower() for n in names}


# --------------------------------------------------------------------------- block lookup

LINE_SUFFIX_RE = re.compile(r"^[A-Za-z]{0,3}\d{1,4}$")


def block_of(key: str) -> str | None:
    """Exchange a line belongs to: action, topic, first entry or cutscene beat (for 'moved fact' tolerance).
    Overlay lines (action.G02.x01, topic.ELA.extra 1.001, entry.S07.x01) belong to the same exchange."""
    parts = key.rsplit(".", 1)
    if len(parts) == 2 and LINE_SUFFIX_RE.match(parts[1]) and key.startswith(("action.", "topic.", "cutscene.", "entry.")):
        return parts[0]
    return None


def block_texts(block: str, index: dict[str, wb.KeyInfo], new: dict[str, str], skip: str) -> str:
    texts = []
    for key, info in index.items():
        if key != skip and block_of(key) == block:
            texts.append(new.get(key, info.text))
    if block.startswith("action."):
        aid = block.split(".", 1)[1]
        for suffix in ("label", "objective", "journal"):
            k = f"action.{aid}.{suffix}"
            if k in index and k != skip:
                texts.append(new.get(k, index[k].text))
    return " ".join(texts)


# --------------------------------------------------------------------------- checks

def check_row(key: str, text: str, note: str, info: wb.KeyInfo, ctx: dict, report: Report) -> None:
    gl = ctx["glossary"]
    cur = info.text
    strict = info.kind in gl["strict_kinds"]
    miss = report.error if strict else report.warn

    if not text.strip():
        report.error(key, "empty text")
        return
    if text != text.strip():
        report.warn(key, "leading/trailing whitespace")
    if re.search(r"[\x00-\x1f\x7f]", text):
        report.error(key, "line break or control character; one key = one subtitle, do not split lines")
    if "\\" in text:
        report.warn(key, "backslash (Godot unescapes sequences such as \\n)")
    if info.never_shown and not info.overlay:
        report.warn(key, "this text is never shown in play (exit without a lock); leave it unchanged")

    # speaker prefix
    match = PREFIX_RE.match(text)
    if match and match.group(1).strip().lower() in ctx["speakers"] and not PREFIX_RE.match(cur):
        report.error(key, f"speaker prefix {match.group(1)!r}: the speaker comes from the data, write only the text")

    # internal ids
    found = set(ctx["id_pattern"].findall(text)) | set(GENERIC_ID_RE.findall(text))
    known = set(ctx["id_pattern"].findall(cur)) | set(GENERIC_ID_RE.findall(cur))
    new_ids = sorted(i for i in found - known if i)
    if new_ids:
        report.error(key, f"internal id(s) in player text: {new_ids}")

    # length
    if info.kind == wb.KIND_UI:
        if len(text) > max(len(cur) * 1.3, len(cur) + 15):
            report.warn(key, f"ui text grew from {len(cur)} to {len(text)} characters; check the layout")
        if tk.placeholders(text) != tk.placeholders(cur):
            report.error(key, f"placeholders changed: {sorted(tk.placeholders(cur))} -> {sorted(tk.placeholders(text))}")
    else:
        limit = gl["limits"].get(info.kind)
        if limit:
            if len(text) > limit["hard"]:
                report.error(key, f"{len(text)} characters, hard limit for {info.kind} is {limit['hard']}")
            elif len(text) > limit["soft"]:
                report.warn(key, f"{len(text)} characters, aim for {info.kind} is <= {limit['soft']}")

    block = block_of(key)
    neighbours = block_texts(block, ctx["index"], ctx["new"], key) if block else ""

    # "drop:<word>" in the note acknowledges an intentional drop of a name, term or number
    # (e.g. a decided rename); protected facts and verbatim texts cannot be dropped.
    dropped = {d.strip().lower() for d in re.findall(r"drop:\s*([^,;]+)", note)}

    def missing(what: str, present_elsewhere: bool, hard: bool, token: str = "") -> None:
        if token and token.lower() in dropped:
            report.warn(key, f"{what} (acknowledged in the note)")
        elif present_elsewhere:
            report.warn(key, f"{what}; it still appears elsewhere in this exchange: confirm the move in the note")
        elif hard:
            report.error(key, what)
        else:
            report.warn(key, what)

    # protected rules
    for rule_id, why, raw, compiled in gl["_protected"].get(key, []):
        for rx_text, rx in zip(raw, compiled):
            if not rx.search(text):
                missing(f"protected fact {rule_id} ({why}) needs /{rx_text}/", bool(rx.search(neighbours)), True)
    for rule in gl["_verbatim"].get(key, []):
        ok = rule["text"] in text if rule.get("substring") else text == rule["text"]
        if not ok:
            report.error(key, f"verbatim text required ({rule['why']}): {rule['text']!r}")

    # codes and numbers
    for code in sorted(codes(cur) - codes(text)):
        missing(f"code/number {code!r} of the current text is missing", code in codes(neighbours), True, code)
    lost = number_values(cur) - number_values(text)
    if lost:
        missing(f"number(s) {sorted(lost)} of the current text are missing", bool(lost & number_values(neighbours)),
                strict, ",".join(str(n) for n in sorted(lost)))

    # names, places, terms
    for name, rx in gl["_names"].items():
        if rx.search(cur) and not rx.search(text):
            missing(f"name {name!r} of the current text is missing", bool(rx.search(neighbours)), strict, name)
    for term, rx in gl["_terms"].items():
        if rx.search(cur) and not rx.search(text):
            if strict or info.kind == wb.KIND_NAME:
                missing(f"term {term!r} of the current text is missing", bool(rx.search(neighbours)), strict, term)

    # wording
    if info.kind != wb.KIND_UI:
        for rx, use in gl["_deprecated"]:
            hit = rx.search(text)
            if hit:
                report.warn(key, f"deprecated {hit.group(0)!r}: use {use}")
        for rx in gl["_jargon"]:
            hit = rx.search(text)
            if hit and not (key.startswith("look.S34") and "kulis" in hit.group(0).lower()):
                report.warn(key, f"design jargon {hit.group(0)!r}: say it as the character would")
        ana = gl["anachronisms"]
        if info.era in ana["eras"] and info.kind == wb.KIND_LINE and (info.speaker or "") not in ana["speakers_exempt"]:
            for rx in gl["_anachronisms"]:
                hit = rx.search(text)
                if hit:
                    report.warn(key, f"{hit.group(0)!r} sounds anachronistic for {info.era}")


def check_pairs(index: dict[str, wb.KeyInfo], new: dict[str, str], game: dict, model: wb.Model, report: Report) -> None:
    def val(key: str) -> str:
        return new.get(key, index[key].text) if key in index else ""

    # journal == objective where game.json has them identical
    for action in game["actions"]:
        if action.get("objective") and action["objective"] == action["journal_text"]:
            jk, ok = tk.action_journal(action["id"]), tk.action_objective(action["id"])
            if (jk in new or ok in new) and val(jk) != val(ok):
                report.error(jk, "game.json keeps journal and objective identical; write the same text in both keys")

    # topic label vs the first line
    def label_vs_first(label_key: str, lines: list[dict]) -> None:
        if not lines or label_key not in index:
            return
        first = lines[0]
        fk = first.get("line_id")
        if fk not in index or (label_key not in new and fk not in new):
            return
        label, line = val(label_key), val(fk)
        if first.get("speaker") == "ADAM":
            ratio = SequenceMatcher(None, label.lower().strip("?!. "), line.lower().strip("?!. ")).ratio()
            if ratio > 0.75:
                report.warn(label_key, f"label repeats Adam's first line ({line!r}); make the label the topic, "
                                       "the line the actual question")

    for character in game["characters"]:
        for topic in character.get("ambient_topics", []):
            label_vs_first(tk.topic_label(topic["id"]), topic.get("lines", []))
    for action in game["actions"]:
        if action["kind"] == "topic":
            label_vs_first(tk.action_label(action["id"]), action.get("lines", []))

    # exit labels that equal the target room name
    for room in game["rooms"]:
        for room_exit in room.get("exits", []):
            lk, rk = tk.exit_label(room_exit["id"]), tk.room_name(room_exit["to"])
            if lk in index and rk in index and index[lk].text == index[rk].text and (lk in new or rk in new):
                if val(lk) != val(rk):
                    report.warn(lk, f"exit label used to equal the room name of {room_exit['to']}; "
                                    f"now {val(lk)!r} vs {val(rk)!r}")


def check_overlay(overlay, index: dict[str, wb.KeyInfo], new: dict[str, str], ctx: dict, report: Report,
                  chunk: str | None) -> int:
    """Checks of the content overlays (see the module docstring). Returns the number of overlay texts checked."""
    from dataclasses import replace

    gl = ctx["glossary"]
    checked = 0
    for key in sorted(overlay.added_keys):
        info = index.get(key)
        if info is None:
            report.error(key, "overlay text has no key in the index (run tools/extract_strings.py)")
            continue
        if chunk and info.chunk != chunk:
            continue
        checked += 1
        check_row(key, info.original or info.text, "", replace(info, text="", original=""), ctx, report)

    def text_of(key: str) -> str:
        if key in new:
            return new[key]
        info = index.get(key)
        return info.text if info else ""

    for block, dropped in overlay.dropped.items():
        if not dropped:
            continue
        sequence = " ".join(text_of(k) for k in overlay.sequences.get(block, []))
        for key in dropped:
            if chunk and ctx["base_chunk"].get(key, chunk) != chunk:
                continue
            for rule in gl["_verbatim"].get(key, []):
                report.error(key, f"verbatim line dropped by the overlay sequence {block} ({rule['why']}); keep it")
            for rule_id, why, raw, compiled in gl["_protected"].get(key, []):
                for rx_text, rx in zip(raw, compiled):
                    if not rx.search(sequence):
                        report.error(key, f"protected fact {rule_id} ({why}) dropped with this line: no line of "
                                          f"{block} states /{rx_text}/ any more")
                    else:
                        report.warn(key, f"line dropped by the overlay; protected fact {rule_id} moved within {block}")
    return checked


def self_test(index: dict[str, wb.KeyInfo], glossary: dict, report: Report, retired: set[str] = frozenset()) -> None:
    """Every protected/verbatim rule must hold for the current texts; every rule key must exist
    (keys an overlay retired are checked by check_overlay instead)."""
    for key, rules in glossary["_protected"].items():
        if key in retired:
            continue
        if key not in index:
            report.error(key, "protected rule refers to an unknown key")
            continue
        for rule_id, _why, raw, compiled in rules:
            for rx_text, rx in zip(raw, compiled):
                if not rx.search(index[key].text):
                    report.error(key, f"rule {rule_id} /{rx_text}/ does not match the current text "
                                      f"{index[key].text[:80]!r}")
    for key, rules in glossary["_verbatim"].items():
        if key in retired:
            report.error(key, "a verbatim line was dropped by a content overlay sequence")
            continue
        if key not in index:
            report.error(key, "verbatim rule refers to an unknown key")
            continue
        for rule in rules:
            cur = index[key].text
            ok = rule["text"] in cur if rule.get("substring") else cur == rule["text"]
            if not ok:
                report.error(key, f"verbatim {rule['text']!r} does not match the current text {cur[:80]!r}")


def write_overrides(path: Path, rows: dict[str, tuple[str, str]], index: dict[str, wb.KeyInfo]) -> tuple[int, int]:
    """Write the merged override table and a ui patch next to it. Returns (override rows, ui rows)."""
    existing, problems = tk.load_sk_overrides(tk.SK_OVERRIDES)
    if problems:
        raise ValueError("current sk_overrides.csv has problems: " + "; ".join(problems[:3]))
    merged = {k: [o.key, o.game_json, o.sk, o.note] for k, o in existing.items()}
    ui_rows = []
    for key, (text, note) in rows.items():
        info = index[key]
        if info.table == tk.TABLE_UI:
            ui_rows.append([key, text, ""])
            continue
        if text == info.original:
            merged.pop(key, None)  # back to the game.json text
        else:
            merged[key] = [key, info.original, text, note or "TEXT-04 rewrite"]
    order = {k: n for n, k in enumerate(index)}
    body = sorted(merged.values(), key=lambda r: order.get(r[0], 10**9))
    path.write_bytes(tk.format_table(tk.OVERRIDE_HEADER, body).encode("utf-8"))
    if ui_rows:
        Path(str(path) + ".ui.csv").write_bytes(tk.format_table(tk.HEADER, ui_rows).encode("utf-8"))
    return len(body), len(ui_rows)


def print_block(title: str, items: list[str], verbose: bool) -> None:
    print(f"{title}: {len(items)}")
    shown = items if verbose else items[:MAX_LISTED]
    for item in shown:
        print(f"  - {item}")
    if len(items) > len(shown):
        print(f"  ... {len(items) - len(shown)} more (use --verbose)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", nargs="?", type=Path, help="chunk output: keys,sk_new,note")
    parser.add_argument("--chunk", choices=list(wb.CHUNKS), help="every key must belong to this chunk")
    parser.add_argument("--strict", action="store_true", help="warnings count as errors")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--overrides-out", type=Path, help="write the merged override table here (not the live file)")
    parser.add_argument("--glossary", type=Path, default=GLOSSARY_JSON)
    parser.add_argument("--self-test", action="store_true", help="check the glossary rules against the current texts")
    parser.add_argument("--overlay", type=Path, help="check this dialogue overlay draft instead of the live dialogue_ext.json "
                        "(a combined draft {world_ext, dialogue_ext} checks both parts)")
    parser.add_argument("--world", type=Path, help="check this world overlay draft instead of the live world_ext.json")
    parser.add_argument("--overlay-only", action="store_true", help="check only the content overlay (no CSV)")
    args = parser.parse_args()
    if not args.csv and not args.self_test and not args.overlay_only:
        parser.error("give a CSV file, --overlay-only or --self-test")

    report = Report()
    try:
        import content_ext  # noqa: E402
        dialogue = args.overlay or content_ext.DIALOGUE_EXT
        world = content_ext.read_overlay(args.world) if args.world else content_ext.read_overlay(content_ext.WORLD_EXT)
        if args.world and isinstance(world, dict) and isinstance(world.get("world_ext"), dict):
            world = world["world_ext"]
        if args.overlay:
            # A writing draft may carry a "travel" proposal; the travel overlay is checked from travel_ext.json.
            draft = json.loads(args.overlay.read_text(encoding="utf-8"))
            if isinstance(draft.get("dialogue_ext"), dict):  # combined content draft
                if isinstance(draft.get("world_ext"), dict) and not args.world:
                    world = draft["world_ext"]
                draft = draft["dialogue_ext"]
            draft.pop("travel", None)
            base = tk.load_json(tk.CANONICAL_GAME_JSON)
            overlay = content_ext.apply_overlays(base, draft, content_ext.read_overlay(content_ext.TRAVEL_EXT), world)
        elif args.world:
            base = tk.load_json(tk.CANONICAL_GAME_JSON)
            overlay = content_ext.apply_overlays(base, content_ext.read_overlay(dialogue), content_ext.read_overlay(content_ext.TRAVEL_EXT), world)
        else:
            overlay = content_ext.load_effective_game(dialogue=dialogue)
        if overlay.errors:
            for error in overlay.errors[:40]:
                print(f"ERROR: overlay: {error}", file=sys.stderr)
            print("RESULT: FAILED (content overlay invalid)")
            return 1
        game = overlay.game
        index, model = wb.build_key_index(game=game)
        for key in overlay.added_keys:
            if key in index:
                index[key].overlay = True
        base_index, _ = wb.build_key_index(game=tk.load_json(tk.CANONICAL_GAME_JSON))
        glossary = load_glossary(args.glossary)
    except (OSError, ValueError, re.error, KeyError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    ctx = {"glossary": glossary, "index": index, "new": {}, "id_pattern": internal_ids(game),
           "speakers": speaker_prefixes(game), "base_chunk": {k: v.chunk for k, v in base_index.items()}}

    if args.self_test:
        self_test(index, glossary, report, overlay.retired_keys)
        n_overlay = check_overlay(overlay, index, {}, ctx, report, None)
        rules = sum(len(v) for v in glossary["_protected"].values())
        print(f"glossary: {len(glossary['names'])} names, {len(glossary['places'])} places, "
              f"{len(glossary['terms'])} terms, {rules} protected key rules, {len(glossary['verbatim'])} verbatim rules")
        print(f"content overlay: {n_overlay} overlay texts checked, {len(overlay.retired_keys)} retired keys")
        print_block("errors", report.errors, args.verbose)
        print_block("warnings", report.warnings, args.verbose)
        print("RESULT: " + ("FAILED" if report.errors else "OK"))
        return 1 if report.errors else 0

    if args.overlay_only:
        n_overlay = check_overlay(overlay, index, {}, ctx, report, args.chunk)
        print(f"content overlay ({dialogue.as_posix()}): {n_overlay} overlay texts checked"
              + (f" in chunk {args.chunk}" if args.chunk else ""))
        print_block("errors", report.errors, args.verbose)
        print_block("warnings", report.warnings, args.verbose)
        failed = bool(report.errors) or (args.strict and bool(report.warnings))
        print("RESULT: " + ("FAILED" if failed else "OK"))
        return 1 if failed else 0

    try:
        rows = read_rewrite(args.csv, report)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    new: dict[str, str] = {}
    notes: dict[str, str] = {}
    for line_no, key, text, note in rows:
        if key in new:
            report.error(key, f"duplicate key (line {line_no})")
            continue
        if key in overlay.retired_keys:
            report.warn(key, f"line {line_no}: removed by a content overlay (dropped line or removed exit); row ignored")
            continue
        if key not in index:
            report.error(key, f"unknown key (line {line_no}); keys come from docs/writing/context/<chunk>_keys.csv")
            continue
        if index[key].overlay:
            report.error(key, f"line {line_no}: this text comes from a content overlay; edit it in the overlay, not here")
            continue
        if args.chunk and index[key].chunk != args.chunk:
            report.error(key, f"belongs to chunk {index[key].chunk}, not {args.chunk}")
        if text == index[key].text:
            continue
        new[key] = text
        notes[key] = note

    ctx["new"] = new
    for key, text in new.items():
        check_row(key, text, notes[key], index[key], ctx, report)
    check_pairs(index, new, game, model, report)
    n_overlay = check_overlay(overlay, index, new, ctx, report, args.chunk)

    print(f"{args.csv.name}: {len(rows)} rows, {len(new)} changed texts")
    if args.chunk:
        total = sum(1 for v in index.values() if v.chunk == args.chunk and not v.never_shown)
        print(f"chunk {args.chunk}: {len(new)} of {total} keys rewritten")
    print(f"content overlay: {n_overlay} overlay texts checked")
    print_block("errors", report.errors, args.verbose)
    print_block("warnings", report.warnings, args.verbose)
    failed = bool(report.errors) or (args.strict and bool(report.warnings))
    if args.overrides_out and not failed:
        try:
            n_over, n_ui = write_overrides(args.overrides_out, {k: (v, notes[k]) for k, v in new.items()}, index)
        except (OSError, ValueError) as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 2
        print(f"wrote {args.overrides_out} ({n_over} override rows)" + (f" and {args.overrides_out}.ui.csv ({n_ui} ui rows)" if n_ui else ""))
    elif args.overrides_out:
        print("overrides not written: fix the errors first")
    print("RESULT: " + ("FAILED" if failed else "OK"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
