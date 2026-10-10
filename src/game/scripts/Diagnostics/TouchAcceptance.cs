using System;
using System.Linq;
using System.Threading.Tasks;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Game.PlayerInput;
using LastBell.Game.Runtime;
using LastBell.Game.UI;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Hud;
using LastBell.Game.UI.Settings;
using LastBell.Game.World;

namespace LastBell.Game.Diagnostics;

/// <summary>
/// Acceptance checks of the touch controls of the phone and tablet ports (docs/PORTS.md "Touch controls"; run with
/// <c>-- --touch --acceptance touch</c>, headless or in a hidden window): real <see cref="InputEventScreenTouch"/> /
/// <see cref="InputEventScreenDrag"/> events through Godot's input pipeline in room S01 of a new game, and the phone
/// events of <see cref="LastBell.Game.UI.Common.MobileLifecycle"/>. The same gestures run on a headless Android
/// emulator with <c>python tools/android_qa.py smoke</c>.
/// </summary>
public partial class DebugHarness
{
    private static string ShownLabel => UiRoot.Instance?.HoverLabel.ShownName ?? "";

    private Vector2 ToWindow(Vector2 canvasPoint) => GetTree().Root.GetFinalTransform() * canvasPoint;

    private async Task Finger(Vector2 canvasPoint, bool down)
    {
        Godot.Input.ParseInputEvent(new InputEventScreenTouch { Index = 0, Position = ToWindow(canvasPoint), Pressed = down });
        await Frames(3);
    }

    private async Task SlideFinger(Vector2 from, Vector2 to, int steps = 8)
    {
        for (int i = 1; i <= steps; i++)
        {
            Godot.Input.ParseInputEvent(new InputEventScreenDrag { Index = 0, Position = ToWindow(from.Lerp(to, i / (float)steps)), Relative = ToWindow(to - from) / steps });
            await Frames(2);
        }
    }

