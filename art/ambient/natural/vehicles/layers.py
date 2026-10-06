"""Writes the vehicle layers into data/blocking/ambient/<room>.json (free, local).

The engine's tween_path layer has no hold and no easing, so a vehicle that stops, waits and leaves is built from
chains of short tween_path layers that all run on one fixed period (every_s = period - duration_s, speed_jitter 1,
fixed start_s). A layer's path is a 0.01 px stub at the vanishing point and its texture pivot is the vanishing point
too, so the only visible change is the scale: exact perspective for something moving along the track. Within a
chain every layer lasts the same frame-aligned quantum ((n + 0.5) / 60 s) and starts exactly one quantum after the
previous one, which never leaves a gap (at most one frame of overlap, at the same scale). Chains meet the painted
vehicle or the empty-track patch only under invisible stand layers (the sprite exactly over the painted vehicle).

  python art/ambient/natural/vehicles/layers.py S11 [--dry]
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
AMB = ROOT / "src" / "game" / "data" / "blocking" / "ambient"
FPS = 60.0


def q(frames: float) -> float:
    """Seconds from a frame count (use x.5 / x.25 / x.75 frames so no frame boundary is ever hit exactly)."""
    return round(frames / FPS, 6)


def stub(vp) -> list:
    return [[vp[0], vp[1]], [round(vp[0] + 0.01, 3), vp[1]]]


def chain(prefix: str, lods: list, pivot_full: list, vp, quantum_frames: float, start_frames: float,
          period_s: float, segments: list, base_scale: float, extra: dict | None = None) -> list:
    """segments: dicts with s0, s1 and optional alpha, plane. lods: [(texture, factor, max_s)] (factor = texture
    resolution relative to the full sprite; the first lod whose max_s >= max(s0, s1) is used)."""
    layers = []
    d = q(quantum_frames)
    for k, seg in enumerate(segments):
        s_hi = max(seg["s0"], seg["s1"])
        tex, factor = next((t, f) for t, f, m in lods if s_hi <= m)
        pv = seg.get("pivot_full", pivot_full)
        layer = {
            "id": f"{prefix}_{k:02d}",
            "type": "tween_path",
            "texture": tex,
            "pivot": [round(pv[0] * factor, 3), round(pv[1] * factor, 3)],
            "path": stub(seg.get("vp", vp)),
            "duration_s": d,
            "every_s": [round(period_s - d, 6)] * 2,
            "start_s": [q(start_frames + k * quantum_frames)] * 2,
            "speed_jitter": [1, 1],
            "scale": [round(seg["s0"] * base_scale / factor, 5), round(seg["s1"] * base_scale / factor, 5)],
        }
        if seg.get("alpha", 1) != 1:
            layer["alpha"] = seg["alpha"]
        if extra:
            layer.update(extra)
        if seg.get("plane") == "front":
            # close to the camera: the body is drawn above the hero, its cast shadow stays on the ground below him
            shadow = dict(layer, id=layer["id"] + "s", texture=tex.replace(".webp", "_shadow.webp"))
            layer["texture"] = tex.replace(".webp", "_body.webp")
            layer["plane"] = "front"
            layers.append(shadow)
        elif seg.get("plane"):
            layer["plane"] = seg["plane"]
        layers.append(layer)
    return layers


def dumps(data) -> str:
    """Indented JSON with short number / point arrays kept on one line (like the hand-written ambient files)."""
    import re
    text = json.dumps(data, indent=2, ensure_ascii=False)
    num = r"-?\d+(?:\.\d+)?(?:e-?\d+)?"
    flat = re.compile(r"\[\s*(" + num + r"(?:,\s*" + num + r")*)\s*\]")
    text = flat.sub(lambda m: "[" + ", ".join(x.strip() for x in m.group(1).split(",")) + "]", text)
    pts = re.compile(r"\[\s*(\[[^\[\]]*\](?:,\s*\[[^\[\]]*\])*)\s*\]")
    return pts.sub(lambda m: "[" + re.sub(r"\],\s*\[", "], [", m.group(1)) + "]", text)


def write(room: str, layers_new: list, prefixes: tuple, before: str | None, notes: str | None, dry: bool) -> None:
    """Replace the layers whose id starts with one of prefixes; '_slot': 'first' layers go to the top of the list,
    the others before the layer `before` (or at the end)."""
    path = AMB / f"{room}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    kept = [l for l in data["layers"] if not any(l.get("id", "").startswith(p) for p in prefixes)]
    head = [l for l in layers_new if l.get("_slot") == "first"]
    tail = [l for l in layers_new if l.get("_slot") != "first"]
    for l in layers_new:
        l.pop("_slot", None)
    out = head[:]
    inserted = False
    for l in kept:
        if before and l.get("id") == before and not inserted:
            out.extend(tail)
            inserted = True
        out.append(l)
    if not inserted:
        out.extend(tail)
    data["layers"] = out
    if notes:
        data["notes"] = notes
    text = dumps(data)
    if dry:
        print(text[:3000])
        return
    path.write_text(text + "\n", encoding="utf-8")
    print(f"{path.relative_to(ROOT)}: {len(out)} layers ({len(layers_new)} vehicle layers)")


# --------------------------------------------------------------------------------------------- S11

# 2026-10-06 (owner Dubravka corrections): the redesigned L_STOP camera. The flat near part of the track vanishes at
# the painted VP (888, 407); from ~22 m ahead the street and the tracks rise (slope up to 7 %) to a crest at y ~333.
# Track points: the pinhole model of the sketch (art/prompts/natural/S11.sketch.json; f 1250, eye 2.04 m, horizon 400,
# yaw 4 deg) plus the x offset measured on the painting (the empty-track edit S11_notram_v2_raw.png).
_F, _E, _TH = 1250.0, 2.04, math.radians(4.0)
_Z0, _L, _S = 22.0, 30.0, 0.07
_DX = [(10.5, 1.5), (20.0, 4.0), (40.0, 0.3), (60.0, 8.0), (80.0, 11.0), (120.0, 13.0), (200.0, 13.0), (300.0, 11.0)]


def _ground(z: float) -> float:
    if z <= _Z0:
        return 0.0
    if z <= _Z0 + _L:
        return _S * (z - _Z0) ** 2 / (2 * _L)
    return _S * (z - _Z0 - _L / 2)


def stop_zc(z: float, x: float = 3.27) -> float:
    return x * math.sin(_TH) + z * math.cos(_TH)


def stop_track(z: float, x: float = 3.27) -> tuple[float, float]:
    """Screen point of the near track's centre at rail level, z metres ahead (L_STOP camera, painted offsets)."""
    xc = x * math.cos(_TH) - z * math.sin(_TH)
    zc = stop_zc(z, x)
    y = -0.25 + _ground(z)
    dx = next((d0 + (d1 - d0) * (z - z0) / (z1 - z0) for (z0, d0), (z1, d1) in zip(_DX, _DX[1:]) if z0 <= z <= z1),
              _DX[0][1] if z < _DX[0][0] else _DX[-1][1])
    return 960 + _F * xc / zc + dx, 400 - _F * (y - _E) / zc


