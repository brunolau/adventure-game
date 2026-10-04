using LastBell.Core.Content;
using LastBell.Core.State;
using LastBell.Core.Text;

namespace LastBell.Core.Rules;

/// <summary>A quest line in the journal.</summary>
/// <param name="QuestId">Quest id.</param>
/// <param name="Title">Title.</param>
/// <param name="Goal">Goal.</param>
/// <param name="Status">Status derived from action ids.</param>
/// <param name="IsPinned">True when pinned.</param>
public sealed record JournalQuest(string QuestId, TextRef Title, TextRef Goal, QuestStatus Status, bool IsPinned);

/// <summary>Kind of a journal finding.</summary>
public enum FindingKind
{
    /// <summary>First look at a hotspot or item (observation only, never progress).</summary>
    Observation,
    /// <summary>Transcript of a committed action, with its objective.</summary>
    Action,
}

/// <summary>An entry of the "Findings" tab, in the order it was recorded.</summary>
/// <param name="Kind">Observation or action.</param>
/// <param name="Key">Journal key (<c>action.&lt;id&gt;</c> or the look text key).</param>
/// <param name="Text">Look text or action journal text.</param>
/// <param name="Objective">Objective of the action (empty for observations).</param>
public sealed record JournalFinding(FindingKind Kind, string Key, TextRef Text, TextRef Objective);

/// <summary>A puzzle clue kept readable in the journal.</summary>
/// <param name="PuzzleId">Puzzle id.</param>
/// <param name="Title">Puzzle title.</param>
/// <param name="Clue">Clue text.</param>
/// <param name="Solved">True when the puzzle action is done.</param>
public sealed record JournalClue(string PuzzleId, TextRef Title, TextRef Clue, bool Solved);

/// <summary>A visited room on the time map.</summary>
/// <param name="RoomId">Room id.</param>
/// <param name="Name">Room name.</param>
public sealed record JournalRoom(string RoomId, TextRef Name);

/// <summary>An unlocked era on the time map.</summary>
/// <param name="Year">Year.</param>
/// <param name="Date">Date text.</param>
/// <param name="VisitedRooms">Visited rooms of the era.</param>
public sealed record JournalEra(int Year, TextRef Date, IReadOnlyList<JournalRoom> VisitedRooms);

/// <summary>A person on the "People" tab.</summary>
/// <param name="CharacterId">Character id.</param>
/// <param name="Name">Name.</param>
/// <param name="Transcript">Everything heard from them.</param>
public sealed record JournalPerson(string CharacterId, TextRef Name, IReadOnlyList<TranscriptEntry> Transcript);

/// <summary>Album entry for a completed side quest.</summary>
/// <param name="QuestId">Side quest id.</param>
/// <param name="Title">Quest title.</param>
/// <param name="Shot">Epilogue shot caption (empty if none).</param>
/// <param name="Line">Epilogue line (empty if none).</param>
public sealed record AlbumEntry(string QuestId, TextRef Title, TextRef Shot, TextRef Line);

/// <summary>Complete journal view model (tabs: Goals, Findings, People, Time map, Album).</summary>
public sealed record JournalView(
    IReadOnlyList<JournalQuest> MainQuests,
    IReadOnlyList<JournalQuest> SideQuests,
    JournalQuest? CurrentMainQuest,
    JournalQuest? ActiveSideQuest,
    TextRef LatestObjective,
    IReadOnlyList<JournalFinding> Findings,
    IReadOnlyList<JournalClue> Clues,
    IReadOnlyList<JournalPerson> People,
    IReadOnlyList<JournalEra> TimeMap,
    IReadOnlyList<AlbumEntry> Album,
    IReadOnlyList<string> ReplayableCutscenes);

/// <summary>
/// Journal (journal_contract): every first look is stored as an observation; only explicit actions
/// change progress. Every successful action stores its transcript and objective (written by the
/// commit transaction). Puzzle clues stay readable. One main and one side quest can be pinned.
/// </summary>
public static class Journal
{
    /// <summary>Journal key of a committed action (same as runtime_contract.ts).</summary>
    public static string ActionEntryKey(string actionId) => "action." + actionId;

