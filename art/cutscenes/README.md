# Cutscene and epilogue frames (style A)

2026-10-05. One 1920x1080 painting per cutscene beat (game.json `cutscenes[]`, 9 cutscenes, 22 beats) and per
epilogue shot (`epilogue[]`, 9 shots): 31 frames. Generator `fal-ai/nano-banana-pro/edit`, 2K 16:9, USD 0.15 per call,
all calls in `art/spend-log.csv` under `cutscenes/` (42 calls, USD 6.30; 11 rejected attempts, 4 free local retouches).

| what | where |
|---|---|
| shipped frames | `src/game/assets/cutscenes/<CS>_<n>.webp` (n from 1), `EPILOGUE_<n>.webp` (epilogue data order) |
| masters + sidecars (prompt, references, seed) | `art/cutscenes/<shot>_v<N>.png/.json` |
| reference cards (keyed sheets on grey, item icons, crops) | `art/cutscenes/refs/` |
| shot briefs, references, camera moves | `art/tools/cutscene_shots.py` |
| tool | `art/tools/cutscenes.py` (list, prompt, paint, retouch, export, camera, contact) |
| camera data read by the game | `src/game/data/cutscene_camera.json` (written by `cutscenes.py camera`) |

## How a frame is made

`cutscenes.py paint <shot>` sends, in this order: the place (the room's painted background `src/game/assets/bg/<room>.webp`,
or for rooms not painted yet their licensed reference photos from `art/source/rooms/<room>/` plus a painted room of the game
as style reference), the approved character sheets (keyed, on a neutral grey card, so no chroma green leaks into the scene),
item icons for props, and for follow-up beats an already approved frame (`frame:<shot>`) so the room and people stay the
same across a cutscene. The prompt = image roles + the shot brief (English, from the Slovak `shot`) + the approved
character briefs from `art/characters/characters.json` + composition rules (the player's letterbox covers the top and
bottom tenth; no text unless quoted) + the canonical style-A sentence read from `design-doc/ART_DIRECTION.md`.
`export` cover-fits the 2752x1536 master to 1920x1080 WebP q90 (`--crop` first if the model painted its own bars).
`retouch` blanks stray lettering in a box (free, new master version).

## Frames and verdicts

| shot | final | notes |
|---|---|---|
| CS01_1 | v1 (crop) | phone photo, "Mira" smears, "Adam" stays; the model painted black bars, cropped away on export (1.18x, slightly softer) |
| CS01_2 | v1 | ring glow in S10, Adam with a brass rim light |
| CS01_3 | v1 | S11 1995 stop, red-cream tram leaving, Adam alone |
| CS02_1 | v1 | cassette deck reels, phone waveform, transcript; small PLAY/RECORD button labels |
| CS02_2 | v1 | Adam silent; the 10-year-old in the yard with the same gesture |
| CS03_1 | v1 | chronometer wheels read 1962 (NB2 crop edit 2026-10-06, `fixes/CS03_1_1962_v1`; Ivanka shown as 1962) at a Danube shelter, Bratislava castle and St Martin's across the river |
| CS03_2 | v2 | v1 rejected: readable gibberish names; v2 ink scribbles, one row dissolving |
| CS04_1 | v1 | 1960 attic, young Mira closes the box, Adam holds the imprint |
| CS04_2 | v2 | triptych 1960s / 1995 / 2020 of the same box; v2 = v1 with the stray label "Matika '95" blanked |
| CS05_1 | v3 | v1 rejected (clock-face chronometer, labels); v2 + "FORM" blanked = v3; photo with a few blank specks |
| CS05_2 | v1 | bag closed, chronometer 2035 |
| CS06_1 | v3 | v1 rejected: Rotunda drawn as a chapel; v2 Rotunda + stations from the summit photos; v3 = v2 with the port X turned into + (PT-S21) |
| CS06_2 | v3 | v1 rejected: Viktor seated with a third arm on the switch; v3 = v2 with the port X turned into + (PT-S21) |
| CS07_1 | v3 | v1 rejected: invented Slovak/English screen and paper text, console unlike CS06; v3 = v2 with the port X turned into + at 0.8 size (PT-S21; the ORIGIN folder in the tray already shows +) |
| CS07_2 | v3 | v1 + stray "INCIDENT REPORT" blanked; Nina on a tablet; v3 = v2 with the port X turned into + (PT-S21) |
| CS07_3 | v1 | S06 house, Adam outside, Mira behind the closed window, the photo inside |
| CS07_4 | v2 | v1 rejected: house and Adam off the S06 / CS07_3 model |
| CS07_5 | v1 | dusk, the gate bell; space left for the end title |
| CS08_1 | v1 | one yard 1982 / 1995 / 2020 blended left to right, phone screenshot of the bare asphalt |
| CS08_2 | v2 | v1 rejected: 1982 snow and lath fence in the 2020 background |
| CS09_1 | v2 | v1 rejected: caricature face, reflections; sign BIELA PÚŤ – PRIEHYBA |
| CS09_2 | v1 | sign FUNITEL PRIEHYBA – CHOPOK; the cabins look like small gondolas, not the large funitel cabins |
| EPILOGUE_1 | v1 | Bodka with the red ball, Lenka |
| EPILOGUE_2 | v2 | v1 rejected: gibberish poster text; v2 "SUSEDSKÁ POMOC 9.00 – 17.00" |
| EPILOGUE_3 | v1 | team photo in the Rotunda gallery, Adam |
| EPILOGUE_4 | v2 | Tamara listening to the radio; v2 = v1 with a stray English chalk word blanked |
| EPILOGUE_5 | v2 | v1 rejected: mural was not panel blocks; v2 Petržalka blocks, every window a different light |
| EPILOGUE_6 | v1 | Béla on the sill, Alojz closes the ledger; wall calendar reads 1962 (local edit 2026-10-06); calendar weekday letters are not Slovak (tiny) |
| EPILOGUE_7 | v1 | Rudo's first line, Lída holding back laughter |
| EPILOGUE_8 | v1 | Tamara hands Očko the card ĎAKUJEM |
| EPILOGUE_9 | v2 | v1 rejected: 12-year-old Jana with grey-green hair, drawing upside down |

