using System.Collections.Generic;
using Godot;
using LastBell.Core.Rules;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Cutscenes;

/// <summary>
/// The ending after the finale (epilogue_rules): only completed side episodes, in Q1–Q9 order
/// (Core's <see cref="Epilogue.Select"/>), about six seconds each (5–7 s; Enter / click goes on,
/// Esc skips to the credits); without any completed episode the credits roll directly. Then the
/// credits roll and, the first time, the postgame note (free play in the stabilised windows).
/// From the album it can be replayed with the episodes completed since. Pure presentation: no rule
/// state changes. Pictures: <c>res://assets/cutscenes/EPILOGUE_&lt;n&gt;.webp</c> (n from 1, data order; see
/// <see cref="ShotPath"/>) or a styled
/// card with the shot caption.
/// </summary>
public partial class EndingSequence : ModalScreen
{
    private const double ShotSeconds = 6.0;
    private TextureRect picture = null!;
    private PanelContainer card = null!;
    private Label caption = null!;
    private Label line = null!;
    private Label counter = null!;
    private IReadOnlyList<EpilogueShot> shots = new List<EpilogueShot>();
    private int index;
    private double elapsed;
    private bool rolling;

    /// <summary>True when replayed from the album (no postgame note afterwards).</summary>
    public bool Replay { get; set; }

    /// <summary>Godot constructor.</summary>
    public EndingSequence()
    {
        PreferredSize = new Vector2(1720, 980);
        Closable = false;
        Dim = 0.96f;
    }

    /// <inheritdoc />
    protected override void Build()
    {
        Panel.AddThemeStyleboxOverride("panel", new StyleBoxFlat { BgColor = new Color(0, 0, 0, 0) });
        // The panel covers almost the whole screen: let clicks on it reach _GuiInput (click = next shot);
        // a PanelContainer stops them by default, so "click goes on" never worked (docs/MILESTONE2.md, bug M2-02).
        Panel.MouseFilter = MouseFilterEnum.Pass;
        for (Node? n = Body; n is not null && n != Panel; n = n.GetParent())
            if (n is Control c) c.MouseFilter = MouseFilterEnum.Pass;
        picture = new TextureRect
        {
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize,
            StretchMode = TextureRect.StretchModeEnum.KeepAspectCentered,
            CustomMinimumSize = new Vector2(0, 640),
            MouseFilter = MouseFilterEnum.Ignore,
        };
        Body.AddChild(picture);
        card = new PanelContainer { CustomMinimumSize = new Vector2(0, 640), MouseFilter = MouseFilterEnum.Ignore };
        var style = UiTheme.PaperPanel(60);
        style.BgColor = new Color("efe2c6");
        card.AddThemeStyleboxOverride("panel", style);
        var box = Ui.VBox(24);
        box.Alignment = BoxContainer.AlignmentMode.Center;
        box.AddChild(new Menus.Emblem { CustomMinimumSize = new Vector2(0, 140), Modulate = new Color(0.55f, 0.42f, 0.3f) });
        caption = Ui.Label("", "HeadingLabel", wrap: true);
        caption.HorizontalAlignment = HorizontalAlignment.Center;
        caption.CustomMinimumSize = new Vector2(1100, 0);
        box.AddChild(caption);
        card.AddChild(box);
        Body.AddChild(card);
        line = Ui.Label("", "OnDarkLabel", wrap: true);
        line.HorizontalAlignment = HorizontalAlignment.Center;
        line.AddThemeFontSizeOverride("font_size", 36);
        line.CustomMinimumSize = new Vector2(1300, 0);
        Body.AddChild(line);
        counter = Ui.Label("", "OnDarkCaption");
        counter.HorizontalAlignment = HorizontalAlignment.Center;
        Body.AddChild(counter);
    }

    /// <inheritdoc />
    protected override void Refresh()
    {
        var game = GameRuntime.Instance;
        shots = Epilogue.Select(game.Content, game.State);
        index = -1;
        rolling = false;
        if (shots.Count == 0) CallDeferred(MethodName.RollCredits);
        else Next();
    }

    private void Next()
    {
        index++;
        elapsed = 0;
        if (index >= shots.Count)
        {
            RollCredits();
            return;
        }
        var shot = shots[index];
        string path = ShotPath(shot.Index);
        var texture = ResourceLoader.Exists(path) ? GD.Load<Texture2D>(path) : null;
        picture.Texture = texture;
        picture.Visible = texture is not null;
        card.Visible = texture is null;
        caption.Text = TextService.Get(shot.Shot);
        var (speaker, text) = Ui.SplitSpeaker(shot.Line);
        speaker ??= shot.SpeakerId;
        line.Text = (speaker is null ? "" : Ui.SpeakerName(speaker) + ": ") + "„" + text + "“";
        counter.Text = (index + 1) + " / " + shots.Count;
        if (!UiSettings.ReducedMotion)
        {
            Body.Modulate = new Color(1, 1, 1, 0);
            CreateTween().TweenProperty(Body, "modulate:a", 1f, 0.6f);
        }
    }

    /// <summary>
    /// Picture of an epilogue shot (index from 0, data order): <c>res://assets/cutscenes/EPILOGUE_&lt;n&gt;.webp</c>
    /// (painted with the cutscene frames, art/tools/cutscenes.py), else the older <c>res://assets/epilogue/&lt;n&gt;.webp</c>.
    /// </summary>
    public static string ShotPath(int index)
    {
        string painted = $"res://assets/cutscenes/EPILOGUE_{index + 1}.webp";
        return ResourceLoader.Exists(painted) ? painted : $"res://assets/epilogue/{index + 1}.webp";
    }

    private void RollCredits()
    {
        if (rolling) return;
        rolling = true;
        bool replay = Replay;
        Back();
        UiRoot.Instance?.OpenCredits(rolling: true, done: () =>
        {
            if (!replay) UiRoot.Instance?.Message(Ui.T("ui.postgame.free_play"), Ui.T("ui.postgame.continue"));
        });
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        base._Process(delta);
        if (!Visible || rolling || index < 0) return;
        elapsed += delta;
        if (elapsed >= ShotSeconds) Next();
    }

    /// <inheritdoc />
    public override void _GuiInput(InputEvent e)
    {
        if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left } && elapsed > 1.5 && !rolling)
        {
            AcceptEvent();
            Next();
        }
    }

    /// <inheritdoc />
    public override void OnKey(InputEventKey key)
    {
        if (!rolling && elapsed > 1.5 && (key.IsAction("ui_accept") || key.IsAction(LastBell.Game.PlayerInput.InputActions.Confirm))) Next();
    }

    /// <summary>Esc skips the remaining shots (straight to the credits).</summary>
    public override void Back()
    {
        if (!rolling) { RollCredits(); return; }
        base.Back();
    }
}
