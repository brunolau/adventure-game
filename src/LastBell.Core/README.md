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

With the content overlays use `GameContent.Load(json, new ContentOverlays(dialogueExt, travelExt))`
(section 13; `GameRuntime` loads `res://data/content_ext/`).

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
- recomputes side rewards and clears the selection after an item use (also a consumed one; an invalid
  item click never reaches the commit and keeps the selection, PT-F09 / PT-S16)
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
- Hints follow the step (PT-F08 / PT-S26): `Hints.CurrentStep(content, state, questId)` is the next undone
  action of the quest (the open puzzle's action first, else the first undone action in quest order whose guards
  pass, else the first undone one). `Hints.RevealNext(content, state, questId)` reveals one level of that step
  per player request, up to `Hints.Levels` (3); levels are kept per step (`hint_levels` keyed by action id;
  quest-id keys of older saves still load and are ignored), so a new step starts at 0. `Hints.Revealed` returns
  `HintText`s: level 1 the direction (the objective of the done action that enabled the step, else the quest's
  latest objective, else quest hint 1 / 2), level 2 the place (`ui.hint.step_place` with `{room}` / `{target}`,
  or `ui.hint.step_bag`), level 3 only that step (`ui.hint_step.<action id>`, never the whole chain).
  `Puzzles.CanFill` needs level 3 of the puzzle's own step.
- `Dialogue.ReturnToMenu(content, state, npcHotspotId)`: after a topic's lines the topic menu of the same NPC
  opens again while it still offers a topic (conversations stay open, PT-S17).
- `Journal.Build(content, state)` returns a `JournalView` with:
  - quests (main and side, with status and pins), the current main goal and the active side quest
  - `Findings`: first looks and action transcripts with objectives, in recorded order
  - `Clues`: readable puzzle clues
  - `People`: transcripts of everyone met
  - `TimeMap`: unlocked eras and visited rooms
  - `Album`: completed side quests with their epilogue shot
  - `ReplayableCutscenes`

## 9. Map, travel, portals

- `ViewBuilder.Map(content, state)` returns the era sheets with their map regions (section 13). Each
  room has `Visited` (unvisited rooms are grey), `IsCurrent`, `IsAnchor`, `CanFastTravel`, `RegionId`
  and `IsHub`.
- `Navigation.FastTravel(content, state, roomId)` works only in map mode, only to a visited room of
  the same era, only if that room is reachable over open connections, and only inside the current
  region or to a hub of another region (travel overlay). A locked door is never bypassed.
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
`ui.save.corrupted`, "Chybný súbor uloženia. Aktuálna hra zostala otvorená."):

- unknown or duplicate ids, unknown fields or schema versions
- a room or era mismatch, or an era that is not unlocked
- a selection that is not owned, or an invalid mode, line or puzzle draft
- a checksum mismatch
- a `done` list whose replay does not produce exactly the saved inventory and side rewards (no
  silent fill-in, no duplicated items)

The UI helper fields (labels toggle, playback cursor, hint levels, pins, room entry marker) are
saved too. Use `user://` paths on the Godot side.

While a puzzle modal is open the save also carries the optional field `open_puzzle` (the puzzle
action id, `GameState.OpenPuzzleAction`; written only in puzzle mode, so other saves keep their payload
and checksum). After a load call `GameRules.ResumeAfterLoad(content, state)`: pause, map and journal
close to the scene, and puzzle mode stays open only when `Puzzles.OpenAction` is still a valid puzzle
action (reopen that modal), otherwise it closes with the draft kept (ISSUES GAME-02, UI-05).

## 12. GameSession (optional)

`GameSession` holds `Content` and the current `State`. It forwards `Resolve`, `Hover`, `Room`,
`Apply(resolution, combineMode)`, `Commit`, `SubmitPuzzle`, `Update(Func<GameState, GameState>)`,
`Save` and `TryLoad`, and raises `StateChanged(old, new)`. It adds no rules.

## 13. Content overlays (`src/game/data/content_ext/`)

game.json is never edited. Two optional overlays are applied on top of it when content loads:

```csharp
var overlays = new ContentOverlays(
    FileAccess.GetFileAsString("res://data/content_ext/dialogue_ext.json"),   // or null
    FileAccess.GetFileAsString("res://data/content_ext/travel_ext.json"));    // or null
GameContent content = GameContent.Load(gameJson, overlays);
```

