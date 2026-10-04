using System.Reflection;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.Save;
using LastBell.Core.State;
using LastBell.Core.Tests.Support;
using LastBell.Core.Views;

namespace LastBell.Core.Tests;

/// <summary>
/// Logic-level versions of design-doc/acceptance_tests.csv (one test per row, named ATnn_...).
/// Rows that can only be verified in the real Godot build are skipped with the reason.
/// </summary>
public sealed class AcceptanceTests
{
    private static readonly GameContent C = TestData.Content;

    private static Resolution Left(GameState s, Hit hit) => GameRules.ResolveInteraction(C, s, hit, PointerButton.Left);
    private static Resolution Right(GameState s, Hit hit) => GameRules.ResolveInteraction(C, s, hit, PointerButton.Right);
    private static GameState Do(GameState s, params string[] ids) => ids.Aggregate(s, (st, id) => Driver.Perform(C, st, C.GetAction(id)));

    [Fact]
    public void Every_csv_row_has_a_test()
    {
        var ids = File.ReadAllLines(TestData.FixturePath("acceptance_tests.csv")).Skip(1)
            .Where(l => l.Length > 0).Select(l => l.TrimStart('﻿').Split(',')[0]).ToList();
        Assert.Equal(30, ids.Count);
        var methods = typeof(AcceptanceTests).GetMethods(BindingFlags.Public | BindingFlags.Instance).Select(m => m.Name).ToList();
        Assert.All(ids, id => Assert.Contains(methods, m => m.StartsWith(id + "_", StringComparison.Ordinal)));
    }

    [Fact]
    public void AT01_new_game_has_phone_only_and_G01_gives_tools_exactly_once()
    {
        var s = C.InitialState;
        Assert.Equal(new[] { "PHONE" }, s.Inventory);
        s = Driver.Interact(C, s, C.GetAction("G01"), null);
        Assert.Equal(new[] { "PHONE", "TOOLS" }, s.Inventory);
        Assert.IsType<Resolution.None>(Left(s, new Hit.Hotspot("S01.tools")));
        Assert.False(GameRules.TryCommitAction(C, s, "G01").Success);
        Assert.Single(s.Inventory, "TOOLS");
    }

    [Fact]
    public void AT02_ball_on_cassette_mechanism_has_no_text_and_changes_nothing()
    {
        var s = Driver.TravelTo(C, Do(TestData.StateBefore("B06"), "Q1A", "Q1B"), "S16");
        s = GameRules.SelectItem(s, "BALL");
        var r = Left(s, new Hit.Hotspot("S16.deck"));
        Assert.IsType<Resolution.None>(r);
        Assert.True(GameRules.ItemActionLabel(r).IsEmpty);
        var session = new GameSession(C, s);
        session.Apply(r);
        Assert.Same(s, session.State); // no walk, ball kept, selection kept
        Assert.Contains("BALL", session.State.Inventory);
    }

    [Fact]
    public void AT03_belt_label_only_while_B06_is_available_and_never_after()
    {
        var before = GameRules.SelectItem(TestData.ReadyFor("B06"), "BELT_NEW");
        Assert.Equal("action.B06.label", GameRules.ItemActionLabel(Left(before, new Hit.Hotspot("S16.deck"))).Key);
        var after = Playback.FinishAll(C, GameRules.CommitAction(C, before, "B06"));
        Assert.DoesNotContain("BELT_NEW", after.Inventory);
        var forged = GameRules.SelectItem(after with { Inventory = after.Inventory.Add("BELT_NEW") }, "BELT_NEW");
        Assert.True(GameRules.ItemActionLabel(Left(forged, new Hit.Hotspot("S16.deck"))).IsEmpty);
        Assert.All(TestData.MainStates.SkipWhile(st => !st.IsDone("B06")), st => Assert.False(GameRules.ValidAction(C, st, C.GetAction("B06"))));
    }

    [Fact]
    public void AT04_right_click_object_free_space_selection_and_drawer_item()
    {
        var s = TestData.StateAfter("G01");
        Assert.IsType<Resolution.Look>(Right(s, new Hit.Hotspot("S01.fuse")));
        Assert.IsType<Resolution.ToggleInventory>(Right(s, new Hit.Floor(10, 10)));
        Assert.IsType<Resolution.CancelSelection>(Right(GameRules.SelectItem(s, "TOOLS"), new Hit.Hotspot("S01.fuse")));
        var drawer = GameRules.ToggleInventory(s);
        var look = Assert.IsType<Resolution.Look>(Right(drawer, new Hit.Item("TOOLS")));
        Assert.Equal(GameMode.Inventory, Journal.ApplyLook(C, drawer, look).Mode);
    }

