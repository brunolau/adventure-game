using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace LastBell.Core.Content;

// Data records mirroring game.json one to one. Property names map to snake_case JSON keys
// through the loader's naming policy. The records are immutable; collections are exposed as
// read-only lists. Ids from game.json are kept verbatim (including spaces, e.g. "S01.ambient 1").

/// <summary>A spoken or displayed line with a stable line id.</summary>
public sealed record LineDef
{
    /// <summary>Speaker id (a character id or a key of <c>non_actor_speakers</c>).</summary>
    public string Speaker { get; init; } = "";
    /// <summary>Slovak fallback text.</summary>
    public string Text { get; init; } = "";
    /// <summary>Stable line id; also the localization key.</summary>
    public string? LineId { get; init; }
}

/// <summary>A conditional look text of a hotspot (evaluated from the last entry to the first).</summary>
public sealed record LookVariantDef
{
    /// <summary>Action id that activates this variant.</summary>
    public string After { get; init; } = "";
    /// <summary>Slovak fallback text.</summary>
    public string Text { get; init; } = "";
    /// <summary>Stable line id of the variant text.</summary>
    public string? LineId { get; init; }
}

/// <summary>An interactive or atmospheric object or an NPC placed in a room.</summary>
public sealed record HotspotDef
{
    /// <summary>Globally unique hotspot id, e.g. <c>S01.tools</c>.</summary>
    public string Id { get; init; } = "";
    /// <summary>Slovak display name.</summary>
    public string Name { get; init; } = "";
    /// <summary><c>npc</c> or <c>prop</c>.</summary>
    public string Kind { get; init; } = "prop";
    /// <summary>Character id for NPC hotspots.</summary>
    public string? CharacterId { get; init; }
    /// <summary>Base look text (fallback when no variant applies).</summary>
    public string Look { get; init; } = "";
    /// <summary>Line id of the base look text.</summary>
    public string? LookLineId { get; init; }
    /// <summary>Hit rectangle [x, y, width, height] in the 1920x1080 logical canvas.</summary>
    public IReadOnlyList<int> Rect { get; init; } = Array.Empty<int>();
    /// <summary>Walk target [x, y] for interacting with the hotspot.</summary>
    public IReadOnlyList<int> InteractionPoint { get; init; } = Array.Empty<int>();
    /// <summary>Anchor [x, y] of the Space label.</summary>
    public IReadOnlyList<int> LabelAnchor { get; init; } = Array.Empty<int>();
    /// <summary>All of these actions must be done for the hotspot to be visible.</summary>
    public IReadOnlyList<string> VisibleAfter { get; init; } = Array.Empty<string>();
    /// <summary>The hotspot hides as soon as any of these actions is done.</summary>
    public IReadOnlyList<string> HideAfter { get; init; } = Array.Empty<string>();
    /// <summary>Conditional look texts.</summary>
    public IReadOnlyList<LookVariantDef> LookVariants { get; init; } = Array.Empty<LookVariantDef>();

    /// <summary>True for NPC hotspots.</summary>
    [JsonIgnore] public bool IsNpc => Kind == "npc";
}

/// <summary>A directional exit zone of a room (one side of a connection).</summary>
public sealed record ExitDef
{
    /// <summary>Exit id, e.g. <c>S01.to_S02</c>.</summary>
    public string Id { get; init; } = "";
    /// <summary>Destination room id.</summary>
    public string To { get; init; } = "";
    /// <summary>Slovak label.</summary>
    public string Label { get; init; } = "";
    /// <summary>All of these actions must be done to pass.</summary>
    public IReadOnlyList<string> RequiresDone { get; init; } = Array.Empty<string>();
    /// <summary>Travel presentation kind (walk, map_transition, car_transition, cable_A6, board_funitel, arrive_funitel).</summary>
    public string Travel { get; init; } = "walk";
    /// <summary>Look text while the exit is locked.</summary>
    public string LockedLook { get; init; } = "";
    /// <summary>Hit rectangle [x, y, width, height].</summary>
    public IReadOnlyList<int> Rect { get; init; } = Array.Empty<int>();
    /// <summary>Walk target [x, y].</summary>
    public IReadOnlyList<int> InteractionPoint { get; init; } = Array.Empty<int>();
}

