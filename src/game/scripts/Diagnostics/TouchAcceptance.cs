using System;
using System.Linq;
using System.Threading.Tasks;
using Godot;
using LastBell.Core.State;
using LastBell.Game.PlayerInput;
using LastBell.Game.Runtime;
using LastBell.Game.UI;
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
        Log($"acceptance touch: {acceptanceFailures} failure(s)");
    }
}