    [Fact]
    public void AT05_space_in_every_room_lists_all_visible_hotspots_and_exits_and_nothing_hidden()
    {
        var end = TestData.MainEnd;
        foreach (var room in C.Rooms)
        {
            var s = Driver.TravelTo(C, end, room.Id);
            var list = GameRules.HotspotList(C, GameRules.ToggleHotspots(s));
            var visible = room.Hotspots.Where(h => GameRules.IsVisible(h, s)).Select(h => h.Id);
            Assert.Equal(visible.Concat(room.Exits.Select(e => e.Id)), list.Select(e => e.Id));
            Assert.All(room.Hotspots.Where(h => !GameRules.IsVisible(h, s)), h => Assert.DoesNotContain(list, e => e.Id == h.Id));
        }
        // Also before any progress: hidden hotspots never appear.
        Assert.All(TestData.MainStates, st => Assert.All(GameRules.HotspotList(C, st),
            e => Assert.True(e.Kind == HotspotListKind.Exit || GameRules.IsVisible(C.FindHotspot(e.Id)!.Hotspot, st))));
    }

    [Fact]
    public void AT06_space_with_selected_item_keeps_names_and_outlines_only_valid_targets()
    {
        var s = TestData.ReadyFor("G10");
        var names = GameRules.HotspotList(C, s);
        var withWrong = GameRules.SelectItem(s, "PHONE");
        Assert.Equal(names, GameRules.HotspotList(C, withWrong));
        Assert.All(ViewBuilder.Room(C, withWrong).Hotspots, h => Assert.False(h.ValidForSelectedItem));
        Assert.All(ViewBuilder.Room(C, withWrong).Hotspots, h => Assert.True(ViewBuilder.Hover(C, withWrong, new Hit.Hotspot(h.Id)).ActionLabel.IsEmpty));
        var withFuse = GameRules.SelectItem(s, "FUSE");
        Assert.Contains(ViewBuilder.Room(C, withFuse).Hotspots, h => h.ValidForSelectedItem && h.Id == "S10.chrono");
    }

    [Fact]
    public void AT07_ten_wrong_puzzle_answers_then_close_load_and_solve_once()
    {
        foreach (var actionId in new[] { "G11", "B16", "B22", "F16", "D05" })
        {
            var action = C.GetAction(actionId);
            var puzzle = C.GetPuzzle(action.Puzzle!);
            var s = Puzzles.Open(C, TestData.ReadyFor(actionId), actionId);
            var start = s;
            for (var i = 0; i < 10; i++) s = Puzzles.Submit(C, s, actionId, Rules.PuzzleAnswers.Grid(9, 9)).State;
            Assert.Equal(start.Inventory, s.Inventory);
            Assert.Equal(start.Done, s.Done);
            s = SaveCodec.Load(C, SaveCodec.Serialize(Puzzles.Close(s)));
            var solved = Puzzles.Submit(C, Puzzles.Open(C, s, actionId), actionId, puzzle.Solution!.DeepClone());
            Assert.True(solved.Solved);
            Assert.Equal(start.Done.Length + 1, solved.State.Done.Length);
        }
    }

    [Fact(Skip = "UI-only: HUD scale 200 %, muted audio and discrete rotation controls are presentation features (Godot build).")]
    public void AT08_P02_at_200_percent_hud_without_sound() { }

    [Fact]
    public void AT09_symmetric_recipes_in_reverse_selection_order()
    {
        foreach (var id in new[] { "B10", "B11", "I04", "I05" })
        {
            var a = C.GetAction(id);
            var s = TestData.ReadyFor(id);
            var reversed = GameRules.SelectItem(GameRules.ToggleInventory(s), a.Target, keepInventoryOpen: true);
            var r = Assert.IsType<Resolution.Action>(Left(reversed, new Hit.Item(a.SelectedItem!)));
            Assert.Equal(id, r.ActionDef.Id);
            var viaReverse = GameRules.CommitAction(C, reversed, r.ActionDef.Id);
            var viaNormal = GameRules.CommitAction(C, s, id);
            Assert.Equal(viaNormal.Inventory.OrderBy(x => x), viaReverse.Inventory.OrderBy(x => x));
            Assert.Null(viaReverse.SelectedItem); // both inputs consumed
        }
    }