    private async Task RunTouchChecks()
    {
        var game = GameRuntime.Instance;
        var controller = InteractionController.Instance!;
        Check("TC01_touch_mode_with_the_phone_defaults", TouchMode.Enabled && UiSettings.HudScalePercent == 200 && UiSettings.SubtitleSize == 42,
            $"touch={TouchMode.Enabled} hud={UiSettings.HudScalePercent}% subtitles={UiSettings.SubtitleSize}px mm/px={TouchMode.MmPerCanvasPx():0.000}");
        if (!TouchMode.Enabled)
        {
            Log("ERROR --acceptance touch needs --touch");
            acceptanceFailures++;
            return;
        }

        game.NewGame();
        await Settle();
        var room = CurrentRoom;
        const string bag = "S01.tools";
        bool hasBag = room.TryGetTarget(bag, out var bagTarget);
        var bagPoint = hasBag ? await FindClickPoint(bag) ?? bagTarget.Rect.GetCenter() : Vector2.Zero;
        string bagName = hasBag ? TextService.Get(bagTarget.Name) : "?";
        var floor = room.Walk.Clamp(new Vector2(1200, 880));

        // ---------------------------------------------------------------- the label at the finger
        await Finger(bagPoint, true);
        string atFinger = ShownLabel;
        var labelRect = UiRoot.Instance!.HoverLabel.ShownRect;
        bool above = DisplayServer.GetName() == "headless" || (labelRect.Size.Y > 0 && labelRect.End.Y <= bagPoint.Y - 40 && Mathf.Abs(labelRect.GetCenter().X - bagPoint.X) < 40);
        Check("TC02_finger_down_shows_the_name_above_the_finger_and_does_nothing_yet",
            hasBag && atFinger == bagName && above && !controller.HasPending && !room.Hero.IsWalking && !game.State.Has("TOOLS"),
            $"label='{atFinger}' rect={labelRect} finger={bagPoint}");

        // ---------------------------------------------------------------- a slide moves the label and lifting does nothing
        await SlideFinger(bagPoint, floor);
        string onFloor = ShownLabel;
        await Finger(floor, false);
        await Seconds(0.4);
        Check("TC03_slide_then_lift_does_nothing", onFloor.Length == 0 && ShownLabel.Length == 0 && !controller.HasPending && !room.Hero.IsWalking && !game.State.Has("TOOLS"),
            $"label over the floor='{onFloor}' walking={room.Hero.IsWalking}");

        // ---------------------------------------------------------------- a tap acts at once, the label stays for a moment
        await RawTouch(bagPoint, "tap");
        string afterTap = ShownLabel;
        bool started = controller.HasPending || room.Hero.IsWalking || game.State.Has("TOOLS");
        bool taken = await WaitUntil(() => game.State.Has("TOOLS") && game.State.IsDone("G01"), 20);
        Check("TC04_one_tap_walks_and_takes_with_the_label_as_confirmation", afterTap == bagName && started && taken,
            $"label after the tap='{afterTap}' started={started} inventory=[{string.Join(",", game.State.Inventory)}]");
        await SkipLines(20);
        await Seconds(InputRouter.TouchLabelSeconds + 0.3);
        Check("TC05_label_goes_away_after_the_tap", ShownLabel.Length == 0, $"label='{ShownLabel}'");

        // ---------------------------------------------------------------- long press: look (no action), on the floor: inventory
        const string pot = "S01.ambient 1";
        var potPoint = room.TryGetTarget(pot, out var potTarget) ? await FindClickPoint(pot) ?? potTarget.Rect.GetCenter() : new Vector2(520, 650);
        var before = game.State;
        await RawTouch(potPoint, "longpress");
        await Frames(4);
        Check("TC06_long_press_looks_without_acting", game.State.Mode == GameMode.World && game.State.Done.SequenceEqual(before.Done) &&
            game.State.Inventory.SequenceEqual(before.Inventory) && !controller.HasPending && game.State.JournalSeen.Length >= before.JournalSeen.Length && ShownLabel.Length == 0,
            $"mode={game.State.Mode} journal {before.JournalSeen.Length}->{game.State.JournalSeen.Length}");
        await Seconds(0.5);
        await RawTouch(floor, "longpress");
        bool drawer = await WaitUntil(() => game.State.Mode == GameMode.Inventory, 3);
        Check("TC07_long_press_on_the_floor_opens_the_inventory", drawer, $"mode={game.State.Mode}");

        // ---------------------------------------------------------------- inventory: hold = look, tap = take in hand and close
        await Seconds(0.4);
        var slot = SlotButton("TOOLS");
        var slotPoint = slot?.GetGlobalRect().GetCenter() ?? Vector2.Zero;
        await RawTouch(slotPoint, "longpress");
        await Frames(4);
        Check("TC08_holding_an_item_looks_at_it_and_selects_nothing", slot is not null && game.State.Mode == GameMode.Inventory && game.State.SelectedItem is null,
            $"mode={game.State.Mode} selected={game.State.SelectedItem ?? "-"}");
        await Seconds(0.4);
        slot = SlotButton("TOOLS");
        slotPoint = slot?.GetGlobalRect().GetCenter() ?? Vector2.Zero;
        await RawTouch(slotPoint, "tap");
        bool inHand = await WaitUntil(() => game.State.SelectedItem == "TOOLS" && game.State.Mode == GameMode.World, 3);
        Check("TC09_tapping_an_item_takes_it_in_hand_and_closes_the_inventory", inHand, $"mode={game.State.Mode} selected={game.State.SelectedItem ?? "-"}");
        await Seconds(0.4);
        // The PC rule stays: an item on a place where it has no use is a complete no-op that keeps the selection.
        await RawTouch(potPoint, "tap");
        await Seconds(0.4);
        Check("TC10_item_on_a_place_without_a_use_is_a_no_op", game.State.SelectedItem == "TOOLS" && !controller.HasPending && !room.Hero.IsWalking && ShownLabel.Length == 0,
            $"selected={game.State.SelectedItem ?? "-"} label='{ShownLabel}'");
        await RawTouch(floor, "longpress");
        bool cancelled = await WaitUntil(() => game.State.SelectedItem is null, 3);
        Check("TC11_long_press_cancels_the_item_in_hand", cancelled && game.State.Mode == GameMode.World, $"mode={game.State.Mode} selected={game.State.SelectedItem ?? "-"}");

        // ---------------------------------------------------------------- the Eye button latches
        await Seconds(0.4);
        var eye = Descendants<Button>(UiRoot.Instance!.Hud).FirstOrDefault(b => b.IsVisibleInTree() && b.TooltipText == TextService.Ui("ui.hud.show_hotspots"));
        var hudButtons = Descendants<Button>(UiRoot.Instance.Hud).Where(b => b.IsVisibleInTree()).ToList();
        float mm = TouchMode.MmPerCanvasPx();
        float smallest = hudButtons.Count == 0 ? 0 : hudButtons.Min(b => Mathf.Min(b.GetGlobalRect().Size.X, b.GetGlobalRect().Size.Y)) * mm;
        Check("TC12_hud_buttons_are_finger_sized", hudButtons.Count >= 6 && smallest >= 8.5f, $"{hudButtons.Count} buttons, the smallest {smallest:0.0} mm");
        if (eye is not null) await RawTouch(eye.GetGlobalRect().GetCenter(), "tap");
        bool on = game.State.HotspotLabels;
        int marked = CurrentRoom.Labels.MarkedIds.Count;
        bool off = await WaitUntil(() => !game.State.HotspotLabels, HudView.EyeLatchSeconds + 3);
        Check("TC13_eye_button_shows_the_markers_for_a_few_seconds", eye is not null && on && marked > 0 && off, $"on={on} markers={marked} off again={off}");

        // ---------------------------------------------------------------- the phone: Back, background, return
        var life = LastBell.Game.UI.Common.MobileLifecycle.Instance;
        life?.Back();
        await Frames(3);
        bool paused = game.State.Mode == GameMode.Pause;
        life?.Back(); // the same press arriving twice: ignored
        await Frames(3);
        bool stillPaused = game.State.Mode == GameMode.Pause;
        await Seconds(LastBell.Game.UI.Common.MobileLifecycle.BackRepeatSeconds + 0.1);
        life?.Back();
        await Frames(3);
        Check("TC14_back_pauses_and_resumes_and_a_doubled_request_counts_once", life is not null && paused && stillPaused && game.State.Mode == GameMode.World,
            $"paused={paused} after the doubled request={stillPaused} then mode={game.State.Mode}");
        life?.Background();
        await Frames(3);
        bool quiet = game.State.Mode == GameMode.World; // nothing opens while the app leaves
        life?.Foreground();
        await Frames(3);
        Check("TC15_back_from_the_background_into_the_pause_menu", quiet && game.State.Mode == GameMode.Pause, $"while away={quiet} back: mode={game.State.Mode}");
        await Seconds(LastBell.Game.UI.Common.MobileLifecycle.BackRepeatSeconds + 0.1);
        life?.Back(); // out of the pause menu
        await WaitUntil(() => game.State.Mode == GameMode.World, 3);
        await Seconds(0.4);

        // ---------------------------------------------------------------- double tap: through the exit without the walk
        const string exit = "S01.to_S02";
        var exitPoint = CurrentRoom.TryGetTarget(exit, out var exitTarget) ? await FindClickPoint(exit) ?? exitTarget.Rect.GetCenter() : new Vector2(1150, 600);
        bool skipped = false;
        void OnSkip() => skipped = true;
        controller.WalkSkipped += OnSkip;
        await RawTouch(exitPoint, "tap");
        await RawTouch(exitPoint, "tap");
        bool arrived = await WaitUntil(() => game.State.Room == "S02", 10);
        controller.WalkSkipped -= OnSkip;
        Check("TC16_double_tap_skips_the_walk", skipped && arrived, $"walk skipped={skipped} room={game.State.Room}");
        await RunTouchExitChecks();
        await RunTouchScrollChecks();
        Log($"acceptance touch: {acceptanceFailures} failure(s)");
    }

