using System;
using System.Collections.Generic;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.Text;
using LastBell.Core.Views;

namespace LastBell.Game.Hooks;

/// <summary>UI panels the world runtime can request or that the UI agent can claim.</summary>
public enum UiPanel
{
    /// <summary>Inventory drawer (Core mode Inventory).</summary>
    Inventory,
    /// <summary>Journal (Core mode Journal).</summary>
    Journal,
    /// <summary>Map (Core mode Map).</summary>
    Map,
    /// <summary>Hint panel (no Core mode; request only).</summary>
    Hints,
    /// <summary>Save screen.</summary>
    Save,
    /// <summary>Load screen.</summary>
    Load,
    /// <summary>Settings screen.</summary>
    Settings,
    /// <summary>Pause menu (Core mode Pause).</summary>
    Pause,
    /// <summary>Puzzle modal (Core mode Puzzle).</summary>
    Puzzle,
    /// <summary>Cutscene framing (Core mode Cutscene).</summary>
    Cutscene,
    /// <summary>Era title card on era change.</summary>
    EraCard,
    /// <summary>Dialogue topic menu.</summary>
    TopicMenu,
    /// <summary>Subtitles and look bubbles.</summary>
    Subtitles,
    /// <summary>Hover text near the cursor.</summary>
    Hover,
    /// <summary>The always-visible HUD buttons (and notices).</summary>
    Hud,
    /// <summary>Chronometer era chooser at anchor nodes (Core portal targets).</summary>
    Portal,
    /// <summary>Main menu: when claimed, Main does not auto-start a new game; the menu calls GameRuntime.NewGame / Load.</summary>
    MainMenu,
}

/// <summary>Hover text payload (from Core's shared resolver; never computed by the UI).</summary>
/// <param name="Info">Core hover info: Name, ActionLabel (non-empty with a selected item only for an executable rule) and the resolution.</param>
/// <param name="ScreenPosition">Pointer or focus position in canvas px.</param>
/// <param name="ShowAction">True when the action sentence should be shown (a selected item is on the cursor).</param>
/// <param name="FromKeyboard">True when it comes from keyboard focus (Tab): the label sits at the target, not at the cursor.</param>
/// <param name="FromInventory">True for an inventory slot (the drawer shows it in its own hover line, not at the cursor).</param>
public sealed record HoverPayload(HoverInfo Info, Vector2 ScreenPosition, bool ShowAction, bool FromKeyboard, bool FromInventory = false);

/// <summary>A line of dialogue / cutscene / first entry ready to show.</summary>
/// <param name="Line">Core playback line.</param>
/// <param name="Speaker">Translated speaker name.</param>
/// <param name="Text">Translated text.</param>
/// <param name="SpeakerAnchor">Canvas point above the speaking actor's head, or null when the speaker is not on screen.</param>
public sealed record SubtitleLine(PlaybackLine Line, string Speaker, string Text, Vector2? SpeakerAnchor);

/// <summary>A non-blocking look/bark text over an actor (no Core mode change).</summary>
/// <param name="Text">Translated text.</param>
/// <param name="SpeakerId">Who says it (normally the hero).</param>
/// <param name="Anchor">Canvas point above the head.</param>
/// <param name="Seconds">Display time.</param>
public sealed record BarkLine(string Text, string SpeakerId, Vector2 Anchor, float Seconds);

/// <summary>Request to show a dialogue topic menu.</summary>
/// <param name="CharacterId">Character spoken to.</param>
/// <param name="HotspotId">NPC hotspot.</param>
/// <param name="Topics">Topics from Core (story actions first, then ambient topics).</param>
/// <param name="Choose">Call with the chosen option.</param>
/// <param name="Close">Call to leave the conversation.</param>
public sealed record TopicMenuRequest(string CharacterId, string HotspotId, IReadOnlyList<TopicOption> Topics, Action<TopicOption> Choose, Action Close);

/// <summary>Subtitle renderer (default: Presentation/DefaultSubtitleView). Logic and timing stay in the DialoguePresenter.</summary>
public interface ISubtitleView
{
    /// <summary>Show a new line (fully hidden text; reveal follows).</summary>
    void ShowLine(SubtitleLine line);

    /// <summary>Typewriter progress: number of visible characters (-1 = all).</summary>
    void SetReveal(int visibleCharacters);

    /// <summary>Hide the current line.</summary>
    void HideLine();

    /// <summary>Show a look/bark bubble (replaces the previous one).</summary>
    void ShowBark(BarkLine bark);

    /// <summary>Hide the bark bubble.</summary>
    void HideBark();
}

/// <summary>Dialogue topic menu.</summary>
public interface ITopicMenuView
{
    /// <summary>Open the menu (keyboard focusable).</summary>
    void Open(TopicMenuRequest request);

    /// <summary>Close it.</summary>
    void Close();
}

