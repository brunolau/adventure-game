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
            : placement?.Variant;
        var set = ActorAnimationSet.Load(context.CharacterId, variant);
        if (set is null)
        {
            GD.PushWarning($"Living: no usable sprite sheets for {context.CharacterId} (placeholder used)");
            return null;
        }
        return new SpriteActorVisual(set, placement);
    }
}
