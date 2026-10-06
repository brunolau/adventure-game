using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Game.Presentation;
using LastBell.Game.Runtime;
using LastBell.Game.UI;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Cutscenes;
using LastBell.Game.UI.Journal;
using LastBell.Game.UI.Menus;
using LastBell.Game.World;

namespace LastBell.Game.Diagnostics;

/// <summary>
/// Milestone-2 content QA (docs/MILESTONE2.md): the whole game through the real input path.
/// <list type="bullet">
/// <item><c>--play-all</c>: all 94 main actions, then the ending (epilogue shots, credits, postgame note)
/// by real clicks / keys, then all 33 side actions after the credits, then the postgame checks.</item>
/// <item><c>--interleave early|seed:&lt;n&gt;</c>: side actions are done during the main route — greedily
/// as soon as they are legal (<c>early</c>) or at seeded random legal points — so the ending has the
/// epilogue shots of every quest completed before the finale.</item>
/// <item><c>--play-side</c>: after <c>--play</c>/<c>--replay</c>, the ending (if pending), all remaining
/// side actions and the postgame checks.</item>
/// <item><c>--save-load-each</c>: save, load and compare after every action (AT17).</item>
/// <item><c>--shots &lt;dir&gt;</c>: a JPEG after every action, puzzle, cutscene beat, ending shot, first
/// sight of a variant layer / causal effect and postgame step (needs a window).</item>
/// <item><c>--coverage &lt;file.json&gt;</c>: what was verified (actions, quests, puzzles, cutscenes, eras,
/// portals, variant layers, causal effects, epilogue, postgame, blockers).</item>
/// </list>
/// </summary>
public partial class DebugHarness
{
    private readonly List<JsonObject> actLog = new();
    private readonly Dictionary<string, SortedSet<int>> cutsceneBeats = new(StringComparer.Ordinal);
    private readonly HashSet<string> puzzlesSolved = new(StringComparer.Ordinal);
    private readonly HashSet<string> variantsSeen = new(StringComparer.Ordinal);
    private readonly HashSet<string> causalSeen = new(StringComparer.Ordinal);
    private readonly HashSet<string> roomsSeen = new(StringComparer.Ordinal);
    private readonly HashSet<string> portalsUsed = new(StringComparer.Ordinal);
    private readonly List<string> qaFailures = new();
    private readonly JsonObject postgameReport = new();
    private readonly List<int> endingShotCounts = new();
    private int shotCounter;
    private int lineCount;
    private readonly HashSet<string> lineIds = new(StringComparer.Ordinal);
    private readonly HashSet<string> lookKeys = new(StringComparer.Ordinal);
    private bool qaHooked;

    private string? ShotsDir => Get("shots");

    private bool CanShoot => ShotsDir is not null && DisplayServer.GetName() != "headless";

    /// <summary>Called once before the first act (Run): hooks presenter/stage events for coverage.</summary>
    private void HookContentQa()
    {
        if (qaHooked) return;
        qaHooked = true;
        keyboardOnly = Has("keyboard"); // AT19: keys only (KeyboardDriver.cs)
        realInput = keyboardOnly || Has("real") || Has("play-all") || Has("play-side");
        if (DialoguePresenter.Instance is { } presenter)
            presenter.LineShown += l =>
            {
                lineCount++;
                lineIds.Add(l.Line.LineId);
                if (!l.Line.IsCutscene) return;
                if (!cutsceneBeats.TryGetValue(l.Line.SourceId, out var beats)) cutsceneBeats[l.Line.SourceId] = beats = new SortedSet<int>();
                if (beats.Add(l.Line.BeatIndex)) _ = ShotLater($"cs_{l.Line.SourceId}_beat{l.Line.BeatIndex + 1}", 0.35);
            };
        if (WorldStage.Instance is { } stage) stage.RoomReady += _ => OnRoomSettled();
    }

    // ------------------------------------------------------------------ evidence

