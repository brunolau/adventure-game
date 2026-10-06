using System.Collections.Immutable;
using System.Text.Json;
using LastBell.Core.State;

namespace LastBell.Core.Content;

/// <summary>Where a line comes from; decides the playback mode (dialogue or cutscene).</summary>
public enum LineSource
{
    /// <summary>Lines of an action (played after the commit).</summary>
    Action,
    /// <summary>Lines of an ambient topic.</summary>
    Topic,
    /// <summary>First-entry lines of a room.</summary>
    FirstEntry,
    /// <summary>Lines of a cutscene beat.</summary>
    Cutscene,
    /// <summary>First-ride lines of a transport exit (travel overlay), played in the room left, before the ride.</summary>
    Travel,
}

/// <summary>A line together with its owner.</summary>
/// <param name="Line">The line.</param>
/// <param name="Source">Owner kind.</param>
/// <param name="SourceId">Owner id (action, topic, room, cutscene or exit id).</param>
/// <param name="BeatIndex">Cutscene beat index (0-based), or -1.</param>
public sealed record LineInfo(LineDef Line, LineSource Source, string SourceId, int BeatIndex = -1);

/// <summary>A hotspot together with the room it belongs to.</summary>
/// <param name="Room">Owning room.</param>
/// <param name="Hotspot">The hotspot.</param>
public sealed record HotspotRef(RoomDef Room, HotspotDef Hotspot);

/// <summary>Thrown when game.json cannot be loaded; every error names the id and the JSON path.</summary>
public sealed class ContentLoadException : Exception
{
    /// <summary>Creates the exception from a list of errors.</summary>
    public ContentLoadException(IReadOnlyList<string> errors)
        : base("game.json failed to load: " + string.Join("; ", errors.Take(20)) + (errors.Count > 20 ? $" (+{errors.Count - 20} more)" : ""))
    {
        Errors = errors;
    }

    /// <summary>All errors ("$.path: message").</summary>
    public IReadOnlyList<string> Errors { get; }
}

/// <summary>
/// Loaded, validated and indexed game content. Immutable and safe to share between threads.
/// Load it from the text of game.json (Godot passes the contents of a <c>res://</c> file).
/// </summary>
public sealed class GameContent
{
    /// <summary>Pseudo room id of inventory combinations.</summary>
    public const string InventoryRoom = "inventory";

    /// <summary>The chronometer item required for portal travel.</summary>
    public const string ChronometerItem = "CHRONO";

