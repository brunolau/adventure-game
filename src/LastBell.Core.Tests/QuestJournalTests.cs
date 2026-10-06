using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Tests.Support;
using LastBell.Core.Text;

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
        var s = C.InitialState with { Difficulty = Difficulty.Easy }; // three levels on Easy (DifficultyTests: Standard, Hard)
        Assert.Empty(Hints.Revealed(C, s, "M01"));
        s = Hints.RevealNext(C, s, "M01");
        Assert.Equal(new[] { "quest.M01.hint.1" }, Hints.Revealed(C, s, "M01").Select(h => h.Text.Key));
        s = Hints.RevealNext(C, Hints.RevealNext(C, Hints.RevealNext(C, s, "M01"), "M01"), "M01");
        Assert.Equal(3, Hints.RevealedLevel(C, s, "M01"));
        Assert.Equal(new[] { 1, 2, 3 }, Hints.Revealed(C, s, "M01").Select(h => h.Level));
        Assert.Equal(s, Hints.RevealNext(C, s, "M01")); // capped at three
        Assert.Equal(s.Done, C.InitialState.Done); // hints never change progress
        Assert.Equal(s.Inventory, C.InitialState.Inventory);
    }

    /// <summary>
    /// PT-F08: after B07 (tape already shown to Juro) the first hint of M05 repeated "Ukáž kazetu Jurovi"; now every
    /// level talks about the next undone step (the scale at Fero's) and level 3 is only that step.
    /// </summary>
    [Fact]
    public void Hints_follow_the_next_undone_step_of_the_quest()
    {
        var s = TestData.StateAfter("B07") with { Difficulty = Difficulty.Easy };
        Assert.Equal("B08", Hints.CurrentStep(C, s, "M05")!.Id);
        for (var i = 0; i < 3; i++) s = Hints.RevealNext(C, s, "M05");
        var hints = Hints.Revealed(C, s, "M05");
        Assert.Equal("action.B07.objective", hints[0].Text.Key); // the objective that sent the player to Fero
        Assert.Equal(Hints.PlaceKey, hints[1].Text.Key);
        Assert.Equal(new[] { "room", "target" }, hints[1].Args.Select(a => a.Name));
        Assert.Equal("room.S25.name", hints[1].Args[0].Value.Key);
        Assert.Equal("hotspot.S25.scale.name", hints[1].Args[1].Value.Key);
        Assert.Equal(Hints.StepKey("B08"), hints[2].Text.Key);
        Assert.Equal(C.GetAction("B08").Label, hints[2].Text.Fallback);
        Assert.DoesNotContain(hints, h => h.Text.Key.StartsWith("quest.M05.hint.", StringComparison.Ordinal));
        Assert.Equal(3, Hints.StepLevel(s, "B08"));
    }

    [Fact]
    public void A_new_step_starts_at_level_zero_and_old_levels_stay_with_their_step()
    {
        var s = TestData.StateAfter("B07") with { Difficulty = Difficulty.Easy };
        for (var i = 0; i < 3; i++) s = Hints.RevealNext(C, s, "M05");
        s = Playback.FinishAll(C, GameRules.CommitAction(C, GameRules.SelectItem(Driver.TravelTo(C, s, "S25"), "TOOLS"), "B08"));
        var step = Hints.CurrentStep(C, s, "M05")!;
        Assert.Equal("B09", step.Id); // first undone step whose guards pass, in quest order
        Assert.Equal(0, Hints.RevealedLevel(C, s, "M05"));
        Assert.Empty(Hints.Revealed(C, s, "M05"));
        Assert.Equal(3, Hints.StepLevel(s, "B08"));
        s = Hints.RevealNext(C, s, "M05");
        Assert.Equal(1, Hints.StepLevel(s, "B09"));
        Assert.Equal("action.B07.objective", Hints.Revealed(C, s, "M05")[0].Text.Key); // B09 needs only B07
    }

    [Fact]
    public void Bag_steps_name_the_bag_and_puzzle_steps_win_while_their_modal_is_open()
    {
        var s = TestData.StateBefore("B10");
        Assert.Equal("B10", Hints.CurrentStep(C, s, "M05")!.Id);
        for (var i = 0; i < 2; i++) s = Hints.RevealNext(C, s, "M05");
        var hints = Hints.Revealed(C, s, "M05");
        Assert.Equal("action.B08.objective", hints[0].Text.Key); // the giver of the connector
        Assert.Equal(Hints.BagKey, hints[1].Text.Key);
        Assert.Empty(hints[1].Args);

        var puzzle = Puzzles.Open(C, TestData.ReadyFor("G11"), "G11");
        Assert.Equal("G11", Hints.CurrentStep(C, puzzle, "M02")!.Id);
    }

    [Fact]
    public void Hints_never_point_at_a_done_step_and_level_three_is_never_the_whole_chain()
    {
        foreach (var state in TestData.MainStates)
        {
            foreach (var quest in C.Quests.Where(q => !state.IsDone(q.Completion)))
            {
                var step = Hints.CurrentStep(C, state, quest.Id);
                Assert.NotNull(step);
                Assert.False(state.IsDone(step!.Id));
                Assert.Contains(step.Id, quest.Actions);
                var s = state with { Difficulty = Difficulty.Easy };
                for (var i = 0; i < 3; i++) s = Hints.RevealNext(C, s, quest.Id);
                var hints = Hints.Revealed(C, s, quest.Id);
                Assert.Equal(3, hints.Count);
                Assert.All(hints, h => Assert.False(h.Text.IsEmpty, $"{quest.Id}/{step.Id} level {h.Level} empty"));
                Assert.All(hints, h => Assert.NotEqual(TextKeys.QuestHint(quest.Id, 3), h.Text.Key));
                // level 3: the written step (ui.hint_step.<id>), or the world overlay's own step text (action.<id>.hint_step)
                Assert.Equal(step.HintStep is null ? Hints.StepKey(step.Id) : TextKeys.ActionHintStep(step.Id), hints[2].Text.Key);
                // a done step is never the direction: the level-1 text is a quest hint or an objective of a done action
                var key = hints[0].Text.Key;
                Assert.True(key.StartsWith("quest." + quest.Id + ".hint.", StringComparison.Ordinal) ||
                            (key.StartsWith("action.", StringComparison.Ordinal) && state.IsDone(key.Split('.')[1])), key);
            }
        }
        Assert.Null(Hints.CurrentStep(C, TestData.StateAfter("G05"), "M01")); // complete quest: no step, no hints
        Assert.Equal(0, Hints.RevealedLevel(C, TestData.StateAfter("G05"), "M01"));
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
