"""Collect EVERY spoken line of the game (all eras) for the full voice-over, in play order by era and scene.

Text = the approved final text: the live tables (src/game/localization/dialogue.csv, the effective game with
src/game/data/content_ext/dialogue_ext.json) with the approved knowledge drafts applied on top
(docs/writing/out_v3/knowledge.csv rewrites, docs/writing/out_v3/knowledge_ext.json sequences/topics that replace
the live overlay entries with the same id). Epilogue lines come from world.csv (epilogue.<n>.line).

Read-only on the game. Writes art/voice/full/lines.json:
  lines[]   line_id, speaker, text, era, scene, scene_name, block, block_label, fx (None/phone/tape/device/radio),
            prologue (True when the trial file exists and its text is unchanged -> not regenerated)
  skipped[] non-verbal lines (Bodka)
"""
from __future__ import annotations

import copy
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import content_ext  # noqa: E402

FULL = ROOT / "art/voice/full"
LOC = ROOT / "src/game/localization"
KNOW_CSV = ROOT / "docs/writing/out_v3/knowledge.csv"
KNOW_EXT = ROOT / "docs/writing/out_v3/knowledge_ext.json"
TRIAL = ROOT / "art/voice/trial/manifest.json"
NON_VERBAL = {"BODKA"}
ERA_ORDER = [2020, 1995, 1960, 2035, 1982]
# inventory actions (combine items) take the room the walkthrough is in after them; side-quest ones by hand
INVENTORY_ROOM = {"Q10C": "S37"}


def read_csv(path: Path, col: str = "sk") -> dict[str, str]:
    with path.open(encoding="utf-8-sig", newline="") as h:
        return {r["keys"]: r[col] for r in csv.DictReader(h)}


def merged_dialogue_overlay() -> Path:
    live = json.loads(content_ext.DIALOGUE_EXT.read_bytes().decode("utf-8-sig"))
    know = json.loads(KNOW_EXT.read_text(encoding="utf-8"))
    out = copy.deepcopy(live)
    for sect in ("sequences", "topics", "topic_extensions"):
        new = know.get(sect) or []
        ids = {e["id"] for e in new}
        out[sect] = [e for e in out.get(sect, []) if e.get("id") not in ids] + new
    p = FULL / "_effective_dialogue_ext.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def texts_and_overlay_sk(overlay: dict) -> dict[str, str]:
    t = read_csv(LOC / "dialogue.csv")
    for sect in ("sequences", "topics", "topic_extensions"):
        for e in overlay.get(sect) or []:
            for l in e.get("lines", []):
                if isinstance(l, dict) and l.get("key") and l.get("sk") and l["key"] not in t:
                    t[l["key"]] = l["sk"]
    t.update({k: v for k, v in read_csv(KNOW_CSV, "sk_new").items() if v.strip()})
    return t


