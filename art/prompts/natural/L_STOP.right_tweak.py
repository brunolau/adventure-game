"""L_STOP (Svantnerova stop) right-hand background tweak, owner request 2026-10-06, for S11 (1995), S51 (2020), S57 (1982).

Owner: "the medical centre should be moved lower - in reality only part of it should be visible ... the houses on the
right side have to be taller, they are 8-storey panelaks". Only the right-hand background changes (x >= 1262, above
the grass verge of the east carriageway); the camera, tracks, shelter, stop post, left side, walk band and blocking stay.

Geometry (game px, measured on the accepted masters, identical in the three rooms):
  * the medical centre is lowered column by column: each column moves down by C_LOWER x its painted height, which is
    the exact projection of a building sunk by about half its height (a column of a facade has one depth, so the drop
    is f*D/Zc = C_LOWER * h(x)); everything below the verge crest (CREST) stays the original painting, so only the
    roof edge, the upper ribbon windows and a strip of the mosaic tiles show above the verge;
  * the old 5-storey-looking slab is replaced by a further-away, taller slab: ground floor + 8 floors + attic (26.5 m),
    rendered as a flat-colour placeholder in the L_STOP pinhole camera (f 1250, horizon y 400, eye 2.04 m) on a plane
    whose lines converge to the painted buildings' vanishing point (~810, 400); far end at x 1288 (Zc 184 m, floor
    pitch 19 px), its top line leaves the frame at x ~1726; the base (ground +6.4 m) is hidden behind the medical
    centre's roof;
  * S11: the paid edit (nano-banana-pro, mock + style + the friend's photo) repaints the placeholder collage into a
    finished painting, but always with ~1.6x bigger floors (5-6 instead of 8). `final` therefore replaces the slab
    by the model's own painted facade RE-PROJECTED at 0.622x (TEX / slab_from_texture: 8 floors + ground floor,
    exact perspective), keeps the rest of the model's edit region, mirrors the painting's trees at the slab's far
    end, restores lamp posts / wires, and puts the T3 back pixel-exact (alpha of the cut sprite tram_t3_body.webp);
  * S51 / S57: full-frame edits rebuilt the medical centre (rejected), so the mock is built deterministically from the
    room's own painting (its medical centre lowered, the S11 facade graded to the room's own slab colours, S57 with
    snow on the parapets) and only the verge strip in front of the medical centre comes from a paid crop edit (`band`);
  * the composite takes only the edit region (x >= X0, above crest + 14 px, 12 px seam), so everything else stays
    pixel-identical; `accept` writes the next master version + sidecar (S11 also the new track_empty patch).

  python art/prompts/natural/L_STOP.right_tweak.py mock S11|S51|S57          free: art/masters/bg_natural/_<room>_right_mock.png
  python art/prompts/natural/L_STOP.right_tweak.py paint S11 --budget 2.5 [--seed N]       paid (USD 0.15), full-frame edit
  python art/prompts/natural/L_STOP.right_tweak.py band S51|S57 --budget 2.5 [--seed N]    paid (USD 0.15), verge-strip crop
  python art/prompts/natural/L_STOP.right_tweak.py final S11 --raw <raw> | final S51 --band <raw>   free candidate (review)
  python art/prompts/natural/L_STOP.right_tweak.py accept <same arguments as final>        free: next master + sidecar
  then: python art/tools/paint_natural.py export <room> <version>; art/tools/ambient_cut.py --natural <room>
Accepted 2026-10-06: S11 v4 (--raw _S11_right_s110601_raw.png), S51 v4 (--band _S51_band_s205111_raw.png),
S57 v5 (--band _S57_band_s198211_raw.png).
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "art" / "tools"))
import fal_api  # noqa: E402
import paint_room as pr  # noqa: E402

MASTERS = ROOT / "art" / "masters" / "bg_natural"
REVIEW = ROOT / "art" / "review" / "natural" / "svantnerova_tweak"
K = 1080 / 1536              # game px per master px
CROP = 7                     # master -> game crops 7 px on the left
MW, MH = 2752, 1536
SCOPE = "bg_natural/svantnerova_tweak/"

BASE_VERSION = {"S11": 3, "S51": 3, "S57": 4}

# ---------------------------------------------------------------- measured geometry (game px)
X0 = 1262                                                     # left edge of the edit region
ROOF = [(1262, 280.5), (1268, 279), (1578, 201), (1580, 190), (1708, 158), (1711, 147), (1920, 152)]
FOOT = [(1262, 428), (1578, 447), (1710, 471), (1920, 476)]   # painted foot of the medical centre
C_LOWER = 0.5


def crest(x):
    """Crest of the grass verge beyond the east carriageway (the street is above the medical centre's ground)."""
    return 432.0 + 0.0699 * (np.asarray(x, dtype=np.float64) - 1262.0)


def pl(x, pts):
    xs, ys = zip(*pts)
    return np.interp(np.asarray(x, dtype=np.float64), xs, ys)


def drop(x):
    return C_LOWER * (pl(x, FOOT) - pl(x, ROOF))


# lamp posts and overhead wires in front of the buildings: kept from the original painting in the mock-up
POSTS = [(1292, 183, 1300, None), (1535, 113, 1550, None), (1677, 0, 1698, None), (1672, 258, 1702, 348)]  # x0, y0, x1, y1 (None = crest)
POST_HEADS = [(1262, 183, 1302, 207), (1462, 86, 1553, 117)]
WIRES = [((1262, 185.0), (1625, 0.0), 5), ((1262, 185.0), (1540, 185.0), 3), ((1262, 248.0), (1292, 248.0), 3)]

# the new slab (camera coordinates of the L_STOP pinhole camera, metres)
F, CX, CY, EYE = 1250.0, 960.0, 400.0, 2.04
PHI = math.radians(-6.5)                    # facade direction (lines converge at x ~ 960 + f tan(PHI))
SLAB_FAR = (48.3, 184.0)                    # Xc, Zc of the far end (x 1288)
SLAB_BASE = 6.4                             # ground under the slab above the platform (hidden)
GROUND_H, FLOOR_H, FLOORS, ATTIC_H = 3.0, 2.8, 8, 1.1
SLAB_H = GROUND_H + FLOOR_H * FLOORS + ATTIC_H


def g2m_x(gx):
    return (np.asarray(gx, dtype=np.float64) + CROP) / K


def m2g_x(mx):
    return np.asarray(mx, dtype=np.float64) * K - CROP


def load_rgb(path) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    if img.size != (MW, MH):
        img = img.resize((MW, MH), Image.Resampling.LANCZOS)
    return np.asarray(img, dtype=np.float32)


def game_alpha_to_master(alpha_g: np.ndarray) -> np.ndarray:
    """A 1920x1080 alpha in game px -> master px (inverse of fit_to_frame)."""
    canvas = np.zeros((1080, 1935), dtype=np.float32)
    canvas[:, CROP:CROP + 1920] = alpha_g
    img = Image.fromarray((canvas * 255).astype(np.uint8), "L").resize((MW, MH), Image.Resampling.BILINEAR)
    return np.asarray(img, dtype=np.float32) / 255


def s11_tram_alpha_master() -> np.ndarray:
    """Alpha of the painted T3 (body + pantograph, without its platform shadow) in master px, from the cut sprite."""
    info = json.loads((ROOT / "art/ambient/natural/vehicles/S11_build.json").read_text(encoding="utf-8"))["tram_t3"]
    body = np.asarray(Image.open(ROOT / "src/game/assets/ambient/S11/natural/tram_t3_body.webp").convert("RGBA"),
                      dtype=np.float32)[..., 3] / 255
    out = np.zeros((MH, MW), dtype=np.float32)
    ox, oy = info["origin_master"]
    h, w = body.shape
    out[oy:oy + h, ox:ox + w] = body
    return out


def s11_track_patch():
    p = Image.open(ROOT / "src/game/assets/ambient/S11/natural/track_empty.webp").convert("RGBA")
    info = json.loads((ROOT / "art/ambient/natural/vehicles/S11_build.json").read_text(encoding="utf-8"))["track_empty"]
    return p, tuple(info["pos"])


def room_base(room: str) -> tuple[np.ndarray, np.ndarray]:
    """(accepted master, view the edit works on) in master px. S11: the view with the T3 gone (painting + the
    track_empty patch's source edit), so the edit also paints what is behind the tram."""
    master = load_rgb(MASTERS / f"{room}_v{BASE_VERSION[room]}.png")
    if room != "S11":
        return master, master.copy()
    notram = load_rgb(ROOT / "art/ambient/natural/vehicles/S11_notram_v2_raw.png")
    patch, (px, py) = s11_track_patch()
    a = np.zeros((1080, 1920), dtype=np.float32)
    pa = np.asarray(patch, dtype=np.float32)[..., 3] / 255
    a[py:py + pa.shape[0], px:px + pa.shape[1]] = pa
    am = game_alpha_to_master(a)[..., None]
    return master, master * (1 - am) + notram * am


# ---------------------------------------------------------------- masks (master px)

def grids():
    my, mx = np.mgrid[0:MH, 0:MW]
    return mx.astype(np.float64) * K - CROP, my.astype(np.float64) * K


def edit_mask(feather_g: float = 12.0, below: float = 14.0) -> np.ndarray:
    """1 inside the edit region (x >= X0 and above the verge crest + `below` game px), soft seam on the left and the
    bottom; the frame's top and right edges are not feathered."""
    gx, gy = grids()
    dx = (gx - X0) / feather_g
    dy = (crest(gx) + below - gy) / feather_g
    m = np.clip(np.minimum(dx, dy) + 0.5, 0, 1)
    return m.astype(np.float32)


def tophat(rgb: np.ndarray, k: int = 7) -> np.ndarray:
    lum = Image.fromarray(np.clip(rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32), 0, 255).astype(np.uint8))
    c = lum.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.MinFilter(k))
    return np.asarray(c, dtype=np.float32) - np.asarray(lum, dtype=np.float32)


