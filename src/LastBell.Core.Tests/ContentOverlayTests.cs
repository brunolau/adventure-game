using System.Text.Json.Nodes;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.Save;
using LastBell.Core.State;
using LastBell.Core.Tests.Support;
using LastBell.Core.Text;
using LastBell.Core.Views;

namespace LastBell.Core.Tests;

/// <summary>
/// Content-extension overlays (src/game/data/content_ext, Core README section 13): longer sequences and extra topics
/// (dialogue_ext.json), the bus to Dúbravka 2020 and the map regions (travel_ext.json). game.json is never edited.
/// </summary>
public sealed class ContentOverlayTests
{
    private static readonly GameContent C = TestData.Content;
    private static readonly GameContent Base = TestData.BaseContent;

    private static GameContent Load(string? dialogue = null, string? travel = null) =>
        GameContent.Load(TestData.GameJson, new ContentOverlays(dialogue, travel));

    private static string Errors(string? dialogue = null, string? travel = null)
    {
        var ex = Assert.Throws<ContentLoadException>(() => Load(dialogue, travel));
        return string.Join("\n", ex.Errors);
    }

    // ------------------------------------------------------------------ loader

    [Theory]
    [InlineData(null, null)]
    [InlineData("", "  ")]
    [InlineData("{}", "{}")]
    [InlineData("""{"format":"lastbell.dialogue_ext","version":1,"sequences":[],"topic_extensions":[],"topics":[]}""",
                """{"format":"lastbell.travel_ext","version":1,"remove_exits":[],"remove_connections":[],"exits":[],"connections":[],"regions":[]}""")]
    public void An_empty_overlay_is_valid_and_plays_exactly_the_handoff(string? dialogue, string? travel)
    {
        var c = Load(dialogue, travel);
        Assert.True(c.Overlay.IsEmpty);
        Assert.Equal(Base.Actions.SelectMany(a => a.Lines).Select(l => l.LineId), c.Actions.SelectMany(a => a.Lines).Select(l => l.LineId));
        Assert.Equal(Base.Data.Connections.Count, c.Data.Connections.Count);
        Assert.Equal(Base.AllLineIds.OrderBy(x => x), c.AllLineIds.OrderBy(x => x));
        // Without regions every district is a region and every room a hub: fast travel as in the handoff.
        Assert.All(c.Rooms, r => Assert.True(c.IsHub(r.Id)));
        Assert.Equal(c.Rooms.Select(r => (r.Era, r.District)).Distinct().Count(), c.Regions.Count);
    }

    [Fact]
    public void The_live_overlays_load_and_only_add_lines_topics_and_travel()
    {
        Assert.False(C.Overlay.IsEmpty);
        Assert.NotEmpty(C.Overlay.ExtendedActions);
        Assert.NotEmpty(C.Overlay.AddedTopics);
        // Logic is untouched: every action keeps its guards, items, quest and puzzle.
        static string Logic(ActionDef a) => System.Text.Json.JsonSerializer.Serialize(a with { Lines = Array.Empty<LineDef>() }, GameContent.JsonOptions);
        foreach (var (a, b) in Base.Actions.Zip(C.Actions))
        {
            Assert.Equal(a.Id, b.Id);
            Assert.Equal(Logic(a), Logic(b));
            Assert.Equal(a.Lines.Select(l => l.LineId).Where(id => !C.Overlay.RetiredLines.Any(r => r.Line.LineId == id)),
                b.Lines.Select(l => l.LineId).Where(id => Base.FindLine(id!) is not null).OrderBy(id => a.Lines.ToList().FindIndex(l => l.LineId == id)));
        }
        string Json(object o) => System.Text.Json.JsonSerializer.Serialize(o, GameContent.JsonOptions);
        Assert.Equal(Json(Base.Items), Json(C.Items));
        Assert.Equal(Json(Base.Quests), Json(C.Quests));
        Assert.Equal(Json(Base.Data.Puzzles), Json(C.Data.Puzzles));
        Assert.Equal(Json(Base.Data.Cutscenes), Json(C.Data.Cutscenes));
        // Every existing line keeps its speaker and text; new lines are listed.
        foreach (var id in C.AllLineIds.Where(id => Base.FindLine(id) is not null))
            Assert.Equal(Base.FindLine(id)!.Line, C.FindLine(id)!.Line);
        Assert.All(C.Overlay.AddedLineIds, id => Assert.Null(Base.FindLine(id)));
    }

