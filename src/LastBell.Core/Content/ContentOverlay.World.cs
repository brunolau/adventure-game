using System.Text.Json.Nodes;
using System.Text.RegularExpressions;

namespace LastBell.Core.Content;

// The world overlay (content_ext/world_ext.json, Core README section 13): new rooms, hotspots, characters, items,
// actions, side quests, epilogue shots, variant layers and connections on top of game.json, and the relocation of an
// existing action to a hotspot in another room of the same era. New ids only; everything is validated as strictly as
// game.json itself (references, item flow, default-click ambiguity, reachability) and the load then runs the
// playability check (ContentPlayability) on the effective content.
internal static partial class OverlayApplier
{
    /// <summary>JSON path root of world overlay errors.</summary>
    internal const string WorldRoot = "$world_ext";

    /// <summary>The only commit policy of game.json (and of overlay actions).</summary>
    internal const string AtomicCommitPolicy = "atomic_after_validation_and_puzzle_before_lines";

    /// <summary>Render layers of a room (game.json uses exactly these, back to front).</summary>
    internal static readonly IReadOnlyList<string> DefaultLayerOrder = new[]
    {
        "background", "prop_state_variants", "npc_shadows", "npcs_and_adam_sorted_by_feet_y", "foreground_mask", "hotspot_labels", "hud",
    };

    /// <summary>Hero animations the actor sheets provide (actions[].animation).</summary>
    internal static readonly IReadOnlySet<string> Animations = new HashSet<string>(StringComparer.Ordinal)
    {
        "talk", "show_item", "inventory_combine", "use_tool", "reach_low", "reach_mid", "reach_high",
    };

    /// <summary>The logical canvas (rects and points of rooms are in these pixels).</summary>
    internal const int CanvasWidth = 1920, CanvasHeight = 1080;

    /// <summary>Minimal hit size of a hotspot or exit (accessibility rule of the handoff).</summary>
    internal const int MinTarget = 44;

    private const string WorldFormat = "lastbell.world_ext";

    private static readonly Regex RoomIdPattern = new(@"^S\d{2,3}$", RegexOptions.CultureInvariant);
    private static readonly Regex CodeIdPattern = new(@"^[A-Z][A-Z0-9_]*$", RegexOptions.CultureInvariant);
    private static readonly Regex QuestIdPattern = new(@"^Q\d{1,3}$", RegexOptions.CultureInvariant);
    private static readonly Regex HotspotSuffixPattern = new(@"^[A-Za-z0-9_]+$", RegexOptions.CultureInvariant);
    private static readonly Regex AssetPattern = new(@"^[a-z_]+(/[A-Za-z0-9_\-]+)+\.(webp|png|jpg|ogg)$", RegexOptions.CultureInvariant);
    private static readonly Regex SfxPattern = new(@"^[a-z0-9_]+$", RegexOptions.CultureInvariant);

    private static readonly string[] WorldRootKeys =
    {
        "format", "version", "about", "note", "schema", "sources", "characters", "items", "rooms", "hotspots", "exits",
        "connections", "quests", "actions", "epilogue", "visual_variant_layers", "relocations",
    };
    private static readonly string[] WorldCharacterKeys = { "id", "name", "age", "role", "voice", "design", "rooms", "note" };
    private static readonly string[] WorldItemKeys = { "id", "name", "look", "purpose", "icon", "origin", "disposition", "note" };
    private static readonly string[] WorldRoomKeys =
    {
        "id", "name", "era", "district", "region", "hub", "art_brief", "ambience", "background_asset", "music", "walk_polygon",
        "spawn", "camera_family", "layer_order", "npc_ids", "first_entry", "hotspots", "exits", "blocking_note", "note",
    };
    private static readonly string[] WorldHotspotKeys =
    {
        "room", "id", "name", "kind", "character_id", "look", "rect", "interaction_point", "label_anchor", "visible_after",
        "hide_after", "look_variants", "note",
    };
    private static readonly string[] WorldQuestKeys = { "id", "type", "title", "goal", "reward", "hints", "actions", "completion", "missable", "note" };
    private static readonly string[] WorldActionKeys =
    {
        "id", "room", "target", "kind", "label", "requires_done", "requires_items", "selected_item", "gives", "consumes",
        "excluded_done", "lines", "quest", "once", "objective", "journal_text", "animation", "sfx", "staging", "commit_policy",
        "symmetric", "hint_step", "puzzle", "cutscene", "note",
    };
    private static readonly string[] WorldEpilogueKeys = { "quest", "after", "shot", "line", "note" };
    private static readonly string[] WorldLayerKeys = { "room", "after", "asset", "change", "note" };
    private static readonly string[] RelocationKeys = { "action", "to_hotspot", "hint_step", "retire_hotspot", "reason", "note" };
    private static readonly string[] LookVariantKeys = { "after", "sk", "note" };
    private static readonly string[] StagingKeys = { "guest_speakers", "rule" };

