"""Install the natural blocking of the content v2 world overlay (S69 + the new targets in S17 S18 S32 S37 S38).

The world overlay draft (docs/writing/out/content_v2_draft.json -> src/game/data/content_ext/world_ext.json) adds
the room S69, the exit S18.to_S69, the 1962 props S37.hopscotch / S32.chalk_arrow / S38.paper_boat, the NPC
S37.ZUZANA and nine visual variant layers. tools/check_blocking.py refuses blocking entries for ids the effective
game does not know, so these entries are kept here (and S69's files in stage/) until the overlay is live.

  python install_content_v2.py check            what would change (no writes)
  python install_content_v2.py install          live data/blocking (refused unless world_ext.json has S69; --force)
  python install_content_v2.py remove           take the entries out again (S69 files deleted)
  python install_content_v2.py install --dir D  apply to another data/blocking folder (QA copies)

Every value was placed on the natural paintings (art/masters/bg_natural/S69.md "Blocking in other rooms").
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LIVE = ROOT / "src" / "game" / "data" / "blocking"
STAGE = HERE / "stage" / "data" / "blocking"
WORLD_EXT = ROOT / "src" / "game" / "data" / "content_ext" / "world_ext.json"

V = "variants_natural/"
SNIPPETS: dict[str, dict] = {
    "S18": {
        "exits": {
            "S18.to_S69": {"rect": [360, 800, 160, 66], "interaction_point": [440, 878], "label_anchor": [480, 760],
                           "reason": "content v2: the side road between the kiosk and the parked red car runs back into the gap between the blocks, towards the walled courtyard S69 (the way to the right of the school, not the podlubie)"},
        },
    },
    "S37": {
        "hotspots": {
            "S37.ZUZANA": {"rect": [204, 626, 118, 268], "interaction_point": [420, 905], "label_anchor": [263, 616],
                           "reason": "content v2: little Zuzana plays hopscotch on the park path left of Vera (feet 262, 892; 0.75 x 350 px = 263 px tall)"},
            "S37.hopscotch": {"rect": [150, 862, 600, 48], "interaction_point": [480, 925], "label_anchor": [520, 852],
                              "reason": "content v2: the chalk hopscotch along the park path (x 150-748, y 870-902, 2.6 x 0.7 m, half circle at the right end); layer variants_natural/S37_hopscotch.webp"},
        },
        "npcs": {
            "S37.ZUZANA": {"variant": "playing", "feet": [262, 892], "facing": "right", "z": "auto",
                           "reason": "ZUZANA.md 2: Zuzana plays hopscotch (actor variant 'playing') on the path left of Vera's bench, near her bell in the grass, away from the spawn and the bird bowl"},
        },
        "variant_layers": {
            "variants/S37_hopscotch.webp": {"texture": V + "S37_hopscotch.webp", "pos": [120, 846]},
            "variants/S37_zuzana_bell.webp": {"texture": V + "S37_zuzana_bell.webp", "pos": [282, 912]},
            "variants/S37_zuzana_bell_gone.webp": {"texture": V + "S37_zuzana_bell_gone.webp", "pos": [282, 912]},
            "variants/S37_zuzana_bell_back.webp": {"texture": V + "S37_zuzana_bell_back.webp", "pos": [282, 912]},
        },
    },
    "S32": {
        "hotspots": {
            "S32.chalk_arrow": {"rect": [206, 640, 140, 66], "interaction_point": [290, 760], "label_anchor": [300, 726],
                                "reason": "content v2: chalk arrow (pointing right, to the park exit) and PARK on the front of the well's stone ring"},
        },
        "variant_layers": {
            "variants/S32_chalk_arrow.webp": {"texture": V + "S32_chalk_arrow.webp", "pos": [206, 640]},
        },
    },
    "S38": {
        "hotspots": {
            "S38.paper_boat": {"rect": [1376, 590, 72, 50], "interaction_point": [1415, 740], "label_anchor": [1412, 580],
                               "reason": "content v2: a paper boat stuck in the grass at the canal edge between the planting table and the reeds"},
        },
        "variant_layers": {
            "variants/S38_paper_boat.webp": {"texture": V + "S38_paper_boat.webp", "pos": [1376, 588]},
        },
    },
    "S17": {
        "variant_layers": {
            "variants/S17_sign_shapes_only.webp": {"texture": V + "S17_sign_shapes_only.webp", "pos": [200, 496]},
        },
    },
}
S69_FILES = ["S69.json", "ambient/S69.json"]

# World-overlay variant layers of an action done in the current room are deferred until the room is re-entered
# (Core WorldEffects.VariantLayers); a prop Adam changes in front of the player needs an immediate state patch too
# (as S37's bowl seeds after Q6C). Drawn after the variant layers, in list order.
STATE_PATCHES = {
    "S37": [
        {"texture": V + "S37_zuzana_bell_gone.webp", "pos": [282, 912], "after": ["Q10A"], "until": [],
         "reason": "content v2: Adam takes Zuzana's mute class bell from the grass (Q10A); shows at once"},
        {"texture": V + "S37_zuzana_bell_back.webp", "pos": [282, 912], "after": ["Q10D"], "until": [],
         "reason": "content v2: the repaired bell lies in the grass again after Zuzana rang it (Q10D); shows at once"},
    ],
}


def overlay_has_s69() -> bool:
    try:
        data = json.loads(WORLD_EXT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return any(r.get("id") == "S69" for r in data.get("rooms", []))


NL = "\n"


def dump2(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + NL


def entry_line(key: str, value) -> str:
    return NL + "    " + json.dumps(key, ensure_ascii=False) + ": " + json.dumps(value, ensure_ascii=False)


def text_insert(text: str, group: str, key: str, value) -> str | None:
    """Insert one compact line `"key": value,` right after the top-level `"group": {` of a hand-formatted file
    (so its own formatting stays untouched). None when the group is missing."""
    marker = NL + '  "' + group + '": {'
    i = text.find(marker)
    if i < 0:
        return None
    j = i + len(marker)
    line = entry_line(key, value)
    if not text[j:].lstrip().startswith("}"):
        line += ","
    return text[:j] + line + text[j:]


def text_remove(text: str, key: str, value) -> str:
    for tail in (",", ""):
        line = entry_line(key, value) + tail
        if line in text:
            return text.replace(line, "", 1)
    return text


def text_add_group(text: str, group: str, entries: dict) -> str:
    body = text.rstrip()
    assert body.endswith("}")
    return body[:-1].rstrip() + "," + NL + '  "' + group + '": ' + json.dumps(entries, ensure_ascii=False) + NL + "}" + NL


def apply(target: Path, remove: bool = False, dry: bool = False) -> list[str]:
    changes = []
    for rel in S69_FILES:
        dst = target / rel
        if remove:
            if dst.exists():
                changes.append(f"delete {rel}")
                if not dry:
                    dst.unlink()
        else:
            src = STAGE / rel
            if not dst.exists() or dst.read_bytes() != src.read_bytes():
                changes.append(f"copy {rel}")
                if not dry:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, dst)
    for rid, groups in SNIPPETS.items():
        path = target / f"{rid}.json"
        original = path.read_text(encoding="utf-8")
        text = original
        data = json.loads(text)
        exact2 = dump2(data) == text
        for group, entries in groups.items():
            for key, value in entries.items():
                present = key in data.get(group, {})
                if remove and present:
                    changes.append(f"{rid}.{group} - {key}")
                    if exact2:
                        del data[group][key]
                        if group == "variant_layers" and not data[group]:
                            del data[group]
                    else:
                        if len(data[group]) == 1 and group == "variant_layers":
                            text = text.replace("," + NL + '  "' + group + '": ' +
                                                json.dumps({key: data[group][key]}, ensure_ascii=False), "", 1)
                        else:
                            text = text_remove(text, key, data[group][key])
                        data = json.loads(text)
                elif not remove and (not present or data[group][key] != value):
                    changes.append(f"{rid}.{group} + {key}")
                    if exact2:
                        data.setdefault(group, {})[key] = value
                    else:
                        if group not in data:
                            text = text_add_group(text, group, {key: value})
                        else:
                            if present:
                                text = text_remove(text, key, data[group][key])
                            text = text_insert(text, group, key, value)
                        data = json.loads(text)
        for patch in STATE_PATCHES.get(rid, []):
            have = [p for p in data.get("state_patches", []) if p.get("texture") == patch["texture"]
                    and p.get("after") == patch["after"]]
            if remove and have:
                changes.append(f"{rid}.state_patches - {patch['texture']}")
                data["state_patches"] = [p for p in data["state_patches"] if p not in have]
            elif not remove and not have:
                changes.append(f"{rid}.state_patches + {patch['texture']}")
                data.setdefault("state_patches", []).append(patch)
            if not exact2 and (have if remove else not have):
                raise SystemExit(f"{rid}.json is hand-formatted: state patches need a manual edit")
        new_text = dump2(data) if exact2 else text
        json.loads(new_text)
        if not dry and new_text != original:
            with path.open("w", encoding="utf-8", newline=NL) as handle:
                handle.write(new_text)
    return changes


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["check", "install", "remove"])
    ap.add_argument("--dir", type=Path)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    target = args.dir or LIVE
    if args.cmd == "install" and target == LIVE and not overlay_has_s69() and not args.force:
        sys.exit("world_ext.json does not define S69 yet: installing would make tools/check_blocking.py fail "
                 "(use --dir for a QA copy, or --force)")
    changes = apply(target, remove=args.cmd == "remove", dry=args.cmd == "check")
    print("\n".join(changes) or "nothing to change")


if __name__ == "__main__":
    main()
