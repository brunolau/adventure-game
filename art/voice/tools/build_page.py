"""Build the listening page docs/voice/trial.html from art/voice/trial/manifest.json and art/voice/ab/ab_results.json.

The page is self-contained (inline CSS/JS, data embedded) and references the OGG files by relative paths:
../../art/voice/trial/<line_id>.ogg (chosen model), ../../art/voice/takes/<model>/<line_id>.ogg (other models),
../../art/voice/ab/<model>/<line_id>.ogg (A/B test).
Recast 2026-10-06: the regenerated lines have a before/after toggle (before = ../../art/voice/takes/gemini_v1/),
plus a recast section (casting v1 -> v2, measured voice features, the voice audition, irony lines, flags).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402
from casting import GEMINI, GEMINI_V2, MODELS, SK  # noqa: E402

PAGE = V.ROOT / "docs/voice/trial.html"
NAMES = {"ADAM": "Adam", "ELA": "Ela", "DANA": "Dana", "MIRA20": "Mira (babka)", "ROMAN": "Roman", "LENKA": "Lenka",
         "JOZEF": "pán Jozef", "SYSTEM": "ZVON (zariadenie)"}
MODEL_LABEL = {"gemini": "Gemini 3.8 Flash TTS", "minimax": "MiniMax Speech 2.8 HD", "eleven": "ElevenLabs Eleven v4"}

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voice Trial Prologue</title>
<style>
:root{--bg:#f6f4ef;--panel:#fffdf8;--ink:#1f1d1a;--muted:#6b665d;--line:#e2ddd2;--accent:#9a4a1c;--accent-ink:#fff;
--ok:#2f6b3a;--warn:#a06400;--chip:#efe9dd;--now:#fbe9d6;--phone:#2c5a7a}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#171513;--panel:#201d1a;--ink:#ece6dc;--muted:#a59d90;
--line:#36312b;--accent:#e08a50;--accent-ink:#1a1310;--ok:#7cc48a;--warn:#e6b45c;--chip:#2b2722;--now:#3a2a1d;--phone:#8cc3e8}}
:root[data-theme="dark"]{--bg:#171513;--panel:#201d1a;--ink:#ece6dc;--muted:#a59d90;--line:#36312b;--accent:#e08a50;
--accent-ink:#1a1310;--ok:#7cc48a;--warn:#e6b45c;--chip:#2b2722;--now:#3a2a1d;--phone:#8cc3e8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 80px;overflow-wrap:anywhere}
html,body{overflow-x:hidden}.tw{max-width:100%}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:36px 0 10px}h3{font-size:16px;margin:0}
.sub{color:var(--muted);margin:0 0 18px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.kpi b{display:block;font-size:20px}.kpi span{color:var(--muted);font-size:13px}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);padding:10px 0;border-bottom:1px solid var(--line);display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.bar label{color:var(--muted);font-size:13px}
select,button{font:inherit;color:inherit}
select{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:5px 8px}
button.play{width:34px;height:34px;border-radius:50%;border:1px solid var(--line);background:var(--panel);cursor:pointer;flex:none;display:grid;place-items:center}
button.play:hover{border-color:var(--accent)}
button.play svg{width:14px;height:14px;fill:var(--ink)}
button.play.on{background:var(--accent);border-color:var(--accent)}button.play.on svg{fill:var(--accent-ink)}
button.scene{border:0;background:var(--accent);color:var(--accent-ink);border-radius:8px;padding:6px 12px;cursor:pointer;font-weight:600}
button.ghost{border:1px solid var(--line);background:var(--panel);border-radius:8px;padding:6px 12px;cursor:pointer}
.scenecard{background:var(--panel);border:1px solid var(--line);border-radius:12px;margin:14px 0;overflow:hidden}
.scenehead{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:12px 14px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.scenehead small{color:var(--muted)}
.block{padding:6px 14px 2px;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.row{display:flex;gap:10px;align-items:flex-start;padding:7px 14px}
.row.now{background:var(--now)}
.who{flex:none;width:118px;font-weight:600;font-size:13px;padding-top:6px}
.txt{flex:1;min-width:0;padding-top:5px}
.meta{color:var(--muted);font-size:12px}
.tag{display:inline-block;font-size:11px;border-radius:999px;padding:0 7px;margin-left:6px;background:var(--chip);color:var(--muted)}
.tag.phone{color:var(--phone)}.tag.warn{color:var(--warn)}
table{border-collapse:collapse;width:100%;background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:14px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:12px;color:var(--muted);font-weight:600}
.tw{overflow-x:auto}
.abcell{display:flex;gap:8px;align-items:flex-start}
.stt{font-size:12px;color:var(--muted)}
.good{color:var(--ok)}.bad{color:var(--warn)}
p.note{color:var(--muted);font-size:14px}
.seg{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:8px;overflow:hidden;background:var(--panel)}
.seg span{padding:5px 8px;color:var(--muted);font-size:13px;border-right:1px solid var(--line)}
.seg button{border:0;background:transparent;padding:5px 10px;cursor:pointer}
.seg button.on{background:var(--accent);color:var(--accent-ink);font-weight:600}
.tag.recast{color:var(--accent)}.tag.irony{color:var(--ok)}
button.cmp{border:1px solid var(--line);background:var(--panel);border-radius:999px;padding:0 8px;margin-left:6px;font-size:11px;cursor:pointer;color:var(--muted)}
button.cmp:hover{border-color:var(--accent);color:var(--ink)}
.recastbox{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:14px 0}
.recastbox p{margin:6px 0}
ul.flags{margin:6px 0 0;padding-left:20px}ul.flags li{margin:3px 0}
code{font-size:13px;background:var(--chip);padding:0 4px;border-radius:4px}
#recastCast td:nth-child(2),#recastCast td:nth-child(3),#audition td:nth-child(n+3):nth-child(-n+6),#recastFeat td{white-space:nowrap}
@media (max-width:620px){.who{width:78px;font-size:12px}.row{gap:8px;padding:7px 10px}}
</style>
</head>
<body>
<main>
<h1>Voice trial: 2020 prologue</h1>
<p class="sub">AI voiceover test for the dialogue of the first part (Chorvátsky Grob and Čierna Voda, S01–S10, CS01). Synthetic stock voices. <b>Recast 2026-10-06</b>: Adam and Roman swapped voices, the four women were recast and the dry or sarcastic lines got a touch of irony; use <i>Recast lines: Before / After</i> to compare.</p>
<div class="kpis" id="kpis"></div>
<div class="bar">
  <label for="model">Takes from</label><select id="model"></select>
  <button class="ghost" id="stop">Stop</button>
  <span class="seg" role="group" aria-label="Recast lines"><span>Recast lines</span><button id="vAfter" class="on" aria-pressed="true">After</button><button id="vBefore" aria-pressed="false">Before</button></span>
  <label><input type="checkbox" id="onlyRecast"> only recast lines</label>
  <label><input type="checkbox" id="onlyIrony"> only dry-irony lines</label>
  <label><input type="checkbox" id="showstt"> show the speech-to-text check</label>
</div>
<h2>Recast 2026-10-06</h2>
<div class="recastbox" id="recastIntro"></div>
<div class="recastbox"><b>Flagged for listening</b><ul class="flags" id="flags"></ul></div>
<h2>Scenes in play order</h2>
<div id="scenes"></div>
<h2>Recast details</h2>
<div class="tw"><table id="recastCast"></table></div>
<p class="note" id="featNote" style="margin-top:12px"></p>
<div class="tw"><table id="recastFeat"></table></div>
<h3 style="margin-top:18px">Voice audition for the women</h3>
<p class="note">One real line per role, spoken by each candidate stock voice with the role's new direction. The chosen voices are in bold.</p>
<div class="tw"><table id="audition"></table></div>
<h2>Casting</h2>
<div class="tw"><table id="cast"></table></div>
<h2>A/B test: same 6 lines, 3 models</h2>
<p class="note">Each take was normalised to the same loudness. The two transcripts under each take are the speech-to-text round trip (ElevenLabs Scribe v2 / Whisper v3 large); WER = word error rate against the script.</p>
<div class="tw"><table id="ab"></table></div>
<h2>Whole-prologue comparison of the two finalists</h2>
<div class="tw"><table id="stats"></table></div>
<h2>Cost</h2>
<div id="cost"></div>
</main>
<script>
const D = __DATA__;
const PLAY='<svg viewBox="0 0 16 16"><path d="M4 2l10 6-10 6z"/></svg>', STOP='<svg viewBox="0 0 16 16"><rect x="3" y="3" width="10" height="10"/></svg>';
const audio = new Audio(); let queue=[], curBtn=null, curRow=null;
function enc(id){return encodeURIComponent(id).replace(/%2F/g,'/')}
let ver='after';
function isRecast(id){return !!D.recast.lines[id]}
function srcV(id, v){return v==='before' && isRecast(id) ? '../../art/voice/takes/gemini_v1/'+enc(id)+'.ogg' : '../../art/voice/trial/'+enc(id)+'.ogg'}
function src(id, model){model=model||sel.value; return model===D.chosen ? srcV(id, ver) : '../../art/voice/takes/'+model+'/'+enc(id)+'.ogg'}
function mark(btn,row,on){ if(btn){btn.classList.toggle('on',on);btn.innerHTML=on?STOP:PLAY;} if(row) row.classList.toggle('now',on); }
function stopAll(){queue=[];audio.pause();mark(curBtn,curRow,false);curBtn=curRow=null}
function playOne(url,btn,row,next){ mark(curBtn,curRow,false); curBtn=btn; curRow=row; mark(btn,row,true);
  audio.src=url; audio.onended=()=>{mark(btn,row,false); curBtn=curRow=null; if(next) setTimeout(next,280)}; audio.play().catch(()=>{mark(btn,row,false)}); }
function runQueue(){ if(!queue.length) return; const [u,b,r]=queue.shift(); if(r) r.scrollIntoView({block:'nearest',behavior:'smooth'}); playOne(u,b,r,runQueue) }
function btn(onclick){const b=document.createElement('button');b.className='play';b.innerHTML=PLAY;b.setAttribute('aria-label','play');b.onclick=onclick;return b}
const sel=document.getElementById('model');
D.models.forEach(m=>{const o=document.createElement('option');o.value=m.key;o.textContent=m.label+(m.key===D.chosen?' (chosen)':'');sel.appendChild(o)});
sel.value=D.chosen;
try{const s=localStorage.getItem('voiceTrialModel'); if(s && D.models.some(m=>m.key===s)) sel.value=s}catch(e){}
sel.onchange=()=>{stopAll(); try{localStorage.setItem('voiceTrialModel',sel.value)}catch(e){} render()};
document.getElementById('stop').onclick=stopAll;
const stt=document.getElementById('showstt'); stt.onchange=render;
const onlyR=document.getElementById('onlyRecast'), onlyI=document.getElementById('onlyIrony'); onlyR.onchange=render; onlyI.onchange=render;
const bA=document.getElementById('vAfter'), bB=document.getElementById('vBefore');
function paintVer(){bA.classList.toggle('on',ver==='after'); bB.classList.toggle('on',ver==='before');
  bA.setAttribute('aria-pressed',String(ver==='after')); bB.setAttribute('aria-pressed',String(ver==='before'))}
function setVer(v){ver=v; paintVer(); try{localStorage.setItem('voiceTrialVer',v)}catch(e){} stopAll(); render()}
bA.onclick=()=>setVer('after'); bB.onclick=()=>setVer('before');
try{const v=localStorage.getItem('voiceTrialVer'); if(v==='before'||v==='after') ver=v}catch(e){}
paintVer();
function kpis(){const k=document.getElementById('kpis'); k.innerHTML='';
  D.kpis.forEach(([v,l])=>{const d=document.createElement('div');d.className='kpi';d.innerHTML='<b></b><span></span>';d.querySelector('b').textContent=v;d.querySelector('span').textContent=l;k.appendChild(d)})}
function render(){
  const box=document.getElementById('scenes'); box.innerHTML='';
  const isChosen=sel.value===D.chosen;
  const per=(isChosen && ver==='before') ? Object.assign({}, D.perModel[D.chosen], D.perModel.gemini_v1) : (D.perModel[sel.value]||{});
  D.scenes.forEach(sc0=>{
    const sc=Object.assign({}, sc0, {lines: sc0.lines.filter(l=>(!onlyR.checked||isRecast(l.id)) && (!onlyI.checked||D.recast.irony[l.id]))});
    if(!sc.lines.length) return;
    const card=document.createElement('section'); card.className='scenecard';
    const head=document.createElement('div'); head.className='scenehead';
    const dur=sc.lines.reduce((a,l)=>a+((per[l.id]||{}).d||0),0);
    head.innerHTML='<div><h3></h3><small></small></div>'; head.querySelector('h3').textContent=sc.room+' · '+sc.name;
    head.querySelector('small').textContent=sc.lines.length+' lines · '+dur.toFixed(0)+' s';
    const pb=document.createElement('button'); pb.className='scene'; pb.textContent='Play whole scene'; head.appendChild(pb);
    card.appendChild(head);
    const rows=[]; let lastBlock=null;
    sc.lines.forEach(l=>{
      if(l.block!==lastBlock){const b=document.createElement('div');b.className='block';b.textContent=l.blockLabel;card.appendChild(b);lastBlock=l.block}
      const row=document.createElement('div'); row.className='row';
      const info=per[l.id]||{};
      const b=btn(()=>{ if(curBtn===b){stopAll();return} queue=[]; playOne(src(l.id),b,row)});
      const who=document.createElement('div'); who.className='who'; who.textContent=D.names[l.sp]||l.sp;
      const t=document.createElement('div'); t.className='txt';
      const p=document.createElement('div'); p.textContent=l.text; t.appendChild(p);
      const m=document.createElement('div'); m.className='meta'; m.textContent=l.id+' · '+(info.d||0).toFixed(1)+' s';
      if(l.phone){const g=document.createElement('span');g.className='tag phone';g.textContent='phone EQ';m.appendChild(g)}
      if(isRecast(l.id) && isChosen){const g=document.createElement('span');g.className='tag recast';g.textContent=ver==='before'?'v1 (before)':'recast';m.appendChild(g)}
      if(D.recast.irony[l.id]){const g=document.createElement('span');g.className='tag irony';g.title=D.recast.irony[l.id];g.textContent='dry irony';m.appendChild(g)}
      if(info.ok===false){const g=document.createElement('span');g.className='tag warn';g.textContent='check';if(info.f)g.title=info.f;m.appendChild(g)}
      if(isRecast(l.id) && isChosen){const c=document.createElement('button');c.className='cmp';const other=ver==='after'?'before':'after';
        c.textContent='play '+other; c.setAttribute('aria-label','play the '+other+' version');
        c.onclick=()=>{queue=[]; playOne(srcV(l.id,other),b,row)}; m.appendChild(c)}
      t.appendChild(m);
      if(stt.checked && info.s){const s=document.createElement('div');s.className='stt';
        s.textContent=(info.w==null ? 'Scribe: '+info.s+'  (WER '+info.ws+')' : 'Scribe: '+info.s+'  |  Whisper: '+info.w+'  (WER '+info.ws+' / '+info.ww+')')+(info.f?'  · '+info.f:'');
        t.appendChild(s)}
      row.append(b,who,t); card.appendChild(row); rows.push([l,b,row]);
    });
    pb.onclick=()=>{stopAll(); queue=rows.map(([l,b,r])=>[src(l.id),b,r]); runQueue()};
    box.appendChild(card);
  });
}
function table(id, head, rows){const t=document.getElementById(id); t.innerHTML='';
  const tr=document.createElement('tr'); head.forEach(h=>{const th=document.createElement('th');th.textContent=h;tr.appendChild(th)}); t.appendChild(tr);
  rows.forEach(r=>{const tr=document.createElement('tr'); r.forEach(c=>{const td=document.createElement('td'); if(c instanceof Node) td.appendChild(c); else td.textContent=c; tr.appendChild(td)}); t.appendChild(tr)})}
table('cast',['Character','Brief (VOICES.md)'].concat(D.models.map(m=>m.label)), D.cast);
(function(){
  const rows=D.ab.lines.map(l=>{
    const first=document.createElement('div'); first.innerHTML='<b></b><div></div>'; first.querySelector('b').textContent=D.names[l.sp]||l.sp; first.querySelector('div').textContent=l.text;
    const cells=D.ab.models.map(mk=>{const r=l.takes[mk]; const c=document.createElement('div'); if(!r){c.textContent='-';return c}
      c.className='abcell'; const b=btn(()=>{ if(curBtn===b){stopAll();return} queue=[]; playOne('../../art/voice/ab/'+mk+'/'+enc(l.id)+'.ogg',b,null)});
      const s=document.createElement('div'); s.className='stt';
      s.innerHTML='<div></div><div></div><div></div>'; s.children[0].textContent=r.voice+' · '+r.d.toFixed(1)+' s · '+r.cps+' chars/s';
      s.children[1].textContent='Scribe: '+r.s+' (WER '+r.ws+')'; s.children[2].textContent='Whisper: '+r.w+' (WER '+r.ww+')';
      c.append(b,s); return c});
    return [first].concat(cells)});
  table('ab',['Line'].concat(D.ab.models.map(m=>D.ab.labels[m])), rows);
  const n=document.createElement('p'); n.className='note'; n.textContent=D.ab.summary; document.getElementById('ab').after(n);
})();
table('stats',['Measure'].concat(D.statModels.map(m=>m.label)), D.statRows);
document.getElementById('cost').innerHTML=D.costHtml;
document.getElementById('recastIntro').innerHTML=D.recast.introHtml;
table('recastCast',['Character','v1 trial voice','v2 recast voice','v2 direction (after the shared Slovak pronunciation prompt)'], D.recast.cast);
document.getElementById('featNote').textContent=D.recast.featNote;
table('recastFeat',['Character','Median pitch v1 → v2','Pitch range v1 → v2','Timbre (spectral centroid) v1 → v2','Pace v1 → v2'], D.recast.feat);
(function(){const rows=D.recast.audition.map(a=>{const c=document.createElement('div');c.className='abcell';
  const b=btn(()=>{ if(curBtn===b){stopAll();return} queue=[]; playOne('../../art/voice/recast/audition/'+enc(a.tag)+'.ogg',b,null)});
  const s=document.createElement('div'); s.textContent=a.voice+(a.chosen?' (chosen)':''); if(a.chosen) s.style.fontWeight='600'; c.append(b,s);
  return [a.role,c,a.f0+' Hz',a.range+' st',a.cent+' Hz',a.cps+' chars/s',a.stt]});
  table('audition',['Role','Voice','Pitch','Range','Timbre','Pace','Scribe transcript'],rows)})();
(function(){const ul=document.getElementById('flags'); Object.entries(D.recast.flags).forEach(([id,why])=>{const li=document.createElement('li');
  const c=document.createElement('code'); c.textContent=id; li.append(c, document.createTextNode(' — '+why)); ul.appendChild(li)});
  if(!Object.keys(D.recast.flags).length){ul.innerHTML='<li>none</li>'}})();
kpis(); render();
</script>
</body>
</html>
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


ORDER = ["ADAM", "ROMAN", "ELA", "DANA", "MIRA20", "LENKA", "JOZEF", "SYSTEM"]
CHOSEN_AUDITION = {"LENKA.Leda", "ELA.Despina", "DANA.Vindemiatrix", "MIRA20.Gacrux.pace2"}


def recast_data(man: dict, rc: dict) -> dict:
    lines = {l["line_id"]: l for l in man["lines"]}
    recast_lines = {lid: True for lid, l in lines.items() if l.get("version") == 2}
    irony = {d["line_id"]: d["kind"] for d in rc.get("delivery_lines", [])}
    flags = {f["line_id"]: f["why"] for f in rc.get("flagged", [])}
    cast = []
    for sp in ORDER:
        v1, v2 = GEMINI[sp], GEMINI_V2[sp]
        same = v1 == v2
        cast.append([NAMES[sp], v1["voice"], v2["voice"] + (" (unchanged)" if same else ""),
                     "unchanged" if same else v2["style"].replace(SK, "")])
    f1 = json.loads((V.ROOT / "art/voice/recast/v1_features.json").read_text(encoding="utf-8"))
    f2p = V.ROOT / "art/voice/recast/v2_features.json"
    f2 = json.loads(f2p.read_text(encoding="utf-8")) if f2p.exists() else {}
    feat = []
    for sp in ["ADAM", "ROMAN", "LENKA", "ELA", "DANA", "MIRA20"]:
        a, b = f1[sp], f2.get(sp)
        if not b:
            continue
        feat.append([NAMES[sp], f"{a['f0_median_hz']:.0f} → {b['f0_median_hz']:.0f} Hz",
                     f"{a['f0_range_semitones']:.1f} → {b['f0_range_semitones']:.1f} semitones",
                     f"{a['centroid_hz']:.0f} → {b['centroid_hz']:.0f} Hz", f"{a['cps']:.1f} → {b['cps']:.1f} chars/s"])
    aud = []
    af = V.ROOT / "art/voice/recast/audition/audition.json"
    for r in (json.loads(af.read_text(encoding="utf-8")) if af.exists() else []):
        tag = f"{r['role']}.{r['voice']}" + (".pace2" if r.get("variant") else "")
        label = r["voice"] + (" (final direction)" if r.get("variant") else (" (first direction: too slow)" if tag == "MIRA20.Gacrux" else ""))
        f = r["features"]
        aud.append({"tag": tag, "role": NAMES[r["role"]], "voice": label, "chosen": tag in CHOSEN_AUDITION,
                    "f0": round(f["f0_median_hz"]), "range": f["f0_range_semitones"], "cent": f["centroid_hz"],
                    "cps": r["measure"]["chars_per_s"], "stt": r["stt_scribe"]})
    summ = f2.get("_summary", {})
    n_flag_meaning = sum(1 for w in flags.values() if not w.startswith("listen"))
    intro = (
        "<p>After listening to the trial the owner asked for three changes. <b>1.</b> Adam and Roman swap voices: Adam now "
        "speaks with Roman's former voice (Achird) and a relaxed, friendly direction close to Roman's; Roman got Adam's former "
        "voice (Iapetus). <b>2.</b> The four women were recast so they differ clearly in pitch, timbre and pace "
        "(audition below). <b>3.</b> Lines read as dry irony or sarcasm got one extra sentence in the style prompt: "
        f"<i>{esc(rc.get('irony_direction', ''))}</i></p>"
        f"<p>Only lines whose voice or delivery changed were regenerated: <b>{rc.get('regenerated', 0)}</b> of {man['count']} "
        f"(all lines of Adam, Roman, Ela, Dana, Mira and Lenka, plus Jozef's three ironic lines); "
        f"<b>{len(irony)}</b> lines carry the irony direction. Each new take was checked once by ElevenLabs Scribe v2 "
        f"(no Whisper this time); {rc.get('retaken', 0)} lines whose transcript differed got one retake. "
        f"{len(flags)} lines are flagged for listening ({n_flag_meaning} where the transcript still differs after the retake). "
        "Same post-processing as the trial (phone EQ for Mira outside S06, −16 LUFS).</p>"
        f"<p>Measured effect of the irony direction: those lines are a little slower ({summ.get('irony_mean_cps', '?')} vs "
        f"{summ.get('plain_mean_cps', '?')} chars/s) with a slightly longer beat before the punchline; no line has a pause "
        "over 1.4 s. Whether it is a <i>tiny</i> bit and not more can only be judged by ear: switch "
        "<i>Recast lines</i> to Before / After, or use <i>play before</i> on a line. The before files are frozen in "
        "<code>art/voice/takes/gemini_v1/</code>.</p>"
        f"<p>Recast cost: <b>${rc.get('spend_usd', 0):.2f}</b> (audition ${rc.get('spend_usd_audition', 0):.2f}, TTS + Scribe "
        "for the regenerated lines and retakes the rest). The A/B test and the model comparison further down are from the v1 trial.</p>")
    note = ("Median per character over the regenerated takes, measured on the raw files (before phone EQ): pitch by YIN, "
            "timbre as spectral centroid. In v1 Lenka, Ela and Dana sat within 2 semitones of each other (153–170 Hz) and "
            "Ela and Dana had the same pitch.")
    return {"lines": recast_lines, "irony": irony, "flags": flags, "cast": cast, "feat": feat, "featNote": note,
            "audition": aud, "introHtml": intro}


def main() -> None:
    man = json.loads((V.ROOT / "art/voice/trial/manifest.json").read_text(encoding="utf-8"))
    ab = json.loads((V.ROOT / "art/voice/ab/ab_results.json").read_text(encoding="utf-8"))
    chosen = man["chosen_key"]
    stats = man["model_stats"]
    model_keys = [chosen] + [k for k in stats if k != chosen]
    # scenes
    scenes, idx = [], {}
    for l in man["lines"]:
        if l["scene"] not in idx:
            idx[l["scene"]] = len(scenes)
            scenes.append({"room": l["scene"][:3], "name": l["scene_name"], "lines": []})
        scenes[idx[l["scene"]]]["lines"].append({"id": l["line_id"], "sp": l["speaker"], "text": l["text"],
                                                  "block": l["block"], "blockLabel": l["block_label"],
                                                  "phone": l["phone_eq"]})
    recast_ids = [l["line_id"] for l in man["lines"] if l.get("version") == 2]

    def v1_info(k: str, lid: str) -> dict | None:
        f = V.ROOT / "art/voice/raw" / k / f"{lid}.json"
        if not f.exists():
            return None
        r = json.loads(f.read_text(encoding="utf-8"))
        b = r["best"]
        return {"d": r["duration_s"], "ok": b["score"] <= 0.15, "s": b["stt_scribe"], "w": b["stt_wizper"],
                "ws": b["wer_scribe"]["wer"], "ww": b["wer_wizper"]["wer"]}
    per_model = {}
    for k in model_keys:
        pm = {}
        for l in man["lines"]:
            if k == chosen and l.get("version") == 2:   # recast take: Scribe check only
                st = l["stt"]
                pm[l["line_id"]] = {"d": l["duration_s"], "ok": st["ok"], "s": st["scribe_v2"], "w": None,
                                    "ws": st["wer_scribe"], "ww": None, "f": st.get("flag")}
                continue
            info = v1_info(k, l["line_id"])
            if info:
                pm[l["line_id"]] = info
        per_model[k] = pm
    per_model["gemini_v1"] = {lid: v1_info("gemini", lid) for lid in recast_ids}
    # casting
    briefs = json.loads((V.ROOT / "art/voice/tools/briefs.json").read_text(encoding="utf-8"))
    cast = []
    for sp in ["ADAM", "ELA", "DANA", "MIRA20", "ROMAN", "LENKA", "JOZEF", "SYSTEM"]:
        row = [NAMES[sp], briefs[sp]]
        for k in model_keys:
            v = (GEMINI_V2 if k == "gemini" else MODELS[k][1])[sp]
            if k == "gemini" and GEMINI[sp]["voice"] != v["voice"]:
                row.append(f"{v['voice']} + style prompt (v1: {GEMINI[sp]['voice']})")
                continue
            extra = ", ".join(f"{a} {b}" for a, b in v.items() if a not in ("voice", "style"))
            row.append(v["voice"] + (f" ({extra})" if extra else "") + (" + style prompt" if "style" in v else ""))
        cast.append(row)
    # A/B
    ab_models = ["gemini", "eleven", "minimax"]
    ab_lines = {}
    for r in ab:
        e = ab_lines.setdefault(r["line_id"], {"id": r["line_id"], "sp": r["speaker"], "text": r["text"], "takes": {}})
        e["takes"][r["model_key"]] = {"voice": r["voice"], "d": r["final_s"], "cps": r["measure"]["chars_per_s"],
                                      "s": r["stt_scribe"], "w": r["stt_wizper"], "ws": r["wer_scribe"]["wer"],
                                      "ww": r["wer_wizper"]["wer"]}
    agg = {}
    for mk in ab_models:
        rs = [r for r in ab if r["model_key"] == mk]
        words = sum(r["wer_scribe"]["ref_words"] for r in rs) or 1
        agg[mk] = (sum(r["wer_scribe"]["wer"] * r["wer_scribe"]["ref_words"] for r in rs) / words,
                   sum(r["wer_wizper"]["wer"] * r["wer_wizper"]["ref_words"] for r in rs) / words)
    ab_summary = "Word error rate over the 6 lines (Scribe / Whisper): " + "; ".join(
        f"{MODEL_LABEL[m]} {agg[m][0]:.1%} / {agg[m][1]:.1%}" for m in ab_models) + \
        ". ElevenLabs v4 had real mispronunciations heard by both STT models (\"Dana ďu\", \"Ve pondelok\") and dropped out; " \
        "Gemini and MiniMax tied, so both voiced the whole prologue (table below)."
    # stats table
    def pct(x): return f"{x:.1%}"
    rows_def = [
        ("Lines", lambda s: str(s["lines"])),
        ("WER Scribe v2 (best take)", lambda s: pct(s["wer_scribe"])),
        ("WER Whisper v3 (best take)", lambda s: pct(s["wer_wizper"])),
        ("WER Scribe / Whisper, first take only", lambda s: f"{pct(s['first_take_wer_scribe'])} / {pct(s['first_take_wer_wizper'])}"),
        ("WER ignoring diacritics (Scribe / Whisper)", lambda s: f"{pct(s['wer_scribe_nodiac'])} / {pct(s['wer_wizper_nodiac'])}"),
        ("Lines transcribed verbatim by Scribe", lambda s: f"{s['lines_exact_scribe']} of {s['lines']}"),
        ("Retakes needed", lambda s: str(s["retakes"])),
        ("Lines still flagged 'check'", lambda s: str(len(s["doubtful"]))),
        ("Mean speaking rate", lambda s: f"{s['mean_chars_per_s']} chars/s"),
        ("Longest pause inside a line", lambda s: f"{s['max_pause_s']} s"),
        ("Clipped lines", lambda s: str(s["clipped_lines"])),
        ("Total audio", lambda s: f"{s['audio_s'] / 60:.1f} min"),
        ("TTS cost incl. retakes", lambda s: f"${s['usd_tts']:.2f}"),
        ("Price", lambda s: f"${V.TTS_PRICE[s['model']]:.3f} / 1000 chars"),
    ]
    stat_rows = [[name] + [f(stats[k]) for k in model_keys] for name, f in rows_def]
    c = stats[chosen]
    per_line = c["usd_tts"] / c["lines"]
    price = V.TTS_PRICE[c["model"]]
    avg_chars = c["chars"] / c["lines"]
    stt_per_line = (man["spend_voice_usd"] - sum(s["usd_tts"] for s in stats.values())) / max(1, sum(s["lines"] for s in stats.values()))
    est = {n: n * avg_chars / 1000 * price * 1.15 for n in (1090, 2500)}
    cost_html = (
        f"<p>Spent on this trial (all models, A/B, retakes and STT checks): <b>${man['spend_voice_usd']:.2f}</b> "
        f"(logged in art/spend-log.csv under voice/).</p>"
        f"<p>{esc(MODEL_LABEL[chosen])}: ${price:.3f} per 1000 characters; a prologue line averages {avg_chars:.0f} characters, "
        f"so <b>about ${per_line:.4f} per line</b> including retakes (STT check about ${stt_per_line:.4f} per line and model).</p>"
        f"<p>Whole game estimate at the same line length, +15 % retakes: 1,090 lines ≈ <b>${est[1090]:.2f}</b>, "
        f"~2,500 lines (longer dialogues) ≈ <b>${est[2500]:.2f}</b>. The automatic STT check costs about $0.0005 per line "
        f"with Scribe v2 (≈ $1.30 for 2,500 lines); the Whisper second opinion is logged at a conservative $0.002 per call "
        f"(≈ $5 for 2,500 lines, real compute is lower). Money is not the constraint; the time to listen and fix lines is.</p>")
    rc = man.get("recast", {})
    kpis = [
        (MODEL_LABEL[chosen], "chosen model"),
        (str(man["count"]), "lines voiced"),
        (str(rc.get("regenerated", 0)), "lines recast 2026-10-06"),
        (str(len(rc.get("delivery_lines", []))), "lines with a touch of dry irony"),
        (f"${man['spend_voice_usd'] + rc.get('spend_usd', 0):.2f}", "spent (trial + recast)"),
        (f"≈ ${est[2500]:.0f}", "for ~2,500 game lines"),
    ]
    recast = recast_data(man, rc)
    data = {"chosen": chosen, "names": NAMES,
            "models": [{"key": k, "label": MODEL_LABEL[k]} for k in model_keys],
            "scenes": scenes, "perModel": per_model, "cast": cast,
            "ab": {"models": ab_models, "labels": MODEL_LABEL, "lines": [ab_lines[k] for k in ab_lines], "summary": ab_summary},
            "statModels": [{"key": k, "label": MODEL_LABEL[k]} for k in model_keys], "statRows": stat_rows,
            "costHtml": cost_html, "kpis": kpis, "recast": recast}
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(HTML.replace("__DATA__", blob), encoding="utf-8")
    print("wrote", PAGE, len(blob))


if __name__ == "__main__":
    main()
