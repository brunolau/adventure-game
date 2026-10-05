using Godot;
using LastBell.Core.State;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;
using LastBell.Game.World;

namespace LastBell.Game.UI.Common;

/// <summary>
/// The three first-start context bubbles (PRIBEH_A_PRAVIDLA: shown once; the same text is in the
/// Help menu). They are mouse-transparent, so no bubble ever consumes the first game click, and
/// they wait until the opening lines have played.
/// </summary>
public partial class TipsOverlay : Control
{
    private static readonly string[] Keys = { "ui.tutorial.left_click", "ui.tutorial.right_click", "ui.tutorial.space", "ui.tutorial.help_menu" };
    private PanelContainer bubble = null!;
    private Label label = null!;
    private int index = -1;
    private double left;
    private bool waiting;

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
        bubble = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore };
        bubble.AddThemeStyleboxOverride("panel", UiTheme.PaperPanel(20));
        var row = Ui.HBox(14);
        row.MouseFilter = MouseFilterEnum.Ignore;
        row.AddChild(new Glyph(GlyphKind.Hint, 44, UiTheme.Accent));
        label = Ui.Label("", "", wrap: false);
        row.AddChild(label);
        bubble.AddChild(row);
        AddChild(bubble);
        bubble.Visible = false;
    }

    /// <summary>Starts the sequence (once per installation).</summary>
    public void Start()
    {
        index = -1;
        waiting = true;
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        if (waiting)
        {
            var game = GameRuntime.Instance;
            var stage = WorldStage.Instance;
            bool calm = game.State.Mode == GameMode.World && game.State.ActiveLineId is null && stage is { IsSettled: true, IsFadedIn: true };
            if (!calm || (UiRoot.Instance?.HasModal ?? false)) return;
            waiting = false;
            Next();
        }
        if (index < 0) return;
        left -= delta;
        if (left <= 0) Next();
        bubble.Position = new Vector2((Size.X - bubble.Size.X) / 2, Size.Y - Hud.HudView.StripHeight - bubble.Size.Y - 40);
    }

    private void Next()
    {
        index++;
        if (index >= Keys.Length)
        {
            index = -1;
            bubble.Visible = false;
            UiSettings.TipsShown = true;
            UiSettings.Save();
            return;
        }
        label.Text = Ui.T(Keys[index]);
        bubble.Visible = true;
        bubble.ResetSize();
        left = 5.5;
    }
}
