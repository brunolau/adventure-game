"""Measurable voice features for casting without ears: pitch (F0 by YIN), pitch range, spectral centroid,
high-band share and aperiodicity (a breathiness / rasp proxy).

usage as a module: features(x_mono_44k) -> dict; as a script: python voice_features.py <file.ogg|wav>...
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402

SR16 = 16000


def _resample16(x: np.ndarray) -> np.ndarray:
    # 44.1k -> 16k by linear interpolation after a crude 7 kHz low-pass (moving average is enough for F0 work)
    k = 3
    xf = np.convolve(x, np.ones(k) / k, mode="same")
    t = np.arange(0, len(xf) / V.SR, 1 / SR16)
    return np.interp(t, np.arange(len(xf)) / V.SR, xf).astype(np.float32)


def yin_f0(x16: np.ndarray, fmin: float = 60, fmax: float = 450, win: int = 640, hop: int = 160,
           thr: float = 0.15) -> tuple[np.ndarray, np.ndarray]:
    """Return (f0 per frame, 0 = unvoiced; aperiodicity per voiced frame)."""
    tmax = int(SR16 / fmin)
    tmin = int(SR16 / fmax)
    L = win + tmax
    if len(x16) < L + hop:
        return np.zeros(0), np.zeros(0)
    n = (len(x16) - L) // hop
    idx = np.arange(L)[None, :] + hop * np.arange(n)[:, None]
    fr = x16[idx]
    rms = np.sqrt(np.mean(fr[:, :win] ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    loud = db > db.max() - 35
    nfft = 1 << int(np.ceil(np.log2(2 * L)))
    A = np.fft.rfft(fr[:, :win], nfft)
    B = np.fft.rfft(fr, nfft)
    corr = np.fft.irfft(np.conj(A) * B, nfft)[:, : tmax + 1]
    sq = np.cumsum(np.concatenate([np.zeros((n, 1)), fr ** 2], axis=1), axis=1)
    e0 = sq[:, win][:, None]
    taus = np.arange(tmax + 1)
    etau = sq[:, taus + win] - sq[:, taus]
    d = e0 + etau - 2 * corr
    d[:, 0] = 0
    cm = np.cumsum(d[:, 1:], axis=1)
    dn = np.ones_like(d)
    dn[:, 1:] = d[:, 1:] * taus[1:] / np.maximum(cm, 1e-12)
    f0 = np.zeros(n)
    ap = np.full(n, np.nan)
    for i in np.where(loud)[0]:
        row = dn[i, tmin:]
        below = np.where(row < thr)[0]
        if len(below):
            j = below[0]
            while j + 1 < len(row) and row[j + 1] < row[j]:
                j += 1
        else:
            j = int(np.argmin(row))
            if row[j] > 0.35:
                continue
        tau = j + tmin
        if 1 <= tau < tmax:  # parabolic refinement
            a, b, c = dn[i, tau - 1], dn[i, tau], dn[i, tau + 1]
            den = a - 2 * b + c
            tau = tau + (0.5 * (a - c) / den if abs(den) > 1e-9 else 0)
        f0[i] = SR16 / tau
        ap[i] = row[j]
    return f0, ap


def features(x: np.ndarray) -> dict:
    x16 = _resample16(x)
    f0, ap = yin_f0(x16)
    v = f0[f0 > 0]
    if len(v) > 10:
        # octave-error guard: keep frames within an octave of the median
        med = np.median(v)
        v = v[(v > med / 1.8) & (v < med * 1.8)]
    semis = 12 * np.log2(v / np.median(v)) if len(v) else np.zeros(1)
    # spectrum on the 44.1k signal (speech frames only)
    w = 2048
    nfr = len(x) // w
    if nfr:
        fr = x[: nfr * w].reshape(nfr, w) * np.hanning(w)
        rms = np.sqrt(np.mean(fr ** 2, axis=1) + 1e-12)
        keep = 20 * np.log10(rms) > 20 * np.log10(rms.max()) - 30
        P = np.abs(np.fft.rfft(fr[keep], axis=1)) ** 2
        f = np.fft.rfftfreq(w, 1 / V.SR)
        tot = P.sum(axis=1) + 1e-12
        cent = float(np.mean((P * f).sum(axis=1) / tot))
        hi = float(np.mean(P[:, f > 3000].sum(axis=1) / tot))
    else:
        cent, hi = 0.0, 0.0
    return {"f0_median_hz": round(float(np.median(v)), 1) if len(v) else 0.0,
            "f0_p10_hz": round(float(np.percentile(v, 10)), 1) if len(v) else 0.0,
            "f0_p90_hz": round(float(np.percentile(v, 90)), 1) if len(v) else 0.0,
            "f0_range_semitones": round(float(np.percentile(semis, 90) - np.percentile(semis, 10)), 1),
            "voiced_share": round(float(len(v) / max(1, len(f0))), 2),
            "aperiodicity": round(float(np.nanmean(ap)), 3) if np.any(~np.isnan(ap)) else 0.0,
            "centroid_hz": round(cent), "hi_band_share": round(hi, 4)}


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(Path(p).name, features(V.load_mono(Path(p))))
