"""Recast 2026-10-06 of the prologue voice trial (owner feedback after listening).

1. Adam <-> Roman voices swapped; the four women recast (casting.GEMINI_V2, chosen by audition.py).
2. Lines classified as dry irony / sarcasm (DELIVERY) get casting.IRONY appended to the style prompt.
3. Only lines whose voice or delivery changed are regenerated: one Gemini take each, one Scribe v2 check
   (no Whisper); `retake` gives a chosen line exactly one more take and keeps the better one.
4. `finalize` writes art/voice/trial/<id>.ogg + manifest.json (voice, delivery, version, before file) and
   `install` copies the regenerated OGGs to src/game/assets/voice/.

usage:
  python recast.py gen [--workers N]        take 1 + Scribe for every line to regenerate (resumable)
  python recast.py report                   mismatches / timing outliers after take 1 (and after retakes)
  python recast.py retake <line_id>...      one retake per line (never a second one)
  python recast.py finalize                 trial folder + manifest
  python recast.py install                  copy the regenerated OGGs into the game
"""
from __future__ import annotations

import argparse
import json

import shutil
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402
from casting import GEMINI, GEMINI_V2, IRONY  # noqa: E402

MODEL = "google/gemini-3.8-flash-tts"
BUDGET = ("voice/recast/", 5.0)          # owner-approved cap for the recast (USD)
TRIAL = V.ROOT / "art/voice/trial"
RAW = V.ROOT / "art/voice/raw/gemini_v2"
TAKES = V.ROOT / "art/voice/takes/gemini_v2"
BEFORE = V.ROOT / "art/voice/takes/gemini_v1"   # frozen copies of the v1 trial files of every regenerated line
GAME = V.ROOT / "src/game/assets/voice"
RECAST_SPEAKERS = {"ADAM", "ROMAN", "ELA", "DANA", "MIRA20", "LENKA"}
DELIVERY_TEXT = "a touch of dry irony, understated"
# Retakes of short lines (<= 6 words, the weak spot of every TTS) add the clarity direction used in the v1 trial.
CLEAR = " Pronounce every word fully and clearly, unhurried."

# Lines read as dry irony / sarcasm (line_id -> kind). Everything else keeps its neutral character direction.
DELIVERY = {
    # Adam: self-irony and dry quips
    "entry.S01.001": "self-irony", "action.G01.001": "self-irony", "topic.ROMAN.extra 2.003": "ironic question",
    "action.Q1A.x04": "mock-serious", "topic.LENKA.ambient 1.003": "mock-serious", "action.G02.003": "dry comeback",
    "topic.ELA.extra 2.003": "dry joke", "topic.ELA.extra 2.005": "ironic remark", "topic.ELA.extra 3.005": "dry remark",
    "action.G03.x04": "ironic request", "topic.DANA.ambient 1.003": "plays along", "topic.DANA.ambient 2.002": "self-irony",
    "entry.S06.001": "wry observation", "action.G05.x01": "dry comeback", "action.G05.x05": "dry tease",
    "topic.MIRA20.ambient 1.003": "tease", "topic.MIRA20.ambient 2.002": "sceptical question",
    "action.G06.001": "self-irony", "entry.S07.001": "wry observation", "entry.S08.001": "wry observation",
    "action.Q1B.001": "dry remark", "action.Q1C.001": "dry remark", "action.Q1C.004": "dry comeback",
    "action.Q1C.x02": "dry suggestion", "entry.S09.001": "ironic contrast", "entry.S10.001": "self-irony",
    "action.G08.002": "understatement", "action.G09.002": "understatement", "action.G10.003": "dry joke",
    "action.G11.002": "dry joke", "cutscene.CS01.02.002": "self-irony (running gag)",
    "cutscene.CS01.03.001": "understatement",
    # Mira: dry comebacks
    "action.G04.x03": "dry comeback", "action.G05.x02": "dry correction", "action.G05.x04": "dry tease",
    "topic.MIRA20.ambient 1.x01": "dry comeback", "topic.MIRA20.ambient 1.x03": "dry comeback",
    "topic.MIRA20.ambient 2.003": "dry comeback", "topic.MIRA20.ambient 2.x02": "dry comeback",
    "topic.MIRA20.extra 1.004": "dry comeback", "topic.MIRA20.extra 2.004": "dry remark",
    # Ela: dry comebacks
    "action.G02.x03": "dry comeback", "action.G02.004": "dry comeback", "action.G02.x05": "dry comeback",
    "topic.ELA.ambient 1.x01": "dry comeback", "topic.ELA.ambient 1.x03": "dry comeback",
    "topic.ELA.ambient 2.x02": "dry remark", "topic.ELA.ambient 2.x04": "dry comeback",
    "topic.ELA.extra 1.006": "dry remark", "topic.ELA.extra 2.002": "dry remark", "topic.ELA.extra 3.004": "dry remark",
    "topic.ELA.extra 3.006": "dry comeback", "action.Q2B.x03": "dry remark",
    # Dana: deadpan comebacks
    "action.G03.004": "dry remark", "topic.DANA.ambient 1.x01": "dry comeback", "topic.DANA.ambient 1.x03": "dry comeback",
    "topic.DANA.extra 1.004": "dry comeback", "topic.DANA.extra 3.004": "ironic understatement",
    # Lenka: amused dry remarks
    "action.Q1A.001": "dry remark", "action.Q1A.x02": "dry remark", "topic.LENKA.extra 1.004": "dry resignation",
    "topic.LENKA.extra 2.004": "tease", "action.Q1C.x03": "deadpan",
    # Roman: wry, never cynical
    "topic.ROMAN.ambient 1.x01": "wry remark", "topic.ROMAN.ambient 2.x02": "wry remark", "topic.ROMAN.extra 2.004": "wry remark",
    # Jozef: gentle irony about technology
    "action.Q2A.x02": "dry irony", "topic.JOZEF.ambient 1.x03": "dry irony", "action.Q2C.003": "dry irony",
}

