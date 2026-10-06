using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Game.Runtime;
using LastBell.Game.UI;
using LastBell.Game.UI.Menus;
using LastBell.Game.World;

namespace LastBell.Game.Diagnostics;

/// <summary>
/// AT19 keyboard-only driver (flag <c>--keyboard</c> with <c>--play-all</c>, <c>--play</c> or <c>--act</c>): the real-input
/// driver (<see cref="DebugHarness"/> RealInputDriver.cs) with every mouse event replaced by the keys a player without a
/// mouse uses. World targets and exits: Tab / Shift+Tab (the shorter way round) until the target has the keyboard focus,
/// then Enter (Backspace for a look). GUI controls (bag slots, topics, puzzle controls, era buttons, map cards, journal
/// tabs, dialogs): Tab until the control owns the GUI focus, then Enter. Epilogue shots: Enter. The mouse is never moved.
/// Besides the walkthrough it runs a shortcut tour once per era (Space hold, I, J, H, M with a fast travel by keys,
/// Esc into the pause menu and out). Every step logs <c>HARNESS keys &lt;step&gt; n=&lt;presses&gt;</c>; a target or control
/// that keys cannot reach is a <c>BLOCKER</c>, a step that needs more than <see cref="AwkwardPresses"/> presses is
/// reported as awkward (<c>HARNESS keyboard awkward ...</c>, summary at the end).
/// </summary>
public partial class DebugHarness
{
    private bool keyboardOnly;

    /// <summary>More key presses than this for one target / control counts as awkward in the AT19 report.</summary>
    private const int AwkwardPresses = 8;

    private readonly List<(string Step, int Presses, int Of)> keySteps = new();
    private readonly List<string> keyboardNotes = new();
    private readonly HashSet<int> erasToured = new();

    private async Task KeyCombo(Godot.Key key, bool shift = false)
    {
        foreach (bool pressed in new[] { true, false })
        {
            Godot.Input.ParseInputEvent(new InputEventKey { Keycode = key, PhysicalKeycode = key, Pressed = pressed, ShiftPressed = shift });
            await Frames(1);
        }
        await Frames(1);
    }

    private void KeyStep(string step, int presses, int of)
    {
        keySteps.Add((step, presses, of));
        Log($"keys {step} n={presses}{(of > 0 ? $" of={of}" : "")}");
        if (presses > AwkwardPresses) Log($"keyboard awkward {step}: {presses} presses");
    }

    private void KeyboardNote(string text)
    {
        keyboardNotes.Add(text);
        Log("keyboard note " + text);
    }

    /// <summary>The room's Tab order as <see cref="InteractionController.MoveFocus"/> builds it (only valid targets while an item is selected).</summary>
    private List<string> TabOrder(Room room)
    {
        var game = GameRuntime.Instance;
        bool itemSelected = game.State.SelectedItem is not null;
        return room.View.AccessibleOrder.Where(id => room.TryGetTarget(id, out var t) &&
            (!itemSelected || InteractionController.IsItemUse(game.Session.Resolve(t.ToHit(), PointerButton.Left)))).ToList();
    }

    /// <summary>Tab / Shift+Tab (shorter way) until the world target has the keyboard focus, then Enter (Backspace for a look).</summary>
    private async Task<bool> KeyTarget(string targetId, MouseButton button)
    {
        var game = GameRuntime.Instance;
        var room = WorldStage.Instance!.Current!;
        if (GetViewport().GuiGetFocusOwner() is { } stray && game.State.Mode == GameMode.World)
        {
            KeyboardNote($"GUI control {PathOf(stray)} kept the keyboard focus in world mode before {targetId} ({room.RoomId}); Tab would move the GUI focus");
            stray.ReleaseFocus();
        }
        var order = TabOrder(room);
        int presses = 0;
        if (InteractionController.Instance?.FocusedId != targetId)
        {
            int at = order.IndexOf(targetId);
            if (at < 0)
            {
                Blocker($"keyboard: target {targetId} in {room.RoomId} is not in the Tab order ({string.Join(",", order)})");
                return false;
            }
            int cur = InteractionController.Instance?.FocusedId is { } f ? order.IndexOf(f) : -1;
            // From no focus Tab lands on index 0, Shift+Tab on the last one.
            int forward = cur < 0 ? at + 1 : (at - cur + order.Count) % order.Count;
            int backward = cur < 0 ? order.Count - at : (cur - at + order.Count) % order.Count;
            bool shift = backward < forward;
            int limit = order.Count + 2;
            while (InteractionController.Instance?.FocusedId != targetId && presses < limit)
            {
                await KeyCombo(Godot.Key.Tab, shift);
                presses++;
            }
            if (InteractionController.Instance?.FocusedId != targetId)
            {
                Blocker($"keyboard: Tab did not reach {targetId} in {room.RoomId} after {presses} presses (focus {InteractionController.Instance?.FocusedId ?? "-"})");
                return false;
            }
        }
        KeyStep($"{room.RoomId}:{targetId}{(button == MouseButton.Right ? ":look" : "")}", presses + 1, order.Count);
        await KeyCombo(button == MouseButton.Right ? Godot.Key.Backspace : Godot.Key.Enter);
        return true;
    }

