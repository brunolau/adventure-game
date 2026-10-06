using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Text;
using LastBell.Game.Hooks;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Cutscenes;
using LastBell.Game.UI.Dialogue;
using LastBell.Game.UI.Diagnostics;
using LastBell.Game.UI.Hud;
using LastBell.Game.UI.Inventory;
using LastBell.Game.UI.Journal;
using LastBell.Game.UI.Map;
using LastBell.Game.UI.Menus;
using LastBell.Game.UI.Puzzles;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;
using LastBell.Game.World;

namespace LastBell.Game.UI;

/// <summary>
/// Root of the UI (res://scenes/ui/UiRoot.tscn, instanced by Main under the HUD host, CanvasLayer 40).
/// Builds every screen, registers the views and claims the panels with <see cref="UiBus"/>, shows
/// the Core-mode panels (inventory, journal, map, pause, puzzle) from <see cref="GameRuntime.ModeChanged"/>,
/// keeps a stack of UI-only modals (main menu, hints, save/load, settings, help, credits, dialogs,
/// ending) and blocks world keys while one is open, and applies the HUD scale.
/// Layers: this control (unscaled) holds the cutscene frame and subtitles; <c>Scaled</c> holds the
/// HUD and all screens and is scaled by the HUD scale setting; CanvasLayer 60 holds the era card
/// (above the world's transition fade), CanvasLayer 70 the hover label at the cursor and the contextual cursor.
/// </summary>
public partial class UiRoot : Control
{
    private Control scaled = null!;
    private Control modalLayer = null!;
    private readonly List<ModalScreen> stack = new();
    private CursorLayer cursor = null!;
    private InventoryPanel inventory = null!;
    private JournalScreen journal = null!;
    private MapScreen map = null!;
    private PauseScreen pause = null!;
    private PuzzleModal puzzle = null!;
    private TopicMenuView? topicMenu;

    /// <summary>The puzzle modal (QA harness).</summary>
    public PuzzleModal PuzzleView => puzzle;
    private MainMenuScreen mainMenu = null!;
    private HintScreen hints = null!;
    private SaveLoadScreen saveLoad = null!;
    private SettingsScreen settings = null!;
    private HelpScreen help = null!;
    private CreditsScreen credits = null!;
    private PortalChooser portal = null!;
    private EndingSequence ending = null!;
    private AlbumScreen album = null!;
    private TipsOverlay tips = null!;
    private float appliedScale = -1;
    private bool endingPending;
    private Image? worldShot;

    /// <summary>The singleton.</summary>
    public static UiRoot? Instance { get; private set; }

    /// <summary>The HUD (and hover view).</summary>
    public HudView Hud { get; private set; } = null!;

    /// <summary>The hover label at the cursor (owner control changes 2026-10-05).</summary>
    public HoverLabel HoverLabel { get; private set; } = null!;

    /// <summary>Notices.</summary>
    public ToastLayer Toasts { get; private set; } = null!;

    /// <summary>True while a UI-only modal (menu, dialog, settings ...) is open.</summary>
    public bool HasModal => stack.Count > 0;

    /// <summary>
    /// True when a screen lies under a canvas point or covers the scene: any UI-only modal (hints, menus, settings
    /// ...), the journal, map, pause and puzzle screens, or the open bag's bar and detail card. The world hover label
    /// hides there (orchestrator decision after the playtests, PT-S23).
    /// </summary>
    public bool ScreenCovers(Vector2 point) =>
        HasModal || journal.Visible || map.Visible || pause.Visible || puzzle.Visible || inventory.CoversPoint(point);

    /// <summary>The topic menu panel in canvas px while a conversation's menu is open, else null (toast placement).</summary>
    public Rect2? TopicMenuRect => topicMenu?.PanelRect;

    /// <summary>The topmost UI-only modal, or null.</summary>
    public ModalScreen? TopModal => stack.Count > 0 ? stack[^1] : null;