    /// <summary>JSON options used for game.json (snake_case, case-sensitive).</summary>
    public static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        ReadCommentHandling = JsonCommentHandling.Disallow,
        AllowTrailingCommas = false,
    };

    private readonly Dictionary<string, RoomDef> rooms;
    private readonly Dictionary<string, ActionDef> actions;
    private readonly Dictionary<string, ItemDef> items;
    private readonly Dictionary<string, CharacterDef> characters;
    private readonly Dictionary<string, HotspotRef> hotspots;
    private readonly Dictionary<string, PuzzleDef> puzzles;
    private readonly Dictionary<string, CutsceneDef> cutscenes;
    private readonly Dictionary<string, QuestDef> quests;
    private readonly Dictionary<string, QuestDef> questOfAction;
    private readonly Dictionary<int, EraDef> eras;
    private readonly Dictionary<string, LineInfo> lines;
    private readonly Dictionary<string, (CharacterDef Character, TopicDef Topic)> topics;
    private readonly Dictionary<string, SpecialTransitionDef> transitions;
    private readonly Dictionary<string, (RoomDef Room, ExitDef Exit)> exits;
    private readonly Dictionary<string, Text.TextRef> looks;
    private readonly Dictionary<string, LineInfo> retiredLines;
    private readonly Dictionary<string, RegionDef> regionOfRoom;
    private readonly List<RegionDef> regions;

    private GameContent(GameData data, OverlayInfo overlay)
    {
        Data = data;
        Overlay = overlay;
        rooms = data.Rooms.ToDictionary(r => r.Id, StringComparer.Ordinal);
        actions = data.Actions.ToDictionary(a => a.Id, StringComparer.Ordinal);
        items = data.Items.ToDictionary(i => i.Id, StringComparer.Ordinal);
        characters = data.Characters.ToDictionary(c => c.Id, StringComparer.Ordinal);
        hotspots = new Dictionary<string, HotspotRef>(StringComparer.Ordinal);
        exits = new Dictionary<string, (RoomDef, ExitDef)>(StringComparer.Ordinal);
        foreach (var room in data.Rooms)
        {
            foreach (var hotspot in room.Hotspots) hotspots[hotspot.Id] = new HotspotRef(room, hotspot);
            foreach (var exit in room.Exits) exits[exit.Id] = (room, exit);
        }
        puzzles = data.Puzzles.ToDictionary(p => p.Id, StringComparer.Ordinal);
        cutscenes = data.Cutscenes.ToDictionary(c => c.Id, StringComparer.Ordinal);
        quests = data.Quests.ToDictionary(q => q.Id, StringComparer.Ordinal);
        questOfAction = new Dictionary<string, QuestDef>(StringComparer.Ordinal);
        foreach (var quest in data.Quests)
            foreach (var actionId in quest.Actions) questOfAction.TryAdd(actionId, quest);
        eras = data.Eras.ToDictionary(e => e.Year);
        transitions = new Dictionary<string, SpecialTransitionDef>(StringComparer.Ordinal);
        foreach (var t in data.SpecialTransitions) transitions.TryAdd(t.After, t);

        topics = new Dictionary<string, (CharacterDef, TopicDef)>(StringComparer.Ordinal);
        lines = new Dictionary<string, LineInfo>(StringComparer.Ordinal);
        foreach (var action in data.Actions)
            foreach (var line in action.Lines) AddLine(new LineInfo(line, LineSource.Action, action.Id));
        foreach (var character in data.Characters)
        {
            foreach (var topic in character.AmbientTopics)
            {
                topics.TryAdd(topic.Id, (character, topic));
                foreach (var line in topic.Lines) AddLine(new LineInfo(line, LineSource.Topic, topic.Id));
            }
        }
        foreach (var room in data.Rooms)
            foreach (var line in room.FirstEntry) AddLine(new LineInfo(line, LineSource.FirstEntry, room.Id));
        foreach (var cutscene in data.Cutscenes)
            for (var b = 0; b < cutscene.Beats.Count; b++)
                foreach (var line in cutscene.Beats[b].Lines) AddLine(new LineInfo(line, LineSource.Cutscene, cutscene.Id, b));
        foreach (var (exitId, rideLines) in overlay.FirstRides)
            foreach (var line in rideLines) AddLine(new LineInfo(line, LineSource.Travel, exitId));
        retiredLines = new Dictionary<string, LineInfo>(StringComparer.Ordinal);
        foreach (var retired in overlay.RetiredLines)
            if (retired.Line.LineId is { } id && !lines.ContainsKey(id)) retiredLines.TryAdd(id, retired);

        // Map regions: the travel overlay's, else one region per district (every room a hub: the handoff behaviour).
        regions = new List<RegionDef>();
        foreach (var era in data.Eras)
        {
            var defined = overlay.Regions.Where(r => r.Era == era.Year).ToList();
            if (defined.Count > 0) { regions.AddRange(defined); continue; }
            foreach (var group in data.Rooms.Where(r => r.Era == era.Year).GroupBy(r => r.District, StringComparer.Ordinal))
            {
                var ids = group.Select(r => r.Id).ToList();
                regions.Add(new RegionDef(group.Key, era.Year, ids, ids, FromOverlay: false));
            }
        }
        regionOfRoom = new Dictionary<string, RegionDef>(StringComparer.Ordinal);
        foreach (var region in regions)
            foreach (var roomId in region.Rooms) regionOfRoom.TryAdd(roomId, region);

        looks = new Dictionary<string, Text.TextRef>(StringComparer.Ordinal);
        foreach (var room in data.Rooms)
        {
            foreach (var hotspot in room.Hotspots)
            {
                var look = Text.TextKeys.BaseLookOf(hotspot);
                looks.TryAdd(look.Key, look);
                for (var i = 0; i < hotspot.LookVariants.Count; i++)
                {
                    var variant = Text.TextKeys.LookVariantOf(hotspot, i);
                    looks.TryAdd(variant.Key, variant);
                }
            }
        }
        foreach (var item in data.Items)
        {
            var look = Text.TextKeys.LookOf(item);
            looks.TryAdd(look.Key, look);
        }

        void AddLine(LineInfo info)
        {
            if (!string.IsNullOrEmpty(info.Line.LineId)) lines.TryAdd(info.Line.LineId, info);
        }
    }

    /// <summary>Raw content records (game.json with the content overlays applied).</summary>
    public GameData Data { get; }

    /// <summary>What the content overlays changed (<see cref="OverlayInfo.Empty"/> without overlays).</summary>
    public OverlayInfo Overlay { get; }

    /// <summary>The initial state of a new game (from <c>initial_state</c>).</summary>
    public GameState InitialState { get; private set; } = new();

    /// <summary>Rooms in data order.</summary>
    public IReadOnlyList<RoomDef> Rooms => Data.Rooms;

    /// <summary>Actions in data order.</summary>
    public IReadOnlyList<ActionDef> Actions => Data.Actions;

    /// <summary>Items in data order.</summary>
    public IReadOnlyList<ItemDef> Items => Data.Items;

    /// <summary>Quests in data order.</summary>
    public IReadOnlyList<QuestDef> Quests => Data.Quests;

    /// <summary>Eras in data order.</summary>
    public IReadOnlyList<EraDef> Eras => Data.Eras;

    /// <summary>Loads content from the text of game.json without overlays. Throws <see cref="ContentLoadException"/>.</summary>
    public static GameContent Load(string json) => Load(json, null);

    /// <summary>
    /// Loads content from the text of game.json and applies the content overlays (<c>content_ext/world_ext.json</c>,
    /// <c>content_ext/dialogue_ext.json</c>, <c>content_ext/travel_ext.json</c>, in this order; README section 13).
    /// Throws <see cref="ContentLoadException"/> when game.json or an overlay is invalid; overlay errors name the overlay
    /// path (<c>$world_ext...</c>, <c>$dialogue_ext...</c>, <c>$travel_ext...</c>) and a softlock found by
    /// <see cref="ContentPlayability"/> names the order that got stuck (<c>$playability(...)</c>).
    /// </summary>
    public static GameContent Load(string json, ContentOverlays? overlays)
    {
        GameData? data;
        try
        {
            data = JsonSerializer.Deserialize<GameData>(json, JsonOptions);
        }
        catch (JsonException ex)
        {
            throw new ContentLoadException(new[] { $"{ex.Path ?? "$"}: invalid JSON ({ex.Message})" });
        }
        if (data is null) throw new ContentLoadException(new[] { "$: empty document" });

        var errors = ContentValidator.Validate(data);
        if (errors.Count > 0) throw new ContentLoadException(errors);

        var overlay = OverlayInfo.Empty;
        if (overlays is not null && !overlays.IsBlank)
        {
            var overlayErrors = new List<string>();
            var effective = OverlayApplier.Apply(data, overlays, overlayErrors, out overlay);
            if (overlayErrors.Count == 0) overlayErrors.AddRange(ContentValidator.Validate(effective));
            if (overlayErrors.Count > 0) throw new ContentLoadException(overlayErrors);
            data = effective;
        }

        var content = new GameContent(data, overlay);
        if (data.InitialState is null) throw new ContentLoadException(new[] { "$.initial_state: missing" });
        try
        {
            content.InitialState = Save.SaveCodec.FromJson(content, data.InitialState, verifyChecksum: false);
        }
        catch (Save.SaveValidationException ex)
        {
            throw new ContentLoadException(new[] { "$.initial_state: " + ex.Reason });
        }
        // New rooms, items, actions and relocations must leave the game finishable in every order the check tries.
        if (overlay.HasWorldChanges)
        {
            var softlocks = ContentPlayability.Check(content);
            if (softlocks.Count > 0) throw new ContentLoadException(softlocks);
        }
        return content;
    }

    /// <summary>Loads content from a UTF-8 stream containing game.json.</summary>
    public static GameContent Load(Stream utf8Json)
    {
        using var reader = new StreamReader(utf8Json, System.Text.Encoding.UTF8, detectEncodingFromByteOrderMarks: true, leaveOpen: true);
        return Load(reader.ReadToEnd());
    }

    // ---- lookups (Get* throws on unknown id, Find* returns null) ----

    /// <summary>Room by id.</summary>
    public RoomDef GetRoom(string id) => rooms.TryGetValue(id, out var r) ? r : throw new KeyNotFoundException("Unknown room: " + id);
    /// <summary>Room by id, or null.</summary>
    public RoomDef? FindRoom(string id) => rooms.GetValueOrDefault(id);
    /// <summary>Action by id.</summary>
    public ActionDef GetAction(string id) => actions.TryGetValue(id, out var a) ? a : throw new KeyNotFoundException("Unknown action: " + id);
    /// <summary>Action by id, or null.</summary>
    public ActionDef? FindAction(string id) => actions.GetValueOrDefault(id);
    /// <summary>Item by id.</summary>
    public ItemDef GetItem(string id) => items.TryGetValue(id, out var i) ? i : throw new KeyNotFoundException("Unknown item: " + id);
    /// <summary>Item by id, or null.</summary>
    public ItemDef? FindItem(string id) => items.GetValueOrDefault(id);
    /// <summary>Character by id, or null.</summary>
    public CharacterDef? FindCharacter(string id) => characters.GetValueOrDefault(id);
    /// <summary>Hotspot (with room) by id, or null.</summary>
    public HotspotRef? FindHotspot(string id) => hotspots.GetValueOrDefault(id);
    /// <summary>Exit (with room) by id, or null.</summary>
    public (RoomDef Room, ExitDef Exit)? FindExit(string id) => exits.TryGetValue(id, out var e) ? e : null;
    /// <summary>Puzzle by id.</summary>
    public PuzzleDef GetPuzzle(string id) => puzzles.TryGetValue(id, out var p) ? p : throw new KeyNotFoundException("Unknown puzzle: " + id);
    /// <summary>Puzzle by id, or null.</summary>
    public PuzzleDef? FindPuzzle(string id) => puzzles.GetValueOrDefault(id);
    /// <summary>Cutscene by id, or null.</summary>
    public CutsceneDef? FindCutscene(string id) => cutscenes.GetValueOrDefault(id);
    /// <summary>Quest by id, or null.</summary>
    public QuestDef? FindQuest(string id) => quests.GetValueOrDefault(id);
    /// <summary>The quest (playbook group) that owns an action.</summary>
    public QuestDef GetQuestOf(string actionId) => questOfAction.TryGetValue(actionId, out var q) ? q : throw new KeyNotFoundException("Action has no quest: " + actionId);
    /// <summary>The quest that owns an action, or null (unknown action).</summary>
    public QuestDef? FindQuestOf(string actionId) => questOfAction.GetValueOrDefault(actionId);
    /// <summary>Era by year, or null.</summary>
    public EraDef? FindEra(int year) => eras.GetValueOrDefault(year);
    /// <summary>
    /// Line (with owner) by line id, or null. Handoff lines that an overlay sequence dropped still resolve (old saves
    /// that stopped on such a line keep loading) but are never queued again.
    /// </summary>
    public LineInfo? FindLine(string lineId) => lines.GetValueOrDefault(lineId) ?? retiredLines.GetValueOrDefault(lineId);
    /// <summary>Ambient topic (with character) by topic id, or null.</summary>
    public (CharacterDef Character, TopicDef Topic)? FindTopic(string topicId) => topics.TryGetValue(topicId, out var t) ? t : null;
    /// <summary>Special transition triggered by an action, or null.</summary>
    public SpecialTransitionDef? FindTransition(string actionId) => transitions.GetValueOrDefault(actionId);

    /// <summary>Display name of any speaker id (actor or non-actor), keyed as <c>char.&lt;id&gt;.name</c>.</summary>
    public Text.TextRef SpeakerName(string speakerId)
    {
        if (characters.TryGetValue(speakerId, out var c)) return Text.TextKeys.NameOf(c);
        return new Text.TextRef(Text.TextKeys.CharacterName(speakerId), Data.NonActorSpeakers.GetValueOrDefault(speakerId, speakerId));
    }

    /// <summary>Look text (hotspot base look, look variant or item look) by its key, or null.</summary>
    public Text.TextRef? FindLookText(string key) => looks.TryGetValue(key, out var t) ? t : null;

    /// <summary>All line ids the content plays (retired overlay lines excluded).</summary>
    public IEnumerable<string> AllLineIds => lines.Keys;

    /// <summary>The world overlay's relocation of an action (it plays in another room than game.json says), or null.</summary>
    public RelocationInfo? FindRelocation(string actionId) => Overlay.RelocationOf(actionId);

    /// <summary>First-ride lines of a transport exit (travel overlay), or an empty list.</summary>
    public IReadOnlyList<LineDef> FirstRideLines(string exitId) =>
        Overlay.FirstRides.TryGetValue(exitId, out var l) ? l : Array.Empty<LineDef>();

    /// <summary>All map regions, era by era (data order of the eras).</summary>
    public IReadOnlyList<RegionDef> Regions => regions;

    /// <summary>Map regions of one era.</summary>
    public IReadOnlyList<RegionDef> RegionsOf(int era) => regions.Where(r => r.Era == era).ToList();

    /// <summary>The map region of a room.</summary>
    public RegionDef RegionOf(string roomId) =>
        regionOfRoom.TryGetValue(roomId, out var r) ? r : throw new KeyNotFoundException("Unknown room: " + roomId);

    /// <summary>True when the room is a hub of its region (entered from other regions through it).</summary>
    public bool IsHub(string roomId) => regionOfRoom.TryGetValue(roomId, out var r) && r.Hubs.Contains(roomId);
}
