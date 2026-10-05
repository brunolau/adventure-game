# Milestone 3 - natural re-blocking of all 68 rooms (integration report, 2026-10-05)

CODING_AGENT_START milestone 3: *"Rovnaké miesta v troch rokoch, skrýša, Tóno a dve príčinné zmeny"* (the same places
in three years, the cache, Tóno and two causal changes). Milestone 4 (art part): final paintings and animations.

## Status

| item | status | evidence |
|---|---|---|
| Natural blocking for all 68 rooms | **done, now the default** (`src/game/project.godot` `last_bell/presentation/blocking="natural"`; `--blocking template` still compares) | `python tools/check_blocking.py` (also `--strict`): 68 rooms, 0 errors, 8 warnings (ISSUES M3-02) |
| Same places in three years (7 camera families) | **done**: every family was painted from one base master and derived with `art/tools/derive_era.py`; `anchors`, `walk_band`, `actor_scale` are identical per family | `docs/families/<family>.png` (in-engine, anchors in red): L_STOP S57/S11/S51, L_SCHOOL_FRONT S58/S12/S52, L_HALL S59/S13/S53, L_CLASS S60/S14, L_CABINET S63/S15/S54, L_YARD S61/S17/S55, L_WINDOW S64/S56 |
| The cache (D05, L_YARD niche) | **done**: closed niche after E08 in 1982, the original niche in the wall in 2020, `S55_cache_open` patch after D05; cache invariant holds in every run (`cache_stage Used`) | `build/m3logs/sheets/variants2.jpg`, coverage files |
| Tóno | **done**: TONO82 seated on a stool at the 1982 service window (S64), Tóno 1995 seated in the entry hall (S13), Tóno 2020 as a window bust behind glass (S56), staged per DECISIONS item 2 | `build/screens/m3/all/S13_00.png`, `S56_00.png`, `S64_00.png` |
| Two causal changes (butterflies) | **done**: BF_TREE (E10: S61 tree guard + closed niche, S17 healthy linden, S55 old linden/wall/bench) and BF_JANA (Q9C: S15 Jana's workbench, S54 refurbished laptops, S44 exhibit) appear after their actions; plus S06 photo fade/partial/restored (G11, C04, F17) and S47 originals (F17) | `build/screens/m3/routeA/*_variant_*.jpg`, `build/m3logs/sheets/variants.jpg`, `variants2.jpg`, `s06_photo.jpg`; coverage: 9 variant layers, 27 causal effects, 2 butterflies |
| Milestone 4, art part | **paintings done for all 68 rooms** (style A, from their real places, owner feedback 2026-10-05 applied); every room has >= 3 ambient layers (3-24) and moves in-engine; 34 natural state patches / variant overlays; occluders where actors pass furniture | `build/screens/m3/all/<room>_00..02.png`, `build/m3logs/motion.txt`, painters' logs `art/masters/bg_natural/<room>.md` |

## Verification (all in natural mode, the new default)

| check | result |
|---|---|
| `dotnet test src/LastBell.sln` | 294 passed, 3 skipped, 0 failed |
| `tools/check_strings.py` | OK (2948 keys, 0 errors, 0 warnings) |
| `tools/check_blocking.py` / `--strict` | 68 rooms, 0 errors, 8 warnings |
| `--acceptance m1` (1280x720 window, time-scale 4) | 24 PASS, 0 FAIL, exit 0 (run twice, the second after the S05 repaint) |
| `--acceptance m2` (incl. AT05 markers in all 68 rooms, AT20 every target clickable) | 41 PASS, 0 FAIL, exit 0 |
| Route A: window 1920x1080, `--play-all --save-load-each --shots build/screens/m3/routeA` | 127/127 actions by real input, 9 cutscenes, 5 puzzles, 68 rooms, 9 variant layers, 27 causal effects, 0 blockers, 0 click retries, 0 failures; 210 shots |
| Route B: headless `--play-all --interleave early --all-lines` | 127/127, 774 lines / 471 look texts shown, 0 blockers, 0 failures |
| Route C7: headless `--play-all --interleave seed:7 --skip-cutscenes` | 127/127, 0 blockers, 0 failures |
| In-engine captures: every room, QA labels on, 3 motion frames 700 ms apart | `build/screens/m3/all/S01_00.png` ... `S68_02.png` (all 68 looked at; contact sheets `build/m3logs/sheets/`) |
| Windows export `build.bat` | exit 0, `build/windows/LastBell.exe` + `LastBell.pck` (448 MB, ISSUES M3-04) |
| Exe smoke test | `LastBell.exe -- --room S05 --labels --screenshot` shows the natural S05 v2 without any flag (default works in the export); `LastBell.exe --headless -- --real --play 11` plays the prologue G01-G11 by real input to S11 1995 |

Coverage JSON: `build/screens/m3/coverage_A.json`, `coverage_B.json`, `coverage_C7.json`; logs `build/m3logs/`.

### What the review of the 68 captures found

- Art present in every room; every room reads as its real place, and the owner feedback is visible: S04 Monar arcade
  with the green canopy and tiled roof, S07 roadside stop with the red-framed shelter on the long straight road, S08
  pond from the pump track without a fence, S11 brown tube shelter + red-cream T3, S12/S13-S16 plain yellowish school
  walls, S17/S61/S55 the yard side with ribbon windows, the yard entrance with steps, the court and the track, S18 the
  carl_eric panel block, S21 department store + Hotel Kyjev + round pavilion, S28 the stair underpass, S41 the gondola
  station plaza, S43 the stone reception wall.
- Props sit in their rects, labels beside their objects; NPCs stand on the floor at the room's perspective, busts on
  their sills (S04 Dana, S06 Mira, S25 Fero, S26 Milada, S62 Ruzena, S64 Oto), seated figures seated (S13 Tóno, S37
  Vera, S64 Tóno); the hero sorts in front of / behind the occluders.
- Ambient motion in every room (0.03-5 % of the picture changes between frames: birds, leaves, clouds, flicker, water,
  critters, tween paths). Weakest: S63 (3 layers, very subtle) and S57.
- Family strips: camera, horizon and anchors line up across the eras; only the era content changes (vehicles,
  facades, seasons, murals only in 2020).
- S05 still had the wide pavement of the pilot (owner: "pathways are thinner"): repainted by the integrator (below).

## Changes made by the integrator

- `src/game/project.godot`: `presentation/blocking="natural"` (ISSUES M3-01); comment updates in `World/RoomBlocking.cs`
  and `Runtime/PresentationSettings.cs`. No rule, Core or game.json change.
- S05: `refit fix` of the ground (USD 0.15) -> `bg_natural/S05.webp` v2; blocking note/status updated; log appended
  (ISSUES M3-03).
- `design-doc/LOCATIONS_REGISTER.csv`: only `notes` (68 rows: "M3 natural (2026-10-05): ..." with final master and
  the painters' register notes; changes to other columns are written as "proposed ...", ISSUES M3-05) and
  `fiction_notes` (S53, S54, S59, S60).
- `tools/build_locations_gallery.py`: prefers `bg_natural` (it already did) and labels it as the game default;
  `docs/locations.html` regenerated (68 rooms, 68 natural paintings).
- `docs/families/*.png` (script: `tools/family_sheets_m3.py`, reads `build/screens/m3/all/`).
- ISSUES.md rows M3-01 ... M3-05.

## Spend (art/spend-log.csv, 679 paid calls)

| group | calls | USD |
|---|---|---|
| characters (actor sheets) | 409 | 63.94 |
| cutscenes | 42 | 6.30 |
| template backgrounds `bg/` (milestones 1-2) | 33 | 4.95 |
| natural: families + 1982/2020 S51-S66 | 33 | 4.95 |
| natural: 1995 S11-S30 | 32 | 4.80 |
| natural: 2020 prologue S01-S10 (incl. the S03/S05 pilot and the integrator's S05 v2) | 22 | 3.30 |
| items | 31 | 3.20 |
| natural: 2035 S41-S50, S67-S68 | 21 | 3.15 |
| natural: 1960 S31-S40 | 12 | 1.80 |
| music | 19 | 1.59 |
| ambient | 8 | 1.32 |
| pre-production backgrounds / style tests | 14 | 2.10 |
| ui (cursors) | 2 | 0.27 |
| derive tool test (`bg_natural` root) | 1 | 0.15 |
| **total** | **679** | **101.82** |

Natural re-blocking wave (all 68 rooms): 121 calls, **USD 18.15** (the integrator: 1 call, USD 0.15).

## Open issues

- ISSUES M3-02: 8 cosmetic exit-label / interaction-point distance warnings.
- ISSUES M3-04: pck 448 MB (lossless imports; template art still shipped).
- ISSUES M3-05: register columns other than notes (real_place, lat/lon, source_files, basis) and two credits entries
  wait for the register owner.
- The real ZŠ Sokolíkova entry hall (S13/S53/S59) is still a type-reference until the owner describes it (owner
  feedback "details pending").
- S21: no moving tram (audio only); S11: the T3 is painted, not a separate sprite (LIVING-05).
- S57: decision 3b is realised by the blocking's audio override; game.json `art_brief` / `ambience` of S57 still name
  the tram (handoff owner, ART-DUBEXT-01).
- S63 and S57 have the subtlest ambient motion; worth one more layer in a polish pass.
- BUILD-03 (QA harness active in release exports) still open.
