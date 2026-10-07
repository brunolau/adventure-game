"""Narrator recast 2026-10-07 (owner: "the narrator is incredibly boring, make it a female with a more interested
pitch"): audition of three female Gemini stock voices for NARRATOR with the new narrator direction.

The game has exactly two NARRATOR lines (cutscene.CS04.02.001, cutscene.CS07.05.001; live tables, overlays,
cutscenes and epilogue searched). The third audition text is a narrator-register game text that is never voiced in
the game (the caption of epilogue shot 5), so every candidate is heard on three lines.

Candidates: the female stock voices used least by the cast and never in the narrator's eras or scenes (all fourteen
female Gemini voices already speak somebody): Callirrhoe (only Alena, 1995), Autonoe (only Adam at 10, a child
direction on a 1995 tape), Laomedeia (only Soňa, 11, a child direction, 1995).

Two takes per candidate and line (pitch measures vary a lot per take). Each take: one Scribe v2 check, pitch / pitch range / rate (voice_features), and a crude timbre distance (mean
log-mel spectrum, level removed) to every female voice of the cast measured on that voice's own finished lines, and
to the old narrator (Charon). Budget scope voice/full/r2/ (USD 3 for the whole narrator + LEAL re-voice).

usage: python audition_narrator.py
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402
import voice_features as F  # noqa: E402
from casting import SK  # noqa: E402

MODEL = "google/gemini-3.8-flash-tts"
OUT = V.ROOT / "art/voice/full/audition/narrator"
BUDGET = ("voice/full/r2/", 3.0)
CANDIDATES = ["Callirrhoe", "Autonoe", "Laomedeia"]
TAKES = (1, 2)  # two takes per candidate and line: per-take pitch measures vary a lot
NARRATOR_STYLE = SK + ("A female narrator of about forty telling the closing moment of a story she loves: warm, "
                       "engaged and genuinely interested, as if sharing a small discovery with the listener; a lively, "
                       "varied natural melody with gentle rises and falls, a slight smile in the voice, medium pace, "
                       "clear and close; never flat or monotone, never theatrical, no exaggerated drama, no jokes.")
FEMALE_VOICES = ["Zephyr", "Kore", "Leda", "Aoede", "Callirrhoe", "Autonoe", "Despina", "Erinome", "Laomedeia",
                 "Achernar", "Gacrux", "Pulcherrima", "Vindemiatrix", "Sulafat"]


def audition_lines() -> list[dict]:
    lines = json.loads((V.ROOT / "art/voice/full/lines.json").read_text(encoding="utf-8"))["lines"]
    nar = [{"line_id": l["line_id"], "text": l["text"]} for l in lines if l["speaker"] == "NARRATOR"]
    import csv
    with (V.ROOT / "src/game/localization/world.csv").open(encoding="utf-8-sig", newline="") as h:
        world = {r["keys"]: r["sk"] for r in csv.DictReader(h)}
    nar.append({"line_id": "epilogue.5.shot", "text": world["epilogue.5.shot"], "audition_only": True})
    return nar


def logmel(x: np.ndarray, n: int = 40) -> np.ndarray:
    """Mean log-mel spectrum of the speech frames, level removed (a crude timbre fingerprint)."""
    w, hop = 2048, 512
    nfr = 1 + (len(x) - w) // hop
    if nfr <= 0:
        return np.zeros(n)
    idx = np.arange(w)[None, :] + hop * np.arange(nfr)[:, None]
    fr = x[idx] * np.hanning(w)
    P = np.abs(np.fft.rfft(fr, axis=1)) ** 2
    rms = np.sqrt(P.mean(axis=1))
    P = P[20 * np.log10(rms + 1e-12) > 20 * np.log10(rms.max() + 1e-12) - 30]
    f = np.fft.rfftfreq(w, 1 / V.SR)
    mel = lambda hz: 2595 * np.log10(1 + hz / 700)  # noqa: E731
    edges = np.linspace(mel(80), mel(8000), n + 2)
    hz = 700 * (10 ** (edges / 2595) - 1)
    fb = np.zeros((n, len(f)))
    for i in range(n):
        a, b, c = hz[i], hz[i + 1], hz[i + 2]
        fb[i] = np.clip(np.minimum((f - a) / (b - a), (c - f) / (c - b)), 0, None)
    m = np.log10(P @ fb.T + 1e-10).mean(axis=0)
    return m - m.mean()


def cast_fingerprints() -> dict[str, np.ndarray]:
    """Per female voice (as cast, adult directions only where possible) and the old narrator: mean fingerprint of up
    to 6 finished lines without a colour effect."""
    man = json.loads((V.ROOT / "art/voice/full/manifest.json").read_text(encoding="utf-8"))["lines"]
    child = {"TONO82", "ADAM10", "JANA82", "SONA", "KUBO", "ZUZANA"}
    out = {}
    for v in FEMALE_VOICES + ["Charon"]:
        ls = [e for e in man if e["voice"] == v and not e.get("fx") and e["source"] == "full"]
        adult = [e for e in ls if e["speaker"] not in child]
        pick = (adult or ls)[:6] if v != "Charon" else [e for e in ls if e["speaker"] == "NARRATOR"]
        if not pick:
            continue
        fp = [logmel(V.load_mono(V.ROOT / "art/voice/full" / e["file"])) for e in pick]
        out[v] = {"fp": np.mean(fp, axis=0), "speakers": sorted({e["speaker"] for e in pick}), "n": len(pick)}
    return out


def one(lid: str, text: str, voice: str, k: int = 1) -> dict:
    tag = f"NARRATOR.{voice}.{lid}" + (f".k{k}" if k > 1 else "")
    cache = OUT / f"{tag}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    tts = V.tts_text(text)
    usd = len(tts) / 1000 * V.TTS_PRICE[MODEL]
    res = V.fal_api.run(MODEL, {"prompt": tts, "voice": voice, "style_instructions": NARRATOR_STYLE},
                        f"voice/full/r2/audition/{tag}", usd, budget=BUDGET, poll_s=1.0)
    url = res["audio"]["url"]
    raw = V.fal_api.download(url, OUT / f"{tag}.wav")
    x = V.load_mono(raw)
    m = V.measure(x, text)
    usd_stt = max(m["raw_s"], 1.0) / 60 * 0.008
    sc = V.fal_api.run(V.SCRIBE, {"audio_url": url, "language_code": "slk", "diarize": False,
                                  "tag_audio_events": False}, f"voice/full/r2/audition/stt/{tag}", usd_stt,
                       budget=BUDGET, poll_s=1.0).get("text", "").strip()
    y, lufs, peak = V.finish(x, phone=False)
    V.write_ogg(OUT / f"{tag}.ogg", y)
    r = {"role": "NARRATOR", "voice": voice, "k": k, "line_id": lid, "text": text, "style": NARRATOR_STYLE, "measure": m,
         "features": F.features(V.trim(x)), "stt_scribe": sc, "wer_scribe": V.wer(text, sc),
         "usd_tts": round(usd, 5), "usd_stt": round(usd_stt, 5), "file": f"{tag}.ogg"}
    cache.write_text(json.dumps(r, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    return r


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines = audition_lines()
    jobs = [(l["line_id"], l["text"], v, k) for k in TAKES for l in lines for v in CANDIDATES]
    print(len(jobs), "takes; logged r2 spend so far", round(V.fal_api.logged_spend(BUDGET[0]), 4))
    with ThreadPoolExecutor(max_workers=9) as pool:
        res = list(pool.map(lambda j: one(*j), jobs))
    # the old narrator (Charon) on the two real lines, from its raw takes, for comparison
    old = []
    for l in lines[:2]:
        rec = json.loads((V.ROOT / "art/voice/raw/full" / f"{l['line_id']}.json").read_text(encoding="utf-8"))
        x = V.load_mono(V.ROOT / "art/voice/raw/full" / rec["best"]["raw"])
        old.append({"voice": "Charon (old)", "line_id": l["line_id"], "features": F.features(V.trim(x)),
                    "measure": rec["best"]["measure"]})
    fps = cast_fingerprints()
    summary = {}
    for v in CANDIDATES:
        rs = [r for r in res if r["voice"] == v]
        fp = np.mean([logmel(V.load_mono(OUT / r["file"])) for r in rs], axis=0)
        dist = {k: round(float(np.linalg.norm(fp - d["fp"])), 3) for k, d in fps.items()}
        others = {k: d for k, d in dist.items() if k != v}
        summary[v] = {
            "f0_median_hz": round(float(np.mean([r["features"]["f0_median_hz"] for r in rs])), 1),
            "f0_range_semitones": round(float(np.mean([r["features"]["f0_range_semitones"] for r in rs])), 1),
            "chars_per_s": round(float(np.mean([r["measure"]["chars_per_s"] for r in rs])), 1),
            "wer_scribe": [r["wer_scribe"]["wer"] for r in rs],
            "timbre_dist": dist, "nearest_other_cast_voice": min(others, key=others.get),
            "nearest_dist": min(others.values()), "dist_gacrux": dist.get("Gacrux"), "dist_kore": dist.get("Kore"),
            "dist_old_charon": dist.get("Charon")}
    for r in sorted(res, key=lambda r: (r["voice"], r["line_id"], r.get("k", 1))):
        f = r["features"]
        print(f"{r['voice']:11} {r['line_id']:22} k{r.get('k', 1)} F0 {f['f0_median_hz']:6.1f} Hz range {f['f0_range_semitones']:4.1f} st"
              f" {r['measure']['chars_per_s']:5.1f} c/s WER {r['wer_scribe']['wer']:.2f} | {r['stt_scribe']}")
    for o in old:
        f = o["features"]
        print(f"{o['voice']:11} {o['line_id']:22} F0 {f['f0_median_hz']:6.1f} Hz range {f['f0_range_semitones']:4.1f} st"
              f" {o['measure']['chars_per_s']:5.1f} c/s")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    usd = round(sum(r["usd_tts"] + r["usd_stt"] for r in res), 4)
    (OUT / "audition.json").write_text(json.dumps({"style": NARRATOR_STYLE, "lines": lines, "takes": res,
                                                   "old_narrator": old, "summary": summary, "usd": usd},
                                                  ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print("usd", usd)


if __name__ == "__main__":
    main()
