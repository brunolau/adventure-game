"""L_STOP (Svantnerova stop) camera + sketch generator (2026-10-06 owner Dubravka corrections). Writes the S11 sketch:
    python art/prompts/natural/S11.sketch_camera.py 4 art/prompts/natural/S11.sketch.json   (yaw 4 deg; prints key points)

World: X metres to the right (NE, towards the tracks), Z metres ahead (NW, along the platform), Y up; platform top Y=0.
Camera on the SW platform at X=0, Z=0, eye E above the platform, yaw THETA to the right, pitch 0.
The far street rises: ground offset g(Z) = 0 until Z0, then a parabola over L metres, then slope S.
"""
from __future__ import annotations

import json
import math
import sys

F, CX, CY = 1250.0, 960.0, 400.0
E = 2.04
THETA = math.radians(float(sys.argv[1]) if len(sys.argv) > 1 else 4.0)
Z0, L, S = 22.0, 30.0, 0.07
CT, ST = math.cos(THETA), math.sin(THETA)


def g(z: float) -> float:
    if z <= Z0:
        return 0.0
    if z <= Z0 + L:
        return S * (z - Z0) ** 2 / (2 * L)
    return S * (z - Z0 - L / 2)


def P(x: float, y: float, z: float, ground: bool = True) -> list[float]:
    """Project; y is relative to the local ground (g(z) added) unless ground=False."""
    yy = y + (g(z) if ground else 0.0)
    xc = x * CT - z * ST
    zc = x * ST + z * CT
    zc = max(zc, 0.05)
    return [round(CX + F * xc / zc, 1), round(CY - F * (yy - E) / zc, 1)]


def zs(z0: float, z1: float, n: int = 24) -> list[float]:
    """Samples along Z, denser near the camera."""
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(z0 * (z1 / z0) ** t)
    return out


def strip(x0, x1, y0, y1, z0, z1, n=30):
    """A ground strip between X x0..x1 (heights y0 at x0, y1 at x1) from Z z0 to z1 (curved with the slope)."""
    a = [P(x0, y0, z) for z in zs(z0, z1, n)]
    b = [P(x1, y1, z) for z in reversed(zs(z0, z1, n))]
    return a + b


def wall(x, z0, z1, yb, yt, n=16):
    """A vertical wall in the plane X=x from z0 to z1, from yb to yt above the local ground."""
    a = [P(x, yb, z) for z in zs(z0, z1, n)]
    b = [P(x, yt, z) for z in reversed(zs(z0, z1, n))]
    return a + b


BASE = None


def Pb(x, y, z):
    """Project with a fixed ground base (buildings stand level on a terrace) when BASE is set."""
    if BASE is None:
        return P(x, y, z)
    return P(x, y + BASE, z, ground=False)


def face_z(x0, x1, z, yb, yt):
    """A vertical face at Z=z from x0 to x1 (facing the camera)."""
    return [Pb(x0, yb, z), Pb(x1, yb, z), Pb(x1, yt, z), Pb(x0, yt, z)]


def box_faces(x0, x1, z0, z1, h, base=0.0):
    """Visible faces of a box (front face at z0 and the side facing the camera)."""
    faces = [face_z(x0, x1, z0, base, h)]
    if x0 > 0:
        faces.append(wall(x0, z0, z1, base, h, 4))     # left side visible
    elif x1 < 0:
        faces.append(wall(x1, z0, z1, base, h, 4))     # right side visible
    return faces


shapes: list[dict] = []


def poly(points, fill, note):
    shapes.append({"type": "poly", "points": points, "fill": fill, "note": note})


def line(points, color, width, note):
    shapes.append({"type": "line", "points": points, "color": color, "width": width, "note": note})


def rect(box, fill, note, **kw):
    shapes.append(dict({"type": "rect", "box": box, "fill": fill, "note": note}, **kw))


def ellipse(box, fill, note, **kw):
    shapes.append(dict({"type": "ellipse", "box": box, "fill": fill, "note": note}, **kw))


ZFAR = 330.0
info: dict = {}

