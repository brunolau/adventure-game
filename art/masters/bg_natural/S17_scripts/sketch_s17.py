"""Generate art/prompts/natural/S17.sketch.json (L_YARD base, 1995 June) from the camera in blocking/S17.json."""
import json
import sys

ERA = sys.argv[1] if len(sys.argv) > 1 else "1995"
S = []


def rect(b, fill, note=None, **kw):
    d = {"type": "rect", "box": [round(v) for v in b], "fill": fill}
    if note:
        d["note"] = note
    d.update(kw)
    S.append(d)


def poly(pts, fill, note=None):
    d = {"type": "poly", "points": [[round(x), round(y)] for x, y in pts], "fill": fill}
    if note:
        d["note"] = note
    S.append(d)


def line(pts, color, width, note=None):
    d = {"type": "line", "points": [[round(x), round(y)] for x, y in pts], "color": color, "width": width}
    if note:
        d["note"] = note
    S.append(d)


def ell(b, fill, note=None, **kw):
    d = {"type": "ellipse", "box": [round(v) for v in b], "fill": fill}
    if note:
        d["note"] = note
    d.update(kw)
    S.append(d)


X1 = 1250


def top(x):
    return 80 + (180 - 80) * x / X1


def base(x):
    return 451 + (428 - 451) * x / X1


def at(x, f):  # f = 0 roof .. 1 foot
    return top(x) + (base(x) - top(x)) * f


def bank(x):
    return 507 + (465 - 507) * x / X1


def tr0(x):
    return 492 + (578 - 492) * (x - 1150) / 770


def tr1(x):
    return 506 + (616 - 506) * (x - 1150) / 770


rect([0, 0, 1920, 420], "#a9cbe6", "June afternoon sky")
rect([0, 300, 1920, 140], "#c3d9ea", "paler sky near the horizon")
poly([(0, 255), (180, 222), (420, 205), (660, 214), (900, 240), (1100, 275), (1300, 318), (1300, 470), (0, 470)], "#5f8048",
     "wooded Dubravka hill behind the school")
for bx, by in ((150, 238), (300, 222), (470, 214), (640, 222), (820, 238), (1010, 262), (1160, 290)):
    rect([bx, by, 46, 22], "#ece6d8", "small family house (villa) on the hill")
    poly([(bx - 4, by), (bx + 23, by - 14), (bx + 50, by)], "#a5543a")
rect([1660, 150, 260, 330], "#e0cf98", "tall yellowish panel block of the estate (balcony bands)")
S.append({"type": "bars", "box": [1660, 170, 260, 300], "step": 34, "bar": 8, "fill": "#b9a87a", "vertical": False})
poly([(1270, 470), (1290, 250), (1315, 130), (1340, 250), (1362, 470)], "#9aa84e", "tall poplar behind the court")
poly([(1350, 470), (1360, 300), (1430, 240), (1520, 255), (1600, 230), (1680, 280), (1760, 260), (1850, 300), (1920, 290),
      (1920, 480), (1350, 480)], "#5e8a3d", "trees of the estate behind the court")
# the school
poly([(0, top(0)), (X1, top(X1)), (X1, base(X1)), (0, base(0))], "#e2cc8a",
     "long three-storey yard facade, plain pale yellowish render")
poly([(0, top(0) - 6), (X1, top(X1) - 4), (X1, top(X1) + 9), (0, top(0) + 14)], "#b9a676", "flat-roof attic edge")
for f0, f1, note in ((0.10, 0.28, "top-floor ribbon windows"), (0.43, 0.61, "first-floor ribbon windows")):
    poly([(0, at(0, f0)), (X1, at(X1, f0)), (X1, at(X1, f1)), (0, at(0, f1))], "#a3b8c2", note)
    x = 6
    while x < X1:
        line([(x, at(x, f0)), (x, at(x, f1))], "#f2efe6", 4)
        x += 46 * (1 - 0.35 * x / X1)
    line([(0, at(0, f1) + 3), (X1, at(X1, f1) + 2)], "#f2efe6", 5)
# ground floor: slab line, recessed dark glazing between square piers
line([(0, at(0, 0.667)), (X1, at(X1, 0.667))], "#c7b277", 8)
poly([(0, at(0, 0.70)), (X1, at(X1, 0.70)), (X1, base(X1)), (0, base(0))], "#4f5d63", "recessed dark glazing of the ground floor")
x = 20
while x < X1:
    w = 22 * (1 - 0.35 * x / X1)
    poly([(x, at(x, 0.70)), (x + w, at(x + w, 0.70)), (x + w, base(x + w)), (x, base(x))], "#dcc684")
    x += 120 * (1 - 0.35 * x / X1)
# yard entrance door (owner: used as the class entrance)
dx0, dx1 = 868, 924
rect([dx0 - 14, at(895, 0.70) - 10, dx1 - dx0 + 28, 9], "#7d888c", "small flat steel canopy over the yard door")
poly([(dx0, at(dx0, 0.72)), (dx1, at(dx1, 0.72)), (dx1, base(dx1)), (dx0, base(dx0))], "#6a4e34",
     "glazed double door of the yard entrance")
rect([dx0 + 6, at(895, 0.75), 20, 52], "#93abb4")
rect([dx0 + 30, at(895, 0.75), 20, 52], "#93abb4")
rect([dx0 - 10, base(895) - 2, dx1 - dx0 + 20, 12], "#cdc7ba", "concrete landing in front of the door")
# grass bank in front of the facade and the path down from the door
poly([(0, base(0)), (X1, base(X1)), (X1, bank(X1)), (0, bank(0))], "#7aa84a", "grass bank along the facade")
poly([(dx0 - 4, base(895) + 9), (dx1 + 4, base(895) + 9), (dx1 + 22, bank(925) + 2), (dx0 - 12, bank(860) + 2)], "#cbc5b8",
     "concrete path down the bank from the yard door")
