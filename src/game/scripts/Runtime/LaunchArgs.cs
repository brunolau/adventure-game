using System;
using Godot;

namespace LastBell.Game.Runtime;

/// <summary>
/// User command-line arguments (the ones after <c>--</c>) for the QA harness and the other QA switches
/// (<c>--ui</c>, <c>--audio-log</c>, <c>--no-ambient</c>, ...). They are honoured only in debug and editor
/// builds (<see cref="OS.IsDebugBuild"/>). A release export ignores them, so a player cannot skip the story
/// from the command line (ISSUES BUILD-03). Engine options before <c>--</c> (<c>--resolution</c>,
/// <c>--log-file</c>, <c>--verbose</c>) still work in every build.
/// </summary>
public static class LaunchArgs
{
    private static string[]? user;

    /// <summary>True when QA arguments are honoured (debug export template, editor binary).</summary>
    public static bool QaAllowed => OS.IsDebugBuild();

    /// <summary>The user arguments in a debug/editor build; always empty in a release build.</summary>
    public static string[] User
    {
        get
        {
            if (user is not null) return user;
            var raw = OS.GetCmdlineUserArgs();
            if (!QaAllowed && raw.Length > 0)
                GD.Print($"LastBell: release build, {raw.Length} QA argument(s) after \"--\" ignored (ISSUES BUILD-03)");
            user = QaAllowed ? raw : Array.Empty<string>();
            return user;
        }
    }

    /// <summary>True when the QA harness or another QA switch was given (debug/editor builds only).</summary>
    public static bool Any => User.Length > 0;

    /// <summary>
    /// <c>--menu</c>: a QA run that starts like a player's (main menu, first-start tips, autosave), still in the QA
    /// background window mode; used with <c>--watch</c> by the OS-level keyboard check (docs/MILESTONE5.md, AT19).
    /// </summary>
    public static bool PlayerStart => Array.IndexOf(User, "--menu") >= 0;

    /// <summary>
    /// <c>--content-ext &lt;dir&gt;</c>: read the content overlays from this folder (an OS path) instead of
    /// <c>res://data/content_ext</c>, file by file (an overlay file missing there is read from the project as usual).
    /// QA only, e.g. the world-overlay sample of the Core tests (src/game/README.md "Content overlays").
    /// </summary>
    public static string? ContentExtDirectory
    {
        get
        {
            var i = Array.IndexOf(User, "--content-ext");
            return i >= 0 && i + 1 < User.Length ? User[i + 1] : null;
        }
    }
}