    private async Task ShotLater(string name, double delaySeconds)
    {
        if (!CanShoot) return;
        await Seconds(delaySeconds);
        await ToSignal(RenderingServer.Singleton, RenderingServerInstance.SignalName.FramePostDraw);
        var image = GetViewport().GetTexture()?.GetImage();
        if (image is null || image.IsEmpty()) return;
        if (image.GetWidth() != 1920 || image.GetHeight() != 1080) image.Resize(1920, 1080, Image.Interpolation.Lanczos);
        string repoRoot = System.IO.Path.GetFullPath(System.IO.Path.Combine(ProjectSettings.GlobalizePath("res://"), "..", ".."));
        string dir = System.IO.Path.IsPathRooted(ShotsDir!) ? ShotsDir! : System.IO.Path.Combine(repoRoot, ShotsDir!);
        System.IO.Directory.CreateDirectory(dir);
        string file = System.IO.Path.Combine(dir, $"{++shotCounter:D3}_{name}.jpg");
        image.SaveJpg(file, 0.86f);
    }

    private void OnRoomSettled()
    {
        var game = GameRuntime.Instance;
        var room = WorldStage.Instance?.Current;
        if (room is null || room.RoomId != game.State.Room) return;
        roomsSeen.Add(room.RoomId);
        foreach (var v in room.View.VariantLayers.Where(v => v.Visible))
        {
            string key = room.RoomId + ":" + v.Layer.Asset;
            if (!variantsSeen.Add(key)) continue;
            Log($"variant visible {key} (after {v.Layer.After})");
            _ = ShotLater($"variant_{room.RoomId}_{System.IO.Path.GetFileNameWithoutExtension(v.Layer.Asset)}", 0.6);
        }
        foreach (var c in room.View.CausalEffects.Where(c => !c.DeferredUntilReentry))
        {
            string key = c.Index + "@" + room.RoomId;
            if (!causalSeen.Add(key)) continue;
            Log($"causal effect {c.Index} (after {c.Effect.After}) active in {room.RoomId}");
            _ = ShotLater($"causal_{c.Effect.After}_{room.RoomId}", 0.6);
        }
    }

    private void OnPuzzleSolved(PuzzleDef def)
    {
        puzzlesSolved.Add(def.Id);
        _ = ShotLater($"puzzle_{def.Id}_solved_line", 0.15);
    }

    private async Task OnActCommitted(ActionDef action)
    {
        var game = GameRuntime.Instance;
        var s = game.State;
        var entry = new JsonObject
        {
            ["action"] = action.Id,
            ["quest"] = game.Content.GetQuestOf(action.Id)?.Id,
            ["order"] = actLog.Count + 1,
            ["room"] = action.Room,
            ["era"] = s.Era,
            ["kind"] = action.Kind,
            ["input"] = realInput ? "real" : "submit",
            ["inventory"] = string.Join(",", s.Inventory),
        };
        actLog.Add(entry);
        _ = ShotLater($"act_{action.Id}_{(action.IsInventoryAction ? "inv" : action.Room)}", 0.45);
        if (Has("all-lines") && action.Id != game.Content.Data.Postgame.Unlock)
        {
            await WaitLinesReal(60);
            foreach (var item in action.Gives) if (game.State.Has(item)) await LookAtItemReal(item);
            if (game.State.Mode == GameMode.Inventory) await CloseDrawerReal();
            await LookAroundReal();
        }
        // The finale's own save/load is compared after the ending (a load would restart the playback).
        if (Has("save-load-each") && action.Id != game.Content.Data.Postgame.Unlock) await SaveLoadCompare(action.Id, entry);
    }

    private void QaFail(string text)
    {
        qaFailures.Add(text);
        Log("FAIL " + text);
    }

    // ------------------------------------------------------------------ AT17: save / load after every action

    private async Task SaveLoadCompare(string actionId, JsonObject entry)
    {
        var game = GameRuntime.Instance;
        await WaitLinesReal(60);
        if (UiRoot.Instance?.HasModal ?? false) return; // ending sequence: compared after it
        var before = game.State;
        game.Save("m2_each");
        bool loaded = game.Load("m2_each");
        await WaitLinesReal(30);
        var after = game.State;
        bool same = loaded && after.Done.SequenceEqual(before.Done) && after.Inventory.SequenceEqual(before.Inventory) &&
                    after.Room == before.Room && after.Era == before.Era && after.SideRewards.SequenceEqual(before.SideRewards);
        entry["save_load"] = same;
        if (!same) QaFail($"save/load after {actionId}: state differs (room {after.Room} vs {before.Room}, done {after.Done.Length} vs {before.Done.Length})");
        GameRuntime.DeleteSlot("m2_each");
    }

    // ------------------------------------------------------------------ interleaving

    private Random? interleaveRandom;

