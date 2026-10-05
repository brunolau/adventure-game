using System;
using Godot;
using LastBell.Game.World;

namespace LastBell.Game.Hooks;

/// <summary>
/// Per-room host for ambient animation (owned by the living-world agent, scripts/Living/**).
/// The generic <see cref="Room"/> creates one per room: this node itself sits right above the
/// background and the state-variant layers (behind actors), <see cref="Front"/> sits above the
/// foreground mask, and <see cref="Actors"/> is the y-sorted actor layer for ambient passers-by
/// that must depth-sort with the hero (add Node2D children whose position is their feet).
/// Content is built from <c>res://data/ambient/&lt;room&gt;.json</c> by the living-world code in
/// response to <see cref="WorldHooks.RoomBuilt"/>. The world runtime never adds children here.
/// </summary>
public partial class AmbientHost : Node2D
{
    /// <summary>Room id.</summary>
    public string RoomId { get; internal set; } = "";

    /// <summary>Era of the room.</summary>
    public int Era { get; internal set; }

    /// <summary>The room this host belongs to.</summary>
    public Room Room { get; internal set; } = null!;

    /// <summary>Layer above the foreground mask (rain, snow, light sweeps in front of everything).</summary>
    public Node2D Front { get; internal set; } = null!;

    /// <summary>The y-sorted actor layer (feet-sorted together with the hero and NPCs).</summary>
    public Node2D Actors { get; internal set; } = null!;

    /// <summary>Path of the room's ambient data file (may not exist).</summary>
    public string DataPath => DataPathOverride ?? $"res://data/ambient/{RoomId}.json";

    /// <summary>Ambient data path set by a natural blocking (World/RoomBlocking.cs); null = the room's default file.</summary>
    public string? DataPathOverride { get; internal set; }
}

/// <summary>
/// World lifecycle events for extensions (living world, UI). Subscribe from a bootstrap node; the
/// events fire on the main thread.
/// </summary>
public static class WorldHooks
{
    /// <summary>A room was built and added to the tree (fill its <see cref="Room.Ambient"/> here).</summary>
    public static event Action<Room>? RoomBuilt;

    /// <summary>The current room was refreshed after a state change (hotspots, NPCs, variant layers).</summary>
    public static event Action<Room>? RoomRefreshed;

    /// <summary>A room is about to be freed (leaving it).</summary>
    public static event Action<Room>? RoomLeaving;

    /// <summary>The room transition finished: the room is visible and accepts input.</summary>
    public static event Action<Room>? RoomReady;

    /// <summary>The hero started or stopped walking.</summary>
    public static event Action<Actor, bool>? HeroWalkingChanged;

    internal static void RaiseRoomBuilt(Room room) => Safe(() => RoomBuilt?.Invoke(room));
    internal static void RaiseRoomRefreshed(Room room) => Safe(() => RoomRefreshed?.Invoke(room));
    internal static void RaiseRoomLeaving(Room room) => Safe(() => RoomLeaving?.Invoke(room));
    internal static void RaiseRoomReady(Room room) => Safe(() => RoomReady?.Invoke(room));
    internal static void RaiseHeroWalking(Actor hero, bool walking) => Safe(() => HeroWalkingChanged?.Invoke(hero, walking));

    private static void Safe(Action action)
    {
        try
        {
            action();
        }
        catch (Exception ex)
        {
            GD.PushError("World hook handler failed: " + ex);
        }
    }
}