# STT spellings that do not change the meaning (checked by hand on the v1 trial): voicing assimilation in "Bodka",
# numbers given back as digits.
BENIGN = {("bodka", "botka"), ("bodku", "botku"), ("bodkovi", "botkovi"), ("bodkova", "botkova"),
          ("bodkom", "botkom"), ("deviatej", "9"), ("siedmej", "7"), ("osmej", "8"), ("siestej", "6"),
          ("desiatej", "10")}


def lines_all() -> list[dict]:
    return json.loads((TRIAL / "lines.json").read_text(encoding="utf-8"))["lines"]


def to_regen(lines: list[dict]) -> list[dict]:
    return [l for l in lines if l["speaker"] in RECAST_SPEAKERS or l["line_id"] in DELIVERY]


def voice_for(line: dict) -> dict:
    v = dict(GEMINI_V2[line["speaker"]])
    if line["line_id"] in DELIVERY:
        v["style"] = v["style"] + IRONY
    return v


def _nd(w: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", w) if unicodedata.category(c) != "Mn")


def meaning_errors(text: str, hyp: str) -> list[tuple[str, str]]:
    """Word errors left after ignoring diacritics, punctuation and the BENIGN spellings; '1995' as digits is fine."""
    ref = [_nd(w) for w in V.norm_words(text)]
    hy = [_nd(w) for w in V.norm_words(hyp)]
    _, ops = V.edit_ops(ref, hy)
    ops = [(a, b) for a, b in ops if (a, b) not in BENIGN and not (a.isdigit() and a == b)]
    # word-boundary differences ("po obede" / "poobede", "balitu" / "bali tu"): a run of edit ops whose joined words
    # are equal on both sides is not an error. Runs are found on the full alignment, so rebuild it with positions.
    out, i = [], 0
    while i < len(ops):
        for j in range(min(len(ops), i + 4), i, -1):
            run = ops[i:j]
            if len(run) > 1 and "".join(a for a, _ in run) == "".join(b for _, b in run):
                i = j
                break
        else:
            out.append(ops[i])
            i += 1
    return out


def check(text: str, sc: str, m: dict) -> dict:
    errs = meaning_errors(text, sc)
    timing = []
    if m.get("longest_pause_s", 0) > 1.4:
        timing.append(f"pause {m['longest_pause_s']} s")
    if not 7 <= m.get("chars_per_s", 12) <= 22:
        timing.append(f"rate {m['chars_per_s']} chars/s")
    return {"meaning_errors": errs, "timing": timing, "ok": not errs and not timing}


def take(line: dict, n: int, extra: str = "") -> dict:
    lid = line["line_id"]
    text = V.tts_text(line["text"])
    voice = voice_for(line)
    voice["style"] += extra
    usd = len(text) / 1000 * V.TTS_PRICE[MODEL]
    res = V.fal_api.run(MODEL, {"prompt": text, "voice": voice["voice"], "style_instructions": voice["style"]},
                        f"voice/recast/gemini/{lid}#t{n}", usd, budget=BUDGET, poll_s=1.0)
    url = res["audio"]["url"]
    raw = V.fal_api.download(url, RAW / f"{lid}.t{n}.wav")
    x = V.load_mono(raw)
    m = V.measure(x, text)
    usd_stt = max(float(m["raw_s"]), 1.0) / 60 * 0.008
    sc = V.fal_api.run(V.SCRIBE, {"audio_url": url, "language_code": "slk", "diarize": False,
                                  "tag_audio_events": False}, f"voice/recast/stt-scribe/{lid}#t{n}", usd_stt,
                       budget=BUDGET, poll_s=1.0).get("text", "").strip()
    m = {k: (float(v) if hasattr(v, "item") else v) for k, v in m.items()}
    return {"take": n, "raw": raw.name, "measure": m, "stt_scribe": sc, "wer_scribe": V.wer(line["text"], sc),
            "check": check(line["text"], sc, m), "usd_tts": round(usd, 5), "usd_stt": round(usd_stt, 5),
            **({"extra_direction": extra.strip()} if extra else {})}


def finish(x, phone: bool, target: float = -16.0):
    """voice_lib.finish (trim, DC, phone EQ, -16 LUFS with a soft limiter at -1.5 dBFS, fades) with the loudness step
    repeated until the line is within 0.3 LU of the target: Adam's new voice is peaky, so one pass through the
    limiter left many of his lines at -17 to -19 LUFS."""
    x = V.trim(x)
    x = x - float(np.mean(x))
    if phone:
        x = V.telephone(x)
    st, lufs, peak = V.audio_lib.normalize(x[:, None], target, max_peak_db=-1.5, sr=V.SR)
    for _ in range(4):
        if lufs >= target - 0.3:
            break
        st, lufs, peak = V.audio_lib.normalize(st, target, max_peak_db=-1.5, sr=V.SR)
    y = st[:, 0]
    fi, fo = int(0.008 * V.SR), int(0.04 * V.SR)
    y[:fi] *= np.linspace(0, 1, fi)
    y[-fo:] *= np.linspace(1, 0, fo)
    return y, lufs, peak


def render(rec: dict) -> dict:
    x = V.load_mono(RAW / rec["best"]["raw"])
    y, lufs, peak = finish(x, phone=rec["phone"])
    V.write_ogg(TAKES / f"{rec['line_id']}.ogg", y)
    rec.update(duration_s=round(len(y) / V.SR, 2), lufs=lufs, peak_dbtp=peak)
    return rec


def gen_one(line: dict) -> dict:
    lid = line["line_id"]
    cache = RAW / f"{lid}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    t = take(line, 1)
    rec = {**line, "model": MODEL, "voice": voice_for(line)["voice"], "voice_settings": voice_for(line),
           "delivery": DELIVERY_TEXT if lid in DELIVERY else None, "delivery_kind": DELIVERY.get(lid),
           "tts_text": V.tts_text(line["text"]), "takes": 1, "all_takes": [t], "best": t, "retaken": False}
    render(rec)
    cache.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


def score(t: dict) -> tuple:
    c = t["check"]
    return (len(c["meaning_errors"]), len(c["timing"]), t["wer_scribe"]["wer_nodiac"], t["wer_scribe"]["wer"])


def cmd_gen(a) -> None:
    lines = to_regen(lines_all())
    if a.only:
        lines = [l for l in lines if l["line_id"] in a.only]
    for d in (RAW, TAKES, BEFORE):
        d.mkdir(parents=True, exist_ok=True)
    for l in lines:  # freeze the v1 file before anything replaces it
        b = BEFORE / f"{l['line_id']}.ogg"
        if not b.exists():
            shutil.copyfile(TRIAL / f"{l['line_id']}.ogg", b)
    failed = []
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs = {pool.submit(gen_one, l): l["line_id"] for l in lines}
        for f, lid in futs.items():
            try:
                f.result()
            except Exception as e:  # noqa: BLE001
                failed.append(lid)
                print("FAILED", lid, str(e)[:300])
    print(f"{len(lines) - len(failed)} done, {len(failed)} failed")
    cmd_report(a)


def records() -> list[dict]:
    out = []
    for l in to_regen(lines_all()):
        f = RAW / f"{l['line_id']}.json"
        if f.exists():
            out.append(json.loads(f.read_text(encoding="utf-8")))
    return out


def spend(recs: list[dict]) -> float:
    return sum(t["usd_tts"] + t["usd_stt"] for r in recs for t in r["all_takes"])


def cmd_report(a=None) -> None:
    recs = records()
    bad = [r for r in recs if not r["best"]["check"]["ok"]]
    for r in bad:
        c = r["best"]["check"]
        print(f"{r['line_id']} [{r['speaker']}{' retaken' if r['retaken'] else ''}] {c['meaning_errors']} {c['timing']}\n"
              f"   script: {r['text']}\n   scribe: {r['best']['stt_scribe']}")
    exact = sum(1 for r in recs if r["best"]["wer_scribe"]["wer"] == 0)
    print(f"{len(recs)} records, {exact} verbatim, {len(bad)} with differences; "
          f"recast spend ${spend(recs):.4f}")


def cmd_retake(a) -> None:
    lines = {l["line_id"]: l for l in lines_all()}

    def one(lid: str) -> None:
        f = RAW / f"{lid}.json"
        rec = json.loads(f.read_text(encoding="utf-8"))
        if rec["retaken"]:
            print("already retaken once:", lid)
            return
        short = len(V.norm_words(rec["text"])) <= 6
        t = take(lines[lid], rec["takes"] + 1, CLEAR if short else "")
        rec["all_takes"].append(t)
        rec["takes"] += 1
        rec["retaken"] = True
        if score(t) < score(rec["best"]):
            rec["best"] = t
            render(rec)
        print(lid, "-> take", rec["best"]["take"], "|", t["stt_scribe"], t["check"])
        f.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(one, a.ids))


