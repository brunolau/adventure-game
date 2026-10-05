using System.Text.Json.Nodes;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.Save;
using LastBell.Core.State;
using LastBell.Core.Tests.Support;

namespace LastBell.Core.Tests;

/// <summary>Save format, validation and rejection without mutating the open game.</summary>
public sealed class SaveLoadTests
{
    private static readonly GameContent C = TestData.Content;

    private static JsonObject SaveOf(GameState s) => JsonNode.Parse(SaveCodec.Serialize(s))!.AsObject();

    private static void Rejects(JsonObject save, string reasonPart)
    {
        var ex = Assert.Throws<SaveValidationException>(() => SaveCodec.ValidateSave(C, save));
        Assert.Contains(reasonPart, ex.Reason);
        Assert.Equal("ui.save.corrupted", ex.Text.Key);
        Assert.Equal("Chybný súbor uloženia. Aktuálna hra zostala otvorená.", ex.Text.Fallback);
    }

    [Fact]
    public void Save_contains_schema_version_and_checksum()
    {
        var save = SaveOf(TestData.StateAfter("G05"));
        Assert.Equal(1, save["schema_version"]!.GetValue<int>());
        Assert.Equal(64, save["checksum"]!.GetValue<string>().Length);
    }

    [Fact]
    public void Corrupt_json_is_rejected()
    {
        Assert.Throws<SaveValidationException>(() => SaveCodec.Load(C, "{ not json"));
        Assert.Throws<SaveValidationException>(() => SaveCodec.Load(C, "[]"));
        Assert.Throws<SaveValidationException>(() => SaveCodec.Load(C, "null"));
    }

    [Fact]
    public void Unknown_ids_are_rejected_not_silently_dropped()
    {
        var s = TestData.StateAfter("G05");
        var a = SaveOf(s); a.Remove("checksum"); a["inventory"]!.AsArray().Add("GOLDEN_KEY"); Rejects(a, "unknown item");
        var b = SaveOf(s); b.Remove("checksum"); b["done"]!.AsArray().Add("Z99"); Rejects(b, "unknown action");
        var c = SaveOf(s); c.Remove("checksum"); c["visited"]!.AsArray().Add("S99"); Rejects(c, "unknown room");
        var d = SaveOf(s); d.Remove("checksum"); d["future_field"] = 1; Rejects(d, "unknown field");
        var e = SaveOf(s); e.Remove("checksum"); e["puzzle_drafts"]!["P99"] = 1; Rejects(e, "unknown puzzle");
    }

    [Fact]
    public void Structural_errors_are_rejected()
    {
        var s = TestData.StateAfter("G05");
        var a = SaveOf(s); a["schema_version"] = 2; Rejects(a, "schema_version");
        var b = SaveOf(s); b.Remove("checksum"); b["era"] = 1995; Rejects(b, "does not exist in era");
        var c = SaveOf(s); c.Remove("checksum"); c["inventory"]!.AsArray().Add("PHONE"); Rejects(c, "duplicate");
        var d = SaveOf(s); d.Remove("checksum"); d["selected_item"] = "CHRONO"; Rejects(d, "not owned");
        var e = SaveOf(s); e.Remove("checksum"); e["mode"] = "flying"; Rejects(e, "mode");
        var f = SaveOf(s); f.Remove("checksum"); f["puzzle_drafts"] = new JsonArray(); Rejects(f, "puzzle_drafts");
        var g = SaveOf(s); g.Remove("done"); Rejects(g, "missing done");
    }

    [Fact]
    public void Inventory_that_does_not_match_the_story_is_rejected()
    {
        var s = TestData.StateAfter("G05");
        var extra = SaveOf(s); extra.Remove("checksum"); extra["inventory"]!.AsArray().Add("CHRONO"); Rejects(extra, "inventory does not match");
        var missing = SaveOf(s); missing.Remove("checksum"); missing["inventory"] = new JsonArray("PHONE"); Rejects(missing, "inventory does not match");
        var order = SaveOf(TestData.StateAfter("G02")); order.Remove("checksum"); order["done"] = new JsonArray("G02", "G01"); Rejects(order, "prerequisites");
        var reward = SaveOf(s); reward.Remove("checksum"); reward["side_rewards"] = new JsonArray("Q1"); Rejects(reward, "side_rewards");
    }

    [Fact]
    public void Tampering_breaks_the_checksum()
    {
        var save = SaveOf(TestData.StateAfter("G05"));
        save["hotspot_labels"] = true;
        Rejects(save, "checksum");
    }

    [Fact]
    public void Failed_import_leaves_the_open_game_untouched()
    {
        var session = new GameSession(C, TestData.StateAfter("G05"));
        var before = session.State;
        Assert.False(session.TryLoad("{\"schema_version\":1}", out var error));
        Assert.Equal("ui.save.corrupted", error.Key);
        Assert.Same(before, session.State);
        Assert.True(session.TryLoad(SaveCodec.Serialize(TestData.StateAfter("G11")), out _));
        Assert.Equal(TestData.StateAfter("G11"), session.State);
    }

    [Fact]
    public void Plain_runtime_contract_states_without_optional_fields_validate()
    {
        var raw = C.Data.InitialState!.DeepClone();
        var s = GameRules.ValidateSave(C, raw);
        Assert.Equal(C.InitialState, s);
    }

    [Fact]
    public void Loading_never_duplicates_items_and_keeps_done_actions()
    {
        var s = TestData.StateAfter("G01");
        for (var i = 0; i < 5; i++) s = SaveCodec.Load(C, SaveCodec.Serialize(s));
        Assert.Single(s.Inventory, "TOOLS");
        Assert.False(GameRules.TryCommitAction(C, Driver.TravelTo(C, s, "S01"), "G01").Success);
    }

