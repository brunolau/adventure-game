using System;
using System.Linq;
using Godot;
using LastBell.Core.Content;
using LastBell.Game.Hooks;
using LastBell.Game.PlayerInput;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Menus;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Cutscenes;

/// <summary>
/// Cutscene framing (<see cref="ICutsceneView"/>): letterbox, one picture per beat
/// (<c>res://assets/cutscenes/&lt;CS&gt;_&lt;n&gt;.webp</c>, n from 1) or, while the art does not exist, a
/// styled card — with the QA flag --dev (PresentationSettings.DevNotes) it prints the beat's shot direction on it as a dev aid (shots are stage
/// directions, not player text, TEXT-03). The last beat of the finale shows the "end of the story"
/// title. Lines and their minimum durations (duration_min_s) are played by the world runtime's
/// presenter through the subtitle view, which sits above this frame. Skippable cutscenes show a
/// skip button (the whole cutscene, like a double Esc; one Esc skips one line, PT-F13). Mouse-transparent
/// elsewhere: a click advances the line.
/// A beat picture can carry a simple camera move (pan / zoom between two rects of the picture,
/// <see cref="CutsceneCamera"/>, <c>res://data/cutscene_camera.json</c>); reduced motion shows its end rect.
/// </summary>
public partial class CutscenePlayer : Control, ICutsceneView
{
    private ColorRect black = null!;
    private TextureRect picture = null!;
    private CutsceneCamera.Move? move;
    private double moveSeconds;
    private double moveElapsed;
    private PanelContainer card = null!;
    private Label cardTitle = null!;
    private Label cardShot = null!;
    private Label endTitle = null!;
    private Button skip = null!;
    private ColorRect top = null!;
    private ColorRect bottom = null!;
    private CutsceneDef? current;

    /// <summary>Path of a beat picture.</summary>
    public static string BeatPath(string cutsceneId, int beatIndex) => $"res://assets/cutscenes/{cutsceneId}_{beatIndex + 1}.webp";

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
        ClipContents = true; // a zoomed picture is larger than the view
        black = new ColorRect { Color = new Color("120d0a"), MouseFilter = MouseFilterEnum.Ignore };
        black.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        AddChild(black);
        // Placed by _Process (CutsceneCamera.Layout): the whole picture stretched so the camera rect covers the view;
        // without a move that is the plain cover fit.
        picture = new TextureRect
        {
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize,
            StretchMode = TextureRect.StretchModeEnum.Scale,
            MouseFilter = MouseFilterEnum.Ignore,
        };
        AddChild(picture);

