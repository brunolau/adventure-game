using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Game.Hooks;
using LastBell.Game.Presentation;
using LastBell.Game.Runtime;
using LastBell.Game.World;

namespace LastBell.Game.PlayerInput;

/// <summary>
/// Maps raw input (mouse, keyboard, touch) onto <see cref="LogicalCommand"/>s
/// and routes them by Core's top mode: world/inventory → <see cref="InteractionController"/>,
/// dialogue lines and cutscenes → <see cref="DialoguePresenter"/>, overlays → Core close/escape.
/// It reads only unhandled input, so HUD and UI controls get their clicks first.
/// One logical left click is one action (no verb choice).
/// Touch: Godot emulates the first finger as a mouse (device <see cref="InputEvent.DeviceIdEmulation"/>), so the GUI
/// still gets taps first; the emulated events that reach the world feed <see cref="TouchGestures"/>
/// (tap = Primary, long press = Secondary, two-finger hold = markers) instead of acting on press.
/// Space is hold-to-show (owner override 2026-10-05): press = <see cref="LogicalCommand.ShowMarkers"/>, release (seen in
/// <c>_Input</c>, so no GUI can swallow it) or losing the window focus = <see cref="LogicalCommand.HideMarkers"/>.
/// The second press of a world double click (or double Enter) that already acted is not passed on to a line that
/// started from it (no accidental skip of the first line).
/// </summary>
public partial class InputRouter : Node2D
{
    /// <summary>The singleton router.</summary>
    public static InputRouter? Instance { get; private set; }

    private readonly TouchGestures touch = new();

    private const int EmulatedDevice = (int)InputEvent.DeviceIdEmulation;

    private static double Now => Time.GetTicksMsec() / 1000.0;

    private Vector2 ToCanvas(Vector2 viewportPosition) => GetCanvasTransform().AffineInverse() * viewportPosition;

    /// <summary>The mouse position in canvas px (hidden QA windows: the last mouse event, QaWindow.UseEventPointer).</summary>
    private Vector2 Pointer() => LastBell.Game.Diagnostics.QaWindow.UseEventPointer
        ? ToCanvas(LastBell.Game.Diagnostics.QaWindow.ViewportPointer(GetViewport()))
        : GetGlobalMousePosition();

    /// <inheritdoc />
    public override void _Ready()
    {
        Instance = this;
        InputActions.EnsureDefaults();
        ProcessMode = ProcessModeEnum.Always;
        // A save made while Space was held carries the markers flag: a loaded game starts without them.
        if (GameRuntime.Instance is { } game)
            game.SessionReplaced += () => Callable.From(ClearStaleMarkers).CallDeferred();
    }

    /// <summary>True while Space (or two fingers, or the HUD eye) holds the markers on.</summary>
    public bool MarkersHeld { get; private set; }

    /// <inheritdoc />
    public override void _Input(InputEvent e)
    {
        LastBell.Game.Diagnostics.QaWindow.NotePointer(e);
        // Extra fingers are not emulated as a mouse; count them for the two-finger hold (never handled here).
        if (e is InputEventScreenTouch { Index: > 0 } st && (touch.Active || !st.Pressed))
        {
            if (touch.Touch(st.Index, ToCanvas(st.Position), st.Pressed, Now) is { } g && g.Command is LogicalCommand.ShowMarkers or LogicalCommand.HideMarkers)
                Dispatch(g.Command, g.Position);
            return;
        }
        // Space released: always hide, whatever has the focus.
        if (e is InputEventKey { Pressed: false } key && key.IsAction(InputActions.ToggleLabels) && MarkersHeld)
            Dispatch(LogicalCommand.HideMarkers, null);
    }

    private void ClearStaleMarkers()
    {
        var game = GameRuntime.Instance;
        if (game.IsReady && game.State.HotspotLabels && !MarkersHeld && !PresentationSettings.QaTextLabels)
            game.Update(s => GameRules.SetHotspots(s, false));
    }