def post_pixels(orig: np.ndarray, thr: float = 26.0) -> np.ndarray:
    """The lamp-post shafts inside their rectangles: pixels that differ from the painting just left AND just right
    of the rectangle in the same row (so the old background beside a shaft is never restored)."""
    out = np.zeros((MH, MW), dtype=bool)
    for x0, y0, x1, y1 in POSTS:
        yb = float(crest(x1)) + 20 if y1 is None else y1
        a, b = int(g2m_x(x0)) - 1, int(np.ceil(g2m_x(x1))) + 1
        r0, r1 = int(y0 / K), min(MH, int(yb / K) + 1)
        band = orig[r0:r1, a:b]
        left = np.median(orig[r0:r1, a - 7:a - 1], 1)[:, None, :]
        right = np.median(orig[r0:r1, b + 1:b + 7], 1)[:, None, :]
        dl = np.abs(band - left).sum(-1)
        dr = np.abs(band - right).sum(-1)
        m = (dl > thr) & (dr > thr)
        # each row: from the first to the last such pixel (the shaft is one solid run)
        idx = np.arange(m.shape[1])[None, :]
        has = m.any(1)
        first = np.where(has, np.argmax(m, 1), 0)[:, None]
        last = np.where(has, m.shape[1] - 1 - np.argmax(m[:, ::-1], 1), -1)[:, None]
        out[r0:r1, a:b] = (idx >= first) & (idx <= last)
    return out


def cutlib_poly(pts) -> np.ndarray:
    img = Image.new("L", (MW, MH), 0)
    ImageDraw.Draw(img).polygon([(float(g2m_x(x)), y / K) for x, y in pts], fill=255)
    return np.asarray(img) > 0


HEAD_ROOM = {"room": "S11"}       # which room's colours head_ok() assumes (set by build_mock / finalize)


def head_ok(img: np.ndarray) -> np.ndarray:
    """Inside the lamp-head boxes only the lamp, its arm and the sky - never the old slab's roof edge behind the arm
    (it has thin dark lines too): S51's grey arm is bluish, the old slab cream; S11/S57's arm is rust-red."""
    gx, gy = grids()
    v = img / 255
    if HEAD_ROOM["room"] == "S51":
        # the grey 2020 arm has the colour of the old slab's roof-edge line: limit it to the arm's own outline
        lum = v @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        poly = cutlib_poly([(1462, 88), (1503, 88), (1503, 99), (1545, 107), (1553, 107), (1553, 120), (1538, 120),
                            (1500, 112), (1462, 112)])
        arm = (lum < 0.75) & poly
    else:
        arm = v[..., 0] - v[..., 2] > 0.16
    new_top = TEX["vp"][1] + TARGET["m_top"] * (gx - TEX["vp"][0])
    return arm | (gy < new_top - 2)


def protect_mask(orig: np.ndarray) -> np.ndarray:
    """Lamp posts and overhead wires in front of the buildings (master px, soft)."""
    img = Image.new("L", (MW, MH), 0)
    d = ImageDraw.Draw(img)
    for x0, y0, x1, y1 in POSTS:
        yb = float(crest(x1)) + 20 if y1 is None else y1
        d.rectangle([g2m_x(x0), y0 / K, g2m_x(x1), yb / K], fill=255)
    for x0, y0, x1, y1 in POST_HEADS:
        d.rectangle([g2m_x(x0), y0 / K, g2m_x(x1), y1 / K], fill=255)
    rect = np.asarray(img) > 0
    th = tophat(orig, 9)
    heads = rect & (th > 6) & head_ok(orig)
    posts = post_pixels(orig)
    wim = Image.new("L", (MW, MH), 0)
    wd = ImageDraw.Draw(wim)
    for (ax, ay), (bx, by), w in WIRES:
        wd.line([(g2m_x(ax), ay / K), (g2m_x(bx), by / K)], fill=255, width=int(round(2 * w / K)))
    wires = (np.asarray(wim) > 0) & (th > 10)
    m = posts | heads | wires
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
                   .filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float32) / 255
    return m


# ---------------------------------------------------------------- the new slab

def slab_colours(orig: np.ndarray) -> dict:
    gx, gy = grids()
    top = np.interp(gx, [1300, 1860, 1920], [175, 0, 0])
    region = (gy > top + 6) & (gy < pl(gx, ROOF) - 6) & (gx > 1340) & (tophat(orig) < 12)
    for x0, _, x1, _ in POSTS:
        region &= ~((gx > x0 - 6) & (gx < x1 + 6))
    px = orig[region] / 255
    mx, mn = px.max(1), px.min(1)
    sat = (mx - mn) / np.maximum(mx, 1e-3)
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    red = (r > g + 0.12) & (r > b + 0.15) & (sat > 0.3)
    beige = (sat < 0.28) & (mx > 0.62)
    dark = mx < 0.45
    med = lambda sel, fb: (np.median(px[sel], 0) * 255) if sel.sum() > 50 else np.array(fb, dtype=np.float64)
    return {"red": med(red, (190, 96, 62)), "wall": med(beige, (214, 200, 176)), "dark": med(dark, (82, 78, 80))}


