using System.Text.Json.Nodes;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Tests.Support;
using LastBell.Core.Text;

namespace LastBell.Core.Tests;

/// <summary>
/// The binding control rules of CODING_AGENT_START.txt and PRIBEH_A_PRAVIDLA.txt (mouse, Space,
/// hover, invalid item click, shared resolver, re-check after walking, modes).
/// </summary>
public sealed class ControlRulesTests
{
    private static readonly GameContent C = TestData.Content;

    private static Resolution Left(GameState s, Hit hit) => GameRules.ResolveInteraction(C, s, hit, PointerButton.Left);
    private static Resolution Right(GameState s, Hit hit) => GameRules.ResolveInteraction(C, s, hit, PointerButton.Right);

    /// <summary>State in S10 after G09 (FUSE owned, service cover open) — the "insert fuse" example of the bible.</summary>
    private static GameState WithFuseAtCradle() => TestData.ReadyFor("G10");

    // ---- left click: one logical action, no verbs

    [Fact]
    public void Left_click_on_a_progress_prop_resolves_to_its_single_action()
    {
        var r = Assert.IsType<Resolution.Action>(Left(C.InitialState, new Hit.Hotspot("S01.tools")));
        Assert.Equal("G01", r.ActionDef.Id);
    }

    [Fact]
    public void Left_click_on_an_atmospheric_prop_plays_its_look()
    {
        var r = Assert.IsType<Resolution.Look>(Left(C.InitialState, new Hit.Hotspot("S01.ambient 1")));
        Assert.Equal("look.S01.ambient 1", r.Text.Key);
    }

    [Fact]
    public void Left_click_on_a_progress_prop_without_available_action_only_looks()
    {
        // S01.fuse has G09 which needs G08 first.
        var r = Assert.IsType<Resolution.Look>(Left(C.InitialState, new Hit.Hotspot("S01.fuse")));
        Assert.Equal("look.S01.fuse", r.Text.Key);
    }

    [Fact]
    public void Left_click_on_npc_opens_topics_with_story_and_ambient_topics()
    {
        var s = Driver.TravelTo(C, TestData.StateAfter("G01"), "S03");
        var d = Assert.IsType<Resolution.Dialogue>(Left(s, new Hit.Hotspot("S03.ELA")));
        Assert.Equal("ELA", d.CharacterId);
        Assert.Contains(d.Topics, t => t.Id == "G02" && t.IsStoryAction);
        Assert.Contains(d.Topics, t => t.Id == "ELA.ambient 1" && !t.IsStoryAction);
        // Item actions on NPCs are never topics.
        Assert.DoesNotContain(d.Topics, t => t.Action is { IsClick: true });
    }

    [Fact]
    public void Left_click_exits_floor_items_and_hidden_hotspots()
    {
        var s = C.InitialState;
        Assert.Equal(new Resolution.Travel("S01.to_S02", "S02"), Left(s, new Hit.Exit("S01.to_S02")));
        Assert.Equal(new Resolution.Walk(400, 900), Left(s, new Hit.Floor(400, 900)));
        Assert.Equal(new Resolution.SelectItem("PHONE"), Left(s, new Hit.Item("PHONE")));
        Assert.IsType<Resolution.None>(Left(s, new Hit.Item("TOOLS"))); // not owned
        Assert.IsType<Resolution.None>(Left(s, new Hit.Empty()));
        var after = TestData.StateAfter("G01");
        Assert.IsType<Resolution.None>(Left(after, new Hit.Hotspot("S01.tools"))); // hidden after G01
    }

    [Fact]
    public void Left_click_on_a_locked_exit_reads_the_locked_look()
    {
        var s = Driver.TravelTo(C, C.InitialState, "S05");
        var exit = C.GetRoom("S05").Exits.Single(e => e.To == "S09");
        var r = Assert.IsType<Resolution.Look>(Left(s, new Hit.Exit(exit.Id)));
        Assert.Equal(TextKeys.LockedOf(exit), r.Text);
        Assert.Equal(s, Navigation.Travel(C, s, exit.Id)); // travel refuses the gate
    }

    // ---- right click

