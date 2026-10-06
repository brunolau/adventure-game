"""Collect the pending text changes (docs/writing/out_v2) into one approval data file for the owner.

Usage: python tools/approval_pack.py
Output: docs/writing/approval/changes.json — a list of scenes; each scene lists its lines in play order with the
current game text ("old") and the proposed text ("new"). The owner's decisions are stored by the approval page.
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_V2 = ROOT / "docs" / "writing" / "out_v2"
LOC = ROOT / "src" / "game" / "localization"
OUT = ROOT / "docs" / "writing" / "approval" / "changes.json"

CHUNK_ERA = {"C2": "1995", "C3": "1962 a 1982", "C4": "2035, scény a UI"}


def load_tables():
    text = {}
    for name in ("dialogue", "world", "ui"):
        for row in csv.DictReader(open(LOC / f"{name}.csv", encoding="utf-8")):
            text[row["keys"]] = row["sk"]
    return text


def scene_id(*parts):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", "-".join(parts)).strip("_")[:120]


def main():
    tables = load_tables()
    game = json.loads((ROOT / "design-doc" / "game.json").read_text(encoding="utf-8"))
    world_ext = json.loads((OUT_V2 / "pending" / "world_ext.json").read_text(encoding="utf-8"))
    rooms = {r["id"]: r for r in game["rooms"]} | {r["id"]: r for r in world_ext.get("rooms", [])}
    actions = {a["id"]: a for a in game["actions"]} | {a["id"]: a for a in world_ext.get("actions", [])}
    names = {c["id"]: tables.get(f"char.{c['id']}.name", c.get("name", c["id"])) for c in game["characters"]}
    names |= {c["id"]: c.get("name", c["id"]) for c in world_ext.get("characters", [])}
    names |= {k: tables.get(f"char.{k}.name", k) for k in game.get("non_actor_speakers", {})}
    speaker_of = {}
    for a in game["actions"]:
        for line in a["lines"]:
            speaker_of[line["line_id"]] = line["speaker"]
    for c in game["characters"]:
        for t in c.get("ambient_topics", []):
            for line in t["lines"]:
                speaker_of[line["line_id"]] = line["speaker"]
    for r in game["rooms"]:
        for line in r.get("first_entry", []):
            speaker_of[line["line_id"]] = line["speaker"]

    def room_label(rid):
        return tables.get(f"room.{rid}.name", rooms.get(rid, {}).get("name", rid))

    scenes, covered = [], set()
    for chunk in ("C2", "C3", "C4"):
        rewrites = {r["keys"]: r for r in csv.DictReader(open(OUT_V2 / f"{chunk}.csv", encoding="utf-8"))}
        ext = json.loads((OUT_V2 / f"{chunk}_ext.json").read_text(encoding="utf-8"))
        de = ext.get("dialogue_ext", {})

        def line_row(item):
            if isinstance(item, str):
                covered.add(item)
                old = tables.get(item, "")
                new = rewrites[item]["sk_new"] if item in rewrites else old
                return {"key": item, "speaker": names.get(speaker_of.get(item, ""), speaker_of.get(item, "")),
                        "old": old, "new": new, "state": "changed" if new != old else "same"}
            return {"key": item["key"], "speaker": names.get(item["speaker"], item["speaker"]),
                    "old": "", "new": item["sk"], "state": "new"}

        for seq in de.get("sequences", []):
            aid = seq.get("action")
            if aid:
                a = actions.get(aid, {})
                title = tables.get(f"action.{aid}.label", a.get("label", aid))
                where = room_label(a.get("room", ""))
            else:
                title, where = "Vstup do miestnosti", room_label(seq.get("room", ""))
            scenes.append({"id": scene_id(chunk, seq["id"]), "chunk": chunk, "era": CHUNK_ERA[chunk], "kind": "Rozhovor",
                           "title": title, "where": where, "lines": [line_row(x) for x in seq["lines"]]})
        for ext_topic in de.get("topic_extensions", []):
            who = names.get(ext_topic.get("character", ""), ext_topic.get("character", ""))
            label = tables.get(f"topic.{ext_topic['topic']}.label", ext_topic["topic"])
            scenes.append({"id": scene_id(chunk, ext_topic["id"]), "chunk": chunk, "era": CHUNK_ERA[chunk],
                           "kind": "Téma (dlhšia)", "title": label, "where": who,
                           "lines": [line_row(x) for x in ext_topic["lines"]]})
        for topic in de.get("topics", []):
            who = names.get(topic.get("character", ""), topic.get("character", ""))
            scenes.append({"id": scene_id(chunk, topic["id"]), "chunk": chunk, "era": CHUNK_ERA[chunk],
                           "kind": "Nová téma", "title": topic.get("label", topic["id"]), "where": who,
                           "lines": [line_row(x) for x in topic["lines"]]})
        # Remaining single-key rewrites, grouped by what they are.
        groups = {}
        for key, row in rewrites.items():
            if key in covered:
                continue
            m = re.match(r"(look|hotspot|exit|room|item|quest|action|puzzle|journal|ui|era|cutscene|epilogue|entry|topic|conn|char)\.", key)
            kind = {"look": "Opisy", "hotspot": "Opisy", "item": "Predmety", "quest": "Denník a nápovedy",
                    "journal": "Denník a nápovedy", "ui": "Rozhranie", "era": "Rozhranie", "cutscene": "Scény",
                    "epilogue": "Epilóg", "entry": "Vstupné repliky", "puzzle": "Hádanky"}.get(m.group(1) if m else "", "Ostatné")
            if key.startswith("action.") and key.rsplit(".", 1)[-1] in ("objective", "journal", "label"):
                kind = "Denník a nápovedy"
            old = tables.get(key, "")
            groups.setdefault(kind, []).append({"key": key, "speaker": names.get(speaker_of.get(key, ""), ""),
                                                "old": old, "new": row["sk_new"], "state": "changed" if row["sk_new"] != old else "same"})
        for kind, lines in groups.items():
            for i in range(0, len(lines), 25):
                part = lines[i:i + 25]
                scenes.append({"id": scene_id(chunk, kind, str(i // 25)), "chunk": chunk, "era": CHUNK_ERA[chunk],
                               "kind": kind, "title": kind + (f" ({i // 25 + 1})" if len(lines) > 25 else ""),
                               "where": "", "lines": part})

    # New content (Zuzana, S69, items, quests) from the merged world overlay.
    new_lines = []
    for item in world_ext.get("items", []):
        new_lines += [{"key": f"item.{item['id']}.name", "speaker": "Predmet", "old": "", "new": item.get("name", ""), "state": "new"},
                      {"key": f"item.{item['id']}", "speaker": "Opis predmetu", "old": "", "new": item.get("look", ""), "state": "new"}]
    for q in world_ext.get("quests", []):
        new_lines += [{"key": f"quest.{q['id']}.title", "speaker": "Úloha", "old": "", "new": q.get("title", ""), "state": "new"},
                      {"key": f"quest.{q['id']}.goal", "speaker": "Cieľ", "old": "", "new": q.get("goal", ""), "state": "new"}]
        new_lines += [{"key": f"quest.{q['id']}.hint.{n}", "speaker": f"Nápoveda {n}", "old": "", "new": h, "state": "new"}
                      for n, h in enumerate(q.get("hints", []), 1)]
    for r in world_ext.get("rooms", []):
        new_lines.append({"key": f"room.{r['id']}.name", "speaker": "Miestnosť", "old": "", "new": r.get("name", ""), "state": "new"})
        new_lines += [{"key": l.get("key", ""), "speaker": names.get(l.get("speaker", ""), l.get("speaker", "")), "old": "",
                       "new": l.get("sk", ""), "state": "new"} for l in r.get("first_entry", [])]
    for h in world_ext.get("hotspots", []):
        new_lines.append({"key": f"hotspot.{h['id']}.name", "speaker": "Objekt", "old": "", "new": h.get("name", ""), "state": "new"})
        if h.get("look"):
            new_lines.append({"key": f"hotspot.{h['id']}.look", "speaker": "Opis", "old": "", "new": h["look"], "state": "new"})
    for a in world_ext.get("actions", []):
        for field, label in (("label", "Akcia"), ("objective", "Cieľ v denníku")):
            if a.get(field):
                new_lines.append({"key": f"action.{a['id']}.{field}", "speaker": label, "old": "", "new": a[field], "state": "new"})
        for l in a.get("lines", []):
            new_lines.append({"key": l.get("key", l.get("line_id", "")), "speaker": names.get(l.get("speaker", ""), l.get("speaker", "")),
                              "old": "", "new": l.get("sk", l.get("text", "")), "state": "new"})
    for n, e in enumerate(world_ext.get("epilogue", []), 1):
        for field in ("shot", "line"):
            if e.get(field):
                new_lines.append({"key": f"epilogue.new{n}.{field}", "speaker": "Epilóg", "old": "", "new": e[field], "state": "new"})
    for i in range(0, len(new_lines), 30):
        scenes.append({"id": scene_id("NEW", str(i // 30)), "chunk": "NEW", "era": "Zuzana a Sokolíkovský dvor",
                       "kind": "Nový obsah", "title": f"Zuzana, Sokolíkovský dvor, nové predmety a úlohy ({i // 30 + 1})",
                       "where": "", "lines": [l for l in new_lines[i:i + 30] if l["new"]]})

    # The five 2020 entry lines already applied today (for the record; they can still be vetoed).
    entries = list(csv.DictReader(open(OUT_V2 / "C1_entries.csv", encoding="utf-8")))
    game_entries = {l["line_id"]: l["text"] for r in game["rooms"] for l in r.get("first_entry", [])}
    scenes.insert(0, {"id": "C1-entries", "chunk": "C1", "era": "2020 (už v hre)", "kind": "Vstupné repliky",
                      "title": "Adamove repliky pri vstupe do miestností", "where": "Čierna Voda",
                      "lines": [{"key": e["keys"], "speaker": "Adam", "old": game_entries.get(e["keys"], ""),
                                 "new": e["sk_new"], "state": "changed"} for e in entries]})

    for s in scenes:
        s["counts"] = {st: sum(1 for l in s["lines"] if l["state"] == st) for st in ("changed", "new", "same")}
    scenes = [s for s in scenes if s["counts"]["changed"] or s["counts"]["new"]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(scenes, ensure_ascii=False, indent=0), encoding="utf-8")
    total = {st: sum(s["counts"][st] for s in scenes) for st in ("changed", "new")}
    print(f"{len(scenes)} scenes, {total['changed']} changed lines, {total['new']} new lines -> {OUT.relative_to(ROOT)}")
    by = {}
    for s in scenes:
        by[s["era"]] = by.get(s["era"], 0) + 1
    print(by)


if __name__ == "__main__":
    main()