    private static GameData ApplyWorld(GameData data, JsonObject root, IReadOnlySet<string> baseLineIds, HashSet<string> newLineIds,
        InfoBuilder info, List<string> errors)
    {
        const string rp = WorldRoot;
        var errorCount = errors.Count;
        CheckHeader(root, rp, WorldFormat, errors);
        CheckKeys(root, rp, WorldRootKeys, errors, root.ContainsKey("topics") || root.ContainsKey("sequences")
            ? "lines of existing exchanges and optional topics belong in dialogue_ext.json" : null);
        foreach (var free in new[] { "about", "note", "schema" }) Str(root, free, rp, errors);

        // ---- what exists (game.json) and the new ids announced by this overlay (references may point forward)
        var rooms = data.Rooms.ToDictionary(r => r.Id, StringComparer.Ordinal);
        var hotspotRoom = new Dictionary<string, string>(StringComparer.Ordinal);
        var hotspots = new Dictionary<string, HotspotDef>(StringComparer.Ordinal);
        foreach (var r in data.Rooms) foreach (var h in r.Hotspots) { hotspotRoom.TryAdd(h.Id, r.Id); hotspots.TryAdd(h.Id, h); }
        var characters = data.Characters.ToDictionary(c => c.Id, StringComparer.Ordinal);
        var items = data.Items.ToDictionary(i => i.Id, StringComparer.Ordinal);
        var actions = data.Actions.ToDictionary(a => a.Id, StringComparer.Ordinal);
        var quests = data.Quests.ToDictionary(q => q.Id, StringComparer.Ordinal);
        var years = new HashSet<int>(data.Eras.Select(e => e.Year));
        var usedKeys = new HashSet<string>(baseLineIds, StringComparer.Ordinal);
        foreach (var h in hotspots.Values)
        {
            if (h.LookLineId is not null) usedKeys.Add(h.LookLineId);
            foreach (var v in h.LookVariants) if (v.LineId is not null) usedKeys.Add(v.LineId);
        }
        foreach (var i in data.Items) if (i.LookLineId is not null) usedKeys.Add(i.LookLineId);

        var newActionIds = PreScanIds(root, "actions");
        var newQuestIds = PreScanIds(root, "quests");
        var actionIds = new HashSet<string>(actions.Keys.Concat(newActionIds), StringComparer.Ordinal);
        var allIds = new HashSet<string>(StringComparer.Ordinal); // every new id of any kind (one id, one meaning)

        bool NewId(string id, string path, Regex pattern, string what, string example, bool exists)
        {
            if (!pattern.IsMatch(id)) { errors.Add($"{path}.id: '{id}' is not a valid {what} id (e.g. {example})"); return false; }
            if (exists) { errors.Add($"{path}.id: {what} '{id}' already exists; the world overlay adds new ids only (to move an action use relocations)"); return false; }
            if (!allIds.Add(what + ":" + id)) { errors.Add($"{path}.id: {what} '{id}' is defined twice"); return false; }
            return true;
        }
        bool NewKey(string key, string path)
        {
            if (!newLineIds.Contains(key) && usedKeys.Add(key)) return true;
            errors.Add($"{path}: text key '{key}' already exists");
            return false;
        }

        // ---- characters
        var newCharacters = new List<(CharacterDef Def, List<string>? Rooms, string Path)>();
        foreach (var (o, path) in Entries(root, "characters", rp, errors))
        {
            var id = Str(o, "id", path, errors, required: true);
            if (id is null) continue;
            var p = path + $"({id})";
            CheckKeys(o, p, WorldCharacterKeys, errors, o.ContainsKey("ambient_topics")
                ? "a character's optional topics belong in dialogue_ext.json topics (id 'ext.<...>' or '<CHARACTER>.extra <n>')" : null);
            if (!NewId(id, p, CodeIdPattern, "character", "ZUZANA, SAMPLE95", characters.ContainsKey(id) || data.NonActorSpeakers.ContainsKey(id))) continue;
            var name = Text(o, "name", p, errors);
            JsonNode? age = null;
            if (o.TryGetPropertyValue("age", out var ageNode) && ageNode is not null)
            {
                if (ageNode is JsonValue av && (av.TryGetValue<int>(out _) || av.TryGetValue<string>(out _))) age = ageNode.DeepClone();
                else errors.Add($"{p}.age: must be a number or a text");
            }
            var role = Str(o, "role", p, errors) ?? "";
            var voice = Str(o, "voice", p, errors) ?? "";
            var design = Str(o, "design", p, errors) ?? "";
            Str(o, "note", p, errors);
            var listed = o.ContainsKey("rooms") ? StrList(o, "rooms", p, errors) : null;
            if (name is null) continue;
            newCharacters.Add((new CharacterDef { Id = id, Name = name, Age = age, Role = role, Voice = voice, Design = design }, listed, p));
        }
        foreach (var (c, _, _) in newCharacters) characters[c.Id] = c;
        var speakers = new HashSet<string>(characters.Keys.Concat(data.NonActorSpeakers.Keys), StringComparer.Ordinal);

        // ---- items
        var newItems = new List<(ItemDef Def, string? Origin, string Path)>();
        foreach (var (o, path) in Entries(root, "items", rp, errors))
        {
            var id = Str(o, "id", path, errors, required: true);
            if (id is null) continue;
            var p = path + $"({id})";
            CheckKeys(o, p, WorldItemKeys, errors);
            if (!NewId(id, p, CodeIdPattern, "item", "BELL_MUTE", items.ContainsKey(id))) continue;
            var name = Text(o, "name", p, errors);
            var look = Text(o, "look", p, errors);
            var purpose = Text(o, "purpose", p, errors);
            var icon = Str(o, "icon", p, errors) ?? $"items/{id}.webp";
            if (!icon.StartsWith("items/", StringComparison.Ordinal) || !AssetPattern.IsMatch(icon))
                errors.Add($"{p}.icon: '{icon}' must be an asset path under items/ (e.g. items/{id}.webp)");
            var origin = Str(o, "origin", p, errors);
            var disposition = Str(o, "disposition", p, errors) ?? "retain";
            if (disposition != "retain") errors.Add($"{p}.disposition: every item is 'retain' (kept in the bag; archived when it has no use left)");
            Str(o, "note", p, errors);
            var lookKey = $"item.{id}";
            if (name is null || look is null || purpose is null || !NewKey(lookKey, p + ".look")) continue;
            newItems.Add((new ItemDef { Id = id, Name = name, Look = look, Purpose = purpose, Icon = icon, Disposition = "retain", LookLineId = lookKey }, origin, p));
        }
        foreach (var (item, _, _) in newItems) items[item.Id] = item;

        // ---- rooms (with their hotspots and first-entry lines; exits once every room is known)
        var newRooms = new List<(RoomDef Def, JsonObject Json, string Path, List<string>? NpcIds)>();
        foreach (var (o, path) in Entries(root, "rooms", rp, errors))
        {
            var id = Str(o, "id", path, errors, required: true);
            if (id is null) continue;
            var p = path + $"({id})";
            CheckKeys(o, p, WorldRoomKeys, errors);
            if (!NewId(id, p, RoomIdPattern, "room", "S69", rooms.ContainsKey(id))) continue;
            var name = Text(o, "name", p, errors);
            int era = 0;
            if (!(o.TryGetPropertyValue("era", out var en) && en is JsonValue ev && ev.TryGetValue<int>(out era))) { errors.Add($"{p}.era: missing year"); continue; }
            if (!years.Contains(era)) { errors.Add($"{p}.era: unknown era {era}"); continue; }
            var district = Text(o, "district", p, errors);
            var region = Str(o, "region", p, errors);
            var hub = Bool(o, "hub", p, errors) ?? false;
            if (region is not null && (string.IsNullOrWhiteSpace(region) || region.Contains('.'))) errors.Add($"{p}.region: a region id is a plain name without dots");
            if (hub && region is null) errors.Add($"{p}.hub: only a room with a 'region' can be its hub");
            var background = Str(o, "background_asset", p, errors, required: true);
            if (background is not null && (!(background.StartsWith("bg/", StringComparison.Ordinal) || background.StartsWith("bg_natural/", StringComparison.Ordinal)) || !AssetPattern.IsMatch(background)))
                errors.Add($"{p}.background_asset: '{background}' must be an asset path under bg/ or bg_natural/ (e.g. bg/{id}.webp)");
            var music = Str(o, "music", p, errors, required: true);
            if (music is not null && (!music.StartsWith("music/", StringComparison.Ordinal) || !music.EndsWith(".ogg", StringComparison.Ordinal) || !AssetPattern.IsMatch(music)))
                errors.Add($"{p}.music: '{music}' must be an .ogg path under music/ (e.g. music/{era}.ogg)");
            var polygon = Polygon(o, "walk_polygon", p, errors);
            var spawn = IntList(o, "spawn", p, 2, errors);
            if (polygon is not null && spawn is not null && !InsidePolygon(polygon, spawn[0], spawn[1])) errors.Add($"{p}.spawn: [{spawn[0]}, {spawn[1]}] is not inside the walk polygon");
            var camera = Str(o, "camera_family", p, errors) ?? id;
            var layers = o.ContainsKey("layer_order") ? StrList(o, "layer_order", p, errors) : DefaultLayerOrder.ToList();
            foreach (var l in layers.Where(l => !DefaultLayerOrder.Contains(l))) errors.Add($"{p}.layer_order: unknown layer '{l}' (known: {string.Join(", ", DefaultLayerOrder)})");
            foreach (var l in new[] { "background", "npcs_and_adam_sorted_by_feet_y" }.Where(l => !layers.Contains(l))) errors.Add($"{p}.layer_order: '{l}' is missing");
            var npcIds = o.ContainsKey("npc_ids") ? StrList(o, "npc_ids", p, errors) : null;
            var artBrief = Str(o, "art_brief", p, errors) ?? "";
            var ambience = Str(o, "ambience", p, errors) ?? "";
            var blockingNote = Str(o, "blocking_note", p, errors) ?? "";
            Str(o, "note", p, errors);
            if (name is null || district is null || background is null || music is null || polygon is null || spawn is null) continue;
            if (region is not null) info.RegionHints[id] = (region, hub);
            var room = new RoomDef
            {
                Id = id, Name = name, Era = era, District = district, ArtBrief = artBrief, Ambience = ambience, BackgroundAsset = background,
                Music = music, WalkPolygon = polygon, Spawn = spawn, CameraFamily = camera, LayerOrder = layers, BlockingNote = blockingNote,
            };
            rooms[id] = room;
            newRooms.Add((room, o, p, npcIds));
        }

        // Hotspots of new rooms (inside rooms[]) and of existing rooms (hotspots[] with "room").
        var addedHotspots = new Dictionary<string, List<HotspotDef>>(StringComparer.Ordinal);
        var newHotspotIds = new HashSet<string>(StringComparer.Ordinal);
        void AddHotspot(JsonObject o, string path, string roomId, bool nested)
        {
            var id = Str(o, "id", path, errors, required: true);
            if (id is null) return;
            var p = path + $"({id})";
            CheckKeys(o, p, nested ? WorldHotspotKeys.Where(k => k != "room").ToArray() : WorldHotspotKeys, errors);
            var room = rooms[roomId];
            if (!id.StartsWith(roomId + ".", StringComparison.Ordinal) || !HotspotSuffixPattern.IsMatch(id[(roomId.Length + 1)..]))
            { errors.Add($"{p}.id: a hotspot id is '<room>.<name>' with letters, digits or '_' (e.g. {roomId}.board)"); return; }
            if (hotspots.ContainsKey(id)) { errors.Add($"{p}.id: hotspot '{id}' already exists"); return; }
            var name = Text(o, "name", p, errors);
            var kind = Str(o, "kind", p, errors) ?? "prop";
            var characterId = Str(o, "character_id", p, errors);
            if (kind is not ("prop" or "npc")) errors.Add($"{p}.kind: '{kind}' (a hotspot is 'prop' or 'npc')");
            if (kind == "npc")
            {
                if (characterId is null) errors.Add($"{p}.character_id: an NPC hotspot names its character");
                else if (!characters.ContainsKey(characterId)) errors.Add($"{p}.character_id: unknown character '{characterId}'");
                else if (id != $"{roomId}.{characterId}") errors.Add($"{p}.id: an NPC hotspot is '<room>.<character>' (here '{roomId}.{characterId}')");
                else if (room.Hotspots.Concat(addedHotspots.GetValueOrDefault(roomId) ?? new List<HotspotDef>()).Any(h => h.IsNpc && h.CharacterId == characterId))
                    errors.Add($"{p}.character_id: '{characterId}' already stands in room '{roomId}'");
            }
            else if (characterId is not null) errors.Add($"{p}.character_id: only an NPC hotspot has a character");
            var look = Text(o, "look", p, errors);
            var rect = IntList(o, "rect", p, 4, errors);
            var point = IntList(o, "interaction_point", p, 2, errors);
            var anchor = o.ContainsKey("label_anchor") ? IntList(o, "label_anchor", p, 2, errors) : rect is null ? null : new List<int> { rect[0] + rect[2] / 2, Math.Max(0, rect[1] - 10) };
            if (rect is not null) CheckRect(rect, p + ".rect", errors);
            if (point is not null && !InsidePolygon(room.WalkPolygon, point[0], point[1])) errors.Add($"{p}.interaction_point: [{point[0]}, {point[1]}] is not inside the walk polygon of '{roomId}'");
            if (anchor is not null && !OnCanvas(anchor)) errors.Add($"{p}.label_anchor: [{anchor[0]}, {anchor[1]}] is off screen");
            var visibleAfter = StrList(o, "visible_after", p, errors);
            var hideAfter = StrList(o, "hide_after", p, errors);
            for (var i = 0; i < visibleAfter.Count; i++) if (!actionIds.Contains(visibleAfter[i])) errors.Add($"{p}.visible_after[{i}]: unknown action '{visibleAfter[i]}'");
            for (var i = 0; i < hideAfter.Count; i++) if (!actionIds.Contains(hideAfter[i])) errors.Add($"{p}.hide_after[{i}]: unknown action '{hideAfter[i]}'");
            var variants = new List<LookVariantDef>();
            var vi = 0;
            foreach (var (v, vp) in Entries(o, "look_variants", p, errors))
            {
                vi++;
                CheckKeys(v, vp, LookVariantKeys, errors);
                var after = Str(v, "after", vp, errors, required: true);
                var text = Text(v, "sk", vp, errors);
                Str(v, "note", vp, errors);
                if (after is not null && !actionIds.Contains(after)) errors.Add($"{vp}.after: unknown action '{after}'");
                var key = $"look.{id}.variant{vi}";
                if (after is null || text is null || !NewKey(key, vp)) continue;
                variants.Add(new LookVariantDef { After = after, Text = text, LineId = key });
            }
            Str(o, "note", p, errors);
            var lookKey = $"look.{id}";
            if (name is null || look is null || rect is null || point is null || anchor is null || !NewKey(lookKey, p + ".look")) return;
            var hotspot = new HotspotDef
            {
                Id = id, Name = name, Kind = kind, CharacterId = characterId, Look = look, LookLineId = lookKey, Rect = rect,
                InteractionPoint = point, LabelAnchor = anchor, VisibleAfter = visibleAfter, HideAfter = hideAfter, LookVariants = variants,
            };
            hotspots[id] = hotspot;
            hotspotRoom[id] = roomId;
            newHotspotIds.Add(id);
            if (!addedHotspots.TryGetValue(roomId, out var list)) addedHotspots[roomId] = list = new List<HotspotDef>();
            list.Add(hotspot);
            info.AddedHotspots.Add(id);
        }
        foreach (var (room, json, path, _) in newRooms)
            foreach (var (o, hp) in Entries(json, "hotspots", path, errors)) AddHotspot(o, hp, room.Id, nested: true);
        foreach (var (o, path) in Entries(root, "hotspots", rp, errors))
        {
            var roomId = Str(o, "room", path, errors, required: true);
            if (roomId is null) continue;
            if (!rooms.ContainsKey(roomId)) { errors.Add($"{path}.room: unknown room '{roomId}'"); continue; }
            if (newRooms.Any(r => r.Def.Id == roomId)) { errors.Add($"{path}.room: '{roomId}' is a new room; list its hotspots in rooms[].hotspots"); continue; }
            AddHotspot(o, path, roomId, nested: false);
        }
        HashSet<string> NpcCharactersIn(string roomId) => new(
            rooms[roomId].Hotspots.Concat(addedHotspots.GetValueOrDefault(roomId) ?? new List<HotspotDef>()).Where(h => h.IsNpc && h.CharacterId is not null).Select(h => h.CharacterId!),
            StringComparer.Ordinal);

        // First-entry lines of new rooms: Adam and the people standing there.
        var firstEntries = new Dictionary<string, IReadOnlyList<LineDef>>(StringComparer.Ordinal);
        foreach (var (room, json, path, _) in newRooms)
        {
            if (!json.ContainsKey("first_entry")) continue;
            var allowed = NpcCharactersIn(room.Id);
            allowed.Add("ADAM");
            var owner = new Owner("room", room.Id, $"entry.{room.Id}.", Array.Empty<LineDef>(), allowed);
            var wrapper = new JsonObject { ["lines"] = json["first_entry"]!.DeepClone() };
            var lines = ParseLines(wrapper, path + ".first_entry", owner, allowExisting: false, speakers, baseLineIds, newLineIds, errors);
            if (lines is not null) { firstEntries[room.Id] = lines; usedKeys.UnionWith(lines.Select(l => l.LineId!)); }
        }

        // ---- exits and connections (new rooms carry their own exits; exits[] adds exits to existing rooms)
        var exitsByRoom = rooms.Values.ToDictionary(r => r.Id, r => r.Exits.ToList(), StringComparer.Ordinal);
        var allExitIds = new HashSet<string>(data.Rooms.SelectMany(r => r.Exits).Select(e => e.Id), StringComparer.Ordinal);
        var addedExits = new List<(string Room, ExitDef Exit)>();
        var noRemovals = Array.Empty<string>();
        void ExitAdded(ExitDef? exit, string? roomId, string path)
        {
            if (exit is null || roomId is null) return;
            addedExits.Add((roomId, exit));
            if (!InsidePolygon(rooms[roomId].WalkPolygon, exit.InteractionPoint[0], exit.InteractionPoint[1]))
                errors.Add($"{path}({exit.Id}).interaction_point: [{exit.InteractionPoint[0]}, {exit.InteractionPoint[1]}] is not inside the walk polygon of '{roomId}'");
            CheckRect(exit.Rect, $"{path}({exit.Id}).rect", errors);
        }
        foreach (var (room, json, path, _) in newRooms)
            foreach (var (o, ep) in Entries(json, "exits", path, errors))
                ExitAdded(ParseExit(o, ep, room.Id, rooms, exitsByRoom, allExitIds, noRemovals, actionIds, speakers, baseLineIds, newLineIds, info, errors, out var r), r, ep);
        foreach (var (o, ep) in Entries(root, "exits", rp, errors))
            ExitAdded(ParseExit(o, ep, null, rooms, exitsByRoom, allExitIds, noRemovals, actionIds, speakers, baseLineIds, newLineIds, info, errors, out var r), r, ep);
        var connections = data.Connections.ToList();
        var addedConnections = new List<(string From, string To)>();
        foreach (var (o, cp) in Entries(root, "connections", rp, errors))
        {
            var c = ParseConnection(o, cp, rooms, connections, actionIds, errors);
            if (c is null) continue;
            connections.Add(c);
            addedConnections.Add((c.From, c.To));
            info.AddedConnections.Add((c.From, c.To));
        }
        foreach (var r in newRooms.Where(r => exitsByRoom[r.Def.Id].Count == 0)) errors.Add($"{r.Path}.exits: a room needs at least one exit");

        // ---- side quests
        var newQuests = new List<(QuestDef Def, string Path)>();
        foreach (var (o, path) in Entries(root, "quests", rp, errors))
        {
            var id = Str(o, "id", path, errors, required: true);
            if (id is null) continue;
            var p = path + $"({id})";
            CheckKeys(o, p, WorldQuestKeys, errors);
            if (!NewId(id, p, QuestIdPattern, "quest", "Q10", quests.ContainsKey(id))) continue;
            var type = Str(o, "type", p, errors) ?? "side";
            if (type != "side") errors.Add($"{p}.type: the world overlay adds side quests only (main quests are the handoff's)");
            var title = Text(o, "title", p, errors);
            var goal = Text(o, "goal", p, errors);
            var reward = o.ContainsKey("reward") ? Text(o, "reward", p, errors) ?? "" : "";
            var hints = StrList(o, "hints", p, errors);
            if (hints.Count != 3) errors.Add($"{p}.hints: exactly three hints (direction, place, the whole chain), got {hints.Count}");
            for (var i = 0; i < hints.Count; i++)
                if (string.IsNullOrWhiteSpace(hints[i]) || hints[i].IndexOfAny(new[] { '\n', '\r' }) >= 0) errors.Add($"{p}.hints[{i}]: empty or a line break");
            var questActions = StrList(o, "actions", p, errors);
            if (questActions.Count == 0) errors.Add($"{p}.actions: empty");
            foreach (var a in questActions.Where(a => !newActionIds.Contains(a)))
                errors.Add($"{p}.actions: '{a}' is not an action of this overlay (a new quest consists of new actions)");
            foreach (var dup in questActions.GroupBy(a => a).Where(g => g.Count() > 1)) errors.Add($"{p}.actions: '{dup.Key}' is listed twice");
            var completion = Str(o, "completion", p, errors, required: true);
            if (completion is not null && !questActions.Contains(completion)) errors.Add($"{p}.completion: '{completion}' is not one of the quest's actions");
            if (Bool(o, "missable", p, errors) == true) errors.Add($"{p}.missable: side quests are never missable");
            Str(o, "note", p, errors);
            if (title is null || goal is null || completion is null) continue;
            newQuests.Add((new QuestDef { Id = id, Title = title, Type = "side", Actions = questActions, Goal = goal, Completion = completion, Hints = hints, Reward = reward }, p));
        }

        // Who speaks for a character: the character and everyone in the lines of its handoff topics and of the actions on
        // its NPC hotspots (a counter's speaker id differs from the hotspot's character, e.g. SKLAD speaks as STEFAN).
        HashSet<string> PartyOf(string characterId)
        {
            var set = new HashSet<string>(StringComparer.Ordinal) { characterId };
            if (characters.TryGetValue(characterId, out var c)) foreach (var t in c.AmbientTopics) set.UnionWith(t.Lines.Select(l => l.Speaker));
            foreach (var a in data.Actions)
                if (hotspots.TryGetValue(a.Target, out var h) && h.IsNpc && h.CharacterId == characterId) set.UnionWith(a.Lines.Select(l => l.Speaker));
            return set;
        }

        // ---- actions
        var newActions = new List<(ActionDef Def, string Path)>();
        foreach (var (o, path) in Entries(root, "actions", rp, errors))
        {
            var id = Str(o, "id", path, errors, required: true);
            if (id is null) continue;
            var p = path + $"({id})";
            CheckKeys(o, p, WorldActionKeys, errors);
            if (!NewId(id, p, CodeIdPattern, "action", "Q10A", actions.ContainsKey(id))) continue;
            var roomId = Str(o, "room", p, errors, required: true);
            var target = Str(o, "target", p, errors, required: true);
            var kind = Str(o, "kind", p, errors, required: true);
            var label = Text(o, "label", p, errors);
            var requires = StrList(o, "requires_done", p, errors);
            var excluded = StrList(o, "excluded_done", p, errors);
            var needs = StrList(o, "requires_items", p, errors);
            var gives = StrList(o, "gives", p, errors);
            var consumes = StrList(o, "consumes", p, errors);
            var selected = Str(o, "selected_item", p, errors);
            var quest = Str(o, "quest", p, errors, required: true);
            var objective = o.ContainsKey("objective") && o["objective"] is not null ? Text(o, "objective", p, errors) : null;
            var journal = Text(o, "journal_text", p, errors);
            var hintStep = Text(o, "hint_step", p, errors);
            var sfx = Str(o, "sfx", p, errors);
            if (sfx is not null && !SfxPattern.IsMatch(sfx)) errors.Add($"{p}.sfx: '{sfx}' is not an sfx id (lower case, digits, '_')");
            if (Bool(o, "once", p, errors) == false) errors.Add($"{p}.once: every action happens at most once");
            var policy = Str(o, "commit_policy", p, errors);
            if (policy is not null && policy != AtomicCommitPolicy) errors.Add($"{p}.commit_policy: only '{AtomicCommitPolicy}'");
            var symmetric = Bool(o, "symmetric", p, errors) ?? false;
            foreach (var field in new[] { "puzzle", "cutscene" })
                if (o.TryGetPropertyValue(field, out var n) && n is not null)
                    errors.Add($"{p}.{field}: new actions cannot have a {field} (puzzles and cutscenes have their art and data in game.json); relocate an existing puzzle action instead");
            Str(o, "note", p, errors);
            if (roomId is null || target is null || kind is null || label is null || quest is null || journal is null || hintStep is null) continue;

            for (var i = 0; i < requires.Count; i++) if (!actionIds.Contains(requires[i])) errors.Add($"{p}.requires_done[{i}]: unknown action '{requires[i]}'");
            for (var i = 0; i < excluded.Count; i++) if (!actionIds.Contains(excluded[i])) errors.Add($"{p}.excluded_done[{i}]: unknown action '{excluded[i]}'");
            foreach (var both in requires.Intersect(excluded)) errors.Add($"{p}: '{both}' is both required and excluded; the action could never happen");
            if (requires.Contains(id)) errors.Add($"{p}.requires_done: the action requires itself");
            void Items(string key, IReadOnlyList<string> ids)
            {
                for (var i = 0; i < ids.Count; i++) if (!items.ContainsKey(ids[i])) errors.Add($"{p}.{key}[{i}]: unknown item '{ids[i]}'");
            }
            Items("requires_items", needs);
            Items("gives", gives);
            Items("consumes", consumes);
            foreach (var g in gives.Where(g => items.ContainsKey(g) && !newItems.Any(n => n.Def.Id == g)))
                errors.Add($"{p}.gives: '{g}' is a game.json item; it already has its one origin (a new action gives new items only)");
            foreach (var c in consumes.Where(c => items.ContainsKey(c) && !newItems.Any(n => n.Def.Id == c)))
                errors.Add($"{p}.consumes: '{c}' is a game.json item; consuming it could block the story (a new action consumes new items only)");
            foreach (var c in consumes.Where(c => !needs.Contains(c))) errors.Add($"{p}.consumes: consumed item '{c}' is not declared in requires_items");
            foreach (var g in gives.Where(needs.Contains)) errors.Add($"{p}.gives: '{g}' is also required; an action cannot need what it gives");
            if (selected is not null && !items.ContainsKey(selected)) errors.Add($"{p}.selected_item: unknown item '{selected}'");
            else if (selected is not null && !needs.Contains(selected)) errors.Add($"{p}.selected_item: selected item '{selected}' is not declared in requires_items");
            if (!newQuestIds.Contains(quest)) errors.Add($"{p}.quest: '{quest}' is not a quest of this overlay (new actions belong to new side quests)");

            // Where the action happens and who may speak in its lines.
            var allowed = new HashSet<string>(StringComparer.Ordinal) { "ADAM" };
            StagingDef? staging = null;
            if (o.TryGetPropertyValue("staging", out var stagingNode) && stagingNode is not null)
            {
                if (stagingNode is not JsonObject so) errors.Add($"{p}.staging: must be {{guest_speakers, rule}}");
                else
                {
                    CheckKeys(so, p + ".staging", StagingKeys, errors);
                    var guests = StrList(so, "guest_speakers", p + ".staging", errors);
                    foreach (var g in guests.Where(g => !speakers.Contains(g))) errors.Add($"{p}.staging.guest_speakers: unknown speaker '{g}'");
                    allowed.UnionWith(guests);
                    staging = new StagingDef { GuestSpeakers = guests, Rule = Str(so, "rule", p + ".staging", errors) ?? "" };
                }
            }
            string defaultAnimation;
            switch (kind)
            {
                case "combine":
                    defaultAnimation = "inventory_combine";
                    if (roomId != GameContent.InventoryRoom) errors.Add($"{p}.room: combine actions use room 'inventory'");
                    if (!items.ContainsKey(target)) errors.Add($"{p}.target: unknown item '{target}' (a combine action targets an item)");
                    else if (!needs.Contains(target)) errors.Add($"{p}.requires_items: the target item '{target}' is not declared");
                    if (selected is null) errors.Add($"{p}.selected_item: a combine action names the item put on the target");
                    else if (selected == target) errors.Add($"{p}.selected_item: an item cannot be combined with itself");
                    break;
                case "click" or "topic":
                    defaultAnimation = kind == "topic" ? "talk" : selected is null ? "reach_mid" : "show_item";
                    if (symmetric) errors.Add($"{p}.symmetric: only combine actions are symmetric");
                    if (!rooms.ContainsKey(roomId)) { errors.Add($"{p}.room: unknown room '{roomId}'"); break; }
                    if (!hotspots.TryGetValue(target, out var h)) { errors.Add($"{p}.target: unknown hotspot '{target}'"); break; }
                    if (hotspotRoom[target] != roomId) { errors.Add($"{p}.target: hotspot '{target}' is not in room '{roomId}'"); break; }
                    if (kind == "topic" && (!h.IsNpc || selected is not null)) errors.Add($"{p}.kind: a topic is chosen in the conversation with an NPC and takes no item");
                    if (kind == "click" && h.IsNpc && selected is null) errors.Add($"{p}.selected_item: a left click on an NPC opens the conversation; an action on an NPC is a topic or uses an item");
                    if (h.IsNpc && h.CharacterId is not null) allowed.UnionWith(PartyOf(h.CharacterId));
                    allowed.UnionWith(NpcCharactersIn(roomId));
                    break;
                default:
                    errors.Add($"{p}.kind: unknown action kind '{kind}' (click, topic, combine)");
                    continue;
            }
            var animation = Str(o, "animation", p, errors) ?? defaultAnimation;
            if (!Animations.Contains(animation)) errors.Add($"{p}.animation: unknown animation '{animation}' (known: {string.Join(", ", Animations)})");
            var owner = new Owner("action", id, $"action.{id}.", Array.Empty<LineDef>(), allowed);
            var lines = ParseLines(o, p, owner, allowExisting: false, speakers, baseLineIds, newLineIds, errors);
            if (lines is null) continue;
            usedKeys.UnionWith(lines.Select(l => l.LineId!));
            newActions.Add((new ActionDef
            {
                Id = id, Room = roomId, Target = target, Label = label, Kind = kind, RequiresDone = requires, RequiresItems = needs,
                SelectedItem = selected, Gives = gives, Consumes = consumes, Lines = lines, Quest = quest, Once = true, Objective = objective,
                Animation = animation, Sfx = sfx ?? "", ExcludedDone = excluded, CommitPolicy = AtomicCommitPolicy, Symmetric = symmetric,
                JournalText = journal, Staging = staging ?? new StagingDef(), HintStep = hintStep,
            }, p));
        }
        foreach (var (a, _) in newActions) actions[a.Id] = a;

        // ---- relocations of existing actions
        var relocated = new Dictionary<string, ActionDef>(StringComparer.Ordinal);
        var retire = new List<(string Hotspot, string Room, string Path)>();
        foreach (var (o, path) in Entries(root, "relocations", rp, errors))
        {
            var id = Str(o, "action", path, errors, required: true);
            if (id is null) continue;
            var p = path + $"({id})";
            CheckKeys(o, p, RelocationKeys, errors, "a relocation moves the action only; its guards, items, quest, puzzle and lines stay as they are");
            var to = Str(o, "to_hotspot", p, errors, required: true);
            var hint = Text(o, "hint_step", p, errors);
            var retireOld = Bool(o, "retire_hotspot", p, errors) ?? false;
            Str(o, "reason", p, errors);
            Str(o, "note", p, errors);
            if (to is null || hint is null) continue;
            if (!data.Actions.Any(a => a.Id == id))
            {
                errors.Add(newActionIds.Contains(id) ? $"{p}.action: '{id}' is a new action; put it into its room directly" : $"{p}.action: unknown action '{id}'");
                continue;
            }
            if (relocated.ContainsKey(id)) { errors.Add($"{p}.action: '{id}' is relocated twice"); continue; }
            var action = actions[id];
            if (action.IsInventoryAction) { errors.Add($"{p}.action: '{id}' is a combination in the bag; it happens in no room"); continue; }
            if (!hotspots.TryGetValue(to, out var newTarget)) { errors.Add($"{p}.to_hotspot: unknown hotspot '{to}'"); continue; }
            var toRoom = rooms[hotspotRoom[to]];
            var fromRoom = rooms[action.Room];
            if (toRoom.Id == fromRoom.Id) { errors.Add($"{p}.to_hotspot: '{to}' is in the action's own room '{fromRoom.Id}'; a relocation moves it to another room"); continue; }
            if (toRoom.Era != fromRoom.Era) { errors.Add($"{p}.to_hotspot: '{to}' is in {toRoom.Era}, '{id}' happens in {fromRoom.Era}; a relocation stays in the same era"); continue; }
            var oldTarget = hotspots[action.Target];
            if (oldTarget.IsNpc != newTarget.IsNpc || (oldTarget.IsNpc && oldTarget.CharacterId != newTarget.CharacterId))
            {
                errors.Add($"{p}.to_hotspot: '{action.Target}' is " + (oldTarget.IsNpc ? $"the NPC {oldTarget.CharacterId}" : "a prop") +
                           $", '{to}' is " + (newTarget.IsNpc ? $"the NPC {newTarget.CharacterId}" : "a prop") + "; the action keeps its kind of target (and its speakers)");
                continue;
            }
            relocated[id] = action with { Room = toRoom.Id, Target = to, HintStep = hint };
            info.Relocations.Add(new RelocationInfo(id, fromRoom.Id, action.Target, toRoom.Id, to, retireOld));
            if (retireOld) retire.Add((action.Target, fromRoom.Id, p + ".retire_hotspot"));
        }
        foreach (var (id, a) in relocated) actions[id] = a;
        var effectiveActions = data.Actions.Select(a => actions[a.Id]).Concat(newActions.Select(n => n.Def)).ToList();
        var retiredHotspots = new HashSet<string>(StringComparer.Ordinal);
        foreach (var (hotspotId, roomId, path) in retire)
        {
            if (newHotspotIds.Contains(hotspotId)) continue;
            var still = effectiveActions.Where(a => a.Target == hotspotId && !a.IsInventoryAction).Select(a => a.Id).ToList();
            if (still.Count > 0) errors.Add($"{path}: '{hotspotId}' is still the target of {string.Join(", ", still)}; it cannot be retired");
            else if (hotspots[hotspotId].IsNpc) errors.Add($"{path}: '{hotspotId}' is an NPC; people are not retired by a relocation");
            else if (retiredHotspots.Add(hotspotId)) info.RetiredHotspots.Add(hotspotId);
        }

        // ---- epilogue shots and visual variant layers
        var newEpilogue = new List<EpilogueDef>();
        foreach (var (o, path) in Entries(root, "epilogue", rp, errors))
        {
            CheckKeys(o, path, WorldEpilogueKeys, errors);
            var quest = Str(o, "quest", path, errors, required: true);
            var after = Str(o, "after", path, errors, required: true);
            var shot = Text(o, "shot", path, errors);
            var line = Text(o, "line", path, errors);
            Str(o, "note", path, errors);
            if (quest is null || after is null || shot is null || line is null) continue;
            var q = newQuests.FirstOrDefault(n => n.Def.Id == quest).Def;
            if (q is null) { errors.Add($"{path}.quest: '{quest}' is not a quest of this overlay (game.json quests keep their own shot)"); continue; }
            if (!q.Actions.Contains(after)) errors.Add($"{path}.after: '{after}' is not an action of quest '{quest}'");
            if (newEpilogue.Any(e => e.Quest == quest)) errors.Add($"{path}.quest: quest '{quest}' has a second epilogue shot");
            var colon = line.IndexOf(": ", StringComparison.Ordinal);
            if (colon > 0 && CodeIdPattern.IsMatch(line[..colon]) && !speakers.Contains(line[..colon])) errors.Add($"{path}.line: unknown speaker '{line[..colon]}' (write \"SPEAKER: text\")");
            newEpilogue.Add(new EpilogueDef { Quest = quest, After = after, Shot = shot, Line = line });
            info.AddedEpilogue.Add(quest);
        }
        var newLayers = new List<VisualVariantLayerDef>();
        foreach (var (o, path) in Entries(root, "visual_variant_layers", rp, errors))
        {
            CheckKeys(o, path, WorldLayerKeys, errors);
            var roomId = Str(o, "room", path, errors, required: true);
            var after = Str(o, "after", path, errors, required: true);
            var asset = Str(o, "asset", path, errors, required: true);
            var change = Str(o, "change", path, errors) ?? "";
            Str(o, "note", path, errors);
            if (roomId is null || after is null || asset is null) continue;
            if (!rooms.ContainsKey(roomId)) errors.Add($"{path}.room: unknown room '{roomId}'");
            if (!actionIds.Contains(after)) errors.Add($"{path}.after: unknown action '{after}'");
            if (!asset.StartsWith("variants/", StringComparison.Ordinal) || !AssetPattern.IsMatch(asset)) errors.Add($"{path}.asset: '{asset}' must be an asset path under variants/");
            if (data.VisualVariantLayers.Concat(newLayers).Any(l => l.Room == roomId && l.After == after && l.Asset == asset)) errors.Add($"{path}: this layer already exists");
            newLayers.Add(new VisualVariantLayerDef { Room = roomId, After = after, Asset = asset, Change = change });
            info.AddedVariantLayers.Add(asset);
        }
        if (errors.Count > errorCount) return data;

        // ---- assemble the effective content
        var newRoomIds = new HashSet<string>(newRooms.Select(r => r.Def.Id), StringComparer.Ordinal);
        List<string> NpcIds(RoomDef room, IEnumerable<HotspotDef> list) =>
            room.NpcIds.Concat(list.Where(h => h.IsNpc && h.CharacterId is not null && !room.NpcIds.Contains(h.CharacterId)).Select(h => h.CharacterId!)).Distinct().ToList();
        var effectiveRooms = new List<RoomDef>();
        foreach (var room in data.Rooms)
        {
            var added = addedHotspots.GetValueOrDefault(room.Id) ?? new List<HotspotDef>();
            var list = room.Hotspots.Where(h => !retiredHotspots.Contains(h.Id)).Concat(added).ToList();
            effectiveRooms.Add(room with { Hotspots = list, Exits = exitsByRoom[room.Id], NpcIds = NpcIds(room, added) });
        }
        foreach (var (room, _, path, listed) in newRooms)
        {
            var list = addedHotspots.GetValueOrDefault(room.Id) ?? new List<HotspotDef>();
            var npcIds = NpcIds(room, list);
            if (listed is not null && !listed.OrderBy(x => x, StringComparer.Ordinal).SequenceEqual(npcIds.OrderBy(x => x, StringComparer.Ordinal)))
                errors.Add($"{path}.npc_ids: [{string.Join(", ", listed)}] but the room's NPC hotspots are [{string.Join(", ", npcIds)}] (leave npc_ids out: it is derived)");
            effectiveRooms.Add(room with { Hotspots = list, Exits = exitsByRoom[room.Id], NpcIds = npcIds, FirstEntry = firstEntries.GetValueOrDefault(room.Id) ?? Array.Empty<LineDef>() });
            info.AddedRooms.Add(room.Id);
        }
        var roomsOfCharacter = effectiveRooms.SelectMany(r => r.Hotspots.Where(h => h.IsNpc && h.CharacterId is not null).Select(h => (r.Id, h.CharacterId!)))
            .GroupBy(x => x.Item2).ToDictionary(g => g.Key, g => g.Select(x => x.Id).ToList(), StringComparer.Ordinal);
        var effectiveCharacters = data.Characters.Select(c =>
        {
            var extra = (roomsOfCharacter.GetValueOrDefault(c.Id) ?? new List<string>()).Where(r => !c.Rooms.Contains(r)).ToList();
            return extra.Count == 0 ? c : c with { Rooms = c.Rooms.Concat(extra).ToList() };
        }).ToList();
        foreach (var (c, listed, path) in newCharacters)
        {
            var where = roomsOfCharacter.GetValueOrDefault(c.Id) ?? new List<string>();
            if (listed is not null && !listed.OrderBy(x => x, StringComparer.Ordinal).SequenceEqual(where.OrderBy(x => x, StringComparer.Ordinal)))
                errors.Add($"{path}.rooms: [{string.Join(", ", listed)}] but the character stands in [{string.Join(", ", where)}] (leave rooms out: it is derived)");
            effectiveCharacters.Add(c with { Rooms = where });
            info.AddedCharacters.Add(c.Id);
        }
        // Items: the one action that gives a new item is its origin.
        var effectiveItems = data.Items.ToList();
        foreach (var (item, origin, path) in newItems)
        {
            var givers = newActions.Where(a => a.Def.Gives.Contains(item.Id)).Select(a => a.Def.Id).ToList();
            if (givers.Count == 0) { errors.Add($"{path}: no action gives item '{item.Id}'"); continue; }
            if (givers.Count > 1) errors.Add($"{path}: item '{item.Id}' is given by {string.Join(" and ", givers)}; an item has exactly one origin");
            if (origin is not null && origin != givers[0]) errors.Add($"{path}.origin: '{origin}' but '{givers[0]}' gives the item");
            effectiveItems.Add(item with { Origin = givers[0] });
            info.AddedItems.Add(item.Id);
        }
        // Quests: a new side quest consists of exactly its new actions, in canonical order.
        foreach (var (q, path) in newQuests)
        {
            var mine = newActions.Where(a => a.Def.Quest == q.Id).Select(a => a.Def.Id).ToList();
            foreach (var missing in mine.Where(a => !q.Actions.Contains(a))) errors.Add($"{path}.actions: '{missing}' has quest '{q.Id}' but is not listed");
            foreach (var wrong in q.Actions.Where(a => newActions.Any(n => n.Def.Id == a && n.Def.Quest != q.Id))) errors.Add($"{path}.actions: '{wrong}' belongs to quest '{actions[wrong].Quest}'");
            info.AddedQuests.Add(q.Id);
        }
        info.AddedActions.AddRange(newActions.Select(a => a.Def.Id));

        var result = data with
        {
            Rooms = effectiveRooms,
            Characters = effectiveCharacters,
            Items = effectiveItems,
            Actions = effectiveActions,
            Quests = data.Quests.Concat(newQuests.Select(q => q.Def)).ToList(),
            Connections = connections,
            Epilogue = data.Epilogue.Concat(newEpilogue).ToList(),
            VisualVariantLayers = data.VisualVariantLayers.Concat(newLayers).ToList(),
        };
        if (errors.Count > errorCount) return data;

        CheckEdges(rp, connections, exitsByRoom, addedConnections, addedExits, errors);
        CheckReachable(rp, result, "cannot be reached", errors);
        var touched = new HashSet<string>(newActions.Select(a => a.Def.Id).Concat(relocated.Keys), StringComparer.Ordinal);
        CheckItemFlow(rp, result, touched, newItems.Select(i => i.Def.Id).ToHashSet(StringComparer.Ordinal), errors);
        CheckDefaultActions(rp, result, touched, errors);
        return errors.Count > errorCount ? data : result;
    }

