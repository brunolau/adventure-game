#!/usr/bin/env python3
"""Reference content validator. Python 3 stdlib only. Not the game runtime.
Usage: python3 validate_handoff.py [path/to/game.json]
Writes validation_report.json and walkthrough.json next to game.json.
"""
from pathlib import Path
import json, sys, random, itertools, collections, copy

PATH=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('game.json')
D=json.loads(PATH.read_text(encoding='utf-8'))
A={a['id']:a for a in D['actions']};R={r['id']:r for r in D['rooms']};I={i['id']:i for i in D['items']}
H={h['id']:h for r in D['rooms'] for h in r['hotspots']};C={c['id']:c for c in D['characters']}
P={p['id']:p for p in D['puzzles']};CS={c['id']:c for c in D['cutscenes']}
AUTO={x['after']:x['to'] for x in D['special_transitions']}
checks=[]
def check(ok,msg):
    if not ok:raise AssertionError(msg)
    checks.append(msg)
def initial():
    s=copy.deepcopy(D['initial_state']);s['done']=set(s['done']);s['inventory']=set(s['inventory']);s['visited']=set(s['visited']);return s
def visible(h,s):return set(h['visible_after'])<=s['done'] and not(set(h['hide_after'])&s['done'])
def unlocked(year,s):
    e=next(e for e in D['eras'] if e['year']==year)
    return e['unlocked_by'] is None or e['unlocked_by'] in s['done']
def graph(s):
    g=collections.defaultdict(list)
    for e in D['connections']:
        if set(e['requires_done'])<=s['done']:
            g[e['from']].append(e['to'])
            if e['bidirectional']:g[e['to']].append(e['from'])
    if 'CHRONO' in s['inventory']:
        for src in D['anchor_nodes']:
            if set(src['requires_done'])<=s['done']:
                for dst in D['eras']:
                    if dst['year']!=src['year'] and unlocked(dst['year'],s):g[src['room']].append(dst['anchor'])
    return g
def path(s,target):
    if target=='inventory' or target==s['room']:return []
    g=graph(s);queue=collections.deque([s['room']]);prev={s['room']:None}
    while queue:
        x=queue.popleft()
        if x==target:
            rev=[]
            while prev[x] is not None:rev.append(x);x=prev[x]
            return rev[::-1]
        for y in g[x]:
            if y not in prev:prev[y]=x;queue.append(y)
    return None
def enabled(a,s,include_path=True):
    if a['id'] in s['done'] or set(a.get('excluded_done',[]))&s['done']:return False
    if not set(a['requires_done'])<=s['done'] or not set(a['requires_items'])<=s['inventory']:return False
    if a['selected_item'] and a['selected_item'] not in s['inventory']:return False
    if a['target'] in H and not visible(H[a['target']],s):return False
    if include_path and path(s,a['room']) is None:return False
    return True
def apply(a,s):
    assert enabled(a,s),(a['id'],s['room'],'missing flags',set(a['requires_done'])-s['done'],'missing items',set(a['requires_items'])-s['inventory'])
    route=path(s,a['room'])
    for rid in route:s['visited'].add(rid);s['room']=rid;s['era']=R[rid]['era']
    assert set(a['consumes'])<=s['inventory'],('consume missing',a['id'])
    assert not(set(a['gives'])&s['inventory']),('duplicate item',a['id'])
    s['inventory']-=set(a['consumes']);s['inventory']|=set(a['gives']);s['done'].add(a['id'])
    if a['id']==D['postgame']['unlock']:s['inventory']|=set(D['postgame']['return_items'])
    if a['id'] in AUTO:s['room']=AUTO[a['id']];s['era']=R[s['room']]['era'];s['visited'].add(s['room'])
    return route

check(len(R)==68,'Exactly 68 unique navigable rooms')
check(len(D['eras'])==5,'Exactly five eras')
check(len(A)==len(D['actions']),'Unique action IDs')
check(len(I)==len(D['items']),'Unique item IDs')
check(len(C)==len(D['characters']),'Unique character IDs')
check(C['TONO82']['age']==12 and C['TONO']['age']==25 and C['TONO20']['age']==50,'Tono ages 12 / 25 / 50')
check(C['OTO']['age']==44 and C['OTO82']['age']==66,'Oto ages 44 / 66')
qactions=[aid for q in D['quests'] for aid in q['actions']]
check(len(qactions)==len(set(qactions)) and set(qactions)==set(A),'Every action is assigned exactly once to a quest/playbook group')
for q in D['quests']:check(q['completion'] in q['actions'],'Quest completion exists: '+q['id'])
for a in A.values():
    check(a['room']=='inventory' or a['room'] in R,'Action room: '+a['id'])
    check(a['target'] in H or a['kind']=='combine' and a['target'] in I,'Action target: '+a['id'])
    check(set(a['requires_done'])<=set(A),'Prerequisite references: '+a['id'])
    check(set(a['requires_items']+a['gives']+a['consumes'])<=set(I),'Item references: '+a['id'])
    check(set(a['consumes'])<=set(a['requires_items']),'All consumed items declared as required: '+a['id'])
    check(not a['selected_item'] or a['selected_item'] in a['requires_items'],'Selected item declared required: '+a['id'])
    check(a['puzzle'] is None or a['puzzle'] in P,'Puzzle reference: '+a['id'])
    check(a['cutscene'] is None or a['cutscene'] in CS,'Cutscene reference: '+a['id'])
    check(bool(a['lines']) and all(x['text'].strip() for x in a['lines']),'Complete nonempty dialogue: '+a['id'])
