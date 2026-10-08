"""Full voice-over 2026-10-07: every spoken line not yet voiced (art/voice/full/lines.json, extract_full.py).

Same model, Slovak prompt and post-processing as the approved prologue (trial + recast): Gemini 3.8 Flash TTS with
the casting of casting_full.CAST, dry-irony direction on irony_full.IRONY, one ElevenLabs Scribe v2 check per take,
exactly one retake when the transcript differs in meaning (short lines get the clarity hint), the rest is flagged.
Post-processing: trim, DC, call/tape/device colour (fx), -16 LUFS (repeated until within 0.3 LU), soft limiter,
fades, OGG Vorbis q4 mono.

usage:
  python gen_full.py gen [--workers N] [--only ID ...] [--limit N]   take 1 + Scribe (resumable, cached per line)
  python gen_full.py report                                          differences after take 1 / retakes
  python gen_full.py retake [--all-flagged | ID ...]                 one retake per line (never a second one)
  python gen_full.py rerender                                        post-process every best take again (free)
  python gen_full.py finalize                                        art/voice/full/manifest.json + casting.json
  python gen_full.py install                                         copy all OGGs into src/game/assets/voice/
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402
import recast as R  # noqa: E402  (meaning_errors, check, score, CLEAR)
from casting import IRONY as IRONY_DIRECTION  # noqa: E402
from casting_full import CAST  # noqa: E402
from irony_full import IRONY  # noqa: E402

MODEL = "google/gemini-3.8-flash-tts"
BUDGET = ("voice/full/", 15.0)            # owner-approved cap for the full voice-over (USD)
ASSET = "voice/full/"                     # spend-log prefix of the calls; a later round uses its own scope and cap
#                                          (gen/retake --scope r2 --cap 3: prefix voice/full/r2/, cap USD 3)
FULL = V.ROOT / "art/voice/full"
RAW = V.ROOT / "art/voice/raw/full"
GAME = V.ROOT / "src/game/assets/voice"
DELIVERY_TEXT = "a touch of dry irony, understated"
# Retake of a longer line: the first take changed or dropped a word (e.g. dialect "jak" for "ako").
VERBATIM = " Say every word exactly as written, in standard Slovak; do not add, drop or change any word."

# Spoken forms the TTS needs (the subtitle text stays unchanged); the STT check accepts either form.
SPOKEN = {
    " = ": " rovná sa ",
    "Z-17": "zet sedemnásť",
    "K-17": "ká sedemnásť",
    "„cca“": "cé cé á",
    # look texts (2026-10-08, looks_full.py); none of these occurs in a dialogue line
    "ČSSR": "čé-es-es-er",
    "ZVONom": "Zvonom",
    "3 × 4": "tri krát štyri",
    "0–9": "nula až deväť",
    "9–17": "deväť až sedemnásť",
    "3–2–6": "tri – dva – šesť",
}


LEAL = re.compile(r"\bLEAL(\w*)")


def name_hint(text: str) -> str:
    """Phonetic hint for the retake of a line with the place name „Pri LEALe“ (owner 2026-10-07; declined pri LEALe,
    k LEALu, od LEALu). The subtitle text keeps the capitals; only the direction tells the voice how to say it."""
    forms = sorted({m.group(0) for m in LEAL.finditer(text)})
    return "".join(f" The place name „{w}“ is one ordinary word: say „{w.capitalize()}“ clearly with all its "
                   f"syllables (le-a-l{m.lower()}), as a separate word, never spelled letter by letter."
                   for w, m in ((w, w[4:]) for w in forms))


def spoken(text: str) -> str:
    t = text
    for a, b in SPOKEN.items():
        t = t.replace(a, b)
    return V.tts_text(t)


def lines_all() -> list[dict]:
    return json.loads((FULL / "lines.json").read_text(encoding="utf-8"))["lines"]


def todo(lines: list[dict]) -> list[dict]:
    return [l for l in lines if not l["prologue"]]


def voice_for(line: dict) -> dict:
    c = CAST[line["speaker"]]
    v = {"voice": c["voice"], "style": c["style"]}
    if line["line_id"] in IRONY:
        v["style"] += IRONY_DIRECTION
    return v


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


# --------------------------------------------------------------------------- audio colour

def _f(x, af):
    return V._ffmpeg_filter(x, af)


def colour(x: np.ndarray, fx: str | None) -> np.ndarray:
    if fx == "phone":      # the trial's telephone EQ (Mira by phone, Lea's voice message)
        return V.telephone(x)
    if fx == "radio":      # service channel / video call: lighter than the phone
        y = _f(x, "highpass=f=220:poles=2,lowpass=f=5200:poles=2,equalizer=f=2000:t=q:w=1.0:g=3")
        return np.tanh(y * 1.4) / np.tanh(1.4)
    if fx == "tape":       # the 1995 school cassette: band-limited, warm, a little saturation and faint hiss
        y = _f(x, "highpass=f=140:poles=2,lowpass=f=6500:poles=2,equalizer=f=250:t=q:w=1.0:g=2,"
                  "equalizer=f=3000:t=q:w=1.5:g=-2")
        y = np.tanh(y * 1.6) / np.tanh(1.6)
        rng = np.random.default_rng(7)
        hiss = _f(rng.standard_normal(len(y)).astype(np.float32) * 0.004, "highpass=f=3000")[: len(y)]
        return y + np.pad(hiss, (0, len(y) - len(hiss)))
    if fx == "device":     # device / station / robot: light band limit and presence, a hint of metal
        y = _f(x, "highpass=f=180:poles=2,lowpass=f=7000:poles=2,equalizer=f=2600:t=q:w=1.2:g=3")
        e = _f(y, "aecho=0.8:0.6:9:0.35")[: len(y)]
        e = np.pad(e, (0, len(y) - len(e)))
        return 0.85 * y + 0.15 * e
    return x


def finish(x: np.ndarray, fx: str | None, target: float = -16.0):
    x = V.trim(x)
    x = x - float(np.mean(x))
    x = colour(x, fx)
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


# --------------------------------------------------------------------------- takes

NUM = re.compile(r"^(nul|jed|jeden|jedn|dv|tri|styr|pat|ses|sest|sedem|osem|devat|desat|dvadsat|tridsat|"
                 r"siedm|osm|devia|desiat|styridsat|patdesiat|sestdesiat|sedemdesiat|osemdesiat|devatdesiat|sto|dvesto|tisic|prv|druh|tret)"
                 r"\w*$")
FILLERS = {"no", "a", "hm", "hmm", "nuz", "tak", "ehm", "aha", "oh", "ach", "eh", "nie", "ano"}


def classify(errs: list[tuple[str, str]]) -> tuple[list, list]:
    """Split recast.meaning_errors into real differences and minor ones (no retake, listed for the ear):
    numbers given back as digits (šesťdesiat / 60, 1995 / tisícdeväťsto...) are ignored; an inserted filler word
    ("No", "A", "Hm") is minor."""
    real, minor = [], []

    def same_sound(x: str, y: str) -> bool:  # STT spelling of the same sounds: y/i, d-t assimilation, Otto/Oto
        f = lambda w: w.replace("y", "i").replace("dt", "t").replace("tt", "t")
        return bool(x and y) and f(x) == f(y)
    for a, b in errs:
        if same_sound(a, b) or (b == "%" and a.startswith("percent")):
            continue
        if (b.isdigit() and (a == "" or NUM.match(a))) or (a.isdigit() and (b == "" or NUM.match(b))):
            continue
        if a == "" and b in FILLERS:
            minor.append((a, b))
            continue
        real.append((a, b))
    return real, minor


def _check(text: str, sc: str, m: dict) -> dict:
    c = R.check(text, sc, m)
    real, minor = classify(c["meaning_errors"])
    c["meaning_errors"], c["minor"] = real, minor
    c["ok"] = not real and not c["timing"]
    return c


def check(line: dict, sc: str, m: dict) -> dict:
    """Against the subtitle text and the spoken form; the one with fewer differences counts."""
    a = _check(line["text"], sc, m)
    sp = spoken(line["text"])
    if sp != V.tts_text(line["text"]):
        b = _check(sp, sc, m)
        if len(b["meaning_errors"]) < len(a["meaning_errors"]):
            return b
    return a


def take(line: dict, n: int, extra: str = "") -> dict:
    lid = line["line_id"]
    text = spoken(line["text"])
    voice = voice_for(line)
    voice["style"] += extra
    usd = len(text) / 1000 * V.TTS_PRICE[MODEL]
    res = V.fal_api.run(MODEL, {"prompt": text, "voice": voice["voice"], "style_instructions": voice["style"]},
                        f"{ASSET}gemini/{lid}#t{n}", usd, budget=BUDGET, poll_s=1.0)
    url = res["audio"]["url"]
    raw = V.fal_api.download(url, RAW / f"{lid}.t{n}.wav")
    x = V.load_mono(raw)
    m = {k: (float(v) if hasattr(v, "item") else v) for k, v in V.measure(x, text).items()}
    usd_stt = max(float(m["raw_s"]), 1.0) / 60 * 0.008
    sc = V.fal_api.run(V.SCRIBE, {"audio_url": url, "language_code": "slk", "diarize": False,
                                  "tag_audio_events": False}, f"{ASSET}stt-scribe/{lid}#t{n}", usd_stt,
                       budget=BUDGET, poll_s=1.0).get("text", "").strip()
    return {"take": n, "raw": raw.name, "measure": m, "stt_scribe": sc, "wer_scribe": V.wer(line["text"], sc),
            "check": check(line, sc, m), "usd_tts": round(usd, 5), "usd_stt": round(usd_stt, 5),
            **({"extra_direction": extra.strip()} if extra else {})}


def render(rec: dict) -> dict:
    x = V.load_mono(RAW / rec["best"]["raw"])
    y, lufs, peak = finish(x, rec.get("fx"))
    V.write_ogg(FULL / f"{rec['line_id']}.ogg", y)
    rec.update(duration_s=round(len(y) / V.SR, 2), lufs=float(lufs), peak_dbtp=float(peak))
    return rec


def new_record(line: dict) -> dict:
    lid = line["line_id"]
    v = voice_for(line)
    return {**line, "model": MODEL, "voice": v["voice"], "voice_settings": v,
            "delivery": DELIVERY_TEXT if lid in IRONY else None, "tts_text": spoken(line["text"]),
            "text_sha1": text_hash(line["text"]), "takes": 0, "all_takes": [], "best": None, "retaken": False}


def gen_one(line: dict) -> dict:
    cache = RAW / f"{line['line_id']}.json"
    if cache.exists():
        rec = json.loads(cache.read_text(encoding="utf-8"))
        if rec.get("text_sha1") == text_hash(line["text"]) and rec.get("voice_settings") == voice_for(line):
            if "duration_s" not in rec or not (FULL / f"{line['line_id']}.ogg").exists():
                render(rec)
                cache.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            return rec
        print("text or casting changed, regenerating:", line["line_id"])
    rec = new_record(line)
    t = take(line, 1)
    rec.update(takes=1, all_takes=[t], best=t)
    cache.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")  # paid take kept even if render fails
    render(rec)
    cache.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


def aliases(lines: list[dict]) -> dict[str, str]:
    """Same speaker, same text, same colour (e.g. Adam's line on the 1995 tape, played again in 2035): one take."""
    first, out = {}, {}
    for l in lines:
        k = (l["speaker"], l["text"], l["fx"])
        if k in first:
            out[l["line_id"]] = first[k]
        else:
            first[k] = l["line_id"]
    return out


def cmd_gen(a) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    lines = todo(lines_all())
    al = aliases(lines)
    lines = [l for l in lines if l["line_id"] not in al]
    if a.only:
        lines = [l for l in lines if l["line_id"] in a.only]
    if a.limit:
        lines = lines[: a.limit]
    print(len(lines), "lines to take,", sum(len(spoken(l["text"])) for l in lines), "chars;",
          f"logged spend so far ${V.fal_api.logged_spend(BUDGET[0]):.3f}")
    failed, done = [], 0
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs = {pool.submit(gen_one, l): l["line_id"] for l in lines}
        for f in as_completed(futs):
            lid = futs[f]
            try:
                f.result()
                done += 1
                if done % 100 == 0:
                    print(f"{done} done, spend ${V.fal_api.logged_spend(BUDGET[0]):.3f}", flush=True)
            except Exception as e:  # noqa: BLE001
                failed.append(lid)
                print("FAILED", lid, str(e)[:300], flush=True)
                if "budget" in str(e).lower() or "cap" in str(e).lower():
                    print("BUDGET CAP REACHED - stopping")
                    pool.shutdown(cancel_futures=True)
                    break
    print(f"{done} done, {len(failed)} failed: {failed[:20]}")
    cmd_report(a)


def records() -> list[dict]:
    out = []
    for l in todo(lines_all()):
        f = RAW / f"{l['line_id']}.json"
        if f.exists():
            out.append(json.loads(f.read_text(encoding="utf-8")))
    return out


def spend(recs: list[dict]) -> float:
    return sum(t["usd_tts"] + t["usd_stt"] for r in recs for t in r["all_takes"])


def cmd_recheck(a=None) -> None:
    """Re-run the free text check on every stored take, re-pick the best take (re-render when it changes)."""
    changed = 0
    for r in records():
        for t in r["all_takes"]:
            t["check"] = check(r, t["stt_scribe"], t["measure"])
        best = min(r["all_takes"], key=R.score)
        if best["take"] != r["best"]["take"]:
            changed += 1
            r["best"] = best
            render(r)
        else:
            r["best"] = best
        (RAW / f"{r['line_id']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print("best take changed for", changed)
    cmd_report()


def cmd_report(a=None) -> None:
    recs = records()
    bad = [r for r in recs if not r["best"]["check"]["ok"]]
    for r in bad:
        c = r["best"]["check"]
        print(f"{r['line_id']} [{r['speaker']}{' retaken' if r['retaken'] else ''}] {c['meaning_errors']} {c['timing']}\n"
              f"   script: {r['text']}\n   scribe: {r['best']['stt_scribe']}")
    exact = sum(1 for r in recs if r["best"]["wer_scribe"]["wer"] == 0)
    me = sum(1 for r in recs if r["best"]["check"]["meaning_errors"])
    print(f"{len(recs)} records, {exact} verbatim, {len(bad)} with differences ({me} meaning); "
          f"spend (per call) ${spend(recs):.4f}; logged ${V.fal_api.logged_spend(BUDGET[0]):.4f}")


def cmd_retake(a) -> None:
    lines = {l["line_id"]: l for l in lines_all()}
    if a.all_flagged:
        ids = [r["line_id"] for r in records() if r["best"]["check"]["meaning_errors"] and not r["retaken"]]
    else:
        ids = a.ids
    print(len(ids), "retakes")

    def one(lid: str) -> None:
        f = RAW / f"{lid}.json"
        rec = json.loads(f.read_text(encoding="utf-8"))
        if rec["retaken"]:
            print("already retaken once:", lid)
            return
        short = len(V.norm_words(rec["text"])) <= 6
        t = take(lines[lid], rec["takes"] + 1, (R.CLEAR if short else VERBATIM) + name_hint(rec["text"]))
        rec["all_takes"].append(t)
        rec["takes"] += 1
        rec["retaken"] = True
        if R.score(t) < R.score(rec["best"]):
            rec["best"] = t
            render(rec)
        print(lid, "-> take", rec["best"]["take"], "|", t["stt_scribe"], t["check"]["meaning_errors"], flush=True)
        f.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    with ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(one, ids))
    cmd_report()


def cmd_rerender(a) -> None:
    recs = records()

    def one(r: dict) -> None:
        render(r)
        (RAW / f"{r['line_id']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(one, recs))
    lu = [r["lufs"] for r in recs]
    print(f"{len(recs)} rendered; LUFS {min(lu)} .. {max(lu)}; peak max {max(r['peak_dbtp'] for r in recs)} dBTP")


def cmd_finalize(a) -> None:
    from manifest_full import build
    build()


def cmd_install(a) -> None:
    from manifest_full import install
    install()


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen")
    g.add_argument("--workers", type=int, default=12)
    g.add_argument("--only", nargs="*")
    g.add_argument("--limit", type=int, default=0)
    sub.add_parser("report")
    for sp in (g,):
        sp.add_argument("--scope", default="", help="own spend-log scope voice/full/<scope>/ with its own --cap")
        sp.add_argument("--cap", type=float, default=0.0)
    sub.add_parser("rerender")
    sub.add_parser("recheck")
    r = sub.add_parser("retake")
    r.add_argument("ids", nargs="*")
    r.add_argument("--all-flagged", action="store_true")
    r.add_argument("--scope", default="")
    r.add_argument("--cap", type=float, default=0.0)
    sub.add_parser("finalize")
    sub.add_parser("install")
    a = ap.parse_args()
    if getattr(a, "scope", ""):
        global ASSET, BUDGET
        if not a.cap:
            raise SystemExit("--scope needs --cap")
        ASSET = f"voice/full/{a.scope.strip('/')}/"
        BUDGET = (ASSET, a.cap)
        print("spend scope", ASSET, "cap", a.cap, "logged so far", round(V.fal_api.logged_spend(ASSET), 4))
    {"gen": cmd_gen, "report": cmd_report, "rerender": cmd_rerender, "recheck": cmd_recheck, "retake": cmd_retake,
     "finalize": cmd_finalize, "install": cmd_install}[a.cmd](a)


if __name__ == "__main__":
    main()
