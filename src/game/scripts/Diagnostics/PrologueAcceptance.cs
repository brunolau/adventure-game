using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Game.Presentation;
using LastBell.Game.Runtime;
using LastBell.Game.World;

namespace LastBell.Game.Diagnostics;

/// <summary>
/// In-engine acceptance checks of the prologue's input rules (milestone 1), run with
/// <c>--acceptance</c> after "--". Every check drives the game through real Godot input events
/// (<see cref="RawMouse"/>, key events) or the documented UI entry points, never by editing Core
/// state behind the resolver; states are prepared with Core walkthrough replays only.
/// Prints <c>HARNESS PASS|FAIL &lt;check&gt;: detail</c> and a summary; the exit code is the number of
/// failures (capped at 1 by the caller). Writes and deletes the save slots <c>m1_accept_*</c>.
/// </summary>
public partial class DebugHarness
{
    private int acceptanceFailures;

    private void Check(string name, bool ok, string detail = "")
    {
        if (!ok) acceptanceFailures++;
        Log($"{(ok ? "PASS" : "FAIL")} {name}{(detail.Length > 0 ? ": " + detail : "")}");
    }

    private async Task Settle()
    {
        await WaitUntil(() => WorldStage.Instance!.IsSettled && WorldStage.Instance.IsFadedIn, 15);
        await SkipLines(15);
        await Frames(3);
    }

    private async Task FromReplay(int steps)
    {
        var game = GameRuntime.Instance;
        game.ReplaceState(WalkthroughReplayer.Replay(game.Content, game.Content.InitialState, steps));
        await Settle();
    }

    private static Room CurrentRoom => WorldStage.Instance!.Current!;

    private static Vector2 CenterOf(string targetId) =>
        CurrentRoom.TryGetTarget(targetId, out var t) ? t.Rect.GetCenter() : throw new InvalidOperationException("no target " + targetId);

    private async Task SelectFromInventory(string itemId)
    {
        // What the inventory drawer does: open it (I), click the slot (Submit Item, Left).
        if (GameRuntime.Instance.State.Mode != GameMode.Inventory) await Key(Godot.Key.I);
        LastBell.Game.PlayerInput.WorldInput.Submit(new Hit.Item(itemId), PointerButton.Left);
        await Frames(2);
        if (GameRuntime.Instance.State.Mode == GameMode.Inventory) await Key(Godot.Key.I);
    }

    private async Task Key(Key key)
    {
        foreach (bool pressed in new[] { true, false })
        {
            Godot.Input.ParseInputEvent(new InputEventKey { Keycode = key, PhysicalKeycode = key, Pressed = pressed });
            await Frames(1);
        }
        await Frames(1);
    }

    private static int Count(GameState s, string item) => s.Inventory.Count(i => i == item);

    /// <summary>Half a key press (hold / release), a real input event.</summary>
    private async Task KeyEdge(Key key, bool pressed)
    {
        Godot.Input.ParseInputEvent(new InputEventKey { Keycode = key, PhysicalKeycode = key, Pressed = pressed });
        await Frames(2);
    }

    /// <summary>A point on the walkable floor (hit test: floor) at least <paramref name="minDistance"/> px from the hero.</summary>
    private static Vector2? FloorPointAway(float minDistance)
    {
        var room = CurrentRoom;
        var feet = room.Hero.Feet;
        for (int y = 1040; y >= 300; y -= 40)
            for (int x = 120; x <= 1800; x += 60)
            {
                var p = new Vector2(x, y);
                if (room.HitTest(p) is Hit.Floor && p.DistanceTo(feet) >= minDistance && room.Walk.FindPath(feet, p) is not null) return p;
            }
        return null;
    }

