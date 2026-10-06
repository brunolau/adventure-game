# Exit layout of all rooms

Owner request 2026-10-06: *"the location navigations are often a bit illogically placed (2 different location
navigations very close to each other in the same direction while none on the other exit of the screen) … revise the
location chain so that the directions make more sense."* Decision record: docs/DECISIONS.md "Control changes" item 9;
issue: design-doc/ISSUES.md NAV-EXITS-01.

The table at the end is generated: `python tools/exit_audit.py` rewrites it from the effective game (game.json + the
content overlays), the natural blockings (`src/game/data/blocking/<room>.json`) and the location register;
`python tools/exit_audit.py --check` only prints the flags (exit code 1 for an open layout flag). `tools/check_blocking.py`
warns about the same crowding and continuity problems room by room.

## Rules

1. **An exit sits on the painted way to its place**: a door, gate, path, road edge, stairs or a vehicle (bus, tram,
   cable car). An edge exit is where the ground visibly continues out of the picture.
2. **Its side matches the direction of travel.** `left` / `right` = out of that picture edge, `up` = into the picture
   (a door, a gate, a path or road leading away from the camera), `down` = towards the viewer (out of the bottom edge).
   The blocking may name the side (`"side": "up"`); otherwise it is derived from the zone exactly as before (left / right
   sixth of the picture, else up, or down in the lowest fifth). The cursor arrow (`CursorLayer.ExitKind`) and the Space
   badge (`HotspotLabelLayer`) follow the side (`World/ExitSides.cs`, `Room.ExitSideOf`).
3. **Two places never share one edge side by side.** When two targets lie the same way they are separated by kind (one
   through a door or along a path into the picture, one along the edge) or the chain is changed so that one is reached
   through the other.
4. **Walking continuity.** Leaving a room out of its right (left) edge arrives at the target's left (right) edge, so Adam
   keeps walking in the same direction. Doors are exempt (a door in a side wall is passed through and turned away from).
