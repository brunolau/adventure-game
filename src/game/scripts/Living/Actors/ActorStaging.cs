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
/// A per-character sprite variant that applies once an action is done (e.g. Jana's Q9C prop variants,
/// PRIBEH_A_PRAVIDLA "variant rekvizít podľa Q9C", ISSUES ART-AGE-01 item 4 / ART-AGE-04).
/// </summary>
/// <param name="After">Action id that must be in <c>done</c>.</param>
/// <param name="Variant">actor.json variant name; <c>{base}</c> is replaced by the room's / manifest's variant
/// (JANA20: <c>{base}_q9c</c> turns <c>laptop</c> into <c>laptop_q9c</c> and <c>screen</c> into <c>screen_q9c</c>).</param>
public sealed record VariantRule(string After, string Variant);

/// <summary>
/// Visual staging data for actor sprites, from <c>res://data/ambient/actors.json</c>: in which rooms
/// the hero wears the 2020 face mask (game.json has no flag, ISSUES ART-ADAM-02) or his December 1982
/// winter coat (ISSUES PT-S20), per-room NPC placements (window busts) and walk tuning. Visual only;
/// never affects rules.
/// </summary>
public static class ActorStaging
{
    /// <summary>Data file path.</summary>
    public const string Path = "res://data/ambient/actors.json";

    /// <summary>Hero sheet variant of the 2020 face mask (<c>*_mask2020</c> sheets).</summary>
    public const string MaskVariant = "mask2020";

    /// <summary>Hero sheet variant of the December 1982 winter coat and scarf (<c>*_coat1982</c> sheets).</summary>
    public const string CoatVariant = "coat1982";

    private static bool loaded;
    private static readonly HashSet<string> MaskRooms = new(StringComparer.Ordinal);
    private static readonly HashSet<string> CoatRooms = new(StringComparer.Ordinal);
    private static readonly HashSet<string> WinterCoatRooms2035 = new(StringComparer.Ordinal);
    private static readonly Dictionary<string, ActorPlacement> Placements = new(StringComparer.Ordinal);
    private static readonly Dictionary<string, List<VariantRule>> VariantRules = new(StringComparer.Ordinal);

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
        foreach (var room in data.Strings("hero_coat1982_rooms")) CoatRooms.Add(room);
        foreach (var room in data.Strings("hero_coat2035_rooms")) WinterCoatRooms2035.Add(room);
        DepthSpeedFactor = data.Num("depth_speed_factor", DepthSpeedFactor);
        ActionHoldSeconds = data.Num("action_hold_s", ActionHoldSeconds);
        HeroBlinkChance = data.Num("hero_blink_chance", HeroBlinkChance);
        if (data.Obj("action_hold_overrides_s") is { } o)
            foreach (var (k, _) in o) holds[k] = o.Num(k, ActionHoldSeconds);
        if (data.Obj("variants_after") is { } rules)
        {
            foreach (var (charId, node) in rules)
            {
                if (node is not System.Text.Json.Nodes.JsonArray list) continue;
                var parsed = new List<VariantRule>();
                foreach (var item in list)
                    if (item is System.Text.Json.Nodes.JsonObject r && r.Str("after") is { } after && r.Str("variant") is { } variant)
                        parsed.Add(new VariantRule(after, variant));
                VariantRules[charId] = parsed;
            }
        }
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

    /// <summary>
    /// True when the hero wears his winter coat and scarf in the room: the December 1982 exteriors
    /// (<c>hero_coat1982_rooms</c>) and the winter Jasna 2035 exteriors (<c>hero_coat2035_rooms</c>, owner
    /// 2026-10-06 "Jasna 2035 is in winter"; the same <c>*_coat1982</c> sheets).
    /// </summary>
    public static bool HeroWearsCoat(string roomId, int era)
    {
        EnsureLoaded();
        return (era == 1982 && CoatRooms.Contains(roomId)) || (era == 2035 && WinterCoatRooms2035.Contains(roomId));
    }

    /// <summary>
    /// The hero's sheet variant in a room: <see cref="MaskVariant"/>, <see cref="CoatVariant"/> or null for the default
    /// jacket set. Every variant clip has the timing and geometry of its default clip; a clip a variant lacks falls back
    /// to the default sheet (ActorAnimationSet.Load).
    /// </summary>
    public static string? HeroVariant(string roomId, int era) =>
        HeroWearsMask(roomId, era) ? MaskVariant : HeroWearsCoat(roomId, era) ? CoatVariant : null;

    /// <summary>Staging of a character in a room, or null.</summary>
    public static ActorPlacement? PlacementFor(string roomId, string characterId)
    {
        EnsureLoaded();
        return Placements.TryGetValue(roomId + "/" + characterId, out var p) ? p : null;
    }

    /// <summary>The <c>variants_after</c> rules of a character (data order), empty when none.</summary>
    public static IReadOnlyList<VariantRule> VariantRulesFor(string characterId)
    {
        EnsureLoaded();
        return VariantRules.TryGetValue(characterId, out var list) ? list : Array.Empty<VariantRule>();
    }

    /// <summary>
    /// The variant to draw: <paramref name="baseVariant"/> (room placement, else the manifest default),
    /// replaced by the last rule whose action is done. Pure; visual only, never a rule.
    /// </summary>
    public static string? ResolveVariant(string? baseVariant, IReadOnlyList<VariantRule> rules, Func<string, bool> isDone)
    {
        string? result = baseVariant;
        foreach (var rule in rules)
        {
            if (!isDone(rule.After)) continue;
            if (rule.Variant.Contains("{base}") && baseVariant is null) continue; // nothing to derive from
            result = rule.Variant.Replace("{base}", baseVariant ?? "");
        }
        return result;
    }

    /// <summary>Hold seconds for a one-shot action.</summary>
    public static float HoldFor(string animation)
    {
        EnsureLoaded();
        return holds.TryGetValue(animation, out var s) ? s : ActionHoldSeconds;
    }
}
