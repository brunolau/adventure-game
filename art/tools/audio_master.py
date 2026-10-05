"""Masters the chosen AI music generations into seamless OGG loops for the game.

  python -X utf8 art/tools/audio_master.py music            # all tracks in CHOICES
  python -X utf8 art/tools/audio_master.py music 1960 1982  # some

For each track:
  1. decode the raw generation (art/masters/music/<track>__<model>_v<N>.mp3), trim leading silence;
  2. find the beat grid (spectral-flux onsets, BPM from the Lyria section plan) and the downbeat phase;
  3. loop start A = second section of the plan, loop end B = start of the plan's last section (the
     resolving ending is cut), both snapped to downbeats and refined by comparing the two bars
     before A and before B (band-energy and onset similarity) so the jump lands on the same beat;
  4. bake an equal-power crossfade of one beat: out[B-X:B] = src[B-X:B]*fade_out + src[A-X:A]*fade_in,
     so the engine's jump from B back to A is continuous;
  5. normalise to -16 LUFS integrated (soft limiter keeps sample peaks under -1 dBFS) and write
     OGG Vorbis q5 to src/game/assets/music/<track>.ogg;
  6. write the loop points to src/game/data/audio/music.json (engine: AudioStreamOggVorbis.LoopOffset)
     and a junction check picture to art/candidates/audio/loopcheck_<track>.png.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audio_lib as A  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "art" / "masters" / "music"
OUT = ROOT / "src" / "game" / "assets" / "music"
DATA = ROOT / "src" / "game" / "data" / "audio" / "music.json"
CHECK = ROOT / "art" / "candidates" / "audio"
TARGET_LUFS = -16.0
SR = A.SR

# track -> (raw file stem, beats per bar)
CHOICES = {
    "1960": ("1960__lyria_v1", 3),
    "1982": ("1982__lyria_v2", 4),
    "1995": ("1995__lyria_v1", 4),
    "2020": ("2020__lyria_v1", 4),
    "2035": ("2035__lyria_v1", 4),
    "menu": ("menu__lyria_v2", 4),
    "puzzle": ("puzzle__lyria_v1", 4),
    "tension": ("tension__lyria_v2", 4),
    "epilogue": ("epilogue__lyria_v3", 4),
}


def plan(stem: str) -> tuple[float, float, list[float]]:
    """(bpm, planned duration, section start times) from the Lyria result's 'lyrics' field."""
    meta = json.loads((RAW / f"{stem}.json").read_text(encoding="utf-8"))
    text = meta["result"].get("lyrics", "")
    bpm = float(re.search(r"^bpm: ([0-9.]+)", text, re.M).group(1))
    dur = float(re.search(r"^duration_secs: ([0-9.]+)", text, re.M).group(1))
    starts = [float(t) for t in re.findall(r"\[\[\w+\]\]\n\[([0-9.]+):\]", text)]
    return bpm, dur, starts


HOP = 512


