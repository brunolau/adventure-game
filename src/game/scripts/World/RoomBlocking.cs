using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Godot;
using LastBell.Game.Runtime;

namespace LastBell.Game.World;

/// <summary>Presentation geometry of one hotspot or exit in a natural blocking (null = keep game.json).</summary>
/// <param name="Rect">Hit / outline rect.</param>
/// <param name="InteractionPoint">Walk target.</param>
/// <param name="LabelAnchor">Space label anchor.</param>
public sealed record BlockingTarget(Rect2? Rect, Vector2? InteractionPoint, Vector2? LabelAnchor);

/// <summary>How an NPC is drawn relative to the hero, the occluders and the y-sorted ambient sprites.</summary>
public enum NpcDepth
{
    /// <summary>Y-sorted by the feet with the hero, the occluders and the y-sorted ambient layers (default).</summary>
    Auto,
    /// <summary>Always behind the hero and every occluder (a bust inside a window, a figure deep in a doorway).</summary>
    Back,
    /// <summary>Always in front of the hero and every occluder, still below the foreground mask.</summary>
    Front,
}

/// <summary>Staging of one NPC in a natural blocking (replaces data/ambient/actors.json's placement for this room).</summary>
/// <param name="Feet">Feet centre in canvas px (null = bottom centre of the hotspot rect).</param>
/// <param name="Scale">Absolute actor scale (null = room perspective at the feet).</param>
/// <param name="Variant">Staging name as written in the file: <c>standing</c>, <c>seated</c>, <c>behind_counter</c>,
/// <c>window_bust</c>, <c>window_bust_glass</c> or any variant name of the actor's <c>actor.json</c>; resolved by
/// <c>ActorAnimationSet.ResolveStaging</c> (null = the manifest default).</param>
/// <param name="SillY">Canvas y of the painted cut line (window sill, counter or table top) a bust variant stands on.</param>
/// <param name="OffsetX">Horizontal nudge of the sprite in canvas px.</param>
/// <param name="Facing">"left", "right" or null (face the room centre / the hero).</param>
/// <param name="Depth">Draw order relative to the hero and the occluders.</param>
/// <param name="ApproachGap">Gap in px between the NPC rect and the hero standing beside it (null = <see cref="Room.NpcApproachGap"/>;
/// larger for a child, so a show_item gesture does not reach into the face, playtest PT-S24).</param>
public sealed record BlockingNpc(Vector2? Feet, float? Scale, string? Variant = null, float? SillY = null, float OffsetX = 0f,
    string? Facing = null, NpcDepth Depth = NpcDepth.Auto, float? ApproachGap = null);

/// <summary>
/// A guest speaker of one action (game.json <c>actions[].staging.rule</c>, ISSUES PT-S18): a character who speaks the
/// action's lines but does not stand in the room. The presentation walks a temporary actor in from
/// <paramref name="Enter"/> (the nearest exit) to <paramref name="Stand"/>, plays the lines and walks it out again.
/// Never a Core NPC: no hotspot, no rules, no save state.
/// </summary>
/// <param name="CharacterId">Speaker id of the lines (game.json characters[].id).</param>
/// <param name="Enter">Where the guest appears and leaves (may lie off screen or outside the walk polygon).</param>
/// <param name="Stand">Feet position while the lines play (walkable floor).</param>
/// <param name="Variant">Staging / actor.json variant (null = the manifest default).</param>
/// <param name="Facing">"left", "right" or null (face the hero).</param>
/// <param name="Delay">Seconds after the commit before this guest starts walking (two guests do not walk in a clump).</param>
public sealed record BlockingGuest(string CharacterId, Vector2 Enter, Vector2 Stand, string? Variant, string? Facing, float Delay);

/// <summary>
/// The painted clock (or device) of an anchor node that opens the era chooser like the HUD clock button (playtest
/// PT-F10, DECISIONS "The painted S11 clock is the time node"). Either its own presentation rect (a clock painted
/// without a game.json hotspot) or <paramref name="HotspotId"/>, a game.json hotspot whose plain left click (no item
/// selected, Core resolves a look) opens the chooser instead. Active only while Core lists portal targets here.
/// </summary>
/// <param name="Rect">Hit rect (ignored when <paramref name="HotspotId"/> is set: the hotspot's rect is used).</param>
/// <param name="InteractionPoint">Where the hero walks before the chooser opens (null = the hotspot's point).</param>
/// <param name="HotspotId">game.json hotspot that doubles as the node, or null.</param>
public sealed record BlockingTimeNode(Rect2? Rect, Vector2? InteractionPoint, string? HotspotId);

