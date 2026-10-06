#!/usr/bin/env python3
"""Step 2 of the writing stack (design-doc/WRITING_METHOD.md): GPT language check of a chunk.

Takes a chunk's outputs (the overrides CSV and, optionally, overlay sequences from
content_ext/dialogue_ext.json) together with its context bundle docs/writing/context/<chunk>.md,
sends one batch per scene / conversation (a "###" block of the bundle) to
openai/gpt-6-astra-pro through fal.ai's OpenRouter proxy with a strict Slovak-editor prompt, and
writes docs/writing/review_gpt/<name>.json:

    {"chunk": "C1", "model": ..., "cost_usd": ..., "batches": {...},
     "keys": {"<key>": {"verdict": "ok" | "fix", "category": ..., "problem": ...,
                        "suggestion": ..., "text": <reviewed text>, "batch": <block id>}},
     "unreviewed": [<keys GPT returned no verdict for>]}

The tool never edits texts. Claude (step 3) decides every "fix" flag: accept / adapt / reject
with a reason, in docs/writing/review_gpt/<name>.decisions.csv (WRITING_METHOD.md section 4).

Batches: every bundle block that contains at least one key of the outputs (changed or new).
GPT judges those keys; the other lines of the block are shown as read-only context so the
conversation is read as a whole. --all-keys judges every key of every selected block.
An overlay sequence that lists existing keys (plain strings) between its new lines is shown in its
full play order, old and new lines interleaved, so GPT judges the flow as the player hears it.

Robustness: each call is retried (network errors, HTTP 429/5xx, malformed JSON, missing
verdicts) with backoff; the result file is rewritten after every batch, and a re-run skips
batches whose content is unchanged (use --force to redo them). Every paid call is logged in
art/spend-log.csv. --max-usd stops before the run's cost would pass the cap.

Usage (PYTHONIOENCODING=utf-8 python -X utf8 tools/gpt_review.py ...):
    tools/gpt_review.py --chunk C1                         # docs/writing/out/C1.csv
    tools/gpt_review.py --chunk C1 --overrides OUT.csv --overlay src/game/data/content_ext/dialogue_ext.json
    tools/gpt_review.py --chunk C1 --only G05 --only ELA   # just these blocks
    tools/gpt_review.py --chunk C1 --dry-run [--show-prompt]   # batches and cost estimate, no call
    tools/gpt_review.py --chunk C1 --limit 2 --name C1_test
    tools/gpt_review.py --chunk C1 --all-keys --skip-role 'hotspot name' --instruction tone.txt --name C1_tone
    tools/gpt_review.py --chunk C1 --decisions-template    # add every "fix" key to <name>.decisions.csv
    tools/gpt_review.py --chunk C1 --check-decisions       # exit 1 while a "fix" key has no decision

Step 3 (Claude's final control) fills docs/writing/review_gpt/<name>.decisions.csv with the header
key,gpt_category,decision,final_text,reason: decision is accept (take the suggestion), adapt (own
fix in final_text) or reject (keep the text; reason says why). final_text is what goes into the
overrides CSV / overlay. Every row needs a reason.

Exit codes: 0 ok, 1 some batches failed, 2 input error.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
WRITING = ROOT / "docs" / "writing"
CONTEXT = WRITING / "context"
OUT_DIR = WRITING / "review_gpt"
LOG = ROOT / "art" / "spend-log.csv"
URL = "https://fal.run/openrouter/router/openai/v1/chat/completions"
MODEL = "openai/gpt-6-astra-pro"
USER_AGENT = "LastBell-ArtPipeline/0.1 (+https://github.com/brunolau/game-lastbell)"
# USD per million tokens (input, output), openrouter.ai/api/v1/models on 2026-10-05.
PRICES = {"openai/gpt-6-astra-pro": (10.0, 50.0), "openai/gpt-6-astra": (10.0, 50.0),
          "openai/gpt-6.1-sol-pro": (2.0, 10.0), "openai/gpt-6.1-sol": (2.0, 10.0)}
# Dry-run estimate, calibrated on the first test run (2026-10-06, C1 G05 + ELA): about 10k prompt
# tokens and 110-175 output tokens per judged key, USD 0.13-0.14 per conversation.
EST_OUTPUT_TOKENS_PER_KEY = 180
CHARS_PER_TOKEN = 0.9             # prompt chars per billed prompt token as measured (proxy overhead included)

KEY_LINE = re.compile(r"^(?P<indent>\s*)- `(?P<key>[^`]+)` \[(?P<role>[^\]]*)\] "
                      r"(?:\*\*(?P<speaker>[A-Z0-9_]+)\*\* \((?P<name>[^)]*)\): )?(?P<text>.*)$")
ID_TOKEN = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")
TOPIC_HEAD = re.compile(r"^- Topic `(?P<topic>[^`]+)`")
TOPIC_KEY = re.compile(r"^topic\.(?P<topic>.+)\.(?:label|\d{3}|x\d{2})$")

SYSTEM_PROMPT = """You are a strict senior Slovak editor (native speaker from Bratislava, years of dubbing,
subtitles and game localisation). You review Slovak dialogue and texts of the hand-painted
point-and-click adventure "Posledný zvonec" before release. You do not write the game; you find
what is wrong and propose the smallest good fix.

