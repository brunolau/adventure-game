using System.Linq;
using Godot;
using LastBell.Game.Runtime;

namespace LastBell.Game.Diagnostics;

/// <summary>
/// Keeps QA runs out of the way of whoever is using the computer (owner request 2026-10-06): a debug/editor
/// run started with any QA argument opens its window off-screen, never takes keyboard focus and never moves
/// the real OS mouse cursor. Rendering, screenshots and Godot-level input events keep working, because the
/// window stays a normal drawable window (a minimized window would stop rendering).
/// Opt out per run: <c>--visible</c> shows the window normally; <c>--warp-mouse</c> lets the harness move the
/// real cursor (only for checks that need the OS cursor, and only when nobody is working on the machine).
/// </summary>
public static class QaWindow
{
    /// <summary>True for QA runs that should stay invisible and unfocused.</summary>
    public static bool Background => LaunchArgs.Any && !LaunchArgs.User.Contains("--visible");

    /// <summary>True when the run explicitly allows moving the real OS cursor.</summary>
    public static bool WarpAllowed => LaunchArgs.User.Contains("--warp-mouse");

    /// <summary>Moves the window to the right of every screen and stops it from taking focus.</summary>
    public static void ApplyBackgroundMode()
    {
        if (!Background || DisplayServer.GetName() == "headless") return;
        DisplayServer.WindowSetFlag(DisplayServer.WindowFlags.NoFocus, true);
        DisplayServer.WindowSetFlag(DisplayServer.WindowFlags.AlwaysOnTop, false);
        var right = 0;
        for (var i = 0; i < DisplayServer.GetScreenCount(); i++)
            right = Mathf.Max(right, DisplayServer.ScreenGetPosition(i).X + DisplayServer.ScreenGetSize(i).X);
        DisplayServer.WindowSetPosition(new Vector2I(right + 64, 0));
        GD.Print("LastBell: QA run in background mode (off-screen, no focus, real cursor untouched; --visible to show)");
    }

    /// <summary>
    /// Replacement for <see cref="Input.WarpMouse"/> in QA code: moves the real cursor only with --warp-mouse.
    /// Callers still send the matching <see cref="InputEventMouseMotion"/>, which is what the game reacts to.
    /// </summary>
    public static void WarpMouse(Vector2 viewportPoint)
    {
        if (WarpAllowed) Input.WarpMouse(viewportPoint);
    }
}
