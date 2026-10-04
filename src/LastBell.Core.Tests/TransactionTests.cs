using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Tests.Support;

namespace LastBell.Core.Tests;

/// <summary>Guards, atomic commit, playback independence and the TS reference functions.</summary>
public sealed class TransactionTests
{
    private static readonly GameContent C = TestData.Content;

    [Fact]
    public void IsVisible_requires_all_visible_after_and_hides_on_any_hide_after()
    {
        var tools = C.FindHotspot("S01.tools")!.Hotspot;
        Assert.True(GameRules.IsVisible(tools, C.InitialState));
        Assert.False(GameRules.IsVisible(tools, C.InitialState with { Done = ["G01"] }));
        var cache = C.FindHotspot("S55.cache")!.Hotspot;
        Assert.False(GameRules.IsVisible(cache, C.InitialState));
        Assert.True(GameRules.IsVisible(cache, C.InitialState with { Done = ["E10"] }));
        Assert.False(GameRules.IsVisible(cache, C.InitialState with { Done = ["E10", "D05"] }));
    }

    [Fact]
    public void LookAt_evaluates_variants_from_last_to_first_with_base_fallback()
    {
        var photo = C.FindHotspot("S06.photo")!.Hotspot;
        Assert.Equal("look.S06.photo", GameRules.LookAt(photo, C.InitialState).Key);
        Assert.Equal("look.S06.photo.variant1", GameRules.LookAt(photo, C.InitialState with { Done = ["G11"] }).Key);
        Assert.Equal("look.S06.photo.variant2", GameRules.LookAt(photo, C.InitialState with { Done = ["G11", "C04"] }).Key);
        Assert.Equal("look.S06.photo.variant3", GameRules.LookAt(photo, C.InitialState with { Done = ["C04", "F17", "G11"] }).Key);
    }

    [Fact]
    public void GuardsPass_checks_done_excluded_prerequisites_and_items()
    {
        var g02 = C.GetAction("G02");
        Assert.False(GameRules.GuardsPass(g02, C.InitialState)); // needs G01
        Assert.True(GameRules.GuardsPass(g02, C.InitialState with { Done = ["G01"] }));
        Assert.False(GameRules.GuardsPass(g02, C.InitialState with { Done = ["G01", "G02"] })); // once
        var excluded = g02 with { ExcludedDone = ["G01"] };
        Assert.False(GameRules.GuardsPass(excluded, C.InitialState with { Done = ["G01"] }));
        var g03 = C.GetAction("G03");
        Assert.False(GameRules.GuardsPass(g03, C.InitialState)); // ORDER missing
        Assert.True(GameRules.GuardsPass(g03, C.InitialState with { Inventory = ["PHONE", "ORDER"] }));
    }

    [Fact]
    public void ValidAction_requires_room_and_visible_target_but_inventory_actions_work_anywhere()
    {
        var s = TestData.StateAfter("G01");
        Assert.False(GameRules.ValidAction(C, s, C.GetAction("G02"))); // wrong room
        Assert.True(GameRules.ValidAction(C, Driver.TravelTo(C, s, "S03"), C.GetAction("G02")));
        var b10 = C.GetAction("B10");
        var before = TestData.StateBefore("B10");
        Assert.True(GameRules.ValidAction(C, before, b10));
        Assert.True(GameRules.ValidAction(C, Driver.TravelTo(C, before, "S11"), b10));
    }

    [Fact]
    public void Commit_gives_items_exactly_once_and_records_journal()
    {
        var s = GameRules.CommitAction(C, C.InitialState, "G01");
        Assert.Equal(new[] { "PHONE", "TOOLS" }, s.Inventory);
        Assert.Equal(new[] { "G01" }, s.Done);
        Assert.Contains("action.G01", s.JournalSeen);
        Assert.Equal(GameMode.Dialogue, s.Mode);
        Assert.Equal("action.G01.001", s.ActiveLineId);
        var again = Assert.Throws<ActionRejectedException>(() => GameRules.CommitAction(C, s, "G01"));
        Assert.Equal(ActionRejection.NoLongerValid, again.Reason);
        Assert.Equal(ActionRejection.UnknownAction, Assert.Throws<ActionRejectedException>(() => GameRules.CommitAction(C, s, "NOPE")).Reason);
    }

    [Fact]
    public void Commit_consumes_and_clears_a_consumed_selection()
    {
        var before = TestData.ReadyFor("G04");
        var selected = GameRules.SelectItem(before, "GROCERIES");
        var s = GameRules.CommitAction(C, selected, "G04");
        Assert.DoesNotContain("GROCERIES", s.Inventory);
        Assert.Null(s.SelectedItem);
        // A retained selected item stays selected.
        var g08 = TestData.ReadyFor("G08");
        var kept = GameRules.CommitAction(C, GameRules.SelectItem(g08, "TOOLS"), "G08");
        Assert.Equal("TOOLS", kept.SelectedItem);
    }

    [Fact]
    public void Commit_rejects_an_invalid_item_transaction_without_changing_state()
    {
        // A forged state already owning the given item.
        var forged = C.InitialState with { Inventory = ["PHONE", "TOOLS"] };
        var result = GameRules.TryCommitAction(C, forged, "G01");
        Assert.False(result.Success);
        Assert.Equal(ActionRejection.InvalidItemTransaction, result.Rejection);
        Assert.Same(forged, result.State);
    }

