using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Tests.Support;

namespace LastBell.Core.Tests;

/// <summary>Causal effects, butterfly effects, variant layers, the temporal cache, epilogue and postgame.</summary>
public sealed class WorldEffectsTests
{
    private static readonly GameContent C = TestData.Content;

    [Fact]
    public void Causal_effects_appear_exactly_after_their_trigger()
    {
        var before = TestData.StateBefore("I17");
        Assert.DoesNotContain(WorldEffects.CausalEffectsAt(C, before, "S15"), e => e.Effect.After == "I17");
        var after = TestData.StateAfter("I17");
        Assert.Contains(WorldEffects.CausalEffectsAt(C, after, "S15"), e => e.Effect.After == "I17");
        Assert.Contains(WorldEffects.CausalEffectsAt(C, after, "S44"), e => e.Effect.After == "I17");
        // No unlisted room ever gets an effect.
        var listed = C.Data.CausalEffects.SelectMany(e => e.At).ToHashSet();
        Assert.All(C.Rooms.Where(r => !listed.Contains(r.Id)), r => Assert.Empty(WorldEffects.CausalEffectsAt(C, TestData.MainEnd, r.Id)));
    }

    [Fact]
    public void Side_quest_effects_change_s43_and_s47_but_create_no_quests()
    {
        var s = TestData.MainEnd;
        var questsBefore = C.Quests.Count(q => Quests.StatusOf(q, s) != QuestStatus.NotStarted);
        Assert.DoesNotContain(WorldEffects.CausalEffectsAt(C, s, "S43"), e => e.Effect.After == "Q4C");
        foreach (var id in C.FindQuest("Q4")!.Actions) s = Driver.Perform(C, s, C.GetAction(id));
        Assert.Contains(WorldEffects.CausalEffectsAt(C, s, "S43"), e => e.Effect.After == "Q4C");
        Assert.Equal(questsBefore + 1, C.Quests.Count(q => Quests.StatusOf(q, s) != QuestStatus.NotStarted));
    }

    [Fact]
    public void Butterfly_tree_changes_s17_and_s55_variants_after_e10_and_photo_effects_are_deferred_until_reentry()
    {
        var before = TestData.StateBefore("E10");
        Assert.All(WorldEffects.VariantLayers(C, before, "S17"), l => Assert.False(l.Visible));
        Assert.False(WorldEffects.IsTriggered(C, before, "BF_TREE"));
        var after = TestData.StateAfter("E10");
        Assert.True(WorldEffects.IsTriggered(C, after, "BF_TREE"));
        Assert.All(WorldEffects.VariantLayers(C, after, "S17"), l => Assert.True(l.Visible)); // hero is elsewhere (1982)
        var at55 = Driver.TravelTo(C, after, "S55");
        Assert.Contains(WorldEffects.VariantLayers(C, at55, "S55"), l => l.Visible && l.Layer.Asset.Contains("linden"));
        // The 2020 retrieval hotspot exists only after E10.
        Assert.False(GameRules.IsVisible(C.FindHotspot("S55.cache")!.Hotspot, before));
        Assert.True(GameRules.IsVisible(C.FindHotspot("S55.cache")!.Hotspot, at55));
    }

    [Fact]
    public void A_change_committed_inside_the_affected_room_takes_effect_on_the_next_entry()
    {
        var s = TestData.ReadyFor("E08");
        Assert.Equal("S61", s.Room);
        var committed = Playback.FinishAll(C, GameRules.CommitAction(C, s, "E08"));
        var niche = WorldEffects.VariantLayers(C, committed, "S61").Single(l => l.Layer.After == "E08");
        Assert.False(niche.Visible);
        Assert.True(niche.DeferredUntilReentry);
        var exit = C.GetRoom("S61").Exits[0];
        var away = Playback.FinishAll(C, Navigation.Travel(C, committed, exit.Id));
        var back = Playback.FinishAll(C, Navigation.Travel(C, away, C.GetRoom(exit.To).Exits.First(e => e.To == "S61").Id));
        Assert.True(WorldEffects.VariantLayers(C, back, "S61").Single(l => l.Layer.After == "E08").Visible);
    }