    [Fact]
    public void AT10_map_before_cassette_and_cassette_before_map_both_work()
    {
        var start = TestData.StateAfter("B03");
        string[] tape = C.FindQuest("M04")!.Actions.Concat(C.FindQuest("M05")!.Actions).ToArray();
        string[] map = C.FindQuest("M06")!.Actions.ToArray();
        var a = Do(Do(start, map), tape);
        var b = Do(Do(start, tape), map);
        Assert.True(a.IsDone("B12") && a.IsDone("B16") && b.IsDone("B12") && b.IsDone("B16"));
        Assert.False(GameRules.GuardsPass(C.GetAction("B22"), Do(start, map)));
        Assert.False(GameRules.GuardsPass(C.GetAction("B22"), Do(start, tape)));
    }

    [Fact]
    public void AT11_first_ivanka_entry_and_returns_to_all_eras_keep_inventory()
    {
        var unlocked = TestData.StateAfter("B22");
        Assert.DoesNotContain("S31", unlocked.Visited);
        var arrival = Navigation.UsePortal(C, Driver.TravelTo(C, unlocked, "S11"), 1960); // first entry plays its lines
        Assert.Equal("S31", arrival.Room);
        Assert.Equal(C.GetRoom("S31").FirstEntry[0].LineId, arrival.ActiveLineId);
        var s = Playback.FinishAll(C, arrival);
        Assert.Equal(1960, s.Era);
        Assert.Equal(unlocked.Inventory.OrderBy(x => x), s.Inventory.OrderBy(x => x));
        var inventory = s.Inventory.OrderBy(x => x).ToList();
        foreach (var era in Navigation.UnlockedEras(C, s))
        {
            var there = Driver.TravelTo(C, s, era.Anchor);
            Assert.Equal(inventory, there.Inventory.OrderBy(x => x));
            Assert.NotNull(Navigation.FindRoute(C, there, "S31"));
        }
    }

    [Fact]
    public void AT12_map_cannot_skip_the_locked_cabinet_pump_or_chamber()
    {
        foreach (var (gateFrom, target, action) in new[] { ("S13", "S15", "B02"), ("S38", "S39", "I08"), ("S48", "S49", "F10") })
        {
            var s = Driver.TravelTo(C, TestData.StateBefore(action), gateFrom);
            Assert.False(s.IsDone(action));
            var forged = GameRules.OpenOverlay(s with { Visited = IdOrSame(s.Visited, target) }, GameMode.Map);
            Assert.False(Navigation.CanFastTravel(C, forged, target));
            Assert.Same(forged, Navigation.FastTravel(C, forged, target));
        }

        static System.Collections.Immutable.ImmutableArray<string> IdOrSame(System.Collections.Immutable.ImmutableArray<string> v, string id) => v.Contains(id) ? v : v.Add(id);
    }

    [Fact]
    public void AT13_main_actions_only_reach_F17_and_return_all_four_evidence_items()
    {
        var end = TestData.MainEnd;
        Assert.True(end.IsDone("F17"));
        Assert.All(end.Done, id => Assert.True(C.GetAction(id).IsMain));
        Assert.All(new[] { "ORIGIN", "TAPE", "CHAIN", "PATCH" }, i => Assert.Contains(i, end.Inventory));
    }

    [Fact]
    public void AT14_all_nine_side_quests_after_the_credits_without_repeating_the_finale()
    {
        var s = TestData.MainEnd;
        Assert.Empty(s.SideRewards);
        var finaleCount = s.Done.Count(d => d == "F17");
        foreach (var id in TestData.OptionalRoute) s = Driver.Perform(C, s, C.GetAction(id));
        Assert.Equal(9, s.SideRewards.Length);
        Assert.Equal(finaleCount, s.Done.Count(d => d == "F17"));
        Assert.Equal(9, Epilogue.Select(C, s).Count);
    }

