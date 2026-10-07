using System;
using System.Linq;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Text;
using LastBell.Game.Hooks;
using LastBell.Game.Presentation.Placeholders;
using LastBell.Game.Runtime;
using LastBell.Game.World;

namespace LastBell.Game.Presentation;

/// <summary>
/// Plays Core line sequences (action lines, topics, cutscene beats, first-entry lines): speaker
/// name and text through <see cref="TextService"/>, typewriter reveal by text speed, advance by
/// click/Enter/Space, auto-advance. Esc skips the current line; a second Esc within
/// <see cref="EscapeDoubleSeconds"/> skips the whole sequence (a cutscene: the rest of it; dialogue:
/// everything queued) (orchestrator decision after the playtests, PT-F13) — playback never changes
/// rules state. The speaking actor gets a talk animation and the view gets a speaker anchor above its
/// head. World input is blocked by Core's mode while a line plays. Also shows non-blocking look texts
/// ("barks") and opens the topic menu; after a topic's lines the same conversation's menu opens again
/// until the player ends it or no topic is left (<see cref="Dialogue.ReturnToMenu"/>, PT-S17).
/// Rendering goes through <see cref="ISubtitleView"/> (UiBus.Subtitles, else <see cref="DefaultSubtitleView"/>).
/// </summary>
public partial class DialoguePresenter : Node
{
    private DefaultSubtitleView defaultView = null!;
    private PlaybackLine? shown;
    private string shownText = "";
    private float revealed;
    private float hold;
    private float lineMinSeconds;
    private float lineElapsed;
    private Actor? speakingActor;
    private float barkLeft;
    private string? cutsceneId;
    private int cutsceneBeat = -1;
    private bool menuOpen;
    private PlaybackLine? preface;

    /// <summary>Line id of a presentation-only preface line (<see cref="ShowPreface"/>).</summary>
    public const string PrefaceLineId = "preface";

    /// <summary>Two Esc presses within this time skip the whole sequence (PT-F13).</summary>
    public const double EscapeDoubleSeconds = 0.5;

    private double lastEscape = -10;

    /// <summary>NPC hotspot (and room) whose topic menu opens again after the chosen topic's lines (PT-S17), or null.</summary>
    private string? resumeHotspot;
    private string? resumeRoom;
    private PlaceholderTopicMenu placeholderMenu = null!;

    /// <summary>NPC actors that take part in the running conversation (<see cref="Actor.SetEngaged"/>).</summary>
    private readonly System.Collections.Generic.HashSet<Actor> engaged = new();

    /// <summary>Seconds without a conversation before the engaged NPCs are released (no flicker between two lines).</summary>
    private const float EngagedReleaseSeconds = 0.35f;

    private float engagedIdle;
    private PlaceholderCutsceneFrame placeholderCutscene = null!;

    /// <summary>Frames whose delta is ignored after a session replacement (load / new game).</summary>
    private int settleFrames;

    /// <summary>The singleton presenter.</summary>
    public static DialoguePresenter? Instance { get; private set; }

    /// <summary>True while a line is on screen.</summary>
    public bool IsShowingLine => shown is not null;

    /// <summary>Line id on screen now, or null (World/GuestStage.cs shows remote speaker badges for it).</summary>
    public static string? ShowingLineId => Instance?.shown?.LineId;

    /// <summary>True while the line on screen is still being typed out.</summary>
    public bool IsRevealing => shown is not null && revealed < shownText.Length;

    /// <summary>Raised when a line appears on screen (debug harness, voice-over hook).</summary>
    public event Action<SubtitleLine>? LineShown;

    private ISubtitleView View => UiBus.Subtitles ?? defaultView;

    private ITopicMenuView Menu => UiBus.TopicMenu ?? placeholderMenu;

    private ICutsceneView CutsceneView => UiBus.Cutscene ?? placeholderCutscene;