# --- sky and the far distance
rect([0, 0, 1920, 520], "#a9c9e8", "sky, clear June morning")
rect([0, 380, 1920, 700], "#86ad55", "ground (lawns) under everything")
poly(strip(-120, 120, 0.0, 0.0, 30, 330.0, 40), "#86ad55", "lawns along the rising street")
poly(strip(-40, -11.2, 0.3, -0.1, 3, 330.0, 40), "#86ad55", "lawn verge and slope left of the west carriageway")
poly(strip(16.4, 60, -0.15, 0.2, 6, 330.0, 40), "#86ad55", "lawn and pavement on the right in front of the medical centre")
# distant white towers on the far rise (behind the crest of the street)
for x0, x1, z, h, col in ((-95, -70, 520, 40, "#e9e3d6"), (-60, -42, 560, 38, "#e4ddcf"), (55, 75, 600, 42, "#e7e0d2"),
                          (-20, -5, 640, 30, "#e2dccf")):
    poly(face_z(x0, x1, z, -1, h), col, "distant white panel tower on the hill beyond the crest of the street")
# far tree belt along the rising street (left and right of the crest)
far_belt = [P(-260, 0, 300), P(-110, 10, 360), P(-45, 8, 470), P(-12, 5, 470), P(14, 5, 470), P(50, 9, 470),
            P(130, 11, 360), P(260, 0, 300), P(260, -1, 150), P(-260, -1, 150)]
poly(far_belt, "#6d9748", "far tree belt along the street as it rises to its crest")

# --- right side: the tall panel blocks with red-orange balconies behind the medical centre
def slab(x0, x1, z0, z1, h, wallc, balc, floors, note):
    global BASE
    BASE = g(z0)
    poly(face_z(x0, x1, z0, -1, h), wallc, note + " (end wall)")
    side = wall(x0, z0, z1, -1, h, 10)
    poly(side, wallc, note + " (long facade towards the street)")
    for k in range(floors):
        yb = 1.0 + k * (h - 2) / floors
        band = [P(x0 - 0.3, yb, z) for z in zs(z0 + 1, z1 - 1, 10)] + \
               [P(x0 - 0.3, yb + 0.9, z) for z in reversed(zs(z0 + 1, z1 - 1, 10))]
        poly(band, balc, note + " (balcony band)")


slab(70, 82, 46, 200, 27, "#eadfca", "#c85a32", 8, "long 8-storey panel block with red-orange balconies behind the medical centre")
# right-hand trees between the street and the blocks
for x, z, r in ((40, 95, 6.5), (36, 130, 7.0), (28, 175, 7.0), (20, 220, 7.0)):
    c = P(x, 5.5, z)
    rr = F * r / (x * ST + z * CT)
    ellipse([c[0] - rr, c[1] - rr * 0.9, 2 * rr, 1.8 * rr], "#5e8f3d", "birch / linden crown on the right")

# --- left side: tall point towers with yellow-orange balconies and the tree slope
def tower(x0, x1, z0, z1, h, wallc, balc, floors, note):
    global BASE
    BASE = g(z0)
    poly(face_z(x0, x1, z0, -1, h), wallc, note)
    poly(wall(x1, z0, z1, -1, h, 4), "#d8c7a0", note + " (side)")
    for k in range(floors):
        yb = 1.2 + k * (h - 2) / floors
        poly([Pb(x0 + 1, yb, z0 - 0.2), Pb(x1 - 1, yb, z0 - 0.2), Pb(x1 - 1, yb + 0.9, z0 - 0.2),
              Pb(x0 + 1, yb + 0.9, z0 - 0.2)], balc, note + " (balcony band)")
    BASE = None


tower(-52, -36, 44, 60, 38, "#e4d5ad", "#dc9a3c", 12, "12-storey point tower with yellow-orange balconies (left)")
tower(-60, -44, 150, 166, 36, "#e8dcc0", "#cc5a3a", 12, "12-storey point tower with red balconies (left, further)")
# tree slope on the left (lindens, maples) beyond the west carriageway
left_trees = [P(-13.5, 0, 14), P(-13.5, 0, 90), P(-13, 0, 240), P(-15, 6, 260), P(-17, 6.5, 130), P(-18, 6.5, 60),
              P(-18, 6, 34), P(-17, 5.5, 20), P(-16, 5, 14)]
poly(left_trees, "#5b8c3a", "line of big lindens on the green slope beyond the west carriageway")
for x, z, r in ((-17, 30, 3.6), (-18, 52, 4.4), (-17, 80, 5.0), (-16, 115, 5.5)):
    c = P(x, 5.5, z)
    rr = F * r / (x * ST + z * CT)
    ellipse([c[0] - rr, c[1] - rr * 0.9, 2 * rr, 1.7 * rr], "#62953f", "linden crown (left)")

