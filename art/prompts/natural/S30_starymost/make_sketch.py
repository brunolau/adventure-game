"""Writes art/prompts/natural/S30.sketch.json: the flat-colour layout sketch of S30 on the old Stary most (1995).

Camera and blocking: src/game/data/blocking/S30.json "note". Free; rerun after changing the numbers here.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
H = 400            # horizon
RAIL_TOP, RAIL_FOOT = 617, 800
S = []


def rect(x, y, w, h, fill, note=None, **kw):
    S.append({"type": "rect", "box": [x, y, w, h], "fill": fill, **({"note": note} if note else {}), **kw})


def poly(points, fill, note=None):
    S.append({"type": "poly", "points": points, "fill": fill, **({"note": note} if note else {})})


def ellipse(x, y, w, h, fill, note=None, **kw):
    S.append({"type": "ellipse", "box": [x, y, w, h], "fill": fill, **({"note": note} if note else {}), **kw})


def line(points, color, width, note=None):
    S.append({"type": "line", "points": points, "color": color, "width": width, **({"note": note} if note else {})})


# sky and clouds
rect(0, 0, 1920, 420, "#a8cbe9", "summer afternoon sky")
ellipse(250, 40, 520, 110, "#f1f4f7", "white cloud")
ellipse(1180, 70, 560, 120, "#f1f4f7", "white cloud")
ellipse(1560, 160, 300, 60, "#eef2f6", "small cloud")
# distant hills upstream (Karlova Ves / Little Carpathians foothills), hazy
poly([[560, 418], [640, 372], [760, 352], [880, 360], [900, 418]], "#9db58f", "hazy green hills far upstream")
# Danube
rect(0, 405, 1920, 400, "#6d9cbf", "the wide Danube")
ellipse(80, 445, 760, 90, "#9cc0dc", "sun glitter on the water")
rect(0, 690, 1920, 115, "#5b89ab", "water closer below the bridge")
# Petrzalka bank (left, near): park trees of Sad Janka Krala and the Tyrsovo nabrezie riverside
poly([[0, 300], [90, 290], [200, 305], [330, 300], [460, 320], [600, 345], [700, 380], [760, 408],
      [760, 425], [500, 450], [250, 480], [0, 505]], "#5d8a45", "dense green park trees on the Petrzalka bank")
poly([[0, 505], [250, 480], [500, 450], [760, 425], [760, 432], [500, 458], [250, 490], [0, 516]], "#c8bc9c",
     "low stone embankment of the Petrzalka bank")
# Most SNP: slanted pylon leaning left (towards Petrzalka) with the saucer, cables, deck
poly([[700, 432], [728, 432], [668, 178], [652, 178]], "#cfd3d6",
     "Most SNP pylon (its two legs seen from the side as one slanted pylon)")
ellipse(612, 150, 100, 30, "#d7dadc", "the round saucer restaurant on top of the pylon")
rect(648, 140, 26, 12, "#d7dadc")
for x2 in (780, 850, 920, 990):
    line([[662, 186], [x2, 412]], "#a9afb4", 2, "stay cable")
rect(560, 409, 520, 9, "#c4c8cb", "the bridge deck of Most SNP crossing the river")
# north bank: embankment, castle hill, castle
rect(760, 404, 900, 16, "#cfc4aa", "stone embankment of the Old Town bank")
poly([[820, 406], [860, 372], [900, 300], [950, 266], [1120, 262], [1172, 300], [1222, 356], [1262, 406]],
     "#6e9a4b", "green castle hill with trees")
rect(880, 258, 300, 14, "#d6ccb2", "castle fortification walls")
rect(915, 192, 210, 70, "#e1c88c", "Bratislava castle: square palace, warm ochre walls")
rect(904, 166, 28, 96, "#e1c88c")
rect(1108, 166, 28, 96, "#e1c88c", "corner towers")
poly([[915, 192], [1125, 192], [1105, 176], [935, 176]], "#57535a", "dark slate roof")
poly([[904, 166], [932, 166], [918, 138]], "#4c4950")
poly([[1108, 166], [1136, 166], [1122, 138]], "#4c4950", "dark pointed tower caps")
rect(990, 150, 22, 42, "#e1c88c")
poly([[990, 150], [1012, 150], [1001, 128]], "#4c4950")
# St Martin's cathedral
rect(1130, 330, 64, 75, "#b4a68e", "cathedral nave")
poly([[1128, 330], [1196, 330], [1162, 312]], "#6a6460")
rect(1180, 262, 30, 143, "#bdb299", "cathedral tower")
poly([[1178, 262], [1212, 262], [1195, 196]], "#6f8f7c", "slender spire with copper green")
# Old Town riverfront of 1995
rect(1210, 330, 450, 76, "#e4d9c0", "old town houses and palaces along the embankment")
S.append({"type": "grid", "box": [1220, 340, 430, 56], "cols": 18, "rows": 2, "color": "#c2b596", "width": 2})
rect(1330, 322, 118, 84, "#f0eee6", "white 1950s riverside hotel block")
rect(1468, 366, 176, 40, "#e8d6ac", "long baroque barracks building")
rect(1478, 342, 156, 24, "#a5573d", "rust-red modern gallery wing on top of it")
rect(1210, 306, 140, 26, "#b0503c", "red tiled roofs")
for x in range(1215, 1650, 46):
    ellipse(x, 384, 44, 28, "#5f8c45")
# white riverboat moored at the passenger quay (hotspot S30.ambient 1)
rect(1236, 438, 330, 26, "#f4f4f2", "white riverboat hull")
rect(1270, 414, 250, 26, "#ecebe6", "boat superstructure with windows")
S.append({"type": "grid", "box": [1278, 420, 236, 14], "cols": 14, "rows": 1, "color": "#7d8c99", "width": 2})
rect(1236, 460, 330, 6, "#3e5466")
rect(1450, 402, 20, 14, "#c8473a", "funnel stripe")
# --- the footway of the old bridge (walk band) ---
rect(0, 800, 1920, 280, "#9f8768", "weathered wooden plank footway")
for xb in range(-1700, 3700, 170):
    # plank joints run across the footway, converging towards the horizon centre
    t = (1080 - RAIL_FOOT) / (1080 - H)
    xt = xb + (960 - xb) * t
    line([[xb, 1080], [round(xt), RAIL_FOOT]], "#8d775a", 3)
rect(0, 1030, 1920, 50, "#6f767c", "bottom chord of the truss under the HUD")
# footway railing (grey steel): top rail, bottom rail, posts, bars
rect(560, RAIL_TOP, 1360, 9, "#8f969c", "top rail of the footway railing")
rect(560, RAIL_FOOT - 14, 1360, 8, "#8f969c", "bottom rail")
S.append({"type": "bars", "box": [560, RAIL_TOP + 9, 1360, RAIL_FOOT - RAIL_TOP - 23], "step": 24, "bar": 5,
          "fill": "#98a0a6", "vertical": True})
for x in range(600, 1920, 240):
    rect(x, RAIL_TOP - 4, 12, RAIL_FOOT - RAIL_TOP + 4, "#80878d", "railing post")
rect(560, RAIL_FOOT - 6, 1360, 10, "#6b6f72", "footway edge beam")
# --- fictional service booth on a small bay above the pier (left) ---
rect(130, 372, 450, 430, "#7b8e7c", "small faded grey-green sheet-metal service booth")
poly([[112, 372], [598, 372], [598, 352], [112, 334]], "#6c7270", "sloping corrugated roof")
line([[540, 352], [540, 286]], "#55595c", 4, "short mast")
poly([[540, 288], [584, 298], [540, 308]], "#c9493b", "small plain red pennant")
rect(158, 438, 394, 180, "#3d4643", "wide open front hatch, shadowed inside")
poly([[150, 438], [560, 438], [574, 408], [136, 408]], "#8a9b88", "hatch flap propped up as an awning")
rect(146, 614, 418, 24, "#a5794d", "wooden counter shelf")
rect(130, 638, 450, 162, "#748774", "lower panel of the booth")
rect(150, 790, 410, 12, "#55605a", "booth base")
# coil holder ring (S30.coil)
ellipse(186, 500, 92, 92, None, "empty round steel holder ring", outline="#c4c9cd", width=13)
rect(226, 588, 13, 28, "#9aa1a6", "short post of the ring")
rect(205, 608, 54, 8, "#8a9095")
# demo circuit board (not a hotspot)
rect(300, 574, 112, 40, "#cfa56b", "isolated demo circuit board")
for i, c in enumerate(["#d23b2e", "#2f4f9e", "#d23b2e", "#222222", "#2f4f9e"]):
    ellipse(310 + i * 18, 584, 9, 9, c)
ellipse(388, 560, 18, 22, "#f4efc8", "small lamp")
line([[318, 600], [350, 612], [392, 602]], "#d23b2e", 3)
# number wheel box (S30.dial)
rect(426, 545, 124, 72, "#a9aeb3", "grey steel box")
for i in range(3):
    rect(438 + i * 37, 560, 28, 42, "#f1eee4", "number wheel window")
# metronome table (S30.metro)
ellipse(632, 652, 146, 32, "#9b6a3e", "round wooden table top")
ellipse(676, 659, 58, 16, None, outline="#f3efe4", width=3)
rect(697, 682, 18, 104, "#7a5230", "single leg")
rect(664, 780, 84, 12, "#6c4828", "foot")
# --- riveted truss members framing the picture (near truss of the road deck) ---
poly([[0, 0], [40, 0], [120, 1080], [0, 1080]], "#7d858d", "riveted grey inclined truss member at the left edge")
poly([[1880, 0], [1920, 0], [1920, 1080], [1806, 1080]], "#7d858d",
     "riveted grey inclined truss member at the right edge")

spec = {"note": "S30 natural, old Stary most 1995: upstream footway above the first river pier near the Petrzalka "
                "end, looking WNW; horizon y 400, railing foot y 800, top rail y 617. Written by "
                "art/prompts/natural/S30_starymost/make_sketch.py.",
        "background": "#a8cbe9", "shapes": S}
(ROOT / "art" / "prompts" / "natural" / "S30.sketch.json").write_text(json.dumps(spec, indent=1), encoding="utf-8")
print(len(S), "shapes")
