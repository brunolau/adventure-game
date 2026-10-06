"""Retake chosen lines with an extra 'clear, unhurried' direction (short lines that both STT models misread).
Keeps the new take only when it scores better. usage: python retake.py <model_key> <line_id>...
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402
import gen_all  # noqa: E402
from casting import MODELS  # noqa: E402

CLEAR = " Pronounce every word fully and clearly, unhurried, with a small natural pause before the question."


def main() -> None:
    key, ids = sys.argv[1], sys.argv[2:]
    model, cast = MODELS[key]
    raw_dir = V.ROOT / "art/voice/raw" / key
    for lid in ids:
        rec = json.loads((raw_dir / f"{lid}.json").read_text(encoding="utf-8"))
        voice = dict(cast[rec["speaker"]])
        if "style" in voice:
            voice["style"] += CLEAR
        else:
            voice["speed"] = 0.92
        text = rec["tts_text"]
        for n in range(1, 4):
            t = rec["takes"] + 1
            res = V.tts(model, text, voice, f"voice/trial/{key}/{lid}#r{t}")
            raw = V.fal_api.download(res["url"], raw_dir / f"{lid}.t{t}{res['raw_ext']}")
            x = V.load_mono(raw)
            m = V.measure(x, text)
            sc = V.stt_scribe(res["url"], m["raw_s"], f"voice/trial/stt-scribe/{key}/{lid}#r{t}")
            wz = V.stt_wizper(res["url"], f"voice/trial/stt-wizper/{key}/{lid}#r{t}")
            r = {"take": t, "raw": raw.name, "measure": m, "stt_scribe": sc, "wer_scribe": V.wer(rec["text"], sc),
                 "stt_wizper": wz, "wer_wizper": V.wer(rec["text"], wz), "usd_tts": round(len(text) / 1000 * V.TTS_PRICE[model], 5),
                 "direction": CLEAR.strip()}
            r["score"] = round(gen_all.score(r), 3)
            rec["all_takes"].append(r)
            rec["takes"] = t
            print(lid, t, r["score"], sc, "|", wz)
            if r["score"] < rec["best"]["score"]:
                rec["best"] = r
                rec["voice_settings"] = voice
            if rec["best"]["score"] <= 0.15:
                break
        y, lufs, peak = V.finish(V.load_mono(raw_dir / rec["best"]["raw"]), phone=rec["phone"])
        V.write_ogg(V.ROOT / "art/voice/takes" / key / f"{lid}.ogg", y)
        rec.update(duration_s=round(len(y) / V.SR, 2), lufs=lufs, peak_dbtp=peak)
        (raw_dir / f"{lid}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
