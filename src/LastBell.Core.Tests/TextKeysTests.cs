using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.Tests.Support;
using LastBell.Core.Text;

namespace LastBell.Core.Tests;

/// <summary>Every row of the key scheme table in ARCHITECTURE.md.</summary>
public sealed class TextKeysTests
{
    private static readonly GameContent C = TestData.Content;

    [Fact]
    public void Lines_use_their_line_id()
    {
        var line = C.GetAction("G01").Lines[0];
        Assert.Equal(new TextRef("action.G01.001", line.Text), TextKeys.Of(line));
        Assert.Equal("action.G01.001", TextKeys.Line("action.G01.001"));
    }

    [Fact]
    public void Room_hotspot_exit_and_connection_keys()
    {
        Assert.Equal("room.S01.name", TextKeys.NameOf(C.GetRoom("S01")).Key);
        var tools = C.FindHotspot("S01.tools")!.Hotspot;
        Assert.Equal("hotspot.S01.tools.name", TextKeys.NameOf(tools).Key);
        Assert.Equal("look.S01.tools", TextKeys.BaseLookOf(tools).Key); // look has a line id
        var noIds = tools with { LookLineId = null, LookVariants = new[] { new LookVariantDef { After = "G01", Text = "x" } } };
        Assert.Equal("hotspot.S01.tools.look", TextKeys.BaseLookOf(noIds).Key);
        Assert.Equal("hotspot.S01.tools.look.1", TextKeys.LookVariantOf(noIds, 0).Key);
        Assert.Equal("hotspot.S01.ambient 1.name", TextKeys.HotspotName("S01.ambient 1")); // spaces kept
        var exit = C.GetRoom("S01").Exits[0];
        Assert.Equal("exit.S01.to_S02.label", TextKeys.LabelOf(exit).Key);
        Assert.Equal("exit.S01.to_S02.locked", TextKeys.LockedOf(exit).Key);
        var conn = C.Data.Connections[0];
        Assert.Equal("conn.S01.S02.label", TextKeys.LabelOf(conn).Key);
        Assert.Equal("conn.S01.S02.locked", TextKeys.LockedOf(conn).Key);
    }

    [Fact]
    public void Look_variants_use_their_line_ids()
    {
        var photo = C.FindHotspot("S06.photo")!.Hotspot;
        Assert.Equal("look.S06.photo.variant1", TextKeys.LookVariantOf(photo, 0).Key);
    }

    [Fact]
    public void Item_keys()
    {
        var phone = C.GetItem("PHONE");
        Assert.Equal("item.PHONE.name", TextKeys.NameOf(phone).Key);
        Assert.Equal("item.PHONE", TextKeys.LookOf(phone).Key); // = look_line_id
        Assert.Equal("item.X.look", TextKeys.ItemLook("X"));
        Assert.Equal("item.PHONE.purpose", TextKeys.PurposeOf(phone).Key);
    }

    [Fact]
    public void Action_character_topic_keys()
    {
        var g01 = C.GetAction("G01");
        Assert.Equal(new TextRef("action.G01.label", g01.Label), TextKeys.LabelOf(g01));
        Assert.Equal("action.G01.journal", TextKeys.JournalOf(g01).Key);
        Assert.Equal("action.G01.objective", TextKeys.ObjectiveOf(g01).Key);
        Assert.True(TextKeys.ObjectiveOf(C.GetAction("B10")).IsEmpty); // objective null
        Assert.Equal("char.ADAM.name", TextKeys.NameOf(C.FindCharacter("ADAM")!).Key);
        Assert.Equal(new TextRef("char.SYSTEM.name", "Text zariadenia"), C.SpeakerName("SYSTEM"));
        var topic = C.FindTopic("ELA.ambient 1")!.Value.Topic;
        Assert.Equal("topic.ELA.ambient 1.label", TextKeys.LabelOf(topic).Key);
    }

    [Fact]
    public void Quest_puzzle_era_epilogue_ui_keys()
    {
        var m01 = C.FindQuest("M01")!;
        Assert.Equal("quest.M01.title", TextKeys.TitleOf(m01).Key);
        Assert.Equal("quest.M01.goal", TextKeys.GoalOf(m01).Key);
        Assert.Equal("quest.M01.reward", Quests.RewardOf(m01).Key);
        Assert.Equal(new[] { "quest.M01.hint.1", "quest.M01.hint.2", "quest.M01.hint.3" },
            Enumerable.Range(0, 3).Select(i => TextKeys.HintOf(m01, i).Key));
        var p02 = C.GetPuzzle("P02");
        Assert.Equal("puzzle.P02.title", TextKeys.TitleOf(p02).Key);
        Assert.Equal("puzzle.P02.clue", TextKeys.ClueOf(p02).Key);
        Assert.Equal("puzzle.P02.wrong", TextKeys.WrongOf(p02).Key);
        Assert.Equal("puzzle.P02.success", TextKeys.SuccessOf(p02).Key);
        Assert.Equal(new TextRef("puzzle.P02.confirm", "Zarovnať tri značky"), TextKeys.ConfirmOf(p02));
        Assert.True(TextKeys.ConfirmOf(C.GetPuzzle("P01")).IsEmpty);
        var era = C.FindEra(1995)!;
        Assert.Equal("era.1995.card", TextKeys.CardOf(era).Key);
        Assert.Equal(new TextRef("era.1995.date", "1995-06-15"), TextKeys.DateOf(era));
        Assert.Equal(new TextRef("era.1960.year", "1960"), TextKeys.YearOf(1960)); // shown as 1962 via ui.csv
        Assert.Equal("epilogue.1.shot", TextKeys.ShotOf(C.Data.Epilogue[0], 0).Key);
        Assert.Equal("epilogue.9.line", TextKeys.LineOf(C.Data.Epilogue[8], 8).Key);
        Assert.Equal("ui.menu.continue", TextKeys.Ui("menu", "continue"));
        Assert.Equal("ui.save.corrupted", UiText.SaveCorrupt.Key);
        Assert.Equal("ui.system.path_blocked", UiText.PathBlocked.Key);
        Assert.Equal(new TextRef("region.Biela Púť.name", "Biela Púť"), TextKeys.RegionOf(C.GetRoom("S41")));
    }

