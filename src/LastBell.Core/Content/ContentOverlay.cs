using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;

namespace LastBell.Core.Content;

/// <summary>
/// The texts of the content-extension overlays (<c>src/game/data/content_ext/</c>) handed to
/// <see cref="GameContent.Load(string, ContentOverlays?)"/>. game.json is never edited; the overlays are applied on
/// top of it when content loads. A null, empty or whitespace text means "no overlay of that kind"; an overlay with
/// empty lists is valid too and changes nothing. Schemas: <c>src/LastBell.Core/README.md</c> section 13.
/// </summary>
/// <param name="DialogueExt">Text of <c>dialogue_ext.json</c> (longer sequences, extra NPC topics), or null.</param>
/// <param name="TravelExt">Text of <c>travel_ext.json</c> (exits, connections, map regions), or null.</param>
public sealed record ContentOverlays(string? DialogueExt = null, string? TravelExt = null)
{
    /// <summary>No overlay: the game plays exactly the handoff content.</summary>
    public static ContentOverlays None { get; } = new();

    /// <summary>File name of the dialogue overlay inside the content_ext folder.</summary>
    public const string DialogueExtFile = "dialogue_ext.json";

    /// <summary>File name of the travel overlay inside the content_ext folder.</summary>
    public const string TravelExtFile = "travel_ext.json";
}

/// <summary>
/// A region of the map of one era: rooms that are reached from each other freely (fast travel inside the region),
/// and the hub rooms (bus stop, tram stop, cable car station) through which the region is entered from another one.
/// </summary>
/// <param name="Id">Region id; its name is <c>region.&lt;id&gt;.name</c> (ui.csv). Defaults use the room district.</param>
/// <param name="Era">Year of the era.</param>
/// <param name="Rooms">Rooms of the region (data order).</param>
/// <param name="Hubs">Hub rooms (a subset of <paramref name="Rooms"/>).</param>
/// <param name="FromOverlay">True when <c>travel_ext.json</c> defines it; false for the default one-region-per-district.</param>
public sealed record RegionDef(string Id, int Era, IReadOnlyList<string> Rooms, IReadOnlyList<string> Hubs, bool FromOverlay);

/// <summary>What the overlays changed (for tools, tests and diagnostics). Empty when no overlay was applied.</summary>
public sealed class OverlayInfo
{
    /// <summary>No overlay applied.</summary>
    public static OverlayInfo Empty { get; } = new();

    /// <summary>Actions whose lines the overlay replaced.</summary>
    public IReadOnlyList<string> ExtendedActions { get; init; } = Array.Empty<string>();
    /// <summary>Handoff ambient topics whose lines the overlay replaced.</summary>
    public IReadOnlyList<string> ExtendedTopics { get; init; } = Array.Empty<string>();
    /// <summary>Rooms whose first-entry lines the overlay replaced.</summary>
    public IReadOnlyList<string> ExtendedFirstEntries { get; init; } = Array.Empty<string>();
    /// <summary>New optional topics added by the overlay.</summary>
    public IReadOnlyList<string> AddedTopics { get; init; } = Array.Empty<string>();
    /// <summary>Line ids that only exist in the overlays (new sequence lines, new topic lines, first-ride lines).</summary>
    public IReadOnlyList<string> AddedLineIds { get; init; } = Array.Empty<string>();
    /// <summary>
    /// Handoff lines a sequence dropped. They are no longer played but stay resolvable through
    /// <see cref="GameContent.FindLine"/>, so a save made in the middle of such a line still loads.
    /// </summary>
    public IReadOnlyList<LineInfo> RetiredLines { get; init; } = Array.Empty<LineInfo>();
    /// <summary>Exit ids removed by the travel overlay.</summary>
    public IReadOnlyList<string> RemovedExits { get; init; } = Array.Empty<string>();
    /// <summary>Exit ids added by the travel overlay.</summary>
    public IReadOnlyList<string> AddedExits { get; init; } = Array.Empty<string>();
    /// <summary>Connections removed by the travel overlay (from, to as written in game.json).</summary>
    public IReadOnlyList<(string From, string To)> RemovedConnections { get; init; } = Array.Empty<(string, string)>();
    /// <summary>Connections added by the travel overlay.</summary>
    public IReadOnlyList<(string From, string To)> AddedConnections { get; init; } = Array.Empty<(string, string)>();
    /// <summary>First-ride lines per exit id (played once, the first time the exit is used).</summary>
    public IReadOnlyDictionary<string, IReadOnlyList<LineDef>> FirstRides { get; init; } = new Dictionary<string, IReadOnlyList<LineDef>>();
    /// <summary>Map regions defined by the travel overlay (eras without an entry use one region per district).</summary>
    public IReadOnlyList<RegionDef> Regions { get; init; } = Array.Empty<RegionDef>();

    /// <summary>True when nothing was changed.</summary>
    public bool IsEmpty => ExtendedActions.Count == 0 && ExtendedTopics.Count == 0 && ExtendedFirstEntries.Count == 0 &&
                           AddedTopics.Count == 0 && RemovedExits.Count == 0 && AddedExits.Count == 0 &&
                           RemovedConnections.Count == 0 && AddedConnections.Count == 0 && Regions.Count == 0;
}

/// <summary>
/// Validates and applies the content overlays to the parsed game.json. The dialogue overlay may only set lines,
/// labels of new topics and their timing conditions (<c>requires_done</c> / <c>excluded_done</c> on existing action
/// ids, <c>repeatable</c>); anything else (items, puzzles, quests, logic) is rejected with an error naming the JSON
/// path. The travel overlay may remove and add exits and connections and define map regions; it is checked against
/// the owner rule "far places are reached through their transport hub".
/// </summary>
internal static class OverlayApplier
{
    /// <summary>Travel styles the presentation knows (game.json's plus <c>bus</c> and <c>tram</c>).</summary>
    internal static readonly IReadOnlySet<string> TravelKinds = new HashSet<string>(StringComparer.Ordinal)
    {
        "walk", "map_transition", "car_transition", "bus", "tram", "cable_A6", "board_funitel", "arrive_funitel",
    };

