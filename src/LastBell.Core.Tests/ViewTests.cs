using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Tests.Support;
using LastBell.Core.Views;

namespace LastBell.Core.Tests;

/// <summary>View models for the Godot presentation and the session wrapper.</summary>
public sealed class ViewTests
{
    private static readonly GameContent C = TestData.Content;

    [Fact]
    public void Room_view_lists_visible_hotspots_exits_and_accessible_order()
    {
        var view = ViewBuilder.Room(C, C.InitialState);
        Assert.Equal("S01", view.RoomId);
        Assert.Equal("room.S01.name", view.Name.Key);
        Assert.Equal("bg/S01.webp", view.BackgroundAsset);
        Assert.Contains(view.Hotspots, h => h.Id == "S01.tools" && !h.IsAtmospheric);
        Assert.Contains(view.Hotspots, h => h.Id == "S01.ambient 1" && h.IsAtmospheric);
        Assert.Single(view.Exits);
        Assert.Equal(view.Exits[0].Id, view.AccessibleOrder[^1]);
        var after = ViewBuilder.Room(C, TestData.StateAfter("G01"));
        Assert.DoesNotContain(after.Hotspots, h => h.Id == "S01.tools");
    }

    [Fact]
    public void Accessible_order_is_npcs_progress_atmospheric_exits()
    {
        var s = Driver.TravelTo(C, TestData.StateAfter("G01"), "S03");
        var view = ViewBuilder.Room(C, s);
        var kinds = view.AccessibleOrder.Select(id =>
            view.Hotspots.FirstOrDefault(h => h.Id == id) is { } h ? (h.IsNpc ? 0 : h.IsAtmospheric ? 2 : 1) : 3).ToList();
        Assert.Equal(kinds.OrderBy(k => k), kinds);
        Assert.Equal(view.Hotspots.Count + view.Exits.Count, view.AccessibleOrder.Count);
        Assert.Contains(view.Npcs, n => n.CharacterId == "ELA");
    }

    [Fact]
    public void Valid_item_targets_are_flagged_for_a_subtle_outline()
    {
        var s = GameRules.SelectItem(TestData.ReadyFor("G10"), "FUSE");
        var view = ViewBuilder.Room(C, s);
        Assert.True(view.Hotspots.Single(h => h.Id == "S10.chrono").ValidForSelectedItem);
        Assert.All(view.Hotspots.Where(h => h.Id != "S10.chrono"), h => Assert.False(h.ValidForSelectedItem));
    }

    [Fact]
    public void Portal_targets_are_part_of_the_anchor_room_view()
    {
        var view = ViewBuilder.Room(C, TestData.StateAfter("G11"));
        Assert.Contains(view.PortalTargets, p => p.Year == 2020);
    }

    [Fact]
    public void Inventory_view_marks_selection_and_archives_used_up_items()
    {
        var s = GameRules.SelectItem(TestData.StateAfter("G01"), "TOOLS");
        var inv = ViewBuilder.Inventory(C, s);
        Assert.True(inv.Single(i => i.Id == "TOOLS").IsSelected);
        Assert.False(inv.Single(i => i.Id == "TOOLS").IsArchived);
        var end = ViewBuilder.Inventory(C, TestData.MainEnd);
        Assert.False(end.Single(i => i.Id == GameContent.ChronometerItem).IsArchived);
        Assert.Contains(end, i => i.IsArchived);
        // Archived items still satisfy requirements.
        Assert.True(TestData.MainEnd.Has(end.First(i => i.IsArchived).Id));
    }

    [Fact]
    public void Map_view_greys_unvisited_rooms_and_flags_fast_travel()
    {
        var s = GameRules.OpenOverlay(Driver.TravelTo(C, TestData.StateAfter("G05"), "S01"), GameMode.Map);
        var map = ViewBuilder.Map(C, s);
        Assert.Equal(5, map.Count);
        var era2020 = map.Single(m => m.Year == 2020);
        Assert.True(era2020.Unlocked);
        Assert.False(map.Single(m => m.Year == 1995).Unlocked);
        Assert.True(era2020.Rooms.Single(r => r.RoomId == "S06").CanFastTravel);
        Assert.False(era2020.Rooms.Single(r => r.RoomId == "S09").Visited);
        Assert.True(era2020.Rooms.Single(r => r.RoomId == "S10").IsAnchor);
    }

    [Fact]
    public void Session_applies_resolutions_and_raises_events()
    {
        var session = new GameSession(C);
        var events = 0;
        session.StateChanged += (_, _) => events++;
        session.Apply(session.Resolve(new Hit.Hotspot("S01.tools"), PointerButton.Left));
        Assert.True(session.State.IsDone("G01"));
        session.Update(s => Playback.FinishAll(C, s));
        session.Apply(session.Resolve(new Hit.Empty(), PointerButton.Right));
        Assert.Equal(GameMode.Inventory, session.State.Mode);
        session.Apply(session.Resolve(new Hit.Item("TOOLS"), PointerButton.Left));
        Assert.Equal("TOOLS", session.State.SelectedItem);
        Assert.Equal(GameMode.World, session.State.Mode);
        session.Apply(session.Resolve(new Hit.Floor(1, 1), PointerButton.Right));
        Assert.Null(session.State.SelectedItem);
        Assert.Equal(5, events);
        Assert.False(session.Commit("G01"));
        Assert.Equal("room.S01.name", session.Room().Name.Key);
    }
}