    /// <summary>
    /// Exits under the phone's HUD buttons (owner report 2026-10-10: the exit badges collided with the buttons at the
    /// bottom). S03 has the worst case: the rect of its exit to S02 lies completely under the Hint and Journal buttons.
    /// The badges sit above the buttons, a finger on a badge names its exit while the Eye shows the badges, and the
    /// raised spot of a covered exit answers when the badges are off too.
    /// </summary>
    private async Task RunTouchExitChecks()
    {
        var game = GameRuntime.Instance;
        const string room = "S03", covered = "S03.to_S02";
        JumpTo(game, room);
        await WaitUntil(() => WorldStage.Instance?.Current?.RoomId == room && WorldStage.Instance.IsSettled, 10);
        await Seconds(0.5);
        var labels = CurrentRoom.Labels;
        var buttons = Descendants<Button>(UiRoot.Instance!.Hud).Where(b => b.IsVisibleInTree()).Select(b => b.GetGlobalRect()).ToList();
        float radius = HotspotLabelLayer.MarkerSize * HotspotLabelLayer.MarkerScale / 2;
        var under = CurrentRoom.Targets.Where(t => buttons.Any(b => b.Grow(radius).HasPoint(labels.MarkerPoint(t)))).Select(t => t.Id).ToList();
        Check("TC21_no_badge_sits_on_a_hud_button", buttons.Count >= 6 && under.Count == 0,
            $"{buttons.Count} buttons, badges on a button: {(under.Count == 0 ? "none" : string.Join(", ", under))}");

        bool known = CurrentRoom.TryGetTarget(covered, out var exit);
        var spot = known ? labels.MarkerPoint(exit) : Vector2.Zero;
        bool rectCovered = known && buttons.Any(b => b.Intersects(exit.Rect)) && exit.Rect.Position.Y >= Room.CanvasSize.Y - PresentationSettings.BottomReservePx;
        string exitName = known ? TextService.Get(exit.Name) : "";
        await Finger(spot, true);
        string off = ShownLabel;
        await SlideFinger(spot, spot + new Vector2(0, -260));
        await Finger(spot + new Vector2(0, -260), false);
        await Seconds(0.3);
        WorldInput.Dispatch(LogicalCommand.ShowMarkers);
        await Frames(4);
        await Finger(spot, true);
        string on = ShownLabel;
        await SlideFinger(spot, spot + new Vector2(0, -260));
        await Finger(spot + new Vector2(0, -260), false);
        WorldInput.Dispatch(LogicalCommand.HideMarkers);
        await Frames(4);
        Check("TC22_an_exit_under_the_buttons_answers_at_its_raised_badge", known && rectCovered && exitName.Length > 0 && off == exitName && on == exitName &&
            CurrentRoom.HitTest(spot) is Hit.Exit { Id: covered } && game.State.Room == room,
            $"exit known={known} rect under the buttons={rectCovered} badge at {spot.X:0},{spot.Y:0} name='{exitName}' finger with badges off='{off}' on='{on}' room={game.State.Room}");
    }