/// <summary>A navigable scene.</summary>
public sealed record RoomDef
{
    /// <summary>Room id (S01..S68).</summary>
    public string Id { get; init; } = "";
    /// <summary>Slovak room name.</summary>
    public string Name { get; init; } = "";
    /// <summary>Era (year) of the room.</summary>
    public int Era { get; init; }
    /// <summary>District (data only).</summary>
    public string District { get; init; } = "";
    /// <summary>Art brief (production data, not displayed).</summary>
    public string ArtBrief { get; init; } = "";
    /// <summary>Ambience brief (production data).</summary>
    public string Ambience { get; init; } = "";
    /// <summary>Lines played on the first visit only.</summary>
    public IReadOnlyList<LineDef> FirstEntry { get; init; } = Array.Empty<LineDef>();
    /// <summary>Hotspots in data order.</summary>
    public IReadOnlyList<HotspotDef> Hotspots { get; init; } = Array.Empty<HotspotDef>();
    /// <summary>Characters present in the room.</summary>
    public IReadOnlyList<string> NpcIds { get; init; } = Array.Empty<string>();
    /// <summary>Background asset path relative to the assets root.</summary>
    public string BackgroundAsset { get; init; } = "";
    /// <summary>Music asset path.</summary>
    public string Music { get; init; } = "";
    /// <summary>Walkable polygon as a list of [x, y] points.</summary>
    public IReadOnlyList<IReadOnlyList<int>> WalkPolygon { get; init; } = Array.Empty<IReadOnlyList<int>>();
    /// <summary>Default spawn point [x, y].</summary>
    public IReadOnlyList<int> Spawn { get; init; } = Array.Empty<int>();
    /// <summary>Camera family id (rooms sharing anchors across eras).</summary>
    public string CameraFamily { get; init; } = "";
    /// <summary>Exits in data order.</summary>
    public IReadOnlyList<ExitDef> Exits { get; init; } = Array.Empty<ExitDef>();
    /// <summary>Render layer order (back to front).</summary>
    public IReadOnlyList<string> LayerOrder { get; init; } = Array.Empty<string>();
    /// <summary>Blocking note (production data).</summary>
    public string BlockingNote { get; init; } = "";
}

/// <summary>An optional, condition-gated conversation topic of a character (no state change).</summary>
public sealed record TopicDef
{
    /// <summary>Topic id, e.g. <c>ELA.ambient 1</c>.</summary>
    public string Id { get; init; } = "";
    /// <summary>Slovak label of the topic choice.</summary>
    public string Label { get; init; } = "";
    /// <summary>All of these actions must be done for the topic to be offered.</summary>
    public IReadOnlyList<string> RequiresDone { get; init; } = Array.Empty<string>();
    /// <summary>Lines of the topic.</summary>
    public IReadOnlyList<LineDef> Lines { get; init; } = Array.Empty<LineDef>();
    /// <summary>Repeatable topics stay in the list after being heard.</summary>
    public bool Repeatable { get; init; } = true;
}

/// <summary>A character (actor) definition.</summary>
public sealed record CharacterDef
{
    /// <summary>Character id.</summary>
    public string Id { get; init; } = "";
    /// <summary>Slovak display name.</summary>
    public string Name { get; init; } = "";
    /// <summary>Age as given in data (number or text).</summary>
    public JsonNode? Age { get; init; }
    /// <summary>Role description (production data).</summary>
    public string Role { get; init; } = "";
    /// <summary>Voice direction (production data).</summary>
    public string Voice { get; init; } = "";
    /// <summary>Visual design brief (production data).</summary>
    public string Design { get; init; } = "";
    /// <summary>Rooms where the character appears.</summary>
    public IReadOnlyList<string> Rooms { get; init; } = Array.Empty<string>();
    /// <summary>Optional atmospheric topics.</summary>
    public IReadOnlyList<TopicDef> AmbientTopics { get; init; } = Array.Empty<TopicDef>();
    /// <summary>Greeting on the first meeting (null in the current data).</summary>
    public JsonNode? GreetingFirst { get; init; }
    /// <summary>Greeting on repeated meetings (null in the current data).</summary>
    public JsonNode? GreetingRepeat { get; init; }
}