def render_slab(cols: dict, sky_row: np.ndarray, ss: int = 2) -> tuple[np.ndarray, np.ndarray]:
    """Placeholder facade of a long Bratislava panel block (ground floor + 8 floors with loggias), master px RGB+alpha."""
    gx_min = 1286
    mx0 = int(g2m_x(gx_min))
    my1 = int(400 / K)
    h, w = my1, MW - mx0
    yy, xx = np.mgrid[0:h * ss, 0:w * ss]
    mx = mx0 + (xx + 0.5) / ss
    my = (yy + 0.5) / ss
    gx = mx * K - CROP
    gy = my * K
    a = (gx - CX) / F
    bb = (CY - gy) / F
    d = np.array([math.sin(PHI), math.cos(PHI)])          # direction towards the far end (camera XZ)
    n = np.array([d[1], -d[0]])                            # facade normal
    pf = np.array(SLAB_FAR)
    t = (n @ pf) / (n[0] * a + n[1] * 1.0)
    px_, pz = t * a, t
    u = -((px_ - pf[0]) * d[0] + (pz - pf[1]) * d[1])      # metres from the far end towards the camera
    v = t * bb + EYE - SLAB_BASE                            # metres above the slab's ground
    inside = (u >= 0) & (v >= 0) & (v <= SLAB_H) & (t > 0)
    wall, red, dark = cols["wall"], cols["red"], cols["dark"]
    col = np.empty(u.shape + (3,), dtype=np.float32)
    col[:] = wall
    M = 7.2                                                # module: loggia 3.6 m between fins + wall bay
    um = np.mod(u, M)
    fin = (um < 0.3) | ((um >= 3.9) & (um < 4.2))
    log_bay = (um >= 0.3) & (um < 3.9)
    wall_bay = um >= 4.2
    fl = (v - GROUND_H) / FLOOR_H
    k = np.floor(fl)
    dv = (fl - k) * FLOOR_H
    upper = (v >= GROUND_H) & (k < FLOORS)
    shade = wall * 0.62
    # loggias: a recess (shaded back wall, a window and a balcony door), its ceiling in shadow, the red-orange
    # parapet panel in front of it
    rec = upper & log_bay & (dv >= 1.0)
    col[rec] = shade
    col[rec & (dv > 2.45)] = wall * 0.45
    door = rec & (um > 0.75) & (um < 1.55) & (dv < 2.3)
    win = rec & (um > 1.9) & (um < 3.45) & (dv > 1.35) & (dv < 2.3)
    col[door | win] = dark
    col[(door | win) & ((np.abs(um - 2.67) < 0.05) | (np.abs(um - 1.15) < 0.05))] = shade * 1.15
    par = upper & log_bay & (dv < 1.0)
    col[par] = red
    col[par & (dv > 0.9)] = np.minimum(red * 1.18, 255)       # lit top edge of the parapet
    col[par & (dv < 0.12)] = red * 0.7                        # its shadowed underside / slab edge
    # wall bays: one window per floor with a light frame
    wb = upper & wall_bay
    wwin = wb & (um > 5.0) & (um < 6.5) & (dv > 0.95) & (dv < 2.35)
    col[wb & (um > 4.92) & (um < 6.58) & (dv > 0.88) & (dv < 2.42)] = np.minimum(wall * 1.12, 255)
    col[wwin] = dark
    col[wwin & (np.abs(um - 5.75) < 0.05)] = np.minimum(wall * 1.1, 255)
    col[wb & (dv < 0.06)] = wall * 0.88                      # panel joint
    col[upper & fin] = np.minimum(wall * 1.1, 255)
    # ground floor and attic
    gf = v < GROUND_H
    col[gf] = wall * 0.82
    gdoor = gf & (np.mod(u, 28.8) > 10.5) & (np.mod(u, 28.8) < 12.3) & (v < 2.3)
    col[gdoor] = dark * 0.8
    att = v > GROUND_H + FLOOR_H * FLOORS
    col[att] = np.minimum(wall * 1.03, 255)
    col[v > SLAB_H - 0.18] = wall * 0.7
    # aerial haze towards the far end
    haze = np.clip((t - 70) / 300, 0, 0.22)[..., None]
    gy_i = np.clip(gy.astype(int), 0, len(sky_row) - 1)
    col = col * (1 - haze) + sky_row[gy_i] * haze
    alpha = inside.astype(np.float32)
    rgba = np.concatenate([col * alpha[..., None], alpha[..., None]], -1)
    rgba = rgba.reshape(h, ss, w, ss, 4).mean((1, 3))
    alpha = rgba[..., 3]
    rgb = rgba[..., :3] / np.maximum(alpha[..., None], 1e-4)
    out_rgb = np.zeros((MH, MW, 3), dtype=np.float32)
    out_a = np.zeros((MH, MW), dtype=np.float32)
    out_rgb[:h, mx0:] = rgb
    out_a[:h, mx0:] = alpha
    return out_rgb, out_a


# ---------------------------------------------------------------- mock-up

ROOM_LOOK = {
    "S11": {"verge": (86, 112, 52), "shrub": (62, 88, 40), "trees": (70, 100, 52)},
    "S51": {"verge": (128, 112, 58), "shrub": (176, 128, 52), "trees": (196, 128, 48)},
    "S57": {"verge": (226, 230, 232), "shrub": (232, 236, 238), "trees": (120, 118, 116)},
}


def old_top(gx):
    """Roof line of the old (5-storey-looking) slab in the accepted paintings; it starts at x 1300."""
    gx = np.asarray(gx, dtype=np.float64)
    return np.where(gx >= 1300, np.interp(gx, [1300, 1860, 1920], [175, 0, 0]), 1e4)


def sky_rows(orig: np.ndarray) -> np.ndarray:
    """Median sky colour per game row, from the painting's sky right of x 1262 above the old roofs (geometric, so it
    also works for the pale winter sky of S57); wires and lamp heads left out."""
    gx, gy = grids()
    sky = (gx >= X0) & (gy < np.minimum(old_top(gx) - 3, 200)) & (tophat(orig) < 6)
    for x0, y0, x1, y1 in POST_HEADS:
        sky &= ~((gx >= x0 - 3) & (gx <= x1 + 3) & (gy >= y0 - 3) & (gy <= y1 + 3))
    for x0, y0, x1, y1 in POSTS:
        sky &= ~((gx >= x0 - 3) & (gx <= x1 + 3))
    rows = np.full((1080, 3), np.nan)
    gyi = gy.astype(int)
    for y in range(0, 200):
        sel = sky & (gyi == y)
        if sel.sum() > 20:
            rows[y] = np.median(orig[sel], 0)
    last = rows[0] if not np.isnan(rows[0, 0]) else np.array([180, 205, 225])
    for y in range(1080):
        if np.isnan(rows[y, 0]):
            rows[y] = last
        else:
            last = rows[y]
    return rows.astype(np.float32)


def lower_centre(view: np.ndarray, orig: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The medical centre moved down column by column (bilinear in y); RGB + alpha in master px, clipped at the crest."""
    gx_cols = m2g_x(np.arange(MW))
    out = np.zeros_like(view)
    alpha = np.zeros((MH, MW), dtype=np.float32)
    ys = np.arange(MH, dtype=np.float64)
    # source mask: inside the painted silhouette, minus the far-end trees that stand in front of it (S51)
    for mx in range(int(g2m_x(1266)), MW):
        g = gx_cols[mx]
        roof, foot = float(pl(g, ROOF)), float(pl(g, FOOT))
        dm = float(drop(g)) / K
        src = ys - dm
        valid = (src * K >= roof - 0.5) & (src * K <= foot) & (ys * K < float(crest(g)))
        if not valid.any():
            continue
        s0 = np.clip(np.floor(src).astype(int), 0, MH - 2)
        fr = (src - s0)[:, None]
        colv = view[s0, mx] * (1 - fr) + view[s0 + 1, mx] * fr
        # soft roof edge (1 master px)
        edge = np.clip((src * K - (roof - 0.5)) / (K * 1.2), 0, 1)
        a = valid * edge
        out[:, mx] = colv
        alpha[:, mx] = a
    return out, alpha


BUSH_SEEDS = [(1790, 448), (1892, 452)]


def bush_mask(room: str, view: np.ndarray, cr) -> np.ndarray:
    """The two bushes on the verge in front of the tiled wing (x >= 1728), from the room's own colours."""
    gx, gy = grids()
    bz = (gx >= 1728) & (gy >= (402 if room == "S57" else 394)) & (gy < cr + 2)
    v = view / 255
    mx, mn = v.max(-1), v.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-3)
    r, g, b = v[..., 0], v[..., 1], v[..., 2]
    if room == "S57":
        # snowy bushes: snow and dark twigs, plus the silhouette of the same bushes in the 1995 painting (S11, green)
        m = ((mx > 0.84) & (sat < 0.12)) | (mx < 0.38)
        s11 = load_rgb(MASTERS / f"S11_v{BASE_VERSION['S11']}.png") / 255
        smx, smn = s11.max(-1), s11.min(-1)
        sg = ((s11[..., 1] > s11[..., 2] + 0.04) | (s11[..., 0] > s11[..., 2] + 0.1)) & ((smx - smn) / np.maximum(smx, 1e-3) > 0.22)
        sg = np.asarray(Image.fromarray(((sg & bz) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)),
                        dtype=np.uint8) > 127
        m |= sg
    else:
        warm_or_green = (g > b + 0.04) | (r > b + 0.1)
        m = warm_or_green & (sat > 0.22) & (mx > 0.18)
    m &= bz
    img = Image.fromarray((m * 255).astype(np.uint8))
    img = img.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    probe = img.copy()
    for sx, sy in BUSH_SEEDS:
        px, py = int(g2m_x(sx)), int(sy / K)
        if probe.getpixel((px, py)) > 127:
            ImageDraw.floodfill(probe, (px, py), 128, thresh=0)
    keep = np.asarray(probe) == 128
    fill = Image.fromarray((keep * 255).astype(np.uint8))
    pad = Image.new("L", (MW + 2, MH + 2), 0)
    pad.paste(fill, (1, 1))
    ImageDraw.floodfill(pad, (0, 0), 64)
    holes = np.asarray(pad)[1:-1, 1:-1] == 0
    return (keep | holes) & bz


