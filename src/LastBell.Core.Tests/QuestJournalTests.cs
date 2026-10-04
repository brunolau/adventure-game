using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Tests.Support;

namespace LastBell.Core.Tests;

/// <summary>Quests, hints, pinning and the journal.</summary>
public sealed class QuestJournalTests
{
    private static readonly GameContent C = TestData.Content;

    [Fact]
    public void Quest_status_is_derived_from_action_ids()
    {
        var m01 = C.FindQuest("M01")!;
        Assert.Equal(QuestStatus.NotStarted, Quests.StatusOf(m01, C.InitialState));
        Assert.Equal(QuestStatus.InProgress, Quests.StatusOf(m01, TestData.StateAfter("G01")));
        Assert.Equal(QuestStatus.Done, Quests.StatusOf(m01, TestData.StateAfter("G05")));
    }

    [Fact]
    public void Hints_reveal_one_level_per_request_up_to_three()
    {
        var s = C.InitialState;
        Assert.Empty(Hints.Revealed(C, s, "M01"));
        s = Hints.RevealNext(C, s, "M01");
        Assert.Equal(new[] { "quest.M01.hint.1" }, Hints.Revealed(C, s, "M01").Select(h => h.Key));
        s = Hints.RevealNext(C, Hints.RevealNext(C, Hints.RevealNext(C, s, "M01"), "M01"), "M01");
        Assert.Equal(3, Hints.RevealedLevel(s, "M01"));
        Assert.Equal(3, Hints.Revealed(C, s, "M01").Count);
        Assert.Equal(s.Done, C.InitialState.Done); // hints never change progress
    }

    [Fact]
    public void Pinning_keeps_one_main_and_one_side_quest()
    {
        var s = Quests.Pin(C, C.InitialState, "M02");
        s = Quests.Pin(C, s, "Q1");
        s = Quests.Pin(C, s, "M03");
        Assert.Equal("M03", s.PinnedMainQuest);
        Assert.Equal("Q1", s.PinnedSideQuest);
        Assert.Equal("M03", Quests.CurrentMainQuest(C, s)!.Id);
        Assert.Null(Quests.Unpin(C, s, "Q1").PinnedSideQuest);
    }

    [Fact]
    public void Parallel_main_lines_work_in_either_order()
    {
        // M05 (cassette, B04..B12) and M06 (map, B13..B16) are independent; B22 needs both lines.
        var start = TestData.StateAfter("B03");
        var tapeFirst = start;
        foreach (var id in C.FindQuest("M04")!.Actions.Concat(C.FindQuest("M05")!.Actions).Concat(C.FindQuest("M06")!.Actions))
            tapeFirst = Driver.Perform(C, tapeFirst, C.GetAction(id));
        var mapFirst = start;
        foreach (var id in C.FindQuest("M06")!.Actions.Concat(C.FindQuest("M04")!.Actions).Concat(C.FindQuest("M05")!.Actions))
            mapFirst = Driver.Perform(C, mapFirst, C.GetAction(id));
        Assert.Equal(tapeFirst.Inventory.OrderBy(x => x), mapFirst.Inventory.OrderBy(x => x));
        var b22 = C.GetAction("B22");
        Assert.Contains("B12", b22.RequiresDone);
        Assert.Contains("B16", b22.RequiresDone);
    }

    [Fact]
    public void Journal_records_first_looks_once_and_actions_with_objectives()
    {
        var s = C.InitialState;
        var look = Assert.IsType<Resolution.Look>(GameRules.ResolveInteraction(C, s, new Hit.Hotspot("S01.fuse"), PointerButton.Right));
        s = Journal.ApplyLook(C, s, look);
        s = Journal.ApplyLook(C, s, look);
        Assert.Single(s.JournalSeen, "look.S01.fuse");
        Assert.Empty(s.Done); // looks never change progress
        s = Playback.FinishAll(C, GameRules.CommitAction(C, s, "G01"));
        var view = Journal.Build(C, s);
        Assert.Equal(2, view.Findings.Count);
        Assert.Equal(FindingKind.Observation, view.Findings[0].Kind);
        Assert.Equal(FindingKind.Action, view.Findings[1].Kind);
        Assert.Equal("action.G01.journal", view.Findings[1].Text.Key);
        Assert.Equal("action.G01.objective", view.Findings[1].Objective.Key);
        Assert.Equal("action.G01.objective", view.LatestObjective.Key);
        Assert.Equal("M01", view.CurrentMainQuest!.QuestId);
        Assert.Contains(view.MainQuests, q => q.QuestId == "M01" && q.Status == QuestStatus.InProgress);
    }

    [Fact]
    public void Journal_keeps_puzzle_clues_readable_and_marks_solved_ones()
    {
        var before = Journal.Build(C, TestData.StateBefore("G11"));
        Assert.Contains(before.Clues, c => c.PuzzleId == "P01" && !c.Solved && c.Clue.Key == "puzzle.P01.clue");
        var end = Journal.Build(C, TestData.MainEnd);
        Assert.Equal(5, end.Clues.Count);
        Assert.All(end.Clues, c => Assert.True(c.Solved));
    }

    [Fact]
    public void Journal_time_map_people_and_album()
    {
        var end = Journal.Build(C, TestData.MainEnd);
        Assert.Equal(5, end.TimeMap.Count);
        Assert.Contains(end.People, p => p.CharacterId == "TONO82");
        Assert.Empty(end.Album);
        Assert.Contains("CS07", end.ReplayableCutscenes);
        var s = TestData.MainEnd;
        foreach (var id in new[] { "Q1A", "Q1B", "Q1C" }) s = Driver.Perform(C, s, C.GetAction(id));
        var album = Journal.Build(C, s).Album;
        Assert.Equal("Q1", Assert.Single(album).QuestId);
        Assert.Equal("epilogue.1.shot", album[0].Shot.Key);
    }

    [Fact]
    public void Active_side_quest_is_the_last_started_one_and_never_hides_the_main_goal()
    {
        var s = Driver.Perform(C, TestData.StateAfter("G01"), C.GetAction("Q1A"));
        Assert.Equal("Q1", Quests.ActiveSideQuest(C, s)!.Id);
        var view = Journal.Build(C, s);
        Assert.Equal("Q1", view.ActiveSideQuest!.QuestId);
        Assert.Equal("M01", view.CurrentMainQuest!.QuestId);
    }
}
