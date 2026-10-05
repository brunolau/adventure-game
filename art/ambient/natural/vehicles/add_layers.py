"""Small helper for the living-scene polish (2026-10-05): insert / replace ambient layers in
src/game/data/blocking/ambient/<room>.json by id, keep the file's formatting style.

  python art/ambient/natural/vehicles/add_layers.py <spec.json>
spec = {"room": "S03", "notes": "...", "layers": [ {..layer.., "_after": "id" | "_before": "id" | "_first": true} ]}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import layers as L  # noqa: E402


def apply(spec: dict) -> None:
    path = L.AMB / f"{spec['room']}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    out = [l for l in data["layers"] if l.get("id") not in {n["id"] for n in spec["layers"]}]
    for new in spec["layers"]:
        new = dict(new)
        after, before, first = new.pop("_after", None), new.pop("_before", None), new.pop("_first", False)
        ids = [l.get("id") for l in out]
        if first:
            out.insert(0, new)
        elif after in ids:
            out.insert(ids.index(after) + 1, new)
        elif before in ids:
            out.insert(ids.index(before), new)
        else:
            out.append(new)
    data["layers"] = out
    if spec.get("notes"):
        data["notes"] = spec["notes"]
    path.write_text(L.dumps(data) + "\n", encoding="utf-8")
    print(f"{spec['room']}: {len(out)} layers: {', '.join(l['id'] for l in out)}")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        spec = json.loads(Path(arg).read_text(encoding="utf-8"))
        for s in spec if isinstance(spec, list) else [spec]:
            apply(s)
