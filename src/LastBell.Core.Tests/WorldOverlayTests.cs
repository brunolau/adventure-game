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
/// The world overlay (content_ext/world_ext.json, Core README section 13): new rooms, hotspots, characters, items,
/// actions, side quests, epilogue shots, variant layers and connections, and relocations of existing actions, on top of
/// game.json (never edited). The sample (Overlays/sample_world_ext.json, test only) adds the 1995 room S90 with the
/// side quest Q90 and moves B19 and the P03 puzzle B22 into it.
/// </summary>
public sealed class WorldOverlayTests
{
    private static readonly GameContent Base = TestData.BaseContent;
    private static readonly string SampleText = File.ReadAllText(TestData.FixturePath(Path.Combine("overlays", "sample_world_ext.json")));
    private static readonly Lazy<GameContent> LazySample = new(() => Load(SampleText));
    private static readonly Lazy<IReadOnlyList<GameState>> LazySampleStates = new(() => MainStates(Sample));
    private static GameContent Sample => LazySample.Value;

    private static GameContent Load(string? world, string? dialogue = null, string? travel = null) =>
        GameContent.Load(TestData.GameJson, new ContentOverlays(dialogue, travel, world));

    private static string Errors(string? world, string? dialogue = null, string? travel = null)
    {
        var ex = Assert.Throws<ContentLoadException>(() => Load(world, dialogue, travel));
        return string.Join("\n", ex.Errors);
    }

    private static JsonObject SampleJson() => JsonNode.Parse(SampleText)!.AsObject();

    private static string Mutated(Action<JsonObject> change)
    {
        var root = SampleJson();
        change(root);
        return root.ToJsonString();
    }

    private static JsonObject Entry(JsonObject root, string list, string id, string idField = "id") =>
        root[list]!.AsArray().Select(n => n!.AsObject()).First(o => o[idField]?.GetValue<string>() == id);

    private static JsonObject Hotspot(JsonObject root, string id) =>
        root["rooms"]!.AsArray()[0]!["hotspots"]!.AsArray().Select(n => n!.AsObject()).First(o => o["id"]!.GetValue<string>() == id);

    private static IReadOnlyList<GameState> MainStates(GameContent c)
    {
        var states = new List<GameState> { c.InitialState };
        var s = c.InitialState;
        foreach (var row in TestData.MainRoute)
        {
            s = Driver.PrepareStep(c, s, row);
            s = Driver.Interact(c, s, c.GetAction(row.Action), row.PuzzleSolution);
            Assert.Equal(row.InventoryAfter, s.Inventory.OrderBy(x => x, StringComparer.Ordinal).ToList());
            Assert.Equal(Driver.ExpectedRoomAfter(c, row), s.Room);
            Driver.AssertInvariants(c, s);
            states.Add(s);
        }
        return states;
    }

    private static GameState SampleBefore(string actionId) =>
        LazySampleStates.Value[TestData.MainRoute.ToList().FindIndex(r => r.Action == actionId)];

