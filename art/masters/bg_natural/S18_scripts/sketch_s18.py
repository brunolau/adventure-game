"""Sketch for S18 (1995 June) / S62 (1982 December) courtyard: the long panel block receding to the VP (305, 404).
usage: sketch_s18.py ERA OUT.json   (ERA 1995 = kiosk; 1982 = bigger shop serving window, see S62 blocking)"""
import json
import sys

ERA = sys.argv[1]
S = []
HC = 2.03
VPX, HOR, SLOPE = 305, 404, 0.177


def add(d, note=None):
    if note:
        d["note"] = note
    S.append(d)


def rect(b, fill, note=None, **kw):
    add({"type": "rect", "box": [round(v) for v in b], "fill": fill, **kw}, note)


def poly(pts, fill, note=None):
    add({"type": "poly", "points": [[round(x), round(y)] for x, y in pts], "fill": fill}, note)


def line(pts, color, width, note=None):
    add({"type": "line", "points": [[round(x), round(y)] for x, y in pts], "color": color, "width": width}, note)


def ell(b, fill, note=None, **kw):
    add({"type": "ellipse", "box": [round(v) for v in b], "fill": fill, **kw}, note)


def foot(x):
    return HOR + (x - VPX) * SLOPE


def yh(x, h):
    """canvas y of height h (m) on the block facade at x"""
    return HOR + (foot(x) - HOR) * (1 - h / HC)


def band(x0, x1, h0, h1, fill, note=None):
    poly([(x0, yh(x0, h1)), (x1, yh(x1, h1)), (x1, yh(x1, h0)), (x0, yh(x0, h0))], fill, note)


def xd(dist):  # x of the facade point at real distance dist (m), f = 1500 px
    o = 1500 * HC / dist
    return VPX + o / SLOPE


winter = ERA == "1982"
SKY = "#c9d3dc" if winter else "#a9cbe6"
rect([0, 0, 1920, 470], SKY, "sky")
rect([0, 330, 1920, 140], "#d6dde3" if winter else "#c3d9ea", "paler sky near the horizon")
# far blocks at the left (end walls) and trees
rect([0, 250, 70, 230], "#d9b54a", "far yellow block")
rect([70, 300, 250, 180], "#cfc6b4", "end wall of a far panel block (beige concrete)")
rect([120, 255, 210, 50], "#cfc6b4")
rect([330, 330, 330, 150], "#c8bfae", "lower far block behind the kiosk")
for px in (30, 150):
    poly([(px, 480), (px + 40, 250), (px + 80, 480)], "#3d5a3a" if not winter else "#4a5a48", "pine tree")
# the long block (main base: the carl_eric photo)
X0, X1 = 650, 1920
poly([(X0, yh(X0, 13.0)), (X1, yh(X1, 13.0)), (X1, foot(X1)), (X0, foot(X0))], "#e3dfd6", "long four-storey panel block, white-grey concrete")
band(X0, X1, 12.6, 13.0, "#c9c4b8", "flat roof attic")
for h in (1.6, 4.4, 7.2, 10.0):
    band(X0, X1, h, h + 1.0, "#b4554a", f"red balcony parapet band at {h} m")
    band(X0, X1, h + 1.0, h + 2.6, "#8f9aa0", "dark loggia recess / windows")
band(X0, X1, 0.0, 1.6, "#cdc8bc", "ground level: storage walls and entrance doors under the raised ground floor")
# loggia dividing walls
for d in [10.6 + i * 3.25 for i in range(13)]:
    x = xd(d)
    if X0 < x < X1:
        line([(x, yh(x, 12.6)), (x, yh(x, 0))], "#f1eee6", max(2, round(9 * 10.6 / d)))
# entrance stairs (one per section)
for d in (14.0, 27.0, 40.0):
    x = xd(d)
    w = 260 * 10.6 / d
    poly([(x - w, foot(x - w)), (x, yh(x, 1.6)), (x + 0.15 * w, yh(x, 1.6)), (x - 0.85 * w, foot(x - w))], "#4a4f52",
         "steel entrance stair rising to the raised ground floor")
    line([(x - w, yh(x - w, 0.9)), (x, yh(x, 2.5))], "#2f3437", 3)
