using System.Text;
using System.Text.Json.Nodes;
using LastBell.Core.Content;
using LastBell.Core.State;
using LastBell.Core.Tests.Support;

namespace LastBell.Core.Tests;

/// <summary>Loading and structural validation of game.json.</summary>
public sealed class ContentTests
{
    private static readonly GameContent C = TestData.Content;

    [Fact]
    public void Loads_the_complete_canonical_content()
    {
        Assert.Equal("2.0.0", C.Data.Version);
        Assert.Equal(68, C.Rooms.Count);
        Assert.Equal(127, C.Actions.Count);
        Assert.Equal(94, C.Actions.Count(a => a.Quest == "main"));
        Assert.Equal(33, C.Actions.Count(a => !a.IsMain));
        Assert.All(C.Actions.Where(a => !a.IsMain), a => Assert.Equal(a.Quest, C.GetQuestOf(a.Id).Id));
        Assert.Equal(78, C.Items.Count);
        Assert.Equal(50, C.Data.Characters.Count);
        Assert.Equal(5, C.Data.Puzzles.Count);
        Assert.Equal(9, C.Data.Cutscenes.Count);
        Assert.Equal(9, C.Quests.Count(q => q.IsSide));
        Assert.Equal(5, C.Eras.Count);
        Assert.Equal(239, C.Rooms.Sum(r => r.Hotspots.Count));
        Assert.Equal(C.Data.Stats["rooms"], C.Rooms.Count);
        Assert.Equal(C.Data.Stats["items"], C.Items.Count);
        Assert.Equal(C.Data.Stats["hotspots"], C.Rooms.Sum(r => r.Hotspots.Count));
    }

    [Fact]
    public void Loads_from_a_stream_as_godot_would_pass_res_file_contents()
    {
        using var stream = new MemoryStream(Encoding.UTF8.GetBytes(TestData.GameJson));
        var content = GameContent.Load(stream);
        Assert.Equal(C.Actions.Count, content.Actions.Count);
    }

    [Fact]
    public void Initial_state_is_phone_only_in_the_garage()
    {
        var s = C.InitialState;
        Assert.Equal("S01", s.Room);
        Assert.Equal(2020, s.Era);
        Assert.Equal(new[] { "PHONE" }, s.Inventory);
        Assert.Empty(s.Done);
        Assert.Equal(new[] { "S01" }, s.Visited);
        Assert.Equal(GameMode.World, s.Mode);
        Assert.Null(s.SelectedItem);
    }

    [Fact]
    public void Every_action_belongs_to_exactly_one_quest_and_completions_exist()
    {
        var all = C.Quests.SelectMany(q => q.Actions).ToList();
        Assert.Equal(all.Count, all.Distinct().Count());
        Assert.Equal(C.Actions.Select(a => a.Id).OrderBy(x => x), all.OrderBy(x => x));
        Assert.All(C.Quests, q => Assert.Contains(q.Completion, q.Actions));
        Assert.All(C.Quests, q => Assert.Equal(3, q.Hints.Count));
    }

    [Fact]
    public void Characters_have_canonical_ages()
    {
        int Age(string id) => C.FindCharacter(id)!.Age!.GetValue<int>();
        Assert.Equal(12, Age("TONO82"));
        Assert.Equal(25, Age("TONO"));
        Assert.Equal(50, Age("TONO20"));
        Assert.Equal(44, Age("OTO"));
        Assert.Equal(66, Age("OTO82"));
    }

    [Fact]
    public void Lines_and_hotspots_are_indexed()
    {
        Assert.NotNull(C.FindLine("action.G01.001"));
        Assert.Equal(LineSource.Cutscene, C.FindLine("cutscene.CS01.01.001")!.Source);
        Assert.Equal(LineSource.FirstEntry, C.FindLine("entry.S01.001")!.Source);
        Assert.Equal(LineSource.Topic, C.FindLine("topic.ELA.ambient 1.001")!.Source);
        Assert.Equal("S01", C.FindHotspot("S01.tools")!.Room.Id);
        Assert.Equal("S01", C.FindExit("S01.to_S02")!.Value.Room.Id);
        Assert.Equal("M01", C.GetQuestOf("G01").Id);
    }

    [Fact]
    public void Broken_reference_reports_id_and_json_path()
    {
        var root = JsonNode.Parse(TestData.GameJson)!.AsObject();
        root["actions"]![1]!["requires_done"] = new JsonArray("NOPE");
        var ex = Assert.Throws<ContentLoadException>(() => GameContent.Load(root.ToJsonString()));
        Assert.Contains(ex.Errors, e => e.Contains("$.actions[1](G02).requires_done[0]") && e.Contains("NOPE"));
    }

    [Fact]
    public void Empty_line_text_is_reported_instead_of_a_silent_empty_dialogue()
    {
        var root = JsonNode.Parse(TestData.GameJson)!.AsObject();
        root["actions"]![0]!["lines"]![0]!["text"] = " ";
        var ex = Assert.Throws<ContentLoadException>(() => GameContent.Load(root.ToJsonString()));
        Assert.Contains(ex.Errors, e => e.Contains("$.actions[0](G01).lines[0].text"));
    }

    [Fact]
    public void Action_without_a_quest_is_reported()
    {
        var root = JsonNode.Parse(TestData.GameJson)!.AsObject();
        root["quests"]![0]!["actions"]!.AsArray().RemoveAt(0);
        var ex = Assert.Throws<ContentLoadException>(() => GameContent.Load(root.ToJsonString()));
        Assert.Contains(ex.Errors, e => e.Contains("'G01' belongs to no quest"));
    }

    [Fact]
    public void Invalid_json_is_reported()
    {
        var ex = Assert.Throws<ContentLoadException>(() => GameContent.Load("{ \"rooms\": [ "));
        Assert.NotEmpty(ex.Errors);
    }

    [Fact]
    public void Exits_mirror_connections_both_ways_with_identical_gates()
    {
        foreach (var c in C.Data.Connections)
        {
            var forward = C.GetRoom(c.From).Exits.Single(e => e.To == c.To);
            Assert.Equal(c.RequiresDone, forward.RequiresDone);
            if (c.Bidirectional)
            {
                var back = C.GetRoom(c.To).Exits.Single(e => e.To == c.From);
                Assert.Equal(c.RequiresDone, back.RequiresDone);
            }
        }
    }
}
