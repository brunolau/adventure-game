"""Build docs/locations.html: every room's real place, reference photos and current painting.

Usage: python tools/build_locations_gallery.py   (re-run any time; all paths are relative)
"""
import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def rel(path):
    """Path relative to docs/, with forward slashes for the browser."""
    return Path("..", path.relative_to(ROOT)).as_posix()


def photos_for(room_id, row):
    folder = ROOT / "art" / "source" / "rooms" / room_id
    files = sorted(p for p in folder.glob("*") if p.suffix.lower() in IMAGE_EXT) if folder.exists() else []
    # Family members store their shared base in the first room's folder; follow source_files too.
    for token in row.get("source_files", "").replace(";", " ").replace("|", " ").split():
        candidate = ROOT / token.strip()
        if candidate.suffix.lower() in IMAGE_EXT and candidate.exists() and candidate not in files:
            files.append(candidate)
    return files


def painting_for(room_id):
    for sub in ("bg_natural", "bg"):
        p = ROOT / "src" / "game" / "assets" / sub / f"{room_id}.webp"
        if p.exists():
            return p, sub
    return None, None


def main():
    game = json.loads((ROOT / "design-doc" / "game.json").read_text(encoding="utf-8"))
    rooms = {r["id"]: r for r in game["rooms"]}
    rows = list(csv.DictReader(open(ROOT / "design-doc" / "LOCATIONS_REGISTER.csv", encoding="utf-8-sig")))
    sections = []
    for row in rows:
        rid = row["room_id"]
        room = rooms.get(rid, {})
        painting, kind = painting_for(rid)
        lat, lon = row.get("lat", "").strip(), row.get("lon", "").strip()
        map_link = (f'<a href="https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=18/{lat}/{lon}" '
                    f'target="_blank">map</a>') if lat and lon else ""
        photos = "".join(
            f'<a href="{rel(p)}" target="_blank"><img loading="lazy" src="{rel(p)}" alt=""></a>'
            for p in photos_for(rid, row)) or '<p class="muted">no reference photo (reconstruction or type reference)</p>'
        paint = (f'<a href="{rel(painting)}" target="_blank"><img loading="lazy" src="{rel(painting)}" alt=""></a>'
                 f'<span class="tag">{"natural layout" if kind == "bg_natural" else "painted"}</span>'
                 if painting else '<p class="muted">not painted yet</p>')
        nc = "nc" if "NC" in row.get("license", "") else ""
        sections.append(f"""
<section data-text="{html.escape((rid + ' ' + row.get('room_name', '') + ' ' + row.get('real_place', '') + ' ' + row.get('area', '')).lower())}">
  <header>
    <h2>{html.escape(rid)} · {html.escape(row.get('room_name', ''))} <small>{html.escape(str(room.get('era', row.get('era', ''))))}</small></h2>
    <p class="place">{html.escape(row.get('real_place', ''))}</p>
    <p class="meta"><b>{html.escape(row.get('basis', ''))}</b> · {html.escape(row.get('area', ''))} {map_link}
      · <span class="{nc}">{html.escape(row.get('license', ''))}</span> · {html.escape(row.get('author', ''))}</p>
  </header>
  <div class="cols">
    <div class="photos">{photos}</div>
    <div class="paint">{paint}</div>
  </div>
  <details><summary>notes</summary><p>{html.escape(row.get('fiction_notes', ''))}</p><p>{html.escape(row.get('notes', ''))}</p></details>
</section>""")
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Real Locations</title>
<style>
:root {{ --bg:#15171c; --fg:#e8e6e1; --muted:#9a9890; --card:#1e2128; --accent:#e0a458; --warn:#e07a5f; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 system-ui,sans-serif; }}
main {{ max-width:1500px; margin:0 auto; padding:24px 16px 64px; }}
h1 {{ font-size:22px; margin:0 0 4px; }} .lead {{ color:var(--muted); margin:0 0 16px; }}
input {{ width:100%; max-width:420px; padding:8px 10px; border-radius:6px; border:1px solid #333; background:var(--card); color:var(--fg); font:inherit; }}
section {{ background:var(--card); border-radius:10px; padding:14px 16px; margin-top:18px; }}
h2 {{ font-size:17px; margin:0; color:var(--accent); }} h2 small {{ color:var(--muted); font-weight:400; }}
.place {{ margin:4px 0 0; font-weight:600; }} .meta {{ margin:2px 0 10px; color:var(--muted); font-size:13px; }}
.meta a {{ color:var(--accent); }} .nc {{ color:var(--warn); }}
.cols {{ display:grid; grid-template-columns:1fr 1.15fr; gap:12px; align-items:start; }}
.photos {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:8px; }}
img {{ display:block; width:100%; height:auto; border-radius:6px; }}
.paint {{ position:relative; }} .tag {{ position:absolute; top:8px; left:8px; background:#000a; padding:2px 8px; border-radius:4px; font-size:12px; }}
.muted {{ color:var(--muted); font-size:13px; }} details {{ margin-top:8px; color:var(--muted); font-size:13px; }}
@media (max-width:760px) {{ .cols {{ grid-template-columns:1fr; }} }}
</style></head><body><main>
<h1>Posledný zvonec: real locations</h1>
<p class="lead">68 rooms from design-doc/LOCATIONS_REGISTER.csv. Left: licensed reference photos of the real place. Right: the game painting (if done). Click any image for full size.</p>
<input id="q" placeholder="filter: Dúbravka, S17, Jasná, photo, reconstruction…">
{''.join(sections)}
</main>
<script>
document.getElementById('q').addEventListener('input', e => {{
  const q = e.target.value.toLowerCase().trim();
  document.querySelectorAll('section').forEach(s => {{
    s.style.display = !q || s.dataset.text.includes(q) || s.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}});
</script></body></html>"""
    DOCS.mkdir(exist_ok=True)
    (DOCS / "locations.html").write_text(page, encoding="utf-8")
    print(f"docs/locations.html: {len(rows)} rooms")


if __name__ == "__main__":
    main()
