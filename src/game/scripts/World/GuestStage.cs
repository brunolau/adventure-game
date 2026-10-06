using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Game.Presentation;
using LastBell.Game.Runtime;

namespace LastBell.Game.World;

/// <summary>How a speaker who is not in the room is shown while one of its lines plays.</summary>
public enum RemoteSpeakerKind
{
    /// <summary>A telephone call (Mira 2020 outside her window room S06).</summary>
    Phone,
    /// <summary>A recording played from a tape or a message (Lea's message, ten-year-old Adam on the cassette).</summary>
    Recording,
    /// <summary>A voice over the service channel (Nina in the Atlas rooms).</summary>
    Radio,
    /// <summary>Text spoken by a device (SYSTEM).</summary>
    Device,
}

/// <summary>Where a remote speaker's indicator sits: beside the hero's head, or at the action's target object.</summary>
public enum RemoteSpeakerAnchor
{
    /// <summary>Beside the hero's head (he holds the phone).</summary>
    Hero,
    /// <summary>Above the action's target (the device, the port, the terminal); the hero when the target is a person.</summary>
    Target,
}

/// <summary>One entry of <c>res://data/staging/remote_speakers.json</c>.</summary>
/// <param name="Kind">Indicator kind.</param>
/// <param name="Anchor">Indicator position rule.</param>
public sealed record RemoteSpeaker(RemoteSpeakerKind Kind, RemoteSpeakerAnchor Anchor);

/// <summary>
/// Staging of speakers who are not in the room (game.json <c>actions[].staging.rule</c>, DECISIONS "Guest speakers walk
/// in briefly", ISSUES PT-S18). Presentation only: Core plays the same lines in the same order; this node only decides
/// who is seen saying them.
/// <list type="bullet">
/// <item>Guests (data/blocking/&lt;room&gt;.json <c>guests.&lt;action&gt;</c>): when the current line belongs to such an
/// action, a temporary actor appears at the nearest exit, fades in and walks to its stand point; that guest's lines wait
/// until it has arrived (<see cref="MayPresent"/>, at most <see cref="MaxWaitSeconds"/>; a click hurries it), and when the
/// action's lines are over it walks back out and is removed. A permanent NPC of the room is never moved: a character
/// that already stands in the room speaks from where it is.</item>
/// <item>Remote speakers (<c>res://data/staging/remote_speakers.json</c>): telephone, recording, service channel and
/// device voices get a <see cref="SpeakerIndicator"/> instead of a body, beside the hero or above the target object; the
/// subtitle's name tag sits above it.</item>
/// </list>
/// A load in the middle of such lines restages the guests (they walk in again); nothing is saved.
/// </summary>
public partial class GuestStage : Node
{
    /// <summary>Hotspot id prefix of guest actors (ActorContext.HotspotId; not a game.json hotspot).</summary>
    public const string HotspotPrefix = "guest:";

    /// <summary>Data file of the remote speakers.</summary>
    public const string RemoteSpeakersPath = "res://data/staging/remote_speakers.json";

    /// <summary>Longest wait for a walking guest before its line is shown anyway (it is put at its stand point).</summary>
    public const float MaxWaitSeconds = 6f;

    private const float FadeSeconds = 0.35f;

    private sealed class Guest
    {
        public required BlockingGuest Def { get; init; }
        public Actor? Actor { get; set; }
        public float Delay { get; set; }
        public bool Arrived { get; set; }
        public bool Leaving { get; set; }
        public float Fade { get; set; }
    }

    private sealed class Scene
    {
        public required Room Room { get; init; }
        public required string ActionId { get; init; }
        public required List<Guest> Guests { get; init; }
        public float Elapsed { get; set; }
        public bool Dismissed { get; set; }
    }

    private static Dictionary<string, RemoteSpeaker>? remote;
    private Scene? scene;
    private string? stagedKey;
    private SpeakerIndicator? indicator;
    private string? indicatorLine;

    /// <summary>The singleton (created by <see cref="WorldStage"/>).</summary>
    public static GuestStage? Instance { get; private set; }

