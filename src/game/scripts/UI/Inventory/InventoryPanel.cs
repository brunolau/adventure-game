using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Views;
using LastBell.Game.PlayerInput;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Hud;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Inventory;

/// <summary>
/// The inventory drawer (Core mode Inventory): a bar of item slots at the bottom (tabs: items /
/// archived, CORE-06) and a detail panel for the focused or hovered item (name, look, purpose and
/// the hint how to use it). Left click on a slot selects the item (the drawer stays open so a
/// recipe can be tried) or, with an item selected, combines through Core's resolver; right click
/// (or the "look" button / Backspace) looks without closing the drawer; Enter selects. A wrong pair
/// is a complete no-op. Everything goes through <see cref="WorldInput"/>.
/// </summary>
public partial class InventoryPanel : Control
{
    private PanelContainer bar = null!;
    private HFlowContainer slots = null!;
    private Button tabItems = null!;
    private Button tabArchived = null!;
    private Label hoverLine = null!;
    private PanelContainer detail = null!;
    private ItemIcon detailIcon = null!;
    private Label detailName = null!;
    private Label detailLook = null!;
    private Label detailPurpose = null!;
    private Label detailHint = null!;
    private Button selectButton = null!;
    private Button lookButton = null!;
    private bool showArchived;
    private string signature = "";
    private string? detailItem;
    private HudView hud = null!;
    private readonly Dictionary<string, Button> slotButtons = new(StringComparer.Ordinal);

    /// <summary>Wires the HUD hover source.</summary>
    public void Init(HudView hudView)
    {
        hud = hudView;
        hud.HoverChanged += UpdateHoverLine;
    }

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;

        // Detail card (above the bar, right side)
        detail = new PanelContainer();
        detail.AddThemeStyleboxOverride("panel", UiTheme.PaperPanel(22));
        var d = Ui.VBox(8);
        var head = Ui.HBox(14);
        detailIcon = new ItemIcon(96);
        head.AddChild(detailIcon);
        detailName = Ui.Label("", "HeadingLabel", wrap: true);
        detailName.VerticalAlignment = VerticalAlignment.Center;
        head.AddChild(detailName);
        d.AddChild(head);
        detailLook = Ui.Para("", "ItalicLabel");
        detailPurpose = Ui.Para("", "CaptionLabel");
        detailHint = Ui.Para("", "CaptionLabel");
        detailHint.AddThemeColorOverride("font_color", UiTheme.Focus);
        d.AddChild(detailLook);
        d.AddChild(detailPurpose);
        d.AddChild(detailHint);
        var actions = Ui.HBox(10);
        selectButton = Ui.Button(Ui.T("ui.inventory.select"), OnSelectButton);
        lookButton = Ui.Button(Ui.T("ui.inventory.look"), () => { if (detailItem is { } id) WorldInput.Submit(new Hit.Item(id), PointerButton.Right); });
        actions.AddChild(selectButton);
        actions.AddChild(lookButton);
        d.AddChild(actions);
        detail.AddChild(d);
        AddChild(detail);