/// <summary>
/// A piece of the painting that is drawn in front of actors standing behind it (a counter front, a pillar, a
/// bench back): the <paramref name="Polygon"/> of <paramref name="Texture"/> (a full-frame 1920x1080 image,
/// null = the room's background painting), y-sorted with the actors at <paramref name="BaselineY"/> (actors whose
/// feet are above that line are hidden behind it, actors below it walk in front of it).
/// </summary>
/// <param name="Id">Name (debug).</param>
/// <param name="Polygon">Canvas polygon.</param>
/// <param name="BaselineY">Sort line: the canvas y where the object stands on the floor.</param>
/// <param name="Texture">Full-frame asset relative to res://assets/ (null = the background painting).</param>
public sealed record BlockingOccluder(string Id, IReadOnlyList<Vector2> Polygon, float BaselineY, string? Texture);

/// <summary>
/// The natural replacement of one game.json <c>visual_variant_layers</c> asset: a full-frame overlay
/// (<paramref name="Position"/> null) or a smaller patch at a canvas position; <paramref name="Texture"/> null = draw
/// nothing (the natural painting needs no overlay for this change; the file says why).
/// </summary>
/// <param name="Texture">Asset relative to res://assets/, or null.</param>
/// <param name="Position">Top-left canvas position of a patch, or null for a full-frame overlay.</param>
public sealed record BlockingVariantLayer(string? Texture, Vector2? Position);

/// <summary>Presentation-only audio of a natural room (e.g. the bus at the 1982 stop S57).</summary>
/// <param name="AmbienceLayers">Layers in the data/audio/ambience.json room schema, or null = keep ambience.json.</param>
/// <param name="AddToTemplate">true: the layers are added to ambience.json's; false: they replace them.</param>
/// <param name="Music">Music asset or cue replacing rooms[].music (music.json room overrides still win), or null.</param>
public sealed record BlockingAudio(JsonArray? AmbienceLayers, bool AddToTemplate, string? Music);

/// <summary>
/// Natural re-blocking of a room (<c>res://data/blocking/&lt;room&gt;.json</c>): presentation-only
/// geometry that replaces the game.json template rects, interaction points, label anchors, walk
/// polygon, exit zones, NPC staging and the perspective range, plus the painting, foreground mask,
/// occluders, state overlays, ambient layers and audio made for it. Ids, conditions and every rule stay
/// in game.json / Core: Core never reads positions. Applied per room when <see cref="Enabled"/> (project
/// setting <c>last_bell/presentation/blocking</c> = <c>"natural"</c>, or the QA flag
/// <c>--blocking natural</c>): a room with a blocking file uses it, a room without one keeps the template.
/// When a blocking applies, the room's template-painting data is ignored (art_overrides.json nudges,
/// npc_feet, state patches and perspective; data/ambient/actors.json placements; data/ambient/&lt;room&gt;.json;
/// the template visual_variant_layers assets), because it belongs to the template painting.
/// Schema (all fields optional except <c>room</c>; validator tools/check_blocking.py, recipe art/tools/PAINTING.md):
/// <code>
/// { "version": 1, "room": "S05", "background": "bg_natural/S05.webp",
///   "walk_polygon": [[x, y], ...], "walk_band": [top, bottom], "actor_scale": [top, bottom], "spawn": [x, y],
///   "hotspots": { "S05.tray": { "rect": [x, y, w, h], "interaction_point": [x, y], "label_anchor": [x, y] } },
///   "exits":    { "S05.to_S02": { "rect": [...], "interaction_point": [...], "label_anchor": [...] } },
///   "npcs":     { "S13.TONO": { "feet": [x, y], "scale": 0.6, "variant": "seated", "sill_y": 600, "offset_x": 0,
///                               "facing": "left", "z": "auto|back|front", "approach_gap": 140 } },
///   "guests":   { "I17": [ { "character": "MIRA60", "enter": [x, y], "stand": [x, y], "variant": null,
///                            "facing": "right", "delay": 0 } ] },
///   "time_node": { "rect": [x, y, w, h], "interaction_point": [x, y] }   or   { "hotspot": "S51.clock" },
///   "foreground_mask": "fg_natural/S05.webp",
///   "occluders": [ { "id": "counter", "polygon": [[x, y], ...], "baseline": 700, "texture": null } ],
///   "variant_layers": { "variants/S17_healthy_linden.webp": "variants_natural/S17_healthy_linden.webp",
///                       "variants/S55_linden_and_wall.webp": { "texture": "variants_natural/S55_linden.webp", "pos": [x, y] },
///                       "variants/S06_family_restored.webp": null },
///   "state_patches": [ { "texture": "variants_natural/...", "pos": [x, y], "after": ["G04"], "until": [] } ],
///   "ambient": "res://data/blocking/ambient/S05.json",
///   "audio": { "ambience": [ { "sound": "bus_pass", "db": -6, "every": [20, 40] } ], "ambience_mode": "replace|add",
///              "music": "music/1982.ogg" } }
/// </code>
/// </summary>
public sealed class RoomBlocking
{
    /// <summary>Folder of the blocking files.</summary>
    public const string Folder = "res://data/blocking/";

