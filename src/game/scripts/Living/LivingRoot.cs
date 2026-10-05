using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using LastBell.Game.Hooks;
using LastBell.Game.Living.Actors;
using LastBell.Game.Living.Ambient;
using LastBell.Game.Runtime;
using LastBell.Game.World;

namespace LastBell.Game.Living;

/// <summary>
/// Bootstrap of the living world (instanced by Main under LivingHost before any room is built):
/// registers the sprite-sheet actor visuals and fills every room's ambient host from
/// <c>data/ambient/&lt;room&gt;.json</c>. Follows <see cref="PresentationSettings.ReducedMotion"/>.
/// Debug args after "--": <c>--reduced-motion</c> (start with reduced motion on),
/// <c>--no-ambient</c> (skip ambient layers), <c>--ambient-report</c> (print the layers of each room).
/// </summary>
public partial class LivingRoot : Node
{
    private readonly SpriteActorVisualFactory factory = new();
    private readonly List<AmbientLayer> layers = new();
    private Room? room;
    private string signature = "";
    private bool reduced;
    private bool noAmbient;
    private bool report;

    /// <summary>The living root, once ready.</summary>
    public static LivingRoot? Instance { get; private set; }

    /// <summary>Layers of the current room (QA).</summary>
    public IReadOnlyList<AmbientLayer> CurrentLayers => layers;

    /// <inheritdoc />
    public override void _Ready()
    {
        Instance = this;
        var args = LaunchArgs.User;
        if (args.Contains("--reduced-motion")) PresentationSettings.ReducedMotion = true;
        noAmbient = args.Contains("--no-ambient");
        report = args.Contains("--ambient-report");
        reduced = PresentationSettings.ReducedMotion;
        ActorVisualRegistry.Register(factory, 100);
        RoomPreloader.PathProviders.Add(SheetsToPreload);
        WorldHooks.RoomBuilt += OnRoomBuilt;
        WorldHooks.RoomRefreshed += OnRoomRefreshed;
        WorldHooks.RoomLeaving += OnRoomLeaving;
        PresentationSettings.Changed += ApplyReducedMotion;
    }

    /// <inheritdoc />
    public override void _ExitTree()
    {
        ActorVisualRegistry.Unregister(factory);
        RoomPreloader.PathProviders.Remove(SheetsToPreload);
        WorldHooks.RoomBuilt -= OnRoomBuilt;
        WorldHooks.RoomRefreshed -= OnRoomRefreshed;
        WorldHooks.RoomLeaving -= OnRoomLeaving;
        PresentationSettings.Changed -= ApplyReducedMotion;
        if (Instance == this) Instance = null;
    }

    /// <summary>Sprite sheets a build of a neighbour room would load (hero variant of that room, its NPCs), for the preloader.</summary>
    private static IEnumerable<string> SheetsToPreload(LastBell.Core.Views.RoomView view)
    {
        string? heroVariant = ActorStaging.HeroWearsMask(view.RoomId, view.Era) ? "mask2020" : null;
        foreach (var path in ActorAnimationSet.SheetImagePaths(GameRuntime.HeroId, heroVariant)) yield return path;
        foreach (var npc in view.Npcs)
            if (npc.CharacterId is { } id && ActorAnimationSet.Exists(id))
                foreach (var path in ActorAnimationSet.SheetImagePaths(id, null)) yield return path;
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        // The settings UI may change the flag without NotifyChanged; poll it (cheap).
        if (PresentationSettings.ReducedMotion != reduced) ApplyReducedMotion();
    }

    private void OnRoomBuilt(Room built)
    {
        room = built;
        layers.Clear();
        if (noAmbient) return;
        layers.AddRange(AmbientBuilder.Build(built, reduced));
        signature = AmbientBuilder.Signature(built);
        if (report)
            GD.Print($"LIVING room={built.RoomId} layers={layers.Count} [" + string.Join(", ", layers.Select(l => $"{l.LayerId}:{l.LayerType}")) + "]");
    }

    private void OnRoomRefreshed(Room refreshed)
    {
        if (noAmbient || refreshed != room) return;
        string now = AmbientBuilder.Signature(refreshed);
        if (now == signature) return;
        foreach (var layer in layers)
            if (IsInstanceValid(layer)) (layer.GetParent() is Node2D { Name: var n } holder && n.ToString().StartsWith("AmbientSort_") ? holder : layer).QueueFree();
        layers.Clear();
        layers.AddRange(AmbientBuilder.Build(refreshed, reduced));
        signature = now;
    }

    private void OnRoomLeaving(Room leaving)
    {
        if (leaving != room) return;
        layers.Clear();
        room = null;
    }

    private void ApplyReducedMotion()
    {
        reduced = PresentationSettings.ReducedMotion;
        foreach (var layer in layers)
            if (IsInstanceValid(layer)) layer.SetReducedMotion(reduced);
    }
}
