"""English review page: every text in Slovak and English side by side, in play order (docs/translation/review.html).

Groups follow the context bundles (docs/translation/context/C1-C4.md: story actions, rooms, conversations, items,
quests, puzzles, cutscenes, epilogue, names, UI). A Standard/Hard variant (<key>.std) is shown under its base text.

    python tools/en_review_page.py [--out path]
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOC = ROOT / "src/game/localization"
CTX = ROOT / "docs/translation/context"
ERA = {"C1": "2020", "C2": "1995", "C3": "1962 / 1982", "C4": "2035 · UI"}
KEY_LINE = re.compile(r"^\s*- `([^`]+)` \[([^\]]*)\]\s?(.*)$")
SPEAKER = re.compile(r"^\*\*([A-Z0-9_]+)\*\* \(([^)]*)\): ")


def tables() -> dict[str, tuple[str, str]]:
    out = {}
    for t in ("dialogue", "world", "ui"):
        with (LOC / f"{t}.csv").open(encoding="utf-8-sig", newline="") as h:
            for r in csv.DictReader(h):
                out[r["keys"]] = (r["sk"], r.get("en", ""))
    return out


def kind_of(key: str, label: str) -> str:
    if key.startswith(("action.", "topic.", "cutscene.", "entry.", "travel.", "epilogue.")) and "spoken" in label or "subtitle" in label or "credits line" in label or "first entry" in label:
        return "dialogue"
    if key.startswith("look.") or key.startswith("item.") and "look" in label or ".locked" in key:
        return "look"
    if key.startswith("ui.") or key.startswith(("hint.", "era.", "region.")):
        return "ui"
    if key.endswith((".objective", ".journal")) or key.startswith("quest."):
        return "journal"
    return "label"


def build() -> list[dict]:
    t = tables()
    groups, seen = [], set()
    for chunk in ("C1", "C2", "C3", "C4"):
        section, head, rows = "", "", []

        def flush():
            nonlocal rows
            if rows:
                groups.append({"era": ERA[chunk], "section": section, "title": head, "rows": rows})
            rows = []

        for raw in (CTX / f"{chunk}.md").read_text(encoding="utf-8").splitlines():
            if raw.startswith("## "):
                flush()
                section, head = raw[3:].strip(), ""
                continue
            if raw.startswith("### "):
                flush()
                head = raw[4:].strip()
                continue
            m = KEY_LINE.match(raw)
            if not m or m.group(1) in seen or m.group(1) not in t:
                continue
            key, label, text = m.groups()
            seen.add(key)
            sm = SPEAKER.match(text)
            speaker = sm.group(2) if sm else ""
            sk, en = t[key]
            row = {"k": key, "s": speaker, "sk": sk, "en": en, "t": kind_of(key, label)}
            if key + ".std" in t:
                row["stdsk"], row["stden"] = t[key + ".std"]
                seen.add(key + ".std")
            rows.append(row)
        flush()
    rest = [k for k in t if k not in seen and not k.endswith(".std")]
    if rest:
        groups.append({"era": "Other", "section": "Not in the bundles", "title": "",
                       "rows": [{"k": k, "s": "", "sk": t[k][0], "en": t[k][1], "t": "label"} for k in rest]})
    return groups


PAGE = """<title>The Last Bell in English</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Alegreya:wght@400;700&family=Alegreya+Sans:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root { --bg:#f5f1e8; --card:#fffdf8; --fg:#2a2620; --muted:#6f675a; --line:#e2d9c8; --accent:#8a5a1f; --std:#3f6b4f; --stdbg:#edf4ee; --hl:#fff1c2; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#1d1b18; --card:#26231f; --fg:#ece6da; --muted:#a69d8d; --line:#3a352e; --accent:#d9a45a; --std:#8fc79f; --stdbg:#22302a; --hl:#4a3f1c; color-scheme:dark } }
:root[data-theme="dark"] { --bg:#1d1b18; --card:#26231f; --fg:#ece6da; --muted:#a69d8d; --line:#3a352e; --accent:#d9a45a; --std:#8fc79f; --stdbg:#22302a; --hl:#4a3f1c; color-scheme:dark }
body { background:var(--bg); color:var(--fg); font:15px/1.5 "Alegreya Sans", system-ui, sans-serif; margin:0; padding-inline:16px; padding-block:24px 64px; }
main { max-width:1100px; margin:0 auto; display:flex; flex-direction:column; gap:20px; }
h1 { font-family:Alegreya, Georgia, serif; font-size:2rem; margin:0; text-wrap:balance; }
h1 small { display:block; font-family:"Alegreya Sans", sans-serif; font-size:1rem; color:var(--muted); font-weight:400; }
.intro { color:var(--muted); max-width:70ch; margin:0; }
.stats { display:flex; flex-wrap:wrap; gap:8px 24px; font-variant-numeric:tabular-nums; color:var(--muted); font-size:.9rem; }
.stats b { color:var(--fg); }
.bar { position:sticky; top:env(safe-area-inset-top,0px); z-index:5; background:var(--bg); padding-block:10px; display:flex; flex-wrap:wrap; gap:8px; border-bottom:1px solid var(--line); }
.bar input, .bar select { font:inherit; padding:6px 10px; border:1px solid var(--line); border-radius:6px; background:var(--card); color:var(--fg); }
.bar input { flex:1 1 220px; min-width:0; }
.group { background:var(--card); border:1px solid var(--line); border-radius:8px; overflow:hidden; }
.group h2 { font-size:1rem; margin:0; padding:10px 14px; border-bottom:1px solid var(--line); display:flex; gap:10px; align-items:baseline; flex-wrap:wrap; }
.group h2 .era { font-size:.75rem; letter-spacing:.06em; text-transform:uppercase; color:var(--accent); font-weight:700; }
.group h2 .sec { color:var(--muted); font-weight:400; font-size:.85rem; }
.row { display:grid; grid-template-columns: minmax(0,1fr) minmax(0,1fr); gap:4px 18px; padding:8px 14px; border-top:1px solid var(--line); }
.row:first-of-type { border-top:0; }
.who { grid-column:1 / -1; font-size:.75rem; color:var(--muted); letter-spacing:.03em; }
.who code { font-size:.7rem; opacity:.7; }
.sk { color:var(--muted); }
.std { grid-column:1 / -1; display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:4px 18px; background:var(--stdbg); border-left:3px solid var(--std); padding:6px 10px; border-radius:4px; margin-top:4px; }
.std .tag { grid-column:1 / -1; font-size:.7rem; color:var(--std); font-weight:700; letter-spacing:.05em; text-transform:uppercase; }
mark { background:var(--hl); color:inherit; }
@media (max-width:640px) { .row, .std { grid-template-columns:minmax(0,1fr); } }
.empty { color:var(--muted); padding:20px; }
</style>
<main>
<header style="display:flex;flex-direction:column;gap:10px">
  <h1>The Last Bell <small>Posledný zvonec in English · every text, Slovak and English side by side</small></h1>
  <p class="intro">Translated by Claude with a fixed glossary (British English, the dry Polda humour rebuilt for English), then checked on this computer with LanguageTool en‑GB; nothing went to an online service. Slovak is grey on the left, English on the right. Green boxes are the less revealing versions used on Standard and Hard. Voices stay Slovak with English subtitles.</p>
  <div class="stats" id="stats"></div>
</header>
<div class="bar">
  <input id="q" type="search" placeholder="Search Slovak or English…" aria-label="Search">
  <select id="era" aria-label="Era"><option value="">All eras</option></select>
  <select id="kind" aria-label="Kind"><option value="">All kinds</option><option value="dialogue">Dialogue</option><option value="look">Looks and items</option><option value="journal">Goals, journal, quests</option><option value="label">Names and labels</option><option value="ui">Menus and hints</option></select>
</div>
<div id="list" style="display:flex;flex-direction:column;gap:14px"></div>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
const G = JSON.parse(document.getElementById("data").textContent);
const esc = s => (s || "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;"}[c]));
const total = G.reduce((n, g) => n + g.rows.length, 0), std = G.reduce((n, g) => n + g.rows.filter(r => r.stdsk).length, 0);
document.getElementById("stats").innerHTML = `<span><b>${total.toLocaleString("en-GB")}</b> texts</span><span><b>${std}</b> with a Standard/Hard version</span><span><b>${G.length}</b> scenes and groups</span>`;
const eraSel = document.getElementById("era");
[...new Set(G.map(g => g.era))].forEach(e => eraSel.insertAdjacentHTML("beforeend", `<option>${esc(e)}</option>`));
function hi(text, q) { const t = esc(text); if (!q) return t; const i = t.toLowerCase().indexOf(q); return i < 0 ? t : t.slice(0, i) + "<mark>" + t.slice(i, i + q.length) + "</mark>" + t.slice(i + q.length); }
function render() {
  const q = document.getElementById("q").value.trim().toLowerCase(), era = eraSel.value, kind = document.getElementById("kind").value;
  const out = [];
  let shown = 0;
  for (const g of G) {
    if (era && g.era !== era) continue;
    const rows = g.rows.filter(r => (!kind || r.t === kind) && (!q || (r.sk + " " + r.en + " " + (r.stdsk || "") + " " + (r.stden || "") + " " + r.s + " " + r.k).toLowerCase().includes(q)));
    if (!rows.length) continue;
    shown += rows.length;
    if (shown > 2500 && !q) { out.push(`<p class="empty">Showing the first 2,500 texts – pick an era or search to see the rest.</p>`); break; }
    out.push(`<section class="group"><h2><span class="era">${esc(g.era)}</span>${esc(g.title || g.section)}<span class="sec">${g.title ? esc(g.section) : ""}</span></h2>` +
      rows.map(r => `<div class="row"><div class="who">${esc(r.s)} <code>${esc(r.k)}</code></div><div class="sk">${hi(r.sk, q)}</div><div>${hi(r.en, q)}</div>` +
        (r.stdsk ? `<div class="std"><span class="tag">Standard / Hard</span><div class="sk">${hi(r.stdsk, q)}</div><div>${hi(r.stden, q)}</div></div>` : "") + `</div>`).join("") + `</section>`);
  }
  document.getElementById("list").innerHTML = out.join("") || `<p class="empty">No text matches.</p>`;
}
let timer; document.getElementById("q").addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(render, 150); });
eraSel.addEventListener("change", render); document.getElementById("kind").addEventListener("change", render);
render();
</script>
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "docs/translation/review.html")
    a = ap.parse_args()
    data = json.dumps(build(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = PAGE.replace("__DATA__", data)
    a.out.write_text(page, encoding="utf-8")
    print(f"wrote {a.out} ({len(page.encode()) // 1024} KB)")


if __name__ == "__main__":
    main()