# right: court fence, big lawn, clay track
poly([(1150, 466), (1920, 452), (1920, 578), (1150, 492)], "#86b14e", "big lawn inside the athletics track")
rect([1235, 318, 685, 162], "#7c9a74", "tall steel-mesh fence of the multi-sport court (see-through, trees behind)")
S.append({"type": "bars", "box": [1235, 318, 685, 162], "step": 62, "bar": 6, "fill": "#4c6a4a", "vertical": True})
rect([1235, 318, 685, 7], "#4c6a4a")
rect([1235, 472, 685, 9], "#a59f92", "low concrete base of the fence")
poly([(1150, tr0(1150)), (1920, tr0(1920)), (1920, tr1(1920)), (1150, tr1(1150))], "#b2674a", "red clay athletics track")
poly([(1150, tr1(1150)), (1920, tr1(1920)), (1920, tr1(1920) + 14), (1150, tr1(1150) + 4)], "#86b14e", "lawn edge")
# yard asphalt (one colour from the bank / track down to the bottom)
poly([(0, bank(0)), (X1, bank(X1)), (1150, bank(1150)), (1150, tr1(1150) + 4), (1920, tr1(1920) + 14), (1920, 1080),
      (0, 1080)], "#8f8a83", "worn asphalt of the school yard")
# basketball hoop at the asphalt edge in front of the track
rect([1612, 290, 12, 312], "#6d7377", "steel pole of the basketball hoop (foot y 602)")
rect([1550, 262, 140, 86], "#f3f1ea", "white backboard")
rect([1596, 300, 46, 36], "#f3f1ea", outline="#c0392b", width=3)
ell([1598, 344, 44, 11], None, "orange hoop ring without a net", outline="#e2702a", width=5)
# art panel on two posts
rect([214, 574, 8, 60], "#6e7073", "post")
rect([370, 574, 8, 60], "#6e7073", "post")
rect([200, 442, 192, 132], "#f5f1e6", "painted art panel: four big shapes and a rhythm pattern")
ell([214, 456, 40, 40], "#d8483a")
poly([(266, 496), (288, 456), (310, 496)], "#3b7bd6")
rect([322, 458, 36, 36], "#e9b62e")
poly([(372, 456), (380, 474), (388, 456), (388, 496), (372, 496)], "#7b4fb5")
line([(212, 526), (226, 512), (240, 526), (254, 512), (268, 526), (282, 512), (296, 526)], "#2e8b57", 5)
for i in range(2):
    rect([306 + i * 14, 508, 6, 22], "#333333")
for i in range(6):
    rect([212 + i * 28, 546, 18, 14], "#d8483a")
# grass bed, linden, bench, service wall, pipe
poly([(452, 676), (788, 676), (806, 706), (440, 706)], "#79a74a", "small grass bed at the back edge of the yard")
rect([440, 702, 366, 6], "#bdb6a8", "low kerb of the bed")
if ERA == "1995":
    poly([(612, 690), (628, 690), (625, 330), (617, 330)], "#6d5641", "thin damaged linden trunk with a bark scar")
    line([(621, 420), (575, 330)], "#6d5641", 7)
    line([(622, 380), (668, 300)], "#6d5641", 7)
    line([(620, 335), (612, 250)], "#6d5641", 6)
    ell([535, 185, 175, 170], "#98b85c", "sparse, weak crown with gaps")
    ell([560, 245, 40, 34], "#a9cbe6")
    ell([640, 210, 30, 30], "#c3d9ea")
    ell([600, 300, 34, 26], "#a9cbe6")
rect([690, 585, 240, 11], "#8a5a34", "bench backrest slats")
rect([690, 602, 240, 11], "#8a5a34")
rect([686, 626, 248, 15], "#93623a", "bench seat")
rect([702, 596, 14, 104], "#9b978f", "concrete bench leg")
rect([904, 596, 14, 104], "#9b978f", "concrete bench leg")
rect([950, 540, 390, 15], "#c9c2b3", "concrete coping of the low brick wall")
rect([958, 555, 374, 145], "#a95a3b", "low red-brick service wall (foot y 700)")
S.append({"type": "grid", "box": [958, 555, 374, 145], "cols": 17, "rows": 9, "color": "#8b4630", "width": 2})
rect([1080, 574, 150, 104], "#a39e94", "inset panel of 3 rows x 4 columns of grey stones (the service niche)")
S.append({"type": "grid", "box": [1080, 574, 150, 104], "cols": 4, "rows": 3, "color": "#6c675f", "width": 4})
rect([1372, 640, 22, 66], "#c23b2a", "red water-pipe elbow rising from the ground (axis x 1382)")
rect([1350, 622, 66, 22], "#c23b2a")
rect([1342, 616, 12, 34], "#8c2a1e", "flange")
spec = {"note": f"S17 natural sketch ({ERA}): L_YARD camera from src/game/data/blocking/S17.json - horizon y 380, prop foot "
                "line y 700, facade roof 80->180, foot 451->428 (x 0->1250); generated by a sketch script (geometry in the note "
                "of the blocking file)",
        "background": "#a9cbe6", "shapes": S}
json.dump(spec, open(sys.argv[2], "w", encoding="utf-8"), indent=1)
print(len(S), "shapes")
