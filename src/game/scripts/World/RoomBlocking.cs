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

/// <summary>Staging of one NPC in a natural blocking.</summary>
/// <param name="Feet">Feet centre in canvas px (null = bottom centre of the hotspot rect).</param>
/// <param name="Scale">Absolute actor scale (null = room perspective at the feet).</param>
public sealed record BlockingNpc(Vector2? Feet, float? Scale);

/// <summary>
/// Natural re-blocking of a room (<c>res://data/blocking/&lt;room&gt;.json</c>): presentation-only
/// geometry that replaces the game.json template rects, interaction points, label anchors, walk
/// polygon, exit zones, NPC feet and the perspective range, plus the background painted for it.
/// Ids, conditions and every rule stay in game.json / Core: Core never reads positions.
/// Applied only when <see cref="Enabled"/> (project setting <c>last_bell/presentation/blocking</c>
/// = <c>"natural"</c>, or the QA flag <c>--blocking natural</c>); default off until the product
/// owner approves it (docs/reblock/README.md). When a blocking applies, the room's
/// <c>art_overrides.json</c> entries (nudges, npc_feet, state patches, perspective) are ignored,
/// because they belong to the template painting; the blocking file carries its own.
/// Schema (all fields optional except <c>room</c>):
/// <code>
/// { "version": 1, "room": "S05", "background": "bg_natural/S05.webp",
///   "walk_polygon": [[x, y], ...], "walk_band": [top, bottom], "actor_scale": [top, bottom], "spawn": [x, y],
///   "hotspots": { "S05.tray": { "rect": [x, y, w, h], "interaction_point": [x, y], "label_anchor": [x, y] } },
///   "exits":    { "S05.to_S02": { "rect": [...], "interaction_point": [...], "label_anchor": [...] } },
///   "npcs":     { "S03.ELA": { "feet": [x, y], "scale": 0.5 } },
///   "foreground_mask": "fg_natural/S05.webp", "ambient": "res://data/blocking/ambient/S05.json",
///   "state_patches": [ { "texture": "...", "pos": [x, y], "after": ["G04"], "until": [] } ] }
/// </code>
/// </summary>
public sealed class RoomBlocking
{
    /// <summary>Folder of the blocking files.</summary>
    public const string Folder = "res://data/blocking/";

    /// <summary>Project setting that turns natural blocking on ("natural") or off ("template", default).</summary>
    public const string ProjectSetting = "last_bell/presentation/blocking";

    private static readonly Dictionary<string, RoomBlocking?> Cache = new(StringComparer.Ordinal);

    /// <summary>True when natural blockings are applied (harness flag first, then the project setting).</summary>
    public static bool Enabled =>
        PresentationSettings.NaturalBlocking ??
        string.Equals(ProjectSettings.GetSetting(ProjectSetting, "template").AsString(), "natural", StringComparison.OrdinalIgnoreCase);

    /// <summary>Room id.</summary>
    public string RoomId { get; private init; } = "";

    /// <summary>Background asset relative to res://assets/ (null = game.json background).</summary>
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

    /// <summary>Foreground mask asset relative to res://assets/ (null = none).</summary>
    public string? ForegroundMask { get; private init; }

    /// <summary>Ambient data file for the natural painting (null = no ambient layers: the template ones are cut from the old painting).</summary>
    public string? AmbientData { get; private init; }

    /// <summary>State patches drawn over the natural painting.</summary>
    public IReadOnlyList<StatePatch> StatePatches { get; private init; } = Array.Empty<StatePatch>();

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
                    if (node is JsonObject o) npcs[id] = new BlockingNpc(ReadVec2(o["feet"]), o["scale"] is JsonValue s ? (float)s.GetValue<double>() : null);
            }
            var patches = new List<StatePatch>();
            if (root["state_patches"] is JsonArray sp)
            {
                foreach (var pv in sp)
                {
                    if (pv is not JsonObject po || po["texture"]?.GetValue<string>() is not { } tex) continue;
                    patches.Add(new StatePatch(tex, ReadVec2(po["pos"]) ?? Vector2.Zero, ReadStrings(po["after"]), ReadStrings(po["until"])));
                }
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
                Background = root["background"]?.GetValue<string>(),
                WalkPolygon = polygon,
                WalkBand = ReadVec2(root["walk_band"]),
                ActorScale = ReadVec2(root["actor_scale"]),
                Spawn = ReadVec2(root["spawn"]),
                Targets = targets,
                Npcs = npcs,
                ForegroundMask = root["foreground_mask"]?.GetValue<string>(),
                AmbientData = root["ambient"]?.GetValue<string>(),
                StatePatches = patches,
            };
        }
        catch (Exception ex) when (ex is JsonException or InvalidOperationException or FormatException)
        {
            GD.PushWarning($"{path}: ignored ({ex.Message})");
            return null;
        }
    }

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
