using System;
using System.Collections.Generic;
using System.Linq;
using Godot;

namespace LastBell.Game.World;

/// <summary>What an actor visual is created for.</summary>
/// <param name="CharacterId">Character id from game.json (e.g. "ADAM", "ELA", "TONO82").</param>
/// <param name="IsHero">True for the player's hero.</param>
/// <param name="RoomId">Room the actor stands in.</param>
/// <param name="Era">Era of the room.</param>
/// <param name="HotspotId">NPC hotspot id (null for the hero).</param>
/// <param name="HotspotRect">NPC hotspot rect in canvas px (null for the hero).</param>
public sealed record ActorContext(string CharacterId, bool IsHero, string RoomId, int Era, string? HotspotId, Rect2? HotspotRect);

/// <summary>
/// Pluggable look of an <see cref="Actor"/>. The actor node owns position (= feet), perspective
/// scale, walking and facing; the visual only draws and animates around its origin, which is the
/// feet centre (sprite sheet pivot). Units are px at actor scale 1.0.
/// The world runtime ships <see cref="PlaceholderActorVisual"/>; the living-world agent registers a
/// sprite-sheet visual through <see cref="ActorVisualRegistry.Register"/>.
/// </summary>
public interface IActorVisual
{
    /// <summary>The node to add under the actor (origin = feet centre).</summary>
    Node2D Node { get; }

    /// <summary>Figure height in px at scale 1 (speaker labels and look bubbles sit above it).</summary>
    float HeightPx { get; }

    /// <summary>Ground speed in px/s at scale 1 that matches the walk cycle (no foot sliding).</summary>
    float WalkSpeedPxPerSecond { get; }

    /// <summary>Called once after the node entered the actor.</summary>
    void Bind(ActorContext context);

    /// <summary>Walking or standing, with the current (normalised) movement or facing direction.</summary>
    void SetLocomotion(bool walking, Vector2 direction);

    /// <summary>Talk animation on/off (the subtitle presenter calls it per line).</summary>
    void SetTalking(bool talking);

    /// <summary>
    /// True while the figure takes part in a conversation (topic menu, the lines of a topic or of an action aimed at
    /// it), also while the other party speaks: an NPC whose idle is an activity (Zuzana's hopscotch) then stands
    /// still and resumes the activity when the conversation ends (manifest clip <c>idle_engaged</c>). Default: no-op.
    /// </summary>
    void SetEngaged(bool engaged) { }

    /// <summary>
    /// One-shot body animation named by <c>actions[].animation</c> (reach_mid, use_tool, show_item,
    /// inventory_combine, talk ...). Unknown names are ignored. Never blocks rules: the action is
    /// already committed when this plays.
    /// </summary>
    void PlayGesture(string animation);

    /// <summary>
    /// False when the figure does not stand on the floor (e.g. a window bust behind a sill), so the
    /// shadow layer draws no feet ellipse for it (ISSUES LIVING-01). Default true.
    /// </summary>
    bool CastsShadow => true;
}

/// <summary>Creates actor visuals. Return null to let the next factory (or the placeholder) handle it.</summary>
public interface IActorVisualFactory
{
    /// <summary>A visual for the context, or null.</summary>
    IActorVisual? TryCreate(ActorContext context);
}

/// <summary>
/// Registry of actor visual factories. Higher priority wins; the placeholder is the final fallback.
/// Register from your bootstrap (e.g. scripts/Living/LivingRoot.cs) before rooms are built; rooms
/// built later use the new factory. <see cref="Changed"/> lets the current room rebuild its actors.
/// </summary>
public static class ActorVisualRegistry
{
    private static readonly List<(int Priority, IActorVisualFactory Factory)> Factories = new();

    /// <summary>Raised after a factory was added or removed.</summary>
    public static event Action? Changed;

    /// <summary>Adds a factory.</summary>
    public static void Register(IActorVisualFactory factory, int priority = 0)
    {
        Factories.Add((priority, factory));
        Factories.Sort((a, b) => b.Priority.CompareTo(a.Priority));
        Changed?.Invoke();
    }

    /// <summary>Removes a factory.</summary>
    public static void Unregister(IActorVisualFactory factory)
    {
        Factories.RemoveAll(f => ReferenceEquals(f.Factory, factory));
        Changed?.Invoke();
    }

    /// <summary>Creates the visual for a context (never null).</summary>
    public static IActorVisual Create(ActorContext context)
    {
        foreach (var (_, factory) in Factories.ToList())
        {
            try
            {
                if (factory.TryCreate(context) is { } visual) return visual;
            }
            catch (Exception ex)
            {
                GD.PushError($"Actor visual factory {factory.GetType().Name} failed for {context.CharacterId}: {ex.Message}");
            }
        }
        return new PlaceholderActorVisual();
    }
}
