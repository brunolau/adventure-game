"""Listening page of the English dub: docs/voice/en.html from art/voice/en/manifest.json.

Self-contained (inline CSS and JS, the data embedded). The recordings are played by relative path from the game folders
(../../src/game/assets/voice_en/ and, for the Slovak original beside it, ../../src/game/assets/voice/), so the page is
opened locally from the repository. Sections: summary, what to listen to first (flagged takes), one sample per speaker,
then every line by era and room with "play room".

usage: python en_dub_page.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import en_dub as E  # noqa: E402
import voice_lib as V  # noqa: E402

PAGE = V.ROOT / "docs/voice/en.html"
ERAS = [("2020", "2020 – Chorvatsky Grob, Cierna Voda, Dubravka"), ("1995", "1995 – Bratislava"), ("1960", "1962 – Ivanka pri Dunaji"),
        ("1982", "1982 – Dubravka"), ("2035", "2035 – Jasna"), ("epilog", "Epilogue")]

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>English Dub</title>
<style>
:root{--bg:#f6f4ef;--panel:#fffdf8;--ink:#1f1d1a;--muted:#6b665d;--line:#e2ddd2;--accent:#9a4a1c;--accent-ink:#fff;
--warn:#a06400;--chip:#efe9dd;--now:#fbe9d6;--fx:#2c5a7a;--irony:#6a3d8a}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#171513;--panel:#201d1a;--ink:#ece6dc;--muted:#a59d90;
--line:#36312b;--accent:#e08a50;--accent-ink:#1a1310;--warn:#e6b45c;--chip:#2b2722;--now:#3a2a1d;--fx:#8cc3e8;--irony:#c9a2e6;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1040px;margin:0 auto;padding-block:24px 90px;padding-inline:16px;overflow-wrap:anywhere}
h1{font-size:26px;margin:0 0 4px;text-wrap:balance}h2{font-size:20px;margin:38px 0 10px}h3{font-size:16px;margin:0}
.sub{color:var(--muted);margin:0 0 16px;max-width:70ch}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:14px 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.kpi b{display:block;font-size:20px;font-variant-numeric:tabular-nums}.kpi span{color:var(--muted);font-size:13px}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);padding:10px 0;border-bottom:1px solid var(--line);display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.bar label{color:var(--muted);font-size:13px;display:flex;gap:6px;align-items:center}
select,button,input{font:inherit;color:inherit}
select,input[type=search]{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:5px 8px;max-width:100%}
button.play{min-width:38px;height:34px;border-radius:17px;border:1px solid var(--line);background:var(--panel);cursor:pointer;flex:none;font-size:12px;font-weight:600;padding:0 9px}
button.play:hover{border-color:var(--accent)}
button.play.on{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
button.sk{color:var(--muted);font-weight:400}
button.scene{border:0;background:var(--accent);color:var(--accent-ink);border-radius:8px;padding:6px 12px;cursor:pointer;font-weight:600}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;margin:12px 0;overflow:hidden}
.head{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:11px 14px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.head small{color:var(--muted)}
.row{display:flex;gap:10px;align-items:flex-start;padding:7px 14px}
.row+.row{border-top:1px solid var(--line)}
.row.now{background:var(--now)}
.who{flex:none;width:112px;font-weight:600;font-size:13px;padding-top:6px}
.who small{display:block;color:var(--muted);font-weight:400}
.txt{flex:1;min-width:0}.txt .sk{color:var(--muted);font-size:13px}
.txt .heard{color:var(--warn);font-size:13px}
.tag{display:inline-block;font-size:11px;border-radius:9px;padding:0 7px;margin-left:6px;background:var(--chip);color:var(--muted);vertical-align:middle}
.tag.flag{color:var(--warn);border:1px solid var(--warn);background:none}.tag.fx{color:var(--fx)}.tag.irony{color:var(--irony)}
.id{color:var(--muted);font-size:11px;font-family:ui-monospace,Consolas,monospace}
table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:6px 8px;border-top:1px solid var(--line);vertical-align:top}
.scroll{overflow-x:auto}
@media (max-width:560px){.who{width:76px}}
</style>
</head>
<body>
<main>
<h1>English dub</h1>
<p class="sub">Every line of the Slovak dub, spoken in British English by the same voice per character. “EN” plays the English take, “SK” the Slovak original beside it. Open this file from the repository folder; it plays the recordings from <code>src/game/assets/</code>.</p>
<div class="kpis" id="kpis"></div>
<div class="bar">
 <label>Show <select id="fGroup"><option value="">everything</option><option value="dialogue">dialogue</option><option value="looks">looks and items</option><option value="std">Standard / Hard variants</option></select></label>
 <label>Speaker <select id="fSpeaker"><option value="">all</option></select></label>
 <label><input type="checkbox" id="fFlag"> flagged only</label>
 <label><input type="search" id="fText" placeholder="search text or id"></label>
</div>
<h2>Listen to these first</h2>
<p class="sub">Takes whose automatic transcript still differs from the script after one retake, has an added word, or is unusually slow or fast. Many are the transcription, not the voice; the ear decides.</p>
<div id="flags"></div>
<h2>Voices</h2>
<div class="card scroll"><table id="cast"></table></div>
<h2>All lines</h2>
<div id="all"></div>
</main>
<script>
const DATA = /*DATA*/;
const EN = "../../src/game/assets/voice_en/", SK = "../../src/game/assets/voice/";
const audio = new Audio(); let current = null, queue = [];
function stop(){ audio.pause(); if(current){current.classList.remove("on"); current.closest(".row")?.classList.remove("now");} current=null; }
function play(btn, chain){ if(current===btn){ stop(); queue=[]; return; } stop(); if(!chain) queue=[];
  current=btn; btn.classList.add("on"); btn.closest(".row")?.classList.add("now");
  audio.src = btn.dataset.src; audio.play().catch(()=>{ stop(); }); }
audio.addEventListener("ended", ()=>{ stop(); const next=queue.shift(); if(next && next.isConnected && next.offsetParent!==null) play(next,true); else queue=[]; });
document.addEventListener("click", e=>{ const b=e.target.closest("button.play"); if(b){ play(b,false); return; }
  const s=e.target.closest("button.scene"); if(s){ const rows=[...s.closest(".card").querySelectorAll("button.play.en")].filter(x=>x.offsetParent!==null); queue=rows.slice(1); if(rows[0]){ stop(); play(rows[0],true);} } });
const enc = f => f.split("/").map(encodeURIComponent).join("/");
function row(l){ const d=document.createElement("div"); d.className="row"; d.dataset.group=l.group; d.dataset.speaker=l.speaker; d.dataset.flag=l.flag?"1":"";
  d.dataset.text=(l.text+" "+l.sk+" "+l.line_id).toLowerCase();
  const who=document.createElement("div"); who.className="who"; who.textContent=DATA.names[l.speaker]||l.speaker; const v=document.createElement("small"); v.textContent=l.voice; who.append(v);
  const t=document.createElement("div"); t.className="txt"; const en=document.createElement("div"); en.textContent=l.text;
  for(const [c,x] of [["flag",l.flag],["fx",l.fx],["irony",l.irony?"dry irony":""],["",l.alias_of?"same take as "+l.alias_of:""]]) if(x){ const s=document.createElement("span"); s.className="tag "+c; s.textContent=x; en.append(s); }
  const sk=document.createElement("div"); sk.className="sk"; sk.textContent=l.sk; t.append(en,sk);
  if(l.flag && l.heard){ const h=document.createElement("div"); h.className="heard"; h.textContent="heard: "+l.heard; t.append(h); }
  const id=document.createElement("div"); id.className="id"; id.textContent=l.line_id; t.append(id);
  const b=document.createElement("button"); b.className="play en"; b.textContent="EN"; b.dataset.src=EN+enc(l.file); b.title="Play the English take";
  d.append(who,t,b);
  if(l.sk_file){ const s=document.createElement("button"); s.className="play sk"; s.textContent="SK"; s.dataset.src=SK+enc(l.sk_file); s.title="Play the Slovak original"; d.append(s); }
  return d; }
const k=document.getElementById("kpis");
for(const [n,label] of DATA.kpis){ const d=document.createElement("div"); d.className="kpi"; const b=document.createElement("b"); b.textContent=n; const s=document.createElement("span"); s.textContent=label; d.append(b,s); k.append(d); }
const fl=document.getElementById("flags"); const fc=document.createElement("div"); fc.className="card";
for(const l of DATA.lines.filter(l=>l.flag && !l.alias_of)) fc.append(row(l)); fl.append(fc);
const cast=document.getElementById("cast"); cast.innerHTML="<tr><th>Character</th><th>Voice</th><th>Lines</th><th>Sample</th></tr>";
for(const c of DATA.cast){ const tr=document.createElement("tr"); for(const x of [c.who,c.voice,c.lines]){ const td=document.createElement("td"); td.textContent=x; tr.append(td);}
  const td=document.createElement("td"); const b=document.createElement("button"); b.className="play en"; b.textContent="EN"; b.dataset.src=EN+enc(c.sample); td.append(b); tr.append(td); cast.append(tr); }
const all=document.getElementById("all");
for(const era of DATA.eras){ const h=document.createElement("h2"); h.textContent=era.label; all.append(h);
  for(const sc of era.scenes){ const card=document.createElement("div"); card.className="card"; const head=document.createElement("div"); head.className="head";
    const h3=document.createElement("h3"); h3.textContent=sc.name; const sm=document.createElement("small"); sm.textContent=" "+sc.id+" · "+sc.lines.length+" lines"; h3.append(sm);
    const pb=document.createElement("button"); pb.className="scene"; pb.textContent="Play room"; head.append(h3,pb); card.append(head);
    for(const i of sc.lines) card.append(row(DATA.lines[i])); all.append(card); } }
const sp=document.getElementById("fSpeaker"); for(const c of DATA.cast){ const o=document.createElement("option"); o.value=c.speaker; o.textContent=c.who; sp.append(o); }
function filter(){ const g=fGroup.value, s=fSpeaker.value, f=fFlag.checked, q=fText.value.trim().toLowerCase();
  for(const r of document.querySelectorAll(".row")) r.hidden = (g&&r.dataset.group!==g)||(s&&r.dataset.speaker!==s)||(f&&!r.dataset.flag)||(q&&!r.dataset.text.includes(q));
  for(const c of document.querySelectorAll("#all .card")) c.hidden = ![...c.querySelectorAll(".row")].some(r=>!r.hidden); }
for(const el of [fGroup,fSpeaker,fFlag,fText]) el.addEventListener("input", filter);
</script>
</body>
</html>
"""


