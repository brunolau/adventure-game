# Milestone 5 - acceptance tests and a fresh playthrough (2026-10-05)

CODING_AGENT_START milestone 5: *"Akceptačné testy a nový priechod bez debug pridávania predmetov"* (acceptance
tests and a new playthrough without debug item spawning). The two playtests (`docs/playtest/first-half.md`,
`second-half.md`) were done before this pass; this file records the final run of every automated check, the play
of the exported release exe, and the row-by-row result of `design-doc/acceptance_tests.csv`.

Owner-facing summary (how to play, sizes, credits, spend, what is left): `docs/RELEASE.md`.

## Status

**Milestone 5: done. All 30 acceptance rows pass** (24 plain, 6 with a note) after the verification and release pass
of 2026-10-06 (two sections below): every suite green on the final code, AT19 closed by a whole-game keyboard-only
route and an OS-level keyboard run, the fixed playtest items spot-checked in a real window, the release rebuilt and
smoke-tested. **Re-verified and rebuilt on the afternoon of 2026-10-06** (next section) after the owner's afternoon
answers (entry hall without the desk, S03 grasshopper, podlubie no-go, S30 on the Starý most): all green, no
regression. What still needs the product owner: docs/DECISIONS.md "Status 2026-10-06"; the remaining known issues:
docs/RELEASE.md.

**Content v2 applied and re-verified on the evening of 2026-10-06** (section "Content v2 applied"): the owner-approved texts, Zuzana
1962 / 1995, the room S69 and side quests Q10 / Q11 are in the game; 134/134 actions in all four routes, release rebuilt.

**Round 2 applied and re-verified on 2026-10-07** (next section): the knowledge fixes, the Standard / Hard hint texts
and the difficulty UI are live, Zuzana stands still in conversations, S69 is at sunset; all suites and four routes
green (134/134), release rebuilt and smoke-tested.

**Owner feedback of 2026-10-07 evening verified and released** (section of that name): S07, S18 / S62, S21 exits, „Pri LEALe“,
the female narrator; all suites green, routes A and K 134/134, release rebuilt (20:20) and smoke-tested.

**Version 0.2.0 verified and released on 2026-10-08** (next section): the less revealing Standard / Hard texts,
English, the voiced look texts; all suites green, routes A, EN (English) and K 134/134, Windows, Linux and macOS
built, published as `v0.2.0`.

**Version 0.2.1 verified and built on 2026-10-09** (next section): English names of the characters, the Android
build with touch controls and the list scrolling the owner asked for after his first test on a phone; all suites
green, the English route 134/134, Windows, Linux, macOS and Android built. **Not published yet** (the owner decides).

The sections after the next seven are the record of the first milestone-5 run (2026-10-05).

## Version 0.2.1 (2026-10-09, verified and built; not published)

What changed since 0.2.0 (commits bb1c97c0 to ec9646a1):

- **Android port and touch controls** (owner: "in other agent work on the android build"): docs/PORTS.md "Android"
  and "Touch controls". Touch mode exists only on phones and tablets (feature tag `mobile`) and in QA runs with
  `--touch`; a desktop build cannot turn it on.
