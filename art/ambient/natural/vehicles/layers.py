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

def s11(dry: bool) -> None:
    info = json.loads((HERE / "S11_build.json").read_text(encoding="utf-8"))
    t = info["tram_t3"]
    vp = tuple(t["vp_game"])
    pivot = t["pivot"]
    base = t["draw_scale_at_stop"]
    lods = [("S11/natural/tram_t3_far.webp", 0.07, 0.115), ("S11/natural/tram_t3_small.webp", 0.16, 0.25),
            ("S11/natural/tram_t3_mid.webp", 0.4, 0.6), ("S11/natural/tram_t3.webp", 1.0, 99)]
    period = 80.0
    dep_q, arr_q = 30.5, 120.5            # 0.508 s and 2.008 s quanta
    t_pre = 840.25                        # first departure 14 s after entering the room
    # departure: from rest at 1.0 m/s2 towards the camera; s = 10.5 / Z (front of the tram 10.5 m ahead at the stop)
    dep_s = [1.0, 1.012, 1.05, 1.1199, 1.2353, 1.4237, 1.75, 2.4, 4.2, 10.0]
    dep = [{"s0": 1.0, "s1": 1.0}]       # invisible stand over the painted tram while the patch appears
    for a, b in zip(dep_s, dep_s[1:]):
        dep.append({"s0": a, "s1": b, "plane": "front" if a >= 2.4 else None})
    # arrival: 12 m/s from the far end, then braking at 1.2 m/s2 into the stop (2 s steps)
    arr_s = [0.0737, 0.0886, 0.1111, 0.1489, 0.2147, 0.3271, 0.5224, 0.814, 1.0]
    arr = [{"s0": a, "s1": b} for a, b in zip(arr_s, arr_s[1:])]
    # the painted track bends a little: far away the rails vanish at (1074, 401), not at the near VP. Below the
    # junction scale the tram scales about that far point, with the pivot shifted so both mappings meet there.
    far_vp, s_j = (1074.0, 401.0), 0.2147
    far_pivot = [pivot[0] + (far_vp[0] - vp[0]) / (s_j * base), pivot[1] + (far_vp[1] - vp[1]) / (s_j * base)]
    for seg in arr:
        if seg["s1"] <= s_j + 1e-6:
            seg["vp"], seg["pivot_full"] = far_vp, far_pivot
    arr[0]["alpha"] = 0.55               # out of the haze
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
    notes = ("Dubravka tram stop, June 1995 morning (natural painting bg_natural/S11.webp): wind in the lindens left and "
             "right, clouds drifting behind the panel towers, the stop clock's red second hand ticking (the time node), "
             "pigeons pecking on the platform near the tram (they fly off when Adam comes close), now and then a small "
             "flock crossing the sky. The red-cream T3 (the exit to S19) is a sprite cut from the painting "
             "(art/ambient/natural/vehicles/build_s11.py): every 80 s it leaves towards the camera (accelerating), the "
             "track stays empty for 8 s and the next T3 comes in from the far end and brakes into the stop (16 s); "
             "tram_patch (the tramless track from one paid edit) covers the painted tram meanwhile. The chains are "
             "written by art/ambient/natural/vehicles/layers.py. Reduced motion hides all tram layers, so the painted "
             "tram stands still.")
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
    vp, pivot, base = tuple(t["vp_game"]), t["pivot"], t["draw_scale_at_stop"]
    lods = [("S51/natural/tram_2020_far.webp", 0.07, 0.115), ("S51/natural/tram_2020_small.webp", 0.16, 0.25),
            ("S51/natural/tram_2020_mid.webp", 0.4, 0.6), ("S51/natural/tram_2020.webp", 1.0, 99)]
    # s = 9.5 / Z (the painted tram's front is ~9.5 m ahead). Arrival: 12 m/s, braking at 1.2 m/s2 (2 s steps);
    # 10 s at the stop; departure from rest at 1.0 m/s2 towards the camera (0.5 s steps).
    arr_s = [0.0671, 0.0809, 0.1016, 0.1367, 0.1983, 0.3055, 0.4974, 0.7983, 1.0]
    dep_s = [1.0, 1.0133, 1.0556, 1.1343, 1.2667, 1.4902, 1.9, 2.8148, 6.333, 12.0]
    segs = [{"s0": a, "s1": b, "frames": 120.5} for a, b in zip(arr_s, arr_s[1:])]
    segs[0]["alpha"] = 0.55
    far_split(segs, vp, pivot, base, (1074.0, 401.0), 0.3055)
    segs.append({"s0": 1.0, "s1": 1.0, "frames": 600.5})
    segs += [{"s0": a, "s1": b, "frames": 30.5, "plane": "front" if a >= 1.9 else None}
             for a, b in zip(dep_s, dep_s[1:])]
    layers = sequence("tram2020", lods, vp, pivot, base, 360.25, 90.0, segs)
    notes = ("Dubravka tram stop, 29 October 2020 afternoon (bg_natural/S51.webp): wind in the yellow lindens, leaves "
             "falling onto the lawn and the road and drifting onto the platform, clouds, the clock's second hand (old "
             "brass frame), the orange dots of the LED board shimmering, pigeons on the platform. Every 90 s (first 6 s "
             "after entering) an unbranded modern low-floor tram comes in from the far end, brakes into the stop, waits "
             "10 s and pulls out towards the camera (tram2020_*: one sprite from a paid edit, cut by "
             "art/ambient/natural/vehicles/build_s51.py, chain written by layers.py; hidden with reduced motion).")
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