def follow_track(segments: list, z_of: dict, anchor_full: list, base: float) -> None:
    """Give every moving segment its own scaling point so the sprite's anchor (the rail-level centre of its front)
    lands on the painted, rising track at both ends: V = (T1 - r T0) / (1 - r), r = s1 / s0; pivot = anchor - (T0 - V)
    / (s0 base). Neighbouring segments meet at the same point and scale, so the motion stays continuous."""
    for seg in segments:
        s0, s1 = seg["s0"], seg["s1"]
        if abs(s1 - s0) < 1e-9:
            continue
        t0, t1 = stop_track(z_of[s0]), stop_track(z_of[s1])
        r = s1 / s0
        v = ((t1[0] - r * t0[0]) / (1 - r), (t1[1] - r * t0[1]) / (1 - r))
        seg["vp"] = (round(v[0], 3), round(v[1], 3))
        seg["pivot_full"] = [anchor_full[0] - (t0[0] - v[0]) / (s0 * base), anchor_full[1] - (t0[1] - v[1]) / (s0 * base)]


def s11(dry: bool) -> None:
    info = json.loads((HERE / "S11_build.json").read_text(encoding="utf-8"))
    t = info["tram_t3"]
    vp = tuple(t["vp_game"])
    pivot = t["pivot"]
    base = t["draw_scale_at_stop"]
    origin = t["origin_master"]
    lods = [("S11/natural/tram_t3_far.webp", 0.07, 0.115), ("S11/natural/tram_t3_small.webp", 0.16, 0.25),
            ("S11/natural/tram_t3_mid.webp", 0.4, 0.6), ("S11/natural/tram_t3.webp", 1.0, 99)]
    period = 80.0
    dep_q, arr_q = 30.5, 120.5            # 0.508 s and 2.008 s quanta
    t_pre = 840.25                        # first departure 14 s after entering the room
    # departure: from rest at 1.0 m/s2 towards the camera on the flat near track (exact: scale about the painted VP);
    # s = Zc(stand) / Zc (front of the tram 10.5 m ahead at the stop)
    dep_s = [1.0, 1.012, 1.05, 1.1199, 1.2353, 1.4237, 1.75, 2.4, 4.2, 10.0]
    dep = [{"s0": 1.0, "s1": 1.0}]       # invisible stand over the painted tram while the patch appears
    for a, b in zip(dep_s, dep_s[1:]):
        dep.append({"s0": a, "s1": b, "plane": "front" if a >= 2.4 else None})
    # arrival: 12 m/s from the crest of the street, then braking at 1.2 m/s2 into the stop (2 s steps); the track
    # rises beyond 22 m, so every segment follows the painted track (follow_track)
    arr_z = [142.5, 118.5, 94.5, 70.5, 48.9, 32.1, 20.1, 12.9, 10.5]
    z_stand = 10.5
    arr_s = [round(stop_zc(z_stand) / stop_zc(z), 5) for z in arr_z]
    z_of = dict(zip(arr_s, arr_z))
    arr = [{"s0": a, "s1": b} for a, b in zip(arr_s, arr_s[1:])]
    anchor_g = stop_track(z_stand)
    anchor_full = [(anchor_g[0] + 7) / base - origin[0], anchor_g[1] / base - origin[1]]
    follow_track(arr, z_of, anchor_full, base)
    arr[0]["alpha"] = 0.55               # out of the haze over the crest
    arr.append({"s0": 1.0, "s1": 1.0})   # invisible stand while the patch goes
    empty_frames = 480.0
    t_dep = t_pre + dep_q
    t_arr = t_dep + 9 * dep_q + empty_frames
    patch_frames = 9 * dep_q + empty_frames + 8 * arr_q
    tp = info["track_empty"]
    patch = {
        "_slot": "first", "id": "tram_patch", "type": "tween_path", "texture": "S11/natural/track_empty.webp",
        "pivot": [0, 0], "path": [[tp["pos"][0], tp["pos"][1]], [tp["pos"][0] + 0.01, tp["pos"][1]]],
        "duration_s": q(patch_frames), "every_s": [round(period - q(patch_frames), 6)] * 2,
        "start_s": [q(t_dep)] * 2, "speed_jitter": [1, 1],
    }
    layers = [patch]
    layers += chain("tram_dep", lods, pivot, vp, dep_q, t_pre, period, dep, base)
    layers += chain("tram_arr", lods, pivot, vp, arr_q, t_arr, period, arr, base)
    notes = ("Svantnerova tram stop, June 1995 morning (natural painting bg_natural/S11.webp, redesigned 2026-10-06): wind "
             "in the lindens and birches, clouds drifting behind the panel towers, the stop clock's red second hand ticking "
             "(the time node), pigeons pecking on the concrete track panels (they fly off when Adam comes close), now and "
             "then a small flock crossing the sky. The red-cream T3 (the exit to S19) is a sprite cut from the painting "
             "(art/ambient/natural/vehicles/build_s11.py): every 80 s it leaves towards the camera (accelerating), the "
             "track stays empty for 8 s and the next T3 comes over the crest of the rising street and brakes into the stop "
             "(16 s, following the painted track uphill: layers.py follow_track); tram_patch (the tramless track from one "
             "paid edit) covers the painted tram meanwhile. Reduced motion hides all tram layers, so the painted tram stands "
             "still.")
    write("S11", layers, ("tram_",), before="birds_sky", notes=notes, dry=dry)


