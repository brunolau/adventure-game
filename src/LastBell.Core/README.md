# LastBell.Core

Pure C# rules engine of *Posledný zvonec* (code name LastBell). It targets net8.0 and has no Godot
dependency. It does no I/O except parsing and producing JSON strings, and it is deterministic.
It ports `design-doc/runtime_contract.ts` function by function and extends it to everything
`game.json` defines.

Core **never formats display text**. Every player-visible string comes back as a
`TextRef(Key, Fallback)`. Show `Tr(Key)` and fall back to `Fallback` (the Slovak text from
`game.json`) when the table has no entry. Keys follow the table in `design-doc/ARCHITECTURE.md`
and are built by `LastBell.Core.Text.TextKeys`.

## Namespaces

| namespace | contents |
|---|---|
| `LastBell.Core.Content` | `GameContent` (loader and indexes), data records (`RoomDef`, `ActionDef`, ...), `ContentValidator` |
| `LastBell.Core.State` | `GameState` (immutable record), `GameMode` |
| `LastBell.Core.Rules` | `GameRules` (the TS port), `Hit`/`Resolution`, `Playback`, `Navigation`, `Dialogue`, `Puzzles`, `Quests`, `Hints`, `Journal`, `WorldEffects`, `TemporalCache`, `Epilogue`, `Postgame`, `JsonDeep` |
| `LastBell.Core.Views` | `ViewBuilder` (room, inventory, map, hover view models) |
| `LastBell.Core.Save` | `SaveCodec`, `SaveValidationException` |
| `LastBell.Core.Text` | `TextRef`, `TextKeys`, `UiText` |
| `LastBell.Core` | `GameSession` (an optional mutable holder with a `StateChanged` event) |

Every rule function is static and pure: `(GameContent, GameState, ...) -> GameState`. Functions
that are not allowed in the current situation return the **same instance**, so
`ReferenceEquals(old, new)` means nothing happened. The exceptions are `CommitAction`, which
throws, and `TryCommitAction`, which returns a result.

## 1. Loading content

```csharp
using Godot;
using LastBell.Core;
using LastBell.Core.Content;

string json = FileAccess.GetFileAsString("res://data/game.json");
GameContent content = GameContent.Load(json);   // or GameContent.Load(Stream)
var session = new GameSession(content);         // starts from content.InitialState
```

Load validates every reference. A failure throws `ContentLoadException`, whose `Errors` list names
the id and the JSON path, for example `$.actions[1](G02).requires_done[0]: unknown action 'NOPE'`.
`GameContent` is immutable and thread-safe, so load it once.

Lookups: `GetRoom/FindRoom`, `GetAction/FindAction`, `GetItem/FindItem`, `FindCharacter`,
`FindHotspot` (returns room and hotspot), `FindExit`, `GetPuzzle`, `FindCutscene`, `FindQuest`,
`GetQuestOf(actionId)`, `FindEra(year)`, `FindLine(lineId)` (returns the line and its owner),
`FindTopic(topicId)`, `SpeakerName(speakerId)`, `FindLookText(key)`. Raw records are in
`content.Data`.

## 2. Rendering a room

```csharp
RoomView view = ViewBuilder.Room(content, state);       // or session.Room()
```

`RoomView` contains the following:

- `BackgroundAsset`, `Music`, `CameraFamily`, `WalkPolygon`, `Spawn`, `LayerOrder`, `Name`.
- `Hotspots`: only visible ones, in data order. Each has `Id`, `Name`, `IsNpc`, `CharacterId`,
  `IsAtmospheric` (look-only), `Rect`, `InteractionPoint`, `LabelAnchor` and
  `ValidForSelectedItem` (draw the subtle outline). `Npcs` holds just the NPC entries.
  Never draw or hit-test a hotspot that is not in this list.
- `Exits`: always present and inspectable, with `Unlocked`, `Travel` (the transition style) and
  `Rect`.
