"""State layers of the content v2 overlay in existing natural rooms (free, local; docs/story/ZUZANA.md 2 and 5,
SOKOLIKOVA_YARD.md 3.5 / 6.4 / 6.5). Each is a small patch cut from the room's natural painting with the change
painted on it, placed by the room's blocking `variant_layers` (snippets in install_content_v2.py).

  S37_hopscotch           chalk hopscotch on the park path left of Vera (8 squares + half circle), after B22
  S37_zuzana_bell         the mute class bell lying in the grass in front of the path (handkerchief), after B22
  S37_zuzana_bell_gone    the same grass without the bell (Adam carries it), after Q10A
  S37_zuzana_bell_back    the repaired bell lying there again (clapper on its new loop, no handkerchief), after Q10D
  S32_chalk_arrow         chalk arrow pointing right (to the park) and PARK on the stone ring of the well, after B22
  S38_paper_boat          a paper boat stuck in the grass at the canal edge, after B22
  S17_sign_shapes_only    the 1995 school-yard art panel with only its four shapes (waves / strokes / pieces painted
                          out: they are on the S69 wall now), after G11

The bell and boat sprites are the scene sprites of the content v2 icon grid (art/items/scene/, content_v2_items.py).

  python content_v2_variants.py all        (writes src/game/assets/variants_natural/*.webp + review boards)
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ART = Path(__file__).resolve().parent.parent
ROOT = ART.parent
BG = ROOT / "src" / "game" / "assets" / "bg_natural"
OUT = ROOT / "src" / "game" / "assets" / "variants_natural"
SCENE = ART / "items" / "scene"
REVIEW = ROOT / "build" / "screens" / "content_v2" / "variants"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ambient_cut  # noqa: E402  (diffusion inpaint)

PLACEMENTS: dict[str, dict] = {}


def room(rid: str) -> Image.Image:
    return Image.open(BG / f"{rid}.webp").convert("RGBA")


def save_patch(name: str, patch: Image.Image, pos: tuple[int, int], meta: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.webp"
    patch.save(path, "WEBP", quality=95, alpha_quality=100, method=6)
    PLACEMENTS[name] = {"texture": f"variants_natural/{name}.webp", "pos": list(pos), **meta}
    print(path.relative_to(ROOT), pos, patch.size)


def soft_box_alpha(size, margin=3, blur=2.0) -> Image.Image:
    w, h = size
    a = Image.new("L", size, 0)
    ImageDraw.Draw(a).rectangle([margin, margin, w - 1 - margin, h - 1 - margin], fill=255)
    return a.filter(ImageFilter.GaussianBlur(blur))


def homography(src, dst) -> np.ndarray:
    a = []
    for (x, y), (u, v) in zip(src, dst):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        a.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, vt = np.linalg.svd(np.asarray(a, float))
    h = vt[-1].reshape(3, 3)
    return h / h[2, 2]


# ----------------------------------------------------------------------------- S37

S37_HORIZON, S37_CAM, S37_FOCAL = 519.7, 1.66, 1800.0     # from the blocking's actor_scale (0.515 @775, 1.0 @1015)


def s37_screen(gx: float, gz: float) -> tuple[float, float]:
    return 960 + S37_FOCAL * gx / gz, S37_HORIZON + S37_FOCAL * S37_CAM / gz


def s37_ground(x: float, y: float) -> tuple[float, float]:
    z = S37_FOCAL * S37_CAM / (y - S37_HORIZON)
    return (x - 960) * z / S37_FOCAL, z


HOP_NEAR_LEFT = (150, 902)          # screen: near-left corner of the hopscotch on the park path
HOP_LEN, HOP_W = 2.6, 0.7           # metres: along the path (to the right), across it (into depth)
HOP_BOX = (120, 846, 790, 914)      # patch box (game px)


def hopscotch_alpha(size, quad) -> np.ndarray:
    W, H = 260, 70                   # plane units = cm, x along the path, y into depth (0 = far edge)
    sc = 4
    plane = Image.new("L", (W * sc, H * sc), 0)
    d = ImageDraw.Draw(plane)
    rng = random.Random(1962)
    lw = 5 * sc

    def wob(v):
        return v + rng.uniform(-1.5, 1.5) * sc

    def rect(x0, y0, x1, y1):
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        d.line([(wob(x * sc), wob(y * sc)) for x, y in pts], fill=255, width=lw, joint="curve")
    s = 35
    x = 0
    for cell in ("single", "single", "single", "pair", "single", "pair"):
        if cell == "single":
            rect(x, 17, x + s, 53)
        else:
            rect(x, 0, x + s, 35)
            rect(x, 35, x + s, 70)
        x += s
    d.arc([(x - 35) * sc, 0, (x + 35) * sc, 70 * sc], 270, 90, fill=255, width=lw)      # half circle ("nebo")
    a = np.asarray(plane, np.float32) / 255
    a = a * (0.45 + 0.55 * np.random.default_rng(3).random(a.shape).astype(np.float32))
    img = Image.fromarray((a * 255).astype(np.uint8), "L")
    src = [(0, 0), (W * sc, 0), (W * sc, H * sc), (0, H * sc)]
    hmat = homography(quad, src)
    warped = img.transform(size, Image.Transform.PERSPECTIVE, tuple(hmat.flatten()[:8]), Image.Resampling.BICUBIC)
    return np.asarray(warped.filter(ImageFilter.GaussianBlur(0.5)), np.float32) / 255


def s37_hopscotch() -> None:
    gx, gz = s37_ground(*HOP_NEAR_LEFT)
    far_l = s37_screen(gx, gz + HOP_W)
    far_r = s37_screen(gx + HOP_LEN, gz + HOP_W)
    near_r = s37_screen(gx + HOP_LEN, gz)
    near_l = s37_screen(gx, gz)
    quad = [far_l, far_r, near_r, near_l]
    frame = room("S37")
    a = hopscotch_alpha(frame.size, quad)
    rgb = np.asarray(frame.convert("RGB"), np.float32)
    lum = rgb.mean(axis=2, keepdims=True) / 255
    chalk = np.asarray([238, 232, 214], np.float32)[None, None] * np.clip(0.55 + lum * 0.8, 0.6, 1.08)
    k = (a * 0.62)[..., None]                     # chalk on a dirt path: paler and patchier than on asphalt
    out = rgb * (1 - k) + np.minimum(chalk, 255) * k
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    patch = img.crop(HOP_BOX)
    patch.putalpha(soft_box_alpha(patch.size, 2, 1.5))
    save_patch("S37_hopscotch", patch, HOP_BOX[:2], {"after": "B22", "quad": [[round(x), round(y)] for x, y in quad]})


BELL_BOX = (282, 912, 386, 972)     # patch box: the near grass in front of the path, right of the hopscotch
BELL_AT = (334, 948)                # bell centre


def grass_over(frame: Image.Image, box, sprite_layer: Image.Image, frac_from: float) -> Image.Image:
    """Put the painting's own bright grass strokes back over the lower part of a sprite (it lies IN the grass)."""
    crop = frame.crop(box).convert("RGB")
    arr = np.asarray(crop, np.float32) / 255
    mx, mn = arr.max(axis=2), arr.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1e-3)
    green = (arr[..., 1] >= arr[..., 0]) & (sat > 0.35) & (mx > 0.45)
    rows = np.arange(arr.shape[0])[:, None] / arr.shape[0]
    m = green & (rows > frac_from)
    mask = Image.fromarray((m * 255).astype(np.uint8), "L").filter(ImageFilter.MinFilter(3)).filter(
        ImageFilter.GaussianBlur(0.6))
    out = sprite_layer.copy()
    out.paste(crop.convert("RGBA"), (0, 0), mask)
    return out


