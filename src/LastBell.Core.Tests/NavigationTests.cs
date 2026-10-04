using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Tests.Support;

namespace LastBell.Core.Tests;

/// <summary>Connections, portals, era unlocks, fast travel and first-entry lines.</summary>
public sealed class NavigationTests
{
    private static readonly GameContent C = TestData.Content;

    [Fact]
    public void Connected_rooms_follow_open_gates_only()
    {
        var reachable = Navigation.ConnectedRooms(C, C.InitialState, includePortals: true);
        Assert.Contains("S05", reachable);
        Assert.DoesNotContain("S06", reachable); // S05->S06 needs G04
        Assert.DoesNotContain("S09", reachable); // needs G06
        Assert.All(reachable, r => Assert.Equal(2020, C.GetRoom(r).Era));
    }

    [Fact]
    public void Eras_unlock_by_their_actions()
    {
        Assert.Equal(new[] { 2020 }, Navigation.UnlockedEras(C, C.InitialState).Select(e => e.Year));
        Assert.Equal(new[] { 2020, 1995 }, Navigation.UnlockedEras(C, TestData.StateAfter("G11")).Select(e => e.Year));
        Assert.Equal(5, Navigation.UnlockedEras(C, TestData.MainEnd).Count);
    }

    [Fact]
    public void Portals_need_the_chronometer_an_open_anchor_node_and_an_unlocked_era()
    {
        var s = TestData.StateAfter("G11"); // in S11 (1995 anchor)
        Assert.Equal(new[] { 2020 }, Navigation.PortalTargets(C, s).Select(p => p.Year));
        var without = s with { Inventory = s.Inventory.Remove(GameContent.ChronometerItem) };
        Assert.Empty(Navigation.PortalTargets(C, without));
        var back = Playback.FinishAll(C, Navigation.UsePortal(C, s, 2020));
        Assert.Equal("S10", back.Room);
        Assert.Equal(2020, back.Era);
        Assert.Equal(s.Inventory, back.Inventory);
        Assert.Same(s, Navigation.UsePortal(C, s, 1960)); // locked era
        var notAnchor = Driver.TravelTo(C, s, "S12");
        Assert.Empty(Navigation.PortalTargets(C, notAnchor));
    }

    [Fact]
    public void Returning_to_every_unlocked_era_keeps_inventory_and_a_way_back()
    {
        var s = TestData.MainEnd;
        foreach (var era in C.Eras)
        {
            foreach (var other in C.Eras.Where(e => e.Year != era.Year))
            {
                var there = Driver.TravelTo(C, s, era.Anchor);
                var jumped = Playback.FinishAll(C, Navigation.UsePortal(C, there, other.Year));
                Assert.Equal(other.Anchor, jumped.Room);
                Assert.Equal(s.Inventory.OrderBy(x => x), jumped.Inventory.OrderBy(x => x));
                Assert.Equal(s.Done, jumped.Done);
                Assert.NotNull(Navigation.FindRoute(C, jumped, era.Anchor));
            }
        }
    }

    [Fact]
    public void Fast_travel_only_from_the_map_to_visited_reachable_rooms_of_the_same_era()
    {
        var s = Driver.TravelTo(C, TestData.StateAfter("G05"), "S01"); // S06 visited, S05->S06 open
        Assert.Contains("S06", s.Visited);
        Assert.False(Navigation.CanFastTravel(C, s, "S06")); // not in map mode
        var map = GameRules.OpenOverlay(s, GameMode.Map);
        Assert.True(Navigation.CanFastTravel(C, map, "S06"));
        var moved = Navigation.FastTravel(C, map, "S06");
        Assert.Equal("S06", moved.Room);
        Assert.Equal(GameMode.World, moved.Mode);
        Assert.False(Navigation.CanFastTravel(C, map, "S09")); // never visited, gate G06 closed
        // A forged "visited" entry still cannot bypass the gate.
        var forged = map with { Visited = map.Visited.Add("S09") };
        Assert.False(Navigation.CanFastTravel(C, forged, "S09"));
        // Other eras are never fast-travel targets.
        var later = GameRules.OpenOverlay(Driver.TravelTo(C, TestData.StateAfter("B03"), "S12"), GameMode.Map);
        Assert.False(Navigation.CanFastTravel(C, later, "S01"));
    }

    [Fact]
    public void First_visit_plays_first_entry_lines_once()
    {
        var s = Navigation.Travel(C, C.InitialState, "S01.to_S02");
        Assert.Equal(GameMode.Dialogue, s.Mode);
        Assert.Equal(C.GetRoom("S02").FirstEntry[0].LineId, s.ActiveLineId);
        s = Playback.FinishAll(C, s);
        var back = Navigation.Travel(C, s, C.GetRoom("S02").Exits.First(e => e.To == "S01").Id);
        Assert.Equal(GameMode.World, Playback.FinishAll(C, back).Mode);
        var again = Navigation.Travel(C, Playback.FinishAll(C, back), "S01.to_S02");
        Assert.Null(again.ActiveLineId); // S02 already visited
    }

    [Fact]
    public void Travel_is_refused_outside_world_mode()
    {
        var s = C.InitialState with { Mode = GameMode.Dialogue };
        Assert.Same(s, Navigation.Travel(C, s, "S01.to_S02"));
    }

    [Fact]
    public void Routes_use_exits_and_portals_and_fail_for_unreachable_rooms()
    {
        Assert.Null(Navigation.FindRoute(C, C.InitialState, "S11"));
        Assert.Empty(Navigation.FindRoute(C, C.InitialState, "S01")!);
        var s = TestData.StateAfter("G11");
        var route = Navigation.FindRoute(C, s, "S01")!;
        Assert.Equal(RouteStepKind.Portal, route[0].Kind);
        Assert.Equal("S01", route[^1].To);
    }

    [Fact]
    public void Jasna_has_no_bypass_to_the_rotunda_before_the_first_ride()
    {
        var s = TestData.ReadyFor("J02");
        Assert.Equal("S41", s.Room);
        Assert.DoesNotContain("S47", Navigation.ConnectedRooms(C, s, includePortals: true));
        Assert.DoesNotContain("S67", Navigation.ConnectedRooms(C, s, includePortals: true));
        var after = TestData.StateAfter("J04");
        Assert.Equal("S47", after.Room);
        Assert.Contains("LIFT_TICKET", after.Inventory); // the ticket is not consumed
        var down = Driver.TravelTo(C, after, "S41");
        Assert.Equal("S41", down.Room);
        Assert.NotNull(Navigation.FindRoute(C, down, "S47"));
    }

    [Fact]
    public void Lifts_keep_working_after_atlas_is_switched_off()
    {
        var s = TestData.StateAfter("F09");
        Assert.True(s.IsDone("J05"));
        var down = Driver.TravelTo(C, Driver.TravelTo(C, s, "S47"), "S41");
        Assert.Equal("S41", down.Room);
        Assert.NotNull(Navigation.FindRoute(C, down, "S50"));
        Assert.NotNull(Navigation.FindRoute(C, TestData.MainEnd, "S68"));
    }
}
