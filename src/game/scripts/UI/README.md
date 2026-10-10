# LastBell UI (`scripts/UI`, `scenes/ui`, `assets/ui`)

All player-facing screens on top of the world runtime. Rules stay in `LastBell.Core`; the UI only
reads Core view models (`ViewBuilder`, `Journal.Build`, `Navigation`, `Quests`, `Hints`, `Puzzles`,
`Epilogue`, `Postgame`) and sends input through the normal path (`WorldInput.Submit/Dispatch`,
`GameRuntime.Commit/SubmitPuzzle/ClosePuzzle/Save/Load`, the documented Core functions).
Every visible string comes from `localization/*.csv` through `TextService`.

## Entry point

`scenes/ui/UiRoot.tscn` (script `UiRoot.cs`) is instanced by `Main` under `HudHost` (CanvasLayer 40).
It registers `ISubtitleView`, `ITopicMenuView`, `IPuzzleView`, `ICutsceneView`, `IEraCardView`,
`IHoverView` and claims Inventory, Journal, Map, Pause, Portal, Hud, MainMenu, Hints, Save, Load,
Settings — every placeholder of the world runtime stands down.

Layers: `UiRoot` (unscaled) → cutscene frame, subtitles, `Scaled` (HUD and all screens, scaled by the
HUD-scale setting: its logical size is 1920x1080 / scale, so layouts reflow instead of overflowing).
CanvasLayer 60: era card (above the world's black transition fade). CanvasLayer 70: hover label at the cursor and the
cursor layer.

Core-mode screens are shown from `GameRuntime.ModeChanged` (Inventory, Journal, Map, Pause, Puzzle);
Esc/J/M/I for them stay with the world's input router (Core `Escape`/`CloseOverlay`). UI-only modals
(main menu, hints, save/load, settings, help, credits, portal chooser, album, dialogs, ending) live on
a stack in `UiRoot`; while one is open `UiRoot._ShortcutInput` closes the top one on Esc and keeps
every other key from the scene, and the backdrop swallows clicks (AT22). The keyboard focus stays in the top screen (`UiRoot.FocusScope`: the top UI modal, else the open puzzle, pause, journal or map): Tab / Shift+Tab wrap at its ends and a focus that lands outside (arrow keys, deferred focus calls) is brought back, so Enter never presses a button hidden under the hints or the save slots (AT19 keyboard pass 2026-10-06).

## Language change

Texts are resolved when a label or button is made, so a change of the language (settings, or the QA flag `--locale`)
makes the UI again: `TextService.LocaleChanged` → `UiRoot.Relocalize` (end of the frame) → `HudView.Relocalize`,
`InventoryPanel.Relocalize` and `ModalScreen.Relocalize` for every screen, open or not. Rules that follow from it:

- `ModalScreen.Build()` can run more than once. Start the lists it fills empty (`tabs.Clear()`), and keep nothing
  from an earlier call.
- A screen that is filled by something other than `Refresh()` overrides `Reopened()` (the puzzle window).
- A view outside `ModalScreen` that reads a text in `_Ready` gets a `Relocalize()` and a call from `UiRoot.Relocalize`.
- Check: `--acceptance language` (LG01-LG07) searches every label, button and tooltip for texts of the old language.

## Screens

| file | what |
|---|---|
| `Theme/UiTheme.cs`, `Theme/Ui.cs`, `Theme/Glyph.cs` | Godot `Theme` built in code (paper/ink, dark wood HUD, brass, teal focus ring), Alegreya + Alegreya Sans (OFL, `assets/ui/fonts`), factory helpers, drawn vector icons. Minimum hit area `UiTheme.MinHit` = 66 canvas px (= 44 px at 1280x720). |
| `Hud/HudView.cs` | thin bottom strip: bag, eye (press and hold = Space held: markers), selected-item chip with cancel (right-click alternative), the optional "hold Space" key hint in the centre, chronometer (portal), hint, journal, map, menu. Buttons avoid the template exit zones at the screen edges and never take keyboard focus. It is the registered `IHoverView` and keeps the payload (`CurrentHover`, `HoverChanged`) for the hover label and the drawer, but shows no hover text itself (owner control changes 2026-10-05). |
| `Hud/HoverLabel.cs` | the hover label next to the cursor (Polda-like behaviour, our look): target name in large outlined Alegreya, the action sentence below only when Core returns one for the selected item; with a selected item nothing at all over targets without a valid use (owner item 6, INT-09), nothing over the floor; right of the cursor image, flips left at the right edge and above the cursor near the HUD strip, clamped on screen, hidden over GUI controls; Tab focus: centred at the focused target; high-contrast setting adds a dark backing. Inventory slots keep the drawer's own hover line. |
| `Hud/CursorSet.cs`, `Hud/CursorLayer.cs` | the painted style-A cursor set as hardware cursors (`Input.SetCustomMouseCursor`, 64/96/128 px by window scale, hotspot = tip pixel; files `assets/ui/cursors/<name>_<size>.png` + `hotspots.json`, masters `art/ui/cursors/`, tool `art/tools/cursors.py`). `CursorLayer` decides the kind every frame: Core's left-click resolution of the hit (talk / hand / look / pointer), exits by side (left / right / up / down), the selected item (icon composed with a small pointer), busy (hourglass) during lines, cutscenes and transitions; GUI = pointer. Fallback without hardware cursors: system cursor + the item icon drawn in software; QA `--soft-cursor` draws the cursor into screenshots. Optional highlight ring. |
| `Hud/SubtitleView.cs` | subtitle panel (size, background, speaker name from settings), speaker tag, continue marker, look bubble. |
| `Hud/ToastLayer.cs`, `Hud/ItemIcon.cs` | notices (item added, new goal, saved), autosave indicator; item pictures or a drawn placeholder token. |
| `Dialogue/TopicMenuView.cs` | topic menu (story topics bold, repeatable heard topics marked). |
| `Inventory/InventoryPanel.cs` | drawer: items / archived tabs, slots, detail card with Select/Combine/Deselect and Look buttons; combining goes through the resolver. |
| `Journal/JournalScreen.cs` | Goals (pins), Findings (clues, progress log, first looks), People (transcripts), Time map, Album (ending replay, cutscene replays). |
| `Map/MapScreen.cs` | era sheets, rooms as nodes by distance from the time node, regions (`region.<district>.name`), connections, fast travel via `Navigation.FastTravel`. Cards fit the panel width: they shrink, then wrap into serpentine bands (no horizontal scrolling). |
| `Menus/*` | main menu (+emblem), the New Game difficulty picker (`DifficultyPicker`), pause, hints (levels per difficulty: Easy direction / place / exact step, Standard nudge / where to look, Hard only the nudge behind a three-minute countdown; `GameRuntime.SecondsWithoutProgress`), save/load (8 slots, quick, autosave, thumbnails, overwrite/delete/load confirmations, corrupt files via Core's validation), settings (tab Hra: the running game's difficulty, `GameRuntime.SetDifficulty`; audio buses, text speed, auto-advance, subtitles, size, language, window mode, HUD scale 100–200 %, reduced motion, high-contrast labels, cursor highlight, walk speed 100/125/150 % (`PresentationSettings.WalkSpeedFactor`), tips), help, credits (`assets/ui/credits.json`), portal chooser, album. |
| `Puzzles/PuzzleModal.cs`, `Puzzles/PuzzleControls.cs` | modal framework for every `puzzles[].controls.type`: matching (P01, P04), rotate_overlay (P02), digits (P03), grid_choice (P05). Drafts stored through Core on every change, reset, hint, "fill in correctly" when `Puzzles.CanFill`, no timers. Option pictures for P01: `assets/ui/puzzle_glyphs.json`. |
| `Cutscenes/CutscenePlayer.cs`, `Cutscenes/CutsceneCamera.cs` | letterbox, beat picture `res://assets/cutscenes/<CS>_<n>.webp` (n from 1) or a styled card (debug builds print the shot as a dev note), finale end card, skip button. Optional pan / zoom per beat from `res://data/cutscene_camera.json` (start and end rect of the 1920x1080 picture, over the beat's `duration_min_s`; reduced motion shows the end rect; written by `art/tools/cutscenes.py camera`, see `art/cutscenes/README.md`). |
| `Cutscenes/EraCardView.cs`, `Cutscenes/EndingSequence.cs` | era title card; epilogue shots (`res://assets/cutscenes/EPILOGUE_<n>.webp`, else `res://assets/epilogue/<n>.webp`, else a card with the caption) → rolling credits → postgame note. |
| `Settings/UiSettings.cs` | `user://settings.cfg`, applied to `PresentationSettings`, audio buses, window and locale. |
| `Diagnostics/UiDebug.cs` | QA steps for screenshots (only with harness args). |

## Data files

- `assets/ui/credits.json` — generated by `python tools/build_credits.py` from `art/source/CREDITS.md`
  and `art/source/rooms/CREDITS_*.md` (`--check` verifies it is current). Rebuild after new photos.
- `assets/ui/puzzle_glyphs.json` — presentation-only shape pictures for puzzle option values.
- Both are non-resource files: the export filter must include `assets/ui/*.json` (like `data/*.json`).
- `default_bus_layout.tres` (project root) defines the Music / Ambience / SFX / Voice buses so the
  world's AudioService finds "Music" at startup.

## QA screenshots (`--ui` steps, after the harness flags)

```
G=.tools/godot/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe
$G --path src/game --resolution 1920x1080 -- --replay 40 --skip-lines --ui journal:1 --wait 1500 --screenshot build/screens/ui/journal.png
$G --path src/game --resolution 1920x1080 -- --replay 26 --skip-lines --ui-scale 200 --ui puzzle:B16 --wait 1800 --screenshot build/screens/ui/p02_200.png
```

Steps (repeatable, 0.4 s apart): `main_menu`, `pause`, `settings[:tab]`, `save`, `load`, `load_corrupt`
(writes a damaged slot 8!), `try_load_corrupt`, `journal[:tab]`, `map`, `hints`, `reveal_hint`,
`inventory`, `select:<ITEM>`, `puzzle:<actionId>`, `draft:<json>`, `submit`, `reveal_all`, `credits[:roll]`,
`ending`, `postgame_all` (commits the postgame route through Core), `help`, `portal`, `tips`, `talk`,
`cutscene:<CS>` (replay of a watched cutscene), `beat:<CS>:<i>`, `era:<year>`, `savegame:<slot>`,
`press:<ui action>`, `key:<Key>`, `wait:<ms>`, `report`, `difficulty:<easy|standard|hard>` (the running game's
difficulty, as the settings row), `idle:<seconds>` (seconds without progress, Hard's hint wait), `new_game` (the difficulty
picker of New Game), `pick:<difficulty>` (a card of the picker); `hints` over an open puzzle opens the hints of its quest. Options: `--ui-scale <100..200>`,
`--ui-reduced-motion`, `--ui-contrast`. Note: `savegame`/`load_corrupt` write into the real
`user://saves` (Windows `%APPDATA%/LastBell/saves`); delete test slots afterwards.

## Known gaps

- No painted UI art yet apart from the cursors and the Space marker badges (frames, panels, menu background "closed bag on
  a table"); everything else is drawn with style boxes and vector glyphs. Cutscene and epilogue pictures exist (31 frames, `art/cutscenes/README.md`).
- No key rebinding UI (the controls tab lists the bindings); no save import/export; no play time.
- No touch layer (long press = look) yet.
- No UI sounds.
