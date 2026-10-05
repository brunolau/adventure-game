using System;
using Godot;
using LastBell.Game.Hooks;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Hud;

/// <summary>
/// Subtitle renderer (<see cref="ISubtitleView"/>): a readable panel at the bottom with the speaker
/// name and the wrapped text (size, background and name from the settings), a name tag above the
/// speaking actor, a "continue" marker when the line is fully shown, and the look bubble above the
/// hero. Timing and advancing stay in the world runtime's DialoguePresenter; this view is purely
/// visual and mouse-transparent (a click anywhere advances through the input router).
/// Lives in the unscaled UI layer (its size has its own setting).
/// </summary>
public partial class SubtitleView : Control, ISubtitleView
{
    private PanelContainer panel = null!;
    private Label speaker = null!;
    private Label text = null!;
    private Glyph more = null!;
    private PanelContainer tag = null!;
    private Label tagLabel = null!;
    private PanelContainer bark = null!;
    private Label barkLabel = null!;
    private Vector2? tagAnchor;
    private Vector2 barkAnchor;
    private bool revealedAll;
    private double blink;

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;

        panel = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore };
        var box = Ui.VBox(4);
        box.MouseFilter = MouseFilterEnum.Ignore;
        speaker = Ui.Label("", "SpeakerLabel");
        text = Ui.Label("", "OnDarkLabel");
        text.AutowrapMode = TextServer.AutowrapMode.WordSmart;
        text.AddThemeColorOverride("font_outline_color", new Color(0, 0, 0, 0.9f));
        speaker.AddThemeColorOverride("font_outline_color", new Color(0, 0, 0, 0.9f));
        var textRow = Ui.HBox(8);
        textRow.MouseFilter = MouseFilterEnum.Ignore;
        text.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        more = new Glyph(GlyphKind.Down, 26, UiTheme.BrassLight) { SizeFlagsVertical = SizeFlags.ShrinkEnd };
        textRow.AddChild(text);
        textRow.AddChild(more);
        box.AddChild(speaker);
        box.AddChild(textRow);
        panel.AddChild(box);
        AddChild(panel);
        panel.Visible = false;

        tag = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore };
        tag.AddThemeStyleboxOverride("panel", UiTheme.DarkPanel(0.88f, 10, 10));
        tagLabel = Ui.Label("", "SpeakerLabel");
        tagLabel.AddThemeFontSizeOverride("font_size", 25);
        tag.AddChild(tagLabel);
        AddChild(tag);
        tag.Visible = false;

        bark = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore };
        var barkStyle = UiTheme.PaperPanel(18);
        barkStyle.ShadowSize = 10;
        bark.AddThemeStyleboxOverride("panel", barkStyle);
        barkLabel = Ui.Label("", "ItalicLabel");
        barkLabel.AutowrapMode = TextServer.AutowrapMode.WordSmart;
        bark.AddChild(barkLabel);
        AddChild(bark);
        bark.Visible = false;
        ApplySettings();
        UiSettings.Changed += ApplySettings;
    }

    /// <inheritdoc />
    public override void _ExitTree() => UiSettings.Changed -= ApplySettings;

    private void ApplySettings()
    {
        int size = Math.Clamp(UiSettings.SubtitleSize, 18, 48);
        text.AddThemeFontSizeOverride("font_size", size);
        speaker.AddThemeFontSizeOverride("font_size", Math.Max(22, (int)(size * 0.8f)));
        var style = UiSettings.SubtitleBackground ? UiTheme.DarkPanel(0.86f, 20, 16) : new StyleBoxFlat { BgColor = new Color(0, 0, 0, 0) };
        if (!UiSettings.SubtitleBackground) style.SetContentMarginAll(20);
        panel.AddThemeStyleboxOverride("panel", style);
        int outline = UiSettings.SubtitleBackground ? 0 : Math.Max(6, size / 4);
        text.AddThemeConstantOverride("outline_size", outline);
        speaker.AddThemeConstantOverride("outline_size", outline);
        barkLabel.AddThemeFontSizeOverride("font_size", Math.Clamp(size - 4, 22, 44));
        barkLabel.CustomMinimumSize = new Vector2(Math.Clamp(size * 17, 420, 760), 0);
    }

    /// <inheritdoc />
    public void ShowLine(SubtitleLine line)
    {
        speaker.Text = line.Speaker;
        speaker.Visible = UiSettings.SpeakerNames && line.Speaker.Length > 0;
        text.Text = line.Text;
        text.VisibleCharacters = 0;
        revealedAll = false;
        more.Visible = false;
        panel.Visible = UiSettings.Subtitles;
        float width = Math.Min(1480, Size.X - 120);
        text.CustomMinimumSize = new Vector2(width - 90, 0);
        panel.CustomMinimumSize = new Vector2(width, 0);
        panel.ResetSize();
        PlacePanel();
        // In a cutscene the frame covers the scene: no tag over an actor that is not visible.
        tagAnchor = line.Line.IsCutscene ? null : line.SpeakerAnchor;
        tagLabel.Text = line.Speaker;
        tag.Visible = tagAnchor is not null && line.Speaker.Length > 0 && UiSettings.SpeakerNames;
        tag.ResetSize();
        PlaceTag();
    }

    /// <inheritdoc />
    public void SetReveal(int visibleCharacters)
    {
        text.VisibleCharacters = visibleCharacters;
        revealedAll = visibleCharacters < 0;
        more.Visible = revealedAll;
        if (revealedAll) blink = 0;
    }

    /// <inheritdoc />
    public void HideLine()
    {
        panel.Visible = false;
        tag.Visible = false;
    }

    /// <inheritdoc />
    public void ShowBark(BarkLine line)
    {
        barkLabel.Text = line.Text;
        barkAnchor = line.Anchor;
        bark.Visible = true;
        bark.ResetSize();
        PlaceBark();
    }

    /// <inheritdoc />
    public void HideBark() => bark.Visible = false;

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        if (panel.Visible)
        {
            PlacePanel();
            if (revealedAll && !UiSettings.ReducedMotion)
            {
                blink += delta;
                more.Modulate = new Color(1, 1, 1, 0.55f + 0.45f * (float)Math.Abs(Math.Sin(blink * 2.2)));
            }
            else more.Modulate = Colors.White;
        }
        if (tag.Visible) PlaceTag();
        if (bark.Visible) PlaceBark();
    }

    private void PlacePanel()
    {
        var size = panel.Size;
        panel.Position = new Vector2((Size.X - size.X) / 2, Size.Y - size.Y - 34);
    }

    private void PlaceTag()
    {
        if (tagAnchor is not { } a) return;
        var size = tag.Size;
        tag.Position = Clamp(a - new Vector2(size.X / 2, size.Y + 18), size);
    }

    private void PlaceBark()
    {
        var size = bark.Size;
        var p = Clamp(barkAnchor - new Vector2(size.X / 2, size.Y + 26), size);
        // Keep the bubble clear of the subtitle panel.
        if (panel.Visible && p.Y + size.Y > panel.Position.Y - 10) p.Y = Math.Max(12, panel.Position.Y - size.Y - 10);
        bark.Position = p;
    }

    private Vector2 Clamp(Vector2 p, Vector2 size) =>
        new(Math.Max(12, Math.Min(p.X, Size.X - size.X - 12)), Math.Max(12, Math.Min(p.Y, Size.Y - size.Y - 12)));
}