    /// <summary>A snapshot of the last world frame (taken when pause opened; save thumbnails).</summary>
    public Image? WorldShot => worldShot;

    /// <inheritdoc />
    public override void _Ready()
    {
        Instance = this;
        Name = "UiRoot";
        ProcessMode = ProcessModeEnum.Always;
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
        Theme = UiTheme.Theme;

        var game = GameRuntime.Instance;
        GetViewport().GuiFocusChanged += OnGuiFocusChanged; // keyboard focus stays in the top screen (AT19)
        bool harness = LaunchArgs.Any && !LaunchArgs.PlayerStart; // --menu: a QA run that starts like a player's
        UiSettings.Load();
        UiSettings.Apply(keepTextTiming: false, applyWindow: !LaunchArgs.Any);

        // Unscaled: cutscene frame under the subtitles.
        var cutscene = new CutscenePlayer { Name = "CutscenePlayer" };
        AddChild(cutscene);
        var subtitles = new SubtitleView { Name = "Subtitles" };
        AddChild(subtitles);

        // Scaled: HUD and screens.
        scaled = new Control { Name = "Scaled", MouseFilter = MouseFilterEnum.Ignore };
        AddChild(scaled);
        Hud = new HudView { Name = "Hud" };
        scaled.AddChild(Hud);
        var topics = new TopicMenuView { Name = "TopicMenu" };
        scaled.AddChild(topics);
        topicMenu = topics;
        inventory = new InventoryPanel { Name = "Inventory" };
        scaled.AddChild(inventory);
        inventory.Init(Hud);
        journal = new JournalScreen { Name = "Journal" };
        scaled.AddChild(journal);
        map = new MapScreen { Name = "Map" };
        scaled.AddChild(map);
        pause = new PauseScreen { Name = "Pause" };
        scaled.AddChild(pause);
        puzzle = new PuzzleModal { Name = "Puzzle" };
        scaled.AddChild(puzzle);
        modalLayer = new Control { Name = "Modals", MouseFilter = MouseFilterEnum.Ignore };
        modalLayer.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        scaled.AddChild(modalLayer);
        mainMenu = AddModal(new MainMenuScreen { Name = "MainMenu" });
        hints = AddModal(new HintScreen { Name = "Hints" });
        saveLoad = AddModal(new SaveLoadScreen { Name = "SaveLoad" });
        settings = AddModal(new SettingsScreen { Name = "Settings" });
        help = AddModal(new HelpScreen { Name = "Help" });
        credits = AddModal(new CreditsScreen { Name = "Credits" });
        portal = AddModal(new PortalChooser { Name = "Portal" });
        ending = AddModal(new EndingSequence { Name = "Ending" });
        album = AddModal(new AlbumScreen { Name = "Album" });
        tips = new TipsOverlay { Name = "Tips" };
        scaled.AddChild(tips);
        Toasts = new ToastLayer { Name = "Toasts" };
        scaled.AddChild(Toasts);

        // Above the world's transition fade (layer 50): era card; then the cursor item.
        var eraLayer = new CanvasLayer { Name = "EraCardLayer", Layer = 60 };
        AddChild(eraLayer);
        var eraCard = new EraCardView { Name = "EraCard", Theme = UiTheme.Theme };
        eraLayer.AddChild(eraCard);
        var cursorLayer = new CanvasLayer { Name = "CursorLayer", Layer = 70 };
        AddChild(cursorLayer);
        HoverLabel = new HoverLabel { Name = "HoverLabel" };
        cursorLayer.AddChild(HoverLabel);
        HoverLabel.Init(Hud);
        cursor = new CursorLayer { Name = "Cursor" };
        cursorLayer.AddChild(cursor);

        // Register views and claim panels: the world runtime's placeholders stand down.
        UiBus.Register((ISubtitleView)subtitles);
        UiBus.Register((ITopicMenuView)topics);
        UiBus.Register((IPuzzleView)puzzle);
        UiBus.Register((ICutsceneView)cutscene);
        UiBus.Register((IEraCardView)eraCard);
        UiBus.Register((IHoverView)Hud);
        foreach (var panel in new[] { UiPanel.Inventory, UiPanel.Journal, UiPanel.Map, UiPanel.Pause, UiPanel.Portal, UiPanel.Hud,
                     UiPanel.MainMenu, UiPanel.Hints, UiPanel.Save, UiPanel.Load, UiPanel.Settings })
            UiBus.Claim(panel);

        UiBus.OpenRequested += OnOpenRequested;
        UiBus.Notice += key => Toasts.Show(TextService.Ui(key));
        Hud.PortalPressed += () => OnOpenRequested(UiPanel.Portal);
        UiSettings.Changed += () => appliedScale = -1;
        if (game.IsReady)
        {
            game.ModeChanged += OnModeChanged;
            game.SessionReplaced += OnSessionReplaced;
            game.InventoryChanged += OnInventoryChanged;
            game.ActionCommitted += OnActionCommitted;
            game.Saved += OnSaved;
            game.LoadFailed += (_, error) => Message(TextService.Get(error));
        }

        if (!harness && game.IsReady) Push(mainMenu);
        if (LaunchArgs.Any) AddChild(new UiDebug { Name = "UiDebug" });
    }