    // ------------------------------------------------------------------ world overlay checks

    /// <summary>
    /// Items flow: every item an overlay action needs (required, selected or the combine target) is obtainable before
    /// it (initial inventory, the postgame return or an action that does not itself depend on this one); a new item is
    /// consumed at most once; an item consumed by one action and needed by another leaves the other possible (the
    /// consumer requires it first), so no order of play can lose a needed item.
    /// </summary>
    private static void CheckItemFlow(string rp, GameData d, IReadOnlySet<string> touched, IReadOnlySet<string> newItems, List<string> errors)
    {
        var actions = d.Actions.ToDictionary(a => a.Id, StringComparer.Ordinal);
        var initial = new HashSet<string>(StringComparer.Ordinal);
        if (d.InitialState?["inventory"] is JsonArray inv) foreach (var n in inv) if (n is JsonValue v && v.TryGetValue<string>(out var s)) initial.Add(s);
        var closure = DependencyClosure(d);
        foreach (var a in d.Actions.Where(a => touched.Contains(a.Id)))
        {
            foreach (var item in Needs(a).Distinct())
            {
                if (initial.Contains(item)) continue;
                var givers = d.Actions.Where(g => g.Gives.Contains(item)).ToList();
                if (d.Postgame.ReturnItems.Contains(item) && actions.ContainsKey(d.Postgame.Unlock)) givers.Add(actions[d.Postgame.Unlock]);
                if (givers.Count == 0) { errors.Add($"{rp}.actions({a.Id}): item '{item}' can never be obtained (no action gives it)"); continue; }
                if (givers.All(g => g.Id == a.Id || closure[g.Id].Contains(a.Id)))
                    errors.Add($"{rp}.actions({a.Id}): item '{item}' comes only from {string.Join(", ", givers.Select(g => g.Id))}, which needs '{a.Id}' first (a cycle)");
            }
        }
        foreach (var item in newItems)
        {
            var consumers = d.Actions.Where(c => c.Consumes.Contains(item)).Select(c => c.Id).ToList();
            if (consumers.Count > 1) errors.Add($"{rp}.items({item}): consumed by {string.Join(" and ", consumers)}; an item that exists once is consumed once");
        }
        foreach (var c in d.Actions)
        {
            foreach (var item in c.Consumes)
            {
                foreach (var b in d.Actions.Where(b => b.Id != c.Id && (touched.Contains(b.Id) || touched.Contains(c.Id)) && Needs(b).Contains(item)))
                {
                    if (closure[c.Id].Contains(b.Id) || b.ExcludedDone.Contains(c.Id) || c.ExcludedDone.Contains(b.Id)) continue;
                    if (d.Postgame.ReturnItems.Contains(item) && closure[b.Id].Contains(d.Postgame.Unlock)) continue;
                    errors.Add($"{rp}.actions({b.Id}): needs '{item}', which '{c.Id}' consumes; done first, '{c.Id}' would make '{b.Id}' impossible " +
                               $"(let '{c.Id}' require '{b.Id}', or give '{b.Id}' its own item)");
                }
            }
        }
    }

