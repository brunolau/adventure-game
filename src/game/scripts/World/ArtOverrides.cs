using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Godot;

namespace LastBell.Game.World;

/// <summary>Visual adjustments of one hotspot or exit (never logic: interaction points stay as in game.json).</summary>
/// <param name="RectNudge">[dx, dy, dw, dh] added to the hit/outline rect, each clamped to ±40 px.</param>
/// <param name="LabelAnchor">Absolute label anchor replacing the game.json one, or null.</param>
/// <param name="LabelOffset">Offset added to the label anchor.</param>
public sealed record TargetOverride(Vector4 RectNudge, Vector2? LabelAnchor, Vector2 LabelOffset);

/// <summary>
/// A painted state patch: a small picture drawn over the background at <paramref name="Position"/>
/// (top-left, canvas px) while all <paramref name="After"/> actions are done and none of
/// <paramref name="Until"/> is (e.g. the empty shelf after the bag was taken, ISSUES ART-VAR-01).
/// Visual only and immediate (the hero changed the prop himself); story-level changes stay in
/// game.json visual_variant_layers.
/// </summary>
/// <param name="Texture">Asset path relative to res://assets/.</param>
/// <param name="Position">Top-left canvas position.</param>
/// <param name="After">Action ids that must all be done.</param>
/// <param name="Until">Action ids of which none may be done.</param>
public sealed record StatePatch(string Texture, Vector2 Position, IReadOnlyList<string> After, IReadOnlyList<string> Until);

/// <summary>Visual adjustments of one room.</summary>
public sealed class RoomOverride
{
    /// <summary>Actor scale at the top and at the bottom of the walk band (default 0.80 → 1.00).</summary>
    public Vector2? ActorScale { get; init; }

    /// <summary>Walk band [top y, bottom y] used for perspective (default: walk polygon extent).</summary>
    public Vector2? WalkBand { get; init; }

    /// <summary>Foreground mask asset relative to res://assets/ (default fg/&lt;room&gt;.webp).</summary>
    public string? ForegroundMask { get; init; }

    /// <summary>Per-hotspot / per-exit overrides by id.</summary>
    public IReadOnlyDictionary<string, TargetOverride> Targets { get; init; } = new Dictionary<string, TargetOverride>();

    /// <summary>NPC feet nudges [dx, dy] by hotspot id (clamped to ±40 px).</summary>
    public IReadOnlyDictionary<string, Vector2> NpcFeet { get; init; } = new Dictionary<string, Vector2>();

    /// <summary>State patches drawn above the background (see <see cref="StatePatch"/>).</summary>
    public IReadOnlyList<StatePatch> StatePatches { get; init; } = Array.Empty<StatePatch>();
}

/// <summary>
/// Loader for <c>res://data/art_overrides.json</c>: visual-only corrections the art pass may need
/// (label anchors, rect nudges ≤ 40 px, per-room actor scale range, foreground mask path). Logic
/// coordinates in game.json are never edited. A missing or broken file means "no overrides".
/// Schema (all fields optional):
/// <code>
/// { "version": 1,
///   "defaults": { "actor_scale": [0.80, 1.00] },
///   "rooms": { "S01": { "actor_scale": [0.78, 1.0], "walk_band": [790, 1015], "foreground_mask": "fg/S01.webp",
///                        "targets": { "S01.tools": { "rect_nudge": [0, -12, 0, 10], "label_anchor": [180, 128], "label_offset": [0, 0] } },
///                        "npc_feet": { "S02.ROMAN": [6, 0] },
///                        "state_patches": [ { "texture": "variants/S01_tools_taken.webp", "pos": [150, 140], "after": ["G01"], "until": [] } ] } } }
/// </code>
/// </summary>
public sealed class ArtOverrides
{
    /// <summary>Path of the overrides file.</summary>
    public const string Path = "res://data/art_overrides.json";

    /// <summary>Largest allowed visual nudge in px (ART_DIRECTION.md section 4).</summary>
    public const float MaxNudge = 40f;

    private readonly Dictionary<string, RoomOverride> rooms = new(StringComparer.Ordinal);

    /// <summary>Default actor scale range (top, bottom of the walk band).</summary>
    public Vector2 DefaultActorScale { get; private set; } = new(0.80f, 1.00f);

