using System;
using System.Collections.Generic;
using Godot;

namespace LastBell.Game.World;

/// <summary>
/// A character in the room (hero or NPC). Its position is the feet centre on the walk area; the
/// parent layer y-sorts by it. The actor applies perspective scale by feet y, walks along paths
/// at the visual's stride speed times the scale, and forwards animation state to its pluggable
/// <see cref="IActorVisual"/>.
/// </summary>
public partial class Actor : Node2D
{
    private readonly Queue<Vector2> path = new();
    private Action? onArrived;
    private Perspective perspective;
    private Vector2 facing = Vector2.Right;

    /// <summary>Character id.</summary>
    public string CharacterId { get; private set; } = "";

    /// <summary>True for the hero.</summary>
    public bool IsHero { get; private set; }

    /// <summary>NPC hotspot id (null for the hero).</summary>
    public string? HotspotId { get; private set; }

    /// <summary>The visual (placeholder or sprite).</summary>
    public IActorVisual Visual { get; private set; } = null!;

    /// <summary>The creation context of the visual.</summary>
    public ActorContext Context { get; private set; } = null!;

    /// <summary>True while following a path.</summary>
    public bool IsWalking => path.Count > 0;

    /// <summary>Feet position in canvas px.</summary>
    public Vector2 Feet => Position;

    /// <summary>Current perspective scale.</summary>
    public float CurrentScale => Scale.X;

    /// <summary>Optional speed multiplier (e.g. fast walk on double click later).</summary>
    public float SpeedMultiplier { get; set; } = 1f;

    /// <summary>Point above the head in canvas px (speaker tags, look bubbles).</summary>
    public Vector2 HeadPosition => Position + new Vector2(0, -Visual.HeightPx * CurrentScale);

    /// <summary>Raised when the actor started or stopped walking.</summary>
    public event Action<bool>? WalkingChanged;

    /// <summary>Creates the actor with a visual from <see cref="ActorVisualRegistry"/>.</summary>
    public void Setup(ActorContext context, Perspective perspectiveScale, Vector2 feet)
    {
        Context = context;
        CharacterId = context.CharacterId;
        IsHero = context.IsHero;
        HotspotId = context.HotspotId;
        Name = (IsHero ? "Hero_" : "Npc_") + context.CharacterId;
        perspective = perspectiveScale;
        SetVisual(ActorVisualRegistry.Create(context));
        Place(feet);
    }

    /// <summary>Swaps the visual (e.g. after a factory was registered).</summary>
    public void SetVisual(IActorVisual visual)
    {
        if (Visual is not null)
        {
            RemoveChild(Visual.Node);
            Visual.Node.QueueFree();
        }
        Visual = visual;
        visual.Node.Name = "Visual";
        AddChild(visual.Node);
        visual.Bind(Context);
        visual.SetLocomotion(false, facing);
    }

    /// <summary>Teleports the feet to a point (no walking).</summary>
    public void Place(Vector2 feet)
    {
        path.Clear();
        Position = feet;
        UpdateScale();
    }

    /// <summary>Turns towards a point.</summary>
    public void FaceTowards(Vector2 point)
    {
        var d = point - Position;
        if (Mathf.Abs(d.X) < 1f && Mathf.Abs(d.Y) < 1f) return;
        facing = d.Normalized();
        Visual.SetLocomotion(IsWalking, facing);
    }

    /// <summary>Follows the waypoints; <paramref name="arrived"/> runs when the last one is reached.</summary>
    public void WalkPath(IReadOnlyList<Vector2> waypoints, Action? arrived)
    {
        bool wasWalking = IsWalking;
        path.Clear();
        foreach (var p in waypoints) path.Enqueue(p);
        onArrived = arrived;
        if (path.Count == 0)
        {
            var callback = onArrived;
            onArrived = null;
            callback?.Invoke();
            return;
        }
        if (!wasWalking) WalkingChanged?.Invoke(true);
    }

    /// <summary>Stops walking without running the arrival callback.</summary>
    public void Stop()
    {
        bool was = IsWalking;
        path.Clear();
        onArrived = null;
        Visual.SetLocomotion(false, facing);
        if (was) WalkingChanged?.Invoke(false);
    }

    /// <summary>Talk animation on/off.</summary>
    public void SetTalking(bool talking) => Visual.SetTalking(talking);

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        if (path.Count == 0) return;
        float step = Visual.WalkSpeedPxPerSecond * CurrentScale * SpeedMultiplier * (float)delta;
        while (step > 0 && path.Count > 0)
        {
            var target = path.Peek();
            var to = target - Position;
            float dist = to.Length();
            if (dist > 0.001f) facing = to / dist;
            if (dist <= step)
            {
                Position = target;
                path.Dequeue();
                step -= dist;
            }
            else
            {
                Position += to / dist * step;
                step = 0;
            }
        }
        UpdateScale();
        if (path.Count > 0)
        {
            Visual.SetLocomotion(true, facing);
            return;
        }
        Visual.SetLocomotion(false, facing);
        WalkingChanged?.Invoke(false);
        var callback = onArrived;
        onArrived = null;
        callback?.Invoke();
    }

    /// <summary>Absolute scale instead of the room perspective (natural blocking NPC staging), or null.</summary>
    public float? ScaleOverride { get; set; }

    private void UpdateScale()
    {
        float s = ScaleOverride ?? perspective.ScaleAt(Position.Y);
        Scale = new Vector2(s, s);
    }
}
