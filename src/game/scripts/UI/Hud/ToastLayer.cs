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
/// Notices wait (orchestrator decision after the playtests, PT-S22 / M5-05): they are queued while lines play
/// (an action's lines, a topic, a cutscene) and while any screen is open (bag, puzzle, journal, map, pause, menus,
/// hints, the ending), so they never cover an open screen and never announce a reward before the lines that explain
/// it. The topic menu of a conversation that stays open (PT-S17) does not hold them, but the column never overlaps
/// its panel: when no slot is free of it, they wait too. At most <see cref="MaxVisible"/> show at once; the rest follow as earlier ones fade.
/// The timers of shown notices stand still while they wait.
/// </summary>
public partial class ToastLayer : Control
{
    private VBoxContainer column = null!;
    private Label autosave = null!;
    private double autosaveLeft;
    private readonly List<(Control Toast, double Left)> toasts = new();
    private readonly Queue<(string Text, string Detail, double Seconds)> waiting = new();

    /// <summary>Most notices on screen at once.</summary>
    public const int MaxVisible = 3;
    private const float ColumnWidth = 760f;
    private string placedFor = "";
    private bool placedClear = true;

    /// <summary>The column's current rect in canvas pixels (1920x1080 base, after the HUD scale); for QA checks.</summary>
    public Rect2 ColumnCanvasRect => new(column.GetGlobalTransformWithCanvas().Origin, column.Size * column.GetGlobalTransformWithCanvas().Scale);

    /// <summary>Number of notices on screen (QA checks).</summary>
    public int Count => toasts.Count;

    /// <summary>Number of notices waiting for the lines to end or a screen to close (QA checks).</summary>
    public int Waiting => waiting.Count;

    /// <summary>True while notices wait: lines play or a screen is open (QA checks).</summary>
    public bool Held => IsHeld();

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

    /// <summary>
    /// Queues a notice; it appears as soon as no line plays and no screen is open. <paramref name="detail"/> is an
    /// optional second line (e.g. the new goal).
    /// </summary>
    public void Show(string text, string detail = "", double seconds = 3.2)
    {
        if (text.Length == 0) return;
        waiting.Enqueue((text, detail, seconds));
    }

    private void Present(string text, string detail, double seconds)
    {
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
        toasts.Add((panel, seconds));
        placedFor = "";
        if (!UiSettings.ReducedMotion)
        {
            panel.Modulate = new Color(1, 1, 1, 0);
            CreateTween().TweenProperty(panel, "modulate:a", 1f, 0.2f);
        }
    }

    /// <summary>The language changed (ISSUES UI-07): the one text made in _Ready.</summary>
    public void Relocalize() => autosave.Text = Ui.T("ui.system.autosaved");

    /// <summary>Flashes the autosave indicator.</summary>
    public void ShowAutosave()
    {
        autosave.Text = Ui.T("ui.system.autosaved");
        autosave.Modulate = Colors.White;
        autosaveLeft = 1.6;
    }

    /// <summary>
    /// Notices wait while a line plays (or a preface line), during a cutscene or a room change, and while any screen
    /// is open: a mode other than the plain scene (bag, topic menu, puzzle, journal, map, pause) or a UI modal.
    /// </summary>
    private static bool IsHeld()
    {
        if (GameRuntime.Instance is not { IsReady: true } game) return true;
        var state = game.State;
        if (state.ActiveLineId is not null) return true;
        bool topicMenu = state.Mode == LastBell.Core.State.GameMode.Dialogue;
        if (state.Mode != LastBell.Core.State.GameMode.World && !topicMenu) return true;
        if (LastBell.Game.Presentation.DialoguePresenter.Instance is { } p && (p.IsShowingLine || p.HasPreface)) return true;
        if (UiRoot.Instance?.HasModal ?? false) return true;
        return WorldStage.Instance is not { IsSettled: true, IsFadedIn: true };
    }

    /// <summary>
    /// Picks the slot with the least overlap with the visible targets of the current room (their
    /// rects and the label strip above them), in canvas pixels; earlier slots win ties.
    /// </summary>
    private bool Place()
    {
        var room = WorldStage.Instance?.Current;
        var panel = UiRoot.Instance?.TopicMenuRect;
        string key = (room?.RoomId ?? "-") + "|" + toasts.Count + "|" + Size + "|" + panel;
        if (key == placedFor) return placedClear;
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
        bool clear = false;
        foreach (var slot in slots)
        {
            var r = new Rect2(slot, new Vector2(width, height));
            bool free = panel is not { } p || !r.Intersects(p.Grow(12));
            float area = free ? 0 : 1e9f; // an open topic menu is a hard obstacle
            foreach (var o in obstacles)
                if (r.Intersects(o)) area += r.Intersection(o).Area;
            if (area < bestArea - 0.5f) { bestArea = area; best = slot; clear = free; }
        }
        column.Position = best / scale;
        column.Size = new Vector2(width / scale, 0);
        placedClear = clear;
        return clear;
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        // Notices wait while lines play or a screen is open (PT-S22, M5-05) and run on afterwards.
        bool hold = IsHeld() || (toasts.Count + waiting.Count > 0 && !PlaceForNext());
        column.Visible = !hold;
        if (autosaveLeft > 0)
        {
            autosaveLeft -= delta;
            autosave.Modulate = new Color(1, 1, 1, (float)Mathf.Clamp(autosaveLeft / 0.5, 0, 1));
        }
        if (hold) return;
        while (toasts.Count < MaxVisible && waiting.Count > 0)
        {
            var (text, detail, seconds) = waiting.Dequeue();
            Present(text, detail, seconds);
        }
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
    }

    /// <summary>True when the column has a slot that does not touch an open topic menu (always true without one).</summary>
    private bool PlaceForNext() => UiRoot.Instance?.TopicMenuRect is null || Place();

    /// <summary>Removes every notice (new game / load).</summary>
    public void ClearAll()
    {
        foreach (var (t, _) in toasts) t.QueueFree();
        toasts.Clear();
        waiting.Clear();
    }
}
