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
        var placement = context.IsHero ? null : ActorStaging.PlacementFor(context.RoomId, context.CharacterId);
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