    /// <summary>
    /// One logical action per target: two actions with the same trigger (the same hotspot clicked without an item, the
    /// same item on the same hotspot, the same pair of items in the bag) must never be possible at the same time, i.e.
    /// one requires (or excludes) the other. Topics are menu entries and may share their NPC.
    /// </summary>
    private static void CheckDefaultActions(string rp, GameData d, IReadOnlySet<string> touched, List<string> errors)
    {
        var closure = DependencyClosure(d);
        IEnumerable<string> Triggers(ActionDef a)
        {
            if (a.IsTopic) yield break;
            if (a.IsCombine)
            {
                yield return $"combine:{a.Target}+{a.SelectedItem}";
                if (a.Symmetric) yield return $"combine:{a.SelectedItem}+{a.Target}";
                yield break;
            }
            yield return $"click:{a.Target}+{a.SelectedItem ?? "-"}";
        }
        var byTrigger = d.Actions.SelectMany(a => Triggers(a).Select(t => (Trigger: t, Action: a))).GroupBy(x => x.Trigger, StringComparer.Ordinal);
        var reported = new HashSet<string>(StringComparer.Ordinal);
        foreach (var group in byTrigger)
        {
            var list = group.Select(x => x.Action).Distinct().ToList();
            for (var i = 0; i < list.Count; i++)
                for (var j = i + 1; j < list.Count; j++)
                {
                    var (a, b) = (list[i], list[j]);
                    if (!touched.Contains(a.Id) && !touched.Contains(b.Id)) continue;
                    if (closure[a.Id].Contains(b.Id) || closure[b.Id].Contains(a.Id) || a.ExcludedDone.Contains(b.Id) || b.ExcludedDone.Contains(a.Id)) continue;
                    if (!reported.Add(string.CompareOrdinal(a.Id, b.Id) < 0 ? a.Id + "|" + b.Id : b.Id + "|" + a.Id)) continue;
                    errors.Add($"{rp}.actions({(touched.Contains(b.Id) ? b.Id : a.Id)}): '{a.Id}' and '{b.Id}' have the same trigger ({group.Key}) and could both be " +
                               "possible at once; one must require the other, or use another item / target");
                }
        }
    }