# --- the medical centre (low, bluish, 2 storeys, ribbon windows) beyond the east carriageway on the right
MC = dict(x0=21.0, x1=33.0, z0=30.0, z1=88.0, h=7.6)
BASE = 0.4
poly(face_z(MC["x0"], MC["x1"], MC["z0"], 0, MC["h"]), "#5f8fa6", "medical centre: end wall")
poly(wall(MC["x0"], MC["z0"], MC["z1"], 0, MC["h"], 12), "#6f9fb4",
     "medical centre: long low bluish 2-storey facade facing the street")
for yb, yt in ((1.1, 2.6), (4.4, 6.0)):
    poly([Pb(MC["x0"] - 0.05, yb, z) for z in zs(37.0, MC["z1"] - 2, 12)] +
         [Pb(MC["x0"] - 0.05, yt, z) for z in reversed(zs(37.0, MC["z1"] - 2, 12))],
         "#dfe9ee", "medical centre: ribbon window band (white frames)")
poly([Pb(MC["x0"] - 0.05, 6.9, z) for z in zs(MC["z0"], MC["z1"], 12)] +
     [Pb(MC["x0"] - 0.05, 7.6, z) for z in reversed(zs(MC["z0"], MC["z1"], 12))], "#e6eef0",
     "medical centre: white roof edge")
# near end of the medical centre: clad in blue-grey mosaic tiles (solid wall, as in the friend's photo)
poly(face_z(21.0, 33.0, 30.0, 0, 7.9), "#5c86a8", "medical centre: end wall clad in blue-grey mosaic tiles")
poly(wall(21.0, 30.0, 36.0, 0, 7.9, 4), "#6a93b4", "medical centre: near part of the facade, solid blue-grey mosaic tiles")
info["medical_centre_px"] = [Pb(MC["x0"], MC["h"], MC["z1"]), Pb(21.0, 0, 30.0), Pb(21.0, 7.9, 30.0)]
BASE = None
for x, z, r in ((18.5, 64, 3.2),):
    c = P(x, 6.0, z)
    rr = F * r / (x * ST + z * CT)
    line([P(x, -0.15, z), c], "#e8e4dc", 4, "white birch trunk")
    ellipse([c[0] - rr * 0.7, c[1] - rr, 1.4 * rr, 2.0 * rr], "#86b04a", "birch in fresh green leaf in front of the medical centre")

# --- ground: verges, roads, track bed, platform
poly(strip(-4.0, 1.8, -0.1, -0.1, 58, ZFAR, 30), "#8db45c", "grass median strip beyond the end of the platform")
poly(strip(-11.2, -4.0, -0.25, -0.25, 2.2, ZFAR, 40), "#7d7b78", "west carriageway (asphalt), rising into the distance")
poly(strip(16.0, 17.8, -0.15, -0.15, 6, ZFAR, 40), "#c6c0b4", "pavement along the east carriageway")
poly(strip(9.4, 16.0, -0.35, -0.35, 3.5, ZFAR, 40), "#7d7b78", "east carriageway (asphalt), rising into the distance")
poly(strip(1.8, 9.2, -0.25, -0.25, 2.0, ZFAR, 40), "#aaa397",
     "tram track bed of big grey concrete panels (two tracks), grass in the joints")
# panel joints across the track bed
for z in (4.6, 6.4, 8.6, 11.4, 15.0, 20.0, 26.0):
    line([P(1.8, -0.25, z), P(9.2, -0.25, z)], "#938c80", 2, "joint between concrete track panels")
# rails: near track (X 2.55, 3.99), far track (X 5.95, 7.39)
for xr in (2.55, 3.99, 5.95, 7.39):
    line([P(xr, -0.25, z) for z in zs(2.0, ZFAR, 40)], "#4a4642", 5, "grooved rail set in the concrete panels")
# red tube railing along the far edge of the track bed
rail_pts = [P(9.25, 1.0, z) for z in zs(3.0, 200, 30)]
line(rail_pts, "#b8322a", 5, "red steel-tube railing between the track bed and the east carriageway")
line([P(9.25, 0.5, z) for z in zs(3.0, 200, 30)], "#b8322a", 3, "red railing lower rail")
for z in (3.4, 5.2, 7.5, 10.5, 14.5, 20, 28, 40, 56, 80):
    line([P(9.25, -0.25, z), P(9.25, 1.0, z)], "#b8322a", 4, "red railing post")
