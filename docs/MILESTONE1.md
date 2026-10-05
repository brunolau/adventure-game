# Milestone 1 - the prologue (G01-G11, P01, CS01, arrival in S11 in 1995)

Status 2026-10-05: **playable end to end with the real assets.** Eleven painted rooms (S01-S11),
sprite actors (Adam, Ela, Dana, Mira, Roman, Lenka, Jozef), ambient layers, the UI agent's HUD,
inventory, subtitles, P01 puzzle modal, cutscene player and era card. The prologue was played through
the normal input path (walking, clicks, real mouse and key events, the puzzle solved by clicking in the
modal) and the input rules were checked in the engine. What still uses a placeholder is listed below.

## How to play

1. Double-click `play.bat` in the repository root. It builds the C# code, imports new assets and opens
   the game window (Godot 4.7.2 .NET in `.tools/godot/`, .NET SDK 8 or newer).
2. In the main menu choose **Nová hra**. The window title says "(DEBUG)" because play.bat runs the editor
   binary; that is expected for now.

Controls (binding, from CODING_AGENT_START.txt):

| input | what it does |
|---|---|
| left click | the one action on the target (walk, take, talk, use the selected item); on a line: next line |
| right click | look at the target; on empty floor: open the bag; with an item on the cursor: drop the item first |
| Space | show the names of everything you can click (hotspots, people, exits); on a line: next line |
| I / J / M / H | bag / journal / map / hints |
| Tab, Shift+Tab, Enter, Backspace | keyboard focus over targets, Enter = left click, Backspace = right click |
| Esc | drop the item, else pause menu; during a cutscene: skip |
| F5 / F9 | quick save / quick load |

Prologue route (spoilers): take the service bag in the garage (S01) → talk to Ela at the volunteer point
(S03) → give Mirka's order to Dana at the shop window (S04) → leave the bag on the tray at Mirka's gate
(S05) → talk to Mira through the window (S06) → open the shed with her key (S05) → take the chronometer
from the brass case (S09) → open the ZVON service cover with the bag (S10) → take the matching fuse from
the garage socket (S01) → put the fuse in (S10) → match the three shapes on the panel (P01) → cutscene
CS01, era card "1995 Bratislava 15. júna 1995", arrival at the Dúbravka stop (S11).

## What was verified (2026-10-05)

| check | result |
|---|---|
| `dotnet build src/LastBell.sln` | OK, 0 warnings |
| `dotnet test src/LastBell.sln` (Core) | 286 passed, 0 failed, 3 skipped (AT08, AT19, AT20: presentation-level, not Core) |
| `python tools/check_strings.py` / `tools/extract_strings.py --dry-run` | OK (2943 keys, no errors) |
| Godot `--headless --import` | OK, no errors |
| `--headless --time-scale 6 -- --fast-text --play 11` (prologue through the input path) | all 11 actions committed, ends in S11 / 1995 with inventory PHONE, TOOLS, SHEDKEY, CHRONO |
| `-- --fast-text --acceptance` headless (1600x900) and in a 1280x720 window | 19/19 PASS (log: `build/screens/m1/logs/acceptance_summary.txt`) |
| `play.bat` | builds, imports, opens the window (title "Posledný zvonec (DEBUG)"), log without errors |
| P01 by real mouse clicks in the modal (left shape → right shape, three pairs, Potvrdiť) | solved, G11 committed once |

The acceptance checks (`src/game/scripts/Diagnostics/PrologueAcceptance.cs`, run with
`<console exe> --headless --path src/game --time-scale 4 -- --fast-text --acceptance`) drive real Godot
input events:

- right click on a hotspot: look text, no walk, no state change; right click on empty floor: bag opens; I closes it;
- Space toggles the labels on and off;
- an invalid item click (TOOLS on the fuse socket before G08): no walk, no text, selection kept, no state change;
  its hover shows the name only, while ORDER over Dana shows "Vyzdvihnúť Mirkin nákup";
- right click with an item on the cursor cancels the item first (the bag does not open);
- a taken prop is gone and cannot be taken twice;
- re-check on arrival: click Dana with ORDER, drop the item while Adam walks → nothing is committed on arrival;
  the same click with the item commits G03 once;
- save while G03's line plays, play on (G04), load → back in S04 with exactly one GROCERIES, no ORDER;
  clicking Dana again adds nothing;
- save after G05, play G06, load → exact state of the save; the prologue then continues normally;
- save with the P01 modal open → the load resumes in the world (ISSUES GAME-02), the puzzle reopens;
- a wrong P01 answer commits nothing; the right one commits G11 once and arrives in S11 / 1995 with
  CHRONO, PHONE, SHEDKEY, TOOLS.

## Screenshots (`build/screens/m1/`)

Local files (`build/` is git-ignored); regenerate them with the command below the table.

