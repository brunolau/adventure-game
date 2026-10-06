using System.Linq;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Game.Hooks;
using LastBell.Game.Runtime;
using LastBell.Game.World;

namespace LastBell.Game.Presentation.Placeholders;

/// <summary>
/// Temporary chronometer era chooser (until the UI agent claims <see cref="UiPanel.Portal"/>): at an
/// open anchor node with CHRONO owned, Core's portal targets are listed as buttons in the top-right
/// corner; choosing one calls Navigation.UsePortal and the world stage runs the transition and the
/// era card. Key T (logical command Travel) focuses the first button.
/// </summary>
public partial class PlaceholderPortalPanel : Control
{
    private PanelContainer panel = null!;
    private VBoxContainer box = null!;
    private string signature = "";

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
        panel = PlaceholderStyle.Panel(0.85f);
        box = new VBoxContainer();
        box.AddThemeConstantOverride("separation", 6);
        panel.AddChild(box);
        AddChild(panel);
        panel.Visible = false;
        UiBus.OpenRequested += p =>
        {
            if (p == UiPanel.Portal && panel.Visible && box.GetChildCount() > 1 && box.GetChild(1) is Button b) b.GrabFocus();
        };
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        var game = GameRuntime.Instance;
        if (!game.IsReady) return;
        var state = game.State;
        bool settled = WorldStage.Instance?.IsSettled ?? false;
        var targets = settled && state.Mode == GameMode.World && !UiBus.IsClaimed(UiPanel.Portal)
            ? Navigation.PortalTargets(game.Content, state)
            : System.Array.Empty<PortalTarget>();
        string sig = state.Room + ":" + string.Join(",", targets.Select(t => t.Year));
        if (sig == signature) return;
        signature = sig;
        foreach (var child in box.GetChildren()) child.QueueFree();
        panel.Visible = targets.Count > 0;
        if (targets.Count == 0) return;
        box.AddChild(PlaceholderStyle.Label(TextService.Ui("ui.travel.choose_era"), 22, new Color(1f, 0.83f, 0.45f)));
        foreach (var target in targets)
        {
            int year = target.Year;
            var button = PlaceholderStyle.Button(TextService.Ui("ui.travel.era_option", ("year", TextService.EraYear(year))) + " · " + TextService.Get(target.Card), 20);
            button.Pressed += () => game.Update(s => Navigation.UsePortal(game.Content, s, year));
            box.AddChild(button);
        }
        panel.ResetSize();
        var size = panel.GetCombinedMinimumSize();
        panel.Position = new Vector2(1920 - size.X - 24, 90);
    }
}