def build_mock(room: str):
    HEAD_ROOM["room"] = room
    master, view = room_base(room)
    look = ROOM_LOOK[room]
    gx, gy = grids()
    rng = np.random.default_rng(1)
    sky = sky_rows(view)
    E = edit_mask(feather_g=1.0, below=0.0) > 0.5
    mock = view.copy()
    roof_now = pl(gx, ROOF) + drop(gx)
    above = E & (gy < roof_now)
    # 1. sky (the painted sky stays where it already is sky; the old slab and roofs above the new roof become sky)
    gyi = np.clip(gy.astype(int), 0, 1079)
    fill = above & (gx >= 1300) & (gy >= old_top(gx) - 2)
    mock[fill] = sky[gyi[fill]]
    # 2. trees behind the far end of the medical centre (x 1262-1300): keep the painted crowns, fill below them
    noise = rng.normal(0, 9, mock.shape).astype(np.float32)
    crowns = np.zeros(gx.shape, dtype=bool)
    for cx_, cy_, r_ in [(1268, 300, 22), (1284, 318, 20), (1272, 338, 18), (1294, 342, 14), (1266, 270, 14)]:
        crowns |= (gx - cx_) ** 2 + (gy - cy_) ** 2 < r_ ** 2
    tree_zone = above & (gx < 1302) & (gy > 262) & crowns
    tc = np.array(look["trees"], dtype=np.float32)
    light = np.clip((330 - gy) / 80, -0.3, 0.4)[..., None]
    mock[tree_zone] = (tc * (1 + light * 0.5) + noise * 1.4)[tree_zone]
    keep_tree = above & (gx < 1302) & (gy <= 262)
    mock[keep_tree] = view[keep_tree]
    # 3. the new slab (S11: flat placeholder; S51/S57: the re-projected S11 facade in the room's own slab colours)
    if room == "S11":
        srgb, sa = render_slab(slab_colours(view), sky)
    else:
        srgb, sa = slab_from_texture(lambda x: new_roof(x) + 1.0, grade=room_grade(view), snow=(room == "S57"))
    sa = sa * above
    mock = mock * (1 - sa[..., None]) + srgb * sa[..., None]
    # 4. the lowered medical centre
    crgb, ca = lower_centre(view, master)
    ca = ca * E
    mock = mock * (1 - ca[..., None]) + crgb * ca[..., None]
    # 5. verge crest: a low irregular band of grass / shrubs along the crest
    cr = crest(gx)
    bump = (np.sin(gx / 23.0) * 0.5 + np.sin(gx / 61.0 + 1.3) * 0.8 + np.sin(gx / 9.0) * 0.3) * 3.0 + 6.0
    shrubs = np.zeros_like(gx)
    for cx_, wdt, hgt in [(1330, 34, 16), (1420, 26, 12), (1490, 40, 18), (1615, 30, 14), (1650, 22, 10)]:
        shrubs = np.maximum(shrubs, hgt * np.clip(1 - ((gx - cx_) / wdt) ** 2, 0, 1) ** 0.5)
    band = E & (gy > cr - bump - shrubs) & (gy < cr + 2)
    tone = np.where((gy > cr - bump)[..., None], np.array(look["verge"], np.float32), np.array(look["shrub"], np.float32))
    mock[band] = (tone + noise * 0.8)[band]
    # 6. the bushes on the verge in front of the tiled wing stay: their own colours (per room), connected to the two
    #    bush centres, holes closed
    bush = bush_mask(room, view, cr)
    mock[bush] = view[bush]
    # 7. lamp posts and wires stay in front
    pm = protect_mask(view)[..., None] * edit_mask(feather_g=1.0, below=20.0)[..., None]
    mock = mock * (1 - pm) + view * pm
    return master, view, np.clip(mock, 0, 255)


def save_preview(arr: np.ndarray, path: Path, box=(1150, 0, 1920, 620)) -> None:
    img = pr.fit_to_frame(Image.fromarray(arr.astype(np.uint8)))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.crop(box).save(path)


def cmd_mock(args) -> None:
    master, view, mock = build_mock(args.room)
    out = MASTERS / f"_{args.room}_right_mock.png"
    Image.fromarray(mock.astype(np.uint8)).save(out)
    save_preview(mock, REVIEW / f"{args.room}_mock_right.png")
    save_preview(view, REVIEW / f"{args.room}_before_right.png")
    print(out.relative_to(ROOT))


# ---------------------------------------------------------------- paid edit

