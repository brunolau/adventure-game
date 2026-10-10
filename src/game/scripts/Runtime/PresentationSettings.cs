using System;

namespace LastBell.Game.Runtime;

/// <summary>
/// Player presentation preferences read by the world runtime (text speed, auto-advance, reduced
/// motion, ...). They never affect rules. The settings UI (scripts/UI) owns persisting them and
/// writes these values; call <see cref="NotifyChanged"/> afterwards so presenters can react.
/// </summary>
public static class PresentationSettings
{
    /// <summary>Typewriter speed in characters per second; 0 or less shows the whole line at once.</summary>
    public static float TextCharsPerSecond { get; set; } = 45f;

    /// <summary>When true, a fully shown line advances by itself after <see cref="AutoAdvanceSeconds"/>.</summary>
    public static bool AutoAdvance { get; set; } = true;

    /// <summary>Base hold time of a fully revealed line before auto-advance.</summary>
    public static float AutoAdvanceBaseSeconds { get; set; } = 1.4f;

    /// <summary>Extra hold time per character (reading speed) before auto-advance.</summary>
    public static float AutoAdvancePerCharSeconds { get; set; } = 0.055f;

    /// <summary>Show subtitles (lines are always shown while there is no voice-over).</summary>
    public static bool Subtitles { get; set; } = true;

    /// <summary>Show the speaker name tag.</summary>
    public static bool SpeakerNames { get; set; } = true;

    /// <summary>Subtitle font size in px at the 1920x1080 base resolution.</summary>
    public static int SubtitleFontSize { get; set; } = 34;

    /// <summary>Reduced motion: room transitions use a short plain fade, ambient motion freezes (Living agent).</summary>
    public static bool ReducedMotion { get; set; }

    /// <summary>High-contrast hotspot labels.</summary>
    public static bool HighContrastLabels { get; set; }

    /// <summary>Multiplier of cutscene beats' duration_min_s (1 = as authored; the debug harness uses 0).</summary>
    public static float CutsceneMinDurationScale { get; set; } = 1f;

    /// <summary>
    /// Developer notes on screen (the stage direction on a cutscene card without its painting, the
    /// placeholder puzzle's solve button). Off for players, also in debug builds such as play.bat;
    /// only the QA harness flag <c>--dev</c> turns it on (ISSUES INT-06).
    /// </summary>
    public static bool DevNotes { get; set; }

    /// <summary>
    /// Natural re-blocking (World/RoomBlocking.cs, data/blocking/&lt;room&gt;.json): true / false forces it,
    /// null (default) follows the project setting <c>last_bell/presentation/blocking</c> ("natural" since milestone 3; "template" unless
    /// approved). The QA flag <c>--blocking natural|template</c> sets it. Takes effect on the next room build.
    /// </summary>
    public static bool? NaturalBlocking { get; set; }

    /// <summary>
    /// The hero's walk speed factor over the sheets' authored stride (product owner 2026-10-05: "a bit faster,
    /// not unnatural"). The one place for it: <see cref="LastBell.Game.World.Actor"/> multiplies the ground speed and
    /// the sprite visual multiplies the walk cycle's playback rate by the same factor, so planted feet never slide.
    /// The settings UI offers 1.0 / 1.25 / 1.5 (ui.settings.walk_speed).
    /// </summary>
    public static float WalkSpeedFactor { get; set; } = DefaultWalkSpeedFactor;

    /// <summary>Default of <see cref="WalkSpeedFactor"/> (+25 %).</summary>
    public const float DefaultWalkSpeedFactor = 1.25f;

    /// <summary>Longest gap between the two presses of a double click / double tap / double Enter that skips the walk.</summary>
    public static float DoubleClickSeconds { get; set; } = 0.35f;

    /// <summary>Largest distance (canvas px) between the two presses of a double click on the floor.</summary>
    public static float DoubleClickSlopPx { get; set; } = 40f;

    /// <summary>
    /// QA only (harness flag <c>--labels</c>): draw the old text labels of every visible target instead of the
    /// Space markers, for art review screenshots. Players never see text labels for all targets at once.
    /// </summary>
    public static bool QaTextLabels { get; set; }

    /// <summary>
    /// Canvas px at the bottom of the picture that the HUD strip covers: 86 for the PC strip; the finger-sized strip of
    /// a phone is about twice as tall (set by the UI settings from the HUD scale). The hotspot markers and the raised
    /// tap spots of the exits stay above it.
    /// </summary>
    public static float BottomReservePx { get; set; } = 86f;

    /// <summary>Room fade duration in seconds (each direction).</summary>
    public static float RoomFadeSeconds { get; set; } = 0.35f;

    /// <summary>Raised by the settings UI after it changed values.</summary>
    public static event Action? Changed;

    /// <summary>Raise <see cref="Changed"/>.</summary>
    public static void NotifyChanged() => Changed?.Invoke();

    /// <summary>Seconds a fully revealed line stays before auto-advance.</summary>
    public static float HoldSecondsFor(string text) => AutoAdvanceBaseSeconds + AutoAdvancePerCharSeconds * (text?.Length ?? 0);
}