    [Fact]
    public void A_longer_sequence_plays_in_the_overlay_order()
    {
        var expected = new List<string>();
        var root = JsonNode.Parse(TestData.OverlayText(ContentOverlays.DialogueExtFile)!)!;
        var seq = root["sequences"]!.AsArray().First(n => n!["action"]?.GetValue<string>() == "G02")!;
        foreach (var line in seq["lines"]!.AsArray())
            expected.Add(line is JsonValue v ? v.GetValue<string>() : line!["key"]!.GetValue<string>());
        Assert.True(expected.Count > Base.GetAction("G02").Lines.Count);
        Assert.Equal(expected, C.GetAction("G02").Lines.Select(l => l.LineId));

        var s = Dialogue.OpenMenu(TestData.ReadyFor("G02"));
        s = GameRules.CommitAction(C, s, "G02");
        var played = new List<string>();
        while (Playback.Current(C, s) is { Source: LineSource.Action } line) { played.Add(line.LineId); s = Playback.Advance(C, s); }
        Assert.Equal(expected, played);
        Assert.Equal(TestData.StateAfter("G02").Inventory, Playback.FinishAll(C, s).Inventory);
    }

    [Fact]
    public void New_topics_follow_their_timing_and_change_no_progress()
    {
        var roman = C.FindHotspot("S02.ROMAN")!.Hotspot;
        var before = Driver.TravelTo(C, TestData.StateBefore("G05"), "S02");
        Assert.DoesNotContain(Dialogue.TopicsFor(C, before, roman), t => t.Id == "ROMAN.extra 1"); // requires G05
        Assert.Contains(Dialogue.TopicsFor(C, before, roman), t => t.Id == "ROMAN.extra 2");
        var after = Driver.TravelTo(C, TestData.StateAfter("G05"), "S02");
        var option = Assert.Single(Dialogue.TopicsFor(C, after, roman), t => t.Id == "ROMAN.extra 1");
        Assert.False(option.IsStoryAction);
        Assert.Equal("topic.ROMAN.extra 1.label", option.Label.Key);

        var s = Dialogue.StartTopic(C, Dialogue.OpenMenu(after), "ROMAN.extra 1");
        Assert.Equal("topic.ROMAN.extra 1.001", s.ActiveLineId);
        s = Playback.FinishAll(C, s);
        Assert.Equal(after.Done, s.Done);
        Assert.Equal(after.Inventory, s.Inventory);
        Assert.Contains(Dialogue.TopicEntryKey("ROMAN.extra 1"), s.JournalSeen);
        Assert.Contains(Dialogue.Transcript(C, s, "ROMAN"), e => e.SourceId == "ROMAN.extra 1");

        // excluded_done hides a topic once the action is done.
        var c = Load("""{"topics":[{"id":"ext.ELA.test","character":"ELA","label":"Test","excluded_done":["G02"],"repeatable":false,"lines":""" +
            """[{"key":"topic.ext.ELA.test.001","speaker":"ADAM","sk":"Ahoj."},{"key":"topic.ext.ELA.test.002","speaker":"ELA","sk":"Ahoj, Adam."}]}]}""");
        var ela = c.FindHotspot("S03.ELA")!.Hotspot;
        var open = Driver.TravelTo(c, c.InitialState, "S03");
        Assert.Contains(Dialogue.TopicsFor(c, open, ela), t => t.Id == "ext.ELA.test");
        var heard = Playback.FinishAll(c, Dialogue.StartTopic(c, open, "ext.ELA.test"));
        Assert.DoesNotContain(Dialogue.TopicsFor(c, heard, ela), t => t.Id == "ext.ELA.test"); // not repeatable
        var done = open with { Done = open.Done.Add("G02") };
        Assert.DoesNotContain(Dialogue.TopicsFor(c, done, ela), t => t.Id == "ext.ELA.test");
        Assert.Same(done, Dialogue.StartTopic(c, done, "ext.ELA.test"));
    }