- `VariantLayers`: draw every layer with `Visible == true` above the background, in order.
  `DeferredUntilReentry` means the trigger is done but the hero has not left the room yet.
  The handoff rule is that changes apply on the next entry, so the walk area never changes under
  the hero.
- `CausalEffects`: the active `causal_effects` for this room. Use them to pick props, ambience and
  NPC staging. Their texts are production notes, not captions.
- `HotspotLabels`: the state of the Space toggle. `AccessibleOrder` is the Tab order: NPCs,
  progress props, atmospheric props, then exits.
- `PortalTargets`: chronometer destinations when this room is an open anchor node.

Rebuild the view after every state change. It is cheap. `ViewBuilder.Inventory(content, state)`
gives the drawer: items in acquisition order, `IsSelected` and `IsArchived`. Archived items have no
remaining use, go on a separate tab and are still owned.

## 3. Hover and click: one resolver

```csharp
Hit hit = new Hit.Hotspot("S10.chrono");   // Hit.Floor(x,y), Hit.Exit(id), Hit.Item(id), Hit.Empty()
Resolution r = GameRules.ResolveInteraction(content, state, hit, PointerButton.Left);
HoverInfo hover = ViewBuilder.Hover(content, state, hit);   // Name + ActionLabel + the same Resolution
```

Use the **same** call for hover and click. The resolution kinds and how to apply them:

| `Resolution` | presentation does | then call |
|---|---|---|
| `None` | nothing at all (an invalid item click is a complete no-op: no walk, no line, selection kept) | — |
| `Look(Text, ObservationKey)` | show the text (left click on an atmospheric prop, or any right click on a target) | `Journal.ApplyLook` (records the first look) |
| `CancelSelection` | — (a right click with an item only cancels the selection) | `GameRules.CancelSelection` |
| `ToggleInventory` | open or close the drawer | `GameRules.ToggleInventory` |
| `SelectItem(ItemId)` | attach the icon to the cursor | `GameRules.SelectItem(state, id, keepInventoryOpen: combineMode)` |
| `Walk(X, Y)` | walk | — |
| `Travel(ExitId, To)` | walk to the exit, **re-resolve on arrival**, transition | `Navigation.Travel(content, state, exitId)` |
| `Dialogue(CharacterId, HotspotId, Topics)` | walk, re-resolve, show the topic menu | `Dialogue.OpenMenu`, then section 6 |
| `Action(ActionDef)` | walk to the target's `InteractionPoint`, **re-resolve on arrival**, and only continue if it is still the same action | `GameRules.CommitAction` or, if `ActionDef.Puzzle != null`, `Puzzles.Open` |

`GameRules.ItemActionLabel(r)` (or `hover.ActionLabel`) is the action sentence. With a selected item
it is non-empty only for an executable rule. A wrong pair keeps `hover.Name` and gets an empty
action line. Only `GameMode.World` and `GameMode.Inventory` accept interactions. Every other mode
resolves to `None`, so the click that closes a dialogue cannot fall through to the scene.

Other input helpers:

- `GameRules.ToggleHotspots` (Space; world mode only; persists across rooms) and
  `GameRules.HotspotList` (the label list).
- `GameRules.Escape`: cancels the selection first, otherwise closes the top panel, otherwise opens
  pause.
- `GameRules.OpenOverlay(state, Map|Journal|Pause)` and `GameRules.CloseOverlay`.
- `GameRules.AvailableActions` is for the dev debug panel only.

## 4. Committing (atomic transaction)

```csharp
state = GameRules.CommitAction(content, state, action.Id);            // throws ActionRejectedException
var result = GameRules.TryCommitAction(content, state, action.Id);   // Success / State / Rejection
```

One call validates guards, room, visibility, the puzzle answer and the item transaction. It then
applies everything in a single step:

