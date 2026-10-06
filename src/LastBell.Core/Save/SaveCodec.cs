using System.Collections.Immutable;
using System.Security.Cryptography;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Nodes;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Text;

namespace LastBell.Core.Save;

/// <summary>
/// Thrown when a save cannot be imported. The open game is never mutated; show <see cref="Text"/>
/// ("Chybný súbor uloženia. Aktuálna hra zostala otvorená.") and log <see cref="Reason"/>.
/// </summary>
public sealed class SaveValidationException : Exception
{
    /// <summary>Creates the exception with a technical reason.</summary>
    public SaveValidationException(string reason) : base(UiText.SaveCorrupt.Fallback + " (" + reason + ")")
    {
        Reason = reason;
    }

    /// <summary>Technical reason (English, for logs and the dev panel).</summary>
    public string Reason { get; }

    /// <summary>Player-facing message.</summary>
    public TextRef Text => UiText.SaveCorrupt;
}

/// <summary>
/// Save/load of <see cref="GameState"/> as JSON with <c>schema_version</c> and a SHA-256 checksum.
/// Loading validates format and every reference before anything is returned, replays the done list
/// to prove the inventory is exactly what the story produced (no silent fill-in, no duplicates) and
/// rejects unknown fields and schema versions (migrations must be explicit).
/// </summary>
public static class SaveCodec
{
    private static readonly string[] KnownFields =
    {
        "schema_version", "room", "era", "inventory", "done", "visited", "selected_item", "mode", "puzzle_drafts",
        "journal_seen", "side_rewards", "hotspot_labels", "active_line_id", "playback_queue", "room_entry_done_count",
        "hint_levels", "pinned_main_quest", "pinned_side_quest", "open_puzzle", "checksum",
    };

    private static readonly JsonSerializerOptions WriteOptions = new() { Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping };
    private static readonly JsonSerializerOptions WriteIndentedOptions = new() { Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping, WriteIndented = true };

    /// <summary>JSON name of a mode (<c>world</c>, <c>inventory</c>, ...).</summary>
    public static string ModeName(GameMode mode) => mode.ToString().ToLowerInvariant();

    /// <summary>Parses a mode name; null when unknown.</summary>
    public static GameMode? ParseMode(string? name) => name switch
    {
        "world" => GameMode.World,
        "inventory" => GameMode.Inventory,
        "dialogue" => GameMode.Dialogue,
        "puzzle" => GameMode.Puzzle,
        "cutscene" => GameMode.Cutscene,
        "map" => GameMode.Map,
        "journal" => GameMode.Journal,
        "pause" => GameMode.Pause,
        _ => null,
    };

    /// <summary>Serializes a state to save JSON (with checksum).</summary>
    public static string Serialize(GameState state, bool indented = false)
    {
        var obj = ToJsonPayload(state);
        obj["checksum"] = Checksum(state);
        return obj.ToJsonString(indented ? WriteIndentedOptions : WriteOptions);
    }