    private const string DialogueFormat = "lastbell.dialogue_ext";
    private const string TravelFormat = "lastbell.travel_ext";
    private static readonly Regex LineSuffix = new(@"^[A-Za-z]{0,3}\d{1,4}$", RegexOptions.CultureInvariant);
    private static readonly Regex DraftTopicId = new(@"^(?<char>[A-Z][A-Z0-9_]*)\.extra \d{1,3}$", RegexOptions.CultureInvariant);

    private static readonly JsonDocumentOptions ParseOptions = new() { AllowTrailingCommas = false, CommentHandling = JsonCommentHandling.Disallow };

    /// <summary>Applies both overlays. Returns the effective data; errors are appended to <paramref name="errors"/>.</summary>
    public static GameData Apply(GameData data, ContentOverlays overlays, List<string> errors, out OverlayInfo info)
    {
        var builder = new InfoBuilder();
        var baseLineIds = AllLineIds(data);
        var newLineIds = new HashSet<string>(StringComparer.Ordinal);
        var result = data;
        var dialogue = Parse(overlays.DialogueExt, "$dialogue_ext", errors);
        if (dialogue is not null) result = ApplyDialogue(result, dialogue, baseLineIds, newLineIds, builder, errors);
        var travel = Parse(overlays.TravelExt, "$travel_ext", errors);
        if (travel is not null) result = ApplyTravel(result, travel, baseLineIds, newLineIds, builder, errors);
        builder.AddedLineIds.AddRange(newLineIds);
        info = builder.Build();
        return result;
    }

    // ------------------------------------------------------------------ helpers

    private static JsonObject? Parse(string? text, string root, List<string> errors)
    {
        if (string.IsNullOrWhiteSpace(text)) return null;
        try
        {
            var node = JsonNode.Parse(text, documentOptions: ParseOptions);
            if (node is JsonObject obj) return obj;
            errors.Add($"{root}: the overlay must be a JSON object");
        }
        catch (JsonException ex)
        {
            errors.Add($"{root}: invalid JSON ({ex.Message})");
        }
        return null;
    }

    private static HashSet<string> AllLineIds(GameData d)
    {
        var ids = new HashSet<string>(StringComparer.Ordinal);
        void Add(IEnumerable<LineDef> lines) { foreach (var l in lines) if (!string.IsNullOrEmpty(l.LineId)) ids.Add(l.LineId); }
        foreach (var a in d.Actions) Add(a.Lines);
        foreach (var c in d.Characters) foreach (var t in c.AmbientTopics) Add(t.Lines);
        foreach (var r in d.Rooms) Add(r.FirstEntry);
        foreach (var c in d.Cutscenes) foreach (var b in c.Beats) Add(b.Lines);
        return ids;
    }

    private static void CheckKeys(JsonObject obj, string path, IReadOnlyCollection<string> allowed, List<string> errors, string? hint = null)
    {
        foreach (var (key, _) in obj)
            if (!allowed.Contains(key))
                errors.Add($"{path}.{key}: field not allowed in a content overlay" + (hint is null ? "" : $" ({hint})") +
                           $"; allowed: {string.Join(", ", allowed)}");
    }

    private static string? Str(JsonObject obj, string key, string path, List<string> errors, bool required = false)
    {
        if (!obj.TryGetPropertyValue(key, out var node) || node is null)
        {
            if (required) errors.Add($"{path}.{key}: missing");
            return null;
        }
        if (node is JsonValue v && v.TryGetValue<string>(out var s)) return s;
        errors.Add($"{path}.{key}: must be a string");
        return null;
    }

    private static bool? Bool(JsonObject obj, string key, string path, List<string> errors)
    {
        if (!obj.TryGetPropertyValue(key, out var node) || node is null) return null;
        if (node is JsonValue v && v.TryGetValue<bool>(out var b)) return b;
        errors.Add($"{path}.{key}: must be true or false");
        return null;
    }

    private static JsonArray? Arr(JsonObject obj, string key, string path, List<string> errors, bool required = false)
    {
        if (!obj.TryGetPropertyValue(key, out var node) || node is null)
        {
            if (required) errors.Add($"{path}.{key}: missing");
            return null;
        }
        if (node is JsonArray a) return a;
        errors.Add($"{path}.{key}: must be a list");
        return null;
    }

    private static List<string> StrList(JsonObject obj, string key, string path, List<string> errors)
    {
        var list = new List<string>();
        var arr = Arr(obj, key, path, errors);
        if (arr is null) return list;
        for (var i = 0; i < arr.Count; i++)
        {
            if (arr[i] is JsonValue v && v.TryGetValue<string>(out var s)) list.Add(s);
            else errors.Add($"{path}.{key}[{i}]: must be a string");
        }
        return list;
    }

    private static List<int>? IntList(JsonObject obj, string key, string path, int count, List<string> errors)
    {
        var arr = Arr(obj, key, path, errors, required: true);
        if (arr is null) return null;
        var list = new List<int>();
        foreach (var n in arr)
        {
            if (n is JsonValue v && v.TryGetValue<int>(out var i)) list.Add(i);
            else { errors.Add($"{path}.{key}: must be a list of {count} integers"); return null; }
        }
        if (list.Count != count) { errors.Add($"{path}.{key}: must have {count} integers"); return null; }
        return list;
    }

    private static void CheckHeader(JsonObject root, string path, string format, List<string> errors)
    {
        var f = Str(root, "format", path, errors);
        if (f is not null && f != format) errors.Add($"{path}.format: expected '{format}', got '{f}'");
        if (root.TryGetPropertyValue("version", out var v) && v is not null &&
            !(v is JsonValue jv && jv.TryGetValue<int>(out var n) && n == 1))
            errors.Add($"{path}.version: only version 1 is supported");
    }

