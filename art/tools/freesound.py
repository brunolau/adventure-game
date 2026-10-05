"""CC0 sound lookup on Freesound without login (public search pages and HQ previews).

  python -X utf8 art/tools/freesound.py search "wall clock ticking" [--min 5] [--max 120] [-n 8] [--sort downloads]
  python -X utf8 art/tools/freesound.py get <sound_id> [<sound_id> ...]

`get` re-checks the licence on the sound page (must be CC0 1.0), downloads the HQ OGG preview to
art/candidates/audio/freesound/<id>.ogg and records title, author, page URL and licence in
art/source/audio_sources.json (the source of art/source/AUDIO_CREDITS.md).
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "art" / "candidates" / "audio" / "freesound"
REGISTRY = ROOT / "art" / "source" / "audio_sources.json"
UA = {"User-Agent": "LastBell-ArtPipeline/0.1 (+https://github.com/brunolau/game-lastbell)"}
SORTS = {"score": "score", "downloads": "num_downloads desc", "rating": "avg_rating desc"}


def search(query: str, dmin: float, dmax: float, n: int, sort: str) -> list[dict]:
    flt = f'license:"Creative Commons 0" duration:[{dmin} TO {dmax}]'
    for attempt in range(6):
        response = requests.get("https://freesound.org/search/", params={"q": query, "f": flt, "s": SORTS[sort]},
                                headers=UA, timeout=60)
        if response.status_code != 429:
            break
        time.sleep(20 * (attempt + 1))  # polite backoff on the public site
    response.raise_for_status()
    time.sleep(3)
    text = response.text
    out = []
    for block in text.split('class="bw-search__result"')[1:]:
        def attr(name: str) -> str:
            m = re.search(name + r'="([^"]*)"', block)
            return html.unescape(m.group(1)) if m else ""
        rating = re.search(r'Average rating of ([0-9.]+)', block)
        out.append({
            "id": attr("data-sound-id"), "user": attr("data-username"), "title": attr("data-title"),
            "duration": float(attr("data-duration") or 0), "downloads": int(attr("data-num-downloads") or 0),
            "rating": float(rating.group(1)) if rating else 0.0,
            "cc0": "License: Creative Commons 0" in block,
        })
        if len(out) >= n:
            break
    return out


def registry() -> dict:
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {}


def get(sound_id: str) -> Path:
    dest = CACHE / f"{sound_id}.ogg"
    reg = registry()
    if dest.exists() and sound_id in reg.get("freesound", {}):
        return dest
    page_url = f"https://freesound.org/s/{sound_id}/"
    page = requests.get(page_url, headers=UA, timeout=60)
    page.raise_for_status()
    text = page.text
    if "creativecommons.org/publicdomain/zero/1.0" not in text:
        sys.exit(f"{sound_id}: not CC0 on its page, refusing")
    title = re.search(r'og:audio:title" content="([^"]*)"', text)
    artist = re.search(r'og:audio:artist" content="([^"]*)"', text)
    lq = re.search(r'https://cdn\.freesound\.org/previews/(\d+)/(\d+_\d+)-lq\.mp3', text)
    if not lq:
        sys.exit(f"{sound_id}: no preview url")
    hq = f"https://cdn.freesound.org/previews/{lq.group(1)}/{lq.group(2)}-hq.ogg"
    data = requests.get(hq, headers=UA, timeout=120)
    if data.status_code != 200:
        hq = hq.replace("-hq.ogg", "-hq.mp3")
        dest = dest.with_suffix(".mp3")
        data = requests.get(hq, headers=UA, timeout=120)
    data.raise_for_status()
    CACHE.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data.content)
    final_url = page.url
    reg = registry()  # re-read: several downloaders may run in parallel
    reg.setdefault("freesound", {})[sound_id] = {
        "title": html.unescape(title.group(1)) if title else "", "author": html.unescape(artist.group(1)) if artist else "",
        "page": final_url, "file": hq, "license": "CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/)",
        "retrieved": time.strftime("%Y-%m-%d"),
    }
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(reg, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(f"got {sound_id}: {reg['freesound'][sound_id]['title']} by {reg['freesound'][sound_id]['author']}")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["search", "get"])
    parser.add_argument("args", nargs="+")
    parser.add_argument("--min", type=float, default=3)
    parser.add_argument("--max", type=float, default=180)
    parser.add_argument("-n", type=int, default=8)
    parser.add_argument("--sort", default="score", choices=sorted(SORTS))
    a = parser.parse_args()
    if a.cmd == "search":
        for q in a.args:
            print(f"## {q}")
            for r in search(q, a.min, a.max, a.n, a.sort):
                print(f"  {r['id']:>7} {r['duration']:6.1f}s dl={r['downloads']:<6} *{r['rating']:.1f} "
                      f"{'CC0' if r['cc0'] else '???'} {r['user']}: {r['title']}")
    else:
        for sid in a.args:
            get(sid)
            time.sleep(0.5)


if __name__ == "__main__":
    main()