    /// <summary>Tab until the GUI control has the focus, then Enter (Backspace = the control's right click).</summary>
    private async Task<bool> KeyControl(Control control, string what, MouseButton button)
    {
        for (Node? p = control.GetParent(); p is not null; p = p.GetParent())
            if (p is ScrollContainer scroll) scroll.EnsureControlVisible(control);
        await Frames(2);
        if (control.FocusMode != Control.FocusModeEnum.All)
        {
            Blocker($"keyboard: {what}: control {PathOf(control)} cannot take the keyboard focus (focus mode {control.FocusMode})");
            return false;
        }
        var viewport = GetViewport();
        int presses = 0;
        // The shorter way round: count the focus chain forward (Tab) and backward (Shift+Tab) from the current owner.
        bool shift = false;
        if (viewport.GuiGetFocusOwner() is { } owner && owner != control)
        {
            int Distance(bool back)
            {
                Control? c = owner;
                for (int i = 1; i <= 80 && c is not null; i++)
                {
                    c = back ? c.FindPrevValidFocus() : c.FindNextValidFocus();
                    if (c == control) return i;
                    if (c == owner) break;
                }
                return int.MaxValue;
            }
            shift = Distance(true) < Distance(false);
        }
        const int limit = 60;
        while (viewport.GuiGetFocusOwner() != control && presses < limit)
        {
            if (presses == 3 && viewport.GuiGetFocusOwner() is null)
            {
                Blocker($"keyboard: {what}: Tab gives no GUI control the focus (mode {GameRuntime.Instance.State.Mode})");
                return false;
            }
            await KeyCombo(Godot.Key.Tab, shift);
            presses++;
        }
        if (viewport.GuiGetFocusOwner() != control)
        {
            Blocker($"keyboard: {what}: Tab did not reach {PathOf(control)} after {presses} presses (focus {PathOf(viewport.GuiGetFocusOwner())})");
            return false;
        }
        KeyStep(what, presses + 1, 0);
        await KeyCombo(button == MouseButton.Right ? Godot.Key.Backspace : Godot.Key.Enter);
        return true;
    }

    // ------------------------------------------------------------------ shortcut tour (once per era)