    // ------------------------------------------------------------------ dialogue overlay

    private static readonly string[] DialogueRootKeys = { "format", "version", "about", "schema", "chunk", "note", "sources", "sequences", "topic_extensions", "topics" };
    private static readonly string[] SequenceKeys = { "id", "action", "topic", "room", "character", "kind", "lines", "note", "chunk" };
    private static readonly string[] TopicKeys = { "id", "character", "label", "label_key", "speaks_first", "repeatable", "requires_done", "excluded_done", "lines", "note", "kind", "chunk" };
    private static readonly string[] LineKeys = { "key", "speaker", "sk", "note" };

    private sealed record Owner(string Kind, string Id, string KeyPrefix, IReadOnlyList<LineDef> Lines, IReadOnlySet<string> Speakers);

    private static GameData ApplyDialogue(GameData data, JsonObject root, IReadOnlySet<string> baseLineIds, HashSet<string> newLineIds,
        InfoBuilder info, List<string> errors)
    {
        const string rp = "$dialogue_ext";
        CheckHeader(root, rp, DialogueFormat, errors);
        CheckKeys(root, rp, DialogueRootKeys, errors, root.ContainsKey("travel") ? "exits and connections belong in travel_ext.json" : null);
        var speakers = new HashSet<string>(data.Characters.Select(c => c.Id).Concat(data.NonActorSpeakers.Keys), StringComparer.Ordinal);
        var actionIds = new HashSet<string>(data.Actions.Select(a => a.Id), StringComparer.Ordinal);

        var actionLines = new Dictionary<string, IReadOnlyList<LineDef>>(StringComparer.Ordinal);
        var topicLines = new Dictionary<string, IReadOnlyList<LineDef>>(StringComparer.Ordinal);
        var entryLines = new Dictionary<string, IReadOnlyList<LineDef>>(StringComparer.Ordinal);
        var newTopics = new Dictionary<string, List<TopicDef>>(StringComparer.Ordinal); // character -> topics

        var hotspots = data.Rooms.SelectMany(r => r.Hotspots).GroupBy(h => h.Id).ToDictionary(g => g.Key, g => g.First(), StringComparer.Ordinal);
        var topicOwner = new Dictionary<string, (CharacterDef Character, TopicDef Topic)>(StringComparer.Ordinal);
        foreach (var c in data.Characters) foreach (var t in c.AmbientTopics) topicOwner.TryAdd(t.Id, (c, t));
        var rooms = data.Rooms.ToDictionary(r => r.Id, StringComparer.Ordinal);
        var actions = data.Actions.GroupBy(a => a.Id).ToDictionary(g => g.Key, g => g.First(), StringComparer.Ordinal);

        // Who takes part in conversations with a character: Adam, the character, and everyone who already speaks in
        // the handoff lines of its topics and of the actions on its NPC hotspots (e.g. Bodka next to Lenka).
        var party = new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);
        HashSet<string> Party(string characterId)
        {
            if (party.TryGetValue(characterId, out var set)) return set;
            set = new HashSet<string>(StringComparer.Ordinal) { "ADAM", characterId };
            foreach (var t in data.Characters.Where(c => c.Id == characterId).SelectMany(c => c.AmbientTopics)) set.UnionWith(t.Lines.Select(l => l.Speaker));
            foreach (var a in data.Actions)
                if (hotspots.TryGetValue(a.Target, out var h) && h.IsNpc && h.CharacterId == characterId) set.UnionWith(a.Lines.Select(l => l.Speaker));
            return party[characterId] = set;
        }

