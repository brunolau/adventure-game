"""Build the listening page docs/voice/full.html from art/voice/full/manifest.json and casting.json.

Self-contained (inline CSS/JS, data embedded); the OGG files are referenced by relative paths
(../../art/voice/full/<line_id>.ogg, prologue: ../../art/voice/trial/<line_id>.ogg), so open it locally.
Sections: summary, the look bubbles of 2026-10-08 („Pohľady a predmety“, flagged first), the lines re-voiced on 2026-10-07 (before/now) with the narrator audition, flagged lines, casting table (family voices, ages), the child/age audition, then every era
and scene in play order with "play scene" (plays the scene's lines in sequence).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402

FULL = V.ROOT / "art/voice/full"
PAGE = V.ROOT / "docs/voice/full.html"
ERA_LABEL = {"2020": "2020 – Chorvátsky Grob, Čierna Voda, Dúbravka", "1995": "1995 – Bratislava",
             "1960": "1962 – Ivanka pri Dunaji", "2035": "2035 – Jasná", "1982": "1982 – Dúbravka",
             "epilog": "Epilóg"}

HTML = r"""<!doctype html>
<html lang="sk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Full Voice-over</title>
<style>
:root{--bg:#f6f4ef;--panel:#fffdf8;--ink:#1f1d1a;--muted:#6b665d;--line:#e2ddd2;--accent:#9a4a1c;--accent-ink:#fff;
--ok:#2f6b3a;--warn:#a06400;--chip:#efe9dd;--now:#fbe9d6;--fx:#2c5a7a;--irony:#6a3d8a}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#171513;--panel:#201d1a;--ink:#ece6dc;--muted:#a59d90;
--line:#36312b;--accent:#e08a50;--accent-ink:#1a1310;--ok:#7cc48a;--warn:#e6b45c;--chip:#2b2722;--now:#3a2a1d;--fx:#8cc3e8;--irony:#c9a2e6}}
:root[data-theme="dark"]{--bg:#171513;--panel:#201d1a;--ink:#ece6dc;--muted:#a59d90;--line:#36312b;--accent:#e08a50;
--accent-ink:#1a1310;--ok:#7cc48a;--warn:#e6b45c;--chip:#2b2722;--now:#3a2a1d;--fx:#8cc3e8;--irony:#c9a2e6}
*{box-sizing:border-box}
html,body{overflow-x:hidden}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1040px;margin:0 auto;padding:24px 16px 90px;overflow-wrap:anywhere}
h1{font-size:26px;margin:0 0 4px}h2{font-size:20px;margin:38px 0 10px}h3{font-size:16px;margin:0}
.sub{color:var(--muted);margin:0 0 16px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:14px 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.kpi b{display:block;font-size:20px;font-variant-numeric:tabular-nums}.kpi span{color:var(--muted);font-size:13px}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);padding:10px 0;border-bottom:1px solid var(--line);display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.bar label{color:var(--muted);font-size:13px;display:flex;gap:6px;align-items:center}
select,button,input{font:inherit;color:inherit}
select{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:5px 8px;max-width:100%}
button.play{width:34px;height:34px;border-radius:50%;border:1px solid var(--line);background:var(--panel);cursor:pointer;flex:none;display:grid;place-items:center}
button.play:hover{border-color:var(--accent)}
button.play svg{width:14px;height:14px;fill:var(--ink)}
button.play.on{background:var(--accent);border-color:var(--accent)}button.play.on svg{fill:var(--accent-ink)}
button.scene{border:0;background:var(--accent);color:var(--accent-ink);border-radius:8px;padding:6px 12px;cursor:pointer;font-weight:600}
button.ghost{border:1px solid var(--line);background:var(--panel);border-radius:8px;padding:6px 12px;cursor:pointer}
.era{margin-top:34px}
.scenecard{background:var(--panel);border:1px solid var(--line);border-radius:12px;margin:12px 0;overflow:hidden}
.scenehead{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:11px 14px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.scenehead small{color:var(--muted)}
.block{padding:6px 14px 2px;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.row{display:flex;gap:10px;align-items:flex-start;padding:7px 14px}
.row.now{background:var(--now)}
.who{flex:none;width:118px;font-weight:600;font-size:14px;padding-top:6px}
.who small{display:block;font-weight:400;color:var(--muted);font-size:12px}
.txt{flex:1;min-width:0;padding-top:5px}
.tags{display:flex;gap:6px;flex-wrap:wrap;margin-top:3px}
.tag{font-size:11.5px;border-radius:999px;padding:1px 8px;background:var(--chip);color:var(--muted)}
.tag.flag{background:none;border:1px solid var(--warn);color:var(--warn)}
.tag.irony{background:none;border:1px solid var(--irony);color:var(--irony)}
.tag.fx{background:none;border:1px solid var(--fx);color:var(--fx)}
.stt{color:var(--muted);font-size:12.5px;margin-top:2px}
.tw{max-width:100%;overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:12px;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.03em}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.fam{font-size:12px;color:var(--muted)}
.dir{font-size:12.5px;color:var(--muted);max-width:420px}
.hidden{display:none}
.note{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:10px 0}
@media (max-width:640px){.who{width:84px}.row{padding:7px 10px}.dir{max-width:none}}
</style>
</head>
<body>
<main>
<h1>Posledný zvonec – celý dabing</h1>
<p class="sub">Every spoken line of the game, by era and scene in play order. AI voices (Gemini 3.8 Flash TTS, stock voices,
Slovak direction), checked once by ElevenLabs Scribe v2. Open this file locally: the audio is read from
<code>art/voice/full/</code> and, for the approved prologue, <code>art/voice/trial/</code>.</p>
<div class="kpis" id="kpis"></div>

<div class="bar">
  <label>Era <select id="fEra"><option value="">all</option></select></label>
  <label>Speaker <select id="fSpk"><option value="">all</option></select></label>
  <label><input type="checkbox" id="fFlag"> only flagged</label>
  <label><input type="checkbox" id="fIrony"> only dry irony</label>
  <label><input type="checkbox" id="fNew"> hide prologue</label>
  <button class="ghost" id="stop">Stop</button>
</div>

<h2 id="looks">Pohľady a predmety (8. 10. 2026)</h2>
<p class="sub">Everything Adam says in a look bubble: room looks, looks that change later in the story, inventory item
descriptions, locked exits and routes, the puzzle lines and „Tadiaľto neprejdem.“ Adam's voice (Achird) with his direction;
a touch of dry irony only on the clearly ironic ones. The same sentence is one take shared by every key that shows it.
The flagged takes come first. Not voiced: the place names shown when looking at an open exit.</p>
<div class="kpis" id="lkpis"></div>
<div class="bar" style="position:static">
  <label>Kind <select id="lKind"><option value="">all</option></select></label>
  <label><input type="checkbox" id="lFlag"> only flagged</label>
  <label><input type="checkbox" id="lIrony"> only dry irony</label>
</div>
<h3 style="margin-top:14px">Flagged (listen first)</h3>
<div class="scenecard" id="lookflags"></div>
<div id="lookkinds"></div>

<h2 id="r2">New on 7 October 2026: a female narrator and „Pri LEALe“</h2>
<p class="sub">The owner asked for a female narrator with a more interested, engaged tone (it was the male voice Charon), and
S69 is now called „Pri LEALe“. These lines were voiced again. Fero's dialect is unchanged. Play "before" and "now" to compare.</p>
<div class="tw"><table id="r2t"><thead><tr><th>line</th><th>text now</th><th>before</th><th>now</th><th>why</th></tr></thead><tbody></tbody></table></div>
<h3 style="margin-top:18px">Narrator audition</h3>
<p class="sub">Three female stock voices with the new narrator direction, on the game's two narrator lines and one narrator-style
caption (epilogue shot 5, audition only), two takes each. Median pitch, pitch range (10th–90th percentile), and the
Scribe transcript. The chosen voice is in bold.</p>
<div class="tw"><table id="naud"><thead><tr><th>voice</th><th>line</th><th class="num">pitch Hz</th><th class="num">range st</th><th>play</th><th>Scribe</th></tr></thead><tbody></tbody></table></div>

<h2 id="flags">Flagged lines (listen first)</h2>
<p class="sub">The transcript differed after the one allowed retake, a filler word was heard, or the pace was unusual. Meaning
differences come first.</p>
<div class="scenecard" id="flagcard"></div>

<h2>Casting</h2>
<p class="sub">One stock voice per person; the same person at another age keeps the same voice with an age direction. Ages as
in game.json / VOICES.md. Every direction starts with the shared Slovak pronunciation prompt (not repeated here).</p>
<div class="tw"><table id="cast"><thead><tr><th>speaker</th><th>who</th><th>age</th><th>voice</th><th class="num">lines</th>
<th class="num">irony</th><th>eras</th><th>direction</th></tr></thead><tbody></tbody></table></div>
<div class="note" id="castnote"></div>

<h2>Audition: children, young Mira, Zuzana</h2>
<p class="sub">Two real lines per role, each candidate voice with the role's direction; median pitch (YIN) and Scribe check.
Chosen voice in bold.</p>
<div class="tw"><table id="aud"><thead><tr><th>role</th><th>voice</th><th class="num">pitch Hz</th><th>play</th><th>Scribe</th></tr></thead><tbody></tbody></table></div>

<div id="eras"></div>
</main>
<audio id="player" preload="none"></audio>
<script>
const MAN = __MANIFEST__;
const CAST = __CASTING__;
const AUD = __AUDITION__;
const NAUD = __NAUDITION__;
const ERA_LABEL = __ERAS__;
const PLAY = '<svg viewBox="0 0 16 16"><path d="M4 2l10 6-10 6z"/></svg>';
const STOPI = '<svg viewBox="0 0 16 16"><rect x="3" y="3" width="10" height="10"/></svg>';
const $ = s => document.querySelector(s);
const player = $('#player');
let queue = [], current = null;
function src(file){
  const parts = file.startsWith('../trial/') ? ['..','..','art','voice','trial', file.slice(9)] : ['..','..','art','voice','full', file];
  return parts.map(p => p === '..' ? p : encodeURIComponent(p)).join('/');
}
function esc(s){return String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function name(spk){return CAST[spk] ? CAST[spk].who : spk;}
function mark(id, on){document.querySelectorAll('[data-id="'+CSS.escape(id)+'"]').forEach(r => {
  r.classList.toggle('now', on); const b = r.querySelector('button.play'); if (b){b.classList.toggle('on', on); b.innerHTML = on ? STOPI : PLAY;}});}
function playOne(l){
  if (current) mark(current.line_id, false);
  current = l; mark(l.line_id, true);
  player.src = src(l.file); player.play().catch(() => next());
}
function next(){ if (current) mark(current.line_id, false); current = null; if (queue.length) playOne(queue.shift()); }
player.addEventListener('ended', () => setTimeout(next, 250));
function stop(){ queue = []; player.pause(); if (current) mark(current.line_id, false); current = null; }
$('#stop').onclick = stop;
function rowHtml(l, showScene){
  const tags = [];
  if (l.source !== 'full') tags.push('<span class="tag">prologue' + (l.source.includes('re-rendered') ? ' · device colour' : '') + '</span>');
  if (l.delivery) tags.push('<span class="tag irony">dry irony</span>');
  if (l.fx) tags.push('<span class="tag fx">' + esc({phone:'telefón', radio:'hovor / kanál', tape:'kazeta 1995', device:'zariadenie'}[l.fx] || l.fx) + '</span>');
  if (l.stt && l.stt.flag) tags.push('<span class="tag flag">check: ' + esc(l.stt.flag) + '</span>');
  if (l.alias_of) tags.push('<span class="tag">same take as ' + esc(l.alias_of) + '</span>');
  if (l.retaken) tags.push('<span class="tag">retake</span>');
  tags.push('<span class="tag">' + esc(l.voice) + (l.duration_s ? ' · ' + l.duration_s.toFixed(1) + ' s' : '') + '</span>');
  if (showScene) tags.push('<span class="tag">' + esc(l.scene + ' ' + l.scene_name) + '</span>');
  tags.push('<span class="tag">' + esc(l.line_id) + '</span>');
  const stt = (l.stt && l.stt.scribe_v2 && l.stt.flag) ? '<div class="stt">Scribe: ' + esc(l.stt.scribe_v2) + '</div>' : '';
  return '<div class="row" data-id="' + esc(l.line_id) + '" data-era="' + esc(l.era) + '" data-spk="' + esc(l.speaker) +
    '" data-flag="' + (l.stt && l.stt.flag ? 1 : 0) + '" data-irony="' + (l.delivery ? 1 : 0) + '" data-new="' + (l.source === 'full' ? 1 : 0) + '">' +
    '<button class="play" title="play">' + PLAY + '</button><div class="who">' + esc(name(l.speaker).split(' (')[0]) +
    '<small>' + esc(l.speaker) + '</small></div><div class="txt">' + esc(l.text) + '<div class="tags">' + tags.join('') + '</div>' + stt + '</div></div>';
}
const byId = {}; MAN.lines.forEach(l => byId[l.line_id] = l);
// KPIs
const c = MAN.counts;
const k = [[c.lines, 'spoken lines in the game'], [c.new, 'newly voiced'], [c.prologue, 'prologue (approved trial)'],
  [c.minutes_new + ' min', 'new audio'], [c.flagged, 'flagged to listen'], [c.retaken, 'retakes'], [c.irony_new, 'dry-irony lines (new)'],
  ['$' + MAN.spend_usd.toFixed(2), 'spend incl. audition']];
$('#kpis').innerHTML = k.map(([b, s]) => '<div class="kpi"><b>' + esc(b) + '</b><span>' + esc(s) + '</span></div>').join('');
// flagged first: meaning differences, then fillers / timing
const flagged = MAN.lines.filter(l => l.stt && l.stt.flag).sort((a, b) =>
  ((b.stt.meaning_errors || []).length > 0) - ((a.stt.meaning_errors || []).length > 0));
$('#flagcard').innerHTML = (flagged.length ? '' : '<div class="row">No flagged lines.</div>') + flagged.map(l => rowHtml(l, true)).join('');
// casting
const order = Object.keys(CAST);
$('#cast tbody').innerHTML = order.map(s => { const x = CAST[s];
  return '<tr><td><b>' + esc(s) + '</b>' + (x.family ? '<div class="fam">' + esc(x.family) + '</div>' : '') + '</td><td>' + esc(x.who) + '</td><td>' + esc(x.age ?? '') +
  '</td><td>' + esc(x.voice) + '</td><td class="num">' + x.lines + '</td><td class="num">' + x.irony_lines + '</td><td>' +
  esc(Object.entries(x.eras).map(([e, n]) => e + ' (' + n + ')').join(', ')) + '</td><td class="dir">' +
  esc(x.style.replace(/^Speak natural, native Slovak.*?Read the text verbatim\. /, '')) + '</td></tr>'; }).join('');
const fam = {}; order.forEach(s => { const f = CAST[s].family; if (f) (fam[f] = fam[f] || []).push(s + ' ' + (CAST[s].age ?? '') + ' → ' + CAST[s].voice); });
$('#castnote').innerHTML = '<b>Same person, other age:</b> ' + Object.entries(fam).map(([f, v]) => esc(f) + ': ' + esc(v.join(', '))).join(' · ') +
  '<br><b>Voices shared by two speakers in one scene:</b> ' + (Object.keys(MAN.voice_clashes_in_scene).length ? esc(JSON.stringify(MAN.voice_clashes_in_scene)) : 'none');
// re-voiced 2026-10-07 and the narrator audition
$('#r2t tbody').innerHTML = MAN.lines.filter(l => l.revoiced).map(l => '<tr><td><b>' + esc(l.speaker) + '</b><div class="fam">' + esc(l.line_id) +
  '</div></td><td>' + esc(l.text) + (l.stt && l.stt.flag ? '<div class="stt">check: ' + esc(l.stt.flag) + '</div>' : '') + '</td><td>' +
  (l.revoiced.before_file ? '<button class="play aud" title="before (' + esc(l.revoiced.before_voice) + ')" data-src="../../art/voice/full/before_r2/' +
  encodeURIComponent(l.line_id) + '.ogg">' + PLAY + '</button><div class="fam">' + esc(l.revoiced.before_voice) + '</div>' : '') +
  '</td><td><button class="play aud" title="now" data-src="' + src(l.file) + '">' + PLAY + '</button><div class="fam">' + esc(l.voice) +
  '</div></td><td class="dir">' + esc(l.revoiced.why) + '</td></tr>').join('');
$('#naud tbody').innerHTML = NAUD.map(r => { const chosen = CAST.NARRATOR && CAST.NARRATOR.voice === r.voice;
  return '<tr><td>' + (chosen ? '<b>' + esc(r.voice) + '</b>' : esc(r.voice)) + '</td><td class="fam">' + esc(r.line_id) + ' · take ' + r.k +
  '</td><td class="num">' + r.f0.toFixed(0) + '</td><td class="num">' + r.range.toFixed(1) + '</td><td><button class="play aud" data-src="../../art/voice/full/audition/narrator/' +
  encodeURIComponent(r.file) + '">' + PLAY + '</button></td><td class="stt">' + esc(r.stt) + '</td></tr>'; }).join('');
// audition
const audBody = AUD.map(r => { const chosen = CAST[r.role] && CAST[r.role].voice === r.voice;
  return '<tr><td>' + esc(r.role) + '</td><td>' + (chosen ? '<b>' + esc(r.voice) + '</b>' : esc(r.voice)) + '</td><td class="num">' + r.f0.toFixed(0) +
  '</td><td><button class="play aud" data-src="../../art/voice/full/audition/' + encodeURIComponent(r.tag) + '.ogg">' + PLAY + '</button></td><td class="stt">' + esc(r.stt) + '</td></tr>'; });
$('#aud tbody').innerHTML = audBody.join('');
document.querySelectorAll('button.aud').forEach(b => b.onclick = () => { stop(); player.src = b.dataset.src; player.play(); });
// look bubbles (2026-10-08)
const LOOKS = MAN.looks || [];
const LC = MAN.counts_looks || null;
const KIND_ORDER = ['look', 'look_changed', 'item', 'locked_exit', 'locked_route', 'puzzle', 'system'];
const lookTakes = LOOKS.filter(l => !l.alias_of);
const usedBy = {}; LOOKS.forEach(l => { const t = l.alias_of || l.line_id; (usedBy[t] = usedBy[t] || []).push(l); });
lookTakes.forEach(l => byId[l.line_id] = l);
if (LC) {
  $('#lkpis').innerHTML = [[LC.keys, 'keys voiced'], [LC.takes, 'distinct takes'], [LC.minutes + ' min', 'audio'],
    [LC.flagged, 'flagged'], [LC.retaken, 'retakes'], [LC.irony, 'dry irony'], ['$' + LC.spend_logged_usd.toFixed(2), 'spend (logged)']]
    .map(([b, s]) => '<div class="kpi"><b>' + esc(b) + '</b><span>' + esc(s) + '</span></div>').join('');
} else { $('#looks').classList.add('hidden'); }
function lookRow(l){
  const keys = usedBy[l.line_id] || [l];
  const tags = [];
  tags.push('<span class="tag">' + esc(l.kind_label) + '</span>');
  if (l.delivery) tags.push('<span class="tag irony">dry irony</span>');
  if (l.stt && l.stt.flag) tags.push('<span class="tag flag">check: ' + esc(l.stt.flag) + '</span>');
  if (l.retaken) tags.push('<span class="tag">retake</span>');
  tags.push('<span class="tag">' + esc(l.voice) + ' · ' + l.duration_s.toFixed(1) + ' s</span>');
  if (l.scene) tags.push('<span class="tag">' + esc(l.scene + ' ' + (l.scene_name || '')) + '</span>');
  const keyList = keys.length > 1 ? '<div class="stt">' + keys.length + ' keys: ' + esc(keys.map(k => k.line_id).join(', ')) + '</div>'
    : '<div class="stt">' + esc(l.line_id) + (l.label ? ' · ' + esc(l.label) : '') + '</div>';
  const stt = (l.stt && l.stt.flag) ? '<div class="stt">Scribe: ' + esc(l.stt.scribe_v2) + '</div>' : '';
  return '<div class="row" data-id="' + esc(l.line_id) + '" data-kind="' + esc(l.kind) + '" data-flag="' + (l.stt && l.stt.flag ? 1 : 0) +
    '" data-irony="' + (l.delivery ? 1 : 0) + '"><button class="play" title="play">' + PLAY + '</button><div class="txt">' + esc(l.text) +
    '<div class="tags">' + tags.join('') + '</div>' + keyList + stt + '</div></div>';
}
const lflagged = lookTakes.filter(l => l.stt && l.stt.flag).sort((a, b) =>
  ((b.stt.meaning_errors || []).length > 0) - ((a.stt.meaning_errors || []).length > 0));
$('#lookflags').innerHTML = (lflagged.length ? '' : '<div class="row">No flagged look lines.</div>') + lflagged.map(lookRow).join('');
let lhtml = '';
KIND_ORDER.forEach(k => { const ls = lookTakes.filter(l => l.kind === k); if (!ls.length) return;
  const nkeys = LOOKS.filter(l => l.kind === k).length, mins = ls.reduce((a, l) => a + l.duration_s, 0) / 60;
  lhtml += '<div class="scenecard" data-kind="' + k + '"><div class="scenehead"><div><h3>' + esc(ls[0].kind_label) + '</h3><small>' + nkeys +
    ' keys · ' + ls.length + ' takes · ' + mins.toFixed(1) + ' min</small></div><button class="scene">Play all</button></div>';
  let sc = null;
  ls.forEach(l => { if (l.scene !== sc && (k === 'look' || k === 'look_changed' || k === 'locked_exit')) { sc = l.scene;
    lhtml += '<div class="block">' + esc((l.scene || '') + ' · ' + (l.scene_name || '')) + '</div>'; } lhtml += lookRow(l); });
  lhtml += '</div>'; });
$('#lookkinds').innerHTML = lhtml;
KIND_ORDER.forEach(k => { const l = lookTakes.find(x => x.kind === k); if (!l) return;
  const o = document.createElement('option'); o.value = k; o.textContent = l.kind_label; $('#lKind').appendChild(o); });
function applyLookFilters(){
  const k = $('#lKind').value;
  document.querySelectorAll('#lookkinds .row, #lookflags .row[data-id]').forEach(r => r.classList.toggle('hidden',
    !((!k || r.dataset.kind === k) && (!$('#lFlag').checked || r.dataset.flag === '1') && (!$('#lIrony').checked || r.dataset.irony === '1'))));
  document.querySelectorAll('#lookkinds .scenecard').forEach(c => c.classList.toggle('hidden', !c.querySelector('.row:not(.hidden)')));
}
['lKind', 'lFlag', 'lIrony'].forEach(id => $('#' + id).addEventListener('change', applyLookFilters));
// eras and scenes
const eras = []; const scenes = {};
MAN.lines.forEach(l => { const e = String(l.era); if (!eras.includes(e)) eras.push(e);
  const key = e + '|' + l.scene; (scenes[key] = scenes[key] || {era: e, scene: l.scene, name: l.scene_name, lines: []}).lines.push(l); });
let html = '';
eras.forEach(e => {
  html += '<section class="era" data-era="' + esc(e) + '"><h2>' + esc(ERA_LABEL[e] || e) + '</h2>';
  Object.values(scenes).filter(s => s.era === e).forEach(s => {
    const n = s.lines.length, mins = s.lines.reduce((a, l) => a + (l.duration_s || 0), 0) / 60;
    html += '<div class="scenecard" data-scene="' + esc(e + '|' + s.scene) + '"><div class="scenehead"><div><h3>' + esc(s.scene + ' · ' + s.name) +
      '</h3><small>' + n + ' lines · ' + mins.toFixed(1) + ' min</small></div><button class="scene">Play scene</button></div>';
    let block = null;
    s.lines.forEach(l => { if (l.block !== block) { block = l.block; html += '<div class="block">' + esc(l.block_label + ' · ' + l.block) + '</div>'; }
      html += rowHtml(l, false); });
    html += '</div>';
  });
  html += '</section>';
});
$('#eras').innerHTML = html;
['fEra', 'fSpk'].forEach(id => { const sel = $('#' + id);
  const vals = id === 'fEra' ? eras : Object.keys(CAST);
  vals.forEach(v => { const o = document.createElement('option'); o.value = v; o.textContent = id === 'fEra' ? (ERA_LABEL[v] || v) : v + ' – ' + CAST[v].who; sel.appendChild(o); }); });
function visible(r){
  const era = $('#fEra').value, spk = $('#fSpk').value;
  return (!era || r.dataset.era === era) && (!spk || r.dataset.spk === spk) && (!$('#fFlag').checked || r.dataset.flag === '1') &&
    (!$('#fIrony').checked || r.dataset.irony === '1') && (!$('#fNew').checked || r.dataset.new === '1');
}
function applyFilters(){
  document.querySelectorAll('#eras .row').forEach(r => r.classList.toggle('hidden', !visible(r)));
  document.querySelectorAll('#eras .scenecard').forEach(card => card.classList.toggle('hidden', !card.querySelector('.row:not(.hidden)')));
  document.querySelectorAll('#eras section.era').forEach(sec => sec.classList.toggle('hidden', !sec.querySelector('.scenecard:not(.hidden)')));
}
['fEra', 'fSpk', 'fFlag', 'fIrony', 'fNew'].forEach(id => $('#' + id).addEventListener('change', applyFilters));
document.addEventListener('click', ev => {
  const b = ev.target.closest('button'); if (!b) return;
  if (b.classList.contains('scene')) { stop(); const card = b.closest('.scenecard');
    queue = [...card.querySelectorAll('.row:not(.hidden)')].map(r => byId[r.dataset.id]); next(); return; }
  if (b.classList.contains('play') && !b.classList.contains('aud')) { const r = b.closest('.row'); const l = byId[r.dataset.id];
    if (current && current.line_id === l.line_id) { stop(); return; } stop(); playOne(l); }
});
</script>
</body>
</html>
"""


def main() -> None:
    man = json.loads((FULL / "manifest.json").read_text(encoding="utf-8"))
    cast = json.loads((FULL / "casting.json").read_text(encoding="utf-8"))
    aud = []
    af = FULL / "audition/audition.json"
    if af.exists():
        for r in sorted(json.loads(af.read_text(encoding="utf-8")), key=lambda r: (r["role"], r["voice"], r["k"])):
            aud.append({"role": r["role"], "voice": r["voice"], "tag": f"{r['role']}.{r['voice']}.{r['k']}",
                        "f0": r["features"]["f0_median_hz"], "stt": r["stt_scribe"]})
    naud = []
    nf = FULL / "audition/narrator/audition.json"
    if nf.exists():
        for r in sorted(json.loads(nf.read_text(encoding="utf-8"))["takes"], key=lambda r: (r["voice"], r["line_id"], r["k"])):
            naud.append({"voice": r["voice"], "line_id": r["line_id"], "k": r["k"], "file": r["file"],
                         "f0": r["features"]["f0_median_hz"], "range": r["features"]["f0_range_semitones"],
                         "stt": r["stt_scribe"]})
    slim = dict(man)
    slim["lines"] = [{k: v for k, v in l.items() if k not in ("style_instructions", "tts_text", "text_sha1")}
                     for l in man["lines"]]
    slim.pop("skipped", None)
    if man.get("looks"):
        slim["looks"] = [{k: v for k, v in l.items() if k not in ("tts_text", "text_sha1")} for l in man["looks"]]
    page = (HTML.replace("__MANIFEST__", json.dumps(slim, ensure_ascii=False))
            .replace("__CASTING__", json.dumps(cast, ensure_ascii=False))
            .replace("__AUDITION__", json.dumps(aud, ensure_ascii=False))
            .replace("__NAUDITION__", json.dumps(naud, ensure_ascii=False))
            .replace("__ERAS__", json.dumps(ERA_LABEL, ensure_ascii=False)))
    page = page.replace("</script>\n</body>", "</script>\n</body>")  # keep
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(page, encoding="utf-8")
    print("wrote", PAGE, round(len(page) / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
