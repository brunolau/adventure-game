"""Generate every scoped prologue line with one model, check it by two STT round trips, retake bad takes,
post-process to OGG. Resumable: one JSON per line in art/voice/raw/<model>/.

usage: python gen_all.py <model_key> [--workers N]
outputs: art/voice/raw/<model>/<line_id>.{mp3|wav,json}, art/voice/takes/<model>/<line_id>.ogg
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402
from casting import MODELS  # noqa: E402

MAX_TAKES = 3


def score(r: dict) -> float:
    """Lower is better: mean diacritics-insensitive WER of the two STT models plus timing penalties."""
    s = (r["wer_scribe"]["wer_nodiac"] + r["wer_wizper"]["wer_nodiac"]) / 2
    m = r["measure"]
    if m.get("longest_pause_s", 0) > 1.4:
        s += 0.2
    if not 6 <= m.get("chars_per_s", 12) <= 22:
        s += 0.2
    return s


def one(model_key: str, line: dict, raw_dir: Path, take_dir: Path) -> dict:
    lid = line["line_id"]
    cache = raw_dir / f"{lid}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    model, cast = MODELS[model_key]
    voice = cast[line["speaker"]]
    text = V.tts_text(line["text"])
    best = None
    takes = []
    for n in range(1, MAX_TAKES + 1):
        res = V.tts(model, text, voice, f"voice/trial/{model_key}/{lid}#t{n}")
        raw = V.fal_api.download(res["url"], raw_dir / f"{lid}.t{n}{res['raw_ext']}")
        x = V.load_mono(raw)
        m = V.measure(x, text)
        sc = V.stt_scribe(res["url"], m["raw_s"], f"voice/trial/stt-scribe/{model_key}/{lid}#t{n}")
        wz = V.stt_wizper(res["url"], f"voice/trial/stt-wizper/{model_key}/{lid}#t{n}")
        r = {"take": n, "raw": raw.name, "measure": m, "stt_scribe": sc, "wer_scribe": V.wer(line["text"], sc),
             "stt_wizper": wz, "wer_wizper": V.wer(line["text"], wz),
             "usd_tts": round(len(text) / 1000 * V.TTS_PRICE[model], 5)}
        r["score"] = round(score(r), 3)
        takes.append(r)
        if best is None or r["score"] < best["score"]:
            best = r
        # good enough: at least one STT reads it (almost) verbatim and timing is sane
        if min(r["wer_scribe"]["wer_nodiac"], r["wer_wizper"]["wer_nodiac"]) <= 0.1 and r["score"] < 0.2:
            break
    x = V.load_mono(raw_dir / best["raw"])
    y, lufs, peak = V.finish(x, phone=line["phone"])
    V.write_ogg(take_dir / f"{lid}.ogg", y)
    out = {**line, "model": model, "model_key": model_key, "voice": voice.get("voice"), "voice_settings": voice,
           "tts_text": text, "duration_s": round(len(y) / V.SR, 2), "lufs": lufs, "peak_dbtp": peak,
           "best": best, "takes": len(takes), "all_takes": takes}
    cache.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("model_key", choices=list(MODELS))
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--reverse", action="store_true", help="work from the end (a second process can share the job)")
    a = ap.parse_args()
    lines = json.loads((V.ROOT / "art/voice/trial/lines.json").read_text(encoding="utf-8"))["lines"]
    if a.model_key == "gemini":
        # Recast 2026-10-06: Adam, Roman, the four women and the dry-irony lines use casting.GEMINI_V2 + IRONY;
        # regenerate those with recast.py, never with the v1 casting here.
        import recast
        rec = {l["line_id"] for l in recast.to_regen(lines)}
        skipped = [l["line_id"] for l in lines if l["line_id"] in rec and (not a.only or l["line_id"] in a.only)]
        if skipped:
            print(f"skipping {len(skipped)} recast lines (use recast.py gen --only ...):", skipped[:5], "...")
        lines = [l for l in lines if l["line_id"] not in rec]
    if a.only:
        lines = [l for l in lines if l["line_id"] in a.only]
    if a.reverse:
        lines = lines[::-1]
    raw_dir = V.ROOT / "art/voice/raw" / a.model_key
    take_dir = V.ROOT / "art/voice/takes" / a.model_key
    raw_dir.mkdir(parents=True, exist_ok=True)
    take_dir.mkdir(parents=True, exist_ok=True)
    done, failed = [], []
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs = {pool.submit(one, a.model_key, l, raw_dir, take_dir): l["line_id"] for l in lines}
        for f, lid in futs.items():
            try:
                done.append(f.result())
            except Exception as e:
                failed.append(lid)
                print("FAILED", lid, str(e)[:300])
    bad = [d for d in done if d["best"]["score"] > 0.15]
    print(f"{a.model_key}: {len(done)} ok, {len(failed)} failed, {len(bad)} still doubtful")
    for d in bad:
        print("  ", d["line_id"], d["best"]["score"], d["text"], "|", d["best"]["stt_scribe"], "|", d["best"]["stt_wizper"])
    print("spent voice/:", round(V.fal_api.logged_spend("voice/"), 3))


if __name__ == "__main__":
    main()