    /// <inheritdoc />
    public override void _Ready()
    {
        Instance = this;
        var layer = new CanvasLayer { Name = "SubtitleLayer", Layer = 20 };
        AddChild(layer);
        placeholderCutscene = new PlaceholderCutsceneFrame { Name = "PlaceholderCutsceneFrame" };
        layer.AddChild(placeholderCutscene);
        defaultView = new DefaultSubtitleView { Name = "DefaultSubtitleView" };
        layer.AddChild(defaultView);
        placeholderMenu = new PlaceholderTopicMenu { Name = "PlaceholderTopicMenu" };
        layer.AddChild(placeholderMenu);
        GameRuntime.Instance.SessionReplaced += ResetAll;
        GameRuntime.Instance.RoomChanged += (_, _) => { HideBark(); resumeHotspot = null; engaged.Clear(); };
    }

    private void ResetAll()
    {
        settleFrames = 2;
        preface = null;
        resumeHotspot = null;
        lastEscape = -10;
        HideLine();
        HideBark();
        if (menuOpen) { Menu.Close(); menuOpen = false; }
        EndCutscene();
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        var game = GameRuntime.Instance;
        if (!game.IsReady) return;
        // After a load the room is built synchronously inside that frame; the next frame's long delta must not
        // count as reading time, or the line that was on screen when the game was saved is skipped (AT17).
        float dt = settleFrames > 0 ? 0f : (float)delta;
        if (settleFrames > 0) settleFrames--;
        var state = game.State;
        var current = Playback.Current(game.Content, state);

        if (preface is not null)
        {
            // A preface line (e.g. a puzzle's success line) plays before Core's queued lines.
            if (!ReferenceEquals(shown, preface))
            {
                HideLine();
                ShowLine(preface);
            }
        }
        else if (current?.LineId != shown?.LineId)
        {
            HideLine();
            if (current is not null)
            {
                var stage = WorldStage.Instance;
                if (stage is not null && stage.CanPresent(current)) ShowLine(current);
                else stage?.PokePendingTransition();
            }
            if (current is null || !current.IsCutscene) EndCutscene();
        }

        if (shown is not null)
        {
            lineElapsed += dt;
            float cps = PresentationSettings.TextCharsPerSecond;
            if (revealed < shownText.Length)
            {
                revealed = cps <= 0 ? shownText.Length : Math.Min(shownText.Length, revealed + cps * dt);
                View.SetReveal(revealed >= shownText.Length ? -1 : (int)revealed);
                if (revealed >= shownText.Length && !LastBell.Game.Audio.AudioService.VoicePlaying) speakingActor?.SetTalking(false);
            }
            else
            {
                // With voice-over, the speaker keeps talking until the line's audio ends, and auto-advance waits for it.
                bool voicePlaying = LastBell.Game.Audio.AudioService.VoicePlaying;
                if (!voicePlaying) speakingActor?.SetTalking(false);
                hold += dt;
                if (PresentationSettings.AutoAdvance && !voicePlaying && hold >= PresentationSettings.HoldSecondsFor(shownText) && lineElapsed >= lineMinSeconds)
                    Advance();
            }
        }

        ResumeConversation(game);
        UpdateTopicMenu(game.State);
        UpdateEngaged(game, dt);

        if (barkLeft > 0)
        {
            barkLeft -= dt;
            if (barkLeft <= 0) HideBark();
        }
    }

    // ------------------------------------------------------------------ lines