    /// <summary>Project setting that turns natural blocking on ("natural", default since milestone 3) or off ("template").</summary>
    public const string ProjectSetting = "last_bell/presentation/blocking";

    private static readonly Dictionary<string, RoomBlocking?> Cache = new(StringComparer.Ordinal);

    /// <summary>True when natural blockings are applied (harness flag first, then the project setting).</summary>
    public static bool Enabled =>
        PresentationSettings.NaturalBlocking ??
        string.Equals(ProjectSettings.GetSetting(ProjectSetting, "template").AsString(), "natural", StringComparison.OrdinalIgnoreCase);

    /// <summary>Room id.</summary>
    public string RoomId { get; private init; } = "";

    /// <summary>Background asset relative to res://assets/ (default: the convention bg_natural/&lt;room&gt;.webp; a
    /// missing file shows the dev blockout, never the template painting, whose geometry does not match).</summary>
    public string? Background { get; private init; }

    /// <summary>Walk polygon replacing game.json's (null = keep).</summary>
    public IReadOnlyList<IReadOnlyList<int>>? WalkPolygon { get; private init; }

    /// <summary>Perspective band [top y, bottom y] (null = walk polygon extent).</summary>
    public Vector2? WalkBand { get; private init; }

    /// <summary>Actor scale at the top and bottom of the band (null = default 0.80 → 1.00).</summary>
    public Vector2? ActorScale { get; private init; }

    /// <summary>Hero spawn replacing game.json's (null = keep).</summary>
    public Vector2? Spawn { get; private init; }

    /// <summary>Hotspot and exit geometry by id.</summary>
    public IReadOnlyDictionary<string, BlockingTarget> Targets { get; private init; } = new Dictionary<string, BlockingTarget>();

    /// <summary>NPC staging by hotspot id.</summary>
    public IReadOnlyDictionary<string, BlockingNpc> Npcs { get; private init; } = new Dictionary<string, BlockingNpc>();

    /// <summary>Guest speakers by action id (walk-ins, ISSUES PT-S18).</summary>
    public IReadOnlyDictionary<string, IReadOnlyList<BlockingGuest>> Guests { get; private init; } = new Dictionary<string, IReadOnlyList<BlockingGuest>>();

    /// <summary>The painted time-node clock of an anchor-node room, or null (ISSUES PT-F10).</summary>
    public BlockingTimeNode? TimeNode { get; private init; }

    /// <summary>The staging of a guest character in this room (any action), or null.</summary>
    public BlockingGuest? GuestFor(string characterId) =>
        Guests.Values.SelectMany(g => g).FirstOrDefault(g => g.CharacterId == characterId);

    /// <summary>Foreground mask asset relative to res://assets/ (null = the convention fg_natural/&lt;room&gt;.webp).</summary>
    public string? ForegroundMask { get; private init; }

    /// <summary>Ambient data file for the natural painting (null = the convention, see <see cref="AmbientDataPath"/>).</summary>
    public string? AmbientData { get; private init; }

    /// <summary>Ambient data file actually used: <see cref="AmbientData"/> or data/blocking/ambient/&lt;room&gt;.json
    /// (the template's data/ambient/&lt;room&gt;.json is cut from the old painting and never used here).</summary>
    public string AmbientDataPath => AmbientData ?? Folder + "ambient/" + RoomId + ".json";

    /// <summary>State patches drawn over the natural painting.</summary>
    public IReadOnlyList<StatePatch> StatePatches { get; private init; } = Array.Empty<StatePatch>();

    /// <summary>Occluders cut from the painting, y-sorted with the actors.</summary>
    public IReadOnlyList<BlockingOccluder> Occluders { get; private init; } = Array.Empty<BlockingOccluder>();

