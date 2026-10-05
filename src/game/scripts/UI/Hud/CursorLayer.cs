using Godot;
using LastBell.Core.State;
using LastBell.Core.Text;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Hud;

/// <summary>
/// Top-most, mouse-transparent layer: the selected item's icon follows the pointer (the item "on the
/// cursor"), and the optional cursor highlight ring (accessibility setting).
/// </summary>
public partial class CursorLayer : Control
{
    private ItemIcon icon = null!;
    private string? shownItem;

    /// <summary>When true the item icon is hidden (e.g. a full-screen menu is open).</summary>
    public bool Suppressed { get; set; }

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
        icon = new ItemIcon(84);
        icon.Size = new Vector2(84, 84);
        AddChild(icon);
        icon.Visible = false;
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        var game = GameRuntime.Instance;
        if (!game.IsReady) return;
        var state = game.State;
        string? item = !Suppressed && state.Mode is GameMode.World or GameMode.Inventory ? state.SelectedItem : null;
        if (item != shownItem)
        {
            shownItem = item;
            icon.Visible = item is not null;
            if (item is not null && game.Content.FindItem(item) is { } def) icon.SetItem(def.Icon, TextService.Get(TextKeys.NameOf(def)));
        }
        var mouse = GetLocalMousePosition();
        if (icon.Visible) icon.Position = mouse + new Vector2(18, 18);
        if (UiSettings.CursorHighlight || icon.Visible) QueueRedraw();
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        if (!UiSettings.CursorHighlight) return;
        var p = GetLocalMousePosition();
        DrawCircle(p, 30, new Color(UiTheme.BrassLight, 0.22f));
        DrawArc(p, 30, 0, Mathf.Tau, 40, new Color(UiTheme.BrassLight, 0.95f), 4, true);
        DrawArc(p, 34, 0, Mathf.Tau, 40, new Color(0, 0, 0, 0.6f), 2, true);
    }
}