        card = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore };
        var style = UiTheme.PaperPanel(48);
        style.BgColor = new Color("efe2c6");
        card.AddThemeStyleboxOverride("panel", style);
        var box = Ui.VBox(18);
        box.MouseFilter = MouseFilterEnum.Ignore;
        box.Alignment = BoxContainer.AlignmentMode.Center;
        var emblem = new Emblem { CustomMinimumSize = new Vector2(0, 150), MouseFilter = MouseFilterEnum.Ignore, Modulate = new Color(0.55f, 0.42f, 0.3f) };
        box.AddChild(emblem);
        cardTitle = Ui.Label("", "HeadingLabel");
        cardTitle.HorizontalAlignment = HorizontalAlignment.Center;
        box.AddChild(cardTitle);
        cardShot = Ui.Label("", "ItalicLabel");
        cardShot.HorizontalAlignment = HorizontalAlignment.Center;
        cardShot.AutowrapMode = TextServer.AutowrapMode.WordSmart;
        cardShot.CustomMinimumSize = new Vector2(1100, 0);
        box.AddChild(cardShot);
        card.AddChild(box);
        AddChild(card);

        endTitle = Ui.Label("", "TitleLabel");
        endTitle.HorizontalAlignment = HorizontalAlignment.Center;
        endTitle.AddThemeFontSizeOverride("font_size", 96);
        endTitle.AddThemeColorOverride("font_color", UiTheme.BrassLight);
        endTitle.AddThemeColorOverride("font_outline_color", new Color(0, 0, 0, 0.85f));
        endTitle.AddThemeConstantOverride("outline_size", 14);
        endTitle.SetAnchorsAndOffsetsPreset(LayoutPreset.Center);
        endTitle.GrowHorizontal = GrowDirection.Both;
        endTitle.GrowVertical = GrowDirection.Both;
        AddChild(endTitle);

        top = new ColorRect { Color = Colors.Black, MouseFilter = MouseFilterEnum.Ignore };
        bottom = new ColorRect { Color = Colors.Black, MouseFilter = MouseFilterEnum.Ignore };
        AddChild(top);
        AddChild(bottom);

        // The button skips the whole cutscene (like a double Esc); a single Esc skips one line (PT-F13).
        skip = Ui.Button(Ui.T("ui.cutscene.skip") + "  (2× Esc)", () => LastBell.Game.Presentation.DialoguePresenter.Instance?.Skip(), "HudButton");
        skip.FocusMode = FocusModeEnum.None;
        skip.AddThemeFontSizeOverride("font_size", 24);
        AddChild(skip);
        Visible = false;
    }

    /// <inheritdoc />
    public void Begin(CutsceneDef cutscene)
    {
        current = cutscene;
        skip.Visible = cutscene.Skippable;
        Visible = true;
        Modulate = Colors.White;
        if (!UiSettings.ReducedMotion)
        {
            Modulate = new Color(1, 1, 1, 0);
            CreateTween().TweenProperty(this, "modulate:a", 1f, 0.35f);
        }
    }

    /// <inheritdoc />
    public void Beat(CutsceneDef cutscene, int beatIndex)
    {
        current = cutscene;
        string path = BeatPath(cutscene.Id, beatIndex);
        var texture = ResourceLoader.Exists(path) ? GD.Load<Texture2D>(path) : null;
        picture.Texture = texture;
        picture.Visible = texture is not null;
        card.Visible = texture is null;
        move = texture is null ? null : CutsceneCamera.For(cutscene.Id, beatIndex);
        moveSeconds = move?.Seconds ?? Math.Max(1.0, cutscene.Beats[beatIndex].DurationMinS);
        moveElapsed = 0;
        PlacePicture();
        int n = Array.IndexOf(GameRuntime.Instance.Content.Data.Cutscenes.ToArray(), cutscene) + 1;
        cardTitle.Text = Ui.T("ui.cutscene.scene_n", ("n", Math.Max(1, n).ToString()));
        cardShot.Text = PresentationSettings.DevNotes ? Ui.T("ui.dev.shot", ("shot", cutscene.Beats[beatIndex].Shot)) : "";
        cardShot.Visible = cardShot.Text.Length > 0;
        bool endCard = IsFinale(cutscene) && beatIndex == cutscene.Beats.Count - 1;
        endTitle.Text = endCard ? Ui.T("ui.cutscene.the_end").ToUpperInvariant() : "";
        endTitle.Visible = endCard;
        if (endCard) card.Visible = false;
        if (!UiSettings.ReducedMotion)
        {
            var target = texture is not null ? (CanvasItem)picture : card;
            target.Modulate = new Color(1, 1, 1, 0);
            CreateTween().TweenProperty(target, "modulate:a", 1f, 0.45f);
            if (endCard)
            {
                endTitle.Modulate = new Color(1, 1, 1, 0);
                CreateTween().TweenProperty(endTitle, "modulate:a", 1f, 1.2f);
            }
        }
    }

    /// <summary>The camera rect of the current beat right now (the whole picture without a move).</summary>
    public Rect2 CameraRect => move is null ? CutsceneCamera.Full
        : UiSettings.ReducedMotion ? move.To
        : CutsceneCamera.At(move, moveElapsed, moveSeconds);

    private void PlacePicture()
    {
        if (picture.Texture is null || Size.X <= 0 || Size.Y <= 0) return;
        var place = CutsceneCamera.Layout(Size, CameraRect);
        picture.Position = place.Position;
        picture.Size = place.Size;
    }

    /// <summary>True for the finale cutscene (the postgame unlock action's cutscene).</summary>
    public static bool IsFinale(CutsceneDef cutscene)
    {
        var content = GameRuntime.Instance.Content;
        var unlock = content.FindAction(content.Data.Postgame.Unlock);
        return unlock?.Cutscene == cutscene.Id;
    }

    /// <inheritdoc />
    public void End(CutsceneDef cutscene)
    {
        current = null;
        if (UiSettings.ReducedMotion) { Visible = false; return; }
        var tween = CreateTween();
        tween.TweenProperty(this, "modulate:a", 0f, 0.3f);
        tween.TweenCallback(Callable.From(() => { if (current is null) Visible = false; }));
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        if (!Visible) return;
        if (move is not null) moveElapsed += delta;
        PlacePicture();
        float bar = Math.Max(60, Size.Y * 0.1f);
        top.Position = Vector2.Zero;
        top.Size = new Vector2(Size.X, bar);
        bottom.Position = new Vector2(0, Size.Y - bar);
        bottom.Size = new Vector2(Size.X, bar);
        var cardSize = new Vector2(Math.Min(1300, Size.X - 200), Math.Min(560, Size.Y - 2 * bar - 220));
        card.Size = cardSize;
        card.CustomMinimumSize = cardSize;
        card.Position = new Vector2((Size.X - cardSize.X) / 2, bar + 60);
        skip.ResetSize();
        skip.Position = new Vector2(Size.X - skip.Size.X - 40, (bar - skip.Size.Y) / 2);
    }
}