    /// <summary>
    /// Every key Core produces itself (UiText, era cards/dates, map regions) exists in ui.csv, with the same
    /// Slovak text where Core has one (ISSUES GAME-03: ui.world.path_blocked did not exist; UI-01:
    /// ui.save.corrupt duplicated ui.save.corrupted).
    /// </summary>
    [Fact]
    public void Core_ui_keys_exist_in_ui_csv()
    {
        var ui = ReadTable(TestData.FixturePath("ui.csv"));
        foreach (var text in new[] { UiText.SaveCorrupt, UiText.PathBlocked, UiText.HelpLeftClick, UiText.HelpRightClick, UiText.HelpSpace })
        {
            Assert.True(ui.ContainsKey(text.Key), $"ui.csv has no {text.Key}");
            Assert.Equal(text.Fallback, ui[text.Key]);
        }
        foreach (var era in C.Data.Eras)
        {
            Assert.True(ui.ContainsKey(TextKeys.CardOf(era).Key), $"ui.csv has no {TextKeys.CardOf(era).Key}");
            Assert.True(ui.ContainsKey(TextKeys.DateOf(era).Key), $"ui.csv has no {TextKeys.DateOf(era).Key}");
        }
        foreach (var room in C.Rooms.Where(r => r.District.Length > 0))
            Assert.True(ui.ContainsKey(TextKeys.RegionOf(room).Key), $"ui.csv has no {TextKeys.RegionOf(room).Key}");
        Assert.False(ui.ContainsKey("ui.save.corrupt"), "the duplicate key ui.save.corrupt is back (UI-01)");
        // Step hints (PT-F08): the level-2 templates with Core's fallback text, and an exact step text for every quest action.
        Assert.Equal(Hints.PlaceFallback, ui[Hints.PlaceKey]);
        Assert.Equal(Hints.BagFallback, ui[Hints.BagKey]);
        foreach (var id in C.Quests.SelectMany(q => q.Actions))
        {
            if (C.GetAction(id).HintStep is not null) continue; // the world overlay's own step text (world.csv, ContentOverlayTests)
            Assert.True(ui.ContainsKey(Hints.StepKey(id)), $"ui.csv has no {Hints.StepKey(id)}");
            Assert.NotEqual(C.GetAction(id).Label, ui[Hints.StepKey(id)]); // a written step, not the label fallback
        }
    }

    /// <summary>Minimal reader of a Godot translation CSV (header "keys,sk,en", RFC 4180 quoting): key to sk text.</summary>
    private static Dictionary<string, string> ReadTable(string path)
    {
        var result = new Dictionary<string, string>(StringComparer.Ordinal);
        var text = File.ReadAllText(path);
        var row = new List<string>();
        var field = new System.Text.StringBuilder();
        bool quoted = false, header = true;
        void EndRow()
        {
            row.Add(field.ToString());
            field.Clear();
            if (!header && row.Count >= 2 && row[0].Length > 0) result[row[0]] = row[1];
            header = false;
            row.Clear();
        }
        for (int i = 0; i < text.Length; i++)
        {
            char c = text[i];
            if (quoted)
            {
                if (c == '"' && i + 1 < text.Length && text[i + 1] == '"') { field.Append('"'); i++; }
                else if (c == '"') quoted = false;
                else field.Append(c);
            }
            else if (c == '"') quoted = true;
            else if (c == ',') { row.Add(field.ToString()); field.Clear(); }
            else if (c == '\n') EndRow();
            else if (c != '\r') field.Append(c);
        }
        if (field.Length > 0 || row.Count > 0) EndRow();
        return result;
    }

    [Fact]
    public void Resolver_returns_keys_not_formatted_text()
    {
        var s = C.InitialState;
        var look = Assert.IsType<Resolution.Look>(GameRules.ResolveInteraction(C, s, new Hit.Hotspot("S01.fuse"), PointerButton.Right));
        Assert.Equal("look.S01.fuse", look.Text.Key);
        Assert.Equal(C.FindHotspot("S01.fuse")!.Hotspot.Look, look.Text.Fallback);
    }

    [Fact]
    public void Every_hotspot_look_and_item_look_key_resolves_back_to_its_text()
    {
        foreach (var h in C.Rooms.SelectMany(r => r.Hotspots))
        {
            Assert.Equal(TextKeys.BaseLookOf(h), C.FindLookText(TextKeys.BaseLookOf(h).Key));
            for (var i = 0; i < h.LookVariants.Count; i++) Assert.Equal(TextKeys.LookVariantOf(h, i), C.FindLookText(TextKeys.LookVariantOf(h, i).Key));
        }
        foreach (var item in C.Items) Assert.Equal(TextKeys.LookOf(item), C.FindLookText(TextKeys.LookOf(item).Key));
    }
}