    private void ShowLine(PlaybackLine line)
    {
        var game = GameRuntime.Instance;
        shown = line;
        shownText = TextService.Get(line.Text);
        revealed = 0;
        hold = 0;
        lineElapsed = 0;
        lineMinSeconds = 0;
        var room = WorldStage.Instance?.Current;
        speakingActor = room?.FindActor(line.SpeakerId);
        speakingActor?.SetTalking(true);
        if (speakingActor is not null && room is not null && speakingActor != room.Hero && !room.Hero.IsWalking) room.Hero.FaceTowards(speakingActor.Feet);
        if (speakingActor is not null && room is not null && speakingActor != room.Hero) speakingActor.FaceTowards(room.Hero.Feet);

        if (line.IsCutscene && game.Content.FindCutscene(line.SourceId) is { } cutscene)
        {
            if (cutsceneId != cutscene.Id)
            {
                EndCutscene();
                cutsceneId = cutscene.Id;
                cutsceneBeat = -1;
                CutsceneView.Begin(cutscene);
            }
            if (line.BeatIndex != cutsceneBeat && line.BeatIndex >= 0 && line.BeatIndex < cutscene.Beats.Count)
            {
                cutsceneBeat = line.BeatIndex;
                CutsceneView.Beat(cutscene, cutsceneBeat);
            }
            var beat = cutscene.Beats[Math.Clamp(line.BeatIndex, 0, cutscene.Beats.Count - 1)];
            lineMinSeconds = (float)(beat.DurationMinS / Math.Max(1, beat.Lines.Count)) * PresentationSettings.CutsceneMinDurationScale;
        }

        // A speaker without a body here (phone, recording, service channel, device; ISSUES PT-S18): the tag sits above its badge.
        var anchor = speakingActor?.HeadPosition ?? GuestStage.Instance?.RemoteAnchor(line);
        var subtitle = new SubtitleLine(line, TextService.Get(line.Speaker), shownText, anchor);
        View.ShowLine(subtitle);
        View.SetReveal(PresentationSettings.TextCharsPerSecond <= 0 ? -1 : 0);
        if (PresentationSettings.TextCharsPerSecond <= 0) revealed = shownText.Length;
        LineShown?.Invoke(subtitle);
    }

    private void HideLine()
    {
        if (shown is null) return;
        speakingActor?.SetTalking(false);
        speakingActor = null;
        shown = null;
        View.HideLine();
    }

    /// <summary>Click/Enter: reveal the whole line first, then advance to the next queued line.</summary>
    public void Advance()
    {
        if (shown is null)
        {
            // The room waits for a guest speaker who is still walking in: a click puts the guest there at once.
            GuestStage.Instance?.Hurry();
            return;
        }
        if (revealed < shownText.Length)
        {
            revealed = shownText.Length;
            View.SetReveal(-1);
            speakingActor?.SetTalking(false);
            return;
        }
        if (ReferenceEquals(shown, preface))
        {
            preface = null;
            HideLine();
            return;
        }
        var game = GameRuntime.Instance;
        game.Update(s => Playback.Advance(game.Content, s));
        ResumeConversation(game, afterUpdate: true);
    }

    /// <summary>
    /// Shows a presentation-only line as a normal subtitle before Core's queued lines (the puzzle
    /// modal's success line, "ADAM: Tri tvary, tri zhody. Hotovo."): same view, speaker tag, talk
    /// animation, reveal and auto-advance; a click / Enter advances it, Esc skips it with the rest.
    /// It changes no rules state.
    /// </summary>
    public void ShowPreface(TextRef text, string speakerId)
    {
        if (TextService.Get(text).Length == 0) return;
        var content = GameRuntime.Instance.Content;
        preface = new PlaybackLine(PrefaceLineId, speakerId, content.SpeakerName(speakerId), text, LineSource.Action, "", -1, 0);
    }

    /// <summary>True while a preface line is pending or on screen.</summary>
    public bool HasPreface => preface is not null;

    /// <summary>
    /// Esc while a line plays (PT-F13): the first press skips the current line (also while it is still being typed),
    /// a second press within <see cref="EscapeDoubleSeconds"/> skips the whole sequence (<see cref="Skip"/>).
    /// </summary>
    public void Escape()
    {
        double now = Time.GetTicksMsec() / 1000.0;
        bool second = now - lastEscape <= EscapeDoubleSeconds;
        lastEscape = now;
        if (second) Skip();
        else SkipLine();
    }

