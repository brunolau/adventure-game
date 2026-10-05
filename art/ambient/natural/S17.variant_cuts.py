"""Ambient cut-outs from a natural VARIANT state (painter "dubravka-yard", rooms S17 S55 S61; free).

art/tools/ambient_cut.py --natural <room> cuts only from the base painting bg_natural/<room>.webp. A crown that exists
only after a state change (S17 healthy linden after E10, S55 big linden after E10) is drawn by a variant overlay, so its
wind-sway sprite has to be cut from the painting WITH that overlay. This script composites the overlay(s) over the
base painting and cuts the items of art/ambient/natural/<room>.variant_cuts.json with the same selection code as
ambient_cut.py (build_room_item). Outputs go to src/game/assets/ambient/<room>/natural/<name>.webp; the ambient file
must give the printed "pos" explicitly (these sprites are not in that folder's manifest.json, which ambient_cut.py
rewrites).

  PYTHONIOENCODING=utf-8 python -X utf8 art/ambient/natural/S17.variant_cuts.py S17|S55 [--preview]

Spec: {"room": "S17", "overlays": [{"texture": "variants_natural/S17_healthy_linden.webp", "pos": [250, 0]}],
       "items": [ ...same item format as ambient_cut.py... ]}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "art" / "tools"))
import ambient_cut  # noqa: E402


def main() -> None:
    room = sys.argv[1]
    preview = "--preview" in sys.argv
    spec = json.loads((ROOT / "art" / "ambient" / "natural" / f"{room}.variant_cuts.json").read_text(encoding="utf-8"))
    frame = Image.open(ROOT / "src" / "game" / "assets" / "bg_natural" / f"{room}.webp").convert("RGBA")
    for ov in spec.get("overlays", []):
        tex = Image.open(ROOT / "src" / "game" / "assets" / ov["texture"]).convert("RGBA")
        frame.alpha_composite(tex, tuple(ov.get("pos", [0, 0])))
    rgb = np.asarray(frame.convert("RGB"))
    for item in spec["items"]:
        info = ambient_cut.build_room_item(f"{room}/natural", item, rgb, preview)
        print(f"{room}/natural/{item['name']}.webp", json.dumps(info))


if __name__ == "__main__":
    main()
