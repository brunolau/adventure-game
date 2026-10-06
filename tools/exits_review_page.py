#!/usr/bin/env python3
"""Owner review page for the exit directions: docs/navigation/exits_review.html (owner request 2026-10-07).

For every room: the in-game capture with the Space markers (arrow badges follow each exit's side) plus a tag with the
destination name drawn over each exit, the camera heading as a compass line ("screen left = north-west, ..."), the
confidence and evidence from docs/navigation/compass/<room>.json, and what changed since the baseline revision
(default 754af07, the 2026-10-06 layout). Rooms with low / medium confidence and rooms with an open owner question come
first. The page is self-contained (inline CSS / JS) and links the captures by relative path
(build/screens/exits_geo/<room>_markers.png, else <room>.png).

Usage: python tools/exits_review_page.py [--baseline REV]
"""
from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exit_audit as ea  # noqa: E402

ROOT = ea.ROOT
OUT = ROOT / "docs" / "navigation" / "exits_review.html"
SHOTS = ROOT / "build" / "screens" / "exits_geo"
COMPASS = ROOT / "docs" / "navigation" / "compass"

OWNER_FACTS = [
    "Švantnerova stop (S11 1995, S51 2020, S57 1982): the way to ZŠ Sokolíkova (S12 / S52 / S58) is on the LEFT.",
    "Karlova Ves (S19 tram platform, S20 repair shop): Dúbravka is on the RIGHT, the city (Staré Mesto, Ružinov, "
    "Petržalka) on the LEFT.",
    "S07 Čierna Voda stop (kept as you set it): the shop S04 at the bottom left on the road, the bus to Dúbravka higher "
    "on the road, pointing up.",
    "General: every next-location arrow points where that place really lies from the camera's real position and "
    "heading; the return exit in the target room points back.",
]

# Open questions for the owner: (room, exit or "", question). Each is a place where the real geography and the game's
# route or an earlier owner layout disagree, or where no real camera exists.
QUESTIONS = [
    ("S07", "S07.to_S04", "Kept as you set it (bottom left). In reality the shop (Centrum MONAR, 550 m) lies straight "
     "ahead along the road, the same way as the bus. Keep it, or move the shop to the road ahead?"),
    ("S51", "S51.to_S07", "The bus back to Čierna Voda now leaves towards you (down), because the route runs south-east "
     "through Karlova Ves and the city. In a straight line Čierna Voda lies east-north-east, which would be the right "
     "edge. Down (route) or right (straight line)?"),
    ("S17", "S17.to_S12", "Same for S55 and S61. The yard's way to the school front goes out of the left edge, round "
     "the south-east end of the main wing. The front entrance really lies ahead-right, and the shorter real walk goes "
     "round the north-west end, but the right side is the way to the panel blocks (your 2026-10-06 note). Keep left?"),
    ("S28", "S28.to_S21", "The bus to Kamenné námestie leaves from the stop on Rusovská cesta, which runs north-west "
     "(left). Kamenné námestie itself lies north-north-east. The heading here is low confidence: the underpass is "
     "painted from a type photo, not the real place. Left (the bus) or up?"),
    ("S02", "S02.to_S05", "The houses are invented, so the heading is a guess. Mira's gate is along the footpath "
     "between the plots (into the picture); it also lies to the right, like the park S03. Keep the footpath, or move "
     "both to the right edge?"),
    ("S18", "", "Same picture as S62. It is the Sokolíkova street painting you liked; its real camera position is "
     "unknown (the Flickr geotag is 400 m away). The school is on the left, the stop on the right, and the yard S69 is "
     "up the side road. Does that match how you picture the street?"),
    ("S21", "", "The painting is a composite: Hotel Kyjev is drawn right of the department store, but from the real "
     "plaza it stands to the left. Every exit decision holds for any heading between north and north-east."),
]



TITLES = {
    "S07": "shop S04: keep bottom left, or straight ahead along the road?",
    "S51": "bus to Čierna Voda: towards you (route) or right edge (straight line)?",
    "S17": "school yard (also S55, S61) to the front: keep the left edge?",
    "S28": "bus to Kamenné námestie: left (bus route) or up?",
    "S02": "Mira's gate: footpath into the picture, or right edge?",
    "S18": "Sokolíkova street (also S62): no real camera; does the layout match?",
    "S21": "composite painting; for information only",
}


def word(deg: float) -> str:
    return ea.compass_word(deg)


