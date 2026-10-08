using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Game.PlayerInput;
using LastBell.Game.Presentation;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Menus;
using LastBell.Game.UI.Theme;
using LastBell.Game.World;

namespace LastBell.Game.UI.Common;

/// <summary>
/// What a phone or tablet asks of an app (docs/PORTS.md "Touch controls"); the notifications below only exist on
/// Android and iOS, so a desktop build never runs any of it.
/// <list type="bullet">
/// <item>The app goes to the background (Home, the app switcher, a call; <c>NOTIFICATION_APPLICATION_PAUSED</c>): the
/// game is autosaved at once, because the system may end a background app at any time. The engine stops there, so
/// nothing moves while the player is away.</item>
/// <item>The app comes back (<c>NOTIFICATION_APPLICATION_RESUMED</c>): when the player left from the scene, the pause
/// menu opens, so nobody comes back into a running game (it opens now and not when leaving: a screen opened in the
/// last moment before the engine stops is laid out half, seen on Android 16 as a scrolled-away first button). Lines
/// and cutscenes need no menu: the line is still there. The first frame may carry the whole time away as its delta;
/// the line on screen must not count it as reading time.</item>
/// <item>The system Back button or gesture (<c>NOTIFICATION_WM_GO_BACK_REQUEST</c>) is Esc: it closes the top screen,
/// skips a line, cancels the selected item or opens the pause menu; on the title screen it asks whether to quit.
/// Godot's default (quit at once) is turned off. One press of a Back button reaches the game twice: Godot's key
/// handler asks when the key goes down and Android's back dispatcher when it comes up (platform/android/
/// android_input_handler.cpp and GodotActivity.kt in 4.7.2), so the second request of the same press is dropped
/// (<see cref="IsSamePress"/>).</item>
/// </list>
/// The title screen is never saved over a game: nothing is on screen there that the player could lose.
/// </summary>
public partial class MobileLifecycle : Node
{
    /// <summary>The singleton (QA: <c>--input app:pause|resume|back</c>).</summary>
    public static MobileLifecycle? Instance { get; private set; }

    /// <summary>True while the autosave of <see cref="Background"/> is written (no frame capture for its thumbnail then).</summary>
    public static bool SavingInBackground { get; private set; }

    /// <summary>Two Back requests closer than this are one press (also the slack between a key event and its request).</summary>
    public const double BackRepeatSeconds = 0.25;

    private double lastBack = -100;
    private double backKeyDown = -100;
    private double backKeyUp = -100;
    private bool backKeyHeld;
    private bool pauseOnReturn;

    private static double Now => Time.GetTicksMsec() / 1000.0;

    /// <inheritdoc />
    public override void _Input(InputEvent e)
    {
        // The Back key itself (not handled here): when it went down and up, to tell one long press from two presses.
        if (e is not InputEventKey { Echo: false } key || (key.Keycode != Key.Back && key.PhysicalKeycode != Key.Back)) return;
        backKeyHeld = key.Pressed;
        if (key.Pressed) backKeyDown = Now;
        else backKeyUp = Now;
    }

    /// <summary>
    /// True when a Back request at <paramref name="now"/> belongs to a press that was acted on already: it follows the
    /// last acted request within <see cref="BackRepeatSeconds"/>, or the Back key of that request is still down or has
    /// just come up (a long press: the first request at key down, the second at key up). Pure (QA).
    /// </summary>
    public static bool IsSamePress(double now, double lastActed, bool keyHeld, double keyDown, double keyUp) =>
        now - lastActed < BackRepeatSeconds ||
        ((keyHeld || now - keyUp < BackRepeatSeconds) && lastActed >= keyDown - BackRepeatSeconds);

    /// <inheritdoc />
    public override void _Ready()
    {
        Instance = this;
        ProcessMode = ProcessModeEnum.Always;
        if (TouchMode.IsMobile) GetTree().QuitOnGoBack = false;
    }

    /// <inheritdoc />
    public override void _ExitTree()
    {
        if (Instance == this) Instance = null;
    }

    /// <inheritdoc />
    public override void _Notification(int what)
    {
        if (what == NotificationApplicationPaused) Background();
        else if (what == NotificationApplicationResumed) Foreground();
        else if (what == NotificationWMGoBackRequest) Back();
    }

    private static bool InScene(GameRuntime game, UiRoot ui) =>
        game.State.Mode is GameMode.World or GameMode.Inventory && !ui.HasModal && WorldStage.Instance is { Transitioning: false };

    /// <summary>The app goes to the background: autosave.</summary>
    public void Background()
    {
        var game = GameRuntime.Instance;
        var ui = UiRoot.Instance;
        pauseOnReturn = false;
        if (!game.IsReady || ui is null) return;
        InputRouter.Instance?.Dispatch(LogicalCommand.HideMarkers, null);
        if (ui.MainMenuOpen) return;
        SavingInBackground = true;
        try { game.Autosave(); }
        finally { SavingInBackground = false; }
        pauseOnReturn = InScene(game, ui);
        GD.Print($"LastBell: app to the background, autosave {(game.AutosaveEnabled ? "written" : "off")}, mode {game.State.Mode}");
    }

    /// <summary>The app is back on screen: the pause menu for a player who left from the scene.</summary>
    public void Foreground()
    {
        DialoguePresenter.Instance?.SkipFrameTime();
        var game = GameRuntime.Instance;
        var ui = UiRoot.Instance;
        bool pause = pauseOnReturn && game.IsReady && ui is not null && InScene(game, ui);
        pauseOnReturn = false;
        if (pause) game.Update(s => GameRules.OpenOverlay(s, GameMode.Pause));
        GD.Print($"LastBell: app back in the foreground{(pause ? ", paused" : "")}");
    }

    /// <summary>The system Back button: Esc.</summary>
    public void Back()
    {
        double now = Now;
        bool repeat = IsSamePress(now, lastBack, backKeyHeld, backKeyDown, backKeyUp);
        GD.Print($"LastBell: Back request{(repeat ? " (repeat, ignored)" : "")}, mode {GameRuntime.Instance.State.Mode}");
        if (repeat) return;
        lastBack = now;
        var ui = UiRoot.Instance;
        if (ui is null)
        {
            GetTree().Quit();
            return;
        }
        if (ui.TopModal is { } top)
        {
            if (top is MainMenuScreen) ui.Confirm(Ui.T("ui.menu.quit_confirm"), Ui.T("ui.menu.quit"), () => GetTree().Quit());
            else top.Back();
            return;
        }
        WorldInput.Dispatch(LogicalCommand.Cancel);
    }
}