    private T AddModal<T>(T screen) where T : ModalScreen
    {
        modalLayer.AddChild(screen);
        screen.Closed += () => Pop(screen);
        return screen;
    }

    /// <inheritdoc />
    public override void _ExitTree()
    {
        UiBus.OpenRequested -= OnOpenRequested;
        if (Instance == this) Instance = null;
    }

    // ------------------------------------------------------------------ modal stack

    /// <summary>Opens a UI-only modal on top.</summary>
    public void Push(ModalScreen screen)
    {
        stack.Remove(screen);
        stack.Add(screen);
        if (screen.GetParent() == modalLayer) modalLayer.MoveChild(screen, -1);
        screen.Open();
        UpdateSuppression();
    }

    /// <summary>Removes a modal from the stack (it hid itself) and refocuses the one below.</summary>
    public void Pop(ModalScreen screen)
    {
        if (!stack.Remove(screen)) return;
        screen.Dismiss();
        if (TopModal is { } top) top.FocusDefault();
        else if (pause.Visible) pause.FocusDefault();
        else if (journal.Visible) journal.FocusDefault();
        else if (map.Visible) map.FocusDefault();
        else if (puzzle.Visible) puzzle.FocusDefault();
        UpdateSuppression();
    }

    private void CloseAllModals()
    {
        foreach (var screen in stack.ToList())
        {
            stack.Remove(screen);
            screen.Dismiss();
        }
        UpdateSuppression();
    }

    private void UpdateSuppression()
    {
        bool full = stack.Count > 0;
        cursor.Suppressed = full;
        Hud.StripWanted = !full || stack.All(s => s is PortalChooser);
    }

    /// <summary>A yes/no confirmation dialog.</summary>
    public void Confirm(string text, string yes, Action onYes, string? no = null)
    {
        var dialog = new ConfirmDialog(text, yes, no ?? Ui.T("ui.common.cancel"), onYes);
        modalLayer.AddChild(dialog);
        dialog.Closed += () => { Pop(dialog); dialog.QueueFree(); };
        Push(dialog);
    }

    /// <summary>A message dialog with one OK button.</summary>
    public void Message(string text, string? ok = null)
    {
        var dialog = new ConfirmDialog(text, ok ?? Ui.T("ui.common.ok"), null, null);
        modalLayer.AddChild(dialog);
        dialog.Closed += () => { Pop(dialog); dialog.QueueFree(); };
        Push(dialog);
    }

    /// <summary>Opens the save (true) or load (false) screen.</summary>
    public void OpenSaveLoad(bool save)
    {
        saveLoad.SaveMode = save;
        Push(saveLoad);
    }

    /// <summary>Opens the settings.</summary>
    public void OpenSettings() => Push(settings);

