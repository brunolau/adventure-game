"""Collect the pending text changes (docs/writing/out_v2) into one approval data file for the owner.

Usage: python tools/approval_pack.py         (round 1: docs/writing/out_v2 -> changes.json)
       python tools/approval_pack.py --r2    (round 2: docs/writing/out_v3 knowledge fixes, step hints, difficulty UI
                                              -> changes_r2.json, scene ids "R2-...")
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
        scenes.append({"id": scene_id("NEW", str(i // 30)), "chunk": "NEW", "era": "Zuzana a Pri LEALe",
                       "kind": "Nový obsah", "title": f"Zuzana, Pri LEALe, nové predmety a úlohy ({i // 30 + 1})",
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


# --------------------------------------------------------------------------- round 2 (out_v3)

OUT_V3 = ROOT / "docs" / "writing" / "out_v3"
OUT_R2 = ROOT / "docs" / "writing" / "approval" / "changes_r2.json"
CONTENT_EXT = ROOT / "src" / "game" / "data" / "content_ext"
STEP_LINE = re.compile(r"^- Step (?P<step>\S+): (?P<where>.*?)(?:, target: (?P<target>.*?))?\. "
                       r"Exact step \(context only, must NOT be revealed\): (?P<exact>.*)$")
UI_LINE = re.compile(r"^- `(?P<key>[^`]+)` \[(?P<role>[^\]]*)\] ?(?P<text>.*)$")


def room_era(rid):
    """Era label of a room id (the chunk ranges of tools/writing_bundles.py; S69 is 1995)."""
    n = int(rid[1:]) if re.fullmatch(r"S\d+", rid or "") else 0
    if 1 <= n <= 10 or 51 <= n <= 56:
        return "2020"
    if 11 <= n <= 30 or n == 69:
        return "1995"
    if 31 <= n <= 40:
        return "1962"
    if 57 <= n <= 66:
        return "1982"
    if 41 <= n <= 50 or n in (67, 68):
        return "2035"
    return ""


def read_csv_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main_r2():
    """Approval data for the round-2 drafts in docs/writing/out_v3 (knowledge fixes, Standard / Hard step hints,
    difficulty UI strings) -> docs/writing/approval/changes_r2.json; every scene id starts with "R2-"."""
    tables = load_tables()
    game = json.loads((ROOT / "design-doc" / "game.json").read_text(encoding="utf-8"))
    world = json.loads((CONTENT_EXT / "world_ext.json").read_text(encoding="utf-8"))
    live_dlg = json.loads((CONTENT_EXT / "dialogue_ext.json").read_text(encoding="utf-8"))
    walk = json.loads((ROOT / "design-doc" / "walkthrough.json").read_text(encoding="utf-8"))
    rooms = {r["id"]: r for r in game["rooms"]} | {r["id"]: r for r in world.get("rooms", [])}
    actions = {a["id"]: a for a in game["actions"]} | {a["id"]: a for a in world.get("actions", [])}
    for rel in world.get("relocations", []) or []:
        if isinstance(rel, dict) and rel.get("action") in actions and rel.get("room"):
            actions[rel["action"]] = dict(actions[rel["action"]], room=rel["room"])
    quests = {q["id"]: q for q in game["quests"]} | {q["id"]: q for q in world.get("quests", [])}
    chars = {c["id"]: c for c in game["characters"]} | {c["id"]: c for c in world.get("characters", [])}
    names = {cid: tables.get(f"char.{cid}.name", c.get("name", cid)) for cid, c in chars.items()}
    names |= {k: tables.get(f"char.{k}.name", k) for k in game.get("non_actor_speakers", {})}
    names.setdefault("SYSTEM", "Prístroj")
    speaker_of = {}
    for a in actions.values():
        for line in a.get("lines", []):
            speaker_of[line.get("line_id")] = line.get("speaker")
    for c in chars.values():
        for t in c.get("ambient_topics", []):
            for line in t.get("lines", []):
                speaker_of[line.get("line_id")] = line.get("speaker")
    live_text, live_speaker = {}, {}
    for grp in ("sequences", "topic_extensions", "topics"):
        for e in live_dlg.get(grp, []):
            if e.get("label_key"):
                live_text[e["label_key"]] = e.get("label", "")
            for ln in e.get("lines", []):
                if isinstance(ln, dict):
                    live_text[ln["key"]] = ln.get("sk", "")
                    live_speaker[ln["key"]] = ln.get("speaker", "")

    # story order: walkthrough main route, then the optional route, then the rest
    order = {}
    for n, s in enumerate(walk.get("main_route", [])):
        order.setdefault(s["action"], n)
    for n, aid in enumerate(walk.get("postgame_optional_route", [])):
        order.setdefault(aid if isinstance(aid, str) else aid.get("action"), 1000 + n)
    step_room = {s["action"]: s.get("room_after", "") for s in walk.get("main_route", [])}
    room_order = {}
    for aid, a in actions.items():
        if aid in order and a.get("room"):
            room_order[a["room"]] = min(room_order.get(a["room"], 1e9), order[aid])
    char_room = {}
    for r in rooms.values():
        for h in r.get("hotspots", []):
            if h.get("character_id"):
                char_room.setdefault(h["character_id"], r["id"])
    for h in world.get("hotspots", []):
        if h.get("character_id") and h.get("room"):
            char_room.setdefault(h["character_id"], h["room"])

    def room_label(rid):
        return tables.get(f"room.{rid}.name", rooms.get(rid, {}).get("name", rid))

    def spk(key, speaker=None):
        s = speaker or speaker_of.get(key) or live_speaker.get(key) or ""
        return names.get(s, s)

    scenes = []

    def add_scene(sid, era, kind, title, where, lines, sort, note=""):
        scenes.append({"id": "R2-" + scene_id(sid), "chunk": "R2", "era": era, "kind": kind, "title": title,
                       "where": where, "note": note, "lines": lines, "_sort": sort})

    # ---- 1. knowledge fixes (Adam never knows what he has not learned), grouped by scene, play order
    kn = {r["keys"]: r for r in read_csv_rows(OUT_V3 / "knowledge.csv")}
    kext = json.loads((OUT_V3 / "knowledge_ext.json").read_text(encoding="utf-8"))
    used = set()
    owner_note = {
        "action.B06.002": "Text presne podľa zadania. „Zhlasniť“ je hovorové, spisovne „zosilniť“; alternatíva: "
                          "„…Kazetu by to chcelo opraviť, ale ako tie hlasy zosilním?“",
        "look.S30.dial": "Na stojane pribudne malý štítok babkiným písmom (rekvizita, ktorú obraz možno neukazuje). "
                         "Alternatíva: opis nechať bez zmeny.",
        "look.S45.bench": "Pod nápisom pribudne lístok s menom a adresou Tamary (rekvizita, ktorú obraz možno neukazuje).",
        "quest.M08.title": "Mení sa názov úlohy (bolo „Ručná pumpa“): pumpa sa v čase, keď sa názov zobrazí, ešte neobjavila.",
    }

    def csv_row(key, speaker=""):
        used.add(key)
        old = tables.get(key, "")
        new = kn[key]["sk_new"]
        row = {"key": key, "speaker": speaker, "old": old, "new": new, "state": "changed" if new != old else "same"}
        if key in owner_note:
            row["note"] = owner_note[key]
        return row

    def ext_line(item):
        if isinstance(item, str):
            if item in kn:
                return csv_row(item, spk(item))
            t = tables.get(item, live_text.get(item, ""))
            return {"key": item, "speaker": spk(item), "old": t, "new": t, "state": "same"}
        old = live_text.get(item["key"], "")
        state = "new" if item["key"] not in live_text else ("changed" if old != item["sk"] else "same")
        return {"key": item["key"], "speaker": spk(item["key"], item.get("speaker")), "old": old, "new": item["sk"],
                "state": state}

    seq_by_action = {}
    for seq in kext.get("sequences", []):
        seq_by_action[seq["action"]] = seq
    extra_by_action, extra_by_room, extra_by_quest, extra_items, extra_topics = {}, {}, {}, [], {}
    for key in kn:
        if key.startswith("action.") or key.startswith("ui.hint_step."):
            aid = key.split(".")[2] if key.startswith("ui.hint_step.") else key.split(".")[1]
            extra_by_action.setdefault(aid, []).append(key)
        elif re.match(r"^(look|exit|conn|entry|hotspot)\.S\d+", key):
            extra_by_room.setdefault(key.split(".")[1], []).append(key)
        elif key.startswith("quest."):
            extra_by_quest.setdefault(key.split(".")[1], []).append(key)
        elif key.startswith("item."):
            extra_items.append(key)
        elif key.startswith("topic."):
            extra_topics.setdefault(key.split(".")[1], []).append(key)
    label_of = {"objective": "Cieľ v denníku", "journal": "Zápis v denníku", "label": "Voľba (akcia)", "hint_step": "Nápoveda (Ľahká, presný krok)"}

    for aid in sorted(set(seq_by_action) | set(extra_by_action), key=lambda a: (order.get(a, 1e9), a)):
        a = actions.get(aid, {})
        rid = a.get("room", "")
        lines = [ext_line(x) for x in seq_by_action[aid]["lines"]] if aid in seq_by_action else []
        lines += [csv_row(k) for k in extra_by_action.get(aid, []) if k not in used and not k.startswith("ui.") and k.rsplit(".", 1)[-1] not in label_of]
        for k in extra_by_action.get(aid, []):
            if k not in used:
                kind = "hint_step" if k.startswith("ui.hint_step.") else k.rsplit(".", 1)[-1]
                lines.append(csv_row(k, label_of.get(kind, "")))
        title = tables.get(f"action.{aid}.label", a.get("label", aid))
        where = room_label(rid) if rid in rooms else "Brašňa (spájanie predmetov)"
        add_scene(f"knowledge-{aid}", room_era(rid) or room_era(step_room.get(aid, "")), "Znalosti: rozhovor" if aid in seq_by_action else "Znalosti: denník",
                  title, where, lines, order.get(aid, 1e9))
    for rid in sorted(extra_by_room, key=lambda r: (room_order.get(r, 1e9), r)):
        lines = []
        for k in extra_by_room[rid]:
            kind = k.split(".")[0]
            lines.append(csv_row(k, {"look": "Opis", "exit": "Zamknutý východ", "conn": "Zamknutá cesta na mape",
                                     "entry": spk(k) or "Adam", "hotspot": "Objekt"}.get(kind, "")))
        add_scene(f"knowledge-{rid}", room_era(rid), "Znalosti: opisy", room_label(rid), room_label(rid), lines,
                  room_order.get(rid, 1e9) + 0.5)
    for qid in sorted(extra_by_quest, key=lambda q: (min((order.get(x, 1e9) for x in quests.get(q, {}).get("actions", [])), default=1e9), q)):
        q = quests.get(qid, {})
        lines = [csv_row(k, {"title": "Názov úlohy", "goal": "Cieľ úlohy"}.get(k.split(".")[-1], "Nápoveda " + k.split(".")[-1]))
                 for k in extra_by_quest[qid]]
        first = min((order.get(x, 1e9) for x in q.get("actions", [])), default=1e9)
        add_scene(f"knowledge-quest-{qid}", room_era(actions.get((q.get("actions") or [""])[0], {}).get("room", "")),
                  "Znalosti: úloha", tables.get(f"quest.{qid}.title", q.get("title", qid)), "Denník", lines, first - 0.5)
    for topic in kext.get("topics", []) + kext.get("topic_extensions", []):
        cid = topic.get("character", "")
        rid = char_room.get(cid, "")
        lines = []
        if topic.get("label_key"):
            lk = topic["label_key"]
            old = live_text.get(lk, tables.get(lk, ""))
            lines.append({"key": lk, "speaker": "Téma (voľba)", "old": old, "new": topic["label"],
                          "state": "changed" if old != topic["label"] else "same"})
        lines += [ext_line(x) for x in topic["lines"]]
        add_scene(f"knowledge-topic-{topic['id']}", room_era(rid), "Znalosti: téma", topic.get("label", topic["id"]),
                  names.get(cid, cid), lines, room_order.get(rid, 1e9) + 0.7)
    for cid, keys in extra_topics.items():
        rid = char_room.get(cid, "")
        lines = [csv_row(k, "Téma (voľba)" if k.endswith(".label") else spk(k)) for k in keys]
        add_scene(f"knowledge-topic-{cid}", room_era(rid), "Znalosti: téma", names.get(cid, cid), names.get(cid, cid),
                  lines, room_order.get(rid, 1e9) + 0.7)
    if extra_items:
        add_scene("knowledge-items", "rôzne", "Znalosti: predmety", "Účel predmetov (hráč ho nevidí, len pre súlad)", "",
                  [csv_row(k, tables.get(f"item.{k.split('.')[1]}.name", k.split(".")[1])) for k in extra_items], 1e9)
    missing = set(kn) - used
    if missing:
        raise SystemExit(f"knowledge.csv keys not placed in a scene: {sorted(missing)}")

    # ---- 2. Standard / Hard step hints, grouped by quest (nudge + where per step, the exact Easy step as context)
    hints = {r["keys"]: r["sk_new"] for r in read_csv_rows(OUT_V3 / "hints.csv")}
    md = (ROOT / "docs" / "writing" / "context" / "hints.md").read_text(encoding="utf-8").splitlines()
    qid, qtitle, cur = None, "", None
    hint_scenes = []
    for raw in md:
        if raw.startswith("### "):
            head = raw[4:].strip()
            qid = head.split(" · ")[0]
            qtitle = re.sub(r" \((main|side) quest\)$", "", head.split(" · ", 1)[1]) if " · " in head else head
            cur = {"qid": qid, "title": qtitle, "lines": []}
            hint_scenes.append(cur)
            continue
        m = STEP_LINE.match(raw.strip())
        if not m or cur is None:
            continue
        step = m["step"]
        nk, wk = f"hint.nudge.{step}", f"hint.where.{step}"
        bag = m["target"] is None
        fallback = (BAG_FALLBACK if bag else f"{m['where']}. Zameraj sa na: {m['target']}.")
        cur["lines"] += [
            {"key": f"context.exact_step.{step}", "speaker": f"{step} · presný krok (Ľahká, len pre kontrolu)",
             "old": m["exact"], "new": m["exact"], "state": "same"},
            {"key": nk, "speaker": f"{step} · Postrčenie (Štandardná a Ťažká)", "old": "", "new": hints[nk], "state": "new"},
            {"key": wk, "speaker": f"{step} · Kde hľadať (Štandardná)", "old": "", "new": hints[wk], "state": "new",
             "note": f"Doteraz Štandardná ukazuje: {fallback}"},
        ]
    placed = {l["key"] for s in hint_scenes for l in s["lines"]}
    if set(hints) - placed:
        raise SystemExit(f"hints.csv keys not placed: {sorted(set(hints) - placed)}")
    for s in hint_scenes:
        q = quests.get(s["qid"], {})
        first = min((order.get(x, 1e9) for x in q.get("actions", [])), default=1e9)
        era = room_era(actions.get((q.get("actions") or [""])[0], {}).get("room", ""))
        add_scene(f"hints-{s['qid']}", era, "Nápovedy (Štandardná / Ťažká)", f"{s['qid']} · {s['title']}", "Nápoveda (H)",
                  s["lines"], 1e10 + first,
                  "Štandardná: 1. postrčenie, 2. kde hľadať, nikdy presný krok. Ťažká: iba postrčenie, po 3 minútach bez pokroku.")

    # ---- 3. difficulty UI strings, one scene per screen (existing strings as context)
    ui_new = {r["keys"]: r["sk_new"] for r in read_csv_rows(OUT_V3 / "ui_difficulty.csv")}
    shown, screen = set(), None
    ui_scenes = []
    for raw in (ROOT / "docs" / "writing" / "context" / "ui_difficulty.md").read_text(encoding="utf-8").splitlines():
        if raw.startswith("### "):
            head = raw[4:].strip()
            screen = {"id": head.split(" · ")[0], "title": head.split(" · ", 1)[-1], "lines": []}
            ui_scenes.append(screen)
            continue
        m = UI_LINE.match(raw.strip())
        if not m or screen is None:
            continue
        key = m["key"]
        if key in ui_new:
            first = key not in shown
            shown.add(key)
            screen["lines"].append({"key": key, "speaker": m["role"], "old": "" if first else ui_new[key], "new": ui_new[key],
                                    "state": "new" if first else "same"})
        else:
            t = tables.get(key, m["text"])
            screen["lines"].append({"key": key, "speaker": m["role"], "old": t, "new": t, "state": "same"})
    if set(ui_new) - shown:
        raise SystemExit(f"ui_difficulty.csv keys not placed: {sorted(set(ui_new) - shown)}")
    for n, s in enumerate(ui_scenes):
        title = {"PICKER": "Nová hra: výber obťažnosti", "SETTINGS": "Nastavenia: nová karta Hra",
                 "HINTS": "Obrazovka nápovedy (H) podľa obťažnosti"}.get(s["id"], s["title"])
        add_scene(f"ui-{s['id']}", "Rozhranie", "Rozhranie: obťažnosť", title, "", s["lines"], 1e12 + n)

    scenes.sort(key=lambda s: s["_sort"])
    for s in scenes:
        del s["_sort"]
        s["counts"] = {st: sum(1 for l in s["lines"] if l["state"] == st) for st in ("changed", "new", "same")}
    scenes = [s for s in scenes if s["counts"]["changed"] or s["counts"]["new"]]
    ids = [s["id"] for s in scenes]
    assert len(ids) == len(set(ids)), "duplicate scene ids"
    OUT_R2.parent.mkdir(parents=True, exist_ok=True)
    OUT_R2.write_text(json.dumps(scenes, ensure_ascii=False, indent=0), encoding="utf-8")
    total = {st: sum(s["counts"][st] for s in scenes) for st in ("changed", "new")}
    by = {}
    for s in scenes:
        by[s["kind"]] = by.get(s["kind"], 0) + 1
    print(f"{len(scenes)} scenes, {total['changed']} changed lines, {total['new']} new lines -> {OUT_R2.relative_to(ROOT)}")
    print(by)


BAG_FALLBACK = "Tento krok urobíš v inventári: spoj dva predmety, ktoré už máš."


if __name__ == "__main__":
    import sys
    main_r2() if "--r2" in sys.argv[1:] else main()
