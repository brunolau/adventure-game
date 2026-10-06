#!/usr/bin/env python3
"""Exit layout audit: every room's exits, where they lead out of the picture, and whether the layout reads logically.

Writes the generated part of docs/navigation/EXITS.md (between the markers <!-- exits:begin --> and <!-- exits:end -->;
the hand-written part around them is kept) from the EFFECTIVE game (game.json + content overlays, tools/content_ext.py),
the natural blockings (src/game/data/blocking/<room>.json) and design-doc/LOCATIONS_REGISTER.csv.

Per exit: the side (named "side" in the blocking, else derived from the zone exactly like World/ExitSides.cs), the zone
and interaction point, the target, the travel style, the real direction of the target (bearing and distance from the
register coordinates; where the camera heading is known, the side of the picture that direction falls on), the side
of the return exit in the target, and flags:

  CROWD       two exits to different places on the same edge closer than 360 px (doors / paths into the picture:
              200 px), check_blocking.py warns about the same
  ONE-SIDED   two or more exits on one edge and none on the opposite edge
  CONTINUITY  an edge walkway whose return exit sits on the same edge of the target (Adam would turn round)
  NO-RETURN   no exit back from the target (one-way)
  COMPASS     the camera heading is known and the target's real direction falls on the other side of the picture
              (advisory: the register coordinates of some rooms are estimates)

Usage: python tools/exit_audit.py            (rewrite the table in docs/navigation/EXITS.md, print the flags)
       python tools/exit_audit.py --check    (print only; exit code 1 when CROWD / ONE-SIDED / CONTINUITY remain
                                              that are not listed as accepted in EXITS.md)
       python tools/exit_audit.py --blocking DIR --travel FILE   (audit other files, e.g. an older revision; print only)
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content_ext  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BLOCKING = ROOT / "src" / "game" / "data" / "blocking"
REGISTER = ROOT / "design-doc" / "LOCATIONS_REGISTER.csv"
DOC = ROOT / "docs" / "navigation" / "EXITS.md"
BEGIN, END = "<!-- exits:begin -->", "<!-- exits:end -->"
W, H = 1920, 1080
CROWD_EDGE_PX, CROWD_UP_PX = 360, 200

# Camera headings (degrees from north) where the register or the painting log states them; overridden by
# docs/navigation/compass/<room>.json (exit-geography pass 2026-10-07) where that file gives a heading.
CAMERA = {
    "S04": (180, "courtyard of the arc facing the mid unit (the concave side faces north)"),
    "S11": (315, "SW platform looking NW along the track"), "S51": (315, "as S11"), "S57": (315, "as S11"),
    "S12": (45, "at the SW entrance facade"), "S52": (45, "as S12"), "S58": (45, "as S12"),
    "S17": (225, "SE corner of the court looking SW at the yard facade"), "S55": (225, "as S17"), "S61": (225, "as S17"),
    "S30": (292, "upstream footway looking WNW"), "S31": (67, "on the crossing looking ENE along the track"),
    "S32": (22, "square park looking NNE to the fire-station tower"), "S37": (157, "NNW of the facade looking SSE"),
    "S38": (135, "looking SE"), "S42": (202, "forecourt looking SSW to Chopok"), "S45": (157, "north shore looking SSE"),
    "S48": (270, "plateau looking W"), "S66": (90, "yard edge looking E at the shed"),
}
COMPASS_DIR = ROOT / "docs" / "navigation" / "compass"
NAMES = ("north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west")


def compass_word(deg: float) -> str:
    return NAMES[int(((deg % 360) + 22.5) // 45) % 8]


def load_compass() -> dict[str, dict]:
    """docs/navigation/compass/<room>.json (exit-geography pass 2026-10-07): camera heading, confidence, evidence."""
    out: dict[str, dict] = {}
    for p in sorted(COMPASS_DIR.glob("S*.json")) if COMPASS_DIR.exists() else []:
        try:
            out[p.stem] = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
    return out


COMPASS_DATA = load_compass()
for _rid, _c in COMPASS_DATA.items():
    if isinstance(_c.get("heading_deg"), (int, float)):
        _h = float(_c["heading_deg"])
        _screen = ", ".join(f"{s} = {compass_word(_h + 90 * i)}" for i, s in enumerate(("into the picture", "screen right", "towards the viewer", "screen left")))
        CAMERA[_rid] = (_h, f"{_c.get('confidence', '?')} confidence; {_screen}; docs/navigation/compass/{_rid}.json")


def side_of(e: dict) -> str:
    if e.get("side") in ("left", "right", "up", "down"):
        return e["side"]
    x, y, w, h = e["rect"]
    cx, cy = x + w / 2, y + h / 2
    if cx < W * 0.16:
        return "left"
    if cx > W * 0.84:
        return "right"
    return "down" if cy > H * 0.80 else "up"


def load(blocking_dir: Path = BLOCKING, travel: Path | None = None) -> tuple[dict, dict, dict]:
    overlay = content_ext.load_effective_game(travel=travel) if travel else content_ext.load_effective_game()
    if overlay.errors:
        raise SystemExit("content overlay invalid: " + "; ".join(overlay.errors[:5]))
    rooms = {r["id"]: r for r in overlay.game["rooms"]}
    reg = {row["room_id"]: row for row in csv.DictReader(REGISTER.open(encoding="utf-8"))}
    eff: dict[str, dict] = {}
    for rid, room in rooms.items():
        path = blocking_dir / f"{rid}.json"
        blocking = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        bex = blocking.get("exits", {})
        exits = []
        for e in room.get("exits", []):
            m = dict(e)
            for key in ("rect", "interaction_point", "side", "arrival", "reason"):
                if key in bex.get(e["id"], {}):
                    m[key] = bex[e["id"]][key]
            m["natural"] = e["id"] in bex
            exits.append(m)
        eff[rid] = {"room": room, "exits": exits}
    return rooms, reg, eff


def bearing(reg: dict, a: str, b: str) -> tuple[float, float] | None:
    try:
        la1, lo1 = float(reg[a]["lat"]), float(reg[a]["lon"])
        la2, lo2 = float(reg[b]["lat"]), float(reg[b]["lon"])
    except (KeyError, ValueError):
        return None
    dy = (la2 - la1) * 111_200
    dx = (lo2 - lo1) * 111_200 * math.cos(math.radians(la1))
    dist = math.hypot(dx, dy)
    return (math.degrees(math.atan2(dx, dy)) % 360, dist) if dist >= 15 else None


def way(e: dict) -> str:
    """The blocking's description of the painted way, shortened for the table."""
    text = re.sub(r"^(exit layout [0-9-]+ \([^)]*\): |content v2: )", "", e.get("reason") or "")
    text = re.split(r"(?<=[a-z)])[;(]| \(owner| \(travel| \(PT-| \(M5", text)[0].strip().replace("|", "/")
    if not e.get("natural"):
        text = "(template geometry)"
    return text if len(text) <= 110 else text[:107].rstrip() + "..."


