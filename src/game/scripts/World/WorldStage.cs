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
/// Transport rides (travel overlay: exits with travel <c>bus</c> / <c>tram</c>, and map fast travel into
/// another region) show a destination card over the fade (region name and the means of transport) with the
/// ride sound; a first ride plays its first-ride lines in the room being left before the fade. Reduced motion:
/// the same fade and card, shorter hold, nothing moves.
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

    /// <summary>Travel styles that show the transport card (and play their ride sound <c>travel_&lt;style&gt;</c>).</summary>
    public static readonly string[] TransportStyles = { "bus", "tram" };

    /// <summary>The transport ride waiting for its first-ride lines to finish (exit id, style), or null.</summary>
    private (string ExitId, string Style)? pendingRide;

    /// <summary>
    /// Set by the map right before a fast travel (<see cref="MarkFastTravel"/>): the next room change gets the transport
    /// card of the first link that leaves the region (bus, tram, cable car), also for the cable cars and the 1995
    /// map-transition links, instead of a plain fade (owner 2026-10-06, DECISIONS control change 8).
    /// </summary>
    private bool pendingFastTravel;

    /// <summary>
    /// What the 1995 cross-region links (game.json travel <c>map_transition</c>) are in the painted scenes: the tram
    /// from Dúbravka over Karlova Ves to Kamenné námestie and on to Ružinov, the bus from Kamenné námestie to Petržalka
    /// (exit reasons in data/blocking/S11, S19, S21). Only the fast-travel card uses it; the exits keep their fade.
    /// </summary>
    private static readonly System.Collections.Generic.Dictionary<string, string> RideOfMapTransition = new(StringComparer.Ordinal)
    {
        ["S11|S19"] = "tram", ["S19|S21"] = "tram", ["S21|S25"] = "tram", ["S21|S28"] = "bus",
    };

    /// <summary>Called by the map right before <c>Navigation.FastTravel</c> (true: the next room change is a fast travel),
    /// and with false when that travel did not change the room.</summary>
    public void MarkFastTravel(bool on) => pendingFastTravel = on;

    /// <summary>
    /// The card style of a fast travel from <paramref name="from"/> to <paramref name="to"/> (same era): the first link of
    /// the shortest open route that leaves the start's region, as a style with a card (<see cref="TransportStyles"/>; cable
    /// cars and the Funitel show the cable car card <c>cable_A6</c>), or null inside one region. The map uses it for its
    /// "Autobusom" / "Električkou" tags too.
    /// </summary>
    public static string? FastTravelCardStyle(GameContent content, GameState state, string from, string to)
    {
        if (content.FindRoom(from) is not { } a || content.FindRoom(to) is not { } b || a.Era != b.Era ||
            ReferenceEquals(content.RegionOf(from), content.RegionOf(to))) return null;
        var route = Navigation.FindRoute(content, state with { Room = from }, to);
        var region = content.RegionOf(from);
        foreach (var step in route ?? Array.Empty<RouteStep>())
        {
            if (step.Kind != RouteStepKind.Exit || ReferenceEquals(content.RegionOf(step.To), region)) continue;
            string style = content.FindExit(step.ExitId ?? "")?.Exit.Travel ?? "";
            string pair = string.CompareOrdinal(step.From, step.To) < 0 ? step.From + "|" + step.To : step.To + "|" + step.From;
            if (style == "map_transition" && RideOfMapTransition.TryGetValue(pair, out var ride)) return ride;
            if (style is "cable_A6" or "board_funitel" or "arrive_funitel") return "cable_A6";
            return Array.IndexOf(TransportStyles, style) >= 0 ? style : null;
        }
        return null;
    }

    /// <summary>Text of the last transport card shown (QA: build/screens/travel), or empty.</summary>
    public string LastTransportCard { get; private set; } = "";

    /// <summary>Milliseconds the last <see cref="BuildRoom"/> took (synchronous: texture loads, sprites, ambient; perf QA).</summary>
    public double LastBuildMs { get; private set; }

    /// <summary>Number of rooms built since start (perf QA).</summary>
    public int RoomsBuilt { get; private set; }

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
        AddChild(new RoomPreloader { Name = "RoomPreloader" });
        AddChild(new GuestStage { Name = "GuestStage" });
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
        // First-ride lines: in the room being left (before the ride), or in the destination after a load mid-line.
        if (line.Source == LineSource.Travel)
            return GameRuntime.Instance.Content.FindExit(line.SourceId) is not { } exit || Current.RoomId == exit.Room.Id || Current.RoomId == exit.Exit.To;
        return GuestStage.Instance?.MayPresent(line) ?? true; // a guest speaker walks in first (ISSUES PT-S18)
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
        var exitDef = game.Content.FindExit(exitId)?.Exit;
        if (exitDef is not null && Array.IndexOf(TransportStyles, exitDef.Travel) >= 0)
        {
            // A ride: Core travel first, so a first ride's lines play here, in the room being left; the fade, the
            // card and the new room follow when they are done (OnStateChanged -> FollowStateRoom).
            var before = game.State;
            game.Update(s => Navigation.Travel(game.Content, s, exitId));
            if (game.State.Room == before.Room) return; // gate closed after all: nothing happens
            pendingRide = (exitId, exitDef.Travel);
            var line = Playback.Current(game.Content, game.State);
            if (line is null || line.Source != LineSource.Travel) FollowStateRoom();
            return;
        }
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
            await EnterDisplayedRoom(before.Room, before.Era, before.Room);
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
        var game = GameRuntime.Instance;
        // A ride through a transport exit, or a map fast travel into another region (one click to any visited room).
        bool fastTravel = pendingFastTravel;
        pendingFastTravel = false;
        string? transport = pendingRide is { } ride && game.Content.FindExit(ride.ExitId)?.Exit.To == game.State.Room ? ride.Style
            : fastTravel ? FastTravelCardStyle(game.Content, game.State, fromRoom, game.State.Room)
            : Navigation.TransportBetween(game.Content, game.State, fromRoom, game.State.Room);
        // Story cable rides (J02-J04) keep their own staging; a fast travel shows the cable car card.
        if (transport is not null && Array.IndexOf(TransportStyles, transport) < 0 && !(fastTravel && transport == "cable_A6")) transport = null;
        // Through a ride's exit the hero arrives at the matching return exit; map fast travel, portals and special
        // transitions use the room spawn (docs/navigation/EXITS.md).
        string? arrivedVia = pendingRide is { } taken && game.Content.FindExit(taken.ExitId)?.Exit.To == game.State.Room ? fromRoom : null;
        pendingRide = null;
        try
        {
            await FadeOut();
            if (transport is not null && game.Content.FindRoom(game.State.Room) is { Era: var era } && era == fromEra)
            {
                BuildRoom(game.State.Room, arrivedVia);
                await ShowTransportCard(transport, game.State.Room);
                await FadeIn();
            }
            else await EnterDisplayedRoom(fromRoom, fromEra, arrivedVia);
        }
        finally
        {
            Transitioning = false;
            AfterArrival();
        }
    }

    /// <param name="arrivedVia">The room left through an exit (the hero comes in at the exit back there), or null (spawn).</param>
    private async Task EnterDisplayedRoom(string fromRoom, int fromEra, string? arrivedVia)
    {
        var game = GameRuntime.Instance;
        BuildRoom(game.State.Room, arrivedVia);
        if (game.State.Era != fromEra && game.Content.FindEra(game.State.Era) is { } era) await ShowEraCard(era);
        await FadeIn();
    }

    private void AfterArrival()
    {
        if (Current is null) return;
        Current.FinishArrival(); // the arrival step never outlasts the transition
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
        long started = System.Diagnostics.Stopwatch.GetTimestamp();
        RoomScopedCaches.NextRoom();
        var view = ViewBuilder.Room(game.Content, game.State, roomId);
        var room = Room.Instantiate();
        room.DevOverlayVisible = DevOverlay;
        AddChild(room);
        MoveChild(room, 0);
        room.Build(game.Content, view, Art, arrivedFrom);
        Current = room;
        WorldHooks.RaiseRoomBuilt(room);
        RoomScopedCaches.Trim(); // sheets of rooms left two rooms ago (the old room is already out of the tree)
        LastBuildMs = System.Diagnostics.Stopwatch.GetElapsedTime(started).TotalMilliseconds;
        RoomsBuilt++;
        if (RoomsBuilt == 1) GD.Print($"LastBell: first room {roomId} built {Time.GetTicksMsec()} ms after engine start ({LastBuildMs:F0} ms)");
        else if (OS.IsStdOutVerbose()) GD.Print($"LastBell: room {roomId} built in {LastBuildMs:F1} ms");
        RoomPreloader.Instance?.Prefetch(room);
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
            else RoomPreloader.Instance?.PrefetchRooms(new[] { next.Room }); // decoded while the lines / cutscene play
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

    /// <summary>
    /// The destination card of a ride: the region name, and "Autobusom · Dúbravská zastávka v roku 2020" (<c>ui.travel.card</c> with
    /// <c>ui.travel.&lt;style&gt;</c>) under it, over the black fade, with the ride sound. Reduced motion: shorter.
    /// </summary>
    private async Task ShowTransportCard(string style, string roomId)
    {
        var content = GameRuntime.Instance.Content;
        var region = TextService.Get(LastBell.Core.Text.TextKeys.NameOf(content.RegionOf(roomId)));
        string means = TextService.Get(new LastBell.Core.Text.TextRef("ui.travel." + style, style));
        eraCardTitle.Text = region;
        eraCardDate.Text = TextService.Ui("ui.travel.card", ("transport", means), ("place", TextService.Get(LastBell.Core.Text.TextKeys.NameOf(content.GetRoom(roomId)))));
        LastTransportCard = eraCardTitle.Text + " | " + eraCardDate.Text;
        LastBell.Game.Audio.AudioService.PlayEvent("travel_" + style);
        await Task.WhenAll(Tween(eraCardTitle, 1f, 0.35f), Tween(eraCardDate, 1f, 0.35f));
        await ToSignal(GetTree().CreateTimer(PresentationSettings.ReducedMotion ? 0.7 : 1.4), SceneTreeTimer.SignalName.Timeout);
        await Task.WhenAll(Tween(eraCardTitle, 0f, 0.3f), Tween(eraCardDate, 0f, 0.3f));
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