    /// <inheritdoc />
    public override void _Notification(int what)
    {
        if (what == NotificationApplicationFocusOut && MarkersHeld) Dispatch(LogicalCommand.HideMarkers, null);
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        if (touch.Poll(Now) is { } gesture) Dispatch(gesture.Command, gesture.Position);
    }

    /// <inheritdoc />
    public override void _UnhandledInput(InputEvent e)
    {
        if (e is InputEventMouseMotion motion)
        {
            if (motion.Device == EmulatedDevice) touch.Drag(0, ToCanvas(motion.Position));
            InteractionController.Instance?.PointerMoved(Pointer());
            return;
        }
        if (e is InputEventMouseButton { Device: EmulatedDevice, ButtonIndex: MouseButton.Left } finger)
        {
            if (touch.Touch(0, ToCanvas(finger.Position), finger.Pressed, Now) is { } gesture) Dispatch(gesture.Command, gesture.Position);
            GetViewport().SetInputAsHandled();
            return;
        }
        if (e is InputEventMouseButton mb && mb.Pressed && !mb.IsEcho())
        {
            if (mb.ButtonIndex == MouseButton.Left) { Dispatch(LogicalCommand.Primary, Pointer()); GetViewport().SetInputAsHandled(); }
            else if (mb.ButtonIndex == MouseButton.Right) { Dispatch(LogicalCommand.Secondary, Pointer()); GetViewport().SetInputAsHandled(); }
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
        if (command == LogicalCommand.HideMarkers)
        {
            // Release hides in every mode and also during a transition: markers never stay stuck on.
            MarkersHeld = false;
            if (game.State.HotspotLabels && !PresentationSettings.QaTextLabels) game.Update(s => GameRules.SetHotspots(s, false));
            return;
        }
        if (stage is null || stage.Transitioning) return;
        var state = game.State;
        var controller = InteractionController.Instance;
        var presenter = DialoguePresenter.Instance;

        switch (state.Mode)
        {
            case GameMode.World or GameMode.Inventory:
                // The second Esc of a double Esc that ended the sequence does not open the pause menu.
                if (command == LogicalCommand.Cancel && presenter?.IsEscapeFollowUp() == true) break;
                RouteWorld(command, position, controller);
                break;
            case GameMode.Dialogue when state.ActiveLineId is null:
                // Topic menu: buttons handle choices; Esc/Backspace leave the conversation (not the second Esc of a
                // double Esc that skipped the topic's last line: the menu has just come back).
                if (command == LogicalCommand.Cancel && presenter?.IsEscapeFollowUp() == true) break;
                if (command is LogicalCommand.Cancel or LogicalCommand.Back) game.Update(LastBell.Core.Rules.Dialogue.CloseMenu);
                break;
            case GameMode.Dialogue or GameMode.Cutscene:
                // The second press of a double click / double Enter that started this line belongs to the world action.
                if (command == LogicalCommand.Primary && controller?.IsDoubleClickFollowUp(position) == true) break;
                if (command is LogicalCommand.Confirm or LogicalCommand.ConfirmSkip && controller?.IsConfirmFollowUp() == true) break;
                if (command is LogicalCommand.Primary or LogicalCommand.Secondary or LogicalCommand.Confirm or LogicalCommand.ConfirmSkip
                    or LogicalCommand.ToggleLabels or LogicalCommand.ShowMarkers)
                    presenter?.Advance();
                else if (command == LogicalCommand.Cancel)
                    presenter?.Escape(); // this line; a second Esc within 0.5 s: the whole sequence (PT-F13)
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

    private void RouteWorld(LogicalCommand command, Vector2? position, InteractionController? controller)
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
            case LogicalCommand.ShowMarkers:
                MarkersHeld = true;
                game.Update(s => GameRules.SetHotspots(s, true)); // world mode only (Core); the open drawer ignores it
                break;
            case LogicalCommand.ConfirmSkip:
                controller?.ConfirmFocused(skipWalk: true);
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
        HoverPresenter.Show(game.Session.Hover(new Hit.Item(itemId)), canvasPosition, game.State.SelectedItem is not null, false, fromInventory: true);
    }

    /// <summary>Hide the hover text.</summary>
    public static void ClearHover() => HoverPresenter.Hide();
}
