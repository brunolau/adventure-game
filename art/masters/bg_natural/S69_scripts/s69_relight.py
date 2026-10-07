"""S69 Sokolikovsky dvor: relight the accepted painting (v6, afternoon) to the evening sunset light of S18 next door.

Owner 2026-10-07 (round 2 approval, promised cosmetic fix): S69 is in afternoon light while the neighbouring kiosk
street S18 is at sunset; match S69 to S18's evening light. Constraints: style A, at most USD 0.45 of fal.ai, the camera,
the blocking and every rect pixel-identical, ambient re-cut.

Method ("light transfer", so no pixel moves):
  paint   ONE nano-banana-pro edit (USD 0.15): image 1 = S69_v6, image 2 = S18's painting as the light reference;
          the model repaints the light only. Its output is a light GUIDE, never pasted: it may drift or redraw details.
  apply   (free) align the guide to v6, take the low-frequency colour ratio guide / v6 per channel (an edge-aware
          guided filter on v6, so the light follows the painting's own edges and nothing halos), clamp it and multiply
          v6 by it -> S69_v<N>. Every edge, object, decal (the 3-2-6 panels, the hopscotch, the tally), the bench and
          the bike stay exactly where they were; only the light and colour change.
  review  side-by-side board v6 / guide / result / S18 for the review folder (free).

Run from the repo root: PYTHONIOENCODING=utf-8 python -X utf8 art/masters/bg_natural/S69_scripts/s69_relight.py ...
"""
from __future__ import annotations

import argparse
import datetime
import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "art" / "tools"))
import fal_api  # noqa: E402
import paint_natural  # noqa: E402
import paint_room as pr  # noqa: E402
import refit_room  # noqa: E402

paint_natural.install()   # masters in art/masters/bg_natural/

ROOM = "S69"
BASE_VERSION = 6
SCOPE = "bg_natural/S69/relight"
CAP_USD = 0.45
S18_MASTER = ROOT / "art" / "masters" / "bg_natural" / "S18_v6.png"
REVIEW = ROOT / "art" / "review" / "natural"

PROMPT = (
    "Image 1 is a finished painting of a walled courtyard playground between panel blocks, painted on a June "
    "afternoon. Image 2 is a painting of the street right next to it, painted at sunset. Relight image 1 so that it is "
    "the same evening as image 2: the same low warm golden sunset light coming from the left, the same warm "
    "orange-pink sky with soft sunset clouds where the sky shows through the trees, warm golden light on the tree tops, "
    "the upper floors of the panel block and the top edges of the concrete walls, longer and softer blue-violet "
    "shadows on the court, the walls and the lawn, slightly deeper and cooler shade under the trees, the overall "
    "colour balance and contrast of image 2.\n\n"
    "Change ONLY the light, the colours and the shadows. Keep the composition, the camera, the perspective and every "
    "object exactly as they are, at the same place and size: the concrete wall panels, the three small painted panels "
    "on the right wall (their shapes and colours stay readable), the chalk hopscotch on the asphalt, the green bench, "
    "the small red bicycle, the lamp, the birch, the blue spruce, every tree, branch and leaf, the building and its "
    "windows. Do not add, remove or move anything; no people, no animals, no text, no letters, no numbers, no logos. "
    "Do not copy anything from image 2 except its light. The result is image 1 relit, same 16:9 framing, no frames, "
    "borders or captions."
)


def master(version: int) -> Image.Image:
    img, _ = refit_room.load_master(ROOM, version)
    return img