PROMPTS = {
    "S11": (
        "Image 1 is one of our finished point-and-click adventure game backgrounds: the Svantnerova tram stop in the "
        "Bratislava housing estate Dubravka on a sunny June morning in 1995. Its right part, above the far grass verge "
        "of the road on the right, is a rough collage that you must turn into a finished painting, keeping its new "
        "layout exactly: "
    ),
    "S51": (
        "Image 1 is one of our finished point-and-click adventure game backgrounds: the rebuilt Svantnerova tram stop "
        "in Bratislava-Dubravka on a sunny late-October afternoon in 2020 (autumn trees). Its right part, above the "
        "far grass verge of the road on the right, is a rough collage that you must turn into a finished painting, "
        "keeping its new layout exactly: "
    ),
    "S57": (
        "Image 1 is one of our finished point-and-click adventure game backgrounds: the Svantnerova stop in "
        "Bratislava-Dubravka on a cold December afternoon in 1982, thin old snow, the tram line still under "
        "construction. Its right part, above the far snowy verge of the road on the right, is a rough collage that "
        "you must turn into a finished painting, keeping its new layout exactly: "
    ),
}
CORE = (
    "(1) The long low bluish medical centre now stands LOWER than the street, below the road level: only its flat "
    "roof edge, its upper row of white ribbon windows and a strip of its blue-grey mosaic-tile facade show above the "
    "crest of the grass verge; its lower floor is hidden below the verge. Keep the medical centre exactly at this new "
    "lower height and paint the verge crest in front of it as a low grassy bank with a few low shrubs, like the "
    "street in image 3, where the same medical centre sits below the road. (2) The big flat beige placeholder block "
    "behind it with the red-orange bands is a long Bratislava prefabricated panel block (panelak) that stands further "
    "away and is much taller: a ground floor plus EIGHT upper floors. Repaint it as a finished painted panel block "
    "but keep its scale exactly: every red-orange band of the placeholder is the loggia parapet of one floor, so "
    "between its roof line and the roof of the medical centre there must be EIGHT rows of loggias, one painted "
    "floor exactly where each placeholder floor is - the floors are small because the block is far away; do NOT "
    "make the floors bigger and do not reduce their number. Keep its outline, roof line and perspective exactly; "
    "it continues to the right edge of the picture (no end wall). Beige-cream concrete wall panels, every floor a "
    "row of recessed loggias with red-orange parapet panels, windows with white frames, a narrow attic band and a "
    "thin dark roof edge; its lowest floors are hidden behind the medical centre's roof. Image 3 is a photo of the "
    "real street: the same 8-storey slab with red-orange loggia panels stands behind the low medical centre. "
)
CORE_DERIVED = (
    "(1) The long low bluish medical centre now stands LOWER than the street, below the road level: only its flat "
    "roof edge, its upper row of white ribbon windows and a strip of its blue-grey mosaic-tile facade show above the "
    "crest of the verge; its lower floor is hidden below the verge. Keep the medical centre exactly at this new lower "
    "height and paint the verge crest in front of it as a low bank with a few low shrubs, like the street in image 3, "
    "where the same medical centre sits below the road; repaint the rough strip along the crest and the trees at the "
    "far left end of the medical centre so they look painted. (2) The tall 8-storey panel block behind it (ground "
    "floor + eight floors of loggias with red-orange parapets) is already finished: keep it exactly as it is - the "
    "same outline, size, number of floors, loggias and position; only its light may match the picture. "
)
KEEP = (
    "Keep the tall lamp posts, the overhead tram wires and their exact positions, the trees at the left end, the "
    "road, the railing, the parked cars and everything in the left two thirds of the picture exactly as in image 1; "
    "the sky stays the same. No people, no animals, no text, no signs, no logos, no satellite dishes, no graffiti. "
    "Image 2 is another background from the same game: keep the same painting technique, brushwork and light. "
)
ERA = {
    "S11": "June 1995: the panel block is in its original state (not insulated), clean light, crisp shadows. ",
    "S51": ("2020: the same buildings 25 years older - the panel block's beige panels a little weathered, the "
            "medical centre's facade as it is in image 1 (teal panels between the windows, blue-grey mosaic tiles); "
            "autumn birches and shrubs on the verge in yellow and orange. "),
    "S57": ("December 1982: the panel block and the medical centre are fairly new; a thin layer of old snow lies on "
            "the flat roofs, on the loggia parapet tops and on the verge; soft low winter light, pale sky. "),
}