/// <summary>An inventory item.</summary>
public sealed record ItemDef
{
    /// <summary>Item id.</summary>
    public string Id { get; init; } = "";
    /// <summary>Slovak name.</summary>
    public string Name { get; init; } = "";
    /// <summary>Slovak look text.</summary>
    public string Look { get; init; } = "";
    /// <summary>Action id that gives the item, or <c>initial</c>.</summary>
    public string Origin { get; init; } = "";
    /// <summary>Slovak purpose text.</summary>
    public string Purpose { get; init; } = "";
    /// <summary>Disposition (all items are <c>retain</c>).</summary>
    public string Disposition { get; init; } = "";
    /// <summary>Icon asset path.</summary>
    public string Icon { get; init; } = "";
    /// <summary>Line id of the look text.</summary>
    public string? LookLineId { get; init; }
}

/// <summary>Staging hints for an action (presentation only).</summary>
public sealed record StagingDef
{
    /// <summary>Characters briefly brought into the scene.</summary>
    public IReadOnlyList<string> GuestSpeakers { get; init; } = Array.Empty<string>();
    /// <summary>Staging rule text (production data).</summary>
    public string Rule { get; init; } = "";
}

/// <summary>A one-time story action: the only thing that changes progression state.</summary>
public sealed record ActionDef
{
    /// <summary>Action id.</summary>
    public string Id { get; init; } = "";
    /// <summary>Room id where the action happens, or <c>inventory</c> for combinations.</summary>
    public string Room { get; init; } = "";
    /// <summary>Hotspot id (click/topic) or item id (combine).</summary>
    public string Target { get; init; } = "";
    /// <summary>Slovak action label.</summary>
    public string Label { get; init; } = "";
    /// <summary><c>click</c>, <c>topic</c> or <c>combine</c>.</summary>
    public string Kind { get; init; } = "click";
    /// <summary>AND-combined prerequisite actions.</summary>
    public IReadOnlyList<string> RequiresDone { get; init; } = Array.Empty<string>();
    /// <summary>Items that must be owned.</summary>
    public IReadOnlyList<string> RequiresItems { get; init; } = Array.Empty<string>();
    /// <summary>Item that must be selected on the cursor, or null.</summary>
    public string? SelectedItem { get; init; }
    /// <summary>Items added by the action.</summary>
    public IReadOnlyList<string> Gives { get; init; } = Array.Empty<string>();
    /// <summary>Items removed by the action.</summary>
    public IReadOnlyList<string> Consumes { get; init; } = Array.Empty<string>();
    /// <summary>Lines played after the commit.</summary>
    public IReadOnlyList<LineDef> Lines { get; init; } = Array.Empty<LineDef>();
    /// <summary><c>main</c> for main-story actions, otherwise the side quest id (Q1..Q9).</summary>
    public string Quest { get; init; } = "main";