    // ------------------------------------------------------------------ empty and live overlays

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("{}")]
    [InlineData("""{"format":"lastbell.world_ext","version":1,"characters":[],"items":[],"rooms":[],"hotspots":[],"exits":[],"connections":[],"quests":[],"actions":[],"epilogue":[],"visual_variant_layers":[],"relocations":[]}""")]
    public void An_empty_world_overlay_is_valid_and_plays_exactly_the_handoff(string? world)
    {
        var c = Load(world);
        Assert.True(c.Overlay.IsEmpty);
        Assert.False(c.Overlay.HasWorldChanges);
        string Json(object o) => System.Text.Json.JsonSerializer.Serialize(o, GameContent.JsonOptions);
        Assert.Equal(Json(Base.Data with { InitialState = null }), Json(c.Data with { InitialState = null }));
    }

    [Fact]
    public void The_live_world_overlay_loads_on_top_of_the_other_overlays()
    {
        // src/game/data/content_ext/world_ext.json (may be empty); TestData.Content is game.json + all three overlays.
        var c = TestData.Content;
        Assert.Equal(Base.Rooms.Count + c.Overlay.AddedRooms.Count, c.Rooms.Count);
        Assert.Equal(Base.Actions.Count + c.Overlay.AddedActions.Count, c.Actions.Count);
        Assert.Empty(ContentPlayability.Check(c));
    }

    // ------------------------------------------------------------------ the sample: what it adds

    [Fact]
    public void A_new_room_is_built_from_data_like_a_handoff_room()
    {
        var room = Sample.GetRoom("S90");
        Assert.Equal(1995, room.Era);
        Assert.Equal("Dúbravka", room.District);
        Assert.Equal("bg/S90.webp", room.BackgroundAsset);
        Assert.Equal(Base.GetRoom("S12").LayerOrder, room.LayerOrder); // the handoff's layer order by default
        Assert.Equal("S90", room.CameraFamily);
        Assert.Equal(new[] { "SAMPLE95" }, room.NpcIds);
        Assert.Equal(new[] { "entry.S90.001" }, room.FirstEntry.Select(l => l.LineId));
        Assert.Equal(new[] { "S90.SAMPLE95", "S90.board", "S90.dial", "S90.rhythm", "S90.rack" }, room.Hotspots.Select(h => h.Id));
        Assert.Equal("look.S90.board", room.Hotspots[1].LookLineId);
        Assert.Equal("look.S90.board.variant1", room.Hotspots[1].LookVariants[0].LineId);
        Assert.Equal(new[] { 1650, 440 }, room.Hotspots[4].LabelAnchor.ToArray()); // default: above the rect's centre
        Assert.Equal("S90.to_S12", Assert.Single(room.Exits).Id);
        Assert.Contains(Sample.GetRoom("S12").Exits, e => e.Id == "S12.to_S90");
        Assert.Contains(Sample.Data.Connections, c => c.From == "S12" && c.To == "S90" && c.Bidirectional);
        Assert.Equal(new[] { "S90" }, Sample.Overlay.AddedRooms);
        Assert.Equal(new[] { ("S12", "S90") }, Sample.Overlay.AddedConnections);
        Assert.Equal("room.S90.name", TextKeys.NameOf(room).Key);
        Assert.Equal(Base.Rooms.Count + 1, Sample.Rooms.Count);

        // The view model and the map treat it like any other room.
        var s = Driver.TravelTo(Sample, SampleBefore("B19"), "S90");
        var view = ViewBuilder.Room(Sample, s);
        Assert.Equal("S90", view.RoomId);
        Assert.Contains(view.Hotspots, h => h.Id == "S90.rack"); // visible_after G11
        Assert.Equal("SAMPLE95", Assert.Single(view.Npcs).CharacterId);
        var sheet = ViewBuilder.Map(Sample, s).Single(e => e.Year == 1995);
        var mapRoom = sheet.Rooms.Single(r => r.RoomId == "S90");
        Assert.True(mapRoom.Visited);
        Assert.Equal("Dúbravka", mapRoom.RegionId); // no travel overlay here: one region per district
        Assert.Contains("S90", Journal.Build(Sample, s).TimeMap.Single(e => e.Year == 1995).VisitedRooms.Select(r => r.RoomId));
    }

    [Fact]
    public void New_hotspots_characters_and_items_get_their_keys_and_derived_fields()
    {
        var sign = Sample.FindHotspot("S12.sample_sign")!;
        Assert.Equal("S12", sign.Room.Id);
        Assert.Equal("look.S12.sample_sign", TextKeys.BaseLookOf(sign.Hotspot).Key);
        Assert.Equal(Base.GetRoom("S12").NpcIds, sign.Room.NpcIds);
        Assert.Equal(Base.GetRoom("S12").Hotspots.Select(h => h.Id).Append("S12.sample_sign"), sign.Room.Hotspots.Select(h => h.Id));
        var resident = Sample.FindCharacter("SAMPLE95")!;
        Assert.Equal(new[] { "S90" }, resident.Rooms);
        Assert.Equal("char.SAMPLE95.name", TextKeys.NameOf(resident).Key);
        var note = Sample.GetItem("SAMPLE_NOTE");
        Assert.Equal("Q90A", note.Origin);
        Assert.Equal("items/SAMPLE_NOTE.webp", note.Icon);
        Assert.Equal("item.SAMPLE_NOTE", TextKeys.LookOf(note).Key);
        Assert.Equal("retain", note.Disposition);
        Assert.Equal(new[] { "SAMPLE_NOTE", "SAMPLE_STAMP", "SAMPLE_CARD" }, Sample.Overlay.AddedItems);
        Assert.Equal(Base.Items.Count + 3, Sample.Items.Count);
        Assert.Equal(new[] { "S90.SAMPLE95", "S90.board", "S90.dial", "S90.rhythm", "S90.rack", "S12.sample_sign" }, Sample.Overlay.AddedHotspots);
    }

    [Fact]
    public void A_new_side_quest_has_hints_step_texts_an_epilogue_shot_and_a_variant_layer()
    {
        var quest = Sample.FindQuest("Q90")!;
        Assert.True(quest.IsSide);
        Assert.Equal(new[] { "Q90A", "Q90B", "Q90C", "Q90D" }, quest.Actions);
        Assert.Equal(3, quest.Hints.Count);
        Assert.Equal("Fotka vnútrobloku v albume.", Quests.RewardOf(quest).Fallback);
        Assert.Equal("quest.Q90.hint.3", TextKeys.HintOf(quest, 2).Key);
        var a = Sample.GetAction("Q90A");
        Assert.Equal("talk", a.Animation);
        Assert.Equal("atomic_after_validation_and_puzzle_before_lines", a.CommitPolicy);
        Assert.Equal(new TextRef("action.Q90A.hint_step", "Porozprávaj sa so susedkou vo vnútrobloku o tom, čo hľadá."), Hints.StepText(a));
        Assert.Equal("Q90", Sample.GetQuestOf("Q90C").Id);
        Assert.Equal("inventory_combine", Sample.GetAction("Q90C").Animation);
        Assert.Equal("show_item", Sample.GetAction("Q90D").Animation);
        Assert.Equal(new TextRef(Hints.StepKey("G01"), Base.GetAction("G01").Label), Hints.StepText(Sample.GetAction("G01")));

        var shot = Sample.Data.Epilogue[^1];
        Assert.Equal(Base.Data.Epilogue.Count + 1, Sample.Data.Epilogue.Count);
        Assert.Equal(("Q90", "Q90D"), (shot.Quest, shot.After));
        var layer = Sample.Data.VisualVariantLayers[^1];
        Assert.Equal(("S90", "Q90D", "variants/S90_card_on_board.webp"), (layer.Room, layer.After, layer.Asset));
    }

    [Fact]
    public void The_new_side_quest_plays_through_the_resolver_and_reaches_the_album_and_the_ending()
    {
        var s = Driver.TravelTo(Sample, SampleBefore("B19"), "S90");
        var resident = Sample.FindHotspot("S90.SAMPLE95")!.Hotspot;
        Assert.Contains(Dialogue.TopicsFor(Sample, s, resident), t => t.Id == "Q90A" && t.IsStoryAction);
        Assert.Equal(QuestStatus.NotStarted, Quests.StatusOf(Sample.FindQuest("Q90")!, s));
        // Hints follow the step: level 3 is the overlay's own step text.
        Assert.Equal("Q90A", Hints.CurrentStep(Sample, s, "Q90")!.Id);
        foreach (var id in new[] { "Q90A", "Q90B", "Q90C" }) s = Driver.Perform(Sample, s, Sample.GetAction(id));
        Assert.Equal(new[] { "SAMPLE_CARD" }, s.Inventory.Where(i => i.StartsWith("SAMPLE_", StringComparison.Ordinal)));
        Assert.Equal("Q90D", Hints.CurrentStep(Sample, s, "Q90")!.Id);
        for (var i = 0; i < 3; i++) s = Hints.RevealNext(Sample, s, "Q90");
        var hints = Hints.Revealed(Sample, s, "Q90");
        Assert.Equal("action.Q90C.objective", hints[0].Text.Key); // the objective of the step that enabled it
        Assert.Equal("room.S90.name", hints[1].Args.Single(a => a.Name == "room").Value.Key);
        Assert.Equal("action.Q90D.hint_step", hints[2].Text.Key);
        Assert.Contains(ViewBuilder.Inventory(Sample, s), i => i.Id == "SAMPLE_CARD" && i.Icon == "items/SAMPLE_CARD.webp");
        s = Driver.Perform(Sample, s, Sample.GetAction("Q90D"));
        Assert.Contains("Q90", s.SideRewards);
        Assert.Equal(QuestStatus.Done, Quests.StatusOf(Sample.FindQuest("Q90")!, s));
        Assert.True(WorldEffects.VariantLayers(Sample, s, "S90").Single().Visible || WorldEffects.VariantLayers(Sample, s, "S90").Single().DeferredUntilReentry);
        Assert.Equal("look.S12.sample_sign.variant1", GameRules.LookAt(Sample.FindHotspot("S12.sample_sign")!.Hotspot, s).Key);
        var album = Journal.Build(Sample, s).Album.Single(e => e.QuestId == "Q90");
        Assert.Equal($"epilogue.{Sample.Data.Epilogue.Count}.shot", album.Shot.Key);
        Assert.Equal("Q90", Epilogue.Select(Sample, s).Single().QuestId);
        Assert.Equal("SAMPLE95", Epilogue.Select(Sample, s).Single().SpeakerId);
    }

    // ------------------------------------------------------------------ relocations

    [Fact]
    public void A_relocation_moves_only_the_place_of_an_action()
    {
        Assert.Equal(new[] { "B19", "B22" }, Sample.Overlay.Relocations.Select(r => r.Action));
        var moved = Sample.FindRelocation("B22")!;
        Assert.Equal(new RelocationInfo("B22", "S30", "S30.dial", "S90", "S90.dial", HotspotRetired: true), moved);
        var b22 = Sample.GetAction("B22");
        Assert.Equal(("S90", "S90.dial"), (b22.Room, b22.Target));
        string Json(ActionDef x) => System.Text.Json.JsonSerializer.Serialize(x, GameContent.JsonOptions);
        Assert.Equal(Json(Base.GetAction("B22") with { Room = "S90", Target = "S90.dial", HintStep = b22.HintStep }), Json(b22));
        Assert.Equal("action.B22.hint_step", Hints.StepText(b22).Key);
        // The retired hotspot is gone; the kept one (B19's S17.rhythm) is look-only now.
        Assert.Null(Sample.FindHotspot("S30.dial"));
        Assert.Equal(new[] { "S30.dial" }, Sample.Overlay.RetiredHotspots);
        Assert.NotNull(Sample.FindHotspot("S17.rhythm"));
        Assert.DoesNotContain(Sample.Actions, a => a.Target == "S17.rhythm");
        Assert.Null(Sample.FindRelocation("B20"));
    }

    [Fact]
    public void The_relocated_puzzle_opens_in_the_new_room_and_the_old_place_has_nothing_left()
    {
        var before = SampleBefore("B22");
        var atOldPlace = Driver.TravelTo(Sample, before, "S30");
        Assert.DoesNotContain(ViewBuilder.Room(Sample, atOldPlace).Hotspots, h => h.Id == "S30.dial");
        Assert.False(GameRules.ValidAction(Sample, atOldPlace, Sample.GetAction("B22")));
        var s = Driver.TravelTo(Sample, before, "S90");
        var r = GameRules.ResolveInteraction(Sample, s, new Hit.Hotspot("S90.dial"), PointerButton.Left);
        Assert.Equal("B22", Assert.IsType<Resolution.Action>(r).ActionDef.Id);
        var quest = Sample.GetQuestOf("B22");
        var place = Hints.TextFor(Sample, s, quest, Sample.GetAction("B22"), 2);
        Assert.Equal("room.S90.name", place.Args.Single(a => a.Name == "room").Value.Key);
        var opened = Puzzles.Open(Sample, s, "B22");
        Assert.Equal(GameMode.Puzzle, opened.Mode);
        var solution = TestData.MainRoute.Single(x => x.Action == "B22").PuzzleSolution;
        Assert.True(Puzzles.Submit(Sample, opened, "B22", solution).Solved);
    }

    [Fact]
    public void The_walkthrough_stays_completable_with_recomputed_paths_and_every_side_quest_after_the_credits()
    {
        var states = LazySampleStates.Value; // asserts the inventory and room after each of the 94 steps
        var end = states[^1];
        Assert.True(end.IsDone("F17"));
        Assert.Equal("S90", states[TestData.MainRoute.ToList().FindIndex(r => r.Action == "B22") + 1].Room);
        var s = end;
        foreach (var id in TestData.OptionalRoute) s = Driver.Perform(Sample, s, Sample.GetAction(id));
        s = Driver.PerformRemaining(Sample, s);
        Assert.Equal(Sample.Actions.Count, s.Done.Length);
        Assert.Equal(10, s.SideRewards.Length);
        Assert.Equal(10, Epilogue.Select(Sample, s).Count);
        var reachable = Navigation.ConnectedRooms(Sample, s, includePortals: true);
        Assert.All(Sample.Rooms, r => Assert.Contains(r.Id, reachable));
    }

    public static IEnumerable<object[]> Seeds() => Enumerable.Range(0, 24).Select(i => new object[] { i });

    [Theory]
    [MemberData(nameof(Seeds))]
    public void Random_legal_orders_finish_every_action_of_the_sample(int seed)
    {
        var rng = new Random(seed + 1000);
        var s = Sample.InitialState;
        for (var i = 0; i <= Sample.Actions.Count; i++)
        {
            var options = Driver.Enabled(Sample, s);
            if (options.Count == 0) break;
            s = Driver.Perform(Sample, s, options[rng.Next(options.Count)]);
            Driver.AssertInvariants(Sample, s);
        }
        Assert.Equal(Sample.Actions.Count, s.Done.Length);
    }

    [Fact]
    public void The_playability_check_finishes_the_handoff_the_live_content_and_the_sample_in_every_order()
    {
        Assert.Empty(ContentPlayability.Check(Base, randomOrders: 8));
        Assert.Empty(ContentPlayability.Check(TestData.Content));
        Assert.Empty(ContentPlayability.Check(Sample, randomOrders: 8));
        Assert.Null(ContentPlayability.Play(Sample, "world overlay first", out var order));
        Assert.Equal("Q90A", order.First(id => id.StartsWith("Q90", StringComparison.Ordinal)));
        Assert.Equal(Sample.Actions.Count, order.Count);
    }

    public static IEnumerable<object[]> RelocatableActions() =>
        TestData.BaseContent.Actions.Where(a => !a.IsInventoryAction && !TestData.BaseContent.FindHotspot(a.Target)!.Hotspot.IsNpc &&
                                                 TestData.BaseContent.GetRoom(a.Room).Era == 1995)
            .Select(a => new object[] { a.Id });

    /// <summary>Every 1995 prop action can move into a new room: the static checks raise no false alarm on the handoff's own design.</summary>
    [Theory]
    [MemberData(nameof(RelocatableActions))]
    public void Any_1995_prop_action_can_be_relocated_into_the_new_room(string actionId)
    {
        var world = Mutated(root =>
        {
            root["rooms"]!.AsArray()[0]!["hotspots"]!.AsArray().Add(JsonNode.Parse(
                """{"id":"S90.moved","name":"Presunutý cieľ","look":"Test.","rect":[600,300,120,120],"interaction_point":[660,900]}"""));
            root["relocations"] = new JsonArray(JsonNode.Parse($$"""{"action":"{{actionId}}","to_hotspot":"S90.moved","hint_step":"Test."}"""));
        });
        var c = Load(world);
        Assert.Equal("S90", c.GetAction(actionId).Room);
    }

    // ------------------------------------------------------------------ overlays on top of the world overlay

    [Fact]
    public void The_dialogue_overlay_can_extend_world_lines_and_give_new_characters_topics()
    {
        const string dialogue = """
            {"sequences":[{"action":"Q90A","lines":["action.Q90A.001",{"key":"action.Q90A.x01","speaker":"SAMPLE95","sk":"Hľadám už od rána."},"action.Q90A.002","action.Q90A.003"]}],
             "topics":[{"id":"SAMPLE95.extra 1","character":"SAMPLE95","label":"Dvor","lines":[{"key":"topic.SAMPLE95.extra 1.001","speaker":"ADAM","sk":"Pekný dvor."},{"key":"topic.SAMPLE95.extra 1.002","speaker":"SAMPLE95","sk":"Keď sa nekleple."}]}]}
            """;
        var c = Load(SampleText, dialogue);
        Assert.Equal(new[] { "action.Q90A.001", "action.Q90A.x01", "action.Q90A.002", "action.Q90A.003" }, c.GetAction("Q90A").Lines.Select(l => l.LineId));
        Assert.Empty(c.Overlay.RetiredLines);
        Assert.Contains("SAMPLE95.extra 1", c.Overlay.AddedTopics);
        var s = Driver.TravelTo(c, SampleBefore("B19"), "S90");
        Assert.Contains(Dialogue.TopicsFor(c, s, c.FindHotspot("S90.SAMPLE95")!.Hotspot), t => t.Id == "SAMPLE95.extra 1" && !t.IsStoryAction);
    }

    [Fact]
    public void People_standing_in_a_room_may_speak_in_its_actions_and_a_counter_speaks_under_its_own_name()
    {
        // dialogue_ext: the resident of the new room joins the relocated B19 (a prop action without speakers but Adam).
        var dialogue = """{"sequences":[{"action":"B19","lines":[""" +
            string.Join(",", Sample.GetAction("B19").Lines.Select(l => $"\"{l.LineId}\"")) +
            """,{"key":"action.B19.x01","speaker":"SAMPLE95","sk":"Tie čiarky kreslili deti z krúžku."}]}]}""";
        var c = Load(SampleText, dialogue);
        Assert.Equal("SAMPLE95", c.GetAction("B19").Lines[^1].Speaker);
        Assert.Contains("does not take part", Errors(null, dialogue: dialogue.Replace("SAMPLE95", "ZITA")));
        // world_ext: a new action on a counter NPC is spoken by the counter's speaker (FOTO speaks as ALENA).
        var world = Mutated(root =>
        {
            root["actions"]!.AsArray().Add(JsonNode.Parse("""
                {"id":"Q90E","room":"S24","target":"S24.FOTO","kind":"topic","label":"Fotky dvora","quest":"Q90","journal_text":"x","hint_step":"x",
                 "lines":[{"key":"action.Q90E.001","speaker":"ADAM","sk":"Robíte aj fotky dvorov?"},{"key":"action.Q90E.002","speaker":"ALENA","sk":"Aj dvorov. Tie sa nehýbu."}]}
                """));
            Entry(root, "quests", "Q90")["actions"]!.AsArray().Add("Q90E");
        });
        Assert.Equal("ALENA", Load(world).GetAction("Q90E").Lines[1].Speaker);
    }

    private const string Regions1995 = """
        {"regions":[
          {"id":"Dúbravka","era":1995,"rooms":["S11","S12","S13","S14","S15","S16","S17","S18"],"hubs":["S11"]},
          {"id":"Karlova Ves","era":1995,"rooms":["S19","S20"],"hubs":["S19"]},
          {"id":"Staré Mesto","era":1995,"rooms":["S21","S22","S23","S24"],"hubs":["S21"]},
          {"id":"Ružinov","era":1995,"rooms":["S25","S26","S27"],"hubs":["S25"]},
          {"id":"Petržalka","era":1995,"rooms":["S28","S29","S30"],"hubs":["S28"]}]}
        """;

    [Fact]
    public void A_new_room_joins_the_map_region_it_names()
    {
        var world = Mutated(root => root["rooms"]!.AsArray()[0]!["region"] = "Dúbravka");
        var c = Load(world, travel: Regions1995);
        Assert.Equal("Dúbravka", c.RegionOf("S90").Id);
        Assert.False(c.IsHub("S90"));
        Assert.Contains("S90", c.RegionsOf(1995).Single(r => r.Id == "Dúbravka").Rooms);
        Assert.Contains("belongs to no region", Errors(SampleText, travel: Regions1995));
        Assert.Contains("is not a region of 1995", Errors(Mutated(root => root["rooms"]!.AsArray()[0]!["region"] = "Nikde"), travel: Regions1995));
        Assert.Contains("has no map regions", Errors(world));
        // The live travel overlay (2020 bus, regions of every era) with the region named: loads.
        var live = Load(world, TestData.OverlayText(ContentOverlays.DialogueExtFile), TestData.OverlayText(ContentOverlays.TravelExtFile));
        Assert.Equal("Dúbravka", live.RegionOf("S90").Id);
    }

    // ------------------------------------------------------------------ saves

    [Fact]
    public void Saves_from_before_the_world_overlay_still_load_and_new_saves_round_trip()
    {
        var old = TestData.StateAfter("B21");
        var json = SaveCodec.Serialize(old);
        Assert.True(SaveCodec.TryLoad(Sample, json, out var loaded, out _, out var reason), reason);
        Assert.Equal(old.Done, loaded!.Done);
        Assert.Equal(old.Inventory, loaded.Inventory);
        // Continue the old save: B22 is played in its new room.
        var s = Driver.Perform(Sample, Playback.FinishAll(Sample, loaded), Sample.GetAction("B22"));
        Assert.True(s.IsDone("B22"));
        Assert.Equal("S90", s.Room);
        // A save with the overlay's ids round-trips (and is refused, without touching anything, by content without them).
        var withQuest = Driver.Perform(Sample, Driver.Perform(Sample, s, Sample.GetAction("Q90A")), Sample.GetAction("Q90B"));
        var saved = SaveCodec.Serialize(withQuest);
        Assert.Equal(withQuest, SaveCodec.Load(Sample, saved));
        Assert.False(SaveCodec.TryLoad(Base, saved, out _, out var error, out _));
        Assert.Equal(UiText.SaveCorrupt, error);
        // A save made in the middle of a world-overlay line resumes on that line.
        var mid = GameRules.CommitAction(Sample, Dialogue.OpenMenu(Driver.TravelTo(Sample, s, "S90")), "Q90A");
        Assert.Equal("action.Q90A.001", mid.ActiveLineId);
        Assert.Equal("action.Q90A.001", SaveCodec.Load(Sample, SaveCodec.Serialize(mid)).ActiveLineId);
    }

    // ------------------------------------------------------------------ bad overlays

    public static IEnumerable<object[]> BadWorldOverlays()
    {
        object[] Bad(Action<JsonObject> change, string expected) => new object[] { Mutated(change), expected };
        JsonArray Arr(JsonObject root, string key) => root[key]!.AsArray();
        JsonObject Room(JsonObject root) => Arr(root, "rooms")[0]!.AsObject();
        JsonObject Act(JsonObject root, string id) => Entry(root, "actions", id);
        return new[]
        {
            // header, unknown fields
            new object[] { """{"format":"lastbell.dialogue_ext"}""", "format: expected 'lastbell.world_ext'" },
            new object[] { """{"version":2}""", "only version 1" },
            new object[] { """{"topics":[]}""", "belong in dialogue_ext.json" },
            new object[] { """[1]""", "must be a JSON object" },
            Bad(r => Room(r)["gives"] = "x", "gives: field not allowed"),
            Bad(r => Entry(r, "characters", "SAMPLE95")["ambient_topics"] = new JsonArray(), "belong in dialogue_ext.json topics"),
            // ids
            Bad(r => Room(r)["id"] = "S12", "room 'S12' already exists"),
            Bad(r => Room(r)["id"] = "Yard", "not a valid room id"),
            Bad(r => Act(r, "Q90A")["id"] = "G01", "action 'G01' already exists"),
            Bad(r => Entry(r, "items", "SAMPLE_NOTE")["id"] = "TOOLS", "item 'TOOLS' already exists"),
            Bad(r => Entry(r, "quests", "Q90")["id"] = "Q1", "quest 'Q1' already exists"),
            Bad(r => Arr(r, "items").Add(JsonNode.Parse("""{"id":"SAMPLE_NOTE","name":"a","look":"b","purpose":"c"}""")), "is defined twice"),
            Bad(r => Hotspot(r, "S90.board")["id"] = "S12.board", "a hotspot id is '<room>.<name>'"),
            Bad(r => Hotspot(r, "S90.SAMPLE95")["id"] = "S90.resident", "an NPC hotspot is '<room>.<character>'"),
            Bad(r => Entry(r, "hotspots", "S12.sample_sign")["id"] = "S12.notice", "hotspot 'S12.notice' already exists"),
            Bad(r => Entry(r, "hotspots", "S12.sample_sign")["room"] = "S90", "list its hotspots in rooms[].hotspots"),
            // geometry
            Bad(r => Hotspot(r, "S90.board")["interaction_point"] = new JsonArray(400, 500), "is not inside the walk polygon"),
            Bad(r => Hotspot(r, "S90.board")["rect"] = new JsonArray(300, 500, 40, 200), "at least 44x44"),
            Bad(r => Room(r)["spawn"] = new JsonArray(10, 10), "spawn: [10, 10] is not inside"),
            Bad(r => Room(r)["walk_polygon"] = JsonNode.Parse("[[0,0],[10,10]]"), "at least 3 points"),
            Bad(r => Room(r)["layer_order"] = JsonNode.Parse("""["background","sky"]"""), "unknown layer 'sky'"),
            Bad(r => Room(r)["background_asset"] = "S90.webp", "under bg/ or bg_natural/"),
            Bad(r => Room(r)["era"] = 1999, "unknown era 1999"),
            Bad(r => Room(r)["npc_ids"] = new JsonArray("ELA"), "npc_ids: [ELA]"),
            // graph
            Bad(r => { r.Remove("connections"); r.Remove("exits"); Room(r)["exits"] = new JsonArray(); }, "a room needs at least one exit"),
            Bad(r => r.Remove("connections"), "no connection leads from"),
            Bad(r => r.Remove("exits"), "room 'S12' needs an exit to 'S90'"),
            Bad(r => { r.Remove("connections"); r.Remove("exits"); Room(r)["exits"]![0]!["to"] = "S30"; Room(r)["exits"]![0]!["id"] = "S90.to_S30"; }, "no connection leads"),
            Bad(r => Arr(r, "exits")[0]!["to"] = "S31", "eras are changed only by the chronometer"),
            // items flow
            Bad(r => Act(r, "Q90A")["gives"] = new JsonArray(), "no action gives item 'SAMPLE_NOTE'"),
            Bad(r => Act(r, "Q90A")["gives"] = new JsonArray("SAMPLE_NOTE", "TOOLS"), "'TOOLS' is a game.json item; it already has its one origin"),
            Bad(r => { Act(r, "Q90C")["consumes"] = new JsonArray("SAMPLE_STAMP", "TOOLS"); }, "'TOOLS' is a game.json item; consuming it"),
            Bad(r => Act(r, "Q90B")["consumes"] = new JsonArray("SAMPLE_CARD"), "is not declared in requires_items"),
            Bad(r => Act(r, "Q90A")["requires_done"] = new JsonArray("Q90D"), "(a cycle)"),
            Bad(r => Act(r, "Q90D")["requires_items"] = new JsonArray("SAMPLE_CARD", "SAMPLE_NOTE"), "done first, 'Q90B' would make 'Q90D' impossible"),
            Bad(r => Act(r, "Q90A")["gives"] = new JsonArray("SAMPLE_NOTE", "SAMPLE_CARD"), "an item has exactly one origin"),
            Bad(r => Entry(r, "items", "SAMPLE_NOTE")["origin"] = "Q90B", "origin: 'Q90B' but 'Q90A' gives the item"),
            Bad(r => Entry(r, "items", "SAMPLE_NOTE")["icon"] = "SAMPLE_NOTE.png", "under items/"),
            Bad(r => Entry(r, "items", "SAMPLE_NOTE")["disposition"] = "consume", "every item is 'retain'"),
            // actions
            Bad(r => Act(r, "Q90A").Remove("hint_step"), "hint_step: missing"),
            Bad(r => Act(r, "Q90A")["puzzle"] = "P01", "cannot have a puzzle"),
            Bad(r => Act(r, "Q90A")["cutscene"] = "CS01", "cannot have a cutscene"),
            Bad(r => Act(r, "Q90A")["quest"] = "Q1", "is not a quest of this overlay"),
            Bad(r => Act(r, "Q90A")["kind"] = "talk", "unknown action kind 'talk'"),
            Bad(r => Act(r, "Q90A")["room"] = "S12", "is not in room 'S12'"),
            Bad(r => Act(r, "Q90B")["kind"] = "topic", "a topic is chosen in the conversation with an NPC"),
            Bad(r => { var a = Act(r, "Q90D"); a.Remove("selected_item"); }, "a left click on an NPC opens the conversation"),
            Bad(r => Act(r, "Q90C")["room"] = "S90", "combine actions use room 'inventory'"),
            Bad(r => Act(r, "Q90C")["symmetric"] = "yes", "must be true or false"),
            Bad(r => Act(r, "Q90A")["once"] = false, "every action happens at most once"),
            Bad(r => Act(r, "Q90A")["animation"] = "dance", "unknown animation 'dance'"),
            Bad(r => Act(r, "Q90A")["commit_policy"] = "lazy", "commit_policy: only"),
            Bad(r => Act(r, "Q90A")["requires_done"] = new JsonArray("NOPE"), "unknown action 'NOPE'"),
            Bad(r => Act(r, "Q90A")["lines"]![0]!["key"] = "action.Q90B.009", "must be 'action.Q90A.<n>'"),
            Bad(r => Act(r, "Q90A")["lines"]![0]!["key"] = "action.G01.001", "must be 'action.Q90A.<n>'"),
            Bad(r => Act(r, "Q90A")["lines"]![0]!["speaker"] = "ELA", "does not take part in action 'Q90A'"),
            Bad(r => Act(r, "Q90A")["lines"] = new JsonArray(), "lines: empty"),
            Bad(r => Act(r, "Q90A")["label"] = "two\nlines", "no line breaks"),
            Bad(r =>
            {
                Arr(r, "actions").Add(JsonNode.Parse("""{"id":"Q90E","room":"S90","target":"S90.dial","kind":"click","label":"x","quest":"Q90","journal_text":"x","hint_step":"x","lines":[{"key":"action.Q90E.001","speaker":"ADAM","sk":"x"}]}"""));
                Entry(r, "quests", "Q90")["actions"]!.AsArray().Add("Q90E");
            }, "'B22' and 'Q90E' have the same trigger (click:S90.dial+-)"),
            Bad(r =>
            {
                Arr(r, "actions").Add(JsonNode.Parse("""{"id":"Q90E","room":"S90","target":"S90.board","kind":"click","label":"x","quest":"Q90","journal_text":"x","hint_step":"x","requires_items":["SAMPLE_NOTE"],"selected_item":"SAMPLE_NOTE","lines":[{"key":"action.Q90E.001","speaker":"ADAM","sk":"x"}]}"""));
                Entry(r, "quests", "Q90")["actions"]!.AsArray().Add("Q90E");
            }, "needs 'SAMPLE_NOTE', which 'Q90B' consumes"),
            // quests, epilogue, layers
            Bad(r => Entry(r, "quests", "Q90")["hints"] = new JsonArray("a", "b"), "exactly three hints"),
            Bad(r => Entry(r, "quests", "Q90")["actions"] = new JsonArray("Q90A", "Q90B", "Q90D"), "'Q90C' has quest 'Q90' but is not listed"),
            Bad(r => Entry(r, "quests", "Q90")["actions"] = new JsonArray("Q90A", "Q90B", "Q90C", "Q90D", "G01"), "is not an action of this overlay"),
            Bad(r => Entry(r, "quests", "Q90")["completion"] = "G01", "completion: 'G01' is not one of the quest's actions"),
            Bad(r => Entry(r, "quests", "Q90")["type"] = "main", "side quests only"),
            Bad(r => Arr(r, "epilogue")[0]!["quest"] = "Q1", "game.json quests keep their own shot"),
            Bad(r => Arr(r, "epilogue")[0]!["after"] = "G01", "is not an action of quest 'Q90'"),
            Bad(r => Arr(r, "epilogue")[0]!["line"] = "NOBODY: x", "unknown speaker 'NOBODY'"),
            Bad(r => Arr(r, "visual_variant_layers")[0]!["asset"] = "bg/S90_x.webp", "under variants/"),
            // relocations
            Bad(r => Arr(r, "relocations")[0]!["action"] = "G01", "in 1995, 'G01' happens in 2020; a relocation stays in the same era"),
            Bad(r => Arr(r, "relocations")[0]!["action"] = "B16", "a combination in the bag"),
            Bad(r => Arr(r, "relocations")[0]!["action"] = "Q90A", "is a new action; put it into its room directly"),
            Bad(r => Arr(r, "relocations")[0]!["to_hotspot"] = "S90.SAMPLE95", "the action keeps its kind of target"),
            Bad(r => Arr(r, "relocations")[0]!["to_hotspot"] = "S17.rhythm", "a relocation moves it to another room"),
            Bad(r => Arr(r, "relocations")[0]!["requires_done"] = new JsonArray(), "a relocation moves the action only"),
            Bad(r => Arr(r, "relocations").Add(JsonNode.Parse("""{"action":"B19","to_hotspot":"S90.board","hint_step":"x"}""")), "relocated twice"),
            Bad(r => Arr(r, "relocations").Add(JsonNode.Parse("""{"action":"B04","to_hotspot":"S90.rack","hint_step":"x","retire_hotspot":true}""")), "'S16.deck' is still the target of B06"),
            // softlocks the playability check finds
            Bad(r => Hotspot(r, "S90.board")["hide_after"] = new JsonArray("Q90A"), "softlock"),
            Bad(r => Hotspot(r, "S90.board")["visible_after"] = new JsonArray("Q90D"), "softlock"),
            Bad(r => { r["rooms"]![0]!["exits"]![0]!["requires_done"] = new JsonArray("Q90D"); Arr(r, "exits")[0]!["requires_done"] = new JsonArray("Q90D"); Arr(r, "connections")[0]!["requires_done"] = new JsonArray("Q90D"); }, "softlock"),
        };
    }

    [Theory]
    [MemberData(nameof(BadWorldOverlays))]
    public void A_broken_world_overlay_fails_loudly_with_the_path_of_the_problem(string world, string expected)
    {
        var errors = Errors(world);
        Assert.Contains(expected, errors);
        Assert.All(errors.Split('\n'), e => Assert.True(e.StartsWith("$world_ext", StringComparison.Ordinal) || e.StartsWith("$playability", StringComparison.Ordinal), e));
    }
}