def sequence(prefix: str, lods: list, vp, pivot_full: list, base: float, start_frames: float, period_s: float,
             segments: list) -> list:
    """Like chain(), but every segment has its own length ("frames", n + 0.5); each layer starts exactly where the
    previous one ends, so the chain never leaves a gap (all layers share the period)."""
    layers, t = [], start_frames
    for k, seg in enumerate(segments):
        for layer in chain(prefix, lods, pivot_full, vp, seg["frames"], t, period_s, [seg], base):
            layer["id"] = layer["id"].replace(f"{prefix}_00", f"{prefix}_{k:02d}", 1)
            layers.append(layer)
        t += seg["frames"]
    return layers


def far_split(segments: list, vp, pivot, base: float, far_vp, s_j: float) -> None:
    """Below the junction scale s_j the sprite scales about far_vp (the painted track bends a little near the
    horizon); the pivot is shifted so both mappings agree at s_j."""
    far_pivot = [pivot[0] + (far_vp[0] - vp[0]) / (s_j * base), pivot[1] + (far_vp[1] - vp[1]) / (s_j * base)]
    for seg in segments:
        if max(seg["s0"], seg["s1"]) <= s_j + 1e-6:
            seg["vp"], seg["pivot_full"] = far_vp, far_pivot


# --------------------------------------------------------------------------------------------- S51