    [Fact]
    public void Butterfly_jana_is_optional_and_never_needed_for_the_main_story()
    {
        Assert.False(WorldEffects.IsTriggered(C, TestData.MainEnd, "BF_JANA"));
        var s = TestData.MainEnd;
        foreach (var id in new[] { "Q9A", "Q9B", "Q9C" }) s = Driver.Perform(C, s, C.GetAction(id));
        Assert.True(WorldEffects.IsTriggered(C, s, "BF_JANA"));
        foreach (var room in new[] { "S15", "S54", "S44" })
            Assert.Contains(WorldEffects.VariantLayers(C, s, room), l => l.Visible);
        Assert.Equal(2, WorldEffects.Butterflies(C, s).Count);
    }

    [Fact]
    public void Temporal_cache_is_one_object_stored_in_1982_and_retrieved_once_in_2020()
    {
        var stages = TestData.MainStates.Select(s => TemporalCache.StatusOf(C, s).Stage).ToList();
        Assert.Equal(stages.OrderBy(x => x), stages); // monotonic lifecycle
        Assert.All(TestData.MainStates, s => Assert.True(TemporalCache.InvariantHolds(C, s)));
        var stored = TestData.StateAfter("E08");
        var status = TemporalCache.StatusOf(C, stored);
        Assert.Equal(CacheStage.Stored, status.Stage);
        Assert.True(status.NicheReserved);
        Assert.Null(status.CarriedItem);
        Assert.False(status.RetrievalAvailable); // E10 and E11 are required first (no softlock order)
        var retrieved = TestData.StateAfter("D05");
        Assert.Equal("SEALED_OLD", TemporalCache.StatusOf(C, retrieved).CarriedItem);
        // Returning to 1982 never gives a second (young) object.
        var back = Driver.TravelTo(C, TestData.MainEnd, "S61");
        Assert.All(new[] { "E04", "E06", "E08", "D05" }, id => Assert.False(GameRules.ValidAction(C, back, C.GetAction(id))));
        Assert.IsType<Resolution.Look>(GameRules.ResolveInteraction(C, back, new Hit.Hotspot("S61.niche"), PointerButton.Left));
        Assert.DoesNotContain(back.Inventory, i => i is "BRIDGE_NEW" or "SEALED_NEW" or "SEALED_OLD");
        Assert.False(GameRules.ValidAction(C, back, C.GetAction("J05")));
        Assert.Equal(CacheStage.Used, TemporalCache.StatusOf(C, back).Stage);
    }

    [Fact]
    public void Epilogue_plays_only_completed_episodes_in_order()
    {
        Assert.True(Epilogue.GoesStraightToCredits(C, TestData.MainEnd));
        var s = TestData.MainEnd;
        foreach (var id in C.FindQuest("Q9")!.Actions.Take(3).Concat(C.FindQuest("Q2")!.Actions)) s = Driver.Perform(C, s, C.GetAction(id));
        var shots = Epilogue.Select(C, s);
        Assert.Equal(new[] { "Q2", "Q9" }, shots.Select(x => x.QuestId)); // Q9 needs only Q9C
        Assert.Equal("JOZEF", shots[0].SpeakerId);
        Assert.Equal("epilogue.2.shot", shots[0].Shot.Key);
    }

    [Fact]
    public void Postgame_replays_cutscenes_without_any_transaction()
    {
        var s = TestData.MainEnd;
        Assert.True(Postgame.IsActive(C, s));
        Assert.Contains("CS07", Postgame.ReplayableCutscenes(C, s));
        var replay = Postgame.ReplayCutscene(C, s, "CS07");
        Assert.Equal(GameMode.Cutscene, replay.Mode);
        var after = Playback.FinishAll(C, replay);
        Assert.Equal(s, after);
        Assert.False(GameRules.ValidAction(C, s, C.GetAction("F17")));
        Assert.False(Postgame.IsActive(C, TestData.StateBefore("F17")));
        Assert.Same(TestData.StateBefore("F17"), Postgame.ReplayCutscene(C, TestData.StateBefore("F17"), "CS07"));
    }
}
