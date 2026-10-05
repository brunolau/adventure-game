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
/// click/Enter/Space, auto-advance, Esc skips (a cutscene: the rest of it; dialogue: everything
/// queued — playback never changes rules state). The speaking actor gets a talk animation and the
/// view gets a speaker anchor above its head. World input is blocked by Core's mode while a line
/// plays. Also shows non-blocking look texts ("barks") and opens the topic menu.
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
    private PlaceholderTopicMenu placeholderMenu = null!;
    private PlaceholderCutsceneFrame placeholderCutscene = null!;

    /// <summary>Frames whose delta is ignored after a session replacement (load / new game).</summary>
    private int settleFrames;

    /// <summary>The singleton presenter.</summary>
    public static DialoguePresenter? Instance { get; private set; }

    /// <summary>True while a line is on screen.</summary>
    public bool IsShowingLine => shown is not null;

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
        GameRuntime.Instance.RoomChanged += (_, _) => HideBark();
    }

    private void ResetAll()
    {
        settleFrames = 2;
        preface = null;
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
                if (revealed >= shownText.Length) speakingActor?.SetTalking(false);
            }
            else
            {
                hold += dt;
                if (PresentationSettings.AutoAdvance && hold >= PresentationSettings.HoldSecondsFor(shownText) && lineElapsed >= lineMinSeconds)
                    Advance();
            }
        }

        UpdateTopicMenu(state);

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

        var subtitle = new SubtitleLine(line, TextService.Get(line.Speaker), shownText, speakingActor?.HeadPosition);
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
        if (shown is null) return;
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

    /// <summary>Esc: skip the rest of the cutscene, or every queued dialogue line.</summary>
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

    private static void ChooseTopic(TopicOption option)
    {
        var game = GameRuntime.Instance;
        if (option.IsStoryAction)
        {
            WorldStage.Instance?.Current?.Hero.Visual.PlayGesture(option.Action!.Animation);
            game.Commit(option.Id);
        }
        else game.Update(s => Dialogue.StartTopic(game.Content, s, option.Id));
    }
}