for h in H.values():check(set(h['visible_after']+h['hide_after'])<=set(A),'Hotspot flags: '+h['id'])
for e in D['connections']:check(e['from'] in R and e['to'] in R and set(e['requires_done'])<=set(A),'Connection: '+e['from']+'→'+e['to'])
for c in C.values():check(set(c['rooms'])<=set(R),'Actor placement: '+c['id'])
speakers=set(C)|set(D['non_actor_speakers'])
def scan_lines(o):
    if isinstance(o,dict):
        if 'speaker' in o and 'text' in o:assert o['speaker'] in speakers,('unknown speaker',o)
        for v in o.values():scan_lines(v)
    elif isinstance(o,list):
        for v in o:scan_lines(v)
scan_lines(D);checks.append('Every spoken line has a declared speaker')

# Presný predpísaný priechod všetkými hlavnými akciami.
s=initial();walk=[]
for q in D['quests']:
    if q['type']!='main':continue
    for aid in q['actions']:
        a=A[aid];route=apply(a,s)
        walk.append({'step':len(walk)+1,'quest':q['id'],'action':aid,'label':a['label'],'travel_path':route,'target':a['target'],'select':a['selected_item'],'puzzle_solution':P[a['puzzle']]['solution'] if a['puzzle'] else None,'inventory_after':sorted(s['inventory']),'room_after':s['room']})
check('F17' in s['done'],'Canonical main-only route reaches ending without side quests')
check(all(a['quest']=='main' for k in s['done'] for a in [A[k]]),'No hidden side-quest dependency in main route')
check(set(D['postgame']['return_items'])<=s['inventory'],'All final evidence returned after ending')
main_saved=copy.deepcopy(s)
for q in D['quests']:
    if q['type']=='side':
        for aid in q['actions']:apply(A[aid],s)
check(len(s['done'])==len(A),'Every side quest and follow-up completes after credits')
check(all(path(s,rid) is not None for rid in R),'All 68 rooms remain reachable in postgame')

# Rôzne legálne poradia, bez testového prideľovania predmetov alebo teleportu cez gate.
for seed in range(120):
    t=initial();rng=random.Random(seed)
    for _ in range(len(A)+1):
        opts=[a for a in A.values() if enabled(a,t)]
        if not opts:break
        apply(rng.choice(opts),t)
    check(len(t['done'])==len(A),'Random legal full route seed '+str(seed))

# 24 poradí finálnych portov a presná nemennosť spotreby.
base=initial()
for row in walk:
    if row['action']=='F12':break
    apply(A[row['action']],base)
for seq in itertools.permutations(['F12','F13','F14','F15']):
    t=copy.deepcopy(base)
    for aid in seq:apply(A[aid],t)
    apply(A['F16'],t);apply(A['F17'],t)
check(True,'All 24 permutations of final evidence ports reach ending')

# Jednoznačnosť bežných akcií v každom kanonickom stave.
t=initial()
for row in walk:
    active=[a for a in A.values() if a['kind']=='click' and a['selected_item'] is None and enabled(a,t)]
    slots=[(a['room'],a['target']) for a in active]
    check(len(slots)==len(set(slots)),'Unambiguous default click before '+row['action'])
    apply(A[row['action']],t)

# Po získaní starého pohára už nie je legálna výroba/pickup mladého kusu.
check('E08' in main_saved['done'] and 'D05' in main_saved['done'],'Temporal cache was stored and retrieved in main route')
check(not enabled(A['E08'],main_saved) and not enabled(A['D05'],main_saved),'Temporal cache cannot be stored or retrieved twice')
check(not({'BRIDGE_NEW','SEALED_NEW','SEALED_OLD'}&main_saved['inventory']),'No duplicate young or sealed version of temporal object')
check(not enabled(A['J05'],main_saved),'Installed return bridge is not reusable or duplicated')

# Uloženie a znovunačítanie každého stavu; iba základný model, nie UI runtime.
t=initial()
for row in walk:
    apply(A[row['action']],t)
    serial={k:sorted(v) if isinstance(v,set) else v for k,v in t.items()}
    back=json.loads(json.dumps(serial,ensure_ascii=False))
    for key in ['done','inventory','visited']:back[key]=set(back[key])
    check(back==t,'Save roundtrip after '+row['action'])

report={'status':'PASS','content_version':D['version'],'stats':D['stats'],'checks_passed':len(checks),'random_full_routes':120,'final_port_permutations':24,'main_only_actions':len(walk),'postgame_all_optional_completed':True,'all_rooms_reachable_postgame':True,'limits':['Not a playable build.','No graphical runtime, audio quality or actual mouse input has been tested.','Historical geography is sourced; future and school interiors remain fiction.'],'checks':checks}
PATH.with_name('validation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
PATH.with_name('walkthrough.json').write_text(json.dumps({'main_route':walk,'postgame_optional_route':[aid for q in D['quests'] if q['type']=='side' for aid in q['actions']]},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['checks','limits']},ensure_ascii=False))