# lawn in front of the block, path edge at y 740
poly([(0, 480), (X0, foot(X0)), (X1, foot(X1)), (1920, 745), (0, 745)], "#7fa652" if not winter else "#a3a48a", "courtyard lawn")
if winter:
    for b in ([700, 560, 220, 30], [1000, 640, 300, 40], [120, 600, 300, 30], [1500, 700, 250, 30]):
        ell(b, "#eef1f3", "thin snow patch")
# drying racks behind a low wire fence on the lawn
for x in (840, 1000, 1160):
    rect([x - 5, 408, 10, 242], "#6c7277", "steel drying-rack post (foot y 650)")
    rect([x - 109, 404, 218, 9], "#6c7277", "T crossbar")
for yl in (418, 440):
    line([(731, yl), (1269, yl)], "#5a5f62", 2)
if not winter:
    for i, (x, c) in enumerate([(760, "#f3f1ea"), (800, "#e7c34a"), (850, "#7fb2de"), (905, "#f3f1ea"), (960, "#e46b5a"),
                                (1030, "#9fd18f"), (1080, "#f3f1ea"), (1130, "#c58ad6"), (1190, "#7fb2de")]):
        rect([x, 420 + (i % 2) * 22, 38, 70 + (i % 3) * 12], c, "laundry on the lines")
rect([790, 562, 440, 128], "#a8b0a6", "low wire-mesh fence around the drying yard (top y 562, foot y 690)")
add({"type": "grid", "box": [790, 562, 440, 128], "cols": 22, "rows": 6, "color": "#7e877e", "width": 1})
rect([790, 556, 440, 8], "#6c7277")
# benches along the path
rect([1200, 594, 280, 14], "#8a5a34", "bench backrest")
rect([1200, 616, 280, 14], "#8a5a34")
rect([1194, 656, 292, 16], "#93623a", "bench seat")
rect([1215, 672, 14, 63], "#9b978f", "bench leg")
rect([1451, 672, 14, 63], "#9b978f", "bench leg")
# big linden at the right
rect([1668, 300, 64, 430], "#6d5641", "linden trunk (foot 1700,728)")
crown = "#5f8f3e" if not winter else None
if crown:
    ell([1380, -80, 620, 620], crown, "big linden crown")
    ell([1300, 60, 300, 300], "#6a9a46")
else:
    for a, b in (((1700, 330), (1560, 120)), ((1700, 360), (1860, 140)), ((1700, 300), (1700, 40)), ((1600, 200), (1480, 60))):
        line([a, b], "#5e4c3e", 14)
# courtyard paving (walk area)
rect([0, 740, 1920, 340], "#b3aa9b", "concrete paving slabs of the courtyard path (one plain surface)")
rect([0, 734, 1920, 8], "#9e9686", "kerb edge between lawn and paving (above the walk area)")
if ERA == "1995":
    # Zita's newspaper kiosk
    rect([310, 318, 440, 30], "#c0392b", "kiosk roof canopy (red)")
    rect([330, 348, 400, 60], "#efe9dc", "plain cream fascia (no lettering)")
    rect([330, 408, 400, 332], "#e9e2d2", "kiosk body (cream sheet metal)")
    rect([345, 410, 95, 190], "#d8e4ea", "left glass panel with newspapers on clips")
    for i in range(3):
        rect([350 + i * 30, 425, 26, 160], ["#f4f1e8", "#e8e2cf", "#f4f1e8"][i])
    rect([445, 410, 180, 156], "#3b3a3a", "open sales window, dim interior (Zita stands here)")
    rect([435, 562, 200, 12], "#bdb7aa", "sales window sill (top y 566)")
    rect([630, 410, 85, 190], "#d8e4ea", "right glass panel with gum and sweets")
    for r in range(5):
        for c in range(3):
            rect([636 + c * 26, 432 + r * 28, 22, 20], ["#e74c3c", "#3498db", "#f1c40f", "#2ecc71", "#e67e22"][(r + c) % 5])
    rect([330, 600, 400, 140], "#c9c0ab", "lower kiosk panels")
    rect([330, 600, 400, 8], "#c0392b", "red trim")
spec = {"note": f"S18/S62 courtyard sketch ({ERA}): VP ({VPX}, {HOR}), block foot y = {HOR} + (x - {VPX}) * {SLOPE}, camera 2.03 m, "
                "path back edge y 740; generated by a sketch script (camera in the blocking note)",
        "background": SKY, "shapes": S}
json.dump(spec, open(sys.argv[2], "w", encoding="utf-8"), indent=1)
print(len(S), "shapes")
