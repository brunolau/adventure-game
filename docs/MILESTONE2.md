# Milestone 2 - all main and side content through the real input path

Status 2026-10-05: **every action, quest, puzzle, cutscene, era, portal, variant layer and causal effect in
game.json can be played through the real input path, including the ending and the postgame.** The content
part of milestone 2 from CODING_AGENT_START.txt ("import a priechod všetkými main aj side dátami bez
grafických blokád") is met. The 57 rooms after S11 still use the dev blockout. After the prologue, NPCs use
the character agent's sprite sheets where they exist and the placeholder figure where they do not. This
milestone allows both.

## Coverage in numbers

| what | covered | how |
|---|---:|---|
| main actions | 94 / 94 | committed through real input in all four runs (A, B, C7, C42) |
| side actions | 33 / 33 | all four runs; run A does them after the credits, runs B, C7 and C42 interleave them with the main route |
| side quests | 9 / 9 | all four runs; Q9 completes with Q9C, and Q9D/E/F were done as well |
| main quests | 17 / 17 | all four runs |
| puzzles P01-P05 | 5 / 5 | solved by clicking the modal's controls and its confirm button (all runs); also wrong answer x10, close, save, load, then solved once (AT07); P02 at 200 % HUD (AT08) |
| cutscenes | 9 / 9 (21 / 21 beats) | every beat shown in runs A and B; skipped with Esc in C7, C42 and AT16, with the same final state as watching them |
| rooms | 68 / 68 | entered in every run; Space labels and a clickable point for every target in all 68 rooms (AT05/AT20) at 1280x720, 1920x1080 and headless 1600x900 |
| eras / portals | 5 / 5 eras, 6 / 6 anchor nodes | every portal hop uses T and a click on the era button; the postgame era tour leaves the inventory unchanged |
| cache 1982 -> 2020 | E04 → E06 → E08 → D05 (P05) → D06 → J05 | ends at stage `Used`; the single-lineage invariant holds (all runs, AT26) |
| butterfly effects | BF_TREE, BF_JANA | both triggered; their 7 variant layers show on re-entry (as dev markers in the blockout rooms) |
| visual variant layers | 9 / 9 | each seen visible in its room in every run (screenshots `variant_*`) |
| causal effects | 14 / 14 (27 / 27 effect@room) | each seen active in every listed room in every run (screenshots `causal_*`); AT21 checks before and after |
| epilogue selection | 0 shots in A, 9 shots in B, C7, C42 | A has no side quest done before the finale, so it goes straight to the credits. After A's postgame side quests, the album replay shows the 9 new shots without a second transaction |
| postgame | return items, free play, era tour, cable cars after F09, album replay, CS07 replay | all four runs (the `postgame` block of each coverage file) |
| dialogue line ids | 1090 / 1090 | run B with `--all-lines` shows 1088: every action, cutscene, entry and topic line, every item look, and 254 of 256 hotspot looks. The acceptance checks show the last two looks (S55.ambient 1 before E10, S06.photo after C04) |
| save / load after every action | 127 / 127 | run A (`--save-load-each`): the state is identical after each load |
| GUI blockers | 0 | in no run was a target, slot, topic, era, puzzle or ending control covered or unreachable |

The four runs (`build/screens/m2/coverage_<run>.json`, logs in `build/screens/m2/logs/`):

- **A**: window 1920x1080, `--play-all --save-load-each --shots build/screens/m2/routeA`. All 94 main actions,
  then the ending with no episode yet, then all 33 side actions after the credits (AT14, AT28: the story is
  finished without Q9C), then the postgame. 210 JPEG screenshots in `build/screens/m2/routeA/`.
- **B**: headless, `--play-all --interleave early --all-lines`. Every side action is done as soon as it is
  legal, so the ending shows all nine episodes. The run looks at every target on every arrival and at every
  item when it is received, and chooses every ambient topic.
- **C7 / C42**: headless, `--play-all --interleave seed:7|42 --skip-cutscenes`. Side actions happen at seeded
  random legal points of the main route, and every cutscene is skipped with Esc. The final inventory, done set
  and side rewards are identical to A and B (AT16 across whole runs).
- Earlier in this pass, before the fixes below: `--play 94` through the old submit path (94/94) and
  `--play-all` headless (127/127).

### Reproduce

```
set G=.tools/godot/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe
dotnet build src/LastBell.sln
%G% --path src/game --resolution 1920x1080 --time-scale 6 -- --fast-text --play-all --save-load-each --shots build/screens/m2/routeA --coverage build/screens/m2/coverage_A.json
%G% --headless --path src/game --time-scale 8 -- --fast-text --play-all --interleave early --all-lines --coverage build/screens/m2/coverage_B.json
%G% --headless --path src/game --time-scale 8 -- --fast-text --play-all --interleave seed:7 --skip-cutscenes --coverage build/screens/m2/coverage_C7.json
%G% --headless --path src/game --time-scale 4 -- --fast-text --acceptance
python tools/m2_coverage.py build/screens/m2/coverage_A.json build/screens/m2/coverage_B.json build/screens/m2/coverage_C7.json build/screens/m2/coverage_C42.json
```

A full window run takes about 25 minutes at `--time-scale 6`; a headless run takes 5-9 minutes. Window runs
inject real input events and move the desktop cursor, so do not use the mouse while one is running.

## What "real input path" means here (QA harness, `src/game/scripts/Diagnostics/`)

`RealInputDriver.cs` (`--real`, implied by `--play-all` and `--play-side`) drives the game only with OS-style
Godot input events. Each event goes through the GUI first and then the InputRouter:

- A world target or exit is clicked at a point inside its rect where the room's own hit test returns that
  target **and** `Viewport.GuiGetHoveredControl()` is null. If no such point exists, the run reports
  `BLOCKER` (a graphic blocker) and fails.
- An item is selected by opening the drawer (I) and clicking its slot button. A combination clicks the second
  slot. The drawer is closed with I, and a kept item is dropped with Esc.
- Topics are chosen by clicking the topic menu's button. A menu still open after the lines is closed with Esc.
- Puzzles are solved by clicking the modal's own buttons (matching pairs, rotate, digit up, grid cell) until
  the modal's draft equals the solution, then clicking its confirm button.
- Portals: T opens the era chooser and the era button is clicked. Exits: the exit zone is clicked.
- The ending: one click per epilogue shot, Esc to close the rolling credits, and a click on the postgame
  note's button. The album replay and the CS07 replay are started from the journal's buttons (J, album tab).
- Lines play out by auto-advance (`--fast-text` shortens the holds). Esc is pressed only with
  `--skip-cutscenes`.

For the acceptance checks, states are prepared through Core rule calls: travel over exits and portals, and
commits, which are the same calls the presentation makes. No item is ever granted. Every checked step then
uses real input.

## In-engine acceptance (`--acceptance`, 59 checks)

`--acceptance` runs the 19 prologue checks from milestone 1 (`PrologueAcceptance.cs`) and 40 new checks
(`ContentAcceptance.cs`; run them alone with `--acceptance m2`). Results: **59 / 59 PASS headless (1600x900)**.
The window runs at 1280x720 and 1920x1080 (`--time-scale 3`) passed 57 / 57; they ran before the two AT24 look
checks were added.

| AT row | check(s) | result |
|---|---|---|
| AT02 | BALL over the cassette deck: no action text, and the click is a full no-op (no walk, selection kept) | PASS |
| AT03 | BELT_NEW over the deck: action text only while B06 exists; committed once; never again | PASS |
| AT04 | right click on an item in the drawer: cancels the selection first, then looks; the drawer stays open | PASS |
| AT05 | Space in all 68 rooms: labels match Core's HotspotList (visible NPCs, props incl. atmospheric, exits) and no hidden one | PASS 68/68 |
| AT06 | Space with BELT_NEW selected: names stay, only valid targets are outlined, wrong targets have no action text | PASS |
| AT07 | P01-P05: wrong answer confirmed 10x (no commit, no consumption), close, save, load, solve: committed once | PASS 5/5 |
| AT08 | P02 solved by clicks at 200 % HUD scale (the puzzle uses no audio) | PASS |
| AT09 | B10/B11 and I04/I05 combined in reverse selection order: same action, consumption and product | PASS |
| AT11 | first entry to 1960, then 1995, 2020 and back to 1960 by portals: inventory unchanged | PASS (also the postgame era tour in every run) |
| AT12 | map: an unvisited node does nothing, a reachable visited node fast-travels; CanFastTravel is set only when a route exists | PASS |
| AT15 | the four ports in reverse order (F15..F12): F16 never becomes available earlier, and the selection is cleared | PASS (all 24 orders: Core tests) |
| AT16 | each of the 9 cutscene actions, watched vs skipped with Esc: identical state | PASS 9/9 |
| AT17 | save/load in the middle of CS06 (F11) and CS07 (F17): same line id, no second reward, the ending still plays | PASS (after fixing M2QA-03) |
| AT18 | a corrupt save file and a save with an unknown item: refused with the readable message, game untouched | PASS |
| AT19 (part) | keyboard only: Tab focus + Enter takes the bag, uses an exit, talks to Ela and chooses the topic | PASS |
| AT20 | every visible target in all 68 rooms has a clickable point not covered by the HUD | PASS at 1280x720, 1920x1080, headless |
| AT21 | S15 / S43 / S47 before and after Q9C / Q4C / Q5C: the effect appears only after the trigger, on re-entry | PASS 3/3 |
| AT22 | triple click on the bag, then click spam on the last line: G01 committed once, one TOOLS, no click falls through (no walk) | PASS |
| AT23 | pause for 30 s (game time) plus the journal before F09: nothing changes, and F09 is still possible | PASS (30 game-seconds, not 30 minutes) |
| AT24 (part) | the two looks that only exist in state windows the play runs do not visit | PASS (line audit above: 1090/1090) |
| AT25 | S17 and S55 before E10 have no variants and after E10 both do; every target is reachable on foot; PHOTO2020 is kept | PASS |
| AT26 | after D05, back in 1982: the niche gives nothing, there is no second young cup, and the lineage invariant holds | PASS |
| AT29 | before J02: no route and no fast travel from Biela Púť to the Rotunda; J02-J04 ride; the return ticket is kept | PASS |
| AT01, AT10, AT13, AT14, AT27, AT28, AT30 | covered by the play runs (AT13, AT14, AT28: run A; AT30: postgame cable cars) and the Core tests (AT10, all 24 orders of AT15, AT27) | yes |
| AT19 (full), AT24 (release audit) | incomplete: only the four keyboard steps above; the release audit needs the final art | open |

Core: `dotnet test src/LastBell.Core.Tests` gives 286 passed, 0 failed, 3 skipped (unchanged; Core was not
changed in this pass). `python tools/check_strings.py` is OK (one new ui key, `ui.dev.causal_active`).

## Bugs fixed (cross-module edits are also in design-doc/ISSUES.md)

| id | module | bug | fix |
|---|---|---|---|
| M2QA-01 | UI `Menus/PortalChooser.cs` | **Blocker**: the era chooser opened as a bare title row with no era buttons, so no player could travel by chronometer after the prologue. | `FitTarget = list`. |
| M2QA-02 | UI `Cutscenes/EndingSequence.cs` | A click did not advance the epilogue shots (the panel swallowed it). | The panel and the body now pass mouse events. |
| M2QA-03 | UI `UiRoot.cs` | Loading a save made during F17's lines or CS07 lost the ending (epilogue, credits, postgame note). | The ending is pending again after such a load. |
| M2QA-04 | UI `Hud/ToastLayer.cs` | Milestone-1 item 5: toasts covered the top hotspot row and the cutscene cards. | The toast column picks the slot with the least overlap with the room's targets and labels; notices wait during cutscenes. |
| M2QA-05 | UI `Puzzles/PuzzleModal.cs`, Presentation `DialoguePresenter.cs` | Milestone-1 item 5: the P01 success line appeared as a toast. | New `DialoguePresenter.ShowPreface`: every puzzle's success line is spoken as a subtitle before the action's lines (`build/screens/m2/p01/001_puzzle_P01_solved_line.jpg`). |
| M2QA-06 | UI `Cutscenes/CutscenePlayer.cs`, `Placeholders/PlaceholderPuzzlePanel.cs`, Runtime `PresentationSettings.cs` | Milestone-1 item 1 / INT-06: debug builds (play.bat) showed stage directions on cutscene cards and a solve button on the placeholder puzzle. | `PresentationSettings.DevNotes`, set only with `--dev`. |
| M2QA-07 | World `Room.cs`, `DevBlockout.cs` | Causal effects had no presentation at all. | Blockout rooms list their settled causal effects next to the missing-variant markers. This is a dev aid; the art must show the effects later. |

Harness additions (no change to game behaviour): `--real`, `--play-all`, `--play-side`, `--interleave`,
`--save-load-each`, `--skip-cutscenes`, `--all-lines`, `--shots`, `--coverage`, `--acceptance m1|m2`
(src/game/README.md), and `tools/m2_coverage.py`, which generates the tables below.

## Milestone-1 polish items (docs/MILESTONE1.md "Known issues")

| item | status |
|---|---|
| 1 CS01 without pictures; stage directions in debug builds | stage directions fixed (M2QA-06); beat paintings still open (all 9 cutscenes, 21 beats) |
| 2 hotspot rect template (ART-BLOCK-01) | open, needs a handoff decision (game.json) |
| 3 more prop states | open (art); the `state_patches` hook is unchanged |
| 4 NPC interaction points | open, handoff (LIVING-02); the presentation workaround works in all 68 rooms |
| 5 toasts over the hotspot row; P01 success line as a toast | fixed (M2QA-04, M2QA-05) |
| 6 internal ids in player-visible texts (TEXT-01) | **open, cannot be fixed in world.csv**: check_strings requires the sk text to equal game.json (M2QA-08) |
| 7 no sound | the audio agent is adding it in parallel (not part of this pass) |
| 8 S11 tram painted in | open (art, LIVING-05) |
| 9 product-owner decisions | open (ART-DUBEXT-01, ART-ITEM-01, ART-NPC-01) |
| 10 sheets over 4096 px | resolved by the character and build agents: no texture in `src/game/assets` is now wider or taller than 4096 px (BUILD-01) |
| 11 input-path play after S11 | done: this document |

## Open issues found or confirmed in this pass

1. **Graphics after the prologue (expected for this milestone)**: 57 rooms use the dev blockout. The 9 variant
   layers have no paintings (dev markers name the missing asset). Causal effects are dev text in blockout
   rooms and invisible in the painted S06 (the photo fade, ART-VAR-02). Cutscenes and epilogue shots are
   styled cards. Several NPCs fall back to the placeholder figure (warnings such as "Living: no usable sprite
   sheets for MARTA82 / RUZENA ...").
2. **TEXT-01** (M2QA-08): 27 quest hint-3 texts and the P01/P03/P05 clues contain internal ids. Fixing them
   needs a game.json change by the handoff owner.
3. **Window QA runs and the desktop cursor** (M2QA-09): the InputRouter reads the current mouse position, so
   another window that moves the cursor can steal a click. The harness re-warps the cursor before each button
   event and retries a travel click once (0 retries in the final run A). The prologue acceptance's
   re-check-on-arrival test is frame-timed and fails at `--time-scale 6` in a window; use 4 or less.
4. Audio was in progress during this pass. The logs show one load error for
   `res://assets/ambience/beds/fluorescent_hum.ogg` (the audio agent's files).
5. Not verified in this pass: AT19 end to end with the keyboard only, touch input (the touch agent's
   gestures), reduced motion, and the look-variant text of every hotspot at every intermediate state. The line
   audit covers every line id once, not every state combination.

## Evidence (`build/screens/m2/`, git-ignored; regenerate with the commands above)

- `routeA/NNN_act_<id>_<room>.jpg`: the 127 actions, 0.45 s after each commit. Because of `--save-load-each`,
  a few short inventory actions show the reload fade instead of the line. Also `cs_<CS>_beat<n>` (all 21
  beats), `puzzle_<P>_solved_line` (the success subtitles), `variant_*` and `causal_*` (first sight of each
  world change), `credits`, `postgame_note`, `postgame_era_*`, `postgame_journal_album`,
  `album_epilogue_01..09`, `album_credits`, `postgame_replay_CS07`.
- `p01/001_puzzle_P01_solved_line.jpg`: the P01 success line as a subtitle at normal text speed, with the goal
  toast below the prop row.
- `logs/`: `routeA.txt`, `routeB.txt`, `routeC7.txt`, `routeC42.txt`, `acceptance_all_headless.txt`,
  `acceptance_all_1280x720.txt`, `acceptance_all_1920x1080.txt`, `acceptance_m1_headless.txt`, `play94.txt`.

Screenshots looked at (sample): the P01 subtitle; the CS01 beat card (no stage direction); epilogue card 5/9;
the postgame note; the S55 and S15 blockouts with the variant and causal markers; S60 after Q9C with the goal
toast top right; the portal chooser bug before the fix.

## Coverage tables

Generated by `python tools/m2_coverage.py` from the four coverage files. "yes #n" means the action was
committed through real input as the n-th action of that run; "s/l" means save, load and compare passed right
after it (run A).

| run | label | actions committed (real input) | blockers | failures | lines shown | rooms | epilogue shots (ending, album) |
|---|---|---:|---:|---:|---:|---:|---|
| A | A: main route, ending, all side actions after the credits, postgame (window 1920x1080, save/load after every action) | 127 | 0 | 0 | 537 | 68 | 0, 9 |
| B | B: side actions interleaved greedily (as early as legal), ending with all nine episodes; looks at every target on every arrival, every item when received, every ambient topic (headless) | 127 | 0 | 0 | 774 | 68 | 9, 9 |
| C7 | C7: side actions at seeded random legal points (seed 7), cutscenes skipped with Esc (headless) | 127 | 0 | 0 | 507 | 68 | 9, 9 |
| C42 | C42: side actions at seeded random legal points (seed 42), cutscenes skipped with Esc (headless) | 127 | 0 | 0 | 507 | 68 | 9, 9 |

### Actions

| action | quest | room | kind | puzzle / cutscene | A | B | C7 | C42 |
|---|---|---|---|---|---|---|---|---|
| G01 | M01 | S01 | click |  | yes #1 s/l | yes #7 | yes #1 | yes #2 |
| G02 | M01 | S03 | topic |  | yes #2 s/l | yes #8 | yes #3 | yes #3 |
| G03 | M01 | S04 | click (ORDER) |  | yes #3 s/l | yes #9 | yes #4 | yes #4 |
| G04 | M01 | S05 | click (GROCERIES) |  | yes #4 s/l | yes #10 | yes #9 | yes #5 |
| G05 | M01 | S06 | topic |  | yes #5 s/l | yes #11 | yes #11 | yes #7 |
| G06 | M02 | S05 | click (SHEDKEY) |  | yes #6 s/l | yes #12 | yes #12 | yes #9 |
| G07 | M02 | S09 | click |  | yes #7 s/l | yes #13 | yes #13 | yes #10 |
| G08 | M02 | S10 | click (TOOLS) |  | yes #8 s/l | yes #14 | yes #14 | yes #11 |
| G09 | M02 | S01 | click |  | yes #9 s/l | yes #15 | yes #15 | yes #12 |
| G10 | M02 | S10 | click (FUSE) |  | yes #10 s/l | yes #16 | yes #16 | yes #13 |
| G11 | M02 | S10 | click | P01 CS01 | yes #11 s/l | yes #17 | yes #17 | yes #14 |
| B01 | M03 | S12 | click |  | yes #12 s/l | yes #22 | yes #21 | yes #15 |
| B02 | M03 | S13 | click (CHRONO) |  | yes #13 s/l | yes #23 | yes #22 | yes #17 |
| B03 | M03 | S14 | topic |  | yes #14 s/l | yes #26 | yes #23 | yes #18 |
| B04 | M04 | S16 | click (TOOLS) |  | yes #15 s/l | yes #31 | yes #24 | yes #19 |
| B05 | M04 | S20 | click (BELT_OLD) |  | yes #16 s/l | yes #32 | yes #26 | yes #21 |
| B06 | M04 | S16 | click (BELT_NEW) |  | yes #17 s/l | yes #33 | yes #28 | yes #22 |
| B07 | M05 | S27 | click (TAPE_RAW) |  | yes #18 s/l | yes #34 | yes #29 | yes #25 |
| B08 | M05 | S25 | click (TOOLS) |  | yes #19 s/l | yes #35 | yes #30 | yes #26 |
| B09 | M05 | S26 | topic |  | yes #20 s/l | yes #36 | yes #31 | yes #27 |
| B10 | M05 | inventory | combine (CONNECTOR) |  | yes #21 s/l | yes #37 | yes #32 | yes #28 |
| B11 | M05 | inventory | combine (BRAID) |  | yes #22 s/l | yes #38 | yes #34 | yes #30 |
| B12 | M05 | S16 | click (STEREOLINK) | CS02 | yes #23 s/l | yes #39 | yes #37 | yes #31 |
| B13 | M06 | S23 | click (LETTER) |  | yes #24 s/l | yes #40 | yes #40 | yes #33 |
| B14 | M06 | S24 | click (NEGATIVE) |  | yes #25 s/l | yes #41 | yes #41 | yes #34 |
| B15 | M06 | S22 | click (CALPHOTO) |  | yes #26 s/l | yes #42 | yes #42 | yes #35 |
| B16 | M06 | inventory | combine (OVERLAY) | P02 | yes #27 s/l | yes #43 | yes #43 | yes #36 |
| B17 | M07 | S29 | click (NODEMAP) |  | yes #28 s/l | yes #44 | yes #44 | yes #38 |
| B18 | M07 | S19 | topic |  | yes #29 s/l | yes #45 | yes #45 | yes #39 |
| B19 | M07 | S17 | click |  | yes #30 s/l | yes #46 | yes #46 | yes #42 |
| B20 | M07 | S30 | click (COIL) |  | yes #31 s/l | yes #47 | yes #47 | yes #44 |
| B21 | M07 | S30 | click (METRONOME) |  | yes #32 s/l | yes #48 | yes #48 | yes #45 |
| B22 | M07 | S30 | click | P03 CS03 | yes #33 s/l | yes #49 | yes #49 | yes #47 |
| I01 | M08 | S36 | click (CHRONO) |  | yes #34 s/l | yes #55 | yes #51 | yes #48 |
| I02 | M08 | S35 | click (SUPPLYSLIP) |  | yes #35 s/l | yes #56 | yes #55 | yes #49 |
| I03 | M08 | S34 | click (TOOLS) |  | yes #36 s/l | yes #57 | yes #57 | yes #50 |
| I04 | M08 | inventory | combine (PUNCH) |  | yes #37 s/l | yes #58 | yes #58 | yes #51 |
| I05 | M08 | inventory | combine (RIVETS) |  | yes #38 s/l | yes #59 | yes #59 | yes #53 |
| I06 | M08 | S38 | click (CUFF) |  | yes #39 s/l | yes #60 | yes #60 | yes #54 |
| I07 | M08 | S36 | topic |  | yes #40 s/l | yes #61 | yes #61 | yes #56 |
| I08 | M08 | S38 | click (PUMPKEY) |  | yes #41 s/l | yes #62 | yes #62 | yes #57 |
| I09 | M09 | S39 | topic |  | yes #42 s/l | yes #65 | yes #64 | yes #58 |
| I10 | M09 | S37 | topic |  | yes #43 s/l | yes #66 | yes #65 | yes #60 |
| I11 | M09 | S40 | click |  | yes #44 s/l | yes #67 | yes #66 | yes #61 |
| I12 | M09 | S39 | click (WAXPAPER) |  | yes #45 s/l | yes #68 | yes #67 | yes #64 |
| I13 | M09 | inventory | combine (STYLUS) |  | yes #46 s/l | yes #69 | yes #69 | yes #65 |
| I14 | M10 | S33 | click |  | yes #47 s/l | yes #70 | yes #70 | yes #67 |
| I15 | M10 | inventory | combine (CARBON) |  | yes #48 s/l | yes #71 | yes #71 | yes #68 |
| I16 | M10 | S33 | click (REGDOUBLE) |  | yes #49 s/l | yes #72 | yes #72 | yes #69 |
| I17 | M10 | S40 | click (REGISTERED) | CS04 | yes #50 s/l | yes #73 | yes #73 | yes #71 |
| C01 | M11A | S06 | click (ORIGIN) |  | yes #51 s/l | yes #74 | yes #74 | yes #72 |
| C02 | M11D | S03 | topic |  | yes #70 s/l | yes #98 | yes #98 | yes #98 |
| C03 | M11D | S02 | click (HANDOVER) |  | yes #71 s/l | yes #99 | yes #99 | yes #99 |
| C04 | M11D | S03 | click (HANDOVER_R) |  | yes #72 s/l | yes #100 | yes #100 | yes #100 |
| C05 | M11D | S10 | click (CHAIN) | CS05 | yes #73 s/l | yes #101 | yes #101 | yes #101 |
| F01 | M12 | S42 | topic |  | yes #74 s/l | yes #107 | yes #102 | yes #103 |
| F02 | M12 | S43 | click (TAPE) |  | yes #75 s/l | yes #108 | yes #104 | yes #106 |
| F03 | M12 | S44 | click (CHAIN) |  | yes #76 s/l | yes #109 | yes #106 | yes #108 |
| F04 | M12 | S46 | click (CATALOG) |  | yes #77 s/l | yes #110 | yes #107 | yes #109 |
| F05 | M12 | S47 | click (PHONE) |  | yes #81 s/l | yes #114 | yes #113 | yes #114 |
| F06 | M12 | S48 | click (READER) |  | yes #82 s/l | yes #115 | yes #114 | yes #115 |
| F07 | M13 | S45 | click (CHRONO) |  | yes #83 s/l | yes #116 | yes #116 | yes #116 |
| F08 | M13 | S48 | click (PULSE) |  | yes #84 s/l | yes #117 | yes #117 | yes #117 |
| F09 | M13 | S50 | click |  | yes #86 s/l | yes #119 | yes #119 | yes #119 |
| F10 | M13 | S48 | click |  | yes #87 s/l | yes #120 | yes #120 | yes #120 |
| F11 | M14 | S49 | click (LEA_MESSAGE) | CS06 | yes #88 s/l | yes #121 | yes #121 | yes #121 |
| F12 | M15 | S49 | click (ORIGIN) |  | yes #89 s/l | yes #122 | yes #122 | yes #122 |
| F13 | M15 | S49 | click (TAPE) |  | yes #90 s/l | yes #123 | yes #123 | yes #123 |
| F14 | M15 | S49 | click (CHAIN) |  | yes #91 s/l | yes #124 | yes #124 | yes #124 |
| F15 | M15 | S49 | click (PATCH) |  | yes #92 s/l | yes #125 | yes #125 | yes #125 |
| F16 | M15 | S49 | click | P04 | yes #93 s/l | yes #126 | yes #126 | yes #126 |
| F17 | M15 | S49 | click | CS07 | yes #94 s/l | yes #127 | yes #127 | yes #127 |
| Q1A | Q1 | S02 | topic |  | yes #95 s/l | yes #1 | yes #5 | yes #1 |
| Q1B | Q1 | S08 | click |  | yes #96 s/l | yes #2 | yes #7 | yes #8 |
| Q1C | Q1 | S02 | click (BALL) |  | yes #97 s/l | yes #3 | yes #8 | yes #23 |
| Q2A | Q2 | S07 | topic |  | yes #98 s/l | yes #4 | yes #2 | yes #6 |
| Q2B | Q2 | S03 | topic |  | yes #99 s/l | yes #5 | yes #6 | yes #40 |
| Q2C | Q2 | S07 | click (FLYER) |  | yes #100 s/l | yes #6 | yes #10 | yes #41 |
| Q3A | Q3 | S17 | topic |  | yes #101 s/l | yes #27 | yes #25 | yes #37 |
| Q3B | Q3 | S18 | topic |  | yes #102 s/l | yes #28 | yes #33 | yes #46 |
| Q3C | Q3 | S24 | click (TEAMNEG) |  | yes #103 s/l | yes #29 | yes #36 | yes #52 |
| Q3D | Q3 | S17 | click (TEAMPHOTO) |  | yes #104 s/l | yes #30 | yes #39 | yes #59 |
| Q4A | Q4 | S19 | topic |  | yes #105 s/l | yes #18 | yes #18 | yes #16 |
| Q4B | Q4 | S22 | topic |  | yes #106 s/l | yes #19 | yes #19 | yes #24 |
| Q4C | Q4 | S19 | click (SCORE) |  | yes #107 s/l | yes #20 | yes #38 | yes #32 |
| Q5A | Q5 | S28 | topic |  | yes #108 s/l | yes #21 | yes #20 | yes #20 |
| Q5B | Q5 | S13 | topic |  | yes #109 s/l | yes #24 | yes #27 | yes #29 |
| Q5C | Q5 | S28 | click (CHALK) |  | yes #110 s/l | yes #25 | yes #35 | yes #43 |
| Q6A | Q6 | S33 | topic |  | yes #111 s/l | yes #50 | yes #50 | yes #55 |
| Q6B | Q6 | S35 | topic |  | yes #112 s/l | yes #51 | yes #53 | yes #62 |
| Q6C | Q6 | S37 | click (SEEDS) |  | yes #113 s/l | yes #52 | yes #54 | yes #66 |
| Q6D | Q6 | S33 | topic |  | yes #114 s/l | yes #53 | yes #56 | yes #74 |
| Q7A | Q7 | S34 | topic |  | yes #115 s/l | yes #54 | yes #52 | yes #63 |
| Q7B | Q7 | S40 | click |  | yes #116 s/l | yes #63 | yes #63 | yes #70 |
| Q7C | Q7 | S34 | click (PLAY) |  | yes #117 s/l | yes #64 | yes #68 | yes #73 |
| Q8A | Q8 | S41 | topic |  | yes #118 s/l | yes #102 | yes #103 | yes #104 |
| Q8B | Q8 | S45 | click |  | yes #119 s/l | yes #103 | yes #105 | yes #105 |
| Q8C | Q8 | S43 | click (DELIVERY_NOTE) |  | yes #120 s/l | yes #104 | yes #108 | yes #107 |
| Q8D | Q8 | S41 | click (DELIVERY_OK) |  | yes #121 s/l | yes #105 | yes #115 | yes #112 |
| D01 | M11A | S52 | click (PHONE) |  | yes #52 s/l | yes #75 | yes #75 | yes #75 |
| D02 | M11A | S56 | click (CHRONO) |  | yes #53 s/l | yes #76 | yes #76 | yes #76 |
| D03 | M11A | S54 | click |  | yes #54 s/l | yes #77 | yes #77 | yes #77 |
| D04 | M11A | S51 | click (LOG1982) |  | yes #55 s/l | yes #78 | yes #78 | yes #78 |
| E01 | M11B | S64 | click (CHRONO) |  | yes #56 s/l | yes #84 | yes #79 | yes #80 |
| E02 | M11B | S64 | click (PHOTO2020) |  | yes #57 s/l | yes #85 | yes #83 | yes #82 |
| E03 | M11B | S65 | click (PARTSNOTE) |  | yes #58 s/l | yes #86 | yes #84 | yes #83 |
| E04 | M11B | S63 | click (CERAMICPARTS) |  | yes #59 s/l | yes #87 | yes #85 | yes #84 |
| E05 | M11B | S62 | topic |  | yes #60 s/l | yes #88 | yes #87 | yes #86 |
| E06 | M11B | inventory | combine (JAR) |  | yes #61 s/l | yes #89 | yes #88 | yes #87 |
| E07 | M11B | S66 | topic |  | yes #62 s/l | yes #90 | yes #89 | yes #90 |
| E08 | M11B | S61 | click (SEALED_NEW) |  | yes #63 s/l | yes #91 | yes #90 | yes #91 |
| E09 | M11B | S61 | click (TREEGUARD) |  | yes #64 s/l | yes #92 | yes #91 | yes #92 |
| E10 | M11B | S66 | topic | CS08 | yes #65 s/l | yes #93 | yes #93 | yes #93 |
| E11 | M11C | S13 | topic |  | yes #66 s/l | yes #94 | yes #94 | yes #94 |
| D05 | M11C | S55 | click (TOOLS) | P05 | yes #67 s/l | yes #95 | yes #95 | yes #95 |
| D06 | M11C | inventory | combine (TOOLS) |  | yes #68 s/l | yes #96 | yes #96 | yes #96 |
| D07 | M11C | S56 | click (RETURNBRIDGE) |  | yes #69 s/l | yes #97 | yes #97 | yes #97 |
| J02 | M12 | S41 | click (LIFT_TICKET) | CS09 | yes #78 s/l | yes #111 | yes #110 | yes #110 |
| J03 | M12 | S67 | click |  | yes #79 s/l | yes #112 | yes #111 | yes #111 |
| J04 | M12 | S68 | click |  | yes #80 s/l | yes #113 | yes #112 | yes #113 |
| J05 | M13 | S50 | click (RETURNBRIDGE) |  | yes #85 s/l | yes #118 | yes #118 | yes #118 |
| Q9A | Q9 | S60 | topic |  | yes #122 s/l | yes #79 | yes #80 | yes #79 |
| Q9B | Q9 | S60 | click (JANA_DRAWING) |  | yes #123 s/l | yes #80 | yes #81 | yes #81 |
| Q9C | Q9 | S60 | click (JANA_APPROVED) |  | yes #124 s/l | yes #81 | yes #82 | yes #85 |
| Q9D | Q9 | S15 | topic |  | yes #125 s/l | yes #82 | yes #86 | yes #89 |
| Q9E | Q9 | S54 | topic |  | yes #126 s/l | yes #83 | yes #92 | yes #88 |
| Q9F | Q9 | S44 | topic |  | yes #127 s/l | yes #106 | yes #109 | yes #102 |

Main actions verified in every run: 94/94; side actions: 33/33.

### Quests

| quest | type | completion | A | B | C7 | C42 |
|---|---|---|---|---|---|---|
| M01 | main | G05 | yes (5/5) | yes (5/5) | yes (5/5) | yes (5/5) |
| M02 | main | G11 | yes (6/6) | yes (6/6) | yes (6/6) | yes (6/6) |
| M03 | main | B03 | yes (3/3) | yes (3/3) | yes (3/3) | yes (3/3) |
| M04 | main | B06 | yes (3/3) | yes (3/3) | yes (3/3) | yes (3/3) |
| M05 | main | B12 | yes (6/6) | yes (6/6) | yes (6/6) | yes (6/6) |
| M06 | main | B16 | yes (4/4) | yes (4/4) | yes (4/4) | yes (4/4) |
| M07 | main | B22 | yes (6/6) | yes (6/6) | yes (6/6) | yes (6/6) |
| M08 | main | I08 | yes (8/8) | yes (8/8) | yes (8/8) | yes (8/8) |
| M09 | main | I13 | yes (5/5) | yes (5/5) | yes (5/5) | yes (5/5) |
| M10 | main | I17 | yes (4/4) | yes (4/4) | yes (4/4) | yes (4/4) |
| M11A | main | D04 | yes (5/5) | yes (5/5) | yes (5/5) | yes (5/5) |
| M11B | main | E10 | yes (10/10) | yes (10/10) | yes (10/10) | yes (10/10) |
| M11C | main | D07 | yes (4/4) | yes (4/4) | yes (4/4) | yes (4/4) |
| M11D | main | C05 | yes (4/4) | yes (4/4) | yes (4/4) | yes (4/4) |
| M12 | main | F06 | yes (9/9) | yes (9/9) | yes (9/9) | yes (9/9) |
| M13 | main | F10 | yes (5/5) | yes (5/5) | yes (5/5) | yes (5/5) |
| M14 | main | F11 | yes (1/1) | yes (1/1) | yes (1/1) | yes (1/1) |
| M15 | main | F17 | yes (6/6) | yes (6/6) | yes (6/6) | yes (6/6) |
| Q1 | side | Q1C | yes (3/3) | yes (3/3) | yes (3/3) | yes (3/3) |
| Q2 | side | Q2C | yes (3/3) | yes (3/3) | yes (3/3) | yes (3/3) |
| Q3 | side | Q3D | yes (4/4) | yes (4/4) | yes (4/4) | yes (4/4) |
| Q4 | side | Q4C | yes (3/3) | yes (3/3) | yes (3/3) | yes (3/3) |
| Q5 | side | Q5C | yes (3/3) | yes (3/3) | yes (3/3) | yes (3/3) |
| Q6 | side | Q6D | yes (4/4) | yes (4/4) | yes (4/4) | yes (4/4) |
| Q7 | side | Q7C | yes (3/3) | yes (3/3) | yes (3/3) | yes (3/3) |
| Q8 | side | Q8D | yes (4/4) | yes (4/4) | yes (4/4) | yes (4/4) |
| Q9 | side | Q9C | yes (6/6) | yes (6/6) | yes (6/6) | yes (6/6) |

### Puzzles, cutscenes, world changes

- **A**: puzzles P01, P02, P03, P04, P05; cutscenes (beats shown) CS01 3/3, CS02 2/2, CS03 2/2, CS04 2/2, CS05 2/2, CS06 2/2, CS07 5/5, CS08 2/2, CS09 2/2; eras [2020, 1995, 1960, 2035, 1982]; butterflies {'BF_TREE': True, 'BF_JANA': True}; cache stage Used, invariant True; variant layers 9/9; causal effect sightings 27 (effect@room).
- **B**: puzzles P01, P02, P03, P04, P05; cutscenes (beats shown) CS01 3/3, CS02 2/2, CS03 2/2, CS04 2/2, CS05 2/2, CS06 2/2, CS07 5/5, CS08 2/2, CS09 2/2; eras [2020, 1995, 1960, 2035, 1982]; butterflies {'BF_TREE': True, 'BF_JANA': True}; cache stage Used, invariant True; variant layers 9/9; causal effect sightings 27 (effect@room).
- **C7**: puzzles P01, P02, P03, P04, P05; cutscenes (beats shown) CS01 1/3, CS02 1/2, CS03 1/2, CS04 1/2, CS05 1/2, CS06 1/2, CS07 5/5, CS08 1/2, CS09 1/2; eras [2020, 1995, 1960, 2035, 1982]; butterflies {'BF_TREE': True, 'BF_JANA': True}; cache stage Used, invariant True; variant layers 9/9; causal effect sightings 27 (effect@room).
- **C42**: puzzles P01, P02, P03, P04, P05; cutscenes (beats shown) CS01 1/3, CS02 1/2, CS03 1/2, CS04 1/2, CS05 1/2, CS06 1/2, CS07 5/5, CS08 1/2, CS09 1/2; eras [2020, 1995, 1960, 2035, 1982]; butterflies {'BF_TREE': True, 'BF_JANA': True}; cache stage Used, invariant True; variant layers 9/9; causal effect sightings 27 (effect@room).

- **A postgame**: `{"return_items_in_bag": true, "postgame_active": true, "era_tour": [{"era": 2020, "room": "S10", "inventory_unchanged": true}, {"era": 1995, "room": "S11", "inventory_unchanged": true}, {"era": 1960, "room": "S31", "inventory_unchanged": true}, {"era": 2035, "room": "S41", "inventory_unchanged": true}, {"era": 1982, "room": "S57", "inventory_unchanged": true}, {"era": 2020, "room": "S10", "inventory_unchanged": true}], "cable_cars_after_F09": true, "revisited_for_effects": ["S14", "S43", "S49"], "album_replay_shots": 9, "cutscene_replay": {"cutscene": "CS07", "started": true, "no_transaction": true}, "done_unchanged": true}`
- **B postgame**: `{"return_items_in_bag": true, "postgame_active": true, "era_tour": [{"era": 2020, "room": "S10", "inventory_unchanged": true}, {"era": 1995, "room": "S11", "inventory_unchanged": true}, {"era": 1960, "room": "S31", "inventory_unchanged": true}, {"era": 2035, "room": "S41", "inventory_unchanged": true}, {"era": 1982, "room": "S57", "inventory_unchanged": true}, {"era": 2020, "room": "S10", "inventory_unchanged": true}], "cable_cars_after_F09": true, "revisited_for_effects": ["S14", "S17", "S42", "S49"], "album_replay_shots": 9, "cutscene_replay": {"cutscene": "CS07", "started": true, "no_transaction": true}, "done_unchanged": true, "all_lines_unreachable_rooms": []}`
- **C7 postgame**: `{"return_items_in_bag": true, "postgame_active": true, "era_tour": [{"era": 2020, "room": "S10", "inventory_unchanged": true}, {"era": 1995, "room": "S11", "inventory_unchanged": true}, {"era": 1960, "room": "S31", "inventory_unchanged": true}, {"era": 2035, "room": "S41", "inventory_unchanged": true}, {"era": 1982, "room": "S57", "inventory_unchanged": true}, {"era": 2020, "room": "S10", "inventory_unchanged": true}], "cable_cars_after_F09": true, "revisited_for_effects": ["S14", "S17", "S42", "S43", "S49"], "album_replay_shots": 9, "cutscene_replay": {"cutscene": "CS07", "started": true, "no_transaction": true}, "done_unchanged": true}`
- **C42 postgame**: `{"return_items_in_bag": true, "postgame_active": true, "era_tour": [{"era": 2020, "room": "S10", "inventory_unchanged": true}, {"era": 1995, "room": "S11", "inventory_unchanged": true}, {"era": 1960, "room": "S31", "inventory_unchanged": true}, {"era": 2035, "room": "S41", "inventory_unchanged": true}, {"era": 1982, "room": "S57", "inventory_unchanged": true}, {"era": 2020, "room": "S10", "inventory_unchanged": true}], "cable_cars_after_F09": true, "revisited_for_effects": ["S14", "S17", "S42", "S43", "S49"], "album_replay_shots": 9, "cutscene_replay": {"cutscene": "CS07", "started": true, "no_transaction": true}, "done_unchanged": true}`