        var index = 0;
        foreach (var listKey in new[] { "sequences", "topic_extensions" })
        {
            var list = Arr(root, listKey, rp, errors);
            if (list is null) continue;
            for (var i = 0; i < list.Count; i++, index++)
            {
                var path = $"{rp}.{listKey}[{i}]";
                if (list[i] is not JsonObject seq) { errors.Add($"{path}: must be an object"); continue; }
                CheckKeys(seq, path, SequenceKeys, errors, "a sequence may only set lines");
                var action = Str(seq, "action", path, errors);
                var topic = Str(seq, "topic", path, errors);
                var room = Str(seq, "room", path, errors);
                var anchors = new[] { action, topic, room }.Count(a => a is not null);
                if (anchors != 1) { errors.Add($"{path}: give exactly one of 'action', 'topic' or 'room' (first-entry lines)"); continue; }
                Owner? owner = null;
                string? expectedKind = null, expectedId = null;
                if (action is not null)
                {
                    path += $"({action})";
                    if (!actions.TryGetValue(action, out var a)) { errors.Add($"{path}.action: unknown action '{action}'"); continue; }
                    var allowed = new HashSet<string>(a.Lines.Select(l => l.Speaker), StringComparer.Ordinal) { "ADAM" };
                    if (hotspots.TryGetValue(a.Target, out var target) && target.IsNpc && target.CharacterId is not null) allowed.UnionWith(Party(target.CharacterId));
                    if (a.Staging is not null) allowed.UnionWith(a.Staging.GuestSpeakers);
                    owner = new Owner("action", a.Id, $"action.{a.Id}.", a.Lines, allowed);
                    expectedKind = "action_lines";
                    expectedId = $"action.{a.Id}";
                    if (actionLines.ContainsKey(a.Id)) { errors.Add($"{path}: action '{a.Id}' is extended twice"); continue; }
                }
                else if (topic is not null)
                {
                    path += $"({topic})";
                    if (!topicOwner.TryGetValue(topic, out var t)) { errors.Add($"{path}.topic: unknown ambient topic '{topic}'"); continue; }
                    var character = Str(seq, "character", path, errors);
                    if (character is not null && character != t.Character.Id) errors.Add($"{path}.character: topic '{topic}' belongs to '{t.Character.Id}', not '{character}'");
                    var allowed = Party(t.Character.Id);
                    owner = new Owner("topic", t.Topic.Id, $"topic.{t.Topic.Id}.", t.Topic.Lines, allowed);
                    expectedKind = "topic_lines";
                    expectedId = $"topic.{t.Topic.Id}";
                    if (topicLines.ContainsKey(t.Topic.Id)) { errors.Add($"{path}: topic '{t.Topic.Id}' is extended twice"); continue; }
                }
                else
                {
                    path += $"({room})";
                    if (!rooms.TryGetValue(room!, out var r)) { errors.Add($"{path}.room: unknown room '{room}'"); continue; }
                    var allowed = new HashSet<string>(r.FirstEntry.Select(l => l.Speaker), StringComparer.Ordinal) { "ADAM" };
                    owner = new Owner("room", r.Id, $"entry.{r.Id}.", r.FirstEntry, allowed);
                    expectedKind = "first_entry_lines";
                    expectedId = $"entry.{r.Id}";
                    if (entryLines.ContainsKey(r.Id)) { errors.Add($"{path}: the first entry of room '{r.Id}' is extended twice"); continue; }
                }
                var kind = Str(seq, "kind", path, errors);
                if (kind is not null && kind != expectedKind) errors.Add($"{path}.kind: expected '{expectedKind}', got '{kind}'");
                var id = Str(seq, "id", path, errors);
                if (id is not null && id != expectedId) errors.Add($"{path}.id: expected '{expectedId}', got '{id}'");
                Str(seq, "note", path, errors);
                Str(seq, "chunk", path, errors);
                var lines = ParseLines(seq, path, owner, allowExisting: true, speakers, baseLineIds, newLineIds, errors);
                if (lines is null) continue;
                var kept = new HashSet<string>(lines.Where(l => l.LineId is not null && baseLineIds.Contains(l.LineId)).Select(l => l.LineId!), StringComparer.Ordinal);
                var source = owner.Kind switch { "action" => LineSource.Action, "topic" => LineSource.Topic, _ => LineSource.FirstEntry };
                foreach (var dropped in owner.Lines.Where(l => l.LineId is not null && !kept.Contains(l.LineId)))
                    info.RetiredLines.Add(new LineInfo(dropped, source, owner.Id));
                switch (owner.Kind)
                {
                    case "action": actionLines[owner.Id] = lines; info.ExtendedActions.Add(owner.Id); break;
                    case "topic": topicLines[owner.Id] = lines; info.ExtendedTopics.Add(owner.Id); break;
                    default: entryLines[owner.Id] = lines; info.ExtendedFirstEntries.Add(owner.Id); break;
                }
            }
        }

        var topicsArr = Arr(root, "topics", rp, errors);
        if (topicsArr is not null)
        {
            var npcCharacters = new HashSet<string>(hotspots.Values.Where(h => h.IsNpc && h.CharacterId is not null).Select(h => h.CharacterId!), StringComparer.Ordinal);
            var characters = data.Characters.ToDictionary(c => c.Id, StringComparer.Ordinal);
            var seenTopicIds = new HashSet<string>(topicOwner.Keys, StringComparer.Ordinal);
            for (var i = 0; i < topicsArr.Count; i++)
            {
                var path = $"{rp}.topics[{i}]";
                if (topicsArr[i] is not JsonObject t) { errors.Add($"{path}: must be an object"); continue; }
                var id = Str(t, "id", path, errors, required: true);
                if (id is null) continue;
                path += $"({id})";
                CheckKeys(t, path, TopicKeys, errors, "a new topic may only set label, lines, repeatable, requires_done and excluded_done");
                var characterId = Str(t, "character", path, errors, required: true);
                if (characterId is null) continue;
                if (!characters.TryGetValue(characterId, out var character)) { errors.Add($"{path}.character: unknown character '{characterId}'"); continue; }
                if (!npcCharacters.Contains(characterId)) { errors.Add($"{path}.character: '{characterId}' has no NPC hotspot to talk to"); continue; }
                var draft = DraftTopicId.Match(id);
                if (!id.StartsWith("ext.", StringComparison.Ordinal) && !(draft.Success && draft.Groups["char"].Value == characterId))
                    errors.Add($"{path}.id: a new topic id must start with 'ext.' or be '<character>.extra <n>' (here '{characterId}.extra 1')");
                if (!seenTopicIds.Add(id)) { errors.Add($"{path}.id: topic id '{id}' already exists"); continue; }
                var kind = Str(t, "kind", path, errors);
                if (kind is not null && kind != "new_topic") errors.Add($"{path}.kind: expected 'new_topic', got '{kind}'");
                var label = Str(t, "label", path, errors, required: true);
                if (label is not null && string.IsNullOrWhiteSpace(label)) errors.Add($"{path}.label: empty");
                var labelKey = Str(t, "label_key", path, errors);
                if (labelKey is not null && labelKey != $"topic.{id}.label") errors.Add($"{path}.label_key: expected 'topic.{id}.label', got '{labelKey}'");
                var requires = StrList(t, "requires_done", path, errors);
                var excluded = StrList(t, "excluded_done", path, errors);
                for (var r = 0; r < requires.Count; r++) if (!actionIds.Contains(requires[r])) errors.Add($"{path}.requires_done[{r}]: unknown action '{requires[r]}'");
                for (var r = 0; r < excluded.Count; r++) if (!actionIds.Contains(excluded[r])) errors.Add($"{path}.excluded_done[{r}]: unknown action '{excluded[r]}'");
                foreach (var both in requires.Intersect(excluded)) errors.Add($"{path}: action '{both}' is both required and excluded; the topic could never be offered");
                var repeatable = Bool(t, "repeatable", path, errors) ?? true;
                Str(t, "note", path, errors);
                Str(t, "chunk", path, errors);
                var owner = new Owner("topic", id, $"topic.{id}.", Array.Empty<LineDef>(), Party(characterId));
                var lines = ParseLines(t, path, owner, allowExisting: false, speakers, baseLineIds, newLineIds, errors);
                if (lines is null || label is null) continue;
                var speaksFirst = Str(t, "speaks_first", path, errors);
                if (speaksFirst is not null && lines.Count > 0 && lines[0].Speaker != speaksFirst)
                    errors.Add($"{path}.speaks_first: '{speaksFirst}' but the first line is spoken by '{lines[0].Speaker}'");
                if (!newTopics.TryGetValue(characterId, out var bucket)) newTopics[characterId] = bucket = new List<TopicDef>();
                bucket.Add(new TopicDef { Id = id, Label = label, RequiresDone = requires, ExcludedDone = excluded, Repeatable = repeatable, Lines = lines });
                info.AddedTopics.Add(id);
            }
        }

