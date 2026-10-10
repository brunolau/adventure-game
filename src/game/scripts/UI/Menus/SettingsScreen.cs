using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using LastBell.Core.State;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Menus;

/// <summary>
/// Settings: game (the difficulty of the running game, saved with it; docs/DECISIONS.md "Difficulty settings"), audio (master, music, ambience, effects, voices, voice-over on/off), text and subtitles (speed,
/// auto-advance, subtitles on/off, size with preview, contrast background, speaker names,
/// language), display (fullscreen / windowed, HUD scale 100–200 % for AT08) and accessibility
/// (reduced motion, high-contrast labels, cursor highlight, Space reminder, tips again), plus the
/// controls list. Every change applies at once and is saved to user://settings.cfg.
/// </summary>
public partial class SettingsScreen : ModalScreen
{
    /// <summary>The tab shown on the next open (UI-only memory).</summary>
    public static int LastTab { get; set; }
    // Voice-over toggle: draft rows in docs/writing/out_v4/ui_voice.csv; the table wins once the rows are in ui.csv.
    private static readonly UiString VoiceOverLabel = new("ui.settings.voice_over", "Hovorené dialógy");
    private static readonly UiString VoiceOverDesc = new("ui.settings.voice_over_desc",
        "Postavy hovoria nahlas. Keď sú vypnuté, titulky sa posúvajú podľa dĺžky textu.");
    // Dubbing language (2026-10-10): the owner approved the rows (docs/writing/out_v7/ui_voice_language.csv) and
    // ui.csv has them; the texts here are the fallback.
    private static readonly (string Key, string Sk, string En) VoiceLanguageLabel = ("ui.settings.voice_language", "Jazyk dabingu", "Voice language");
    private static readonly (string Key, string Sk, string En) VoiceLanguageAuto = ("ui.settings.voice_language_auto", "Ako texty", "Same as the text");
    private readonly List<Button> tabs = new();
    private VBoxContainer content = null!;
    private int tab;
    private Control? languageRow;
    private bool refocusLanguage;

    /// <summary>Godot constructor.</summary>
    public SettingsScreen() { PreferredSize = new Vector2(1500, 1020); } // 1020: the Sound tab with its dubbing row fits without scrolling

    /// <inheritdoc />
    protected override void Build()
    {
        SetTitle(Ui.T("ui.settings.title"));
        tabs.Clear(); // Build runs again after a change of the language (ModalScreen.Relocalize)
        // Phones (touch mode, UI at 200 %): the tabs stand in a column beside the rows. In a row they wrap to two lines
        // and leave the list a strip of two rows (seen on the emulator 2026-10-09); beside it the list has the whole
        // height of the panel. "Restore defaults" goes under the tabs.
        bool columns = TouchMode.Enabled;
        Container row = columns ? Ui.VBox(8) : new HFlowContainer();
        row.AddThemeConstantOverride("h_separation", 10);
        row.AddThemeConstantOverride("v_separation", 10);
        var group = new ButtonGroup();
        string[] names = { Ui.T(DifficultyText.SettingsTab), Ui.T("ui.settings.tab_audio"), Ui.T("ui.settings.tab_text"), Ui.T("ui.settings.tab_display"),
                           Ui.T("ui.settings.tab_accessibility"), Ui.T("ui.settings.tab_controls") };
        for (int i = 0; i < names.Length; i++)
        {
            int index = i;
            var b = Ui.Tab(names[i], group);
            b.Toggled += on => { if (on) { tab = LastTab = index; Rebuild(); } };
            tabs.Add(b);
            row.AddChild(b);
        }
        content = Ui.VBox(18);
        var reset = Ui.Button(Ui.T("ui.settings.reset_defaults"), () => UiRoot.Instance?.Confirm(Ui.T("ui.settings.reset_confirm"), Ui.T("ui.settings.reset_defaults"), () =>
        {
            UiSettings.ResetDefaults();
            Commit();
            Rebuild();
        }), "FlatButton");
        if (columns)
        {
            row.AddChild(reset);
            var tabList = Ui.Scroll(row);
            tabList.SizeFlagsHorizontal = SizeFlags.Fill; // as wide as the widest tab
            var split = Ui.HBox(22);
            split.SizeFlagsVertical = SizeFlags.ExpandFill;
            split.AddChild(tabList);
            split.AddChild(Ui.Scroll(content));
            Body.AddChild(split);
            return;
        }
        Body.AddChild(row);
        Body.AddChild(Ui.Scroll(content));
        var bottom = Ui.HBox(12);
        bottom.AddChild(Ui.Spacer());
        bottom.AddChild(reset);
        Body.AddChild(bottom);
    }

