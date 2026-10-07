using System;
using Godot;
using LastBell.Game.Runtime;

namespace LastBell.Game.UI.Settings;

/// <summary>Text speed presets (characters per second; Instant shows the whole line at once).</summary>
public enum TextSpeed
{
    /// <summary>25 cps.</summary>
    Slow,
    /// <summary>45 cps.</summary>
    Normal,
    /// <summary>90 cps.</summary>
    Fast,
    /// <summary>Whole line at once.</summary>
    Instant,
}

/// <summary>
/// Player settings owned by the UI: persisted in <c>user://settings.cfg</c> and applied to the
/// world runtime (<see cref="PresentationSettings"/>), the audio buses, the window and the locale.
/// Never touches rules state.
/// </summary>
public static class UiSettings
{
    private const string FilePath = "user://settings.cfg";

    /// <summary>Audio bus names (created at startup when the project has no bus layout for them).</summary>
    public static readonly string[] Buses = { "Master", "Music", "Ambience", "SFX", "Voice" };

    /// <summary>Volume 0..100 per bus (index as <see cref="Buses"/>).</summary>
    public static readonly int[] Volume = { 80, 70, 80, 80, 90 };

    /// <summary>Mute while the game window is not focused.</summary>
    public static bool MuteUnfocused { get; set; }

    /// <summary>
    /// Voice-over on (default). Off: AudioService plays no voice lines and the dialogue presenter advances on the
    /// text timing only (it waits only while a voice line plays).
    /// </summary>
    public static bool VoiceOver { get; set; } = true;

    /// <summary>Text speed.</summary>
    public static TextSpeed TextSpeed { get; set; } = TextSpeed.Normal;

    /// <summary>Auto-advance fully shown lines.</summary>
    public static bool AutoAdvance { get; set; } = true;

    /// <summary>Auto-advance pace multiplier for the hold time (0.5 = quick, 1 = normal, 1.6 = slow).</summary>
    public static float AutoAdvancePace { get; set; } = 1f;

    /// <summary>Show subtitles.</summary>
    public static bool Subtitles { get; set; } = true;

    /// <summary>Subtitle font size (logical px, 18..48).</summary>
    public static int SubtitleSize { get; set; } = 34;

    /// <summary>Opaque (contrast) background behind subtitles.</summary>
    public static bool SubtitleBackground { get; set; } = true;

    /// <summary>Show the speaker name.</summary>
    public static bool SpeakerNames { get; set; } = true;

    /// <summary>Fullscreen (else windowed).</summary>
    public static bool Fullscreen { get; set; }

    /// <summary>HUD / UI scale in percent (100..200, AT08).</summary>
    public static int HudScalePercent { get; set; } = 100;

    /// <summary>Reduced motion.</summary>
    public static bool ReducedMotion { get; set; }

    /// <summary>High-contrast hotspot labels.</summary>
    public static bool HighContrastLabels { get; set; }

    /// <summary>Hero walk speed in percent of the sheets' stride: 100 calm, 125 normal (default), 150 brisk.</summary>
    public static int WalkSpeedPercent { get; set; } = 125;

    /// <summary>A ring that highlights the mouse cursor.</summary>
    public static bool CursorHighlight { get; set; }

    /// <summary>Remind the Space key in the HUD strip.</summary>
    public static bool HotspotKeyHint { get; set; } = true;

    /// <summary>Locale ("sk" or "en").</summary>
    public static string Locale { get; set; } = "sk";

    /// <summary>The first-start tips were shown.</summary>
    public static bool TipsShown { get; set; }

    /// <summary>Raised after <see cref="Apply"/>.</summary>
    public static event Action? Changed;

    /// <summary>HUD scale as a factor.</summary>
    public static float HudScale => Math.Clamp(HudScalePercent, 100, 200) / 100f;