    /// <summary>True for main-story actions.</summary>
    [JsonIgnore] public bool IsMain => Quest == "main";
    /// <summary>Puzzle id that must be solved before the commit, or null.</summary>
    public string? Puzzle { get; init; }
    /// <summary>Cutscene id played after the lines, or null.</summary>
    public string? Cutscene { get; init; }
    /// <summary>Always true: every action happens at most once.</summary>
    public bool Once { get; init; } = true;
    /// <summary>Objective sentence recorded in the journal, or null.</summary>
    public string? Objective { get; init; }
    /// <summary>Hero animation id.</summary>
    public string Animation { get; init; } = "";
    /// <summary>Sound effect id.</summary>
    public string Sfx { get; init; } = "";
    /// <summary>The action is impossible once any of these actions is done.</summary>
    public IReadOnlyList<string> ExcludedDone { get; init; } = Array.Empty<string>();
    /// <summary>Commit policy (always <c>atomic_after_validation_and_puzzle_before_lines</c>).</summary>
    public string CommitPolicy { get; init; } = "";
    /// <summary>Combine recipes: the selection order does not matter.</summary>
    public bool Symmetric { get; init; }
    /// <summary>Journal transcript text.</summary>
    public string JournalText { get; init; } = "";
    /// <summary>Staging hints.</summary>
    public StagingDef? Staging { get; init; }

    /// <summary>True for <c>kind == click</c>.</summary>
    [JsonIgnore] public bool IsClick => Kind == "click";
    /// <summary>True for <c>kind == topic</c>.</summary>
    [JsonIgnore] public bool IsTopic => Kind == "topic";
    /// <summary>True for <c>kind == combine</c>.</summary>
    [JsonIgnore] public bool IsCombine => Kind == "combine";
    /// <summary>True for inventory combinations (<c>room == inventory</c>).</summary>
    [JsonIgnore] public bool IsInventoryAction => Room == GameContent.InventoryRoom;
}

/// <summary>Control description of a puzzle modal.</summary>
public sealed record PuzzleControlsDef
{
    /// <summary><c>matching</c>, <c>rotate_overlay</c>, <c>digits</c> or <c>grid_choice</c>.</summary>
    public string Type { get; init; } = "";
    /// <summary>Matching: left column (the slots).</summary>
    public IReadOnlyList<string>? Left { get; init; }
    /// <summary>Matching: right column (the choices).</summary>
    public IReadOnlyList<string>? Right { get; init; }
    /// <summary>Rotate overlay: discrete orientations in degrees.</summary>
    public IReadOnlyList<int>? Orientations { get; init; }
    /// <summary>Confirm button label.</summary>
    public string? ConfirmLabel { get; init; }
    /// <summary>Digits: number of digits.</summary>
    public int? Digits { get; init; }
    /// <summary>Digits: inclusive range [min, max].</summary>
    public IReadOnlyList<int>? Range { get; init; }
    /// <summary>Grid choice: row count.</summary>
    public int? Rows { get; init; }
    /// <summary>Grid choice: column count.</summary>
    public int? Columns { get; init; }
    /// <summary>Grid choice: row numbering origin.</summary>
    public string? RowOrigin { get; init; }
    /// <summary>Grid choice: column numbering origin.</summary>
    public string? ColumnOrigin { get; init; }
}

/// <summary>A modal puzzle (P01..P05).</summary>
public sealed record PuzzleDef
{
    /// <summary>Puzzle id.</summary>
    public string Id { get; init; } = "";
    /// <summary>Slovak title.</summary>
    public string Title { get; init; } = "";
    /// <summary>Controls of the modal.</summary>
    public PuzzleControlsDef Controls { get; init; } = new();
    /// <summary>Initial draft value.</summary>
    public JsonNode? Initial { get; init; }
    /// <summary>The single correct answer (compared by deep equality).</summary>
    public JsonNode? Solution { get; init; }
    /// <summary>Readable clue (also stored in the journal).</summary>
    public string Clue { get; init; } = "";
    /// <summary>Line shown on a wrong confirm ("SPEAKER: text").</summary>
    public string WrongLine { get; init; } = "";
    /// <summary>Line shown on success ("SPEAKER: text").</summary>
    public string SuccessLine { get; init; } = "";
    /// <summary>No timer (always true).</summary>
    public bool NoTimer { get; init; } = true;
    /// <summary>The draft can be reset to <see cref="Initial"/>.</summary>
    public bool ResetAllowed { get; init; } = true;
    /// <summary>The third hint level may fill in the solution.</summary>
    public bool HintCanFill { get; init; }
}