- **Lists scroll with a finger** (owner, first test of the 0.2.0 APK on a phone: "none of the things that are meant
  to be scrollable is actually scrollable"): `UI/Common/TouchScroller.cs`, sliders, the settings layout on phones
  (ISSUES ANDROID-12, -13).
- **English names of the characters** (owner: "Bodka => Dotty ... and come up with English sounding names", "for all
  platforms of course"): `tools/en_person_names.py`, 896 of 5,255 English texts; the Slovak column is byte-identical
  (docs/translation/README.md "English names of people").

| check | result |
|---|---|
| Godot `--headless --import` (after the names) | exit 0, 0 errors; only the three `.en.translation` files changed |
| `dotnet test src/LastBell.sln` | 506 passed, 3 skipped, 0 failed |
| `check_strings.py` | OK, 5255 keys, 0 errors, 0 warnings |
| `en_person_names.py --check` | OK, 0 leftovers in 5255 texts |
| `--acceptance m1` / `travel` (headless) | 34 / 4 PASS, 0 failures |
| `--acceptance m2` (headless, x3) | 46 PASS, 0 failures |
| `--touch --acceptance touch` (headless, private profile) | 20 PASS, 0 failures (TC17 to TC20 are the scroll and slider checks) |
| Route EN `--play-all --locale en --lines` (headless, x6) | 134/134 actions, 1001 lines, the ending and the album replay (11 shots), 0 warnings, exit 0; the lines show the new names ("Adam Perry", "Mira Perry") |
| Android emulator (Android 16, x86_64, no window): `android_qa.py smoke` on the 0.2.1 debug APK | 11 of 11 with real touch events, the new scroll check included |

Said plainly: routes A (Slovak) and K (keyboard only) were **not** run again; no Slovak text and no PC input code
changed (the scroller, the phone settings layout and the hover change exist in touch mode only; `SettingsScreen.Build`
was rearranged, its PC branch builds the same tree). The English route ran without `--coverage`, so there is no
coverage file for it; the counts above are from its log. Known headless-only engine lines in the logs, as before:
`Parameter "t" is null` (dummy renderer, room change; 4 times in the English route, once with `wrong RID` /
`Parameter "mem" is null` in front of it). Logs: `build/verify_1009/logs/` (review run of the Android commits),
`build/verify_1009/logs2/` (this pass), `build/verify_1009/android/`.

**Windows.** `build.bat` exit 0 (C# 0 warnings, 0 errors; release filters OK, 576 natural-mode references, 0 errors;
the known `ERR_CANT_OPEN` icon pass). `LastBell.exe` 109.5 MB (file version 0.2.1.0), `LastBell.pck` 320.8 MB,
`data_LastBell_windows_x86_64/` 81.5 MB; `build/m5/ship/PoslednyZvonec/` 511.8 MB, 190 files, zipped as
**`build/m5/ship/PoslednyZvonec-0.2.1-windows-x64.zip`, 373.2 MB** (373,220,212 bytes, zip test OK, sha256
`b9762101…658b2512`). Smoke test of the shipped copy (`build/verify_1008b/release_smoke.py`, hidden window, the
player's profile moved aside and restored): QA arguments ignored, new game, first action, autosave S01 / 2020 /
[G01] / [PHONE, TOOLS].

**Linux and macOS** (`build_ports.py linux macos --skip-import`, `verify`): `PoslednyZvonec-0.2.1-linux-x86_64.tar.gz`
362.2 MB (sha256 `cadb24eb…e231018b`), started with `--headless --quit-after 900` in an `ubuntu:24.04` container:
exit 0, no error line, user folder created. `PoslednyZvonec-0.2.1-macos.zip` 429.6 MB (sha256 `8641bdef…8ee5ac0f`),
structure verified, not started on a Mac.

**Android** (`build_ports.py android-qa android android-aab`): `PoslednyZvonec-0.2.1.apk` 584.3 MB (sha256
`0173d1a0…ef38346a`; version code 3, arm64-v8a, minimum API 24, no permission, release key) and
`PoslednyZvonec-0.2.1.aab` 520.6 MB. The arm64 APK itself was checked statically; what was played is the x86_64
debug APK of the same project. **0.2.1 has not been on a real phone yet.**

The player's save folder is identical to its state before the runs. Nothing was published: the GitHub release page
still has `v0.2.0`. Paid generation in this pass: none.

## Version 0.2.0 (2026-10-08, verified and released)

What changed since 0.1.0 (each applied by its own task, commits f9283b2c to f3fccb25):

- **Standard / Hard texts** (owner: "the game is still hinting way too much…"; approved "yup, good adjustments"): 163
  `<key>.std` variants in `src/game/localization/overrides/guidance_std.csv` (30 dialogue lines, 133 world texts).
  `TextService.VariantKey` picks them unless the difficulty is Easy; the voice follows (`<key>.std.ogg`, 32 takes).
- **English**: all 5,255 keys (`overrides/en.csv`, docs/translation/README.md), the language follows the system on a
  first start, `--locale sk|en` for QA runs; English place names by the owner's rule (`tools/en_place_names.py`).
- **Voiced look texts**: 567 keys, 390 takes (`assets/voice/aliases.json` maps repeated sentences to one take).
- Tóno's label, the first workshop goal (docs/DECISIONS.md "Owner answers 2026-10-08").

| check | result |
|---|---|
| Godot `--headless --import` | exit 0, 0 errors; the three `.en.translation` files re-imported with the place names |
| `dotnet test src/LastBell.sln` | 506 passed, 3 skipped, 0 failed |
| `check_strings.py` | OK, 5255 keys, 0 errors, 0 warnings (placeholders checked in both languages) |
| `check_rewrite.py --self-test` / `--overlay-only` | OK, 1712 overlay texts, 0 errors, 0 warnings |
| `content_ext.py check` | OK |
| `check_blocking.py --strict` (all 69 rooms) | 0 errors, 15 warnings (the same known ones as on 2026-10-07) |
| `knowledge_audit.py --simulate 200` | 200 legal orders, 0 must-set violations, 0 problems, 0 unjudged |
| `--acceptance m1` / `travel` (headless) | 34 / 4 PASS, 0 failures |
| `--acceptance m2` (headless, x3, Standard difficulty: the `.std` lines and their voices play) | 46 PASS, 0 failures (second run, see below) |
| Route A `--play-all` (headless, x6) | 134/134, 9 cutscenes, 5 puzzles, 18 variant layers, 27 causal effects; 0 blockers, 0 failures |
| Route EN `--play-all --locale en --lines` (headless, x6) | 134/134 in English, 1001 lines shown, 0 blockers, 0 failures |
| Route K `--play-all --keyboard` (headless, x8) | 134/134: 697 steps, 1982 key presses, 0 awkward, 0 blockers, 0 failures |
| English with the final place names: `--locale en --lines --real --play 14` | 14 actions (prologue and the first of 1995), 98 lines, 0 errors; "the Grasshopper playground" shown, no Slovak spelling left in the lines |

Order of the runs, said plainly: m1, travel and the three routes ran on commit f5c4bd88 (the variants and English wired
in). The place-name commit f3fccb25 changed English texts only; after it ran the import, the static checks, m2, the
short English run, the builds and the smoke tests. Logs: `build/verify_1008/logs/`, `build/verify_1008b/logs/`.

**First m2 run failed, not a game bug (ISSUES QA-CPU-STARVE).** 32 PASS, then `AT16_skip_CS03_same_state` failed after
`WARN lines still playing after 120s` (action.B22.k01) and AT15 stopped at `item CHAIN: no visible slot in the drawer`
after `lines still playing after 30s` (action.F15.x01). QA runs start at below-normal priority and the harness's line
waits count wall-clock time; at that moment other work kept every core busy (the Android staging import and export,
and another project's test runs on the same PC), so the game got almost no CPU. Re-run alone with `--qa-priority
normal`: 46 PASS, 0 failures, the two checks included. The release smoke test hit the same thing (no window within
60 s at below-normal priority) and passed at normal priority.

**Release (Windows).** `build.bat` 22:25-22:28, exit 0 (C# 0 warnings, 0 errors; release filters OK, 576 natural-mode
references, 0 errors; the known `ERR_CANT_OPEN` icon pass, second pass applied). `LastBell.exe` 109.5 MB,
`LastBell.pck` 320.8 MB (7874 files; 127.9 MB voice, the six `.translation` files), `data_LastBell_windows_x86_64/`
81.4 MB; `build/m5/ship/PoslednyZvonec/` refreshed (511.7 MB, 190 files) and zipped:
**`build/m5/ship/PoslednyZvonec-0.2.0-windows-x64.zip`, 373.2 MB** (373,201,659 bytes, zip test OK, sha256
`ec878759…8e1455`). Smoke test (`build/verify_1008b/release_smoke.py`, the shipped copy, hidden window, key messages
to that window only, the player's profile moved aside and restored): QA arguments ignored, Nová hra -> difficulty ->
Začať hru -> S01 -> G01, autosave S01 / 2020 / [G01] / [PHONE, TOOLS]. On this PC (English Windows) the fresh profile
started in English (`locale="en"`), as designed; the owner's own profile has `locale="sk"` and keeps it.

**Linux and macOS** (`python tools/build_ports.py linux macos --skip-import`, then `verify`):
`PoslednyZvonec-0.2.0-linux-x86_64.tar.gz` 362.2 MB (sha256 `dc043ade…a67b7d`), unpacked and started with
`--headless --quit-after 900` in an `ubuntu:24.04` container: exit 0, no error line, `~/.local/share/LastBell`
created. `PoslednyZvonec-0.2.0-macos.zip` 429.6 MB (sha256 `4eeaee9e…d3e48d`): bundle id eu.inviton.lastbell,
version 0.2.0, x86_64 + arm64 executable and .NET runtime, ad-hoc signature, icon, PCK 320.6 MB; not started on a Mac.

The player's save folder is identical to its backup (`build/verify_1008/saves_backup/`) after all runs. Published as
GitHub release `v0.2.0` (three files). Paid generation in this pass: none.

## Owner feedback of 2026-10-07 evening (verified and released)

The owner's notes (art/feedback/2026-10-05_owner_feedback.md, "answers to the exit review + new notes") were applied
by separate tasks: S07 exit `S07.to_S04` side `down` and the paint edit with suburb houses behind the stop (1 call,
USD 0.15); S18 / S62 stop on the left and school yard on the right, S21 `S21.to_S28` in the lower right corner pointing
right (blocking + compass only, USD 0); S69 renamed „Pri LEALe“ in every player text (25 texts, GPT check USD 0.0596;
`docs/writing/out_v5/leal_rename.csv`); narrator recast to the female voice Callirrhoe with a warmer direction and the
four „Pri LEALe“ lines re-voiced (docs/voice/FULL.md). This pass verified everything and rebuilt the release.

| check | result |
|---|---|
| Godot `--headless --import` | exit 0; the re-voiced clips (CS04.02.001, CS07.05.001, B17.003 / .004, entry.S69.001, ZITA extra 2.002) and the translations re-imported |
| `dotnet test src/LastBell.sln` | 506 passed, 3 skipped, 0 failed |
| `check_strings.py` | OK, 5092 keys, 0 errors, 0 warnings |
| `check_rewrite.py --self-test` / `--overlay-only` | OK, 1712 overlay texts, 0 errors, 0 warnings |
| `content_ext.py check` | OK |
| `check_blocking.py --strict` (all 69 rooms) | 0 errors, 15 warnings (11 known exit-point distances / S48 crowding, 4 owner-accepted continuity pairs S11/S51/S57 -> school, S17 <-> S18) |
| `knowledge_audit.py --simulate 200` | 200 legal orders, 0 must-set violations, **0 problems, 0 unjudged** (no new candidate) |
| `--acceptance m1` / `m2` / `travel` (headless) | 34 / 46 / 4 PASS, 0 failures |
| Route A `--play-all --save-load-each` (headless, x6) | 134/134, 9 cutscenes, 5 puzzles, 18 variant layers, 27 causal effects; 0 blockers, 0 failures |
| Route K `--play-all --keyboard` (headless, x8) | 134/134: 697 steps, 1982 key presses (mean 2.8, max 7), 0 awkward, 0 blockers, 0 failures |

Both routes walked the changed exits (S07.to_S04, S18.to_S11 / S17 / S69, S21.to_S28 and the returns). Hidden
1920x1080 screenshots `build/screens/verify_1007/` (S07, S18, S21 with labels; `S07_markers*` / `S21_markers*`): the
S07 shop badge points down, S18 "Dúbravská zastávka" left / "Školský dvor" right / "Pri LEALe" at the courtyard,
S21 "Petržalský podchod" bottom right with a right arrow.

**Regression found and fixed (ISSUES QA-VOICE-SPEED).** The first route runs timed out after 60 minutes (exit 124 at
about 94 of 134 actions, no failure): with the full voice set imported each route played about 1000 voice clips, and
auto-advance waits for a clip that plays at real speed whatever `--time-scale` is. QA-only fix in `DebugHarness.cs`:
`--fast-text` runs with a time scale above 1 set `AudioServer.PlaybackSpeedScale` to the time scale. Re-run: both
routes green, no `WARN lines still playing`. First-attempt logs: `build/verify_1007/logs/first_attempt/`.

**Release.** `build.bat` 20:09-20:20, exit 0 (C# 0 errors; release filters OK, 576 natural-mode references, 0 errors;
the known `ERR_CANT_OPEN` icon pass, second pass applied). `LastBell.exe` 109.5 MB, `LastBell.pck` 291.2 MB (7026
files, 98.9 MB voice), `data_LastBell_windows_x86_64/` 81.4 MB; `build/m5/ship/PoslednyZvonec/` refreshed (482.2 MB, 190
files, no `*.TMP`) and zipped: **`build/m5/ship/PoslednyZvonec-0.1.0-windows-x64.zip`, 346.8 MB** (zip test OK).
Smoke test (`build/verify_1007/release_smoke.py`, hidden window, key messages to that window only): QA arguments
ignored, Nová hra -> difficulty -> Začať hru -> S01 -> G01, autosave S01 / 2020 / [G01] / [PHONE, TOOLS]. The player's
save folder was backed up (`build/verify_1007/saves_backup/`) and is identical afterwards. Logs: `build/verify_1007/logs/`
(`run_verify.sh`). Paid generation in this pass: none.

## Round 2 applied (2026-10-07)

The owner reviewed round 2 on his approval page and answered "i guess ok" with no card marked: every text of
`docs/writing/approval/changes_r2.json` is approved (docs/DECISIONS.md "Round 2 approved and applied"). ISSUES
`APPLY-R2`, `COSM-ZUZANA-TALK`, `COSM-S69-LIGHT`.

| what | where | count |
|---|---|---|
| knowledge rewrites of existing keys | `out_v3/knowledge.csv` -> `check_rewrite.py --overrides-out` -> `sk_overrides.csv`; `ui.hint_step.G07` -> ui.csv | 48 rows: 3 new + 44 changed override rows, 1 ui row; 1519 overrides applied (1521 rows, 2 retired) |
| knowledge overlay | `out_v3/knowledge_ext.json` -> `dialogue_ext.json`: the 13 live C1-C4 entries of the same ids removed first (merge note), then `content_ext.py merge` | 11 sequences (B02, B05, B06, B13, B16, B22, C01, C05, E02, G05, Q7A), 5 topics (ELA.extra 2, JANA95.extra 1, VERA60.extra 2, ZUZANA.extra 7, TAMARA.extra 1); 1453 overlay lines in all |
| Standard / Hard hints | `out_v3/hints.csv` -> ui.csv `hint.nudge.<id>` / `hint.where.<id>` (Core `Hints.NudgeKey` / `WhereKey`) | 268 rows (134 steps); B07's hint went live together with the B05 / B06 Juro fix |
| difficulty UI | `out_v3/ui_difficulty.csv` -> ui.csv; `DifficultyText.cs` fallbacks follow `easy_desc` / `standard_end` | 24 rows; ui.csv 768 keys |

| check | result |
|---|---|
| `extract_strings.py` | OK, 1519 overrides, 0 problems, 0 internal ids; 5090 keys (dialogue 2209, world 2113, ui 768) |
| `check_strings.py` | OK, 0 errors, 0 warnings |
| `check_rewrite.py` `--self-test` / `--overlay-only` / out_v3 knowledge, hints, ui_difficulty / `--overlay-only --overlay knowledge_ext.json` | all OK, 0 errors, 0 warnings (1712 overlay texts, 18 retired keys) |
| `content_ext.py check` | OK |
| `knowledge_audit.py --simulate 200 --write --write-md` | 200 random legal orders, 0 must-set violations; **0 problems, 0 unjudged** (2174 fine, 150 acceptable). The tool now also audits the live `hint.nudge.*` / `hint.where.*` (292 more mentions, all introduced or background). The 29 fixed rows stay as *fine* with `resolved`; the 6 known "Adam reads it off something he sees" rows (B16.k01 Dezider on the map, look.S30.dial Mira's label, look.S45.bench and Q8B.001 / Q8B.002 / Q8B.journal Tamara's note) and the 3 that follow B16.k01 (B16 objective / journal, M07 hint 1) are acceptable; 55 verdicts of replaced texts moved to `retired`. `docs/writing/knowledge/AUDIT.md` |
| `check_blocking.py` | 69 rooms, 0 errors, 15 warnings (the known exit-point distances, none in S69 / S37); `--strict S69 S18` clean |
| `dotnet test src/LastBell.sln` | 506 passed, 3 skipped, 0 failed |
| `--acceptance m1` / `m2` / `travel` (headless) | 34 PASS / 46 PASS / 4 PASS, 0 failures |
| Route A `--play-all --save-load-each` | 134/134, save + load + compare after each, 9 cutscenes, 5 puzzles, 18 variant layers, 27 causal effects; 0 blockers, 0 failures |
| Route B `--play-all --interleave early --all-lines` | 134/134, 2148 distinct lines, 500 looks; 0 blockers, 0 failures |
| Route C7 `--play-all --interleave seed:7 --skip-cutscenes` | 134/134; 0 blockers, 0 failures |
| Route K `--play-all --keyboard` | 134/134 by keys only: 697 steps, 1982 key presses (mean 2.8, max 7), 0 awkward, 0 blockers, 0 failures |
| hint check, Standard (harness `--ui difficulty:standard`, two reveals) | steps G02, B07, I01, D01, F02 (replay 1 / 17 / 33 / 51 / 74): "Postrčenie" + "Kde hľadať" shown, then "Viac sa na štandardnej obťažnosti nedozvieš…", never the exact step |
| hint check, Hard | B07 with 20 s idle: "Ešte nie (2:39)" + the countdown, no text; with 200 s idle: the nudge only + "Na ťažkej obťažnosti je to všetko…" |

Logs: `build/apply_r2/logs/` (`build/apply_r2/run_verify.sh`), coverage `build/apply_r2/coverage_{A,B,C7,K}.json`.

**Cosmetic fixes.** (1) Zuzana: `IActorVisual.SetEngaged` + `DialoguePresenter` mark the NPCs of the running
conversation; `SpriteActorVisual` then plays the manifest clip `idle_engaged` (ZUZANA: the calm video idle) instead of
her hopscotch loop. New harness flag `--clips` logs each NPC's clip per screenshot frame: in Q10A she shows `talk`
while she speaks and `idle_engaged` while Adam speaks, and her hop loop `idle` again after the conversation. (2) S69:
one paid relight guide (nano-banana-pro, USD 0.15, S18 as the light reference) transferred as low-frequency light onto
v6 (`S69_scripts/s69_relight.py`), so no pixel moved (blocking, rects, the 3-2-6 panels, hopscotch, bench and bike are
identical); foreground mask, bike occluder and bell-cap patches rebuilt; ambient re-cut with identical shapes
(`ambient_cut.py` `select_source`). art/masters/bg_natural/S69.md.

**Screens** (hidden QA window 1920x1080, `build/screens/apply_r2/`, all looked at): `S37_zuzana_talk_*`,
`S37_zuzana_seq_*` and `S37_zuzana_talk_strip.png` (standing during Q10A), `S37_zuzana_after_strip.png` (hopping again);
`S18_evening.png`, `S69_evening.png`, `S18_S69_side_by_side.png`; `hint_standard_step{1,17,33,51,74}.png` +
`hint_standard_montage.png`, `hint_hard_waiting.png`, `hint_hard_after_wait.png`, `hint_easy.png`;
`new_game_picker.png` (the approved texts, "…riešenie hádanky ti na požiadanie doplní.").

**Release.** `build.bat` 08:07-08:17, exit 0 (C# 0 errors, release filters OK: 576 natural-mode references, 0 errors;
the known harmless `ERR_CANT_OPEN` of the icon pass, second pass applied). `LastBell.exe` 109.5 MB, `LastBell.pck`
291.3 MB (7026 files; 98.9 MB of it the voice clips present at build time, while a separate voice task was still
regenerating them), `data_LastBell_windows_x86_64/` 81.4 MB; copied to `build/m5/ship/PoslednyZvonec/` (482.2 MB) and
zipped: **`build/m5/ship/PoslednyZvonec-0.1.0-windows-x64.zip`, 346.8 MB** (zip test OK, 190 files). Smoke test
(`build/apply_r2/release_smoke.py`, hidden window, key messages to that window only, player profile moved aside and
restored): QA arguments ignored (still running after `--quit-after 1`, no jump to S44), Nová hra -> the difficulty
step (Standard preselected) -> Začať hru -> S01 -> G01, autosave S01 / 2020 / [G01] / [PHONE, TOOLS]. The player's
save folder was backed up before the runs (`build/apply_r2/saves_backup/`) and restored afterwards (identical).
Paid generation in this pass: USD 0.15 (the S69 relight guide).

## Content v2 applied (2026-10-06, evening)

The owner reviewed the proposed texts on his approval page and said "ok, they are good": everything in
`docs/writing/approval/changes.json` is approved. Applied on top of commit 9f0d2a9 (Core overlay v2):

| what | where | count |
|---|---|---|
| world overlay | `src/game/data/content_ext/world_ext.json` (from `docs/writing/out_v2/pending/world_ext.json`, = C2 + C3 world parts + the C4 epilogue texts; re-checked against the drafts) | room S69 "Sokolíkovský dvor" (exit S18.to_S69 + connection), characters ZUZANA / ZUZANA95 / KUBO, items BELL_MUTE / ZUZA_SLIP / STRAP / BELL_FIXED / BELLCAP, side quests Q10 (Q10A-D, Ivanka 1962) and Q11 (Q11A-C, S69 1995), 15 new hotspots (4 in S32 / S37 / S38), 9 variant layers, epilogue shots 10 and 11, relocation B19 S17 -> S69.rhythm |
| dialogue overlay | `src/game/data/content_ext/dialogue_ext.json` (`content_ext.py merge` of C2 / C3 / C4; identical to the pending `dialogue_ext.integrated.json`) | chunks C2-C4: 70 longer exchanges, 84 extended topics, 114 new topics, 1151 new lines; whole overlay now 88 + 100 extended exchanges, 136 topics |
| existing keys | `sk_overrides.csv` via `check_rewrite.py --overrides-out` (C2, then C3, then C4) and `ui.csv` | C2 69, C3 51 (+1 unchanged), C4 55 + 18 ui rows (incl. `ui.hint_step.B19`); 1517 overrides applied |
| glossary change | `docs/writing/glossary.json` P03 rules -> `look.S69.rhythm`, "Sokolíkovský dvor"; GLOSSARY.md rows | already in 9f0d2a9, verified |

Zuzana rules kept: she appears only in 1962 (S37, traces in S32 / S38) and 1995 (S69); no 2020 / 2035 reference;
nothing about her life; the family photo is not in the repository.

| check | result |
|---|---|
| `extract_strings.py` | OK, 1517 overrides, 0 problems, 0 internal ids; 4785 keys (dialogue 2196, world 2113, ui 476) |
| `check_strings.py` | OK, 0 errors, 0 warnings |
| `check_rewrite.py --self-test` / `--overlay-only` / C1-C4 | OK, 0 errors, 0 warnings (1687 overlay texts, 6 retired keys) |
| `content_ext.py check` | OK |
| `check_blocking.py` | 69 rooms, 0 errors, the 9 known M3-02 warnings; S69 strict clean |
| `dotnet test src/LastBell.sln` | 493 passed, 3 skipped, 0 failed (incl. the new test: saves from before content v2 load at every main step and the game goes on; B19 in S69) |
| `--acceptance m1` headless | 34 PASS, 0 failures |
| `--acceptance m2` headless | 44 PASS, 1 FAIL (AT25: the check counted the new S17 layer after G11 as an E10 layer) -> harness fixed (`ContentAcceptance.cs`, E10 layers only); re-run below |
| `--acceptance travel` headless | TR01-TR03 PASS |
| Route A `--play-all --save-load-each` | 134/134 (94 main + 40 side) by real input, save + load + compare after each; 69 rooms, 18 variant layers, 27 causal effects, Q10 + Q11 done, B19 played in S69; 0 blockers, 0 failures |
| Route B `--play-all --interleave early --all-lines` | 134/134, 2152 lines shown (2135 distinct), 500 looks, epilogue 11 + 11; 0 blockers, 0 failures |
| Route C7 `--play-all --interleave seed:7 --skip-cutscenes` | 134/134, epilogue 11 + 11; 0 blockers, 0 failures |
| Route K `--play-all --keyboard` | 134/134 by keys only: 697 steps, 1978 key presses (mean 2.8, max 8), 0 awkward, 0 blockers |
| old saves | the saves of the previous passes (`build/m5/saves_backup`, `build/m5/m5_run_saves`, `build/m5/verify2/...`) load in the new content |

Fixes in this pass (ISSUES `CONTENT-V2-APPLY`): Core fallback text of `ui.save.corrupted` follows the approved UI
text; tests adjusted to the applied content (no rule changed); engine AT25 check; S69.rhythm interaction point
[1465, 732] -> [1590, 742] because Adam stood facing the camera in front of the painted panels.

**Screens** (hidden QA window, 1920x1080, `build/screens/applied/`, all looked at): 01 Zuzana playing hopscotch in
S37; 02 / 07 Q10A and I10 conversations; 03 Q10B at Štefan's; 04 Q10C; 05 / 06 Q10D (the bell rings, lies in the
grass again afterwards); 10 S69 with Zuzana (40) and Kubo; 11 / 11b her topic menu and the recognition topic
"Odkiaľ ma poznáte?"; 12b B19 at the wall (after the fix); 13-16 Q11; 17b the S18 exit "Sokolíkovský dvor" between the
kiosk and the red car; `c<era>_*` three conversations per era (2020 G05 / C01 / D07, 1995 B03 / B13 / E11, 1962 I01 /
I03 / I09, 1982 E02 / E05 / E08, 2035 F01 / F03 / F11); `epilogue/ending_*` the ending with the Zuzana shots 1/2
(1962, the school door) and 2/2 (1995, the yard). Every text fits its box; nothing covers a speaker.

**Final tree and release.** A parallel change round landed while the routes ran (exit layout NAV-EXITS-01 with a new
2020 Grob chain, "brašňa" -> "inventár"). Its open step "run extract_strings once" was done here; then on the combined
tree: extract_strings OK (1516 overrides), check_strings OK (4785 keys), check_rewrite self-test / overlay-only / C1-C4
OK (1699 overlay texts, 18 retired keys), content_ext OK, check_blocking 69 rooms 0 errors (11 warnings, 2 new from the
exit round), `dotnet test` 493 passed / 3 skipped / 0 failed, `--import` OK, `--acceptance m1` 34 PASS, `m2` 46 PASS,
`travel` 4 PASS, Route C7 again 134/134 (0 blockers, 0 failures; `build/applied/coverage_C7_final.json`).
`build.bat` (release) 23:14, exit 0, C# 0 warnings / 0 errors, release filters OK (576 natural-mode references, 0
errors), the known harmless `ERR_CANT_OPEN`. `LastBell.exe` 109.5 MB, `LastBell.pck` 191.7 MB (2590 files, S69 /
ZUZANA95 / world_ext included), `data_LastBell_windows_x86_64/` 81.4 MB; copied to `build/m5/ship/PoslednyZvonec/`
(382.6 MB) and zipped: **`build/m5/ship/PoslednyZvonec-0.1.0-windows-x64.zip`, 259.1 MB** (zip test OK, 190 files).
Smoke test of the shipped exe (`build/applied/release_smoke.py`, hidden window, key messages to that window only,
player profile moved aside and restored): QA arguments ignored, Nová hra -> S01 -> G01, autosave S01 / 2020 /
[G01] / [PHONE, TOOLS]. The route runs wrote to the player's save folder; it was restored afterwards to the saved
state of `build/m5/saves_backup/` (route saves kept in `build/applied/route_saves*/`). Logs: `build/applied/logs/`.
Paid generation in this pass: none.

## Second verification and release pass (2026-10-06, afternoon)

On the final tree after the change agents for the owner answers of 2026-10-06 afternoon (docs/DECISIONS.md "Owner
answers (2026-10-06, afternoon)"): S13 / S53 / S59 entry hall without the caretaker's desk; S03 with a made-up wooden
grasshopper; S17 / S55 / S61 podlubie leading only into the school's inner yard (no exit), the way to the panel blocks
to the right of the school; S30 renamed "Merací stánok na Starom moste" (21 text keys) and CS03_1 on the Starý most.
Rooms repainted since the first pass: S03, S08, S11, S13, S17, S30, S51, S53, S55, S57, S59, S61 (+ CS03_1, CS09_1).
Nothing changed in the tree while this pass ran (checked by file times). Logs: `build/m5/verify2/logs/`, coverage:
`build/m5/verify2/coverage_{A,B,C7,K}.json`, tables: `build/m5/verify2/coverage_tables.md`.

| check | result |
|---|---|
| `godot --headless --import` | exit 0 |
| `dotnet test src/LastBell.sln` | 361 passed, 3 skipped (UI-only AT08 / AT19 / AT20, covered in the engine), 0 failed |
| `python tools/check_strings.py` | OK: 3359 keys, 0 errors, 0 warnings |
| `python tools/check_blocking.py` | 68 rooms, 0 errors, 9 warnings: the same nine accepted M3-02 distances as in the first pass, none in a changed room |
| `check_rewrite.py --self-test` / `--overlay-only` | OK (44 names, 22 places, 65 terms, 118 protected key rules, 21 verbatim rules; 261 overlay texts, 6 retired keys) |
| `check_rewrite.py` on the current passes | OK (0 errors): ivanka1962_C1, ivanka1962_C3, jasna_winter, m5_verify, S03_lucny_konik, S03_lucny_konik_C4, S03_grasshopper, S30_starymost, S30_starymost_C4. C1 and ivanka1962 now report the new place names as missing (C1: "Lúčny koník" in action.G01.objective / .journal and quest.M01.hint.1; ivanka1962: "Starý most" in quest.M07.goal): those keys were rewritten later on purpose by S03_lucny_konik and S30_starymost, no text is lost (ISSUES M5-07) |
| `extract_strings.py --dry-run` | OK, 1474 overrides applied, 0 override problems, 0 internal ids in player text |
| `--acceptance m1` headless, time-scale 4 | 34 PASS, 0 failures |
| `--acceptance m2` headless, time-scale 3 | 45 PASS, 0 failures |
| `--acceptance travel` headless, time-scale 3 | TR01-TR03 PASS, 0 failures |
| Route A `--play-all --save-load-each` (time-scale 6) | 127/127 by real input, save + load + compare after each; 68 rooms, 9 cutscenes, 5 puzzles, 9 variant layers, 27 causal effects, album replay 9 shots; 0 blockers, 0 failures |
| Route B `--play-all --interleave early --all-lines` (time-scale 8) | 127/127, 1007 lines shown (990 distinct ids), 471 look texts, epilogue 9 + 9; 0 blockers, 0 failures |
| Route C7 `--play-all --interleave seed:7 --skip-cutscenes` (time-scale 8) | 127/127, every cutscene skipped; 0 blockers, 0 failures |
| Route K `--play-all --keyboard` (time-scale 8, AT19) | 127/127 by keys only: 660 steps, 1846 key presses (mean 2.8, max 8), 0 awkward, 0 blockers, 0 failures |

Engine messages in the headless logs are the known ones: `Parameter "t" is null` from the dummy renderer when an
ambient shader parameter is set (headless only, also in the first pass) and, in route A, two leak notes at exit.

**Changed rooms in a real window** (hidden QA window via `tools/qa_godot.py`, 1920x1080, `--room <id> --labels`,
looked at one by one; `build/screens/verify2/`): S13 / S53 / S59 have no desk (Tóno sits on his chair by the wall
lectern in S13, every label on its thing); S17 shows the right exit "Sídliskový dvor s kioskom" at the right edge and
no exit at the podlubie; S55 (2020) and S61 (1982, right exit "Školský záhradný sklad v roku 1982" at the right
edge) have no exit at the podlubie either; S03 shows the grasshopper behind the
slide, clear of the hotspots; S30 shows the booth on the Starý most with the holder, the three digits, the table, the
railing and the boat labelled where they are painted. CS03_1 (`assets/cutscenes/CS03_1.webp`) shows the same booth,
metronome table and truss.

**Regressions found: none**, so nothing was fixed in code or data.

**Release:** `build.bat` (release) 12:50, exit 0, C# build 0 warnings / 0 errors, `release_assets.py` filters OK
(557 natural-mode references, 0 errors), the known harmless `ERR_CANT_OPEN` after the .NET publish; exe version info
0.1.0.0 "Posledný zvonec". `LastBell.exe` 109.5 MB, `LastBell.pck` 186.8 MB (2521 files,
`build/pck_contents_release.txt`), `data_LastBell_windows_x86_64/` 81.3 MB; folder 377.5 MB. Copied to
`build/m5/ship/PoslednyZvonec/` (old copy removed first) and zipped:
**`build/m5/ship/PoslednyZvonec-0.1.0-windows-x64.zip`, 254.8 MB** (zip test OK, 190 files). Log:
`build/m5/verify2/logs/build_release.txt`.

**Smoke test of the shipped exe** (`build/m5/verify2/release_smoke.py`, the exe in `build/m5/ship/PoslednyZvonec/`,
hidden window, key messages posted to that window only, the player's saves and settings moved aside and restored):
started with QA arguments, it was still running at the main menu after 15 s (they are ignored, BUILD-03); Tab x5 +
Enter on "Nová hra", Esc, Tab + Enter in S01: the autosave says room S01, 2020, done [G01], inventory [PHONE, TOOLS].
The process was stopped by the script that started it. The route runs also wrote to the player's save folder; it was
backed up before the pass and restored afterwards (checked by checksum; the route saves are in
`build/m5/verify2/route_saves/`).

Paid generation in this pass: none. Since the first pass the log grew by USD 5.28 in 35 calls (the repaints and edits
listed above); total now USD 151.02 in 950 calls (`art/spend-log.csv`).

## Verification and release pass (2026-10-06)

After the three fix agents (playtest fixes, staging pass, art fixes) and the later owner-requested changes (Jasná in
winter, Ivanka shown as 1962, 2020 text rewrite v2, bus S07-S51 and map regions). Logs: `build/m5/verify/logs/`,
coverage: `build/m5/verify/coverage_{A,B,C7,K}.json`, tables: `build/m5/verify/coverage_tables.md`.

### Suites (final code)

| check | result |
|---|---|
| `dotnet test src/LastBell.sln` | 361 passed, 3 skipped (UI-only AT08 / AT19 / AT20, covered in the engine), 0 failed |
| `python tools/check_strings.py` | OK: 3359 keys, 0 errors, 0 warnings |
| `python tools/check_blocking.py` | 68 rooms, 0 errors, 9 warnings (the accepted M3-02 distances; two new ones of the same kind, S12.to_S13 and S41.to_S42) |
| `python tools/check_rewrite.py --self-test` / `--overlay-only` | OK (44 names, 20 places, 65 terms, 118 protected key rules, 21 verbatim rules; 261 overlay texts) |
| `check_rewrite.py` on the current passes (C1, ivanka1962, ivanka1962_C1, ivanka1962_C3, jasna_winter, m5_verify) | 6 x OK. The older drafts C2 / C3 / C4 / consistency.csv now report the 1962 numbers as "missing": every differing key was rewritten later on purpose (ISSUES M5-07), no text is lost |
| `extract_strings.py --dry-run` | OK, 0 override problems, 0 internal ids in player text |
| `--acceptance m1` headless, time-scale 4 | 34 PASS, 0 failures |
| `--acceptance m2` headless, time-scale 3 | 45 PASS, 0 failures (new: `AT19_tab_stays_in_top_screen`, ISSUES M5-06) |
| Route A `--play-all --save-load-each` (time-scale 6) | 127/127 by real input, save + load + compare after all 127; 68 rooms, 9 cutscenes, 5 puzzles, 9 variant layers, 27 causal effects, era tour with the inventory unchanged, cable cars after F09, album replay 9 shots; 0 blockers, 0 failures |
| Route B `--play-all --interleave early --all-lines` (time-scale 8) | 127/127, 1007 lines shown (990 distinct ids), 471 look texts, epilogue 9 + 9; 0 blockers, 0 failures |
| Route C7 `--play-all --interleave seed:7 --skip-cutscenes` (time-scale 8) | 127/127, every cutscene skipped with Esc, same final state; 0 blockers, 0 failures |
| Route K `--play-all --keyboard` (time-scale 8, AT19) | 127/127 by keys only, see below; 0 blockers, 0 failures |

Regressions found and fixed in this pass: the v2 2020 rewrite had made the S05 hasp look wrong after G06 again
(PT-F05, text fixed back); the Tab focus escaped from a modal into the screen under it (M5-06, fixed in UiRoot). The
S34 look now matches the painting (PT-S19). The first route run after the fixes (all four green) was repeated on the
final code after the UiRoot change.

### AT19: the whole game with the keyboard only

1. **Engine route K** (`--play-all --keyboard`, new `scripts/Diagnostics/KeyboardDriver.cs`): the walkthrough's 94 main
   actions, the ending, the 33 side actions and the postgame checks, with no mouse event at all. World targets and
   exits: Tab / Shift+Tab, whichever way is shorter, then Enter (Backspace = look). GUI: Tab to the bag slot, topic,
   puzzle control, era button, map card, journal tab or dialog button, then Enter. Epilogue shots: Enter. Once per
   era (S03 2020, S12 1995, S36 1962, S64 1982, S42 2035) a shortcut tour: Space held (markers on, off on release),
   I (bag opens with a slot focused), J (journal, Tab reaches it, J closes), H (hints, Esc closes), Esc (pause, Esc
   closes), M (map) with a fast travel by keys (region card, room card). Result: 660 steps, 1846 key presses for
   targets and controls, mean 2.8, maximum 8, no step above 8 ("awkward"), 0 blockers, 0 failures. By kind: world
   targets 472 steps (mean 2.7, max 6), bag slots 85 (mean 4.0, max 7), topics 32 (always 1: the story topic has the
   focus), era buttons 23 (max 3), map 10 (max 8), puzzles P01 max 6, P02 2, P03 3, P04 7, P05 7.
2. **OS level** (`tools/keyboard_os_check.py`, editor runtime = debug build, hidden unfocused window): real Windows
   WM_KEYDOWN / WM_KEYUP messages only, the next key decided from what the game shows (`--menu --watch` prints the
   focus and state, sends nothing). From the main menu of a fresh profile: Nová hra, first-start tips, intro, Space
   held, G01-G11 with every item picked in the bag by keys, J / H / M (fast travel S06 -> S05), save from the pause
   menu, G07, load, G07 again, G08-G10, P01 with one wrong set first (nothing consumed) then the right one, CS01,
   arrival in S11 1995, quit from the pause menu: **27/27 steps, 263 key presses**
   (`build/m5/verify/logs/os_keys_editor.txt`). The topic menu came back after each topic (PT-S17) and Esc left it.
   The player's saves and settings were moved aside and restored.
3. **Found:** the first OS-level run stopped in P01: with the hints opened from the puzzle's "Nápoveda" button, Tab ran
   on from the hint screen into the puzzle underneath and Enter pressed its hidden buttons (the same with the save
   slots over the pause menu). Fixed: UiRoot keeps the focus in the top screen (ISSUES M5-06), checked by the new m2
   row and by the second OS-level run. **Awkward, not blocking:** a full bag needs up to 7 presses to reach an item and
   the map's room graph up to 8 (the OS script went forward only and needed 11 for S05; Shift+Tab is shorter).
   Subtitles are always on; no puzzle depends on colour or sound (unchanged from milestone 5).

### Fixed ISSUES items, spot-checked in a real 1920x1080 window

Hidden QA window (`tools/qa_godot.py`), state by `--replay` / `--act` through the input path, one screenshot each in
`build/screens/fixes/verify/` (looked at one by one). Text-only fixes were checked in the generated tables.

| item | what the screenshot / check shows | file |
|---|---|---|
| PT-F01 | S14: Adam talks to Mira from the front left of the desk; S19: right of Emil's folding table, the table free; S17: right of the rhythm panel | `PT-F01_S14_talk_mira.png`, `PT-F01_S19_talk_emil.png`, `PT-F01_S17_rhythm.png` |
| PT-F02 | item selected: the chip "Vybraný predmet: Servisná brašna" alone, no key hint beside it | `PT-F02_chip_no_hint.png` |
| PT-F03 | map region captions with accents: PETRŽALKA, STARÉ MESTO, DÚBRAVKA | `PT-F03_map_captions.png` |
| PT-F04 | S30 dial: lining 0 digits, the háček of "Číslica" whole | `PT-F04_dial_digits.png` |
| PT-F05 / M5-02 | S05 after G06: the padlock is gone, the middle of the door is the exit "Predsieň záhradnej dielne"; the hasp look was regressed by the v2 rewrite and is fixed again (ISSUES PT-F05) | `PT-F05_M5-02_door_hover.png` |
| PT-F06, PT-S07, PT-S09, PT-S12, PT-S14 | texts in the tables: one S10 sign text (NEPREPISOVAŤ ORIGINÁL), S68 door / S50 switch looks, E06 without Oto, S55 niche needs tools, "Nezačatá" | world.csv / ui.csv |
| PT-F07 | bag with the selected item: "Klikni ním na niečo v scéne, alebo vyber druhý predmet a spoj ich." | `PT-F07_bag_selected_hint.png` |
| PT-F08 / PT-S26 | hints after B07 start at the step that is next, not "Ukáž kazetu Jurovi" | `PT-F08_hint_after_B07.png` |
| PT-F09 / PT-S16 | after G06 no item stays selected (no chip), log `selected=-` | `PT-F09_no_chip_after_G06.png` |
| PT-F10 | hover on the painted S11 clock: "Hodiny časového uzla – výber obdobia" | `PT-F10_S11_clock_hover.png` |
| PT-F11 / PT-S03 | S03: Ela's topic panel on the left, both speakers visible on the right | `PT-F11_S03_topic_left.png` |
| PT-F12 | bag caption "Prenosný chronometer ZVON" whole | `PT-F12_bag_captions.png` |
| PT-F13 | Esc during the (now one-line) intro skips that line and does not open the pause menu (log: mode World after Esc) | `PT-F13_esc_one_line.png` |
| PT-S01 | journal after Q9C: current goal "Človek, ktorý si to zapamätá" with its own next step, not the side-step sentence | `PT-S01_journal_after_Q9C.png` |
| PT-S02 | after D06 nothing archived stays selected (log) | `PT-S02_after_D06.png` |
| PT-S04 | S52 notice marker on the left leaf, separate from the door arrow; S58 marker on the emblem | `PT-S04_S52_markers.png`, `PT-S04_S58_markers.png` |
| PT-S05 | S54 Jana's marker on the laptop, inside her rect | `PT-S05_S54_jana_marker.png` |
| PT-S06 / M5-04 / STAGE-01 | Adam beside what he uses: S54 log, S30 counter (3-2-6 visible), S49 panel, S05 tray, S09 case, S10 cradle | `PT-S06_*.png`, `M5-04_*.png` |
| PT-S08, PT-S15 | album scene titles in ui.csv; map era tabs 1962, 1982, 1995, 2020, 2035 | `PT-S15_map_tabs.png` |
| PT-S10 | S61: tree guard and closed board visible in the same visit as E08 / E09 | `PT-S10_S61_same_visit.png` |
| PT-S13 | S68 cabin interior in winter; the passing cabin was not in these three frames (it passes periodically; earlier evidence `verify/S68_opposite_cabin_on_rope.png`) | `PT-S13_S68_cabin_0*.png` |
| PT-S17 | the topic menu comes back after a topic: seen in the OS-level run (focus on "Ako to zvládate?" after G02, Esc leaves) | `build/m5/verify/logs/os_keys_editor.txt` |
| PT-S18 | S40 I17: Mira (1962) stands in the attic and speaks | `PT-S18_S40_guest_mira_00.png` |
| PT-S20 | December 1982 exteriors: Adam in the charcoal coat and mustard scarf (S58, S61) | `PT-S04_S58_markers.png`, `PT-S10_S61_same_visit.png` |
| PT-S21 | CS07_1 / CS07_2 / CS06 frames: ○ + □ △ on the plate; the ORIGIN folder's symbol is a foreshortened + (checked at 5x zoom) | assets/cutscenes |
| PT-S22 / M5-05 | toasts appear only after G02's lines (frame 0: line, no toast; frame 3: toasts) | `PT-S22_M5-05_toast_waits_0*.png` |
| PT-S23 | hint modal open: no world hover label on top | `PT-S23_hover_hidden_hint.png` |
| PT-S24 | S60 Q9C: Adam shows the drawing from a child's distance | `PT-S24_S60_gap.png` |
| PT-S27 | S43 wall lettering RECEPCIA | bg_natural/S43.webp |
| PT-S28 | S53: Adam wears the mask indoors | `PT-S28_S53_mask.png` |
| M5-01 | the CS07 album replay works in all route runs | route logs |
| M5-03 | main menu "Verzia 0.1.0" | `M5-03_menu_version.png` |

### Release build and smoke test

`build.bat` (release) on 2026-10-06 07:36: exit 0, C# build 0 warnings / 0 errors, `release_assets.py` filters OK,
one engine message `ERR_CANT_OPEN` right after the .NET publish (seen in earlier builds, harmless: the exe carries
the icon and version info 0.1.0.0 "Posledny zvonec", so no second export pass was needed); `build/windows/` was clean (no old window running, the
old `*.dll~RF*.TMP` leftovers are gone). `LastBell.exe` 109.5 MB, `LastBell.pck` 186.6 MB (2511 files,
`build/pck_contents_release.txt`), `data_LastBell_windows_x86_64/` 81.3 MB; folder 377.4 MB. Copied to
`build/m5/ship/PoslednyZvonec/` and zipped: **`build/m5/ship/PoslednyZvonec-0.1.0-windows-x64.zip`, 254.2 MB**
(zip test OK, 190 files). Log: `build/m5/verify/logs/build_release.txt`.

Smoke test of the shipped exe (`build/m5/verify/release_smoke.py`, hidden window, real Windows key messages, the
player's saves and settings moved aside and restored): started with `-- --room S44 --replay 94 --quit-after 1`, it
was still running at the main menu after 15 s (the QA arguments are ignored in a release build, BUILD-03); Tab x5 +
Enter on "Nová hra", Esc on the first-start tips, then Tab + Enter in S01: the autosave says room S01, 2020, done
[G01], inventory [PHONE, TOOLS]. The hidden window cannot be captured by PrintWindow, so this run has no
screenshots (the menu with "Verzia 0.1.0" is `build/screens/fixes/verify/M5-03_menu_version.png`). The process was
stopped by the script that started it.

Note: other agents kept working in the repository during this pass (S03 / S17 / S55 / S61 repaints, S03 texts and the
C4 writing context, 07:26-07:40). The release snapshot of 07:36 contains their state of S03 and S17 at that time;
the four route runs above had started before those files changed. `check_strings`, `check_blocking`,
`check_rewrite --self-test` and `extract_strings --dry-run` were re-run on the tree of the build (all OK). Rebuild
with `build.bat` (and re-run the routes) once that work is finished. Done in the second pass of the same afternoon
(section above): the shipped build now contains that work and the later owner changes.

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
| AT19 | **passed** | 2026-10-06: engine route K, the whole game (127 actions, ending, postgame) by key events only, 0 blockers, max 8 presses per step; the prologue from the main menu by real Windows key messages, 27/27 steps; Tab focus kept inside the top screen (M5-06, m2 `AT19_tab_stays_in_top_screen`); puzzles do not depend on colour or sound; subtitles always on (section "AT19" above) |
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

Summary (updated 2026-10-06): **30 of 30 passed** (24 plain, 6 with a note).

| result | rows | count |
|---|---|---|
| passed | AT01-04, AT07-15, AT17-19, AT21, AT22, AT25-30 | 24 |
| passed with note | AT05, AT06, AT16, AT20, AT23, AT24 | 6 |

## Found in this pass

2026-10-06: M5-02 to M5-05 are fixed since (ISSUES, spot checks in the verification section); M5-06 to M5-08 are
the findings of the verification pass. The locked DLL copies are gone with the rebuild.

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
