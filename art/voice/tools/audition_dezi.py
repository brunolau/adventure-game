"""Dezider recast audition 2026-10-07 (owner: "make DEZI with a roma accent; it's typical for Dezider to be a Roma
person with their distinctive Slovak accent").

Dezider Kováč (47) is the radio amateur and technical expert in his Petržalka garage (S29). The accent is a voice
direction only: the text stays standard Slovak, word for word. Direction rules: a natural, respectful everyday
Romani-Slovak (Bratislava) melody, never a caricature, never comic, no broken grammar.

Three variants on three of his lines (one take each, one Scribe check):
  A  Rasalgethi (his current voice), clear accent, natural delivery
  B  Rasalgethi, clear accent, comic delivery (owner wants him funny: the humour comes from the over-eager radio
     nerd, the accent itself stays natural - no ethnic caricature)
  C  Enceladus (only Emil, Karlova Ves 1995, never in S29), clear accent, comic delivery

Output: art/voice/full/audition/dezi/<variant>_<line>.ogg + results.json + index.html.
Budget scope voice/full/dezi/ (USD 1, own cap so it never touches the running r2 cap).

usage: python audition_dezi.py [variant ...]
"""
from __future__ import annotations

import html
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402

MODEL = "google/gemini-3.8-flash-tts"
OUT = V.ROOT / "art/voice/full/audition/dezi"
BUDGET = ("voice/full/dezi/", 1.0)
LINES = ["action.B17.001", "topic.DEZI.extra 1.004", "topic.DEZI.extra 2.004"]

BASE = ("Read the Slovak text verbatim, every word as written. A 47-year-old radio amateur in his garage in "
        "Petržalka, Bratislava: lively, friendly and clear, he loves explaining technical things in everyday words. ")
ACCENT = ("He is a Slovak Roma man from Bratislava who grew up speaking Romani at home, and his Slovak has the "
          "characteristic Romani-Slovak melody: a lively, sing-song intonation that rises and falls within the "
          "sentence, expressive emphasis, long vowels a little shorter, a slightly quicker rhythm. ")
RESPECT = ("The accent itself stays natural and respectful, a real person's everyday speech: never exaggerated, "
           "never a caricature of how Roma people speak, no broken grammar.")
COMIC = ("Play him with comic energy: an over-enthusiastic radio nerd who gets carried away, warm theatrical "
         "emphasis on technical words, a proud little pause before his punchlines, delighted with his own "
         "explanations. The humour comes from his personality, not from the accent. ")
VARIANTS = {
    "A": {"voice": "Rasalgethi", "label": "Rasalgethi (his current voice), clear accent, natural delivery",
          "style": BASE + ACCENT + "The accent should be clearly audible. " + RESPECT},
    "B": {"voice": "Rasalgethi", "label": "Rasalgethi (his current voice), clear accent, comic delivery",
          "style": BASE + ACCENT + "The accent should be clearly audible. " + COMIC + RESPECT},
    "C": {"voice": "Enceladus", "label": "Enceladus (different voice), clear accent, comic delivery",
          "style": BASE + ACCENT + "The accent should be clearly audible. " + COMIC + RESPECT},
    "D": {"voice": "Rasalgethi", "label": "Rasalgethi (his current voice), strong authentic accent (Romani as first language)",
          "style": BASE + ACCENT.replace("grew up speaking Romani at home", "speaks Romani as his first language and "
                                         "Slovak as his second") + "The accent should be strong and full, as it really "
                                         "sounds in such a speaker, not softened. " + COMIC + RESPECT},
}


def line_texts() -> dict[str, str]:
    man = json.loads((V.ROOT / "art/voice/full/manifest.json").read_text(encoding="utf-8"))["lines"]
    return {m["line_id"]: m["text"] for m in man if m["line_id"] in LINES}