def cmd_rerender(a) -> None:
    """Post-process every best take again from its raw WAV (free)."""
    recs = records()

    def one(r: dict) -> None:
        render(r)
        (RAW / f"{r['line_id']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(one, recs))
    lu = [r["lufs"] for r in recs]
    pk = [r["peak_dbtp"] for r in recs]
    print(f"{len(recs)} rendered; LUFS {min(lu)} .. {max(lu)}; peak max {max(pk)} dBTP")


def cmd_recheck(a) -> None:
    """Re-run the (free) text check on every stored take and re-pick the best take; re-render when it changes."""
    changed = 0
    for r in records():
        for t in r["all_takes"]:
            t["check"] = check(r["text"], t["stt_scribe"], t["measure"])
        best = min(r["all_takes"], key=score)
        if best["take"] != r["best"]["take"]:
            changed += 1
            r["best"] = best
            render(r)
        else:
            r["best"] = best
        (RAW / f"{r['line_id']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print("best take changed for", changed)
    cmd_report()


def cmd_finalize(a) -> None:
    man = json.loads((TRIAL / "manifest.json").read_text(encoding="utf-8"))
    recs = {r["line_id"]: r for r in records()}
    flags = json.loads(a.flags.read_text(encoding="utf-8")) if a.flags and a.flags.exists() else {}
    for l in man["lines"]:
        lid = l["line_id"]
        r = recs.get(lid)
        l["delivery"] = DELIVERY_TEXT if lid in DELIVERY else None
        if r is None:
            l.setdefault("version", 1)
            continue
        if "before" not in l:
            l["before"] = {"version": 1, "voice": l["voice"], "file": f"../takes/gemini_v1/{lid}.ogg",
                           "duration_s": l["duration_s"], "stt": l["stt"]}
        shutil.copyfile(TAKES / f"{lid}.ogg", TRIAL / f"{lid}.ogg")
        b = r["best"]
        l.update({"text": r["text"], "tts_text": r["tts_text"],
                  "version": 2, "recast": "2026-10-06", "voice": r["voice"], "delivery_kind": r["delivery_kind"],
                  "style_instructions": r["voice_settings"]["style"], "duration_s": r["duration_s"],
                  "lufs": r["lufs"], "peak_dbtp": r["peak_dbtp"], "takes": r["takes"],
                  "stt": {"scribe_v2": b["stt_scribe"], "wer_scribe": b["wer_scribe"]["wer"],
                          "wer_scribe_nodiac": b["wer_scribe"]["wer_nodiac"],
                          "errors_scribe": b["wer_scribe"]["errors"], "meaning_errors": b["check"]["meaning_errors"],
                          "timing": b["check"]["timing"], "ok": lid not in flags, "flag": flags.get(lid)}})
    cast = {sp: {"voice": v["voice"], "style": v["style"], "v1_voice": GEMINI[sp]["voice"]} for sp, v in GEMINI_V2.items()}
    rs = list(recs.values())
    man["version"] = 2
    man["versions"] = {"1": "trial 2026-10-06 (237 lines, Gemini 3.8 Flash TTS)",
                       "2": "recast 2026-10-06: Adam/Roman voices swapped, women recast, dry-irony delivery"}
    man["recast"] = {
        "date": "2026-10-06", "casting": cast, "irony_direction": IRONY.strip(), "delivery_text": DELIVERY_TEXT,
        "delivery_lines": [{"line_id": k, "speaker": next(x["speaker"] for x in man["lines"] if x["line_id"] == k),
                            "kind": v} for k, v in DELIVERY.items()],
        "regenerated": len(rs), "retaken": sum(1 for r in rs if r["retaken"]),
        "flagged": [{"line_id": k, "why": v} for k, v in flags.items()],
        "stt": "ElevenLabs Scribe v2 only (no Whisper)",
        "spend_usd": round(spend(rs) + audition_spend(), 4), "spend_usd_audition": round(audition_spend(), 4),
        "before_dir": "art/voice/takes/gemini_v1/",
    }
    (TRIAL / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print("manifest v2:", len(rs), "regenerated,", len(DELIVERY), "irony lines,", len(flags), "flagged,",
          f"spend ${man['recast']['spend_usd']:.4f}")


def audition_spend() -> float:
    f = V.ROOT / "art/voice/recast/audition/audition.json"
    if not f.exists():
        return 0.0
    return sum(r["usd_tts"] + r["usd_stt"] for r in json.loads(f.read_text(encoding="utf-8")))


def cmd_install(a) -> None:
    n = 0
    for r in records():
        shutil.copyfile(TRIAL / f"{r['line_id']}.ogg", GAME / f"{r['line_id']}.ogg")
        n += 1
    print("copied", n, "files to", GAME)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen")
    g.add_argument("--workers", type=int, default=8)
    g.add_argument("--only", nargs="*")
    sub.add_parser("report")
    sub.add_parser("recheck")
    sub.add_parser("rerender")
    r = sub.add_parser("retake")
    r.add_argument("ids", nargs="+")
    f = sub.add_parser("finalize")
    f.add_argument("--flags", type=Path, default=V.ROOT / "art/voice/recast/flags.json")
    sub.add_parser("install")
    a = ap.parse_args()
    {"gen": cmd_gen, "report": cmd_report, "recheck": cmd_recheck, "rerender": cmd_rerender, "retake": cmd_retake, "finalize": cmd_finalize,
     "install": cmd_install}[a.cmd](a)


if __name__ == "__main__":
    main()
