"""Pick the trial model, copy its takes to art/voice/trial/<line_id>.ogg and write art/voice/trial/manifest.json
(plus per-model statistics used by the listening page and TRIAL.md).

usage: python finalize.py <chosen_model_key>
"""
from __future__ import annotations

import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402
from casting import MODELS  # noqa: E402

TRIAL = V.ROOT / "art/voice/trial"


def model_stats(key: str, lines: list[dict]) -> dict | None:
    raw = V.ROOT / "art/voice/raw" / key
    recs = []
    for l in lines:
        f = raw / f"{l['line_id']}.json"
        if f.exists():
            recs.append(json.loads(f.read_text(encoding="utf-8")))
    if not recs:
        return None
    words = sum(r["best"]["wer_scribe"]["ref_words"] for r in recs)

    def wsum(field: str, sub: str) -> float:
        return round(sum(r["best"][field][sub] * r["best"][field]["ref_words"] for r in recs) / words, 4)
    first = [r["all_takes"][0] for r in recs]
    words_first = sum(t["wer_scribe"]["ref_words"] for t in first)
    usd_tts = sum(t["usd_tts"] for r in recs for t in r["all_takes"])
    return {
        "model": MODELS[key][0], "lines": len(recs), "words": words,
        "wer_scribe": wsum("wer_scribe", "wer"), "wer_scribe_nodiac": wsum("wer_scribe", "wer_nodiac"),
        "wer_wizper": wsum("wer_wizper", "wer"), "wer_wizper_nodiac": wsum("wer_wizper", "wer_nodiac"),
        "first_take_wer_scribe": round(sum(t["wer_scribe"]["wer"] * t["wer_scribe"]["ref_words"] for t in first) / words_first, 4),
        "first_take_wer_wizper": round(sum(t["wer_wizper"]["wer"] * t["wer_wizper"]["ref_words"] for t in first) / words_first, 4),
        "lines_exact_scribe": sum(1 for r in recs if r["best"]["wer_scribe"]["wer"] == 0),
        "retakes": sum(r["takes"] - 1 for r in recs),
        "doubtful": [r["line_id"] for r in recs if r["best"]["score"] > 0.15],
        "audio_s": round(sum(r["duration_s"] for r in recs), 1),
        "chars": sum(len(r["tts_text"]) for r in recs),
        "usd_tts": round(usd_tts, 4),
        "mean_chars_per_s": round(sum(r["best"]["measure"]["chars_per_s"] for r in recs) / len(recs), 1),
        "max_pause_s": max(r["best"]["measure"]["longest_pause_s"] for r in recs),
        "clipped_lines": sum(1 for r in recs if r["best"]["measure"]["clip_frac"] > 0.0005),
    }


def main() -> None:
    chosen = sys.argv[1]
    cur = TRIAL / "manifest.json"
    if cur.exists() and json.loads(cur.read_text(encoding="utf-8")).get("version") == 2 and "--force-v1" not in sys.argv:
        sys.exit("manifest.json is the recast v2: this script would put the v1 takes back. Use recast.py finalize "
                 "(after gen_all.py for Jozef/SYSTEM lines, copy their takes/gemini OGG by hand) or pass --force-v1.")
    data = json.loads((TRIAL / "lines.json").read_text(encoding="utf-8"))
    lines = data["lines"]
    stats = {k: s for k in MODELS if (s := model_stats(k, lines))}
    manifest = []
    for l in lines:
        r = json.loads((V.ROOT / "art/voice/raw" / chosen / f"{l['line_id']}.json").read_text(encoding="utf-8"))
        shutil.copyfile(V.ROOT / "art/voice/takes" / chosen / f"{l['line_id']}.ogg", TRIAL / f"{l['line_id']}.ogg")
        b = r["best"]
        manifest.append({
            "line_id": l["line_id"], "speaker": l["speaker"], "text": l["text"], "tts_text": r["tts_text"],
            "scene": l["scene"], "scene_name": l["scene_name"], "block": l["block"], "block_label": l["block_label"],
            "model": r["model"], "voice": r["voice"], "phone_eq": l["phone"],
            "duration_s": r["duration_s"], "lufs": r["lufs"], "peak_dbtp": r["peak_dbtp"], "takes": r["takes"],
            "stt": {"scribe_v2": b["stt_scribe"], "wer_scribe": b["wer_scribe"]["wer"],
                    "whisper_v3": b["stt_wizper"], "wer_whisper": b["wer_wizper"]["wer"],
                    "wer_nodiac_mean": round((b["wer_scribe"]["wer_nodiac"] + b["wer_wizper"]["wer_nodiac"]) / 2, 3),
                    "errors_scribe": b["wer_scribe"]["errors"], "errors_whisper": b["wer_wizper"]["errors"],
                    "ok": b["score"] <= 0.15},
            "file": f"{l['line_id']}.ogg",
        })
    out = {"chosen_model": MODELS[chosen][0], "chosen_key": chosen, "count": len(manifest), "model_stats": stats,
           "skipped": data["skipped"], "excluded_topics": data["excluded_topics"],
           "spend_voice_usd": round(V.fal_api.logged_spend("voice/"), 3), "lines": manifest}
    (TRIAL / "manifest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "doubtful"} | {"doubtful": len(v["doubtful"])}
                      for k, v in stats.items()}, indent=1))
    print("spend", out["spend_voice_usd"])


if __name__ == "__main__":
    main()
