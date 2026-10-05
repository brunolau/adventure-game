# Milestone 5 - acceptance tests and a fresh playthrough (2026-10-05)

CODING_AGENT_START milestone 5: *"Akceptačné testy a nový priechod bez debug pridávania predmetov"* (acceptance
tests and a new playthrough without debug item spawning). The two playtests (`docs/playtest/first-half.md`,
`second-half.md`) were done before this pass; this file records the final run of every automated check, the play
of the exported release exe, and the row-by-row result of `design-doc/acceptance_tests.csv`.

Owner-facing summary (how to play, sizes, credits, spend, what is left): `docs/RELEASE.md`.

## Status

**Milestone 5: done, with known issues.** Every automated suite is green on the final code and the release build.
29 of the 30 acceptance rows pass (23 plain, 6 with a note). AT19 (keyboard only) is partly verified and stays
open.
The open items are listed in `docs/RELEASE.md` "Known issues" and in `design-doc/ISSUES.md`
(PT-F08 ... PT-S28, M5-01 ... M5-05).

## What was run (final code, natural blocking = the default)

| check | result | log / evidence |
|---|---|---|
| `dotnet test src/LastBell.sln` | 294 passed, 3 skipped (UI-only AT08/AT19/AT20, covered in-engine), 0 failed | console |
| `python tools/check_strings.py` | OK: 2956 keys, 0 errors, 0 warnings | console |
| `python tools/check_blocking.py` | 68 rooms, 0 errors, 8 warnings (the accepted M3-02 label/point distances) | console |
| `python tools/check_rewrite.py --self-test` | OK (44 names, 20 places, 65 terms, 112 protected key rules, 21 verbatim rules) | console |
| `check_rewrite.py docs/writing/out/C1..C4.csv --chunk Cn` | 4 x OK, 0 errors, 0 warnings | console |
| override table `src/game/localization/overrides/sk_overrides.csv` | 1447 rows, 0 load problems; `extract_strings.py --dry-run` OK (1447 overrides applied, 0 problems, 0 internal ids in player text) | console |
| `--acceptance m1` headless, time-scale 4 | 24 PASS, 0 FAIL | `build/m5/logs/acceptance_m1.txt` |
| `--acceptance m2` headless, time-scale 3 | 41 PASS, 0 failures | `build/m5/logs/acceptance_m2.txt` |
| `--acceptance m2` window 1280x720 | 41 PASS, 0 failures (AT20 at 1280x720) | `build/m5/logs/acceptance_m2_720.txt` |
| `--acceptance` (m1 + m2) window 1920x1080 | 65 PASS, 0 failures (AT20 at 1920x1080) | `build/m5/logs/acceptance_all_1080.txt` |
| Route A: `--play-all --save-load-each` (headless, time-scale 6) | 127/127 actions by real input events, save + load + compare after every one; 9 cutscenes, 5 puzzles, 68 rooms, 9 variant layers, 27 causal effects, epilogue 9 shots in the album replay, CS07 replay without a second transaction, era tour over all 5 eras with the inventory unchanged, cable cars after F09; 0 blockers, 0 failures | `build/m5/logs/routeA.txt`, `build/m5/coverage_A.json` |
| Route B: `--play-all --interleave early --all-lines` (headless, time-scale 8) | 127/127, side quests as early as legal, 774 lines shown (757 distinct ids), 471 look texts; 0 blockers, 0 failures | `routeB.txt`, `coverage_B.json` |
| Route C7: `--play-all --interleave seed:7 --skip-cutscenes` (headless, time-scale 8) | 127/127, side actions at seeded random points, every cutscene skipped with Esc; 0 blockers, 0 failures | `routeC7.txt`, `coverage_C7.json` |
| `build.bat` (release) | exit 0; `build/windows/LastBell.exe` 109.5 MB (icon + version info, second export pass), `LastBell.pck` 176.2 MB (2335 files), `data_LastBell_windows_x86_64/` 81.0 MB; `release_assets.py pck --release` OK (no excluded file inside) | `build/m5/logs/build_release.txt`, `build/pck_contents_release.txt` |
| Release exe, harness flags | `LastBell.exe -- --room S44 --replay 94 --screenshot ... --quit-after 1`: log says `release build, 8 QA argument(s) after "--" ignored`; the game stayed at the main menu after 15 s, wrote no screenshot, did not quit | `build/m5/logs/release_harness_refused.txt`, `build/screens/release/m5/harness_refused_still_running_menu.png` |
| Release exe, new game by real input | see below: G01-G11, P01 (one wrong answer first), CS01, arrival in S11/1995 with PHONE, TOOLS, SHEDKEY (archived), CHRONO; save/load round trip; quit from the pause menu; log without any warning | `build/screens/release/m5/000_menu.png` ... `080_quit.png`, `build/m5/logs/release_play.txt` |
| Combined coverage tables | `python tools/m2_coverage.py build/m5/coverage_*.json` | `build/m5/coverage_tables.md` |