`GameRuntime` does this (a missing file means no overlay of that kind). `GameContent.Load(json)` alone is
the handoff. An empty overlay (`{}`, or empty lists) is valid and changes nothing; to revert, remove an
entry or the whole file. Load validates everything and throws `ContentLoadException`; overlay errors name
the overlay path, e.g. `$dialogue_ext.sequences[3](G02).lines[2].speaker: 'TONO20' does not take part in
action 'G02'`. After load, `content.Data` is the effective content (game.json + overlays) and
`content.Overlay` (`OverlayInfo`) lists what changed. The Python mirror is `tools/content_ext.py`
(`check`, `merge`); the localization tools build their tables from the effective game.

### dialogue_ext.json: longer sequences and extra NPC topics

Only lines, labels of new topics and their timing conditions may be set. Any other field (gives, consumes,
requires_items, puzzle, quest, cutscene, logic) is an error. The writing drafts
(`docs/writing/out*/<chunk>_ext.json`, WRITING_METHOD.md section 5) have this shape and are merged as is
with `python tools/content_ext.py merge docs/writing/out_v2/C1_ext.json` (each entry gets a `chunk`
field; a draft's `travel` proposal is not merged).

```jsonc
{
  "format": "lastbell.dialogue_ext", "version": 1,          // optional; "about", "schema", "chunk", "note", "sources" are free text
  "sequences": [                                             // also "topic_extensions": same entry shape
    { "action": "G02",                                       // exactly one of: "action" (action lines), "topic" (an ambient
                                                             //   topic of game.json), "room" (that room's first_entry lines)
      "id": "action.G02", "kind": "action_lines",            // optional checks: id = action.<id> | topic.<id> | entry.<room>,
                                                             //   kind = action_lines | topic_lines | first_entry_lines
      "lines": [                                             // the FULL play order
        "action.G02.001",                                    //   a string: an existing line of THIS exchange (kept, may be
                                                             //   reordered; one that is not listed is dropped)
        { "key": "action.G02.x01", "speaker": "ELA", "sk": "…" }   // an object: a new line at this position
      ] }
  ],
  "topics": [                                                // new optional topics (only play lines, like ambient topics)
    { "id": "ELA.extra 1",                                   // "ext.<anything>" or "<CHARACTER>.extra <n>" (draft form)
      "character": "ELA", "label": "Dobrovoľníci",          // label key: topic.<id>.label ("label_key" optional check)
      "repeatable": true,                                    // default true; false: offered until heard once
      "requires_done": [], "excluded_done": [],              // existing action ids only: offered when all requires are
                                                             //   done and no excluded action is done
      "speaks_first": "ADAM",                                // optional check of the first line's speaker
      "lines": [ { "key": "topic.ELA.extra 1.001", "speaker": "ADAM", "sk": "…" } ] }
  ]
}
```

Rules checked on load:

- New line keys are `<owner>.<n>` with `<owner>` = `action.<id>`, `topic.<topicId>` or `entry.<roomId>`
  and `<n>` up to three letters plus digits (`x01`, `001`); they are new (no game.json or other overlay
  line uses them) and stable: the key is the localization key (`Tr(key)`, Slovak fallback = `sk`).
- Speakers: Adam, the speakers already in that exchange, and for conversations with a character (its
  topics and the actions on its NPC hotspots) that character and everyone already speaking with it (Bodka
  next to Lenka); for actions also the staging guest speakers. An existing line keeps its speaker and text
  (its text comes from the tables / `sk_overrides.csv`).
- An exchange is extended at most once; `lines` is never empty; a new topic id is unique and its character
  has an NPC hotspot.
- Dropped handoff lines are "retired" (`OverlayInfo.RetiredLines`): never queued again, not in
  `AllLineIds`, but `FindLine` still resolves them, so a save made on such a line loads.
- `tools/check_rewrite.py` checks the texts (lengths, ids, wording) and the protected facts: a fact may move
  within its action / topic but must stay present; a verbatim line may not be dropped.

`Dialogue.TopicsFor` lists new topics after the character's handoff topics (same `TopicOption`, not a
story action); `Dialogue.StartTopic` plays them and records `topic.<id>` in `journal_seen`.
`TopicDef.ExcludedDone` is set only by the overlay.

