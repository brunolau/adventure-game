using System.Text.Json.Nodes;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.Save;
using LastBell.Core.State;
using LastBell.Core.Tests.Support;

namespace LastBell.Core.Tests;

/// <summary>Puzzle modals and NPC conversations.</summary>
public sealed class PuzzleAndDialogueTests
{
    private static readonly GameContent C = TestData.Content;

    public static IEnumerable<object[]> PuzzleActions() =>
        new[] { "G11", "B16", "B22", "F16", "D05" }.Select(a => new object[] { a });

    [Theory]
    [MemberData(nameof(PuzzleActions))]
    public void Wrong_answers_cost_nothing_and_the_right_answer_commits_once(string actionId)
    {
        var action = C.GetAction(actionId);
        var puzzle = C.GetPuzzle(action.Puzzle!);
        var start = TestData.ReadyFor(actionId);
        if (action.SelectedItem is not null) start = GameRules.SelectItem(start, action.SelectedItem);
        var s = Puzzles.Open(C, start, actionId);
        Assert.Equal(GameMode.Puzzle, s.Mode);
        Assert.Equal(JsonDeep.ToCanonicalText(puzzle.Initial), JsonDeep.ToCanonicalText(Puzzles.Draft(C, s, puzzle.Id)));
        var wrong = WrongAnswer(puzzle);
        for (var i = 0; i < 10; i++)
        {
            var r = Puzzles.Submit(C, s, actionId, wrong);
            Assert.False(r.Solved);
            Assert.Equal($"puzzle.{puzzle.Id}.wrong", r.Feedback.Key);
            Assert.Equal(start.Inventory, r.State.Inventory);
            Assert.Equal(start.Done, r.State.Done);
            Assert.Equal(GameMode.Puzzle, r.State.Mode);
            s = r.State;
        }
        // Close, save, load: the draft survives but is not "solved".
        s = Puzzles.Close(s);
        var loaded = SaveCodec.Load(C, SaveCodec.Serialize(s));
        Assert.True(JsonDeep.Equals(wrong, Puzzles.Draft(C, loaded, puzzle.Id)));
        Assert.False(loaded.IsDone(actionId));
        // Reset and solve.
        var reopened = Puzzles.Reset(C, Puzzles.Open(C, loaded, actionId), puzzle.Id);
        Assert.Equal(JsonDeep.ToCanonicalText(puzzle.Initial), JsonDeep.ToCanonicalText(Puzzles.Draft(C, reopened, puzzle.Id)));
        var ok = Puzzles.Submit(C, reopened, actionId, puzzle.Solution!.DeepClone());
        Assert.True(ok.Solved);
        Assert.Equal($"puzzle.{puzzle.Id}.success", ok.Feedback.Key);
        Assert.True(ok.State.IsDone(actionId));
        Assert.False(ok.State.PuzzleDrafts.ContainsKey(puzzle.Id));
        Assert.False(Puzzles.Submit(C, ok.State, actionId, puzzle.Solution!.DeepClone()).Solved); // once
    }

    private static JsonNode WrongAnswer(PuzzleDef p) => p.Controls.Type switch
    {
        "matching" => new JsonArray(p.Controls.Left!.Reverse().Select(x => (JsonNode?)JsonValue.Create(x)).ToArray()),
        "rotate_overlay" => PuzzleAnswers.Rotation(90),
        "digits" => PuzzleAnswers.Digits(1, 2, 3),
        "grid_choice" => PuzzleAnswers.Grid(1, 1),
        _ => throw new InvalidOperationException(p.Controls.Type),
    };