- removes consumed items and adds given items
- appends the id to `done` and writes the journal entry
- returns the postgame evidence on F17
- recomputes side rewards and clears a consumed selection
- applies `special_transitions` (G11 to S11, F17 to S06, J02, J03, J04) and queues the lines

The lines, then the cutscene, then the first-entry lines of a newly reached room play **after**
the commit. Skipping them never changes rules state. A repeated click or a reload can never give
an item twice. Autosave right after a successful commit, or after arriving in a room, and never
during a walk.

## 5. Lines and cutscenes (playback)

After a commit, `state.Mode` is `Dialogue` or `Cutscene` and `state.ActiveLineId` is set.

```csharp
PlaybackLine? line = Playback.Current(content, state);  // LineId, SpeakerId, Speaker, Text, Source, BeatIndex, IsCutscene
state = Playback.Advance(content, state);       // next line; back to World when done
state = Playback.SkipCutscene(content, state);  // skip the rest of the current cutscene
state = Playback.SkipAll(state);
```

The cursor (`ActiveLineId` and `PlaybackQueue`) is saved, so a load in the middle of a dialogue
continues on the exact `line_id`. Use `Postgame.ReplayCutscene` for the scene list. Replays never
re-run a transaction.

## 6. Dialogue topics

`Resolution.Dialogue.Topics` (also `Dialogue.TopicsFor`) lists the valid story `topic` actions on
that NPC, then the ambient topics whose `requires_done` are met. The `TopicOption` fields:

- `IsStoryAction`: commit it with `GameRules.CommitAction(content, state, option.Id)`.
- Otherwise it is an ambient topic: call `Dialogue.StartTopic(content, state, option.Id)`. It plays
  the lines, records the topic as heard and changes no progress.

`Dialogue.CloseMenu` returns to the world. `Dialogue.Transcript(content, state, characterId)` and
`Dialogue.MetCharacters` feed the People tab. Item actions on NPCs are never topics. The player
uses the item on the NPC.

## 7. Puzzles (P01–P05)

```csharp
state = Puzzles.Open(content, state, actionId);           // Mode = Puzzle, draft from `initial`
JsonNode? draft = Puzzles.Draft(content, state, puzzleId);
state = Puzzles.UpdateDraft(content, state, puzzleId, newDraft);   // keep drafts while editing
state = Puzzles.Reset(content, state, puzzleId);
var r = Puzzles.Submit(content, state, actionId, answer); // r.Solved, r.State, r.Feedback (wrong/success line)
state = Puzzles.Close(state);                             // draft kept, never "solved"
bool fill = Puzzles.CanFill(content, state, puzzleId);    // hint level 3 + hint_can_fill
state = Puzzles.Fill(content, state, puzzleId);           // player still confirms with Submit
```

Answer shapes are built by `PuzzleAnswers`: `Matching("kruh", "trojuholník", "štvorec")` (one
value per left slot), `Rotation(180)`, `Digits(3, 2, 6)` and `Grid(row: 2, column: 3)`. A wrong
answer only stores the draft. Nothing is consumed and the modal stays open. Use
`content.GetPuzzle(id).Controls` to build the modal, and `TextKeys.TitleOf`, `ClueOf` and
`ConfirmOf` for its texts.

## 8. Quests, hints, journal

- `Quests.NextMainQuest` (the TS port), `Quests.CurrentMainQuest` (the pin wins),
  `Quests.ActiveSideQuest`, `Quests.StatusOf`, `Quests.Pin` / `Unpin` (one main and one side
  quest), `Quests.LatestObjective`.
- `Hints.RevealNext(content, state, questId)` reveals one level per player request, up to 3.
  `Hints.Revealed` returns the texts.
- `Journal.Build(content, state)` returns a `JournalView` with:
  - quests (main and side, with status and pins), the current main goal and the active side quest
  - `Findings`: first looks and action transcripts with objectives, in recorded order
  - `Clues`: readable puzzle clues
  - `People`: transcripts of everyone met
  - `TimeMap`: unlocked eras and visited rooms
  - `Album`: completed side quests with their epilogue shot
  - `ReplayableCutscenes`

