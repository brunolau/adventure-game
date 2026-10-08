"""Lines that give away the next steps (owner 2026-10-08: "the game is hinting way too much in the texts and dialogues").

For every action in play order (walkthrough main route + side quests in quest order) it lists the texts the player sees at
that step (spoken lines, objective/journal) that name the target, room or required item of one of the next two steps of
the same quest. Output: docs/writing/guidance/spoilers.md (worksheet for the Standard/Hard variants in
src/game/localization/overrides/guidance_std.csv).
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOC = ROOT / "src/game/localization"


def table() -> dict[str, str]:
    out = {}
    for t in ("dialogue", "world", "ui"):
        with (LOC / f"{t}.csv").open(encoding="utf-8-sig", newline="") as h:
            for r in csv.DictReader(h):
                out[r["keys"]] = r["sk"]
    return out


def stems(text: str) -> set[str]:
    return {w.lower()[:5] for w in re.findall(r"[A-Za-zÁ-ž]{5,}", text)}


def main() -> None:
    sk = table()
    g = json.loads((ROOT / "src/game/data/game.json").read_text(encoding="utf-8"))
    acts = {a["id"]: a for a in g["actions"]}
    ext = json.loads((ROOT / "src/game/data/content_ext/world_ext.json").read_text(encoding="utf-8"))
    for a in ext.get("actions", ext.get("add_actions", [])) if isinstance(ext, dict) else []:
        if isinstance(a, dict) and "id" in a:
            acts.setdefault(a["id"], a)
    chars = {c["id"]: c for c in g["characters"]}
    rooms = {r["id"]: r for r in g["rooms"]}
    hot = {h["id"]: h for r in g["rooms"] for h in r.get("hotspots", [])}

    def target_words(a: dict) -> set[str]:
        words = set()
        t = a.get("target", "")
        for key in (f"char.{t}.name", f"hotspot.{a.get('room')}.{t}.name", f"hotspot.{t}.name"):
            if key in sk:
                words |= stems(sk[key])
        if t in hot:
            words |= stems(sk.get(f"hotspot.{t}.name", hot[t].get("name", "")))
        r = a.get("room")
        if f"room.{r}.name" in sk:
            words |= stems(sk[f"room.{r}.name"])
        for it in a.get("requires_items", []):
            words |= stems(sk.get(f"item.{it}.name", ""))
        return words - {"adamo", "servi", "brašn", "prenos", "chron", "zvonu", "dieln"}

    order: dict[str, list[str]] = {}
    for a in acts.values():
        order.setdefault(a.get("quest_id") or a.get("quest", "main"), []).append(a["id"])
    route = json.loads((ROOT / "design-doc/walkthrough.json").read_text(encoding="utf-8"))
    main_ids = [s if isinstance(s, str) else s.get("id") for s in route["main_route"]]
    ids = [i for i in main_ids if i in acts] + sorted(i for i in acts if i not in main_ids)
    out = ["# Lines that give away the next steps", "",
           "Per step: texts shown at that step that name a target/room/item of the next two steps. Worksheet for guidance_std.csv.", ""]
    n = 0
    for pos, aid in enumerate(ids):
        a = acts[aid]
        nxt = ids[pos + 1: pos + 3]
        words = set().union(*(target_words(acts[x]) for x in nxt)) if nxt else set()
        keys = [k for k in sk if re.fullmatch(rf"action\.{re.escape(aid)}\.(\d+|x\d+|k\d+|z\d+|objective|journal)", k)]
        hits = []
        for k in keys:
            hit = sorted(stems(sk[k]) & words)
            if hit:
                hits.append(f"- `{k}` ({', '.join(hit)}): {sk[k]}")
        if hits:
            n += len(hits)
            out.append(f"### {aid} → next: {', '.join(nxt)}")
            out += hits + [""]
    p = ROOT / "docs/writing/guidance/spoilers.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out), encoding="utf-8")
    print(f"{n} flagged texts -> {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