    /// <summary>Character ids of the guests in the room now (QA).</summary>
    public IReadOnlyList<string> GuestsOnStage =>
        scene?.Guests.Where(g => g.Actor is not null && IsInstanceValid(g.Actor)).Select(g => g.Def.CharacterId).ToList() ?? new List<string>();

    /// <summary>The remote speaker indicator now on screen, or null (QA).</summary>
    public SpeakerIndicator? Indicator => indicator is not null && IsInstanceValid(indicator) && indicator.Visible ? indicator : null;

    /// <inheritdoc />
    public override void _Ready()
    {
        Instance = this;
        GameRuntime.Instance.SessionReplaced += () => { scene = null; stagedKey = null; indicatorLine = null; };
    }

    /// <summary>The remote speaker table (data file), loaded once.</summary>
    public static IReadOnlyDictionary<string, RemoteSpeaker> RemoteSpeakers
    {
        get
        {
            if (remote is not null) return remote;
            remote = new Dictionary<string, RemoteSpeaker>(StringComparer.Ordinal);
            if (!Godot.FileAccess.FileExists(RemoteSpeakersPath)) return remote;
            try
            {
                if (JsonNode.Parse(Godot.FileAccess.GetFileAsString(RemoteSpeakersPath))?["speakers"] is JsonObject speakers)
                    foreach (var (id, node) in speakers)
                    {
                        if (node is not JsonObject o) continue;
                        var kind = Enum.TryParse<RemoteSpeakerKind>(o["kind"]?.GetValue<string>(), true, out var k) ? k : RemoteSpeakerKind.Device;
                        var at = string.Equals(o["at"]?.GetValue<string>(), "hero", StringComparison.OrdinalIgnoreCase) ? RemoteSpeakerAnchor.Hero : RemoteSpeakerAnchor.Target;
                        remote[id] = new RemoteSpeaker(kind, at);
                    }
            }
            catch (Exception ex) when (ex is System.Text.Json.JsonException or InvalidOperationException)
            {
                GD.PushWarning($"{RemoteSpeakersPath}: ignored ({ex.Message})");
            }
            return remote;
        }
    }

    // ------------------------------------------------------------------ guests

    /// <summary>
    /// False while the line's speaker is a guest still walking in (the dialogue presenter waits; Core's line cursor does
    /// not move). Starts the guests of the line's action when they are not on stage yet.
    /// </summary>
    public bool MayPresent(PlaybackLine line)
    {
        var room = WorldStage.Instance?.Current;
        if (room is null || line.Source != LineSource.Action) return true;
        EnsureScene(room, line.SourceId);
        if (scene is null || scene.ActionId != line.SourceId) return true;
        var guest = scene.Guests.FirstOrDefault(g => g.Def.CharacterId == line.SpeakerId);
        if (guest is null || guest.Arrived || guest.Leaving) return true;
        if (scene.Elapsed >= MaxWaitSeconds) { Hurry(); return true; }
        return false;
    }

    /// <summary>Puts every guest that is still walking in at its stand point now (a click while the room waits for it).</summary>
    public bool Hurry()
    {
        if (scene is null) return false;
        bool any = false;
        foreach (var g in scene.Guests.Where(g => !g.Arrived && !g.Leaving))
        {
            if (g.Actor is null || !IsInstanceValid(g.Actor)) Spawn(scene, g);
            if (g.Actor is null) continue;
            if (!g.Actor.FinishWalk()) g.Actor.Place(g.Def.Stand);
            g.Fade = FadeSeconds;
            g.Actor.Modulate = Colors.White;
            Arrive(scene, g);
            any = true;
        }
        return any;
    }

    private void EnsureScene(Room room, string actionId)
    {
        string key = room.GetInstanceId() + "/" + actionId;
        if (scene is not null && scene.Room == room && scene.ActionId == actionId) return;
        if (stagedKey == key) return; // this action's guests already came and went in this room build
        if (room.Blocking?.Guests.TryGetValue(actionId, out var defs) != true || defs is null) return;
        if (scene is not null) Dismiss(scene);
        stagedKey = key;
        var guests = new List<Guest>();
        foreach (var def in defs)
        {
            // A character that already stands in the room as a permanent NPC speaks from there: never moved or doubled.
            if (room.FindNpc(def.CharacterId) is not null) continue;
            guests.Add(new Guest { Def = def, Delay = PresentationSettings.ReducedMotion ? 0 : def.Delay });
        }
        scene = new Scene { Room = room, ActionId = actionId, Guests = guests };
    }