/// <summary>A quest (main playbook group or side quest).</summary>
public sealed record QuestDef
{
    /// <summary>Quest id (M01.., Q1..).</summary>
    public string Id { get; init; } = "";
    /// <summary>Slovak title.</summary>
    public string Title { get; init; } = "";
    /// <summary><c>main</c> or <c>side</c>.</summary>
    public string Type { get; init; } = "main";
    /// <summary>Actions of the quest in canonical order.</summary>
    public IReadOnlyList<string> Actions { get; init; } = Array.Empty<string>();
    /// <summary>Slovak goal text.</summary>
    public string Goal { get; init; } = "";
    /// <summary>Action that completes the quest.</summary>
    public string Completion { get; init; } = "";
    /// <summary>Three hint levels: direction, concrete steps, exact solution.</summary>
    public IReadOnlyList<string> Hints { get; init; } = Array.Empty<string>();

    /// <summary>True for main quests.</summary>
    [JsonIgnore] public bool IsMain => Type == "main";
    /// <summary>True for side quests.</summary>
    [JsonIgnore] public bool IsSide => Type == "side";
}

/// <summary>One beat (shot) of a cutscene.</summary>
public sealed record CutsceneBeatDef
{
    /// <summary>Shot direction (production data, not a displayed caption).</summary>
    public string Shot { get; init; } = "";
    /// <summary>Lines of the beat.</summary>
    public IReadOnlyList<LineDef> Lines { get; init; } = Array.Empty<LineDef>();
    /// <summary>Minimum duration in seconds.</summary>
    public double DurationMinS { get; init; }
}

/// <summary>A cutscene. Cutscenes never carry hidden rule effects.</summary>
public sealed record CutsceneDef
{
    /// <summary>Cutscene id.</summary>
    public string Id { get; init; } = "";
    /// <summary>All cutscenes are skippable.</summary>
    public bool Skippable { get; init; } = true;
    /// <summary>Beats in order.</summary>
    public IReadOnlyList<CutsceneBeatDef> Beats { get; init; } = Array.Empty<CutsceneBeatDef>();
}

/// <summary>A graph edge between two rooms (all are bidirectional in the data).</summary>
public sealed record ConnectionDef
{
    /// <summary>Source room.</summary>
    public string From { get; init; } = "";
    /// <summary>Target room.</summary>
    public string To { get; init; } = "";
    /// <summary>AND-combined gate.</summary>
    public IReadOnlyList<string> RequiresDone { get; init; } = Array.Empty<string>();
    /// <summary>Whether the edge also goes from <see cref="To"/> to <see cref="From"/>.</summary>
    public bool Bidirectional { get; init; }
    /// <summary>Travel presentation kind.</summary>
    public string Travel { get; init; } = "walk";
    /// <summary>Slovak label.</summary>
    public string Label { get; init; } = "";
    /// <summary>Slovak locked look text.</summary>
    public string LockedLook { get; init; } = "";
}

/// <summary>A time window (era).</summary>
public sealed record EraDef
{
    /// <summary>Year (1960, 1982, 1995, 2020, 2035).</summary>
    public int Year { get; init; }
    /// <summary>ISO date of the in-game day.</summary>
    public string Date { get; init; } = "";
    /// <summary>Primary arrival room for portal travel.</summary>
    public string Anchor { get; init; } = "";
    /// <summary>Action that unlocks the era, or null for the start era.</summary>
    public string? UnlockedBy { get; init; }
}

/// <summary>An automatic room change committed as part of an action transaction.</summary>
public sealed record SpecialTransitionDef
{
    /// <summary>Triggering action.</summary>
    public string After { get; init; } = "";
    /// <summary>Destination room.</summary>
    public string To { get; init; } = "";
    /// <summary>Always true.</summary>
    public bool Auto { get; init; } = true;
}

