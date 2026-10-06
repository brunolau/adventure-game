"""Generate art/prompts/natural/S17.sketch.json (L_YARD base, 1995 June) - relayout 2026-10-06 (owner satellite view).

Camera (same lens and height as the first S17 layout, so walk_band / actor_scale stay): pinhole, focal 1220 px,
centre x 960, eye 2.1 m above the yard asphalt, horizon y 380.  World: X metres to the right, Z metres ahead.
    screen x = 960 + 1220 * X / Z ;  screen y = 380 + 1220 * (2.1 - Y) / Z   (Y = height above the yard)

Layout (owner 2026-10-06, art/feedback/2026-10-05_owner_feedback.md, satellite view looked at only): standing in the
yard and looking SW at the long yard facade of the main wing:
  - LEFT: the red clay running track ("antuka") with grass inside it - the NW end curve of the oval (outer radius
    17.5 m, inner 12.5 m, centre X -21, Z 22), its far straight running out of the left edge in front of the school;
  - RIGHT: the court fence runs AWAY from the camera (perpendicular to the facade, 90 deg to the old painting) along
    X = 6.6 m, from the right frame edge (Z 8.4) to the court's far end (Z 30); behind it the court
    (1995/1982 concrete playground with basketball baskets, 2020 artificial-turf football pitch);
  - a paved way (X 2.6-6.6) runs along that fence from the yard to the yard entrance door (the owner's class entrance);
  - BACKGROUND: the main wing (3 storeys on a 1.2 m grass bank) from its SE corner (x 430, Z 60) to the right edge
    (Z 45), the lower gym wing left of the corner, trees and the wooded Dubravka hill with villas behind.
Story props keep their places (linden bed, bench, service wall with the stone panel, red pipe, art panel); a litter bin
stands by the fence at the yard edge (the S55 "Kos" hotspot, the same bin in every era).

    python art/masters/bg_natural/S17_scripts/sketch_s17.py 1995 art/prompts/natural/S17.sketch.json
"""
import json
import math
import sys

ERA = sys.argv[1] if len(sys.argv) > 1 else "1995"
F, CX, HOR, EYE = 1220.0, 960.0, 380.0, 2.1
S = []


def P(X, Z, Y=0.0):
    return (CX + F * X / Z, HOR + F * (EYE - Y) / Z)


def rect(b, fill, note=None, **kw):
    d = {"type": "rect", "box": [round(v) for v in b], "fill": fill}
    if note:
        d["note"] = note
    d.update(kw)
    S.append(d)


def poly(pts, fill, note=None, **kw):
    d = {"type": "poly", "points": [[round(x), round(y)] for x, y in pts], "fill": fill}
    if note:
        d["note"] = note
    d.update(kw)
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


def clipx(pts):
    return [(min(max(x, -40), 1960), y) for x, y in pts]


# --------------------------------------------------------------------------- sky, hill
rect([0, 0, 1920, 430], "#a9cbe6", "June afternoon sky")
rect([0, 280, 1920, 150], "#c3d9ea", "paler sky near the horizon")
poly([(0, 240), (220, 212), (460, 196), (700, 204), (950, 222), (1200, 214), (1450, 196), (1700, 186), (1920, 178),
      (1920, 430), (0, 430)], "#5f8048", "wooded Dubravka hill behind the school")
for bx, by in ((40, 236), (150, 226), (265, 214), (380, 206)):
    rect([bx, by, 42, 20], "#ece6d8", "small family house (villa) on the hill")
    poly([(bx - 4, by), (bx + 21, by - 13), (bx + 46, by)], "#a5543a")

# --------------------------------------------------------------------------- school: gym wing + main wing
poly([(0, 262), (300, 262), (300, 250), (430, 250), (430, 400), (0, 400)], "#8fae6a", "tree crowns beside the gym wing")
poly([(0, 300), (425, 288), (425, 399), (0, 401)], "#dcc78f", "lower two-storey gym wing, plain yellowish render")
poly([(0, 293), (425, 282), (425, 290), (0, 302)], "#b9a676", "gym wing roof edge")
poly([(20, 318), (405, 309), (405, 352), (20, 360)], "#8fa3ad", "tall gym windows")
for x in range(40, 410, 48):
    line([(x, 316), (x, 358)], "#efe9d8", 4)

C_T, C_F = P(-26, 60, 11.7), P(-26, 60, 1.2)      # corner roof / foot
R_T, R_F = P(35.4, 45, 11.7), P(35.4, 45, 1.2)    # right edge roof / foot


def fac(t, Y):
    """point on the facade plane: t 0 corner .. 1 right edge, Y height above the yard."""
    return P(-26 + 61.4 * t, 60 - 15 * t, Y)