    private bool SideEligible(ActionDef a)
    {
        var game = GameRuntime.Instance;
        var s = game.State;
        if (!GameRules.GuardsPass(a, s)) return false;
        if (a.SelectedItem is not null && !s.Has(a.SelectedItem)) return false;
        if (a.IsInventoryAction) return true;
        var target = game.Content.FindHotspot(a.Target);
        if (target is null || !GameRules.IsVisible(target.Hotspot, s)) return false;
        return a.Room == s.Room || Navigation.FindRoute(game.Content, s, a.Room) is not null;
    }

    private IEnumerable<ActionDef> PendingSide()
    {
        var content = GameRuntime.Instance.Content;
        var order = SideOrder();
        return order.Select(content.GetAction).Where(a => !GameRuntime.Instance.State.IsDone(a.Id));
    }

    private static List<string> SideOrder()
    {
        var root = JsonNode.Parse(Godot.FileAccess.GetFileAsString(WalkthroughReplayer.Path))!;
        var order = root["postgame_optional_route"]!.AsArray().Select(n => n!.GetValue<string>()).ToList();
        // Side quests of the world overlay (content_ext/world_ext.json) are not in walkthrough.json: their data order.
        order.AddRange(GameRuntime.Instance.Content.Overlay.AddedActions.Where(a => !order.Contains(a)));
        return order;
    }

    /// <summary>Before a main action: side actions at legal points (greedy or seeded random).</summary>
    private async Task Interleave(string nextMain)
    {
        string? mode = Get("interleave");
        if (mode is null) return;
        if (mode.StartsWith("seed:", StringComparison.Ordinal))
            interleaveRandom ??= new Random(int.Parse(mode[5..], System.Globalization.CultureInfo.InvariantCulture));
        for (int guard = 0; guard < 40; guard++)
        {
            var eligible = PendingSide().Where(SideEligible).ToList();
            if (eligible.Count == 0) return;
            ActionDef pick;
            if (interleaveRandom is not null)
            {
                if (interleaveRandom.NextDouble() < 0.55) return;
                pick = eligible[interleaveRandom.Next(eligible.Count)];
            }
            else pick = eligible[0];
            Log($"interleave {pick.Id} before {nextMain}");
            await PerformAct(pick.Id);
        }
    }

    // ------------------------------------------------------------------ ending, side content, postgame

    /// <summary>After F17: epilogue shots → credits → postgame note, all by real input; returns the number of shots shown.</summary>
    private async Task<int> FinishEndingReal(bool replay)
    {
        var game = GameRuntime.Instance;
        var root = UiRoot.Instance!;
        int expected = Epilogue.Select(game.Content, game.State).Count;
        if (!await WaitUntil(() => root.TopModal is EndingSequence or CreditsScreen || (!replay && root.TopModal is ConfirmDialog), replay ? 10 : 120))
        {
            QaFail($"ending did not start (mode {game.State.Mode}, line {game.State.ActiveLineId ?? "-"}, modal {root.TopModal?.Name ?? "-"})");
            return -1;
        }
        int shots = 0;
        while (root.TopModal is EndingSequence ending)
        {
            shots++;
            await Seconds(1.8);
            await ShotLater($"{(replay ? "album_" : "")}epilogue_{shots:D2}", 0);
            if (keyboardOnly) await KeyCombo(Godot.Key.Enter); // Enter: next shot (AT19)
            else await RawMouseReal(new Vector2(960, 500), MouseButton.Left); // click: next shot
            await Frames(3);
            if (shots > 20) break;
        }
        if (root.TopModal is not ConfirmDialog)
        {
            if (!await WaitUntil(() => root.TopModal is CreditsScreen, 10)) QaFail("credits did not roll after the epilogue");
            await Seconds(1.5);
            await ShotLater(replay ? "album_credits" : "credits", 0);
            await KeyReal(Godot.Key.Escape); // close the rolling credits
        }
        if (!replay)
        {
            if (!await WaitUntil(() => root.TopModal is ConfirmDialog, 10)) QaFail("postgame note not shown after the credits");
            else
            {
                await ShotLater("postgame_note", 0.3);
                var ok = Descendants<Button>(root.TopModal!).FirstOrDefault(b => b.IsVisibleInTree());
                if (ok is null || !await ClickControl(ok, "postgame note OK")) QaFail("postgame note has no clickable button");
            }
        }
        await WaitUntil(() => !root.HasModal, 10);
        int counted = shots;
        Log($"ending{(replay ? " (album replay)" : "")}: {counted} epilogue shot(s) shown, Core selected {expected}");
        if (counted != expected) QaFail($"ending showed {counted} shots, Epilogue.Select has {expected}");
        endingShotCounts.Add(counted);
        return counted;
    }

