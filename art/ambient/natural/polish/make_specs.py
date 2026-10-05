"""Living-scene polish 2026-10-05: per-room ambient additions as spec files for add_layers.py (free, local).

  python art/ambient/natural/polish/make_specs.py      writes art/ambient/natural/polish/<room>.json
  python art/ambient/natural/vehicles/add_layers.py art/ambient/natural/polish/<room>.json
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

# a house fly buzzing around a sunny window (summer interiors)
FLY = {"type": "tween_path", "texture": "builtin:dot", "modulate": "#1d1a17", "scale": 0.3, "speed_px_s": 150,
       "speed_jitter": [0.8, 1.2], "bob_px": 5, "bob_hz": 5.5, "direction": "random", "reduced_motion": "hide"}


def fly(after: str, path: list, every=(4, 9), start=(0.5, 2)) -> dict:
    return {"_after": after, "id": "window_fly", **FLY, "path": path, "every_s": list(every), "start_s": list(start)}


def sun(after_or_before: tuple, rect: list, max_: float, period: float, id_: str = "floor_sun") -> dict:
    key, ref = after_or_before
    return {key: ref, "id": id_, "type": "flicker", "mode": "pulse", "rect": rect, "texture": "builtin:softrect",
            "color": "#fff0c8", "min": 0.0, "max": max_, "period_s": period}


SPECS = {
    "S13": [sun(("_after", "dust_sunbeams"), [200, 660, 1140, 240], 0.09, 7.5)],
    "S16": [sun(("_after", "dust_window"), [950, 880, 420, 100], 0.12, 7.0),
            fly("floor_sun", [[1080, 420], [1180, 360], [1260, 440], [1170, 500], [1300, 540], [1220, 390], [1340, 330]],
                (3, 8))],
    "S20": [{"_after": "scope_trace", "id": "scope_sweep", "type": "flicker", "mode": "sweep", "rect": [1306, 508, 60, 50],
             "texture": "builtin:glow", "color": "#a8ffcc", "blend": "add", "min": 0.0, "max": 0.55, "period_s": 0.9,
             "duty": 1.0},
            {"_after": "scope_sweep", "id": "radio_dial", "type": "flicker", "mode": "noise", "pos": [836, 528],
             "size": [120, 34], "texture": "builtin:glow", "color": "#ffcf80", "blend": "add", "min": 0.12, "max": 0.32,
             "period_s": 0.6}],
    "S22": [sun(("_before", "dust"), [340, 790, 980, 140], 0.1, 8.0),
            {**sun(("_after", "floor_sun"), [540, 290, 430, 300], 0.07, 8.0, "window_beam"), "color": "#fff3d6"},
            fly("ceiling_lamp", [[580, 360], [700, 320], [820, 420], [720, 500], [880, 540], [930, 380], [640, 450]])],
    "S23": [{"_after": "pigeons_window", "id": "square_pigeons", "type": "critters", "sheet": "common/pigeon_sheet",
             "count": 3, "ground": [[660, 566], [960, 578]], "scale": 0.05, "flee_radius": 0, "return_s": [10, 20],
             "exit": [[1100, 300], [500, 280]], "clip": [556, 258, 448, 326]},
            {**sun(("_after", "desk_lamps"), [550, 250, 460, 340], 0.08, 9.0, "window_light"), "color": "#fff6dc"}],
    "S26": [sun(("_before", "dust"), [380, 800, 640, 150], 0.1, 7.5),
            fly("passage_passers_window", [[560, 350], [650, 420], [730, 360], [700, 480], [600, 520], [760, 560]],
                (4, 10))],
    "S27": [{"_after": "vu_meters", "id": "woofer_top", "type": "water", "texture": "S27/natural/woofer_top.webp",
             "amp_px": 0.55, "speed": 5.5, "glint": 0.0},
            {"_after": "woofer_top", "id": "woofer_bottom", "type": "water", "texture": "S27/natural/woofer_bottom.webp",
             "amp_px": 0.7, "speed": 5.0, "glint": 0.0},
            {"_after": "woofer_bottom", "id": "woofer_small", "type": "water", "texture": "S27/natural/woofer_small.webp",
             "amp_px": 0.5, "speed": 6.0, "glint": 0.0}],
    "S33": [{"_after": "window_trees", "id": "pigeon_past", "type": "tween_path", "sheet": "common/pigeon_sheet",
             "frames": "fly", "fps": 11, "path": [[430, 420], [560, 380], [670, 400]], "speed_px_s": 200, "scale": 0.09,
             "flock": 2, "flock_spread": [40, 16], "bob_px": 3, "direction": "random", "every_s": [7, 15],
             "start_s": [1, 3], "clip": [455, 330, 186, 256]},
            fly("pigeon_past", [[470, 360], [560, 430], [620, 350], [600, 520], [500, 480], [640, 560]], (5, 11),
                (2, 4))],
    "S40": [{"_after": "window_light", "id": "swallows", "type": "tween_path", "sheet": "common/pigeon_sheet",
             "frames": "fly", "fps": 14, "path": [[890, 372], [960, 352], [1040, 362]], "speed_px_s": 260,
             "scale": 0.045, "modulate": "#26242a", "flock": 2, "flock_spread": [30, 10], "bob_px": 2,
             "direction": "random", "every_s": [4, 9], "start_s": [0.5, 2], "clip": [918, 338, 90, 46]},
            {"_after": "dust_beam", "id": "dust_beam_bright", "type": "particles", "preset": "dust",
             "emit_rect": [560, 120, 360, 560], "count": 26, "size": [4, 8], "alpha_range": [0.5, 0.95],
             "color": "#fff3d0"}],
    "S43": [{"_after": "desk_lamp", "id": "radio_dial", "type": "flicker", "mode": "noise", "pos": [1142, 588],
             "size": [60, 26], "texture": "builtin:glow", "color": "#ffcf80", "blend": "add", "min": 0.1, "max": 0.35,
             "period_s": 0.7},
            {"_after": "radio_dial", "id": "choughs_window", "type": "tween_path", "sheet": "common/pigeon_sheet",
             "frames": "fly", "fps": 10, "path": [[1750, 300], [1820, 270], [1890, 290]], "speed_px_s": 120,
             "scale": 0.05, "modulate": "#2f2f36", "flock": 2, "flock_spread": [25, 12], "bob_px": 3,
             "direction": "random", "every_s": [6, 14], "start_s": [1, 3], "clip": [1772, 205, 96, 160]}],
    # (a tape flutter on the barrier tape was tried and dropped: the water shader saw-tooths a thin horizontal strip)
    "S53": [sun(("_after", "dust_sunbeams"), [300, 700, 860, 240], 0.11, 7.0)],   # + leaves_outside rate 0.35 -> 0.8
    "S59": [{"_first": True, "id": "wet_terrazzo", "type": "water", "texture": "S59/natural/wet_terrazzo.webp",
             "amp_px": 0.3, "speed": 0.7, "glint": 0.55, "glint_color": "#f4f8ff"}],
    "S65": [{"_after": "snow_window", "id": "heat_shimmer", "type": "water", "texture": "S65/natural/window_low.webp",
             "amp_px": 0.5, "speed": 1.6, "glint": 0.0}],
}


def main() -> None:
    for room, layers in SPECS.items():
        (HERE / f"{room}.json").write_text(json.dumps({"room": room, "layers": layers}, indent=1) + "\n",
                                           encoding="utf-8")
    print(", ".join(SPECS))


if __name__ == "__main__":
    main()