    [Fact]
    public void Typed_answers_match_the_data_solutions()
    {
        Assert.True(Puzzles.IsCorrect(C.GetPuzzle("P01"), PuzzleAnswers.Matching("kruh", "trojuholník", "štvorec")));
        Assert.True(Puzzles.IsCorrect(C.GetPuzzle("P02"), PuzzleAnswers.Rotation(180)));
        Assert.True(Puzzles.IsCorrect(C.GetPuzzle("P03"), PuzzleAnswers.Digits(3, 2, 6)));
        Assert.True(Puzzles.IsCorrect(C.GetPuzzle("P04"), PuzzleAnswers.Matching("1960", "1995", "2020", "2035")));
        Assert.True(Puzzles.IsCorrect(C.GetPuzzle("P05"), PuzzleAnswers.Grid(2, 3)));
        Assert.True(Puzzles.IsCorrect(C.GetPuzzle("P05"), JsonNode.Parse("{\"column\":3,\"row\":2.0}")));
        Assert.False(Puzzles.IsCorrect(C.GetPuzzle("P05"), PuzzleAnswers.Grid(3, 2)));
        Assert.False(Puzzles.IsCorrect(C.GetPuzzle("P01"), PuzzleAnswers.Matching("kruh", "trojuholník", null)));
        Assert.False(Puzzles.IsCorrect(C.GetPuzzle("P02"), null));
    }

    [Fact]
    public void Hint_fill_needs_the_third_hint_level_and_still_needs_confirmation()
    {
        var s = Puzzles.Open(C, TestData.ReadyFor("G11"), "G11");
        Assert.False(Puzzles.CanFill(C, s, "P01"));
        for (var i = 0; i < 2; i++) s = Hints.RevealNext(C, s, "M02");
        Assert.False(Puzzles.CanFill(C, s, "P01"));
        s = Hints.RevealNext(C, s, "M02");
        Assert.True(Puzzles.CanFill(C, s, "P01"));
        var filled = Puzzles.Fill(C, s, "P01");
        Assert.False(filled.IsDone("G11"));
        Assert.True(JsonDeep.Equals(C.GetPuzzle("P01").Solution, Puzzles.Draft(C, filled, "P01")));
        Assert.True(Puzzles.Submit(C, filled, "G11", Puzzles.Draft(C, filled, "P01")).Solved);
    }

    [Fact]
    public void Hint_fill_belongs_to_the_puzzle_step_not_to_other_steps_of_the_quest()
    {
        // Three levels revealed on another step of M02 (G06) do not unlock "fill in correctly" for P01.
        var s = TestData.StateAfter("G05");
        for (var i = 0; i < 3; i++) s = Hints.RevealNext(C, s, "M02");
        Assert.Equal(3, Hints.StepLevel(s, "G06"));
        s = s with { Done = TestData.ReadyFor("G11").Done, Inventory = TestData.ReadyFor("G11").Inventory };
        Assert.False(Puzzles.CanFill(C, s, "P01"));
    }

    /// <summary>PT-S17: after a topic the conversation returns to the topic list until it is closed or exhausted.</summary>
    [Fact]
    public void Conversation_returns_to_the_topic_menu_while_topics_are_left()
    {
        var checkedNpcs = 0;
        foreach (var state in TestData.MainStates)
        {
            foreach (var npc in C.GetRoom(state.Room).Hotspots.Where(h => h.IsNpc && GameRules.IsVisible(h, state)))
            {
                var topics = Dialogue.TopicsFor(C, state, npc);
                var back = Dialogue.ReturnToMenu(C, state, npc.Id);
                if (topics.Count > 0)
                {
                    Assert.Equal(GameMode.Dialogue, back.Mode);
                    Assert.Null(back.ActiveLineId);
                    Assert.Equal(state.Done, back.Done);
                    checkedNpcs++;
                }
                else Assert.Equal(state, back); // exhausted: the conversation stays closed
                // never while a line plays, an item is selected or another panel is open
                Assert.Equal(state with { SelectedItem = state.Inventory[0] }, Dialogue.ReturnToMenu(C, state with { SelectedItem = state.Inventory[0] }, npc.Id));
                Assert.Equal(GameMode.Inventory, Dialogue.ReturnToMenu(C, state with { Mode = GameMode.Inventory }, npc.Id).Mode);
            }
            Assert.Equal(state, Dialogue.ReturnToMenu(C, state, "S99.NOBODY"));
        }
        Assert.True(checkedNpcs > 20);

        // A story topic: after its lines the same NPC's menu opens again with the remaining topics.
        var s = Driver.TravelTo(C, TestData.StateBefore("G02"), "S03");
        s = Dialogue.OpenMenu(s);
        s = GameRules.CommitAction(C, s, "G02");
        Assert.Equal(s, Dialogue.ReturnToMenu(C, s, "S03.ELA")); // lines still playing
        s = Playback.FinishAll(C, s);
        Assert.Equal(GameMode.World, s.Mode);
        var reopened = Dialogue.ReturnToMenu(C, s, "S03.ELA");
        Assert.Equal(Dialogue.TopicsFor(C, s, C.FindHotspot("S03.ELA")!.Hotspot).Count > 0 ? GameMode.Dialogue : GameMode.World, reopened.Mode);
    }