| file | what to look at |
|---|---|
| `00_S01_start.png` | new game, first-entry line, Adam in the garage |
| `act01_G01_S01.png` | G01: bag taken (shelf now empty), toast "Do brašny pribudlo", new goal |
| `act02_G02_S03.png` | G02: Adam beside Ela (no longer covering her), subtitle |
| `act03_G03_S04.png` | G03: hand-over at Dana's window, no shadow on the wall under the bust |
| `act04_G04_S05.png` | G04: groceries on the tray |
| `act05_G05_S06.png` | G05: Mira at the window on the phone, Adam beside the window |
| `act06_G06_S05.png` | G06: shed unlocked (padlock gone, see `room_S05.png`) |
| `act07_G07_S09.png` … `act10_G10_S10.png` | G07-G10 with their lines and gestures (use_tool for G08) |
| `act11a_G11_S10_hover_panel.png` | hover text over the panel (name only, no item) |
| `act11b_G11_P01_modal.png` | P01 modal opened by a real click in the room |
| `act11c_G11_P01_solved_device_line.png` | success toast + "Referencia 1995 obnovená" |
| `act11d/e/f_CS01_beat1..3.png` | CS01 (styled cards, see gaps), subtitles, skip button |
| `act11g_era_card_1995.png`, `act11h_arrival_S11_1995.png` | era card and the S11 arrival with the first-entry line |
| `room_<S01..S11>.png`, `room_<id>_labels.png` | every prologue room with art, actors, ambient, HUD; and with Space labels |
| `ui_inventory_open.png`, `ui_hover_valid_item_S04.png`, `ui_hover_invalid_item_S01.png`, `ui_right_click_look_S01.png` | bag with item icons, item hover rules, look bubble |
| `play_bat_launch_S01.png` | a play.bat launch (harness args) |
| `g11seq/` | the whole G11 → CS01 → era card → S11 sequence as frames |

Reproduce a capture: `<console exe> --path src/game --resolution 1920x1080 --time-scale 3 -- --lines --play 5 --wait 1800 --screenshot build/screens/m1/act05_G05_S06.png`
(relative paths are taken from the repository root).

## Integration fixes made in this pass (cross-module edits noted)

- **Hero beside the NPC** (world runtime `Room.ApproachPoint`, `InteractionController`): the data puts every
  NPC interaction point straight below the NPC, so Adam covered Ela, Dana and Mira while talking (ISSUES INT-03 / LIVING-02).
- **No shadow under window busts** (`IActorVisual.CastsShadow`, world runtime; `SpriteActorVisual`, living world) (INT-02).
- **Prop state patches** (`art_overrides.json state_patches`, world runtime `ArtOverrides` / `Room`; three local
  patches in `src/game/assets/variants/`, no paid call): S01 shelf empty after G01, S05 groceries on the tray
  after G04, S05 shed unlocked after G06 (INT-04 / ART-VAR-01).
- **Space no longer presses GUI buttons** (`InputActions.EnsureDefaults` removes Space from `ui_accept`): in the
  open bag Space used to select the focused item (INT-01).
- **QA harness**: canvas → window coordinate mapping (hover/raw input were wrong at any size but 1920x1080),
  relative screenshot paths from the repo root, real input events (`mouse:`, `rmouse:`, `keyev:`), `--acceptance` (INT-05).
- `DialoguePresenter.IsShowingBark` (read-only, for the checks). Docs: `src/game/README.md`, `scripts/Living/README.md`.

No Core behaviour, game.json, walkthrough or localization text was changed.

## Known issues and gaps (for milestone 2)

1. **CS01 has no pictures** - the three beats are styled cards; debug builds (play.bat) also show the stage
   direction as a dev note (INT-06). Needs three style-A beat paintings (~USD 0.45) for all nine cutscenes eventually.
2. **Hotspot rects are the handoff template** (ART-BLOCK-01): every room has its props in one row near the top, so the
   paintings hang them high (shelves, raised plots, a doormat on the fence). It reads, but it is a convention the
   handoff owner should confirm or re-block from the paintings (game.json change); S51/S57 need it (ART-STOP-01).
3. **More prop states**: Dana's basket stays on her table after G03; the S09 case looks closed after G07; the S06
   photo should fade after G11 (ART-VAR-02). The new `state_patches` hook is ready for them.
4. **NPC interaction points** in game.json should move beside the NPC (LIVING-02); the presentation works around it.
5. **Toasts** ("Do brašny pribudlo", "Nový cieľ") sit over the top hotspot row for a few seconds; the P01 success
   line appears as a toast, not as a subtitle.
6. **Texts with internal ids** in player-visible strings, e.g. the P01 clue "S10.panel: spoj rovnaké tvary"
   (TEXT-01) - rewrite in `world.csv`.
7. **No sound**: no SFX (`actions[].sfx`), music or ambience files yet; no voice-over.
8. **S11 tram is painted** into the background, so it cannot arrive or depart as CS01 describes (LIVING-05).
9. **Open product-owner decisions**: S57 tram in 1982 (ART-DUBEXT-01), fuse value on the icons, ORDER icon handwriting
   (ART-ITEM-01), Ela seated vs standing in S03 (ART-NPC-01).
10. Mobile: sprite strips wider than 4096 px (LIVING-04); no touch long-press yet.
11. Beyond S11: all 94 main-route steps replay through Core in the engine (`-- --replay 94`, verified), but the
    input-path play after step 11 was not re-run in this pass, and the 57 rooms after S11 have no paintings, actors
    or ambient yet (dev blockout) - milestone 2 scope.

## Spend so far (art/spend-log.csv)

Total **USD 23.82** in 147 logged paid calls (no paid call in this integration pass):

| scope | USD | calls |
|---|---:|---:|
| characters (Adam set, NPC sets, idles) | 15.92 | 94 |
| backgrounds (`bg/` + `backgrounds/`) | 5.40 | 36 |
| ambient sprites | 1.32 | 8 |
| style tests | 0.90 | 6 |
| item icons | 0.28 | 3 |