def load_baseline(rev: str) -> Path | None:
    tmp = ROOT / "build" / "exits_review_baseline"
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        files = subprocess.run(["git", "ls-tree", "--name-only", rev, "src/game/data/blocking/"], cwd=ROOT,
                               capture_output=True, text=True, check=True).stdout.split()
        for f in files:
            if f.endswith(".json"):
                data = subprocess.run(["git", "show", f"{rev}:{f}"], cwd=ROOT, capture_output=True, check=True).stdout
                (tmp / Path(f).name).write_bytes(data)
    except (OSError, subprocess.CalledProcessError):
        return None
    return tmp


def exit_notes(c: dict) -> dict[str, dict]:
    ex = c.get("exits", [])
    if isinstance(ex, dict):
        return {k: v for k, v in ex.items()}
    return {e.get("id"): e for e in ex if isinstance(e, dict)}


def shot(rid: str) -> str | None:
    for name in (f"{rid}_markers.png", f"{rid}.png"):
        if (SHOTS / name).exists():
            return "../../build/screens/exits_geo/" + name
    return None


ARROW = {"left": "←", "right": "→", "up": "↑", "down": "↓"}
SIDE_TXT = {"left": "left edge", "right": "right edge", "up": "into the picture", "down": "towards you"}


def tag_pos(rect: list[int], side: str) -> tuple[float, float, str]:
    """Where the destination tag goes (percent of the picture) and its anchor class."""
    x, y, w, h = rect
    cx, cy = x + w / 2, y + h / 2
    cx = min(max(cx, 40), 1880)
    cy = min(max(cy, 40), 990)
    anchor = "l" if cx < 300 else "r" if cx > 1620 else "c"
    ty = cy + 46 if cy < 900 else cy - 46
    return cx / 19.2, ty / 10.8, anchor