### travel_ext.json: exits, connections, first rides, map regions

```jsonc
{
  "format": "lastbell.travel_ext", "version": 1,
  "remove_exits": [ { "exit": "S02.to_S51", "reason": "…" } ],            // or plain exit ids
  "remove_connections": [ { "from": "S02", "to": "S51", "reason": "…" } ],// in its game.json direction
  "exits": [
    { "room": "S07", "id": "S07.to_S51", "to": "S51", "travel": "bus",   // id = <room>.to_<to>; same era
      "label": "…", "locked_look": "…", "requires_done": [],              // keys exit.<id>.label / .locked
      "rect": [960, 975, 55, 70], "interaction_point": [985, 965],          // template geometry (natural blocking:
                                                                            //   data/blocking/<room>.json)
      "first_ride": { "lines": [ { "key": "travel.S07.to_S51.first.001", "speaker": "ADAM", "sk": "…" } ] } }
  ],
  "connections": [ { "from": "S07", "to": "S51", "bidirectional": true, "travel": "bus",
                     "label": "…", "locked_look": "…", "requires_done": [] } ],   // keys conn.<from>.<to>.label / .locked
  "regions": [ { "id": "Chorvátsky Grob", "era": 2020, "rooms": ["S01", "…"], "hubs": ["S07"] } ]
}
```

Rules checked on load: known rooms, exits and actions; travel styles `walk`, `map_transition`,
`car_transition`, `bus`, `tram`, `cable_A6`, `board_funitel`, `arrive_funitel`; an added connection has
an exit on each side (same travel and requires_done), an added exit has a connection, a removed
connection leaves no exit behind and a removed exit no connection; every room stays reachable from its
era's time node; first-ride lines are Adam's, keyed `travel.<exitId>.first.<n>`.

Regions (owner rule 2026-10-06, "far places are reached through their transport hub"): an era that has
regions lists every room in exactly one region; each region has at least one hub; a connection between two
regions must join a hub to a hub. Eras without regions get one region per district with every room a hub
(the handoff behaviour). Region names are `region.<id>.name` in ui.csv (`TextKeys.NameOf(region)`).

- `content.Regions`, `RegionsOf(era)`, `RegionOf(roomId)`, `IsHub(roomId)`.
- `Navigation.CanFastTravel` adds `Navigation.IsRegionTarget`: inside the current region, or to a hub of
  another region. `ViewBuilder.Map` gives each `MapEraView` its `Regions` (`MapRegionView`: name, rooms,
  hubs, current, visited, `CanTravel`, `Transport` = the travel style into it) and each `MapRoomView` its
  `RegionId` and `IsHub`.
- `Navigation.TransportBetween(content, state, from, to)`: the travel style of the first cross-region
  connection on the route (the presentation's transport card for a fast travel).
- `Navigation.Travel` through an exit with first-ride lines that were not heard yet queues them before
  the destination's first-entry lines and records `Navigation.FirstRideKey(exitId)` in `journal_seen`.
  `PlaybackLine.Source` is `LineSource.Travel` (`SourceId` = exit id): the presentation plays them in the
  room being left, then runs the ride (fade, transport card, ride sound) and shows the new room.
- `content.FirstRideLines(exitId)`.

## Tests

Run `dotnet test src/LastBell.sln`. The suite covers:

- unit tests per rule and control rule
- a replay of `walkthrough.json` with inventory checks after each of the 94 steps
- all side quests after the credits
- 120 seeded random legal orders and 24 final-port orders
- a save/load round-trip at every step and in the middle of each dialogue
- the logic-level rows of `acceptance_tests.csv` (UI-only rows are skipped with a reason)
- the content overlays (`ContentOverlayTests`): empty overlays, the live C1 sequences and topics in play order,
  timing conditions, retired lines and old saves, every rejected field and broken key, the travel overlay
  (bus S07 <-> S51, first rides, the hub rule, region fast travel, map regions) and that every overlay text
  has its key in the generated tables

`TestData.Content` is the content the game plays (game.json + `src/game/data/content_ext/*.json`, copied
to the test fixtures); `TestData.BaseContent` is the handoff alone. The walkthrough replay follows
`walkthrough.json` (never edited); a hop that the travel overlay removed (S02 -> S51) is recomputed as the
shortest legal route under the overlay (`Driver.FollowTravelPath`, by bus from S07).