def cmd_paint(args) -> None:
    room = args.room
    mock_path = MASTERS / f"_{room}_right_mock.png"
    if not mock_path.exists():
        sys.exit("run mock first")
    core = CORE if room == "S11" else CORE_DERIVED
    prompt = PROMPTS[room] + core + ERA[room] + KEEP + pr.style_sentence()
    images = [fal_api.image_data_uri(mock_path, fmt="PNG"),
              fal_api.image_data_uri(ROOT / "art/backgrounds/sokolikova-street.png", max_side=1376, fmt="JPEG"),
              fal_api.image_data_uri(ROOT / "art/source/owner_refs/imgur_gnv1VFF.jpg", max_side=1376, fmt="JPEG")]
    refs = [mock_path.relative_to(ROOT).as_posix(), "art/backgrounds/sokolikova-street.png",
            "art/source/owner_refs/imgur_gnv1VFF.jpg"]
    if args.ref:
        ref = MASTERS / f"{args.ref}.png"
        images.append(fal_api.image_data_uri(ref, max_side=1600, fmt="JPEG"))
        refs.append(ref.relative_to(ROOT).as_posix())
        prompt += (" Image 4 is the same place in another year, already finished: paint the medical centre and the "
                   "panel block with the same shapes, heights, number of floors and details as in image 4.")
    seed = args.seed if args.seed is not None else random.randint(1, 2**31 - 1)
    tag = f"{room}_right_s{seed}"
    arguments = {"prompt": prompt, "image_urls": images, "aspect_ratio": pr.ASPECT, "resolution": pr.RESOLUTION,
                 "output_format": "png", "num_images": 1, "seed": seed}
    price = fal_api.IMAGE_PRICES[(pr.MODEL, pr.RESOLUTION)]
    result = fal_api.run(pr.MODEL, arguments, f"{SCOPE}{tag}", price, budget=(SCOPE, args.budget), timeout_s=900)
    raw = MASTERS / f"_{tag}_raw.png"
    fal_api.download(result["images"][0]["url"], raw)
    (raw.with_suffix(".json")).write_text(json.dumps({
        "room": room, "seed": seed, "usd": price, "scope": SCOPE, "prompt": prompt, "image_urls": refs,
        "model": pr.MODEL, "started": datetime.datetime.now().isoformat(timespec="seconds"),
        "model_description": result.get("description")}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(raw.relative_to(ROOT), f"spent {fal_api.logged_spend(SCOPE):.2f}")
    args.raw = str(raw.relative_to(ROOT))
    args.save = False
    cmd_compose(args)


# ---------------------------------------------------------------- composite

def align(result: np.ndarray, ref: np.ndarray, mask: np.ndarray, radius: int = 12) -> tuple[int, int]:
    lum = np.array([0.299, 0.587, 0.114], dtype=np.float32)
    a, b = result @ lum, ref @ lum
    s = 4
    a, b, m = a[::s, ::s], b[::s, ::s], mask[::s, ::s] > 0.99
    best = (1e18, 0, 0)
    for dy in range(-radius // s, radius // s + 1):
        for dx in range(-radius // s, radius // s + 1):
            sh = np.roll(np.roll(a, dy, 0), dx, 1)
            v = float(np.abs(sh - b)[m].mean())
            if v < best[0]:
                best = (v, dx, dy)
    return best[1] * s, best[2] * s


def compose(room: str, raw_path: Path):
    master, view = room_base(room)
    res = load_rgb(raw_path)
    M = edit_mask()
    outside = (M < 0.01).astype(np.float32)
    outside[: int(80 / K)] = 0          # the sky band at the very top is uniform: ignore it for the alignment
    dx, dy = align(res, view, outside)
    if dx or dy:
        res = np.roll(np.roll(res, dy, 0), dx, 1)
    Mx = M[..., None]
    new_view = view * (1 - Mx) + res * Mx
    if room == "S11":
        ta = s11_tram_alpha_master()[..., None]
        new_master = master + Mx * (1 - ta) * (res - master)
    else:
        new_master = new_view
    return np.clip(new_master, 0, 255), np.clip(new_view, 0, 255), (dx, dy)


def write_track_patch(new_view: np.ndarray, out_path: Path) -> None:
    patch, (px, py) = s11_track_patch()
    g = np.asarray(pr.fit_to_frame(Image.fromarray(new_view.astype(np.uint8))), dtype=np.uint8)
    pa = np.asarray(patch)
    h, w = pa.shape[:2]
    new = np.dstack([g[py:py + h, px:px + w], pa[..., 3]])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(new, "RGBA").save(out_path, "WEBP", lossless=True, quality=100, method=6)


def cmd_compose(args) -> None:
    room = args.room
    raw = ROOT / args.raw
    new_master, new_view, (dx, dy) = compose(room, raw)
    tag = raw.stem.replace("_raw", "").lstrip("_")
    cand = REVIEW / f"{tag}_master.png"
    cand.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(new_master.astype(np.uint8)).save(cand)
    if room == "S11":
        Image.fromarray(new_view.astype(np.uint8)).save(REVIEW / f"{tag}_empty.png")
    save_preview(new_master, REVIEW / f"{tag}_right.png")
    pr.fit_to_frame(Image.fromarray(new_master.astype(np.uint8))).save(REVIEW / f"{tag}_full.png")
    print(f"candidate {cand.relative_to(ROOT)} (drift compensated {dx:+d},{dy:+d} master px)")


def cmd_accept(args) -> None:
    """Write the final as the next master version + sidecar (then export with paint_natural.py export), and for S11
    the new track_empty patch (same alpha, the new background behind the T3)."""
    import re
    room = args.room
    raw = ROOT / args.raw if args.raw else None
    band = ROOT / args.band if args.band else None
    new_master, new_view, (dx, dy) = finalize(room, raw, band)
    versions = [int(m.group(1)) for q in MASTERS.glob(f"{room}_v*.png")
                if (m := re.fullmatch(rf"{room}_v(\d+)\.png", q.name))]
    version = max(versions, default=0) + 1
    out = MASTERS / f"{room}_v{version}.png"
    Image.fromarray(new_master.astype(np.uint8)).save(out)
    src = raw or band
    side = json.loads(src.with_suffix(".json").read_text(encoding="utf-8")) if src and src.with_suffix(".json").exists() else {}
    meta = {
        "room": room, "version": version, "kind": "fix", "from_version": BASE_VERSION[room],
        "tool": "art/prompts/natural/L_STOP.right_tweak.py",
        "note": args.note or ("owner 2026-10-06: the medical centre lower (below the road, only its roof edge and upper "
                              "windows show above the verge), the panel block behind it an 8-storey panelak"),
        "edit_region_game_px": f"x >= {X0}, y < crest(x) + 14 (crest 432 at x 1262 -> 478 at x 1920), 12 px seam",
        "medical_centre": f"column shift C_LOWER {C_LOWER} x painted height (roof {ROOF}, foot {FOOT})",
        "slab": {"texture": TEX["raw"], "tex_params": {k: v for k, v in TEX.items() if k != "raw"}, "target": TARGET,
                 "graded_to_room": room != "S11", "snow": room == "S57"},
        "mock": f"art/masters/bg_natural/_{room}_right_mock.png",
        "model_output": src.relative_to(ROOT).as_posix() if src else None,
        "model_output_use": ("everything in the edit region except the slab (replaced) and the far-end trees "
                             "(mirrored)") if raw else "only the verge strip crest-36..crest+12 (BAND_CROP crop edit)",
        "drift_compensated_master_px": [dx, dy], "model": pr.MODEL, "seed": side.get("seed"),
        "usd": side.get("usd", 0.0), "scope": SCOPE, "prompt": side.get("prompt"),
        "image_urls": side.get("image_urls"), "output_size": [MW, MH],
        "started": datetime.datetime.now().isoformat(timespec="seconds")}
    if room == "S11":
        meta["tram"] = "the painted T3 kept pixel-exact (alpha of tram_t3_body.webp); the edit painted what is behind it"
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out.relative_to(ROOT))
    if room == "S11":
        Image.fromarray(new_view.astype(np.uint8)).save(MASTERS / f"_S11_v{version}_empty.png")
        write_track_patch(new_view, ROOT / "src/game/assets/ambient/S11/natural/track_empty.webp")
        print("src/game/assets/ambient/S11/natural/track_empty.webp rewritten (same alpha, new background)")


# ---------------------------------------------------------------- the slab, re-projected from a painted facade
#
# nano-banana-pro repaints the placeholder slab well but always with ~1.6x bigger floors (5-6 visible floors instead
# of 8; S11 attempts s110601 and s110602). So the painted facade of the first attempt is used as a TEXTURE: in the
# coordinates w = 1/(x - VPX), m = (y - VPY)/(x - VPX) a receding facade is an orthographic, axis-aligned image of the
# wall (w affine in the distance along the facade, m affine in the height), so its floors and loggia modules are
# equally spaced there. The texture's floors and modules were measured once (TEX), and the target slab - roof line
# through (1288, 190), ground floor + 8 floors + attic, every element 0.622x the texture's size - samples one clean
# module (a loggia stack + a wall bay with a window, no lamp post or wire in front of it) periodically.

TEX = {
    "raw": "art/masters/bg_natural/_S11_right_s110601_raw.png",
    "vp": (812.0, 408.0),                    # where the painted facade lines converge (game px)
    "m_slab0": -0.4411,                       # floor slab line above the first loggia row
    "dm": 0.06428,                            # floor period in m
    "par_top": 0.06428 - 0.0240,              # parapet top inside a floor cell (from its ceiling)
    "floors": (2, 3),                         # clean source floors (floors 0-1 have the span wire in front)
    "module_w": (0.0018450, 0.0018450 - 0.0002476),   # module A: x 1354 (loggia left edge) .. x 1438 (next loggia)
    "attic_m": (-0.4525, -0.4411),            # dark roof edge + attic band down to the top floor's ceiling
    "attic_w": (1 / 858.0, 1 / 748.0),        # sampled between lamp posts B and C (x 1560-1670)
}
TARGET = {"m_top": (190.0 - 408.0) / (1288.0 - 812.0), "scale": 0.622, "x_far": 1288.0, "lead": 0.75}


def _bilinear(img: np.ndarray, mx: np.ndarray, my: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    mx = np.clip(mx, 0, w - 1.001)
    my = np.clip(my, 0, h - 1.001)
    x0, y0 = np.floor(mx).astype(int), np.floor(my).astype(int)
    fx, fy = (mx - x0)[..., None], (my - y0)[..., None]
    a = img[y0, x0] * (1 - fx) + img[y0, x0 + 1] * fx
    b = img[y0 + 1, x0] * (1 - fx) + img[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def slab_from_texture(bottom_g, grade=None, snow: bool = False, ss: int = 2):
    """RGB + alpha (master px) of the 8-storey slab between its roof line and bottom_g(x) (game y of the medical
    centre's roof per game x)."""
    tex = load_rgb(ROOT / TEX["raw"])
    tex = np.asarray(Image.fromarray(tex.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.45)), dtype=np.float32)
    vx, vy = TEX["vp"]
    sc = TARGET["scale"]
    dm_s = TEX["dm"]
    dm_t = dm_s * sc
    a_s = TEX["attic_m"][1] - TEX["attic_m"][0]
    a_t = a_s * sc
    m_top = TARGET["m_top"]
    w_far = 1.0 / (TARGET["x_far"] - vx)
    mw0, mw1 = TEX["module_w"]
    dw_s = mw0 - mw1
    dw_t = dw_s * sc
    mx0 = int(g2m_x(TARGET["x_far"])) - 1
    my1 = int(400 / K)
    h, wdt = my1, MW - mx0
    yy, xx = np.mgrid[0:h * ss, 0:wdt * ss]
    gx = (mx0 + (xx + 0.5) / ss) * K - CROP
    gy = ((yy + 0.5) / ss) * K
    w = 1.0 / np.maximum(gx - vx, 1e-3)
    m = (gy - vy) / np.maximum(gx - vx, 1e-3)
    inside = (gx >= TARGET["x_far"]) & (m >= m_top) & (gy <= bottom_g(gx))
    # vertical: attic, then the floors (top floor first), then the ground floor
    d = m - m_top
    attic = d < a_t
    j = np.floor((d - a_t) / dm_t)
    fm = (d - a_t) / dm_t - j
    floors = np.array(TEX["floors"])
    k = floors[np.mod(np.maximum(j, 0).astype(int), len(floors))]
    m_s = TEX["m_slab0"] + (k + fm) * dm_s
    # horizontal: module A repeated, starting a quarter module before the far end (a wall strip at the end)
    u = (w_far + TARGET["lead"] * dw_t - w) / dw_t
    fw = u - np.floor(u)
    w_s = mw0 - fw * dw_s
    # attic: a uniform band, sampled anywhere between the lamp posts
    aw0, aw1 = TEX["attic_w"]
    w_att = aw0 + np.mod((w_far - w) / sc, aw1 - aw0)
    m_att = TEX["attic_m"][0] + d / sc
    w_s = np.where(attic, w_att, w_s)
    m_s = np.where(attic, m_att, m_s)
    xs_ = vx + 1.0 / w_s
    ys_ = vy + m_s * (xs_ - vx)
    col = _bilinear(tex, (xs_ + CROP) / K, ys_ / K)
    ground = (~attic) & (j >= 8)
    col = np.where(ground[..., None], col * 0.86, col)
    # a little variation between the loggia stacks (painted panels are never identical)
    mod_i = np.floor(u).astype(int)
    jit = 1.0 + 0.025 * np.sin(mod_i * 2.39 + 0.7) + 0.012 * np.sin(np.maximum(j, 0) * 1.7)
    col = col * jit[..., None]
    if snow:
        # thin old snow on the loggia parapet tops and on the roof edge
        on_par = (~attic) & (np.abs(fm - TEX["par_top"] / dm_s) < 0.035)
        cap = on_par & (col[..., 0] > col[..., 2] + 25)
        col = np.where(cap[..., None], col * 0.25 + np.array([238, 240, 244]) * 0.75, col)
        roof = attic & (d < a_t * 0.35)
        col = np.where(roof[..., None], col * 0.3 + np.array([236, 238, 242]) * 0.7, col)
    if grade is not None:
        col = grade(col)
    alpha = inside.astype(np.float32)
    rgba = np.concatenate([col * alpha[..., None], alpha[..., None]], -1)
    rgba = rgba.reshape(h, ss, wdt, ss, 4).mean((1, 3))
    al = rgba[..., 3]
    rgb = rgba[..., :3] / np.maximum(al[..., None], 1e-4)
    out_rgb = np.zeros((MH, MW, 3), dtype=np.float32)
    out_a = np.zeros((MH, MW), dtype=np.float32)
    out_rgb[:h, mx0:] = rgb
    out_a[:h, mx0:] = al
    return out_rgb, out_a


def new_roof(gx):
    return pl(gx, ROOF) + drop(gx)


def post_mask_from(img: np.ndarray) -> np.ndarray:
    """Lamp posts (their rectangles), the lamp heads and the wires as painted in `img` (master px, soft)."""
    th = tophat(img, 9)
    pim = Image.new("L", (MW, MH), 0)
    pd = ImageDraw.Draw(pim)
    for x0, y0, x1, y1 in POSTS:
        yb = float(crest(x1)) + 20 if y1 is None else y1
        pd.rectangle([g2m_x(x0), y0 / K, g2m_x(x1), yb / K], fill=255)
    hm = Image.new("L", (MW, MH), 0)
    hd = ImageDraw.Draw(hm)
    for x0, y0, x1, y1 in POST_HEADS:
        hd.rectangle([g2m_x(x0), y0 / K, g2m_x(x1), y1 / K], fill=255)
    wim = Image.new("L", (MW, MH), 0)
    wd = ImageDraw.Draw(wim)
    for (ax, ay), (bx, by), wv in WIRES:
        wd.line([(g2m_x(ax), ay / K), (g2m_x(bx), by / K)], fill=255, width=int(round(2 * wv / K)))
    m = post_pixels(img)
    m |= (np.asarray(hm) > 0) & (th > 8) & head_ok(img)
    m |= (np.asarray(wim) > 0) & (th > 10)
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)),
                      dtype=np.float32) / 255


def make_grade(src: dict, dst: dict):
    """Per-channel affine colour map sending the texture's wall and parapet colours to the room's."""
    a = np.stack([src["wall"], src["red"]])
    b = np.stack([dst["wall"], dst["red"]])
    den = a[0] - a[1]
    gain = np.clip((b[0] - b[1]) / np.where(np.abs(den) < 1, 1, den), 0.6, 1.5)
    off = b[0] - gain * a[0]
    return lambda c: np.clip(c * gain + off, 0, 255)


def facade_samples(img: np.ndarray, x0: float, x1: float, y_top, y_bot) -> dict:
    gx, gy = grids()
    region = (gx > x0) & (gx < x1) & (gy > y_top(gx)) & (gy < y_bot(gx)) & (tophat(img) < 12)
    for a, _, b, _ in POSTS:
        region &= ~((gx > a - 4) & (gx < b + 4))
    px = img[region] / 255
    mx, mn = px.max(1), px.min(1)
    sat = (mx - mn) / np.maximum(mx, 1e-3)
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    red = (r > g + 0.12) & (r > b + 0.15) & (sat > 0.3)
    wall = (sat < 0.3) & (mx > 0.6)
    return {"red": np.median(px[red], 0) * 255, "wall": np.median(px[wall], 0) * 255}


def room_grade(view: np.ndarray):
    """Colour map from the S11 texture's facade to this room's own (old) slab: same building, the room's light."""
    src = facade_samples(load_rgb(ROOT / TEX["raw"]), 1340, 1780,
                         lambda x: np.interp(x, [1300, 1726], [185, 0]) + 8, lambda x: new_roof(x) - 6)
    dst = facade_samples(view, 1340, 1920, lambda x: np.interp(x, [1300, 1860, 1920], [175, 0, 0]) + 6,
                         lambda x: pl(x, ROOF) - 6)
    return make_grade(src, dst)


# ---------------------------------------------------------------- derived rooms: only the verge strip from the model
#
# S51 s205101 and S57 s198201 (full-frame edits of the mock) rebuilt the medical centre (a footbridge in S51, a grey
# wall in S57), so in the derived rooms everything is deterministic (the room's own medical centre lowered, the
# re-projected slab, mirrored trees) and the model only repaints the placeholder shrubs along the verge crest, on a
# 16:9 crop of the mock (x 1152-1920, y 152-584) so it works at 3.6x the game resolution.

BAND_CROP = (1152, 152, 1920, 584)
BAND_PROMPT = {
    "S51": ("late October 2020, a sunny autumn afternoon: the low shrubs are autumn-coloured (yellow, ochre and "
            "orange leaves, like the two bushes at the right edge), the grass of the verge yellow-green with fallen leaves"),
    "S57": ("December 1982, thin old snow: the low shrubs are bare or evergreen and covered with snow like the two "
            "bushes at the right edge, the verge is under a thin layer of snow"),
}


def band_mask(feather: float = 6.0) -> np.ndarray:
    gx, gy = grids()
    cr = crest(gx)
    top, bot = cr - 36, cr + 12
    m = np.clip(np.minimum(gy - top, bot - gy) / feather, 0, 1) * np.clip((gx - X0) / feather, 0, 1)
    return m.astype(np.float32)


def cmd_band(args) -> None:
    room = args.room
    mock = Image.open(MASTERS / f"_{room}_right_mock.png").convert("RGB")
    x0, y0, x1, y1 = BAND_CROP
    box = (round(g2m_x(x0)), round(y0 / K), round(g2m_x(x1)), round(y1 / K))
    crop = mock.crop(box)
    crop_path = REVIEW / f"{room}_band_input.png"
    crop.resize((2048, 1152), Image.Resampling.LANCZOS).save(crop_path)
    prompt = ("Image 1 is a crop of one of our finished point-and-click adventure game backgrounds: a long low bluish "
              "medical centre whose upper floor shows above the grass verge of a street, a tall panel block behind it, "
              "lamp posts, a road with a railing in front. Along the crest of the verge, right in front of the "
              "medical centre's ribbon windows, there is a row of flat placeholder blobs: repaint ONLY them as a few "
              "low painted shrubs and the edge of the verge, " + BAND_PROMPT[room] + ". The shrubs stay as low as the "
              "blobs (they hide only the bottom of the windows) and at the same places. Keep everything else exactly "
              "as it is, pixel for pixel: the medical centre, its windows and tiles, the panel block, the lamp posts, "
              "the road, the cars, the railing, the two bushes at the right edge and the sky. No people, no animals, "
              "no text, no logos. " + pr.style_sentence())
    images = [fal_api.image_data_uri(crop_path, fmt="PNG")]
    seed = args.seed if args.seed is not None else random.randint(1, 2**31 - 1)
    tag = f"{room}_band_s{seed}"
    arguments = {"prompt": prompt, "image_urls": images, "aspect_ratio": pr.ASPECT, "resolution": pr.RESOLUTION,
                 "output_format": "png", "num_images": 1, "seed": seed}
    price = fal_api.IMAGE_PRICES[(pr.MODEL, pr.RESOLUTION)]
    result = fal_api.run(pr.MODEL, arguments, f"{SCOPE}{tag}", price, budget=(SCOPE, args.budget), timeout_s=900)
    raw = MASTERS / f"_{tag}_raw.png"
    fal_api.download(result["images"][0]["url"], raw)
    raw.with_suffix(".json").write_text(json.dumps({
        "room": room, "seed": seed, "usd": price, "scope": SCOPE, "prompt": prompt, "kind": "band crop edit",
        "crop_game_px": list(BAND_CROP), "image_urls": [crop_path.relative_to(ROOT).as_posix()], "model": pr.MODEL,
        "started": datetime.datetime.now().isoformat(timespec="seconds"),
        "model_description": result.get("description")}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(raw.relative_to(ROOT), f"spent {fal_api.logged_spend(SCOPE):.2f}")


def derived_base(room: str, band_raw: Path | None) -> np.ndarray:
    """The room's mock with the model's verge strip pasted in (master px)."""
    mock = load_rgb(MASTERS / f"_{room}_right_mock.png")
    if band_raw is None:
        return mock
    x0, y0, x1, y1 = BAND_CROP
    box = (round(g2m_x(x0)), round(y0 / K), round(g2m_x(x1)), round(y1 / K))
    band = Image.open(band_raw).convert("RGB").resize((box[2] - box[0], box[3] - box[1]), Image.Resampling.LANCZOS)
    full = mock.copy()
    full[box[1]:box[3], box[0]:box[2]] = np.asarray(band, dtype=np.float32)
    bm = band_mask()
    gx, gy = grids()
    view = room_base(room)[1]
    bm *= ~bush_mask(room, view, crest(gx))
    bm = bm[..., None]
    return mock * (1 - bm) + full * bm


def finalize(room: str, raw_path: Path | None, band_raw: Path | None = None):
    """Model output in the edit region, the slab replaced by the re-projected 8-storey facade, the sky above its
    roof line from the painting itself, lamp posts / wires as painted, the T3 of S11 kept pixel-exact."""
    HEAD_ROOM["room"] = room
    master, view = room_base(room)
    M = edit_mask()
    if raw_path is not None:
        res = load_rgb(raw_path)
        outside = (M < 0.01).astype(np.float32)
        outside[: int(80 / K)] = 0
        dx, dy = align(res, view, outside)
        if dx or dy:
            res = np.roll(np.roll(res, dy, 0), dx, 1)
    else:
        res, dx, dy = derived_base(room, band_raw), 0, 0
    gx, gy = grids()
    grade = None
    if room != "S11":
        grade = room_grade(view)
    srgb, sa = slab_from_texture(lambda x: new_roof(x) + 1.0, grade=grade, snow=(room == "S57"))
    # the sky above the slab's roof line: the painting's own pixels where the old slab did not reach (geometric, the
    # winter sky of S57 is as pale as the walls), a sky row in the thin sliver where the old slab stood higher
    top_g = TEX["vp"][1] + TARGET["m_top"] * (gx - TEX["vp"][0])
    above = (gx >= TARGET["x_far"]) & (gy < top_g)
    from_view = above & ((gx < 1300) | (gy < old_top(gx) - 2))
    out = res.copy()
    out[from_view] = view[from_view]
    rest = above & ~from_view
    rows = sky_rows(view)
    gyi = np.clip(gy.astype(int), 0, 1079)
    out[rest] = rows[gyi[rest]]
    # the wire and the lamp head in that sky come from the painting too (they are at the same places)
    pv_m = protect_mask(view)[..., None] * above[..., None]
    out = out * (1 - pv_m) + view * pv_m
    # the trees in front of the slab's far end (x 1262-1290): the mock's placeholder crown became a flat hedge in the
    # model output, so continue the painting's own trees there (mirrored about the left edge of the edit region)
    tz = (gx >= X0) & (gx < TARGET["x_far"] + 4) & (gy > 196) & (gy < new_roof(gx) + 1)
    mx_src = np.clip(np.round(2 * g2m_x(X0) - np.arange(MW)).astype(int), 0, MW - 1)
    mirrored = view[:, mx_src]
    ta_blend = np.clip((gy - 196) / 8, 0, 1) * np.clip((TARGET["x_far"] + 4 - gx) / 6, 0, 1)
    tw = (tz * ta_blend)[..., None]
    out = out * (1 - tw) + mirrored * tw
    out = out * (1 - sa[..., None]) + srgb * sa[..., None]
    if room == "S51":
        # the span wire at y 185 (x 1150-1537, to lamp post B) crosses the new slab: one continuous line in the
        # wire's own colour (sampled where it crosses the sky left of the slab)
        lum = view @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        wsel = (gx > 1200) & (gx < 1250) & (np.abs(gy - 185) < 3) & (lum < 110)
        wcol = np.median(view[wsel], 0) if wsel.sum() > 5 else np.array([70, 72, 80])
        print("S51 span wire colour", wcol.round(1), int(wsel.sum()))
        wd = np.abs(gy - 185.0)
        wa = np.clip(1.0 - (wd - 0.45) / 0.7, 0, 1) * ((gx >= TARGET["x_far"]) & (gx <= 1537)) * (sa > 0.01)
        out = out * (1 - wa[..., None]) + wcol * wa[..., None]
    # lamp posts, heads and wires in front of the slab as the model painted them
    pm = post_mask_from(res)[..., None] * (sa[..., None] > 0.01)
    out = out * (1 - pm) + res * pm
    Mx = M[..., None]
    new_view = view * (1 - Mx) + out * Mx
    if room == "S11":
        ta = s11_tram_alpha_master()[..., None]
        new_master = master + Mx * (1 - ta) * (out - master)
    else:
        new_master = new_view
    return np.clip(new_master, 0, 255), np.clip(new_view, 0, 255), (dx, dy)


def cmd_final(args) -> None:
    raw = ROOT / args.raw if args.raw else None
    band = ROOT / args.band if args.band else None
    new_master, new_view, (dx, dy) = finalize(args.room, raw, band)
    src = raw or band
    tag = (src.stem.replace("_raw", "").lstrip("_") if src else f"{args.room}_mockonly") + "_final"
    cand = REVIEW / f"{tag}_master.png"
    cand.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(new_master.astype(np.uint8)).save(cand)
    if args.room == "S11":
        Image.fromarray(new_view.astype(np.uint8)).save(REVIEW / f"{tag}_empty.png")
    save_preview(new_master, REVIEW / f"{tag}_right.png")
    pr.fit_to_frame(Image.fromarray(new_master.astype(np.uint8))).save(REVIEW / f"{tag}_full.png")
    print(f"candidate {cand.relative_to(ROOT)} (drift {dx:+d},{dy:+d} master px)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("mock", "paint", "compose", "final", "accept", "band"):
        p = sub.add_parser(name)
        p.add_argument("room", choices=sorted(BASE_VERSION))
        if name in ("paint", "band"):
            p.add_argument("--seed", type=int)
            p.add_argument("--budget", type=float, default=2.5)
            p.add_argument("--ref") if name == "paint" else None
        if name == "compose":
            p.add_argument("--raw", required=True)
        if name in ("final", "accept"):
            p.add_argument("--raw")
            p.add_argument("--band")
        if name == "accept":
            p.add_argument("--note", default="")
    args = ap.parse_args()
    {"mock": cmd_mock, "paint": cmd_paint, "compose": cmd_compose, "final": cmd_final,
     "accept": cmd_accept, "band": cmd_band}[args.cmd](args)


if __name__ == "__main__":
    main()