def cmd_paint(args) -> None:
    base = master(BASE_VERSION)
    s18 = Image.open(S18_MASTER).convert("RGB")
    prompt = PROMPT + "\n\n" + pr.style_sentence()
    seed = args.seed if args.seed is not None else random.randint(1, 2 ** 31 - 1)
    stamp = datetime.datetime.now().strftime("%H%M%S")
    asset = f"{SCOPE}/{ROOM}_v{BASE_VERSION}_sunset_{stamp}"
    arguments = {"prompt": prompt,
                 "image_urls": [fal_api.image_data_uri(base, fmt="PNG"),
                                fal_api.image_data_uri(s18, max_side=2048, fmt="JPEG")],
                 "aspect_ratio": pr.ASPECT, "resolution": pr.RESOLUTION, "output_format": "png", "num_images": 1,
                 "seed": seed}
    price = fal_api.IMAGE_PRICES[(pr.MODEL, pr.RESOLUTION)]
    started = datetime.datetime.now().isoformat(timespec="seconds")
    result = fal_api.run(pr.MODEL, arguments, asset, price, budget=(SCOPE, CAP_USD), timeout_s=900)
    raw = pr.MASTERS / f"_{ROOM}_relight_guide_{stamp}.png"
    fal_api.download(result["images"][0]["url"], raw)
    raw.with_suffix(".json").write_text(json.dumps({
        "kind": "relight guide (paid edit, never pasted)", "base": f"{ROOM}_v{BASE_VERSION}", "model": pr.MODEL,
        "seed": result.get("seed", seed), "usd": price, "spend_log_asset": asset, "started": started,
        "light_reference": S18_MASTER.relative_to(ROOT).as_posix(), "prompt": prompt,
        "model_description": result.get("description")}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(raw.relative_to(ROOT))


# --------------------------------------------------------------------------- light transfer

def box(a: np.ndarray, r: int) -> np.ndarray:
    """Mean over a (2r+1)^2 window (edge-replicated), per channel, via an integral image."""
    pad = np.pad(a, ((r + 1, r), (r + 1, r)) + ((0, 0),) * (a.ndim - 2), mode="edge")
    c = pad.cumsum(0).cumsum(1)
    n = 2 * r + 1
    s = c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n]
    return s / (n * n)


def guided(guide: np.ndarray, src: np.ndarray, r: int, eps: float) -> np.ndarray:
    """He et al. guided filter with a grey guide (float arrays, guide HxW, src HxWxC)."""
    g = guide[..., None]
    mg, ms = box(g, r), box(src, r)
    cov = box(g * src, r) - mg * ms
    var = box(g * g, r) - mg * mg
    a = cov / (var + eps)
    b = ms - a * mg
    return box(a, r) * g + box(b, r)


def to_lin(x: np.ndarray) -> np.ndarray:
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def to_srgb(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)


def transfer(base: Image.Image, guide: Image.Image, radius: int, eps: float, lo: float, hi: float) -> Image.Image:
    b = to_lin(np.asarray(base, dtype=np.float64) / 255.0)
    g = to_lin(np.asarray(guide, dtype=np.float64) / 255.0)
    # the ratio is taken on blurred versions (local light level), then made edge-aware on the base painting
    bb, gb = box(b, radius), box(g, radius)
    ratio = np.clip((gb + 0.004) / (bb + 0.004), lo, hi)
    grey = b @ np.array([0.2126, 0.7152, 0.0722])
    ratio = guided(grey, ratio, radius, eps)
    out = to_srgb(b * np.clip(ratio, lo, hi))
    return Image.fromarray((out * 255 + 0.5).astype(np.uint8))


def cmd_apply(args) -> None:
    base = master(BASE_VERSION)
    raw_path = ROOT / args.raw
    guide = Image.open(raw_path).convert("RGB")
    if guide.size != pr.MODEL_FRAME:
        guide = guide.resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    full = Image.new("L", pr.MODEL_FRAME, 255)
    # align on edges (the light differs, so compare gradients rather than values)
    dx, dy = refit_room.align_shift(edges(guide), edges(base), full)
    if dx or dy:
        guide = ImageChops.offset(guide, -dx, -dy)
        print(f"guide drifted by {dx:+d},{dy:+d} master px; compensated")
    out = transfer(base, guide, args.radius, args.eps, args.lo, args.hi)
    version = pr.next_version(ROOM)
    path = pr.MASTERS / f"{ROOM}_v{version}.png"
    out.save(path)
    meta = json.loads(raw_path.with_suffix(".json").read_text(encoding="utf-8")) if raw_path.with_suffix(".json").exists() else {}
    path.with_suffix(".json").write_text(json.dumps({
        "kind": "relight (light transfer from a paid guide; every pixel of v6 keeps its place)",
        "from_version": BASE_VERSION, "usd": 0, "guide": raw_path.relative_to(ROOT).as_posix(),
        "guide_usd": meta.get("usd"), "guide_seed": meta.get("seed"), "guide_drift_compensated_master_px": [dx, dy],
        "transfer": {"space": "linear RGB", "box_radius_master_px": args.radius, "guided_eps": args.eps,
                     "ratio_clamp": [args.lo, args.hi]},
        "light_reference": "S18_v6 (sunset)", "room": ROOM, "version": version, "output_size": list(out.size),
        "started": datetime.datetime.now().isoformat(timespec="seconds")}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(path.relative_to(ROOT))


def edges(img: Image.Image) -> Image.Image:
    a = np.asarray(img.convert("L"), dtype=np.float32)
    gx = np.abs(np.diff(a, axis=1, append=a[:, -1:]))
    gy = np.abs(np.diff(a, axis=0, append=a[-1:, :]))
    return Image.fromarray(np.clip((gx + gy) * 2, 0, 255).astype(np.uint8))


def cmd_review(args) -> None:
    base = pr.fit_to_frame(master(BASE_VERSION)).convert("RGB")
    out = pr.fit_to_frame(master(args.version)).convert("RGB")
    s18 = Image.open(ROOT / "src/game/assets/bg_natural/S18.webp").convert("RGB")
    tiles = [base, out, s18]
    if args.raw:
        tiles.insert(1, pr.fit_to_frame(Image.open(ROOT / args.raw).convert("RGB").resize(pr.MODEL_FRAME)).convert("RGB"))
    w, h = 960, 540
    board = Image.new("RGB", (w * 2, h * ((len(tiles) + 1) // 2)), (0, 0, 0))
    for i, t in enumerate(tiles):
        board.paste(t.resize((w, h), Image.Resampling.LANCZOS), ((i % 2) * w, (i // 2) * h))
    REVIEW.mkdir(parents=True, exist_ok=True)
    p = REVIEW / f"{ROOM}_relight_v{args.version}_board.png"
    board.save(p)
    print(p.relative_to(ROOT))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("paint")
    p.add_argument("--seed", type=int)
    p = sub.add_parser("apply")
    p.add_argument("--raw", required=True)
    p.add_argument("--radius", type=int, default=24)
    p.add_argument("--eps", type=float, default=1e-3)
    p.add_argument("--lo", type=float, default=0.25)
    p.add_argument("--hi", type=float, default=3.0)
    p = sub.add_parser("review")
    p.add_argument("--version", type=int, required=True)
    p.add_argument("--raw")
    args = ap.parse_args()
    {"paint": cmd_paint, "apply": cmd_apply, "review": cmd_review}[args.cmd](args)


if __name__ == "__main__":
    main()