    /// <summary>Opens the controls help.</summary>
    public void OpenHelp() => Push(help);

    /// <summary>Opens the hint panel (optionally for one quest).</summary>
    public void OpenHints(string? questId = null)
    {
        hints.PreferredQuest = questId;
        Push(hints);
    }

    /// <summary>Opens the credits (rolling after the ending, or browsable from the menu).</summary>
    public void OpenCredits(bool rolling, Action? done = null)
    {
        credits.Rolling = rolling;
        credits.Done = done;
        Push(credits);
    }

    /// <summary>Shows the main menu (from pause: the session stays until new game / load).</summary>
    public void ShowMainMenu()
    {
        CloseAllModals();
        var game = GameRuntime.Instance;
        if (game.State.Mode is GameMode.Pause or GameMode.Journal or GameMode.Map or GameMode.Inventory) game.Update(GameRules.CloseOverlay);
        Push(mainMenu);
    }

    /// <summary>The main menu is open (no game shown yet or returned to the menu).</summary>
    public bool MainMenuOpen => stack.Contains(mainMenu);

    /// <summary>Plays the epilogue shots (epilogue_rules) and the credits; <paramref name="replay"/> from the album.</summary>
    public void PlayEnding(bool replay)
    {
        ending.Replay = replay;
        Push(ending);
    }

    /// <summary>Opens the read-only album of a saved game (main menu).</summary>
    public void OpenAlbum(GameState state)
    {
        album.Source = state;
        Push(album);
    }

    /// <summary>Opens the portal chooser.</summary>
    public void OpenPortal() => OnOpenRequested(UiPanel.Portal);

    // ------------------------------------------------------------------ events

    private void OnOpenRequested(UiPanel panel)
    {
        var game = GameRuntime.Instance;
        switch (panel)
        {
            case UiPanel.Hints:
                if (!HasModal) OpenHints();
                break;
            case UiPanel.Settings:
                OpenSettings();
                break;
            case UiPanel.Save:
                OpenSaveLoad(true);
                break;
            case UiPanel.Load:
                OpenSaveLoad(false);
                break;
            case UiPanel.MainMenu:
                ShowMainMenu();
                break;
            case UiPanel.Portal:
                if (!HasModal && game.State.Mode == GameMode.World && (WorldStage.Instance?.IsSettled ?? false) &&
                    Navigation.PortalTargets(game.Content, game.State).Count > 0)
                    Push(portal);
                break;
        }
    }

    private void OnModeChanged(GameMode mode, GameMode previous)
    {
        if (mode == GameMode.Pause && previous is GameMode.World or GameMode.Inventory && !HasModal) CaptureWorldShot();
        SyncMode();
    }

    private void SyncMode()
    {
        var mode = GameRuntime.Instance.State.Mode;
        inventory.SetOpen(mode == GameMode.Inventory);
        SetShown(journal, mode == GameMode.Journal);
        SetShown(map, mode == GameMode.Map);
        SetShown(pause, mode == GameMode.Pause);
        if (mode != GameMode.Puzzle && puzzle.Visible) puzzle.Close();
        if (mode != GameMode.Pause && portal.Visible) Pop(portal);
    }

    private static void SetShown(ModalScreen screen, bool show)
    {
        if (show && !screen.Visible) screen.Open();
        else if (!show && screen.Visible) screen.Dismiss();
    }

    private void OnSessionReplaced()
    {
        CloseAllModals();
        Toasts.ClearAll();
        var game = GameRuntime.Instance;
        // A save made while the finale's lines or its cutscene play (autosave after F17, quit in CS07)
        // still owes the ending: it plays once that playback is over (docs/MILESTONE2.md, bug M2-03).
        endingPending = IsFinalePlaying(game);
        SyncMode();
        // A brand-new game: the first-start tips (once).
        if (game.State.Done.Length == 0 && !UiSettings.TipsShown && (!LaunchArgs.Any || LaunchArgs.PlayerStart)) tips.Start();
    }