    /// <summary>Overrides of a room (an empty instance when none).</summary>
    public RoomOverride For(string roomId) => rooms.TryGetValue(roomId, out var r) ? r : Empty;

    private static readonly RoomOverride Empty = new();

    /// <summary>Loads the file (or returns empty overrides).</summary>
    public static ArtOverrides Load()
    {
        var result = new ArtOverrides();
        if (!Godot.FileAccess.FileExists(Path)) return result;
        try
        {
            var root = JsonNode.Parse(Godot.FileAccess.GetFileAsString(Path)) as JsonObject;
            if (root is null) return result;
            if (root["defaults"]?["actor_scale"] is JsonArray ds && ReadVec2(ds) is { } d) result.DefaultActorScale = d;
            if (root["rooms"] is JsonObject roomsNode)
            {
                foreach (var (roomId, value) in roomsNode)
                {
                    if (value is not JsonObject r) continue;
                    var targets = new Dictionary<string, TargetOverride>(StringComparer.Ordinal);
                    if (r["targets"] is JsonObject t)
                    {
                        foreach (var (id, tv) in t)
                        {
                            if (tv is not JsonObject o) continue;
                            var nudge = o["rect_nudge"] is JsonArray n && n.Count == 4
                                ? new Vector4(Clamp(n[0]), Clamp(n[1]), Clamp(n[2]), Clamp(n[3])) : Vector4.Zero;
                            Vector2? anchor = o["label_anchor"] is JsonArray la ? ReadVec2(la) : null;
                            var offset = o["label_offset"] is JsonArray lo && ReadVec2(lo) is { } ov ? ov : Vector2.Zero;
                            targets[id] = new TargetOverride(nudge, anchor, offset);
                        }
                    }
                    var feet = new Dictionary<string, Vector2>(StringComparer.Ordinal);
                    if (r["npc_feet"] is JsonObject f)
                    {
                        foreach (var (id, fv) in f)
                            if (fv is JsonArray fa && ReadVec2(fa) is { } v) feet[id] = new Vector2(Mathf.Clamp(v.X, -MaxNudge, MaxNudge), Mathf.Clamp(v.Y, -MaxNudge, MaxNudge));
                    }
                    var patches = new List<StatePatch>();
                    if (r["state_patches"] is JsonArray sp)
                    {
                        foreach (var pv in sp)
                        {
                            if (pv is not JsonObject po || po["texture"]?.GetValue<string>() is not { } tex) continue;
                            var pos = po["pos"] is JsonArray pa && ReadVec2(pa) is { } pp ? pp : Vector2.Zero;
                            patches.Add(new StatePatch(tex, pos, ReadStrings(po["after"]), ReadStrings(po["until"])));
                        }
                    }
                    result.rooms[roomId] = new RoomOverride
                    {
                        StatePatches = patches,
                        ActorScale = r["actor_scale"] is JsonArray a ? ReadVec2(a) : null,
                        WalkBand = r["walk_band"] is JsonArray wb ? ReadVec2(wb) : null,
                        ForegroundMask = r["foreground_mask"]?.GetValue<string>(),
                        Targets = targets,
                        NpcFeet = feet,
                    };
                }
            }
        }
        catch (Exception ex) when (ex is JsonException or InvalidOperationException or FormatException)
        {
            GD.PushWarning($"{Path}: ignored ({ex.Message})");
        }
        return result;
    }

    private static float Clamp(JsonNode? n)
    {
        float v = n is null ? 0f : (float)n.GetValue<double>();
        if (Mathf.Abs(v) > MaxNudge) GD.PushWarning($"{Path}: nudge {v} clamped to ±{MaxNudge}px");
        return Mathf.Clamp(v, -MaxNudge, MaxNudge);
    }

    private static IReadOnlyList<string> ReadStrings(JsonNode? n) =>
        n is JsonArray a ? a.Where(x => x is not null).Select(x => x!.GetValue<string>()).ToList() : Array.Empty<string>();

    private static Vector2? ReadVec2(JsonArray a) =>
        a.Count >= 2 && a[0] is not null && a[1] is not null ? new Vector2((float)a[0]!.GetValue<double>(), (float)a[1]!.GetValue<double>()) : null;
}