# the platform (walkable) with its light edge strip along the track
poly(strip(-3.4, 1.8, 0.0, 0.0, 1.2, 60, 30), "#bab3a7", "platform of big grey concrete slabs (walkable)")
poly(strip(1.35, 1.8, 0.0, 0.0, 1.2, 60, 30), "#e9e3d4", "light, almost white edge strip along the track")
poly(strip(1.8, 1.9, 0.0, -0.25, 1.2, 60, 20), "#8f8a80", "platform edge face down to the track bed")
# the low road-side wall with the railing (beyond the shelter and at the near end)
poly(wall(-3.4, 1.5, 4.4, -0.25, 0.55, 4), "#c9c3b6", "low concrete wall along the platform's road side (near end)")
poly(wall(-3.4, 24.0, 60.0, -0.25, 0.55, 8), "#c9c3b6", "low concrete wall along the platform's road side (far part)")
line([P(-3.4, 1.05, z) for z in zs(1.5, 4.4, 4)], "#5a6470", 4, "steel tube railing on the low wall")
line([P(-3.4, 1.05, z) for z in zs(24.0, 60.0, 8)], "#5a6470", 3, "steel tube railing on the low wall (far)")
for z in (2.5, 4.4, 24, 30, 38, 48):
    line([P(-3.4, 0.55, z), P(-3.4, 1.05, z)], "#5a6470", 3, "railing post")
# ramp + zebra crossing at the near left (towards the school)
ramp = [P(-3.4, 0.0, 4.4), P(-3.4, 0.0, 6.9), P(-4.4, -0.25, 6.9), P(-4.4, -0.25, 4.4)]
poly(ramp, "#a49d91", "short concrete ramp down from the platform to the zebra crossing (gap in the wall)")
line([P(-3.4, 0.0, 6.9), P(-3.4, 0.0, 3.0)], "#8f887c", 4, "kerb edge where the platform drops to the ramp")
for k in range(5):
    xa, xb = -4.6 - k * 1.3, -4.6 - k * 1.3 - 0.6
    poly([P(xa, -0.24, 4.4), P(xb, -0.24, 4.4), P(xb, -0.24, 6.9), P(xa, -0.24, 6.9)], "#ecebe6",
         "white zebra-crossing stripe on the west carriageway")
info["curb"] = P(-3.4, 0.0, 6.9)
poly(wall(-3.4, 6.9, 24.0, -0.25, 0.0, 10), "#8f887c", "platform kerb face down to the west carriageway")
poly(face_z(-3.4, -3.12, 6.9, 0.0, 0.55), "#a8a196", "end of the low concrete wall at the ramp, its corner chipped off")
poly(wall(-3.12, 6.9, 7.05, 0.0, 0.55, 2), "#c9c3b6", "low concrete wall end (side)")
info["wall_end"] = [P(-3.4, 0.0, 6.9), P(-3.12, 0.55, 6.9)]
# centre line of the west carriageway
for z in (10, 18, 30, 50, 80, 130):
    line([P(-7.6, -0.25, z), P(-7.6, -0.25, z * 1.18)], "#f2f0ea", 3, "dashed centre line")
for z in (12, 20, 32, 52, 85, 140):
    line([P(12.7, -0.35, z), P(12.7, -0.35, z * 1.18)], "#f2f0ea", 3, "dashed centre line (east)")

# --- street lamps (tall, rust-red, curved arms) along the outer edges of both carriageways; span wires across
for z in (30.0, 48.0, 70.0, 100.0, 140.0, 190.0):
    for x, arm in ((-11.8, 1.8), (16.6, -1.8)):
        b, t = P(x, -0.25, z), P(x, 9.0, z)
        line([b, t], "#8a3c2a", 6 if z < 60 else 3, "tall rust-red street lamp post")
        line([t, P(x + arm, 9.5, z)], "#8a3c2a", 3, "curved lamp arm with the lamp head")
    line([P(-11.8, 7.2, z), P(16.6, 7.2, z)], "#3a3a3a", 1, "span wire across the street carrying the contact wires")
line([P(3.27, 5.6, z) for z in zs(3.0, 200, 30)], "#2e2e2e", 2, "overhead contact wire above the near track")
line([P(6.67, 5.6, z) for z in zs(3.0, 200, 30)], "#2e2e2e", 2, "overhead contact wire above the far track")
# near traction pole on the right (frame edge)
line([P(9.5, -0.25, 14.0), P(9.5, 9.5, 14.0)], "#8a3c2a", 9, "near tall rust-red lamp / traction pole on the right")
line([P(9.5, 7.0, 14.0), P(3.27, 7.0, 14.0)], "#3a3a3a", 2, "near cross-span wire")