    [Fact]
    public void AT15_final_ports_in_all_24_orders()
    {
        var ports = new[] { "F12", "F13", "F14", "F15" };
        var orders = ports.SelectMany(a => ports.Where(b => b != a).SelectMany(b => ports.Where(c => c != a && c != b)
            .SelectMany(c => ports.Where(d => d != a && d != b && d != c).Select(d => new[] { a, b, c, d })))).ToList();
        Assert.Equal(24, orders.Count);
        var baseState = TestData.StateBefore("F12");
        foreach (var order in orders)
        {
            var s = baseState;
            foreach (var id in order)
            {
                Assert.False(GameRules.GuardsPass(C.GetAction("F16"), s));
                s = Driver.Perform(C, s, C.GetAction(id));
            }
            s = Do(s, "F16", "F17");
            Assert.True(s.IsDone("F17"));
        }
    }

    [Fact]
    public void AT16_skipping_every_cutscene_gives_the_same_save()
    {
        GameState Run(bool skip)
        {
            var s = C.InitialState;
            foreach (var row in TestData.MainRoute)
            {
                s = Driver.FollowTravelPath(C, s, row.TravelPath);
                var a = C.GetAction(row.Action);
                s = a.Puzzle is null ? GameRules.CommitAction(C, s, a.Id) : GameRules.CommitAction(C, Puzzles.Open(C, s, a.Id), a.Id, row.PuzzleSolution);
                var guard = 0;
                while (s.ActiveLineId is not null && guard++ < 1000)
                    s = skip && Playback.Current(C, s)!.IsCutscene ? Playback.SkipCutscene(C, s) : Playback.Advance(C, s);
                s = GameRules.CancelSelection(s);
            }
            return s;
        }
        Assert.Equal(SaveCodec.Serialize(Run(false)), SaveCodec.Serialize(Run(true)));
        Assert.Equal(9, C.Data.Cutscenes.Count); // the CSV says "seven"; see design-doc/ISSUES.md
    }

    [Fact]
    public void AT17_save_restore_after_main_actions_and_in_the_middle_of_F11()
    {
        var s = TestData.ReadyFor("F11");
        var committed = GameRules.CommitAction(C, s, "F11");
        var mid = Playback.Advance(C, Playback.Advance(C, committed));
        var loaded = SaveCodec.Load(C, SaveCodec.Serialize(mid));
        Assert.Equal(mid.ActiveLineId, loaded.ActiveLineId);
        Assert.Equal(mid.PlaybackQueue, loaded.PlaybackQueue);
        Assert.False(GameRules.TryCommitAction(C, loaded, "F11").Success);
        Assert.Equal(Playback.FinishAll(C, committed), Playback.FinishAll(C, loaded));
        Assert.Equal(Playback.SkipAll(committed), Playback.SkipAll(loaded));
        foreach (var st in TestData.MainStates) Assert.Equal(st, SaveCodec.Load(C, SaveCodec.Serialize(st)));
    }

    [Fact]
    public void AT18_corrupt_save_and_unknown_item_are_rejected_without_mutation()
    {
        var session = new GameSession(C, TestData.StateAfter("G05"));
        var before = session.State;
        Assert.False(session.TryLoad("{\"schema_version\": 1, \"room\": ", out _));
        var save = System.Text.Json.Nodes.JsonNode.Parse(SaveCodec.Serialize(before))!.AsObject();
        save.Remove("checksum");
        save["inventory"]!.AsArray().Add("UNKNOWN_THING");
        Assert.False(session.TryLoad(save.ToJsonString(), out var error));
        Assert.Equal("ui.save.corrupt", error.Key);
        Assert.Same(before, session.State);
    }

    [Fact(Skip = "UI-only: keyboard-only play and subtitles are presentation features; Core only provides Escape/selection rules (covered in ControlRulesTests).")]
    public void AT19_whole_game_with_keyboard_and_subtitles_only() { }

    [Fact(Skip = "UI-only: scaling and HUD overlap at 1280x720 / 1920x1080 need the Godot build; the data-level minimum hit area is checked by AT20_data_minimum_hit_area.")]
    public void AT20_all_hotspots_at_two_resolutions() { }

    [Fact]
    public void AT20_data_minimum_hit_area()
    {
        Assert.All(C.Rooms.SelectMany(r => r.Hotspots), h => Assert.True(h.Rect[2] >= 44 && h.Rect[3] >= 44, h.Id));
        Assert.All(C.Rooms.SelectMany(r => r.Exits), e => Assert.True(e.Rect[2] >= 44 && e.Rect[3] >= 44, e.Id));
    }

