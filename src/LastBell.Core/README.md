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
  the same era, and only if that room is reachable over open connections; in any map region, one step
  (owner override 2026-10-06, docs/DECISIONS.md control change 8: no stop at the hub). A locked door is
  never bypassed.
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
`ui.save.corrupted`, "Chybný súbor uloženia. Rozohraná hra beží ďalej."):

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

game.json is never edited. Three optional overlays are applied on top of it when content loads, in the order
world, dialogue, travel (so the dialogue overlay can extend world lines and give new characters topics, and the
travel overlay's map regions see the new rooms):

```csharp
var overlays = new ContentOverlays(
    FileAccess.GetFileAsString("res://data/content_ext/dialogue_ext.json"),   // or null
    FileAccess.GetFileAsString("res://data/content_ext/travel_ext.json"),     // or null
    FileAccess.GetFileAsString("res://data/content_ext/world_ext.json"));     // or null
GameContent content = GameContent.Load(gameJson, overlays);
```

`GameRuntime` does this (a missing file means no overlay of that kind; QA runs can read them from another
folder with `-- --content-ext <dir>`). `GameContent.Load(json)` alone is the handoff. An empty overlay (`{}`, or
empty lists) is valid and changes nothing; to revert, remove an entry or the whole file. Load validates
everything and throws `ContentLoadException`; overlay errors name the overlay path, e.g.
`$dialogue_ext.sequences[3](G02).lines[2].speaker: 'TONO20' does not take part in action 'G02'` or
`$world_ext.actions(Q90D): needs 'SAMPLE_NOTE', which 'Q90B' consumes; ...`. After load, `content.Data` is the
effective content (game.json + overlays) and `content.Overlay` (`OverlayInfo`) lists what changed. The Python
mirror is `tools/content_ext.py` (`check`, `merge`, `merge-world`; the world part in `tools/content_world.py`);
the localization and writing tools build their tables from the effective game.

### world_ext.json: new rooms, hotspots, characters, items, actions, side quests; relocations

The world overlay adds content with **new ids only** and may move an existing action to another room of the same
era. Everything it adds has the game.json record shape, so the rules, views, journal, hints, map, saves and the
localization tools treat it like handoff content. Every list is optional; the order of the lists does not matter
(references may point forward). Field names are game.json's; texts are Slovak strings on one line.

```jsonc
{
  "format": "lastbell.world_ext", "version": 1,             // optional; "about", "note", "schema" are free text
  "characters": [ { "id": "ZUZANA95", "name": "Zuzana", "age": 40, "role": "…", "voice": "…", "design": "…" } ],
                                                            // rooms are derived from the NPC hotspots (key char.<id>.name);
                                                            // optional topics go in dialogue_ext.json "topics"
  "items": [ { "id": "BELL_MUTE", "name": "…", "look": "…", "purpose": "…",
               "icon": "items/BELL_MUTE.webp" } ],          // icon default items/<id>.webp; origin is derived (the one
                                                            // action that gives it); disposition always "retain"
                                                            // keys item.<id>.name, item.<id> (look), item.<id>.purpose
  "rooms": [ {
      "id": "S69", "name": "Sokolíkovský dvor", "era": 1995, "district": "Dúbravka",
      "region": "Dúbravka", "hub": false,                   // only when travel_ext.json defines regions for the era:
                                                            // the room joins that region (else: the district's region)
      "background_asset": "bg/S69.webp", "music": "music/1995.ogg",
      "art_brief": "…", "ambience": "…", "blocking_note": "…", // production notes (not shown)
      "walk_polygon": [[90, 790], [1830, 790], [1830, 1015], [90, 1015]], "spawn": [960, 935],
      "camera_family": "S69", "layer_order": [ … ],         // defaults: own id, game.json's 7 layers
      "first_entry": [ { "key": "entry.S69.001", "speaker": "ADAM", "sk": "…" } ],   // Adam and the room's NPCs
      "hotspots": [                                          // ids <room>.<name>; NPC hotspots <room>.<CHARACTER>
        { "id": "S69.ZUZANA95", "name": "Zuzana", "kind": "npc", "character_id": "ZUZANA95", "look": "…",
          "rect": [1600, 670, 120, 265], "interaction_point": [1560, 955] },
        { "id": "S69.rhythm", "name": "…", "look": "…", "rect": [1440, 585, 185, 125], "interaction_point": [1520, 790],
          "label_anchor": [1532, 575],                       // default: 10 px above the rect's centre
          "visible_after": [], "hide_after": [],
          "look_variants": [ { "after": "B19", "sk": "…" } ] }   // keys look.<id>, look.<id>.variant<n>
      ],
      "exits": [ { "id": "S69.to_S18", "to": "S18", "travel": "walk", "label": "…", "locked_look": "…",
                   "requires_done": [], "rect": [1150, 1000, 430, 80], "interaction_point": [1360, 1000] } ]
  } ],                                                       // npc_ids derived (if given they must match)
  "hotspots": [ { "room": "S37", "id": "S37.ZUZANA", "kind": "npc", "character_id": "ZUZANA", … } ],
                                                            // new hotspots in EXISTING rooms (same fields + "room")
  "exits": [ { "room": "S18", "id": "S18.to_S69", "to": "S69", "travel": "walk", "label": "…", "locked_look": "…",
               "rect": [430, 850, 190, 45], "interaction_point": [525, 880] } ],   // exits of existing rooms
  "connections": [ { "from": "S18", "to": "S69", "bidirectional": true, "travel": "walk", "label": "…",
                     "locked_look": "…", "requires_done": [] } ],                  // as in travel_ext.json
  "quests": [ { "id": "Q10", "title": "…", "goal": "…", "reward": "…",
                "hints": ["direction", "place", "the whole chain"],                // exactly three
                "actions": ["Q10A", "Q10B", "Q10C", "Q10D"], "completion": "Q10D" } ],  // side quests only
  "actions": [ { "id": "Q10A", "room": "S37", "target": "S37.ZUZANA", "kind": "topic", "label": "…", "quest": "Q10",
                 "requires_done": [], "excluded_done": [], "requires_items": [], "selected_item": null,
                 "gives": ["BELL_MUTE", "ZUZA_SLIP"], "consumes": [],
                 "objective": "…", "journal_text": "…",
                 "hint_step": "…",                           // required: the exact level-3 hint (action.<id>.hint_step)
                 "animation": "talk", "sfx": "item_soft",    // defaults: talk / show_item / reach_mid / inventory_combine
                 "staging": { "guest_speakers": [], "rule": "" }, "symmetric": false,   // symmetric: combine only
                 "lines": [ { "key": "action.Q10A.001", "speaker": "ZUZANA", "sk": "…" } ] } ],
                                                            // once: true and commit_policy (atomic...) are fixed;
                                                            // puzzle / cutscene must stay null
  "epilogue": [ { "quest": "Q10", "after": "Q10D", "shot": "…", "line": "ZUZANA: …" } ],  // keys epilogue.<n>,
                                                            // n continues after game.json's 9 (picture EPILOGUE_<n>.webp)
  "visual_variant_layers": [ { "room": "S69", "after": "Q11C", "asset": "variants/S69_bike_bell.webp", "change": "…" } ],
  "relocations": [ { "action": "B19", "to_hotspot": "S69.rhythm", "retire_hotspot": false,
                     "hint_step": "V Sokolíkovskom dvore si prečítaj rytmický nákres na múre.", "reason": "…" } ]
}
```

Rules checked on load (every error names its `$world_ext...` path):

- **Ids.** New and unique (also across kinds' lists): rooms `S<nn>`, hotspots `<room>.<name>` (NPCs
  `<room>.<CHARACTER>`), characters / items / actions upper case (`ZUZANA`, `BELL_MUTE`, `Q10A`), quests `Q<n>`.
  A game.json id is refused ("adds new ids only"); to move an existing action use `relocations`. Text keys come
  from the ids (table above), new line keys are `action.<id>.<n>` / `entry.<room>.<n>` like game.json's.
- **References.** Rooms, hotspots, characters, items, actions and quests resolve (game.json's or the overlay's);
  a topic targets an NPC and takes no item; a click on an NPC uses an item; a combination has room `inventory`,
  targets an item and names the other one in `selected_item`; an action's target lies in its room. Speakers:
  Adam, the target character and everyone who speaks for it in game.json (a counter's `SKLAD` speaks as
  `STEFAN`), the NPCs standing in the room and the staging guests.
- **Geometry.** Walk polygon of at least 3 points inside 1920x1080; spawn, every new hotspot's and exit's
  interaction point inside the room's walk polygon; rects at least 44x44 px on screen; asset paths under
  `bg/`, `music/`, `items/`, `variants/`.
- **Graph.** Exits and connections describe the same edges (as in travel_ext.json); every room keeps an exit and
  stays reachable from its era's time node; with map regions in travel_ext.json a new room names its region.
- **Items flow.** A new item has exactly one origin (the action giving it); new actions give and consume new items
  only (game.json items keep their one origin and are never used up by new content, so no main step can lose an
  item); every needed item is obtainable before the action (no cycle through prerequisites or item givers); a new
  item is consumed at most once; an item consumed by one action and needed by another forces an order (the
  consumer requires the other), so no order of play loses it.
- **One logical action per target.** Two actions with the same trigger (the same hotspot without an item, the
  same item on the same hotspot, the same pair of items) must never be possible at once.
- **Quests.** A new side quest consists of exactly its new actions (canonical order), its completion is one of
  them, three hints, at most one epilogue shot; every new action has a `hint_step`.
- **Relocations.** An existing, non-inventory action moves to a hotspot in another room of the **same era**; the
  target keeps its kind (prop stays prop, an NPC stays the same character); nothing else may be set (guards,
  items, quest, puzzle, cutscene and lines stay); `hint_step` is required (the old `ui.hint_step.<id>` names the old
  place). `retire_hotspot: true` removes the old hotspot when no other action targets it (props only).
- **No softlock** (`ContentPlayability`): whenever the world overlay adds or moves anything, the load plays the
  whole game, ending and side quests included, through the real rules in eight orders (data order, side quests
  first, overlay first, overlay last, four seeded random orders; the hero is put into any room reachable over open
  exits and portals). An order that gets stuck is an error: `$playability(data order): softlock after 128 actions
  (...): 3 action(s) can never be done: Q90B (target S90.board is hidden); ...`. `ContentPlayability.Check` also
  runs on the handoff in the tests.
- **Walkthrough and saves.** walkthrough.json stays untouched; the test driver and the in-engine replayer follow
  its travel paths, recompute a hop the hero cannot take because a relocated action put him elsewhere, travel to
  a relocated action's room and expect it as `room_after`. Saves from before the overlay load (no unknown ids)
  and continue there (a relocated step is done in its new room); a save with overlay ids is refused by content
  without the overlay (`ui.save.corrupted`, the current game untouched).

`OverlayInfo` lists `AddedRooms`, `AddedHotspots`, `AddedCharacters`, `AddedItems`, `AddedActions`, `AddedQuests`,
`AddedEpilogue`, `AddedVariantLayers`, `Relocations` (`RelocationInfo`: action, from room / hotspot, to room /
hotspot, retired), `RetiredHotspots` and `HasWorldChanges`; `content.FindRelocation(actionId)`.
`ActionDef.HintStep` holds the step text; `Hints.StepText(action)` returns it (key `action.<id>.hint_step`, world.csv)
or, for game.json's actions, `ui.hint_step.<id>` (ui.csv). `QuestDef.Reward` is game.json's reward text
(`Quests.RewardOf`).

How to add …

- **a room**: an entry in `rooms` with its hotspots and exits, the way back as an exit of the neighbouring room in
  `exits`, the edge in `connections`; `region` when its era has map regions. Art: `bg/<id>.webp` (or
  `data/blocking/<id>.json` + `bg_natural/<id>.webp` for natural blocking), optional `data/ambient/<id>.json`; a
  room without a painting shows the dev blockout. Its texts get keys with `python tools/extract_strings.py`; a new
  district also needs its `region.<district>.name` row in ui.csv.
- **an item**: an entry in `items` and the one action that `gives` it; `items/<id>.webp` for the icon (until it
  exists the bag shows a paper token with the item's initials).
- **an action**: an entry in `actions` with `quest` = a new side quest that lists it; `hint_step`; lines with keys
  `action.<id>.<n>`; the target is a hotspot of that room (new or game.json's), a combination targets an item.
- **a quest**: an entry in `quests` (three hints, its actions, completion), usually an `epilogue` shot
  (`EPILOGUE_<n>.webp`, n = 9 + its position) and the album reward text.
- **a relocation**: an entry in `relocations` (`action`, `to_hotspot` in another room of the same era, `hint_step`,
  optionally `retire_hotspot`); then move protected facts / looks that named the old place with `sk_overrides.csv`.

Then `python tools/content_ext.py check` (fast mirror), `dotnet test src/LastBell.sln` (Core: everything above
plus the playability check and the walkthrough), `python tools/extract_strings.py`, `python tools/check_strings.py`,
`python tools/check_rewrite.py --self-test`, `python tools/check_blocking.py`. A combined writing draft
(`{"world_ext": {...}, "dialogue_ext": {...}}`) goes in with `python tools/content_ext.py merge-world DRAFT` and
then `python tools/content_ext.py merge DRAFT`.

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
  next to Lenka); for actions also the staging guest speakers and the NPCs standing in the action's room (its
  effective room: a relocated action's new room, NPCs added by the world overlay). An existing line keeps its
  speaker and text (its text comes from the tables / `sk_overrides.csv`).
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
- Fast travel ignores the regions (control change 8, it replaced the hub-only rule `IsRegionTarget`): every
  visited, reachable room of the era is one step away; the hubs are where the physical rides enter a region.
  `ViewBuilder.Map` gives each `MapEraView` its `Regions` (`MapRegionView`: name, rooms, hubs, current,
  visited, `CanTravel`, `Transport` = the travel style into it) and each `MapRoomView` its `RegionId` and `IsHub`.
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
  (bus S07 <-> S51, first rides, the hub rule of the links, direct fast travel across regions, map regions) and that every overlay text
  (world overlay texts included) has its key in the generated tables
- the world overlay (`WorldOverlayTests`, sample `Overlays/sample_world_ext.json`, test only: a new 1995 room S90
  with an NPC, three items, the side quest Q90, an epilogue shot, a variant layer, a prop in S12, and the
  relocation of B19 and of the P03 puzzle B22 into S90): every added record and key, the quest through the
  resolver to the album and the ending, hints, the relocated puzzle, the walkthrough with recomputed paths and
  all side quests, 24 random legal orders, the playability check on the handoff, the live content and the
  sample, every 1995 prop action relocatable without a false alarm, dialogue / travel overlays on top (room
  NPCs speaking, a counter's speaker alias, map region hints), old and new saves, and 80 broken overlays

`TestData.Content` is the content the game plays (game.json + `src/game/data/content_ext/*.json`, copied
to the test fixtures); `TestData.BaseContent` is the handoff alone. The walkthrough replay follows
`walkthrough.json` (never edited); a hop that the travel overlay removed (S02 -> S51) is recomputed as the
shortest legal route under the overlay (`Driver.FollowTravelPath`, by bus from S07), and a relocated step travels
on to its new room (`Driver.PrepareStep`, `Driver.ExpectedRoomAfter`); side quests of the world overlay, which
walkthrough.json does not know, are played after its optional route (`Driver.PerformRemaining`).
