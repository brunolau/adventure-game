"""Free, local asset builder for the LastBell living world (ambient layers).

Reads art/ambient/cuts.json and writes src/game/assets/ambient/**:
  * cut-outs of the painted backgrounds (RGBA, for sway / water / occluder layers), selected by a rect plus
    colour rules (HSV ranges, luma) and include/exclude polygons, feathered and padded;
  * masks (alpha only) that limit where a layer may show (sky above roofs, the road behind a hedge);
  * patches: the selected area inpainted from its surroundings (drawn under a moving cut-out so the
    original object does not show twice);
  * the shared sprites (leaves, pigeon sheet, cars, cat walk, clouds, ducks) from the keyed parts in
    art/ambient/*_parts/ and art/ambient/cat_walk/.
Re-run it whenever a background is repainted:  python art/tools/ambient_cut.py [--only S02] [--preview]
It records the SHA-1 of each source background in assets/ambient/manifest.json, and `--check` reports cut-outs
whose background changed since they were cut.

Natural re-blocking (per room, art/tools/PAINTING.md "Natural mode"; nothing shared is touched):
  python art/tools/ambient_cut.py --natural S05 [--preview]
reads art/ambient/natural/<room>.cuts.json (a list of items, same format as one room of cuts.json; optional top-level
"select_source": the image whose colours the rules read, e.g. the painting before a relight), cuts from
src/game/assets/bg_natural/<room>.webp and writes src/game/assets/ambient/<room>/natural/<name>.webp plus that folder's
own manifest.json (pos, size, mask_rect, patch_pos; read by AmbientContext.CutInfo for paths "<room>/natural/<name>").
Reference them in data/blocking/ambient/<room>.json as "<room>/natural/<name>.webp". `--natural S05 --check` reports
whether the painting changed since the cut.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "art"
SPEC = ART / "ambient" / "cuts.json"
BG = ROOT / "src" / "game" / "assets" / "bg"
OUT = ROOT / "src" / "game" / "assets" / "ambient"
PREVIEW = ART / "ambient" / "preview"


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def hsv(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Hue in degrees, saturation and value in 0..1."""
    f = rgb.astype(np.float32) / 255.0
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    mx, mn = f.max(-1), f.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    nz = d > 1e-6
    rm = nz & (mx == r)
    gm = nz & (mx == g) & ~rm
    bm = nz & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6
    h[gm] = ((b - r)[gm] / d[gm]) + 2
    h[bm] = ((r - g)[bm] / d[bm]) + 4
    h = h * 60.0
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0)
    return h, s, mx


def rule_mask(rgb: np.ndarray, rule: dict) -> np.ndarray:
    """One colour rule: {"hue": [a, b], "sat": [a, b], "val": [a, b], "luma": [a, b]} (all optional, hue may wrap)."""
    h, s, v = hsv(rgb)
    m = np.ones(h.shape, dtype=bool)
    if "hue" in rule:
        a, b = rule["hue"]
        m &= ((h >= a) & (h <= b)) if a <= b else ((h >= a) | (h <= b))
    if "sat" in rule:
        m &= (s >= rule["sat"][0]) & (s <= rule["sat"][1])
    if "val" in rule:
        m &= (v >= rule["val"][0]) & (v <= rule["val"][1])
    if "luma" in rule:
        y = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]) / 255.0
        m &= (y >= rule["luma"][0]) & (y <= rule["luma"][1])
    return m


def polygon_mask(size: tuple[int, int], polys: list, offset: tuple[int, int]) -> np.ndarray:
    img = Image.new("L", size, 0)
    d = ImageDraw.Draw(img)
    for poly in polys:
        pts = [(x - offset[0], y - offset[1]) for x, y in poly]
        if len(pts) == 2:  # rect given as two corners
            d.rectangle([pts[0], pts[1]], fill=255)
        else:
            d.polygon(pts, fill=255)
    return np.asarray(img) > 0


