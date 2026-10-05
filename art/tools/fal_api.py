"""Shared fal.ai client for the LastBell art pipeline.

Provides key lookup, the queue API (submit, poll, fetch result), image encoding as data URIs,
downloads, and spend logging with a hard budget guard.

Every paid call goes through `run()`, which
  1. refuses to submit when the logged spend for the given budget scope plus the call's price
     would exceed the scope's cap, and
  2. appends one row to art/spend-log.csv (timestamp, model, asset, usd) once the call completed
     (or timed out, in which case it is assumed to be charged).
"""
from __future__ import annotations

import base64
import csv
import datetime
import io
import os
import sys
import time
from pathlib import Path

import requests
from PIL import Image

ART = Path(__file__).resolve().parent.parent
SPEND_LOG = ART / "spend-log.csv"
USER_AGENT = "LastBell-ArtPipeline/0.1 (+https://github.com/brunolau/adventure-game)"
QUEUE_BASE = "https://queue.fal.run"

# Documented prices (USD) taken from fal.ai model pages on 2026-10-05.
# Image editors: per image. Video models: functions of (duration seconds, resolution).
IMAGE_PRICES = {
    ("fal-ai/nano-banana-pro/edit", "1K"): 0.15,
    ("fal-ai/nano-banana-pro/edit", "2K"): 0.15,
    ("fal-ai/nano-banana-pro/edit", "4K"): 0.30,
    ("fal-ai/nano-banana-2/edit", "0.5K"): 0.06,
    ("fal-ai/nano-banana-2/edit", "1K"): 0.08,
    ("fal-ai/nano-banana-2/edit", "2K"): 0.12,
    ("fal-ai/nano-banana-2/edit", "4K"): 0.16,
}


def video_price(model: str, seconds: float, resolution: str) -> float:
    """Documented price of one image-to-video call."""
    if model.startswith("fal-ai/kling-video/v2.5-turbo/pro"):
        return 0.35 + 0.07 * max(0.0, seconds - 5)
    if model.startswith("fal-ai/minimax/hailuo-02/pro"):
        return 0.08 * seconds
    if model.startswith("fal-ai/minimax/hailuo-02/standard"):
        return 0.045 * seconds
    if model.startswith("fal-ai/bytedance/seedance/v1/pro/fast"):
        # fal: 1M video tokens = $1, tokens = w*h*fps*s/1024; page examples: 480p 5 s $0.061, 720p 5 s $0.137.
        per_5s = {"480p": 0.061, "720p": 0.137, "1080p": 0.243}[resolution]
        return per_5s * seconds / 5
    if model.startswith("fal-ai/wan/v2.2-a14b/image-to-video"):
        return {"480p": 0.04, "580p": 0.06, "720p": 0.08}[resolution] * seconds
    if model.startswith("fal-ai/veo3.1/fast"):
        return 0.10 * seconds
    raise KeyError(f"no documented price for {model}")


def fal_key() -> str:
    """FAL_KEY from the environment, else from HKCU\\Environment on Windows."""
    key = os.environ.get("FAL_KEY")
    if not key and sys.platform == "win32":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as handle:
            key, _ = winreg.QueryValueEx(handle, "FAL_KEY")
    if not key:
        sys.exit("FAL_KEY not found")
    return key


def image_data_uri(image: Image.Image | Path | str, max_side: int | None = None, fmt: str = "PNG") -> str:
    """Encode an image (path or PIL image) as a data URI, optionally downscaled to max_side."""
    img = Image.open(image) if isinstance(image, (str, Path)) else image
    if max_side and max(img.size) > max_side:
        scale = max_side / max(img.size)
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    if fmt.upper() == "JPEG":
        img.convert("RGB").save(buf, "JPEG", quality=92)
        mime = "image/jpeg"
    else:
        img.save(buf, "PNG")
        mime = "image/png"
    return f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode()


def logged_spend(scope_prefix: str = "") -> float:
    """Sum of logged USD for rows whose asset starts with scope_prefix."""
    if not SPEND_LOG.exists():
        return 0.0
    with SPEND_LOG.open(encoding="utf-8") as handle:
        return sum(float(row["usd"]) for row in csv.DictReader(handle) if row["asset"].startswith(scope_prefix))


def log_spend(model: str, asset: str, usd: float) -> None:
    # Parallel processes append to the same log; an exclusive lock file serialises the appends (one row was lost
    # in an unlocked batch of ~24 parallel calls, PIPELINE.md section 10). A stale lock (> 20 s) is broken.
    lock = SPEND_LOG.with_name(SPEND_LOG.name + ".lock")
    fd, deadline = None, time.time() + 60
    while fd is None:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > 20:
                    lock.unlink()
            except OSError:
                pass
            if time.time() > deadline:
                break
            time.sleep(0.05)
    try:
        new_file = not SPEND_LOG.exists()
        with SPEND_LOG.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            if new_file:
                writer.writerow(["timestamp", "model", "asset", "usd"])
            writer.writerow([datetime.datetime.now().isoformat(timespec="seconds"), model, asset, f"{usd:.3f}"])
    finally:
        if fd is not None:
            os.close(fd)
            try:
                lock.unlink()
            except OSError:
                pass


class BudgetExceeded(RuntimeError):
    pass


def run(model: str, arguments: dict, asset: str, usd: float, budget: tuple[str, float] | None = None,
        timeout_s: int = 900, poll_s: float = 4.0) -> dict:
    """Submit a request to the fal queue, wait for it, log the spend and return the result JSON.

    budget = (asset scope prefix, cap in USD); the call is refused if it would push the scope over the cap.
    """
    if budget:
        scope, cap = budget
        spent = logged_spend(scope)
        if spent + usd > cap + 1e-9:
            raise BudgetExceeded(f"{asset}: {spent:.3f} + {usd:.3f} USD would exceed the {cap:.2f} USD cap")
    headers = {"Authorization": f"Key {fal_key()}", "Content-Type": "application/json", "User-Agent": USER_AGENT}
    submit = requests.post(f"{QUEUE_BASE}/{model}", headers=headers, json=arguments, timeout=120)
    if submit.status_code not in (200, 201, 202):
        raise RuntimeError(f"{model} submit failed: HTTP {submit.status_code}: {submit.text[:500]}")
    ticket = submit.json()
    status_url, response_url = ticket["status_url"], ticket["response_url"]
    deadline = time.time() + timeout_s
    while True:
        status = requests.get(status_url, headers=headers, timeout=60).json().get("status")
        if status == "COMPLETED":
            break
        if time.time() > deadline:
            log_spend(model, asset + " (timeout, assumed charged)", usd)
            raise TimeoutError(f"{model} request {ticket['request_id']} still {status} after {timeout_s}s")
        time.sleep(poll_s)
    result = requests.get(response_url, headers=headers, timeout=120)
    if result.status_code != 200:
        # Failed generations are not billed by fal; record nothing but report the error.
        raise RuntimeError(f"{model} failed: HTTP {result.status_code}: {result.text[:800]}")
    log_spend(model, asset, usd)
    return result.json()


def download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=300, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    dest.write_bytes(response.content)
    return dest