def band(Y0, Y1, fill, note=None):
    poly([fac(0, Y1), fac(1, Y1), fac(1, Y0), fac(0, Y0)], fill, note)


poly([fac(0, 11.7), fac(1, 11.7), fac(1, 1.2), fac(0, 1.2)], "#e2cc8a",
     "long three-storey main wing, yard facade, plain pale yellowish render (1995)")
band(11.2, 11.9, "#b9a676", "flat-roof attic edge")
for Y0, Y1, note in ((8.75, 10.6, "top-floor ribbon windows"), (5.3, 7.2, "first-floor ribbon windows")):
    band(Y0, Y1, "#a3b8c2", note)
    t = 0.004
    while t < 1:
        line([fac(t, Y0), fac(t, Y1)], "#f2efe6", 4)
        t += 1.45 / 63.2
    line([fac(0, Y0 - 0.05), fac(1, Y0 - 0.05)], "#f2efe6", 5)
band(4.35, 4.9, "#c7b277", "ground-floor slab band")
band(1.2, 4.35, "#4f5d63", "recessed dark glazing of the ground floor between square piers")
t = 0.01
while t < 1:
    poly([fac(t, 4.35), fac(t + 0.007, 4.35), fac(t + 0.007, 1.2), fac(t, 1.2)], "#dcc684")
    t += 4.6 / 63.2
# yard entrance (the owner's class entrance): glazed double door, small flat steel canopy, steps down the bank
d0, d1 = 0.45, 0.49
poly([fac(d0 - 0.008, 4.05), fac(d1 + 0.008, 4.05), fac(d1 + 0.008, 3.8), fac(d0 - 0.008, 3.8)], "#7d888c",
     "small flat steel canopy over the yard door")
poly([fac(d0, 3.75), fac(d1, 3.75), fac(d1, 1.2), fac(d0, 1.2)], "#6a4e34", "glazed double door of the yard entrance")
poly([fac(d0 + 0.005, 3.4), fac(d0 + 0.018, 3.4), fac(d0 + 0.018, 1.5), fac(d0 + 0.005, 1.5)], "#93abb4")
poly([fac(d1 - 0.018, 3.4), fac(d1 - 0.005, 3.4), fac(d1 - 0.005, 1.5), fac(d1 - 0.018, 1.5)], "#93abb4")

# --------------------------------------------------------------------------- ground: bank, lawn, track
poly([fac(0, 1.2), fac(1, 1.2), (1920, P(35.4, 41)[1]), P(-26, 56)], "#7aa84a", "grass bank along the facade")
poly([P(-26, 56), (1920, P(35.4, 41)[1]), (1920, 700), (0, 700), (0, P(-26, 56)[1])], "#86b14e",
     "big lawn between the school, the track and the yard")
# steps + landing from the yard door down the bank to the paved way
poly([fac(d0 - 0.01, 1.25), fac(d1 + 0.01, 1.25), P(4.6, 48.4), P(1.4, 48.4)], "#cbc5b8",
     "concrete steps down the bank from the yard door")


def oval(r, th0, th1, n=40):
    return [P(-21 + r * math.cos(math.radians(a)), 22 - r * math.sin(math.radians(a)))
            for a in [th0 + (th1 - th0) * i / n for i in range(n + 1)]]


outer = oval(17.5, -90, 43)
inner = oval(12.5, -90, 39)
far_out, far_in = P(-21, 39.5), P(-21, 34.5)
track = [(0, far_out[1])] + outer + [(0, outer[-1][1])]
poly(clipx(track), "#b2674a", "red clay running track (antuka): the NW end curve of the oval, far straight to the left")
infield = [(0, far_in[1])] + inner + [(0, inner[-1][1])]
poly(clipx(infield), "#8cb553", "grass inside the running track")
line(clipx(oval(15.0, -90, 41)), "#d9b8a0", 2, "faint lane line")