/// <summary>Postgame rules.</summary>
public sealed record PostgameDef
{
    /// <summary>Action that ends the main story and unlocks the postgame (F17).</summary>
    public string Unlock { get; init; } = "";
    /// <summary>Evidence items returned to the bag in the same transaction.</summary>
    public IReadOnlyList<string> ReturnItems { get; init; } = Array.Empty<string>();
    /// <summary>Reason text (data).</summary>
    public string Reason { get; init; } = "";
    /// <summary>Era visit rule text (data).</summary>
    public string EraVisits { get; init; } = "";
    /// <summary>Final replay rule text (data).</summary>
    public string RepeatFinal { get; init; } = "";
}

/// <summary>A visible, exactly listed consequence of an action in later scenes.</summary>
public sealed record CausalEffectDef
{
    /// <summary>Triggering action.</summary>
    public string After { get; init; } = "";
    /// <summary>Affected rooms.</summary>
    public IReadOnlyList<string> At { get; init; } = Array.Empty<string>();
    /// <summary>Description of the change (production data).</summary>
    public string Change { get; init; } = "";
    /// <summary>Reason (production data).</summary>
    public string Reason { get; init; } = "";
}

/// <summary>An epilogue shot shown in the credits for a completed side quest.</summary>
public sealed record EpilogueDef
{
    /// <summary>Side quest id.</summary>
    public string Quest { get; init; } = "";
    /// <summary>Action that enables the shot.</summary>
    public string After { get; init; } = "";
    /// <summary>Slovak shot caption.</summary>
    public string Shot { get; init; } = "";
    /// <summary>Slovak line ("SPEAKER: text").</summary>
    public string Line { get; init; } = "";
}

/// <summary>A room from which the chronometer can open a portal.</summary>
public sealed record AnchorNodeDef
{
    /// <summary>Portal source room.</summary>
    public string Room { get; init; } = "";
    /// <summary>Year of the source room.</summary>
    public int Year { get; init; }
    /// <summary>AND-combined gate.</summary>
    public IReadOnlyList<string> RequiresDone { get; init; } = Array.Empty<string>();
}

/// <summary>The same physical place in several eras (shared camera and anchors).</summary>
public sealed record LocationFamilyDef
{
    /// <summary>Family id (L_STOP, ...).</summary>
    public string Id { get; init; } = "";
    /// <summary>Slovak place name.</summary>
    public string Place { get; init; } = "";
    /// <summary>Year (as string) to room id.</summary>
    public IReadOnlyDictionary<string, string> Versions { get; init; } = new Dictionary<string, string>();
    /// <summary>Fixed architectural anchors (production data).</summary>
    public IReadOnlyList<string> FixedAnchors { get; init; } = Array.Empty<string>();
    /// <summary>Per-year descriptions keyed by year (production data).</summary>
    [JsonExtensionData] public Dictionary<string, System.Text.Json.JsonElement>? EraDescriptions { get; init; }
}

/// <summary>Lifecycle of the item stored in 1982 and retrieved in 2020.</summary>
public sealed record CacheContractDef
{
    /// <summary>Cache id.</summary>
    public string Id { get; init; } = "";
    /// <summary>All item ids that are stages of the single physical object, in order.</summary>
    public IReadOnlyList<string> PhysicalItemLineage { get; init; } = Array.Empty<string>();
    /// <summary>Action that creates the object.</summary>
    public string CreatedBy { get; init; } = "";
    /// <summary>Action that seals it.</summary>
    public string SealedBy { get; init; } = "";
    /// <summary>Action that stores it in the niche (1982).</summary>
    public string StoredBy { get; init; } = "";
    /// <summary>Actions that preserve the niche until 2020.</summary>
    public IReadOnlyList<string> PreservedBy { get; init; } = Array.Empty<string>();
    /// <summary>Action that retrieves it (2020).</summary>
    public string RetrievedBy { get; init; } = "";
    /// <summary>Action that opens it.</summary>
    public string OpenedBy { get; init; } = "";
    /// <summary>Action that finally uses it.</summary>
    public string UsedBy { get; init; } = "";
    /// <summary>Location description (data).</summary>
    public string Location { get; init; } = "";
    /// <summary>Aging rule (data).</summary>
    public string Aging { get; init; } = "";
    /// <summary>Uniqueness rule (data).</summary>
    public string Uniqueness { get; init; } = "";
    /// <summary>No-softlock rule (data).</summary>
    public string NoSoftlock { get; init; } = "";
    /// <summary>Clue description (data).</summary>
    public string Clue { get; init; } = "";
}