    private async Task RunSideAndPostgame()
    {
        var game = GameRuntime.Instance;
        var unlock = game.Content.Data.Postgame.Unlock;
        if (game.State.IsDone(unlock))
        {
            await FinishEndingReal(replay: false);
            await WaitLinesReal(30);
            if (Has("save-load-each") && actLog.LastOrDefault(a => (string?)a["action"] == unlock) is { } finaleEntry) await SaveLoadCompare(unlock, finaleEntry);
            bool returned = game.Content.Data.Postgame.ReturnItems.All(game.State.Has);
            postgameReport["return_items_in_bag"] = returned;
            postgameReport["postgame_active"] = Postgame.IsActive(game.Content, game.State);
            if (!returned) QaFail("postgame: the four evidence items are not back in the bag");
        }
        foreach (var a in PendingSide().ToList())
        {
            if (game.State.IsDone(a.Id)) continue;
            if (!SideEligible(a))
            {
                QaFail($"side action {a.Id} not legal now (postgame={Postgame.IsActive(game.Content, game.State)}, room {game.State.Room})");
                continue;
            }
            await PerformAct(a.Id);
        }
        await WaitLinesReal(30);
        if (game.State.IsDone(unlock)) await PostgameChecks();
        if (Has("all-lines")) await AllLinesPass();
    }

    /// <summary>Right click on every target of the current room whose current look text was not seen yet.</summary>
    private async Task LookAroundReal()
    {
        var game = GameRuntime.Instance;
        if (game.State.SelectedItem is not null) await DropSelectionReal();
        foreach (var t in WorldStage.Instance!.Current!.Targets.ToList())
        {
            if (game.Session.Resolve(t.ToHit(), PointerButton.Right) is not Resolution.Look look || lookKeys.Contains(look.Text.Key)) continue;
            if (await ClickTarget(t.Id, MouseButton.Right))
            {
                await WaitUntil(() => DialoguePresenter.Instance!.IsShowingBark, 3);
                lookKeys.Add(look.Text.Key);
            }
            DialoguePresenter.Instance!.HideBark();
        }
    }

    /// <summary>Right click on the item's slot in the drawer (the archive tab if it is archived): its look text.</summary>
    private async Task LookAtItemReal(string itemId)
    {
        var game = GameRuntime.Instance;
        await OpenDrawerReal();
        Button? Tab(string key) => Descendants<Button>(UiRoot.Instance!).FirstOrDefault(b => b.IsVisibleInTree() && b.ToggleMode && b.Text.StartsWith(TextService.Ui(key), StringComparison.Ordinal));
        bool archived = false;
        if (SlotButton(itemId) is null && Tab("ui.inventory.tab_archived") is { } archive)
        {
            await ClickControl(archive, "archive tab");
            await Frames(3);
            archived = true;
        }
        var slot = SlotButton(itemId);
        if (slot is not null && await ClickControl(slot, "look " + itemId, MouseButton.Right))
        {
            await WaitUntil(() => DialoguePresenter.Instance!.IsShowingBark, 3);
            if (game.Content.FindItem(itemId) is { } def) lookKeys.Add(LastBell.Core.Text.TextKeys.LookOf(def).Key);
        }
        DialoguePresenter.Instance!.HideBark();
        if (archived && Tab("ui.inventory.tab_items") is { } items) { await ClickControl(items, "items tab"); await Frames(2); }
    }

