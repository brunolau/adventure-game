"""Full voice-over 2026-10-07: manifest, casting table, flags, prologue device colour, install into the game.

build()   art/voice/full/manifest.json (every spoken line of the game: the new takes of gen_full.py plus the approved
          prologue files of art/voice/trial/), art/voice/full/casting.json, art/voice/full/flags.json; the four prologue
          SYSTEM lines are re-rendered from their raw takes with the device colour (free) into art/voice/full/
install() copies every OGG of art/voice/full/ (new lines, alias copies, the re-rendered SYSTEM lines) into
          src/game/assets/voice/ - after checking that each line's text still equals the live text (text_sha1)
"""
from __future__ import annotations

import json
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402
import gen_full as G  # noqa: E402
from casting_full import CAST  # noqa: E402

FULL = G.FULL
TRIAL = V.ROOT / "art/voice/trial"
PROLOGUE_RAW = V.ROOT / "art/voice/raw/gemini"


def audition_spend() -> float:
    f = FULL / "audition/audition.json"
    if not f.exists():
        return 0.0
    return sum(r["usd_tts"] + r["usd_stt"] for r in json.loads(f.read_text(encoding="utf-8")))


def flag_of(rec: dict) -> str | None:
    c = rec["best"]["check"]
    why = []
    if c["meaning_errors"]:
        pairs = ", ".join(f"„{a}“ → „{b}“" if a and b else (f"chýba „{a}“" if a else f"navyše „{b}“")
                          for a, b in c["meaning_errors"])
        why.append(("still different after the one retake: " if rec["retaken"] else "different: ") + pairs)
    if c["timing"]:
        why.append("timing: " + ", ".join(c["timing"]))
    if c.get("minor"):
        why.append("extra filler word heard (meaning unchanged, no retake): "
                   + ", ".join(f"„{b}“" for _, b in c["minor"]))
    return "; ".join(why) or None


def rerender_prologue_system(lines: list[dict]) -> list[dict]:
    """The four prologue SYSTEM lines get the device colour of the full voice-over (from their raw best take)."""
    out = []
    for l in lines:
        if not (l["prologue"] and l["speaker"] == "SYSTEM"):
            continue
        raw_rec = json.loads((PROLOGUE_RAW / f"{l['line_id']}.json").read_text(encoding="utf-8"))
        x = V.load_mono(PROLOGUE_RAW / raw_rec["best"]["raw"])
        y, lufs, peak = G.finish(x, "device")
        V.write_ogg(FULL / f"{l['line_id']}.ogg", y)
        out.append({"line_id": l["line_id"], "duration_s": round(len(y) / V.SR, 2), "lufs": float(lufs),
                    "peak_dbtp": float(peak), "from": f"art/voice/raw/gemini/{raw_rec['best']['raw']}"})
    return out


