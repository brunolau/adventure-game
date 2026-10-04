/** Complete pure reference logic for the content contract. No engine dependency.
 * The coding agent supplies rendering, animation, pathfinding, persistence UI and assets.
 * This module deliberately contains no generated-story hooks or unspecified puzzle rules.
 */
export type RoomId = string;
export type ActionId = string;
export type ItemId = string;
export type Mode = 'world' | 'inventory' | 'dialogue' | 'puzzle' | 'cutscene' | 'map' | 'journal' | 'pause';
export interface Line { speaker: string; text: string; line_id?: string }
export interface State {
  schema_version: 1; room: RoomId; era: number; inventory: ItemId[]; done: ActionId[];
  visited: RoomId[]; selected_item: ItemId | null; mode: Mode;
  puzzle_drafts: Record<string, unknown>; journal_seen: string[]; side_rewards: string[];
  hotspot_labels?: boolean; active_line_id?: string | null;
}
export interface Hotspot {
  id: string; name: string; kind: 'npc' | 'prop'; character_id?: string;
  visible_after: ActionId[]; hide_after: ActionId[]; look: string;
  look_variants: { after: ActionId; text: string }[];
  rect: [number, number, number, number]; interaction_point: [number, number];
}
export interface Exit { id: string; to: RoomId; label: string; requires_done: ActionId[]; locked_look: string; travel: string }
export interface Room { id: RoomId; name: string; era: number; hotspots: Hotspot[]; exits: Exit[] }
export interface Action {
  id: ActionId; room: RoomId | 'inventory'; target: string; label: string;
  kind: 'click' | 'topic' | 'combine'; requires_done: ActionId[]; excluded_done: ActionId[];
  requires_items: ItemId[]; selected_item: ItemId | null; gives: ItemId[]; consumes: ItemId[];
  lines: Line[]; quest: string; puzzle: string | null; cutscene: string | null;
  once: true; symmetric?: boolean; journal_text: string;
}
export interface Topic { id: string; label: string; requires_done?: ActionId[]; lines: Line[]; repeatable: boolean }
export interface Content {
  rooms: Room[]; actions: Action[]; items: { id: ItemId; name: string; look: string }[];
  characters: { id: string; ambient_topics: Topic[] }[];
  puzzles: { id: string; solution: unknown; wrong_line: string }[];
  quests: { id: string; type: 'main' | 'side'; completion: ActionId; actions: ActionId[]; hints: string[] }[];
  eras: { year: number; anchor: RoomId; unlocked_by: ActionId | null }[];
  anchor_nodes: { room: RoomId; year: number; requires_done: ActionId[] }[];
  connections: { from: RoomId; to: RoomId; requires_done: ActionId[]; bidirectional: boolean }[];
  special_transitions: { after: ActionId; to: RoomId; auto: boolean }[];
  postgame: { unlock: ActionId; return_items: ItemId[] };
}
const includesAll = <T>(owned: T[], wanted: T[]): boolean => wanted.every(x => owned.includes(x));
const unique = <T>(xs: T[]): T[] => [...new Set(xs)];
const clone = (s: State): State => structuredClone(s);
export function isVisible(h: Hotspot, s: State): boolean {
  return includesAll(s.done, h.visible_after) && !h.hide_after.some(x => s.done.includes(x));
}
export function lookAt(h: Hotspot, s: State): string {
  return [...h.look_variants].reverse().find(x => s.done.includes(x.after))?.text ?? h.look;
}
export function guardsPass(a: Action, s: State): boolean {
  return !s.done.includes(a.id) && !a.excluded_done.some(x => s.done.includes(x)) &&
    includesAll(s.done, a.requires_done) && includesAll(s.inventory, a.requires_items);
}
function targetHotspot(d: Content, a: Action): Hotspot | undefined {
  return d.rooms.find(r => r.id === a.room)?.hotspots.find(h => h.id === a.target);
}
export function validAction(d: Content, s: State, a: Action): boolean {
  if (!guardsPass(a, s) || (a.room !== 'inventory' && a.room !== s.room)) return false;
  const h = targetHotspot(d, a);
  return a.room === 'inventory' || !!h && isVisible(h, s);
}
export type Hit = { type: 'floor'; x: number; y: number } | { type: 'hotspot'; id: string } |
  { type: 'exit'; id: string } | { type: 'item'; id: ItemId } | { type: 'empty' };
