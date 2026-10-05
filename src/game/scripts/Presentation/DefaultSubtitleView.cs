using Godot;
using LastBell.Game.Hooks;
using LastBell.Game.Runtime;

namespace LastBell.Game.Presentation;

/// <summary>
/// Default subtitle renderer: a readable panel at the bottom (speaker name + text), a speaker tag
/// above the speaking actor and a look bubble above the hero. Purely visual and mouse-transparent
/// (clicks fall through to the input router, which advances the line). The UI agent can replace it
/// with UiBus.Register(ISubtitleView).
/// </summary>
public partial class DefaultSubtitleView : Control, ISubtitleView
{
    private PanelContainer panel = null!;
    private Label speaker = null!;
    private Label text = null!;
    private PanelContainer tag = null!;
    private Label tagLabel = null!;
    private PanelContainer bark = null!;
    private Label barkLabel = null!;
    private Vector2? tagAnchor;
    private Vector2 barkAnchor;

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;

        panel = MakePanel(new Color(0.04f, 0.05f, 0.08f, 0.82f));
        panel.Position = new Vector2(220, 840);
        panel.CustomMinimumSize = new Vector2(1480, 0);
        var box = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore };
        box.AddThemeConstantOverride("separation", 6);
        panel.AddChild(box);
        speaker = MakeLabel(26, new Color(1f, 0.83f, 0.45f));
        text = MakeLabel(PresentationSettings.SubtitleFontSize, Colors.White);
        text.AutowrapMode = TextServer.AutowrapMode.WordSmart;
        text.CustomMinimumSize = new Vector2(1440, 0);
        box.AddChild(speaker);
        box.AddChild(text);
        AddChild(panel);
        panel.Visible = false;

        tag = MakePanel(new Color(0.08f, 0.08f, 0.12f, 0.85f));
        tagLabel = MakeLabel(24, new Color(1f, 0.83f, 0.45f));
        tag.AddChild(tagLabel);
        AddChild(tag);
        tag.Visible = false;

        bark = MakePanel(new Color(0.98f, 0.96f, 0.9f, 0.94f));
        barkLabel = MakeLabel(28, new Color(0.1f, 0.1f, 0.12f));
        barkLabel.AutowrapMode = TextServer.AutowrapMode.WordSmart;
        barkLabel.CustomMinimumSize = new Vector2(560, 0);
        bark.AddChild(barkLabel);
        AddChild(bark);
        bark.Visible = false;
    }

    private static PanelContainer MakePanel(Color color)
    {
        var p = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore };
        var style = new StyleBoxFlat { BgColor = color, CornerRadiusBottomLeft = 10, CornerRadiusBottomRight = 10, CornerRadiusTopLeft = 10, CornerRadiusTopRight = 10 };
        style.SetContentMarginAll(16);
        p.AddThemeStyleboxOverride("panel", style);
        return p;
    }

    private static Label MakeLabel(int size, Color color)
    {
        var l = new Label { MouseFilter = MouseFilterEnum.Ignore };
        l.AddThemeFontSizeOverride("font_size", size);
        l.AddThemeColorOverride("font_color", color);
        return l;
    }

    /// <inheritdoc />
    public void ShowLine(SubtitleLine line)
    {
        text.AddThemeFontSizeOverride("font_size", PresentationSettings.SubtitleFontSize);
        speaker.Text = line.Speaker;
        speaker.Visible = PresentationSettings.SpeakerNames && line.Speaker.Length > 0;
        text.Text = line.Text;
        text.VisibleCharacters = 0;
        panel.Visible = PresentationSettings.Subtitles;
        panel.ResetSize();
        tagAnchor = line.SpeakerAnchor;
        tagLabel.Text = line.Speaker;
        tag.Visible = tagAnchor is not null && line.Speaker.Length > 0 && PresentationSettings.SpeakerNames;
        tag.ResetSize();
        PlaceTag();
    }

    /// <inheritdoc />
    public void SetReveal(int visibleCharacters) => text.VisibleCharacters = visibleCharacters;

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
        if (tag.Visible) PlaceTag();
        if (bark.Visible) PlaceBark();
    }

    private void PlaceTag()
    {
        if (tagAnchor is not { } a) return;
        var size = tag.Size;
        tag.Position = ClampToScreen(a - new Vector2(size.X / 2, size.Y + 16), size);
    }

    private void PlaceBark()
    {
        var size = bark.Size;
        // Above the hero's head, clear of the bottom subtitle panel.
        bark.Position = ClampToScreen(barkAnchor - new Vector2(size.X / 2, size.Y + 24), size);
    }

    private static Vector2 ClampToScreen(Vector2 p, Vector2 size) =>
        new(Mathf.Clamp(p.X, 12, 1920 - size.X - 12), Mathf.Clamp(p.Y, 12, 1080 - size.Y - 12));
}
