"""Recast 2026-10-06: audition of Gemini stock voices for the four women (Ela, Dana, Mira 2020, Lenka).

One real line per role, spoken by each candidate voice with the role's v2 direction; every take is measured
(pitch, pitch range, timbre, aperiodicity = rasp/breath proxy, speaking rate) and checked once by Scribe.
Paid: ~15 short TTS calls + 15 Scribe calls (about $0.07). Results: art/voice/recast/audition/audition.json.

usage: python audition.py
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402
import voice_features as F  # noqa: E402
from casting import GEMINI_V2  # noqa: E402

MODEL = "google/gemini-3.8-flash-tts"
OUT = V.ROOT / "art/voice/recast/audition"
BUDGET = ("voice/recast/", 5.0)

ROLES = {
    "LENKA": ("topic.LENKA.extra 3.002", ["Leda", "Laomedeia", "Zephyr", "Autonoe", "Aoede"]),
    "ELA": ("topic.ELA.ambient 1.x01", ["Kore", "Pulcherrima", "Erinome", "Despina"]),
    "DANA": ("action.G03.x03", ["Sulafat", "Vindemiatrix", "Achernar"]),
    "MIRA20": ("topic.MIRA20.extra 1.006", ["Gacrux", "Vindemiatrix", "Achernar"]),
}


def one(role: str, lid: str, text: str, voice: str) -> dict:
    tag = f"{role}.{voice}"
    cache = OUT / f"{tag}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    style = GEMINI_V2[role]["style"]
    usd = len(text) / 1000 * V.TTS_PRICE[MODEL]
    res = V.fal_api.run(MODEL, {"prompt": text, "voice": voice, "style_instructions": style},
                        f"voice/recast/audition/{tag}", usd, budget=BUDGET, poll_s=1.0)
    url = res["audio"]["url"]
    raw = V.fal_api.download(url, OUT / f"{tag}.wav")
    x = V.load_mono(raw)
    m = V.measure(x, text)
    usd_stt = max(m["raw_s"], 1.0) / 60 * 0.008
    sc = V.fal_api.run(V.SCRIBE, {"audio_url": url, "language_code": "slk", "diarize": False,
                                  "tag_audio_events": False}, f"voice/recast/audition/stt/{tag}", usd_stt,
                       budget=BUDGET, poll_s=1.0).get("text", "").strip()
    y, lufs, peak = V.finish(x, phone=False)
    V.write_ogg(OUT / f"{tag}.ogg", y)
    r = {"role": role, "voice": voice, "line_id": lid, "text": text, "measure": m,
         "features": F.features(V.trim(x)), "stt_scribe": sc, "wer_scribe": V.wer(text, sc),
         "usd_tts": round(usd, 5), "usd_stt": round(usd_stt, 5)}
    cache.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    return r


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines = {l["line_id"]: l for l in json.loads((V.ROOT / "art/voice/trial/lines.json").read_text(encoding="utf-8"))["lines"]}
    jobs = [(role, lid, V.tts_text(lines[lid]["text"]), v) for role, (lid, vs) in ROLES.items() for v in vs]
    with ThreadPoolExecutor(max_workers=8) as pool:
        res = list(pool.map(lambda j: one(*j), jobs))
    for r in res:
        f = r["features"]
        print(f"{r['role']:7} {r['voice']:13} F0 {f['f0_median_hz']:6.1f} Hz  range {f['f0_range_semitones']:4.1f} st  "
              f"centroid {f['centroid_hz']:5d}  hi {f['hi_band_share']:.3f}  aper {f['aperiodicity']:.3f}  "
              f"{r['measure']['chars_per_s']:5.1f} c/s  WER {r['wer_scribe']['wer']:.2f}  | {r['stt_scribe']}")
    (OUT / "audition.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("usd", round(sum(r["usd_tts"] + r["usd_stt"] for r in res), 4))


if __name__ == "__main__":
    main()