    /// <summary>Owner control changes 2026-10-05: hold Space, hover label at the cursor, contextual cursor, double click.</summary>
    private async Task RunControlChecks()
    {
        var game = GameRuntime.Instance;
        var presenter = DialoguePresenter.Instance!;
        var room = CurrentRoom;
        var hero = room.Hero;

        // ---------------------------------------------------------------- Space: hold to show markers (no text), release hides
        var layer = room.Labels;
        int targets = room.Targets.Count();
        await KeyEdge(Godot.Key.Space, true);
        await Frames(2);
        bool held = game.State.HotspotLabels && layer.MarkersVisible;
        int marked = layer.MarkedIds.Count;
        int texts = layer.TextLabelsDrawn;
        var expected = GameRules.HotspotList(game.Content, game.State).Select(h => h.Id).OrderBy(x => x, StringComparer.Ordinal);
        bool all = layer.MarkedIds.OrderBy(x => x, StringComparer.Ordinal).SequenceEqual(expected);
        await Frames(10); // still held: no toggle back
        bool stillHeld = game.State.HotspotLabels;
        await KeyEdge(Godot.Key.Space, false);
        await Frames(2);
        Check("space_hold_shows_markers_release_hides", held && stillHeld && all && marked == targets && texts == 0 && !game.State.HotspotLabels && layer.MarkedIds.Count == 0,
              $"held={held} still={stillHeld} markers={marked}/{targets} all={all} text_labels={texts} after_release={game.State.HotspotLabels}");

        // ---------------------------------------------------------------- hover label at the cursor and the contextual cursor
        var ui = LastBell.Game.UI.UiRoot.Instance;
        if (ui is not null && room.TryGetTarget("S01.ambient 2", out var look))
        {
            var lookPoint = await FindClickPoint(look.Id) ?? look.Rect.GetCenter();
            await MoveMouse(lookPoint);
            await Frames(3);
            string shown = ui.HoverLabel.ShownName;
            var rect = ui.HoverLabel.ShownRect;
            var lookCursor = LastBell.Game.UI.Hud.CursorSet.Current;
            var floor = FloorPointAway(0) ?? new Vector2(960, 1000);
            await MoveMouse(floor);
            await Frames(3);
            string onFloor = ui.HoverLabel.ShownName;
            var floorCursor = LastBell.Game.UI.Hud.CursorSet.Current;
            Check("hover_label_at_cursor_not_in_hud", shown == TextService.Get(look.Name) && shown.Length > 0 && !rect.HasPoint(lookPoint) &&
                  rect.Position.X >= 0 && rect.End.X <= Room.CanvasSize.X && rect.End.Y <= Room.CanvasSize.Y && onFloor.Length == 0,
                  $"label='{shown}' rect={rect} pointer={lookPoint} floor_label='{onFloor}'");
            var exitHit = room.Targets.FirstOrDefault(t => t.Kind == TargetKind.Exit);
            var exitCursor = LastBell.Game.UI.Hud.CursorKind.Pointer;
            if (exitHit is not null && await FindClickPoint(exitHit.Id) is { } ep)
            {
                await MoveMouse(ep);
                await Frames(3);
                exitCursor = LastBell.Game.UI.Hud.CursorSet.Current;
            }
            Check("contextual_cursor", lookCursor == LastBell.Game.UI.Hud.CursorKind.Look && floorCursor == LastBell.Game.UI.Hud.CursorKind.Pointer &&
                  exitCursor.ToString().StartsWith("Exit", StringComparison.Ordinal),
                  $"look={lookCursor} floor={floorCursor} exit={exitCursor}");
        }

        // ---------------------------------------------------------------- double click on the floor: the hero is there at once
        if (FloorPointAway(400) is { } dest)
        {
            int skips = 0;
            void OnSkip() => skips++;
            InteractionController.Instance!.WalkSkipped += OnSkip;
            await RawMouse(dest, MouseButton.Left);
            await RawMouse(dest, MouseButton.Left);
            await Frames(1);
            InteractionController.Instance!.WalkSkipped -= OnSkip;
            var target = room.Walk.Clamp(dest);
            Check("double_click_floor_skips_walk", skips == 1 && !hero.IsWalking && hero.Feet.DistanceTo(target) < 3f,
                  $"skips={skips} walking={hero.IsWalking} feet={hero.Feet} target={target}");
        }

        // ---------------------------------------------------------------- double click on a look-only prop: placed at its point, the look runs once
        if (room.TryGetTarget("S01.ambient 2", out var prop) && await FindClickPoint(prop.Id) is { } pp)
        {
            presenter.HideBark();
            var far = FloorPointAway(500); // stand away from the prop first (a double click on the floor gets him there)
            if (far is { } f) { await RawMouse(f, MouseButton.Left); await RawMouse(f, MouseButton.Left); await Frames(2); }
            int done = game.State.Done.Length;
            await RawMouse(pp, MouseButton.Left);
            await RawMouse(pp, MouseButton.Left);
            await Frames(2);
            Check("double_click_prop_arrives_and_acts_once", !hero.IsWalking && hero.Feet.DistanceTo(prop.InteractionPoint) < 3f && presenter.IsShowingBark &&
                  game.State.Done.Length == done && !InteractionController.Instance!.HasPending,
                  $"walking={hero.IsWalking} feet={hero.Feet} point={prop.InteractionPoint} bark={presenter.IsShowingBark} pending={InteractionController.Instance!.HasPending}");
            presenter.HideBark();
        }

        // ---------------------------------------------------------------- Shift+Enter on the focused exit: skip the walk, travel once
        var exit = room.Targets.FirstOrDefault(t => t.Kind == TargetKind.Exit && t.Unlocked && game.Session.Resolve(t.ToHit(), PointerButton.Left) is Resolution.Travel);
        if (exit is not null)
        {
            string from = game.State.Room;
            int changes = 0;
            void OnRoom(string a, string? b) => changes++;
            game.RoomChanged += OnRoom;
            if (await FindClickPoint(exit.Id) is { } xp)
            {
                // double click on the exit
                await RawMouse(xp, MouseButton.Left);
                await RawMouse(xp, MouseButton.Left);
                await Frames(1);
                bool placed = hero.Feet.DistanceTo(exit.InteractionPoint) < 3f && !hero.IsWalking;
                await WaitUntil(() => game.State.Room != from && WorldStage.Instance!.IsSettled && WorldStage.Instance.IsFadedIn, 20);
                await Settle();
                game.RoomChanged -= OnRoom;
                Check("double_click_exit_skips_walk_travels_once", placed && game.State.Room != from && changes == 1,
                      $"placed={placed} room={game.State.Room} room_changes={changes}");
            }
            else game.RoomChanged -= OnRoom;
        }
    }

