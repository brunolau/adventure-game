using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Text;
using LastBell.Game.Presentation;
using LastBell.Game.Runtime;
using LastBell.Game.UI;
using LastBell.Game.UI.Dialogue;
using LastBell.Game.UI.Menus;
using LastBell.Game.UI.Puzzles;
using LastBell.Game.World;

namespace LastBell.Game.Diagnostics;

/// <summary>
/// The harness's "real player" driver (flag <c>--real</c>, implied by <c>--play-all</c> and
/// <c>--play-side</c>): every step is an OS-style Godot input event that goes through the GUI first
/// and then the InputRouter, exactly like a mouse or keyboard. World targets and exits are clicked
/// at a point inside their rect where the room's own hit test returns that target and no GUI control
/// is hovered (a point that fails both is reported as a <c>BLOCKER</c>); items are picked from the
/// inventory drawer's slot buttons; topics are chosen by clicking the topic menu's button; puzzles are
/// solved by clicking the modal's controls and its confirm button; portals by T and the era button.
/// Nothing here edits Core state; lines play out by auto-advance (or Esc when skipping is asked for).
/// </summary>
public partial class DebugHarness
{
    private bool realInput;
    private int retries;

    /// <summary>Points where a target could not be clicked (GUI covers it or the hit test picks another target).</summary>
    private readonly List<string> blockers = new();

    // ------------------------------------------------------------------ primitives

    private async Task MoveMouse(Vector2 canvasPoint)
    {
        var viewportPoint = GetTree().Root.GetFinalTransform() * canvasPoint;
        QaWindow.WarpMouse(viewportPoint);
        Godot.Input.ParseInputEvent(new InputEventMouseMotion { Position = viewportPoint, GlobalPosition = viewportPoint });
        await Frames(2);
    }

    private Control? HoveredGui() => GetViewport().GuiGetHoveredControl();

    /// <summary>
    /// A real mouse click like <see cref="RawMouse"/>, but the OS cursor is warped back onto the point
    /// right before each button event: the InputRouter reads the current mouse position, and another
    /// window on the desktop (a second Godot run, the user) may have moved the cursor in between.
    /// </summary>
    private async Task RawMouseReal(Vector2 canvasPoint, MouseButton button)
    {
        var viewportPoint = GetTree().Root.GetFinalTransform() * canvasPoint;
        QaWindow.WarpMouse(viewportPoint);
        Godot.Input.ParseInputEvent(new InputEventMouseMotion { Position = viewportPoint, GlobalPosition = viewportPoint });
        await Frames(2);
        foreach (bool pressed in new[] { true, false })
        {
            QaWindow.WarpMouse(viewportPoint);
            Godot.Input.ParseInputEvent(new InputEventMouseMotion { Position = viewportPoint, GlobalPosition = viewportPoint });
            Godot.Input.ParseInputEvent(new InputEventMouseButton
            {
                ButtonIndex = button, Pressed = pressed, Position = viewportPoint, GlobalPosition = viewportPoint,
                ButtonMask = pressed ? (button == MouseButton.Left ? MouseButtonMask.Left : MouseButtonMask.Right) : 0,
            });
            await Frames(1);
        }
    }

    private static IEnumerable<T> Descendants<T>(Node root) where T : Node
    {
        foreach (var child in root.GetChildren())
        {
            if (child is T t) yield return t;
            foreach (var d in Descendants<T>(child)) yield return d;
        }
    }

    private static string PathOf(Node? node) => node is null ? "-" : node.GetPath().ToString().Replace("/root/Main/", "");

    private static Vector2 CanvasCenter(Control c)
    {
        var t = c.GetGlobalTransformWithCanvas();
        return t * (c.Size / 2);
    }

