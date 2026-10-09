"""English names for the characters (owner 2026-10-09: "in english - also change the character names .. Bodka => Dotty
... and come up with English sounding names").

English texts only; the Slovak column and the Slovak voices are not touched. Rules (docs/translation/README.md
"English names of people"):

- the natural English form of a first name where there is one (Tóno / Anton -> Tony / Anthony, Jana -> Jane,
  Fero -> Frank, Viera -> Faith), a name that already reads as English stays (Adam, Mira, Nina, Vera, Boris ...);
- one English form for all Slovak pet forms of a name, plus at most one English nickname (Zuzana / Zuzka ->
  Susanna / Susie, Dezider / Dezi -> Desmond / Des);
- surnames of the (all fictional) characters: the meaning where it gives a common English surname (Hruška -> Perry,
  Kováč -> Smith, Mlynár -> Miller), else an English surname that sounds close (Vargová -> Varley); the same Slovak
  surname gives the same English one, and the feminine -ová goes;
- the dog, the pigeon and the robot by meaning or sound (Bodka -> Dotty, fixed by the owner; Béla -> Barnaby;
  Očko -> Blinky);
- no two characters share a first name, no diacritics are left in a person's name;
- real people (credits, photo sources), historical figures, bands, brands and place names are not touched
  (places: tools/en_place_names.py).

Rewrites every English text that contains one of the names and stores the result in
docs/translation/en/C8_person_names.json (read after every other batch, the place names included). Order of a full
regeneration: en_place_names.py, en_person_names.py, en_batches.py merge, extract_strings.py.

    python tools/en_person_names.py [--show] [--check] [--table]

--check only scans the merged English texts (en_batches.done()) for a Slovak name form or a person's name with
diacritics and fails when one is left; --table prints the mapping as a Markdown table.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import en_batches as E  # noqa: E402

OUT = E.OUT / "C8_person_names.json"

# (who, Slovak forms -> English forms, note). A form missing on the right side of a pair is not listed: every name
# that stays as it is has its own row with the same text on both sides, so the table is the full cast.
PEOPLE: list[tuple[str, dict[str, str], str]] = [
    ("ADAM", {"Adam": "Adam", "Hruška": "Perry"}, "hruška = pear; Perry is the pear-tree surname"),
    ("MIRA", {"Mira": "Mira", "Hrušková": "Perry"}, "Gran; the case in S09 reads M. Perry"),
    ("TONO", {"Tóno": "Tony", "Anton": "Anthony", "Farkaš": "Wolfe"}, "farkas = wolf"),
    ("OTO", {"Oto": "Otto", "Bielik": "Whitlock"}, "biely = white"),
    ("JANA", {"Jana": "Jane", "Vargová": "Varley"}, ""),
    ("LEA", {"Lea": "Leah", "Kormanová": "Korman"}, ""),
    ("VIKTOR", {"Viktor": "Victor", "Korman": "Korman"}, "Leah's son"),
    ("NINA", {"Nina": "Nina", "Švecová": "Swift"}, ""),
    ("ELA", {"Ela": "Ella"}, "Nina's mother, also Swift"),
    ("DANA", {"Dana": "Dana", "Valová": "Vale"}, ""),
    ("ROMAN", {"Roman": "Roman", "Kováč": "Smith"}, "kováč = smith"),
    ("LENKA", {"Lenka": "Helen", "Bartošová": "Bartlett"}, "Bartoš = Bartholomew, as in Bartlett"),
    ("BODKA", {"Bodka": "Dotty"}, "the dog; fixed by the owner (bodka = dot)"),
    ("JOZEF", {"Jozef": "Joseph", "Mlynár": "Miller"}, "mlynár = miller; Mr Joseph"),
    ("SONA", {"Soňa": "Sonia", "Urbanová": "Urban"}, ""),
    ("ZITA", {"Zita": "Rita", "Ondrušová": "Andrews"}, "Ondruš = Andrew"),
    ("EMIL", {"Emil": "Emil", "Belan": "Bellamy"}, ""),
    ("PALI", {"Pali": "Paulie", "Pavol": "Paul", "Drobný": "Small"}, "drobný = small"),
    ("VIERA", {"Viera": "Faith", "Holubová": "Holbrook"}, "viera = faith; not Vera, who is the 1962 draughtswoman"),
    ("KAROL", {"Karol": "Charles", "Merta": "Merton"}, ""),
    ("ALENA", {"Alena": "Elaine", "Svobodová": "Freeman"}, "svoboda = freedom"),
    ("FERO", {"Fero": "Frank", "Lánik": "Furlong"}, "lán = an old measure of land"),
    ("MILADA", {"Milada": "Mildred", "Kyselová": "Sowerby"}, "kyslý = sour"),
    ("JURO", {"Juro": "Jerry"}, "Juro Kazeta -> Jerry Cassette; not George, who is the painter"),
    ("JURAJ", {"Juraj": "George", "Križan": "Crossley"}, "kríž = cross"),
    ("DEZI", {"Dezider": "Desmond", "Dezi": "Des"}, "also Smith (Kováč)"),
    ("BOZO", {"Božidar": "Theodore", "Božo": "Ted", "Fiala": "Fielding"}, "both names mean 'gift of God'"),
    ("BERTA", {"Berta": "Bertha", "Kovárová": "Smithson"}, ""),
    ("ALOJZ", {"Alojz": "Aloysius", "Baran": "Ramsey"}, "baran = ram"),
    ("BELA", {"Béla": "Barnaby"}, "the carrier pigeon"),
    ("LIDA", {"Lída": "Lydia", "Fialová": "Fielding"}, ""),
    ("RUDO", {"Rudolf": "Rudolph", "Rudo": "Rudy", "Pavlík": "Pawley"}, ""),
    ("STEFAN", {"Štefan": "Stephen", "Haluška": "Hallam"}, ""),
    ("VERA60", {"Vera": "Vera", "Nemcová": "Norman"}, ""),
    ("ZUZANA", {"Zuzana": "Susanna", "Zuzka": "Susie"}, "no surname, as in Slovak"),
    ("KUBO", {"Kubo": "Jake", "Kubko": "Jake"}, "Jakub = Jacob"),
    ("DOBRO", {"Dobrovič": "Goodwin"}, "dobro = good; no first name"),
    ("RUZENA", {"Ružena": "Rose", "Malá": "Little"}, "ruža = rose, malá = little"),
    ("MARTA82", {"Marta": "Martha", "Dobiášová": "Dobson"}, ""),
    ("SIMON", {"Šimon": "Simon", "Rybár": "Fisher"}, "rybár = fisherman"),
    ("TAMARA", {"Tamara": "Tamara", "Kráľová": "King"}, "kráľ = king"),
    ("BORIS", {"Boris": "Boris", "Urban": "Urban"}, ""),
    ("SARA", {"Sára": "Sarah", "Vrbová": "Willows"}, "vŕba = willow"),
    ("ROBOT", {"Očko": "Blinky"}, "the delivery robot (očko = little eye)"),
    ("IVAN", {"Ivan": "Ian", "Horský": "Hill"}, "Ivan = John = Ian; horský = of the hills"),
    ("TURISTA", {"Miloš": "Miles", "Polák": "Pollard"}, ""),
]

# Whole texts that need their own wording (a joke or a detail that hangs on the spelling of a name).
CUSTOM = {
    # The name falls apart letter by letter on the visitor list: "Adam Hru" in Slovak.
    "action.F01.x02": "Letter by letter. A minute ago you were all there; now you’re just ‘Adam Per’.",
    # Slovak: "Aj s mäkčeňom?" (the hook on the š of Hruška). Perry has no hook; it has two r's.
    "action.F09.x02": "With both r’s?",
    "action.F09.x03": "Both r’s. Now confirm entry to the chamber at the terminal.",
    # Why the dog is called Bodka ("dosť, bodka" = that's enough, full stop): the dot is now in his English name.
    "topic.LENKA.ambient 1.002": "Because when I say ‘that’s enough, full stop’, he always has one more woof to add. "
                                 "With him, it’s never just the one dot.",
}

# Words with Slovak letters that stay in English texts on purpose (not names of people).
KEPT_DIACRITICS = {"DRUHÝ", "ŽIVOT", "Druhý", "život", "Slovenčina", "café", "lángos", "Lángos"}

SK_LETTERS = "áäčďéíĺľňóôŕšťúýžÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽ"


def mapping() -> dict[str, str]:
    """Slovak form -> English form, with the ALL CAPS variants (a name written on a slip or a cover)."""
    out: dict[str, str] = {}
    for _who, forms, _note in PEOPLE:
        for sk, en in forms.items():
            if out.get(sk, en) != en:
                raise ValueError(f"{sk}: two English forms ({out[sk]}, {en})")
            out[sk] = en
    for sk, en in list(out.items()):
        out[sk.upper()] = en.upper()
    return out


def changed() -> dict[str, str]:
    return {sk: en for sk, en in mapping().items() if sk != en}


def pattern(forms) -> re.Pattern:
    # Whole words only: "Korman" never matches inside "Kormanová", "Ivan" never inside "Ivanka", "Lea" never
    # inside "LEAL". The possessive ’s, a hyphen or punctuation after the name is not a word character.
    alt = "|".join(re.escape(f) for f in sorted(forms, key=len, reverse=True))
    return re.compile(rf"(?<![\w])(?:{alt})(?![\w])")


def convert(text: str) -> str:
    table = changed()
    return pattern(table).sub(lambda m: table[m.group(0)], text)  # one pass: a result is never renamed again


def base_texts() -> dict[str, str]:
    """The English texts of every batch file that sorts before this tool's own output."""
    base: dict[str, str] = {}
    for p in sorted(E.OUT.glob("*.json")):
        if p.name < OUT.name and not p.name.startswith("_meta"):
            base.update(json.loads(p.read_text(encoding="utf-8")))
    return base