    /// <summary>A point of the target that the room's hit test returns and no GUI control covers (no blocker logged), or null.</summary>
    private async Task<Vector2?> ScenePoint(string targetId)
    {
        var room = CurrentRoom;
        if (!room.TryGetTarget(targetId, out var target)) return null;
        var want = target.ToHit();
        foreach (var (fx, fy) in new[]
                 {
                     (0.5f, 0.5f), (0.5f, 0.3f), (0.5f, 0.7f), (0.3f, 0.5f), (0.7f, 0.5f), (0.25f, 0.25f), (0.75f, 0.25f),
                     (0.25f, 0.75f), (0.75f, 0.75f), (0.5f, 0.12f), (0.5f, 0.88f), (0.12f, 0.5f), (0.88f, 0.5f),
                 })
        {
            var p = target.Rect.Position + new Vector2(target.Rect.Size.X * fx, target.Rect.Size.Y * fy);
            if (p.X < 1 || p.Y < 1 || p.X > Room.CanvasSize.X - 1 || p.Y > Room.CanvasSize.Y - 1 || !Equals(room.HitTest(p), want)) continue;
            await MoveMouse(p);
            if (HoveredGui() is null && !(LastBell.Game.UI.UiRoot.Instance?.ScreenCovers(p) ?? false)) return p;
        }
        return null;
    }