def compass_side(heading: float, brg: float) -> str:
    rel = (brg - heading + 360) % 360
    if rel <= 35 or rel >= 325:
        return "up"
    if rel < 145:
        return "right"
    if rel <= 215:
        return "down"
    return "left"


def audit(blocking_dir: Path = BLOCKING, travel: Path | None = None) -> tuple[list[str], list[str]]:
    rooms, reg, eff = load(blocking_dir, travel)
    lines: list[str] = []
    flags: list[str] = []
    eras = {}
    for rid in sorted(rooms):
        eras.setdefault(rooms[rid]["era"], []).append(rid)
    for era in sorted(eras, key=lambda e: [2020, 1995, 1960, 2035, 1982].index(e) if e in (2020, 1995, 1960, 2035, 1982) else 9):
        lines.append(f"\n### {era}\n")
        for rid in eras[era]:
            room = rooms[rid]
            exits = eff[rid]["exits"]
            cam = CAMERA.get(rid)
            conf = COMPASS_DATA.get(rid, {}).get("confidence")
            camtxt = (f"camera {cam[0]:.0f}° ({cam[1]})" if cam else
                      f"camera heading not determinable ({conf} confidence; docs/navigation/compass/{rid}.json)" if conf else
                      "camera heading not recorded")
            lines.append(f"**{rid} {room['name']}** — {camtxt}\n")
            lines.append("| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |")
            lines.append("|---|---|---|---|---|---|---|---|---|")
            by_side: dict[str, list[dict]] = {}
            for e in exits:
                by_side.setdefault(side_of(e), []).append(e)
            for e in exits:
                s = side_of(e)
                f: list[str] = []
                for o in exits:
                    if o is e or o["to"] == e["to"] or side_of(o) != s:
                        continue
                    ca = (e["rect"][0] + e["rect"][2] / 2, e["rect"][1] + e["rect"][3] / 2)
                    cb = (o["rect"][0] + o["rect"][2] / 2, o["rect"][1] + o["rect"][3] / 2)
                    if math.dist(ca, cb) < (CROWD_UP_PX if s == "up" else CROWD_EDGE_PX):
                        f.append(f"CROWD with {o['id']}")
                if s in ("left", "right"):
                    opposite = "right" if s == "left" else "left"
                    if len(by_side.get(s, [])) >= 2 and not by_side.get(opposite):
                        f.append(f"ONE-SIDED ({len(by_side[s])} {s}, none {opposite})")
                back = next((x for x in eff.get(e["to"], {}).get("exits", []) if x["to"] == rid), None)
                bside = side_of(back) if back else None
                if back is None:
                    f.append("NO-RETURN")
                elif (s in ("left", "right") and s == bside and e.get("travel", "walk") == "walk"
                      and (e["rect"][0] <= 5 if s == "left" else e["rect"][0] + e["rect"][2] >= W - 5)
                      and (back["rect"][0] <= 5 if bside == "left" else back["rect"][0] + back["rect"][2] >= W - 5)):
                    f.append("CONTINUITY")
                b = bearing(reg, rid, e["to"])
                real = "—"
                if b:
                    real = f"{b[0]:.0f}° {b[1]:.0f} m"
                    if cam:
                        cs = compass_side(cam[0], b[0])
                        real += f" (→ {cs})"
                        if {cs, s} in ({"left", "right"},):
                            f.append("COMPASS")
                zone = f"{e['rect']} → {e.get('interaction_point')}"
                named = "" if "side" not in e else " (named)"
                ret = f"{back['id']} ({bside})" if back else "—"
                lines.append(f"| {e['id']} | {s}{named} | {way(e)} | {zone} | {e['to']} | {e.get('travel', 'walk')} | {real} | {ret} | "
                             f"{'; '.join(f) if f else 'ok'} |")
                for x in f:
                    flags.append(f"{e['id']}: {x}")
            lines.append("")
    return lines, flags


