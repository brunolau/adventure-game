using System;
using System.Collections.Generic;
using System.Linq;
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
using LastBell.Game.UI.Map;
using LastBell.Game.UI.Settings;
using LastBell.Game.World;

namespace LastBell.Game.Diagnostics;

/// <summary>
/// Milestone-2 in-engine acceptance checks: the rows of design-doc/acceptance_tests.csv that need the
/// running game beyond the prologue (run with <c>--acceptance</c>, or <c>--acceptance m2</c> for these
/// only). States are prepared through Core rules (<see cref="CoreDo"/>: travel over exits/portals and
/// commits, the same calls the presentation makes; never a granted item); every checked step then goes
/// through real Godot input events (RealInputDriver.cs). Prints <c>HARNESS PASS|FAIL ATxx_name</c>.
/// Writes and deletes the save slots <c>m2_accept_*</c>.
/// </summary>
public partial class DebugHarness
{
    // ------------------------------------------------------------------ state preparation (Core only)

    private static GameState CoreDo(GameContent content, GameState s, string actionId)
    {
        var a = content.GetAction(actionId);
        s = Playback.FinishAll(content, GameRules.CancelSelection(s));
        if (s.Mode != GameMode.World) s = s with { Mode = GameMode.World };
        if (!a.IsInventoryAction && a.Room != s.Room)
        {
            var route = Navigation.FindRoute(content, s, a.Room) ?? throw new InvalidOperationException($"prep: no route to {a.Room} for {actionId}");
            foreach (var step in route)
            {
                s = step.Kind == RouteStepKind.Exit ? Navigation.Travel(content, s, step.ExitId!) : Navigation.UsePortal(content, s, step.Year!.Value);
                s = Playback.FinishAll(content, s);
            }
        }
        if (a.Puzzle is not null)
        {
            s = Puzzles.Open(content, s, a.Id);
            var r = Puzzles.Submit(content, s, a.Id, content.GetPuzzle(a.Puzzle).Solution?.DeepClone());
            if (!r.Solved) throw new InvalidOperationException("prep: puzzle not solved " + a.Puzzle);
            s = r.State;
        }
        else s = GameRules.CommitAction(content, s, a.Id);
        return GameRules.CancelSelection(Playback.FinishAll(content, s));
    }

    private static List<string> MainRoute() => WalkthroughReplayer.LoadMainRoute().Select(st => st.Action).ToList();

    /// <summary>Main route up to (excluding) <paramref name="before"/>, plus extra actions first.</summary>
    private async Task Prepare(string? before, params string[] extra)
    {
        var game = GameRuntime.Instance;
        var content = game.Content;
        var s = content.InitialState;
        foreach (var id in extra) s = CoreDo(content, s, id);
        foreach (var id in MainRoute())
        {
            if (id == before) break;
            if (!s.IsDone(id)) s = CoreDo(content, s, id);
        }
        game.ReplaceState(s);
        await Settle();
        if (realInput) await WaitLinesReal(20);
    }

    private static bool SameProgress(GameState a, GameState b) =>
        a.Done.SequenceEqual(b.Done) && a.Inventory.OrderBy(x => x).SequenceEqual(b.Inventory.OrderBy(x => x)) &&
        a.Room == b.Room && a.Era == b.Era && a.SideRewards.SequenceEqual(b.SideRewards);

    private static string Inv(GameState s) => string.Join(",", s.Inventory);

    private static string ItemLabel(Hit hit) => TextService.Get(GameRuntime.Instance.Session.Hover(hit).ActionLabel);

    // ------------------------------------------------------------------ the checks