    [Fact]
    public void Dropped_lines_are_retired_but_still_resolve_for_old_saves()
    {
        var c = Load("""{"sequences":[{"action":"G02","lines":["action.G02.001",{"key":"action.G02.x01","speaker":"ELA","sk":"Áno."},"action.G02.004"]}]}""");
        Assert.Equal(new[] { "action.G02.001", "action.G02.x01", "action.G02.004" }, c.GetAction("G02").Lines.Select(l => l.LineId));
        Assert.Equal(new[] { "action.G02.002", "action.G02.003" }, c.Overlay.RetiredLines.Select(r => r.Line.LineId));
        Assert.DoesNotContain("action.G02.002", c.AllLineIds);
        Assert.Equal(LineSource.Action, c.FindLine("action.G02.002")!.Source);
        var mid = GameRules.CommitAction(c, Dialogue.OpenMenu(TestData.ReadyFor("G02")), "G02") with { ActiveLineId = "action.G02.002" };
        Assert.True(SaveCodec.TryLoad(c, SaveCodec.Serialize(mid), out var loaded, out _, out var reason), reason);
        Assert.Equal("action.G02.002", loaded!.ActiveLineId);
    }

    public static IEnumerable<object[]> BadDialogueOverlays() => new[]
    {
        new object[] { """{"sequences":[{"action":"G02","gives":["TOOLS"],"lines":["action.G02.001"]}]}""", "gives: field not allowed" },
        new object[] { """{"sequences":[{"action":"G02","lines":["action.G02.001"],"requires_done":["G01"]}]}""", "requires_done: field not allowed" },
        new object[] { """{"sequences":[{"action":"NOPE","lines":["action.G02.001"]}]}""", "unknown action 'NOPE'" },
        new object[] { """{"sequences":[{"action":"G02","topic":"ELA.ambient 1","lines":["action.G02.001"]}]}""", "exactly one of" },
        new object[] { """{"sequences":[{"action":"G02","lines":["action.G03.001"]}]}""", "is not a line of action 'G02'" },
        new object[] { """{"sequences":[{"action":"G02","lines":["action.G02.001","action.G02.001"]}]}""", "listed twice" },
        new object[] { """{"sequences":[{"action":"G02","lines":[]}]}""", "lines: empty" },
        new object[] { """{"sequences":[{"action":"G02","lines":[{"key":"action.G02.003","speaker":"ADAM","sk":"x"}]}]}""", "already exists" },
        new object[] { """{"sequences":[{"action":"G02","lines":[{"key":"action.G03.x01","speaker":"ADAM","sk":"x"}]}]}""", "must be 'action.G02.<n>'" },
        new object[] { """{"sequences":[{"action":"G02","lines":[{"key":"action.G02.label","speaker":"ADAM","sk":"x"}]}]}""", "must be 'action.G02.<n>'" },
        new object[] { """{"sequences":[{"action":"G02","lines":[{"key":"action.G02.x01","speaker":"NOBODY","sk":"x"}]}]}""", "unknown speaker 'NOBODY'" },
        new object[] { """{"sequences":[{"action":"G02","lines":[{"key":"action.G02.x01","speaker":"TONO20","sk":"x"}]}]}""", "does not take part" },
        new object[] { """{"sequences":[{"action":"G02","lines":[{"key":"action.G02.x01","speaker":"ADAM","sk":"  "}]}]}""", "empty text" },
        new object[] { """{"sequences":[{"action":"G02","lines":[{"key":"action.G02.x01","speaker":"ADAM","sk":"x","gives":"TOOLS"}]}]}""", "gives: field not allowed" },
        new object[] { """{"sequences":[{"action":"G02","lines":["action.G02.001"]},{"action":"G02","lines":["action.G02.002"]}]}""", "extended twice" },
        new object[] { """{"topics":[{"id":"ext.ELA.a","character":"ELA","label":"A","requires_done":["NOPE"],"lines":[{"key":"topic.ext.ELA.a.001","speaker":"ADAM","sk":"x"}]}]}""", "unknown action 'NOPE'" },
        new object[] { """{"topics":[{"id":"ext.ELA.a","character":"ELA","label":"A","requires_done":["G02"],"excluded_done":["G02"],"lines":[{"key":"topic.ext.ELA.a.001","speaker":"ADAM","sk":"x"}]}]}""", "both required and excluded" },
        new object[] { """{"topics":[{"id":"ext.ELA.a","character":"ELA","label":"A","gives":["TOOLS"],"lines":[{"key":"topic.ext.ELA.a.001","speaker":"ADAM","sk":"x"}]}]}""", "gives: field not allowed" },
        new object[] { """{"topics":[{"id":"ext.ELA.a","character":"ELA","label":"A","puzzle":"P01","lines":[{"key":"topic.ext.ELA.a.001","speaker":"ADAM","sk":"x"}]}]}""", "puzzle: field not allowed" },
        new object[] { """{"topics":[{"id":"ELA.ambient 1","character":"ELA","label":"A","lines":[{"key":"topic.ELA.ambient 1.009","speaker":"ADAM","sk":"x"}]}]}""", "already exists" },
        new object[] { """{"topics":[{"id":"ELA.chat","character":"ELA","label":"A","lines":[{"key":"topic.ELA.chat.001","speaker":"ADAM","sk":"x"}]}]}""", "must start with 'ext.'" },
        new object[] { """{"topics":[{"id":"ext.ELA.a","character":"ELA","label":"A","lines":["action.G02.001"]}]}""", "a new topic has no existing lines" },
        new object[] { """{"topics":[{"id":"ext.ELA.a","character":"ELA","label":"A","speaks_first":"ELA","lines":[{"key":"topic.ext.ELA.a.001","speaker":"ADAM","sk":"x"}]}]}""", "speaks_first" },
        new object[] { """{"topics":[{"id":"ext.X.a","character":"NOPE","label":"A","lines":[{"key":"topic.ext.X.a.001","speaker":"ADAM","sk":"x"}]}]}""", "unknown character 'NOPE'" },
        new object[] { """{"travel":{"id":"bus"}}""", "travel_ext.json" },
        new object[] { """{"format":"other"}""", "format: expected 'lastbell.dialogue_ext'" },
        new object[] { """[1,2]""", "must be a JSON object" },
        new object[] { """{"sequences":[""", "invalid JSON" },
    };