    /// <summary>
    /// Lists on a phone (UI/Common/TouchScroller; owner report 2026-10-09: nothing scrolled): the settings screen at the
    /// phone's 200 % has more rows than room. A tap on a tab presses it, a slide that starts on a button of the list
    /// scrolls the list and presses nothing, a slider follows a slide along it and lets a slide across it scroll.
    /// The settings are not written in this run (UiSettings.Save, desktop touch emulation).
    /// </summary>
    private async Task RunTouchScrollChecks()
    {
        await SkipLines(20);
        await Seconds(0.5);
        var ui = UiRoot.Instance!;
        ui.OpenSettings();
        await Frames(8);
        var screen = ui.TopModal;
        Button? TabOf(string key) => screen is null ? null
            : Descendants<Button>(screen).FirstOrDefault(b => b.IsVisibleInTree() && b.ToggleMode && b.Text == TextService.Ui(key));
        // The rows (the widest scroll area; on a phone the tabs stand in a narrow scroll column of their own beside it).
        ScrollContainer? ListOf() => screen is null ? null
            : Descendants<ScrollContainer>(screen).Where(c => c.IsVisibleInTree()).OrderByDescending(c => c.Size.X).FirstOrDefault();
        static double Room(ScrollContainer list) => list.GetVScrollBar().MaxValue - list.GetVScrollBar().Page;

        // ---------------------------------------------------------------- a tap on a button of a row of tabs
        var accessTab = TabOf("ui.settings.tab_accessibility");
        if (accessTab is not null) await RawTouch(accessTab.GetGlobalRect().GetCenter(), "tap");
        await Frames(8);
        Check("TC17_a_tap_on_a_tab_still_presses_it", accessTab is { ButtonPressed: true }, $"tab found={accessTab is not null} pressed={accessTab?.ButtonPressed}");

        // ---------------------------------------------------------------- a slide that starts on a button scrolls the list
        var list = ListOf();
        var view = list?.GetGlobalRect() ?? new Rect2();
        float scale = list?.GetGlobalTransformWithCanvas().Scale.Y ?? 1f;
        var buttons = list is null ? new System.Collections.Generic.List<BaseButton>()
            : Descendants<BaseButton>(list).Where(b => b.IsVisibleInTree() && view.HasPoint(b.GetGlobalRect().GetCenter())).ToList();
        var startButton = buttons.OrderByDescending(b => b.GetGlobalRect().GetCenter().Y).FirstOrDefault();
        int presses = 0;
        void OnPress() => presses++;
        foreach (var b in buttons) b.Pressed += OnPress;
        var from = startButton?.GetGlobalRect().GetCenter() ?? view.GetCenter();
        var to = new Vector2(from.X + 12, Mathf.Max(20, from.Y - 260)); // the finger may leave the list: the scroll goes on
        double room = list is null ? 0 : Room(list);
        int before = list?.ScrollVertical ?? 0;
        await Finger(from, true);
        await SlideFinger(from, to);
        int dragged = (list?.ScrollVertical ?? 0) - before;
        bool scrolledFlag = TouchScroller.ScrolledThisTouch;
        await Finger(to, false);
        await Seconds(1.5); // the list coasts and stops
        foreach (var b in buttons) if (IsInstanceValid(b)) b.Pressed -= OnPress;
        double slide = (from.Y - to.Y) / scale;
        double least = Math.Min(room, (from.Y - to.Y - 2 * TouchGestures.SlopPx) / scale) * 0.8;
        Check("TC18_a_slide_that_starts_on_a_button_scrolls_the_list_and_presses_nothing",
            list is not null && startButton is not null && room > 40 && dragged >= least && dragged <= slide + 2 && presses == 0 && scrolledFlag,
            $"list={list is not null} start on a button={startButton is not null} room={room:0} slide={slide:0} scrolled={dragged} (at least {least:0}) presses={presses} flag={scrolledFlag}");

        // ---------------------------------------------------------------- sliders: along = the value, across = the list
        var soundTab = TabOf("ui.settings.tab_audio");
        if (soundTab is not null) await RawTouch(soundTab.GetGlobalRect().GetCenter(), "tap");
        await Frames(8);
        list = ListOf();
        if (list is not null) list.ScrollVertical = 0;
        await Frames(3);
        view = list?.GetGlobalRect() ?? new Rect2();
        var knob = list is null ? null : Descendants<HSlider>(list).FirstOrDefault(k => k.IsVisibleInTree() && view.HasPoint(k.GetGlobalRect().GetCenter()));
        double volume = knob?.Value ?? 0;
        var knobAt = knob?.GetGlobalRect().GetCenter() ?? Vector2.Zero;
        float side = knob is null || knob.Value > (knob.MinValue + knob.MaxValue) / 2 ? -1 : 1; // towards the free half
        var along = knobAt + new Vector2(side * 170, 8);
        await Finger(knobAt, true);
        double onTouch = knob?.Value ?? 0; // a touch alone changes nothing
        await SlideFinger(knobAt, along);
        await Finger(along, false);
        await Frames(4);
        double slid = knob?.Value ?? 0;
        int listAfterAlong = list?.ScrollVertical ?? -1;
        if (knob is not null) knob.Value = volume;
        await Frames(3);
        var across = new Vector2(knobAt.X + 10, Mathf.Min(view.End.Y - 8, knobAt.Y + 40));
        var acrossTo = new Vector2(across.X, Mathf.Max(20, across.Y - 240));
        await Finger(across, true);
        await SlideFinger(across, acrossTo);
        int acrossScrolled = list?.ScrollVertical ?? 0;
        await Finger(acrossTo, false);
        await Seconds(1.5);
        double afterAcross = knob?.Value ?? 0;
        Check("TC19_a_slide_along_a_slider_moves_its_value_and_a_slide_across_it_scrolls_the_list",
            knob is not null && onTouch == volume && Math.Abs(slid - volume) >= 5 && Math.Sign(slid - volume) == Math.Sign(side) && listAfterAlong == 0 &&
            acrossScrolled > 20 && afterAcross == volume,
            $"slider={knob is not null} value {volume:0} touch {onTouch:0} along {slid:0} (list at {listAfterAlong}); across: list at {acrossScrolled}, value {afterAcross:0}");

        // ---------------------------------------------------------------- a tap on a slider sets the value at that point
        if (list is not null) list.ScrollVertical = 0;
        await Frames(3);
        var bar = knob?.GetGlobalRect() ?? new Rect2();
        await RawTouch(new Vector2(bar.Position.X + bar.Size.X * 0.3f, bar.GetCenter().Y), "tap");
        await Frames(4);
        double tapped = knob?.Value ?? -1;
        double third = knob is null ? 0 : knob.MinValue + 0.3 * (knob.MaxValue - knob.MinValue);
        Check("TC20_a_tap_on_a_slider_sets_the_value_at_that_point", knob is not null && Math.Abs(tapped - third) <= 12, $"value {tapped:0}, the point is at {third:0}");
        if (knob is not null) knob.Value = volume;
        await Frames(3);
        ui.TopModal?.Back();
        await Frames(6);
    }
}