    private async Task RunContentAcceptance()
    {
        var game = GameRuntime.Instance;
        var content = game.Content;
        realInput = true;
        int failuresBefore = acceptanceFailures;
        Log("acceptance m2: start");

        // ---------------------------------------------------------------- AT19 (part): keyboard only (Tab focus + Enter)
        game.NewGame();
        await Settle();
        await WaitLinesReal(20);
        bool focused = await FocusByTab("S01.tools");
        await KeyReal(Godot.Key.Enter);
        await WaitUntil(() => game.State.IsDone("G01"), 20);
        await WaitLinesReal(20);
        bool exitFocused = await FocusByTab(content.GetRoom("S01").Exits.First(e => e.To == "S02").Id);
        await KeyReal(Godot.Key.Enter);
        await WaitUntil(() => game.State.Room == "S02" && WorldStage.Instance!.IsSettled && WorldStage.Instance.IsFadedIn, 20);
        await WaitLinesReal(20);
        await TravelToReal("S03");
        bool elaFocused = await FocusByTab("S03.ELA");
        await KeyReal(Godot.Key.Enter);
        await WaitUntil(() => game.State.Mode == GameMode.Dialogue && game.State.ActiveLineId is null, 20);
        await Frames(4);
        await KeyReal(Godot.Key.Enter); // the first (story) topic has keyboard focus
        await WaitUntil(() => game.State.IsDone("G02"), 20);
        Check("AT19_keyboard_only_take_travel_talk", focused && exitFocused && elaFocused && game.State.IsDone("G01") && game.State.IsDone("G02") && game.State.Room == "S03",
              $"tab_focus={focused}/{exitFocused}/{elaFocused} G01={game.State.IsDone("G01")} G02={game.State.IsDone("G02")} room={game.State.Room}");
        await WaitLinesReal(20);

        // ---------------------------------------------------------------- AT22: double-click spam on a give action and the last line
        game.NewGame();
        await Settle();
        await WaitLinesReal(20);
        var p = await FindClickPoint("S01.tools");
        if (p is { } pt)
        {
            await RawMouseReal(pt, MouseButton.Left);
            await RawMouseReal(pt, MouseButton.Left);
            await RawMouseReal(pt, MouseButton.Left);
        }
        await WaitUntil(() => game.State.IsDone("G01"), 20);
        // Spam clicks on the last line of G01: they must not fall through to the scene (no walk afterwards).
        for (int i = 0; i < 12 && game.State.ActiveLineId is not null; i++) { await RawMouseReal(new Vector2(1500, 880), MouseButton.Left); await Frames(2); }
        await Frames(6);
        bool walkingAfter = CurrentRoom.Hero.IsWalking;
        Check("AT22_click_spam_commits_once_no_fall_through", game.State.Done.Count(d => d == "G01") == 1 && Count(game.State, "TOOLS") == 1 && !walkingAfter,
              $"G01x{game.State.Done.Count(d => d == "G01")} TOOLS={Count(game.State, "TOOLS")} walking_after_last_line={walkingAfter}");
        await WaitLinesReal(20);

        // ---------------------------------------------------------------- AT02: BALL over the cassette deck: no text, full no-op
        await Prepare("B04", "G01", "Q1A", "Q1B");
        await TravelToReal("S16");
        await SelectItemReal("BALL", keepDrawerOpen: false);
        string ballLabel = ItemLabel(new Hit.Hotspot("S16.deck"));
        var before = game.State;
        var feet = CurrentRoom.Hero.Feet;
        bool clicked = await ClickTarget("S16.deck");
        await Frames(8);
        Check("AT02_wrong_item_no_text_no_op", clicked && ballLabel.Length == 0 && !CurrentRoom.Hero.IsWalking && CurrentRoom.Hero.Feet == feet &&
              game.State.SelectedItem == "BALL" && SameProgress(before, game.State) && game.State.ActiveLineId is null,
              $"label='{ballLabel}' walking={CurrentRoom.Hero.IsWalking} selected={game.State.SelectedItem} done={game.State.Done.Length}");

        // ---------------------------------------------------------------- AT04: right click on an item in the drawer looks, drawer stays open
        await ClickSlotReal("BALL", MouseButton.Right); // with BALL selected: cancels the selection first
        bool cancelled = game.State.SelectedItem is null;
        await ClickSlotReal("PHONE", MouseButton.Right);
        await Frames(4);
        Check("AT04_right_click_item_in_drawer", cancelled && game.State.Mode == GameMode.Inventory && DialoguePresenter.Instance!.IsShowingBark,
              $"cancelled={cancelled} mode={game.State.Mode} bark={DialoguePresenter.Instance!.IsShowingBark}");
        await CloseDrawerReal();

        // ---------------------------------------------------------------- AT03 / AT06: BELT_NEW over the deck, labels with an item
        await Prepare("B06");
        await TravelToReal("S16");
        await SelectItemReal("BELT_NEW", keepDrawerOpen: false);
        string beltLabel = ItemLabel(new Hit.Hotspot("S16.deck"));
        await KeyEdge(Godot.Key.Space, true); // Space is hold-to-show (owner override 2026-10-05, ISSUES INT-08)
        bool labelsOn = game.State.HotspotLabels && CurrentRoom.Labels.MarkersVisible;
        await Frames(3);
        var outlines = CurrentRoom.Targets.ToList();
        bool outlineRule = outlines.All(t => t.ValidForSelectedItem == (ItemLabel(t.ToHit()).Length > 0));
        bool deckOutlined = outlines.Any(t => t.Id == "S16.deck" && t.ValidForSelectedItem);
        string wrongLabel = outlines.Where(t => t.Id != "S16.deck").Select(t => ItemLabel(t.ToHit())).FirstOrDefault(l => l.Length > 0) ?? "";
        Check("AT06_labels_with_item_only_valid_targets_outlined", labelsOn && outlineRule && deckOutlined && wrongLabel.Length == 0,
              $"labels={labelsOn} rule={outlineRule} deck_outlined={deckOutlined} wrong_label='{wrongLabel}'");
        await KeyEdge(Godot.Key.Space, false);
        await ClickTarget("S16.deck");
        await WaitUntil(() => game.State.IsDone("B06"), 20);
        await WaitLinesReal(20);
        bool b06Gone = !game.State.Has("BELT_NEW") && GameRules.AvailableActions(content, game.State).All(a => a.Id != "B06");
        Check("AT03_item_text_only_while_rule_exists", beltLabel.Length > 0 && game.State.Done.Count(d => d == "B06") == 1 && b06Gone,
              $"label_before='{beltLabel}' B06x{game.State.Done.Count(d => d == "B06")} belt_owned={game.State.Has("BELT_NEW")}");

        // ---------------------------------------------------------------- AT09: symmetric combinations
        foreach (var (id, other) in new[] { ("B10", "B11"), ("I04", "I05") })
        {
            await Prepare(id);
            var results = new List<string>();
            foreach (var actionId in new[] { id, other })
            {
                var a = content.GetAction(actionId);
                var inv = game.State;
                // Reverse order: the action's target item first, then click the item the data selects.
                await SelectItemReal(a.Target, keepDrawerOpen: true);
                await ClickSlotReal(a.SelectedItem!);
                await WaitUntil(() => game.State.IsDone(actionId), 15);
                await WaitLinesReal(20);
                bool ok = game.State.IsDone(actionId) && a.Gives.All(game.State.Has) && a.Consumes.All(c => !game.State.Has(c)) &&
                          game.State.Done.Length == inv.Done.Length + 1;
                results.Add($"{actionId}:{ok}");
            }
            Check($"AT09_reverse_selection_{id}_{other}", results.All(r => r.EndsWith(":True")), string.Join(" ", results));
        }

        // ---------------------------------------------------------------- AT07 / AT08: wrong answers 10x, close, load, solve once (all five puzzles)
        foreach (var actionId in content.Actions.Where(a => a.Puzzle is not null).Select(a => a.Id))
        {
            var a = content.GetAction(actionId);
            var def = content.GetPuzzle(a.Puzzle!);
            bool hud200 = def.Id == "P02";
            await Prepare(actionId);
            if (!a.IsInventoryAction) await TravelToReal(a.Room);
            if (hud200) { UiSettings.HudScalePercent = 200; await Frames(6); }
            var start = game.State;
            await OpenPuzzleReal(a);
            bool opened = game.State.Mode == GameMode.Puzzle;
            await EnterPuzzleAnswerReal(def, WrongAnswer(def));
            for (int i = 0; i < 10; i++) await ConfirmPuzzleReal(def);
            bool noCommit = !game.State.IsDone(actionId) && game.State.Mode == GameMode.Puzzle && game.State.Inventory.SequenceEqual(start.Inventory);
            await KeyReal(Godot.Key.Escape); // close the modal
            bool closed = await WaitUntil(() => game.State.Mode is GameMode.World or GameMode.Inventory, 5);
            if (game.State.Mode == GameMode.Inventory) await CloseDrawerReal();
            game.Save("m2_accept_puzzle");
            game.Load("m2_accept_puzzle");
            await Settle();
            await OpenPuzzleReal(a);
            await EnterPuzzleAnswerReal(def, def.Solution?.DeepClone());
            await ConfirmPuzzleReal(def);
            await WaitUntil(() => game.State.IsDone(actionId), 20);
            await WaitLinesReal(60);
            var expected = start.Inventory.Where(x => !a.Consumes.Contains(x)).Concat(a.Gives).OrderBy(x => x).ToList();
            bool once = game.State.Done.Count(d => d == actionId) == 1 && game.State.Inventory.OrderBy(x => x).SequenceEqual(expected);
            Check($"AT07_{def.Id}_wrong_x10_close_load_solve_once", opened && noCommit && closed && once,
                  $"opened={opened} no_commit={noCommit} closed={closed} once={once} inv=[{Inv(game.State)}]");
            if (hud200)
            {
                Check("AT08_P02_at_200_percent_hud", once && blockers.Count == 0, $"solved={once} blockers={blockers.Count}");
                UiSettings.HudScalePercent = 100;
                await Frames(4);
            }
        }
        GameRuntime.DeleteSlot("m2_accept_puzzle");

        // ---------------------------------------------------------------- AT16: skip every cutscene (Esc) vs watch it: same state
        foreach (var a in content.Actions.Where(x => x.Cutscene is not null))
        {
            await Prepare(a.Id);
            game.Save("m2_accept_cs");
            await PerformActReal(a.Id);
            await WaitLinesReal(120);
            if (UiRoot.Instance!.TopModal is EndingSequence) await FinishEndingReal(replay: false);
            var watched = game.State;
            game.Load("m2_accept_cs");
            await Settle();
            await PerformActReal(a.Id);
            bool sawCutscene = await WaitUntil(() => game.State.Mode == GameMode.Cutscene, 30);
            await KeyReal(Godot.Key.Escape);
            await WaitLinesReal(60);
            if (UiRoot.Instance!.TopModal is EndingSequence) await FinishEndingReal(replay: false);
            var skipped = game.State;
            Check($"AT16_skip_{a.Cutscene}_same_state", sawCutscene && SameProgress(watched, skipped),
                  $"cutscene_seen={sawCutscene} room={skipped.Room}/{watched.Room} done={skipped.Done.Length}/{watched.Done.Length} inv_same={skipped.Inventory.OrderBy(x => x).SequenceEqual(watched.Inventory.OrderBy(x => x))}");
        }
        GameRuntime.DeleteSlot("m2_accept_cs");

        // ---------------------------------------------------------------- AT17: save/load in the middle of F11 (CS06) and of the finale (CS07)
        foreach (var id in new[] { "F11", "F17" })
        {
            await Prepare(id);
            await PerformActReal(id);
            await WaitUntil(() => game.State.Mode == GameMode.Cutscene, 30);
            await Seconds(0.3);
            string? line = game.State.ActiveLineId;
            game.Save("m2_accept_mid");
            var saved = game.State;
            game.Load("m2_accept_mid");
            await Frames(4);
            bool sameLine = game.State.ActiveLineId == line && SameProgress(saved, game.State);
            await WaitUntil(() => game.State.ActiveLineId is null && game.State.Mode == GameMode.World, 120);
            if (id != "F17") await WaitLinesReal(60);
            bool ending = true;
            if (id == "F17") ending = await FinishEndingReal(replay: false) >= 0;
            Check($"AT17_save_load_mid_{id}_cutscene", line is not null && sameLine && game.State.Done.Count(d => d == id) == 1 && ending,
                  $"line={line} same_line={sameLine} ending_after_load={ending}");
        }
        GameRuntime.DeleteSlot("m2_accept_mid");

        // ---------------------------------------------------------------- AT18: corrupt save and unknown item: readable refusal, game untouched
        await Prepare("B01");
        var untouched = game.State;
        string? refused = null;
        void OnFailed(string slot, LastBell.Core.Text.TextRef error) => refused = TextService.Get(error);
        game.LoadFailed += OnFailed;
        DirAccess.MakeDirRecursiveAbsolute(GameRuntime.SaveDirectory);
        using (var f = Godot.FileAccess.Open(GameRuntime.SlotPath("m2_accept_corrupt"), Godot.FileAccess.ModeFlags.Write)) f.StoreString("{\"schema_version\": 1, \"state\": {not json");
        bool loadedCorrupt = game.Load("m2_accept_corrupt");
        string json = LastBell.Core.Save.SaveCodec.Serialize(game.State).Replace("\"TOOLS\"", "\"UNKNOWN_ITEM\"");
        bool loadedUnknown = game.LoadFromJson(json, "m2 unknown item");
        game.LoadFailed -= OnFailed;
        await Frames(4);
        bool dialog = UiRoot.Instance!.TopModal is ConfirmDialog;
        while (UiRoot.Instance!.TopModal is ConfirmDialog) await KeyReal(Godot.Key.Escape);
        Check("AT18_corrupt_and_unknown_item_save_refused", !loadedCorrupt && !loadedUnknown && SameProgress(untouched, game.State) && refused is { Length: > 0 } && dialog,
              $"corrupt_loaded={loadedCorrupt} unknown_loaded={loadedUnknown} message='{refused}' dialog={dialog}");
        GameRuntime.DeleteSlot("m2_accept_corrupt");

        // ---------------------------------------------------------------- AT11: first entry to Ivanka 1960 and back through every unlocked era
        await Prepare("I01");
        var invStart = game.State.Inventory.OrderBy(x => x).ToList();
        var visitedEras = new List<int>();
        foreach (var room in new[] { "S11", "S10", "S31" })
        {
            await TravelToReal(room);
            visitedEras.Add(game.State.Era);
        }
        Check("AT11_return_to_all_unlocked_eras", visitedEras.SequenceEqual(new[] { 1995, 2020, 1960 }) && game.State.Inventory.OrderBy(x => x).SequenceEqual(invStart),
              $"eras=[{string.Join(",", visitedEras)}] inv_same={game.State.Inventory.OrderBy(x => x).SequenceEqual(invStart)}");

        // ---------------------------------------------------------------- AT12: the map never skips a closed gate
        await Prepare("B02"); // S16 (cabinet) not yet open
        await KeyReal(Godot.Key.M);
        await WaitUntil(() => game.State.Mode == GameMode.Map, 5);
        await Frames(6);
        var map = Descendants<MapScreen>(UiRoot.Instance!).First();
        var view = LastBell.Core.Views.ViewBuilder.Map(content, game.State);
        var sameEra = view.First(e => e.Year == game.State.Era).Rooms;
        bool flagsMatch = sameEra.All(r => !r.CanFastTravel || (r.Visited && Navigation.FindRoute(content, game.State, r.RoomId) is not null));
        string here = game.State.Room;
        var unvisited = Descendants<Button>(map).FirstOrDefault(b => b.IsVisibleInTree() && b.Text == TextService.Ui("ui.map.unvisited"));
        if (unvisited is not null) await ClickControl(unvisited, "map unvisited node");
        await Frames(6);
        bool stayed = game.State.Room == here;
        var target = sameEra.FirstOrDefault(r => r.CanFastTravel);
        bool travelled = false;
        if (target is not null)
        {
            string name = TextService.Get(target.Name);
            var node = Descendants<Button>(map).FirstOrDefault(b => b.IsVisibleInTree() && b.Text == name);
            if (node is not null && await ClickControl(node, "map node " + target.RoomId))
                travelled = await WaitUntil(() => game.State.Room == target.RoomId && WorldStage.Instance!.IsSettled, 20);
        }
        if (game.State.Mode == GameMode.Map) await KeyReal(Godot.Key.Escape);
        Check("AT12_map_fast_travel_respects_gates", flagsMatch && stayed && (target is null || travelled),
              $"flags_match={flagsMatch} unvisited_click_stays={stayed} fast_travel={(target is null ? "-" : target.RoomId + ":" + travelled)}");
        await WaitLinesReal(20);

        // ---------------------------------------------------------------- AT15 (one order in the engine): ports in reverse order
        await Prepare("F12");
        foreach (var id in new[] { "F15", "F14", "F13", "F12" })
        {
            bool f16Early = GameRules.AvailableActions(content, game.State).Any(a => a.Id == "F16");
            if (f16Early) { Check("AT15_F16_never_early", false, "F16 available before all four ports"); break; }
            await PerformActReal(id);
        }
        Check("AT15_ports_reverse_order_then_F16", GameRules.AvailableActions(content, game.State).Any(a => a.Id == "F16") && game.State.SelectedItem is null,
              $"F16_available={GameRules.AvailableActions(content, game.State).Any(a => a.Id == "F16")} selected={game.State.SelectedItem ?? "-"}");

        // ---------------------------------------------------------------- AT23: menus and waiting before F09 change nothing
        await Prepare("F09");
        var waitStart = game.State;
        await KeyReal(Godot.Key.Escape); // pause
        bool paused = game.State.Mode == GameMode.Pause;
        await Seconds(30);
        await KeyReal(Godot.Key.Escape);
        await KeyReal(Godot.Key.J);
        await Seconds(10);
        await KeyReal(Godot.Key.Escape);
        await Frames(4);
        Check("AT23_no_timer_before_F09", paused && SameProgress(waitStart, game.State) && game.State.Mode == GameMode.World &&
              GameRules.GuardsPass(content.GetAction("F09"), game.State), $"paused={paused} mode={game.State.Mode}");

        // ---------------------------------------------------------------- AT29: no shortcut from Biela Púť to the Rotunda before the first ride
        await Prepare("J02");
        var rotundaRoute = Navigation.FindRoute(content, game.State, "S47");
        bool noEdge = rotundaRoute is null && !LastBell.Core.Views.ViewBuilder.Map(content, game.State).SelectMany(e => e.Rooms).Any(r => r.RoomId == "S47" && r.CanFastTravel);
        await PerformActReal("J02");
        await PerformActReal("J03");
        await PerformActReal("J04");
        bool ticketKept = game.State.Has("LIFT_TICKET");
        Check("AT29_no_bypass_before_J02_J04", noEdge && game.State.Room == "S47" && ticketKept,
              $"route_before={(rotundaRoute is null ? "none" : rotundaRoute.Count + " steps")} room={game.State.Room} ticket_kept={ticketKept}");

        // ---------------------------------------------------------------- AT25 / AT21: variant layers and causal effects appear on re-entry
        await Prepare("E10");
        await TravelToReal("S17");
        bool s17Before = CurrentRoom.View.VariantLayers.Any(v => v.Visible);
        await TravelToReal("S55");
        bool s55Before = CurrentRoom.View.VariantLayers.Any(v => v.Visible);
        string s55Look = (game.Session.Resolve(new Hit.Hotspot("S55.ambient 1"), PointerButton.Right) as Resolution.Look)?.Text.Key ?? "";
        bool s55LookShown = await ClickTarget("S55.ambient 1", MouseButton.Right) && await WaitUntil(() => DialoguePresenter.Instance!.IsShowingBark, 3);
        Check("AT24_look_before_E10_S55_ambient_1", s55Look == "look.S55.ambient 1" && s55LookShown, $"key={s55Look} bark={s55LookShown}");
        bool photoBefore = game.State.Has("PHOTO2020");
        await PerformActReal("E10");
        await WaitLinesReal(60);
        await TravelToReal("S17");
        bool s17After = CurrentRoom.View.VariantLayers.Any(v => v.Visible && v.Layer.After == "E10") && MarkerCount() > 0;
        bool walkable = CurrentRoom.Targets.All(t => CurrentRoom.Walk.FindPath(CurrentRoom.Hero.Feet, t.InteractionPoint) is not null || t.Kind == TargetKind.Npc);
        await TravelToReal("S55");
        bool s55After = CurrentRoom.View.VariantLayers.Any(v => v.Visible && v.Layer.After == "E10") && MarkerCount() > 0;
        Check("AT25_tree_variants_after_E10_walkable", !s17Before && !s55Before && s17After && s55After && walkable && photoBefore == game.State.Has("PHOTO2020"),
              $"S17 before={s17Before} after={s17After} S55 before={s55Before} after={s55After} walkable={walkable} photo2020_kept={game.State.Has("PHOTO2020")}");

        foreach (var (room, trigger, before2) in new[] { ("S15", "Q9C", "E01"), ("S43", "Q4C", "F02"), ("S47", "Q5C", "F07") })
        {
            await Prepare(before2);
            await TravelToReal(room);
            int causalBefore = CurrentRoom.View.CausalEffects.Count(c => c.Effect.After == trigger);
            string? janaBefore = room == "S15" ? NpcVariant("S15.JANA95") : null;
            var quests = Quests.ActiveSideQuest(content, game.State)?.Id;
            var s = game.State;
            var all = content.Quests.First(q => q.Actions.Contains(trigger)).Actions.ToList();
            var questActions = all.Take(all.IndexOf(trigger) + 1);
            foreach (var id in questActions) if (!s.IsDone(id)) s = CoreDo(content, s, id);
            game.ReplaceState(s);
            await Settle();
            await WaitLinesReal(20);
            await TravelToReal(room);
            int causalAfter = CurrentRoom.View.CausalEffects.Count(c => c.Effect.After == trigger && !c.DeferredUntilReentry);
            Check($"AT21_{room}_causal_effect_after_{trigger}", causalBefore == 0 && causalAfter == 1 && (CurrentRoom.HasBackgroundArt || MarkerCount() > 0),
                  $"before={causalBefore} after={causalAfter} markers={MarkerCount()} active_side_before={quests ?? "-"}");
            if (room == "S15")
            {
                // Jana's Q9C prop variants (BF_JANA; ISSUES ART-AGE-04): data/ambient/actors.json variants_after.
                string? janaAfter = NpcVariant("S15.JANA95");
                var rules20 = LastBell.Game.Living.Actors.ActorStaging.VariantRulesFor("JANA20");
                string? jana20 = LastBell.Game.Living.Actors.ActorStaging.ResolveVariant("laptop", rules20, game.State.IsDone);
                string? jana20Screen = LastBell.Game.Living.Actors.ActorStaging.ResolveVariant("screen", rules20, game.State.IsDone);
                bool sheets = LastBell.Game.Living.Actors.ActorAnimationSet.Load("JANA20", jana20) is not null &&
                              LastBell.Game.Living.Actors.ActorAnimationSet.Load("JANA35", "q9c") is not null;
                Check("AT21_S15_jana_prop_variant_after_Q9C", janaBefore is null && janaAfter == "q9c" && jana20 == "laptop_q9c" && jana20Screen == "screen_q9c" && sheets,
                      $"JANA95 before={janaBefore ?? "default"} after={janaAfter ?? "default"} JANA20={jana20}/{jana20Screen} sheets={sheets}");
            }
        }

        // ---------------------------------------------------------------- AT24 (lines): the S06 photo between C04 and F17
        await Prepare("C05");
        await TravelToReal("S06");
        string photoLook = (game.Session.Resolve(new Hit.Hotspot("S06.photo"), PointerButton.Right) as Resolution.Look)?.Text.Key ?? "";
        bool photoShown = await ClickTarget("S06.photo", MouseButton.Right) && await WaitUntil(() => DialoguePresenter.Instance!.IsShowingBark, 3);
        Check("AT24_look_after_C04_S06_photo_variant2", photoLook == "look.S06.photo.variant2" && photoShown, $"key={photoLook} bark={photoShown}");

        // ---------------------------------------------------------------- AT26: one cache lineage, no second young cup
        await Prepare("D06");
        bool invariant = TemporalCache.InvariantHolds(content, game.State);
        await TravelToReal("S61");
        var niche = CurrentRoom.Targets.FirstOrDefault(t => t.Id.Contains("niche") || t.Id.Contains("cache") || t.Id.Contains("wall"));
        var beforeNiche = game.State;
        if (niche is not null) await ClickTarget(niche.Id);
        await WaitLinesReal(20);
        bool noSecond = !game.State.Has("SEALED_NEW") && game.State.Inventory.Length == beforeNiche.Inventory.Length &&
                        GameRules.AvailableActions(content, game.State).All(a => a.Room != "S61");
        Check("AT26_cache_single_lineage", invariant && noSecond && TemporalCache.InvariantHolds(content, game.State),
              $"invariant={invariant} clicked={niche?.Id ?? "-"} no_second_item={noSecond} stage={TemporalCache.StatusOf(content, game.State).Stage}");

        // ---------------------------------------------------------------- AT05 / AT20: Space labels and a clickable point for every target in all 68 rooms
        var full = content.InitialState;
        foreach (var id in MainRoute()) full = CoreDo(content, full, id);
        foreach (var id in SideOrder()) full = CoreDo(content, full, id);
        int roomsOk = 0;
        var bad = new List<string>();
        int blockersBefore = blockers.Count;
        foreach (var room in content.Rooms)
        {
            var st = full with
            {
                Room = room.Id, Era = room.Era, Mode = GameMode.World, ActiveLineId = null, SelectedItem = null, HotspotLabels = false,
                PlaybackQueue = System.Collections.Immutable.ImmutableArray<string>.Empty, RoomEntryDoneCount = full.Done.Length,
            };
            game.ReplaceState(st); // dev jump: labels and hit areas only depend on done, not on how the hero got here
            await Settle();
            // Space held: a marker on every visible target, no text labels; released: none (owner override 2026-10-05).
            await KeyEdge(Godot.Key.Space, true);
            await Frames(2);
            var expectedIds = GameRules.HotspotList(content, game.State).Select(h => h.Id).OrderBy(x => x).ToList();
            var shownIds = CurrentRoom.Targets.Select(t => t.Id).OrderBy(x => x).ToList();
            var markedIds = CurrentRoom.Labels.MarkedIds.OrderBy(x => x).ToList();
            bool labels = game.State.HotspotLabels && expectedIds.SequenceEqual(shownIds) && expectedIds.SequenceEqual(markedIds) &&
                          CurrentRoom.Labels.TextLabelsDrawn == 0 && CurrentRoom.Targets.All(t => TextService.Get(t.Name).Length > 0);
            await KeyEdge(Godot.Key.Space, false);
            labels &= !game.State.HotspotLabels && CurrentRoom.Labels.MarkedIds.Count == 0;
            bool clickable = true;
            foreach (var t in CurrentRoom.Targets.ToList()) clickable &= await FindClickPoint(t.Id) is not null;
            if (labels && clickable) roomsOk++;
            else bad.Add($"{room.Id}(labels={labels},clickable={clickable})");
        }
        var size = DisplayServer.GetName() == "headless" ? "headless" : DisplayServer.WindowGetSize().ToString();
        Check("AT05_space_markers_all_68_rooms", bad.All(b => b.Contains("labels=True")), $"{roomsOk}/{content.Rooms.Count} rooms ok; {string.Join(" ", bad)}");
        Check("AT20_every_target_clickable_" + size.Replace(" ", ""), blockers.Count == blockersBefore, $"{blockers.Count - blockersBefore} target(s) without a clickable point at {size}");

        Log($"acceptance m2: {acceptanceFailures - failuresBefore} failure(s)");
    }

