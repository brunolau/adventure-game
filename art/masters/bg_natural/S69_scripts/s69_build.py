"""S69 Sokolikovsky dvor: everything the room needs besides the painting (free, local).

  export     master S69_v<N> -> src/game/assets/bg_natural/S69.webp (1920x1080, WebP q90)
  fg         art/prompts/natural/S69.fg.json -> src/game/assets/fg_natural/S69.webp (+ review preview)
  occluder   the moved bike as a y-sorted occluder texture (fg_natural/S69_bike_occluder.webp, alpha = bike only)
  variants   variants_natural/S69_bellcap_glint.webp / S69_bellcap_gone.webp (state patches after Q11A / Q11B)
  ambient    the yard ball sprite (assets/ambient/S69/natural/ball.webp) + data/blocking/ambient/S69.json
  blocking   data/blocking/S69.json (natural blocking; staged copy in S69_scripts/stage/)
  all        everything above

The live data files (blocking + ambient) name ids of the content v2 world overlay (S69, ZUZANA95, KUBO, Q11A...):
`tools/check_blocking.py` refuses them until src/game/data/content_ext/world_ext.json has S69. `blocking` therefore
always writes the staged copies (S69_scripts/stage/) and writes the live files only with --live (or when the live
world overlay already defines S69). `install_content_v2.py install` copies the stage into the game.

Run from the repo root: PYTHONIOENCODING=utf-8 python -X utf8 art/masters/bg_natural/S69_scripts/s69_build.py all
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "art" / "tools"))
sys.path.insert(0, str(HERE))
import paint_room as pr  # noqa: E402
import s69_paint as sp  # noqa: E402

ASSETS = ROOT / "src" / "game" / "assets"
DATA = ROOT / "src" / "game" / "data"
STAGE = HERE / "stage"
REVIEW = ROOT / "art" / "review" / "natural"
FINAL_VERSION = 7   # v7 = v6 relit to the S18 sunset (s69_relight.py, 2026-10-07)
WORLD_EXT = DATA / "content_ext" / "world_ext.json"


def frame_of(version: int = FINAL_VERSION) -> Image.Image:
    return pr.fit_to_frame(Image.open(pr.MASTERS / f"S69_v{version}.png").convert("RGB")).convert("RGB")


def webp(img: Image.Image, path: Path, lossless_alpha: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if img.mode == "RGBA":
        img.save(path, "WEBP", quality=95, alpha_quality=100, method=6)
    else:
        img.save(path, "WEBP", quality=90, method=6)


def cmd_export(_args=None) -> None:
    out = ASSETS / "bg_natural" / "S69.webp"
    webp(frame_of(), out)
    print(out.relative_to(ROOT))


def cmd_fg(_args=None) -> None:
    spec = json.loads((ROOT / "art" / "prompts" / "natural" / "S69.fg.json").read_text(encoding="utf-8"))
    painting = frame_of().convert("RGBA")
    alpha = Image.new("L", painting.size, 0)
    d = ImageDraw.Draw(alpha)
    for poly in spec["polygons"]:
        d.polygon([tuple(p) for p in poly["points"]], fill=255)
    alpha = alpha.filter(ImageFilter.GaussianBlur(float(spec.get("feather", 1.2))))
    mask = painting.copy()
    mask.putalpha(alpha)
    webp(mask, ASSETS / "fg_natural" / "S69.webp")
    dim = painting.convert("RGB").point(lambda v: v // 3).convert("RGBA")
    Image.alpha_composite(dim, mask).convert("RGB").save(REVIEW / "S69_fg_preview.png")
    print("fg_natural/S69.webp")


def bike_alpha_game() -> Image.Image:
    base = sp.base_image(1)
    raw = Image.open(ROOT / "art/masters/bg_natural/_S69_v2_bench_bike_raw.png").convert("RGB") \
        .resize(pr.MODEL_FRAME, Image.Resampling.LANCZOS)
    spr, (ox, oy), _f, _bbox = sp.bike_placement(raw, base)
    full = Image.new("L", pr.MODEL_FRAME, 0)
    full.paste(spr.getchannel("A"), (ox, oy))
    return pr.fit_to_frame(full.convert("RGB")).convert("L")


BIKE_OCCLUDER_BOX = [[930, 715], [1075, 715], [1075, 846], [930, 846]]
BIKE_BASELINE = 836


def cmd_occluder(_args=None) -> None:
    a = bike_alpha_game()
    a = a.point(lambda v: 255 if v > 150 else (0 if v < 40 else v))   # crisp silhouette, soft 1 px rim
    tex = frame_of().convert("RGBA")
    tex.putalpha(a)
    webp(tex, ASSETS / "fg_natural" / "S69_bike_occluder.webp")
    prev = Image.new("RGBA", tex.size, (255, 0, 255, 255))
    prev.alpha_composite(tex)
    prev.convert("RGB").crop((880, 650, 1120, 860)).resize((720, 630)).save(REVIEW / "S69_bike_occluder.png")
    print("fg_natural/S69_bike_occluder.webp")


GLINT_BOX = (846, 728, 910, 772)        # game px: the back-wall foot under the spruce, left of the bike


def _needles(d: ImageDraw.ImageDraw, rng, box, n, sc):
    x0, y0, x1, y1 = box
    for _ in range(n):
        x = rng.uniform(x0 + 4, x1 - 4)
        y = rng.uniform(y0 + 14, y1 - 6)
        ang = rng.uniform(-0.6, 0.6)
        ln = rng.uniform(3, 6)
        col = rng.choice([(86, 74, 48), (104, 92, 58), (70, 76, 52), (122, 104, 66)])
        d.line([((x - x0) * sc, (y - y0) * sc), ((x - x0 + ln * np.cos(ang)) * sc, (y - y0 + ln * np.sin(ang) * 0.4) * sc)],
               fill=col + (220,), width=sc)


def cmd_variants(_args=None) -> None:
    """Two small state patches (glint after Q11A, needles only + a forgotten chalk after Q11B), painted locally on
    the patch box; outside the painted marks they are the painting itself, so the 'gone' patch drawn over the glint
    restores the spot."""
    import random
    frame = frame_of().convert("RGBA")
    x0, y0, x1, y1 = GLINT_BOX
    base = frame.crop(GLINT_BOX)
    sc = 4
    w, h = base.size
    out = {}
    for name in ("glint", "gone"):
        rng = random.Random(1995 if name == "glint" else 1996)
        layer = Image.new("RGBA", (w * sc, h * sc), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        _needles(d, rng, GLINT_BOX, 22, sc)
        if name == "glint":
            # the brass cap, ~5 x 4 px at this depth (4.5 cm at ~113 px/m), tilted in the needles, with a sun glint
            cx, cy = 877 - x0, 752 - y0
            d.ellipse([(cx - 3.2) * sc, (cy - 2.2) * sc, (cx + 3.2) * sc, (cy + 2.0) * sc], fill=(150, 112, 44, 255))
            d.ellipse([(cx - 2.6) * sc, (cy - 2.0) * sc, (cx + 2.2) * sc, (cy + 0.6) * sc], fill=(214, 172, 78, 255))
            d.ellipse([(cx - 1.6) * sc, (cy - 1.7) * sc, (cx + 0.2) * sc, (cy - 0.5) * sc], fill=(255, 240, 190, 255))
            glow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
            ImageDraw.Draw(glow).ellipse([(cx - 7) * sc, (cy - 6) * sc, (cx + 5) * sc, (cy + 4) * sc],
                                         fill=(255, 236, 170, 70))
            glow = glow.filter(ImageFilter.GaussianBlur(3 * sc))
            layer = Image.alpha_composite(glow, layer)
            # a needle lying across the cap
            d = ImageDraw.Draw(layer)
            d.line([((cx - 4) * sc, (cy + 1.4) * sc), ((cx + 2) * sc, (cy - 0.4) * sc)], fill=(84, 72, 46, 230), width=sc)
        else:
            # the forgotten chalk stick (look.S69.spruce variant 2)
            cx, cy = 879 - x0, 754 - y0
            d.polygon([((cx - 4) * sc, (cy - 0.6) * sc), ((cx + 3) * sc, (cy - 1.6) * sc), ((cx + 3.3) * sc, (cy - 0.2) * sc),
                       ((cx - 3.7) * sc, (cy + 0.8) * sc)], fill=(236, 232, 220, 255))
        layer = layer.resize((w, h), Image.Resampling.LANCZOS)
        patch = Image.alpha_composite(base, layer)
        # soft edge so the patch never shows a box
        edge = Image.new("L", (w, h), 0)
        ImageDraw.Draw(edge).rectangle([3, 3, w - 4, h - 4], fill=255)
        patch.putalpha(edge.filter(ImageFilter.GaussianBlur(2)))
        path = ASSETS / "variants_natural" / f"S69_bellcap_{name}.webp"
        webp(patch, path)
        out[name] = path
        print(path.relative_to(ROOT))
    view = frame.copy()
    view.alpha_composite(Image.open(out["glint"]).convert("RGBA"), (x0, y0))
    a = view.crop((x0 - 60, y0 - 60, x1 + 60, y1 + 40)).resize(((x1 - x0 + 120) * 4, (y1 - y0 + 100) * 4),
                                                              Image.Resampling.LANCZOS)
    view2 = frame.copy()
    view2.alpha_composite(Image.open(out["glint"]).convert("RGBA"), (x0, y0))
    view2.alpha_composite(Image.open(out["gone"]).convert("RGBA"), (x0, y0))
    b = view2.crop((x0 - 60, y0 - 60, x1 + 60, y1 + 40)).resize(a.size, Image.Resampling.LANCZOS)
    board = Image.new("RGB", (a.width * 2 + 10, a.height), (0, 0, 0))
    board.paste(a.convert("RGB"), (0, 0))
    board.paste(b.convert("RGB"), (a.width + 10, 0))
    board.save(REVIEW / "S69_bellcap_states.png")


def cmd_ball(_args=None) -> None:
    src = Image.open(ROOT / "art" / "items" / "scene" / "BALL95.png").convert("RGBA")
    ball = src.crop(src.getbbox())
    ball = ball.resize((28, 28), Image.Resampling.LANCZOS)
    webp(ball, ASSETS / "ambient" / "S69" / "natural" / "ball.webp")
    print("ambient/S69/natural/ball.webp")


# ----------------------------------------------------------------------------- blocking

def scale_at(y: float) -> float:
    return round((y - sp.HORIZON) / 729.0, 3)


WALK = [[792, 790], [850, 766], [900, 758], [950, 748], [1000, 740], [1050, 731], [1100, 723], [1150, 716],
        [1200, 710], [1270, 704], [1330, 701], [1380, 706], [1450, 715], [1550, 722], [1640, 732], [1560, 790],
        [1480, 852], [1432, 888], [1420, 940], [1418, 1015], [1215, 1015], [1185, 950], [1166, 902], [1112, 880],
        [1076, 852], [1070, 812], [938, 812], [932, 840], [850, 826], [810, 812]]

BLOCKING = {
    "version": 1,
    "room": "S69",
    "status": "natural blocking of the new 1995 room S69 (content v2 world overlay; docs/story/SOKOLIKOVA_YARD.md). Base: the owner-loved style-test painting art/backgrounds/sokolikova-yard.png, kept pixel-for-pixel outside the added bench, bike, wall painting, chalk tally and hopscotch (art/masters/bg_natural/S69.md).",
    "note": "The walled courtyard playground between the Sokolikova panel blocks on a June evening in 1995 at sunset (relit 2026-10-07 to the light of S18 next door, art/masters/bg_natural/S69_v7), seen from the lawn outside the near wall. Two-point perspective: the right wall's lines meet at VP (-1146, 478), the back wall's at (2836, 470); horizon y ~475, focal ~1988 px (nearly level camera). Camera ~2.45 m above the court (the bench and the 16-inch bike painted by the edit, the right wall ~1.3 m, the low back wall ~0.7 m, the near wall ~1.4 m, the passage ~1.1 m): px per metre at a ground point = (y - 475) / 2.45, hero scale (y - 475) / 729 (0.31 at the passage y 700, 0.74 at the bottom y 1015). The bike was painted ~1.5x too large by the edit and is placed at 0.66 of its perspective size (handlebar ~0.7 m). The court is ~9 m along the back wall. The near wall in the foreground left is always in front of every actor (foreground mask); the walk area is the court behind it (the left strip between the low back wall and the near wall's top edge, the open centre, the right wall's foot) and stops short of the bench footprint and the overhanging branches at the right. The bike in the left strip is a y-sorted occluder (baseline 836).",
    "background": "bg_natural/S69.webp",
    "walk_polygon": WALK,
    "walk_band": [701, 1015],
    "actor_scale": [scale_at(701), scale_at(1015)],
    "spawn": [1260, 1000],
    "hotspots": {
        "S69.wall": {"rect": [240, 880, 860, 190], "interaction_point": [1200, 955], "label_anchor": [700, 870],
                     "reason": "the near wall of upright concrete panels in the foreground left (the lower half of its panels; the upper half stays the walk area's backdrop); the hero looks at it from the court beside its end panel"},
        "S69.rhythm": {"rect": [1376, 582, 178, 128], "interaction_point": [1465, 732], "label_anchor": [1490, 540],
                       "reason": "B19 target: the school club's painting on the three right-wall panels next to the passage (x 1381-1549): four shapes / three waves over two strokes / six pieces; the hero reads it from the wall foot"},
        "S69.court": {"rect": [1100, 812, 225, 84], "interaction_point": [1250, 905], "label_anchor": [1212, 802],
                      "reason": "the chalk hopscotch on the asphalt (8 squares + half circle, 0.8 x 3.0 m, quad 1098-1462 x 814-894); the rect covers its near half so Zuzana's rect stays clear"},
        "S69.birch": {"rect": [610, 20, 230, 620], "interaction_point": [838, 800], "label_anchor": [700, 300],
                      "reason": "the birch behind the low back wall at the left (trunk x ~650-705, drooping crown up to x ~1000); looked at from the left tip of the court"},
        "S69.spruce": {"rect": [846, 40, 262, 590], "interaction_point": [870, 795], "label_anchor": [980, 300],
                       "reason": "Q11B target: the blue spruce behind the low back wall; the cap lies at the wall foot under its lowest branches, left of the bike (glint patch at 877, 752); the hero reaches low from the left strip"},
        "S69.lamp": {"rect": [300, 448, 72, 250], "interaction_point": [830, 798], "label_anchor": [336, 438],
                     "reason": "the globe street lamp behind the near wall at the left (globe 311-358 x 457-505, post down to the wall top)"},
        "S69.bench": {"rect": [1430, 740, 362, 200], "interaction_point": [1395, 975], "label_anchor": [1610, 730],
                      "reason": "the green bench painted by the edit at the right edge of the court where the grass bank begins (seat and backrest x 1428-1790, y 738-1035, facing the court's open bottom); the hero stands at its left end"},
        "S69.bike": {"rect": [935, 720, 135, 122], "interaction_point": [1040, 802], "label_anchor": [1000, 710],
                     "reason": "Q11C target: Kubo's small red bike with stabilisers in the left strip in front of the low back wall (x 945-1063, wheels on y ~836); the hero stands behind its handlebar (the bike occluder hides his legs) to screw the cap on the bell"},
        "S69.ZUZANA95": {"rect": [1345, 595, 110, 285], "interaction_point": [1280, 905], "label_anchor": [1392, 586],
                         "reason": "Zuzana by the left end of the bench (feet 1400, 880; 0.56 x 512 px = 285 px tall); the hero talks to her from her left, on the court"},
        "S69.KUBO": {"rect": [1068, 669, 76, 184], "interaction_point": [1205, 868], "label_anchor": [1106, 659],
                     "reason": "Kubo at the front wheel of his bike (feet 1105, 852; 0.52 x 350 px = 181 px tall); the hero talks to him from his right, on the court"},
        "S69.gap": {"rect": [1272, 600, 110, 102], "interaction_point": [1325, 712], "label_anchor": [1336, 642],
                    "reason": "the narrow passage between the end of the back wall and the right wall (x 1270-1378); a look, not an exit"},
    },
    "exits": {
        "S69.to_S18": {"rect": [1190, 985, 225, 85], "interaction_point": [1300, 1008], "label_anchor": [1302, 975],
                       "reason": "the court opens towards the camera between the end of the near wall (x 1150) and the bench / grass bank: the way back out to the kiosk street"},
    },
    "npcs": {
        "S69.ZUZANA95": {"variant": "standing", "feet": [1400, 880], "facing": "left", "z": "auto",
                         "reason": "SOKOLIKOVA_YARD.md 2: Zuzana stands by the green bench (just left of its left end), chalk in hand, facing the court and the player coming in from the bottom; the hopscotch she drew lies behind her to the left"},
        "S69.KUBO": {"variant": "standing", "feet": [1105, 852], "facing": "left", "z": "auto",
                     "reason": "SOKOLIKOVA_YARD.md 2.3: Kubo stands at the front wheel of his bike in the left strip, facing it (the handlebar with the mute bell is at its right end); in front of the bike (feet below its baseline)"},
    },
    "occluders": [
        {"id": "bike", "polygon": BIKE_OCCLUDER_BOX, "baseline": BIKE_BASELINE,
         "texture": "fg_natural/S69_bike_occluder.webp"},
    ],
    "foreground_mask": "fg_natural/S69.webp",
    "state_patches": [
        {"texture": "variants_natural/S69_bellcap_glint.webp", "pos": [GLINT_BOX[0], GLINT_BOX[1]], "after": ["Q11A"],
         "until": []},
        {"texture": "variants_natural/S69_bellcap_gone.webp", "pos": [GLINT_BOX[0], GLINT_BOX[1]], "after": ["Q11B"],
         "until": []},
    ],
    "variant_layers": {
        "variants/S69_bellcap_glint.webp": {"texture": "variants_natural/S69_bellcap_glint.webp",
                                            "pos": [GLINT_BOX[0], GLINT_BOX[1]]},
        "variants/S69_bellcap_gone.webp": {"texture": "variants_natural/S69_bellcap_gone.webp",
                                           "pos": [GLINT_BOX[0], GLINT_BOX[1]]},
    },
    "ambient": "res://data/blocking/ambient/S69.json",
}

AMBIENT = {
    "room": "S69",
    "notes": "Natural S69 (bg_natural/S69.webp, the Sokolikova-yard painting, a June afternoon in 1995). The birch's leaves tremble (look.S69.birch: even when there is no wind), the blue spruce barely moves, wind in the big tree crowns at the left and the right and in the branches hanging into the frame over the right wall; swifts race high over the blocks; now and then a cat walks along the top of the low back wall; the children playing behind the right wall (the red climbing frame) throw a ball that rises above the wall and drops back; a few leaves drift down onto the court. After Q11A a tiny glint blinks at the cap under the spruce until Q11B.",
    "layers": [
        {"id": "trees_right_sway", "type": "sway", "texture": "S69/natural/trees_right.webp",
         "anchor": 1.0, "amp_px": 2.2, "freq": 0.26, "wavelength_px": 180, "flutter_px": 0.8, "gust": 0.5},
        {"id": "spruce_sway", "type": "sway", "texture": "S69/natural/spruce.webp",
         "anchor": 1.0, "amp_px": 0.7, "freq": 0.2, "wavelength_px": 140, "flutter_px": 0.3},
        {"id": "birch_tremble", "type": "sway", "texture": "S69/natural/birch.webp",
         "anchor": 1.0, "amp_px": 1.6, "freq": 0.5, "wavelength_px": 60, "flutter_px": 1.3, "gust": 0.4},
        {"id": "tree_left_sway", "type": "sway", "texture": "S69/natural/tree_left.webp",
         "anchor": 1.0, "amp_px": 2.0, "freq": 0.24, "wavelength_px": 170, "flutter_px": 0.8, "gust": 0.5},
        {"id": "branches_right_hang", "type": "sway", "texture": "S69/natural/branches_right.webp",
         "anchor": 0.0, "hang": True, "amp_px": 2.4, "freq": 0.32, "wavelength_px": 90, "flutter_px": 1.0, "gust": 0.6},
        {"id": "swifts_a", "type": "tween_path", "sheet": "common/pigeon_sheet", "frames": "fly", "fps": 16,
         "path": [[1990, 120], [1500, 60], [1180, 130], [900, 70], [600, 40], [-60, 90]],
         "speed_px_s": 420, "scale": 0.045, "flock": 4, "flock_spread": [140, 50], "bob_px": 6, "bob_hz": 3,
         "modulate": "#1d1b22", "direction": "random", "every_s": [8, 16], "start_s": [2, 5]},
        {"id": "swifts_b", "type": "tween_path", "sheet": "common/pigeon_sheet", "frames": "fly", "fps": 16,
         "path": [[-60, 170], [420, 90], [800, 150], [1150, 60], [1450, 120], [1990, 40]],
         "speed_px_s": 380, "scale": 0.04, "flock": 3, "flock_spread": [110, 40], "bob_px": 5, "bob_hz": 2.6,
         "modulate": "#1d1b22", "direction": "random", "every_s": [11, 22], "start_s": [6, 10]},
        {"id": "cat_back_wall", "type": "tween_path", "sheet": "common/cat_walk_sheet", "fps": 18,
         "path": [[1262, 625], [1100, 638], [1000, 650], [900, 661], [800, 671], [700, 681], [610, 690]],
         "speed_px_s": 42, "scale": [0.17, 0.2], "faces": "right", "fade_px": 40, "direction": "random",
         "every_s": [45, 80], "start_s": [8, 16]},
        {"id": "ball_over_wall", "type": "tween_path", "texture": "S69/natural/ball.webp",
         "path": [[1590, 640], [1604, 560], [1618, 506], [1632, 486], [1646, 506], [1660, 560], [1674, 640]],
         "duration_s": 1.5, "scale": 0.5, "clip": [1376, 0, 544, 588], "every_s": [16, 36], "start_s": [4, 9]},
        {"id": "leaves_drift", "type": "particles", "preset": "leaves",
         "textures": ["common/leaf_01.webp", "common/leaf_04.webp", "common/leaf_06.webp", "common/leaf_09.webp",
                      "common/leaf_13.webp"],
         "emit_rect": [640, 140, 860, 260], "rate": 0.1, "size": [7, 11], "speed_x": [-18, 22], "speed_y": [36, 60],
         "land_y": [742, 900], "rest_s": [4, 8]},
        {"id": "bellcap_glint", "type": "flicker", "mode": "blink", "rect": [866, 741, 22, 20],
         "texture": "builtin:glow", "color": "#fff1c4", "min": 0.0, "max": 0.8, "period_s": 2.6, "duty": 0.2,
         "if_done": ["Q11A"], "unless_done": ["Q11B"]},
    ],
}


def overlay_has_s69() -> bool:
    if not WORLD_EXT.exists():
        return False
    try:
        data = json.loads(WORLD_EXT.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return any(r.get("id") == "S69" for r in data.get("rooms", []))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def cmd_blocking(args) -> None:
    write_json(STAGE / "data" / "blocking" / "S69.json", BLOCKING)
    write_json(STAGE / "data" / "blocking" / "ambient" / "S69.json", AMBIENT)
    print("staged", (STAGE / "data").relative_to(ROOT))
    if getattr(args, "live", False) or overlay_has_s69():
        write_json(DATA / "blocking" / "S69.json", BLOCKING)
        write_json(DATA / "blocking" / "ambient" / "S69.json", AMBIENT)
        print("live: data/blocking/S69.json + ambient")
    else:
        print("live world overlay has no S69 yet: live blocking not written (install_content_v2.py install does it)")


def cmd_all(args) -> None:
    cmd_export()
    cmd_fg()
    cmd_occluder()
    cmd_variants()
    cmd_ball()
    cmd_blocking(args)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["export", "fg", "occluder", "variants", "ball", "blocking", "all"])
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()
    {"export": cmd_export, "fg": cmd_fg, "occluder": cmd_occluder, "variants": cmd_variants, "ball": cmd_ball,
     "blocking": cmd_blocking, "all": cmd_all}[args.cmd](args)


if __name__ == "__main__":
    main()
