"""Approval data for the Standard/Hard guidance variants (design-doc/WRITING_METHOD.md "Guidance by difficulty").

Reads src/game/localization/overrides/guidance_std.csv, the base texts of the live tables and the context bundles
(docs/translation/context/C1-C4.md, for speakers and play order) and writes docs/writing/approval/changes_r3.json in
the format of the script-review page (one card per action / room, lines with old = Easy text, new = Standard/Hard text).

    python tools/guidance_approval.py
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOC = ROOT / "src/game/localization"
CTX = ROOT / "docs/translation/context"
OUT = ROOT / "docs/writing/approval/changes_r3.json"
ERA = {"C1": "2020", "C2": "1995", "C3": "1962 / 1982", "C4": "2035"}
KEY_LINE = re.compile(r"^\s*- `([^`]+)` \[([^\]]*)\]\s?(.*)$")
SPEAKER = re.compile(r"^\*\*([A-Z0-9_]+)\*\* \(([^)]*)\): (.*)$")


def live() -> dict[str, str]:
    out = {}
    for t in ("dialogue", "world", "ui"):
        with (LOC / f"{t}.csv").open(encoding="utf-8-sig", newline="") as h:
            for r in csv.DictReader(h):
                out[r["keys"]] = r["sk"]
    return out


def main() -> None:
    sk = live()
    with (LOC / "overrides/guidance_std.csv").open(encoding="utf-8", newline="") as h:
        variants = {r["keys"][:-4]: r for r in csv.DictReader(h)}
    cards: list[dict] = []
    seen: set[str] = set()
    for chunk in ("C1", "C2", "C3", "C4"):
        heading, where, block = "", "", []

        def flush() -> None:
            nonlocal block
            if any(l["state"] == "changed" for l in block):
                m = re.match(r"(\S+) · (.*)", heading)
                cid, title = (m.group(1), m.group(2)) if m else (heading, heading)
                cards.append({"id": f"R3-{cid}", "chunk": "R3", "era": ERA[chunk], "kind": "Menej návodné (Štandardná / Ťažká)",
                              "title": title.replace("main quest", "hlavná úloha").replace("side quest", "vedľajšia úloha"),
                              "where": where, "note": "Ľahká obťažnosť ponecháva pôvodný text.",
                              "lines": block, "counts": {"changed": sum(l["state"] == "changed" for l in block), "new": 0,
                                                         "same": sum(l["state"] == "same" for l in block)}})
            block = []

        for raw in (CTX / f"{chunk}.md").read_text(encoding="utf-8").splitlines():
            if raw.startswith("### "):
                flush()
                heading, where = raw[4:].strip(), ""
                continue
            if raw.startswith("- Where:"):
                where = raw[len("- Where:"):].strip()
                continue
            m = KEY_LINE.match(raw)
            if not m or m.group(1) in seen:
                continue
            key, kind, text = m.groups()
            seen.add(key)
            sm = SPEAKER.match(text)
            speaker = sm.group(2) if sm else ("Cieľ" if key.endswith(".objective") else "Denník" if key.endswith(".journal")
                                              else "Pohľad" if key.startswith("look.") else kind.split("(")[0].strip())
            if key.endswith(".journal") and key.replace(".journal", ".objective") in variants:
                continue  # the journal repeats the goal; one row is enough on the card
            if key in variants:
                block.append({"key": key, "speaker": speaker, "old": sk.get(key, ""), "new": variants[key]["sk"],
                              "state": "changed", "note": variants[key]["note"]})
            elif re.match(r"action\.[A-Z0-9]+\.(\d+|x\d+|k\d+|z\d+)$", key) and block is not None:
                block.append({"key": key, "speaker": speaker, "old": sk.get(key, ""), "new": sk.get(key, ""), "state": "same"})
        flush()
    missing = [k for k in variants if k not in seen]
    OUT.write_text(json.dumps(cards, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(cards)} cards, {sum(c['counts']['changed'] for c in cards)} changed lines; not placed: {missing}")


if __name__ == "__main__":
    main()