    [Theory]
    [MemberData(nameof(BadDialogueOverlays))]
    public void A_dialogue_overlay_that_touches_logic_or_breaks_keys_fails_loudly(string dialogue, string expected) =>
        Assert.Contains(expected, Errors(dialogue: dialogue));

    private const string BusExit = """{"room":"S07","id":"S07.to_S51","to":"S51","travel":"bus","label":"A","locked_look":"B","rect":[960,975,55,70],"interaction_point":[985,965]}""";
    private const string BusBack = """{"room":"S51","id":"S51.to_S07","to":"S07","travel":"bus","label":"A","locked_look":"B","rect":[50,975,55,70],"interaction_point":[130,965]}""";
    private const string BusConnection = """{"from":"S07","to":"S51","travel":"bus","label":"A","locked_look":"B"}""";

    public static IEnumerable<object[]> BadTravelOverlays() => new[]
    {
        new object[] { $$"""{"exits":[{{BusExit}}]}""", "no connection leads from 'S07' to 'S51'" },
        new object[] { $$"""{"connections":[{{BusConnection}}],"exits":[{{BusExit}}]}""", "room 'S51' needs an exit to 'S07'" },
        new object[] { """{"remove_connections":[{"from":"S02","to":"S51"}]}""", "still leads there; add it to remove_exits" },
        new object[] { """{"remove_exits":["S02.to_S51"]}""", "still exists; add it to remove_connections" },
        new object[] { """{"remove_exits":["NOPE"]}""", "unknown exit 'NOPE'" },
        new object[] { """{"remove_connections":[{"from":"S51","to":"S02"}]}""", "write it in its game.json direction" },
        new object[] { """{"remove_exits":["S03.to_S07","S07.to_S03"],"remove_connections":[{"from":"S03","to":"S07"}]}""", "can no longer be reached" },
        new object[] { """{"exits":[{"room":"S07","id":"S07.to_S11","to":"S11","travel":"bus","label":"A","locked_look":"B","rect":[1,2,3,4],"interaction_point":[1,2]}]}""", "eras are changed only by the chronometer" },
        new object[] { """{"exits":[{"room":"S07","id":"S07.to_S51","to":"S51","travel":"rocket","label":"A","locked_look":"B","rect":[1,2,3,4],"interaction_point":[1,2]}]}""", "unknown travel style 'rocket'" },
        new object[] { """{"exits":[{"room":"S07","id":"S07.to_S51","to":"S51","travel":"bus","label":"A","locked_look":"B","rect":[1,2,3],"interaction_point":[1,2]}]}""", "rect: must have 4 integers" },
        new object[] { """{"exits":[{"room":"S07","id":"S07.bus","to":"S51","travel":"bus","label":"A","locked_look":"B","rect":[1,2,3,4],"interaction_point":[1,2]}]}""", "expected 'S07.to_S51'" },
        new object[] { """{"exits":[{"room":"S07","id":"S07.to_S51","to":"S51","travel":"bus","label":"A","locked_look":"B","rect":[1,2,3,4],"interaction_point":[1,2],"gives":["TOOLS"]}]}""", "gives: field not allowed" },
        new object[] { """{"exits":[{"room":"S07","id":"S07.to_S51","to":"S51","travel":"bus","label":"A","locked_look":"B","rect":[1,2,3,4],"interaction_point":[1,2],"first_ride":{"lines":[{"key":"travel.S07.to_S51.first.001","speaker":"JOZEF","sk":"x"}]}}]}""", "does not take part" },
        new object[] { """{"regions":[{"id":"Chorvátsky Grob","era":2020,"rooms":["S01","S02","S03","S04","S05","S06","S07","S08","S09","S10"],"hubs":["S07"]},{"id":"Dúbravka","era":2020,"rooms":["S51","S52","S53","S54","S55","S56"],"hubs":["S51"]}]}""", "not hub to hub" },
        new object[] { """{"regions":[{"id":"Dúbravka","era":2020,"rooms":["S51","S52","S53","S54","S55","S56"],"hubs":["S51"]}]}""", "belongs to no region" },
        new object[] { """{"regions":[{"id":"A","era":1960,"rooms":["S31","S32"],"hubs":["S33"]}]}""", "is not one of the region's rooms" },
        new object[] { """{"regions":[{"id":"A.b","era":1960,"rooms":["S31"],"hubs":["S31"]}]}""", "without dots" },
    };