    /// <summary>Natural replacements of the room's visual_variant_layers, by their game.json asset path.</summary>
    public IReadOnlyDictionary<string, BlockingVariantLayer> VariantLayers { get; private init; } = new Dictionary<string, BlockingVariantLayer>();

    /// <summary>Presentation-only audio override (null = data/audio as for the template).</summary>
    public BlockingAudio? Audio { get; private init; }

    /// <summary>The room's blocking when natural blocking is enabled and a file exists, else null.</summary>
    public static RoomBlocking? For(string roomId)
    {
        if (!Enabled) return null;
        if (Cache.TryGetValue(roomId, out var cached)) return cached;
        var loaded = Load(roomId);
        Cache[roomId] = loaded;
        return loaded;
    }

    /// <summary>The visual overrides to use instead of the template's art_overrides entry.</summary>
    public RoomOverride ToOverride() => new()
    {
        ActorScale = ActorScale,
        WalkBand = WalkBand,
        ForegroundMask = ForegroundMask ?? $"fg_natural/{RoomId}.webp",
        StatePatches = StatePatches,
    };

    /// <summary>Geometry of a target, or null when the blocking keeps game.json's.</summary>
    public BlockingTarget? Target(string id) => Targets.TryGetValue(id, out var t) ? t : null;

    /// <summary>The natural replacement of a visual_variant_layers asset, or null when the file maps none.</summary>
    public BlockingVariantLayer? VariantLayer(string templateAsset) => VariantLayers.TryGetValue(templateAsset, out var v) ? v : null;