    /// <summary>Records the first look at a hotspot or item as an observation (no-op for unknown keys or repeats).</summary>
    public static GameState RecordObservation(GameContent content, GameState state, string? lookKey)
    {
        if (lookKey is null || content.FindLookText(lookKey) is null || state.JournalSeen.Contains(lookKey)) return state;
        return state with { JournalSeen = IdList.AddUnique(state.JournalSeen, lookKey) };
    }

    /// <summary>
    /// Applies the bookkeeping of a look resolution: records the observation. The look itself is shown
    /// by the presentation; nothing else changes (the inventory drawer stays open).
    /// </summary>
    public static GameState ApplyLook(GameContent content, GameState state, Resolution.Look look) =>
        RecordObservation(content, state, look.ObservationKey);

    /// <summary>Builds the journal view model.</summary>
    public static JournalView Build(GameContent content, GameState state)
    {
        JournalQuest Entry(QuestDef q) => new(q.Id, TextKeys.TitleOf(q), TextKeys.GoalOf(q), Quests.StatusOf(q, state),
            q.Id == state.PinnedMainQuest || q.Id == state.PinnedSideQuest);

        var next = Quests.NextMainQuest(content, state);
        var main = content.Quests.Where(q => q.IsMain && (Quests.StatusOf(q, state) != QuestStatus.NotStarted || q == next))
            .Select(Entry).ToList();
        var side = content.Quests.Where(q => q.IsSide && Quests.StatusOf(q, state) != QuestStatus.NotStarted).Select(Entry).ToList();
        var current = Quests.CurrentMainQuest(content, state);
        var activeSide = state.PinnedSideQuest is not null && content.FindQuest(state.PinnedSideQuest) is { } ps && !state.IsDone(ps.Completion)
            ? ps : Quests.ActiveSideQuest(content, state);

        var findings = new List<JournalFinding>();
        foreach (var key in state.JournalSeen)
        {
            if (key.StartsWith("action.", StringComparison.Ordinal) && content.FindAction(key["action.".Length..]) is { } action)
                findings.Add(new JournalFinding(FindingKind.Action, key, TextKeys.JournalOf(action), TextKeys.ObjectiveOf(action)));
            else if (content.FindLookText(key) is { } look)
                findings.Add(new JournalFinding(FindingKind.Observation, key, look, TextRef.Empty));
        }

        var clues = new List<JournalClue>();
        foreach (var puzzle in content.Data.Puzzles)
        {
            var action = Puzzles.ActionFor(content, puzzle.Id);
            if (action is null) continue;
            var solved = state.IsDone(action.Id);
            if (solved || state.AllDone(action.RequiresDone))
                clues.Add(new JournalClue(puzzle.Id, TextKeys.TitleOf(puzzle), TextKeys.ClueOf(puzzle), solved));
        }

        var people = Dialogue.MetCharacters(content, state)
            .Select(c => new JournalPerson(c.Id, TextKeys.NameOf(c), Dialogue.Transcript(content, state, c.Id))).ToList();

        var timeMap = Navigation.UnlockedEras(content, state).Select(e => new JournalEra(e.Year, TextKeys.DateOf(e),
            state.Visited.Select(content.GetRoom).Where(r => r.Era == e.Year).Select(r => new JournalRoom(r.Id, TextKeys.NameOf(r))).ToList())).ToList();

        var album = content.Quests.Where(q => q.IsSide && state.SideRewards.Contains(q.Id)).Select(q =>
        {
            var index = content.Data.Epilogue.ToList().FindIndex(e => e.Quest == q.Id);
            var shot = index < 0 ? TextRef.Empty : TextKeys.ShotOf(content.Data.Epilogue[index], index);
            var line = index < 0 ? TextRef.Empty : TextKeys.LineOf(content.Data.Epilogue[index], index);
            return new AlbumEntry(q.Id, TextKeys.TitleOf(q), shot, line);
        }).ToList();

        return new JournalView(main, side, current is null ? null : Entry(current), activeSide is null ? null : Entry(activeSide),
            Quests.LatestObjective(content, state), findings, clues, people, timeMap, album, Postgame.ReplayableCutscenes(content, state));
    }
}