    /// <summary>
    /// True for an Esc right after an Esc that skipped a line: the router swallows it when the sequence already ended,
    /// so a quick double Esc on the last line neither opens the pause menu nor closes the topic menu that comes back.
    /// </summary>
    public bool IsEscapeFollowUp() => Time.GetTicksMsec() / 1000.0 - lastEscape <= EscapeDoubleSeconds;

    /// <summary>Skips only the line on screen (the next queued line follows; the last one ends the sequence).</summary>
    public void SkipLine()
    {
        if (shown is null) return;
        if (ReferenceEquals(shown, preface))
        {
            preface = null;
            HideLine();
            return;
        }
        var game = GameRuntime.Instance;
        game.Update(s => Playback.Advance(game.Content, s));
        ResumeConversation(game, afterUpdate: true);
    }

    /// <summary>Skips the whole sequence: the rest of the cutscene, or every queued dialogue line (cutscene skip button, double Esc).</summary>
    public void Skip()
    {
        if (preface is not null)
        {
            preface = null;
            HideLine();
        }
        var game = GameRuntime.Instance;
        if (shown?.IsCutscene == true) game.Update(s => Playback.SkipCutscene(game.Content, s));
        else game.Update(Playback.SkipAll);
        ResumeConversation(game, afterUpdate: true);
    }

    private void EndCutscene()
    {
        if (cutsceneId is null) return;
        var cutscene = GameRuntime.Instance.Content.FindCutscene(cutsceneId);
        cutsceneId = null;
        cutsceneBeat = -1;
        if (cutscene is not null) CutsceneView.End(cutscene);
    }

    // ------------------------------------------------------------------ barks (looks)

    /// <summary>Shows a non-blocking look text above the speaker (normally the hero).</summary>
    public void ShowBark(TextRef text, string speakerId)
    {
        string translated = TextService.Get(text);
        if (translated.Length == 0) return;
        var room = WorldStage.Instance?.Current;
        var actor = room?.FindActor(speakerId) ?? room?.Hero;
        var anchor = actor?.HeadPosition ?? new Vector2(960, 700);
        float seconds = PresentationSettings.HoldSecondsFor(translated) + 0.6f;
        barkLeft = seconds;
        View.ShowBark(new BarkLine(translated, speakerId, anchor, seconds));
    }

    /// <summary>True while a look text (bark) is on screen.</summary>
    public bool IsShowingBark => barkLeft > 0;

    /// <summary>Hides the look text.</summary>
    public void HideBark()
    {
        barkLeft = 0;
        View.HideBark();
    }

    // ------------------------------------------------------------------ conversation partners

    /// <summary>
    /// Marks the NPCs of the running conversation as engaged, so an NPC whose idle is an activity stands still while
    /// either side speaks (owner 2026-10-07: Zuzana hopped through her talks): the NPC of the topic menu, the speaker of
    /// each non-cutscene line, the NPC an action's lines are aimed at, and the NPC whose menu reopens. They stay engaged
    /// until nothing of the conversation is left for <see cref="EngagedReleaseSeconds"/>.
    /// </summary>
    private void UpdateEngaged(GameRuntime game, float dt)
    {
        var room = WorldStage.Instance?.Current;
        var state = game.State;
        bool lineOn = shown is not null && !shown.IsCutscene && !ReferenceEquals(shown, preface);
        bool active = room is not null && (state.Mode == GameMode.Dialogue || lineOn || resumeHotspot is not null);
        if (active && room is not null)
        {
            engagedIdle = 0;
            void Add(Actor? a)
            {
                if (a is null || a.IsHero || !engaged.Add(a)) return;
                a.SetEngaged(true);
            }
            string? talk = InteractionController.Instance?.TalkHotspotId;
            if ((state.Mode == GameMode.Dialogue || (lineOn && shown!.Source == LineSource.Topic)) && talk is not null)
                Add(NpcOf(room, talk));
            if (resumeHotspot is not null) Add(NpcOf(room, resumeHotspot));
            if (lineOn)
            {
                if (speakingActor is not null) Add(speakingActor);
                if (shown!.Source == LineSource.Action && game.Content.FindAction(shown.SourceId) is { } action)
                    Add(NpcOf(room, action.Target));
            }
            return;
        }
        if (engaged.Count == 0) return;
        engagedIdle += dt;
        if (room is not null && engagedIdle < EngagedReleaseSeconds) return;
        foreach (var a in engaged)
            if (IsInstanceValid(a)) a.SetEngaged(false);
        engaged.Clear();
    }