    private void Spawn(Scene s, Guest g)
    {
        var room = s.Room;
        bool still = PresentationSettings.ReducedMotion;
        var start = still ? g.Def.Stand : g.Def.Enter;
        var actor = room.AddGuest(g.Def.CharacterId, start);
        actor.Modulate = new Color(1, 1, 1, 0);
        g.Actor = actor;
        g.Fade = 0;
        if (still) { Arrive(s, g); return; }
        var from = room.Walk.Clamp(start);
        var path = room.Walk.FindPath(from, room.Walk.Clamp(g.Def.Stand)) ?? new List<Vector2> { room.Walk.Clamp(g.Def.Stand) };
        if (from.DistanceTo(start) > 1f) path.Insert(0, from);
        actor.WalkPath(path, () => Arrive(s, g));
    }

    private void Arrive(Scene s, Guest g)
    {
        if (g.Arrived || g.Actor is null) return;
        g.Arrived = true;
        var hero = s.Room.Hero;
        if (g.Def.Facing is "left" or "right") g.Actor.FaceTowards(g.Actor.Feet + new Vector2(g.Def.Facing == "left" ? -10 : 10, 0));
        else g.Actor.FaceTowards(hero.Feet);
        if (!hero.IsWalking) hero.FaceTowards(g.Actor.Feet);
    }

    private void Dismiss(Scene s)
    {
        s.Dismissed = true;
        foreach (var g in s.Guests)
        {
            if (g.Actor is null || !IsInstanceValid(g.Actor) || g.Leaving) continue;
            g.Leaving = true;
            g.Actor.SetTalking(false);
            if (PresentationSettings.ReducedMotion) continue; // fades out where it stands
            var room = s.Room;
            var path = room.Walk.FindPath(room.Walk.Clamp(g.Actor.Feet), room.Walk.Clamp(g.Def.Enter)) ?? new List<Vector2>();
            if (room.Walk.Clamp(g.Def.Enter).DistanceTo(g.Def.Enter) > 1f) path.Add(g.Def.Enter);
            g.Actor.WalkPath(path, null);
        }
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        float dt = (float)delta;
        var game = GameRuntime.Instance;
        if (!game.IsReady) return;
        var room = WorldStage.Instance?.Current;
        var current = Playback.Current(game.Content, game.State);

        if (scene is not null)
        {
            if (!IsInstanceValid(scene.Room) || scene.Room != room) scene = null; // the room was rebuilt: its actors are gone
            else
            {
                bool stillOurs = current is not null && current.Source == LineSource.Action && current.SourceId == scene.ActionId;
                if (!stillOurs && !scene.Dismissed) Dismiss(scene);
                StepScene(scene, dt);
                if (scene.Dismissed && scene.Guests.All(g => g.Actor is null || !IsInstanceValid(g.Actor))) scene = null;
            }
        }
        // Start the guests with the action's first line, even when that line is the hero's (they walk in while he speaks).
        if (room is not null && current is { Source: LineSource.Action } && (scene is null || scene.ActionId != current.SourceId))
            EnsureScene(room, current.SourceId);

        UpdateIndicator(room, current);
    }

    private void StepScene(Scene s, float dt)
    {
        s.Elapsed += dt;
        foreach (var g in s.Guests)
        {
            if (g.Actor is null)
            {
                if (s.Dismissed) continue;
                g.Delay -= dt;
                if (g.Delay <= 0) Spawn(s, g);
                continue;
            }
            if (!IsInstanceValid(g.Actor)) { g.Actor = null; continue; }
            if (g.Leaving)
            {
                // Fade out over the last part of the walk out (or at once when it stands still).
                if (!g.Actor.IsWalking || g.Actor.Feet.DistanceTo(g.Def.Enter) < 140f) g.Fade -= dt;
                g.Actor.Modulate = new Color(1, 1, 1, Mathf.Clamp(g.Fade / FadeSeconds, 0, 1));
                if (g.Fade <= 0) { s.Room.RemoveGuest(g.Actor); g.Actor = null; }
                continue;
            }
            g.Fade = Math.Min(FadeSeconds, g.Fade + dt);
            g.Actor.Modulate = new Color(1, 1, 1, Mathf.Clamp(g.Fade / FadeSeconds, 0, 1));
            if (s.Elapsed >= MaxWaitSeconds && !g.Arrived) Hurry();
        }
    }

