using System.Linq;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Text;
using LastBell.Core.Views;
using LastBell.Game.Hooks;
using LastBell.Game.PlayerInput;
using LastBell.Game.Runtime;

namespace LastBell.Game.Presentation.Placeholders;

/// <summary>
/// Temporary inventory strip (until the UI agent claims <see cref="UiPanel.Inventory"/>): visible in
/// Core's Inventory mode, one button per owned item (archived ones dimmed, at the end). Left click =
/// select / combine with the selected item, right click or Backspace = look (drawer stays open).
/// All clicks go through <see cref="WorldInput"/>, i.e. Core's resolver. Also shows the selected
/// item's name next to the cursor (stand-in for the item icon).
/// </summary>
public partial class PlaceholderInventoryStrip : Control
{
    private PanelContainer panel = null!;
    private HBoxContainer row = null!;
    private Label cursorItem = null!;
    private string signature = "";

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
        panel = PlaceholderStyle.Panel(0.92f);
        panel.Position = new Vector2(40, 1080 - 150);
        panel.CustomMinimumSize = new Vector2(1840, 120);
        var box = new VBoxContainer();
        box.AddChild(PlaceholderStyle.Label(TextService.Ui("ui.inventory.title"), 20, new Color(1f, 0.83f, 0.45f)));
        var scroll = new ScrollContainer { CustomMinimumSize = new Vector2(1810, 70), VerticalScrollMode = ScrollContainer.ScrollMode.Disabled };
        row = new HBoxContainer();
        row.AddThemeConstantOverride("separation", 10);
        scroll.AddChild(row);
        box.AddChild(scroll);
        panel.AddChild(box);
        AddChild(panel);
        panel.Visible = false;
        cursorItem = PlaceholderStyle.Label("", 22, new Color(1f, 0.9f, 0.6f));
        AddChild(cursorItem);
        cursorItem.Visible = false;
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        var game = GameRuntime.Instance;
        if (!game.IsReady) return;
        var state = game.State;
        bool claimed = UiBus.IsClaimed(UiPanel.Inventory);
        bool open = !claimed && state.Mode == GameMode.Inventory;
        if (open != panel.Visible)
        {
            panel.Visible = open;
            if (open)
            {
                Rebuild(state);
                FocusFirst();
            }
        }
        if (open && Signature(state) != signature) Rebuild(state);
        // Selected item follows the cursor (icon stand-in).
        if (!claimed && state.SelectedItem is { } selected && game.Content.FindItem(selected) is { } item)
        {
            cursorItem.Visible = true;
            cursorItem.Text = "[" + TextService.Get(TextKeys.NameOf(item)) + "]";
            cursorItem.Position = GetViewport().GetMousePosition() + new Vector2(18, -34);
        }
        else cursorItem.Visible = false;
    }

    private static string Signature(GameState state) => string.Join(",", state.Inventory) + "|" + state.SelectedItem;

    private void Rebuild(GameState state)
    {
        var game = GameRuntime.Instance;
        signature = Signature(state);
        foreach (var child in row.GetChildren()) child.QueueFree();
        var items = ViewBuilder.Inventory(game.Content, state);
        if (items.Count == 0) row.AddChild(PlaceholderStyle.Label(TextService.Ui("ui.inventory.empty"), 22));
        foreach (var item in items.Where(i => !i.IsArchived).Concat(items.Where(i => i.IsArchived)))
        {
            var view = item;
            var button = PlaceholderStyle.Button(TextService.Get(view.Name), 22);
            button.ToggleMode = true;
            button.ButtonPressed = view.IsSelected;
            if (view.IsArchived) button.Modulate = new Color(1, 1, 1, 0.55f);
            string icon = "res://assets/" + view.Icon;
            if (!string.IsNullOrEmpty(view.Icon) && ResourceLoader.Exists(icon))
            {
                button.Icon = GD.Load<Texture2D>(icon);
                button.ExpandIcon = true;
            }
            button.GuiInput += e => OnItemInput(view, e);
            button.MouseEntered += () => WorldInput.HoverItem(view.Id, GetViewport().GetMousePosition());
            button.MouseExited += WorldInput.ClearHover;
            button.FocusEntered += () => WorldInput.HoverItem(view.Id, button.GlobalPosition + new Vector2(0, -60));
            row.AddChild(button);
        }
    }

    private void OnItemInput(InventoryItemView item, InputEvent e)
    {
        if (e is InputEventMouseButton { Pressed: true } mb && mb.ButtonIndex is MouseButton.Left or MouseButton.Right)
        {
            AcceptEvent();
            WorldInput.Submit(new Hit.Item(item.Id), mb.ButtonIndex == MouseButton.Right ? PointerButton.Right : PointerButton.Left);
        }
        else if (e is InputEventKey { Pressed: true, Echo: false } key)
        {
            if (key.IsAction(InputActions.Confirm))
            {
                AcceptEvent();
                WorldInput.Submit(new Hit.Item(item.Id), PointerButton.Left);
            }
            else if (key.IsAction(InputActions.Back))
            {
                AcceptEvent();
                WorldInput.Submit(new Hit.Item(item.Id), PointerButton.Right);
            }
        }
    }

    private void FocusFirst()
    {
        if (row.GetChildCount() > 0 && row.GetChild(0) is Button b) b.CallDeferred(Control.MethodName.GrabFocus);
    }
}