def main() -> None:
    man = json.loads((E.OUT / "manifest.json").read_text(encoding="utf-8"))
    rows = E.english()
    sk_alias = json.loads((V.ROOT / "src/game/assets/voice/aliases.json").read_text(encoding="utf-8"))
    sk_dir = V.ROOT / "src/game/assets/voice"
    lines = []
    for l in man["lines"]:
        sk_stem = sk_alias.get(l["line_id"], l["line_id"])
        lines.append({k: l.get(k) for k in ("line_id", "group", "speaker", "voice", "text", "sk", "fx", "irony", "alias_of",
                                             "file", "flag", "heard")}
                     | {"era": str(l["era"]) if l["era"] is not None else "epilog", "scene": l["scene"] or "",
                        "sk_file": f"{sk_stem}.ogg" if (sk_dir / f"{sk_stem}.ogg").exists() else None})
    names = {sp: c["who"] for sp, c in E.CAST.items()}
    cast = []
    for sp, c in E.CAST.items():
        mine = [l for l in lines if l["speaker"] == sp and not l["alias_of"]]
        if not mine:
            continue
        sample = next((l for l in mine if 60 <= len(l["text"]) <= 160 and not l["flag"]), mine[0])
        cast.append({"speaker": sp, "who": c["who"], "voice": c["voice"], "lines": sum(1 for l in lines if l["speaker"] == sp),
                     "sample": sample["file"]})
    eras = []
    for era, label in ERAS:
        scenes, order = {}, []
        for i, l in enumerate(lines):
            if l["era"] != era:
                continue
            if l["scene"] not in scenes:
                scenes[l["scene"]] = []
                order.append(l["scene"])
            scenes[l["scene"]].append(i)
        if order:
            eras.append({"label": label, "scenes": [{"id": s, "name": rows.get(f"room.{s}.name", ("", s))[1] or s, "lines": scenes[s]}
                                                    for s in order]})
    placed = {i for e in eras for s in e["scenes"] for i in s["lines"]}
    rest = [i for i in range(len(lines)) if i not in placed]
    if rest:
        eras.append({"label": "Everywhere", "scenes": [{"id": "", "name": "Lines without a room", "lines": rest}]})
    c = man["counts"]
    kpis = [(f"{c['keys']:,}", "spoken keys"), (f"{c['takes']:,}", "recordings"), (f"{c['minutes'] / 60:.1f} h", "of English audio"),
            (str(len(cast)), "speaking roles"), (str(c["retaken"]), "retaken once"), (str(c["flagged"]), "to listen to first")]
    data = {"lines": lines, "names": names, "cast": cast, "eras": eras, "kpis": kpis}
    html = HTML.replace("/*DATA*/", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    PAGE.write_text(html, encoding="utf-8", newline="\n")
    print("page:", PAGE.relative_to(V.ROOT), f"{PAGE.stat().st_size / 1e6:.1f} MB,", len(lines), "lines,", len(cast), "roles")


if __name__ == "__main__":
    main()