    // ------------------------------------------------------------------ remote speakers

    /// <summary>
    /// Where a remote speaker of <paramref name="line"/> is shown (the indicator's top, for the subtitle name tag), or null
    /// when the speaker has a body in the room or is not a remote speaker.
    /// </summary>
    public Vector2? RemoteAnchor(PlaybackLine line)
    {
        var room = WorldStage.Instance?.Current;
        if (room is null || line.IsCutscene || room.FindActor(line.SpeakerId) is not null) return null;
        if (!RemoteSpeakers.TryGetValue(line.SpeakerId, out var speaker)) return null;
        var (point, _) = IndicatorPlacement(room, line, speaker);
        return point - new Vector2(0, SpeakerIndicator.Radius + 6);
    }

    private static (Vector2 Point, bool AtHero) IndicatorPlacement(Room room, PlaybackLine line, RemoteSpeaker speaker)
    {
        if (speaker.Anchor == RemoteSpeakerAnchor.Target && line.Source == LineSource.Action &&
            GameRuntime.Instance.Content.FindAction(line.SourceId) is { } action &&
            room.TryGetTarget(action.Target, out var target) && target.Kind != TargetKind.Npc)
        {
            var r = target.Rect;
            var p = new Vector2(r.GetCenter().X, r.Position.Y - SpeakerIndicator.Radius - 10);
            if (p.Y < SpeakerIndicator.Radius + 70) p.Y = r.GetCenter().Y; // a target at the top edge: on it
            return (ClampOnScreen(p), false);
        }
        var hero = room.Hero;
        float side = hero.Feet.X > Room.CanvasSize.X - 220 ? -1 : 1;
        var head = hero.HeadPosition;
        float h = hero.Visual.HeightPx * hero.CurrentScale;
        return (ClampOnScreen(new Vector2(head.X + side * (h * 0.16f + SpeakerIndicator.Radius), head.Y + h * 0.10f)), true);
    }

    private static Vector2 ClampOnScreen(Vector2 p)
    {
        float r = SpeakerIndicator.Radius + 8;
        return new Vector2(Mathf.Clamp(p.X, r, Room.CanvasSize.X - r), Mathf.Clamp(p.Y, r + 60, Room.CanvasSize.Y - 96 - r));
    }

    private void UpdateIndicator(Room? room, PlaybackLine? current)
    {
        bool showing = DialoguePresenter.ShowingLineId is { } shownId && current is not null && shownId == current.LineId;
        RemoteSpeaker? speaker = null;
        bool want = room is not null && showing && current is not null && !current.IsCutscene && room.FindActor(current.SpeakerId) is null &&
                    RemoteSpeakers.TryGetValue(current.SpeakerId, out speaker);
        if (!want || room is null || current is null || speaker is null)
        {
            if (indicator is not null && IsInstanceValid(indicator)) indicator.FadeOut();
            indicatorLine = null;
            return;
        }
        if (indicator is null || !IsInstanceValid(indicator) || indicator.GetParent() != room)
        {
            indicator = new SpeakerIndicator { Name = "SpeakerIndicator", ZIndex = 50 };
            room.AddChild(indicator);
        }
        var (point, atHero) = IndicatorPlacement(room, current, speaker);
        if (indicatorLine != current.LineId)
        {
            indicatorLine = current.LineId;
            indicator.Present(speaker.Kind, point, atHero);
        }
        else indicator.Position = point;
        indicator.Talking = DialoguePresenter.Instance?.IsRevealing == true;
    }
}