export type Resolution = { kind: 'none' } | { kind: 'look'; text: string } | { kind: 'cancel_selection' } |
  { kind: 'toggle_inventory' } | { kind: 'select_item'; item: ItemId } |
  { kind: 'walk'; x: number; y: number } | { kind: 'travel'; to: RoomId } |
  { kind: 'dialogue'; character: string; topics: (Action | Topic)[] } | { kind: 'action'; action: Action };

/** Same resolver for hover preview and click. Only kind=action has an item-action label. */
export function resolveInteraction(d: Content, s: State, hit: Hit, button: 'left' | 'right'): Resolution {
  if (!['world', 'inventory'].includes(s.mode)) return { kind: 'none' };
  const room = d.rooms.find(r => r.id === s.room)!;
  const h = hit.type === 'hotspot' ? room.hotspots.find(x => x.id === hit.id && isVisible(x, s)) : undefined;
  const it = hit.type === 'item' ? d.items.find(x => x.id === hit.id && s.inventory.includes(x.id)) : undefined;
  if (button === 'right') {
    if (s.selected_item) return { kind: 'cancel_selection' };
    if (it) return { kind: 'look', text: it.look };
    if (h) return { kind: 'look', text: lookAt(h, s) };
    if (hit.type === 'exit') {
      const ex = room.exits.find(x => x.id === hit.id);
      return ex ? { kind: 'look', text: includesAll(s.done, ex.requires_done) ? ex.label : ex.locked_look } : { kind: 'none' };
    }
    return { kind: 'toggle_inventory' };
  }
  if (s.selected_item) {
    const a = d.actions.find(x => {
      if (!validAction(d, s, x)) return false;
      if (hit.type === 'item' && x.kind === 'combine') {
        return x.target === hit.id && x.selected_item === s.selected_item ||
          !!x.symmetric && x.target === s.selected_item && x.selected_item === hit.id;
      }
      return !!h && x.kind === 'click' && x.target === h.id && x.selected_item === s.selected_item;
    });
    return a ? { kind: 'action', action: a } : { kind: 'none' };
  }
  if (it) return { kind: 'select_item', item: it.id };
  if (h?.kind === 'npc') {
    const topics = d.actions.filter(a => a.kind === 'topic' && a.target === h.id && validAction(d, s, a));
    const ambient = d.characters.find(c => c.id === h.character_id)?.ambient_topics.filter(t => includesAll(s.done, t.requires_done ?? [])) ?? [];
    return { kind: 'dialogue', character: h.character_id!, topics: [...topics, ...ambient] };
  }
  if (h) {
    const candidates = d.actions.filter(a => a.kind === 'click' && !a.selected_item && a.target === h.id && validAction(d, s, a));
    if (candidates.length > 1) throw new Error('Ambiguous action target: ' + h.id);
    return candidates[0] ? { kind: 'action', action: candidates[0] } : { kind: 'look', text: lookAt(h, s) };
  }
  if (hit.type === 'exit') {
    const ex = room.exits.find(x => x.id === hit.id);
    return !ex ? { kind: 'none' } : includesAll(s.done, ex.requires_done) ?
      { kind: 'travel', to: ex.to } : { kind: 'look', text: ex.locked_look };
  }
  if (hit.type === 'floor') return { kind: 'walk', x: hit.x, y: hit.y };
  return { kind: 'none' };
}
export function itemActionLabel(result: Resolution): string {
  return result.kind === 'action' ? result.action.label : '';
}
function deepEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (!a || !b || typeof a !== 'object' || typeof b !== 'object') return false;
  if (Array.isArray(a) || Array.isArray(b)) return Array.isArray(a) && Array.isArray(b) && a.length === b.length && a.every((v,i) => deepEqual(v,b[i]));
  const aa=a as Record<string,unknown>, bb=b as Record<string,unknown>;
  return Object.keys(aa).length===Object.keys(bb).length && Object.keys(aa).every(k=>Object.hasOwn(bb,k)&&deepEqual(aa[k],bb[k]));
}
/** Call after walking and revalidating the SAME resolution; answer required for puzzle actions. */
export function commitAction(d: Content, s: State, id: ActionId, answer?: unknown): State {
  const a = d.actions.find(x => x.id === id);
  if (!a || !validAction(d, s, a)) throw new Error('Action no longer valid: '+id);
  if (a.puzzle) {
    const puzzle = d.puzzles.find(p=>p.id===a.puzzle);
    if (!puzzle || !deepEqual(answer,puzzle.solution)) throw new Error('Puzzle not solved; state unchanged: '+a.puzzle);
  }
  if (!includesAll(s.inventory,a.consumes) || a.gives.some(x=>s.inventory.includes(x))) throw new Error('Invalid item transaction: '+id);
  const n=clone(s);
  n.inventory=unique([...n.inventory.filter(x=>!a.consumes.includes(x)),...a.gives]);
  n.done.push(id);n.journal_seen=unique([...n.journal_seen,'action.'+id]);
  if (id===d.postgame.unlock) n.inventory=unique([...n.inventory,...d.postgame.return_items]);
  n.side_rewards=unique([...n.side_rewards,...d.quests.filter(q=>q.type==='side'&&n.done.includes(q.completion)).map(q=>q.id)]);
  if (n.selected_item&&!n.inventory.includes(n.selected_item))n.selected_item=null;
  const transition=d.special_transitions.find(x=>x.after===id);
  if(transition){n.room=transition.to;n.era=d.rooms.find(r=>r.id===n.room)!.era;n.visited=unique([...n.visited,n.room]);}
  n.active_line_id=a.lines[0]?.line_id??null;
  n.mode=a.lines.length?'dialogue':a.cutscene?'cutscene':'world';
  return n;
}
export function toggleHotspots(s: State): State {
  return s.mode==='world'?{...s,hotspot_labels:!s.hotspot_labels}:s;
}
export function hotspotList(d: Content,s:State): {id:string;name:string}[] {
  const r=d.rooms.find(x=>x.id===s.room)!;
  return [...r.hotspots.filter(h=>isVisible(h,s)).map(h=>({id:h.id,name:h.name})),...r.exits.map(e=>({id:e.id,name:e.label}))];
}
export function connectedRooms(d:Content,s:State,includePortals:boolean): Set<RoomId> {
  const g=new Map<RoomId,RoomId[]>();
  const edge=(a:RoomId,b:RoomId)=>g.set(a,[...(g.get(a)??[]),b]);
  for(const e of d.connections)if(includesAll(s.done,e.requires_done)){edge(e.from,e.to);if(e.bidirectional)edge(e.to,e.from);}
  if(includePortals&&s.inventory.includes('CHRONO'))for(const src of d.anchor_nodes)if(includesAll(s.done,src.requires_done))for(const dst of d.eras)if(dst.year!==src.year&&(!dst.unlocked_by||s.done.includes(dst.unlocked_by)))edge(src.room,dst.anchor);
  const seen=new Set<RoomId>([s.room]),todo=[s.room];
  while(todo.length){const from=todo.shift()!;for(const to of g.get(from)??[])if(!seen.has(to)){seen.add(to);todo.push(to);}}
  return seen;
}
export function canFastTravel(d:Content,s:State,to:RoomId): boolean {
  return s.mode==='map'&&s.visited.includes(to)&&d.rooms.find(r=>r.id===to)?.era===s.era&&connectedRooms(d,s,false).has(to);
}
export function nextMainQuest(d:Content,s:State): Content['quests'][number] | undefined {
  const reachable=connectedRooms(d,s,true);
  return d.quests.find(q=>q.type==='main'&&!s.done.includes(q.completion)&&q.actions.some(id=>{
    const a=d.actions.find(x=>x.id===id)!;return guardsPass(a,s)&&(a.room==='inventory'||reachable.has(a.room));
  }));
}
export function validateSave(d: Content, raw: unknown): State {
  if(!raw||typeof raw!=='object')throw new Error('Chybný súbor uloženia. Aktuálna hra zostala otvorená.');
  const s=raw as State;
  const ids=(x:unknown):x is string[]=>Array.isArray(x)&&x.every(y=>typeof y==='string')&&new Set(x).size===x.length;
  if(s.schema_version!==1||!d.rooms.some(r=>r.id===s.room&&r.era===s.era)||!ids(s.inventory)||!ids(s.done)||!ids(s.visited)||
    !s.inventory.every(i=>d.items.some(x=>x.id===i))||!s.done.every(a=>d.actions.some(x=>x.id===a))||!s.visited.every(r=>d.rooms.some(x=>x.id===r))||
    s.selected_item!==null&&!s.inventory.includes(s.selected_item)||!['world','inventory','dialogue','puzzle','cutscene','map','journal','pause'].includes(s.mode)||
    !s.puzzle_drafts||typeof s.puzzle_drafts!=='object'||!ids(s.journal_seen)||!ids(s.side_rewards))throw new Error('Chybný súbor uloženia. Aktuálna hra zostala otvorená.');
  return clone(s);
}