/// <summary>One of the two fixed butterfly effects (BF_TREE, BF_JANA).</summary>
public sealed record ButterflyEffectDef
{
    /// <summary>Effect id.</summary>
    public string Id { get; init; } = "";
    /// <summary>Triggering action.</summary>
    public string Trigger { get; init; } = "";
    /// <summary>Scale description (data).</summary>
    public string Scale { get; init; } = "";
    /// <summary>State before the trigger (data).</summary>
    public string Before { get; init; } = "";
    /// <summary>Causal chain (data).</summary>
    public IReadOnlyList<string> Chain { get; init; } = Array.Empty<string>();
    /// <summary>Rooms where the effect is visible.</summary>
    public IReadOnlyList<string> VisibleRooms { get; init; } = Array.Empty<string>();
    /// <summary>Human payoff (data).</summary>
    public string HumanPayoff { get; init; } = "";
    /// <summary>Limits (data).</summary>
    public string Limits { get; init; } = "";
}

/// <summary>A background overlay drawn in a room once an action is done.</summary>
public sealed record VisualVariantLayerDef
{
    /// <summary>Room id.</summary>
    public string Room { get; init; } = "";
    /// <summary>Triggering action.</summary>
    public string After { get; init; } = "";
    /// <summary>Asset path.</summary>
    public string Asset { get; init; } = "";
    /// <summary>Description (production data).</summary>
    public string Change { get; init; } = "";
}

/// <summary>Travel rules as written in the handoff (data, implemented by <c>Navigation</c>).</summary>
public sealed record TravelContractDef
{
    /// <summary>Era unlock rule.</summary>
    public string EraUnlock { get; init; } = "";
    /// <summary>Portal use rule.</summary>
    public string PortalUse { get; init; } = "";
    /// <summary>Same era return rule.</summary>
    public string SameEraReturn { get; init; } = "";
    /// <summary>First cable ride rule.</summary>
    public string FirstCableRides { get; init; } = "";
    /// <summary>Fast travel rule.</summary>
    public string FastTravel { get; init; } = "";
    /// <summary>Reduced motion rule.</summary>
    public string ReducedMotion { get; init; } = "";
}

/// <summary>Journal rules as written in the handoff (data, implemented by <c>Journal</c>).</summary>
public sealed record JournalContractDef
{
    /// <summary>Automatic entry rule.</summary>
    public string AutoEntries { get; init; } = "";
    /// <summary>Short clue summaries per puzzle ("P01: ...").</summary>
    public IReadOnlyList<string> Clues { get; init; } = Array.Empty<string>();
    /// <summary>Journal tab names (Slovak).</summary>
    public IReadOnlyList<string> Tabs { get; init; } = Array.Empty<string>();
    /// <summary>Pinning rule.</summary>
    public string Pinning { get; init; } = "";
}

