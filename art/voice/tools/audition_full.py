"""Full voice-over (2026-10-07): audition of the child roles, young Mira and Zuzana at two ages.

For each role in casting_full.CHILD_CANDIDATES two real lines are spoken by every candidate stock voice with the
role's direction; each take is measured (pitch, pitch range, timbre, rate) and checked once by Scribe.
Results: art/voice/full/audition/audition.json (+ OGGs for the listening page).

usage: python audition_full.py
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402
import voice_features as F  # noqa: E402
from casting_full import CAST, CHILD_CANDIDATES  # noqa: E402

MODEL = "google/gemini-3.8-flash-tts"
OUT = V.ROOT / "art/voice/full/audition"
BUDGET = ("voice/full/", 15.0)


def pick_lines(lines: list[dict], spk: str, n: int = 2) -> list[dict]:
    own = [l for l in lines if l["speaker"] == spk and 45 <= len(l["text"]) <= 110]
    own.sort(key=lambda l: abs(len(l["text"]) - 75))
    if not own:  # ADAM10 has one short line only
        own = [l for l in lines if l["speaker"] == spk][:1]
    return own[:n]


def one(role: str, lid: str, text: str, voice: str, k: int) -> dict:
    tag = f"{role}.{voice}.{k}"
    cache = OUT / f"{tag}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    style = CAST[role]["style"]
    usd = len(text) / 1000 * V.TTS_PRICE[MODEL]
    res = V.fal_api.run(MODEL, {"prompt": text, "voice": voice, "style_instructions": style},
                        f"voice/full/audition/{tag}", usd, budget=BUDGET, poll_s=1.0)
    url = res["audio"]["url"]
    raw = V.fal_api.download(url, OUT / f"{tag}.wav")
    x = V.load_mono(raw)
    m = V.measure(x, text)
    usd_stt = max(m["raw_s"], 1.0) / 60 * 0.008
    sc = V.fal_api.run(V.SCRIBE, {"audio_url": url, "language_code": "slk", "diarize": False,
                                  "tag_audio_events": False}, f"voice/full/audition/stt/{tag}", usd_stt,
                       budget=BUDGET, poll_s=1.0).get("text", "").strip()
    y, lufs, peak = V.finish(x, phone=False)
    V.write_ogg(OUT / f"{tag}.ogg", y)
    r = {"role": role, "voice": voice, "k": k, "line_id": lid, "text": text, "measure": m,
         "features": F.features(V.trim(x)), "stt_scribe": sc, "wer_scribe": V.wer(text, sc),
         "usd_tts": round(usd, 5), "usd_stt": round(usd_stt, 5)}
    cache.write_text(json.dumps(r, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    return r


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines = json.loads((V.ROOT / "art/voice/full/lines.json").read_text(encoding="utf-8"))["lines"]
    jobs = []
    for role, voices in CHILD_CANDIDATES.items():
        for k, l in enumerate(pick_lines(lines, role)):
            for v in voices:
                jobs.append((role, l["line_id"], V.tts_text(l["text"]), v, k))
    print(len(jobs), "takes")
    with ThreadPoolExecutor(max_workers=10) as pool:
        res = list(pool.map(lambda j: one(*j), jobs))
    for r in sorted(res, key=lambda r: (r["role"], r["voice"], r["k"])):
        f = r["features"]
        print(f"{r['role']:9} {r['voice']:12} {r['k']} F0 {f['f0_median_hz']:6.1f} Hz range {f['f0_range_semitones']:4.1f} "
              f"st centroid {f['centroid_hz']:5d} {r['measure']['chars_per_s']:5.1f} c/s WER {r['wer_scribe']['wer']:.2f}"
              f" | {r['stt_scribe'][:70]}")
    (OUT / "audition.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print("usd", round(sum(r["usd_tts"] + r["usd_stt"] for r in res), 4))


if __name__ == "__main__":
    main()