    /// <summary>
    /// <c>--all-lines</c> (after the postgame): every room is visited, every visible target is looked at
    /// with a right click, every NPC's ambient topics are chosen from the topic menu until none is left,
    /// and every item in the bag is looked at in the drawer (AT24: all line ids reachable).
    /// </summary>
    private async Task AllLinesPass()
    {
        var game = GameRuntime.Instance;
        var content = game.Content;
        var unreachable = new List<string>();
        foreach (var room in content.Rooms.OrderBy(r => r.Era).ThenBy(r => r.Id, StringComparer.Ordinal))
        {
            if (game.State.Room != room.Id && Navigation.FindRoute(content, game.State, room.Id) is null) { unreachable.Add(room.Id); continue; }
            await TravelToReal(room.Id);
            await LookAroundReal();
            foreach (var npc in room.Hotspots.Where(h => h.CharacterId is not null && GameRules.IsVisible(h, game.State)))
            {
                for (int guard = 0; guard < 12; guard++)
                {
                    var open = Dialogue.TopicsFor(content, game.State, npc).Where(o => !o.IsStoryAction &&
                        !game.State.JournalSeen.Contains(Dialogue.TopicEntryKey(o.Id))).ToList();
                    if (open.Count == 0) break;
                    if (!await ClickTarget(npc.Id)) break;
                    if (!await WaitUntil(() => game.State.Mode == GameMode.Dialogue && game.State.ActiveLineId is null, 20)) break;
                    await Frames(3);
                    string label = TextService.Get(open[0].Label);
                    var button = Descendants<UI.Dialogue.TopicMenuView>(UiRoot.Instance!).SelectMany(Descendants<Button>)
                        .FirstOrDefault(b => b.IsVisibleInTree() && b.Text.StartsWith(label, StringComparison.Ordinal));
                    if (button is null || !await ClickControl(button, "ambient topic " + open[0].Id)) { await KeyReal(Godot.Key.Escape); break; }
                    await WaitLinesReal(30);
                }
            }
        }
        foreach (var item in game.State.Inventory.ToList()) await LookAtItemReal(item);
        await CloseDrawerReal();
        postgameReport["all_lines_unreachable_rooms"] = new JsonArray(unreachable.Select(x => (JsonNode?)x).ToArray());
        Log($"all-lines pass: {lineIds.Count} distinct line ids shown, {lookKeys.Count} look texts");
    }

