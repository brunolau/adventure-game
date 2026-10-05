using System;
using System.Collections.Generic;
using Godot;
using LastBell.Game.Runtime;
using LastBell.Game.World;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Hud;

/// <summary>
/// Short, mouse-transparent notices at the top of the screen (item added, saved, new goal ...) and
/// the small autosave indicator in the top-right corner. Nothing here blocks input or covers the
/// scene for long (the goal card fades after a few seconds). The column never sits on the room's
/// hotspots: it takes the first free slot of top-centre, top-right, top-left and the band below the
/// prop row (the handoff blocking puts every prop rect in a row at y 150-250, ISSUES ART-BLOCK-01),
/// chosen against the current room's visible targets whenever a notice appears or the room changes
/// (docs/MILESTONE2.md, milestone-1 polish item 5).
/// </summary>
public partial class ToastLayer : Control
{
    private VBoxContainer column = null!;
    private Label autosave = null!;
    private double autosaveLeft;
    private readonly List<(Control Toast, double Left)> toasts = new();
    private const float ColumnWidth = 760f;
    private string placedFor = "";

    /// <summary>The column's current rect in canvas pixels (1920x1080 base, after the HUD scale); for QA checks.</summary>
    public Rect2 ColumnCanvasRect => new(column.GetGlobalTransformWithCanvas().Origin, column.Size * column.GetGlobalTransformWithCanvas().Scale);

    /// <summary>Number of notices on screen (QA checks).</summary>
    public int Count => toasts.Count;

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
        column = Ui.VBox(10);
        column.MouseFilter = MouseFilterEnum.Ignore;
        column.SetAnchorsAndOffsetsPreset(LayoutPreset.TopLeft);
        column.Position = new Vector2(580, 24);
        column.Size = new Vector2(ColumnWidth, 0);
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
        placedFor = "";
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

    /// <summary>
    /// Picks the slot with the least overlap with the visible targets of the current room (their
    /// rects and the label strip above them), in canvas pixels; earlier slots win ties.
    /// </summary>
    private void Place()
    {
        var room = WorldStage.Instance?.Current;
        string key = (room?.RoomId ?? "-") + "|" + toasts.Count + "|" + Size;
        if (key == placedFor) return;
        placedFor = key;
        var scale = GetGlobalTransformWithCanvas().Scale.X;
        if (scale <= 0) scale = 1;
        var canvas = Size * scale;
        float width = Math.Min(ColumnWidth * scale, canvas.X - 56);
        float height = Math.Max(column.Size.Y * scale, 130 * scale);
        var slots = new[]
        {
            new Vector2((canvas.X - width) / 2, 24),
            new Vector2(canvas.X - width - 28, 64),
            new Vector2(28, 24),
            new Vector2((canvas.X - width) / 2, 268),
            new Vector2(canvas.X - width - 28, 268),
        };
        var obstacles = new List<Rect2>();
        if (room is not null)
            foreach (var t in room.Targets)
                obstacles.Add(t.Rect.Merge(new Rect2(t.LabelAnchor - new Vector2(90, 40), new Vector2(180, 44))));
        Vector2 best = slots[0];
        float bestArea = float.MaxValue;
        foreach (var slot in slots)
        {
            var r = new Rect2(slot, new Vector2(width, height));
            float area = 0;
            foreach (var o in obstacles)
                if (r.Intersects(o)) area += r.Intersection(o).Area;
            if (area < bestArea - 0.5f) { bestArea = area; best = slot; }
        }
        column.Position = best / scale;
        column.Size = new Vector2(width / scale, 0);
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        // Notices wait while a cutscene plays (they used to cover the cutscene card) and run on afterwards.
        bool hold = GameRuntime.Instance is { IsReady: true } g && g.State.Mode == LastBell.Core.State.GameMode.Cutscene;
        column.Visible = !hold;
        if (hold) return;
        if (toasts.Count > 0) Place();
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