    /// <summary>
    /// Owner control change 6 (2026-10-06, ISSUES INT-09): a right click outside the open drawer closes it and keeps the
    /// picked item; with an item selected only valid combinations get a hover label, a Space marker and a Tab stop;
    /// without one every visible target does. S05 with GROCERIES (after G03): the tray is the one valid target among
    /// four props and three exits.
    /// </summary>
    private async Task RunSelectionControlChecks()
    {
        var game = GameRuntime.Instance;
        var presenter = DialoguePresenter.Instance!;
        var ui = LastBell.Game.UI.UiRoot.Instance;
        await FromReplay(3);
        await TravelTo("S05");
        await Settle();
        var room = CurrentRoom;
        var hero = room.Hero;
        const string valid = "S05.tray";

        // ---------------------------------------------------------------- without a selection: every target hovers, gets a marker and a Tab stop
        var all = room.Targets.Select(t => t.Id).OrderBy(x => x, StringComparer.Ordinal).ToList();
        int hovered = 0;
        var unlabelled = new List<string>();
        if (ui is not null)
            foreach (var id in all)
            {
                if (await ScenePoint(id) is not { } p) { unlabelled.Add(id + "(no point)"); continue; }
                await MoveMouse(p);
                await Frames(2);
                if (ui.HoverLabel.ShownName.Length > 0) hovered++;
                else unlabelled.Add(id);
            }
        Check("no_selection_every_target_hover_label", ui is not null && hovered == all.Count,
              $"{hovered}/{all.Count} labelled; missing [{string.Join(",", unlabelled)}]");
        await KeyEdge(Godot.Key.Space, true);
        await Frames(2);
        var markedAll = room.Labels.MarkedIds.OrderBy(x => x, StringComparer.Ordinal).ToList();
        await KeyEdge(Godot.Key.Space, false);
        Check("no_selection_space_marks_every_target", markedAll.SequenceEqual(all), $"marked {markedAll.Count}/{all.Count}");
        var focusedAll = new HashSet<string>(StringComparer.Ordinal);
        for (int i = 0; i < all.Count + 1; i++)
        {
            await Key(Godot.Key.Tab);
            if (InteractionController.Instance!.FocusedId is { } f) focusedAll.Add(f);
        }
        InteractionController.Instance!.ClearFocus();
        Check("no_selection_tab_cycles_every_target", focusedAll.Count == room.View.AccessibleOrder.Count(id => room.TryGetTarget(id, out _)),
              $"focused {focusedAll.Count}");

        // ---------------------------------------------------------------- pick the item in the drawer, right click outside: drawer closes, item stays
        var invalid = room.Targets.FirstOrDefault(t => t.Kind == TargetKind.Prop && t.Id != valid)?.Id ?? "S05.shed_door";
        bool picked = await ClickSlotReal("GROCERIES");
        await Frames(2);
        bool drawerOpen = game.State.Mode == GameMode.Inventory && game.State.SelectedItem == "GROCERIES";
        var outside = await ScenePoint(invalid);
        var feet = hero.Feet;
        if (outside is { } o) await RawMouseReal(o, MouseButton.Right);
        await Frames(4);
        Check("right_click_outside_drawer_closes_keeps_selection", picked && drawerOpen && outside is not null && game.State.Mode == GameMode.World &&
              game.State.SelectedItem == "GROCERIES" && !presenter.IsShowingBark && !hero.IsWalking && hero.Feet == feet,
              $"picked={picked} drawer_open_before={drawerOpen} point={outside} mode={game.State.Mode} selected={game.State.SelectedItem} bark={presenter.IsShowingBark}");

        // ---------------------------------------------------------------- with the item: only the valid target gets a label, a marker and a Tab stop
        string validName = "", validAction = "", invalidName = "", exitName = "";
        var invalidCursor = LastBell.Game.UI.Hud.CursorKind.Pointer;
        if (ui is not null)
        {
            if (await ScenePoint(valid) is { } vp) { await MoveMouse(vp); await Frames(2); validName = ui.HoverLabel.ShownName; validAction = ui.HoverLabel.ShownAction; }
            if (await ScenePoint(invalid) is { } ip) { await MoveMouse(ip); await Frames(2); invalidName = ui.HoverLabel.ShownName + ui.HoverLabel.ShownAction; invalidCursor = LastBell.Game.UI.Hud.CursorSet.Current; }
            var exitId = room.Targets.FirstOrDefault(t => t.Kind == TargetKind.Exit)?.Id;
            if (exitId is not null && await ScenePoint(exitId) is { } ep) { await MoveMouse(ep); await Frames(2); exitName = ui.HoverLabel.ShownName + ui.HoverLabel.ShownAction; }
        }
        bool cursorChecked = DisplayServer.GetName() == "headless" || invalidCursor == LastBell.Game.UI.Hud.CursorKind.Item;
        Check("with_selection_only_valid_target_hover_label", validName.Length > 0 && validAction.Length > 0 && invalidName.Length == 0 && exitName.Length == 0 && cursorChecked,
              $"valid='{validName} / {validAction}' invalid='{invalidName}' exit='{exitName}' cursor_over_invalid={invalidCursor}");
        await KeyEdge(Godot.Key.Space, true);
        await Frames(2);
        var markedWith = room.Labels.MarkedIds.ToList();
        bool layerOn = room.Labels.MarkersVisible;
        await KeyEdge(Godot.Key.Space, false);
        Check("with_selection_space_marks_only_valid_targets", layerOn && markedWith.SequenceEqual(new[] { valid }),
              $"marked [{string.Join(",", markedWith)}]");
        var focusedWith = new HashSet<string>(StringComparer.Ordinal);
        for (int i = 0; i < 3; i++)
        {
            await Key(Godot.Key.Tab);
            if (InteractionController.Instance!.FocusedId is { } f) focusedWith.Add(f);
        }
        InteractionController.Instance!.ClearFocus();
        Check("with_selection_tab_cycles_only_valid_targets", focusedWith.SetEquals(new[] { valid }), $"focused [{string.Join(",", focusedWith)}]");

        // ---------------------------------------------------------------- further right click (drawer closed) cancels the selection
        if (outside is { } o2) await RawMouseReal(o2, MouseButton.Right);
        await Frames(3);
        Check("right_click_after_drawer_closed_cancels_selection", game.State.SelectedItem is null && game.State.Mode == GameMode.World,
              $"selected={game.State.SelectedItem} mode={game.State.Mode}");

        // ---------------------------------------------------------------- left click outside the drawer: closes it; invalid target = no-op, valid one uses the item
        await ClickSlotReal("GROCERIES");
        await Frames(2);
        var before = game.State;
        feet = hero.Feet;
        var invalidPoint = await ScenePoint(invalid);
        if (invalidPoint is { } ipt) await RawMouseReal(ipt, MouseButton.Left);
        await Frames(6);
        Check("left_click_outside_drawer_closes_invalid_noop", invalidPoint is not null && game.State.Mode == GameMode.World && game.State.SelectedItem == "GROCERIES" &&
              !hero.IsWalking && hero.Feet == feet && !presenter.IsShowingBark && game.State.ActiveLineId is null && game.State.Done.SequenceEqual(before.Done),
              $"mode={game.State.Mode} selected={game.State.SelectedItem} walking={hero.IsWalking} bark={presenter.IsShowingBark}");
        await ClickSlotReal("GROCERIES"); // drawer open again with the item picked
        await Frames(2);
        bool reopened = game.State.Mode == GameMode.Inventory;
        var validPoint = await ScenePoint(valid);
        if (validPoint is { } vpt) await RawMouseReal(vpt, MouseButton.Left);
        await Frames(2);
        bool closedOnClick = game.State.Mode != GameMode.Inventory;
        await WaitUntil(() => game.State.IsDone("G04"), 20);
        Check("left_click_outside_drawer_valid_target_uses_item", reopened && validPoint is not null && closedOnClick && game.State.IsDone("G04") &&
              !game.State.Has("GROCERIES"), $"reopened={reopened} closed={closedOnClick} G04={game.State.IsDone("G04")}");
        await SkipLines(15);
        await Settle();
    }