        // Bar
        bar = new PanelContainer();
        bar.AddThemeStyleboxOverride("panel", UiTheme.PaperPanel(18));
        var box = Ui.VBox(10);
        var top = Ui.HBox(10);
        var title = Ui.Label(Ui.T("ui.inventory.title"), "HeadingLabel");
        top.AddChild(title);
        var group = new ButtonGroup();
        tabItems = Ui.Tab(Ui.T("ui.inventory.tab_items"), group);
        tabArchived = Ui.Tab(Ui.T("ui.inventory.tab_archived"), group);
        tabItems.ButtonPressed = true;
        tabItems.Toggled += on => { if (on) { showArchived = false; signature = ""; } };
        tabArchived.Toggled += on => { if (on) { showArchived = true; signature = ""; } };
        top.AddChild(tabItems);
        top.AddChild(tabArchived);
        hoverLine = Ui.Label("", "SubheadingLabel");
        hoverLine.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        hoverLine.HorizontalAlignment = HorizontalAlignment.Center;
        hoverLine.VerticalAlignment = VerticalAlignment.Center;
        hoverLine.TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis;
        hoverLine.AddThemeColorOverride("font_color", UiTheme.Accent);
        top.AddChild(hoverLine);
        var close = Ui.CloseButton(() => WorldInput.Dispatch(LogicalCommand.Inventory));
        close.FocusMode = FocusModeEnum.Click;
        top.AddChild(close);
        box.AddChild(top);
        slots = new HFlowContainer();
        slots.AddThemeConstantOverride("h_separation", 12);
        slots.AddThemeConstantOverride("v_separation", 12);
        var scroll = Ui.Scroll(slots);
        scroll.CustomMinimumSize = new Vector2(0, 170);
        box.AddChild(scroll);
        bar.AddChild(box);
        AddChild(bar);
        Visible = false;
    }

    /// <summary>Shows or hides the drawer (driven by Core's mode).</summary>
    public void SetOpen(bool open)
    {
        if (open == Visible) return;
        Visible = open;
        if (open)
        {
            signature = "";
            Rebuild();
            FocusFirstSlot();
        }
        else
        {
            var focused = GetViewport()?.GuiGetFocusOwner();
            if (focused is not null && IsAncestorOf(focused)) focused.ReleaseFocus();
        }
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        if (!Visible) return;
        Layout();
        var state = GameRuntime.Instance.State;
        string sig = string.Join(",", state.Inventory) + "|" + state.SelectedItem + "|" + showArchived + "|" + state.Done.Length;
        if (sig != signature) Rebuild();
    }

    private void Layout()
    {
        float width = Math.Min(1700, Size.X - 60);
        float barHeight = Math.Min(300, Size.Y * 0.42f);
        bar.Size = new Vector2(width, barHeight);
        bar.CustomMinimumSize = bar.Size;
        bar.Position = new Vector2((Size.X - width) / 2, Size.Y - barHeight - 20);
        float dw = Math.Min(640, width * 0.5f);
        detail.CustomMinimumSize = new Vector2(dw, 0);
        detail.ResetSize();
        float dh = detail.Size.Y;
        detail.Position = new Vector2(bar.Position.X + width - dw, Math.Max(16, bar.Position.Y - dh - 14));
        detail.Size = new Vector2(dw, dh);
    }

    private void Rebuild()
    {
        var game = GameRuntime.Instance;
        var state = game.State;
        signature = string.Join(",", state.Inventory) + "|" + state.SelectedItem + "|" + showArchived + "|" + state.Done.Length;
        var focusedId = GetViewport()?.GuiGetFocusOwner()?.GetMeta("item_id", "").AsString();
        Ui.Clear(slots);
        slotButtons.Clear();
        var items = ViewBuilder.Inventory(game.Content, state);
        int archivedCount = items.Count(i => i.IsArchived);
        tabItems.Text = Ui.T("ui.inventory.tab_items") + " (" + (items.Count - archivedCount) + ")";
        tabArchived.Text = Ui.T("ui.inventory.tab_archived") + " (" + archivedCount + ")";
        var shown = items.Where(i => i.IsArchived == showArchived).ToList();
        if (shown.Count == 0)
            slots.AddChild(Ui.Label(Ui.T(showArchived ? "ui.inventory.archived_empty" : "ui.inventory.empty"), "CaptionLabel"));
        foreach (var item in shown) slots.AddChild(MakeSlot(item));
        if (focusedId is { Length: > 0 } && slotButtons.TryGetValue(focusedId, out var again)) Ui.FocusLater(again);
        string? show = detailItem is not null && state.Has(detailItem) ? detailItem : state.SelectedItem ?? shown.FirstOrDefault()?.Id;
        ShowDetail(show);
        UpdateHoverLine();
    }

    private Button MakeSlot(InventoryItemView item)
    {
        string name = TextService.Get(item.Name);
        var button = new Button
        {
            ToggleMode = false,
            CustomMinimumSize = new Vector2(150, 160),
            TooltipText = name,
        };
        button.SetMeta("item_id", item.Id);
        if (item.IsSelected)
        {
            button.AddThemeStyleboxOverride("normal", UiTheme.Box(new Color("fbf2df"), UiTheme.Accent, 4, 12, 8));
            button.AddThemeStyleboxOverride("hover", UiTheme.Box(new Color("fbf2df"), UiTheme.Accent, 4, 12, 8));
        }
        var box = Ui.VBox(2);
        box.MouseFilter = MouseFilterEnum.Ignore;
        box.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        box.OffsetLeft = 6; box.OffsetRight = -6; box.OffsetTop = 6; box.OffsetBottom = -4;
        var icon = new ItemIcon(96) { SizeFlagsHorizontal = SizeFlags.ShrinkCenter };
        icon.SetItem(item.Icon, name, item.IsArchived);
        box.AddChild(icon);
        var caption = Ui.Label(name, "CaptionLabel");
        caption.HorizontalAlignment = HorizontalAlignment.Center;
        caption.AutowrapMode = TextServer.AutowrapMode.WordSmart;
        caption.MaxLinesVisible = 2;
        caption.TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis;
        caption.AddThemeFontSizeOverride("font_size", 20);
        caption.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        box.AddChild(caption);
        button.AddChild(box);
        string id = item.Id;
        button.GuiInput += e => OnSlotInput(id, e);
        button.MouseEntered += () => { ShowDetail(id); WorldInput.HoverItem(id, GetViewport().GetMousePosition()); };
        button.MouseExited += WorldInput.ClearHover;
        button.FocusEntered += () => { ShowDetail(id); WorldInput.HoverItem(id, button.GetGlobalRect().GetCenter()); };
        slotButtons[id] = button;
        return button;
    }

    private void OnSlotInput(string id, InputEvent e)
    {
        if (e is InputEventMouseButton { Pressed: true } mb && mb.ButtonIndex is MouseButton.Left or MouseButton.Right)
        {
            AcceptEvent();
            WorldInput.Submit(new Hit.Item(id), mb.ButtonIndex == MouseButton.Right ? PointerButton.Right : PointerButton.Left);
        }
        else if (e is InputEventKey { Pressed: true, Echo: false } key)
        {
            if (key.IsAction(InputActions.Confirm) || key.IsAction("ui_accept"))
            {
                AcceptEvent();
                WorldInput.Submit(new Hit.Item(id), PointerButton.Left);
            }
            else if (key.IsAction(InputActions.Back))
            {
                AcceptEvent();
                WorldInput.Submit(new Hit.Item(id), PointerButton.Right);
            }
        }
    }

    private void ShowDetail(string? id)
    {
        var game = GameRuntime.Instance;
        var state = game.State;
        var view = id is null ? null : ViewBuilder.Inventory(game.Content, state).FirstOrDefault(i => i.Id == id);
        detail.Visible = view is not null;
        detailItem = view?.Id;
        if (view is null) return;
        string name = TextService.Get(view.Name);
        detailIcon.SetItem(view.Icon, name, view.IsArchived);
        detailName.Text = name;
        detailLook.Text = TextService.Get(view.Look);
        string purpose = TextService.Get(view.Purpose);
        detailPurpose.Text = purpose.Length > 0 ? Ui.T("ui.inventory.purpose", ("purpose", purpose)) : "";
        detailPurpose.Visible = purpose.Length > 0;
        bool somethingSelected = state.SelectedItem is not null;
        detailHint.Text = view.IsSelected ? Ui.T("ui.inventory.combine_hint")
            : somethingSelected ? ""
            : Ui.T("ui.inventory.look_hint");
        detailHint.Visible = detailHint.Text.Length > 0;
        selectButton.Text = view.IsSelected ? Ui.T("ui.inventory.deselect") : somethingSelected ? Ui.T("ui.inventory.combine") : Ui.T("ui.inventory.select");
        // With an item on the cursor every right click only cancels the selection, so "look" is offered without one.
        lookButton.Visible = !somethingSelected;
        if (view.IsArchived) { detailHint.Text = Ui.T("ui.inventory.archived_badge"); detailHint.Visible = true; }
    }

    private void OnSelectButton()
    {
        if (detailItem is not { } id) return;
        var state = GameRuntime.Instance.State;
        if (state.SelectedItem == id) WorldInput.Submit(new Hit.Empty(), PointerButton.Right); // cancel the selection
        else WorldInput.Submit(new Hit.Item(id), PointerButton.Left);
    }

    private void UpdateHoverLine()
    {
        if (hoverLine is null || hud is null) return;
        var (name, action) = HudView.Texts(hud.CurrentHover);
        var state = GameRuntime.Instance.State;
        if (action.Length > 0) hoverLine.Text = action;
        else if (state.SelectedItem is { } sel && GameRuntime.Instance.Content.FindItem(sel) is { } item)
            hoverLine.Text = Ui.T("ui.inventory.selected", ("item", TextService.Get(LastBell.Core.Text.TextKeys.NameOf(item))));
        else hoverLine.Text = name;
    }

    private void FocusFirstSlot()
    {
        var state = GameRuntime.Instance.State;
        if (state.SelectedItem is { } sel && slotButtons.TryGetValue(sel, out var selected)) { Ui.FocusLater(selected); return; }
        foreach (var child in slots.GetChildren())
            if (child is Button b) { Ui.FocusLater(b); return; }
    }
}
