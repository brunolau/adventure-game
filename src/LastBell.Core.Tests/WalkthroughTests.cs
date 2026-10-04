using System.Collections.Immutable;
using LastBell.Core.Rules;
using LastBell.Core.Save;
using LastBell.Core.State;
using LastBell.Core.Tests.Support;

namespace LastBell.Core.Tests;

/// <summary>End-to-end replays through the public API (walkthrough, postgame, random orders, final ports).</summary>
public sealed class WalkthroughTests
{
    private static readonly Content.GameContent C = TestData.Content;

    [Fact]
    public void MainRoute_replays_all_94_steps_with_exact_inventory_and_room()
    {
        Assert.Equal(94, TestData.MainRoute.Count);
        var s = C.InitialState;
        foreach (var row in TestData.MainRoute)
        {
            s = Driver.FollowTravelPath(C, s, row.TravelPath);
            s = Driver.Interact(C, s, C.GetAction(row.Action), row.PuzzleSolution);
            Assert.Equal(row.InventoryAfter, s.Inventory.OrderBy(x => x, StringComparer.Ordinal).ToList());
            Assert.Equal(row.RoomAfter, s.Room);
            Driver.AssertInvariants(C, s);
        }
        Assert.True(s.IsDone("F17"));
        Assert.All(s.Done, id => Assert.Equal("main", C.GetAction(id).Quest));
        Assert.All(C.Data.Postgame.ReturnItems, item => Assert.Contains(item, s.Inventory));
        Assert.True(Postgame.IsActive(C, s));
        Assert.Empty(s.SideRewards);
    }

    [Fact]
    public void Every_side_quest_is_completable_after_the_credits()
    {
        var s = TestData.MainEnd;
        Assert.Equal(33, TestData.OptionalRoute.Count);
        foreach (var id in TestData.OptionalRoute)
        {
            s = Driver.Perform(C, s, C.GetAction(id));
            Driver.AssertInvariants(C, s);
        }
        Assert.Equal(C.Actions.Count, s.Done.Length);
        Assert.Equal(9, s.SideRewards.Length);
        Assert.All(C.Quests, q => Assert.Equal(QuestStatus.Done, Quests.StatusOf(q, s)));
        // All 68 rooms remain reachable in the postgame.
        var reachable = Navigation.ConnectedRooms(C, s, includePortals: true);
        Assert.All(C.Rooms, r => Assert.Contains(r.Id, reachable));
        // New epilogue shots are added without repeating the final transaction.
        Assert.Equal(9, Epilogue.Select(C, s).Count);
        Assert.False(GameRules.ValidAction(C, s, C.GetAction("F17")));
    }

    public static IEnumerable<object[]> Seeds() => Enumerable.Range(0, 120).Select(i => new object[] { i });

    [Theory]
    [MemberData(nameof(Seeds))]
    public void Random_legal_order_completes_every_action(int seed)
    {
        var rng = new Random(seed);
        var s = C.InitialState;
        for (var i = 0; i <= C.Actions.Count; i++)
        {
            var options = Driver.Enabled(C, s);
            if (options.Count == 0) break;
            s = Driver.Perform(C, s, options[rng.Next(options.Count)]);
            Driver.AssertInvariants(C, s);
        }
        Assert.Equal(C.Actions.Count, s.Done.Length);
    }

    public static IEnumerable<object[]> PortPermutations()
    {
        var ports = new[] { "F12", "F13", "F14", "F15" };
        IEnumerable<IEnumerable<string>> Permute(IEnumerable<string> xs) =>
            !xs.Any() ? new[] { Enumerable.Empty<string>() } : xs.SelectMany(x => Permute(xs.Where(y => y != x)).Select(p => new[] { x }.Concat(p)));
        return Permute(ports).Select(p => new object[] { string.Join(",", p) });
    }

    [Theory]
    [MemberData(nameof(PortPermutations))]
    public void Final_ports_in_any_order_reach_the_ending(string order)
    {
        var s = TestData.StateBefore("F12");
        var seq = order.Split(',');
        Assert.Equal(4, seq.Distinct().Count());
        foreach (var id in seq)
        {
            Assert.False(GameRules.GuardsPass(C.GetAction("F16"), s), "F16 must not unlock before all four ports");
            var action = C.GetAction(id);
            var consumed = action.Consumes.ToList();
            s = Driver.Perform(C, s, action);
            Assert.All(consumed, item => Assert.DoesNotContain(item, s.Inventory));
            Assert.Null(s.SelectedItem);
        }
        Assert.True(GameRules.GuardsPass(C.GetAction("F16"), s));
        s = Driver.Perform(C, s, C.GetAction("F16"));
        s = Driver.Perform(C, s, C.GetAction("F17"));
        Assert.True(s.IsDone("F17"));
        Assert.Equal("S06", s.Room);
        Assert.All(C.Data.Postgame.ReturnItems, item => Assert.Contains(item, s.Inventory));
    }

    [Fact]
    public void Save_load_roundtrip_at_every_walkthrough_step_and_mid_dialogue()
    {
        var s = C.InitialState;
        foreach (var row in TestData.MainRoute)
        {
            s = Driver.FollowTravelPath(C, s, row.TravelPath);
            var action = C.GetAction(row.Action);
            // Commit, then save in the middle of the lines (before they are played).
            var mid = action.Puzzle is null
                ? GameRules.CommitAction(C, s, action.Id)
                : GameRules.CommitAction(C, Puzzles.Open(C, s, action.Id), action.Id, row.PuzzleSolution);
            var midLoaded = SaveCodec.Load(C, SaveCodec.Serialize(mid));
            Assert.Equal(mid, midLoaded);
            Assert.Equal(mid.ActiveLineId, midLoaded.ActiveLineId);
            // Re-committing after the load is impossible: no second reward.
            Assert.False(GameRules.TryCommitAction(C, midLoaded, action.Id, row.PuzzleSolution).Success);
            s = GameRules.CancelSelection(Playback.FinishAll(C, midLoaded));
            var json = SaveCodec.Serialize(s);
            var loaded = SaveCodec.Load(C, json);
            Assert.Equal(s, loaded);
            Assert.Equal(json, SaveCodec.Serialize(loaded));
            Assert.Equal(row.InventoryAfter, loaded.Inventory.OrderBy(x => x, StringComparer.Ordinal).ToList());
        }
    }

    [Fact]
    public void Main_states_are_reproducible_and_immutable()
    {
        var states = TestData.MainStates;
        Assert.Equal(95, states.Count);
        Assert.Empty(states[0].Done);
        for (var i = 1; i < states.Count; i++)
        {
            Assert.Equal(i, states[i].Done.Length);
            Assert.Equal(states[i - 1].Done, states[i].Done.RemoveAt(i - 1));
        }
        Assert.Equal(ImmutableArray.Create("PHONE"), C.InitialState.Inventory);
    }
}