    [Theory]
    [MemberData(nameof(BadTravelOverlays))]
    public void A_travel_overlay_that_breaks_the_graph_or_the_hub_rule_fails_loudly(string travel, string expected) =>
        Assert.Contains(expected, Errors(travel: travel));

    // ------------------------------------------------------------------ travel: the bus to Dúbravka 2020

    [Fact]
    public void The_bus_from_Cierna_Voda_replaces_the_car_to_Dubravka_2020()
    {
        Assert.Contains(Base.GetRoom("S02").Exits, e => e.To == "S51");
        Assert.DoesNotContain(C.GetRoom("S02").Exits, e => e.To == "S51");
        Assert.DoesNotContain(C.GetRoom("S51").Exits, e => e.To == "S02");
        var bus = Assert.Single(C.GetRoom("S07").Exits, e => e.To == "S51");
        Assert.Equal("bus", bus.Travel);
        Assert.Equal("exit.S07.to_S51.label", TextKeys.LabelOf(bus).Key);
        Assert.Equal("bus", Assert.Single(C.GetRoom("S51").Exits, e => e.To == "S07").Travel);
        Assert.DoesNotContain(C.Data.Connections, c => c.From == "S02" && c.To == "S51");

        var s = Driver.TravelTo(C, TestData.StateAfter("C01"), "S07");
        Assert.Equal(new Resolution.Travel(bus.Id, "S51"), GameRules.ResolveInteraction(C, s, new Hit.Exit(bus.Id), PointerButton.Left));
        var route = Navigation.FindRoute(C, TestData.StateAfter("C01"), "S52")!;
        Assert.Contains(route, step => step.From == "S07" && step.To == "S51");
        Assert.DoesNotContain(route, step => step.From == "S02" && step.To == "S51");
    }