    /// <inheritdoc />
    protected override void Refresh()
    {
        tab = LastTab;
        tabs[tab].SetPressedNoSignal(true);
        Rebuild();
    }

    /// <inheritdoc />
    protected override Control? InitialFocus()
    {
        // The player changed the language and the screen was made again (ISSUES UI-07): the focus goes back to the
        // choice just made, not to the tab.
        if (refocusLanguage)
        {
            refocusLanguage = false;
            if (languageRow is not null && IsInstanceValid(languageRow) && PressedChoice(languageRow) is { } chosen) return chosen;
        }
        return tabs[tab];
    }

    private static Button? PressedChoice(Node root)
    {
        foreach (var child in root.GetChildren())
        {
            if (child is Button { ToggleMode: true, ButtonPressed: true } button) return button;
            if (PressedChoice(child) is { } inner) return inner;
        }
        return null;
    }

    /// <inheritdoc />
    public override void Open()
    {
        refocusLanguage = false;
        base.Open();
    }

    private static void Commit()
    {
        UiSettings.Apply();
        UiSettings.Save();
    }

    private void Rebuild()
    {
        Ui.Clear(content);
        switch (tab)
        {
            case 0:
                // Game: the difficulty of the running game (saved with it); on the title screen only how it works.
                if (UiRoot.Instance?.MainMenuOpen ?? true)
                {
                    content.AddChild(Labelled(Ui.T(DifficultyText.Title), Ui.Para(Ui.T(DifficultyText.SettingsInMenu))));
                    break;
                }
                var game = GameRuntime.Instance;
                var options = DifficultyText.All.Select(d => (Ui.T(DifficultyText.Name(d)), (int)d)).ToArray();
                Label? describe = null;
                content.AddChild(ChoiceRow(Ui.T(DifficultyText.Title), options, () => (int)game.State.Difficulty, v =>
                {
                    game.SetDifficulty((Difficulty)v);
                    if (describe is not null) describe.Text = Ui.T(DifficultyText.Description((Difficulty)v));
                }));
                describe = Ui.Para(Ui.T(DifficultyText.Description(game.State.Difficulty)));
                content.AddChild(describe);
                content.AddChild(Ui.Para(Ui.T(DifficultyText.SettingsInGame), "CaptionLabel"));
                break;
            case 1:
                string[] volumeKeys = { "ui.settings.volume_master", "ui.settings.volume_music", "ui.settings.volume_ambience", "ui.settings.volume_sfx", "ui.settings.volume_voice" };
                for (int i = 0; i < volumeKeys.Length; i++)
                {
                    int bus = i;
                    content.AddChild(SliderRow(Ui.T(volumeKeys[i]), 0, 100, 5, () => UiSettings.Volume[bus], v => UiSettings.Volume[bus] = (int)v,
                        v => Ui.T("ui.settings.volume_value", ("percent", ((int)v).ToString()))));
                    if (volumeKeys[i] == "ui.settings.volume_voice") // voice-over on/off right under the Voice volume
                    {
                        content.AddChild(ToggleRow(Ui.T(VoiceOverLabel), Ui.T(VoiceOverDesc), () => UiSettings.VoiceOver, v => UiSettings.VoiceOver = v));
                        // Only where there is a choice: the Android build carries one dub.
                        if (LastBell.Game.Audio.AudioService.VoiceLanguagesInBuild.Count > 1)
                            content.AddChild(ChoiceRow(TouchMode.Text(VoiceLanguageLabel.Key, VoiceLanguageLabel.Sk, VoiceLanguageLabel.En),
                                new[]
                                {
                                    (TouchMode.Text(VoiceLanguageAuto.Key, VoiceLanguageAuto.Sk, VoiceLanguageAuto.En), 0),
                                    (Ui.T("ui.settings.language_sk"), 1), (Ui.T("ui.settings.language_en"), 2),
                                },
                                () => UiSettings.VoiceLanguage switch { "sk" => 1, "en" => 2, _ => 0 },
                                v => UiSettings.VoiceLanguage = v switch { 1 => "sk", 2 => "en", _ => "auto" }));
                    }
                }
                content.AddChild(ToggleRow(Ui.T("ui.settings.mute_unfocused"), "", () => UiSettings.MuteUnfocused, v => UiSettings.MuteUnfocused = v));
                break;
            case 2:
                content.AddChild(ChoiceRow(Ui.T("ui.settings.text_speed"),
                    new[] { (Ui.T("ui.settings.text_speed_slow"), 0), (Ui.T("ui.settings.text_speed_normal"), 1), (Ui.T("ui.settings.text_speed_fast"), 2), (Ui.T("ui.settings.text_speed_instant"), 3) },
                    () => (int)UiSettings.TextSpeed, v => UiSettings.TextSpeed = (TextSpeed)v));
                content.AddChild(ToggleRow(Ui.T("ui.settings.auto_advance"), "", () => UiSettings.AutoAdvance, v => UiSettings.AutoAdvance = v));
                content.AddChild(ChoiceRow(Ui.T("ui.settings.auto_advance_speed"),
                    new[] { (Ui.T("ui.settings.text_speed_slow"), 160), (Ui.T("ui.settings.text_speed_normal"), 100), (Ui.T("ui.settings.text_speed_fast"), 60) },
                    () => (int)Math.Round(UiSettings.AutoAdvancePace * 100), v => UiSettings.AutoAdvancePace = v / 100f));
                content.AddChild(ToggleRow(Ui.T("ui.settings.subtitles"), "", () => UiSettings.Subtitles, v => UiSettings.Subtitles = v));
                Label? preview = null;
                PanelContainer? previewPanel = null;
                content.AddChild(SliderRow(Ui.T("ui.settings.subtitle_size"), 18, 48, 2, () => UiSettings.SubtitleSize, v =>
                {
                    UiSettings.SubtitleSize = (int)v;
                    preview?.AddThemeFontSizeOverride("font_size", (int)v);
                }, v => Ui.T("ui.settings.subtitle_size_value", ("size", ((int)v).ToString()))));
                previewPanel = new PanelContainer();
                previewPanel.AddThemeStyleboxOverride("panel", UiTheme.DarkPanel(0.9f, 18, 14));
                preview = Ui.Para(Ui.T("ui.settings.subtitle_preview"), "OnDarkLabel");
                preview.AddThemeFontSizeOverride("font_size", UiSettings.SubtitleSize);
                previewPanel.AddChild(preview);
                content.AddChild(previewPanel);
                content.AddChild(ToggleRow(Ui.T("ui.settings.subtitle_background"), "", () => UiSettings.SubtitleBackground, v => UiSettings.SubtitleBackground = v));
                content.AddChild(ToggleRow(Ui.T("ui.settings.speaker_names"), "", () => UiSettings.SpeakerNames, v => UiSettings.SpeakerNames = v));
                // The change rebuilds the HUD and every screen, this one included (UiRoot.Relocalize, ISSUES UI-07).
                languageRow = ChoiceRow(Ui.T("ui.settings.language"),
                    new[] { (Ui.T("ui.settings.language_sk"), 0), (Ui.T("ui.settings.language_en"), 1) },
                    () => UiSettings.Locale == "en" ? 1 : 0, v =>
                    {
                        refocusLanguage = true;
                        UiSettings.Locale = v == 1 ? "en" : "sk";
                    });
                content.AddChild(languageRow);
                break;
            case 3:
                if (!TouchMode.IsMobile) // a phone has no window mode
                    content.AddChild(ChoiceRow(Ui.T("ui.settings.window_mode"),
                        new[] { (Ui.T("ui.settings.windowed"), 0), (Ui.T("ui.settings.fullscreen"), 1) },
                        () => UiSettings.Fullscreen ? 1 : 0, v => UiSettings.Fullscreen = v == 1));
                content.AddChild(ChoiceRow(Ui.T("ui.settings.hud_scale"),
                    new[] { ("100 %", 100), ("125 %", 125), ("150 %", 150), ("175 %", 175), ("200 %", 200) },
                    () => UiSettings.HudScalePercent, v => UiSettings.HudScalePercent = v));
                break;
            case 4:
                content.AddChild(ToggleRow(Ui.T("ui.settings.reduced_motion"), Ui.T("ui.settings.reduced_motion_desc"), () => UiSettings.ReducedMotion, v => UiSettings.ReducedMotion = v));
                content.AddChild(ToggleRow(Ui.T("ui.settings.high_contrast_labels"), Ui.T("ui.settings.high_contrast_labels_desc"), () => UiSettings.HighContrastLabels, v => UiSettings.HighContrastLabels = v));
                if (!TouchMode.Enabled) // no cursor on a touch screen
                    content.AddChild(ToggleRow(Ui.T("ui.settings.cursor_highlight"), "", () => UiSettings.CursorHighlight, v => UiSettings.CursorHighlight = v));
                content.AddChild(ChoiceRow(Ui.T("ui.settings.walk_speed"),
                    new[] { (Ui.T("ui.settings.walk_speed_calm"), 100), (Ui.T("ui.settings.text_speed_normal"), 125), (Ui.T("ui.settings.walk_speed_brisk"), 150) },
                    () => UiSettings.WalkSpeedPercent, v => UiSettings.WalkSpeedPercent = v));
                if (!TouchMode.Enabled) // the Space reminder; touch has the Eye button
                    content.AddChild(ToggleRow(Ui.T("ui.settings.hotspot_key_hint"), Ui.T("ui.settings.hotspot_key_hint_desc"), () => UiSettings.HotspotKeyHint, v => UiSettings.HotspotKeyHint = v));
                var tips = Ui.Button(Ui.T("ui.settings.reset_tips"), () =>
                {
                    UiSettings.TipsShown = false;
                    UiSettings.Save();
                    ShowStatus(Ui.T("ui.settings.tips_reset_done"));
                });
                tips.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
                content.AddChild(tips);
                break;
            default:
                foreach (var line in HelpScreen.ControlLines()) content.AddChild(Ui.Para("• " + line));
                break;
        }
    }

