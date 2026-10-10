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
/// they wait until the opening lines have played. Phones and tablets (<see cref="TouchMode"/>) get the touch tips
/// (tap, hold, the Eye button) instead of the mouse and keyboard ones, wrapped to the narrower logical screen.
/// </summary>
public partial class TipsOverlay : Control
{
    private static readonly string[] MouseKeys = { "ui.tutorial.left_click", "ui.tutorial.right_click", "ui.tutorial.space", "ui.tutorial.help_menu" };
    private static readonly string[] TouchKeys = { "ui.tutorial.touch_tap", "ui.tutorial.touch_hold", "ui.tutorial.touch_eye", "ui.tutorial.help_menu" };

    /// <summary>The tips of this device: mouse and keyboard, or touch.</summary>
    public static string[] Keys => TouchMode.Enabled ? TouchKeys : MouseKeys;

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
        // Phones: at 200 % the bubble covered the second slot of the open inventory (ISSUES ANDROID-11). There it
        // steps aside while the inventory or a screen is open, and its time does not run meanwhile.
        bool covered = TouchMode.Enabled && (GameRuntime.Instance.State.Mode != GameMode.World || (UiRoot.Instance?.HasModal ?? false));
        bubble.Visible = !covered;
        if (covered) return;
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
        SetTipText();
        bubble.Visible = true;
        bubble.ResetSize();
        left = TouchMode.Enabled ? 7.0 : 5.5;
    }

    private void SetTipText()
    {
        label.Text = Ui.T(Keys[index]);
        if (!TouchMode.Enabled) return;
        // A phone runs the UI at up to 200 %: the logical screen is 960 px wide and a long tip must wrap.
        float room = Mathf.Max(240f, Size.X - 200f);
        float needed = label.GetThemeFont("font").GetStringSize(label.Text, HorizontalAlignment.Left, -1, label.GetThemeFontSize("font_size")).X;
        label.AutowrapMode = needed > room ? TextServer.AutowrapMode.WordSmart : TextServer.AutowrapMode.Off;
        label.CustomMinimumSize = new Vector2(needed > room ? room : 0, 0);
    }

    /// <summary>The language changed (ISSUES UI-07): the tip on screen is shown in the new language; its time runs on.</summary>
    public void Relocalize()
    {
        if (index < 0 || index >= Keys.Length) return;
        SetTipText();
        bubble.ResetSize();
    }
}
