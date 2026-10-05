# LastBell — Godot 4.7 .NET presentation layer (`src/game`)

The Godot project of *Posledný zvonec*. It renders and animates; **every rule lives in
`../LastBell.Core`** (see its README). The world runtime asks Core for view models and resolutions,
walks the hero, asks Core again on arrival and commits through Core. It never decides rules.

## Run

| what | command (from the repo root) |
|---|---|
| play (product owner) | double-click `play.bat` (builds C#, imports assets, starts the game window) |
| build C# | `dotnet build src/LastBell.sln` (game + Core + tests) or `dotnet build src/game/LastBell.csproj` |
| import assets (after adding files) | `.tools/godot/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe --headless --path src/game --import` |
| Core tests | `dotnet test src/LastBell.sln` |
| headless QA run | `<console exe> --headless --path src/game -- --replay 94 --quit-after 1` |
| screenshot (needs a window, no `--headless`) | `<console exe> --path src/game --resolution 1920x1080 -- --room S05 --screenshot build/screens/S05.png` |

Godot runs the assembly that `dotnet build` puts into `.godot/mono/temp/bin/Debug/`, so build after
every C# change before launching from the command line (the editor builds by itself).
Exports must include `data/*.json` and `data/**/*.json` (non-resource files) in the export filter.
Windows export: `build.bat` → `build/windows/`; presets, templates and mobile notes: `docs/BUILD.md`.

## Project layout and ownership

```
project.godot  LastBell.csproj  icon.svg  README.md
data/game.json                  canonical data (tools/sync_data.py, never hand-edit)
data/art_overrides.json         visual-only corrections (schema in scripts/World/ArtOverrides.cs)
data/debug/walkthrough.json     copy of design-doc/walkthrough.json for --replay/--play
data/ambient/**                 living-world agent
localization/{dialogue,world,ui}.csv (+ generated .translation, imported by Godot)
assets/bg|variants|fg|items|music|sfx|voice/   art agents (paths from game.json / assets.csv)
assets/ambience/**  data/audio/*.json  scripts/Audio/**   audio (scripts/Audio/README.md)
assets/actors/<ID>/             character sheets (art pipeline)
assets/ambient/**  scripts/Living/**            living-world agent
assets/ui/**  scenes/ui/**  scripts/UI/**       UI agent
scenes/Main.tscn  scenes/room/Room.tscn         world runtime (this agent)
scripts/Runtime/      GameRuntime (autoload "Game"), TextService, PresentationSettings
scripts/World/        WorldStage, Room, WalkArea, Actor, IActorVisual, PlaceholderActorVisual,
                      InteractionController, HotspotLabelLayer, DevBlockout, ArtOverrides
scripts/PlayerInput/  InputRouter, LogicalCommand, InputActions, WorldInput
scripts/Presentation/ DialoguePresenter, DefaultSubtitleView, HoverPresenter, MusicPlayer,
                      Placeholders/ (temporary UI until the UI agent claims each panel)
scripts/Hooks/        UiBus + UI interfaces, WorldHooks, AmbientHost
scripts/Diagnostics/  DebugHarness, WalkthroughReplayer
```

Namespaces: `LastBell.Game.Runtime|World|PlayerInput|Presentation|Hooks|Diagnostics`; use
`LastBell.Game.UI` and `LastBell.Game.Living` for your own code. All code and comments are English;
player-visible text only comes from the CSV tables through `TextService`.

## Node tree

```
/root/Game                      GameRuntime (autoload, C#): content, session, events, save/load
/root/Main                      Main.cs
  WorldStage (Node2D)           displayed room, transitions, era card
    Room_<id>                   scenes/room/Room.tscn, built from Core's RoomView
      background                painted art res://assets/bg/<id>.webp, else DevBlockout (dev aid)
      prop_state_variants       visible visual_variant_layers (res://assets/variants/...)
      AmbientHost               living world: behind actors (fill from data/ambient/<id>.json)
      npc_shadows               ShadowLayer
      npcs_and_adam_sorted_by_feet_y   y-sorted actors (Hero_ADAM, Npc_<ID>), position = feet
      foreground_mask           res://assets/fg/<id>.webp (or art_overrides foreground_mask)
      ambient_front             living world: in front of everything (AmbientHost.Front)
      hotspot_labels            HotspotLabelLayer: Space labels, item-valid outlines, Tab focus
      hud                       marker only (the HUD is the persistent HudHost below)
      DevOverlay                F3 / --dev: rects and walk polygon above painted art
    TransitionOverlay (CanvasLayer 50)   fade + placeholder era card
  InteractionController         resolver-driven clicks, walking, re-resolve on arrival, Tab focus
  InputRouter (Node2D)          raw input -> LogicalCommand, routed by Core mode
  DialoguePresenter             line playback; SubtitleLayer (CanvasLayer 20) with default views
  PlaceholderLayer (CanvasLayer 30)/PlaceholderUi   hover, inventory strip, puzzle, pause/journal/map, portal
  HudHost (CanvasLayer 40)      UI agent's res://scenes/ui/UiRoot.tscn is instanced here
  LivingHost                    living agent's res://scripts/Living/LivingRoot.cs (Node) is instanced here
  AudioService                  scripts/Audio: music crossfades + cues, room ambience, sfx, voice bus (replaces MusicPlayer)
  DebugHarness                  only with user args after "--"
```

## Extension points (no need to edit world-runtime files)

**UI agent** — create `res://scenes/ui/UiRoot.tscn`; Main instances it under `HudHost` before the
game starts. In its scripts:

- Register views: `UiBus.Register(ISubtitleView | ITopicMenuView | IPuzzleView | ICutsceneView |
  IEraCardView | IHoverView)`. Registering claims the panel and the placeholder stands down.
- Claim state-driven panels you implement: `UiBus.Claim(UiPanel.Inventory | Journal | Map | Pause |
  Portal | Hud | MainMenu | Hints | Save | Load | Settings)`. Show them from Core's mode
  (`GameRuntime.Instance.ModeChanged`, `State.Mode`) or on `UiBus.OpenRequested` (keys H, settings
  button of the pause placeholder, T for the portal chooser).
- Claiming `UiPanel.MainMenu` stops Main from auto-starting; call `GameRuntime.Instance.NewGame()` or
  `Load(slot)` yourself.
- Send player input through the normal path only: `WorldInput.Submit(new Hit.Item(id), PointerButton.Left|Right)`
  for inventory slots, `WorldInput.Dispatch(LogicalCommand.X)` for HUD buttons, `WorldInput.HoverItem(id, pos)`.
  Never change Core state behind the resolver (exception: modal UIs call the documented Core
  functions: `Puzzles.UpdateDraft/Reset/Fill` via `GameRuntime.Update`, `GameRuntime.SubmitPuzzle`,
  `ClosePuzzle`, `Navigation.FastTravel`/`UsePortal`, `Quests.Pin`, `Hints.RevealNext`, `GameRules.CloseOverlay`).
- Era card: `IEraCardView.Show(era, card, date, done)`; the transition waits for `done()`.
- Settings: write `PresentationSettings.*` then `PresentationSettings.NotifyChanged()`; locale via
  `TextService.SetLocale`; key rebinding through Godot `InputMap` (action names in `InputActions`).
- Notices: `UiBus.Notice` (ui keys); claim `UiPanel.Hud` to take them over.

**Living-world agent** — create `res://scripts/Living/LivingRoot.cs` (a `partial class LivingRoot : Node`);
Main instances it under `LivingHost` before any room is built. In `_Ready`:

- `ActorVisualRegistry.Register(IActorVisualFactory factory, priority)`: return an `IActorVisual`
  (origin = feet centre = sheet pivot; `HeightPx`, `WalkSpeedPxPerSecond` = sheet `stride_px_per_s`,
  `SetLocomotion`, `SetTalking`, `PlayGesture(actions[].animation)`) or null to fall through. The
  current room swaps visuals immediately (`ActorVisualRegistry.Changed`).
- `WorldHooks.RoomBuilt += room => ...`: fill `room.Ambient` (behind actors), `room.Ambient.Front`
  (above the foreground mask) and `room.Ambient.Actors` (y-sorted with the hero). Data path:
  `room.Ambient.DataPath`. Also `RoomRefreshed`, `RoomLeaving`, `RoomReady`, `HeroWalkingChanged`.
- Useful room data: `room.View` (Core RoomView incl. `CausalEffects`, `VariantLayers`), `room.Walk`
  (polygon, Top/Bottom), `room.Perspective`, `room.Overrides` (art_overrides), `room.Hero`, `room.Npcs`.
- Respect `PresentationSettings.ReducedMotion`.

## GameRuntime (autoload "Game")

`GameRuntime.Instance`: `Content`, `Session`, `State`, `NewGame()`, `Commit(actionId)`,
`OpenPuzzle / SubmitPuzzle / ClosePuzzle`, `Update(Func<GameState,GameState>)`, `Save(slot)`,
`Load(slot)`, `LoadFromJson`, `ListSlots`, `DeleteSlot`, `Autosave()` (after commits and room
arrivals, never while walking; slot `autosave`), saves in `user://saves/<slot>.json` (Windows:
`%APPDATA%/LastBell/saves`).

C# events: `StateChanged(old,new)`, `RoomChanged(new,old)`, `EraChanged`, `ModeChanged(new,old)`,
`InventoryChanged(added,removed)`, `SelectionChanged`, `HotspotLabelsChanged`, `ActionCommitted(ActionDef)`,
`ActiveLineChanged`, `PuzzleOpened(actionId, PuzzleDef)`, `PuzzleClosed`, `SessionReplaced` (new
game/load: rebuild everything), `Saved`, `LoadFailed(slot, TextRef)`. Godot signals (plain types):
`StateChangedSignal`, `RoomChangedSignal(roomId)`, `ModeChangedSignal(mode)`.

`TextService.Get(key, fallback)` / `Get(TextRef)` returns `Tr(key)`, or the Slovak fallback when the
table has no entry. `TextService.Ui("ui.area.name", ("placeholder", value))` for ui.csv keys.

## Input (CODING_AGENT_START.txt)

| input | logical command | world / inventory | dialogue line / cutscene | topic menu | overlays |
|---|---|---|---|---|---|
| left click | Primary | the one logical action (resolver) | advance | buttons | UI |
| right click | Secondary | look at target; empty floor: inventory; selected item: cancel first | advance | — | — |
| Space | ToggleLabels | labels of all visible hotspots incl. atmospheric ones and exits (Core toggles in `world` mode only, as `runtime_contract.ts`; in the open drawer Space does nothing) | advance | — | — |
| Tab / Shift+Tab | FocusNext/Previous | cycle targets (NPCs, progress props, atmospheric, exits) | — | GUI focus | GUI focus |
| Enter | Confirm | left click on the focused target | advance | GUI accept | GUI |
| Backspace | Back | right click on the focused target (or empty floor) | — | leave | — |
| Esc | Cancel | cancel selection, else pause (GameRules.Escape) | skip cutscene / queued lines | leave | close |
| I / J / M / H / T | Inventory / Journal / Map / Hint / Travel | open (T: era chooser at anchor nodes) | — | — | J/M close |
| F3 / F5 / F9 | DevOverlay / QuickSave / QuickLoad | dev conveniences | | | |

Hover text comes from `Session.Hover(hit)`: the name always, the action sentence only while an item
is selected and Core says the rule is executable. An invalid item click resolves to `None`: no walk,
no text, the selection stays. Touch (`PlayerInput/TouchGestures.cs`, docs/BUILD.md): tap = left, long press 0.5 s = right,
two-finger tap = Space; the GUI gets emulated taps first, gestures fire on release in the world.

## Room build, movement, perspective

- `Room.Build` uses `RoomView.LayerOrder`; unknown layer names get an empty node (warning).
- Hit test order: NPC rects, props (later data entries on top), exits, walk polygon (floor), empty.
  A left click on empty background walks to the closest walkable point.
- `WalkArea`: deterministic polygon pathfinding (straight line or visibility graph over reflex
  corners, A*); no NavigationServer.
- Perspective: scale 0.80 at the top of the walk band → 1.00 at the bottom (feet y), overridable
  per room in `art_overrides.json` (`actor_scale`, `walk_band`). Walk speed = visual stride × scale.
- NPCs stand at their hotspot rect's bottom centre (+ `npc_feet` nudge ≤ 40 px).
- Walking to an NPC: every NPC interaction point in the data lies straight below the NPC, so the hero
  stands beside the NPC instead (`Room.ApproachPoint`: `NpcApproachGap` px left or right of the rect,
  the side he comes from if walkable) and turns side-on to the person (ISSUES LIVING-02). Props and
  exits use the game.json interaction point. Presentation only; arrival still re-resolves through Core.
- Window busts (`IActorVisual.CastsShadow == false`) get no feet shadow (ISSUES LIVING-01).
- State patches (`art_overrides.json` `rooms.<id>.state_patches`: texture, top-left `pos`, `after` /
  `until` action ids) are drawn above the background in `prop_state_variants`, immediately, for props
  the hero changed himself (S01 bag taken, S05 groceries on the tray, S05 shed unlocked; ISSUES ART-VAR-01).
- Hero spawn: the interaction point of the exit leading back to the previous room, else `spawn`.
- Transitions: exits fade out → `Navigation.Travel` → build → era card on era change → fade in.
  Special transitions, portals and fast travel follow Core's room change; the old room stays visible
  while the action's own lines/cutscene play, the new room appears before its first-entry lines.

## Debug / QA harness (user args after `--`)

| flag | effect |
|---|---|
| `--room <id>` | dev jump into a room (after `--replay`, if given). Not a legal Core travel. |
| `--replay <n>` | replay walkthrough steps 1..n through Core rules (same as the Core tests); checks inventory and room per step |
| `--play <n>` | perform walkthrough actions (after `--replay`, up to step n) through the **input path**: travel by clicking exits / portals, select items, click targets, choose topics, solve puzzles |
| `--act <actionId>` | (repeatable) resolve + commit one action through the input path; travels to its room first |
| `--input <spec>` | (repeatable, in order) `key:<LogicalCommand>`, `select:<ITEM>`, `portal:<year>`, `click:x,y`, `rclick:x,y`, `hover:x,y`, `wait:<ms>`; real Godot input events (GUI first, then the InputRouter): `mouse:x,y` (left), `rmouse:x,y` (right), `keyev:<Godot Key>` (e.g. `keyev:Space`), touch `tap:x,y`, `longpress:x,y`, `twotap:x,y` — coordinates are canvas px (1920x1080) at any window size |
| `--acceptance [m1\|m2]` | in-engine acceptance checks through real input events; both sets by default. `m1`: the prologue input rules (right click, Space, invalid item no-op, re-check on arrival, save/load without duplicates, P01, arrival in S11; `scripts/Diagnostics/PrologueAcceptance.cs`, docs/MILESTONE1.md). `m2`: the acceptance_tests.csv rows beyond the prologue (AT02-AT09, AT11, AT12, AT15-AT26, AT29 and parts of AT19/AT24; `ContentAcceptance.cs`, docs/MILESTONE2.md). Prints `HARNESS PASS/FAIL`, exit code 1 on a failure. Frame-timed m1 checks want `--time-scale` ≤ 4 in a window |
| `--real` | acts (`--act`, `--play`) use real Godot input events only: the target is clicked at a point where the room's hit test returns it and no GUI control is on top (else `HARNESS BLOCKER`), items are picked from the drawer's slot buttons, topics from the topic menu's buttons, puzzles by clicking the modal's controls and confirm button, portals with T and the era button; lines play out by auto-advance (`scripts/Diagnostics/RealInputDriver.cs`) |
| `--play-all` | (implies `--real`) all 94 main actions, the ending (epilogue shots, credits, postgame note by clicks/keys), all 33 side actions after the credits, then the postgame checks (era tour through the portals, cable cars after F09, re-entry of every room with a triggered causal effect / variant layer, album replay of the ending, CS07 replay from the journal); exit code 1 on a blocker or failure (`ContentQa.cs`) |
| `--play-side` | the same ending + side + postgame part after `--play`/`--replay` |
| `--interleave early\|seed:<n>` | with `--play-all`: side actions at legal points of the main route, greedily as early as possible or at seeded random points |
| `--save-load-each` | save, load and compare the state after every action (AT17) |
| `--skip-cutscenes` | press Esc in every cutscene (AT16) |
| `--all-lines` | look at every target on every arrival and after every action, at every item when it is received, and choose every ambient topic in every room after the postgame (AT24 line audit) |
| `--shots <dir>` | JPEG evidence after every action, puzzle success line, cutscene beat, ending shot, first sight of a variant layer / causal effect, postgame step and blocker (needs a window) |
| `--coverage <file.json>` (`--coverage-label <text>`) | what the run verified (actions with order and save/load result, quests, puzzles, cutscene beats, line ids, look texts, rooms, eras, variant layers, causal effects, butterflies, cache, ending shot counts, postgame, blockers, click retries, failures); `python tools/m2_coverage.py <files>` turns them into the docs/MILESTONE2.md tables |
| `--screenshot <path.png>` | after everything is settled (+`--wait`, default 400 ms) save the viewport and quit; needs a window |
| `--frames <k>` `--interval <ms>` | k screenshots `<name>_00.png …` (or `{n}` in the path) every interval ms |
| `--labels` | turn on the Space labels |
| `--dev` | dev overlay over painted art; also `PresentationSettings.DevNotes` (stage directions on cutscene cards without a painting, the placeholder puzzle's solve button) — off for players, also in debug builds such as play.bat |
| `--lines` | print every shown line (`HARNESS line <id> [speaker] name: text`) |
| `--fast-text` | instant text, short holds, no cutscene minimum (QA speed) |
| `--skip-lines` | skip remaining lines after the acts |
| `--quit-after <s>` | quit after s seconds (headless runs) |
| `--autosave` | keep autosave on (off by default in harness runs) |

For speed, add Godot's own engine flag `--time-scale <k>` before `--` (walking, fades and timers run
k times faster), e.g. `--headless --path src/game --time-scale 6 -- --fast-text --play 94 --quit-after 1`.

The harness prints `HARNESS state room=… era=… mode=… done=… inventory=[…] selected=… line=…` and
`HARNESS ERROR …` lines (exit code 1 on error with `--screenshot`/`--quit-after`).

Examples:

```
# all 94 main steps through Core in the engine
<console exe> --headless --path src/game -- --replay 94 --quit-after 1
# the prologue through the real input path (walking, clicks, puzzle, special transition)
<console exe> --headless --path src/game -- --fast-text --play 11 --quit-after 1
# blockout + labels screenshot
<console exe> --path src/game --resolution 1920x1080 -- --room S02 --labels --screenshot build/screens/S02.png
# walk animation frames
<console exe> --path src/game --resolution 1920x1080 -- --skip-lines --input click:1600,1000 --frames 4 --interval 220 --screenshot build/screens/walk.png
```

## Known gaps (world runtime)

- Status of milestone 1 (prologue G01–G11, P01, CS01, arrival in S11): see `docs/MILESTONE1.md`.
- The UI agent's screens (scripts/UI) and the living-world sprites (scripts/Living) have replaced the
  placeholders; the placeholders stay as fallbacks.
- Audio: see `scripts/Audio/README.md` (music, ambience, sfx; voice lines play from `assets/voice/<line_id>.ogg` once they exist). QA: `-- --audio-report`.
- A save made while a puzzle modal is open resumes in the world (ISSUES GAME-02).
- Space is not part of Godot's `ui_accept` (removed in `InputActions.EnsureDefaults`): Enter accepts in the GUI,
  Space stays the labels key and never presses a focused inventory slot or button (ISSUES INT-01).
