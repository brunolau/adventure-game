"""English translation workbench (docs/translation/README.md).

The translator (Claude) works through the context bundles of tools/writing_bundles.py (docs/translation/context/
C1-C4.md, story order, speakers and situations) in batches. Translations are stored per batch as JSON
(docs/translation/en/<chunk>_<NNN>.json, {key: english}); `merge` writes the persistent source
src/game/localization/overrides/en.csv (keys,en), which tools/extract_strings.py puts into the en column.

    python tools/en_batches.py prefill            fixed renderings from docs/translation/glossary_en.json
                                                  (rooms, items, quests, topic labels, hotspots, UI, speakers,
                                                  cutscene titles, verbatim lines) -> en/00_glossary.json
    python tools/en_batches.py autofill           room names on exit labels; identical Slovak -> same English
    python tools/en_batches.py dump C1 [--count 220]  next untranslated keys of a chunk with their context
    python tools/en_batches.py status             translated / total per chunk
    python tools/en_batches.py check              placeholders, markup, glossary names, empty strings
    python tools/en_batches.py merge              write overrides/en.csv (only keys whose Slovak still matches)
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CTX = ROOT / "docs/translation/context"
OUT = ROOT / "docs/translation/en"
LOC = ROOT / "src/game/localization"
GLOSSARY = ROOT / "docs/translation/glossary_en.json"
EN_CSV = LOC / "overrides/en.csv"
CHUNKS = ("C1", "C2", "C3", "C4")
KEY_LINE = re.compile(r"^\s*- `([^`]+)` \[([^\]]*)\]\s?(.*)$")
PLACEHOLDER = re.compile(r"\{[^{}]*\}|\[/?[a-z]+[^\]]*\]|%[sd]|\\n")


def live_sk() -> dict[str, str]:
    out: dict[str, str] = {}
    for t in ("dialogue", "world", "ui"):
        with (LOC / f"{t}.csv").open(encoding="utf-8-sig", newline="") as h:
            for r in csv.DictReader(h):
                out[r["keys"]] = r["sk"]
    return out


def done() -> dict[str, str]:
    """All translations so far: {key: en}, later batch files win."""
    res: dict[str, str] = {}
    for p in sorted(OUT.glob("*.json")):
        if p.name.startswith("_meta"):
            continue
        res.update(json.loads(p.read_text(encoding="utf-8")))
    return res


def chunk_items(chunk: str) -> list[tuple[str, str, str, str]]:
    """(kind 'key' or 'ctx', key, kind_label, text) in bundle order."""
    items, seen = [], set()
    for line in (CTX / f"{chunk}.md").read_text(encoding="utf-8").splitlines():
        m = KEY_LINE.match(line)
        if m:
            key = m.group(1)
            if key not in seen:
                seen.add(key)
                items.append(("key", key, m.group(2), m.group(3)))
        elif line.startswith(("## ", "### ", "- Where:", "- How:", "#### ")):
            items.append(("ctx", "", "", line))
    return items


def short_kind(k: str) -> str:
    k = k.lower()
    for word, s in (("spoken", "line"), ("objective", "goal"), ("journal", "journal"), ("dialogue choice", "choice"),
                    ("look", "look"), ("hint", "hint"), ("name", "name"), ("label", "label"), ("topic", "topic"),
                    ("ui", "ui"), ("caption", "caption"), ("option", "option"), ("clue", "clue"), ("goal", "goal")):
        if word in k:
            return s
    return k[:20]


def cmd_prefill(_a) -> None:
    g = json.loads(GLOSSARY.read_text(encoding="utf-8"))
    sk = live_sk()
    res, stale = {}, []
    for sect in ("rooms", "items", "quests", "topic_labels", "hotspots", "speaker_labels"):
        for _id, v in g[sect].items():
            k = v.get("key")
            if k and k in sk:
                (res.__setitem__(k, v["en"]) if v.get("sk") == sk[k] else stale.append(k))
    for sect in ("ui", "cutscene_titles", "verbatim"):
        for k, v in g[sect].items():
            en = v.get("en", "")
            if k in sk and en and not re.search(r"\b(must|quote|exactly)\b", en):
                (res.__setitem__(k, en) if v.get("sk") == sk[k] else stale.append(k))
    if "game.title" in sk:
        res["game.title"] = dict(g["title"])["en"] if isinstance(g["title"], list) else g["title"]["en"]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "00_glossary.json").write_text(json.dumps(res, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"prefilled {len(res)} keys; {len(stale)} glossary entries skipped (Slovak changed since): {stale[:12]}")


def cmd_autofill(_a) -> None:
    """Exit/connection labels that are room names get the glossary room name; a key whose Slovak text is
    identical to an already translated key gets the same English (locked-exit lines, repeated short lines)."""
    g = json.loads(GLOSSARY.read_text(encoding="utf-8"))
    sk, have = live_sk(), done()
    rooms = {v["sk"]: v["en"] for v in g["rooms"].values()}
    by_sk: dict[str, str] = {}
    for k, en in have.items():
        if k in sk:
            by_sk.setdefault(sk[k], en)
    res = {}
    for k, s in sk.items():
        if k in have:
            continue
        if re.fullmatch(r"(exit|conn)\..+\.label", k) and s in rooms:
            res[k] = rooms[s]
        elif s in by_sk and len(s) > 3:
            res[k] = by_sk[s]
    old = json.loads((OUT / "01_autofill.json").read_text(encoding="utf-8")) if (OUT / "01_autofill.json").exists() else {}
    old.update(res)
    (OUT / "01_autofill.json").write_text(json.dumps(old, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"autofilled {len(res)} keys")


def cmd_dump(a) -> None:
    have = done()
    items = chunk_items(a.chunk)
    out, n, pending_ctx = [], 0, []
    for kind, key, label, text in items:
        if kind == "ctx":
            pending_ctx.append(text)
            continue
        if key in have:
            pending_ctx = [c for c in pending_ctx if c.startswith(("## ", "### "))][-2:]
            continue
        if n >= a.count:
            break
        out.extend(pending_ctx)
        pending_ctx = []
        out.append(f"{key} |{short_kind(label)}| {text}")
        n += 1
    left = sum(1 for k, key, *_ in items if k == "key" and key not in have) - n
    print("\n".join(out))
    print(f"\n[{n} keys in this batch; {left} more untranslated in {a.chunk}]")


def cmd_status(_a) -> None:
    have = done()
    sk = live_sk()
    total = 0
    for c in CHUNKS:
        keys = [key for k, key, *_ in chunk_items(c) if k == "key"]
        total += len(keys)
        print(c, sum(1 for k in keys if k in have), "/", len(keys))
    print("all", sum(1 for k in sk if k in have), "/", len(sk))


def cmd_check(_a) -> int:
    have, sk = done(), live_sk()
    errs = []
    for k, en in have.items():
        if k not in sk:
            errs.append(f"{k}: key not in the tables")
            continue
        if not en.strip():
            errs.append(f"{k}: empty")
        if sorted(PLACEHOLDER.findall(sk[k])) != sorted(PLACEHOLDER.findall(en)):
            errs.append(f"{k}: placeholders/markup differ: {PLACEHOLDER.findall(sk[k])} vs {PLACEHOLDER.findall(en)}")
        if re.search(r"[áäčďéíĺľňóôŕšťúýž]", en.lower()) and not k.startswith(("char.", "room.", "hotspot.")):
            words = re.findall(r"\b\w*[áäčďéíĺľňóôŕšťúýžÁČĎÉÍĽŇÓŠŤÚÝŽ]\w*\b", en)
            allow = set(json.loads(GLOSSARY.read_text(encoding="utf-8")).get("spellcheck_allow", [])) | {"café", "cafés", "naïve", "déjà", "façade"}
            odd = [w for w in words if w not in allow and not w[0].isupper()]
            if odd:
                errs.append(f"{k}: lowercase Slovak-looking words {odd}")
    for e in errs[:80]:
        print(e)
    print(f"RESULT: {'OK' if not errs else 'ERRORS'} ({len(errs)} issues, {len(have)} keys)")
    return 1 if errs else 0


def cmd_merge(_a) -> None:
    have, sk = done(), live_sk()
    rows = [(k, have[k]) for k in sk if k in have and have[k].strip()]
    EN_CSV.parent.mkdir(parents=True, exist_ok=True)
    with EN_CSV.open("w", encoding="utf-8", newline="") as h:
        w = csv.writer(h, lineterminator="\n")
        w.writerow(["keys", "en"])
        w.writerows(rows)
    print(f"wrote {EN_CSV.relative_to(ROOT)}: {len(rows)} of {len(sk)} keys")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prefill")
    sub.add_parser("autofill")
    d = sub.add_parser("dump")
    d.add_argument("chunk", choices=CHUNKS)
    d.add_argument("--count", type=int, default=220)
    sub.add_parser("status")
    sub.add_parser("check")
    sub.add_parser("merge")
    a = ap.parse_args()
    return {"prefill": cmd_prefill, "autofill": cmd_autofill, "dump": cmd_dump, "status": cmd_status, "check": cmd_check,
            "merge": cmd_merge}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
