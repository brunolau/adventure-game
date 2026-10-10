"""Manifest and install of the English dub (en_dub.py finalize | install).

build():   art/voice/en/manifest.json (every spoken key: speaker, voice, English and Slovak text, colour, the take's
           transcript and check, flags) + flags.json (what to listen to first).
install(): copies the finished OGGs into src/game/assets/voice_en/ (only files whose content changed), removes
           recordings the script no longer has, writes aliases.json (key -> the key that owns the recording). Refuses
           while a line is missing or its text changed since its take.
"""
from __future__ import annotations

import collections
import json
import shutil

import en_dub as E
import voice_lib as V


def flag_of(check: dict) -> str | None:
    if check["meaning_errors"]:
        return "differs: " + ", ".join(f"{a or '∅'}→{b or '∅'}" for a, b in check["meaning_errors"])
    if check["timing"]:
        return "timing: " + ", ".join(check["timing"])
    fillers = [b for a, b in check["minor"] if not a]
    if fillers:
        return "extra word: " + ", ".join(fillers)
    return None


def build() -> dict:
    all_jobs = E.jobs()
    al = E.aliases(all_jobs)
    recs = {}
    for j in all_jobs:
        f = E.cache_path(j["line_id"])
        if j["line_id"] not in al and f.exists():
            recs[j["line_id"]] = json.loads(f.read_text(encoding="utf-8"))
    missing = [j["line_id"] for j in all_jobs if j["line_id"] not in al and j["line_id"] not in recs]
    stale = [lid for lid, r in recs.items() if r["text_sha1"] != E.text_hash(next(j["text"] for j in all_jobs if j["line_id"] == lid))]
    lines, flags, names = [], [], []
    for j in all_jobs:
        owner = al.get(j["line_id"], j["line_id"])
        r = recs.get(owner)
        entry = {"line_id": j["line_id"], "group": j["group"], "kind": j["kind"], "speaker": j["speaker"],
                 "voice": E.CAST[j["speaker"]]["voice"], "era": j["era"], "scene": j["scene"], "text": j["text"],
                 "sk": j["sk"], "fx": j["fx"], "irony": j["irony"], "alias_of": al.get(j["line_id"]),
                 "file": f"{owner}.ogg"}
        if r is not None:
            c = r["best"]["check"]
            entry.update(duration_s=r.get("duration_s"), lufs=r.get("lufs"), takes=r["takes"], retaken=r["retaken"],
                         heard=r["best"]["heard"], ok=c["ok"], flag=flag_of(c),
                         chars_per_s=r["best"]["measure"].get("chars_per_s"))
            if owner == j["line_id"]:
                if entry["flag"]:
                    flags.append({"line_id": owner, "speaker": j["speaker"], "why": entry["flag"], "text": j["text"],
                                  "heard": r["best"]["heard"], "retaken": r["retaken"]})
                for a, b in c["minor"]:
                    if a:
                        names.append({"line_id": owner, "name": a, "heard": b})
        lines.append(entry)
    own = list(recs.values())
    by_group = collections.Counter(j["group"] for j in all_jobs)
    takes_by_group = collections.Counter(r["group"] for r in own)
    why = collections.Counter(f["why"].split(":")[0] for f in flags)
    man = {
        "version": 1, "language": "en", "model": E.MODEL,
        "about": "English dub of every key the Slovak dub speaks (art/voice/full/manifest.json, std_manifest.json): the "
                 "same stock voice, character direction, dry-irony marking and colour per line; text = the en column of "
                 "the live tables. Method and tools: art/voice/tools/en_dub.py, docs/voice/ENGLISH.md.",
        "language_direction": E.EN.strip(), "irony_direction": E.IRONY_DIRECTION.strip(),
        "name_hints": [{"name": n, "say": s} for n, s in E.HINTS], "spoken_forms": E.SPOKEN,
        "counts": {"keys": len(all_jobs), "by_group": dict(by_group), "takes": len(own), "takes_by_group": dict(takes_by_group),
                   "aliases": len(al), "retaken": sum(1 for r in own if r["retaken"]),
                   "clean": sum(1 for r in own if r["best"]["check"]["ok"] and not r["best"]["check"]["minor"]),
                   "flagged": len(flags), "flagged_by_reason": dict(why), "names_heard_differently": len(names),
                   "minutes": round(sum(r.get("duration_s", 0) for r in own) / 60, 1),
                   "chars": sum(len(r["tts_text"]) for r in own),
                   "all_takes": sum(r["takes"] for r in own)},
        "spend_usd": round(E.spend(own), 4), "spend_logged_usd": round(V.fal_api.logged_spend(E.ASSET), 4),
        "missing": missing, "stale": stale, "lines": lines,
    }
    E.OUT.mkdir(parents=True, exist_ok=True)
    (E.OUT / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (E.OUT / "flags.json").write_text(json.dumps({"flags": flags, "names": names}, ensure_ascii=False, indent=1),
                                      encoding="utf-8", newline="\n")
    c = man["counts"]
    print(f"manifest: {c['keys']} keys, {c['takes']} takes, {c['aliases']} aliases, {c['retaken']} retaken, {c['clean']} clean, "
          f"{c['flagged']} flagged {dict(why)}, {c['names_heard_differently']} names heard differently, {c['minutes']} min; "
          f"spend ${man['spend_usd']} (logged ${man['spend_logged_usd']}); missing {len(missing)}, stale {len(stale)}")
    return man


def install() -> None:
    man = build()
    if man["missing"] or man["stale"]:
        raise SystemExit(f"not installed: {len(man['missing'])} lines without a take, {len(man['stale'])} with changed text "
                         f"(run en_dub.py gen): {(man['missing'] + man['stale'])[:10]}")
    E.GAME.mkdir(parents=True, exist_ok=True)
    owners = sorted({l["file"] for l in man["lines"]})
    copied = 0
    for name in owners:
        src, dst = E.TAKES / name, E.GAME / name
        data = src.read_bytes()
        if not dst.exists() or dst.read_bytes() != data:
            shutil.copyfile(src, dst)
            copied += 1
    removed = 0
    keep = set(owners)
    for f in list(E.GAME.glob("*.ogg")):
        if f.name not in keep:
            f.unlink()
            imp = f.with_name(f.name + ".import")
            if imp.exists():
                imp.unlink()
            removed += 1
    aliases = {l["line_id"]: l["alias_of"] for l in man["lines"] if l["alias_of"]}
    (E.GAME / "aliases.json").write_text(json.dumps(dict(sorted(aliases.items())), ensure_ascii=False, indent=1) + "\n",
                                         encoding="utf-8", newline="\n")
    size = sum((E.GAME / n).stat().st_size for n in owners)
    print(f"installed into {E.GAME.relative_to(V.ROOT)}: {len(owners)} recordings ({size / 1e6:.1f} MB), {copied} copied, "
          f"{removed} removed, {len(aliases)} aliases. Run the Godot import next (build.bat does).")