/// <summary>The root of game.json. Sections that are purely editorial (bible, sources) are kept raw.</summary>
public sealed record GameData
{
    /// <summary>Content version.</summary>
    public string Version { get; init; } = "";
    /// <summary>Content language (sk-SK).</summary>
    public string Language { get; init; } = "";
    /// <summary>Slovak title.</summary>
    public string Title { get; init; } = "";
    /// <summary>All rooms.</summary>
    public IReadOnlyList<RoomDef> Rooms { get; init; } = Array.Empty<RoomDef>();
    /// <summary>All characters.</summary>
    public IReadOnlyList<CharacterDef> Characters { get; init; } = Array.Empty<CharacterDef>();
    /// <summary>All items.</summary>
    public IReadOnlyList<ItemDef> Items { get; init; } = Array.Empty<ItemDef>();
    /// <summary>All actions.</summary>
    public IReadOnlyList<ActionDef> Actions { get; init; } = Array.Empty<ActionDef>();
    /// <summary>All puzzles.</summary>
    public IReadOnlyList<PuzzleDef> Puzzles { get; init; } = Array.Empty<PuzzleDef>();
    /// <summary>All quests (main groups first, then side quests).</summary>
    public IReadOnlyList<QuestDef> Quests { get; init; } = Array.Empty<QuestDef>();
    /// <summary>All cutscenes.</summary>
    public IReadOnlyList<CutsceneDef> Cutscenes { get; init; } = Array.Empty<CutsceneDef>();
    /// <summary>Room graph.</summary>
    public IReadOnlyList<ConnectionDef> Connections { get; init; } = Array.Empty<ConnectionDef>();
    /// <summary>Speakers that are not actors (id to Slovak name).</summary>
    public IReadOnlyDictionary<string, string> NonActorSpeakers { get; init; } = new Dictionary<string, string>();
    /// <summary>Initial state (same schema as a save).</summary>
    public JsonObject? InitialState { get; init; }
    /// <summary>Eras.</summary>
    public IReadOnlyList<EraDef> Eras { get; init; } = Array.Empty<EraDef>();
    /// <summary>Automatic transitions.</summary>
    public IReadOnlyList<SpecialTransitionDef> SpecialTransitions { get; init; } = Array.Empty<SpecialTransitionDef>();
    /// <summary>Postgame rules.</summary>
    public PostgameDef Postgame { get; init; } = new();
    /// <summary>Causal effects.</summary>
    public IReadOnlyList<CausalEffectDef> CausalEffects { get; init; } = Array.Empty<CausalEffectDef>();
    /// <summary>Epilogue shots in Q1..Q9 order.</summary>
    public IReadOnlyList<EpilogueDef> Epilogue { get; init; } = Array.Empty<EpilogueDef>();
    /// <summary>Epilogue rule text (data).</summary>
    public string EpilogueRules { get; init; } = "";
    /// <summary>Portal anchors.</summary>
    public IReadOnlyList<AnchorNodeDef> AnchorNodes { get; init; } = Array.Empty<AnchorNodeDef>();
    /// <summary>Location families.</summary>
    public IReadOnlyList<LocationFamilyDef> LocationFamilies { get; init; } = Array.Empty<LocationFamilyDef>();
    /// <summary>Temporal cache contract.</summary>
    public CacheContractDef CacheContract { get; init; } = new();
    /// <summary>Butterfly effects.</summary>
    public IReadOnlyList<ButterflyEffectDef> ButterflyEffects { get; init; } = Array.Empty<ButterflyEffectDef>();
    /// <summary>Landmark layouts: family id to anchor name to [x, y].</summary>
    public IReadOnlyDictionary<string, IReadOnlyDictionary<string, IReadOnlyList<int>>> LandmarkLayouts { get; init; } =
        new Dictionary<string, IReadOnlyDictionary<string, IReadOnlyList<int>>>();
    /// <summary>Visual variant layers.</summary>
    public IReadOnlyList<VisualVariantLayerDef> VisualVariantLayers { get; init; } = Array.Empty<VisualVariantLayerDef>();
    /// <summary>Travel contract (data).</summary>
    public TravelContractDef TravelContract { get; init; } = new();
    /// <summary>Journal contract (data).</summary>
    public JournalContractDef JournalContract { get; init; } = new();
    /// <summary>Content statistics.</summary>
    public IReadOnlyDictionary<string, int> Stats { get; init; } = new Dictionary<string, int>();
}