    /// <summary>Clicks a GUI control with a real mouse event (scrolls it into view first). False when another control is on top.</summary>
    private async Task<bool> ClickControl(Control control, string what, MouseButton button = MouseButton.Left)
    {
        if (keyboardOnly) return await KeyControl(control, what, button); // KeyboardDriver.cs (AT19)
        for (Node? p = control.GetParent(); p is not null; p = p.GetParent())
            if (p is ScrollContainer scroll) scroll.EnsureControlVisible(control);
        await Frames(2);
        var point = CanvasCenter(control);
        await MoveMouse(point);
        var hovered = HoveredGui();
        bool ok = hovered is not null && (hovered == control || control.IsAncestorOf(hovered));
        if (!ok)
        {
            Blocker($"{what}: control {PathOf(control)} at {point} is covered by {PathOf(hovered)}");
            return false;
        }
        await RawMouseReal(point, button);
        return true;
    }

    private void Blocker(string text)
    {
        blockers.Add(text);
        Log("BLOCKER " + text);
        _ = ShotLater($"BLOCKER_{blockers.Count:D2}", 0);
    }

    /// <summary>A point inside the target's rect that hit-tests to the target and has no GUI on top.</summary>
    private async Task<Vector2?> FindClickPoint(string targetId)
    {
        var room = WorldStage.Instance!.Current!;
        if (!room.TryGetTarget(targetId, out var target)) return null;
        var want = target.ToHit();
        var r = target.Rect;
        var fractions = new (float X, float Y)[]
        {
            (0.5f, 0.5f), (0.5f, 0.3f), (0.5f, 0.7f), (0.3f, 0.5f), (0.7f, 0.5f), (0.25f, 0.25f), (0.75f, 0.25f),
            (0.25f, 0.75f), (0.75f, 0.75f), (0.5f, 0.12f), (0.5f, 0.88f), (0.12f, 0.5f), (0.88f, 0.5f),
        };
        string? coveredBy = null;
        foreach (var (fx, fy) in fractions)
        {
            var p = r.Position + new Vector2(r.Size.X * fx, r.Size.Y * fy);
            if (p.X < 1 || p.Y < 1 || p.X > Room.CanvasSize.X - 1 || p.Y > Room.CanvasSize.Y - 1) continue;
            if (!Equals(room.HitTest(p), want)) continue;
            await MoveMouse(p);
            var gui = HoveredGui();
            if (gui is null) return p;
            coveredBy ??= PathOf(gui);
        }
        Blocker($"target {targetId} in {room.RoomId}: no clickable point (rect {r}; GUI on top: {coveredBy ?? "none, hit test returns another target"})");
        return null;
    }

    private async Task<bool> ClickTarget(string targetId, MouseButton button = MouseButton.Left)
    {
        if (keyboardOnly) return await KeyTarget(targetId, button); // KeyboardDriver.cs (AT19)
        var p = await FindClickPoint(targetId);
        if (p is null) return false;
        await RawMouseReal(p.Value, button);
        return true;
    }

    private async Task KeyReal(Key key)
    {
        foreach (bool pressed in new[] { true, false })
        {
            Godot.Input.ParseInputEvent(new InputEventKey { Keycode = key, PhysicalKeycode = key, Pressed = pressed });
            await Frames(1);
        }
        await Frames(1);
    }

    // ------------------------------------------------------------------ inventory

    private Button? SlotButton(string itemId) =>
        Descendants<Button>(UiRoot.Instance!).FirstOrDefault(b => b.HasMeta("item_id") && b.GetMeta("item_id").AsString() == itemId && b.IsVisibleInTree());

    private async Task OpenDrawerReal()
    {
        if (GameRuntime.Instance.State.Mode == GameMode.Inventory) return;
        await KeyReal(Godot.Key.I);
        await WaitUntil(() => GameRuntime.Instance.State.Mode == GameMode.Inventory, 5);
        await Frames(3);
    }

    private async Task CloseDrawerReal()
    {
        if (GameRuntime.Instance.State.Mode != GameMode.Inventory) return;
        await KeyReal(Godot.Key.I);
        await WaitUntil(() => GameRuntime.Instance.State.Mode == GameMode.World, 5);
    }

