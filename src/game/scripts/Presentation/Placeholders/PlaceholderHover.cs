using Godot;
using LastBell.Game.Hooks;
using LastBell.Game.Runtime;

namespace LastBell.Game.Presentation.Placeholders;

/// <summary>Placeholder hover text: name, and the action sentence only when Core returned one for the selected item.</summary>
public partial class PlaceholderHover : Control, IHoverView
{
    private PanelContainer panel = null!;
    private Label name = null!;
    private Label action = null!;

    /// <inheritdoc />
    public override void _Ready()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        SetAnchorsPreset(LayoutPreset.FullRect);
        panel = PlaceholderStyle.Panel(0.8f);
        panel.MouseFilter = MouseFilterEnum.Ignore;
        var box = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore };
        name = PlaceholderStyle.Label("", 24);
        action = PlaceholderStyle.Label("", 22, new Color(1f, 0.85f, 0.5f));
        box.AddChild(name);
        box.AddChild(action);
        panel.AddChild(box);
        AddChild(panel);
        panel.Visible = false;
    }

    /// <inheritdoc />
    public void ShowHover(HoverPayload payload)
    {
        if (UiBus.IsClaimed(UiPanel.Hover)) return;
        name.Text = TextService.Get(payload.Info.Name);
        string sentence = payload.ShowAction ? TextService.Get(payload.Info.ActionLabel) : "";
        action.Text = sentence;
        action.Visible = sentence.Length > 0;
        name.Visible = name.Text.Length > 0;
        panel.Visible = name.Visible || action.Visible;
        panel.ResetSize();
        var p = payload.ScreenPosition + new Vector2(24, 28);
        panel.Position = new Vector2(Mathf.Clamp(p.X, 8, 1920 - panel.Size.X - 8), Mathf.Clamp(p.Y, 8, 1080 - panel.Size.Y - 8));
    }

    /// <inheritdoc />
    public void HideHover() => panel.Visible = false;
}