    /// <summary>SHA-256 (lowercase hex) of the canonical payload of a state.</summary>
    public static string Checksum(GameState state)
    {
        var payload = ToJsonPayload(state).ToJsonString(WriteOptions);
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(payload))).ToLowerInvariant();
    }

    /// <summary>Loads and validates save JSON text. Throws <see cref="SaveValidationException"/>.</summary>
    public static GameState Load(GameContent content, string json)
    {
        JsonNode? node;
        try
        {
            node = JsonNode.Parse(json);
        }
        catch (JsonException ex)
        {
            throw new SaveValidationException("invalid JSON: " + ex.Message);
        }
        return ValidateSave(content, node);
    }

    /// <summary>Non-throwing <see cref="Load"/>; on failure <paramref name="error"/> holds the player-facing message.</summary>
    public static bool TryLoad(GameContent content, string json, out GameState? state, out TextRef error, out string? reason)
    {
        try
        {
            state = Load(content, json);
            error = TextRef.Empty;
            reason = null;
            return true;
        }
        catch (SaveValidationException ex)
        {
            state = null;
            error = ex.Text;
            reason = ex.Reason;
            return false;
        }
    }

    /// <summary>
    /// <c>validateSave</c>: rejects anything that is not an exact, consistent state of this content
    /// and returns a fresh copy. Checksums are verified when present.
    /// </summary>
    public static GameState ValidateSave(GameContent content, JsonNode? raw)
    {
        if (raw is not JsonObject obj) throw new SaveValidationException("root is not an object");
        return FromJson(content, obj, verifyChecksum: true);
    }

    /// <summary>Builds and validates a state from a JSON object (also used for <c>initial_state</c>).</summary>
    public static GameState FromJson(GameContent content, JsonObject obj, bool verifyChecksum)
    {
        foreach (var (key, _) in obj)
            if (!KnownFields.Contains(key)) throw new SaveValidationException($"unknown field '{key}'");

        var schema = Int(obj, "schema_version") ?? throw new SaveValidationException("missing schema_version");
        if (schema != GameState.CurrentSchemaVersion) throw new SaveValidationException($"unsupported schema_version {schema}");

        var room = Str(obj, "room") ?? throw new SaveValidationException("missing room");
        var era = Int(obj, "era") ?? throw new SaveValidationException("missing era");
        var roomDef = content.FindRoom(room);
        if (roomDef is null || roomDef.Era != era) throw new SaveValidationException($"room '{room}' does not exist in era {era}");

        var inventory = Ids(obj, "inventory", required: true);
        var done = Ids(obj, "done", required: true);
        var visited = Ids(obj, "visited", required: true);
        var journal = Ids(obj, "journal_seen", required: true);
        var rewards = Ids(obj, "side_rewards", required: true);
        var queue = Ids(obj, "playback_queue", required: false);

        foreach (var i in inventory) if (content.FindItem(i) is null) throw new SaveValidationException($"unknown item '{i}'");
        foreach (var a in done) if (content.FindAction(a) is null) throw new SaveValidationException($"unknown action '{a}'");
        foreach (var r in visited) if (content.FindRoom(r) is null) throw new SaveValidationException($"unknown room '{r}'");
        foreach (var q in rewards) if (content.FindQuest(q) is not { IsSide: true }) throw new SaveValidationException($"unknown side quest '{q}'");
        foreach (var l in queue) if (content.FindLine(l) is null) throw new SaveValidationException($"unknown line '{l}'");

        if (!obj.ContainsKey("selected_item")) throw new SaveValidationException("missing selected_item");
        var selected = obj["selected_item"] is null ? null : Str(obj, "selected_item") ?? throw new SaveValidationException("selected_item is not a string");
        if (selected is not null && !inventory.Contains(selected)) throw new SaveValidationException($"selected item '{selected}' is not owned");

        var mode = ParseMode(Str(obj, "mode")) ?? throw new SaveValidationException("unknown mode");

        if (obj["puzzle_drafts"] is not JsonObject draftsObj) throw new SaveValidationException("puzzle_drafts is not an object");
        var drafts = ImmutableSortedDictionary.CreateBuilder<string, string>(StringComparer.Ordinal);
        foreach (var (puzzleId, value) in draftsObj)
        {
            if (content.FindPuzzle(puzzleId) is null) throw new SaveValidationException($"unknown puzzle draft '{puzzleId}'");
            drafts[puzzleId] = JsonDeep.ToCanonicalText(value);
        }

        var activeLine = obj["active_line_id"] is null ? null : Str(obj, "active_line_id") ?? throw new SaveValidationException("active_line_id is not a string");
        if (activeLine is not null && content.FindLine(activeLine) is null) throw new SaveValidationException($"unknown line '{activeLine}'");
        if (activeLine is null && !queue.IsEmpty) throw new SaveValidationException("playback_queue without active line");
        if (activeLine is not null && mode is not (GameMode.Dialogue or GameMode.Cutscene)) throw new SaveValidationException("active line outside dialogue/cutscene mode");

        var entryCount = obj.ContainsKey("room_entry_done_count") ? Int(obj, "room_entry_done_count") ?? throw new SaveValidationException("room_entry_done_count is not a number") : done.Length;
        if (entryCount < 0 || entryCount > done.Length) throw new SaveValidationException("room_entry_done_count out of range");

        var hints = ImmutableSortedDictionary.CreateBuilder<string, int>(StringComparer.Ordinal);
        if (obj["hint_levels"] is JsonObject hintObj)
        {
            // Keys are step action ids (hints per step, PT-F08); quest ids from older saves stay valid and are ignored.
            foreach (var (key, value) in hintObj)
            {
                int max;
                if (content.FindAction(key) is { } step && content.FindQuestOf(step.Id) is not null) max = Hints.Levels;
                else if (content.FindQuest(key) is { } quest) max = quest.Hints.Count;
                else throw new SaveValidationException($"unknown quest or step '{key}' in hint_levels");
                var level = value is JsonValue v && v.TryGetValue<int>(out var n) ? n : -1;
                if (level < 0 || level > max) throw new SaveValidationException($"hint level out of range for '{key}'");
                hints[key] = level;
            }
        }
        else if (obj.ContainsKey("hint_levels") && obj["hint_levels"] is not null) throw new SaveValidationException("hint_levels is not an object");

        // open_puzzle (optional, GAME-02): the puzzle action whose modal was open; only in puzzle mode.
        string? openPuzzle = null;
        if (obj["open_puzzle"] is not null)
        {
            openPuzzle = Str(obj, "open_puzzle") ?? throw new SaveValidationException("open_puzzle is not a string");
            if (content.FindAction(openPuzzle)?.Puzzle is null) throw new SaveValidationException($"open_puzzle '{openPuzzle}' is not a puzzle action");
            if (mode != GameMode.Puzzle) throw new SaveValidationException("open_puzzle outside puzzle mode");
        }

        var pinnedMain = OptionalQuest(content, obj, "pinned_main_quest", main: true);
        var pinnedSide = OptionalQuest(content, obj, "pinned_side_quest", main: false);
        var labels = obj["hotspot_labels"] switch
        {
            null => false,
            JsonValue b when b.GetValueKind() is JsonValueKind.True or JsonValueKind.False => b.GetValue<bool>(),
            _ => throw new SaveValidationException("hotspot_labels is not a boolean"),
        };

        if (!Navigation.IsEraUnlocked(content, new GameState { Done = done }, era)) throw new SaveValidationException($"era {era} is not unlocked");
        VerifyStory(content, done, inventory, rewards);

        var state = new GameState
        {
            SchemaVersion = schema,
            Room = room,
            Era = era,
            Inventory = inventory,
            Done = done,
            Visited = visited,
            SelectedItem = selected,
            Mode = mode,
            PuzzleDrafts = drafts.ToImmutable(),
            JournalSeen = journal,
            SideRewards = rewards,
            HotspotLabels = labels,
            ActiveLineId = activeLine,
            PlaybackQueue = queue,
            RoomEntryDoneCount = entryCount,
            HintLevels = hints.ToImmutable(),
            PinnedMainQuest = pinnedMain,
            PinnedSideQuest = pinnedSide,
            OpenPuzzleAction = openPuzzle,
        };

        if (verifyChecksum && obj["checksum"] is not null)
        {
            var given = Str(obj, "checksum") ?? throw new SaveValidationException("checksum is not a string");
            if (!string.Equals(given, Checksum(state), StringComparison.OrdinalIgnoreCase)) throw new SaveValidationException("checksum mismatch");
        }
        return state;
    }

    /// <summary>The JSON payload of a state without checksum, fields in a fixed order.</summary>
    public static JsonObject ToJsonPayload(GameState s)
    {
        var drafts = new JsonObject();
        foreach (var (k, v) in s.PuzzleDrafts) drafts[k] = JsonNode.Parse(v);
        var hints = new JsonObject();
        foreach (var (k, v) in s.HintLevels) hints[k] = v;
        var payload = new JsonObject
        {
            ["schema_version"] = s.SchemaVersion,
            ["room"] = s.Room,
            ["era"] = s.Era,
            ["inventory"] = IdArray(s.Inventory),
            ["done"] = IdArray(s.Done),
            ["visited"] = IdArray(s.Visited),
            ["selected_item"] = s.SelectedItem,
            ["mode"] = ModeName(s.Mode),
            ["puzzle_drafts"] = drafts,
            ["journal_seen"] = IdArray(s.JournalSeen),
            ["side_rewards"] = IdArray(s.SideRewards),
            ["hotspot_labels"] = s.HotspotLabels,
            ["active_line_id"] = s.ActiveLineId,
            ["playback_queue"] = IdArray(s.PlaybackQueue),
            ["room_entry_done_count"] = s.RoomEntryDoneCount,
            ["hint_levels"] = hints,
            ["pinned_main_quest"] = s.PinnedMainQuest,
            ["pinned_side_quest"] = s.PinnedSideQuest,
        };
        // Written only while a puzzle modal is open, so saves without it keep their payload and checksum.
        if (s.Mode == GameMode.Puzzle && s.OpenPuzzleAction is not null) payload["open_puzzle"] = s.OpenPuzzleAction;
        return payload;
    }

    /// <summary>
    /// Replays the done list in order from the initial inventory: every action's prerequisites must be
    /// earlier, nothing excluding it may be earlier, consumed and required items must be owned and given
    /// items must not be owned. The resulting inventory and side rewards must equal the saved ones.
    /// </summary>
    private static void VerifyStory(GameContent content, ImmutableArray<string> done, ImmutableArray<string> inventory, ImmutableArray<string> rewards)
    {
        var initial = content.Data.InitialState?["inventory"] as JsonArray;
        var owned = new HashSet<string>(initial?.Select(n => n?.GetValue<string>() ?? "") ?? Enumerable.Empty<string>(), StringComparer.Ordinal);
        var past = new HashSet<string>(StringComparer.Ordinal);
        foreach (var id in done)
        {
            var a = content.GetAction(id);
            if (!a.RequiresDone.All(past.Contains)) throw new SaveValidationException($"action '{id}' is done before its prerequisites");
            if (a.ExcludedDone.Any(past.Contains)) throw new SaveValidationException($"action '{id}' is excluded by an earlier action");
            if (!a.RequiresItems.All(owned.Contains) || !a.Consumes.All(owned.Contains)) throw new SaveValidationException($"action '{id}' lacks its items");
            if (a.Gives.Any(owned.Contains)) throw new SaveValidationException($"action '{id}' would duplicate an item");
            foreach (var c in a.Consumes) owned.Remove(c);
            foreach (var g in a.Gives) owned.Add(g);
            past.Add(id);
            if (id == content.Data.Postgame.Unlock) foreach (var r in content.Data.Postgame.ReturnItems) owned.Add(r);
        }
        if (!owned.SetEquals(inventory)) throw new SaveValidationException("inventory does not match the story (missing or extra items)");
        var expectedRewards = content.Quests.Where(q => q.IsSide && past.Contains(q.Completion)).Select(q => q.Id);
        if (!new HashSet<string>(expectedRewards, StringComparer.Ordinal).SetEquals(rewards)) throw new SaveValidationException("side_rewards do not match the story");
    }

    private static JsonArray IdArray(ImmutableArray<string> ids) => new(ids.Select(id => (JsonNode?)JsonValue.Create(id)).ToArray());

    private static string? Str(JsonObject obj, string key) =>
        obj[key] is JsonValue v && v.GetValueKind() == JsonValueKind.String ? v.GetValue<string>() : null;

    private static int? Int(JsonObject obj, string key) =>
        obj[key] is JsonValue v && v.GetValueKind() == JsonValueKind.Number && v.TryGetValue<int>(out var n) ? n
        : obj[key] is JsonValue d && d.GetValueKind() == JsonValueKind.Number && int.TryParse(d.ToJsonString(), out var m) ? m
        : null;

    private static ImmutableArray<string> Ids(JsonObject obj, string key, bool required)
    {
        if (!obj.ContainsKey(key))
        {
            if (required) throw new SaveValidationException($"missing {key}");
            return ImmutableArray<string>.Empty;
        }
        if (obj[key] is not JsonArray array) throw new SaveValidationException($"{key} is not an array");
        var builder = ImmutableArray.CreateBuilder<string>(array.Count);
        var seen = new HashSet<string>(StringComparer.Ordinal);
        foreach (var node in array)
        {
            if (node is not JsonValue v || v.GetValueKind() != JsonValueKind.String) throw new SaveValidationException($"{key} contains a non-string");
            var id = v.GetValue<string>();
            if (!seen.Add(id)) throw new SaveValidationException($"{key} contains duplicate '{id}'");
            builder.Add(id);
        }
        return builder.MoveToImmutable();
    }

    private static string? OptionalQuest(GameContent content, JsonObject obj, string key, bool main)
    {
        if (obj[key] is null) return null;
        var id = Str(obj, key) ?? throw new SaveValidationException($"{key} is not a string");
        var quest = content.FindQuest(id);
        if (quest is null || quest.IsMain != main) throw new SaveValidationException($"{key} '{id}' is not a {(main ? "main" : "side")} quest");
        return id;
    }
}
