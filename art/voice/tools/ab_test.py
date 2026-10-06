"""A/B test: the same 6 lines (Adam, Ela, Mira, Jozef) with 3 Slovak-capable TTS models on fal.ai.

Per take: raw download, measurements (duration, silence, clipping, speaking rate), two speech-to-text round
trips (ElevenLabs Scribe v2 and Whisper v3 large via fal 'wizper') with word error rate, and a processed OGG
for listening. Output: art/voice/ab/<model>/<line_id>.*, art/voice/ab/ab_results.json.
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402
from casting import MODELS  # noqa: E402

AB = V.ROOT / "art" / "voice" / "ab"
LINES = ["entry.S03.001", "action.G07.001", "action.G02.002", "action.G05.001", "action.G04.x03", "action.Q2A.001"]


def take(model_key: str, line: dict) -> dict:
    model, cast = MODELS[model_key]
    voice = cast[line["speaker"]]
    text = V.tts_text(line["text"])
    lid = line["line_id"]
    out_dir = AB / model_key
    res = V.tts(model, text, voice, f"voice/ab/{model_key}/{lid}")
    raw = V.fal_api.download(res["url"], out_dir / f"{lid}{res['raw_ext']}")
    x = V.load_mono(raw)
    m = V.measure(x, text)
    scribe = V.stt_scribe(res["url"], m["raw_s"], f"voice/ab/stt-scribe/{model_key}/{lid}")
    wiz = V.stt_wizper(res["url"], f"voice/ab/stt-wizper/{model_key}/{lid}")
    y, lufs, peak = V.finish(x, phone=False)
    V.write_ogg(out_dir / f"{lid}.ogg", y)
    return {"model_key": model_key, "model": model, "voice": voice.get("voice"), "line_id": lid,
            "speaker": line["speaker"], "text": line["text"], "tts_text": text, "usd_tts": len(text) / 1000 * V.TTS_PRICE[model],
            "measure": m, "final_s": round(len(y) / V.SR, 2), "lufs": lufs, "peak": peak,
            "stt_scribe": scribe, "wer_scribe": V.wer(line["text"], scribe),
            "stt_wizper": wiz, "wer_wizper": V.wer(line["text"], wiz),
            "ogg": f"{model_key}/{lid}.ogg"}


def main() -> None:
    lines = {l["line_id"]: l for l in json.loads((V.ROOT / "art/voice/trial/lines.json").read_text(encoding="utf-8"))["lines"]}
    jobs = [(mk, lines[lid]) for mk in MODELS for lid in LINES]
    results = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = [pool.submit(take, mk, l) for mk, l in jobs]
        for f in futs:
            try:
                results.append(f.result())
            except Exception as e:  # report and continue
                print("FAILED", e)
    AB.mkdir(parents=True, exist_ok=True)
    (AB / "ab_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in results:
        print(r["model_key"], r["line_id"], r["measure"], "WER scribe", r["wer_scribe"]["wer"], "wizper", r["wer_wizper"]["wer"])
        print("   ", r["stt_scribe"], "|", r["stt_wizper"])


if __name__ == "__main__":
    main()