# --- the old shelter: long arches of brown steel tube, solid brown back wall, translucent light-blue roof
SH = dict(xb=-3.2, xf=-1.30, z0=7.0, z1=23.0, hb=2.30, hf=2.35, apex=2.75)
poly(wall(SH["xb"], SH["z0"], SH["z1"], 0.0, SH["hb"], 10), "#7a4a30",
     "solid brown back wall of vertical boards along the road side")
roof = [P(SH["xb"], SH["hb"], z) for z in zs(SH["z0"], SH["z1"], 10)] + \
       [P(SH["xf"], SH["hf"], z) for z in reversed(zs(SH["z0"], SH["z1"], 10))]
poly(roof, "#86bddc", "translucent light-blue curved plastic roof")
n_arch = 7
for k in range(n_arch):
    z = SH["z0"] + k * (SH["z1"] - SH["z0"]) / (n_arch - 1)
    w = 6 if z < 12 else 4
    arch = [P(SH["xb"], 0.0, z), P(SH["xb"], SH["hb"], z), P(-2.6, SH["apex"], z), P(-1.9, SH["apex"] - 0.05, z),
            P(SH["xf"], SH["hf"], z), P(SH["xf"], 0.0, z)]
    line(arch, "#6b2f22", w, "brown steel-tube arch of the shelter")
line([P(SH["xf"], SH["hf"], z) for z in zs(SH["z0"], SH["z1"], 8)], "#6b2f22", 5, "front tube along the roof edge")
# bench along the inside of the back wall
BE = dict(xa=-3.15, xb=-2.70, z0=8.6, z1=12.6, h=0.46)
seat = [P(BE["xa"], BE["h"], BE["z0"]), P(BE["xb"], BE["h"], BE["z0"]), P(BE["xb"], BE["h"], BE["z1"]),
        P(BE["xa"], BE["h"], BE["z1"])]
poly(seat, "#c08a50", "wooden slat bench seat (along the back wall)")
back = [P(SH["xb"] + 0.05, 0.5, BE["z0"]), P(SH["xb"] + 0.05, 0.95, BE["z0"]), P(SH["xb"] + 0.05, 0.95, BE["z1"]),
        P(SH["xb"] + 0.05, 0.5, BE["z1"])]
poly(back, "#a8743e", "bench backrest slats")
for z in (BE["z0"] + 0.2, BE["z1"] - 0.2):
    line([P(BE["xb"], BE["h"], z), P(BE["xb"], 0.0, z)], "#2b2b2b", 4, "bench leg")
pts = [seat[0], seat[1], seat[2], seat[3], P(BE["xb"], 0.0, BE["z0"])]
info["bench_box"] = [min(p[0] for p in pts + back), min(p[1] for p in pts + back),
                     max(p[0] for p in pts + back), max(p[1] for p in pts)]
# poster in the first bay of the back wall
poster = [P(SH["xb"] + 0.03, 1.0, 7.2), P(SH["xb"] + 0.03, 2.0, 7.2), P(SH["xb"] + 0.03, 2.0, 8.4),
          P(SH["xb"] + 0.03, 1.0, 8.4)]
poly(poster, "#d9b54a", "colourful 1990s poster with abstract shapes, no lettering")

# --- the stop post at the shelter's near front corner: clock, stop plate, timetable case
POST = dict(x=-0.95, z=6.2)
pb, pt = P(POST["x"], 0.0, POST["z"]), P(POST["x"], 3.0, POST["z"])
line([pb, pt], "#4f555c", 7, "grey steel stop post")
clock_c = P(POST["x"], 3.28, POST["z"])
r_px = F * 0.29 / (POST["x"] * ST + POST["z"] * CT)
ellipse([clock_c[0] - r_px, clock_c[1] - r_px, 2 * r_px, 2 * r_px], "#f6f2e4", "round stop clock: white dial",
        outline="#c9a040", width=8)
info["clock_c"] = clock_c
info["clock_r"] = r_px
plate = [P(POST["x"] - 0.24, 2.45, POST["z"]), P(POST["x"] + 0.24, 2.45, POST["z"]),
         P(POST["x"] + 0.24, 2.85, POST["z"]), P(POST["x"] - 0.24, 2.85, POST["z"])]
poly(plate, "#f4f3ee", "small white stop plate with red border and tram pictogram")
case = [P(POST["x"] - 0.26, 1.20, POST["z"]), P(POST["x"] + 0.26, 1.20, POST["z"]),
        P(POST["x"] + 0.26, 1.80, POST["z"]), P(POST["x"] - 0.26, 1.80, POST["z"])]