THE TONE THE OWNER WANTS: humour in the spirit of the Czech "Polda" adventure games: playful,
a little absurd, character comedy, real situational jokes, running gags, lively characters with
quirks. But every line must make sense in its situation and must be natural spoken Slovak.
Conversations are deliberately longer than the original (greetings, small talk, reactions,
follow-up questions) so they feel natural. Important emotional moments stay plain and simple.

FLAG (verdict "fix") a line when it has any of these problems:
- nonsense: the sentence or image does not make sense, or does not follow from the line before,
  or the reply does not answer what was asked, or the label does not match the exchange;
- unnatural: no Slovak would say it like this in this situation (stiff, written, translated,
  officialese outside an official character);
- grammar: declension, agreement, word order, prepositions (v/vo, s/so, k/ku), aspect, commas,
  typography („…“, …, –);
- calque or anglicism where Slovak has its own word (e.g. "toaster", "dáva zmysel", "byť v pohode"
  in 1960, "stres" in 1960/1982, "okej" outside 2020);
- joke: the joke needs an explanation, is a non sequitur, is a meta joke (about games, puzzles,
  inventory, players), is mean, or is the old pattern of an ironic one-liner summary tacked onto
  the end of an exchange instead of a joke that comes from the situation or the character;
- tone/voice: the line does not sound like this character at this age and in this era (see
  VOICES), or the era register is wrong (modern words in 1960/1982 mouths);
- ty/vy: the address form between the two people is wrong or mixed (see the ty/vy table);
- length: a spoken line or look longer than about 110 characters (hard limit 160); a topic label
  longer than 28 characters.

DO NOT flag or change: the story, facts, names, items, numbers, codes, dates, who gives what, or
which line carries a clue. A suggestion keeps every fact and every name of the original line and
the same speaker. Do not flag a line only because you would phrase it differently; flag only real
problems. Do not add stage directions, speaker names or line breaks. Painted texts and codes in
CAPITALS stay exactly as they are.

ANSWER with one JSON object and nothing else:
{"items": [{"key": "<key>", "verdict": "ok" | "fix",
            "category": "" | "nonsense" | "unnatural" | "grammar" | "calque" | "joke" | "tone" | "tyvy" | "length",
            "problem": "<English, one or two sentences; empty when ok>",
            "suggestion": "<the complete corrected Slovak text; empty when ok>"}],
 "conversation_note": "<English, optional: a problem of the exchange as a whole, e.g. it is too short, a reply is missing, the joke rhythm>"}
