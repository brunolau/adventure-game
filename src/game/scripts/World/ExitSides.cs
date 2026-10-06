using Godot;

namespace LastBell.Game.World;

/// <summary>Which way an exit leads out of the picture (cursor arrow, Space badge, arrival walk-in).</summary>
public enum ExitSide
{
    /// <summary>Out of the left edge.</summary>
    Left,
    /// <summary>Out of the right edge.</summary>
    Right,
    /// <summary>Into the picture: a door, a gate, a path or stairs leading away from the camera.</summary>
    Up,
    /// <summary>Towards the viewer: out of the bottom edge.</summary>
    Down,
}

/// <summary>
/// Exit directions (docs/navigation/EXITS.md, owner 2026-10-06 "exits must be logical"). A natural blocking may name an
/// exit's side (<c>"side": "left|right|up|down"</c>); otherwise it is derived from the exit zone: zones near the left /
/// right picture edge lead there, zones in the middle lead into the picture above the lower fifth and towards the
/// viewer below it.
/// </summary>
public static class ExitSides
{
    /// <summary>How far (px) the hero walks in from an edge or a door when he arrives through an exit.</summary>
    public const float ArrivalStep = 110f;

    /// <summary>The side derived from an exit zone (the rule the cursor used before sides could be named).</summary>
    public static ExitSide FromRect(Rect2 rect)
    {
        var c = rect.GetCenter();
        float w = Room.CanvasSize.X, h = Room.CanvasSize.Y;
        if (c.X < w * 0.16f) return ExitSide.Left;
        if (c.X > w * 0.84f) return ExitSide.Right;
        return c.Y > h * 0.80f ? ExitSide.Down : ExitSide.Up;
    }

    /// <summary>Parses a blocking file's <c>side</c> value (null when missing or unknown).</summary>
    public static ExitSide? Parse(string? value) => value?.Trim().ToLowerInvariant() switch
    {
        "left" => ExitSide.Left,
        "right" => ExitSide.Right,
        "up" or "in" or "back" => ExitSide.Up,
        "down" or "out" or "front" => ExitSide.Down,
        _ => null,
    };

    /// <summary>Rotation of a right-pointing arrow towards the side.</summary>
    public static float Angle(ExitSide side) => side switch
    {
        ExitSide.Left => Mathf.Pi,
        ExitSide.Right => 0f,
        ExitSide.Down => Mathf.Pi / 2,
        _ => -Mathf.Pi / 2,
    };

    /// <summary>
    /// Where the hero appears when he comes in through an exit on <paramref name="side"/>: a step beyond its interaction
    /// point towards the edge or the door (he then walks in to the point). Callers clamp it into the walk polygon.
    /// </summary>
    public static Vector2 ArrivalStart(ExitSide side, Vector2 interactionPoint) => interactionPoint + side switch
    {
        ExitSide.Left => new Vector2(-ArrivalStep, 0),
        ExitSide.Right => new Vector2(ArrivalStep, 0),
        ExitSide.Down => new Vector2(0, ArrivalStep * 0.6f),
        _ => new Vector2(0, -ArrivalStep * 0.45f),
    };

    /// <summary>
    /// Where the arrival step ends: a little inside the room from an edge exit's interaction point (which lies at the
    /// very edge), so the hero stands clearly in the picture; in front of a door or path (<see cref="ExitSide.Up"/>) the
    /// point itself. Callers clamp it into the walk polygon.
    /// </summary>
    public static Vector2 ArrivalStand(ExitSide side, Vector2 interactionPoint) => interactionPoint + side switch
    {
        ExitSide.Left => new Vector2(ArrivalStep * 0.6f, 0),
        ExitSide.Right => new Vector2(-ArrivalStep * 0.6f, 0),
        ExitSide.Down => new Vector2(0, -ArrivalStep * 0.35f),
        _ => Vector2.Zero,
    };

    /// <summary>Lower-case name as written in the blocking files.</summary>
    public static string Name(ExitSide side) => side.ToString().ToLowerInvariant();
}
