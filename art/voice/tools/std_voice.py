"""Voice for the Standard/Hard text variants (<key>.std, src/game/localization/overrides/guidance_std.csv).

Every variant whose base key has a recording gets its own take with the base line's voice, casting style and delivery
(art/voice/full/manifest.json + casting.json), one Scribe v2 check and one retake when the transcript differs. Output:
src/game/assets/voice/<key>.std.ogg (AudioService plays it through TextService.VariantKey) and
art/voice/full/std_manifest.json. Budget scope voice/full/std/ (USD 0.5).

usage: python std_voice.py [key ...]
"""
from __future__ import annotations

import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402

MODEL = "google/gemini-3.8-flash-tts"
BUDGET = ("voice/full/std/", 0.5)
RAW = V.ROOT / "art/voice/raw/full/std"
DEST = V.ROOT / "src/game/assets/voice"
OUT_MANIFEST = V.ROOT / "art/voice/full/std_manifest.json"


def jobs() -> list[dict]:
    man = json.loads((V.ROOT / "art/voice/full/manifest.json").read_text(encoding="utf-8"))
    recs = {r["line_id"]: r for r in man["lines"]}
    for r in man.get("looks", []):
        recs.setdefault(r["line_id"], r)
    cast = json.loads((V.ROOT / "art/voice/full/casting.json").read_text(encoding="utf-8"))
    speakers = cast.get("speakers", cast)
    irony = man.get("irony_direction", "")
    rows = list(csv.DictReader((V.ROOT / "src/game/localization/overrides/guidance_std.csv").open(encoding="utf-8")))
    out = []
    for r in rows:
        base = r["keys"][: -len(".std")]
        rec = recs.get(base)
        if not rec:
            continue
        style = speakers.get(rec["speaker"], {}).get("style", "")
        if rec.get("delivery"):
            style = style + " " + irony
        out.append({"key": r["keys"], "base": base, "speaker": rec["speaker"], "voice": rec["voice"], "style": style.strip(),
                    "text": r["sk"], "fx": rec.get("fx")})
    return out


def take(job: dict, n: int) -> dict:
    tag = f"{job['key'].replace(' ', '_')}.t{n}"
    text = V.tts_text(job["text"])
    usd = len(text) / 1000 * V.TTS_PRICE[MODEL]
    res = V.fal_api.run(MODEL, {"prompt": text, "voice": job["voice"], "style_instructions": job["style"]},
                        f"voice/full/std/{tag}", usd, budget=BUDGET, poll_s=1.0)
    url = res["audio"]["url"]
    for attempt in range(4):
        try:
            raw = V.fal_api.download(url, RAW / f"{tag}.wav")
            break
        except Exception:
            if attempt == 3:
                raise
    x = V.load_mono(raw)
    heard = V.fal_api.run(V.SCRIBE, {"audio_url": url, "language_code": "slk", "diarize": False, "tag_audio_events": False},
                          f"voice/full/std/{tag}.stt", max(len(x) / V.SR, 1.0) / 60 * 0.008, budget=BUDGET,
                          poll_s=1.0).get("text", "").strip()
    return {"x": x, "heard": heard, "wer": V.wer(job["text"], heard)}


def one(job: dict) -> dict:
    t = take(job, 1)
    retaken = False
    if t["wer"]["wer_nodiac"] > 0:
        t2 = take(job, 2)
        retaken = True
        if t2["wer"]["wer_nodiac"] < t["wer"]["wer_nodiac"]:
            t = t2
    y, lufs, peak = V.finish(t["x"], phone=False)
    V.write_ogg(DEST / f"{job['key']}.ogg", y)
    return {"key": job["key"], "speaker": job["speaker"], "voice": job["voice"], "text": job["text"], "heard": t["heard"],
            "wer": t["wer"], "retaken": retaken, "seconds": round(len(y) / V.SR, 2), "lufs": round(lufs, 1)}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    todo = jobs()
    if sys.argv[1:]:
        todo = [j for j in todo if j["key"] in sys.argv[1:]]
    with ThreadPoolExecutor(6) as ex:
        results = list(ex.map(one, todo))
    OUT_MANIFEST.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in results:
        flag = "  <-- check" if r["wer"]["wer_nodiac"] > 0 else ""
        print(f"{r['key']}: {r['seconds']}s retake={r['retaken']}{flag}\n   heard: {r['heard']}")
    print(len(results), "lines; logged spend", round(V.fal_api.logged_spend(BUDGET[0]), 4))


if __name__ == "__main__":
    main()
