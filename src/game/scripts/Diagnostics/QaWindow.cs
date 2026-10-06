using System.Linq;
using Godot;
using LastBell.Game.Runtime;

namespace LastBell.Game.Diagnostics;

/// <summary>
/// Keeps QA runs out of the way of whoever is using the computer (owner requests 2026-10-06): a debug/editor
/// run started with any QA argument opens its window off-screen, never takes keyboard focus, never moves
/// the real OS mouse cursor and is silent. Rendering, screenshots and Godot-level input events keep working,
/// because the window stays a normal drawable window: a minimized Godot window stops drawing, so screenshot,
/// frame and settle waits would hang (measured 2026-10-06).
/// <para>
/// The engine creates and shows the window before any script runs, so a plain console-exe launch still shows
/// it in the middle of the screen for about a second and lets it take the keyboard focus.
/// <c>tools/qa_godot.py</c> avoids that: it creates the window hidden (Windows STARTUPINFO SW_HIDE; a hidden
/// window keeps rendering, a minimized one does not) and sets <c>LASTBELL_QA_LAUNCHER</c>; a windowed QA run
/// started without it prints a warning so the launch gets fixed (window never on screen, never focused, measured
/// 2026-10-06 with a read-only window/foreground probe).
/// </para>
/// Opt out per run: <c>--visible</c> shows the window normally; <c>--audible</c> keeps the sound;
/// <c>--warp-mouse</c> lets the harness move the real cursor (only for checks that need the OS cursor, and only
/// when nobody is working on the machine).
/// </summary>
public static class QaWindow
{
    /// <summary>True for QA runs that should stay invisible and unfocused.</summary>
    public static bool Background => LaunchArgs.Any && !LaunchArgs.User.Contains("--visible");

    /// <summary>True for QA runs whose Master bus stays muted (background runs without <c>--audible</c>).</summary>
    public static bool Silent => Background && !LaunchArgs.User.Contains("--audible");

    /// <summary>True when the run explicitly allows moving the real OS cursor.</summary>
    public static bool WarpAllowed => LaunchArgs.User.Contains("--warp-mouse");

    /// <summary>
    /// Hidden windowed QA runs (background, not headless, no <c>--warp-mouse</c>): the real OS cursor is never moved,
    /// so Godot's mouse position (read from the OS in a window) never follows the harness's mouse events. Then the
    /// pointer of the world input and the hover label is the position of the last mouse event the game received,
    /// as in a headless run (added 2026-10-06 for the hover-label evidence; also lets raw world clicks land).
    /// Players' runs (no QA argument) never use it.
    /// </summary>
    public static bool UseEventPointer => Background && !WarpAllowed && DisplayServer.GetName() != "headless";

    /// <summary>Viewport position of the last mouse event (see <see cref="UseEventPointer"/>), or null.</summary>
    public static Vector2? LastEventPointer { get; private set; }

    /// <summary>Records a mouse event's viewport position (only while <see cref="UseEventPointer"/>).</summary>
    public static void NotePointer(InputEvent e)
    {
        if (e is InputEventMouse m && UseEventPointer) LastEventPointer = m.Position;
    }

    /// <summary>The mouse position in viewport px: the last mouse event in a hidden QA window, else Godot's.</summary>
    public static Vector2 ViewportPointer(Viewport viewport) =>
        UseEventPointer && LastEventPointer is { } p ? p : viewport.GetMousePosition();

    /// <summary>
    /// Moves the window to the right of every screen and stops it from taking focus. A window that starts
    /// minimized (tools/qa_godot.py) is moved first and restored off-screen, so it never appears on a screen.
    /// </summary>
    public static void ApplyBackgroundMode()
    {
        if (!Background) return;
        if (Silent) Mute();
        if (DisplayServer.GetName() == "headless") return;
        DisplayServer.WindowSetFlag(DisplayServer.WindowFlags.NoFocus, true);
        DisplayServer.WindowSetFlag(DisplayServer.WindowFlags.AlwaysOnTop, false);
        var offScreen = OffScreenPosition();
        bool minimized = DisplayServer.WindowGetMode() == DisplayServer.WindowMode.Minimized;
        DisplayServer.WindowSetPosition(offScreen);
        if (minimized)
        {
            // Restore so the window draws again (a minimized window renders nothing); position again in case
            // the restore used the creation position.
            DisplayServer.WindowSetMode(DisplayServer.WindowMode.Windowed);
            DisplayServer.WindowSetPosition(offScreen);
        }
        if (string.IsNullOrEmpty(System.Environment.GetEnvironmentVariable("LASTBELL_QA_LAUNCHER")))
            GD.PushWarning("LastBell: windowed QA run started without tools/qa_godot.py - its window was shown on "
                           + "screen and could take the keyboard focus; launch QA runs with python tools/qa_godot.py");
        GD.Print($"LastBell: QA run in background mode (off-screen{(minimized ? ", started minimized" : "")}, no focus, "
                 + $"{(Silent ? "muted, " : "")}real cursor untouched; --visible to show, --audible for sound)");
    }

    /// <summary>Mutes the Master bus of a silent QA run (settings and focus changes call this again).</summary>
    public static void Mute()
    {
        int master = AudioServer.GetBusIndex("Master");
        if (master >= 0) AudioServer.SetBusMute(master, true);
    }

    /// <summary>A position to the right of every screen (window rect fully outside the desktop).</summary>
    private static Vector2I OffScreenPosition()
    {
        var right = 0;
        for (var i = 0; i < DisplayServer.GetScreenCount(); i++)
            right = Mathf.Max(right, DisplayServer.ScreenGetPosition(i).X + DisplayServer.ScreenGetSize(i).X);
        return new Vector2I(right + 64, 0);
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