        if (actionLines.Count == 0 && topicLines.Count == 0 && entryLines.Count == 0 && newTopics.Count == 0) return data;
        return data with
        {
            Actions = data.Actions.Select(a => actionLines.TryGetValue(a.Id, out var l) ? a with { Lines = l } : a).ToList(),
            Characters = data.Characters.Select(c =>
            {
                var topics = c.AmbientTopics.Select(t => topicLines.TryGetValue(t.Id, out var l) ? t with { Lines = l } : t).ToList();
                if (newTopics.TryGetValue(c.Id, out var added)) topics.AddRange(added);
                return c with { AmbientTopics = topics };
            }).ToList(),
            Rooms = data.Rooms.Select(r => entryLines.TryGetValue(r.Id, out var l) ? r with { FirstEntry = l } : r).ToList(),
        };
    }

    /// <summary>
    /// Parses the full play order of a sequence: a string is an existing line of the same owner (kept at that
    /// position), an object <c>{key, speaker, sk}</c> is a new line. Returns null when the list is unusable.
    /// </summary>
    private static List<LineDef>? ParseLines(JsonObject seq, string path, Owner owner, bool allowExisting, IReadOnlySet<string> speakers,
        IReadOnlySet<string> baseLineIds, HashSet<string> newLineIds, List<string> errors)
    {
        var arr = Arr(seq, "lines", path, errors, required: true);
        if (arr is null) return null;
        if (arr.Count == 0) { errors.Add($"{path}.lines: empty (remove the entry to keep the handoff lines)"); return null; }
        var existing = owner.Lines.Where(l => l.LineId is not null).GroupBy(l => l.LineId!).ToDictionary(g => g.Key, g => g.First(), StringComparer.Ordinal);
        var used = new HashSet<string>(StringComparer.Ordinal);
        var lines = new List<LineDef>();
        var ok = true;
        for (var i = 0; i < arr.Count; i++)
        {
            var lp = $"{path}.lines[{i}]";
            if (arr[i] is JsonValue v && v.TryGetValue<string>(out var key))
            {
                if (!allowExisting) { errors.Add($"{lp}: '{key}': a new topic has no existing lines; write {{key, speaker, sk}}"); ok = false; continue; }
                if (!existing.TryGetValue(key, out var line))
                {
                    errors.Add($"{lp}: '{key}' is not a line of {owner.Kind} '{owner.Id}'" +
                               (baseLineIds.Contains(key) ? " (lines may only be reordered within their own exchange)" : ""));
                    ok = false;
                    continue;
                }
                if (!used.Add(key)) { errors.Add($"{lp}: '{key}' is listed twice"); ok = false; continue; }
                lines.Add(line);
                continue;
            }
            if (arr[i] is not JsonObject obj) { errors.Add($"{lp}: must be an existing line id or an object {{key, speaker, sk}}"); ok = false; continue; }
            CheckKeys(obj, lp, LineKeys, errors, "a line has only key, speaker and sk");
            var newKey = Str(obj, "key", lp, errors, required: true);
            var speaker = Str(obj, "speaker", lp, errors, required: true);
            var text = Str(obj, "sk", lp, errors, required: true);
            Str(obj, "note", lp, errors);
            if (newKey is null || speaker is null || text is null) { ok = false; continue; }
            if (!newKey.StartsWith(owner.KeyPrefix, StringComparison.Ordinal) || !LineSuffix.IsMatch(newKey[owner.KeyPrefix.Length..]))
            {
                errors.Add($"{lp}.key: '{newKey}' must be '{owner.KeyPrefix}<n>' (e.g. {owner.KeyPrefix}x01)");
                ok = false;
            }
            if (baseLineIds.Contains(newKey) || !newLineIds.Add(newKey)) { errors.Add($"{lp}.key: '{newKey}' already exists; new lines need new stable keys"); ok = false; }
            if (!speakers.Contains(speaker)) { errors.Add($"{lp}.speaker: unknown speaker '{speaker}'"); ok = false; }
            else if (!owner.Speakers.Contains(speaker))
            {
                errors.Add($"{lp}.speaker: '{speaker}' does not take part in {owner.Kind} '{owner.Id}' (allowed: {string.Join(", ", owner.Speakers.OrderBy(s => s, StringComparer.Ordinal))})");
                ok = false;
            }
            if (string.IsNullOrWhiteSpace(text)) { errors.Add($"{lp}.sk: empty text"); ok = false; }
            else if (text.IndexOfAny(new[] { '\n', '\r' }) >= 0) { errors.Add($"{lp}.sk: one line is one subtitle; no line breaks"); ok = false; }
            lines.Add(new LineDef { Speaker = speaker, Text = text, LineId = newKey });
        }
        return ok ? lines : null;
    }

    // ------------------------------------------------------------------ travel overlay

    private static readonly string[] TravelRootKeys = { "format", "version", "about", "note", "remove_exits", "remove_connections", "exits", "connections", "regions" };
    private static readonly string[] ExitKeys = { "room", "id", "to", "label", "locked_look", "travel", "requires_done", "rect", "interaction_point", "first_ride", "note" };
    private static readonly string[] ConnectionKeys = { "from", "to", "bidirectional", "travel", "label", "locked_look", "requires_done", "note" };
    private static readonly string[] RegionKeys = { "id", "era", "rooms", "hubs", "note" };

    private static GameData ApplyTravel(GameData data, JsonObject root, IReadOnlySet<string> baseLineIds, HashSet<string> newLineIds,
        InfoBuilder info, List<string> errors)
    {
        const string rp = "$travel_ext";
        CheckHeader(root, rp, TravelFormat, errors);
        CheckKeys(root, rp, TravelRootKeys, errors);
        var rooms = data.Rooms.ToDictionary(r => r.Id, StringComparer.Ordinal);
        var actionIds = new HashSet<string>(data.Actions.Select(a => a.Id), StringComparer.Ordinal);
        var exitsByRoom = data.Rooms.ToDictionary(r => r.Id, r => r.Exits.ToList(), StringComparer.Ordinal);
        var connections = data.Connections.ToList();
        var errorCount = errors.Count;

        // Removals.
        var removeExits = Arr(root, "remove_exits", rp, errors);
        for (var i = 0; removeExits is not null && i < removeExits.Count; i++)
        {
            var path = $"{rp}.remove_exits[{i}]";
            string? exitId = removeExits[i] is JsonValue v && v.TryGetValue<string>(out var s) ? s : null;
            if (removeExits[i] is JsonObject o)
            {
                CheckKeys(o, path, new[] { "exit", "reason" }, errors);
                exitId = Str(o, "exit", path, errors, required: true);
                Str(o, "reason", path, errors);
            }
            else if (exitId is null) { errors.Add($"{path}: must be an exit id or {{exit, reason}}"); continue; }
            if (exitId is null) continue;
            var owner = exitsByRoom.FirstOrDefault(kv => kv.Value.Any(e => e.Id == exitId));
            if (owner.Key is null) { errors.Add($"{path}: unknown exit '{exitId}'"); continue; }
            owner.Value.RemoveAll(e => e.Id == exitId);
            info.RemovedExits.Add(exitId);
        }
        var removeConnections = Arr(root, "remove_connections", rp, errors);
        for (var i = 0; removeConnections is not null && i < removeConnections.Count; i++)
        {
            var path = $"{rp}.remove_connections[{i}]";
            if (removeConnections[i] is not JsonObject o) { errors.Add($"{path}: must be {{from, to, reason}}"); continue; }
            CheckKeys(o, path, new[] { "from", "to", "reason" }, errors);
            var from = Str(o, "from", path, errors, required: true);
            var to = Str(o, "to", path, errors, required: true);
            Str(o, "reason", path, errors);
            if (from is null || to is null) continue;
            var index = connections.FindIndex(c => c.From == from && c.To == to);
            if (index < 0) { errors.Add($"{path}: no connection {from}->{to} in game.json (write it in its game.json direction)"); continue; }
            connections.RemoveAt(index);
            info.RemovedConnections.Add((from, to));
        }

        // Additions.
        var allExitIds = new HashSet<string>(data.Rooms.SelectMany(r => r.Exits).Select(e => e.Id), StringComparer.Ordinal);
        var addedExits = new List<(string Room, ExitDef Exit)>();
        var exitsArr = Arr(root, "exits", rp, errors);
        for (var i = 0; exitsArr is not null && i < exitsArr.Count; i++)
        {
            var path = $"{rp}.exits[{i}]";
            if (exitsArr[i] is not JsonObject o) { errors.Add($"{path}: must be an object"); continue; }
            var id = Str(o, "id", path, errors, required: true);
            if (id is null) continue;
            path += $"({id})";
            CheckKeys(o, path, ExitKeys, errors);
            var roomId = Str(o, "room", path, errors, required: true);
            var to = Str(o, "to", path, errors, required: true);
            var label = Str(o, "label", path, errors, required: true);
            var locked = Str(o, "locked_look", path, errors, required: true);
            var travel = Str(o, "travel", path, errors, required: true);
            var requires = StrList(o, "requires_done", path, errors);
            var rect = IntList(o, "rect", path, 4, errors);
            var point = IntList(o, "interaction_point", path, 2, errors);
            Str(o, "note", path, errors);
            if (roomId is null || to is null || label is null || locked is null || travel is null || rect is null || point is null) continue;
            if (!rooms.TryGetValue(roomId, out var room)) { errors.Add($"{path}.room: unknown room '{roomId}'"); continue; }
            if (!rooms.TryGetValue(to, out var target)) { errors.Add($"{path}.to: unknown room '{to}'"); continue; }
            if (to == roomId) errors.Add($"{path}.to: an exit cannot lead into its own room");
            if (target.Era != room.Era) errors.Add($"{path}.to: '{to}' is in {target.Era}, not {room.Era}; eras are changed only by the chronometer");
            if (id != $"{roomId}.to_{to}") errors.Add($"{path}.id: expected '{roomId}.to_{to}' (exit ids name their room and target)");
            if (!allExitIds.Add(id) && !info.RemovedExits.Contains(id)) errors.Add($"{path}.id: exit '{id}' already exists");
            if (exitsByRoom[roomId].Any(e => e.To == to)) errors.Add($"{path}: room '{roomId}' already has an exit to '{to}'");
            if (!TravelKinds.Contains(travel)) errors.Add($"{path}.travel: unknown travel style '{travel}' (known: {string.Join(", ", TravelKinds)})");
            for (var r = 0; r < requires.Count; r++) if (!actionIds.Contains(requires[r])) errors.Add($"{path}.requires_done[{r}]: unknown action '{requires[r]}'");
            if (string.IsNullOrWhiteSpace(label)) errors.Add($"{path}.label: empty");
            if (string.IsNullOrWhiteSpace(locked)) errors.Add($"{path}.locked_look: empty");
            if (o.TryGetPropertyValue("first_ride", out var rideNode) && rideNode is not null)
            {
                var ridePath = path + ".first_ride";
                if (rideNode is not JsonObject ride) errors.Add($"{ridePath}: must be {{lines: [...]}}");
                else
                {
                    CheckKeys(ride, ridePath, new[] { "id", "lines", "note" }, errors);
                    var rideId = Str(ride, "id", ridePath, errors);
                    if (rideId is not null && rideId != $"travel.{id}.first") errors.Add($"{ridePath}.id: expected 'travel.{id}.first'");
                    Str(ride, "note", ridePath, errors);
                    var owner = new Owner("first ride", id, $"travel.{id}.first.", Array.Empty<LineDef>(), new HashSet<string>(StringComparer.Ordinal) { "ADAM" });
                    var speakers = new HashSet<string>(data.Characters.Select(c => c.Id).Concat(data.NonActorSpeakers.Keys), StringComparer.Ordinal);
                    var lines = ParseLines(ride, ridePath, owner, allowExisting: false, speakers, baseLineIds, newLineIds, errors);
                    if (lines is not null) info.FirstRides[id] = lines;
                }
            }
            var exit = new ExitDef { Id = id, To = to, Label = label, LockedLook = locked, Travel = travel, RequiresDone = requires, Rect = rect, InteractionPoint = point };
            exitsByRoom[roomId].Add(exit);
            addedExits.Add((roomId, exit));
            info.AddedExits.Add(id);
        }
        var connArr = Arr(root, "connections", rp, errors);
        for (var i = 0; connArr is not null && i < connArr.Count; i++)
        {
            var path = $"{rp}.connections[{i}]";
            if (connArr[i] is not JsonObject o) { errors.Add($"{path}: must be an object"); continue; }
            CheckKeys(o, path, ConnectionKeys, errors);
            var from = Str(o, "from", path, errors, required: true);
            var to = Str(o, "to", path, errors, required: true);
            if (from is null || to is null) continue;
            path += $"({from}->{to})";
            var label = Str(o, "label", path, errors, required: true);
            var locked = Str(o, "locked_look", path, errors, required: true);
            var travel = Str(o, "travel", path, errors, required: true);
            var requires = StrList(o, "requires_done", path, errors);
            var bidirectional = Bool(o, "bidirectional", path, errors) ?? true;
            Str(o, "note", path, errors);
            if (label is null || locked is null || travel is null) continue;
            if (!rooms.TryGetValue(from, out var a)) { errors.Add($"{path}.from: unknown room '{from}'"); continue; }
            if (!rooms.TryGetValue(to, out var b)) { errors.Add($"{path}.to: unknown room '{to}'"); continue; }
            if (a.Era != b.Era) errors.Add($"{path}: connections stay inside one era");
            if (connections.Any(c => (c.From == from && c.To == to) || (c.From == to && c.To == from)))
                errors.Add($"{path}: a connection between '{from}' and '{to}' already exists");
            if (!TravelKinds.Contains(travel)) errors.Add($"{path}.travel: unknown travel style '{travel}'");
            for (var r = 0; r < requires.Count; r++) if (!actionIds.Contains(requires[r])) errors.Add($"{path}.requires_done[{r}]: unknown action '{requires[r]}'");
            if (string.IsNullOrWhiteSpace(label)) errors.Add($"{path}.label: empty");
            if (string.IsNullOrWhiteSpace(locked)) errors.Add($"{path}.locked_look: empty");
            connections.Add(new ConnectionDef { From = from, To = to, Bidirectional = bidirectional, Travel = travel, Label = label, LockedLook = locked, RequiresDone = requires });
            info.AddedConnections.Add((from, to));
        }
        if (errors.Count > errorCount) return data;

        // Exits and connections stay consistent: the map graph (connections) and the room exits describe the same edges.
        foreach (var (from, to) in info.AddedConnections)
        {
            var c = connections.First(x => x.From == from && x.To == to);
            void Side(string a, string b)
            {
                var e = exitsByRoom[a].FirstOrDefault(x => x.To == b);
                if (e is null) errors.Add($"{rp}.connections({from}->{to}): room '{a}' needs an exit to '{b}' in exits");
                else if (e.Travel != c.Travel || !e.RequiresDone.SequenceEqual(c.RequiresDone))
                    errors.Add($"{rp}.exits({e.Id}): travel and requires_done must equal those of connection {from}->{to}");
            }
            Side(from, to);
            if (c.Bidirectional) Side(to, from);
        }
        foreach (var (roomId, exit) in addedExits)
        {
            if (!connections.Any(c => (c.From == roomId && c.To == exit.To) || (c.Bidirectional && c.From == exit.To && c.To == roomId)))
                errors.Add($"{rp}.exits({exit.Id}): no connection leads from '{roomId}' to '{exit.To}'; add one in connections");
        }
        foreach (var (from, to) in info.RemovedConnections)
        {
            foreach (var (a, b) in new[] { (from, to), (to, from) })
            {
                var stale = exitsByRoom[a].FirstOrDefault(e => e.To == b);
                if (stale is not null && !connections.Any(c => (c.From == a && c.To == b) || (c.Bidirectional && c.From == b && c.To == a)))
                    errors.Add($"{rp}.remove_connections({from}->{to}): exit '{stale.Id}' still leads there; add it to remove_exits");
            }
        }
        foreach (var exitId in info.RemovedExits)
        {
            var (roomId, exit) = data.Rooms.SelectMany(r => r.Exits.Select(e => (r.Id, e))).First(x => x.e.Id == exitId);
            if (connections.Any(c => (c.From == roomId && c.To == exit.To) || (c.Bidirectional && c.From == exit.To && c.To == roomId)))
                errors.Add($"{rp}.remove_exits({exitId}): connection {roomId}<->{exit.To} still exists; add it to remove_connections");
        }

        var result = data with
        {
            Rooms = data.Rooms.Select(r => r with { Exits = exitsByRoom[r.Id] }).ToList(),
            Connections = connections,
        };

        // Every room stays reachable from its era's time node over the (ungated) graph.
        foreach (var era in data.Eras)
        {
            var seen = new HashSet<string>(StringComparer.Ordinal) { era.Anchor };
            var queue = new Queue<string>(seen);
            while (queue.Count > 0)
            {
                var r = queue.Dequeue();
                foreach (var c in connections)
                {
                    if (c.From == r && seen.Add(c.To)) queue.Enqueue(c.To);
                    if (c.Bidirectional && c.To == r && seen.Add(c.From)) queue.Enqueue(c.From);
                }
            }
            foreach (var r in data.Rooms.Where(r => r.Era == era.Year && !seen.Contains(r.Id)))
                errors.Add($"{rp}: room '{r.Id}' can no longer be reached from the {era.Year} time node '{era.Anchor}'");
        }

        ParseRegions(root, result, info, errors);
        return result;
    }

    private static void ParseRegions(JsonObject root, GameData data, InfoBuilder info, List<string> errors)
    {
        const string rp = "$travel_ext";
        var arr = Arr(root, "regions", rp, errors);
        if (arr is null) return;
        var rooms = data.Rooms.ToDictionary(r => r.Id, StringComparer.Ordinal);
        var years = new HashSet<int>(data.Eras.Select(e => e.Year));
        var regionOf = new Dictionary<string, RegionDef>(StringComparer.Ordinal);
        var regions = new List<RegionDef>();
        for (var i = 0; i < arr.Count; i++)
        {
            var path = $"{rp}.regions[{i}]";
            if (arr[i] is not JsonObject o) { errors.Add($"{path}: must be an object"); continue; }
            var id = Str(o, "id", path, errors, required: true);
            if (id is null) continue;
            path += $"({id})";
            CheckKeys(o, path, RegionKeys, errors);
            Str(o, "note", path, errors);
            int era = 0;
            if (!(o.TryGetPropertyValue("era", out var en) && en is JsonValue ev && ev.TryGetValue<int>(out era))) { errors.Add($"{path}.era: missing year"); continue; }
            if (!years.Contains(era)) { errors.Add($"{path}.era: unknown era {era}"); continue; }
            if (string.IsNullOrWhiteSpace(id) || id.Contains('.')) errors.Add($"{path}.id: a region id is a plain name without dots (its text key is region.<id>.name)");
            if (regions.Any(r => r.Era == era && r.Id == id)) errors.Add($"{path}.id: region '{id}' is defined twice in {era}");
            var list = StrList(o, "rooms", path, errors);
            var hubs = StrList(o, "hubs", path, errors);
            if (list.Count == 0) errors.Add($"{path}.rooms: empty");
            if (hubs.Count == 0) errors.Add($"{path}.hubs: a region needs at least one hub (the stop or station it is entered through)");
            var region = new RegionDef(id, era, list, hubs, FromOverlay: true);
            foreach (var r in list)
            {
                if (!rooms.TryGetValue(r, out var room)) errors.Add($"{path}.rooms: unknown room '{r}'");
                else if (room.Era != era) errors.Add($"{path}.rooms: '{r}' is in {room.Era}, not {era}");
                else if (!regionOf.TryAdd(r, region)) errors.Add($"{path}.rooms: '{r}' already belongs to region '{regionOf[r].Id}'");
            }
            foreach (var h in hubs)
                if (!list.Contains(h)) errors.Add($"{path}.hubs: hub '{h}' is not one of the region's rooms");
            regions.Add(region);
        }
        foreach (var era in regions.Select(r => r.Era).Distinct())
            foreach (var room in data.Rooms.Where(r => r.Era == era && !regionOf.ContainsKey(r.Id)))
                errors.Add($"{rp}.regions: room '{room.Id}' of {era} belongs to no region (an era with regions lists every room)");

        // Owner rule (2026-10-06): far places are reached through their transport hub. A connection between two
        // regions must join a hub of one region to a hub of the other.
        foreach (var c in data.Connections)
        {
            if (!regionOf.TryGetValue(c.From, out var a) || !regionOf.TryGetValue(c.To, out var b) || ReferenceEquals(a, b)) continue;
            if (!a.Hubs.Contains(c.From) || !b.Hubs.Contains(c.To))
                errors.Add($"{rp}.regions: connection {c.From}->{c.To} joins region '{a.Id}' and '{b.Id}' but not hub to hub " +
                           $"(hubs: {string.Join(", ", a.Hubs)} / {string.Join(", ", b.Hubs)}); far places are reached through their transport hub");
        }
        info.Regions.AddRange(regions);
    }

    private sealed class InfoBuilder
    {
        public readonly List<string> ExtendedActions = new(), ExtendedTopics = new(), ExtendedFirstEntries = new(), AddedTopics = new(), AddedLineIds = new();
        public readonly List<LineInfo> RetiredLines = new();
        public readonly List<string> RemovedExits = new(), AddedExits = new();
        public readonly List<(string, string)> RemovedConnections = new(), AddedConnections = new();
        public readonly Dictionary<string, IReadOnlyList<LineDef>> FirstRides = new(StringComparer.Ordinal);
        public readonly List<RegionDef> Regions = new();

        public OverlayInfo Build() => new()
        {
            ExtendedActions = ExtendedActions, ExtendedTopics = ExtendedTopics, ExtendedFirstEntries = ExtendedFirstEntries,
            AddedTopics = AddedTopics, AddedLineIds = AddedLineIds, RetiredLines = RetiredLines, RemovedExits = RemovedExits,
            AddedExits = AddedExits, RemovedConnections = RemovedConnections, AddedConnections = AddedConnections,
            FirstRides = FirstRides, Regions = Regions,
        };
    }
}
