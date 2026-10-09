"""English place names (owner 2026-10-08: "translate the location names too … some like Ružinov turn into Ruzinov …
for others like Lúčny koník find a proper English name").

Rules: real geographic names lose their diacritics (Dubravka, Ruzinov, Petrzalka, Jasna, Cierna Voda …); names that
mean something get an English name (the Old Town, the Old Bridge, Kamenne Square, Lake Vrbicke, the Grasshopper
playground, LEAL Court, Light photo studio). People's names: tools/en_person_names.py (since 2026-10-09).

Rewrites every English text that contains one of the names and stores the result in
docs/translation/en/C7_place_names.json (read after the translation batches). Run `en_person_names.py` and then
`en_batches.py merge` afterwards.

    python tools/en_place_names.py [--show]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import en_batches as E  # noqa: E402

OUT = E.OUT / "C7_place_names.json"

# Whole texts that need their own wording.
CUSTOM = {
    "entry.S03.001": "The Grasshopper playground. The wooden grasshopper it is named after watches Ela under the shelter, "
                     "handling phone calls and potatoes at the same time.",
    "region.Staré Mesto.name": "Old Town",
    "action.B14.x04": "On your phone? Phones are for ringing people. Photos are taken with light – that’s why we’re called Light.",
    "puzzle.P03.title": "Calibration on the Old Bridge",
}
# Ordered replacements (regex -> text); the specific phrases come first.
RULES: list[tuple[str, str]] = [
    (r"Lúčny koník – pick-up point", "Grasshopper playground – pick-up point"),
    (r"\b(at|by) Lúčny koník", r"\1 the Grasshopper playground"),
    (r"Lúčny koník", "the Grasshopper playground"),
    (r"\b(at|At) Pri LEALe", r"\1 LEAL Court"),
    (r"Pri LEALe", "LEAL Court"),
    (r"the Svetlo studio", "the Light studio"),
    (r"Svetlo photo studio", "Light photo studio"),
    (r"Starý [mM]ost", "the Old Bridge"),
    (r"Staré Mesto", "the Old Town"),
    (r"Kamenné námestie", "Kamenne Square"),
    (r"Vrbické pleso", "Lake Vrbicke"),
    (r"Chorvátsky Grob", "Chorvatsky Grob"),
    (r"Čierna Voda", "Cierna Voda"),
    (r"Biela Púť", "Biela Put"),
    (r"Dúbravka", "Dubravka"),
    (r"Ružinov", "Ruzinov"),
    (r"Petržalka", "Petrzalka"),
    (r"Jasná", "Jasna"),
    (r"Miletičova", "Mileticova"),
    (r"Miletička", "Mileticka"),
    (r"Sokolíkova", "Sokolikova"),
]


def convert(text: str) -> str:
    for pattern, repl in RULES:
        text = re.sub(pattern, repl, text)
    # A sentence or label that now starts with a lower-case article gets its capital back.
    text = re.sub(r"(^|[.!?…] |‘|: )the (Old Town|Old Bridge|Grasshopper playground|Light studio)",
                  lambda m: m.group(1) + ("The " if m.group(1) in ("", ". ", "! ", "? ", "… ") else "the ") + m.group(2), text)
    return text


def main() -> None:
    # Start from the batches that sort before this file's own output: neither its earlier output nor the files
    # derived from it (C8_person_names.json of tools/en_person_names.py, which must be regenerated after this one).
    have = {}
    for p in sorted(E.OUT.glob("*.json")):
        if p.name < OUT.name and not p.name.startswith("_meta"):
            have.update(json.loads(p.read_text(encoding="utf-8")))
    out = {}
    for k, v in have.items():
        new = CUSTOM.get(k) or convert(v)
        if new != v:
            out[k] = new
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{len(out)} texts changed -> {OUT.relative_to(E.ROOT)}")
    if "--show" in sys.argv:
        for k, v in out.items():
            print(k, "|", v)


if __name__ == "__main__":
    main()