def build() -> dict:
    lines = G.lines_all()
    recs = {r["line_id"]: r for r in G.records()}
    al = G.aliases(G.todo(lines))
    trial = {l["line_id"]: l for l in json.loads((TRIAL / "manifest.json").read_text(encoding="utf-8"))["lines"]}
    sys_rerender = {r["line_id"]: r for r in rerender_prologue_system(lines)}
    out, flags, missing = [], {}, []
    for l in lines:
        lid = l["line_id"]
        base = {k: l[k] for k in ("line_id", "speaker", "text", "era", "scene", "scene_name", "block", "block_label",
                                  "kind", "fx")}
        base["text_sha1"] = G.text_hash(l["text"])
        if l["prologue"]:
            t = trial[lid]
            e = {**base, "source": "prologue", "version": t.get("version", 1), "voice": t["voice"],
                 "delivery": t.get("delivery"), "file": f"../trial/{lid}.ogg", "duration_s": t["duration_s"],
                 "stt": {"scribe_v2": t["stt"].get("scribe_v2"), "ok": t["stt"].get("ok", True),
                         "flag": t["stt"].get("flag")}}
            if lid in sys_rerender:
                e.update(source="prologue, re-rendered with the device colour", file=f"{lid}.ogg",
                         duration_s=sys_rerender[lid]["duration_s"], lufs=sys_rerender[lid]["lufs"],
                         peak_dbtp=sys_rerender[lid]["peak_dbtp"], rerender_from=sys_rerender[lid]["from"])
            out.append(e)
            continue
        src = al.get(lid, lid)
        r = recs.get(src)
        if r is None:
            missing.append(lid)
            continue
        if src != lid:
            shutil.copyfile(FULL / f"{src}.ogg", FULL / f"{lid}.ogg")
        b = r["best"]
        f = flag_of(r)
        if f:
            flags[lid] = f
        out.append({**base, "source": "full", "alias_of": src if src != lid else None, "model": r["model"],
                    "voice": r["voice"], "style_instructions": r["voice_settings"]["style"], "delivery": r["delivery"],
                    "tts_text": r["tts_text"], "file": f"{lid}.ogg", "duration_s": r["duration_s"], "lufs": r["lufs"],
                    "peak_dbtp": r["peak_dbtp"], "takes": r["takes"], "retaken": r["retaken"],
                    "stt": {"scribe_v2": b["stt_scribe"], "wer_scribe": b["wer_scribe"]["wer"],
                            "wer_scribe_nodiac": b["wer_scribe"]["wer_nodiac"], "errors_scribe": b["wer_scribe"]["errors"],
                            "meaning_errors": b["check"]["meaning_errors"], "minor": b["check"].get("minor", []),
                            "timing": b["check"]["timing"], "chars_per_s": b["measure"].get("chars_per_s"),
                            "ok": f is None, "flag": f}})
    new = [e for e in out if e["source"] == "full"]
    rs = list(recs.values())
    spend = G.spend(rs) + audition_spend()
    # casting table
    by_spk: dict[str, dict] = defaultdict(lambda: {"eras": Counter(), "lines": 0, "irony": 0, "fx": Counter()})
    for e in out:
        d = by_spk[e["speaker"]]
        d["eras"][str(e["era"])] += 1
        d["lines"] += 1
        d["irony"] += 1 if e.get("delivery") else 0
        if e.get("fx"):
            d["fx"][e["fx"]] += 1
    casting = {}
    for spk, d in sorted(by_spk.items(), key=lambda kv: -kv[1]["lines"]):
        c = CAST[spk]
        casting[spk] = {"who": c["who"], "age": c["age"], "family": c.get("family"), "voice": c["voice"],
                        "style": c["style"].replace(V.ROOT.as_posix(), ""), "lines": d["lines"],
                        "irony_lines": d["irony"], "eras": dict(d["eras"]), "fx": dict(d["fx"]),
                        "new_lines": sum(1 for e in new if e["speaker"] == spk)}
    scene_voices = defaultdict(lambda: defaultdict(set))
    for e in out:
        if e["scene"] != "EPI":
            scene_voices[e["scene"]][e["voice"]].add(e["speaker"])
    clashes = {s: {v: sorted(sp) for v, sp in vs.items() if len(sp) > 1} for s, vs in scene_voices.items()}
    clashes = {s: v for s, v in clashes.items() if v}
    man = {
        "version": 1, "date": "2026-10-07", "model": G.MODEL,
        "about": "Full voice-over of every spoken line (new lines: gen_full.py; prologue: art/voice/trial/, approved). "
                 "Text = live tables + docs/writing/out_v3/knowledge*.",
        "counts": {"lines": len(out), "new": len(new), "prologue": len(out) - len(new),
                   "aliases": sum(1 for e in new if e.get("alias_of")),
                   "by_era_new": dict(Counter(str(e["era"]) for e in new)),
                   "retaken": sum(1 for r in rs if r["retaken"]), "flagged": len(flags),
                   "verbatim": sum(1 for e in new if e["stt"]["wer_scribe"] == 0),
                   "irony_new": sum(1 for e in new if e.get("delivery")),
                   "minutes_new": round(sum(e["duration_s"] for e in new) / 60, 1),
                   "chars_new": sum(len(e["text"]) for e in new)},
        "spend_usd": round(spend, 4), "spend_usd_audition": round(audition_spend(), 4),
        "spend_logged_usd": round(V.fal_api.logged_spend(G.BUDGET[0]), 3),
        "missing": missing, "voice_clashes_in_scene": clashes,
        "irony_direction": G.IRONY_DIRECTION.strip(), "skipped": json.loads((FULL / "lines.json").read_text(
            encoding="utf-8"))["skipped"],
        "lines": out,
    }
    (FULL / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    (FULL / "casting.json").write_text(json.dumps(casting, ensure_ascii=False, indent=1), encoding="utf-8")
    (FULL / "flags.json").write_text(json.dumps(flags, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(man["counts"], ensure_ascii=False), "spend", man["spend_usd"], "logged", man["spend_logged_usd"],
          "missing", len(missing), "clashes", clashes)
    return man


def install() -> None:
    """Copy all OGGs into the game, after re-checking every text against lines.json (run extract_full.py first, so
    lines.json holds the live text; a changed line must be regenerated before installing)."""
    man = json.loads((FULL / "manifest.json").read_text(encoding="utf-8"))
    live = {l["line_id"]: l["text"] for l in G.lines_all()}
    stale = [e["line_id"] for e in man["lines"] if live.get(e["line_id"]) != e["text"]]
    if stale:
        raise SystemExit(f"{len(stale)} lines changed since generation, not installing: {stale[:10]}")
    n = 0
    for e in man["lines"]:
        if e["source"] == "prologue":
            continue  # already in the game, unchanged
        shutil.copyfile(FULL / e["file"], G.GAME / f"{e['line_id']}.ogg")
        n += 1
    print("copied", n, "files to", G.GAME)
