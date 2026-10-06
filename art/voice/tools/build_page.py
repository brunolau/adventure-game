"""Build the listening page docs/voice/trial.html from art/voice/trial/manifest.json and art/voice/ab/ab_results.json.

The page is self-contained (inline CSS/JS, data embedded) and references the OGG files by relative paths:
../../art/voice/trial/<line_id>.ogg (chosen model), ../../art/voice/takes/<model>/<line_id>.ogg (other models),
../../art/voice/ab/<model>/<line_id>.ogg (A/B test).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402
from casting import MODELS  # noqa: E402

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
@media (max-width:620px){.who{width:78px;font-size:12px}.row{gap:8px;padding:7px 10px}}
</style>
</head>
<body>
<main>
<h1>Voice trial: 2020 prologue</h1>
<p class="sub">AI voiceover test for the dialogue of the first part (Chorvátsky Grob and Čierna Voda, S01–S10, CS01). Synthetic stock voices; nothing is in the game yet.</p>
<div class="kpis" id="kpis"></div>
<div class="bar">
  <label for="model">Takes from</label><select id="model"></select>
  <button class="ghost" id="stop">Stop</button>
  <label><input type="checkbox" id="showstt"> show the speech-to-text check</label>
</div>
<h2>Scenes in play order</h2>
<div id="scenes"></div>
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
function src(id, model){model=model||sel.value; return model===D.chosen ? '../../art/voice/trial/'+enc(id)+'.ogg' : '../../art/voice/takes/'+model+'/'+enc(id)+'.ogg'}
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
function kpis(){const k=document.getElementById('kpis'); k.innerHTML='';
  D.kpis.forEach(([v,l])=>{const d=document.createElement('div');d.className='kpi';d.innerHTML='<b></b><span></span>';d.querySelector('b').textContent=v;d.querySelector('span').textContent=l;k.appendChild(d)})}
function render(){
  const box=document.getElementById('scenes'); box.innerHTML='';
  const per=D.perModel[sel.value]||{};
  D.scenes.forEach(sc=>{
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
      if(info.ok===false){const g=document.createElement('span');g.className='tag warn';g.textContent='check';m.appendChild(g)}
      t.appendChild(m);
      if(stt.checked && info.s){const s=document.createElement('div');s.className='stt';s.textContent='Scribe: '+info.s+'  |  Whisper: '+info.w+'  (WER '+info.ws+' / '+info.ww+')';t.appendChild(s)}
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
kpis(); render();
</script>
</body>
</html>
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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
    per_model = {}
    for k in model_keys:
        pm = {}
        for l in man["lines"]:
            f = V.ROOT / "art/voice/raw" / k / f"{l['line_id']}.json"
            if f.exists():
                r = json.loads(f.read_text(encoding="utf-8"))
                b = r["best"]
                pm[l["line_id"]] = {"d": r["duration_s"], "ok": b["score"] <= 0.15, "s": b["stt_scribe"], "w": b["stt_wizper"],
                                    "ws": b["wer_scribe"]["wer"], "ww": b["wer_wizper"]["wer"]}
        per_model[k] = pm
    # casting
    briefs = json.loads((V.ROOT / "art/voice/tools/briefs.json").read_text(encoding="utf-8"))
    cast = []
    for sp in ["ADAM", "ELA", "DANA", "MIRA20", "ROMAN", "LENKA", "JOZEF", "SYSTEM"]:
        row = [NAMES[sp], briefs[sp]]
        for k in model_keys:
            v = MODELS[k][1][sp]
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
    kpis = [
        (MODEL_LABEL[chosen], "chosen model"),
        (str(man["count"]), "lines voiced"),
        (f"{c['audio_s'] / 60:.1f} min", "of dialogue"),
        (pct(c["wer_scribe"]), "word error (STT check)"),
        (f"${man['spend_voice_usd']:.2f}", "spent on the trial"),
        (f"≈ ${est[2500]:.0f}", "for ~2,500 game lines"),
    ]
    data = {"chosen": chosen, "names": NAMES,
            "models": [{"key": k, "label": MODEL_LABEL[k]} for k in model_keys],
            "scenes": scenes, "perModel": per_model, "cast": cast,
            "ab": {"models": ab_models, "labels": MODEL_LABEL, "lines": [ab_lines[k] for k in ab_lines], "summary": ab_summary},
            "statModels": [{"key": k, "label": MODEL_LABEL[k]} for k in model_keys], "statRows": stat_rows,
            "costHtml": cost_html, "kpis": kpis}
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(HTML.replace("__DATA__", blob), encoding="utf-8")
    print("wrote", PAGE, len(blob))


if __name__ == "__main__":
    main()