def main() -> None:
    FULL.mkdir(parents=True, exist_ok=True)
    ov_path = merged_dialogue_overlay()
    overlay = json.loads(ov_path.read_text(encoding="utf-8"))
    res = content_ext.load_effective_game(dialogue=ov_path)
    if res.errors:
        print("overlay errors:", res.errors[:10])
    eff = res.game
    texts = texts_and_overlay_sk(overlay)
    world = read_csv(LOC / "world.csv")
    rooms = {r["id"]: r for r in eff["rooms"]}
    era_of_room = {r["id"]: r.get("era") for r in eff["rooms"]}
    room_name = {r["id"]: world.get(f"room.{r['id']}.name") or r.get("name") or r["id"] for r in eff["rooms"]}
    actions = {a["id"]: a for a in eff["actions"]}
    cutscenes = {c["id"]: c for c in eff["cutscenes"]}
    cs_action = {}
    for a in eff["actions"]:
        if a.get("cutscene"):
            cs_action.setdefault(a["cutscene"], a["id"])

    # scene order: rooms in order of first use on the main route, then the rest in data order
    walk = json.loads((ROOT / "design-doc/walkthrough.json").read_text(encoding="utf-8"))
    order: list[str] = []
    act_rank = {}
    room_after = {st["action"]: st.get("room_after") for st in walk["main_route"]}
    steps = walk["main_route"] + [{"action": x} for x in walk.get("postgame_optional_route", [])]
    for i, st in enumerate(steps):
        act_rank.setdefault(st["action"], i)
        for r in st.get("travel_path", []) + [actions.get(st["action"], {}).get("room")]:
            if r and r in rooms and r not in order:
                order.append(r)
    for r in rooms:
        if r not in order:
            order.append(r)
    order.sort(key=lambda r: ERA_ORDER.index(era_of_room[r]) if era_of_room[r] in ERA_ORDER else 9)

    trial = {l["line_id"]: l for l in json.loads(TRIAL.read_text(encoding="utf-8"))["lines"]}
    out, skipped, seen = [], [], set()
    by_room_actions: dict[str, list[dict]] = {}
    for a in eff["actions"]:
        room_of = a["room"] if a["room"] in rooms else (room_after.get(a["id"]) or INVENTORY_ROOM.get(a["id"]))
        if room_of not in rooms:
            raise SystemExit(f"no room for inventory action {a['id']}")
        by_room_actions.setdefault(room_of, []).append(a)
    chars_in_room: dict[str, list[dict]] = {}
    for c in eff["characters"]:
        rs = c.get("rooms") or []
        if rs:
            chars_in_room.setdefault(rs[0], []).append(c)
    epi_by_after = {}
    for i, e in enumerate(eff.get("epilogue", [])):
        epi_by_after.setdefault(e["after"], []).append((i, e))

    def fx_of(lid: str, spk: str, room: str, block: str, block_speakers: set[str]) -> str | None:
        if spk == "MIRA20" and room != "S06":
            return "phone"
        if spk == "LEA_REC":          # her 2032 voice message: telephone colour
            return "phone"
        if spk == "ADAM10":
            return "tape"
        if spk == "LEA95" and "ADAM10" in block_speakers:
            return "tape"
        if spk in ("NINA_REMOTE", "JANA20"):   # service channel / video call: light call colour
            return "radio"
        if spk in ("SYSTEM", "ROBOT"):
            return "device"
        return None

    def emit(room: str, block: str, label: str, lines: list[dict], kind: str) -> None:
        spks = {l["speaker"] for l in lines}
        for l in lines:
            lid = l.get("line_id") or l.get("key")
            if lid in seen:
                continue
            seen.add(lid)
            spk = l["speaker"]
            text = texts.get(lid)
            if text is None:
                text = l.get("text") or l.get("sk")
                print("no table text, using data text:", lid)
            if spk in NON_VERBAL:
                skipped.append({"line_id": lid, "speaker": spk, "text": text, "why": "non-verbal (dog) -> SFX"})
                continue
            tr = trial.get(lid)
            epi = kind == "epilogue"
            out.append({"line_id": lid, "speaker": spk, "text": text,
                        "era": "epilog" if epi else era_of_room.get(room), "scene": "EPI" if epi else room,
                        "scene_name": "Epilóg (záverečné zábery)" if epi else room_name.get(room, room), "block": block, "block_label": label, "kind": kind,
                        "fx": fx_of(lid, spk, room, block, spks),
                        "prologue": bool(tr and tr["text"] == text),
                        "prologue_text_changed": bool(tr and tr["text"] != text)})

    for room in order:
        r = rooms[room]
        if r.get("first_entry"):
            emit(room, f"entry.{room}", "Prvý vstup", r["first_entry"], "entry")
        for ex in r.get("exits", []):
            if ex.get("first_ride"):
                emit(room, f"travel.{ex['id']}", "Prvá cesta", ex["first_ride"], "travel")
        acts = sorted(by_room_actions.get(room, []), key=lambda a: act_rank.get(a["id"], 10_000))
        for a in acts:
            label = texts.get(f"action.{a['id']}.label") or world.get(f"action.{a['id']}.label") or a.get("label", a["id"])
            emit(room, f"action.{a['id']}", label, a.get("lines", []), "action")
            cs = a.get("cutscene")
            if cs and cs_action.get(cs) == a["id"]:
                emit(room, f"cutscene.{cs}", f"Animácia {cs}", [l for b in cutscenes[cs]["beats"] for l in b["lines"]],
                     "cutscene")
            for i, e in epi_by_after.get(a["id"], []):
                spk, _, _ = e["line"].partition(":")
                lid = f"epilogue.{i + 1}.line"
                emit(room, f"epilogue.{i + 1}", "Epilóg", [{"line_id": lid, "speaker": spk.strip(),
                                                            "text": world.get(lid)}], "epilogue")
        for c in chars_in_room.get(room, []):
            for t in c.get("ambient_topics", []):
                label = texts.get(f"topic.{t['id']}.label") or t.get("label", t["id"])
                emit(room, f"topic.{t['id']}", label, t["lines"], "topic")
    # anything not reached (cutscenes without an action, ...)
    for cid, cs in cutscenes.items():
        lines = [l for b in cs["beats"] for l in b["lines"]]
        if any((l.get("line_id") or l.get("key")) not in seen for l in lines):
            room = actions[cs_action[cid]]["room"] if cid in cs_action else "S10"
            print("unplaced cutscene", cid, "->", room)
            emit(room, f"cutscene.{cid}", f"Animácia {cid}", lines, "cutscene")
    for i, e in enumerate(eff.get("epilogue", [])):
        lid = f"epilogue.{i + 1}.line"
        if lid not in seen:
            spk = e["line"].partition(":")[0].strip()
            print("unplaced epilogue", lid)
            emit("S10", f"epilogue.{i + 1}", "Epilóg", [{"line_id": lid, "speaker": spk, "text": world.get(lid)}],
                 "epilogue")

    out.sort(key=lambda l: l["era"] == "epilog")  # stable: epilogue lines last, in quest order
    (FULL / "lines.json").write_text(json.dumps({"lines": out, "skipped": skipped}, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    new = [l for l in out if not l["prologue"]]
    print(len(out), "spoken lines;", len(new), "to voice;", sum(len(l["text"]) for l in new), "chars")
    print("changed prologue lines:", [l["line_id"] for l in out if l["prologue_text_changed"]])
    print("missing trial lines:", [k for k in trial if k not in seen])
    print("by era:", Counter(l["era"] for l in new))
    print("by speaker:", Counter(l["speaker"] for l in new).most_common())
    print("fx:", Counter(l["fx"] for l in new))
    print("skipped:", len(skipped))


if __name__ == "__main__":
    main()