Give exactly one item for every key listed under KEYS TO REVIEW, in that order."""


# --------------------------------------------------------------------------- inputs

@dataclass
class Line:
    key: str
    role: str
    speaker: str | None
    name: str | None
    text: str
    new: bool = False        # from the overlay (does not exist in the tables)
    changed: bool = False    # text differs from the bundle text


@dataclass
class Block:
    bid: str
    section: str
    heading: str
    body: list[str] = field(default_factory=list)   # raw bundle lines (context)
    lines: list[Line] = field(default_factory=list)
    overlay: list[tuple[str, list[Line]]] = field(default_factory=list)  # (sequence title, lines)
    # sequence title -> full play order (existing key str or new Line) when the overlay lists it
    orders: dict[str, list] = field(default_factory=dict)
    parts: list["Block"] = field(default_factory=list)   # --merge-small: the scenes of a merged batch
    focus: set[str] | None = None   # --trim-topics: only these topics of a conversation block are shown


def parse_bundle(path: Path) -> list[Block]:
    blocks: list[Block] = []
    section = ""
    current: Block | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("## "):
            section = raw[3:].strip()
            current = None
            continue
        if raw.startswith("### "):
            heading = raw[4:].strip()
            bid = re.split(r" · | — | ", heading, maxsplit=1)[0].strip()
            current = Block(bid=bid, section=section, heading=heading)
            blocks.append(current)
            continue
        if current is None:
            continue
        current.body.append(raw)
        m = KEY_LINE.match(raw)
        if m:
            current.lines.append(Line(m["key"], m["role"], m["speaker"], m["name"], m["text"]))
    return blocks


def read_overrides(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        text_col = "sk_new" if "sk_new" in cols else "sk" if "sk" in cols else None
        if "keys" not in cols or text_col is None:
            raise SystemExit(f"{path}: need columns 'keys' and 'sk_new' (chunk output) or 'sk' (sk_overrides.csv)")
        return {row["keys"]: row[text_col] for row in reader if row.get("keys")}


def _text_of(value) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for k in ("sk", "text"):
            if isinstance(value.get(k), str):
                return value[k]
    return None


def read_overlay(path: Path) -> list[dict]:
    """Collect sequences from an overlay file, tolerant of the exact schema.

    Any object with a "lines" list is a sequence. Its id is the first of id / topic / key /
    action; it attaches to a bundle block via action / after_action / extends / character /
    npc, or via a block id contained in its id. Each line needs a text (sk or text, or a dict
    {"sk": ...}); its key is key / line_id / id, else <sequence id>.<NNN>.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    seqs: list[dict] = []

    def walk(node, parent_key: str = "") -> None:
        if isinstance(node, dict):
            if isinstance(node.get("lines"), list):
                sid = next((str(node[k]) for k in ("id", "topic", "key", "action") if node.get(k)), parent_key)
                lines, order = [], []
                for n, ln in enumerate(node["lines"], 1):
                    if isinstance(ln, str):          # an existing key at this position of the play order
                        order.append(ln)
                        continue
                    if not isinstance(ln, dict):
                        continue
                    text = _text_of(ln.get("sk")) or _text_of(ln.get("text")) or ""
                    key = str(ln.get("key") or ln.get("line_id") or ln.get("id") or f"{sid}.{n:03d}")
                    lines.append(Line(key, "new spoken line", ln.get("speaker"), None, text, new=True))
                    order.append(lines[-1])
                label = _text_of(node.get("label"))
                if label is not None:
                    lines.insert(0, Line(str(node.get("label_key") or f"topic.{sid}.label"),
                                         "new topic label", None, None, label, new=True))
                anchors = [str(node[k]) for k in ("action", "after_action", "extends", "character", "npc", "owner")
                           if isinstance(node.get(k), str)]
                seqs.append({"id": sid, "anchors": anchors, "lines": lines, "order": order})
            for k, v in node.items():
                if k != "lines":
                    walk(v, k if isinstance(v, (dict, list)) else parent_key)
        elif isinstance(node, list):
            for v in node:
                walk(v, parent_key)

    walk(data)
    return seqs


# --------------------------------------------------------------------------- voices

def voices_index(path: Path) -> tuple[str, dict[str, str]]:
    """(ty/vy table section, {speaker id: voice entry text + humour table rows})."""
    text = path.read_text(encoding="utf-8")
    tyvy = ""
    m = re.search(r"^## Who says.*?(?=^---|^## )", text, re.S | re.M)
    if m:
        tyvy = m.group(0).strip()
    entries: dict[str, str] = {}
    for sec in re.split(r"(?=^### )", text, flags=re.M):
        if not sec.startswith("### "):
            continue
        heading = sec.splitlines()[0]
        if "→" in heading:
            continue
        body = re.split(r"^---|^## ", sec, flags=re.M)[0].strip()
        for sid in ID_TOKEN.findall(heading):
            entries.setdefault(sid, body)
    # rows of tables whose first cell starts with a speaker id (e.g. the humour table)
    for row in re.findall(r"^\|[^\n]+\|$", text, re.M):
        first = row.strip("|").split("|")[0]
        for sid in ID_TOKEN.findall(first):
            if sid in entries and row not in entries[sid]:
                entries[sid] += "\n" + row
    return tyvy, entries


# --------------------------------------------------------------------------- batches

