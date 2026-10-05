#!/usr/bin/env python3
"""Milestone-2 content coverage table from the QA harness reports.

Reads the coverage JSON files written by the Godot QA harness
(`-- --play-all --coverage build/screens/m2/coverage_<run>.json`, see src/game/README.md) and
prints Markdown tables: every action id (main and side) and every quest id with the runs in
which it was committed through the real input path, plus puzzles, cutscenes, variant layers,
causal effects, epilogue and postgame.

Usage:
    python tools/m2_coverage.py build/screens/m2/coverage_A.json build/screens/m2/coverage_B.json ...
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(paths: list[str]) -> int:
    game = json.loads((ROOT / "src/game/data/game.json").read_text(encoding="utf-8"))
    runs = []
    for p in paths:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        name = Path(p).stem.replace("coverage_", "")
        runs.append((name, data))
    if not runs:
        print("no coverage files given", file=sys.stderr)
        return 1
    quest_of = {}
    for q in game["quests"]:
        for a in q["actions"]:
            quest_of[a] = q["id"]
    out = []
    w = out.append
    w("| run | label | actions committed (real input) | blockers | failures | lines shown | rooms | epilogue shots (ending, album) |")
    w("|---|---|---:|---:|---:|---:|---:|---|")
    for name, d in runs:
        w(f"| {name} | {d.get('label', '')} | {len(d['acts'])} | {len(d['blockers'])} | {len(d['failures'])} | "
          f"{d['lines_shown']} | {d['rooms_seen']} | {', '.join(str(x) for x in d['ending_shot_counts'])} |")
    w("")
    w("### Actions")
    w("")
    w("| action | quest | room | kind | puzzle / cutscene | " + " | ".join(n for n, _ in runs) + " |")
    w("|---|---|---|---|---|" + "---|" * len(runs))
    total = {"main": 0, "side": 0}
    verified = {"main": 0, "side": 0}
    for a in game["actions"]:
        q = quest_of.get(a["id"], "")
        side = q.startswith("Q")
        total["side" if side else "main"] += 1
        cells = []
        hit_all = True
        for _, d in runs:
            entry = next((x for x in d["acts"] if x["action"] == a["id"]), None)
            if entry is None:
                cells.append("no")
                hit_all = False
            else:
                sl = entry.get("save_load")
                cells.append(f"yes #{entry['order']}" + (" s/l" if sl else ""))
        if hit_all:
            verified["side" if side else "main"] += 1
        extra = " ".join(x for x in (a.get("puzzle") or "", a.get("cutscene") or "") if x)
        w(f"| {a['id']} | {q} | {a['room']} | {a['kind']}{' (' + a['selected_item'] + ')' if a.get('selected_item') else ''} | {extra} | " + " | ".join(cells) + " |")
    w("")
    w(f"Main actions verified in every run: {verified['main']}/{total['main']}; side actions: {verified['side']}/{total['side']}.")
    w("")
    w("### Quests")
    w("")
    w("| quest | type | completion | " + " | ".join(n for n, _ in runs) + " |")
    w("|---|---|---|" + "---|" * len(runs))
    for q in game["quests"]:
        cells = []
        for _, d in runs:
            r = d["quests"][q["id"]]
            cells.append(("yes" if r["completed"] else "no") + f" ({r['actions_done']}/{r['actions_total']})")
        w(f"| {q['id']} | {q['type']} | {q['completion']} | " + " | ".join(cells) + " |")
    w("")
    w("### Puzzles, cutscenes, world changes")
    w("")
    for name, d in runs:
        cs = ", ".join(f"{k} {v['beats_shown']}/{v['beats_total']}" for k, v in d["cutscenes"].items())
        w(f"- **{name}**: puzzles {', '.join(d['puzzles_solved'])}; cutscenes (beats shown) {cs}; eras {d['eras_unlocked']}; "
          f"butterflies {d['butterflies']}; cache stage {d['cache_stage']}, invariant {d['cache_invariant']}; "
          f"variant layers {len(d['variant_layers_seen'])}/{len(game['visual_variant_layers'])}; "
          f"causal effect sightings {len(d['causal_effects_seen'])} (effect@room).")
    w("")
    return_ok = runs[0][1]
    for name, d in runs:
        if d.get("postgame"):
            w(f"- **{name} postgame**: `{json.dumps(d['postgame'], ensure_ascii=False)}`")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