    private async Task PostgameChecks()
    {
        var game = GameRuntime.Instance;
        var content = game.Content;
        var startInventory = game.State.Inventory.OrderBy(x => x, StringComparer.Ordinal).ToList();
        int doneBefore = game.State.Done.Length;

        // Era tour (AT11): every unlocked era through the chronometer portals, then back to the start era.
        var eras = Navigation.UnlockedEras(content, game.State).Select(e => e.Year).ToList();
        var tour = new JsonArray();
        foreach (var era in content.Eras.Where(e => eras.Contains(e.Year)).Concat(content.Eras.Where(e => e.Year == 2020)))
        {
            await TravelToReal(era.Anchor);
            await ShotLater($"postgame_era_{era.Year}_{era.Anchor}", 0.4);
            var inv = game.State.Inventory.OrderBy(x => x, StringComparer.Ordinal).ToList();
            bool same = inv.SequenceEqual(startInventory);
            tour.Add(new JsonObject { ["era"] = era.Year, ["room"] = game.State.Room, ["inventory_unchanged"] = same });
            if (!same) QaFail($"postgame era tour: inventory changed in {era.Year}");
        }
        postgameReport["era_tour"] = tour;

        // AT30: the resort's normal transport after J05/F09: S47 → S41 by the cable cars and back.
        if (content.FindRoom("S47") is not null && game.State.IsDone("F09"))
        {
            await TravelToReal("S47");
            await TravelToReal("S41");
            postgameReport["cable_cars_after_F09"] = game.State.Room == "S41";
        }

        // Revisit every room of a triggered causal effect / variant layer not yet seen there (AT21, AT25):
        // the change shows on the next entry, so the side quests done after the credits are looked at too.
        var revisit = new SortedSet<string>(StringComparer.Ordinal);
        for (int i = 0; i < content.Data.CausalEffects.Count; i++)
        {
            var effect = content.Data.CausalEffects[i];
            if (!game.State.IsDone(effect.After)) continue;
            foreach (var r in effect.At) if (!causalSeen.Contains(i + "@" + r)) revisit.Add(r);
        }
        foreach (var layer in content.Data.VisualVariantLayers)
            if (game.State.IsDone(layer.After) && !variantsSeen.Contains(layer.Room + ":" + layer.Asset)) revisit.Add(layer.Room);
        foreach (var r in revisit)
        {
            if (game.State.Room == r)
            {
                // Leave and come back so the change is no longer deferred.
                var exit = content.GetRoom(r).Exits.First(e => game.State.AllDone(e.RequiresDone));
                await TravelToReal(exit.To);
            }
            await TravelToReal(r);
        }
        postgameReport["revisited_for_effects"] = new JsonArray(revisit.Select(x => (JsonNode?)x).ToArray());

        // Album: replay the ending with the episodes completed since (epilogue_rules), by the journal's button.
        await TravelToReal("S06");
        await KeyReal(Godot.Key.J);
        await WaitUntil(() => game.State.Mode == GameMode.Journal, 5);
        await Frames(4);
        var journal = Descendants<JournalScreen>(UiRoot.Instance!).First();
        var albumTab = Descendants<Button>(journal).FirstOrDefault(b => b.IsVisibleInTree() && b.Text == TextService.Ui("ui.journal.tab_album"));
        if (albumTab is null || !await ClickControl(albumTab, "journal album tab")) QaFail("journal: album tab not clickable");
        await Frames(4);
        await ShotLater("postgame_journal_album", 0.3);
        var replayButton = Descendants<Button>(journal).FirstOrDefault(b => b.IsVisibleInTree() && b.Text == TextService.Ui("ui.journal.replay_ending"));
        if (replayButton is null || !await ClickControl(replayButton, "replay ending")) QaFail("journal: replay-ending button not clickable");
        else postgameReport["album_replay_shots"] = await FinishEndingReal(replay: true);

        // Cutscene replay from the journal's scene list (repeat_final: never a second transaction).
        await KeyReal(Godot.Key.J);
        await WaitUntil(() => game.State.Mode == GameMode.Journal, 5);
        await Frames(4);
        albumTab = Descendants<Button>(journal).FirstOrDefault(b => b.IsVisibleInTree() && b.Text == TextService.Ui("ui.journal.tab_album"));
        if (albumTab is not null) await ClickControl(albumTab, "journal album tab");
        await Frames(4);
        var finale = content.GetAction(content.Data.Postgame.Unlock);
        // Same title rule as JournalScreen's scene list: a ui.csv scene title wins over the action label (PT-S08).
        string finaleTitle = TextService.Get("ui.journal.scene_" + (finale.Cutscene ?? "").ToLowerInvariant(), "");
        string finaleLabel = finaleTitle.Length > 0 ? finaleTitle : TextService.Get(LastBell.Core.Text.TextKeys.LabelOf(finale));
        var sceneButton = Descendants<Button>(journal).FirstOrDefault(b => b.IsVisibleInTree() && b.Text == finaleLabel);
        var inventoryBefore = game.State.Inventory.ToList();
        if (sceneButton is null || !await ClickControl(sceneButton, "replay " + finale.Cutscene)) QaFail($"journal: no replay button for {finale.Cutscene}");
        else
        {
            bool started = await WaitUntil(() => game.State.Mode == GameMode.Cutscene || UiRoot.Instance!.HasModal is false && game.State.ActiveLineId is not null, 10);
            await Seconds(1.0);
            await ShotLater($"postgame_replay_{finale.Cutscene}", 0);
            await WaitLinesReal(90);
            bool noTransaction = game.State.Done.Length == doneBefore + 0 && game.State.Inventory.SequenceEqual(inventoryBefore);
            postgameReport["cutscene_replay"] = new JsonObject { ["cutscene"] = finale.Cutscene, ["started"] = started, ["no_transaction"] = noTransaction };
            if (!started || !noTransaction) QaFail($"cutscene replay {finale.Cutscene}: started={started} no_transaction={noTransaction}");
        }
        if (game.State.Mode == GameMode.Journal) await KeyReal(Godot.Key.Escape);
        postgameReport["done_unchanged"] = game.State.Done.Length == doneBefore;
    }

    // ------------------------------------------------------------------ coverage report

