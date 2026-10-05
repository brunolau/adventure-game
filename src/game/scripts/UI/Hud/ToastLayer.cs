using System.Collections.Generic;
using Godot;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Hud;

/// <summary>
/// Short, mouse-transparent notices at the top of the screen (item added, saved, new goal ...) and
/// the small autosave indicator in the top-right corner. Nothing here blocks input or covers the
/// scene for long (the goal card fades after a few seconds).
/// </summary>
public partial class ToastLayer : Control
{
    private VBoxContainer column = null!;
    private Label autosave = null!;
    private double autosaveLeft;
    private readonly List<(Control Toast, double Left)> toasts = new();

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
        column = Ui.VBox(10);
        column.MouseFilter = MouseFilterEnum.Ignore;
        column.SetAnchorsAndOffsetsPreset(LayoutPreset.CenterTop);
        column.GrowHorizontal = GrowDirection.Both;
        column.OffsetTop = 24;
        column.OffsetLeft = -460;
        column.OffsetRight = 460;
        AddChild(column);
        autosave = Ui.Label(Ui.T("ui.system.autosaved"), "OnDarkCaption");
        autosave.SetAnchorsAndOffsetsPreset(LayoutPreset.TopRight);
        autosave.GrowHorizontal = GrowDirection.Begin;
        autosave.OffsetRight = -28;
        autosave.OffsetTop = 18;
        autosave.AddThemeColorOverride("font_outline_color", new Color(0, 0, 0, 0.8f));
        autosave.AddThemeConstantOverride("outline_size", 6);
        autosave.Modulate = new Color(1, 1, 1, 0);
        AddChild(autosave);
    }

    /// <summary>Shows a notice. <paramref name="detail"/> is an optional second line (e.g. the new goal).</summary>
    public void Show(string text, string detail = "", double seconds = 3.2)
    {
        if (text.Length == 0) return;
        var panel = new PanelContainer { ThemeTypeVariation = "DarkPanel", MouseFilter = MouseFilterEnum.Ignore };
        panel.AddThemeStyleboxOverride("panel", UiTheme.DarkPanel(0.9f, 16, 14));
        var box = Ui.VBox(4);
        box.MouseFilter = MouseFilterEnum.Ignore;
        var label = Ui.Label(text, "OnDarkLabel");
        label.HorizontalAlignment = HorizontalAlignment.Center;
        label.AutowrapMode = TextServer.AutowrapMode.WordSmart;
        box.AddChild(label);
        if (detail.Length > 0)
        {
            var d = Ui.Label(detail, "OnDarkCaption");
            d.HorizontalAlignment = HorizontalAlignment.Center;
            d.AutowrapMode = TextServer.AutowrapMode.WordSmart;
            d.AddThemeFontSizeOverride("font_size", 25);
            box.AddChild(d);
        }
        panel.AddChild(box);
        column.AddChild(panel);
        if (column.GetChildCount() > 3) DropOldest();
        toasts.Add((panel, seconds));
        if (!UiSettings.ReducedMotion)
        {
            panel.Modulate = new Color(1, 1, 1, 0);
            CreateTween().TweenProperty(panel, "modulate:a", 1f, 0.2f);
        }
    }

    /// <summary>Flashes the autosave indicator.</summary>
    public void ShowAutosave()
    {
        autosave.Text = Ui.T("ui.system.autosaved");
        autosave.Modulate = Colors.White;
        autosaveLeft = 1.6;
    }

    private void DropOldest()
    {
        if (toasts.Count == 0) return;
        toasts[0].Toast.QueueFree();
        toasts.RemoveAt(0);
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        for (int i = toasts.Count - 1; i >= 0; i--)
        {
            var (toast, left) = toasts[i];
            left -= delta;
            if (left <= 0)
            {
                toasts.RemoveAt(i);
                toast.QueueFree();
                continue;
            }
            if (left < 0.3 && !UiSettings.ReducedMotion) toast.Modulate = new Color(1, 1, 1, (float)(left / 0.3));
            toasts[i] = (toast, left);
        }
        if (autosaveLeft > 0)
        {
            autosaveLeft -= delta;
            autosave.Modulate = new Color(1, 1, 1, (float)Mathf.Clamp(autosaveLeft / 0.5, 0, 1));
        }
    }

    /// <summary>Removes every notice (new game / load).</summary>
    public void ClearAll()
    {
        foreach (var (t, _) in toasts) t.QueueFree();
        toasts.Clear();
    }
}
