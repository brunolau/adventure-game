"""Shared audio helpers for the LastBell audio pipeline (numpy + the imageio-ffmpeg binary).

decode() / encode_ogg() go through ffmpeg; loudness() uses ffmpeg's ebur128 (integrated LUFS,
true peak); spectrogram_png() draws an overview picture to judge a file by eye.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

FFMPEG = r"C:\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
SR = 44100


def ffmpeg(*args: str, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run([FFMPEG, "-hide_banner", "-nostdin", "-y", *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def decode(path: Path | str, sr: int = SR, channels: int = 2) -> np.ndarray:
    """Float32 array (frames, channels) at sr."""
    proc = subprocess.run([FFMPEG, "-hide_banner", "-nostdin", "-i", str(path), "-f", "f32le", "-acodec", "pcm_f32le",
                           "-ac", str(channels), "-ar", str(sr), "-"], check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    return np.frombuffer(proc.stdout, dtype=np.float32).reshape(-1, channels).copy()


def write_wav(path: Path | str, audio: np.ndarray, sr: int = SR) -> None:
    audio = np.clip(audio, -1, 1).astype(np.float32)
    proc = subprocess.run([FFMPEG, "-hide_banner", "-nostdin", "-y", "-f", "f32le", "-ar", str(sr), "-ac",
                           str(audio.shape[1]), "-i", "-", "-c:a", "pcm_s16le", str(path)],
                          input=audio.tobytes(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode(errors="replace")[-800:])


def encode_ogg(path: Path | str, audio: np.ndarray, sr: int = SR, quality: float = 5.0) -> None:
    """OGG Vorbis (libvorbis VBR quality q)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    audio = np.clip(audio, -1, 1).astype(np.float32)
    proc = subprocess.run([FFMPEG, "-hide_banner", "-nostdin", "-y", "-f", "f32le", "-ar", str(sr), "-ac",
                           str(audio.shape[1]), "-i", "-", "-c:a", "libvorbis", "-q:a", str(quality),
                           "-map_metadata", "-1", str(path)],
                          input=audio.tobytes(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode(errors="replace")[-800:])


def loudness(audio: np.ndarray, sr: int = SR) -> tuple[float, float]:
    """(integrated LUFS, true peak dBTP) by ffmpeg ebur128."""
    proc = subprocess.run([FFMPEG, "-hide_banner", "-nostdin", "-f", "f32le", "-ar", str(sr), "-ac", str(audio.shape[1]),
                           "-i", "-", "-af", "ebur128=peak=true", "-f", "null", "-"],
                          input=np.ascontiguousarray(audio, dtype=np.float32).tobytes(), stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    err = proc.stderr.decode(errors="replace")
    summary = err[err.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[0-9.]+|-inf) LUFS", summary)
    p = re.search(r"Peak:\s+(-?[0-9.]+|-inf) dBFS", summary)
    lufs = float(i.group(1)) if i and i.group(1) != "-inf" else -70.0
    peak = float(p.group(1)) if p and p.group(1) != "-inf" else -70.0
    return lufs, peak


def normalize(audio: np.ndarray, target_lufs: float, max_peak_db: float = -1.0, sr: int = SR) -> tuple[np.ndarray, float, float]:
    """Gain to target LUFS, then a soft limiter so the sample peak stays under max_peak_db."""
    lufs, _ = loudness(audio, sr)
    out = audio * (10 ** ((target_lufs - lufs) / 20))
    ceiling = 10 ** (max_peak_db / 20)
    peak = float(np.max(np.abs(out))) if out.size else 0.0
    if peak > ceiling:
        out = soft_limit(out, ceiling)
    lufs2, peak2 = loudness(out, sr)
    return out, lufs2, peak2


def moving_mean(x: np.ndarray, win: int) -> np.ndarray:
    """Moving average with a window of win samples ("valid" length), via cumulative sums."""
    c = np.cumsum(np.concatenate([[0.0], x.astype(np.float64)]))
    return ((c[win:] - c[:-win]) / win).astype(np.float32)


def soft_limit(audio: np.ndarray, ceiling: float) -> np.ndarray:
    """Look-ahead-free smooth limiter: gain envelope from a smoothed peak follower."""
    mag = np.max(np.abs(audio), axis=1)
    need = np.maximum(mag / ceiling, 1.0)
    # attack instant (max filter over 5 ms), release 80 ms
    win = max(1, int(0.005 * SR))
    padded = np.pad(need, (win, win), mode="edge")
    from numpy.lib.stride_tricks import sliding_window_view
    held = sliding_window_view(padded, 2 * win + 1).max(axis=1)[: len(need)]
    rel = np.exp(-1.0 / (0.08 * SR))
    env = np.empty_like(held)
    cur = 1.0
    for i, v in enumerate(held):  # fine for a few million samples
        cur = v if v > cur else max(v, cur * rel + v * (1 - rel))
        env[i] = cur
    return audio / env[:, None]


def spectrogram_png(audio: np.ndarray, path: Path | str, sr: int = SR, title: str = "", marks: list[float] | None = None) -> None:
    """Log-frequency spectrogram (top) and RMS envelope (bottom), 1600x520."""
    mono = audio.mean(axis=1)
    n_fft, hop = 2048, 1024
    frames = 1 + max(0, (len(mono) - n_fft) // hop)
    win = np.hanning(n_fft).astype(np.float32)
    spec = np.empty((frames, n_fft // 2 + 1), dtype=np.float32)
    for f in range(frames):
        seg = mono[f * hop:f * hop + n_fft]
        spec[f] = np.abs(np.fft.rfft(seg * win))
    db = 20 * np.log10(spec + 1e-6)
    freqs = np.fft.rfftfreq(n_fft, 1 / sr)
    rows = 360
    edges = np.geomspace(40, 16000, rows + 1)
    img = np.zeros((rows, frames), dtype=np.float32)
    for r in range(rows):
        sel = (freqs >= edges[r]) & (freqs < edges[r + 1])
        img[rows - 1 - r] = db[:, sel].max(axis=1) if sel.any() else db[:, np.argmin(np.abs(freqs - edges[r]))]
    img = np.clip((img - (img.max() - 80)) / 80, 0, 1)
    width = 1600
    pic = Image.fromarray((img * 255).astype(np.uint8)).resize((width, rows))
    canvas = Image.new("RGB", (width, rows + 160), "black")
    canvas.paste(Image.merge("RGB", (pic, pic.point(lambda v: v * 0.7), pic.point(lambda v: 255 - v if v > 0 else 0))), (0, 0))
    draw = ImageDraw.Draw(canvas)
    rms = np.sqrt(moving_mean(mono ** 2, 4410))[::441]
    rms_db = 20 * np.log10(rms + 1e-6)
    xs = np.linspace(0, width - 1, len(rms_db))
    pts = [(float(x), rows + 150 - float(np.clip((v + 60) / 60, 0, 1)) * 140) for x, v in zip(xs, rms_db)]
    draw.line(pts, fill=(80, 220, 120), width=1)
    dur = len(mono) / sr
    for t in range(0, int(dur) + 1, 10):
        x = t / dur * width
        draw.line([(x, rows), (x, rows + 8)], fill="white")
        if t % 30 == 0:
            draw.text((x + 2, rows + 8), f"{t}s", fill="white")
    for m in marks or []:
        x = m / dur * width
        draw.line([(x, 0), (x, rows + 160)], fill=(255, 60, 60), width=2)
    draw.text((8, 6), f"{title}  {dur:.1f}s", fill="yellow")
    for hz in (100, 1000, 3000, 8000):
        y = rows - 1 - int(np.searchsorted(edges, hz))
        draw.text((width - 60, y), f"{hz}Hz", fill="yellow")
    canvas.save(path)
