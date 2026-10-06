"""Collect the spoken dialogue lines of the 2020 prologue (rooms S01-S10, actions G01-G11, the 2020 Grob side
quests Q1/Q2, the topics of the 2020 Grob characters, cutscene CS01) in play order.

Read-only: speakers and play order come from the effective game (game.json + content overlays, via
tools/content_ext.py); the CURRENT text of every line comes from src/game/localization/dialogue.csv.
Writes art/voice/trial/lines.json.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import content_ext  # noqa: E402

OUT = ROOT / "art" / "voice" / "trial" / "lines.json"
CSV = ROOT / "src" / "game" / "localization" / "dialogue.csv"
ROOMS = {f"S{n:02d}" for n in range(1, 11)}
CHARS = ["LENKA", "ROMAN", "ELA", "DANA", "MIRA20", "JOZEF"]
NON_VERBAL = {"BODKA"}          # the dog only barks -> SFX, no voice line
PROLOGUE_ACTIONS = {f"G{n:02d}" for n in range(1, 12)} | {"Q1A", "Q1B", "Q1C", "Q2A", "Q2B", "Q2C"}

# Play order of the scenes (walkthrough.json main route + the side quests where they first become available).
SCENES = [
    ("S01", "Adamova garáž", ["entry:S01", "act:G01"]),
    ("S02", "Ulica medzi plotmi", ["entry:S02", "topics:ROMAN", "act:Q1A", "topics:LENKA"]),
    ("S03", "Lúčny koník – výdajné miesto", ["entry:S03", "act:G02", "topics:ELA"]),
    ("S04", "Potraviny cez okienko", ["entry:S04", "act:G03", "topics:DANA"]),
    ("S05", "Babkina bránka", ["entry:S05", "act:G04"]),
    ("S06", "Pod zatvoreným oknom", ["entry:S06", "act:G05", "topics:MIRA20"]),
    ("S05b", "Babkina bránka – dielňa", ["act:G06"]),
    ("S07", "Čierna Voda pri výveske", ["entry:S07", "act:Q2A", "topics:JOZEF"]),
    ("S03b", "Výdajné miesto – oznam", ["act:Q2B"]),
    ("S07b", "Čierna Voda – oznam pripnutý", ["act:Q2C"]),
    ("S08", "Chodník pri retenčnej nádrži", ["entry:S08", "act:Q1B"]),
    ("S02b", "Ulica – Bodkova loptička", ["act:Q1C"]),
    ("S09", "Predsieň záhradnej dielne", ["entry:S09", "act:G07"]),
    ("S10", "Dielňa ZVON", ["entry:S10", "act:G08", "act:G09", "act:G10", "act:G11", "cs:CS01"]),
]


def topic_allowed(topic: dict) -> bool:
    """Only topics available in the prologue (no requirement, or only prologue actions)."""
    req = topic.get("requires_done") or []
    return all(r in PROLOGUE_ACTIONS for r in req)


def main() -> None:
    texts = {}
    with CSV.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            texts[row["keys"]] = row["sk"]
    eff = content_ext.load_effective_game().game
    rooms = {r["id"]: r for r in eff["rooms"]}
    actions = {a["id"]: a for a in eff["actions"]}
    chars = {c["id"]: c for c in eff["characters"]}
    cutscenes = {c["id"]: c for c in eff["cutscenes"]}

    def key_of(line: dict) -> str:
        return line.get("line_id") or line.get("key")

    out, skipped, excluded_topics = [], [], []
    for scene_id, scene_name, parts in SCENES:
        room = scene_id[:3]
        for part in parts:
            kind, ref = part.split(":")
            blocks: list[tuple[str, str, list[dict]]] = []
            if kind == "entry":
                blocks.append((f"entry.{ref}", "Prvý vstup", rooms[ref]["first_entry"]))
            elif kind == "act":
                a = actions[ref]
                blocks.append((f"action.{ref}", a.get("label", ref), a["lines"]))
            elif kind == "cs":
                cs = cutscenes[ref]
                blocks.append((f"cutscene.{ref}", "Animácia CS01", [l for b in cs["beats"] for l in b["lines"]]))
            elif kind == "topics":
                for t in chars[ref].get("ambient_topics", []):
                    if topic_allowed(t):
                        blocks.append((f"topic.{t['id']}", t.get("label", t["id"]), t["lines"]))
                    else:
                        excluded_topics.append({"topic": t["id"], "requires_done": t.get("requires_done")})
            for block_id, label, lines in blocks:
                for line in lines:
                    lid = key_of(line)
                    spk = line["speaker"]
                    text = texts.get(lid)
                    if text is None:
                        raise SystemExit(f"{lid} missing in dialogue.csv")
                    if spk in NON_VERBAL:
                        skipped.append({"line_id": lid, "speaker": spk, "text": text, "why": "non-verbal (dog) -> SFX"})
                        continue
                    phone = spk == "MIRA20" and room != "S06"
                    out.append({"line_id": lid, "speaker": spk, "text": text, "scene": scene_id,
                                "scene_name": scene_name, "block": block_id, "block_label": label,
                                "phone": phone})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"lines": out, "skipped": skipped, "excluded_topics": excluded_topics},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print(len(out), "lines,", sum(len(l["text"]) for l in out), "chars")
    print(Counter(l["speaker"] for l in out))
    print("skipped", skipped)
    print("excluded topics", excluded_topics)


if __name__ == "__main__":
    main()
