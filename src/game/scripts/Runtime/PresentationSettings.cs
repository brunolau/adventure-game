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

    /// <summary>Room fade duration in seconds (each direction).</summary>
    public static float RoomFadeSeconds { get; set; } = 0.35f;

    /// <summary>Raised by the settings UI after it changed values.</summary>
    public static event Action? Changed;

    /// <summary>Raise <see cref="Changed"/>.</summary>
    public static void NotifyChanged() => Changed?.Invoke();

    /// <summary>Seconds a fully revealed line stays before auto-advance.</summary>
    public static float HoldSecondsFor(string text) => AutoAdvanceBaseSeconds + AutoAdvancePerCharSeconds * (text?.Length ?? 0);
}