def attach_overlay(blocks: list[Block], seqs: list[dict]) -> list[Block]:
    by_id = {b.bid: b for b in blocks}
    extra: list[Block] = []
    for seq in seqs:
        target = next((by_id[a] for a in seq["anchors"] if a in by_id), None)
        if target is None:
            parts = re.split(r"[.\s:/]", seq["id"])
            target = next((by_id[p] for p in parts if p in by_id), None)
        if target is None:
            target = Block(bid=f"overlay:{seq['id']}", section="Overlay sequences", heading=f"overlay {seq['id']}")
            extra.append(target)
        target.overlay.append((seq["id"], seq["lines"]))
        if any(isinstance(x, str) for x in seq.get("order", [])):
            target.orders[seq["id"]] = seq["order"]
    return blocks + extra


def select_batches(blocks: list[Block], overrides: dict[str, str], all_keys: bool,
                   only: list[str], skip_roles: list[str] | None = None,
                   trim_topics: bool = False, all_keys_in: list[str] | None = None) -> list[tuple[Block, list[Line]]]:
    skip = re.compile("|".join(f"(?:{r})" for r in skip_roles)) if skip_roles else None
    batches = []
    for b in blocks:
        if only and b.bid not in only:
            continue
        block_all = all_keys or b.bid in (all_keys_in or [])
        for ln in b.lines:
            if ln.key in overrides and overrides[ln.key] != ln.text:
                ln.text, ln.changed = overrides[ln.key], True
        # a bundle built from the effective game already lists the overlay's new lines: the overlay
        # (the draft under review) is their source, so each key is judged once, with the overlay text
        ov_new = {ln.key for _, seq in b.overlay for ln in seq}
        review = [ln for ln in b.lines if (ln.changed or (block_all and ln.text)) and ln.key not in ov_new]
        # an overlay line whose text equals the bundle's (the bundle already shows the applied overlay)
        # is unchanged: context only, unless --all-keys
        bundle_text = {ln.key: ln.text for ln in b.lines}
        review += [ln for _, seq in b.overlay for ln in seq
                   if ln.text and (block_all or bundle_text.get(ln.key) != ln.text)]
        if skip:   # --skip-role: shown as context, not judged
            review = [ln for ln in review if not skip.search(ln.role)]
        if review and trim_topics and not block_all and any(TOPIC_HEAD.match(r) for r in b.body):
            b.focus = {m["topic"] for ln in review if (m := TOPIC_KEY.match(ln.key))}
        if review:
            batches.append((b, review))
    return batches


def merge_small(batches: list[tuple[Block, list[Line]]], min_keys: int,
                any_section: bool = False) -> list[tuple[Block, list[Line]]]:
    """--merge-small: consecutive batches of the same bundle section with fewer than min_keys keys are
    sent together (each scene still under its own heading), until the merged batch has min_keys keys.
    Saves the fixed prompt cost (instructions, voices, ty/vy table) of many one-line batches."""
    out: list[tuple[Block, list[Line]]] = []
    group: list[tuple[Block, list[Line]]] = []

    def flush() -> None:
        if len(group) == 1:
            out.append(group[0])
        elif group:
            parts = [b for b, _ in group]
            m = Block(bid="+".join(b.bid for b in parts), section=parts[0].section,
                      heading=" | ".join(b.heading for b in parts))
            m.lines = [ln for b in parts for ln in b.lines]
            m.overlay = [s for b in parts for s in b.overlay]
            m.parts = parts
            out.append((m, [ln for _, r in group for ln in r]))
        group.clear()

    for b, review in batches:
        small = len(review) < min_keys
        if group and (not small or (b.section != group[0][0].section and not any_section)):
            flush()
        if small:
            group.append((b, review))
            if sum(len(r) for _, r in group) >= min_keys:
                flush()
        else:
            out.append((b, review))
    flush()
    return out