poly(case, "#efeadf", "glazed timetable case")
info["case"] = case
info["plate"] = plate
info["post_foot"] = pb

# --- the red-cream Tatra T3 standing at the platform on the near track
TR = dict(x0=2.02, x1=4.52, zf=10.5, zr=25.0, rail=-0.25)
tb, tw0, tw1, troof = TR["rail"] + 0.35, TR["rail"] + 1.55, TR["rail"] + 2.70, TR["rail"] + 3.10
side_poly = lambda yb, yt: [P(TR["x0"], yb, TR["zf"]), P(TR["x0"], yb, TR["zr"]), P(TR["x0"], yt, TR["zr"]),
                            P(TR["x0"], yt, TR["zf"])]
poly(side_poly(tb, troof), "#efe3c8", "tram side (cream)")
poly(side_poly(tb, tw0), "#c8322a", "tram side lower body (red)")
poly(side_poly(tw0 + 0.15, tw1), "#5a6e7c", "tram side windows")
front = face_z(TR["x0"], TR["x1"], TR["zf"], tb, troof)
poly(front, "#efe3c8", "tram front (cream upper part)")
poly(face_z(TR["x0"], TR["x1"], TR["zf"], tb, tw0 + 0.05), "#c8322a", "tram front (red lower part)")
poly(face_z(TR["x0"] + 0.2, TR["x1"] - 0.2, TR["zf"], tw0 + 0.2, tw1), "#3e5260", "tram windscreen")
poly(face_z(TR["x0"] + 0.6, TR["x1"] - 0.6, TR["zf"], tw1 + 0.05, troof - 0.05), "#2e2e2e", "blank route box")
poly([P(TR["x0"], troof, TR["zf"]), P(TR["x1"], troof, TR["zf"]), P(TR["x1"], troof, TR["zr"]),
      P(TR["x0"], troof, TR["zr"])], "#d8ccb2", "tram roof")
pant = [P(3.27, troof, 15.0), P(2.9, 5.6, 14.2), P(3.6, 5.6, 14.2), P(3.27, troof, 15.0)]
line(pant, "#3a3a3a", 4, "diamond pantograph raised to the contact wire")
info["tram_front"] = front
info["tram_side_far"] = P(TR["x0"], tb, TR["zr"])

# horizon VP of the near track (flat part) and far points of the rising track
info["vp_flat"] = P(3.27, 0, 1e6, ground=False)
info["track_far"] = {z: P(3.27, -0.25, z) for z in (40, 60, 80, 120, 200, 300)}
info["track_line"] = P(3.99, -0.25, 7.4)


def wp(x, z):
    return P(x, 0.0, z)


# walk polygon on the platform (in front of the shelter, beside it up to the edge strip, plus the ramp)
info["walk"] = {"bottom_left": wp(-3.4, 1.0), "ramp_outer": P(-4.2, -0.25, 2.0), "curb": P(-3.4, 0.0, 3.2),
                "shelter_near_back": wp(-3.4, 6.6), "post_front": wp(-0.55, 6.6), "shelter_front_far": wp(-1.0, 9.6),
                "edge_far": wp(1.30, 9.6), "edge_near": wp(1.30, 3.9), "edge_bottom": wp(1.30, 3.2)}

sketch = {"note": ("L_STOP natural sketch 2026-10-06 (owner Dubravka corrections): pinhole camera f 1250 px, eye 2.04 m "
                   f"above the platform, horizon y 400, yaw {math.degrees(THETA):.1f} deg right of the platform axis; "
                   f"the street rises from Z {Z0:.0f} m (slope {S * 100:.0f} %). Platform X -3.4..1.8 m, shelter "
                   "X -3.2..-1.3, Z 7-23; tracks X 2.55-7.39 on concrete panels, red railing X 9.25, east carriageway "
                   "X 9.4-16, medical centre X 21-33 Z 30-88 (2 storeys, blue mosaic near end), red-balcony 8-storey slab X 70-82 Z 46-200, yellow-balcony point tower X -52..-36 Z 44-60. Generator: scratchpad stop_cam.py (log S11.md)."),
          "background": "#a9c9e8", "shapes": shapes}
json.dump(sketch, open(sys.argv[2] if len(sys.argv) > 2 else "S11.sketch.json", "w", encoding="utf-8"), indent=1)
print(json.dumps(info, indent=1))
