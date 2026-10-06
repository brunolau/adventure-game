"""Voice trial helpers: fal.ai TTS / STT calls (logged in art/spend-log.csv through art/tools/fal_api.run),
text preparation, measurements, word error rate and the local post-processing chain
(trim silence, optional telephone EQ, loudness normalisation, fades, OGG Vorbis).
"""
from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "art" / "tools"))
import audio_lib  # noqa: E402
import fal_api  # noqa: E402

SR = 44100
BUDGET = ("voice/", 15.0)  # owner-approved cap for this trial, USD

# fal pricing API (api.fal.ai/v1/models/pricing), read 2026-10-06: USD per 1000 characters.
TTS_PRICE = {
    "elevenlabs/tts/eleven-v4": 0.08,
    "elevenlabs/tts/eleven-v4-turbo": 0.04,
    "google/gemini-3.8-flash-tts": 0.045,
    "fal-ai/minimax/speech-2.8-hd": 0.10,
}
SCRIBE = "fal-ai/elevenlabs/speech-to-text/scribe-v2"   # 0.008 USD per audio minute
WIZPER = "fal-ai/wizper"                                # 0.000625 USD per compute second (~1-3 s per line)
WIZPER_USD = 0.002                                      # logged conservatively per call


# --------------------------------------------------------------------------- text

def tts_text(text: str) -> str:
    """Spoken form for the TTS: typographic quotes removed, all-caps words (ZVON, NEPREPISOVAŤ) in normal case so
    they are read as words and not spelled; two-letter abbreviations (QR) stay."""
    t = text.replace("„", "").replace("“", "").replace("”", "").replace("\"", "")

    def fix(m: re.Match) -> str:
        w = m.group(0)
        return w.capitalize() if len(w) >= 3 else w
    t = re.sub(r"\b[A-ZÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽ]{3,}\b", fix, t)
    return t.strip()


def norm_words(text: str) -> list[str]:
    t = unicodedata.normalize("NFC", text.lower())
    t = re.sub(r"[„“”\"'’‚.,!?;:()\[\]…–—-]", " ", t)
    return [w for w in t.split() if w]


def strip_diacritics(w: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", w) if unicodedata.category(c) != "Mn")


def edit_ops(ref: list[str], hyp: list[str]) -> tuple[int, list[tuple[str, str]]]:
    """Levenshtein distance on word lists plus the list of (ref, hyp) substitutions/insertions/deletions."""
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1]))
    ops, i, j = [], n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1]):
            if ref[i - 1] != hyp[j - 1]:
                ops.append((ref[i - 1], hyp[j - 1]))
            i, j = i - 1, j - 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            ops.append((ref[i - 1], ""))
            i -= 1
        else:
            ops.append(("", hyp[j - 1]))
            j -= 1
    return d[n][m], ops[::-1]


def wer(ref_text: str, hyp_text: str) -> dict:
    ref, hyp = norm_words(ref_text), norm_words(hyp_text)
    dist, ops = edit_ops(ref, hyp)
    # diacritics-insensitive distance separates "wrong word" from "STT dropped a háček"
    dist_nd, _ = edit_ops([strip_diacritics(w) for w in ref], [strip_diacritics(w) for w in hyp])
    n = max(1, len(ref))
    return {"wer": round(dist / n, 3), "wer_nodiac": round(dist_nd / n, 3), "errors": ops, "ref_words": len(ref)}


# --------------------------------------------------------------------------- fal calls

def tts(model: str, text: str, voice: dict, asset: str) -> dict:
    """One paid TTS call; returns {'url', 'raw_ext'}."""
    usd = len(text) / 1000 * TTS_PRICE[model]
    if model.startswith("elevenlabs/"):
        args = {"text": text, "voice": voice["voice"], "language_code": "sk", "output_format": "mp3_44100_192",
                "stability": voice.get("stability", 0.5), "similarity_boost": voice.get("similarity", 0.75)}
        if "seed" in voice:
            args["seed"] = voice["seed"]
        res = fal_api.run(model, args, asset, usd, budget=BUDGET, poll_s=1.0)
        return {"url": res["audio"]["url"], "raw_ext": ".mp3"}
    if model.startswith("google/gemini"):
        args = {"prompt": text, "voice": voice["voice"], "style_instructions": voice.get("style")}
        res = fal_api.run(model, args, asset, usd, budget=BUDGET, poll_s=1.0)
        return {"url": res["audio"]["url"], "raw_ext": ".wav"}
    if model.startswith("fal-ai/minimax"):
        vs = {"voice_id": voice["voice"], "speed": voice.get("speed", 1.0), "vol": 1, "pitch": voice.get("pitch", 0)}
        if voice.get("emotion"):
            vs["emotion"] = voice["emotion"]
        args = {"prompt": text, "voice_setting": vs, "language_boost": "Slovak", "output_format": "url",
                "audio_setting": {"sample_rate": 44100, "bitrate": 128000, "format": "mp3", "channel": 1}}
        res = fal_api.run(model, args, asset, usd, budget=BUDGET, poll_s=1.0)
        return {"url": res["audio"]["url"], "raw_ext": ".mp3"}
    raise KeyError(model)