def s51(dry: bool) -> None:
    t = json.loads((HERE / "S51_build.json").read_text(encoding="utf-8"))["tram_2020"]
    vp, pivot, base, origin = tuple(t["vp_game"]), t["pivot"], t["draw_scale_at_stop"], t["origin_master"]
    lods = [("S51/natural/tram_2020_far.webp", 0.07, 0.115), ("S51/natural/tram_2020_small.webp", 0.16, 0.25),
            ("S51/natural/tram_2020_mid.webp", 0.4, 0.6), ("S51/natural/tram_2020.webp", 1.0, 99)]
    # 2026-10-06 redesigned L_STOP camera (see s11): the painted tram's front stands ~9.2 m ahead (rail level y ~704).
    # Arrival: 12 m/s over the crest of the rising street, braking at 1.2 m/s2 (2 s steps), following the painted track
    # (follow_track); 10 s at the stop; departure from rest at 1.0 m/s2 towards the camera (0.5 s steps, flat track:
    # scaled about the painted VP).
    z_stand = 9.2
    arr_z = [141.2, 117.2, 93.2, 69.2, 47.6, 30.8, 18.8, 11.6, 9.2]
    arr_s = [round(stop_zc(z_stand) / stop_zc(z), 5) for z in arr_z]
    z_of = dict(zip(arr_s, arr_z))
    dep_s = [1.0, 1.0133, 1.0556, 1.1343, 1.2667, 1.4902, 1.9, 2.8148, 6.333, 12.0]
    segs = [{"s0": a, "s1": b, "frames": 120.5} for a, b in zip(arr_s, arr_s[1:])]
    anchor_g = stop_track(z_stand)
    follow_track(segs, z_of, [(anchor_g[0] + 7) / base - origin[0], anchor_g[1] / base - origin[1]], base)
    segs[0]["alpha"] = 0.55
    segs.append({"s0": 1.0, "s1": 1.0, "frames": 600.5})
    segs += [{"s0": a, "s1": b, "frames": 30.5, "plane": "front" if a >= 1.9 else None}
             for a, b in zip(dep_s, dep_s[1:])]
    layers = sequence("tram2020", lods, vp, pivot, base, 360.25, 90.0, segs)
    notes = ("Svantnerova tram stop, 29 October 2020 afternoon (bg_natural/S51.webp, redesigned 2026-10-06): wind in the "
             "autumn trees, leaves falling onto the lawn and the road and drifting onto the platform, clouds, the clock's "
             "second hand (old brass frame), the orange dots of the LED board shimmering, pigeons on the platform. Every "
             "90 s (first 6 s after entering) an unbranded modern low-floor tram comes over the crest of the rising "
             "street, brakes into the stop, waits 10 s and pulls out towards the camera (tram2020_*: one sprite from a "
             "paid edit, cut by art/ambient/natural/vehicles/build_s51.py, chain written by layers.py; hidden with "
             "reduced motion).")
    write("S51", layers, ("tram2020_",), before=None, notes=notes, dry=dry)


ROOMS = {"S11": s11, "S51": s51}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("room", choices=sorted(ROOMS))
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    ROOMS[args.room](args.dry)


if __name__ == "__main__":
    main()