    private async Task KeyboardTourIfNew()
    {
        var game = GameRuntime.Instance;
        if (!keyboardOnly || erasToured.Contains(game.State.Era)) return;
        // Wait for a moment in the era when the map offers a fast travel, so the tour can try one by keys.
        if (!game.State.Visited.Any(r => r != game.State.Room && game.Content.FindRoom(r)?.Era == game.State.Era &&
                                          Navigation.CanFastTravel(game.Content, game.State with { Mode = GameMode.Map }, r))) return;
        erasToured.Add(game.State.Era);
        await WaitLinesReal(30);
        await DropSelectionReal();
        string where = $"{game.State.Room}/{game.State.Era}";
        Log($"keyboard tour in {where}");

        // Space held: markers on while held, off on release.
        Godot.Input.ParseInputEvent(new InputEventKey { Keycode = Godot.Key.Space, PhysicalKeycode = Godot.Key.Space, Pressed = true });
        await Frames(4);
        bool shown = game.State.HotspotLabels;
        await ShotLater($"keyboard_space_{game.State.Era}", 0);
        await Frames(2);
        Godot.Input.ParseInputEvent(new InputEventKey { Keycode = Godot.Key.Space, PhysicalKeycode = Godot.Key.Space, Pressed = false });
        await Frames(4);
        if (!shown || game.State.HotspotLabels) QaFail($"keyboard tour {where}: Space hold markers shown={shown}, after release={game.State.HotspotLabels}");

        // I: the bag opens with a slot focused; I closes it.
        await KeyCombo(Godot.Key.I);
        bool bag = await WaitUntil(() => game.State.Mode == GameMode.Inventory, 5);
        await Frames(4);
        bool slotFocused = GetViewport().GuiGetFocusOwner() is Button b && b.HasMeta("item_id");
        await KeyCombo(Godot.Key.I);
        await WaitUntil(() => game.State.Mode == GameMode.World, 5);
        if (!bag || !slotFocused) QaFail($"keyboard tour {where}: I opened the bag={bag}, a slot had the focus={slotFocused}");

        // J: the journal; Tab reaches its controls; J closes it again.
        await KeyCombo(Godot.Key.J);
        bool journal = await WaitUntil(() => game.State.Mode == GameMode.Journal, 5);
        await Frames(4);
        await KeyCombo(Godot.Key.Tab);
        bool journalFocus = GetViewport().GuiGetFocusOwner() is not null;
        await ShotLater($"keyboard_journal_{game.State.Era}", 0);
        await KeyCombo(Godot.Key.J);
        bool journalClosed = await WaitUntil(() => game.State.Mode == GameMode.World, 5);
        if (!journal || !journalFocus || !journalClosed) QaFail($"keyboard tour {where}: J journal opened={journal} focus={journalFocus} closed by J={journalClosed}");

        // H: the hints; Enter on the focused control (quest or "show hint"); Esc closes.
        await KeyCombo(Godot.Key.H);
        bool hints = await WaitUntil(() => UiRoot.Instance!.TopModal is HintScreen, 5);
        await Frames(4);
        await KeyCombo(Godot.Key.Tab);
        bool hintFocus = GetViewport().GuiGetFocusOwner() is not null;
        await ShotLater($"keyboard_hints_{game.State.Era}", 0);
        await KeyCombo(Godot.Key.Escape);
        bool hintsClosed = await WaitUntil(() => !UiRoot.Instance!.HasModal, 5);
        if (!hints || !hintFocus || !hintsClosed) QaFail($"keyboard tour {where}: H hints opened={hints} focus={hintFocus} closed by Esc={hintsClosed}");

        // Esc: the pause menu with a focused button; Esc closes it.
        await KeyCombo(Godot.Key.Escape);
        bool pause = await WaitUntil(() => game.State.Mode == GameMode.Pause, 5);
        await Frames(4);
        await KeyCombo(Godot.Key.Tab);
        bool pauseFocus = GetViewport().GuiGetFocusOwner() is not null;
        await KeyCombo(Godot.Key.Escape);
        bool pauseClosed = await WaitUntil(() => game.State.Mode == GameMode.World, 5);
        if (!pause || !pauseFocus || !pauseClosed) QaFail($"keyboard tour {where}: Esc pause opened={pause} focus={pauseFocus} closed by Esc={pauseClosed}");

        // M: the map; a fast travel by keys (the room card), when one is possible; then back by keys.
        string start = game.State.Room;
        string? target = game.State.Visited.Where(r => r != start && game.Content.FindRoom(r)?.Era == game.State.Era)
            .FirstOrDefault(r => Navigation.CanFastTravel(game.Content, game.State with { Mode = GameMode.Map }, r));
        await KeyCombo(Godot.Key.M);
        bool map = await WaitUntil(() => game.State.Mode == GameMode.Map, 5);
        await Frames(6);
        bool travelled = target is null;
        if (map && target is not null)
        {
            var mapRoot = (Control)UiRoot.Instance!;
            // Every region of the sheet is on screen with its rooms: one key press on the room card (control change 8).
            Button? RoomButton() => Descendants<Button>(mapRoot).FirstOrDefault(x => x.IsVisibleInTree() && x.Name == "Room_" + target);
            if (RoomButton() is { } roomButton && await KeyControl(roomButton, $"map room {target}", MouseButton.Left))
                travelled = await WaitUntil(() => game.State.Room == target && WorldStage.Instance!.IsSettled && WorldStage.Instance.IsFadedIn, 30);
            else KeyboardNote($"map in {where}: no room card for {target} reachable by keys");
        }
        if (game.State.Mode == GameMode.Map) await KeyCombo(Godot.Key.M);
        await WaitLinesReal(30);
        if (!map || !travelled) QaFail($"keyboard tour {where}: M map opened={map} fast travel to {target ?? "-"}={travelled}");
        await ShotLater($"keyboard_after_map_{game.State.Era}", 0.3);
        if (game.State.Room != start) await TravelToReal(start);
        Log($"keyboard tour in {where}: done (fast travel target {target ?? "-"})");
    }

