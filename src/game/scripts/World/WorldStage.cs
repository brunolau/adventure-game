using System;
using System.Linq;
using System.Threading.Tasks;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Views;
using LastBell.Game.Hooks;
using LastBell.Game.Runtime;

namespace LastBell.Game.World;

/// <summary>
/// Owns the displayed room: builds it from Core's view, refreshes it after state changes, and runs
/// room transitions (short fade, era card on era change) for exits, special transitions
/// (e.g. G11 → S11), portals, fast travel and loads. While an action's own lines play, the old room
/// stays on screen; the new room appears before its first-entry lines.
/// </summary>
public partial class WorldStage : Node2D
{
    private CanvasLayer overlay = null!;
    private ColorRect fade = null!;
    private Label eraCardTitle = null!;
    private Label eraCardDate = null!;

    /// <summary>The singleton stage.</summary>
    public static WorldStage? Instance { get; private set; }

    /// <summary>The displayed room (null before the first build).</summary>
    public Room? Current { get; private set; }

    /// <summary>True while a fade/transition runs (world input is ignored).</summary>
    public bool Transitioning { get; private set; }

    /// <summary>Visual overrides (loaded once).</summary>
    public ArtOverrides Art { get; private set; } = new();

    /// <summary>Show the dev overlay above painted art.</summary>
    public bool DevOverlay { get; set; }

    /// <summary>True when the displayed room matches the state and no transition runs.</summary>
    public bool IsSettled => !Transitioning && Current is not null && Current.RoomId == GameRuntime.Instance.State.Room;

    /// <summary>True when no fade covers the room.</summary>
    public bool IsFadedIn => fade is not null && fade.Modulate.A <= 0.001f;

    /// <summary>Raised when a room finished its transition and accepts input.</summary>
    public event Action<Room>? RoomReady;

    /// <inheritdoc />
    public override void _Ready()
    {
        Instance = this;
        Art = ArtOverrides.Load();
        overlay = new CanvasLayer { Name = "TransitionOverlay", Layer = 50 };
        AddChild(overlay);
        fade = new ColorRect { Name = "Fade", Color = Colors.Black, MouseFilter = Control.MouseFilterEnum.Ignore };
        fade.SetAnchorsPreset(Control.LayoutPreset.FullRect);
        fade.Modulate = new Color(1, 1, 1, 0);
        overlay.AddChild(fade);
        eraCardTitle = MakeCardLabel(64, new Vector2(0, 430));
        eraCardDate = MakeCardLabel(36, new Vector2(0, 530));
        var game = GameRuntime.Instance;
        game.StateChanged += OnStateChanged;
        game.SessionReplaced += OnSessionReplaced;
    }

    /// <inheritdoc />
    public override void _ExitTree()
    {
        var game = GameRuntime.Instance;
        if (game is null) return;
        game.StateChanged -= OnStateChanged;
        game.SessionReplaced -= OnSessionReplaced;
    }

    private Label MakeCardLabel(int size, Vector2 position)
    {
        var label = new Label
        {
            HorizontalAlignment = HorizontalAlignment.Center,
            Position = position,
            Size = new Vector2(1920, size * 1.5f),
            MouseFilter = Control.MouseFilterEnum.Ignore,
            Modulate = new Color(1, 1, 1, 0),
        };
        label.AddThemeFontSizeOverride("font_size", size);
        label.AddThemeColorOverride("font_color", new Color(0.96f, 0.92f, 0.82f));
        overlay.AddChild(label);
        return label;
    }

    /// <summary>
    /// True when a playback line may be shown now: never during a transition, and first-entry lines
    /// only once their room is on screen.
    /// </summary>
    public bool CanPresent(PlaybackLine line)
    {
        if (Transitioning || Current is null) return false;
        if (line.Source == LineSource.FirstEntry) return line.SourceId == Current.RoomId;
        return true;
    }

    /// <summary>Builds the current state's room immediately (start, load, debug jump), fading in from black.</summary>
    public void ShowCurrentRoomNow()
    {
        var state = GameRuntime.Instance.State;
        BuildRoom(state.Room, null);
        _ = FadeIn();
    }

    /// <summary>Walks through an exit: fade out, Core travel (gate re-checked), build, era card, fade in.</summary>
    public async void TravelThrough(string exitId)
    {
        if (Transitioning) return;
        var game = GameRuntime.Instance;
        Transitioning = true;
        try
        {
            await FadeOut();
            var before = game.State;
            game.Update(s => Navigation.Travel(game.Content, s, exitId));
            if (game.State.Room == before.Room)
            {
                // Gate closed after all: nothing happens (the resolver said Travel on arrival).
                await FadeIn();
                return;
            }
            await EnterDisplayedRoom(before.Room, before.Era);
        }
        finally
        {
            Transitioning = false;
            AfterArrival();
        }
    }