    /// <summary>Opens the drawer and clicks the item's slot (left = select / combine with the selected item, right = look).</summary>
    private async Task<bool> ClickSlotReal(string itemId, MouseButton button = MouseButton.Left)
    {
        await OpenDrawerReal();
        var slot = SlotButton(itemId);
        if (slot is null)
        {
            Blocker($"item {itemId}: no visible slot in the drawer");
            return false;
        }
        return await ClickControl(slot, "slot " + itemId, button);
    }

    private async Task SelectItemReal(string itemId, bool keepDrawerOpen)
    {
        var game = GameRuntime.Instance;
        if (game.State.SelectedItem == itemId)
        {
            if (keepDrawerOpen) await OpenDrawerReal();
            return;
        }
        await DropSelectionReal();
        if (!await ClickSlotReal(itemId)) throw new InvalidOperationException($"cannot click the slot of {itemId}");
        await Frames(2);
        if (game.State.SelectedItem != itemId) throw new InvalidOperationException($"slot click did not select {itemId} (selected {game.State.SelectedItem ?? "-"})");
        if (!keepDrawerOpen) await CloseDrawerReal();
    }

    /// <summary>A player drops a kept item from the cursor with Esc (GameRules.Escape cancels the selection first).</summary>
    private async Task DropSelectionReal()
    {
        var game = GameRuntime.Instance;
        if (game.State.SelectedItem is not null && game.State.Mode is GameMode.World or GameMode.Inventory) await KeyReal(Godot.Key.Escape);
        if (game.State.Mode == GameMode.Inventory) await CloseDrawerReal();
        if (game.State.Mode == GameMode.Pause) await KeyReal(Godot.Key.Escape);
    }

    // ------------------------------------------------------------------ topics, portals

    private async Task ChooseTopicReal(ActionDef action)
    {
        var game = GameRuntime.Instance;
        var hotspot = game.Content.FindHotspot(action.Target)?.Hotspot ?? throw new InvalidOperationException("no hotspot " + action.Target);
        var option = Dialogue.TopicsFor(game.Content, game.State, hotspot).FirstOrDefault(t => t.Id == action.Id)
                     ?? throw new InvalidOperationException($"topic {action.Id} not offered by {action.Target}");
        string label = TextService.Get(option.Label);
        Button? button = null;
        await WaitUntil(() =>
        {
            button = Descendants<TopicMenuView>(UiRoot.Instance!).SelectMany(Descendants<Button>)
                .FirstOrDefault(b => b.IsVisibleInTree() && b.Text.StartsWith(label, StringComparison.Ordinal));
            return button is not null;
        }, 5);
        if (button is null) throw new InvalidOperationException($"topic button '{label}' not shown");
        if (!await ClickControl(button, "topic " + action.Id)) throw new InvalidOperationException($"topic button {action.Id} not clickable");
    }

    private async Task UsePortalReal(int year)
    {
        var game = GameRuntime.Instance;
        await KeyReal(Godot.Key.T);
        if (!await WaitUntil(() => UiRoot.Instance!.TopModal is PortalChooser, 5)) throw new InvalidOperationException($"portal chooser did not open in {game.State.Room}");
        await Frames(3);
        // The button shows the presented year (Ivanka: era 1960 is shown as 1962), as the player sees it.
        string shown = TextService.EraYear(year) + " · ";
        var button = Descendants<Button>(UiRoot.Instance!.TopModal!).FirstOrDefault(b => b.IsVisibleInTree() && b.Text.StartsWith(shown, StringComparison.Ordinal))
                     ?? throw new InvalidOperationException($"no era button {year}");
        if (button.Disabled) throw new InvalidOperationException($"era button {year} is disabled in {game.State.Room}");
        if (!await ClickControl(button, "portal " + year)) throw new InvalidOperationException($"era button {year} not clickable");
    }