def select(rgb_full: np.ndarray, item: dict) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Alpha (float 0..1) of the selection inside item['rect'] and the rect."""
    x, y, w, h = item["rect"]
    crop = rgb_full[y:y + h, x:x + w]
    if "rules" in item:
        m = np.zeros(crop.shape[:2], dtype=bool)
        for rule in item["rules"]:
            m |= rule_mask(crop, rule)
    else:
        m = np.ones(crop.shape[:2], dtype=bool)
    for rule in item.get("except", []):
        m &= ~rule_mask(crop, rule)
    if "include" in item:
        m &= polygon_mask((w, h), item["include"], (x, y))
    if "exclude" in item:
        m &= ~polygon_mask((w, h), item["exclude"], (x, y))
    if "add" in item:  # polygons always included regardless of colour
        m |= polygon_mask((w, h), item["add"], (x, y))
    img = Image.fromarray((m * 255).astype(np.uint8), "L")
    # clean speckles: open then close
    clean = item.get("clean", 1)
    if clean:
        k = 2 * clean + 1
        img = img.filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k))
        img = img.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.MinFilter(k))
    grow = item.get("grow", 0)
    if grow > 0:
        img = img.filter(ImageFilter.MaxFilter(2 * grow + 1))
    elif grow < 0:
        img = img.filter(ImageFilter.MinFilter(-2 * grow + 1))
    feather = item.get("feather", 1.5)
    if feather:
        img = img.filter(ImageFilter.GaussianBlur(feather))
    alpha = np.asarray(img, dtype=np.float32) / 255.0 * item.get("alpha", 1.0)
    for zone in item.get("alpha_zones", []):  # multiply alpha inside polygons (glass = 0.6, posts = 0)
        zm = Image.fromarray((polygon_mask((w, h), [zone["poly"]], (x, y)) * 255).astype(np.uint8), "L")
        if zone.get("feather", 0.8):
            zm = zm.filter(ImageFilter.GaussianBlur(zone.get("feather", 0.8)))
        z = np.asarray(zm, dtype=np.float32) / 255.0
        alpha = alpha * (1 - z) + alpha * z * zone["alpha"]
    if "alpha_rules" in item:  # alpha from luma: e.g. glass highlights
        lo, hi = item["alpha_rules"]["luma"]
        yv = (0.299 * crop[..., 0] + 0.587 * crop[..., 1] + 0.114 * crop[..., 2]) / 255.0
        alpha = alpha * np.clip((yv - lo) / max(1e-3, hi - lo), 0, 1) * item["alpha_rules"].get("max", 1.0)
    return alpha, (x, y, w, h)


def inpaint(rgb: np.ndarray, hole: np.ndarray, iterations: int = 400) -> np.ndarray:
    """Fill hole pixels by repeated neighbour averaging from the border (diffusion), then add soft noise."""
    out = rgb.astype(np.float32).copy()
    known = ~hole
    out[hole] = 0
    weight = known.astype(np.float32)
    acc = out * weight[..., None]
    for _ in range(iterations):
        pad_a = np.pad(acc, ((1, 1), (1, 1), (0, 0)), mode="edge")
        pad_w = np.pad(weight, ((1, 1), (1, 1)), mode="edge")
        sa = pad_a[:-2, 1:-1] + pad_a[2:, 1:-1] + pad_a[1:-1, :-2] + pad_a[1:-1, 2:]
        sw = pad_w[:-2, 1:-1] + pad_w[2:, 1:-1] + pad_w[1:-1, :-2] + pad_w[1:-1, 2:]
        fill = hole & (sw > 0)
        acc[fill] = sa[fill] / 4.0
        weight[fill] = sw[fill] / 4.0
    res = np.where(weight[..., None] > 1e-4, acc / np.maximum(weight, 1e-4)[..., None], out)
    res = np.where(hole[..., None], res, rgb)
    return res.clip(0, 255).astype(np.uint8)


def save_webp(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "WEBP", lossless=True, quality=100, method=6)


def build_room_item(room: str, item: dict, rgb_full: np.ndarray, preview: bool, rgb_select: np.ndarray | None = None) -> dict:
    # rgb_select: the colours the selection rules read (natural spec "select_source", e.g. the painting before a
    # relight with the same geometry); the cut-out's pixels always come from rgb_full.
    alpha, (x, y, w, h) = select(rgb_full if rgb_select is None else rgb_select, item)
    kind = item.get("kind", "cutout")
    name = item["name"]
    pad = item.get("pad", 12 if kind == "cutout" else 0)
    info: dict = {"kind": kind}
    if kind in ("cutout", "patch_cutout"):
        crop = rgb_full[y:y + h, x:x + w]
        rgba = np.dstack([crop, (alpha * 255).astype(np.uint8)])
        img = Image.fromarray(rgba, "RGBA")
        if pad:
            padded = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
            padded.paste(img, (pad, pad))
            img = padded
        save_webp(img, OUT / room / f"{name}.webp")
        info["pos"] = [x - pad, y - pad]
        info["size"] = list(img.size)
        if item.get("patch"):
            hole_img = Image.fromarray(((alpha > 0.02) * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(2 * item.get("patch_grow", 6) + 1))
            hole = np.asarray(hole_img) > 0
            filled = inpaint(crop, hole)
            soft = np.asarray(hole_img.filter(ImageFilter.GaussianBlur(3)), dtype=np.float32) / 255.0
            patch = np.dstack([filled, (soft * 255).astype(np.uint8)])
            save_webp(Image.fromarray(patch, "RGBA"), OUT / room / f"{name}_patch.webp")
            info["patch_pos"] = [x, y]
        if preview:
            PREVIEW.mkdir(parents=True, exist_ok=True)
            bgc = Image.new("RGBA", img.size, (255, 0, 255, 255))
            bgc.alpha_composite(img)
            bgc.convert("RGB").save(PREVIEW / f"{room.replace('/', '_')}_{name}.png")
    elif kind == "mask":
        scale = item.get("scale", 0.5)
        full = np.zeros(rgb_full.shape[:2], dtype=np.float32)
        full[y:y + h, x:x + w] = alpha
        mrect = item.get("mask_rect", [x, y, w, h])
        mx, my, mw, mh = mrect
        sub = full[my:my + mh, mx:mx + mw]
        img = Image.fromarray((sub * 255).astype(np.uint8), "L")
        img = img.resize((max(1, round(mw * scale)), max(1, round(mh * scale))), Image.Resampling.LANCZOS)
        white = Image.new("RGBA", img.size, (255, 255, 255, 0))
        white.putalpha(img)
        save_webp(white, OUT / room / f"{name}.webp")
        info["mask_rect"] = mrect
        if preview:
            PREVIEW.mkdir(parents=True, exist_ok=True)
            base = Image.fromarray(rgb_full).convert("RGBA").crop((mx, my, mx + mw, my + mh))
            tint = Image.new("RGBA", base.size, (255, 0, 255, 0))
            a = Image.fromarray((sub * 160).astype(np.uint8), "L")
            tint.putalpha(a)
            base.alpha_composite(tint)
            base.convert("RGB").save(PREVIEW / f"{room.replace('/', '_')}_{name}.png")
    return info


# ----------------------------------------------------------------------------- shared sprites

def fit(img: Image.Image, longest: int) -> Image.Image:
    s = longest / max(img.size)
    return img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.Resampling.LANCZOS)


def sheet_from_parts(parts: list[Image.Image], names: list[str], pivots: list[str], height: int, out: Path, fps: float) -> dict:
    """Uniform-cell horizontal sheet; each part scaled by a common factor (tallest part -> height) and placed
    with its pivot ('feet' = bottom centre, 'centre') at the cell pivot."""
    scale = height / max(p.height for p in parts)
    scaled = [p.resize((max(1, round(p.width * scale)), max(1, round(p.height * scale))), Image.Resampling.LANCZOS) for p in parts]
    cw = max(p.width for p in scaled) + 8
    ch = max(p.height for p in scaled) + 8
    cw += cw % 2
    pivot = (cw // 2, ch - 4)
    sheet = Image.new("RGBA", (cw * len(scaled), ch), (0, 0, 0, 0))
    for i, (p, how) in enumerate(zip(scaled, pivots)):
        if how == "feet":
            ox, oy = pivot[0] - p.width // 2, pivot[1] - p.height
        else:  # centre of the figure on the cell centre
            ox, oy = pivot[0] - p.width // 2, (ch - p.height) // 2
        sheet.paste(p, (i * cw + ox, oy), p)
    save_webp(sheet, out.with_suffix(".webp"))
    meta = {"name": out.stem, "frames": len(scaled), "cell": [cw, ch], "pivot": list(pivot), "playback_fps": fps,
            "frame_names": names, "oneshot": False}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def build_shared() -> None:
    common = OUT / "common"
    common.mkdir(parents=True, exist_ok=True)
    amb = ART / "ambient"
    # leaves: 16 single sprites, longest side 48 px (drawn at 14-30 px)
    for i, p in enumerate(sorted((amb / "leaves_parts").glob("*.png"))):
        save_webp(fit(Image.open(p), 48), common / f"leaf_{i:02d}.webp")
    # pigeon: parts in reading order 0-3 flight, 4 stand, 5 look, 6 walk, 7 peck
    parts = [Image.open(amb / "pigeon_parts" / f"{i:02d}.png") for i in range(8)]
    order = [4, 7, 5, 6, 0, 1, 2, 3]
    names = ["stand", "peck", "look", "walk", "fly_0", "fly_1", "fly_2", "fly_3"]
    pivots = ["feet", "feet", "feet", "feet", "centre", "centre", "centre", "centre"]
    sheet_from_parts([parts[i] for i in order], names, pivots, 160, common / "pigeon_sheet", 10)
    # cars: single side views, wheels on the bottom (pivot = bottom centre)
    for name, longest in (("car2020", 420), ("car1995", 420)):
        img = fit(Image.open(amb / f"{name}_parts" / "00.png"), longest)
        save_webp(img, common / f"{name}.webp")
        meta = {"frames": 1, "cell": list(img.size), "pivot": [img.width // 2, img.height - 2], "playback_fps": 1}
        (common / f"{name}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    # clouds
    for i, p in enumerate(sorted((amb / "clouds_parts").glob("*.png"))):
        save_webp(fit(Image.open(p), 640), common / f"cloud_{i:02d}.webp")
    # ducks: four swimming poses on the waterline (pivot = bottom centre)
    parts = [Image.open(p) for p in sorted((amb / "ducks_parts").glob("*.png"))]
    sheet_from_parts(parts, ["swim_0", "swim_1", "dip", "swim_2"], ["feet"] * 4, 90, common / "duck_sheet", 1)
    # cat walk loop (built by frames.py loop from the Hailuo clip)
    src = Image.open(amb / "cat_walk" / "cat_walk_sheet.png")
    meta = json.loads((amb / "cat_walk" / "cat_walk_sheet.json").read_text(encoding="utf-8"))
    save_webp(src, common / "cat_walk_sheet.webp")
    keep = {k: meta[k] for k in ("frames", "cell", "pivot", "playback_fps", "stride_px_per_s")}
    keep["name"] = "cat_walk"
    (common / "cat_walk_sheet.json").write_text(json.dumps(keep, indent=2), encoding="utf-8")


def cut_natural(room: str, preview: bool, check: bool) -> None:
    """Per-room cut of a natural re-blocking painting into assets/ambient/<room>/natural/ with its own manifest."""
    spec_path = ART / "ambient" / "natural" / f"{room}.cuts.json"
    bg_path = ROOT / "src" / "game" / "assets" / "bg_natural" / f"{room}.webp"
    folder = OUT / room / "natural"
    manifest_path = folder / "manifest.json"
    if not bg_path.exists():
        raise SystemExit(f"missing {bg_path.relative_to(ROOT)} (export the natural painting first)")
    if check:
        old = json.loads(manifest_path.read_text(encoding="utf-8")).get("bg_sha1") if manifest_path.exists() else None
        print(f"{room} natural: {'ok' if old == sha1(bg_path) else 'STALE (re-run ambient_cut.py --natural ' + room + ')'}")
        return
    if not spec_path.exists():
        raise SystemExit(f"write {spec_path.relative_to(ROOT)} first (a list of cut items, see art/ambient/cuts.json)")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    items = spec.get("items", []) if isinstance(spec, dict) else spec
    rgb = np.asarray(Image.open(bg_path).convert("RGB"))
    # "select_source": an image with the painting's geometry whose colours the rules read (after a relight the
    # shapes stay those the rules were tuned on; the pixels are the new painting's).
    rgb_select = None
    if isinstance(spec, dict) and spec.get("select_source"):
        rgb_select = np.asarray(Image.open(ROOT / spec["select_source"]).convert("RGB"))
        if rgb_select.shape != rgb.shape:
            raise SystemExit(f"{spec['select_source']}: size {rgb_select.shape[1::-1]} differs from the painting")
    infos = {}
    for item in items:
        infos[item["name"]] = build_room_item(f"{room}/natural", item, rgb, preview, rgb_select)
        if "patch_pos" in infos[item["name"]]:
            infos[item["name"] + "_patch"] = {"kind": "patch", "pos": infos[item["name"]]["patch_pos"]}
        print(f"{room}/natural/{item['name']}", infos[item["name"]])
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"room": room, "source": bg_path.relative_to(ROOT).as_posix(),
                                         "bg_sha1": sha1(bg_path), "items": infos}, indent=2), encoding="utf-8")
    print(f"{manifest_path.relative_to(ROOT)}: {len(infos)} item(s)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", help="room id")
    parser.add_argument("--preview", action="store_true", help="write previews to art/ambient/preview/")
    parser.add_argument("--shared", action="store_true", help="also rebuild the shared sprites")
    parser.add_argument("--check", action="store_true", help="report rooms whose background changed since cutting")
    parser.add_argument("--natural", metavar="ROOM", help="cut the natural painting bg_natural/<ROOM>.webp from "
                                                          "art/ambient/natural/<ROOM>.cuts.json")
    args = parser.parse_args()
    if args.natural:
        cut_natural(args.natural, args.preview, args.check)
        return
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"rooms": {}}
    if args.check:
        for room in spec["rooms"]:
            old = manifest["rooms"].get(room, {}).get("bg_sha1")
            now = sha1(BG / f"{room}.webp")
            print(f"{room}: {'ok' if old == now else 'STALE (re-run ambient_cut.py --only ' + room + ')'}")
        return
    if args.shared:
        build_shared()
    for room, items in spec["rooms"].items():
        if args.only and room != args.only:
            continue
        bg_path = BG / f"{room}.webp"
        rgb = np.asarray(Image.open(bg_path).convert("RGB"))
        infos = {}
        for item in items:
            infos[item["name"]] = build_room_item(room, item, rgb, args.preview)
            if "patch_pos" in infos[item["name"]]:
                infos[item["name"] + "_patch"] = {"kind": "patch", "pos": infos[item["name"]]["patch_pos"]}
            print(room, item["name"], infos[item["name"]])
        manifest["rooms"][room] = {"bg_sha1": sha1(bg_path), "items": infos}
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
