using System.Text.Json.Nodes;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.Save;
using LastBell.Core.State;
using LastBell.Core.Tests.Support;
using LastBell.Core.Text;

namespace LastBell.Core.Tests;

/// <summary>
/// Difficulty settings (docs/DECISIONS.md "Difficulty settings", owner 2026-10-06): Easy = three levels incl. the exact
/// step and the puzzle fill-in; Standard (default) = a nudge and where to look, never the exact step or a fill-in; Hard =
/// only the nudge after three minutes without progress, no puzzle help. Saved per save file, old saves are Standard.
/// </summary>
public sealed class DifficultyTests
{
    private static readonly GameContent C = TestData.Content;

    private static GameState On(GameState s, Difficulty d) => Hints.WithDifficulty(s, d);

    private static GameState RevealAll(GameState s, string questId, double seconds = double.PositiveInfinity)
    {
        for (var i = 0; i < Hints.Levels + 1; i++) s = Hints.RevealNext(C, s, questId, seconds);
        return s;
    }

    [Fact]
    public void A_new_game_and_the_initial_state_are_standard()
    {
        Assert.Equal(Difficulty.Standard, C.InitialState.Difficulty);
        Assert.Equal(Difficulty.Standard, new GameState().Difficulty);
        Assert.Equal(Difficulty.Standard, new GameSession(C).State.Difficulty);
    }

    [Fact]
    public void Levels_per_difficulty()
    {
        var walk = C.GetAction("B08");
        var puzzle = C.GetAction("G11");
        Assert.Equal(3, Hints.MaxLevel(Difficulty.Easy, walk));
        Assert.Equal(2, Hints.MaxLevel(Difficulty.Standard, walk));
        Assert.Equal(1, Hints.MaxLevel(Difficulty.Hard, walk));
        Assert.Equal(3, Hints.MaxLevel(Difficulty.Easy, puzzle));
        Assert.Equal(2, Hints.MaxLevel(Difficulty.Standard, puzzle));
        Assert.Equal(0, Hints.MaxLevel(Difficulty.Hard, puzzle)); // no puzzle help on Hard
        Assert.True(Hints.AllowsPuzzleFill(Difficulty.Easy));
        Assert.False(Hints.AllowsPuzzleFill(Difficulty.Standard));
        Assert.False(Hints.AllowsPuzzleFill(Difficulty.Hard));
    }

    [Fact]
    public void Easy_keeps_todays_three_levels_with_the_exact_step()
    {
        var s = RevealAll(On(TestData.StateAfter("B07"), Difficulty.Easy), "M05");
        var hints = Hints.Revealed(C, s, "M05");
        Assert.Equal(new[] { HintKind.Direction, HintKind.Place, HintKind.Step }, hints.Select(h => h.Kind));
        Assert.All(hints, h => Assert.Null(h.OwnKey));
        Assert.Equal("action.B07.objective", hints[0].Text.Key);
        Assert.Equal(Hints.PlaceKey, hints[1].Text.Key);
        Assert.Equal(Hints.StepKey("B08"), hints[2].Text.Key);
        Assert.Equal(HintGate.AllShown, Hints.Availability(C, s, "M05").Gate);
    }

    [Fact]
    public void Standard_gives_a_nudge_and_where_to_look_and_never_the_step()
    {
        var start = TestData.StateAfter("B07");
        Assert.Equal(Difficulty.Standard, start.Difficulty);
        var first = Hints.Availability(C, start, "M05");
        Assert.True(first.CanReveal);
        Assert.Equal((0, 2), (first.Revealed, first.Max));
        Assert.False(first.NextIsExactStep);

        var s = RevealAll(start, "M05");
        Assert.Equal(2, Hints.StepLevel(s, "B08"));
        Assert.Same(s, Hints.RevealNext(C, s, "M05")); // capped at two
        Assert.Equal(HintGate.AllShown, Hints.Availability(C, s, "M05").Gate);
        var hints = Hints.Revealed(C, s, "M05");
        Assert.Equal(new[] { HintKind.Nudge, HintKind.Where }, hints.Select(h => h.Kind));
        Assert.Equal(new[] { 1, 2 }, hints.Select(h => h.Level));
        Assert.Equal(new[] { "hint.nudge.B08", "hint.where.B08" }, hints.Select(h => h.OwnKey));
        Assert.Equal(Hints.NudgeKey("B08"), hints[0].OwnKey);
        Assert.Equal(Hints.WhereKey("B08"), hints[1].OwnKey);
        // Fallbacks until the writers' texts are approved: the Easy level-1 direction and the level-2 place text.
        var easy = Hints.Revealed(C, RevealAll(On(start, Difficulty.Easy), "M05"), "M05");
        Assert.Equal(easy[0].Text, hints[0].Text);
        Assert.Equal(easy[1].Text, hints[1].Text);
        Assert.Equal(easy[1].Args, hints[1].Args);
        Assert.DoesNotContain(hints, h => h.Text.Key == Hints.StepKey("B08"));
    }