5. **Real direction where it is known.** Where the register or the painting log gives the camera heading, the target's
   real bearing should fall on the exit's side; the coordinates of some rooms are estimates (e.g. S18), so this is
   advisory (flag `COMPASS`), never above rules 1-4 or an owner statement (the S17 family: "the way to the panel blocks
   is to the right of the school").

**Arrival** (`Room.Build` / `HeroSpawn`, `WorldStage`): when Adam comes in through an exit he appears at the matching
return exit of the new room: at the edge (or in the door), and during the fade-in he walks a step in to a point a little
inside the room (edge exits) or in front of the door (`ExitSides.ArrivalStart` / `ArrivalStand`; a blocking may give an
explicit `"arrival": [x, y]`). The step always ends when the transition ends (`Room.FinishArrival`), so input and the QA
harness start from a standing hero; reduced motion places him at once. Map fast travel, portals, special transitions,
new game and load use the room's spawn.

## Problems found (audit of the committed state before this pass)

`python tools/exit_audit.py --blocking <HEAD blocking files> --travel <HEAD travel_ext.json>` plus a visual review of
all 69 paintings with the zones drawn in (Space markers):

| room | problem | kind |
|---|---|---|
| S02 Ulica medzi plotmi | the way to the park S03 (left edge) and the footpath to Mira S05 (left of the gate) both on the left, nothing on the right (the former S51 car exit on the right was removed by item 7) | owner's example; continuity S02 left ↔ S03 left |
| S03 Lúčny koník | S04 (right edge) and S07 (gravel path at the right edge) 100 px apart on the right; the park reached the bus stop S07 by a map transition although the shop S04 lies between them | crowd |
| S07 / S08 | the pond S08 (next to the park, ~120 m) was reached only from the bus stop S07 1.3 km away by a "trodden path" | chain |
| S04 Potraviny | only one exit (left); the camera faces south, so the park (SSW) is ahead-right, the bus stop (ESE) left | compass |
| S17 → S18 | leaving the school yard out of its right edge arrived at the right edge of the estate yard S18 (Adam turned round) | continuity |
| S18 / S62 | same picture in 1995 and 1982: the stop on the left, the school side on the right — the reverse of the walk from the yard | continuity |
| S11 / S51 / S57 → S12 / S52 / S58 | the ramp to the zebra crossing (near left, towards the viewer) counted as a left-edge exit, arriving at the school's left edge | continuity |
| S21 Kamenné námestie | the side street to Ventúrska S22 (far left, into the picture) and the tram to Karlova Ves S19 (left edge) both marked "left", 330 px apart; the reading-room door S23 marked "right" next to the tram to Ružinov S25 | crowd |
| S42 Pred hotelom | the way down to Biela Púť S41 (left edge) next to the side path to the client centre S46 (back left); the hotel entrance S43 marked "right" | crowd |
| S52 Pred ZŠ 2020 | the caretaker's window S56 and the way round the corner to the yard S55 both marked "right", 320 px apart | crowd |
| S61 Školský dvor 1982 | the way to the front S58 (left edge) directly above the way to the service window S64 (bottom-left corner) | crowd |
| S48 Atlas plateau | the Rotunda entrance S47 and the terrace stairs S50 189 px apart (both painted on the Rotunda) | crowd, accepted |

No exit lacked a painted way at its logical spot, so no paint edit was needed (spend USD 0).

## Changes per room

| room | change |
|---|---|
| S02 | S03 moved to the right edge (the street continues past the courier van towards Javorová alej and the park)¹; left of the gate only the footpath to S05 (into the picture). |
| S03 | S08 (pond) out of the right edge (the meadow continues below the gravel path down to the pump track); S04 towards the viewer (bottom edge, across the park to Triangel)¹; S02 left edge. The map transition S03 ↔ S07 is gone (`travel_ext.json`). |
| S04 | S03 out of the right edge, S07 out of the left edge (the courtyard paving continues both ways along the arcade; the camera faces south). New exit S04.to_S07 (walk, ~550 m to the bus stop). |
| S07 | The far end of the platform ("towards the village") now leads to the shop S04 (walk, was the map transition to S03); the trodden path to S08 is gone; the bus S51 at the kerb stays. |
| S08 | Its left-edge trail leads back up to the park S03 (was to the bus stop S07). |
| S18 | S17 (school yard) out of the left edge (the side street in front of the kiosk), S11 (tram stop) out of the right edge (the pavement past the big tree, zone enlarged from the 60x45 corner); S69 stays up the side road. |
| S62 | Same picture as S18: S65 (the service building by the school) left, S57 (stop) right. |
| S11, S51, S57 | The ramp to the zebra crossing towards the school is side `down` (arrow down-left of the shelter). |
| S19, S25 | The zebra crossing to S20 and the passage to S26 are side `up` (into the picture), apart from the edge exits. |
| S21 | Ventúrska S22 and the reading-room door S23 are side `up`; S19 left edge and S25 right edge are the only edge exits. |
| S42 | S41 towards the viewer (bottom edge, down the access road; S41 looks up that road)¹; S46 side path and S43 entrance side `up`. |
| S52 | The service window S56 is side `up`; the right edge leads only to the yard S55. |
| S61 | S64 towards the viewer (bottom edge, back past the south end of the wing)¹; S58 left edge, S66 right edge. |
| all rooms | Arrival at the matching return exit with a walk-in step (above); cursor and badge arrows from the exit side. |

¹ Already moved in the working tree when this pass started (same owner message, 22:09); kept as they are and
folded into this layout (the S03 note now names the pond on the right edge).

Chain changes (`src/game/data/content_ext/travel_ext.json`, 2020 Chorvátsky Grob): removed S03 ↔ S07 (map transition) and
S07 ↔ S08; added S04 ↔ S07 and S03 ↔ S08 (walk). The region and its hub S07 are unchanged; the walkthrough's travel paths
are recomputed by the Core driver and the in-engine replayer (S51 → S07 → S04 → S03). New text keys (labels = room
names, locked = the standard line): `exit.S04.to_S07`, `exit.S07.to_S04`, `exit.S03.to_S08`, `exit.S08.to_S03`
(`.label` / `.locked`), `conn.S04.S07`, `conn.S03.S08`; retired: the keys of S03.to_S07, S07.to_S03, S07.to_S08,
S08.to_S07, conn.S03.S07, conn.S07.S08. They are generated by `python tools/extract_strings.py` (the text owner runs it;
the localization tables are theirs).

## Accepted

- accepted: `S48.to_S47` / accepted: `S48.to_S50` — the Rotunda's entrance and the external stairs to the roof terrace
  are two different painted ways on the same building (a door at its base, a steel staircase beside it); 189 px apart.
- `COMPASS` advisories that stay: S17 / S55 / S61 lead left to the front (S12 / S52 / S58) although the register
  coordinates put the front entrance west-north-west of the yard camera (right of a south-west view): the owner-confirmed
  layout of the S17 family goes round the SE end of the main wing (left); S61.to_S66 (the shed by the east fence) and
  S37.to_S32 (the square, behind-right of the SSE view, kept left for continuity with S32.to_S37 on S32's right edge).
- S11 / S51 / S57: the far end of the platform (S18 / S07 / S62) and the tram (S19) are both into the picture, 340 px
  apart — a walkway and a vehicle, kept.

## Table (generated)

<!-- exits:begin -->
### 2020

**S01 Adamova garáž** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S01.to_S02 | up | the open sectional garage door: out onto the driveway and the street (S02) | [930, 440, 450, 352] → [1150, 822] | S02 | walk | 202° 103 m | S02.to_S01 (up) | ok |

**S02 Ulica medzi plotmi** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S02.to_S01 | up | Adam's open driveway gate | [705, 560, 300, 170] → [855, 760] | S01 | walk | 22° 103 m | S01.to_S02 (up) | ok |
| S02.to_S03 | right | the street continues out of the right edge past the courier van towards Javorova alej and the park | [1855, 815, 65, 200] → [1850, 915] | S03 | walk | 62° 1347 m | S03.to_S02 (left) | ok |
| S02.to_S05 | up | narrow paved footpath between two plots, a short cut to the old core on Pezinska (Mira) | [430, 560, 170, 175] → [520, 755] | S05 | walk | 29° 879 m | S05.to_S02 (left) | ok |

**S03 Dobrovoľnícke výdajné miesto** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S03.to_S02 | left (named) | the sandy path and the trampled meadow continue out of the left edge towards the street | [0, 720, 60, 295] → [70, 880] | S02 | walk | 242° 1347 m | S02.to_S03 (right) | ok |
| S03.to_S04 | down (named) | the trampled meadow runs towards the camera, across the park to the village shop at Triangel | [1120, 950, 440, 110] → [1340, 995] | S04 | walk | 22° 1187 m | S04.to_S03 (right) | ok |
| S03.to_S08 | right (named) | the trampled meadow continues out of the right edge below the gravel path, down to the pump track and the p... | [1860, 700, 60, 315] → [1850, 880] | S08 | walk | 141° 160 m | S08.to_S03 (left) | ok |

**S04 Potraviny cez okienko** — camera 180° (courtyard of the arc facing the mid unit (the concave side faces north))

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S04.to_S03 | right (named) | the courtyard paving continues out of the right edge along the arcade, towards Javorová alej and the park w... | [1850, 805, 70, 210] → [1845, 905] | S03 | walk | 202° 1187 m (→ up) | S03.to_S04 (down) | ok |
| S04.to_S07 | left (named) | the courtyard paving continues out of the left edge along the arcade, out to the road and on to the bus sto... | [0, 805, 70, 210] → [75, 905] | S07 | walk | 110° 548 m (→ left) | S07.to_S04 (left) | ok |

**S05 Mirkina bránka** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S05.to_S02 | left | the pavement continues out of the left edge (street between the fences) | [0, 740, 60, 275] → [70, 900] | S02 | walk | 209° 879 m | S02.to_S05 (up) | ok |
| S05.to_S06 | right | narrow side passage between the house corner and the neighbour's wall, leading along the house to the close... | [1655, 520, 130, 215] → [1725, 760] | S06 | walk | — | S06.to_S05 (left) | ok |
| S05.to_S09 | up | the whole workshop door leaf and its threshold step | [725, 400, 150, 330] → [800, 765] | S09 | walk | — | S09.to_S05 (left) | ok |

**S06 Pod zatvoreným oknom** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S06.to_S05 | left | the side path continues out of the left edge back to the street passage beside the gate (S05) | [0, 800, 60, 215] → [70, 905] | S05 | walk | — | S05.to_S06 (right) | ok |

**S07 Čierna Voda pri výveske** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S07.to_S51 | up (named) | owner 2026-10-06: the bus to Dúbravka higher on the road by the bus-stop sign, direction up the road | [450, 440, 260, 130] → [655, 640] | S51 | bus | 251° 17009 m | S51.to_S07 (up) | ok |
| S07.to_S04 | left (named) | owner 2026-10-06: back to the shop (S04) at the bottom left, on the road towards the viewer | [30, 800, 360, 200] → [470, 965] | S04 | walk | 290° 548 m | S04.to_S07 (left) | ok |

**S08 Chodník pri retenčnej nádrži** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S08.to_S03 | left (named) | the trail leaves the mound out of the left edge, back up to the park shelter S03 (S03.to_S08 is its right e... | [0, 815, 65, 200] → [70, 910] | S03 | walk | 321° 160 m | S03.to_S08 (right) | ok |

**S09 Predsieň záhradnej dielne** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S09.to_S05 | left | the open outer door to the street (Mira's gate, S05) | [24, 342, 262, 470] → [155, 840] | S05 | walk | — | S05.to_S09 (up) | ok |
| S09.to_S10 | right | the inner doorway to the back room (ZVON workshop, S10) | [1630, 342, 262, 470] → [1760, 840] | S10 | walk | — | S10.to_S09 (left) | ok |

**S10 Dielňa ZVON** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S10.to_S09 | left | the doorway back to the anteroom (S09) | [24, 342, 262, 470] → [155, 840] | S09 | walk | — | S09.to_S10 (right) | ok |

**S51 Dúbravská zastávka v roku 2020** — camera 315° (as S11)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S51.to_S52 | down (named) | the ramp at the near left down to the zebra crossing, towards the school (same as S11.to_S12, L_STOP family) | [0, 760, 250, 200] → [110, 930] | S52 | walk | 257° 274 m (→ left) | S52.to_S51 (left) | ok |
| S51.to_S07 | up | the far end of the platform and the path to the bus stop beyond it: the 2020 bus back to Cierna Voda | [780, 430, 240, 212] → [880, 690] | S07 | bus | 71° 17024 m (→ right) | S07.to_S51 (up) | ok |

**S52 Pred ZŠ Sokolíkova v roku 2020** — camera 45° (as S12)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S52.to_S51 | left | the forecourt path out of the left edge towards the street and the tram stop | [0, 790, 62, 225] → [70, 900] | S51 | walk | 77° 274 m (→ up) | S51.to_S52 (down) | ok |
| S52.to_S56 | up (named) | the caretaker's service window, the last ground-floor window before the corner (L_WINDOW is its close-up) | [1618, 388, 164, 212] → [1700, 706] | S56 | walk | 135° 67 m (→ right) | S56.to_S52 (left) | ok |
| S52.to_S53 | up | the closed glazed entrance doors at the top of the steps (open after D02) | [897, 362, 357, 291] → [1110, 792] | S53 | walk | 121° 43 m (→ right) | S53.to_S52 (left) | ok |
| S52.to_S55 | right | past the building corner the path leads round to the school yard (right edge) | [1830, 600, 90, 330] → [1850, 800] | S55 | walk | 91° 93 m (→ right) | S55.to_S52 (left) | ok |

**S53 Školské zádverie v roku 2020** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S53.to_S52 | left | glazed entrance double door (same as S13.to_S12) | [30, 290, 160, 545] → [125, 885] | S52 | walk | 301° 43 m | S52.to_S53 (up) | ok |
| S53.to_S54 | right | open doorway to the corridor and staircase up to the physics cabinet = the approved separate service route... | [1690, 306, 192, 530] → [1782, 862] | S54 | walk | 135° 16 m | S54.to_S53 (left) | ok |

**S54 Fyzikálny kabinet v roku 2020** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S54.to_S53 | left | door in the left wall to the corridor and the entrance hall (same as S15.to_S13) | [55, 395, 135, 560] → [190, 935] | S53 | walk | 315° 16 m | S53.to_S54 (right) | ok |

**S55 Školský dvor v roku 2020** — camera 225° (as S17)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S55.to_S52 | left | the yard asphalt continues out of the left edge in front of the running track, past the SE end of the main... | [0, 722, 60, 293] → [70, 880] | S52 | walk | 271° 93 m (→ right) | S52.to_S55 (right) | COMPASS |

**S56 Školnícke servisné okno v roku 2020** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S56.to_S52 | left | the path along the facade back to the main entrance (left edge) | [0, 860, 64, 155] → [60, 950] | S52 | walk | 315° 67 m | S52.to_S56 (up) | ok |


### 1995

**S11 Dúbravská zastávka** — camera 315° (SW platform looking NW along the track)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S11.to_S12 | down (named) | the short ramp at the near left down to the zebra crossing over the west carriageway, towards the school | [0, 760, 250, 200] → [110, 930] | S12 | walk | 257° 274 m (→ left) | S12.to_S11 (left) | ok |
| S11.to_S18 | up | the platform continues past the shelter to its far end and the path to the housing-estate yard (L_STOP family) | [780, 430, 240, 212] → [880, 690] | S18 | walk | 277° 85 m (→ left) | S18.to_S11 (right) | ok |
| S11.to_S19 | up | the red-cream tram standing at the platform: board it towards Karlova Ves | [1108, 300, 250, 330] → [1050, 720] | S19 | map_transition | 162° 2652 m (→ down) | S19.to_S11 (left) | ok |

**S12 Pred ZŠ Sokolíkova** — camera 45° (at the SW entrance facade)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S12.to_S11 | left | the forecourt path continues out of the left edge towards the street and the tram stop | [0, 790, 62, 225] → [70, 900] | S11 | walk | 77° 274 m (→ up) | S11.to_S12 (down) | ok |
| S12.to_S13 | up | the glazed entrance doors at the top of the steps | [897, 362, 357, 291] → [1110, 792] | S13 | walk | 121° 43 m (→ right) | S13.to_S12 (left) | ok |
| S12.to_S17 | right | past the building corner the path leads round to the school yard (right edge) | [1830, 600, 90, 330] → [1850, 800] | S17 | walk | 91° 93 m (→ right) | S17.to_S12 (left) | ok |

**S13 Školská vstupná chodba** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S13.to_S12 | left | glazed entrance double door at the front of the left facade wall (out to the forecourt) | [30, 290, 160, 545] → [125, 885] | S12 | walk | 301° 43 m | S12.to_S13 (up) | ok |
| S13.to_S14 | up | middle double door with glass panes in the back wall: the classroom wing | [849, 368, 222, 332] → [960, 738] | S14 | walk | 49° 42 m | S14.to_S13 (up) | ok |
| S13.to_S15 | right | open doorway in the right wall to the corridor with the staircase up to the physics cabinet | [1690, 306, 192, 530] → [1782, 862] | S15 | walk | 135° 16 m | S15.to_S13 (left) | ok |

**S14 Trieda pamäťového krúžku** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S14.to_S13 | up | classroom door at the left end of the front wall, to the corridor and the entrance hall | [337, 376, 168, 344] → [418, 758] | S13 | walk | 229° 42 m | S13.to_S14 (up) | ok |

**S15 Fyzikálny kabinet** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S15.to_S13 | left | door in the left wall to the corridor (stairs down to the entrance hall) | [55, 395, 135, 560] → [190, 935] | S13 | walk | 315° 16 m | S13.to_S15 (right) | ok |
| S15.to_S16 | right | door in the right wall to the small school-radio room | [1730, 395, 135, 560] → [1730, 935] | S16 | walk | 20° 21 m | S16.to_S15 (up) | ok |

**S16 Miestnosť školského rozhlasu** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S16.to_S15 | up | door in the left wall back to the physics cabinet | [355, 405, 132, 580] → [470, 960] | S15 | walk | 200° 21 m | S15.to_S16 (right) | ok |

**S17 Školský dvor** — camera 225° (SE corner of the court looking SW at the yard facade)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S17.to_S12 | left | the yard asphalt continues out of the left edge in front of the running track, past the SE end of the main... | [0, 722, 60, 293] → [70, 880] | S12 | walk | 271° 93 m (→ right) | S12.to_S17 (right) | COMPASS |
| S17.to_S18 | right | the yard asphalt continues out of the right edge past the near end of the court fence: the way to the housi... | [1860, 722, 60, 293] → [1850, 880] | S18 | walk | 50° 117 m (→ down) | S18.to_S17 (left) | ok |

**S18 Sídliskový dvor s kioskom** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S18.to_S11 | right (named) | the pavement along the lawn strip continues out of the right edge, past the big tree, towards the tram stop... | [1800, 930, 120, 85] → [1880, 995] | S11 | walk | 97° 85 m | S11.to_S18 (up) | ok |
| S18.to_S17 | left (named) | the side street in front of the kiosk continues out of the left edge towards the school yard (S17.to_S18 le... | [0, 892, 60, 123] → [40, 950] | S17 | walk | 230° 117 m | S17.to_S18 (right) | ok |
| S18.to_S69 | up | the side road between the kiosk and the parked red car runs back into the gap between the blocks, towards t... | [360, 800, 160, 66] → [440, 878] | S69 | walk | 241° 51 m | S69.to_S18 (down) | ok |

**S19 Karloveské nástupište** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S19.to_S11 | left | the platform continues out of the left edge (tram towards Dubravka) | [0, 815, 60, 200] → [70, 910] | S11 | map_transition | 342° 2652 m | S11.to_S19 (up) | ok |
| S19.to_S20 | up (named) | zebra crossing over the double track to the gap in the far railing and the steps up the slope to the Kutiky... | [1510, 540, 150, 260] → [1580, 850] | S20 | walk | 306° 511 m | S20.to_S19 (up) | ok |
| S19.to_S21 | right | the platform continues out of the right edge (tram towards the centre) | [1860, 815, 60, 200] → [1850, 910] | S21 | map_transition | 109° 4898 m | S21.to_S19 (left) | ok |

**S20 Palova opravovňa** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S20.to_S19 | up | glazed shop door to the pavilion arcade and the tram stop | [335, 345, 195, 418] → [432, 820] | S19 | walk | 126° 511 m | S19.to_S20 (up) | ok |

**S21 Kamenné námestie** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S21.to_S19 | left | the plaza continues out of the left edge (tram stop for Karlova Ves) | [0, 712, 60, 303] → [70, 900] | S19 | map_transition | 289° 4899 m | S19.to_S21 (right) | ok |
| S21.to_S22 | up (named) | side street at the far left leading towards the Old Town (Venturska) | [0, 370, 128, 330] → [80, 760] | S22 | walk | 256° 571 m | S22.to_S21 (up) | ok |
| S21.to_S23 | up (named) | entrance door of the cream city block (the reading room) | [1645, 372, 90, 328] → [1690, 760] | S23 | walk | 22° 293 m | S23.to_S21 (up) | ok |
| S21.to_S24 | up | street beside the department store leading towards Obchodna | [770, 352, 130, 348] → [835, 760] | S24 | walk | 350° 456 m | S24.to_S21 (up) | ok |
| S21.to_S25 | right | the plaza continues out of the right edge (tram to Ruzinov) | [1860, 712, 60, 303] → [1850, 900] | S25 | map_transition | 59° 1959 m | S25.to_S21 (left) | ok |
| S21.to_S28 | up | bus stop at the edge of the square (bus to Petrzalka) | [1385, 375, 175, 325] → [1470, 760] | S28 | map_transition | 212° 2485 m | S28.to_S21 (left) | ok |

**S22 Antikvariát Pod druhou rukou** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S22.to_S21 | up | glazed shop door with the bell, out to Venturska | [985, 340, 206, 425] → [1085, 820] | S21 | walk | 76° 571 m | S21.to_S22 (up) | ok |

**S23 Archívna študovňa** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S23.to_S21 | up | door of the reading room, out to Kamenne namestie | [322, 345, 200, 420] → [420, 822] | S21 | walk | 202° 293 m | S21.to_S23 (up) | ok |

**S24 Fotoateliér Svetlo** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S24.to_S21 | up | glazed entrance door to Obchodna | [314, 345, 180, 420] → [404, 822] | S21 | walk | 170° 456 m | S21.to_S24 (up) | ok |

**S25 Miletičova medzi stánkami** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S25.to_S21 | left | the aisle runs out of the left edge (tram towards the centre) | [0, 762, 60, 253] → [70, 890] | S21 | map_transition | 239° 1959 m | S21.to_S25 (right) | ok |
| S25.to_S26 | up (named) | short aisle to the passage through the market-edge building (Pasaz Mileticova) | [250, 340, 190, 300] → [356, 672] | S26 | walk | 294° 47 m | S26.to_S25 (up) | ok |
| S25.to_S27 | right | the aisle runs out of the right edge towards the estate blocks on Mileticova | [1860, 762, 60, 253] → [1850, 890] | S27 | walk | 280° 129 m | S27.to_S25 (up) | ok |

**S26 Opravovňa odevov** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S26.to_S25 | up | glazed shop door to the passage and the market | [314, 345, 184, 420] → [406, 825] | S25 | walk | 114° 47 m | S25.to_S26 (up) | ok |

**S27 Kazetový klub v suteréne** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S27.to_S25 | up | ajar basement door, the stairs up to the courtyard and the market | [314, 360, 184, 405] → [406, 825] | S25 | walk | 100° 129 m | S25.to_S27 (right) | ok |

**S28 Petržalský podchod** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S28.to_S21 | left | the path and the lawn run out of the left edge (bus stop, back to the centre) | [0, 790, 60, 225] → [70, 900] | S21 | map_transition | 32° 2485 m | S21.to_S28 (up) | ok |
| S28.to_S29 | up | up the stairs on the embankment to the garage row | [1340, 300, 420, 405] → [1395, 760] | S29 | walk | 136° 1428 m | S29.to_S28 (left) | ok |
| S28.to_S30 | up | through the lit tunnel towards the Danube embankment | [812, 330, 300, 365] → [960, 740] | S30 | walk | 49° 2030 m | S30.to_S28 (left) | ok |

**S29 Garáž rádioamatéra** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S29.to_S28 | left | the forecourt runs out of the left edge towards the underpass | [0, 716, 60, 299] → [70, 880] | S28 | walk | 316° 1428 m | S28.to_S29 (up) | ok |

**S30 Nábrežný merací prístrešok** — camera 292° (upstream footway looking WNW)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S30.to_S28 | left | the footway runs out of the left edge (behind the left truss member) back to the Petrzalka bridgehead and t... | [0, 800, 90, 215] → [60, 905] | S28 | walk | 229° 2029 m (→ left) | S28.to_S30 (up) | ok |

**S69 Sokolíkovský dvor** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S69.to_S18 | down | the court opens towards the camera between the end of the near wall (x 1150) and the bench / grass bank: th... | [1190, 985, 225, 85] → [1300, 1008] | S18 | walk | 61° 51 m | S18.to_S69 (up) | ok |


### 1960

**S31 Ivanská železničná zastávka** — camera 67° (on the crossing looking ENE along the track)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S31.to_S32 | right | the forecourt in front of the gable continues out of the right edge onto Nadrazna, the road south into the... | [1860, 705, 60, 300] → [1845, 870] | S32 | walk | 201° 718 m (→ right) | S32.to_S31 (left) | ok |

**S32 Ivanská náves** — camera 22° (square park looking NNE to the fire-station tower)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S32.to_S31 | left | the dirt road leaves the square to the left (north, Nadrazna towards the railway halt) | [0, 672, 60, 330] → [70, 860] | S31 | walk | 21° 718 m (→ up) | S31.to_S32 (right) | ok |
| S32.to_S33 | up | the plank door of the post-office house on the left, enamel POSTA sign above it | [398, 396, 104, 186] → [450, 628] | S33 | walk | 115° 112 m (→ right) | S33.to_S32 (left) | ok |
| S32.to_S34 | up | the street mouth between the post-office house and the next houses (Moyzesova, towards the culture hall) | [595, 440, 140, 175] → [662, 650] | S34 | walk | 338° 138 m (→ left) | S34.to_S32 (right) | ok |
| S32.to_S35 | up | the village road leaving the square at the back right, towards the manor's service courtyard | [1045, 440, 140, 175] → [1115, 652] | S35 | walk | 31° 259 m (→ up) | S35.to_S32 (left) | ok |
| S32.to_S37 | right | the path leaves the green to the right in front of the big linden (east, towards the manor park) | [1860, 720, 60, 285] → [1850, 870] | S37 | walk | 36° 331 m (→ up) | S37.to_S32 (left) | ok |

**S33 Pošta s prepážkou** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S33.to_S32 | left | the glazed wooden double door to the village square at the left of the back wall | [50, 410, 210, 290] → [155, 765] | S32 | walk | 295° 112 m | S32.to_S33 (up) | ok |

**S34 Kultúrna sála pred skúškou** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S34.to_S32 | right | the panelled double door on the right of the end wall, one leaf ajar, daylight from the street | [1630, 430, 170, 290] → [1715, 770] | S32 | walk | 158° 138 m | S32.to_S34 (up) | ok |

**S35 Dvor hospodárskej dielne** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S35.to_S32 | left | the yard opens to the left towards the village road and the square | [0, 795, 60, 215] → [95, 982] | S32 | walk | 211° 259 m | S32.to_S35 (up) | ok |
| S35.to_S36 | up | the plank door of Oto's workshop under the columned porch | [1125, 400, 95, 210] → [1172, 652] | S36 | walk | — | S36.to_S35 (left) | ok |

**S36 Otova mechanická dielňa** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S36.to_S35 | left | the plank door in the back wall at the far left, ajar, daylight of the courtyard behind it | [70, 430, 192, 290] → [170, 790] | S35 | walk | — | S35.to_S36 (up) | ok |

**S37 Park pri kaštieli** — camera 157° (NNW of the facade looking SSE)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S37.to_S32 | left | the gravel path leaves the park to the left, back to the village square | [0, 780, 60, 230] → [70, 900] | S32 | walk | 216° 331 m (→ right) | S32.to_S37 (right) | COMPASS |
| S37.to_S38 | right | the path leaves the park to the right through the pines, towards the fields and the canal | [1860, 780, 60, 230] → [1850, 900] | S38 | walk | 227° 1635 m (→ right) | S38.to_S37 (left) | ok |

**S38 Pred skúšobnou čerpacou búdkou** — camera 135° (looking SE)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S38.to_S37 | left | the dirt track leads back out of the left edge towards the village and the manor park | [0, 712, 60, 295] → [70, 880] | S37 | walk | 47° 1635 m (→ left) | S37.to_S38 (right) | ok |
| S38.to_S39 | up | lower part of the measuring-room door and its concrete threshold step (the door leaf above is the S38.door... | [440, 578, 132, 104] → [505, 712] | S39 | walk | — | S39.to_S38 (left) | ok |

**S39 Miestnosť prvého ZVONu** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S39.to_S38 | left | the plank door of the hut, standing open on the left side wall, daylight and reeds of the canal bank outsid... | [20, 270, 185, 540] → [180, 825] | S38 | walk | — | S38.to_S39 (up) | ok |
| S39.to_S40 | right | the narrow plank door with a brass knob on the right side wall, to the technical archive loft (v1 painting) | [1705, 200, 180, 620] → [1785, 850] | S40 | walk | 47° 1560 m | S40.to_S39 (left) | ok |

**S40 Povala technického archívu** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S40.to_S39 | left | the wooden staircase with a solid handrail and newel post going down through the opening in the floor at th... | [20, 560, 330, 345] → [380, 935] | S39 | walk | 227° 1560 m | S39.to_S40 (right) | ok |


### 2035

**S41 Biela Púť pri dolnej stanici** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S41.to_S42 | up | the access road continues past Hotel Posta towards Hotel Grand Jasna (S42): the far end of the road | [780, 352, 230, 150] → [800, 630] | S42 | walk | — | S42.to_S41 (down) | ok |
| S41.to_S67 | up | the gondola valley station (bullwheel housing and boarding hall) behind the fence | [1252, 262, 260, 120] → [1120, 745] | S67 | cable_A6 | 151° 1093 m | S67.to_S41 (left) | ok |

**S42 Pred hotelom Grand Jasná** — camera 202° (forecourt looking SSW to Chopok)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S42.to_S41 | down | the paved forecourt runs back towards the camera, down the access road to the Biela Put gondola station pla... | [700, 950, 520, 110] → [960, 995] | S41 | walk | — | S41.to_S42 (up) | ok |
| S42.to_S43 | up (named) | the hotel's main entrance under its canopy (lobby) | [1625, 450, 270, 255] → [1760, 800] | S43 | walk | 243° 134 m (→ right) | S43.to_S42 (left) | ok |
| S42.to_S44 | up | the glazed side door of the hotel's lower wing that leads to the rented exhibition salon | [1190, 425, 125, 269] → [1252, 740] | S44 | walk | 243° 134 m (→ right) | S44.to_S42 (right) | ok |
| S42.to_S45 | up | the gravel footpath leading through the gap in the stone wall into the spruce forest to Vrbicke pleso | [650, 560, 110, 92] → [702, 676] | S45 | walk | 267° 373 m (→ right) | S45.to_S42 (left) | ok |
| S42.to_S46 | up (named) | the paved side path past the gondola station structure towards the Biela Put client centre | [130, 560, 130, 92] → [195, 676] | S46 | walk | 99° 162 m (→ left) | S46.to_S42 (left) | ok |

**S43 Lobby hotela Grand Jasná** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S43.to_S42 | left | the glazed entrance doors in the back wall, left of the reception, out to the forecourt | [60, 420, 200, 285] → [160, 800] | S42 | walk | 63° 134 m | S42.to_S43 (up) | ok |

**S44 Výstavný salón hotela Grand Jasná** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S44.to_S42 | right | the salon door to the hotel corridor and out to the forecourt | [1700, 400, 180, 305] → [1790, 800] | S42 | walk | 63° 134 m | S42.to_S44 (up) | ok |

**S45 Chodník pri Vrbickom plese** — camera 157° (north shore looking SSE)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S45.to_S42 | left | the path continues out of the left edge back to Hotel Grand Jasna | [0, 735, 60, 280] → [70, 880] | S42 | walk | 87° 373 m (→ left) | S42.to_S45 (up) | ok |

**S46 Klientske centrum Biela Púť** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S46.to_S42 | left | the glazed entrance doors out to the plaza (and on to Hotel Grand Jasna) | [60, 420, 195, 285] → [160, 800] | S42 | walk | 279° 162 m | S42.to_S46 (up) | ok |

**S47 Chopok pri Rotunde** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S47.to_S48 | right | the glazed door in the stone wall to the stairs down to the plateau with the Atlas pavilion | [1600, 360, 190, 345] → [1695, 800] | S48 | walk | 98° 77 m | S48.to_S47 (up) | ok |
| S47.to_S68 | left | the lounge continues out of the left edge towards the Funitel summit station | [0, 738, 60, 277] → [70, 890] | S68 | arrive_funitel | 359° 1058 m | S68.to_S47 (right) | ok |

**S48 Servisný pavilón výstavy Atlas** — camera 270° (plateau looking W)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S48.to_S47 | up | the Rotunda's entrance in its stone base under the red band, at the end of the plateau path | [600, 470, 120, 130] → [650, 640] | S47 | walk | 278° 77 m (→ up) | S47.to_S48 (right) | CROWD with S48.to_S50 |
| S48.to_S49 | right | the pavilion's door to the inner chamber | [1615, 420, 170, 345] → [1700, 786] | S49 | walk | — | S49.to_S48 (right) | ok |
| S48.to_S50 | up | the external steel staircase up to the roof viewing terrace beside the Rotunda | [400, 380, 150, 230] → [470, 652] | S50 | walk | 253° 48 m (→ up) | S50.to_S48 (left) | CROWD with S48.to_S47 |

**S49 Chronokomora pavilónu Atlas** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S49.to_S48 | right | the door at the right back to the service bay and the plateau | [1815, 380, 105, 345] → [1840, 820] | S48 | walk | — | S48.to_S49 (right) | ok |

**S50 Vyhliadková terasa pri Rotunde** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S50.to_S48 | left | the top of the external steel stairs down to the plateau and the Atlas pavilion at the left end of the deck | [0, 600, 160, 190] → [80, 860] | S48 | walk | 73° 48 m | S48.to_S50 (up) | ok |

**S67 Priehyba pri prestupe na Funitel** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S67.to_S41 | left | the open passage with daylight at the left end of the hall towards the gondola from Biela Put (cable ride b... | [0, 380, 160, 345] → [80, 830] | S41 | cable_A6 | 331° 1093 m | S41.to_S67 (up) | ok |
| S67.to_S68 | up | the open doors of the docked Funitel cabin behind the boarding gate (ride to Chopok after J03) | [960, 330, 200, 255] → [1060, 760] | S68 | board_funitel | 178° 1026 m | S68.to_S67 (left) | ok |

**S68 Kabína Funitelu medzi Priehybou a Chopkom** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S68.to_S67 | left | the downhill end panel of the cabin with its door (back to Priehyba once the cabin is in the station) | [0, 240, 120, 530] → [70, 880] | S67 | board_funitel | 358° 1026 m | S67.to_S68 (up) | ok |
| S68.to_S47 | right | the closed sliding doors of the cabin, opened by the attendant on arrival at the summit (after J04) | [1580, 235, 240, 535] → [1700, 870] | S47 | arrive_funitel | 179° 1058 m | S47.to_S68 (left) | ok |


### 1982

**S57 Dúbravská zastávka v roku 1982** — camera 315° (as S11)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S57.to_S58 | down (named) | the ramp at the near left down to the zebra crossing, towards the school (same as S11.to_S12, L_STOP family) | [0, 760, 250, 200] → [110, 930] | S58 | walk | 257° 274 m (→ left) | S58.to_S57 (left) | ok |
| S57.to_S62 | up | the far end of the platform and the path to the housing-estate shop (same place as S11.to_S18) | [780, 430, 240, 212] → [880, 690] | S62 | walk | 277° 85 m (→ left) | S62.to_S57 (right) | ok |

**S58 Pred ZŠ Sokolíkova v roku 1982** — camera 45° (as S12)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S58.to_S57 | left | the forecourt path out of the left edge towards the street and the stop | [0, 790, 62, 225] → [70, 900] | S57 | walk | 77° 274 m (→ up) | S57.to_S58 (down) | ok |
| S58.to_S59 | up | the glazed entrance doors at the top of the steps | [897, 362, 357, 291] → [1110, 792] | S59 | walk | 121° 43 m (→ right) | S59.to_S58 (left) | ok |
| S58.to_S61 | right | past the building corner the path leads round to the school yard (right edge) | [1830, 600, 90, 330] → [1850, 800] | S61 | walk | 91° 93 m (→ right) | S61.to_S58 (left) | ok |

**S59 Školská chodba v roku 1982** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S59.to_S58 | left | copied from S13.to_S12 (same template position) | [30, 290, 160, 545] → [125, 885] | S58 | walk | 301° 43 m | S58.to_S59 (up) | ok |
| S59.to_S60 | up | copied from S13.to_S14 (same template position) | [849, 368, 222, 332] → [960, 738] | S60 | walk | 49° 42 m | S60.to_S59 (up) | ok |
| S59.to_S63 | right | copied from S13.to_S15 (same template position) | [1690, 306, 192, 530] → [1782, 862] | S63 | walk | 135° 16 m | S63.to_S59 (left) | ok |

**S60 Trieda pred technickou výstavkou v roku 1982** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S60.to_S59 | up | classroom door at the left end of the front wall (same as S14.to_S13) | [337, 376, 168, 344] → [418, 758] | S59 | walk | 229° 42 m | S59.to_S60 (up) | ok |

**S61 Školský dvor s mladou lipou v roku 1982** — camera 225° (as S17)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S61.to_S58 | left | the yard asphalt continues out of the left edge in front of the running track, past the SE end of the main... | [0, 722, 60, 190] → [70, 820] | S58 | walk | 271° 93 m (→ right) | S58.to_S61 (right) | COMPASS |
| S61.to_S64 | down | the asphalt runs towards the camera: back past the south end of the main wing to the service window on the... | [380, 950, 460, 110] → [610, 995] | S64 | walk | 225° 64 m (→ up) | S64.to_S61 (right) | ok |
| S61.to_S66 | right | the yard asphalt continues out of the right edge past the near end of the court fence towards the garden sh... | [1800, 722, 120, 293] → [1850, 880] | S66 | walk | 101° 117 m (→ left) | S66.to_S61 (left) | COMPASS |

**S62 Sídliskový obchod v roku 1982** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S62.to_S57 | right (named) | the pavement below the fence continues out of the right edge towards the stop (S57.to_S62 is the far end of... | [1700, 971, 220, 44] → [1890, 1006] | S57 | walk | 97° 85 m | S57.to_S62 (up) | ok |
| S62.to_S65 | left (named) | the side street in front of the shop continues out of the left edge towards the small service building by t... | [0, 892, 60, 123] → [40, 950] | S65 | walk | 135° 76 m | S65.to_S62 (left) | ok |

**S63 Fyzikálny kabinet v roku 1982** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S63.to_S59 | left | door in the left wall to the corridor and the entrance hall (same as S15.to_S13) | [55, 395, 135, 560] → [190, 935] | S59 | walk | 315° 16 m | S59.to_S63 (right) | ok |

**S64 Tóno a dedo pri servisnom okne v roku 1982** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S64.to_S61 | right | the path round the building corner into the school yard with the young linden (right edge) | [1856, 780, 64, 235] → [1840, 950] | S61 | walk | 45° 64 m | S61.to_S64 (down) | ok |

**S65 Výdajňa školského údržbového materiálu v roku 1982** — camera heading not recorded

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S65.to_S62 | left | the half-glazed entrance door in the back wall at the left, out to the courtyard and the shop | [90, 362, 200, 380] → [190, 785] | S62 | walk | 315° 76 m | S62.to_S65 (left) | ok |

**S66 Školský záhradný sklad v roku 1982** — camera 90° (yard edge looking E at the shed)

| exit | side | painted way | zone / point | to | travel | real direction | return exit | flags |
|---|---|---|---|---|---|---|---|---|
| S66.to_S61 | left | the trodden path continues out of the left edge back to the school yard | [0, 722, 120, 293] → [70, 880] | S61 | walk | 281° 117 m (→ down) | S61.to_S66 (right) | ok |
<!-- exits:end -->
