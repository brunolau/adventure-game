using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Game.Hooks;
using LastBell.Game.Presentation;
using LastBell.Game.Runtime;
using LastBell.Game.World;

namespace LastBell.Game.PlayerInput;

/// <summary>
/// Maps raw input (mouse, keyboard; touch arrives as emulated mouse) onto <see cref="LogicalCommand"/>s
/// and routes them by Core's top mode: world/inventory → <see cref="InteractionController"/>,
/// dialogue lines and cutscenes → <see cref="DialoguePresenter"/>, overlays → Core close/escape.
/// It reads only unhandled input, so HUD and UI controls get their clicks first.
/// One logical left click is one action (no verb choice).
/// </summary>
public partial class InputRouter : Node2D
{
    /// <summary>The singleton router.</summary>
    public static InputRouter? Instance { get; private set; }

    /// <inheritdoc />
    public override void _Ready()
    {
        Instance = this;
        InputActions.EnsureDefaults();
        ProcessMode = ProcessModeEnum.Always;
    }

    /// <inheritdoc />
    public override void _UnhandledInput(InputEvent e)
    {
        if (e is InputEventMouseMotion)
        {
            InteractionController.Instance?.PointerMoved(GetGlobalMousePosition());
            return;
        }
        if (e is InputEventMouseButton mb && mb.Pressed && !mb.IsEcho())
        {
            if (mb.ButtonIndex == MouseButton.Left) { Dispatch(LogicalCommand.Primary, GetGlobalMousePosition()); GetViewport().SetInputAsHandled(); }
            else if (mb.ButtonIndex == MouseButton.Right) { Dispatch(LogicalCommand.Secondary, GetGlobalMousePosition()); GetViewport().SetInputAsHandled(); }
            return;
        }
        if (e is InputEventKey { Pressed: true, Echo: false })
        {
            foreach (var (action, command) in InputActions.Bindings)
            {
                if (!e.IsAction(action)) continue;
                Dispatch(command, null);
                GetViewport().SetInputAsHandled();
                return;
            }
        }
    }

    /// <summary>Routes a logical command by the current Core mode. Pointer commands need a canvas position.</summary>
    public void Dispatch(LogicalCommand command, Vector2? position)
    {
        var game = GameRuntime.Instance;
        if (!game.IsReady) return;
        var stage = WorldStage.Instance;
        if (command == LogicalCommand.DevOverlay) { ToggleDevOverlay(); return; }
        if (stage is null || stage.Transitioning) return;
        var state = game.State;
        var controller = InteractionController.Instance;
        var presenter = DialoguePresenter.Instance;

        switch (state.Mode)
        {
            case GameMode.World or GameMode.Inventory:
                RouteWorld(command, position, controller);
                break;
            case GameMode.Dialogue when state.ActiveLineId is null:
                // Topic menu: buttons handle choices; Esc/Backspace leave the conversation.
                if (command is LogicalCommand.Cancel or LogicalCommand.Back) game.Update(LastBell.Core.Rules.Dialogue.CloseMenu);
                break;
            case GameMode.Dialogue or GameMode.Cutscene:
                if (command is LogicalCommand.Primary or LogicalCommand.Secondary or LogicalCommand.Confirm or LogicalCommand.ToggleLabels)
                    presenter?.Advance();
                else if (command == LogicalCommand.Cancel)
                    presenter?.Skip();
                break;
            case GameMode.Puzzle:
                if (command == LogicalCommand.Cancel) game.ClosePuzzle();
                break;
            case GameMode.Journal or GameMode.Map or GameMode.Pause:
                if (command == LogicalCommand.Cancel ||
                    (command == LogicalCommand.Journal && state.Mode == GameMode.Journal) ||
                    (command == LogicalCommand.Map && state.Mode == GameMode.Map))
                    game.Update(GameRules.Escape);
                break;
        }
    }

    private static void RouteWorld(LogicalCommand command, Vector2? position, InteractionController? controller)
    {
        var game = GameRuntime.Instance;
        switch (command)
        {
            case LogicalCommand.Primary or LogicalCommand.Secondary when position is { } p:
                controller?.PointerAt(p, InputActions.ButtonOf(command));
                break;
            case LogicalCommand.ToggleLabels:
                game.Update(GameRules.ToggleHotspots);
                break;
            case LogicalCommand.FocusNext:
                controller?.MoveFocus(+1);
                break;
            case LogicalCommand.FocusPrevious:
                controller?.MoveFocus(-1);
                break;
            case LogicalCommand.Confirm:
                controller?.ConfirmFocused();
                break;
            case LogicalCommand.Back:
                controller?.BackFocused();
                break;
            case LogicalCommand.Cancel:
                game.Update(GameRules.Escape);
                break;
            case LogicalCommand.Inventory:
                game.Update(GameRules.ToggleInventory);
                break;
            case LogicalCommand.Journal:
                game.Update(s => GameRules.OpenOverlay(s, GameMode.Journal));
                UiBus.RequestOpen(UiPanel.Journal);
                break;
            case LogicalCommand.Map:
                game.Update(s => GameRules.OpenOverlay(s, GameMode.Map));
                UiBus.RequestOpen(UiPanel.Map);
                break;
            case LogicalCommand.Hint:
                UiBus.RequestOpen(UiPanel.Hints);
                break;
            case LogicalCommand.Travel:
                UiBus.RequestOpen(UiPanel.Portal);
                break;
            case LogicalCommand.QuickSave:
                if (game.Save("quick")) UiBus.PostNotice("ui.dev.quick_saved");
                break;
            case LogicalCommand.QuickLoad:
                if (!GameRuntime.SlotExists("quick")) UiBus.PostNotice("ui.dev.no_save");
                else game.Load("quick");
                break;
        }
    }

    private static void ToggleDevOverlay()
    {
        var stage = WorldStage.Instance;
        if (stage is null) return;
        stage.DevOverlay = !stage.DevOverlay;
        if (stage.Current is not null) stage.Current.DevOverlayVisible = stage.DevOverlay;
    }
}

/// <summary>
/// Static entry points for UI and touch code to drive the world through the normal input path
/// (never by changing Core state behind the resolver's back).
/// </summary>
public static class WorldInput
{
    /// <summary>Same as a pointer press on a hit (e.g. an inventory slot: <c>new Hit.Item(id)</c>).</summary>
    public static void Submit(Hit hit, PointerButton button) => InteractionController.Instance?.Submit(hit, button);

    /// <summary>A pointer press at a canvas position (touch tap → Left, long press → Right).</summary>
    public static void PointerAt(Vector2 canvasPosition, PointerButton button) => InteractionController.Instance?.PointerAt(canvasPosition, button);

    /// <summary>Any logical command (keyboard/touch buttons of the HUD).</summary>
    public static void Dispatch(LogicalCommand command, Vector2? canvasPosition = null) => InputRouter.Instance?.Dispatch(command, canvasPosition);

    /// <summary>Hover over an inventory item (shows name; with a selected item the action line only for an executable recipe).</summary>
    public static void HoverItem(string itemId, Vector2 canvasPosition)
    {
        var game = GameRuntime.Instance;
        HoverPresenter.Show(game.Session.Hover(new Hit.Item(itemId)), canvasPosition, game.State.SelectedItem is not null, false);
    }

    /// <summary>Hide the hover text.</summary>
    public static void ClearHover() => HoverPresenter.Hide();
}
