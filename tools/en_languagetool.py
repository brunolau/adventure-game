"""Local LanguageTool en-GB check of the English texts (owner 2026-10-08: "recheck yourself using some of your language
plugins [don't include fal here]").

LanguageTool runs locally (Java + language_tool_python, which downloads the LanguageTool server once); nothing is sent
to any online service. Names and terms from docs/translation/glossary_en.json (spellcheck_allow, people, places, rooms)
are ignored by the spelling rule. Output: docs/translation/en/languagetool.json (all matches) and a short summary.

    python tools/en_languagetool.py            check every English text
    python tools/en_languagetool.py --keys a b only these keys
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import en_batches as E  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/translation/en/languagetool.json"
# Style rules that do not apply to game text (short labels, curly typography, deliberate fragments).
DISABLED = {"EN_QUOTES", "WHITESPACE_RULE", "UPPERCASE_SENTENCE_START", "DASH_RULE", "PUNCTUATION_PARAGRAPH_END",
            "SENTENCE_FRAGMENT", "EN_UNPAIRED_QUOTES", "EN_UNPAIRED_BRACKETS", "ELLIPSIS", "ENGLISH_WORD_REPEAT_BEGINNING_RULE",
            "COMMA_COMPOUND_SENTENCE", "COMMA_COMPOUND_SENTENCE_2", "PLUS_MINUS", "MULTIPLICATION_SIGN",
            "THREE_NN", "CONSECUTIVE_SPACES", "EN_SPECIFIC_CASE"}


def allow_words() -> set[str]:
    g = json.loads(E.GLOSSARY.read_text(encoding="utf-8"))
    words = set(g.get("spellcheck_allow", []))
    for sect in ("rooms", "items", "speaker_labels", "hotspots"):
        for v in g.get(sect, {}).values():
            for field in ("sk", "en"):
                words |= set(re.findall(r"[\wÀ-ž’']+", v.get(field, "")))
    for p in g.get("people", []) + g.get("places", []):
        for v in p.values() if isinstance(p, dict) else []:
            if isinstance(v, str):
                words |= set(re.findall(r"[\wÀ-ž’']+", v))
    return words


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", nargs="*")
    a = ap.parse_args()
    import language_tool_python
    tool = language_tool_python.LanguageTool("en-GB")
    tool.disabled_rules = DISABLED
    have = E.done()
    keys = a.keys or list(have)
    allow = allow_words()
    results = {}
    for i, k in enumerate(keys):
        text = re.sub(r"\{[^}]*\}", "X", have[k])
        found = []
        for m in tool.check(text):
            if m.rule_id in DISABLED:
                continue
            word = text[m.offset:m.offset + m.error_length]
            if m.rule_issue_type == "misspelling" and (word in allow or word.strip("’'") in allow or word[:1].isupper()):
                continue
            found.append({"rule": m.rule_id, "message": m.message, "word": word,
                          "replacements": m.replacements[:3], "context": m.context})
        if found:
            results[k] = {"text": have[k], "matches": found}
        if i % 500 == 0:
            print(f"{i}/{len(keys)} checked, {len(results)} with matches", flush=True)
    tool.close()
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    rules = Counter(m["rule"] for r in results.values() for m in r["matches"])
    print(f"{len(results)} texts with matches -> {OUT.relative_to(ROOT)}")
    for rule, n in rules.most_common(25):
        print(f"  {rule}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
