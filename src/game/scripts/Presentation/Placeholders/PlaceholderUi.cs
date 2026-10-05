using Godot;
using LastBell.Game.Hooks;
using LastBell.Game.Runtime;

namespace LastBell.Game.Presentation.Placeholders;

/// <summary>
/// Hosts every temporary placeholder (hover, inventory strip, puzzle modal, pause/journal/map
/// panels, notices). Each one stands down when the UI agent claims its panel via <see cref="UiBus"/>.
/// </summary>
public partial class PlaceholderUi : Control
{
    private Label notice = null!;
    private double noticeLeft;

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
        AddChild(new PlaceholderInventoryStrip { Name = "InventoryStrip" });
        AddChild(new PlaceholderPuzzlePanel { Name = "PuzzlePanel" });
        AddChild(new PlaceholderOverlayPanel { Name = "OverlayPanel" });
        AddChild(new PlaceholderPortalPanel { Name = "PortalPanel" });
        var hover = new PlaceholderHover { Name = "Hover" };
        AddChild(hover);
        HoverPresenter.Placeholder = hover;
        notice = PlaceholderStyle.Label("", 24, new Color(1f, 0.95f, 0.8f));
        notice.Position = new Vector2(40, 30);
        AddChild(notice);
        notice.Visible = false;
        UiBus.Notice += OnNotice;
    }

    /// <inheritdoc />
    public override void _ExitTree() => UiBus.Notice -= OnNotice;

    private void OnNotice(string key)
    {
        if (UiBus.IsClaimed(UiPanel.Hud)) return;
        notice.Text = TextService.Ui(key);
        notice.Visible = true;
        noticeLeft = 2.5;
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        if (noticeLeft <= 0) return;
        noticeLeft -= delta;
        if (noticeLeft <= 0) notice.Visible = false;
    }
}