    [Fact]
    public void First_ride_lines_play_once_in_the_room_left_then_the_entry_lines()
    {
        var at = Driver.TravelTo(C, TestData.StateAfter("C01"), "S07");
        at = at with { Visited = at.Visited.Remove("S51"), JournalSeen = at.JournalSeen.Remove(Navigation.FirstRideKey("S07.to_S51")) };
        var s = Navigation.Travel(C, at, "S07.to_S51");
        Assert.Equal("S51", s.Room);
        var played = new List<(string, LineSource)>();
        while (Playback.Current(C, s) is { } line) { played.Add((line.LineId, line.Source)); s = Playback.Advance(C, s); }
        Assert.Equal(new[]
        {
            ("travel.S07.to_S51.first.001", LineSource.Travel), ("travel.S07.to_S51.first.002", LineSource.Travel),
            ("entry.S51.001", LineSource.FirstEntry),
        }, played);
        Assert.Contains(Navigation.FirstRideKey("S07.to_S51"), s.JournalSeen);
        Assert.Equal(at.Done, s.Done);
        // The second ride plays nothing; the way back has its own first ride.
        var back = Navigation.Travel(C, s, "S51.to_S07");
        Assert.Equal("travel.S51.to_S07.first.001", back.ActiveLineId);
        var again = Navigation.Travel(C, Playback.FinishAll(C, back), "S07.to_S51");
        Assert.Null(again.ActiveLineId);
        Assert.Equal(GameMode.World, again.Mode);
        // Saved in the middle of a ride line, the game loads on that line.
        var mid = Navigation.Travel(C, at, "S07.to_S51");
        Assert.True(SaveCodec.TryLoad(C, SaveCodec.Serialize(mid), out var loaded, out _, out _));
        Assert.Equal("travel.S07.to_S51.first.001", loaded!.ActiveLineId);
    }

    [Fact]
    public void Walkthrough_paths_are_recomputed_through_the_bus_stop()
    {
        // Step 52 (D01) walks S05 -> S02 -> S51 in walkthrough.json; under the overlay the driver goes by bus.
        var d01 = TestData.StateAfter("D01");
        Assert.Contains("S07", d01.Visited);
        Assert.Contains(Navigation.FirstRideKey("S07.to_S51"), d01.JournalSeen);
        Assert.Equal(TestData.MainRoute.Single(r => r.Action == "D01").RoomAfter, d01.Room);
    }

    // ------------------------------------------------------------------ map regions and fast travel