    private async Task TravelToReal(string roomId)
    {
        var game = GameRuntime.Instance;
        var route = Navigation.FindRoute(game.Content, game.State, roomId) ?? throw new InvalidOperationException($"no route to {roomId}");
        foreach (var step in route)
        {
            await WaitLinesReal(30);
            await DropSelectionReal();
            bool arrived = false;
            for (int attempt = 0; attempt < 2 && !arrived; attempt++)
            {
                if (attempt > 0)
                {
                    // The hero stands idle in the old room: the click did not land (see RawMouseReal). Click again.
                    Log($"WARN travel to {step.To}: no transition after the click, clicking again");
                    retries++;
                }
                if (step.Kind == RouteStepKind.Exit)
                {
                    if (!await ClickTarget(step.ExitId!)) throw new InvalidOperationException($"exit {step.ExitId} not clickable");
                }
                else await UsePortalReal(step.Year!.Value);
                arrived = await WaitUntil(() => game.State.Room == step.To && WorldStage.Instance!.IsSettled && WorldStage.Instance.IsFadedIn, 20) ||
                          (game.State.Room != step.From && await WaitUntil(() => game.State.Room == step.To && WorldStage.Instance!.IsSettled && WorldStage.Instance.IsFadedIn, 20));
            }
            if (!arrived)
                throw new InvalidOperationException($"travel to {step.To} failed (room {game.State.Room}, mode {game.State.Mode})");
            Log($"travelled to {step.To} ({(step.Kind == RouteStepKind.Exit ? "exit " + step.ExitId : "portal " + step.Year)})");
            OnRoomSettled();
            if (Has("all-lines")) { await WaitLinesReal(30); await LookAroundReal(); }
        }
        await WaitLinesReal(30);
    }

    // ------------------------------------------------------------------ puzzles

    private PuzzleControl? OpenPuzzleControl() =>
        UiRoot.Instance!.PuzzleView is { Visible: true } modal ? Descendants<PuzzleControl>(modal).FirstOrDefault() : null;

    private Button? PuzzleConfirmButton(PuzzleDef def)
    {
        var t = TextKeys.ConfirmOf(def);
        string text = t.IsEmpty ? TextService.Ui("ui.puzzle.confirm") : TextService.Get(t);
        var control = OpenPuzzleControl();
        return Descendants<Button>(UiRoot.Instance!.PuzzleView).FirstOrDefault(b => b.IsVisibleInTree() && b.Text == text && (control is null || !control.IsAncestorOf(b)));
    }