    [Fact]
    public void Puzzle_actions_need_the_exact_solution_and_reject_without_change()
    {
        var s = TestData.StateBefore("G11");
        Assert.Equal(ActionRejection.PuzzleNotSolved, GameRules.TryCommitAction(C, s, "G11").Rejection);
        Assert.Equal(ActionRejection.PuzzleNotSolved, GameRules.TryCommitAction(C, s, "G11", PuzzleAnswers.Matching("kruh", "štvorec", "trojuholník")).Rejection);
        var ok = GameRules.TryCommitAction(C, s, "G11", PuzzleAnswers.Matching("kruh", "trojuholník", "štvorec"));
        Assert.True(ok.Success);
    }

    [Fact]
    public void Special_transition_is_part_of_the_same_transaction()
    {
        var s = GameRules.CommitAction(C, TestData.StateBefore("G11"), "G11", PuzzleAnswers.Matching("kruh", "trojuholník", "štvorec"));
        Assert.Equal("S11", s.Room);
        Assert.Equal(1995, s.Era);
        Assert.Contains("S11", s.Visited);
        Assert.Equal(s.Done.Length, s.RoomEntryDoneCount);
        // Lines first, then the cutscene, then the first-entry lines of S11.
        var queue = new[] { s.ActiveLineId! }.Concat(s.PlaybackQueue).ToList();
        var g11Lines = C.GetAction("G11").Lines.Select(l => l.LineId!).ToList();
        var cs = Playback.CutsceneLineIds(C.FindCutscene("CS01")!).ToList();
        var entry = C.GetRoom("S11").FirstEntry.Select(l => l.LineId!).ToList();
        Assert.Equal(g11Lines.Concat(cs).Concat(entry), queue);
    }

    [Fact]
    public void Skipping_cutscenes_gives_the_same_rule_state_as_watching_them()
    {
        foreach (var id in new[] { "G11", "B12", "B22", "I17", "C05", "F11", "F17", "E10", "J02" })
        {
            var before = TestData.ReadyFor(id);
            var row = TestData.MainRoute.Single(r => r.Action == id);
            var committed = GameRules.CommitAction(C, Puzzles.Open(C, before, id) is var p && p.Mode == GameMode.Puzzle ? p : before, id, row.PuzzleSolution);
            var watched = Playback.FinishAll(C, committed);
            var skipped = committed;
            var guard = 0;
            while (skipped.ActiveLineId is not null && guard++ < 1000)
                skipped = Playback.Current(C, skipped)!.IsCutscene ? Playback.SkipCutscene(C, skipped) : Playback.Advance(C, skipped);
            Assert.Equal(watched, skipped);
            Assert.Equal(watched, Playback.SkipAll(committed));
        }
    }

    [Fact]
    public void Playback_cursor_walks_lines_and_switches_modes()
    {
        var s = GameRules.CommitAction(C, TestData.StateBefore("G11"), "G11", PuzzleAnswers.Matching("kruh", "trojuholník", "štvorec"));
        var current = Playback.Current(C, s)!;
        Assert.Equal(LineSource.Action, current.Source);
        Assert.Equal("char." + C.GetAction("G11").Lines[0].Speaker + ".name", current.Speaker.Key);
        while (Playback.Current(C, s)!.Source == LineSource.Action) s = Playback.Advance(C, s);
        Assert.Equal(GameMode.Cutscene, s.Mode);
        Assert.True(Playback.Current(C, s)!.IsCutscene);
        s = Playback.SkipCutscene(C, s);
        Assert.Equal(LineSource.FirstEntry, Playback.Current(C, s)!.Source);
        Assert.Equal(GameMode.Dialogue, s.Mode);
        s = Playback.FinishAll(C, s);
        Assert.Equal(GameMode.World, s.Mode);
        Assert.Null(Playback.Current(C, s));
    }

    [Fact]
    public void Postgame_unlock_returns_the_evidence_in_the_same_transaction()
    {
        var before = TestData.StateBefore("F17");
        Assert.All(C.Data.Postgame.ReturnItems, i => Assert.DoesNotContain(i, before.Inventory));
        var s = GameRules.CommitAction(C, before, "F17");
        Assert.All(C.Data.Postgame.ReturnItems, i => Assert.Contains(i, s.Inventory));
        Assert.Equal("S06", s.Room);
    }

    [Fact]
    public void Side_rewards_are_recomputed_on_commit()
    {
        var s = TestData.MainEnd;
        foreach (var id in new[] { "Q1A", "Q1B" }) s = Driver.Perform(C, s, C.GetAction(id));
        Assert.Empty(s.SideRewards);
        s = Driver.Perform(C, s, C.GetAction("Q1C"));
        Assert.Equal(new[] { "Q1" }, s.SideRewards);
    }

    [Fact]
    public void Next_main_quest_follows_the_lowest_available_group()
    {
        Assert.Equal("M01", GameRules.NextMainQuest(C, C.InitialState)!.Id);
        Assert.Equal("M02", GameRules.NextMainQuest(C, TestData.StateAfter("G05"))!.Id);
        Assert.Null(GameRules.NextMainQuest(C, TestData.MainEnd));
    }

    [Fact]
    public void States_are_immutable_values()
    {
        var a = C.InitialState;
        var b = GameRules.CommitAction(C, a, "G01");
        Assert.Empty(a.Done);
        Assert.Equal(new[] { "PHONE" }, a.Inventory);
        Assert.NotEqual(a, b);
        Assert.Equal(a, a with { });
    }

    [Fact]
    public void Available_actions_lists_only_valid_actions_for_the_debug_panel()
    {
        Assert.Equal(new[] { "G01" }, GameRules.AvailableActions(C, C.InitialState).Select(a => a.Id));
    }
}
