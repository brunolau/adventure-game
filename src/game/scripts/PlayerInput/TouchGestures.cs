using System.Collections.Generic;
using Godot;

namespace LastBell.Game.PlayerInput;

/// <summary>
/// Touch gestures for phones and tablets (docs/BUILD.md, CODING_AGENT_START input table):
/// tap = left click (<see cref="LogicalCommand.Primary"/>), long press = right click
/// (<see cref="LogicalCommand.Secondary"/>), two-finger hold = Space held: the markers show while two fingers touch
/// (<see cref="LogicalCommand.ShowMarkers"/> when the second finger goes down, <see cref="LogicalCommand.HideMarkers"/>
/// when fewer than two remain; owner override 2026-10-05). A double tap is two taps, recognised by the world as a double click.
/// A finger that moves further than <see cref="SlopPx"/> becomes a drag: it only moves the hover pointer
/// and releases without an action. Pure state machine: positions are canvas px, times are seconds; the
/// <see cref="InputRouter"/> feeds it and dispatches what it returns.
/// </summary>
public sealed class TouchGestures
{
    /// <summary>Hold time for a long press.</summary>
    public const double LongPressSeconds = 0.5;

    /// <summary>Longest two-finger tap (first finger down to last finger up).</summary>
    public const double TwoFingerTapSeconds = 0.45;

    /// <summary>Movement (canvas px, 1920x1080) under which a touch still counts as a tap.</summary>
    public const float SlopPx = 28f;

    /// <summary>A recognised gesture.</summary>
    public readonly record struct Gesture(LogicalCommand Command, Vector2 Position);

    private readonly Dictionary<int, Vector2> down = new();
    private Vector2 startPosition;
    private double startTime;
    private int maxFingers;
    private bool moved;
    private bool longPressFired;
    private bool active;
    private bool markers;

    /// <summary>True while at least one finger touches the screen.</summary>
    public bool Active => active;

    /// <summary>True while the single finger moved beyond the slop (hover drag).</summary>
    public bool Dragging => active && moved && maxFingers == 1;

    /// <summary>A finger went down or up. Returns a gesture when one completes on release.</summary>
    public Gesture? Touch(int index, Vector2 position, bool pressed, double now)
    {
        if (pressed)
        {
            if (!active)
            {
                active = true;
                startPosition = position;
                startTime = now;
                maxFingers = 0;
                moved = false;
                longPressFired = false;
            }
            down[index] = position;
            maxFingers = Mathf.Max(maxFingers, down.Count);
            if (down.Count >= 2 && !markers && !longPressFired)
            {
                markers = true;
                return new Gesture(LogicalCommand.ShowMarkers, startPosition);
            }
            return null;
        }
        down.Remove(index);
        if (markers && down.Count < 2)
        {
            markers = false;
            if (down.Count == 0) active = false;
            return new Gesture(LogicalCommand.HideMarkers, startPosition);
        }
        if (down.Count > 0 || !active) return null;
        active = false;
        if (longPressFired || moved || maxFingers >= 2) return null;
        return new Gesture(LogicalCommand.Primary, startPosition);
    }

    /// <summary>A finger moved.</summary>
    public void Drag(int index, Vector2 position)
    {
        if (!active || !down.ContainsKey(index)) return;
        down[index] = position;
        if (index == 0 && position.DistanceTo(startPosition) > SlopPx) moved = true;
    }

    /// <summary>Called every frame: returns the long press once the single finger has been held still long enough.</summary>
    public Gesture? Poll(double now)
    {
        if (!active || longPressFired || moved || maxFingers != 1 || now - startTime < LongPressSeconds) return null;
        longPressFired = true;
        return new Gesture(LogicalCommand.Secondary, startPosition);
    }

    /// <summary>Forget the current touch (e.g. a room transition started).</summary>
    public void Reset()
    {
        down.Clear();
        active = false;
        markers = false;
    }
}