    /// <summary>Clicks the puzzle modal's controls until its draft equals <paramref name="answer"/> (no confirm).</summary>
    private async Task EnterPuzzleAnswerReal(PuzzleDef def, JsonNode? answer)
    {
        if (!await WaitUntil(() => OpenPuzzleControl() is not null, 10)) throw new InvalidOperationException($"puzzle {def.Id}: modal not shown");
        await Frames(4);
        var control = OpenPuzzleControl()!;
        var buttons = Descendants<Button>(control).Where(b => b.IsVisibleInTree()).ToList();
        switch (control)
        {
            case MatchingControl:
            {
                var left = def.Controls.Left ?? Array.Empty<string>();
                var right = (def.Controls.Right ?? Array.Empty<string>()).ToList();
                var values = (answer as JsonArray)?.Select(n => n?.GetValue<string>()).ToList() ?? new List<string?>();
                for (int i = 0; i < left.Count && i < values.Count; i++)
                {
                    int j = right.IndexOf(values[i]!);
                    if (j < 0) throw new InvalidOperationException($"puzzle {def.Id}: no right option {values[i]}");
                    if (!await ClickControl(buttons[i], $"{def.Id} left {i + 1}")) throw new InvalidOperationException("matching left button covered");
                    if (!await ClickControl(buttons[left.Count + j], $"{def.Id} right {j + 1}")) throw new InvalidOperationException("matching right button covered");
                }
                break;
            }
            case RotateOverlayControl rotate:
            {
                int want = answer!.GetValue<int>();
                for (int k = 0; k < 8 && rotate.Draft?.GetValue<int>() != want; k++)
                    if (!await ClickControl(buttons[1], $"{def.Id} rotate right")) throw new InvalidOperationException("rotate button covered");
                break;
            }
            case DigitsControl digits:
            {
                var want = (answer as JsonArray)!.Select(n => n!.GetValue<int>()).ToList();
                for (int i = 0; i < want.Count; i++)
                    for (int k = 0; k < 12 && (digits.Draft as JsonArray)![i]!.GetValue<int>() != want[i]; k++)
                        if (!await ClickControl(buttons[i * 2], $"{def.Id} digit {i + 1} up")) throw new InvalidOperationException("digit button covered");
                break;
            }
            case GridChoiceControl:
            {
                int rows = def.Controls.Rows ?? 3, columns = def.Controls.Columns ?? 4;
                bool fromBottom = def.Controls.RowOrigin == "bottom", fromRight = def.Controls.ColumnOrigin == "right";
                int row = answer!["row"]!.GetValue<int>(), column = answer["column"]!.GetValue<int>();
                int r = fromBottom ? rows - row : row - 1;
                int c = fromRight ? columns - column : column - 1;
                if (!await ClickControl(buttons[r * columns + c], $"{def.Id} cell {row},{column}")) throw new InvalidOperationException("grid cell covered");
                break;
            }
            default:
                throw new InvalidOperationException($"puzzle {def.Id}: unknown control {control.GetType().Name}");
        }
        await Frames(2);
        if (!JsonDeep.Equals(control.Draft, answer))
            throw new InvalidOperationException($"puzzle {def.Id}: modal draft {control.Draft?.ToJsonString()} != wanted {answer?.ToJsonString()}");
    }

    private async Task ConfirmPuzzleReal(PuzzleDef def)
    {
        var confirm = PuzzleConfirmButton(def) ?? throw new InvalidOperationException($"puzzle {def.Id}: no confirm button");
        if (!await ClickControl(confirm, def.Id + " confirm")) throw new InvalidOperationException($"puzzle {def.Id}: confirm covered");
        await Frames(3);
    }

    /// <summary>A wrong answer for the puzzle (first value that differs from the solution).</summary>
    private static JsonNode? WrongAnswer(PuzzleDef def)
    {
        var solution = def.Solution;
        switch (solution)
        {
            case JsonArray a when a.Count > 1 && a[0] is JsonValue v0 && v0.TryGetValue<string>(out _):
                var swapped = a.Select(n => n!.DeepClone()).ToList();
                (swapped[0], swapped[1]) = (swapped[1], swapped[0]);
                return new JsonArray(swapped.ToArray());
            case JsonArray a:
                var digits = a.Select(n => n!.GetValue<int>()).ToArray();
                digits[0] = (digits[0] + 1) % 10;
                return PuzzleAnswers.Digits(digits);
            case JsonObject o:
                int row = o["row"]!.GetValue<int>();
                return PuzzleAnswers.Grid(row == 1 ? 2 : 1, o["column"]!.GetValue<int>());
            case JsonValue v:
                int deg = v.GetValue<int>();
                return PuzzleAnswers.Rotation((deg + 90) % 360);
        }
        return null;
    }

    // ------------------------------------------------------------------ lines