    /// <summary>Loads the file (missing file: defaults).</summary>
    public static void Load()
    {
        var cfg = new ConfigFile();
        if (cfg.Load(FilePath) != Error.Ok) return;
        for (int i = 0; i < Buses.Length; i++) Volume[i] = Math.Clamp((int)cfg.GetValue("audio", Buses[i], Volume[i]), 0, 100);
        MuteUnfocused = (bool)cfg.GetValue("audio", "mute_unfocused", MuteUnfocused);
        VoiceOver = (bool)cfg.GetValue("audio", "voice_over", VoiceOver);
        TextSpeed = (TextSpeed)Math.Clamp((int)cfg.GetValue("text", "speed", (int)TextSpeed), 0, 3);
        AutoAdvance = (bool)cfg.GetValue("text", "auto_advance", AutoAdvance);
        AutoAdvancePace = Math.Clamp((float)cfg.GetValue("text", "auto_advance_pace", AutoAdvancePace), 0.4f, 2f);
        Subtitles = (bool)cfg.GetValue("text", "subtitles", Subtitles);
        SubtitleSize = Math.Clamp((int)cfg.GetValue("text", "subtitle_size", SubtitleSize), 18, 48);
        SubtitleBackground = (bool)cfg.GetValue("text", "subtitle_background", SubtitleBackground);
        SpeakerNames = (bool)cfg.GetValue("text", "speaker_names", SpeakerNames);
        Locale = (string)cfg.GetValue("text", "locale", Locale);
        Fullscreen = (bool)cfg.GetValue("display", "fullscreen", Fullscreen);
        HudScalePercent = Math.Clamp((int)cfg.GetValue("display", "hud_scale", HudScalePercent), 100, 200);
        ReducedMotion = (bool)cfg.GetValue("access", "reduced_motion", ReducedMotion);
        HighContrastLabels = (bool)cfg.GetValue("access", "high_contrast_labels", HighContrastLabels);
        CursorHighlight = (bool)cfg.GetValue("access", "cursor_highlight", CursorHighlight);
        WalkSpeedPercent = Math.Clamp((int)cfg.GetValue("access", "walk_speed", WalkSpeedPercent), 100, 150);
        HotspotKeyHint = (bool)cfg.GetValue("access", "hotspot_key_hint", HotspotKeyHint);
        TipsShown = (bool)cfg.GetValue("tips", "shown", TipsShown);
    }

    /// <summary>Writes the file.</summary>
    public static void Save()
    {
        var cfg = new ConfigFile();
        for (int i = 0; i < Buses.Length; i++) cfg.SetValue("audio", Buses[i], Volume[i]);
        cfg.SetValue("audio", "mute_unfocused", MuteUnfocused);
        cfg.SetValue("audio", "voice_over", VoiceOver);
        cfg.SetValue("text", "speed", (int)TextSpeed);
        cfg.SetValue("text", "auto_advance", AutoAdvance);
        cfg.SetValue("text", "auto_advance_pace", AutoAdvancePace);
        cfg.SetValue("text", "subtitles", Subtitles);
        cfg.SetValue("text", "subtitle_size", SubtitleSize);
        cfg.SetValue("text", "subtitle_background", SubtitleBackground);
        cfg.SetValue("text", "speaker_names", SpeakerNames);
        cfg.SetValue("text", "locale", Locale);
        cfg.SetValue("display", "fullscreen", Fullscreen);
        cfg.SetValue("display", "hud_scale", HudScalePercent);
        cfg.SetValue("access", "reduced_motion", ReducedMotion);
        cfg.SetValue("access", "high_contrast_labels", HighContrastLabels);
        cfg.SetValue("access", "cursor_highlight", CursorHighlight);
        cfg.SetValue("access", "walk_speed", WalkSpeedPercent);
        cfg.SetValue("access", "hotspot_key_hint", HotspotKeyHint);
        cfg.SetValue("tips", "shown", TipsShown);
        if (cfg.Save(FilePath) != Error.Ok) GD.PushWarning("UiSettings: cannot write " + FilePath);
    }

