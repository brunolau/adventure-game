using Godot;
using LastBell.Game.World;

namespace LastBell.Game.Living.Actors;

/// <summary>
/// Creates <see cref="SpriteActorVisual"/>s for every character that has sprite data under
/// <c>res://assets/actors/&lt;ID&gt;/</c>; returns null otherwise so the placeholder stays.
/// </summary>
public sealed class SpriteActorVisualFactory : IActorVisualFactory
{
    /// <inheritdoc />
    public IActorVisual? TryCreate(ActorContext context)
    {
        if (!ActorAnimationSet.Exists(context.CharacterId)) return null;
        var placement = context.IsHero ? null : PlacementFor(context);
        string? variant = context.IsHero
            ? (ActorStaging.HeroWearsMask(context.RoomId, context.Era) ? "mask2020" : null)
            : NpcVariant(context, placement);
        var set = ActorAnimationSet.Load(context.CharacterId, variant);
        if (set is null)
        {
            GD.PushWarning($"Living: no usable sprite sheets for {context.CharacterId} (placeholder used)");
            return null;
        }
        return new SpriteActorVisual(set, placement);
    }

    /// <summary>
    /// NPC staging: a room with a natural blocking (World/RoomBlocking.cs) stages its NPCs from the blocking file's
    /// <c>npcs</c> entry (variant, sill line, offset, facing; the absolute scale is the Actor's ScaleOverride) and
    /// ignores data/ambient/actors.json's placement, whose sill heights belong to the template painting. An NPC the
    /// blocking does not stage gets the default sheets. Other rooms keep actors.json.
    /// </summary>
    private static ActorPlacement? PlacementFor(ActorContext context)
    {
        if (RoomBlocking.For(context.RoomId) is not { } blocking) return ActorStaging.PlacementFor(context.RoomId, context.CharacterId);
        if (context.HotspotId is null || !blocking.Npcs.TryGetValue(context.HotspotId, out var staging)) return null;
        if (!ActorAnimationSet.TryResolveStaging(context.CharacterId, staging.Variant, out var variant))
        {
            GD.PushWarning($"Living: {context.RoomId} blocking stages {context.CharacterId} as '{staging.Variant}', which its actor.json does not have (default sheets used)");
            variant = null;
        }
        return new ActorPlacement(variant, staging.SillY, null, staging.OffsetX, staging.Facing);
    }

    /// <summary>
    /// NPC variant: the room placement's variant (else the manifest's <c>default_variant</c>), switched by the
    /// character's <c>variants_after</c> rules in data/ambient/actors.json once their action is done (ART-AGE-04).
    /// Evaluated when the room is built, i.e. on the next entry after the action (bible: changes show on re-entry).
    /// </summary>
    private static string? NpcVariant(ActorContext context, ActorPlacement? placement)
    {
        var rules = ActorStaging.VariantRulesFor(context.CharacterId);
        var baseVariant = placement?.Variant ?? ActorAnimationSet.DefaultVariant(context.CharacterId);
        if (rules.Count == 0 || Runtime.GameRuntime.Instance?.State is not { } state) return placement?.Variant;
        var resolved = ActorStaging.ResolveVariant(baseVariant, rules, state.IsDone);
        return resolved == baseVariant ? placement?.Variant : resolved;
    }
}