def leftovers(texts: dict[str, str]) -> list[str]:
    """Slovak name forms and words with Slovak letters that should not be in an English text any more."""
    old = pattern(changed())
    odd = re.compile(rf"[\w’']*[{SK_LETTERS}][\w’']*")
    problems = []
    for k, v in texts.items():
        for m in old.finditer(v):
            problems.append(f"{k}: Slovak name form '{m.group(0)}' in: {v}")
        for w in odd.findall(v):
            if w.strip("’'") not in KEPT_DIACRITICS and re.sub(r"’s$", "", w) not in KEPT_DIACRITICS:
                problems.append(f"{k}: word with Slovak letters '{w}' in: {v}")
    return problems


def table_markdown() -> str:
    rows = ["| character | Slovak | English | note |", "|---|---|---|---|"]
    for who, forms, note in PEOPLE:
        rows.append(f"| {who} | {' · '.join(forms)} | {' · '.join(dict.fromkeys(forms.values()))} | {note} |")
    return "\n".join(rows)


def main() -> int:
    if "--table" in sys.argv:
        print(table_markdown())
        return 0
    if "--check" in sys.argv:
        problems = leftovers(E.done())
        for p in problems[:60]:
            print(p)
        print(f"RESULT: {'OK' if not problems else 'ERRORS'} ({len(problems)} leftovers, {len(E.done())} texts)")
        return 1 if problems else 0
    first = [en for _w, forms, _n in PEOPLE for sk, en in list(forms.items())[:1]]
    twice = sorted({n for n in first if first.count(n) > 1})
    if twice:
        raise SystemExit(f"two characters share a first name: {twice}")
    base = base_texts()
    missing = [k for k in CUSTOM if k not in base]
    if missing:
        raise SystemExit(f"custom texts for unknown keys: {missing}")
    out = {}
    for k, v in base.items():
        new = CUSTOM.get(k) or convert(v)
        if new != v:
            out[k] = new
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{len(out)} texts changed -> {OUT.relative_to(E.ROOT)}")
    if "--show" in sys.argv:
        for k, v in out.items():
            print(k, "|", v)
    return 0


if __name__ == "__main__":
    sys.exit(main())