    [Fact]
    public void Right_click_looks_at_targets_and_toggles_inventory_on_free_space()
    {
        var s = TestData.StateAfter("G01");
        Assert.IsType<Resolution.Look>(Right(s, new Hit.Hotspot("S01.fuse")));
        Assert.IsType<Resolution.ToggleInventory>(Right(s, new Hit.Floor(100, 900)));
        Assert.IsType<Resolution.ToggleInventory>(Right(s, new Hit.Empty()));
        var exitLook = Assert.IsType<Resolution.Look>(Right(s, new Hit.Exit("S01.to_S02")));
        Assert.Equal("exit.S01.to_S02.label", exitLook.Text.Key);
        var inv = GameRules.ToggleInventory(s);
        var itemLook = Assert.IsType<Resolution.Look>(Right(inv, new Hit.Item("TOOLS")));
        Assert.Equal("item.TOOLS", itemLook.Text.Key);
        // Looking at an item in the drawer keeps the drawer open.
        Assert.Equal(GameMode.Inventory, Journal.ApplyLook(C, inv, itemLook).Mode);
    }

    [Fact]
    public void Right_click_with_selected_item_cancels_the_selection_first_and_nothing_else()
    {
        var s = GameRules.SelectItem(TestData.StateAfter("G01"), "TOOLS");
        Assert.Equal("TOOLS", s.SelectedItem);
        foreach (Hit hit in new Hit[] { new Hit.Hotspot("S01.fuse"), new Hit.Floor(1, 1), new Hit.Exit("S01.to_S02"), new Hit.Item("PHONE") })
            Assert.IsType<Resolution.CancelSelection>(Right(s, hit));
        var cleared = GameRules.CancelSelection(s);
        Assert.Null(cleared.SelectedItem);
        Assert.Equal(s with { SelectedItem = null }, cleared);
    }

    // ---- selected item: hover text only for an executable rule; invalid click = complete no-op

    [Fact]
    public void Item_action_label_exists_only_for_an_executable_rule()
    {
        var s = GameRules.SelectItem(WithFuseAtCradle(), "FUSE");
        var valid = Left(s, new Hit.Hotspot("S10.chrono"));
        Assert.Equal(new TextRef("action.G10.label", C.GetAction("G10").Label), GameRules.ItemActionLabel(valid));
        // Wrong pair: same name on hover, empty action line.
        var phone = GameRules.SelectItem(GameRules.CancelSelection(s), "PHONE");
        var wrong = Left(phone, new Hit.Hotspot("S10.chrono"));
        Assert.IsType<Resolution.None>(wrong);
        Assert.True(GameRules.ItemActionLabel(wrong).IsEmpty);
        var hover = Views.ViewBuilder.Hover(C, phone, new Hit.Hotspot("S10.chrono"));
        Assert.Equal("hotspot.S10.chrono.name", hover.Name.Key);
        Assert.True(hover.ActionLabel.IsEmpty);
    }

    [Fact]
    public void Invalid_item_click_is_a_complete_noop_that_keeps_the_selection()
    {
        var s = GameRules.SelectItem(WithFuseAtCradle(), "PHONE");
        foreach (Hit hit in new Hit[] { new Hit.Hotspot("S10.chrono"), new Hit.Hotspot("S10.panel"), new Hit.Floor(500, 900), new Hit.Exit(C.GetRoom("S10").Exits[0].Id), new Hit.Empty() })
        {
            var r = Left(s, hit);
            Assert.IsType<Resolution.None>(r); // no walk, no travel, no rejection line
            var session = new GameSession(C, s);
            var changed = false;
            session.StateChanged += (_, _) => changed = true;
            session.Apply(r);
            Assert.False(changed);
            Assert.Equal("PHONE", session.State.SelectedItem);
        }
    }

    [Fact]
    public void Hover_and_click_use_the_same_resolver_and_conditions_are_rechecked_on_arrival()
    {
        var s = C.InitialState;
        var hover = Views.ViewBuilder.Hover(C, s, new Hit.Hotspot("S01.tools"));
        var click = Left(s, new Hit.Hotspot("S01.tools"));
        Assert.Equal(click, hover.Resolution);
        // While walking the state changes (e.g. the action got committed by an earlier click).
        var changed = GameRules.CommitAction(C, s, "G01");
        Assert.NotEqual(click, Left(Playback.FinishAll(C, changed), new Hit.Hotspot("S01.tools")));
        var stale = GameRules.TryCommitAction(C, changed, "G01");
        Assert.False(stale.Success);
        Assert.Equal(ActionRejection.NoLongerValid, stale.Rejection);
        Assert.Same(changed, stale.State);
    }