def bell_patch(sprite: Image.Image, width_px: int, angle: float, name: str, after: str) -> None:
    frame = room("S37")
    patch = frame.crop(BELL_BOX)
    spr = sprite.crop(sprite.getbbox()).rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    spr = spr.crop(spr.getbbox())
    spr = spr.resize((width_px, max(1, round(spr.height * width_px / spr.width))), Image.Resampling.LANCZOS)
    # match the park's warm afternoon light a little (icons are lit evenly)
    r, g, b, a = spr.split()
    spr = Image.merge("RGBA", (r.point(lambda v: min(255, int(v * 1.0))), g.point(lambda v: int(v * 0.96)),
                               b.point(lambda v: int(v * 0.88)), a))
    cx, cy = BELL_AT[0] - BELL_BOX[0], BELL_AT[1] - BELL_BOX[1]
    ox, oy = round(cx - spr.width / 2), round(cy - spr.height / 2)
    shadow = Image.new("RGBA", patch.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([ox + 2, oy + spr.height * 0.55, ox + spr.width + 4, oy + spr.height + 5],
                                   fill=(30, 40, 10, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))
    layer = Image.alpha_composite(patch, shadow)
    layer.alpha_composite(spr, (ox, oy))
    layer = grass_over(frame, BELL_BOX, layer, 0.62)
    layer.putalpha(soft_box_alpha(layer.size, 3, 2.0))
    save_patch(name, layer, BELL_BOX[:2], {"after": after})


def s37_bells() -> None:
    lying = Image.open(SCENE / "BELL_LYING.png").convert("RGBA")
    fixed = Image.open(ART / "items" / "BELL_FIXED.png").convert("RGBA")
    bell_patch(lying, 58, 0, "S37_zuzana_bell", "B22")
    bell_patch(fixed, 58, -80, "S37_zuzana_bell_back", "Q10D")
    frame = room("S37")
    gone = frame.crop(BELL_BOX)
    gone.putalpha(soft_box_alpha(gone.size, 3, 2.0))
    save_patch("S37_zuzana_bell_gone", gone, BELL_BOX[:2], {"after": "Q10A"})


# ----------------------------------------------------------------------------- S32

ARROW_BOX = (206, 640, 346, 706)     # the front of the well's stone ring (game px)


def s32_chalk_arrow() -> None:
    frame = room("S32")
    patch = frame.crop(ARROW_BOX).convert("RGB")
    w, h = patch.size
    sc = 4
    layer = Image.new("L", (w * sc, h * sc), 0)
    d = ImageDraw.Draw(layer)
    rng = random.Random(55)
    # arrow pointing right (the park is the square's right exit)
    y = 18
    d.line([(26 * sc, y * sc), (104 * sc, (y - 1) * sc)], fill=255, width=3 * sc)
    d.line([(104 * sc, (y - 1) * sc), (92 * sc, (y - 9) * sc)], fill=255, width=3 * sc)
    d.line([(104 * sc, (y - 1) * sc), (93 * sc, (y + 8) * sc)], fill=255, width=3 * sc)
    # PARK in a child's chalk capitals
    font = None
    for cand in ("C:/Windows/Fonts/comicbd.ttf", "C:/Windows/Fonts/arialbd.ttf"):
        try:
            font = ImageFont.truetype(cand, 21 * sc)
            break
        except OSError:
            continue
    x = 34
    for ch in "PARK":
        d.text((x * sc + rng.uniform(-2, 2) * sc, (30 + rng.uniform(-2, 2)) * sc), ch, fill=255, font=font)
        x += 17
    a = np.asarray(layer, np.float32) / 255
    a = a * (0.5 + 0.5 * np.random.default_rng(9).random(a.shape).astype(np.float32))
    a_img = Image.fromarray((a * 255).astype(np.uint8), "L").resize((w, h), Image.Resampling.LANCZOS) \
        .filter(ImageFilter.GaussianBlur(0.4))
    k = np.asarray(a_img, np.float32)[..., None] / 255 * 0.8
    rgb = np.asarray(patch, np.float32)
    lum = rgb.mean(axis=2, keepdims=True) / 255
    chalk = np.asarray([236, 234, 228], np.float32)[None, None] * np.clip(0.6 + lum * 0.7, 0.65, 1.05)
    out = Image.fromarray(np.clip(rgb * (1 - k) + chalk * k, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    out.putalpha(soft_box_alpha(out.size, 2, 1.2))
    save_patch("S32_chalk_arrow", out, ARROW_BOX[:2], {"after": "B22"})


# ----------------------------------------------------------------------------- S38

BOAT_BOX = (1376, 588, 1456, 642)
BOAT_AT = (1414, 618)


def s38_paper_boat() -> None:
    frame = room("S38")
    patch = frame.crop(BOAT_BOX)
    boat = Image.open(SCENE / "PAPERBOAT.png").convert("RGBA")
    boat = boat.crop(boat.getbbox()).rotate(-8, expand=True, resample=Image.Resampling.BICUBIC)
    boat = boat.crop(boat.getbbox())
    width = 38
    boat = boat.resize((width, round(boat.height * width / boat.width)), Image.Resampling.LANCZOS)
    r, g, b, a = boat.split()
    boat = Image.merge("RGBA", (r.point(lambda v: int(v * 0.97)), g.point(lambda v: int(v * 0.97)),
                                b.point(lambda v: int(v * 0.9)), a))
    ox, oy = BOAT_AT[0] - BOAT_BOX[0] - boat.width // 2, BOAT_AT[1] - BOAT_BOX[1] - boat.height // 2
    shadow = Image.new("RGBA", patch.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([ox, oy + boat.height * 0.7, ox + boat.width + 3, oy + boat.height + 3],
                                   fill=(20, 40, 30, 90))
    layer = Image.alpha_composite(patch, shadow.filter(ImageFilter.GaussianBlur(2)))
    layer.alpha_composite(boat, (ox, oy))
    layer = grass_over(frame, BOAT_BOX, layer, 0.6)
    layer.putalpha(soft_box_alpha(layer.size, 3, 2.0))
    save_patch("S38_paper_boat", layer, BOAT_BOX[:2], {"after": "B22"})


# ----------------------------------------------------------------------------- S17

SIGN_BOX = (200, 496, 394, 574)      # the board area below the four shapes (waves, strokes, pieces rows)


def s17_sign_shapes_only() -> None:
    frame = room("S17").convert("RGB")
    crop = frame.crop(SIGN_BOX)
    arr = np.asarray(crop, np.float32)
    board = np.median(arr.reshape(-1, 3)[arr.reshape(-1, 3).mean(axis=1) > np.percentile(arr.mean(axis=2), 60)], axis=0)
    dist = np.abs(arr - board[None, None]).max(axis=2)
    marks = dist > 34
    # keep the board's own edges out (the outer 3 px of the box are the frame of the patch only)
    marks[:2], marks[-2:], marks[:, :2], marks[:, -2:] = False, False, False, False
    hole = np.asarray(Image.fromarray((marks * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(5))) > 0
    filled = ambient_cut.inpaint(arr.astype(np.uint8), hole, iterations=600).astype(np.float32)
    noise = np.random.default_rng(17).normal(0, 2.2, filled.shape[:2])[..., None]
    filled = np.where(hole[..., None], np.clip(filled + noise, 0, 255), filled)
    out = Image.fromarray(filled.astype(np.uint8), "RGB").convert("RGBA")
    out.putalpha(soft_box_alpha(out.size, 1, 0.8))
    save_patch("S17_sign_shapes_only", out, SIGN_BOX[:2], {"after": "G11", "base": "bg_natural/S17.webp as of "
                                                           "2026-10-06 (master S17 L_YARD_nogo v12)"})


# ----------------------------------------------------------------------------- review

def board(rid: str, names: list[str], view_box) -> None:
    frame = room(rid)
    tiles = []
    for upto in range(len(names) + 1):
        img = frame.copy()
        for n in names[:upto]:
            p = PLACEMENTS[n]
            img.alpha_composite(Image.open(ROOT / "src/game/assets" / p["texture"]).convert("RGBA"), tuple(p["pos"]))
        x0, y0, x1, y1 = view_box
        tiles.append(img.crop(view_box).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.Resampling.LANCZOS))
    W = max(t.width for t in tiles)
    out = Image.new("RGB", (W, sum(t.height for t in tiles) + 6 * len(tiles)), (0, 0, 0))
    y = 0
    for t in tiles:
        out.paste(t.convert("RGB"), (0, y))
        y += t.height + 6
    REVIEW.mkdir(parents=True, exist_ok=True)
    out.save(REVIEW / f"{rid}_states.png")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["all"])
    ap.parse_args()
    s37_hopscotch()
    s37_bells()
    s32_chalk_arrow()
    s38_paper_boat()
    s17_sign_shapes_only()
    (ART / "masters" / "bg_natural" / "content_v2_variants.json").write_text(
        json.dumps(PLACEMENTS, indent=1), encoding="utf-8", newline="\n")
    board("S37", ["S37_hopscotch", "S37_zuzana_bell", "S37_zuzana_bell_gone", "S37_zuzana_bell_back"],
          (100, 820, 800, 990))
    board("S32", ["S32_chalk_arrow"], (150, 560, 420, 740))
    board("S38", ["S38_paper_boat"], (1300, 540, 1520, 700))
    board("S17", ["S17_sign_shapes_only"], (180, 420, 420, 600))
    print("review boards in", REVIEW.relative_to(ROOT))


if __name__ == "__main__":
    main()
