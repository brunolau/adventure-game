using System;
using System.Collections.Generic;
using Godot;

namespace LastBell.Game.Living.Actors;

/// <summary>How one NPC is staged in one room (window busts, scale).</summary>
/// <param name="Variant">actor.json variant name (window_glass, window) or null for the default.</param>
/// <param name="SillY">Canvas y of the painted window sill the bust stands on (window variants).</param>
/// <param name="Scale">Absolute sprite scale instead of the room perspective (null = perspective).</param>
/// <param name="OffsetX">Horizontal nudge in canvas px.</param>
/// <param name="Facing">Fixed facing: "left", "right" or null (face the hero).</param>
public sealed record ActorPlacement(string? Variant, float? SillY, float? Scale, float OffsetX, string? Facing);

/// <summary>
/// Visual staging data for actor sprites, from <c>res://data/ambient/actors.json</c>: in which rooms
/// the hero wears the 2020 face mask (game.json has no flag, ISSUES ART-ADAM-02), per-room NPC
/// placements (window busts) and walk tuning. Visual only; never affects rules.
/// </summary>
public static class ActorStaging
{
    /// <summary>Data file path.</summary>
    public const string Path = "res://data/ambient/actors.json";

    private static bool loaded;
    private static readonly HashSet<string> MaskRooms = new(StringComparer.Ordinal);
    private static readonly Dictionary<string, ActorPlacement> Placements = new(StringComparer.Ordinal);

    /// <summary>Depth walk speed (toward / away cycles) as a fraction of the side stride.</summary>
    public static float DepthSpeedFactor { get; private set; } = 0.3f;

    /// <summary>Seconds a one-shot action holds its last frame before playing back to idle.</summary>
    public static float ActionHoldSeconds { get; private set; } = 0.45f;

    /// <summary>Per-animation hold overrides (show_item holds longer so the item reads).</summary>
    public static IReadOnlyDictionary<string, float> ActionHolds => holds;

    private static readonly Dictionary<string, float> holds = new(StringComparer.Ordinal);

    /// <summary>Probability that one 4 s hero idle loop contains its blink (random blinking).</summary>
    public static float HeroBlinkChance { get; private set; } = 0.7f;

    private static void EnsureLoaded()
    {
        if (loaded) return;
        loaded = true;
        var data = Json.Load(Path, warnIfMissing: false);
        if (data is null) return;
        foreach (var room in data.Strings("hero_mask2020_rooms")) MaskRooms.Add(room);
        DepthSpeedFactor = data.Num("depth_speed_factor", DepthSpeedFactor);
        ActionHoldSeconds = data.Num("action_hold_s", ActionHoldSeconds);
        HeroBlinkChance = data.Num("hero_blink_chance", HeroBlinkChance);
        if (data.Obj("action_hold_overrides_s") is { } o)
            foreach (var (k, _) in o) holds[k] = o.Num(k, ActionHoldSeconds);
        if (data.Obj("placements") is { } rooms)
        {
            foreach (var (roomId, node) in rooms)
            {
                if (node is not System.Text.Json.Nodes.JsonObject chars) continue;
                foreach (var (charId, pnode) in chars)
                {
                    if (pnode is not System.Text.Json.Nodes.JsonObject p) continue;
                    Placements[roomId + "/" + charId] = new ActorPlacement(p.Str("variant"), p.NumOrNull("sill_y"), p.NumOrNull("scale"),
                        p.Num("offset_x"), p.Str("facing"));
                }
            }
        }
    }

    /// <summary>True when the hero wears the 2020 face mask in the room.</summary>
    public static bool HeroWearsMask(string roomId, int era)
    {
        EnsureLoaded();
        return era == 2020 && MaskRooms.Contains(roomId);
    }

    /// <summary>Staging of a character in a room, or null.</summary>
    public static ActorPlacement? PlacementFor(string roomId, string characterId)
    {
        EnsureLoaded();
        return Placements.TryGetValue(roomId + "/" + characterId, out var p) ? p : null;
    }

    /// <summary>Hold seconds for a one-shot action.</summary>
    public static float HoldFor(string animation)
    {
        EnsureLoaded();
        return holds.TryGetValue(animation, out var s) ? s : ActionHoldSeconds;
    }
}