    [Fact]
    public void AT21_S15_S43_S47_change_exactly_by_their_causal_effects()
    {
        var all = TestData.MainEnd;
        foreach (var id in TestData.OptionalRoute) all = Driver.Perform(C, all, C.GetAction(id));
        foreach (var room in new[] { "S15", "S43", "S47" })
        {
            var expected = C.Data.CausalEffects.Where(e => e.At.Contains(room)).ToList();
            Assert.Empty(WorldEffects.CausalEffectsAt(C, C.InitialState, room));
            Assert.Equal(expected, WorldEffects.CausalEffectsAt(C, all, room).Select(e => e.Effect));
        }
        // No new quests appear: the quest list is fixed data.
        Assert.Equal(27, C.Quests.Count);
    }

    [Fact]
    public void AT22_double_click_spam_commits_once_and_clicks_do_not_fall_through_dialogue()
    {
        var s = C.InitialState;
        var first = GameRules.TryCommitAction(C, s, "G01");
        var second = GameRules.TryCommitAction(C, first.State, "G01");
        Assert.True(first.Success);
        Assert.False(second.Success);
        Assert.Single(second.State.Inventory, "TOOLS");
        Assert.Equal(GameMode.Dialogue, first.State.Mode);
        Assert.IsType<Resolution.None>(Left(first.State, new Hit.Floor(500, 900)));
        Assert.IsType<Resolution.None>(Left(first.State, new Hit.Hotspot("S01.fuse")));
    }

    [Fact]
    public void AT23_no_timer_or_time_fail_before_F09()
    {
        var s = TestData.ReadyFor("F09");
        var paused = GameRules.OpenOverlay(s, GameMode.Pause);
        var resumed = GameRules.CloseOverlay(paused);
        Assert.Equal(s, resumed);
        Assert.True(GameRules.ValidAction(C, resumed, C.GetAction("F09")));
        Assert.All(C.Data.Puzzles, p => Assert.True(p.NoTimer));
        Assert.DoesNotContain(typeof(GameState).GetProperties(), p => p.PropertyType == typeof(DateTime) || p.PropertyType == typeof(TimeSpan));
    }