    /// <summary>The items an action needs: required, selected, and the target of a combination.</summary>
    private static IEnumerable<string> Needs(ActionDef a)
    {
        foreach (var i in a.RequiresItems) yield return i;
        if (a.SelectedItem is not null) yield return a.SelectedItem;
        if (a.IsCombine) yield return a.Target;
    }

    /// <summary>
    /// Every action's transitive "happens after" set: its requires_done and the one action giving each item it needs,
    /// recursively (every item has exactly one origin, so an action can never happen before the giver of its item).
    /// </summary>
    private static Dictionary<string, HashSet<string>> DependencyClosure(GameData d)
    {
        var actions = d.Actions.ToDictionary(a => a.Id, StringComparer.Ordinal);
        var giver = d.Actions.SelectMany(a => a.Gives.Select(i => (Item: i, a.Id))).GroupBy(x => x.Item, StringComparer.Ordinal)
            .Where(g => g.Count() == 1).ToDictionary(g => g.Key, g => g.First().Id, StringComparer.Ordinal);
        IEnumerable<string> Direct(string id) => actions.TryGetValue(id, out var a)
            ? a.RequiresDone.Concat(Needs(a).Where(giver.ContainsKey).Select(i => giver[i]))
            : Enumerable.Empty<string>();
        var result = new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);
        foreach (var a in d.Actions)
        {
            // Breadth-first per action, so a cycle shows up as the action being its own prerequisite.
            var set = new HashSet<string>(StringComparer.Ordinal);
            var queue = new Queue<string>(Direct(a.Id));
            while (queue.Count > 0)
            {
                var next = queue.Dequeue();
                if (!set.Add(next)) continue;
                foreach (var n in Direct(next)) queue.Enqueue(n);
            }
            result[a.Id] = set;
        }
        return result;
    }

    // ------------------------------------------------------------------ world overlay helpers

    private static HashSet<string> PreScanIds(JsonObject root, string key)
    {
        var ids = new HashSet<string>(StringComparer.Ordinal);
        if (root[key] is JsonArray arr)
            foreach (var n in arr)
                if (n is JsonObject o && o["id"] is JsonValue v && v.TryGetValue<string>(out var id)) ids.Add(id);
        return ids;
    }

    /// <summary>The objects of a list field with their paths (a non-object entry is an error).</summary>
    private static IEnumerable<(JsonObject Entry, string Path)> Entries(JsonObject parent, string key, string path, List<string> errors)
    {
        var arr = Arr(parent, key, path, errors);
        if (arr is null) yield break;
        for (var i = 0; i < arr.Count; i++)
        {
            var p = $"{path}.{key}[{i}]";
            if (arr[i] is JsonObject o) yield return (o, p);
            else errors.Add($"{p}: must be an object");
        }
    }

    /// <summary>A player-visible text: a non-empty string on one line.</summary>
    private static string? Text(JsonObject o, string key, string path, List<string> errors, bool required = true)
    {
        var t = Str(o, key, path, errors, required);
        if (t is null) return null;
        if (string.IsNullOrWhiteSpace(t)) { errors.Add($"{path}.{key}: empty text"); return null; }
        if (t.IndexOfAny(new[] { '\n', '\r' }) >= 0) { errors.Add($"{path}.{key}: one text is one line; no line breaks"); return null; }
        if (t != t.Trim()) errors.Add($"{path}.{key}: leading or trailing spaces");
        return t;
    }

    private static List<IReadOnlyList<int>>? Polygon(JsonObject o, string key, string path, List<string> errors)
    {
        var arr = Arr(o, key, path, errors, required: true);
        if (arr is null) return null;
        var points = new List<IReadOnlyList<int>>();
        foreach (var n in arr)
        {
            if (n is JsonArray pt && pt.Count == 2 && pt[0] is JsonValue x && x.TryGetValue<int>(out var px) && pt[1] is JsonValue y && y.TryGetValue<int>(out var py))
                points.Add(new[] { px, py });
            else { errors.Add($"{path}.{key}: must be a list of [x, y] integer points"); return null; }
        }
        if (points.Count < 3) { errors.Add($"{path}.{key}: at least 3 points"); return null; }
        if (points.Any(pt => !OnCanvas(pt))) { errors.Add($"{path}.{key}: every point lies inside the {CanvasWidth}x{CanvasHeight} frame"); return null; }
        return points;
    }

    private static bool OnCanvas(IReadOnlyList<int> p) => p[0] >= 0 && p[0] <= CanvasWidth && p[1] >= 0 && p[1] <= CanvasHeight;

    private static void CheckRect(IReadOnlyList<int> r, string path, List<string> errors)
    {
        if (r[2] < MinTarget || r[3] < MinTarget) { errors.Add($"{path}: at least {MinTarget}x{MinTarget} px (got {r[2]}x{r[3]})"); return; }
        var w = Math.Min(r[0] + r[2], CanvasWidth) - Math.Max(r[0], 0);
        var h = Math.Min(r[1] + r[3], CanvasHeight) - Math.Max(r[1], 0);
        if (w < MinTarget || h < MinTarget) errors.Add($"{path}: at least {MinTarget}x{MinTarget} px of it on screen");
    }

    /// <summary>Point in polygon (even-odd); a point on the outline counts as inside.</summary>
    internal static bool InsidePolygon(IReadOnlyList<IReadOnlyList<int>> poly, double x, double y)
    {
        var inside = false;
        for (int i = 0, j = poly.Count - 1; i < poly.Count; j = i++)
        {
            double xi = poly[i][0], yi = poly[i][1], xj = poly[j][0], yj = poly[j][1];
            var cross = (x - xi) * (yj - yi) - (y - yi) * (xj - xi);
            if (Math.Abs(cross) < 1e-9 && x >= Math.Min(xi, xj) - 1e-9 && x <= Math.Max(xi, xj) + 1e-9 && y >= Math.Min(yi, yj) - 1e-9 && y <= Math.Max(yi, yj) + 1e-9)
                return true;
            if ((yi > y) != (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) inside = !inside;
        }
        return inside;
    }
}