    /// <summary>Lets queued lines play out (auto-advance), or presses Esc when <c>--skip-cutscenes</c>; returns when the world is idle.</summary>
    private async Task WaitLinesReal(double timeout)
    {
        var game = GameRuntime.Instance;
        var deadline = Time.GetTicksMsec() + timeout * 1000;
        while (Time.GetTicksMsec() < deadline)
        {
            var stage = WorldStage.Instance!;
            bool hasPending = InteractionController.Instance?.HasPending ?? false;
            bool walking = stage.Current?.Hero.IsWalking ?? false;
            var presenter = DialoguePresenter.Instance;
            if (Has("skip-cutscenes") && game.State.Mode == GameMode.Cutscene && presenter?.IsShowingLine == true) await KeyReal(Godot.Key.Escape);
            if (game.State.Mode == GameMode.Dialogue && game.State.ActiveLineId is null && !(presenter?.HasPreface ?? false))
            {
                // A topic menu left open after a topic's lines: the player ends the conversation (Esc).
                await KeyReal(Godot.Key.Escape);
            }
            bool idle = game.State.ActiveLineId is null && !(presenter?.HasPreface ?? false) && stage.IsSettled && stage.IsFadedIn && !hasPending && !walking &&
                        game.State.Mode is GameMode.World or GameMode.Inventory;
            // The ending (epilogue, credits) is a modal of its own: the caller drives it (FinishEndingReal).
            if (idle && (!(UiRoot.Instance?.HasModal ?? false) || UiRoot.Instance!.TopModal is UI.Cutscenes.EndingSequence or CreditsScreen)) return;
            await Frames(1);
        }
        Log($"WARN lines still playing after {timeout}s (mode {game.State.Mode}, line {game.State.ActiveLineId ?? "-"}, modal {UiRoot.Instance?.TopModal?.Name ?? "-"})");
    }

    // ------------------------------------------------------------------ one action

    private async Task PerformActReal(string actionId)
    {
        var game = GameRuntime.Instance;
        var content = game.Content;
        var action = content.FindAction(actionId) ?? throw new InvalidOperationException("unknown action " + actionId);
        if (game.State.IsDone(actionId)) throw new InvalidOperationException($"act {actionId}: already done");
        await WaitLinesReal(30);
        await DropSelectionReal();
        if (!action.IsInventoryAction && action.Room != game.State.Room) await TravelToReal(action.Room);
        await KeyboardTourIfNew(); // --keyboard: shortcut tour once per era (KeyboardDriver.cs)
        int doneBefore = game.State.Done.Length;

        if (action.SelectedItem is not null) await SelectItemReal(action.SelectedItem, keepDrawerOpen: action.IsCombine);
        var hit = action.IsCombine ? (Hit)new Hit.Item(action.Target) : new Hit.Hotspot(action.Target);
        var expected = game.Session.Resolve(hit, PointerButton.Left);
        Log($"act {actionId}: {hit} resolves to {expected.GetType().Name} (real input)");
        bool clicked = action.IsCombine ? await ClickSlotReal(action.Target) : await ClickTarget(action.Target);
        if (!clicked) throw new InvalidOperationException($"act {actionId}: target {action.Target} not clickable");

        if (action.IsTopic)
        {
            if (!await WaitUntil(() => game.State.Mode == GameMode.Dialogue && game.State.ActiveLineId is null, 30))
                throw new InvalidOperationException($"act {actionId}: topic menu did not open (mode {game.State.Mode})");
            await Frames(3);
            await ChooseTopicReal(action);
        }
        else if (action.Puzzle is not null)
        {
            if (!await WaitUntil(() => game.State.Mode == GameMode.Puzzle, 30)) throw new InvalidOperationException($"act {actionId}: puzzle did not open");
            var def = content.GetPuzzle(action.Puzzle);
            await EnterPuzzleAnswerReal(def, def.Solution?.DeepClone());
            await ConfirmPuzzleReal(def);
            OnPuzzleSolved(def);
        }
        if (!await WaitUntil(() => game.State.IsDone(actionId), 30))
            throw new InvalidOperationException($"act {actionId}: not committed (mode {game.State.Mode}, room {game.State.Room}, selected {game.State.SelectedItem ?? "-"})");
        if (game.State.Done.Length != doneBefore + 1) throw new InvalidOperationException($"act {actionId}: {game.State.Done.Length - doneBefore} actions committed");
        Log($"act {actionId}: committed (real input)");
        await OnActCommitted(action);
    }
}
