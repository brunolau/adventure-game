"""Recast 2026-10-06: per-speaker voice features of the v2 takes next to the v1 trial (free, local).
Writes art/voice/recast/v2_features.json. usage: python recast_stats.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402
import voice_features as F  # noqa: E402
import recast as R  # noqa: E402


def main() -> None:
    by: dict[str, list[dict]] = {}
    irony_cps, plain_cps, lufs, peaks = [], [], [], []
    for r in R.records():
        x = V.trim(V.load_mono(R.RAW / r["best"]["raw"]))
        f = F.features(x)
        f["cps"] = r["best"]["measure"]["chars_per_s"]
        by.setdefault(r["speaker"], []).append(f)
        (irony_cps if r["delivery"] else plain_cps).append(f["cps"])
        lufs.append(r["lufs"])
        peaks.append(r["peak_dbtp"])
    out = {sp: {k: round(float(np.median([f[k] for f in fs])), 3) for k in fs[0]} | {"n": len(fs)} for sp, fs in by.items()}
    out["_summary"] = {"irony_mean_cps": round(float(np.mean(irony_cps)), 2), "plain_mean_cps": round(float(np.mean(plain_cps)), 2),
                       "lufs_min": min(lufs), "lufs_max": max(lufs), "peak_max_dbtp": max(peaks)}
    (V.ROOT / "art/voice/recast/v2_features.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    v1 = json.loads((V.ROOT / "art/voice/recast/v1_features.json").read_text(encoding="utf-8"))
    for sp, f in out.items():
        if sp.startswith("_"):
            continue
        o = v1[sp]
        print(f"{sp:7} F0 {o['f0_median_hz']:6.1f} -> {f['f0_median_hz']:6.1f} Hz | centroid {o['centroid_hz']:6.0f} -> {f['centroid_hz']:6.0f} | "
              f"range {o['f0_range_semitones']:4.1f} -> {f['f0_range_semitones']:4.1f} st | aper {o['aperiodicity']:.3f} -> {f['aperiodicity']:.3f} | "
              f"cps {o['cps']:4.1f} -> {f['cps']:4.1f}")
    print(out["_summary"])


if __name__ == "__main__":
    main()