def features(mono: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(onset strength per hop, log band energies per hop [frames, 24])."""
    n_fft = 2048
    frames = 1 + (len(mono) - n_fft) // HOP
    idx = np.arange(n_fft)[None, :] + HOP * np.arange(frames)[:, None]
    spec = np.abs(np.fft.rfft(mono[idx] * np.hanning(n_fft), axis=1)).astype(np.float32)
    freqs = np.fft.rfftfreq(n_fft, 1 / SR)
    edges = np.geomspace(60, 12000, 25)
    bands = np.stack([spec[:, (freqs >= edges[i]) & (freqs < edges[i + 1])].sum(axis=1) for i in range(24)], axis=1)
    logb = np.log1p(bands)
    flux = np.maximum(0, np.diff(logb, axis=0)).sum(axis=1)
    flux = np.concatenate([[0], flux])
    flux = flux - np.convolve(flux, np.ones(43) / 43, mode="same")  # local mean removal (~0.5 s)
    return np.maximum(flux, 0), logb


def beat_grid(onset: np.ndarray, bpm: float, beats_per_bar: int, duration: float) -> tuple[float, float, float]:
    """(refined beat period s, beat phase s, downbeat phase s)."""
    fps = SR / HOP
    best = (-1.0, 60 / bpm, 0.0)
    for period in np.linspace(60 / bpm * 0.985, 60 / bpm * 1.015, 31):
        for phase in np.arange(0, period, 1 / fps):
            ticks = np.arange(phase, duration - 0.1, period)
            score = onset[np.clip((ticks * fps).astype(int), 0, len(onset) - 1)].sum()
            if score > best[0]:
                best = (score, period, phase)
    _, period, phase = best
    # downbeat = the beat position within the bar with the strongest summed onsets
    sums = []
    for k in range(beats_per_bar):
        ticks = np.arange(phase + k * period, duration - 0.1, period * beats_per_bar)
        sums.append(onset[np.clip((ticks * fps).astype(int), 0, len(onset) - 1)].sum())
    down = phase + int(np.argmax(sums)) * period
    return period, phase, down


def snap(t: float, down: float, bar: float) -> float:
    return down + round((t - down) / bar) * bar


def window_score(logb: np.ndarray, onset: np.ndarray, a: float, b: float, length: float) -> float:
    """Similarity of the windows [a-length, a) and [b-length, b) (higher = more alike)."""
    fps = SR / HOP
    ia, ib, n = int(a * fps), int(b * fps), int(length * fps)
    if ia - n < 0 or ib > len(onset):
        return -1e9
    fa, fb = logb[ia - n:ia], logb[ib - n:ib]
    spec = -np.mean(np.abs(fa - fb))
    oa, ob = onset[ia - n:ia], onset[ib - n:ib]
    corr = float(np.dot(oa - oa.mean(), ob - ob.mean()) / (np.linalg.norm(oa - oa.mean()) * np.linalg.norm(ob - ob.mean()) + 1e-9))
    return spec + corr


def master(track: str) -> dict:
    stem, bpb = CHOICES[track]
    src_path = RAW / f"{stem}.mp3"
    audio = A.decode(src_path)
    mono = audio.mean(axis=1)
    # trim leading digital silence
    lead = int(np.argmax(np.abs(mono) > 1e-3))
    audio, mono = audio[lead:], mono[lead:]
    duration = len(mono) / SR
    bpm, planned, starts = plan(stem)
    onset, logb = features(mono)
    period, phase, down = beat_grid(onset, bpm, bpb, duration)
    bar = period * bpb
    # tail decay: last time the 1 s RMS is within 5 dB of the median level
    win = SR
    rms = np.sqrt(A.moving_mean(mono ** 2, win)[::SR // 10])
    rms_db = 20 * np.log10(rms + 1e-9)
    level = np.median(rms_db)
    loud = np.where(rms_db > level - 5)[0]
    decay_at = (loud[-1] / 10 + 0.5) if len(loud) else duration
    scale = duration / planned if planned > 0 else 1.0
    plan_starts = [s * scale for s in starts]
    plan_a = plan_starts[1] if len(plan_starts) > 1 else 8 * bar
    tail_starts = [s for s in plan_starts if s <= decay_at - bar]
    plan_b = tail_starts[-1] if len(tail_starts) >= 3 else decay_at - bar
    if plan_b - plan_a < 75:  # keep the loop body long enough
        plan_b = snap(decay_at - 2 * bar, down, bar)
    best = (-1e9, 0.0, 0.0)
    for da in range(-2, 3):
        a = snap(plan_a, down, bar) + da * bar
        if a < 2 * bar:
            continue
        for db in range(-2, 3):
            b = snap(plan_b, down, bar) + db * bar
            if b > decay_at or b - a < 60:
                continue
            # fine phase search +-60 ms around b
            for fine in np.arange(-0.06, 0.0601, HOP / SR):
                s = window_score(logb, onset, a, b + fine, 2 * bar) - 0.02 * (abs(da) + abs(db))
                if s > best[0]:
                    best = (s, a, b + fine)
    score, a, b = best
    ia, ib = int(round(a * SR)), int(round(b * SR))
    xf = int(round(period * SR))
    out = audio[:ib].copy()
    t = np.linspace(0, np.pi / 2, xf, dtype=np.float32)[:, None]
    out[ib - xf:ib] = audio[ib - xf:ib] * np.cos(t) + audio[ia - xf:ia] * np.sin(t)
    # gentle 5 ms fade-in at the very start (first play only)
    fi = int(0.005 * SR)
    out[:fi] *= np.linspace(0, 1, fi, dtype=np.float32)[:, None]
    # loudness of the loop body (what the player hears most)
    body = out[ia:ib]
    lufs_body, _ = A.loudness(body)
    gain = 10 ** ((TARGET_LUFS - lufs_body) / 20)
    out = out * gain
    ceiling = 10 ** (-1.0 / 20)
    if np.max(np.abs(out)) > ceiling:
        out = A.soft_limit(out, ceiling)
    lufs, peak = A.loudness(out[ia:ib])
    dest = OUT / f"{track}.ogg"
    A.encode_ogg(dest, out, quality=5.0)
    # junction check: 10 s before B, then 10 s after A (what the loop plays)
    junction = np.concatenate([out[ib - 10 * SR:ib], out[ia:ia + 10 * SR]])
    A.spectrogram_png(junction, CHECK / f"loopcheck_{track}.png", title=f"{track} loop junction (B->A at 10 s)", marks=[10.0])
    # discontinuity: band-energy jump across the junction vs the median frame-to-frame jump
    _, jb = features(junction.mean(axis=1))
    steps = np.abs(np.diff(jb, axis=0)).mean(axis=1)
    jf = int(10 * SR / HOP)
    jump = float(steps[jf - 2:jf + 2].max() / (np.percentile(steps, 95) + 1e-9))  # <1: smaller than a typical onset
    info = {"file": f"music/{track}.ogg", "source": stem, "bpm": round(60 / period, 2), "beats_per_bar": bpb,
            "loop_start": round(float(a), 4), "loop_end": round(float(ib / SR), 4), "length": round(len(out) / SR, 3),
            "loop_seconds": round(float(b - a), 2), "lufs": lufs, "peak_dbfs": peak, "junction_jump_ratio": round(jump, 2),
            "match_score": round(float(score), 3), "intro_seconds": round(float(a), 2)}
    print(json.dumps(info))
    return info


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] != "music":
        sys.exit(__doc__)
    tracks = sys.argv[2:] or list(CHOICES)
    data = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {"tracks": {}}
    for track in tracks:
        data["tracks"][track] = master(track)
    # cues and presentation-only overrides read by scripts/Audio/AudioService.cs
    data["crossfade_seconds"] = 2.0
    data["cues"] = {"menu": "music/menu.ogg", "puzzle": "music/puzzle.ogg", "tension": "music/tension.ogg",
                    "epilogue": "music/epilogue.ogg"}
    # CS06/CS07: the Viktor confrontation and the resolution in the Atlas chronochamber (S49)
    data["cutscenes"] = {"CS06": "tension", "CS07": "epilogue"}
    # S48/S49 (Atlas service pavilion, chronochamber) play the light tension cue until the confrontation is resolved (F17)
    data["rooms"] = {"S48": [{"cue": "tension", "until": "F17"}], "S49": [{"cue": "tension", "until": "F17"}]}
    data["note"] = ("Loop points in seconds: the engine plays the file once from 0, then loops from loop_start to "
                    "the end of the file (= loop_end; a one-beat crossfade is baked in). Built by art/tools/audio_master.py.")
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
