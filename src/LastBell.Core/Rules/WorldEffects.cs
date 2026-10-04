using LastBell.Core.Content;
using LastBell.Core.State;

namespace LastBell.Core.Rules;

/// <summary>A causal effect that applies to a room.</summary>
/// <param name="Effect">The effect record (its texts are production data, not captions).</param>
/// <param name="Index">Index in <c>causal_effects</c>.</param>
/// <param name="DeferredUntilReentry">
/// True when the trigger was committed while the hero was already in this room: the change takes
/// effect on the next entry (handoff rule), so the presentation keeps the old look for now.
/// </param>
public sealed record ActiveCausalEffect(CausalEffectDef Effect, int Index, bool DeferredUntilReentry);

/// <summary>A visual variant layer of a room.</summary>
/// <param name="Layer">The layer record (asset path, trigger).</param>
/// <param name="Visible">True when the layer must be drawn now.</param>
/// <param name="DeferredUntilReentry">True when the trigger is done but the hero has not re-entered the room since.</param>
public sealed record VariantLayerState(VisualVariantLayerDef Layer, bool Visible, bool DeferredUntilReentry);

/// <summary>State of a butterfly effect.</summary>
/// <param name="Effect">The effect record.</param>
/// <param name="Triggered">True when the trigger action is done.</param>
/// <param name="VisibleRooms">Rooms whose variants show the effect.</param>
public sealed record ButterflyState(ButterflyEffectDef Effect, bool Triggered, IReadOnlyList<string> VisibleRooms);

/// <summary>
/// Exactly listed world changes: causal_effects, the two fixed butterfly effects (BF_TREE, BF_JANA)
/// and visual_variant_layers. There is no general butterfly simulator: nothing outside these lists
/// ever changes. Changes become effective after the atomic action and the next entry into the
/// affected room, so geometry never disappears under the hero.
/// </summary>
public static class WorldEffects
{
    /// <summary>True when the action is done and was committed before the hero entered the current room.</summary>
    public static bool IsSettledInCurrentRoom(GameState state, string actionId)
    {
        var index = state.Done.IndexOf(actionId);
        return index >= 0 && index < state.RoomEntryDoneCount;
    }

    /// <summary>Causal effects whose trigger is done and which list the room.</summary>
    public static IReadOnlyList<ActiveCausalEffect> CausalEffectsAt(GameContent content, GameState state, string roomId)
    {
        var result = new List<ActiveCausalEffect>();
        var effects = content.Data.CausalEffects;
        for (var i = 0; i < effects.Count; i++)
        {
            var effect = effects[i];
            if (!effect.At.Contains(roomId) || !state.IsDone(effect.After)) continue;
            var deferred = roomId == state.Room && !IsSettledInCurrentRoom(state, effect.After);
            result.Add(new ActiveCausalEffect(effect, i, deferred));
        }
        return result;
    }

    /// <summary>All visual variant layers of a room in data order (drawn above the background in this order).</summary>
    public static IReadOnlyList<VariantLayerState> VariantLayers(GameContent content, GameState state, string roomId) =>
        content.Data.VisualVariantLayers.Where(l => l.Room == roomId).Select(l =>
        {
            var done = state.IsDone(l.After);
            var deferred = done && roomId == state.Room && !IsSettledInCurrentRoom(state, l.After);
            return new VariantLayerState(l, done && !deferred, deferred);
        }).ToList();

    /// <summary>State of BF_TREE and BF_JANA.</summary>
    public static IReadOnlyList<ButterflyState> Butterflies(GameContent content, GameState state) =>
        content.Data.ButterflyEffects.Select(b => new ButterflyState(b, state.IsDone(b.Trigger), b.VisibleRooms)).ToList();

    /// <summary>True when the butterfly effect with this id is triggered.</summary>
    public static bool IsTriggered(GameContent content, GameState state, string butterflyId) =>
        content.Data.ButterflyEffects.FirstOrDefault(b => b.Id == butterflyId) is { } b && state.IsDone(b.Trigger);
}