    [Fact]
    public void Standard_never_reveals_an_exact_step_or_the_whole_chain_anywhere_in_the_game()
    {
        foreach (var state in TestData.MainStates)
        {
            foreach (var quest in C.Quests.Where(q => !state.IsDone(q.Completion)))
            {
                var step = Hints.CurrentStep(C, state, quest.Id)!;
                var hints = Hints.Revealed(C, RevealAll(On(state, Difficulty.Standard), quest.Id), quest.Id);
                Assert.Equal(2, hints.Count);
                Assert.All(hints, h => Assert.False(h.Text.IsEmpty, $"{quest.Id}/{step.Id} level {h.Level} empty"));
                Assert.All(hints, h => Assert.NotEqual(Hints.StepKey(step.Id), h.Text.Key));
                Assert.All(hints, h => Assert.NotEqual(TextKeys.ActionHintStep(step.Id), h.Text.Key));
                Assert.All(hints, h => Assert.NotEqual(TextKeys.QuestHint(quest.Id, 3), h.Text.Key)); // the walkthrough hint
                Assert.Equal(new[] { Hints.NudgeKey(step.Id), Hints.WhereKey(step.Id) }, hints.Select(h => h.OwnKey));
            }
        }
    }

    [Fact]
    public void Only_easy_fills_in_a_puzzle_and_a_level_revealed_on_easy_is_capped_after_a_switch()
    {
        var open = Puzzles.Open(C, TestData.ReadyFor("G11"), "G11");
        var standard = RevealAll(open, "M02");
        Assert.Equal(2, Hints.StepLevel(standard, "G11"));
        Assert.False(Puzzles.CanFill(C, standard, "P01"));
        Assert.Same(standard, Puzzles.Fill(C, standard, "P01"));

        var easy = RevealAll(On(open, Difficulty.Easy), "M02");
        Assert.True(Puzzles.CanFill(C, easy, "P01"));
        // Switched to Standard after Easy's level 3: the stored level stays, but only two levels show and no fill-in.
        var switched = On(easy, Difficulty.Standard);
        Assert.Equal(3, Hints.StepLevel(switched, "G11"));
        Assert.Equal(2, Hints.RevealedLevel(C, switched, "M02"));
        Assert.Equal(2, Hints.Revealed(C, switched, "M02").Count);
        Assert.False(Puzzles.CanFill(C, switched, "P01"));
        Assert.Same(switched, Hints.RevealNext(C, switched, "M02"));
        // Back to Easy: everything that was revealed is there again.
        var back = On(switched, Difficulty.Easy);
        Assert.Equal(3, Hints.Revealed(C, back, "M02").Count);
        Assert.True(Puzzles.CanFill(C, back, "P01"));
    }

    [Fact]
    public void Hard_offers_only_the_nudge_after_three_minutes_without_progress()
    {
        var s = On(TestData.StateAfter("B07"), Difficulty.Hard);
        var waiting = Hints.Availability(C, s, "M05", 60);
        Assert.Equal(HintGate.Waiting, waiting.Gate);
        Assert.False(waiting.CanReveal);
        Assert.Equal(Hints.HardWaitSeconds - 60, waiting.WaitSeconds, 3);
        Assert.Equal(Hints.HardWaitSeconds, Hints.Availability(C, s, "M05", 0).WaitSeconds, 3);
        Assert.Same(s, Hints.RevealNext(C, s, "M05", 0));
        Assert.Same(s, Hints.RevealNext(C, s, "M05", Hints.HardWaitSeconds - 0.5));
        Assert.Empty(Hints.Revealed(C, s, "M05"));

        s = Hints.RevealNext(C, s, "M05", Hints.HardWaitSeconds);
        var hints = Hints.Revealed(C, s, "M05");
        Assert.Single(hints);
        Assert.Equal(HintKind.Nudge, hints[0].Kind);
        Assert.Equal(Hints.NudgeKey("B08"), hints[0].OwnKey);
        Assert.Same(s, Hints.RevealNext(C, s, "M05", 10_000)); // only the nudge
        var done = Hints.Availability(C, s, "M05", 0);
        Assert.Equal(HintGate.AllShown, done.Gate); // a revealed nudge stays visible; no new wait for it
        Assert.Equal(0, done.WaitSeconds);
    }