    private void KeyboardSummary()
    {
        if (!keyboardOnly) return;
        foreach (var era in GameRuntime.Instance.Content.Eras.Where(e => !erasToured.Contains(e.Year)))
            KeyboardNote($"no shortcut tour in era {era.Year} (no fast travel target seen before an action there)");
        int total = keySteps.Sum(s => s.Presses);
        var awkward = keySteps.Where(s => s.Presses > AwkwardPresses).ToList();
        Log($"keyboard summary: {keySteps.Count} steps, {total} key presses for targets / controls (mean {(keySteps.Count > 0 ? total / (double)keySteps.Count : 0):0.0}, max {(keySteps.Count > 0 ? keySteps.Max(s => s.Presses) : 0)}), {awkward.Count} awkward (> {AwkwardPresses}), {keyboardNotes.Count} notes, {blockers.Count} blockers");
        foreach (var group in awkward.GroupBy(s => s.Step).OrderByDescending(g => g.Max(s => s.Presses)))
            Log($"keyboard awkward step {group.Key}: max {group.Max(s => s.Presses)} presses, {group.Count()}x");
    }
}

/// <summary>
/// <c>--watch</c> (with <c>--menu</c>): a passive observer for input driven from outside the engine (the OS-level
/// keyboard check posts real Windows key messages to the window). It prints one <c>HARNESS watch ...</c> line whenever
/// the visible state changes: room, era, mode, done count, inventory, selection, the active line, whether the world is
/// idle, the world keyboard focus, the GUI focus owner and the top UI modal. It never sends input.
/// </summary>
public partial class DebugHarness
{
    private async Task Watch()
    {
        string last = "";
        while (true)
        {
            await Frames(1);
            var game = GameRuntime.Instance;
            if (!game.IsReady) continue;
            var s = game.State;
            var stage = WorldStage.Instance;
            bool idle = s.ActiveLineId is null && stage is { IsSettled: true, IsFadedIn: true } && !(stage.Current?.Hero.IsWalking ?? false) &&
                        !(InteractionController.Instance?.HasPending ?? false) && s.Mode is GameMode.World;
            var gui = GetViewport().GuiGetFocusOwner();
            string guiText = gui is null ? "-" : gui.HasMeta("item_id") ? "slot:" + gui.GetMeta("item_id").AsString()
                : gui.Name + (gui is Button b && b.Text.Length > 0 ? "'" + b.Text.Replace("\n", " ") + "'" : "") +
                  (gui is BaseButton { ToggleMode: true } t ? (t.ButtonPressed ? "[on]" : "[off]") : "") + "@" + (int)gui.GetGlobalRect().GetCenter().X;
            string sig = $"room={s.Room} era={s.Era} mode={s.Mode} done={s.Done.Length} last={(s.Done.Length > 0 ? s.Done[^1] : "-")} " +
                         $"inv=[{string.Join(",", s.Inventory)}] sel={s.SelectedItem ?? "-"} line={(s.ActiveLineId is null ? "-" : "on")} idle={idle} " +
                         $"labels={s.HotspotLabels} focus={InteractionController.Instance?.FocusedId ?? "-"} gui={guiText} modal={UiRoot.Instance?.TopModal?.GetType().Name ?? "-"}";
            if (sig == last) continue;
            last = sig;
            Log("watch " + sig);
        }
    }
}