    /// <summary>Runs a transition for a state whose room differs from the displayed one (special transitions, portals, fast travel).</summary>
    public async void FollowStateRoom()
    {
        if (Transitioning || Current is null) return;
        Transitioning = true;
        string fromRoom = Current.RoomId;
        int fromEra = Current.View.Era;
        try
        {
            await FadeOut();
            await EnterDisplayedRoom(fromRoom, fromEra);
        }
        finally
        {
            Transitioning = false;
            AfterArrival();
        }
    }

    private async Task EnterDisplayedRoom(string fromRoom, int fromEra)
    {
        var game = GameRuntime.Instance;
        BuildRoom(game.State.Room, fromRoom);
        if (game.State.Era != fromEra && game.Content.FindEra(game.State.Era) is { } era) await ShowEraCard(era);
        await FadeIn();
    }

    private void AfterArrival()
    {
        if (Current is null) return;
        // The state may have moved on during the fade (e.g. the next special transition).
        var game = GameRuntime.Instance;
        if (Current.RoomId != game.State.Room)
        {
            CallDeferred(MethodName.FollowStateRoomDeferred);
            return;
        }
        Current.Refresh(game.Content, ViewBuilder.Room(game.Content, game.State));
        WorldHooks.RaiseRoomReady(Current);
        RoomReady?.Invoke(Current);
        game.Autosave();
    }

    private void FollowStateRoomDeferred() => FollowStateRoom();

    private void BuildRoom(string roomId, string? arrivedFrom)
    {
        var game = GameRuntime.Instance;
        if (Current is not null)
        {
            WorldHooks.RaiseRoomLeaving(Current);
            RemoveChild(Current);
            Current.QueueFree();
            Current = null;
        }
        var view = ViewBuilder.Room(game.Content, game.State, roomId);
        var room = Room.Instantiate();
        room.DevOverlayVisible = DevOverlay;
        AddChild(room);
        MoveChild(room, 0);
        room.Build(game.Content, view, Art, arrivedFrom);
        Current = room;
        WorldHooks.RaiseRoomBuilt(room);
    }

    private void OnSessionReplaced()
    {
        Transitioning = false;
        BuildRoom(GameRuntime.Instance.State.Room, null);
        fade.Modulate = new Color(1, 1, 1, 1);
        _ = FadeIn();
        if (Current is not null)
        {
            WorldHooks.RaiseRoomReady(Current);
            RoomReady?.Invoke(Current);
        }
    }

    private void OnStateChanged(GameState old, GameState next)
    {
        if (Current is null || Transitioning) return;
        if (next.Room != Current.RoomId)
        {
            // Keep the old room while the action's own lines or a cutscene play; switch before the
            // new room's first-entry lines (or when playback is over).
            var line = Playback.Current(GameRuntime.Instance.Content, next);
            if (line is null || line.Source == LineSource.FirstEntry) FollowStateRoom();
            return;
        }
        var view = ViewBuilder.Room(GameRuntime.Instance.Content, next);
        Current.Refresh(GameRuntime.Instance.Content, view);
    }

    /// <summary>Called by the dialogue presenter when a line could not be shown yet (room pending).</summary>
    public void PokePendingTransition()
    {
        if (Current is not null && !Transitioning && Current.RoomId != GameRuntime.Instance.State.Room) FollowStateRoom();
    }

    // ------------------------------------------------------------------ fades and era card

    private float FadeSeconds => PresentationSettings.ReducedMotion ? 0.2f : PresentationSettings.RoomFadeSeconds;

    private async Task FadeOut()
    {
        fade.MouseFilter = Control.MouseFilterEnum.Stop;
        await Tween(fade, 1f, FadeSeconds);
    }

    private async Task FadeIn()
    {
        await Tween(fade, 0f, FadeSeconds);
        fade.MouseFilter = Control.MouseFilterEnum.Ignore;
    }

    private async Task Tween(CanvasItem item, float alpha, float seconds)
    {
        var tween = CreateTween();
        tween.TweenProperty(item, "modulate:a", alpha, Math.Max(0.01f, seconds));
        await ToSignal(tween, Godot.Tween.SignalName.Finished);
    }

    private async Task ShowEraCard(EraDef era)
    {
        var card = LastBell.Core.Text.TextKeys.CardOf(era);
        var date = LastBell.Core.Text.TextKeys.DateOf(era);
        if (UiBus.EraCard is { } custom)
        {
            var done = new TaskCompletionSource();
            custom.Show(era, card, date, () => done.TrySetResult());
            await done.Task;
            return;
        }
        eraCardTitle.Text = TextService.Get(card);
        eraCardDate.Text = TextService.Get(date);
        await Task.WhenAll(Tween(eraCardTitle, 1f, 0.4f), Tween(eraCardDate, 1f, 0.4f));
        await ToSignal(GetTree().CreateTimer(PresentationSettings.ReducedMotion ? 0.8 : 1.6), SceneTreeTimer.SignalName.Timeout);
        await Task.WhenAll(Tween(eraCardTitle, 0f, 0.3f), Tween(eraCardDate, 0f, 0.3f));
    }
}