    [Fact]
    public void AT24_content_audit()
    {
        Assert.Equal(68, C.Rooms.Count);
        var postgame = Navigation.ConnectedRooms(C, TestData.MainEnd, includePortals: true);
        Assert.Equal(68, postgame.Count);
        Assert.Equal(127, C.Actions.Count);
        Assert.All(C.Actions, a => Assert.All(a.Lines, l => Assert.False(string.IsNullOrEmpty(l.LineId))));
        Assert.Equal(9, C.Quests.Count(q => q.IsSide && q.Actions.Count >= 3));
        var texts = C.Actions.SelectMany(a => a.Lines.Select(l => l.Text)).Concat(C.Rooms.SelectMany(r => r.Hotspots.Select(h => h.Look)));
        Assert.DoesNotContain(texts, t => t.Contains("TODO", StringComparison.OrdinalIgnoreCase) || t.Contains("placeholder", StringComparison.OrdinalIgnoreCase) || t.Contains("lorem", StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public void AT25_tree_and_wall_variants_after_E10_without_softlock()
    {
        var before = TestData.StateBefore("E10");
        var visited55 = Driver.TravelTo(C, before, "S55");
        Assert.All(WorldEffects.VariantLayers(C, visited55, "S55"), l => Assert.False(l.Visible));
        Assert.All(WorldEffects.VariantLayers(C, visited55, "S17"), l => Assert.False(l.Visible));
        var photoLook = Rules.GameRules.ResolveInteraction(C, GameRules.ToggleInventory(visited55), new Hit.Item("PHOTO2020"), PointerButton.Right);
        var after = Driver.Perform(C, visited55, C.GetAction("E10"));
        var back55 = Driver.TravelTo(C, after, "S55");
        Assert.All(WorldEffects.VariantLayers(C, back55, "S55"), l => Assert.True(l.Visible));
        var back17 = Driver.TravelTo(C, after, "S17");
        Assert.All(WorldEffects.VariantLayers(C, back17, "S17"), l => Assert.True(l.Visible));
        // The 2020 photograph item is unchanged.
        Assert.Equal(photoLook, Rules.GameRules.ResolveInteraction(C, GameRules.ToggleInventory(back55), new Hit.Item("PHOTO2020"), PointerButton.Right));
        // Not stuck: the way back exists from both rooms.
        Assert.NotNull(Navigation.FindRoute(C, back55, "S10"));
        Assert.NotNull(Navigation.FindRoute(C, back17, "S11"));
    }

    [Fact]
    public void AT26_single_item_lineage_across_1982_1995_2020()
    {
        Assert.All(TestData.MainStates, s => Assert.True(TemporalCache.InvariantHolds(C, s)));
        var s2 = TestData.StateAfter("D05");
        for (var i = 0; i < 3; i++)
        {
            s2 = Driver.TravelTo(C, s2, "S61");
            Assert.False(GameRules.ValidAction(C, s2, C.GetAction("E08")));
            Assert.DoesNotContain("SEALED_NEW", s2.Inventory);
            s2 = Driver.TravelTo(C, s2, "S55");
            Assert.False(GameRules.ValidAction(C, s2, C.GetAction("D05")));
        }
        Assert.Single(s2.Inventory, "SEALED_OLD");
    }

    [Fact]
    public void AT27_tono_encounters_have_exact_conditions_and_ages()
    {
        Assert.Equal(new[] { "E01" }, C.GetAction("E02").RequiresDone);
        Assert.Equal(new[] { "E02", "E10" }, C.GetAction("E11").RequiresDone);
        Assert.Equal(new[] { "D06" }, C.GetAction("D07").RequiresDone);
        Assert.False(GameRules.GuardsPass(C.GetAction("E11"), TestData.StateBefore("E02")));
        Assert.Equal(12, C.FindCharacter("TONO82")!.Age!.GetValue<int>());
        Assert.Equal(25, C.FindCharacter("TONO")!.Age!.GetValue<int>());
        Assert.Equal(50, C.FindCharacter("TONO20")!.Age!.GetValue<int>());
        // E02 does not auto-complete E11/D07.
        var afterE02 = TestData.StateAfter("E02");
        Assert.False(afterE02.IsDone("E11"));
        Assert.False(afterE02.IsDone("D07"));
    }

    [Fact]
    public void AT28_story_without_Q9C_then_Q9C_with_follow_ups()
    {
        var end = TestData.MainEnd;
        Assert.False(end.IsDone("Q9C"));
        var s = Do(end, "Q9A", "Q9B", "Q9C");
        Assert.Contains("Q9", s.SideRewards);
        foreach (var room in new[] { "S15", "S54", "S44" })
            Assert.Contains(WorldEffects.VariantLayers(C, s, room), l => l.Visible && l.Layer.After == "Q9C");
        s = Do(s, "Q9D", "Q9E", "Q9F");
        Assert.Equal(QuestStatus.Done, Quests.StatusOf(C.FindQuest("Q9")!, s));
        Assert.All(new[] { "ORIGIN", "TAPE", "CHAIN", "PATCH" }, i => Assert.Contains(i, s.Inventory));
    }

    [Fact]
    public void AT29_no_bypass_from_biela_put_to_the_rotunda()
    {
        var s = TestData.ReadyFor("J02");
        Assert.DoesNotContain("S47", Navigation.ConnectedRooms(C, s, includePortals: true));
        var afterRide = TestData.StateAfter("J04");
        Assert.True(afterRide.IsDone("J02") && afterRide.IsDone("J03") && afterRide.IsDone("J04"));
        Assert.Contains("S67", afterRide.Visited);
        Assert.Contains("S68", afterRide.Visited);
        Assert.Contains("LIFT_TICKET", afterRide.Inventory);
    }

    [Fact]
    public void AT30_lifts_work_after_J05_and_F09()
    {
        var s = TestData.StateAfter("F09");
        var down = Driver.TravelTo(C, s, "S41");
        Assert.Equal("S41", down.Room);
        var up = Driver.TravelTo(C, down, "S50");
        Assert.Equal("S50", up.Room);
        Assert.DoesNotContain(new[] { "J02", "J03", "J04" }, id => GameRules.ValidAction(C, up, C.GetAction(id)));
    }
}