    [Fact]
    public void Symmetric_recipes_resolve_to_the_same_action_in_both_selection_orders()
    {
        foreach (var id in new[] { "B10", "B11", "I04", "I05" })
        {
            var a = C.GetAction(id);
            var s = TestData.MainStates[TestData.MainRoute.ToList().FindIndex(r => r.Action == id)];
            var first = Left(GameRules.SelectItem(GameRules.ToggleInventory(s), a.SelectedItem!, keepInventoryOpen: true), new Hit.Item(a.Target));
            var second = Left(GameRules.SelectItem(GameRules.ToggleInventory(s), a.Target, keepInventoryOpen: true), new Hit.Item(a.SelectedItem!));
            Assert.Equal(id, Assert.IsType<Resolution.Action>(first).ActionDef.Id);
            Assert.Equal(id, Assert.IsType<Resolution.Action>(second).ActionDef.Id);
            var viaFirst = GameRules.CommitAction(C, s, id);
            Assert.Equal(viaFirst.Inventory, GameRules.CommitAction(C, s, id).Inventory);
        }
    }

    [Fact]
    public void Only_world_and_inventory_modes_accept_interactions()
    {
        var s = C.InitialState;
        foreach (var mode in new[] { GameMode.Dialogue, GameMode.Puzzle, GameMode.Cutscene, GameMode.Map, GameMode.Journal, GameMode.Pause })
        {
            Assert.IsType<Resolution.None>(Left(s with { Mode = mode }, new Hit.Hotspot("S01.tools")));
            Assert.IsType<Resolution.None>(Right(s with { Mode = mode }, new Hit.Empty()));
        }
    }

    [Fact]
    public void Ambiguous_default_actions_throw_instead_of_choosing_randomly()
    {
        var root = JsonNode.Parse(TestData.GameJson)!.AsObject();
        var copy = root["actions"]![0]!.DeepClone().AsObject();
        copy["id"] = "G01_DUP";
        copy["gives"] = new JsonArray();
        foreach (var line in copy["lines"]!.AsArray()) line!["line_id"] = line["line_id"]!.GetValue<string>() + ".dup";
        root["actions"]!.AsArray().Add(copy);
        root["quests"]![0]!["actions"]!.AsArray().Add("G01_DUP");
        var content = GameContent.Load(root.ToJsonString());
        Assert.Throws<InvalidOperationException>(() => GameRules.ResolveInteraction(content, content.InitialState, new Hit.Hotspot("S01.tools"), PointerButton.Left));
    }

    // ---- Space

    [Fact]
    public void Space_toggles_labels_only_in_world_mode_and_persists_across_rooms()
    {
        var s = GameRules.ToggleHotspots(C.InitialState);
        Assert.True(s.HotspotLabels);
        Assert.Equal(s with { Mode = GameMode.Dialogue }, GameRules.ToggleHotspots(s with { Mode = GameMode.Dialogue }));
        Assert.Equal(s with { Mode = GameMode.Cutscene }, GameRules.ToggleHotspots(s with { Mode = GameMode.Cutscene }));
        var moved = Playback.FinishAll(C, Navigation.Travel(C, s, "S01.to_S02"));
        Assert.True(moved.HotspotLabels);
        Assert.False(GameRules.ToggleHotspots(moved).HotspotLabels);
    }

    [Fact]
    public void Hotspot_list_contains_every_visible_hotspot_including_atmospheric_and_all_exits_but_no_hidden_one()
    {
        var before = GameRules.HotspotList(C, C.InitialState);
        Assert.Contains(before, e => e.Id == "S01.tools");
        Assert.Contains(before, e => e.Id == "S01.ambient 1" && e.Kind == HotspotListKind.Prop);
        Assert.Contains(before, e => e.Id == "S01.to_S02" && e.Kind == HotspotListKind.Exit);
        var after = GameRules.HotspotList(C, TestData.StateAfter("G01"));
        Assert.DoesNotContain(after, e => e.Id == "S01.tools");
    }

    [Fact]
    public void Escape_cancels_selection_before_anything_else()
    {
        var s = GameRules.SelectItem(TestData.StateAfter("G01"), "TOOLS");
        var e1 = GameRules.Escape(s);
        Assert.Null(e1.SelectedItem);
        Assert.Equal(GameMode.World, e1.Mode);
        Assert.Equal(GameMode.Pause, GameRules.Escape(e1).Mode);
        Assert.Equal(GameMode.World, GameRules.Escape(GameRules.Escape(e1)).Mode);
    }

    [Fact]
    public void Selecting_an_item_closes_the_drawer_unless_combining()
    {
        var inv = GameRules.ToggleInventory(TestData.StateAfter("G01"));
        Assert.Equal(GameMode.World, GameRules.SelectItem(inv, "TOOLS").Mode);
        Assert.Equal(GameMode.Inventory, GameRules.SelectItem(inv, "TOOLS", keepInventoryOpen: true).Mode);
        Assert.Same(inv, GameRules.SelectItem(inv, "CHRONO")); // not owned
    }
}