/// <summary>Puzzle modal (P01–P05). Use GameRuntime.SubmitPuzzle / ClosePuzzle and Core Puzzles.* for drafts.</summary>
public interface IPuzzleView
{
    /// <summary>Open the modal for a puzzle action.</summary>
    void Open(string actionId, PuzzleDef puzzle);

    /// <summary>Close it (solved, closed or state replaced).</summary>
    void Close();
}

/// <summary>Cutscene framing (letterbox, shot art). Lines are shown by the subtitle view.</summary>
public interface ICutsceneView
{
    /// <summary>A cutscene started.</summary>
    void Begin(CutsceneDef cutscene);

    /// <summary>A beat started (index into beats).</summary>
    void Beat(CutsceneDef cutscene, int beatIndex);

    /// <summary>The cutscene ended or was skipped.</summary>
    void End(CutsceneDef cutscene);
}

/// <summary>Era title card shown during a room transition into another era.</summary>
public interface IEraCardView
{
    /// <summary>Show the card; call <paramref name="done"/> when it has finished (the transition waits).</summary>
    void Show(EraDef era, TextRef card, TextRef date, Action done);
}

/// <summary>Hover text near the cursor or keyboard focus.</summary>
public interface IHoverView
{
    /// <summary>Show/update.</summary>
    void ShowHover(HoverPayload payload);

    /// <summary>Hide.</summary>
    void HideHover();
}

/// <summary>
/// UI registry and event bus between the world runtime and the UI agent (scripts/UI/**,
/// scenes/ui/**). The UI registers implementations or claims panels; every unclaimed panel uses a
/// temporary placeholder from Presentation/Placeholders. UI code reads state from
/// GameRuntime.Instance (events StateChanged, ModeChanged, InventoryChanged ...) and sends player
/// input to the world through <see cref="LastBell.Game.PlayerInput.WorldInput"/>.
/// </summary>
public static class UiBus
{
    private static readonly HashSet<UiPanel> Claimed = new();

    /// <summary>Custom subtitle view, or null for the default.</summary>
    public static ISubtitleView? Subtitles { get; private set; }

    /// <summary>Custom topic menu, or null for the placeholder.</summary>
    public static ITopicMenuView? TopicMenu { get; private set; }

    /// <summary>Custom puzzle modal, or null for the placeholder.</summary>
    public static IPuzzleView? Puzzle { get; private set; }

    /// <summary>Custom cutscene framing, or null for the placeholder.</summary>
    public static ICutsceneView? Cutscene { get; private set; }

    /// <summary>Custom era card, or null for the placeholder fade card.</summary>
    public static IEraCardView? EraCard { get; private set; }

    /// <summary>Custom hover view, or null for the placeholder.</summary>
    public static IHoverView? Hover { get; private set; }

    /// <summary>Raised when the world asks for a panel (keys J/M/H, placeholder pause buttons ...).</summary>
    public static event Action<UiPanel>? OpenRequested;

    /// <summary>Raised when a panel was claimed or a view registered (placeholders hide themselves).</summary>
    public static event Action<UiPanel>? PanelClaimed;

    /// <summary>Raised for short system notices (ui key, e.g. ui.system.autosaved).</summary>
    public static event Action<string>? Notice;

    /// <summary>Claims a panel: the placeholder for it is no longer shown.</summary>
    public static void Claim(UiPanel panel)
    {
        if (Claimed.Add(panel)) PanelClaimed?.Invoke(panel);
    }

    /// <summary>True when the UI agent provides the panel.</summary>
    public static bool IsClaimed(UiPanel panel) => Claimed.Contains(panel);

    /// <summary>Registers the subtitle view (claims Subtitles).</summary>
    public static void Register(ISubtitleView view) { Subtitles = view; Claim(UiPanel.Subtitles); }

    /// <summary>Registers the topic menu (claims TopicMenu).</summary>
    public static void Register(ITopicMenuView view) { TopicMenu = view; Claim(UiPanel.TopicMenu); }

    /// <summary>Registers the puzzle modal (claims Puzzle).</summary>
    public static void Register(IPuzzleView view) { Puzzle = view; Claim(UiPanel.Puzzle); }

    /// <summary>Registers the cutscene framing (claims Cutscene).</summary>
    public static void Register(ICutsceneView view) { Cutscene = view; Claim(UiPanel.Cutscene); }

    /// <summary>Registers the era card (claims EraCard).</summary>
    public static void Register(IEraCardView view) { EraCard = view; Claim(UiPanel.EraCard); }

    /// <summary>Registers the hover view (claims Hover).</summary>
    public static void Register(IHoverView view) { Hover = view; Claim(UiPanel.Hover); }

    /// <summary>Asks the UI to open a panel.</summary>
    public static void RequestOpen(UiPanel panel) => OpenRequested?.Invoke(panel);

    /// <summary>Posts a short notice (ui key).</summary>
    public static void PostNotice(string uiKey) => Notice?.Invoke(uiKey);
}