    private static bool IsFinalePlaying(GameRuntime game)
    {
        var unlock = game.Content.FindAction(game.Content.Data.Postgame.Unlock);
        var s = game.State;
        if (unlock is null || !s.IsDone(unlock.Id) || s.ActiveLineId is null) return false;
        bool Finale(string id) => id.StartsWith("action." + unlock.Id + ".", StringComparison.Ordinal) ||
                                  (unlock.Cutscene is { } cs && id.StartsWith("cutscene." + cs + ".", StringComparison.Ordinal));
        return Finale(s.ActiveLineId) || s.PlaybackQueue.Any(Finale);
    }

    private void OnInventoryChanged(IReadOnlyList<string> added, IReadOnlyList<string> removed)
    {
        var content = GameRuntime.Instance.Content;
        foreach (var id in added)
            if (content.FindItem(id) is { } item)
                Toasts.Show(Ui.T("ui.inventory.item_added", ("item", TextService.Get(TextKeys.NameOf(item)))));
    }

    private void OnActionCommitted(ActionDef action)
    {
        var game = GameRuntime.Instance;
        if (action.Objective is not null)
            Toasts.Show(Ui.T("ui.hud.goal_updated"), TextService.Get(TextKeys.ObjectiveOf(action)), 6);
        if (action.Id == game.Content.Data.Postgame.Unlock) endingPending = true;
    }

    private void OnSaved(string slot)
    {
        if (slot == GameRuntime.AutosaveSlot)
        {
            Toasts.ShowAutosave();
            SaveThumbnail(slot, CaptureFrame());
        }
        else if (slot == SaveSlots.Quick && !HasModal) SaveThumbnail(slot, CaptureFrame()); // F5 from the scene
    }

    // ------------------------------------------------------------------ thumbnails

    private void CaptureWorldShot() => worldShot = CaptureFrame();

    /// <summary>A 384x216 snapshot of the last rendered frame (null without a renderer).</summary>
    public Image? CaptureFrame()
    {
        if (DisplayServer.GetName() == "headless") return null;
        var image = GetViewport()?.GetTexture()?.GetImage();
        if (image is null || image.IsEmpty()) return null;
        image.Resize(384, 216, Image.Interpolation.Bilinear);
        return image;
    }

    /// <summary>Writes the slot thumbnail next to the save (user://saves/&lt;slot&gt;.png).</summary>
    public static void SaveThumbnail(string slot, Image? image)
    {
        if (image is null) return;
        DirAccess.MakeDirRecursiveAbsolute(GameRuntime.SaveDirectory);
        image.SavePng($"{GameRuntime.SaveDirectory}/{slot}.png");
    }