    private static RoomBlocking? Load(string roomId)
    {
        string path = Folder + roomId + ".json";
        if (!Godot.FileAccess.FileExists(path)) return null;
        try
        {
            if (JsonNode.Parse(Godot.FileAccess.GetFileAsString(path)) is not JsonObject root) return null;
            var targets = new Dictionary<string, BlockingTarget>(StringComparer.Ordinal);
            foreach (var section in new[] { "hotspots", "exits" })
            {
                if (root[section] is not JsonObject list) continue;
                foreach (var (id, node) in list)
                {
                    if (node is not JsonObject t) continue;
                    targets[id] = new BlockingTarget(ReadRect(t["rect"]), ReadVec2(t["interaction_point"]), ReadVec2(t["label_anchor"]));
                }
            }
            var npcs = new Dictionary<string, BlockingNpc>(StringComparer.Ordinal);
            if (root["npcs"] is JsonObject n)
            {
                foreach (var (id, node) in n)
                {
                    if (node is not JsonObject o) continue;
                    var depth = (o["z"]?.GetValue<string>() ?? "auto").ToLowerInvariant() switch
                    {
                        "back" or "behind" => NpcDepth.Back,
                        "front" => NpcDepth.Front,
                        _ => NpcDepth.Auto,
                    };
                    npcs[id] = new BlockingNpc(ReadVec2(o["feet"]), ReadFloat(o["scale"]), o["variant"]?.GetValue<string>(),
                        ReadFloat(o["sill_y"]), ReadFloat(o["offset_x"]) ?? 0f, o["facing"]?.GetValue<string>(), depth,
                        ReadFloat(o["approach_gap"]));
                }
            }
            var guests = new Dictionary<string, IReadOnlyList<BlockingGuest>>(StringComparer.Ordinal);
            if (root["guests"] is JsonObject g)
            {
                foreach (var (actionId, node) in g)
                {
                    if (node is not JsonArray list) continue;
                    var parsed = new List<BlockingGuest>();
                    foreach (var gv in list)
                    {
                        if (gv is not JsonObject go || go["character"]?.GetValue<string>() is not { } character) continue;
                        if (ReadVec2(go["enter"]) is not { } enter || ReadVec2(go["stand"]) is not { } stand) continue;
                        parsed.Add(new BlockingGuest(character, enter, stand, go["variant"]?.GetValue<string>(), go["facing"]?.GetValue<string>(),
                            ReadFloat(go["delay"]) ?? 0f));
                    }
                    if (parsed.Count > 0) guests[actionId] = parsed;
                }
            }
            BlockingTimeNode? timeNode = null;
            if (root["time_node"] is JsonObject tn)
                timeNode = new BlockingTimeNode(ReadRect(tn["rect"]), ReadVec2(tn["interaction_point"]), tn["hotspot"]?.GetValue<string>());
            var patches = new List<StatePatch>();
            if (root["state_patches"] is JsonArray sp)
            {
                foreach (var pv in sp)
                {
                    if (pv is not JsonObject po || po["texture"]?.GetValue<string>() is not { } tex) continue;
                    patches.Add(new StatePatch(tex, ReadVec2(po["pos"]) ?? Vector2.Zero, ReadStrings(po["after"]), ReadStrings(po["until"])));
                }
            }
            var occluders = new List<BlockingOccluder>();
            if (root["occluders"] is JsonArray oc)
            {
                int index = 0;
                foreach (var ov in oc)
                {
                    index++;
                    if (ov is not JsonObject oo || oo["polygon"] is not JsonArray poly) continue;
                    var points = poly.Select(ReadVec2).Where(p => p is not null).Select(p => p!.Value).ToList();
                    if (points.Count < 3) continue;
                    float baseline = ReadFloat(oo["baseline"]) ?? points.Max(p => p.Y);
                    occluders.Add(new BlockingOccluder(oo["id"]?.GetValue<string>() ?? $"occluder_{index}", points, baseline,
                        oo["texture"]?.GetValue<string>()));
                }
            }
            var variantLayers = new Dictionary<string, BlockingVariantLayer>(StringComparer.Ordinal);
            if (root["variant_layers"] is JsonObject vl)
            {
                foreach (var (asset, node) in vl)
                {
                    variantLayers[asset] = node switch
                    {
                        null => new BlockingVariantLayer(null, null),
                        JsonObject vo => new BlockingVariantLayer(vo["texture"]?.GetValue<string>(), ReadVec2(vo["pos"])),
                        _ => new BlockingVariantLayer(node.GetValue<string>() is { Length: > 0 } t && t != "none" ? t : null, null),
                    };
                }
            }
            BlockingAudio? audio = null;
            if (root["audio"] is JsonObject au)
            {
                audio = new BlockingAudio(au["ambience"] is JsonArray layers ? (JsonArray)layers.DeepClone() : null,
                    string.Equals(au["ambience_mode"]?.GetValue<string>(), "add", StringComparison.OrdinalIgnoreCase),
                    au["music"]?.GetValue<string>());
            }
            List<IReadOnlyList<int>>? polygon = null;
            if (root["walk_polygon"] is JsonArray wp)
            {
                polygon = wp.OfType<JsonArray>().Where(p => p.Count >= 2)
                    .Select(p => (IReadOnlyList<int>)new[] { (int)Math.Round(p[0]!.GetValue<double>()), (int)Math.Round(p[1]!.GetValue<double>()) }).ToList();
                if (polygon.Count < 3) polygon = null;
            }
            return new RoomBlocking
            {
                RoomId = roomId,
                Background = root["background"]?.GetValue<string>() ?? $"bg_natural/{roomId}.webp",
                WalkPolygon = polygon,
                WalkBand = ReadVec2(root["walk_band"]),
                ActorScale = ReadVec2(root["actor_scale"]),
                Spawn = ReadVec2(root["spawn"]),
                Targets = targets,
                Npcs = npcs,
                Guests = guests,
                TimeNode = timeNode,
                ForegroundMask = root["foreground_mask"]?.GetValue<string>(),
                AmbientData = root["ambient"]?.GetValue<string>(),
                StatePatches = patches,
                Occluders = occluders,
                VariantLayers = variantLayers,
                Audio = audio,
            };
        }
        catch (Exception ex) when (ex is JsonException or InvalidOperationException or FormatException)
        {
            GD.PushWarning($"{path}: ignored ({ex.Message})");
            return null;
        }
    }

    private static float? ReadFloat(JsonNode? n) =>
        n is JsonValue v && v.GetValueKind() == JsonValueKind.Number ? (float)v.GetValue<double>() : null;

    private static Rect2? ReadRect(JsonNode? n) =>
        n is JsonArray a && a.Count >= 4 && a.All(v => v is not null)
            ? new Rect2((float)a[0]!.GetValue<double>(), (float)a[1]!.GetValue<double>(), (float)a[2]!.GetValue<double>(), (float)a[3]!.GetValue<double>())
            : null;

    private static Vector2? ReadVec2(JsonNode? n) =>
        n is JsonArray a && a.Count >= 2 && a[0] is not null && a[1] is not null
            ? new Vector2((float)a[0]!.GetValue<double>(), (float)a[1]!.GetValue<double>())
            : null;

    private static IReadOnlyList<string> ReadStrings(JsonNode? n) =>
        n is JsonArray a ? a.Where(x => x is not null).Select(x => x!.GetValue<string>()).ToList() : Array.Empty<string>();
}
