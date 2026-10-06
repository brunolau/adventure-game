using System;
using System.Collections.Generic;
using Godot;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Menus;

/// <summary>
/// Settings: audio (master, music, ambience, effects, voices), text and subtitles (speed,
/// auto-advance, subtitles on/off, size with preview, contrast background, speaker names,
/// language), display (fullscreen / windowed, HUD scale 100–200 % for AT08) and accessibility
/// (reduced motion, high-contrast labels, cursor highlight, Space reminder, tips again), plus the
/// controls list. Every change applies at once and is saved to user://settings.cfg.
/// </summary>
public partial class SettingsScreen : ModalScreen
{
    /// <summary>The tab shown on the next open (UI-only memory).</summary>
    public static int LastTab { get; set; }
    private readonly List<Button> tabs = new();
    private VBoxContainer content = null!;
    private int tab;

    /// <summary>Godot constructor.</summary>
    public SettingsScreen() { PreferredSize = new Vector2(1500, 940); }

    /// <inheritdoc />
    protected override void Build()
    {
        SetTitle(Ui.T("ui.settings.title"));
        var row = new HFlowContainer();
        row.AddThemeConstantOverride("h_separation", 10);
        row.AddThemeConstantOverride("v_separation", 10);
        var group = new ButtonGroup();
        string[] keys = { "ui.settings.tab_audio", "ui.settings.tab_text", "ui.settings.tab_display", "ui.settings.tab_accessibility", "ui.settings.tab_controls" };
        for (int i = 0; i < keys.Length; i++)
        {
            int index = i;
            var b = Ui.Tab(Ui.T(keys[i]), group);
            b.Toggled += on => { if (on) { tab = LastTab = index; Rebuild(); } };
            tabs.Add(b);
            row.AddChild(b);
        }
        Body.AddChild(row);
        content = Ui.VBox(18);
        Body.AddChild(Ui.Scroll(content));
        var bottom = Ui.HBox(12);
        bottom.AddChild(Ui.Spacer());
        bottom.AddChild(Ui.Button(Ui.T("ui.settings.reset_defaults"), () => UiRoot.Instance?.Confirm(Ui.T("ui.settings.reset_confirm"), Ui.T("ui.settings.reset_defaults"), () =>
        {
            UiSettings.ResetDefaults();
            Commit();
            Rebuild();
        }), "FlatButton"));
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
    protected override Control? InitialFocus() => tabs[tab];

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
                string[] volumeKeys = { "ui.settings.volume_master", "ui.settings.volume_music", "ui.settings.volume_ambience", "ui.settings.volume_sfx", "ui.settings.volume_voice" };
                for (int i = 0; i < volumeKeys.Length; i++)
                {
                    int bus = i;
                    content.AddChild(SliderRow(Ui.T(volumeKeys[i]), 0, 100, 5, () => UiSettings.Volume[bus], v => UiSettings.Volume[bus] = (int)v,
                        v => Ui.T("ui.settings.volume_value", ("percent", ((int)v).ToString()))));
                }
                content.AddChild(ToggleRow(Ui.T("ui.settings.mute_unfocused"), "", () => UiSettings.MuteUnfocused, v => UiSettings.MuteUnfocused = v));
                break;
            case 1:
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
                content.AddChild(ChoiceRow(Ui.T("ui.settings.language"),
                    new[] { (Ui.T("ui.settings.language_sk"), 0), (Ui.T("ui.settings.language_en"), 1) },
                    () => UiSettings.Locale == "en" ? 1 : 0, v => UiSettings.Locale = v == 1 ? "en" : "sk"));
                break;
            case 2:
                content.AddChild(ChoiceRow(Ui.T("ui.settings.window_mode"),
                    new[] { (Ui.T("ui.settings.windowed"), 0), (Ui.T("ui.settings.fullscreen"), 1) },
                    () => UiSettings.Fullscreen ? 1 : 0, v => UiSettings.Fullscreen = v == 1));
                content.AddChild(ChoiceRow(Ui.T("ui.settings.hud_scale"),
                    new[] { ("100 %", 100), ("125 %", 125), ("150 %", 150), ("175 %", 175), ("200 %", 200) },
                    () => UiSettings.HudScalePercent, v => UiSettings.HudScalePercent = v));
                break;
            case 3:
                content.AddChild(ToggleRow(Ui.T("ui.settings.reduced_motion"), Ui.T("ui.settings.reduced_motion_desc"), () => UiSettings.ReducedMotion, v => UiSettings.ReducedMotion = v));
                content.AddChild(ToggleRow(Ui.T("ui.settings.high_contrast_labels"), Ui.T("ui.settings.high_contrast_labels_desc"), () => UiSettings.HighContrastLabels, v => UiSettings.HighContrastLabels = v));
                content.AddChild(ToggleRow(Ui.T("ui.settings.cursor_highlight"), "", () => UiSettings.CursorHighlight, v => UiSettings.CursorHighlight = v));
                content.AddChild(ChoiceRow(Ui.T("ui.settings.walk_speed"),
                    new[] { (Ui.T("ui.settings.walk_speed_calm"), 100), (Ui.T("ui.settings.text_speed_normal"), 125), (Ui.T("ui.settings.walk_speed_brisk"), 150) },
                    () => UiSettings.WalkSpeedPercent, v => UiSettings.WalkSpeedPercent = v));
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
                foreach (var line in HelpScreen.ControlKeys) content.AddChild(Ui.Para("• " + Ui.T(line)));
                break;
        }
    }

    private static Control Labelled(string label, Control control, string description = "")
    {
        var box = Ui.VBox(4);
        var row = Ui.HBox(20);
        var l = Ui.Label(label, "SubheadingLabel", wrap: true);
        l.CustomMinimumSize = new Vector2(420, 0);
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
        var slider = new HSlider { MinValue = min, MaxValue = max, Step = step, Value = get(), CustomMinimumSize = new Vector2(360, UiTheme.MinHit), SizeFlagsHorizontal = SizeFlags.ExpandFill, SizeFlagsVertical = SizeFlags.ShrinkCenter };
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