    private async Task RunPrologueAcceptance()
    {
        var game = GameRuntime.Instance;
        var presenter = DialoguePresenter.Instance!;

        // ---------------------------------------------------------------- right click: look, no walk
        game.NewGame();
        await Settle();
        var hero = CurrentRoom.Hero;
        var feet = hero.Feet;
        int done = game.State.Done.Length;
        await RawMouse(CenterOf("S01.ambient 2"), MouseButton.Right);
        await Frames(4);
        Check("right_click_hotspot_looks", presenter.IsShowingBark && !hero.IsWalking && hero.Feet == feet && game.State.Done.Length == done &&
              game.State.Mode == GameMode.World, $"bark={presenter.IsShowingBark} walking={hero.IsWalking} mode={game.State.Mode}");

        // ---------------------------------------------------------------- right click on empty floor: inventory
        presenter.HideBark();
        await RawMouse(new Vector2(1500, 900), MouseButton.Right);
        await Frames(3);
        Check("right_click_floor_opens_inventory", game.State.Mode == GameMode.Inventory && !hero.IsWalking, $"mode={game.State.Mode}");
        await Key(Godot.Key.I);
        Check("inventory_key_closes", game.State.Mode == GameMode.World, $"mode={game.State.Mode}");

        // ---------------------------------------------------------------- owner control changes (Space hold, hover label, cursor, double click)
        // Replaces the old check "space_toggles_labels" (owner override 2026-10-05, ISSUES INT-08).
        await RunControlChecks();

        // ---------------------------------------------------------------- owner control change 6 (2026-10-06): drawer close on right click, valid-only hover / markers / Tab
        await RunSelectionControlChecks();

        // ---------------------------------------------------------------- invalid item click: complete no-op
        await FromReplay(1); // G01 done, TOOLS in the bag, still in S01
        hero = CurrentRoom.Hero;
        await SelectFromInventory("TOOLS");
        Check("select_item", game.State.SelectedItem == "TOOLS" && game.State.Mode == GameMode.World, $"selected={game.State.SelectedItem} mode={game.State.Mode}");
        var hoverInvalid = game.Session.Hover(new Hit.Hotspot("S01.fuse"));
        Check("hover_invalid_item_has_no_action_text", hoverInvalid.ActionLabel.Key.Length == 0 || TextService.Get(hoverInvalid.ActionLabel).Length == 0,
              $"label='{TextService.Get(hoverInvalid.ActionLabel)}'");
        feet = hero.Feet;
        var stateBefore = game.State;
        await RawMouse(CenterOf("S01.fuse"), MouseButton.Left);
        await Frames(6);
        Check("invalid_item_click_is_noop", !hero.IsWalking && hero.Feet == feet && game.State.SelectedItem == "TOOLS" && game.State.ActiveLineId is null &&
              !presenter.IsShowingBark && !presenter.IsShowingLine && game.State.Done.SequenceEqual(stateBefore.Done) && game.State.Inventory.SequenceEqual(stateBefore.Inventory),
              $"walking={hero.IsWalking} selected={game.State.SelectedItem} bark={presenter.IsShowingBark} line={game.State.ActiveLineId}");

        // ---------------------------------------------------------------- right click with a selected item cancels it first
        await RawMouse(new Vector2(1500, 900), MouseButton.Right);
        await Frames(3);
        Check("right_click_cancels_selection_first", game.State.SelectedItem is null && game.State.Mode == GameMode.World,
              $"selected={game.State.SelectedItem} mode={game.State.Mode}");

        // ---------------------------------------------------------------- a taken prop cannot be taken twice
        var toolsRect = CurrentRoom.TryGetTarget("S01.tools", out _);
        await RawMouse(new Vector2(225, 200), MouseButton.Left); // where the bag was
        await Settle();
        Check("taken_prop_gone_no_duplicate", !toolsRect && Count(game.State, "TOOLS") == 1, $"tools_visible={toolsRect} count={Count(game.State, "TOOLS")}");

        // ---------------------------------------------------------------- hover sentence only for an executable rule
        await FromReplay(2); // in S03 with ORDER
        await TravelTo("S04");
        await SelectFromInventory("ORDER");
        var hoverValid = game.Session.Hover(new Hit.Hotspot("S04.DANA"));
        Check("hover_valid_item_shows_action_text", TextService.Get(hoverValid.ActionLabel).Length > 0, $"label='{TextService.Get(hoverValid.ActionLabel)}'");

        // ---------------------------------------------------------------- re-check on arrival
        hero = CurrentRoom.Hero;
        await RawMouse(CenterOf("S04.DANA"), MouseButton.Left);
        await Frames(3);
        bool walkingAway = hero.IsWalking && InteractionController.Instance!.HasPending;
        await RawMouse(new Vector2(1500, 900), MouseButton.Right); // player drops the item while the hero walks
        await WaitUntil(() => !hero.IsWalking, 15);
        await Frames(6);
        Check("recheck_on_arrival_blocks_stale_action", walkingAway && !game.State.IsDone("G03") && Count(game.State, "ORDER") == 1 && Count(game.State, "GROCERIES") == 0,
              $"walked={walkingAway} G03={game.State.IsDone("G03")} mode={game.State.Mode} inv=[{string.Join(",", game.State.Inventory)}]");
        await SkipLines(5);
        if (game.State.Mode == GameMode.Dialogue && game.State.ActiveLineId is null) game.Update(LastBell.Core.Rules.Dialogue.CloseMenu);
        await Settle();

        // positive control: the same click with the item commits once
        await SelectFromInventory("ORDER");
        await RawMouse(CenterOf("S04.DANA"), MouseButton.Left);
        await WaitUntil(() => game.State.IsDone("G03"), 20);
        Check("item_on_npc_commits", game.State.IsDone("G03") && Count(game.State, "GROCERIES") == 1 && Count(game.State, "ORDER") == 0,
              $"inv=[{string.Join(",", game.State.Inventory)}]");

        // ---------------------------------------------------------------- save while the action's line plays, load: no duplicate
        await Frames(2);
        bool lineActive = game.State.ActiveLineId is not null;
        game.Save("m1_accept_line");
        await Settle();
        await PerformAct("G04"); // walk on: groceries consumed on the tray
        await Settle();
        bool loaded = game.Load("m1_accept_line");
        await Settle();
        Check("save_during_line_load_no_duplicate", lineActive && loaded && game.State.IsDone("G03") && !game.State.IsDone("G04") &&
              Count(game.State, "GROCERIES") == 1 && Count(game.State, "ORDER") == 0 && game.State.Room == "S04",
              $"line={lineActive} loaded={loaded} room={game.State.Room} inv=[{string.Join(",", game.State.Inventory)}]");

        // repeated click on Dana after the hand-over: nothing new
        await RawMouse(CenterOf("S04.DANA"), MouseButton.Left);
        await WaitUntil(() => !CurrentRoom.Hero.IsWalking && !InteractionController.Instance!.HasPending, 15);
        await SkipLines(10);
        if (game.State.Mode == GameMode.Dialogue && game.State.ActiveLineId is null) game.Update(LastBell.Core.Rules.Dialogue.CloseMenu);
        await Settle();
        Check("repeat_click_no_duplicate", Count(game.State, "GROCERIES") == 1 && game.State.Done.Count(d => d == "G03") == 1,
              $"inv=[{string.Join(",", game.State.Inventory)}]");

        // ---------------------------------------------------------------- save/load in the middle of the prologue, then finish it
        await PerformAct("G04");
        await PerformAct("G05");
        await Settle();
        game.Save("m1_accept_mid");
        var savedState = game.State;
        await PerformAct("G06");
        await Settle();
        game.Load("m1_accept_mid");
        await Settle();
        Check("load_mid_prologue_restores", game.State.Done.SequenceEqual(savedState.Done) && game.State.Inventory.SequenceEqual(savedState.Inventory) &&
              game.State.Room == savedState.Room && !game.State.IsDone("G06"),
              $"done={game.State.Done.Length} room={game.State.Room} inv=[{string.Join(",", game.State.Inventory)}]");
        foreach (var id in new[] { "G06", "G07", "G08", "G09", "G10" }) await PerformAct(id);
        await Settle();

        // ---------------------------------------------------------------- save with the puzzle modal open (GAME-02)
        await RawMouse(CenterOf("S10.panel"), MouseButton.Left);
        bool opened = await WaitUntil(() => game.State.Mode == GameMode.Puzzle, 20);
        game.Save("m1_accept_puzzle");
        game.ClosePuzzle();
        await Settle();
        game.Load("m1_accept_puzzle");
        await Settle();
        // The save carries open_puzzle, so the load reopens the same modal (GAME-02; before: resumed in the world).
        bool modalShown = LastBell.Game.UI.UiRoot.Instance is not { } uiRoot || uiRoot.PuzzleView.Visible;
        Check("load_saved_in_puzzle_reopens_the_modal", opened && game.State.Mode == GameMode.Puzzle && game.OpenPuzzleActionId == "G11" && modalShown &&
              game.State.Room == "S10" && !game.State.IsDone("G11"),
              $"opened={opened} mode={game.State.Mode} open_puzzle={game.OpenPuzzleActionId ?? "-"} modal={modalShown}");
        await KeyReal(Godot.Key.Escape); // close it again: the next check opens it by a click
        if (game.State.Mode == GameMode.Puzzle) game.ClosePuzzle();
        await Settle();

        // ---------------------------------------------------------------- wrong answer, then the right one: commits once
        await RawMouse(CenterOf("S10.panel"), MouseButton.Left);
        await WaitUntil(() => game.State.Mode == GameMode.Puzzle, 20);
        var wrong = game.SubmitPuzzle(System.Text.Json.Nodes.JsonNode.Parse("[\"kruh\",\"štvorec\",\"trojuholník\"]"));
        Check("p01_wrong_answer_no_commit", wrong is { Solved: false } && !game.State.IsDone("G11") && game.State.Mode == GameMode.Puzzle,
              $"solved={wrong?.Solved} mode={game.State.Mode}");
        var right = game.SubmitPuzzle(game.Content.GetPuzzle("P01").Solution?.DeepClone());
        await WaitUntil(() => game.State.Room == "S11" && game.State.Mode == GameMode.World && WorldStage.Instance!.IsSettled && WorldStage.Instance.IsFadedIn, 90);
        await Settle();
        Check("p01_solved_arrives_s11_1995", right is { Solved: true } && game.State.IsDone("G11") && game.State.Done.Count(d => d == "G11") == 1 &&
              game.State.Room == "S11" && game.State.Era == 1995 && CurrentRoom.RoomId == "S11",
              $"room={game.State.Room} era={game.State.Era} mode={game.State.Mode} inv=[{string.Join(",", game.State.Inventory)}]");
        var expected = new[] { "CHRONO", "PHONE", "SHEDKEY", "TOOLS" };
        Check("prologue_final_inventory", game.State.Inventory.OrderBy(x => x, StringComparer.Ordinal).SequenceEqual(expected),
              $"inv=[{string.Join(",", game.State.Inventory)}]");

        foreach (var slot in new[] { "m1_accept_line", "m1_accept_mid", "m1_accept_puzzle" }) GameRuntime.DeleteSlot(slot);
        Log($"acceptance: {acceptanceFailures} failure(s)");
    }
}