Places without a painted room (S16, S30, S40, S49, S41, S67, S43, S47, S33, S34, S17/S55/S61) are painted from their
register photos; when those rooms are painted later, the frames may differ in detail from the room art. The chamber of
CS06/CS07 (S49, fictional interior) is invented: light wood panels, the steel console plate with the four symbols, the
real Rotunda through the window.

**Port symbols (2026-10-05, ISSUES PT-S21):** the room S49 and the journal read circle, plus, square, triangle; the
four console frames had painted an X. `art/tools/art_fixes.py ports` (free, local) lifts the X's own painted strokes
off an in-painted plate, turns them upright (angle searched 30-60 deg, 41.5-44.5 found) and puts them back, so the
engraving and brushwork are the painting's; before / after crops in `build/screens/fixes/art/ports_*.png`.

## Camera moves

17 beats carry a slow pan or zoom (`cutscene_shots.py` `CAMERA`): rects [x, y, w, h] of the 1920x1080 frame, 16:9,
zoom at most 1.33x, over the beat's `duration_min_s`, ease in-out; CS09_1 starts with a rect reaching into the top
letterbox margin so the cabin sign is visible under the bar. `cutscenes.py contact` draws the from (yellow) and to (cyan)
rects on a contact sheet. The player: `src/game/scripts/UI/Cutscenes/CutsceneCamera.cs` + `CutscenePlayer.cs`.

## Jasná 2035 in winter (owner 2026-10-06)

Every frame set in Jasná 2035 was turned into 6 February 2035 (docs/DECISIONS.md "Jasná 2035 is in winter") with
`art/tools/winter_jasna.py run <SHOT>` (one Nano Banana Pro edit of the shipped summer frame, USD 0.15, scope
`cutscenes/winter/<SHOT>/`; prompt and composite config `art/prompts/winter/<SHOT>.txt / .json`). The summer frames
are kept only here as `<SHOT>_summer.webp`. People and objects keep their summer pixels: window frames use
`diff_regions` (the model output is taken only where it changed the view behind the glass), the two CS09 frames are
full edits with the sign protected. Reviews: `art/review/natural/winter/<SHOT>_v<N>_winter.jpg`.

| shot | final | winter |
|---|---|---|
| CS06_1 | v4 | the Rotunda through the chamber window under snow, icicles, rime, frost flowers; Viktor, reader, glass unchanged |
| CS06_2 | v4 | same window; Viktor, Adam, console unchanged |
| CS07_1 | v4 | the window at the right edge frosted with ice flowers and a drift; plate, ports, cassette, hand unchanged |
| CS07_2 | v4 | the snowy Rotunda behind Viktor and the tablet; the signature and Nina's call unchanged |
| CS09_1 | v3 | the resort in deep snow with pistes and skiers through every window, frost rims, snow tracked in; Adam in the 1982 winter coat and mustard scarf (reference `actors/ADAM/idle_front_coat1982`); sign BIELA PÚŤ – PRIEHYBA kept |
| CS09_2 | v2 | snowy slope through the open side, snow on the cabin roofs, snow and boot prints on the platform; Adam in coat and scarf; sign FUNITEL PRIEHYBA – CHOPOK kept |
| EPILOGUE_3 | v2 | white mountains through both gallery windows, frost; team photo and Adam unchanged |
| EPILOGUE_4 | v3 | laden spruces behind Tamara; everything inside unchanged |
| EPILOGUE_5 | v3 | white mountains and snowy spruces through the gallery windows (left region widened to the panel in a free re-composite) |
| EPILOGUE_8 | v2 | laden spruces through the café windows and the far window; ĎAKUJEM card unchanged |
| EPILOGUE_9 | v3 | only the 2035 panel: snowy mountains and spruces behind Jana; the 1982 and 2020 panels unchanged |

Not changed: EPILOGUE_1, 2, 6, 7 (other places and eras); CS05 (2020 workshop). Cost: 11 calls, USD 1.65.