def render_block(b: Block) -> str:
    """The bundle block with the reviewed texts substituted and overlay lines appended."""
    if b.parts:   # a --merge-small batch: every scene under its own heading
        return "\n\n".join(f"### {p.heading}\n{render_block(p)}" for p in b.parts)
    by_key = {ln.key: ln for ln in b.lines}
    # keys shown in an overlay sequence below (new lines, and existing lines of an extended exchange)
    # are left out of the bundle body, so every line appears once, in play order
    in_overlay = {ln.key for _, seq in b.overlay for ln in seq}
    in_overlay |= {k for order in b.orders.values() for k in order if isinstance(k, str)}
    out = []
    topic = None
    for raw in b.body:
        t = TOPIC_HEAD.match(raw)
        if t:
            topic = t["topic"]
        if b.focus is not None and topic is not None and topic not in b.focus:
            continue
        m = KEY_LINE.match(raw)
        if m and m["key"] in in_overlay:
            continue
        if m and m["key"] in by_key:
            ln = by_key[m["key"]]
            tag = " (REWRITTEN)" if ln.changed else ""
            spk = f"**{m['speaker']}** ({m['name']}): " if m["speaker"] else ""
            out.append(f"{m['indent']}- `{ln.key}` [{ln.role}{tag}] {spk}{ln.text}")
        elif raw.strip():
            out.append(raw)
    if b.focus is not None:
        out.append("- (the character's other topics are left out of this check)")
    for sid, seq in b.overlay:
        if b.focus is not None and sid.removeprefix("topic.") not in b.focus:
            continue
        order = b.orders.get(sid)
        if order:
            # an extended existing exchange: show the whole exchange as it plays, old and new lines
            out.append(f"- EXTENDED exchange `{sid}`: the FULL play order after the rewrite "
                       f"(existing lines and the writer's NEW lines, in this order):")
            out += [f"  - `{ln.key}` [{ln.role}] {ln.text}" for ln in seq if ln.role == "new topic label"]
            for item in order:
                if isinstance(item, str):
                    old = by_key.get(item)
                    if old is None:
                        out.append(f"  - `{item}` [existing line of another block]")
                        continue
                    spk = f"**{old.speaker}**: " if old.speaker else ""
                    tag = " (REWRITTEN)" if old.changed else ""
                    out.append(f"  - `{item}` [existing line{tag}] {spk}{old.text}")
                else:
                    spk = f"**{item.speaker}**: " if item.speaker else ""
                    out.append(f"  - `{item.key}` [NEW line] {spk}{item.text}")
            continue
        out.append(f"- NEW sequence `{sid}` (added by the writer; plays as written, in this order):")
        for ln in seq:
            spk = f"**{ln.speaker}**: " if ln.speaker else ""
            out.append(f"  - `{ln.key}` [{ln.role}] {spk}{ln.text}")
    return "\n".join(out)


def build_prompt(chunk_title: str, b: Block, review: list[Line], tyvy: str, voices: dict[str, str],
                 instruction: str = "") -> str:
    speakers = []
    for ln in b.lines + [x for _, s in b.overlay for x in s]:
        if ln.speaker and ln.speaker not in speakers:
            speakers.append(ln.speaker)
    for sid in ID_TOKEN.findall(b.heading):   # conversation blocks: the NPC of the heading
        if sid in voices and sid not in speakers:
            speakers.append(sid)
    if "ADAM" not in speakers:
        speakers.insert(0, "ADAM")
    voice_text = "\n\n".join(voices[s] for s in speakers if s in voices)
    keys = "\n".join(f"- `{ln.key}`: {ln.text}" for ln in review)
    return (f"CHUNK: {chunk_title}\nSECTION: {b.section}\nSCENE / CONVERSATION: {b.heading}\n\n"
            f"CONTEXT (where it happens, who speaks, every text of this scene in play order; ids in brackets "
            f"are internal context and never appear in the Slovak text):\n\n{render_block(b)}\n\n"
            f"VOICES of the speakers:\n\n{voice_text}\n\n{tyvy}\n\n"
            + (f"ADDITIONAL INSTRUCTION FOR THIS REVIEW:\n{instruction.strip()}\n\n" if instruction else "")
            + f"KEYS TO REVIEW ({len(review)}):\n{keys}\n")


# --------------------------------------------------------------------------- API

def fal_key() -> str:
    key = os.environ.get("FAL_KEY")
    if not key and sys.platform == "win32":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                key, _ = winreg.QueryValueEx(k, "FAL_KEY")
        except OSError:
            key = None
    if not key:
        raise SystemExit("FAL_KEY not set (env or HKCU\\Environment)")
    return key


def cost_of(model: str, usage: dict) -> float:
    if isinstance(usage.get("cost"), (int, float)):
        return float(usage["cost"])
    pin, pout = PRICES.get(model, (10.0, 50.0))
    return usage.get("prompt_tokens", 0) / 1e6 * pin + usage.get("completion_tokens", 0) / 1e6 * pout


def log_spend(model: str, asset: str, usd: float) -> None:
    new = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "model", "asset", "usd"])
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), model, asset, f"{usd:.4f}"])


def parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise


def call(model: str, key: str, prompt: str, asset: str, expected: list[str], retries: int,
         timeout: int) -> tuple[dict, float]:
    """One batch; retries on transport errors, 429/5xx, bad JSON and missing verdicts."""
    use_format = True
    total = 0.0
    last_err = ""
    for attempt in range(1, retries + 1):
        body = {"model": model, "temperature": 0.2, "max_tokens": min(8000, 1500 + 250 * len(expected)),
                "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                             {"role": "user", "content": prompt}]}
        if use_format:
            body["response_format"] = {"type": "json_object"}
        try:
            r = requests.post(URL, json=body, timeout=timeout,
                              headers={"Authorization": f"Key {key}", "Content-Type": "application/json",
                                       "User-Agent": USER_AGENT})
        except requests.RequestException as e:
            last_err = f"network: {e}"
        else:
            if r.status_code == 400 and use_format and "response_format" in r.text:
                use_format = False
                last_err = "response_format rejected"
                continue
            if r.status_code in (408, 409, 425, 429) or r.status_code >= 500:
                last_err = f"HTTP {r.status_code}: {r.text[:200]}"
            elif r.status_code >= 400:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:500]}")
            else:
                data = r.json()
                usage = data.get("usage") or {}
                c = cost_of(model, usage)
                total += c
                log_spend(model, asset + (f"#retry{attempt - 1}" if attempt > 1 else ""), c)
                try:
                    content = data["choices"][0]["message"]["content"] or ""
                    result = parse_json(content)
                    got = {it.get("key") for it in result.get("items", []) if isinstance(it, dict)}
                    missing = [k for k in expected if k not in got]
                    if missing and attempt < retries:
                        last_err = f"missing verdicts for {len(missing)} keys"
                    else:
                        result["_usage"] = usage
                        return result, total
                except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
                    last_err = f"bad response: {e}"
        wait = min(60, 4 * 2 ** (attempt - 1))
        print(f"    attempt {attempt} failed ({last_err}); retry in {wait}s", flush=True)
        time.sleep(wait)
    raise RuntimeError(f"gave up after {retries} attempts: {last_err}")


# --------------------------------------------------------------------------- decisions (step 3)

DECISION_COLS = ["key", "gpt_category", "gpt_problem", "gpt_suggestion", "text", "decision", "final_text", "reason"]
DECISIONS = ("accept", "adapt", "reject")


def read_decisions(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {row["key"]: row for row in csv.DictReader(f) if row.get("key")}


def decisions_template(result: dict, path: Path) -> int:
    rows = read_decisions(path)
    added = 0
    for k, v in result.get("keys", {}).items():
        if v.get("verdict") == "fix" and k not in rows:
            rows[k] = {"key": k, "gpt_category": v.get("category", ""), "gpt_problem": v.get("problem", ""),
                       "gpt_suggestion": v.get("suggestion", ""), "text": v.get("text", ""),
                       "decision": "", "final_text": "", "reason": ""}
            added += 1
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=DECISION_COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows.values())
    return added


def check_decisions(result: dict, path: Path) -> list[str]:
    rows = read_decisions(path)
    problems = []
    for k, v in result.get("keys", {}).items():
        if v.get("verdict") != "fix":
            continue
        row = rows.get(k)
        if row is None:
            problems.append(f"{k}: no decision")
            continue
        d = (row.get("decision") or "").strip().lower()
        if d not in DECISIONS:
            problems.append(f"{k}: decision must be one of {', '.join(DECISIONS)}")
        if not (row.get("reason") or "").strip():
            problems.append(f"{k}: reason missing")
        if d in ("accept", "adapt") and not (row.get("final_text") or "").strip():
            problems.append(f"{k}: final_text missing")
        if d == "accept" and (row.get("final_text") or "").strip() != (v.get("suggestion") or "").strip():
            problems.append(f"{k}: accept means final_text = the GPT suggestion (use adapt otherwise)")
    for k in result.get("unreviewed", []):
        problems.append(f"{k}: GPT gave no verdict; re-run the batch or read it yourself")
    return problems


# --------------------------------------------------------------------------- main