    /// <summary>Restores the defaults (keeps the tips flag).</summary>
    public static void ResetDefaults()
    {
        int[] defaults = { 80, 70, 80, 80, 90 };
        Array.Copy(defaults, Volume, defaults.Length);
        MuteUnfocused = false;
        VoiceOver = true;
        TextSpeed = TextSpeed.Normal;
        AutoAdvance = true;
        AutoAdvancePace = 1f;
        Subtitles = true;
        SubtitleSize = 34;
        SubtitleBackground = true;
        SpeakerNames = true;
        Fullscreen = false;
        HudScalePercent = 100;
        ReducedMotion = false;
        HighContrastLabels = false;
        CursorHighlight = false;
        WalkSpeedPercent = 125;
        HotspotKeyHint = true;
    }

    /// <summary>Characters per second of a preset.</summary>
    public static float CharsPerSecond(TextSpeed speed) => speed switch
    {
        TextSpeed.Slow => 25f,
        TextSpeed.Fast => 90f,
        TextSpeed.Instant => 0f,
        _ => 45f,
    };

    /// <summary>
    /// Applies everything to the runtime. <paramref name="keepTextTiming"/> leaves the text timing
    /// untouched (the debug harness sets fast text for QA runs).
    /// </summary>
    public static void Apply(bool keepTextTiming = false, bool applyWindow = true)
    {
        EnsureBuses();
        for (int i = 0; i < Buses.Length; i++)
        {
            int bus = AudioServer.GetBusIndex(Buses[i]);
            if (bus < 0) continue;
            AudioServer.SetBusVolumeDb(bus, Volume[i] <= 0 ? -80f : Mathf.LinearToDb(Volume[i] / 100f));
            AudioServer.SetBusMute(bus, Volume[i] <= 0);
        }
        if (LastBell.Game.Diagnostics.QaWindow.Silent) LastBell.Game.Diagnostics.QaWindow.Mute(); // QA runs stay silent
        if (!keepTextTiming)
        {
            PresentationSettings.TextCharsPerSecond = CharsPerSecond(TextSpeed);
            PresentationSettings.AutoAdvance = AutoAdvance;
            PresentationSettings.AutoAdvanceBaseSeconds = 1.4f * AutoAdvancePace;
            PresentationSettings.AutoAdvancePerCharSeconds = 0.055f * AutoAdvancePace;
        }
        PresentationSettings.Subtitles = Subtitles;
        PresentationSettings.SubtitleFontSize = SubtitleSize;
        PresentationSettings.SpeakerNames = SpeakerNames;
        PresentationSettings.ReducedMotion = ReducedMotion;
        PresentationSettings.HighContrastLabels = HighContrastLabels;
        PresentationSettings.WalkSpeedFactor = Math.Clamp(WalkSpeedPercent, 100, 150) / 100f;
        if (TextService.Locale != Locale) TextService.SetLocale(Locale);
        if (applyWindow && DisplayServer.GetName() != "headless" && !LastBell.Game.Diagnostics.QaWindow.Background)
        {
            var mode = DisplayServer.WindowGetMode();
            bool isFull = mode is DisplayServer.WindowMode.Fullscreen or DisplayServer.WindowMode.ExclusiveFullscreen;
            if (Fullscreen && !isFull) DisplayServer.WindowSetMode(DisplayServer.WindowMode.Fullscreen);
            else if (!Fullscreen && isFull) DisplayServer.WindowSetMode(DisplayServer.WindowMode.Windowed);
        }
        PresentationSettings.NotifyChanged();
        Changed?.Invoke();
    }

    /// <summary>Creates the Music/Ambience/SFX/Voice buses (sending to Master) when they do not exist.</summary>
    public static void EnsureBuses()
    {
        foreach (var name in Buses)
        {
            if (AudioServer.GetBusIndex(name) >= 0) continue;
            AudioServer.AddBus();
            int index = AudioServer.BusCount - 1;
            AudioServer.SetBusName(index, name);
            AudioServer.SetBusSend(index, "Master");
        }
    }
}
