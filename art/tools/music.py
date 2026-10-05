"""Music generation for LastBell (fal.ai), one call per track variant.

Usage:
  python -X utf8 art/tools/music.py list
  python -X utf8 art/tools/music.py gen <track> [--model lyria|minimax|eleven] [--variant N] [--seconds S]

Raw generations land in art/masters/music/<track>__<model>_v<N>.<ext>; every paid call is logged
in art/spend-log.csv under the asset scope "music/". The budget guard refuses calls beyond the cap.
Mastering (loop points, loudness, OGG) is done by art/tools/audio_master.py.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fal_api  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "art" / "masters" / "music"
MUSIC_CAP_USD = 17.0  # task budget 25: music <= 17, AI sfx <= 8 (logged under "sfx-ai/")

MODELS = {
    # documented prices on the fal model pages (2026-10-05)
    "lyria": ("fal-ai/lyria3/pro", lambda s: 0.08),
    "minimax": ("fal-ai/minimax-music/v2.6", lambda s: 0.15),
    "eleven": ("elevenlabs/music/v2.5", lambda s: 0.60 * math.ceil(s / 60.0)),
}

COMMON = ("Instrumental only, absolutely no vocals, no singing, no humming, no spoken words, no choir. "
          "Video game background score for a warm, gentle, humorous point-and-click adventure about a "
          "kind repairman who travels through time in Bratislava, Slovakia. Civil and friendly, never "
          "epic or dark. Steady tempo and steady texture from start to finish so it can loop: no fade-in, "
          "no fade-out, no big finale, no long silence; keep the same energy throughout, ending on the groove.")

TRACKS = {
    "1960": ("music/1960.ogg", 150,
             "Slovak village in early summer 1960. Light acoustic folk waltz-like lilt in 3/4 at 96 BPM, "
             "G major. Lead: warm piano accordion (musette, not polka-loud) playing a simple whistleable "
             "melody; acoustic guitar strumming, upright double bass, a little clarinet answering phrases, "
             "soft brushed snare. Sunny, nostalgic, a gentle smile, like a black-and-white comedy film."),
    "1982": ("music/1982.ogg", 150,
             "Socialist housing estate in winter, December 1982, Dubravka Bratislava. Cosy, slightly ironic "
             "chamber piece at 88 BPM in D minor turning to F major: soft analog polysynth pads and a warm "
             "monophonic analog synth lead in the style of early 80s Eastern European TV and cartoon "
             "scores, celesta and glockenspiel sparkle like snow, pizzicato strings, upright bass, light "
             "brushed drums. Warm interiors, frosty windows, quietly funny."),
    "1995": ("music/1995.ogg", 150,
             "Bratislava in summer 1995, trams and a lively city. Breezy mid-90s pop-jazz instrumental at "
             "104 BPM, A major: bright Rhodes electric piano, clean funky electric guitar, fretless-style "
             "electric bass, light drum machine plus live shaker, a few soft 90s synth pad and synth bell "
             "touches, muted trumpet answering phrases. Sunny, optimistic, curious, a little cheeky."),
    "2020": ("music/2020.ogg", 150,
             "Quiet suburban village near Bratislava in autumn 2020, during the pandemic: calm, intimate, "
             "hopeful. Gentle acoustic chamber piece at 80 BPM, E minor to G major: fingerpicked nylon "
             "guitar, felt piano, cello and soft violin, light marimba, tiny ticking percussion like a clock "
             "in a repair workshop. Neighbourly kindness, falling leaves, small hopeful smile."),
    "2035": ("music/2035.ogg", 150,
             "Alpine ski resort Jasna and Chopok in the Low Tatras, a bright summer day in 2035. Airy, "
             "optimistic light-orchestral piece at 92 BPM, D major: plucked harp and acoustic guitar "
             "arpeggios, flute and soft horn melody, warm strings, subtle modern clean synth arpeggio "
             "shimmer, light hand percussion. Fresh mountain air, cable cars, wonder without bombast."),
    "menu": ("music/menu.ogg", 150,
             "Main menu theme. A gentle, memorable signature melody at 84 BPM, C major, introduced by solo "
             "piano and then shared by accordion, clarinet and pizzicato strings, with a soft ticking "
             "clock-like woodblock and a small bell. Warm, nostalgic, inviting, a little whimsical, like "
             "opening an old repair toolbox full of memories."),
    "puzzle": ("music/puzzle.ogg", 150,
               "Thinking cue for solving a mechanical puzzle. Sparse, curious and light at 90 BPM, A minor "
               "and C major: plucked pizzicato strings, marimba and celesta playing an inquisitive ostinato, "
               "soft bassoon, a ticking woodblock like clockwork, muted felt piano. Calm concentration, "
               "playful, never stressful, unobtrusive under dialogue."),
    "tension": ("music/tension.ogg", 150,
                "Light tension cue for a cosy adventure: something is wrong with time, but it is safe and "
                "family friendly. 100 BPM, D minor: soft low string ostinato, ticking clock percussion, "
                "pizzicato bass, a few curious bassoon and clarinet phrases, gentle tremolo strings, muted "
                "timpani. Suspenseful in a playful detective-comedy way, not horror, not action."),
    "epilogue": ("music/epilogue.ogg", 180,
                 "Epilogue and end credits theme. Warm, heartfelt and gently uplifting at 76 BPM, F major: "
                 "the main melody on piano and accordion, then strings and soft horns join, acoustic guitar, "
                 "a small music-box bell, light brushed drums. Grateful, reconciled, a happy end of a long "
                 "journey through the decades of one neighbourhood."),
}


def prompt_for(track: str) -> str:
    return TRACKS[track][2] + " " + COMMON


def arguments(model: str, track: str, seconds: int) -> dict:
    text = prompt_for(track)
    if model == "lyria":
        return {"prompt": text + f" Length about {seconds // 60} minutes {seconds % 60} seconds."}
    if model == "minimax":
        return {"prompt": text[:2000], "is_instrumental": True,
                "audio_setting": {"sample_rate": 44100, "bitrate": 256000, "format": "mp3"}}
    if model == "eleven":
        return {"prompt": text, "music_length_ms": seconds * 1000, "force_instrumental": True,
                "output_format": "mp3_44100_192"}
    raise KeyError(model)


def generate(track: str, model: str, variant: int, seconds: int | None) -> Path:
    endpoint, price = MODELS[model]
    seconds = seconds or TRACKS[track][1]
    usd = price(seconds)
    dest = OUT / f"{track}__{model}_v{variant}.mp3"
    if dest.exists():
        print("exists", dest)
        return dest
    result = fal_api.run(endpoint, arguments(model, track, seconds), f"music/{track}__{model}_v{variant}", usd,
                         budget=("music/", MUSIC_CAP_USD), timeout_s=1200)
    audio = result.get("audio") or (result.get("audio_file")) or result
    url = audio["url"] if isinstance(audio, dict) else audio
    fal_api.download(url, dest)
    meta = dest.with_suffix(".json")
    meta.write_text(json.dumps({"endpoint": endpoint, "usd": usd, "arguments": arguments(model, track, seconds),
                                "result": result}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", dest, f"{usd:.2f} USD")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["list", "gen"])
    parser.add_argument("track", nargs="?")
    parser.add_argument("--model", default="lyria", choices=sorted(MODELS))
    parser.add_argument("--variant", type=int, default=1)
    parser.add_argument("--seconds", type=int)
    args = parser.parse_args()
    if args.cmd == "list":
        for name, (path, secs, _) in TRACKS.items():
            print(f"{name:9s} {path:22s} {secs}s")
        print(f"spent on music so far: {fal_api.logged_spend('music/'):.2f} / {MUSIC_CAP_USD:.2f} USD")
        return
    generate(args.track, args.model, args.variant, args.seconds)


if __name__ == "__main__":
    main()