def save(path: Path, report: dict) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chunk", required=True, help="bundle name: docs/writing/context/<chunk>.md")
    ap.add_argument("--overrides", type=Path, help="keys,sk_new,note (default docs/writing/out/<chunk>.csv) "
                    "or keys,game_json,sk,note (sk_overrides.csv)")
    ap.add_argument("--overlay", type=Path, action="append", default=[], help="overlay JSON with new sequences")
    ap.add_argument("--name", help="output name (default: the chunk) -> docs/writing/review_gpt/<name>.json")
    ap.add_argument("--only", action="append", default=[], help="block id, e.g. G05, ELA, S01 (repeatable)")
    ap.add_argument("--all-keys", action="store_true", help="judge every key of the selected blocks")
    ap.add_argument("--limit", type=int, help="at most N batches")
    ap.add_argument("--dry-run", action="store_true", help="list batches and estimated cost, no API call")
    ap.add_argument("--show-prompt", action="store_true", help="with --dry-run: print the prompt of each batch")
    ap.add_argument("--force", action="store_true", help="redo batches already in the result file")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--max-usd", type=float, default=5.0, help="stop before the run passes this cost")
    ap.add_argument("--decisions-template", action="store_true", help="no call: add the fix keys to <name>.decisions.csv")
    ap.add_argument("--check-decisions", action="store_true", help="no call: every fix key has a valid decision")
    ap.add_argument("--skip-role", action="append", default=[],
                    help="regex on the bundle role (e.g. 'hotspot name'): such keys stay as context but are "
                         "not judged, also under --all-keys (repeatable)")
    ap.add_argument("--instruction", type=Path, help="text file with an extra instruction appended to every "
                    "batch prompt (e.g. a tone pass)")
    ap.add_argument("--merge-small", type=int, metavar="N", help="send consecutive blocks of one section with "
                    "fewer than N keys together, until a batch has N keys (cheaper; scenes keep their headings)")
    ap.add_argument("--merge-any-section", action="store_true", help="with --merge-small: also merge across "
                    "bundle sections (actions, rooms, conversations)")
    ap.add_argument("--trim-topics", action="store_true", help="conversation blocks show only the topics that "
                    "contain a reviewed key (cheaper re-checks; not with --all-keys)")
    ap.add_argument("--all-keys-in", action="append", default=[], metavar="BLOCK",
                    help="judge every key of this block (like --all-keys, for one block; repeatable)")
    ap.add_argument("--retries", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    name = args.name or args.chunk
    if args.decisions_template or args.check_decisions:
        res_path = OUT_DIR / f"{name}.json"
        if not res_path.exists():
            print(f"no review result {res_path}", file=sys.stderr)
            return 2
        result = json.loads(res_path.read_text(encoding="utf-8"))
        dec_path = OUT_DIR / f"{name}.decisions.csv"
        if args.decisions_template:
            print(f"{dec_path.relative_to(ROOT)}: {decisions_template(result, dec_path)} rows added")
        if args.check_decisions:
            problems = check_decisions(result, dec_path)
            for p in problems:
                print("  " + p)
            flagged = sum(1 for v in result.get("keys", {}).values() if v.get("verdict") == "fix")
            print(f"{flagged} flagged keys, {len(problems)} problems")
            return 1 if problems else 0
        return 0

    bundle = CONTEXT / f"{args.chunk}.md"
    if not bundle.exists():
        print(f"no bundle {bundle} (run tools/writing_bundles.py)", file=sys.stderr)
        return 2
    ov_path = (args.overrides or WRITING / "out" / f"{args.chunk}.csv").resolve()
    overrides = read_overrides(ov_path) if ov_path.exists() else {}
    if args.overrides and not ov_path.exists():
        print(f"no overrides file {ov_path}", file=sys.stderr)
        return 2
    blocks = parse_bundle(bundle)
    seqs = [s for p in args.overlay for s in read_overlay(p)]
    blocks = attach_overlay(blocks, seqs)
    batches = select_batches(blocks, overrides, args.all_keys, args.only, args.skip_role,
                             args.trim_topics, args.all_keys_in)
    instruction = args.instruction.read_text(encoding="utf-8") if args.instruction else ""
    if args.merge_small:
        batches = merge_small(batches, args.merge_small, args.merge_any_section)
    if args.limit is not None:
        batches = batches[:args.limit]
    chunk_title = bundle.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
    tyvy, voices = voices_index(WRITING / "VOICES.md")
    pin, pout = PRICES.get(args.model, (10.0, 50.0))
    sys_tokens = len(SYSTEM_PROMPT) / CHARS_PER_TOKEN

    prompts = []
    est_total = 0.0
    for b, review in batches:
        prompt = build_prompt(chunk_title, b, review, tyvy, voices, instruction)
        est = (sys_tokens + len(prompt) / CHARS_PER_TOKEN) / 1e6 * pin + \
            len(review) * EST_OUTPUT_TOKENS_PER_KEY / 1e6 * pout
        est_total += est
        prompts.append((b, review, prompt, est))
    print(f"{args.chunk}: {len(batches)} batches, {sum(len(r) for _, r in batches)} keys to review, "
          f"{len(seqs)} overlay sequences; estimated USD {est_total:.2f} with {args.model}")

    if args.dry_run:
        for b, review, prompt, est in prompts:
            print(f"  {b.bid:<14} {len(review):>3} keys  ~{len(prompt) / CHARS_PER_TOKEN:,.0f} tokens in  "
                  f"~USD {est:.3f}  {b.heading[:60]}")
            if args.show_prompt:
                print("-" * 100 + "\n" + prompt + "-" * 100)
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{args.name or args.chunk}.json"
    report = {"chunk": args.chunk, "model": args.model, "overrides": str(ov_path.relative_to(ROOT)) if ov_path.exists() else None,
              "overlay": [str(p) for p in args.overlay], "cost_usd": 0.0, "batches": {}, "keys": {}, "unreviewed": []}
    if out_path.exists():
        try:
            old = json.loads(out_path.read_text(encoding="utf-8"))
            if old.get("chunk") == args.chunk:
                report.update({k: old[k] for k in ("cost_usd", "batches", "keys", "unreviewed") if k in old})
        except json.JSONDecodeError:
            pass
    key = fal_key()
    run_cost, failed = 0.0, 0
    for b, review, prompt, est in prompts:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
        prev = report["batches"].get(b.bid)
        if prev and prev.get("hash") == digest and prev.get("status") == "ok" and not args.force:
            print(f"  {b.bid}: unchanged, skipped")
            continue
        if run_cost + est > args.max_usd:
            print(f"  {b.bid}: stop, the run would pass --max-usd {args.max_usd}")
            break
        print(f"  {b.bid}: {len(review)} keys ...", flush=True)
        expected = [ln.key for ln in review]
        try:
            result, cost = call(args.model, key, prompt, f"writing/gpt_review/{args.name or args.chunk}/{b.bid}",
                                expected, args.retries, args.timeout)
        except RuntimeError as e:
            failed += 1
            report["batches"][b.bid] = {"hash": digest, "status": "failed", "error": str(e)}
            save(out_path, report)
            print(f"    FAILED: {e}")
            continue
        run_cost += cost
        report["cost_usd"] = round(report.get("cost_usd", 0.0) + cost, 4)
        texts = {ln.key: ln.text for ln in review}
        items = {it["key"]: it for it in result.get("items", []) if isinstance(it, dict) and it.get("key") in texts}
        for k in expected:
            it = items.get(k)
            if it is None:
                if k not in report["unreviewed"]:
                    report["unreviewed"].append(k)
                continue
            if k in report["unreviewed"]:
                report["unreviewed"].remove(k)
            verdict = "fix" if str(it.get("verdict", "")).lower() == "fix" else "ok"
            report["keys"][k] = {"verdict": verdict, "category": it.get("category", "") if verdict == "fix" else "",
                                 "problem": it.get("problem", "") if verdict == "fix" else "",
                                 "suggestion": it.get("suggestion", "") if verdict == "fix" else "",
                                 "text": texts[k], "batch": b.bid}
        report["batches"][b.bid] = {"hash": digest, "status": "ok", "heading": b.heading, "keys": expected,
                                    "fix": sum(1 for k in expected if report["keys"].get(k, {}).get("verdict") == "fix"),
                                    "conversation_note": result.get("conversation_note", ""),
                                    "usage": result.get("_usage", {}), "usd": round(cost, 4)}
        save(out_path, report)
        print(f"    {report['batches'][b.bid]['fix']} fix / {len(expected)}  USD {cost:.4f}")
    flags = sum(1 for v in report["keys"].values() if v["verdict"] == "fix")
    print(f"wrote {out_path.relative_to(ROOT)}: {len(report['keys'])} keys, {flags} flagged, "
          f"{len(report['unreviewed'])} unreviewed; this run USD {run_cost:.4f}, file total USD {report['cost_usd']:.4f}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
