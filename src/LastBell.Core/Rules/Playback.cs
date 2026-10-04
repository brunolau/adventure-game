using System.Collections.Immutable;
using LastBell.Core.Content;
using LastBell.Core.State;
using LastBell.Core.Text;

namespace LastBell.Core.Rules;

/// <summary>The line currently on screen.</summary>
/// <param name="LineId">Stable line id (also the text key).</param>
/// <param name="SpeakerId">Speaker id.</param>
/// <param name="Speaker">Speaker name text.</param>
/// <param name="Text">Line text.</param>
/// <param name="Source">Where the line comes from.</param>
/// <param name="SourceId">Owner id (action, topic, room or cutscene).</param>
/// <param name="BeatIndex">Cutscene beat index, or -1.</param>
/// <param name="RemainingLines">Lines still queued after this one.</param>
public sealed record PlaybackLine(string LineId, string SpeakerId, TextRef Speaker, TextRef Text, LineSource Source,
    string SourceId, int BeatIndex, int RemainingLines)
{
    /// <summary>True when the line belongs to a (skippable) cutscene.</summary>
    public bool IsCutscene => Source == LineSource.Cutscene;
}

/// <summary>
/// Dialogue / cutscene / first-entry line playback. The cursor (<see cref="GameState.ActiveLineId"/>
/// plus <see cref="GameState.PlaybackQueue"/>) is part of the save, so a load mid-dialogue continues on
/// the exact line. Playback never changes rules state: the action was committed before the first line,
/// so skipping a cutscene leaves inventory, done, era, room and rewards identical.
/// </summary>
public static class Playback
{
    /// <summary>The current line, or null when nothing is playing.</summary>
    public static PlaybackLine? Current(GameContent content, GameState state)
    {
        if (state.ActiveLineId is null) return null;
        var info = content.FindLine(state.ActiveLineId);
        if (info is null) return null;
        return new PlaybackLine(state.ActiveLineId, info.Line.Speaker, content.SpeakerName(info.Line.Speaker), TextKeys.Of(info.Line),
            info.Source, info.SourceId, info.BeatIndex, state.PlaybackQueue.Length);
    }

    /// <summary>Advances to the next queued line; returns to world mode when the queue is empty.</summary>
    public static GameState Advance(GameContent content, GameState state)
    {
        if (state.ActiveLineId is null) return state;
        if (state.PlaybackQueue.IsEmpty) return state with { ActiveLineId = null, Mode = GameMode.World };
        var next = state.PlaybackQueue[0];
        return state with { ActiveLineId = next, PlaybackQueue = state.PlaybackQueue.RemoveAt(0), Mode = ModeFor(content, next) };
    }

    /// <summary>Skips the rest of the current cutscene (following non-cutscene lines still play).</summary>
    public static GameState SkipCutscene(GameContent content, GameState state)
    {
        var current = state.ActiveLineId is null ? null : content.FindLine(state.ActiveLineId);
        if (current is null || current.Source != LineSource.Cutscene) return state;
        var queue = state.PlaybackQueue;
        var skip = 0;
        while (skip < queue.Length && content.FindLine(queue[skip]) is { Source: LineSource.Cutscene } l && l.SourceId == current.SourceId) skip++;
        var rest = queue.RemoveRange(0, skip);
        if (rest.IsEmpty) return state with { ActiveLineId = null, PlaybackQueue = rest, Mode = GameMode.World };
        return state with { ActiveLineId = rest[0], PlaybackQueue = rest.RemoveAt(0), Mode = ModeFor(content, rest[0]) };
    }

    /// <summary>Skips everything that is queued (e.g. after a crash recovery the player chose "skip").</summary>
    public static GameState SkipAll(GameState state) =>
        state.ActiveLineId is null && state.PlaybackQueue.IsEmpty ? state
            : state with { ActiveLineId = null, PlaybackQueue = ImmutableArray<string>.Empty, Mode = GameMode.World };

    /// <summary>Plays to the end, returning the final state (tests, auto-advance).</summary>
    public static GameState FinishAll(GameContent content, GameState state)
    {
        var guard = 0;
        while (state.ActiveLineId is not null && guard++ < 10_000) state = Advance(content, state);
        return state;
    }

    /// <summary>All line ids of a cutscene in beat order.</summary>
    public static IEnumerable<string> CutsceneLineIds(CutsceneDef cutscene) =>
        cutscene.Beats.SelectMany(b => b.Lines).Select(l => l.LineId ?? "").Where(id => id.Length > 0);

    /// <summary>Starts playing a list of line ids (or returns to world mode when it is empty).</summary>
    internal static GameState Start(GameContent content, GameState state, IReadOnlyList<string> lineIds)
    {
        if (lineIds.Count == 0) return state with { ActiveLineId = null, PlaybackQueue = ImmutableArray<string>.Empty, Mode = GameMode.World };
        return state with
        {
            ActiveLineId = lineIds[0],
            PlaybackQueue = lineIds.Skip(1).ToImmutableArray(),
            Mode = ModeFor(content, lineIds[0]),
        };
    }

    private static GameMode ModeFor(GameContent content, string lineId) =>
        content.FindLine(lineId)?.Source == LineSource.Cutscene ? GameMode.Cutscene : GameMode.Dialogue;
}