The first route run failed in all three routes at the same postgame step (`HARNESS FAIL journal: no replay button
for CS07`). Cause: the harness looked for the album button by the action label, but the second-half playtest had
renamed the album scene buttons (PT-S08, `ui.journal.scene_cs07` = "Mená sú späť"). Fixed in the harness only
(`scripts/Diagnostics/ContentQa.cs` uses the same title rule as `JournalScreen`), ISSUES M5-01. All three routes
were then run again from the start and passed. Logs of the failed run: `build/m5/logs/run1/`.

## Release exe played by real input (build/windows/LastBell.exe, 1920x1080 window)

Driven like the playtests: the OS cursor is moved to each point and real mouse/keyboard window messages are posted
to the game window; screenshots by PrintWindow (the hardware cursor is not in them). No harness, no `--` arguments.
The owner's save folder and settings were backed up first and restored afterwards (`build/m5/saves_backup/`; the
saves of this run are in `build/m5/m5_run_saves/`).

| step | what I did | result |
|---|---|---|
| menu | Nová hra, confirm the overwrite dialog | intro monologue in S01 (`002_intro.png`) |
| G01 | held Space (markers on 5 targets, `004`), clicked the service bag | bag gone from the chair, objective toast (`005`) |
| G02 | double-click exits S01 -> S02 -> S03, Ela, topic "Babkin nákup" | ORDER in the bag (`009`-`011`) |
| G03 | S04, bag -> shopping list -> close drawer, hover Dana ("Vyzdvihnúť Mirin nákup"), click | GROCERIES; the bag on the counter disappears (`016`-`019`) |
| G04 | S03 -> S02 -> S05, groceries on the little table | bag shown on the table (`024`, `025`) |
| G05 | S06, Mira, topic "Potrebuješ ešte niečo?" | SHEDKEY (`027`-`030`) |
| save | pause -> Uložiť hru -> slot 8 | "Hra je uložená.", thumbnail and room name "Pod zatvoreným oknom · 2020" (`033`) |
| G06 | S05, key on the padlock | padlock gone (`037`) |
| load | pause -> Načítať hru -> slot 8 -> confirm | back in S06, bag PHONE / TOOLS / SHEDKEY, G06 not done: the padlock is back in S05 (`042`-`044`) |
| G06 again | key on the padlock | unlocked; one key, no duplicate (`045`) |
| G07 | clicked the upper door leaf first: got the door look (ISSUES M5-02), then the lower door -> S09, brass case | CHRONO, objective (`046`-`051`) |
| G08 | S10, service bag on the cradle | old fuse out, objective "Vo svojej garáži vezmi zo zásuvky rovnakú poistku" (`055`) |
| G09 | map -> "Adamova garáž" (fast travel), fuse drawer | FUSE; the old key archived (`057`-`061`) |
| G10 | map -> "Dielňa ZVON", fuse on the cradle | objective: shape panel (`065`, `066`) |
| G11 / P01 | panel: one wrong set (kruh-štvorec ...) -> Potvrdiť -> hint line, nothing consumed; Začať odznova; correct pairs -> Potvrdiť | "Tri tvary, tri zhody. Hotovo.", CS01 beats, arrival S11 1995 with the era-chooser clock in the HUD (`069`-`078`) |
| quit | pause -> Ukončiť hru -> confirm | process ended; log: 4 lines, no warning or error |

