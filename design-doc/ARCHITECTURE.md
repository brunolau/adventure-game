# Posledný zvonec — Implementation architecture (binding for all coding agents)

Added 2026-10-05. The handoff (`CODING_AGENT_START.txt`, `README.txt`, `game.json`, `runtime_contract.ts`,
`walkthrough.json`, `acceptance_tests.csv`) defines *what* the game does. This file defines *how* it is built.
Art rules are in `ART_DIRECTION.md`.

## Engine and tools

- **Godot 4.7.2 .NET (C#)**, binary: `.tools/godot/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe`
  (use the `_console` exe for headless runs: `--headless --path src/game ...`).
- .NET SDK 9/10 installed; all C# projects target **net8.0** (what Godot 4.7 .NET uses) unless Godot's SDK requires otherwise.
- Python 3.14 with Pillow + requests for art/tool scripts. ffmpeg is not installed system-wide; tools that need it
  use `imageio-ffmpeg` (pip) or a binary under `.tools/ffmpeg/`.
- Targets: Windows first; macOS, Android, iOS later. Keep code platform-neutral (no Win32 APIs, `user://` for saves,
  input abstracted so touch can map onto the same logical actions).

## Repository layout

```
design-doc/          handoff (canonical, do not edit game.json/walkthrough/runtime_contract) + this file,
                     ART_DIRECTION.md, LOCATIONS_REGISTER.csv, ISSUES.md (contradictions found)
art/                 art pipeline: tools/ (python), source/ (reference photos + CREDITS.md),
                     masters/ (full-res generated PNGs), spend-log.csv
src/LastBell.sln
src/LastBell.Core/     pure C# rules engine, no Godot dependency (net8.0)
src/LastBell.Core.Tests/  xUnit tests: rules, walkthrough replay, random legal orders, save/load, acceptance (logic level)
src/game/            Godot project (project.godot, LastBell.csproj referencing ../LastBell.Core)
  data/game.json     copy of design-doc/game.json (synced by tools/sync_data.py — never hand-edit)
  data/ambient/<room>.json   ambient animation layers per room
  data/art_overrides.json    visual-only adjustments (label anchors, rect nudges ≤40 px, foreground masks)
  localization/      Godot CSV translation tables (see below)
  assets/bg/ items/ actors/ variants/ ambient/ ui/ music/ sfx/ voice/   shipped assets (webp/ogg)
  scenes/ scripts/   Godot scenes and C# presentation code
tools/               repo tooling (sync_data.py, extract_strings.py, validators)
```

## Layering

1. **LastBell.Core** owns all rules: content model loaded from `game.json`, `GameState`, the shared resolver for
   hover *and* click (`resolveInteraction`), guards, atomic `commitAction`, puzzles' solution checking, travel and
   connections, fast travel, journal and hints, quests, butterfly/causal effects, cache contract, epilogue selection,
   postgame, and save validation. It is a faithful C# port of `runtime_contract.ts` extended to cover the whole
   `game.json`. It is deterministic, has no I/O besides loading/saving JSON strings, and never formats display text:
   it returns **text keys** (with the Slovak fallback string) for the presentation layer.
2. **Godot presentation** (`src/game`) renders and animates: one generic data-driven `Room` scene builds any of the
   68 rooms from data (background, variant layers by state, hotspots, exits, NPCs, walk polygon → navigation,
   feet-y depth sorting and scaling, foreground mask, ambient layers). UI: inventory, dialogue/subtitles, journal,
   map, hints, save/load, settings, accessibility. Puzzle modals and cutscenes are data-driven where the data allows.
   Presentation never decides rules; it asks Core, and after the hero finishes walking it asks Core again
   (conditions re-checked on arrival, as the handoff requires).
3. **Assets** are referenced by the paths in `assets.csv` under `src/game/assets/`.

## Text keys and localization (texts live outside code)

All player-visible text is shown through Godot `Tr(key)` from CSV translation tables in `src/game/localization/`:
`dialogue.csv` (spoken lines), `world.csv` (names, looks, labels, journal, hints, quests, puzzles, epilogue),
`ui.csv` (menus, buttons, settings, system messages). Format: header `keys,sk,en` (en empty for now), UTF-8,
comma-delimited, quoted as needed. Missing translation → fall back to the Slovak text from `game.json`.

Key scheme (stable, derived from ids; spaces inside ids are kept as-is):

| text | key |
|---|---|
| any line with a `line_id` (dialogues.csv, lines, looks, entries, cutscene beats, topics) | the `line_id` itself |
| room name | `room.<roomId>.name` |
| hotspot name / look without line id / look variant without line id | `hotspot.<hotspotId>.name` / `hotspot.<hotspotId>.look` / `hotspot.<hotspotId>.look.<n>` |
| exit label / exit locked look | `exit.<exitId>.label` / `exit.<exitId>.locked` |
| connection label / locked look | `conn.<from>.<to>.label` / `conn.<from>.<to>.locked` |
| item name / look / purpose | `item.<id>.name` / `item.<id>.look` (= its look_line_id if present) / `item.<id>.purpose` |
| action label / journal text / objective | `action.<id>.label` / `action.<id>.journal` / `action.<id>.objective` |
| character name | `char.<id>.name` |
| topic label | `topic.<topicId>.label` |
| quest title / goal / reward / hint n | `quest.<id>.title` / `.goal` / `.reward` / `.hint.<n>` (n from 1) |
| puzzle title / clue / wrong / success / confirm label | `puzzle.<id>.title` / `.clue` / `.wrong` / `.success` / `.confirm` |
| era card / date | `era.<year>.card` / `era.<year>.date` |
| map region (a `rooms[].district`, kept verbatim) | `region.<district>.name` (ui.csv) |
| epilogue shot caption / line | `epilogue.<n>.shot` / `epilogue.<n>.line` (n from 1) |
| UI | `ui.<area>.<name>` (e.g. `ui.menu.continue`) |

Core exposes these via a static `TextKeys` helper so both sides build identical keys. `tools/extract_strings.py`
generates the tables from `game.json` + `dialogues.csv` and reports any visible string without a key.
Accepted Slovak rewrites of game.json texts (ISSUES TEXT-01) live in `src/game/localization/overrides/sk_overrides.csv`
and are applied by `extract_strings.py` while game.json still has the replaced text; `check_strings.py` verifies them.

## Language of code

The product owner's rule (2026-10-05): **all code is English** — identifiers (types, members, variables,
parameters, files, folders, scenes, nodes, script names), comments, XML docs, log messages, commit messages and
technical docs. Slovak appears only in player-facing content: `game.json` data, `dialogues.csv` and the `sk` column
of the localization tables. Domain concepts get English names (e.g. *skrýša* → `Cache`, *školník* → `Caretaker`,
*zápisník* → `Notebook`, *denník* → `Journal`); ids from `game.json` (`S17`, `G01`, `TONO82`…) are used as data,
never as Slovak-derived identifiers. The code name of the project is **LastBell** (English for *Posledný zvonec*).

## Conventions for agents

- Work only inside the directories your task assigns. Do **not** `git commit` or push — the orchestrator commits.
- Never edit `design-doc/game.json`, `walkthrough.json`, `runtime_contract.ts`, `acceptance_tests.csv`. If you find a
  contradiction or bug in the handoff, append it to `design-doc/ISSUES.md` (id, file, description, proposed fix) and
  work around it in a clearly marked place.
- Build and test what you write (`dotnet build`, `dotnet test`, Godot `--headless` import/run). Report honestly what
  passes and what does not.
- C# style: nullable enabled, file-scoped namespaces, records for immutable data, `System.Text.Json`, no reflection
  magic; public APIs documented with XML comments. Namespaces `LastBell.Core.*`, `LastBell.Game.*`.
- HTTP user agent for any web/API calls: `LastBell-ArtPipeline/0.1 (+https://github.com/brunolau/adventure-game)`.
- Paid generation (fal.ai, key in env `FAL_KEY` or Windows HKCU\Environment) only within the budget your task states;
  log every paid call in `art/spend-log.csv`.