def main(argv: list[str]) -> int:
    rev = argv[argv.index("--baseline") + 1] if "--baseline" in argv else "754af07"
    rooms, reg, eff = ea.load()
    base_dir = load_baseline(rev)
    old = ea.load(base_dir)[2] if base_dir else {}
    qs: dict[str, list[tuple[str, str]]] = {}
    for rid, eid, q in QUESTIONS:
        qs.setdefault(rid, []).append((eid, q))
    cards = []
    n_changed_rooms = n_changed_exits = 0
    for rid in sorted(rooms):
        room = rooms[rid]
        cpath = COMPASS / f"{rid}.json"
        c = json.loads(cpath.read_text(encoding="utf-8")) if cpath.exists() else {}
        notes = exit_notes(c)
        conf = c.get("confidence") or "low"
        h = c.get("heading_deg")
        if isinstance(h, (int, float)):
            heading = (f"Camera looks {word(h)} ({h:.0f}°): screen left = {word(h - 90)}, screen right = {word(h + 90)}, "
                       f"into the picture = {word(h)}, towards you = {word(h + 180)}.")
        else:
            heading = "No real compass heading (an interior or an invented place): the exits follow the painted doors and ways."
        oex = {e["id"]: e for e in old.get(rid, {}).get("exits", [])}
        rows, tags, changed = [], [], 0
        for e in eff[rid]["exits"]:
            side = ea.side_of(e)
            to = e["to"]
            tname = rooms.get(to, {}).get("name", to)
            o = oex.get(e["id"])
            oside = ea.side_of(o) if o else None
            moved = o is not None and (oside != side or o["rect"] != e["rect"])
            if moved:
                changed += 1
            note = notes.get(e["id"], {})
            why = note.get("why") or note.get("route") or ""
            back = next((x for x in eff.get(to, {}).get("exits", []) if x["to"] == rid), None)
            bside = ea.side_of(back) if back else None
            change = (f"{oside} → {side}" if oside != side else "moved (same side)") if moved else ("new" if o is None and base_dir else "")
            travel = e.get("travel", "walk")
            rows.append(
                f"<tr class='{'chg' if moved else ''}'><td><span class='arr'>{ARROW[side]}</span> {SIDE_TXT[side]}</td>"
                f"<td><b>{html.escape(to)}</b> {html.escape(tname)}<div class='sub'>{html.escape(travel)}"
                f"{' · return: ' + SIDE_TXT[bside] if bside else ''}</div></td>"
                f"<td>{'<span class=pill>' + html.escape(change) + '</span>' if change else '<span class=muted>unchanged</span>'}</td>"
                f"<td class='why'>{html.escape(why)}</td></tr>")
            px, py, anchor = tag_pos(e["rect"], side)
            tags.append(f"<span class='tag a{anchor}{' tchg' if moved else ''}' style='left:{px:.2f}%;top:{py:.2f}%'>"
                        f"{ARROW[side]} {html.escape(tname)}</span>")
        if changed:
            n_changed_rooms += 1
            n_changed_exits += changed
        ev = "".join(f"<li>{html.escape(x)}</li>" for x in (c.get("evidence") or [])[:4])
        qhtml = "".join(f"<div class='q'><b>Question{' (' + html.escape(eid) + ')' if eid else ''}:</b> {html.escape(q)}</div>"
                        for eid, q in qs.get(rid, []))
        img = shot(rid)
        pic = (f"<div class='pic'><img loading='lazy' src='{img}' alt='{rid} with exit markers'>{''.join(tags)}</div>"
               if img else "<div class='pic none'>no capture</div>")
        fam = room.get("camera_family") or ""
        fam = "" if fam == rid else fam
        order = (0 if rid in qs else 1, {"low": 0, "medium": 0}.get(conf, 1), rid)
        cards.append((order, f"""
<section class="card" id="{rid}" data-conf="{conf}" data-chg="{1 if changed else 0}" data-q="{1 if rid in qs else 0}">
  <header><h2><span class="rid">{rid}</span> {html.escape(room['name'])}</h2>
    <div class="meta"><span class="conf c-{conf}">{conf} confidence</span><span>{room['era']}</span>{'<span>' + html.escape(fam) + '</span>' if fam else ''}
    {'<span class="pill">' + str(changed) + ' exit' + ('s' if changed > 1 else '') + ' changed</span>' if changed else '<span class="muted">no change</span>'}</div></header>
  <p class="heading">{html.escape(heading)}</p>
  {qhtml}
  {pic}
  <table><thead><tr><th>arrow</th><th>leads to</th><th>since yesterday</th><th>why</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
  {'<details><summary>Evidence for the heading</summary><ul>' + ev + '</ul></details>' if ev else ''}
</section>"""))
    cards.sort(key=lambda x: x[0])
    facts = "".join(f"<li>{html.escape(f)}</li>" for f in OWNER_FACTS)
    qlist = "".join(f"<li><a href='#{r}'>{r}</a>{' ' + html.escape(TITLES.get(r, '')) if TITLES.get(r) else ''}</li>"
                    for r, _, _ in QUESTIONS)
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Exit Direction Review</title>
<style>
:root {{ --bg:#f6f3ee; --card:#fffdf9; --ink:#22201c; --muted:#6d675e; --line:#e2dbcf; --accent:#0f6e6e; --chg:#b4531a;
  --chgbg:#fbeee3; --low:#a33a2a; --med:#9a6a00; --high:#2f7d3b; --tag:#102a2a; --tagink:#fff; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#171614; --card:#211f1c; --ink:#ece7df;
  --muted:#a59d91; --line:#36322c; --accent:#5cc0bd; --chg:#f0a060; --chgbg:#3a2a1d; --low:#ef8a78; --med:#e2b44a;
  --high:#7fcf8a; --tag:#0b1d1d; --tagink:#fff; }} }}
:root[data-theme="dark"] {{ --bg:#171614; --card:#211f1c; --ink:#ece7df; --muted:#a59d91; --line:#36322c; --accent:#5cc0bd;
  --chg:#f0a060; --chgbg:#3a2a1d; --low:#ef8a78; --med:#e2b44a; --high:#7fcf8a; --tag:#0b1d1d; --tagink:#fff; }}
* {{ box-sizing:border-box; }}
html, body {{ overflow-x:hidden; }} td, p, li {{ overflow-wrap:anywhere; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif; }}
main {{ max-width:1180px; margin:0 auto; padding:24px 16px 64px; }}
h1 {{ font-size:26px; margin:0 0 4px; }} .lead {{ color:var(--muted); margin:0 0 20px; }}
.box {{ background:var(--card); border:1px solid var(--line); border-left:4px solid var(--accent); border-radius:8px; padding:12px 16px; margin:0 0 16px; }}
.box h3 {{ margin:0 0 6px; font-size:15px; }} .box ul {{ margin:0; padding-left:20px; }}
.box.q {{ border-left-color:var(--chg); }}
a {{ color:var(--accent); }}
.bar {{ display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 20px; align-items:center; }}
.bar button {{ font:inherit; padding:6px 12px; border-radius:16px; border:1px solid var(--line); background:var(--card); color:var(--ink); cursor:pointer; }}
.bar button.on {{ background:var(--accent); color:#fff; border-color:var(--accent); }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px; margin:0 0 22px; }}
.card h2 {{ font-size:19px; margin:0; }} .rid {{ color:var(--accent); font-variant-numeric:tabular-nums; }}
.meta {{ display:flex; flex-wrap:wrap; gap:6px 12px; color:var(--muted); font-size:13px; margin-top:4px; }}
.conf {{ font-weight:600; }} .c-low {{ color:var(--low); }} .c-medium {{ color:var(--med); }} .c-high {{ color:var(--high); }}
.pill {{ background:var(--chgbg); color:var(--chg); border-radius:10px; padding:0 8px; font-weight:600; white-space:nowrap; }}
.muted {{ color:var(--muted); }}
.heading {{ margin:10px 0; font-weight:500; }}
.q {{ background:var(--chgbg); border-radius:6px; padding:8px 12px; margin:8px 0; }}
.pic {{ position:relative; width:100%; aspect-ratio:16/9; background:#000; border-radius:6px; overflow:hidden; margin:10px 0; }}
.pic img {{ width:100%; height:100%; display:block; object-fit:cover; }}
.pic.none {{ display:flex; align-items:center; justify-content:center; color:#aaa; }}
.tag {{ position:absolute; transform:translate(-50%,0); background:var(--tag); color:var(--tagink); font-size:clamp(9px,1.25vw,14px);
  padding:2px 7px; border-radius:5px; white-space:nowrap; opacity:.92; pointer-events:none; border:1px solid rgba(255,255,255,.35); }}
.tag.al {{ transform:none; }} .tag.ar {{ transform:translate(-100%,0); }}
.tag.tchg {{ border-color:#f0a060; box-shadow:0 0 0 1px #f0a060; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; }}
th,td {{ text-align:left; vertical-align:top; padding:6px 8px; border-top:1px solid var(--line); }}
th {{ color:var(--muted); font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:.03em; }}
tr.chg td:first-child {{ color:var(--chg); font-weight:600; }}
.arr {{ font-size:17px; }} .sub {{ color:var(--muted); font-size:12px; }} td.why {{ color:var(--muted); }}
details {{ margin-top:8px; color:var(--muted); font-size:13px; }}
@media (max-width:700px) {{ table, thead, tbody, tr, td, th {{ display:block; }} thead {{ display:none; }}
  tr {{ border-top:1px solid var(--line); padding:6px 0; }} td {{ border:0; padding:2px 0; }} }}
</style></head><body><main>
<h1>Exit direction review</h1>
<p class="lead">Every room with its exit arrows. Generated {html.escape(__import__('datetime').date.today().isoformat())}
by <code>tools/exits_review_page.py</code>. {n_changed_exits} exits in {n_changed_rooms} rooms changed since yesterday's
layout (revision {html.escape(rev)}). Uncertain rooms and rooms with a question come first. The round badges in the
pictures are the game's own Space markers. The dark tags give the destination and its arrow; an orange outline marks a
changed exit.</p>
<div class="box"><h3>Owner facts (binding)</h3><ul>{facts}</ul></div>
<div class="box q"><h3>Questions for you</h3><ul>{qlist}</ul></div>
<div class="bar"><span class="muted">Show:</span>
<button data-f="all" class="on">all rooms</button><button data-f="q">questions</button>
<button data-f="unc">low / medium confidence</button><button data-f="chg">changed</button></div>
{''.join(c for _, c in cards)}
</main>
<script>
document.querySelectorAll('.bar button').forEach(b => b.addEventListener('click', () => {{
  document.querySelectorAll('.bar button').forEach(x => x.classList.toggle('on', x === b));
  const f = b.dataset.f;
  document.querySelectorAll('.card').forEach(c => {{
    const show = f === 'all' || (f === 'q' && c.dataset.q === '1') || (f === 'chg' && c.dataset.chg === '1') ||
      (f === 'unc' && c.dataset.conf !== 'high');
    c.style.display = show ? '' : 'none';
  }});
}}));
</script>
</body></html>
"""
    OUT.write_text(page, encoding="utf-8", newline="\n")
    missing = [r for r in rooms if not shot(r)]
    print(f"exits_review_page: {OUT.relative_to(ROOT)}: {len(rooms)} rooms, {n_changed_exits} changed exits in "
          f"{n_changed_rooms} rooms, {len(QUESTIONS)} questions; missing captures: {missing or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
