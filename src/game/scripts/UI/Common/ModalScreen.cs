using System;
using Godot;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Common;

/// <summary>
/// Base of every full-screen panel: a dimmed backdrop that swallows clicks (no click falls through
/// to the scene, AT22), a centred paper panel with a title row and the visible close cross, and a
/// content box. The panel size is the preferred size clamped to the available logical area, so
/// the same screen works from 1280x720 to 4K and at 200 % HUD scale (content scrolls).
/// Touch mode (<see cref="LastBell.Game.Runtime.TouchMode"/>): a phone runs the UI at 200 %, a logical screen of 960x540.
/// A panel whose content cannot scroll and needs more than that (the difficulty step, a long confirmation, a puzzle)
/// is scaled down as a whole until it is on screen; nothing is ever cut off or out of reach.
/// </summary>
public partial class ModalScreen : Control
{
    private PanelContainer panel = null!;
    private Label title = null!;
    private Button? close;
    private Label status = null!;
    private double statusLeft;
    private Vector2 lastSize;

    /// <summary>Preferred panel size in logical px (clamped to the screen).</summary>
    protected Vector2 PreferredSize { get; set; } = new(1400, 860);

    /// <summary>Backdrop opacity.</summary>
    protected float Dim { get; set; } = 0.55f;

    /// <summary>Shrink the panel height to its content (small dialogs).</summary>
    protected bool FitHeight { get; set; }

    /// <summary>With <see cref="FitHeight"/>: the content whose minimum height decides (instead of the whole body, e.g. inside a scroll area).</summary>
    protected Control? FitTarget { get; set; }

    /// <summary>Show the close cross.</summary>
    protected bool Closable { get; set; } = true;

    /// <summary>The content area under the title row.</summary>
    protected VBoxContainer Body { get; private set; } = null!;

    /// <summary>The row right of the title (extra buttons).</summary>
    protected HBoxContainer TitleRow { get; private set; } = null!;

    /// <summary>The panel.</summary>
    protected PanelContainer Panel => panel;

    /// <summary>True while shown.</summary>
    public bool IsOpen => Visible;

    /// <summary>Raised when the screen closed itself (Back / close cross).</summary>
    public event Action? Closed;

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Stop;
        var backdrop = new ColorRect { Color = new Color(0.06f, 0.04f, 0.03f, Dim), MouseFilter = MouseFilterEnum.Ignore };
        backdrop.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        AddChild(backdrop);
        panel = new PanelContainer { Name = "Panel" };
        AddChild(panel);
        var outer = Ui.VBox(16);
        panel.AddChild(outer);
        TitleRow = Ui.HBox(16);
        title = Ui.Label("", "TitleLabel");
        title.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        title.VerticalAlignment = VerticalAlignment.Center;
        TitleRow.AddChild(title);
        outer.AddChild(TitleRow);
        if (Closable)
        {
            close = Ui.CloseButton(Back);
            close.FocusMode = FocusModeEnum.Click;
        }
        Body = Ui.VBox(14);
        Body.SizeFlagsVertical = SizeFlags.ExpandFill;
        outer.AddChild(Body);
        Build();
        // Feedback for an action inside the screen ("Uložené"): notices never draw over open screens (PT-S22).
        status = Ui.Label("", "CaptionLabel");
        status.VerticalAlignment = VerticalAlignment.Center;
        status.Visible = false;
        TitleRow.AddChild(status);
        if (close is not null) TitleRow.AddChild(close);
        if (title.Text.Length == 0 && close is null && TitleRow.GetChildCount() == 1) TitleRow.Visible = false;
        Visible = false;
    }

    /// <summary>Builds the static content (called once from _Ready).</summary>
    protected virtual void Build() { }

    /// <summary>Refreshes the content from the current state (called on every open).</summary>
    protected virtual void Refresh() { }

    /// <summary>The control that gets keyboard focus on open (null: the first focusable control).</summary>
    protected virtual Control? InitialFocus() => null;

    /// <summary>Sets the title text.</summary>
    protected void SetTitle(string text)
    {
        title.Text = text;
        TitleRow.Visible = true;
    }

    /// <summary>Shows a short confirmation in the title row for a few seconds (instead of a notice over the screen).</summary>
    public void ShowStatus(string text, double seconds = 3.0)
    {
        status.Text = text;
        status.Visible = text.Length > 0;
        statusLeft = seconds;
    }

    /// <summary>Shows the screen, rebuilt from the current state.</summary>
    public virtual void Open()
    {
        Visible = true;
        Refresh();
        Layout(true);
        FocusDefault();
    }

    /// <summary>Hides the screen (no events).</summary>
    public virtual void Dismiss()
    {
        if (!Visible) return;
        var focused = GetViewport()?.GuiGetFocusOwner();
        if (focused is not null && IsAncestorOf(focused)) focused.ReleaseFocus();
        Visible = false;
    }

    /// <summary>Esc / close cross: default closes and raises <see cref="Closed"/>.</summary>
    public virtual void Back()
    {
        Dismiss();
        Closed?.Invoke();
    }

    /// <summary>A key press that reached the modal and no focused control used (Esc is handled by the root).</summary>
    public virtual void OnKey(InputEventKey key) { }

    /// <summary>Gives keyboard focus to the default control.</summary>
    public void FocusDefault()
    {
        var target = InitialFocus() ?? FirstFocusable(Body);
        Ui.FocusLater(target);
    }

    /// <summary>The first visible focusable control under a node.</summary>
    protected static Control? FirstFocusable(Node root)
    {
        foreach (var child in root.GetChildren())
        {
            if (child is Control { Visible: true } c)
            {
                if (c.FocusMode == FocusModeEnum.All && c is BaseButton { Disabled: false } or Slider) return c;
                if (FirstFocusable(c) is { } inner) return inner;
            }
        }
        return null;
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        if (Visible) Layout(false);
        if (statusLeft > 0 && (statusLeft -= delta) <= 0) status.Visible = false;
    }

    private void Layout(bool force)
    {
        bool fit = LastBell.Game.Runtime.TouchMode.Enabled; // checked every frame: wrapped texts settle a frame late
        if (!force && Size == lastSize && !FitHeight && !fit) return;
        lastSize = Size;
        var avail = Size - new Vector2(48, 48);
        var size = new Vector2(Math.Min(PreferredSize.X, avail.X), Math.Min(PreferredSize.Y, avail.Y));
        if (FitHeight && panel.GetChildCount() > 0 && panel.GetChild(0) is Control inner)
        {
            float margins = panel.GetThemeStylebox("panel").GetMinimumSize().Y;
            float content = FitTarget is null ? inner.GetCombinedMinimumSize().Y
                : (TitleRow.Visible ? TitleRow.GetCombinedMinimumSize().Y + 16 : 0) + FitTarget.GetCombinedMinimumSize().Y + 40;
            size.Y = Math.Min(size.Y, content + margins);
        }
        panel.Size = size;
        panel.CustomMinimumSize = size;
        panel.Position = (Size - size) / 2;
        if (!fit) return;
        // Godot has grown the panel to its content's minimum by now; scale it back into the screen if that is too much.
        var room = Size - new Vector2(16, 16);
        var actual = panel.Size;
        float k = Mathf.Min(1f, Mathf.Min(room.X / Mathf.Max(1f, actual.X), room.Y / Mathf.Max(1f, actual.Y)));
        panel.Scale = new Vector2(k, k);
        panel.Position = (Size - actual * k) / 2;
    }
}