## 9. Map, travel, portals

- `ViewBuilder.Map(content, state)` returns the era sheets. Each room has `Visited` (unvisited
  rooms are grey), `IsCurrent`, `IsAnchor` and `CanFastTravel`.
- `Navigation.FastTravel(content, state, roomId)` works only in map mode, only to a visited room of
  the same era, and only if that room is reachable over open connections. A locked door is never
  bypassed.
- `Navigation.PortalTargets(content, state)` and `Navigation.UsePortal(content, state, year)`
  handle the chronometer at anchor nodes. Travel is free and always reversible.
- `Navigation.UnlockedEras` and `Navigation.IsEraUnlocked` report era state.
- `Navigation.ConnectedRooms` and `Navigation.FindRoute` (exits and portals) are for hints and
  debugging.
- `Navigation.Travel` handles exits. A first visit queues the room's `first_entry` lines.
- `Navigation.BeginNewGame` queues the start room's `first_entry` lines on a new game (the initial
  state already lists the start room as visited; ISSUES.md GAME-01).
- Show `TextKeys.CardOf(era)` and `DateOf(era)` on the era title card. For reduced motion, use a
  fade with the year name.

## 10. World changes

- `WorldEffects.CausalEffectsAt(content, state, room)`
- `WorldEffects.VariantLayers(content, state, room)`
- `WorldEffects.Butterflies` and `IsTriggered("BF_TREE" | "BF_JANA")`
- `TemporalCache.StatusOf(content, state)` returns the cache stage (NotCreated, Created, Sealed,
  Stored, Retrieved, Opened, Used), the carried lineage item and the niche reservation.
  `TemporalCache.InvariantHolds` checks that only one physical object exists.
- `Epilogue.Select(content, state)` returns the credits shots in Q1–Q9 order (5–7 s each).
  `Epilogue.GoesStraightToCredits` is true when no episode is complete.
- `Postgame.IsActive` and `Postgame.ReplayableCutscenes` report the postgame.

## 11. Save / load

```csharp
string json = SaveCodec.Serialize(state);                 // schema_version 1 + sha256 checksum
if (!SaveCodec.TryLoad(content, json, out var loaded, out TextRef error, out string? reason)) { show(error); }
GameState s = GameRules.ValidateSave(content, jsonNode);  // TS-compatible validateSave
```

A load rejects any of the following, and the current game is never touched (`error` is
`ui.save.corrupt`, "Chybný súbor uloženia. Aktuálna hra zostala otvorená."):

- unknown or duplicate ids, unknown fields or schema versions
- a room or era mismatch, or an era that is not unlocked
- a selection that is not owned, or an invalid mode, line or puzzle draft
- a checksum mismatch
- a `done` list whose replay does not produce exactly the saved inventory and side rewards (no
  silent fill-in, no duplicated items)

The UI helper fields (labels toggle, playback cursor, hint levels, pins, room entry marker) are
saved too. Use `user://` paths on the Godot side.

## 12. GameSession (optional)

`GameSession` holds `Content` and the current `State`. It forwards `Resolve`, `Hover`, `Room`,
`Apply(resolution, combineMode)`, `Commit`, `SubmitPuzzle`, `Update(Func<GameState, GameState>)`,
`Save` and `TryLoad`, and raises `StateChanged(old, new)`. It adds no rules.

## Tests

Run `dotnet test src/LastBell.sln`. The suite covers:

- unit tests per rule and control rule
- a replay of `walkthrough.json` with inventory checks after each of the 94 steps
- all side quests after the credits
- 120 seeded random legal orders and 24 final-port orders
- a save/load round-trip at every step and in the middle of each dialogue
- the logic-level rows of `acceptance_tests.csv` (UI-only rows are skipped with a reason)