    private void WriteCoverage()
    {
        var game = GameRuntime.Instance;
        var content = game.Content;
        var s = game.State;
        var report = new JsonObject
        {
            ["label"] = Get("coverage-label") ?? "",
            ["args"] = string.Join(" ", LaunchArgs.User),
            ["window"] = DisplayServer.GetName() == "headless" ? "headless" : DisplayServer.WindowGetSize().ToString(),
            ["real_input"] = realInput,
            ["lines_shown"] = lineCount,
            ["line_ids_shown"] = new JsonArray(lineIds.OrderBy(x => x, StringComparer.Ordinal).Select(x => (JsonNode?)x).ToArray()),
            ["look_keys_shown"] = new JsonArray(lookKeys.OrderBy(x => x, StringComparer.Ordinal).Select(x => (JsonNode?)x).ToArray()),
            ["final_room"] = s.Room,
            ["final_era"] = s.Era,
            ["done_count"] = s.Done.Length,
            ["side_rewards"] = new JsonArray(s.SideRewards.Select(x => (JsonNode?)x).ToArray()),
            ["inventory"] = new JsonArray(s.Inventory.Select(x => (JsonNode?)x).ToArray()),
            ["acts"] = new JsonArray(actLog.Select(a => (JsonNode?)a.DeepClone()).ToArray()),
            ["quests"] = new JsonObject(content.Quests.Select(q => new KeyValuePair<string, JsonNode?>(q.Id, new JsonObject
            {
                ["type"] = q.IsSide ? "side" : "main",
                ["completion"] = q.Completion,
                ["completed"] = s.IsDone(q.Completion),
                ["actions_done"] = q.Actions.Count(s.IsDone),
                ["actions_total"] = q.Actions.Count,
            }))),
            ["puzzles_solved"] = new JsonArray(puzzlesSolved.OrderBy(x => x).Select(x => (JsonNode?)x).ToArray()),
            ["cutscenes"] = new JsonObject(cutsceneBeats.OrderBy(k => k.Key).Select(k => new KeyValuePair<string, JsonNode?>(k.Key,
                new JsonObject { ["beats_shown"] = k.Value.Count, ["beats_total"] = content.FindCutscene(k.Key)?.Beats.Count ?? 0 }))),
            ["rooms_seen"] = roomsSeen.Count,
            ["rooms_seen_list"] = new JsonArray(roomsSeen.OrderBy(x => x).Select(x => (JsonNode?)x).ToArray()),
            ["eras_unlocked"] = new JsonArray(Navigation.UnlockedEras(content, s).Select(x => (JsonNode?)x.Year).ToArray()),
            ["variant_layers_seen"] = new JsonArray(variantsSeen.OrderBy(x => x).Select(x => (JsonNode?)x).ToArray()),
            ["causal_effects_seen"] = new JsonArray(causalSeen.OrderBy(x => x).Select(x => (JsonNode?)x).ToArray()),
            ["butterflies"] = new JsonObject(WorldEffects.Butterflies(content, s).Select(b => new KeyValuePair<string, JsonNode?>(b.Effect.Id, b.Triggered))),
            ["cache_invariant"] = TemporalCache.InvariantHolds(content, s),
            ["cache_stage"] = TemporalCache.StatusOf(content, s).Stage.ToString(),
            ["ending_shot_counts"] = new JsonArray(endingShotCounts.Select(x => (JsonNode?)x).ToArray()),
            ["postgame"] = postgameReport.DeepClone(),
            ["blockers"] = new JsonArray(blockers.Select(x => (JsonNode?)x).ToArray()),
            ["click_retries"] = retries,
            ["keyboard_only"] = keyboardOnly,
            ["keyboard_steps"] = keySteps.Count,
            ["keyboard_presses"] = keySteps.Sum(k => k.Presses),
            ["keyboard_awkward"] = new JsonArray(keySteps.Where(k => k.Presses > AwkwardPresses).Select(k => (JsonNode?)$"{k.Step} {k.Presses}").ToArray()),
            ["keyboard_notes"] = new JsonArray(keyboardNotes.Select(x => (JsonNode?)x).ToArray()),
            ["failures"] = new JsonArray(qaFailures.Select(x => (JsonNode?)x).ToArray()),
        };
        string? file = Get("coverage");
        if (file is null) return;
        string repoRoot = System.IO.Path.GetFullPath(System.IO.Path.Combine(ProjectSettings.GlobalizePath("res://"), "..", ".."));
        string full = System.IO.Path.IsPathRooted(file) ? file : System.IO.Path.Combine(repoRoot, file);
        System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(full)!);
        System.IO.File.WriteAllText(full, report.ToJsonString(new JsonSerializerOptions { WriteIndented = true, Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping }));
        Log($"coverage written to {full}: {actLog.Count} actions, {cutsceneBeats.Count} cutscenes, {puzzlesSolved.Count} puzzles, {variantsSeen.Count} variant layers, {causalSeen.Count} causal effects, {blockers.Count} blockers, {qaFailures.Count} failures");
    }
}