def take(var: str, lid: str, text: str) -> dict:
    v = VARIANTS[var]
    tag = f"{var}_{lid.replace(' ', '_')}"
    tts = V.tts_text(text)
    usd = len(tts) / 1000 * V.TTS_PRICE[MODEL]
    res = V.fal_api.run(MODEL, {"prompt": tts, "voice": v["voice"], "style_instructions": v["style"]},
                        f"voice/full/dezi/audition/{tag}", usd, budget=BUDGET, poll_s=1.0)
    url = res["audio"]["url"]
    for attempt in range(4):  # fal.media downloads sometimes time out
        try:
            raw = V.fal_api.download(url, OUT / f"{tag}.wav")
            break
        except Exception:
            if attempt == 3:
                raise
    x = V.load_mono(raw)
    sc = V.fal_api.run(V.SCRIBE, {"audio_url": url, "language_code": "slk", "diarize": False,
                                  "tag_audio_events": False}, f"voice/full/dezi/audition/{tag}.stt",
                       max(len(x) / V.SR, 1.0) / 60 * 0.008, budget=BUDGET, poll_s=1.0).get("text", "").strip()
    y, lufs, peak = V.finish(x, phone=False)
    V.write_ogg(OUT / f"{tag}.ogg", y)
    (OUT / f"{tag}.wav").unlink(missing_ok=True)
    return {"variant": var, "line_id": lid, "text": text, "file": f"{tag}.ogg", "seconds": round(len(y) / V.SR, 2),
            "stt_scribe": sc, "wer_scribe": V.wer(text, sc)}


def page(results: list[dict], old: dict[str, str]) -> str:
    rows = []
    for lid in LINES:
        text = next(r["text"] for r in results if r["line_id"] == lid)
        cells = [f'<div class="take"><b>Teraz</b><audio controls preload="none" src="{html.escape(old[lid])}"></audio></div>']
        for var in VARIANTS:
            r = next(r for r in results if r["line_id"] == lid and r["variant"] == var)
            cells.append(f'<div class="take"><b>{var}</b><audio controls preload="none" src="{html.escape(r["file"])}">'
                         f'</audio><small>počuté: {html.escape(r["stt_scribe"])}</small></div>')
        rows.append(f'<section><p class="line">„{html.escape(text)}“</p><div class="takes">{"".join(cells)}</div></section>')
    legend = "".join(f"<li><b>{k}</b> – {html.escape(v['label'])}</li>" for k, v in VARIANTS.items())
    return f"""<!doctype html><html lang="sk"><head><meta charset="utf-8"><title>Dezider – konkurz na hlas</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><style>
body{{font:15px/1.5 system-ui,sans-serif;max-width:60rem;margin:0 auto;padding:1.5rem 1rem;background:#f6f4ef;color:#222}}
h1{{font-size:1.4rem;margin:0 0 .3rem}} section{{background:#fff;border-radius:8px;padding:1rem;margin:1rem 0}}
.line{{font-size:1.05rem;margin:0 0 .6rem}} .takes{{display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:.8rem}}
.take{{display:flex;flex-direction:column;gap:.3rem}} audio{{width:100%}} small{{color:#666}}
@media (prefers-color-scheme:dark){{body{{background:#1c1b19;color:#ddd}} section{{background:#2a2926}} small{{color:#999}}}}
</style></head><body><h1>Dezider Kováč – konkurz na hlas</h1>
<p>Prízvuk je len v prednese; text ostáva spisovný. „Teraz“ je hlas, ktorý je v hre teraz.</p><ul>{legend}</ul>
{"".join(rows)}</body></html>"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    texts = line_texts()
    prev = json.loads((OUT / "results.json").read_text(encoding="utf-8")) if (OUT / "results.json").exists() else []
    only = set(sys.argv[1:]) or set(VARIANTS)  # e.g. "python audition_dezi.py D" renders only variant D
    keep = [r for r in prev if r["variant"] not in only and r["variant"] in VARIANTS]
    jobs = [(var, lid, texts[lid]) for var in VARIANTS if var in only for lid in LINES]
    with ThreadPoolExecutor(6) as ex:
        results = keep + list(ex.map(lambda j: take(*j), jobs))
    old = {lid: "../../../../../src/game/assets/voice/" + lid + ".ogg" for lid in LINES}
    (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "index.html").write_text(page(results, old), encoding="utf-8")
    for r in results:
        print(r["variant"], r["line_id"], r["seconds"], "s | heard:", r["stt_scribe"])
    print("logged spend", round(V.fal_api.logged_spend(BUDGET[0]), 4))


if __name__ == "__main__":
    main()