    private static Actor? NpcOf(Room room, string id) => room.Npcs.TryGetValue(id, out var actor) ? actor : null;

    // ------------------------------------------------------------------ topic menu

    private void UpdateTopicMenu(GameState state)
    {
        bool wantMenu = state.Mode == GameMode.Dialogue && state.ActiveLineId is null;
        if (wantMenu == menuOpen) return;
        menuOpen = wantMenu;
        if (!wantMenu)
        {
            Menu.Close();
            return;
        }
        var game = GameRuntime.Instance;
        var hotspotId = InteractionController.Instance?.TalkHotspotId;
        var hotspot = hotspotId is null ? null : game.Content.GetRoom(state.Room).Hotspots.FirstOrDefault(h => h.Id == hotspotId);
        var topics = hotspot is null ? Array.Empty<TopicOption>() : (System.Collections.Generic.IReadOnlyList<TopicOption>)Dialogue.TopicsFor(game.Content, state, hotspot);
        Menu.Open(new TopicMenuRequest(hotspot?.CharacterId ?? "", hotspotId ?? "", topics, ChooseTopic, () => game.Update(Dialogue.CloseMenu)));
    }

    /// <summary>
    /// After the chosen topic's lines: back in the scene with nothing playing, the same NPC's topic menu opens again
    /// through Core (<see cref="Dialogue.ReturnToMenu"/>; closed for good when no topic is left). A room change, a
    /// cutscene or a puzzle in between ends the conversation. Called right after the update that ends the lines
    /// (<paramref name="afterUpdate"/>: the old line is still on screen until the next frame), so the scene never has a
    /// frame in world mode between the last line and the menu; and every frame as a fallback.
    /// </summary>
    private void ResumeConversation(GameRuntime game, bool afterUpdate = false)
    {
        if (resumeHotspot is null) return;
        var state = game.State;
        if (state.Room != resumeRoom || state.Mode is GameMode.Cutscene or GameMode.Puzzle or GameMode.Map or GameMode.Journal or GameMode.Pause)
        {
            resumeHotspot = null;
            return;
        }
        if (state.Mode != GameMode.World || state.ActiveLineId is not null || preface is not null || (!afterUpdate && shown is not null)) return;
        var stage = WorldStage.Instance;
        if (stage is null || !stage.IsSettled || stage.Transitioning || (stage.Current?.Hero.IsWalking ?? false)) return;
        string id = resumeHotspot;
        resumeHotspot = null;
        if (InteractionController.Instance?.TalkHotspotId != id) return;
        game.Update(s => Dialogue.ReturnToMenu(game.Content, s, id));
    }

    private void ChooseTopic(TopicOption option)
    {
        var game = GameRuntime.Instance;
        resumeHotspot = InteractionController.Instance?.TalkHotspotId;
        resumeRoom = game.State.Room;
        if (option.IsStoryAction)
        {
            WorldStage.Instance?.Current?.Hero.Visual.PlayGesture(option.Action!.Animation);
            game.Commit(option.Id);
        }
        else game.Update(s => Dialogue.StartTopic(game.Content, s, option.Id));
        ResumeConversation(game, afterUpdate: true); // a topic without lines: straight back to the menu
    }
}