    [Fact]
    public void Puzzles_open_only_for_a_valid_action()
    {
        Assert.Same(C.InitialState, Puzzles.Open(C, C.InitialState, "G11"));
        Assert.Same(C.InitialState, Puzzles.Open(C, C.InitialState, "G01")); // no puzzle
        Assert.All(C.Data.Puzzles, p => Assert.True(p.NoTimer));
    }

    [Fact]
    public void Ambient_topics_repeat_without_state_change()
    {
        var s = Driver.TravelTo(C, TestData.StateAfter("G01"), "S03");
        var heard = Dialogue.StartTopic(C, s, "ELA.ambient 1");
        Assert.Equal(GameMode.Dialogue, heard.Mode);
        Assert.Equal("topic.ELA.ambient 1.001", heard.ActiveLineId);
        heard = Playback.FinishAll(C, heard);
        Assert.Equal(s.Done, heard.Done);
        Assert.Equal(s.Inventory, heard.Inventory);
        Assert.Contains("topic.ELA.ambient 1", heard.JournalSeen);
        var again = Dialogue.TopicsFor(C, heard, C.FindHotspot("S03.ELA")!.Hotspot);
        Assert.Contains(again, t => t.Id == "ELA.ambient 1");
        // Not offered in a room without the character.
        Assert.Same(C.InitialState, Dialogue.StartTopic(C, C.InitialState, "ELA.ambient 1"));
    }

    [Fact]
    public void Gated_ambient_topics_appear_only_after_their_requirement()
    {
        var mira = C.FindHotspot("S06.MIRA20")!.Hotspot;
        Assert.DoesNotContain(Dialogue.TopicsFor(C, TestData.StateBefore("F17"), mira), t => t.Id == "MIRA20.after");
        Assert.Contains(Dialogue.TopicsFor(C, TestData.MainEnd, mira), t => t.Id == "MIRA20.after");
    }

    [Fact]
    public void Done_story_topics_leave_the_menu_and_go_to_the_transcript()
    {
        var before = Driver.TravelTo(C, TestData.StateAfter("G01"), "S03");
        var ela = C.FindHotspot("S03.ELA")!.Hotspot;
        Assert.Contains(Dialogue.TopicsFor(C, before, ela), t => t.Id == "G02");
        var after = Playback.FinishAll(C, GameRules.CommitAction(C, Dialogue.OpenMenu(before), "G02"));
        Assert.DoesNotContain(Dialogue.TopicsFor(C, after, ela), t => t.Id == "G02");
        var transcript = Dialogue.Transcript(C, after, "ELA");
        Assert.Contains(transcript, e => e.SourceId == "G02");
        Assert.Contains(Dialogue.MetCharacters(C, after), c => c.Id == "ELA");
        // Repeating the conversation never gives ORDER again.
        Assert.False(GameRules.TryCommitAction(C, after, "G02").Success);
        Assert.Single(after.Inventory, "ORDER");
    }

    [Fact]
    public void Topic_menu_opens_and_closes()
    {
        var s = Dialogue.OpenMenu(C.InitialState);
        Assert.Equal(GameMode.Dialogue, s.Mode);
        Assert.Null(s.ActiveLineId);
        Assert.Equal(GameMode.World, Dialogue.CloseMenu(s).Mode);
        Assert.Equal(GameMode.World, GameRules.CloseOverlay(s).Mode);
    }
}
