using Godot;
using LastBell.Core.Rules;

namespace LastBell.Game.PlayerInput;

/// <summary>
/// Device-independent player commands. Mouse, keyboard (and later touch or a gamepad) are mapped
/// onto these by <see cref="InputRouter"/>; UI code can inject them through <see cref="WorldInput"/>.
/// </summary>
public enum LogicalCommand
{
    /// <summary>Logical left click at a canvas position.</summary>
    Primary,
    /// <summary>Right click at a canvas position: look / inventory / cancel selection.</summary>
    Secondary,
    /// <summary>Toggle the hotspot markers (QA <c>key:ToggleLabels</c>); Space itself is hold-to-show (<see cref="ShowMarkers"/>).</summary>
    ToggleLabels,
    /// <summary>Space pressed / two fingers down / HUD eye pressed: show the markers of every visible target (world mode).</summary>
    ShowMarkers,
    /// <summary>Space released / fingers lifted / HUD eye released: hide the markers (any mode).</summary>
    HideMarkers,
    /// <summary>Shift+Enter: left click on the focused target and skip the walk (as a double click).</summary>
    ConfirmSkip,
    /// <summary>Tab: focus the next target (accessible order).</summary>
    FocusNext,
    /// <summary>Shift+Tab: focus the previous target.</summary>
    FocusPrevious,
    /// <summary>Enter: left click on the focused target / advance a line.</summary>
    Confirm,
    /// <summary>Backspace: right click on the focused target (or empty floor).</summary>
    Back,
    /// <summary>Esc: cancel selection, close the top panel, skip a cutscene, or pause.</summary>
    Cancel,
    /// <summary>I: open/close the inventory.</summary>
    Inventory,
    /// <summary>J: journal.</summary>
    Journal,
    /// <summary>M: map.</summary>
    Map,
    /// <summary>H: hints.</summary>
    Hint,
    /// <summary>T: chronometer era chooser (only at an open anchor node).</summary>
    Travel,
    /// <summary>F3: dev overlay (rects over painted art).</summary>
    DevOverlay,
    /// <summary>F5: quick save (dev convenience).</summary>
    QuickSave,
    /// <summary>F9: quick load (dev convenience).</summary>
    QuickLoad,
}

/// <summary>Input map action names and their default bindings (registered at startup, rebindable by the settings UI).</summary>
public static class InputActions
{
    /// <summary>Space (hold: markers; the action name is kept for saved key bindings).</summary>
    public const string ToggleLabels = "lb_toggle_labels";
    /// <summary>Shift+Enter.</summary>
    public const string ConfirmSkip = "lb_confirm_skip";
    /// <summary>Tab.</summary>
    public const string FocusNext = "lb_focus_next";
    /// <summary>Shift+Tab.</summary>
    public const string FocusPrevious = "lb_focus_previous";
    /// <summary>Enter.</summary>
    public const string Confirm = "lb_confirm";
    /// <summary>Backspace.</summary>
    public const string Back = "lb_back";
    /// <summary>Escape.</summary>
    public const string Cancel = "lb_cancel";
    /// <summary>I.</summary>
    public const string Inventory = "lb_inventory";
    /// <summary>J.</summary>
    public const string Journal = "lb_journal";
    /// <summary>M.</summary>
    public const string Map = "lb_map";
    /// <summary>H.</summary>
    public const string Hint = "lb_hint";
    /// <summary>T.</summary>
    public const string Travel = "lb_travel";
    /// <summary>F3.</summary>
    public const string DevOverlay = "lb_dev_overlay";
    /// <summary>F5.</summary>
    public const string QuickSave = "lb_quick_save";
    /// <summary>F9.</summary>
    public const string QuickLoad = "lb_quick_load";

    /// <summary>Action → command, checked in this order (Shift+Tab before Tab).</summary>
    public static readonly (string Action, LogicalCommand Command)[] Bindings =
    {
        (FocusPrevious, LogicalCommand.FocusPrevious),
        (FocusNext, LogicalCommand.FocusNext),
        (ToggleLabels, LogicalCommand.ShowMarkers), // released: HideMarkers (InputRouter._Input)
        (ConfirmSkip, LogicalCommand.ConfirmSkip), // before Confirm: Shift+Enter also matches Enter
        (Confirm, LogicalCommand.Confirm),
        (Back, LogicalCommand.Back),
        (Cancel, LogicalCommand.Cancel),
        (Inventory, LogicalCommand.Inventory),
        (Journal, LogicalCommand.Journal),
        (Map, LogicalCommand.Map),
        (Hint, LogicalCommand.Hint),
        (Travel, LogicalCommand.Travel),
        (DevOverlay, LogicalCommand.DevOverlay),
        (QuickSave, LogicalCommand.QuickSave),
        (QuickLoad, LogicalCommand.QuickLoad),
    };

    /// <summary>Registers the default bindings for actions that do not exist yet.</summary>
    public static void EnsureDefaults()
    {
        Add(ToggleLabels, Key.Space);
        Add(FocusPrevious, Key.Tab, shift: true);
        Add(FocusNext, Key.Tab);
        Add(ConfirmSkip, Key.Enter, shift: true);
        Add(Confirm, Key.Enter, false, Key.KpEnter);
        Add(Back, Key.Backspace);
        Add(Cancel, Key.Escape);
        Add(Inventory, Key.I);
        Add(Journal, Key.J);
        Add(Map, Key.M);
        Add(Hint, Key.H);
        Add(Travel, Key.T);
        Add(DevOverlay, Key.F3);
        Add(QuickSave, Key.F5);
        Add(QuickLoad, Key.F9);
        // Space is the markers key (hold) in the world and in the open inventory (CODING_AGENT_START input table);
        // Godot's built-in ui_accept also contains Space, so a focused inventory slot or HUD button would
        // swallow it as "press". GUI accept stays on Enter / keypad Enter.
        foreach (var e in InputMap.ActionGetEvents("ui_accept"))
            if (e is InputEventKey k && (k.Keycode == Key.Space || k.PhysicalKeycode == Key.Space)) InputMap.ActionEraseEvent("ui_accept", e);
    }

    private static void Add(string action, Key key, bool shift = false, params Key[] alternatives)
    {
        if (InputMap.HasAction(action)) return;
        InputMap.AddAction(action);
        InputMap.ActionAddEvent(action, new InputEventKey { PhysicalKeycode = key, ShiftPressed = shift });
        foreach (var alt in alternatives) InputMap.ActionAddEvent(action, new InputEventKey { PhysicalKeycode = alt });
    }

    /// <summary>The pointer button of a pointer command.</summary>
    public static PointerButton ButtonOf(LogicalCommand command) => command == LogicalCommand.Secondary ? PointerButton.Right : PointerButton.Left;
}