    // ------------------------------------------------------------------ frame

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        float s = UiSettings.HudScale;
        var viewport = GetViewportRect().Size;
        if (Math.Abs(s - appliedScale) > 0.001f || scaled.Size != viewport / s)
        {
            appliedScale = s;
            scaled.Scale = new Vector2(s, s);
            scaled.Position = Vector2.Zero;
            scaled.Size = viewport / s;
        }
        if (endingPending)
        {
            var game = GameRuntime.Instance;
            var stage = WorldStage.Instance;
            if (game.State.Mode == GameMode.World && game.State.ActiveLineId is null && stage is { IsSettled: true, IsFadedIn: true } && !HasModal)
            {
                endingPending = false;
                PlayEnding(replay: false);
            }
        }
    }

    /// <inheritdoc />
    public override void _Notification(int what)
    {
        if (what is not ((int)NotificationApplicationFocusOut or (int)NotificationApplicationFocusIn)) return;
        int master = AudioServer.GetBusIndex("Master");
        if (master < 0) return;
        bool mute = what == (int)NotificationApplicationFocusOut && UiSettings.MuteUnfocused;
        AudioServer.SetBusMute(master, mute || UiSettings.Volume[0] <= 0 || LastBell.Game.Diagnostics.QaWindow.Silent);
    }

    // ------------------------------------------------------------------ keyboard focus scope (AT19)

    /// <summary>
    /// The screen that owns the keyboard focus: the top UI-only modal, else the open puzzle, pause, journal or map
    /// screen; null in the world (the bag and the topic menu keep Godot's own focus chain).
    /// </summary>
    private Control? FocusScope => TopModal is { } top ? top
        : puzzle.Visible ? puzzle : pause.Visible ? pause : journal.Visible ? journal : map.Visible ? map : null;

    /// <summary>
    /// Tab / Shift+Tab inside a screen: Godot's focus chain runs through the whole tree, so from the last control of a
    /// modal (hints over a puzzle, save slots over the pause menu) Tab went on into the screen underneath, and Enter
    /// then pressed a button nobody could see (AT19 keyboard pass, 2026-10-06). The chain now wraps inside
    /// <see cref="FocusScope"/>; with no focus at all the first (Shift+Tab: last) control of the scope is taken.
    /// </summary>
    public override void _Input(InputEvent e)
    {
        if (e is not InputEventKey { Pressed: true } key) return;
        bool back = key.IsAction("ui_focus_prev");
        if (!back && !key.IsAction("ui_focus_next")) return;
        if (FocusScope is not { } scope) return;
        var owner = GetViewport().GuiGetFocusOwner();
        if (owner is not null && scope.IsAncestorOf(owner))
        {
            var next = back ? owner.FindPrevValidFocus() : owner.FindNextValidFocus();
            if (next is not null && next != owner && scope.IsAncestorOf(next)) return; // Godot's own step stays inside
        }
        var edge = EdgeFocusable(scope, last: back);
        if (edge is null) return;
        edge.GrabFocus();
        GetViewport().SetInputAsHandled();
    }

    /// <summary>Arrow keys or a deferred focus call that land outside the top screen are brought back into it.</summary>
    private void OnGuiFocusChanged(Control control)
    {
        if (FocusScope is not { } scope || scope.IsAncestorOf(control)) return;
        Callable.From(() =>
        {
            if (FocusScope is not { } now || GetViewport().GuiGetFocusOwner() is not { } owner || now.IsAncestorOf(owner)) return;
            EdgeFocusable(now, last: false)?.GrabFocus();
        }).CallDeferred();
    }

    /// <summary>The first (or last) control under a node that Tab can reach: visible, focus mode All, not a disabled button.</summary>
    private static Control? EdgeFocusable(Node root, bool last)
    {
        var children = root.GetChildren().ToList();
        if (last) children.Reverse();
        foreach (var child in children)
        {
            if (child is not Control { Visible: true } c) continue;
            if (!last && c.FocusMode == FocusModeEnum.All && c is not BaseButton { Disabled: true }) return c;
            if (EdgeFocusable(c, last) is { } inner) return inner;
            if (last && c.FocusMode == FocusModeEnum.All && c is not BaseButton { Disabled: true }) return c;
        }
        return null;
    }

    /// <summary>Keys while a UI-only modal is open: Esc closes the top one, everything else is kept from the world.</summary>
    public override void _ShortcutInput(InputEvent e)
    {
        if (!HasModal) return;
        if (e is not InputEventKey { Pressed: true } key) return;
        var top = TopModal!;
        if (key.IsActionPressed("ui_cancel") || key.IsAction(LastBell.Game.PlayerInput.InputActions.Cancel))
        {
            if (!key.Echo) top.Back();
        }
        else if ((key.IsAction("ui_focus_next") || key.IsAction("ui_focus_prev") || key.IsAction("ui_down") || key.IsAction("ui_up")) &&
                 GetViewport().GuiGetFocusOwner() is null)
        {
            top.FocusDefault();
        }
        else top.OnKey(key);
        GetViewport().SetInputAsHandled();
    }

    /// <summary>Mouse buttons that reach unhandled input while a modal is open never reach the scene.</summary>
    public override void _UnhandledInput(InputEvent e)
    {
        if (HasModal && e is InputEventMouseButton) GetViewport().SetInputAsHandled();
    }
}