    [Fact]
    public void Hard_gives_no_puzzle_help()
    {
        var open = Puzzles.Open(C, On(TestData.ReadyFor("G11"), Difficulty.Hard), "G11");
        Assert.Equal("G11", Hints.CurrentStep(C, open, "M02")!.Id);
        var available = Hints.Availability(C, open, "M02", 10_000);
        Assert.Equal(HintGate.NoPuzzleHelp, available.Gate);
        Assert.Equal(0, available.Max);
        Assert.Same(open, Hints.RevealNext(C, open, "M02", 10_000));
        Assert.Empty(Hints.Revealed(C, open, "M02"));
        Assert.False(Puzzles.CanFill(C, On(RevealAll(On(open, Difficulty.Easy), "M02"), Difficulty.Hard), "P01"));
    }

    [Fact]
    public void A_complete_quest_has_no_step_on_any_difficulty()
    {
        foreach (var d in Enum.GetValues<Difficulty>())
        {
            var s = On(TestData.StateAfter("G05"), d);
            Assert.Equal(HintGate.NoStep, Hints.Availability(C, s, "M01").Gate);
            Assert.Same(s, Hints.RevealNext(C, s, "M01"));
            Assert.Empty(Hints.Revealed(C, s, "M01"));
        }
    }

    [Fact]
    public void Changing_the_difficulty_never_changes_progress()
    {
        var s = TestData.StateAfter("B07");
        Assert.Same(s, Hints.WithDifficulty(s, Difficulty.Standard));
        foreach (var d in Enum.GetValues<Difficulty>())
        {
            var changed = Hints.WithDifficulty(s, d);
            Assert.Equal(d, changed.Difficulty);
            Assert.Equal(s.Done, changed.Done);
            Assert.Equal(s.Inventory, changed.Inventory);
            Assert.Equal(s.Room, changed.Room);
            Assert.Equal(s.HintLevels, changed.HintLevels);
        }
    }

    [Fact]
    public void Difficulty_is_saved_per_save_file()
    {
        var s = Hints.RevealNext(C, TestData.StateAfter("B07"), "M05");
        foreach (var d in new[] { Difficulty.Easy, Difficulty.Hard })
        {
            var on = On(s, d);
            var json = SaveCodec.Serialize(on);
            Assert.Equal(SaveCodec.DifficultyName(d), JsonNode.Parse(json)!["difficulty"]!.GetValue<string>());
            var loaded = SaveCodec.Load(C, json);
            Assert.Equal(d, loaded.Difficulty);
            Assert.Equal(on, loaded);
            Assert.NotEqual(SaveCodec.Checksum(s), SaveCodec.Checksum(on)); // the difficulty is covered by the checksum
        }
    }

    /// <summary>Saves made before the difficulty settings have no field: they load as Standard, checksum intact.</summary>
    [Fact]
    public void Old_saves_without_the_field_load_as_standard()
    {
        var s = Hints.RevealNext(C, TestData.StateAfter("B07"), "M05");
        var json = SaveCodec.Serialize(s);
        Assert.False(JsonNode.Parse(json)!.AsObject().ContainsKey("difficulty")); // Standard writes no field
        // An old save: the same payload and checksum as before the field existed.
        var old = JsonNode.Parse(json)!.AsObject();
        old.Remove("difficulty");
        var loaded = SaveCodec.Load(C, old.ToJsonString());
        Assert.Equal(Difficulty.Standard, loaded.Difficulty);
        Assert.Equal(s, loaded);
        Assert.Equal(1, Hints.StepLevel(loaded, "B08"));
        // An old save that revealed three levels (old rules) keeps them stored, shows two on Standard.
        var legacy = SaveCodec.ToJsonPayload(s);
        legacy["hint_levels"] = new JsonObject { ["B08"] = 3 };
        var three = SaveCodec.ValidateSave(C, legacy);
        Assert.Equal(Difficulty.Standard, three.Difficulty);
        Assert.Equal(3, Hints.StepLevel(three, "B08"));
        Assert.Equal(2, Hints.Revealed(C, three, "M05").Count);
        // An explicit "standard" is accepted as well.
        var explicitStandard = SaveCodec.ToJsonPayload(s);
        explicitStandard["difficulty"] = "standard";
        Assert.Equal(Difficulty.Standard, SaveCodec.ValidateSave(C, explicitStandard).Difficulty);
    }

    [Fact]
    public void Broken_difficulty_fields_are_rejected()
    {
        var s = TestData.StateAfter("B07");
        foreach (JsonNode bad in new JsonNode[] { "nightmare", "Easy", 1, true, new JsonObject() })
        {
            var payload = SaveCodec.ToJsonPayload(s);
            payload["difficulty"] = bad;
            Assert.Throws<SaveValidationException>(() => SaveCodec.ValidateSave(C, payload));
        }
        var tampered = JsonNode.Parse(SaveCodec.Serialize(On(s, Difficulty.Hard)))!.AsObject();
        tampered["difficulty"] = "easy"; // checksum written for Hard
        Assert.Throws<SaveValidationException>(() => SaveCodec.Load(C, tampered.ToJsonString()));
    }
}