    /// <summary>Sprite variant of an NPC in the current room ("-" when it has no sprite visual).</summary>
    private static string? NpcVariant(string hotspotId) =>
        CurrentRoom.Npcs.TryGetValue(hotspotId, out var actor)
            ? (actor.Visual as LastBell.Game.Living.Actors.SpriteActorVisual)?.Variant ?? (actor.Visual is LastBell.Game.Living.Actors.SpriteActorVisual ? null : "-")
            : "-";

    private static int MarkerCount() => CurrentRoom.Layer("prop_state_variants")?.GetChildCount() ?? 0;

    /// <summary>Presses Tab until the target has keyboard focus (at most one round over all targets).</summary>
    private async Task<bool> FocusByTab(string targetId)
    {
        int n = CurrentRoom.Targets.Count() + 2;
        for (int i = 0; i < n; i++)
        {
            if (InteractionController.Instance?.FocusedId == targetId) return true;
            await KeyReal(Godot.Key.Tab);
        }
        return InteractionController.Instance?.FocusedId == targetId;
    }

    private async Task OpenPuzzleReal(ActionDef a)
    {
        var game = GameRuntime.Instance;
        if (a.SelectedItem is not null) await SelectItemReal(a.SelectedItem, keepDrawerOpen: a.IsCombine);
        if (a.IsCombine) await ClickSlotReal(a.Target);
        else await ClickTarget(a.Target);
        await WaitUntil(() => game.State.Mode == GameMode.Puzzle, 20);
        await Frames(4);
    }
}
