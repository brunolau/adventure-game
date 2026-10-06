"""Inventory icons of the content v2 overlay (Zuzana 1962, Sokolikovsky dvor 1995) plus three small scene sprites cut
from the same grid, so they share the icons' camera, light and brushwork (docs/story/SOKOLIKOVA_YARD.md 6.3/6.4,
docs/story/ZUZANA.md 4.1).

Icons (items/<ID>.webp, 256 px, like the existing set): BELLCAP, BELL_MUTE, ZUZA_SLIP, STRAP, BELL_FIXED.
Scene sprites (not items; art/items/scene/): BELL_LYING (the class bell dropped in the grass of S37), PAPERBOAT (the
paper boat at the S38 canal edge), BALL95 (the yard ball of the S69 ambient layer).

Paid: one Nano Banana 2 2K 4 x 2 grid through items.py (style reference = a grid of approved icons), behind the
content v2 task guard. Free: cut + export through items.py.

  python content_v2_items.py stylegrid
  python content_v2_items.py sheet [--seed N]
  python content_v2_items.py cut RAW
  python content_v2_items.py export
"""
from __future__ import annotations

import argparse
import shutil
import sys

import content_v2_budget as guard
import items

_BELL = ("a small brass hand bell of a 1960s village school class, about 12 cm tall, polished warm brass with a few "
         "dull spots, a turned dark-brown wooden handle on its crown")

BRIEFS = {
    "BELLCAP": ("The domed top cap of a child's bicycle bell, shown large and tilted so that both its outside and "
                "its inside are visible: a shiny brass dome about 5 cm across; inside it a small ring of fine gear "
                "teeth around a centre hole; one fresh bright scratch on the side of the dome."),
    "BELL_MUTE": ("A school class bell that cannot ring: " + _BELL + ", standing and tilted towards the viewer so "
                  "that its open mouth is visible: inside, the clapper (a small metal ball on a short rod) is wrapped "
                  "in a little white cotton handkerchief with a thin blue border whose corner hangs out of the bell; "
                  "a short torn end of an old thin dark leather loop dangles beside it."),
    "ZUZA_SLIP": ("A child's handwritten supply note: a small sheet torn from a 1960s ruled school exercise book "
                  "(pale blue lines, one red margin line, a ragged torn left edge), folded once and opened again; "
                  "on it four lines of large, wobbly grey pencil strokes in a child's hand that look like big "
                  "capital letters from afar but are only illegible wavy marks, and at the bottom one big wobbly "
                  "pencil squiggle as a signature. No real letters, no words and no digits."),
    "STRAP": ("A narrow cut-off strip of tan leather from a harness strap, about as long as a hand and a finger "
              "wide, with two clean straight cut ends, lying in a gentle S-curve; fine leather grain, a little "
              "darker along the edges."),
    "BELL_FIXED": ("The same school class bell, repaired: " + _BELL + ", standing and tilted towards the viewer so "
                   "that its open mouth is visible: inside, the small metal clapper hangs free on a new short loop "
                   "of tan leather whose knot is tucked away inside; no handkerchief; the brass gleams."),
    "BELL_LYING": ("The same school class bell (" + _BELL + ") lying on its side on the ground as if put down by a "
                   "child, seen from slightly above, its open mouth towards the right with the corner of a white "
                   "handkerchief peeking out; nothing under it, no ground and no shadow."),
    "PAPERBOAT": ("A small folded paper boat made from a sheet of a ruled school exercise book (pale blue lines), "
                  "slightly crumpled and darker and damp along its bottom edge; on its side a few faint short grey "
                  "pencil marks, illegible."),
    "BALL95": ("A worn children's football of the 1990s: a classic leather ball of white hexagons and black "
               "pentagons, scuffed grey from the asphalt, seen as a plain round ball."),
}
ORDER = ["BELLCAP", "BELL_MUTE", "ZUZA_SLIP", "STRAP", "BELL_FIXED", "BELL_LYING", "PAPERBOAT", "BALL95"]
ICONS = ORDER[:5]
STYLE_IDS = ["CHALK", "CARBON", "LEATHER", "STYLUS", "SUPPLYSLIP", "PUNCH", "SHEDKEY", "BALL"]
STYLE_GRID = items.RAW / "content_v2_stylegrid.png"
SCOPE = "items/content_v2/"

items.ICON_BRIEFS.update(BRIEFS)


def _guard(args, asset: str, usd: float) -> None:
    total = guard.spent()
    if total + usd > guard.CAP + 1e-9:
        sys.exit(f"BUDGET: {asset}: {total:.3f} + {usd:.3f} USD would exceed the content v2 cap {guard.CAP:.2f}")
    if not asset.startswith(SCOPE):
        sys.exit(f"{asset}: not under {SCOPE}")
    print(f"[content v2 budget] {total:.3f} spent of {guard.CAP:.2f}; this call {usd:.3f}", file=sys.stderr)


items.task_guard = _guard


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["stylegrid", "sheet", "cut", "export"])
    ap.add_argument("raw", nargs="?")
    ap.add_argument("--seed", type=int, default=1962)
    args = ap.parse_args()
    if args.cmd == "stylegrid":
        items.cmd_stylegrid(argparse.Namespace(ids=STYLE_IDS, out=str(STYLE_GRID)))
    elif args.cmd == "sheet":
        ns = argparse.Namespace(ids=",".join(ORDER), style_ref=str(STYLE_GRID), out="content_v2/items_sheet_v1",
                                seed=args.seed, budget=guard.CAP, budget_scope=SCOPE, budget_since=guard.START)
        items.cmd_sheet(ns)
    elif args.cmd == "cut":
        items.cmd_cut(argparse.Namespace(raw=args.raw, ids=",".join(ORDER)))
        scene = items.ITEMS / "scene"
        scene.mkdir(exist_ok=True)
        for sid in ORDER[5:]:                       # scene sprites are not inventory items: keep them apart
            for suffix in (".png", "_256.png", ".json"):
                src = items.ITEMS / f"{sid}{suffix}"
                if src.exists():
                    shutil.move(str(src), scene / src.name)
        print("scene sprites ->", scene)
    elif args.cmd == "export":
        items.cmd_export(argparse.Namespace(ids=ICONS))


if __name__ == "__main__":
    main()