    [Fact]
    public void Ui_helper_fields_roundtrip()
    {
        var s = Quests.Pin(C, Hints.RevealNext(C, GameRules.ToggleHotspots(TestData.StateAfter("G05")), "M02"), "M02");
        s = Puzzles.UpdateDraft(C, s, "P01", PuzzleAnswers.Matching("kruh", null, "štvorec"));
        var loaded = SaveCodec.Load(C, SaveCodec.Serialize(s, indented: true));
        Assert.Equal(s, loaded);
        Assert.True(loaded.HotspotLabels);
        Assert.Equal("M02", loaded.PinnedMainQuest);
        Assert.Equal(1, Hints.RevealedLevel(loaded, "M02"));
    }

    // ---- GAME-02 / UI-05: what a load resumes in ----

    [Fact]
    public void Open_puzzle_is_saved_and_reopened_after_load()
    {
        var open = Puzzles.UpdateDraft(C, Puzzles.Open(C, TestData.ReadyFor("G11"), "G11"), "P01", PuzzleAnswers.Matching("kruh", null, null));
        Assert.Equal("G11", open.OpenPuzzleAction);
        var save = SaveOf(open);
        Assert.Equal("G11", save["open_puzzle"]!.GetValue<string>());
        var loaded = SaveCodec.Load(C, SaveCodec.Serialize(open));
        Assert.Equal(open, loaded);
        var resumed = GameRules.ResumeAfterLoad(C, loaded);
        Assert.Equal(GameMode.Puzzle, resumed.Mode);
        Assert.Equal("G11", Puzzles.OpenAction(C, resumed)?.Id);
        Assert.True(JsonDeep.Equals(PuzzleAnswers.Matching("kruh", null, null), Puzzles.Draft(C, resumed, "P01")));
    }

    [Fact]
    public void Old_save_in_puzzle_mode_without_open_puzzle_resumes_in_the_world_with_its_draft()
    {
        var open = Puzzles.UpdateDraft(C, Puzzles.Open(C, TestData.ReadyFor("G11"), "G11"), "P01", PuzzleAnswers.Matching("kruh", null, null));
        var legacy = SaveOf(open);
        legacy.Remove("open_puzzle");
        legacy.Remove("checksum");
        var loaded = SaveCodec.ValidateSave(C, legacy);
        Assert.Null(loaded.OpenPuzzleAction);
        var resumed = GameRules.ResumeAfterLoad(C, loaded);
        Assert.Equal(GameMode.World, resumed.Mode);
        Assert.Null(Puzzles.OpenAction(C, resumed));
        Assert.True(JsonDeep.Equals(PuzzleAnswers.Matching("kruh", null, null), Puzzles.Draft(C, resumed, "P01")));
    }

    [Fact]
    public void Open_puzzle_is_validated()
    {
        var open = Puzzles.Open(C, TestData.ReadyFor("G11"), "G11");
        var a = SaveOf(open); a.Remove("checksum"); a["open_puzzle"] = "G01"; Rejects(a, "not a puzzle action");
        var b = SaveOf(open); b.Remove("checksum"); b["mode"] = "world"; Rejects(b, "outside puzzle mode");
        var c = SaveOf(open); c.Remove("checksum"); c["open_puzzle"] = 7; Rejects(c, "open_puzzle is not a string");
        // A puzzle action that is no longer valid (already done) is closed on resume instead of reopened.
        var done = TestData.StateAfter("G11") with { Mode = GameMode.Puzzle, OpenPuzzleAction = "G11" };
        Assert.Null(Puzzles.OpenAction(C, done));
        Assert.Equal(GameMode.World, GameRules.ResumeAfterLoad(C, done).Mode);
    }

    [Fact]
    public void Saves_without_an_open_puzzle_keep_their_payload_and_checksum()
    {
        var s = TestData.StateAfter("G05");
        Assert.False(SaveOf(s).ContainsKey("open_puzzle"));
        Assert.Equal(SaveCodec.Checksum(s), SaveCodec.Checksum(SaveCodec.Load(C, SaveCodec.Serialize(s))));
    }

    [Fact]
    public void Closing_or_solving_clears_the_open_puzzle()
    {
        var open = Puzzles.Open(C, TestData.ReadyFor("G11"), "G11");
        Assert.Null(Puzzles.Close(open).OpenPuzzleAction);
        var solved = Puzzles.Submit(C, open, "G11", C.GetPuzzle("P01").Solution?.DeepClone());
        Assert.True(solved.Solved);
        Assert.Null(solved.State.OpenPuzzleAction);
        var wrong = Puzzles.Submit(C, open, "G11", PuzzleAnswers.Matching("kruh", null, null));
        Assert.Equal("G11", wrong.State.OpenPuzzleAction);
    }

    [Fact]
    public void A_save_taken_in_an_overlay_resumes_in_the_scene()
    {
        var s = TestData.StateAfter("G05");
        foreach (var overlay in new[] { GameMode.Pause, GameMode.Map, GameMode.Journal })
        {
            var loaded = SaveCodec.Load(C, SaveCodec.Serialize(GameRules.OpenOverlay(s, overlay)));
            Assert.Equal(overlay, loaded.Mode);
            Assert.Equal(GameMode.World, GameRules.ResumeAfterLoad(C, loaded).Mode);
        }
        Assert.Equal(s, GameRules.ResumeAfterLoad(C, s));
    }
}
