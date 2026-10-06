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
| screenshot (needs a window, no `--headless`) | `python tools/qa_godot.py --path src/game --resolution 1920x1080 -- --room S05 --screenshot build/screens/S05.png` |
| any QA run with a window (screenshots, `--shots`, `--frames`, `--acceptance`, `--perf`) | `python tools/qa_godot.py <the same Godot arguments>`: the window is created hidden (never on a screen, never focused), the run is muted, capped at 60 fps and runs at below-normal priority; a minimized window would stop drawing, so it is hidden instead (owner request 2026-10-06; `scripts/Diagnostics/QaWindow.cs`, options in the script header) |

Godot runs the assembly that `dotnet build` puts into `.godot/mono/temp/bin/Debug/`, so build after
every C# change before launching from the command line (the editor builds by itself).
Exports must include `data/*.json` and `data/**/*.json` (non-resource files) in the export filter.
Windows export: `build.bat` → `build/windows/`; presets, templates and mobile notes: `docs/BUILD.md`.

## Project layout and ownership

```
project.godot  LastBell.csproj  icon.svg  README.md
data/game.json                  canonical data (tools/sync_data.py, never hand-edit)
data/content_ext/*.json         content overlays applied by Core on load (dialogue_ext: longer sequences and extra
                                topics; travel_ext: exits, connections, map regions; LastBell.Core/README.md section 13)
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
scripts/Presentation/ DialoguePresenter, DefaultSubtitleView, HoverPresenter,
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
      hotspot_labels            HotspotLabelLayer: Space-held markers (QA --labels: text labels), item-valid outlines, Tab focus
      hud                       marker only (the HUD is the persistent HudHost below)
      DevOverlay                F3 / --dev: rects and walk polygon above painted art
    TransitionOverlay (CanvasLayer 50)   fade + placeholder era card
  InteractionController         resolver-driven clicks, walking, re-resolve on arrival, Tab focus
  InputRouter (Node2D)          raw input -> LogicalCommand, routed by Core mode
  DialoguePresenter             line playback; SubtitleLayer (CanvasLayer 20) with default views
  PlaceholderLayer (CanvasLayer 30)/PlaceholderUi   hover, inventory strip, puzzle, pause/journal/map, portal
  HudHost (CanvasLayer 40)      UI agent's res://scenes/ui/UiRoot.tscn is instanced here
  LivingHost                    living agent's res://scripts/Living/LivingRoot.cs (Node) is instanced here
  AudioService                  scripts/Audio: music crossfades + cues, room ambience, sfx, voice bus (replaced the removed MusicPlayer, ISSUES AUDIO-01)
  DebugHarness                  only with user args after "--", only in debug/editor builds (BUILD-03)
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

## Input (CODING_AGENT_START.txt + owner control changes 2026-10-05, docs/DECISIONS.md, ISSUES INT-08)

| input | logical command | world / inventory | dialogue line / cutscene | topic menu | overlays |
|---|---|---|---|---|---|
| left click | Primary | the one logical action (resolver) | advance | buttons | UI |
| double click / double tap (same target, ≤ `PresentationSettings.DoubleClickSeconds` 0.35 s; floor ≤ 40 px) | Primary ×2 | skip the walk: the hero is put at the destination (`Actor.FinishWalk`), arrival re-resolves through Core and runs once; the second press never submits again and is not passed to a line the first one started | — | — | — |
| right click | Secondary | look at target; empty floor: inventory; selected item: cancel first; open bag with an item picked: a right click outside the panel only closes it and keeps the item (owner item 6, INT-09) | advance | — | — |
| Space (hold) | ShowMarkers / HideMarkers | while held: a painted round marker on every visible hotspot incl. atmospheric ones and exits (arrow badge), no text; release (or window focus loss) hides them (Core `GameRules.SetHotspots`: show in `world` mode only, hide in any mode; in the open drawer Space does nothing). With a selected item only the targets where it has an executable use get a marker (owner item 6, INT-09). HUD eye button: press and hold. Touch: two-finger hold | advance | — | — |
| Tab / Shift+Tab | FocusNext/Previous | cycle targets (NPCs, progress props, atmospheric, exits; with a selected item only its valid targets) | — | GUI focus | GUI focus |
| Enter | Confirm | left click on the focused target; Enter twice quickly = skip the walk | advance | GUI accept | GUI |
| Shift+Enter | ConfirmSkip | left click on the focused target and skip the walk | advance | — | — |
| Backspace | Back | right click on the focused target (or empty floor) | — | leave | — |
| Esc | Cancel | cancel selection, else pause (GameRules.Escape) | skip this line; a second Esc within 0.5 s skips the rest of the cutscene / all queued lines (PT-F13; that second Esc never opens the pause or closes the returning topic menu) | leave | close |
| I / J / M / H / T | Inventory / Journal / Map / Hint / Travel | open (T: era chooser at anchor nodes) | — | — | J/M close |
| F3 / F5 / F9 | DevOverlay / QuickSave / QuickLoad | dev conveniences | | | |

Hover text comes from `Session.Hover(hit)`: without a selected item the name of every target; with a selected item a label
(name + action sentence) only over a target where Core says the item rule is executable, nothing over any other target
(owner control change 6, 2026-10-06, ISSUES INT-09); nothing over empty floor. A left click into the scene closes the open bag
and then resolves normally. It is drawn **next to the cursor**
(`UI/Hud/HoverLabel.cs`, large outlined Alegreya, flips left / up near the edges, hidden over GUI controls, over the open
bag's bar and detail card and while any screen is open, `UiRoot.ScreenCovers`, PT-S23); the bottom HUD strip no longer
shows it. Keyboard focus (Tab) shows the same label at the focused target. The cursor is the painted
contextual set (`UI/Hud/CursorSet.cs`, `CursorLayer.cs`): pointer (floor), hand (action), speech (dialogue), magnifier
(look-only), exit arrow by side, the selected item's icon, hourglass while lines / cutscenes / transitions play; hardware
cursors sized to the window (64/96/128 px), system cursor as fallback. An invalid item click resolves to `None`: no walk,
no text, the selection stays; a successful item use clears it (Core `CommitAction`, PT-F09 / PT-S16). After a topic's
lines the same conversation's topic menu opens again until "Ukončiť rozhovor" / Esc or until no topic is left
(`DialoguePresenter` + Core `Dialogue.ReturnToMenu`, PT-S17). Notices (`UI/Hud/ToastLayer.cs`) are queued while lines
play and while any screen is open (bag, puzzle, journal, map, pause, menus, hints, ending), at most three at once; beside
an open topic menu only in a slot that does not touch it (PT-S22, M5-05). Screens show their own confirmations in the
title row (`ModalScreen.ShowStatus`, e.g. "Uložené"). The main menu shows the game version from project.godot
`application/config/version` (0.1.0; the export presets leave their version fields empty and take the same number;
game.json `version` is the internal content data version, M5-03). Touch (`PlayerInput/TouchGestures.cs`, docs/BUILD.md): tap = left, long press 0.5 s = right,
two-finger hold = Space held, double tap = double click; the GUI gets emulated taps first, gestures fire on release in the world.

## Room build, movement, perspective

- `Room.Build` uses `RoomView.LayerOrder`; unknown layer names get an empty node (warning).
- Hit test order: NPC rects, props (later data entries on top), exits, walk polygon (floor), empty.
  A left click on empty background walks to the closest walkable point.
- `WalkArea`: deterministic polygon pathfinding (straight line or visibility graph over reflex
  corners, A*); no NavigationServer.
- Perspective: scale 0.80 at the top of the walk band → 1.00 at the bottom (feet y), overridable
  per room in `art_overrides.json` (`actor_scale`, `walk_band`). Walk speed = visual stride × scale × the hero's
  `PresentationSettings.WalkSpeedFactor` (default 1.25, owner 2026-10-05; Settings → Accessibility → walk speed 100/125/150 %);
  the sprite visual plays the walk cycle at the same factor, so the feet do not slide.
- NPCs stand at their hotspot rect's bottom centre (+ `npc_feet` nudge ≤ 40 px).
- Walking to an NPC: every NPC interaction point in the data lies straight below the NPC, so the hero
  stands beside the NPC instead (`Room.ApproachPoint`: `NpcApproachGap` px left or right of the rect,
  the side he comes from if walkable) and turns side-on to the person (ISSUES LIVING-02). Props and
  exits use the game.json interaction point. Presentation only; arrival still re-resolves through Core.
- Window busts (`IActorVisual.CastsShadow == false`) get no feet shadow (ISSUES LIVING-01).
- NPC labels (Space, Tab focus) sit 18 px above the drawn figure (`Room.PlaceNpcLabels`, `Actor.HeadPosition`), not at
  the template `label_anchor`; an art_overrides `label_anchor` still wins (ISSUES INT-07).
- NPC sprite variants can switch after an action: `data/ambient/actors.json` `variants_after` (Jana after Q9C, ART-AGE-04).
- Hero clothing per room: `data/ambient/actors.json` `hero_mask2020_rooms` (2020 face mask) and `hero_coat1982_rooms`
  (December 1982 winter coat in the exteriors S57, S58, S61, S62, S64, S66 and S65; ISSUES PT-S20) and
  `hero_coat2035_rooms` (the same coat in winter Jasná 2035: S41, S42, S45, S48, S50, S67, S68; DECISIONS "Jasná 2035
  is in winter"), resolved by `ActorStaging.HeroVariant`; the variant sheets (`assets/actors/ADAM/*_mask2020`, `*_coat1982`) share the default
  sheets' timing and geometry rules.
- State patches (`art_overrides.json` `rooms.<id>.state_patches`: texture, top-left `pos`, `after` /
  `until` action ids) are drawn above the background in `prop_state_variants`, immediately, for props
  the hero changed himself (S01 bag taken, S05 groceries on the tray, S05 shed unlocked; ISSUES ART-VAR-01).
- Hero spawn: the interaction point of the exit leading back to the previous room, else `spawn`.
- Props the hero uses: the natural blocking puts the use point beside the object (not in front of it), so it stays
  visible while he reaches sideways (PT-S06, M5-04, staging pass 2026-10-05); a child NPC may get a wider
  `approach_gap` (S60 Jana, PT-S24).
- Speakers who are not in the room (`actions[].staging.rule`, ISSUES PT-S18; `World/GuestStage.cs`): **guests**
  (blocking `guests.<action>`: character, `enter` point at the nearest exit, `stand` point, staging `variant`,
  `facing`, `delay`) walk in with the action's first line, their own lines wait until they stand (at most 6 s, a
  click hurries them), and they walk out and are removed when the action's lines end (S40 I17 Mira 60; S61 E08
  Tóno 82 + Oto 82). They are temporary actors (`Room.Guests`, hotspot id `guest:<ID>`), never Core NPCs; a character
  who stands in the room as an NPC is never moved or doubled. **Remote speakers** (`data/staging/remote_speakers.json`:
  phone, recording, radio = service channel, device) get a `SpeakerIndicator` badge beside the hero or above the
  action's target instead of a body; the subtitle name tag sits above it. Walk cycles of the guests: three-quarter
  `walk_right` sheets in their actor.json (`art/tools/guest_walks.py`); TONO82 has a `guest_standing` variant.
- Time node (PT-F10, DECISIONS "The painted S11 clock is the time node"): blocking `time_node` (own `rect`, or
  `hotspot` = a game.json hotspot whose plain left click Core resolves as a look) in S10, S11, S31, S51, S57; while
  Core lists portal targets in the room, a click walks there and opens the same era chooser as the HUD clock (T);
  hover label `ui.travel.time_node`, hand cursor, a Space marker for the own-rect clocks. Right click still looks;
  item uses on a bound hotspot (D04, C05) still work.
- Transitions: exits fade out → `Navigation.Travel` → build → era card on era change → fade in.
  Special transitions, portals and fast travel follow Core's room change; the old room stays visible
  while the action's own lines/cutscene play, the new room appears before its first-entry lines.
- Rides (travel overlay, exits with travel `bus` / `tram`): Core travel first; a first ride's lines
  (`LineSource.Travel`) play in the stop being left; then fade, the transport card (region name and
  `ui.travel.card`: "Autobusom · <stop>") with the `travel_bus` / `travel_tram` sound, fade in. A map fast
  travel into another region (to its hub) shows the same card. Reduced motion: same, shorter, nothing moves.
- Map (`UI/Map/MapScreen.cs`): era tabs, then the era's regions as cards (visited rooms, hub, "Tu si",
  the transport into the region) joined by their transport links; a card opens the region's room graph
  (district captions, hub tag, back button). Fast travel only where Core says `CanFastTravel` (inside the
  current region, or to a hub of another region; tooltip `ui.map.via_hub` on the other rooms).

## Debug / QA harness (user args after `--`)

Only **debug and editor builds** read these arguments (`Runtime/LaunchArgs.cs`, `OS.IsDebugBuild()`): the editor
binary, `play.bat` and the QA export (`build.bat debug` → `build/windows_debug/`). A release export
(`build.bat` → `build/windows/`) ignores everything after `--` and logs one line saying so (ISSUES BUILD-03).
The other QA switches (`--ui …`, `--audio-log`, `--audio-report`, `--no-ambient`, `--ambient-report`,
`--reduced-motion`) follow the same rule. Engine options before `--` (`--resolution`, `--log-file`, `--verbose`)
work in every build.

| flag | effect |
|---|---|
| `--room <id>` | dev jump into a room (after `--replay`, if given). Not a legal Core travel. |
| `--replay <n>` | replay walkthrough steps 1..n through Core rules (same as the Core tests); checks inventory and room per step |
| `--play <n>` | perform walkthrough actions (after `--replay`, up to step n) through the **input path**: travel by clicking exits / portals, select items, click targets, choose topics, solve puzzles |
| `--act <actionId>` | (repeatable) resolve + commit one action through the input path; travels to its room first |
| `--input <spec>` | (repeatable, in order) `key:<LogicalCommand>`, `select:<ITEM>`, `portal:<year>`, `click:x,y`, `rclick:x,y`, `hover:x,y`, `wait:<ms>`; real Godot input events (GUI first, then the InputRouter): `mouse:x,y` (left), `rmouse:x,y` (right), `dblclick:x,y` (two left clicks), `move:x,y` (mouse motion: hover label, cursor), `keyev:<Godot Key>` (press + release), `keydown:<Key>` / `keyup:<Key>` (e.g. `keydown:Space` holds the markers for a screenshot), touch `tap:x,y`, `longpress:x,y`, `twotap:x,y` (two-finger hold and release) — coordinates are canvas px (1920x1080) at any window size |
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
| `--labels` | QA text labels of every visible target (the pre-2026-10-05 Space labels, for art review; players only get markers) |
| `--markers` | the Space markers on (as if Space were held) |
| `--soft-cursor` | also draw the cursor in software, so `--screenshot` shows it (hardware cursors are not in viewport captures) |
| `--targets` | print every target of the room (`HARNESS target <id> kind rect point anchor`) |
| `--blocking natural\|template` | natural re-blocking proposal: rooms with `data/blocking/<room>.json` use its presentation geometry and `assets/bg_natural/<room>.webp` (`World/RoomBlocking.cs`; project setting `last_bell/presentation/blocking`, default `natural` since milestone 3 (all 68 rooms), `--blocking template` shows the old geometry; validator `tools/check_blocking.py`; docs/reblock/README.md) |
| `--dev` | dev overlay over painted art; also `PresentationSettings.DevNotes` (stage directions on cutscene cards without a painting, the placeholder puzzle's solve button) — off for players, also in debug builds such as play.bat |
| `--lines` | print every shown line (`HARNESS line <id> [speaker] name: text`) |
| `--fast-text` | instant text, short holds, no cutscene minimum (QA speed) |
| `--skip-lines` | skip remaining lines after the acts |
| `--quit-after <s>` | quit after s seconds (headless runs) |
| `--autosave` | keep autosave on (off by default in harness runs) |
| `--perf [n]` (`--perf-dwell <s>`, `--no-preload`) | release-engineering probe (`Diagnostics/PerfProbe.cs`): from the first room walk n rooms (default 20) through their exits (dev jumps, unvisited neighbours first), stay `--perf-dwell` s (1.5) in each; logs per hop the room build time, the longest frame of the transition and in the room before, then process / Godot / texture memory (`HARNESS perf …`). `--no-preload` turns `World/RoomPreloader.cs` off for comparison. Needs a window for real texture uploads; numbers in docs/BUILD.md "Performance" |

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
# blockout + QA text labels screenshot (players see markers: --markers or --input keydown:Space)
python tools/qa_godot.py --path src/game --resolution 1920x1080 -- --room S02 --labels --screenshot build/screens/S02.png
# walk animation frames
python tools/qa_godot.py --path src/game --resolution 1920x1080 -- --skip-lines --input click:1600,1000 --frames 4 --interval 220 --screenshot build/screens/walk.png
```

## Known gaps (world runtime)

- Status of milestone 1 (prologue G01–G11, P01, CS01, arrival in S11): see `docs/MILESTONE1.md`.
- The UI agent's screens (scripts/UI) and the living-world sprites (scripts/Living) have replaced the
  placeholders; the placeholders stay as fallbacks.
- Audio: see `scripts/Audio/README.md` (music, ambience, sfx; voice lines play from `assets/voice/<line_id>.ogg` once they exist). QA: `-- --audio-report`.
- A save made while a puzzle modal is open reopens that modal on load (`open_puzzle`, ISSUES GAME-02); a save
  made in pause / map / journal resumes in the scene (`GameRules.ResumeAfterLoad`, UI-05).
- Space is not part of Godot's `ui_accept` (removed in `InputActions.EnsureDefaults`): Enter accepts in the GUI,
  Space stays the labels key and never presses a focused inventory slot or button (ISSUES INT-01).