    private static Control Labelled(string label, Control control, string description = "")
    {
        var box = Ui.VBox(4);
        var row = Ui.HBox(20);
        var l = Ui.Label(label, "SubheadingLabel", wrap: true);
        // Phones: the logical screen is 960 px wide and the tabs take a column of it; a narrower label (it wraps) and a
        // shorter slider keep a row inside the panel, so the panel is not scaled down as a whole (ModalScreen).
        l.CustomMinimumSize = new Vector2(TouchMode.Enabled ? 220 : 420, 0);
        l.SizeFlagsHorizontal = SizeFlags.Fill;
        l.VerticalAlignment = VerticalAlignment.Center;
        row.AddChild(l);
        control.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        row.AddChild(control);
        box.AddChild(row);
        if (description.Length > 0) box.AddChild(Ui.Para(description, "CaptionLabel"));
        return box;
    }

    private static Control SliderRow(string label, double min, double max, double step, Func<double> get, Action<double> set, Func<double, string> format)
    {
        var row = Ui.HBox(16);
        var slider = new HSlider { MinValue = min, MaxValue = max, Step = step, Value = get(), CustomMinimumSize = new Vector2(TouchMode.Enabled ? 200 : 360, UiTheme.MinHit), SizeFlagsHorizontal = SizeFlags.ExpandFill, SizeFlagsVertical = SizeFlags.ShrinkCenter };
        var value = Ui.Label(format(get()), "");
        value.CustomMinimumSize = new Vector2(110, 0);
        value.VerticalAlignment = VerticalAlignment.Center;
        slider.ValueChanged += v =>
        {
            set(v);
            value.Text = format(v);
            Commit();
        };
        row.AddChild(slider);
        row.AddChild(value);
        return Labelled(label, row);
    }

    private static Control ToggleRow(string label, string description, Func<bool> get, Action<bool> set)
    {
        var toggle = Ui.Tab(Ui.T(get() ? "ui.common.on" : "ui.common.off"));
        toggle.ButtonPressed = get();
        toggle.CustomMinimumSize = new Vector2(200, UiTheme.MinHit);
        toggle.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
        toggle.Toggled += on =>
        {
            set(on);
            toggle.Text = Ui.T(on ? "ui.common.on" : "ui.common.off");
            Commit();
        };
        var holder = Ui.HBox(0);
        holder.AddChild(toggle);
        return Labelled(label, holder, description);
    }

    private static Control ChoiceRow(string label, (string Text, int Value)[] options, Func<int> get, Action<int> set)
    {
        var flow = new HFlowContainer();
        flow.AddThemeConstantOverride("h_separation", 8);
        flow.AddThemeConstantOverride("v_separation", 8);
        var group = new ButtonGroup();
        foreach (var (text, value) in options)
        {
            int v = value;
            var b = Ui.Tab(text, group);
            b.ButtonPressed = get() == v;
            b.Toggled += on =>
            {
                if (!on) return;
                set(v);
                Commit();
            };
            flow.AddChild(b);
        }
        return Labelled(label, flow);
    }
}