def stt_scribe(url: str, seconds: float, asset: str) -> str:
    usd = max(seconds, 1.0) / 60 * 0.008
    res = fal_api.run(SCRIBE, {"audio_url": url, "language_code": "slk", "diarize": False,
                                "tag_audio_events": False}, asset, usd, budget=BUDGET, poll_s=1.0)
    return res.get("text", "").strip()


def stt_wizper(url: str, asset: str) -> str:
    res = fal_api.run(WIZPER, {"audio_url": url, "language": "sk", "task": "transcribe"}, asset, WIZPER_USD,
                      budget=BUDGET, poll_s=1.0)
    return res.get("text", "").strip()


# --------------------------------------------------------------------------- audio

def load_mono(path: Path) -> np.ndarray:
    return audio_lib.decode(path, SR, 1)[:, 0]


def measure(x: np.ndarray, text: str) -> dict:
    """Raw-file checks: duration, leading/trailing silence, clipping, long inner pauses, speaking rate."""
    dur = len(x) / SR
    win = int(0.02 * SR)
    frames = len(x) // win
    if frames == 0:
        return {"raw_s": round(dur, 2)}
    rms = np.sqrt(np.mean(x[: frames * win].reshape(frames, win) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    thr = max(db.max() - 40, -60)
    voiced = np.where(db > thr)[0]
    lead = voiced[0] * 0.02 if len(voiced) else dur
    trail = (frames - 1 - voiced[-1]) * 0.02 if len(voiced) else dur
    # longest run of silence inside the speech
    longest, run = 0, 0
    for v in (db[voiced[0]:voiced[-1] + 1] <= thr) if len(voiced) else []:
        run = run + 1 if v else 0
        longest = max(longest, run)
    speech = max(0.01, dur - lead - trail)
    clip = float(np.mean(np.abs(x) >= 0.995))
    return {"raw_s": round(dur, 2), "lead_s": round(lead, 2), "trail_s": round(trail, 2),
            "speech_s": round(speech, 2), "longest_pause_s": round(longest * 0.02, 2),
            "chars_per_s": round(len(text) / speech, 1), "clip_frac": round(clip, 5),
            "peak_db": round(20 * np.log10(max(1e-9, float(np.max(np.abs(x))))), 1)}


def _ffmpeg_filter(x: np.ndarray, af: str) -> np.ndarray:
    proc = subprocess.run([audio_lib.FFMPEG, "-hide_banner", "-nostdin", "-f", "f32le", "-ar", str(SR), "-ac", "1",
                           "-i", "-", "-af", af, "-f", "f32le", "-ar", str(SR), "-ac", "1", "-"],
                          input=np.ascontiguousarray(x, dtype=np.float32).tobytes(), stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True)
    return np.frombuffer(proc.stdout, dtype=np.float32).copy()


def trim(x: np.ndarray, pad_s: float = 0.06) -> np.ndarray:
    win = int(0.01 * SR)
    frames = len(x) // win
    rms = np.sqrt(np.mean(x[: frames * win].reshape(frames, win) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    thr = max(db.max() - 42, -62)
    voiced = np.where(db > thr)[0]
    if not len(voiced):
        return x
    a = max(0, voiced[0] * win - int(pad_s * SR))
    b = min(len(x), (voiced[-1] + 1) * win + int((pad_s + 0.04) * SR))
    return x[a:b]


def telephone(x: np.ndarray) -> np.ndarray:
    """Light telephone colour: 300-3400 Hz band, a little mid presence and soft saturation."""
    y = _ffmpeg_filter(x, "highpass=f=300:poles=2,highpass=f=300:poles=2,lowpass=f=3400:poles=2,"
                          "lowpass=f=3600:poles=2,equalizer=f=1700:t=q:w=1.2:g=4")
    y = np.tanh(y * 2.0) / np.tanh(2.0)
    return 0.8 * y + 0.2 * _ffmpeg_filter(x, "highpass=f=500,lowpass=f=2800")


def finish(x: np.ndarray, phone: bool, target_lufs: float = -16.0) -> tuple[np.ndarray, float, float]:
    x = trim(x)
    x = x - float(np.mean(x))
    if phone:
        x = telephone(x)
    st = x[:, None]
    st, lufs, peak = audio_lib.normalize(st, target_lufs, max_peak_db=-1.5, sr=SR)
    y = st[:, 0]
    fi, fo = int(0.008 * SR), int(0.04 * SR)
    y[:fi] *= np.linspace(0, 1, fi)
    y[-fo:] *= np.linspace(1, 0, fo)
    return y, lufs, peak


def write_ogg(path: Path, y: np.ndarray, quality: float = 4.0) -> None:
    audio_lib.encode_ogg(path, y[:, None], SR, quality)
