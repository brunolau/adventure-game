"""Task budget guard for the content v2 art run (2026-10-06 evening: S69 Sokolikovsky dvor, ZUZANA95, KUBO, the
Zuzana / yard items, state layers and epilogue stills; docs/story/SOKOLIKOVA_YARD.md section 6, ZUZANA.md).

Every paid call of the run goes through `guard(asset, usd)` before it is submitted: the spend log rows of this run
(asset prefixes below, logged since START) plus the calls in flight must stay within CAP. The rows themselves are
written by fal_api.run (serialised by npc_batch's lock).
"""
from __future__ import annotations

import csv
import threading

import chars
import fal_api
import hero_coat

# fal media reads stalled twice in this run (a NB2 gesture and the icon grid were billed, then lost in the download):
# every tool of the run keeps the raw result JSON (URLs) first and downloads with curl retries.
chars.save_outputs = hero_coat.save_result
fal_api.download = hero_coat.robust_download

START = "2026-10-06T17:45:00"
CAP = 12.0
PREFIXES = ("bg_natural/S69/", "characters/ZUZANA95/", "characters/KUBO/", "items/content_v2/",
            "variants/content_v2/", "cutscenes/content_v2/", "ambient/S69/")

_lock = threading.Lock()
_in_flight = 0.0


def spent() -> float:
    if not fal_api.SPEND_LOG.exists():
        return 0.0
    with fal_api.SPEND_LOG.open(encoding="utf-8") as handle:
        return sum(float(r["usd"]) for r in csv.DictReader(handle)
                   if r["asset"].startswith(PREFIXES) and r["timestamp"] >= START)


def reserve(asset: str, usd: float) -> None:
    global _in_flight
    if not asset.startswith(PREFIXES):
        raise ValueError(f"{asset}: not a content v2 asset prefix")
    with _lock:
        total = spent()
        if total + _in_flight + usd > CAP + 1e-9:
            raise fal_api.BudgetExceeded(f"{asset}: {total:.3f} spent + {_in_flight:.3f} in flight + {usd:.3f} "
                                         f"would exceed the task cap {CAP:.2f}")
        _in_flight += usd
        print(f"[content v2 budget] {total:.3f} spent, {_in_flight:.3f} in flight, cap {CAP:.2f}", flush=True)


def release(usd: float) -> None:
    global _in_flight
    with _lock:
        _in_flight -= usd


def run(model: str, arguments: dict, asset: str, usd: float, **kw) -> dict:
    """fal_api.run behind the task guard."""
    reserve(asset, usd)
    try:
        return fal_api.run(model, arguments, asset, usd, budget=None, **kw)
    finally:
        release(usd)


if __name__ == "__main__":
    print(f"content v2 art run: USD {spent():.3f} of {CAP:.2f} spent since {START}")