# --------------------------------------------------------------------------- court behind the fence (right)
FX, FZ0, FZ1, FH = 6.6, 1220 * 6.6 / 960, 30.0, 3.5
court = [P(FX, FZ1), (1920, P(FX, FZ1)[1]), (1920, P(FX, FZ0)[1]), P(FX, FZ0)]
poly(court, "#a9a49a", "the court behind the fence: 1995 concrete playground (grey concrete slabs, faded white lines)")
line([P(FX + 1.0, FZ1 - 1.0), P(FX + 1.0, 9.6)], "#e3e0d8", 2, "faded white court line")
line([P(FX + 1.0, FZ1 - 1.0), (1920, P(FX + 1.0, FZ1 - 1.0)[1])], "#e3e0d8", 2)
poly([P(FX, FZ1), (1920, P(FX, FZ1)[1]), (1920, P(FX, 41)[1]), P(FX, 41)], "#86b14e", "lawn beyond the court")
# far basketball basket (the hotspot of S17.ambient 1), on the court's centre line 1.2 m inside the far end
bx, bz = 15.6, 28.8
line([P(bx, bz), P(bx, bz, 3.9)], "#6d7377", 7, "steel pole of a basketball basket")
b_tl, b_br = P(bx - 0.9, bz - 0.4, 3.95), P(bx + 0.9, bz - 0.4, 2.9)
rect([b_tl[0], b_tl[1], b_br[0] - b_tl[0], b_br[1] - b_tl[1]], "#f3f1ea", "white backboard facing the camera")
r0, r1 = P(bx - 0.25, bz - 0.85, 3.05), P(bx + 0.25, bz - 0.85, 3.05)
ell([r0[0], r0[1] - 4, r1[0] - r0[0], 8], None, "orange hoop ring without a net", outline="#e2702a", width=4)
# the fence: long side running away from the camera along X = 6.6, far short side at Z 30
posts = [FZ0, 10.0, 12.0, 14.5, 17.5, 21.0, 25.0, FZ1]
for z in posts:
    line([P(FX, z), P(FX, z, FH)], "#3f5a40", 9 if z < 12 else 6, "dark green steel fence post")
for Y, w in ((FH, 7), (2.3, 3), (1.15, 3)):
    line([P(FX, FZ0, Y), P(FX, FZ1, Y)], "#3f5a40", w, "fence rail")
for i in range(1, 15):
    z = FZ0 + (FZ1 - FZ0) * (i / 15) ** 1.6
    line([P(FX, z), P(FX, z, FH)], "#6f8a6c", 2, "wire mesh (see-through)")
line([P(FX, FZ0, 0.15), P(FX, FZ1, 0.15)], "#a59f92", 8, "low concrete base of the fence")
for x in range(int(P(FX, FZ1)[0]), 1921, 70):
    zt = FZ1
    line([(x, P(FX, zt)[1]), (x, P(FX, zt, FH)[1])], "#4c6a4a", 4, "far fence of the court (see-through)")
line([P(FX, FZ1, FH), (1920, P(FX, FZ1, FH)[1])], "#4c6a4a", 4)

# --------------------------------------------------------------------------- yard asphalt and the paved way
asphalt = [(0, 640), P(2.6, 9.85), P(2.6, 48.4), P(5.4, 48.4), P(FX, FZ1), (1920, P(FX, FZ0)[1]), (1920, 1080),
           (0, 1080)]
poly(asphalt, "#8f8a83", "worn asphalt of the school yard and the paved way along the court fence to the yard door")
line([(0, 640), P(2.6, 9.85), P(2.6, 48.4)], "#bdb6a8", 4, "low kerb at the back edge of the yard / along the way")
# litter bin by the fence at the yard edge (S55 'Kos'; the same bin in every era)
b0, b1 = P(5.15, 8.0, 0.92), P(5.65, 8.0, 0.0)
rect([b0[0], b0[1] + 12, b1[0] - b0[0], b1[1] - b0[1] - 12], "#3e5b45", "dark green steel litter bin on a short post")
rect([b0[0] - 4, b0[1], b1[0] - b0[0] + 8, 14], "#2f4535")

# --------------------------------------------------------------------------- art panel on two posts
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
# --------------------------------------------------------------------------- grass bed, linden, bench, wall, pipe
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
    ell([600, 300, 34, 26], "#a3b8c2")
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

spec = {"note": f"S17 natural sketch ({ERA}), relayout 2026-10-06: L_YARD camera (focal 1220, eye 2.1 m, horizon y 380) "
                "looking SW at the yard facade; clay track with grass inside on the LEFT, the court fence running away "
                "from the camera on the RIGHT with the court behind it; generated by "
                "art/masters/bg_natural/S17_scripts/sketch_s17.py (geometry in its docstring and in the blocking note)",
        "background": "#a9cbe6", "shapes": S}
json.dump(spec, open(sys.argv[2], "w", encoding="utf-8"), indent=1)
print(len(S), "shapes; corner", [round(v) for v in C_T], [round(v) for v in C_F], "right", [round(v) for v in R_T],
      [round(v) for v in R_F], "door", [round(v) for v in fac(d0, 1.2)], [round(v) for v in fac(d1, 3.75)],
      "fence near", [round(v) for v in P(FX, FZ0)], [round(v) for v in P(FX, FZ0, FH)], "far",
      [round(v) for v in P(FX, FZ1)], [round(v) for v in P(FX, FZ1, FH)], "board", [round(v) for v in b_tl],
      [round(v) for v in b_br], "bin", [round(v) for v in b0], [round(v) for v in b1])