def accepted() -> set[str]:
    if not DOC.exists():
        return set()
    text = DOC.read_text(encoding="utf-8")
    return set(re.findall(r"accepted: `([^`]+)`", text))


def main(argv: list[str]) -> int:
    def opt(name: str) -> str | None:
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else None
    other = opt("--blocking") is not None or opt("--travel") is not None
    lines, flags = audit(Path(opt("--blocking") or BLOCKING), Path(opt("--travel")) if opt("--travel") else None)
    if "--check" not in argv and not other:
        DOC.parent.mkdir(parents=True, exist_ok=True)
        text = DOC.read_text(encoding="utf-8") if DOC.exists() else f"# Exits\n\n{BEGIN}\n{END}\n"
        if BEGIN not in text:
            text += f"\n{BEGIN}\n{END}\n"
        head, rest = text.split(BEGIN, 1)
        _, tail = rest.split(END, 1)
        body = "\n".join(lines).strip("\n")
        DOC.write_text(f"{head}{BEGIN}\n{body}\n{END}{tail}", encoding="utf-8", newline="\n")
    ok = accepted()
    blocking_kinds = ("CROWD", "ONE-SIDED", "CONTINUITY")
    open_flags = [f for f in flags if f.split(": ", 1)[1].split(" ")[0] in blocking_kinds and f.split(":")[0] not in ok]
    for f in flags:
        print(("  " if f.split(":")[0] in ok else "! ") + f)
    print(f"exit_audit: {sum(len(r) for r in [lines])} lines, {len(flags)} flag(s), {len(open_flags)} open layout flag(s)")
    return 1 if ("--check" in argv and open_flags) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