    [Fact]
    public void Fast_travel_is_free_inside_a_region_and_reaches_another_region_only_through_its_hub()
    {
        var s = GameRules.OpenOverlay(TestData.StateAfter("C02"), GameMode.Map); // in S03 (Chorvátsky Grob), Dúbravka 2020 visited
        Assert.Equal("S03", s.Room);
        Assert.Contains("S52", s.Visited);
        Assert.True(Navigation.CanFastTravel(C, s, "S05"));  // same region
        Assert.True(Navigation.CanFastTravel(C, s, "S07"));  // Čierna Voda belongs to the Chorvátsky Grob region
        Assert.True(Navigation.CanFastTravel(C, s, "S51"));  // hub of Dúbravka (bus stop)
        Assert.False(Navigation.CanFastTravel(C, s, "S52")); // not a hub: only through S51
        Assert.True(Navigation.CanFastTravel(Base, s, "S52")); // the handoff without the overlay allowed it
        Assert.Same(s, Navigation.FastTravel(C, s, "S52"));
        var there = Playback.FinishAll(C, Navigation.FastTravel(C, s, "S51"));
        Assert.Equal("S51", there.Room);
        Assert.Equal("bus", Navigation.TransportBetween(C, there, "S03", "S51"));
        Assert.Null(Navigation.TransportBetween(C, there, "S01", "S07"));
        Assert.True(Navigation.CanFastTravel(C, GameRules.OpenOverlay(there, GameMode.Map), "S52")); // free inside Dúbravka

        var sheet = ViewBuilder.Map(C, s).Single(e => e.Year == 2020);
        Assert.Equal(new[] { "Chorvátsky Grob", "Dúbravka" }, sheet.Regions.Select(r => r.Id));
        var grob = sheet.Regions[0];
        var dubravka = sheet.Regions[1];
        Assert.True(grob.IsCurrent);
        Assert.Equal("region.Chorvátsky Grob.name", grob.Name.Key);
        Assert.Equal(new[] { "S51" }, dubravka.Hubs);
        Assert.True(dubravka.CanTravel);
        Assert.Equal("bus", dubravka.Transport);
        Assert.Null(grob.Transport);
        Assert.Equal("Dúbravka", sheet.Rooms.Single(r => r.RoomId == "S52").RegionId);
        Assert.False(sheet.Rooms.Single(r => r.RoomId == "S52").CanFastTravel);
        Assert.True(sheet.Rooms.Single(r => r.RoomId == "S51").IsHub);
        Assert.All(sheet.Rooms.Where(r => !r.IsCurrent), r => Assert.Equal(r.CanFastTravel, Navigation.CanFastTravel(C, s, r.RoomId)));
    }

    [Fact]
    public void Every_cross_region_connection_joins_two_hubs()
    {
        foreach (var c in C.Data.Connections)
        {
            var a = C.RegionOf(c.From);
            var b = C.RegionOf(c.To);
            if (ReferenceEquals(a, b)) continue;
            Assert.True(C.IsHub(c.From) && C.IsHub(c.To), $"{c.From}->{c.To} ({a.Id} / {b.Id})");
            Assert.NotEqual("walk", c.Travel);
        }
        Assert.All(C.Eras, e => Assert.All(C.RegionsOf(e.Year), r => Assert.True(r.FromOverlay)));
        Assert.Equal(C.Rooms.Count, C.Regions.Sum(r => r.Rooms.Count));
    }

    // ------------------------------------------------------------------ text keys

    [Fact]
    public void Every_overlay_text_has_its_key_in_the_tables()
    {
        var dialogue = CsvTable.Read("dialogue.csv");
        var world = CsvTable.Read("world.csv");
        var ui = CsvTable.Read("ui.csv");
        foreach (var id in C.AllLineIds) Assert.True(dialogue.ContainsKey(id), $"dialogue.csv has no {id} (run tools/extract_strings.py)");
        foreach (var id in C.Overlay.AddedLineIds) Assert.Equal(C.FindLine(id)!.Line.Text, dialogue[id]);
        foreach (var topic in C.Data.Characters.SelectMany(c => c.AmbientTopics))
            Assert.True(world.ContainsKey(TextKeys.LabelOf(topic).Key), $"world.csv has no {TextKeys.LabelOf(topic).Key}");
        foreach (var exit in C.Rooms.SelectMany(r => r.Exits))
        {
            Assert.True(world.ContainsKey(TextKeys.LabelOf(exit).Key), TextKeys.LabelOf(exit).Key);
            Assert.True(world.ContainsKey(TextKeys.LockedOf(exit).Key), TextKeys.LockedOf(exit).Key);
            Assert.True(ui.ContainsKey("ui.travel." + exit.Travel), "ui.travel." + exit.Travel);
        }
        foreach (var c in C.Data.Connections) Assert.True(world.ContainsKey(TextKeys.LabelOf(c).Key), TextKeys.LabelOf(c).Key);
        foreach (var removed in C.Overlay.RemovedExits) Assert.False(world.ContainsKey(TextKeys.ExitLabel(removed)), removed);
        foreach (var region in C.Regions) Assert.True(ui.ContainsKey(TextKeys.NameOf(region).Key), TextKeys.NameOf(region).Key);
    }
}