Final autosave of that run: room S11, era 1995, done G01-G11, inventory PHONE, TOOLS, SHEDKEY, CHRONO.

## acceptance_tests.csv row by row

The handoff file is read-only (ARCHITECTURE.md), so the results are recorded here.
"Core" = `src/LastBell.Core.Tests/AcceptanceTests.cs` (the test of the same AT number); "m1"/"m2" = the in-engine
acceptance sets; A/B/C7 = the route runs above; "release" = the release exe play above.

| id | result | how |
|---|---|---|
| AT01 | **passed** | Core AT01; m1 `taken_prop_gone_no_duplicate`, `repeat_click_no_duplicate`; release: bag gone after G01, one TOOLS |
| AT02 | **passed** | Core AT02; m2 AT02 (no action text, no walk, selection kept) |
| AT03 | **passed** | Core AT03; m2 AT03 (label only while B06 exists, committed once) |
| AT04 | **passed** | Core AT04; m1 right-click checks (look, inventory, cancel selection first); m2 AT04 (item in the drawer, drawer stays open) |
| AT05 | **passed with note** | m2 AT05 68/68 rooms; Core AT05. Note: by the owner's control change (DECISIONS, INT-08) Space shows round markers, not name labels; names come from the hover label at the cursor |
| AT06 | **passed with note** | m2 AT06 (names stay, empty action text for wrong targets, outline only on valid ones); Core AT06. Same note as AT05 |
| AT07 | **passed** | m2 AT07 P01-P05 (10 wrong answers, close, save, load, solve: one commit); release: a wrong P01 answer gave the hint line and consumed nothing |
| AT08 | **passed** | m2 AT08 (P02 by clicks at 200 % HUD scale; the puzzles use no audio cue) |
| AT09 | **passed** | Core AT09; m2 AT09 (B10/B11 and I04/I05 in reverse selection order) |
| AT10 | **passed** | Core AT10 (map strand first in one save, cassette strand first in another; B22 needs both); the routes play the walkthrough order |
| AT11 | **passed** | Core AT11; m2 AT11; postgame era tour in A, B, C7 (inventory unchanged in all 5 eras) |
| AT12 | **passed** | Core AT12; m2 AT12 (unvisited node inert, fast travel only where a route exists) |
| AT13 | **passed** | Core AT13; route A reaches F17 with main actions only (side actions after the credits) and all four evidence items return |
| AT14 | **passed** | Core AT14; route A: all 33 side actions (9 side quests) after the credits, finale not repeated, new epilogue shots in the album replay (9) |
| AT15 | **passed** | Core AT15 (all 24 orders); m2 AT15 (reverse order, selection cleared on consumption) |
| AT16 | **passed with note** | m2 AT16 9/9; route C7 skips every cutscene and ends in the same final state. Note: the CSV says seven cutscenes, the game has nine (ISSUES CORE-02) |
| AT17 | **passed** | route A: save, load and compare after all 127 actions; m2 AT17 (mid CS06/F11 and CS07/F17); release: save/load round trip |
| AT18 | **passed** | Core AT18; m2 AT18 (corrupt save and unknown item refused with the readable message, open game untouched) |
| AT19 | **open (partly verified)** | m2 AT19 part (Tab focus + Enter: bag, exit, talk, topic); every mouse-only input has a key (right click = Backspace, Space = HUD eye button, double click is only a shortcut); puzzles do not depend on colour ("Na farbách nezáleží", shapes are named) or sound; subtitles always on. A whole-game keyboard-only playthrough was not done |
| AT20 | **passed with note** | m2 AT20 at 1280x720 and 1920x1080 windows and headless (every target has a clickable point not under the HUD); Core AT20 minimum hit area; both playtests at 1280x720 found nothing unreadable. Note: hover label and toasts can sit over open GUI (PT-S22, PT-S23) |
| AT21 | **passed** | Core AT21; m2 AT21 (S15 / S43 / S47 change only after Q9C / Q4C / Q5C, on re-entry); 27 causal effects seen in every route |
| AT22 | **passed** | Core AT22; m2 AT22 (triple click on the bag, click spam on the last line: one commit, no fall-through) |
| AT23 | **passed with note** | Core AT23 (no timer in the rules); m2 AT23 (pause + journal for 30 game-seconds before F09, F09 still possible). Note: 30 game-seconds, not 30 real minutes |
| AT24 | **passed with note** | 68 navigable rooms painted (route runs visit all 68); all 127 actions; route B shows 774 lines / 471 looks; 9 complete side quests; no placeholder art or dev notes in release (`--dev` only); story unchanged by the text rewrite (game.json untouched, overrides only). Note: known continuity issues PT-S18 (Mira speaks in S40 without being there), PT-S21 (CS07 port symbol), PT-S20 (Adam's autumn clothes in the 1982 snow) |
| AT25 | **passed** | Core AT25; m2 AT25 (S17/S55 variants only after E10, every target reachable, PHOTO2020 kept) |
| AT26 | **passed** | Core AT26; m2 AT26; cache invariant held in all routes |
| AT27 | **passed** | Core AT27 (exact conditions, ages 12/25/50); routes A/B/C7 meet all three Tónos |
| AT28 | **passed** | Core AT28; route A finishes the story without Q9C, then does Q9C-Q9F (variant layers and texts in three eras) |
| AT29 | **passed** | Core AT29; m2 AT29 (no edge or fast travel past J02-J04, return ticket kept) |
| AT30 | **passed** | Core AT30; postgame `cable_cars_after_F09 = true` in A, B, C7 |

Summary: **29 of 30 passed** (23 plain, 6 with a note), **1 open** (AT19, partly verified).

| result | rows | count |
|---|---|---|
| passed | AT01-04, AT07-15, AT17, AT18, AT21, AT22, AT25-30 | 23 |
| passed with note | AT05, AT06, AT16, AT20, AT23, AT24 | 6 |
| open | AT19 | 1 |

## Found in this pass

- M5-01 (fixed, harness only): the CS07 album-replay lookup used the old button text (see above).
- M5-02 (open, presentation data): S05 after G06 the upper two fifths of the workshop door (the former padlock rect
  770,470,130,130) still answer with the door look; only the lower part is the way in. A player who clicks the
  middle of the door gets "Zámok na dverách otvára babkin kľúč" once more. Fix: shrink `S05.shed_door` to the hasp
  (about 815,520,50,60) or hide it after G06 (needs a game.json visibility condition).
- M5-03 (open, owner): the main menu shows "Verzia 2.0.0" (game.json data version) while the exe says 0.1.0.0.
- M5-04 (open, minor art/staging): Adam stands in front of the thing he uses in S05 (tray, G04), S09 (case, G07)
  and S10 (cradle, G08/G10), like PT-S06; and the service-bag item icon is brown leather while the painted bag on
  the S01 chair is green canvas.
- M5-05 (open, minor UI): reward and objective toasts appear as soon as a topic or puzzle is confirmed, before the
  lines that explain them (S03 G02, S06 G05, S10 G11 shows the 1995 goal before CS01); see PT-S22.
- Build: a `LastBell.exe` from `build/windows/` that this pass did not start (PID 32692, running since 08:43) keeps
  29 old DLLs locked; they stay behind as `*.dll~RF*.TMP` (34 MB) in `build/windows/data_LastBell_windows_x86_64/`.
  The clean distributable is `build/m5/ship/` (see RELEASE.md).
