using System.Linq;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Text;
using LastBell.Core.Views;
using LastBell.Game.Hooks;
using LastBell.Game.Presentation;
using LastBell.Game.Runtime;

namespace LastBell.Game.World;

/// <summary>
/// Turns logical pointer input into Core interactions. Hover and click use the same Core resolver.
/// A click on a hotspot or exit walks the hero to its interaction point, then asks Core again on
/// arrival (conditions re-checked) and only executes when the resolution is still the same.
/// An invalid item click resolves to None and is a complete no-op (no walk, no text, selection kept).
/// Also owns keyboard focus (Tab / Shift+Tab over the accessible order, Enter = left, Backspace = right).
/// Double click (owner control changes 2026-10-05): a second left press on the same target (floor: within
/// <see cref="PresentationSettings.DoubleClickSlopPx"/>) within <see cref="PresentationSettings.DoubleClickSeconds"/> puts
/// the hero at the end of his walk at once (<see cref="Actor.FinishWalk"/>) and the flow continues exactly as if the walk
/// had ended: Core is asked again on arrival and the action / exit runs once. The second press never submits again, so
/// a double click can never commit twice. Keyboard: Enter twice on the same focus, or Shift+Enter. Touch: double tap.
/// </summary>
public partial class InteractionController : Node
{
    private sealed record Pending(Hit Hit, PointerButton Button, Resolution Resolution, Vector2 FacePoint);

    private sealed record Press(double Time, Vector2 Position, string Key);

    private Pending? pending;
    private Press? lastPress;
    private (double Time, Vector2 Position)? lastWorldPress;
    private (double Time, string Id)? lastConfirm;
    private double lastWorldConfirm = -10;
    private int focusIndex = -1;
    private string? focusRoom;

    /// <summary>The singleton controller.</summary>
    public static InteractionController? Instance { get; private set; }

    /// <summary>The NPC hotspot of the current conversation (topic menu), or null.</summary>
    public string? TalkHotspotId { get; private set; }

    /// <summary>True while the hero walks towards a pending interaction.</summary>
    public bool HasPending => pending is not null;

    /// <summary>True when nothing is in progress (no walk, no transition, no playback) — used by the debug harness.</summary>
    public bool IsIdle
    {
        get
        {
            var stage = WorldStage.Instance;
            var state = GameRuntime.Instance.State;
            return pending is null && stage is not null && stage.IsSettled && stage.IsFadedIn && !(stage.Current?.Hero.IsWalking ?? false) &&
                   state.ActiveLineId is null;
        }
    }

    /// <summary>The keyboard-focused target id, or null.</summary>
    public string? FocusedId => WorldStage.Instance?.Current?.Labels.FocusedId;

    /// <inheritdoc />
    public override void _Ready()
    {
        Instance = this;
        GameRuntime.Instance.SessionReplaced += () => { pending = null; ResetDoubleClick(); ClearFocus(); HoverPresenter.Hide(); };
        GameRuntime.Instance.RoomChanged += (_, _) => { pending = null; ResetDoubleClick(); ClearFocus(); HoverPresenter.Hide(); };
        // The hover sentence belongs to the selection it was resolved with: when a successful use clears the cursor item
        // (PT-F09 / PT-S16) the old "use X on Y" text goes away; the next pointer motion resolves the hover again.
        GameRuntime.Instance.SelectionChanged += _ => HoverPresenter.Hide();
        GameRuntime.Instance.ModeChanged += (mode, _) =>
        {
            ResetDoubleClick(); // a press pair never spans a mode change (drawer, line, overlay)
            if (mode is not (GameMode.World or GameMode.Inventory)) HoverPresenter.Hide();
        };
    }

    private static GameRuntime Game => GameRuntime.Instance;

    private static Room? CurrentRoom => WorldStage.Instance is { IsSettled: true } s ? s.Current : null;

    private static double Now => Time.GetTicksMsec() / 1000.0;

    /// <summary>Forgets the first press of a pair: any other input in between makes the next press a single one.</summary>
    private void ResetDoubleClick()
    {
        lastPress = null;
        lastConfirm = null;
    }

    /// <summary>Double-click identity of a hit: the target id, or "floor" for floor and empty background.</summary>
    private static string PressKey(Hit hit) => hit switch
    {
        Hit.Hotspot h => "h:" + h.Id,
        Hit.Exit e => "e:" + e.Id,
        Hit.Floor or Hit.Empty => "floor",
        _ => "",
    };

    /// <summary>
    /// True for the second press of a world double click (near the first, within the threshold): the router does not
    /// pass it on to a line that the first press started.
    /// </summary>
    public bool IsDoubleClickFollowUp(Vector2? position) =>
        lastWorldPress is { } p && position is { } at && Now - p.Time <= PresentationSettings.DoubleClickSeconds &&
        p.Position.DistanceTo(at) <= PresentationSettings.DoubleClickSlopPx * 2;

    /// <summary>True for an Enter right after an Enter that acted in the world (double Enter).</summary>
    public bool IsConfirmFollowUp() => Now - lastWorldConfirm <= PresentationSettings.DoubleClickSeconds;

    /// <summary>
    /// Double-click skip: when the hero walks, he is put at the destination and the arrival runs now (re-resolved
    /// through Core). Returns false when he does not walk (the first press already acted or was a no-op).
    /// </summary>
    public bool SkipWalk()
    {
        var room = CurrentRoom;
        if (room is null || !room.Hero.IsWalking) return false;
        WalkSkipped?.Invoke();
        return room.Hero.FinishWalk();
    }

    /// <summary>Raised right before a double click / Shift+Enter skips the walk (QA).</summary>
    public event System.Action? WalkSkipped;

    // ------------------------------------------------------------------ pointer

    /// <summary>A pointer press at a canvas position (mouse, touch tap, or injected).</summary>
    public void PointerAt(Vector2 canvasPosition, PointerButton button)
    {
        var room = CurrentRoom;
        if (room is null) return;
        ClearFocus();
        var hit = room.HitTest(canvasPosition);
        if (button == PointerButton.Left && AcceptsWorldInput(Game.State))
        {
            string key = PressKey(hit);
            bool second = lastPress is { } last && key.Length > 0 && last.Key == key &&
                          Now - last.Time <= PresentationSettings.DoubleClickSeconds &&
                          (key != "floor" || last.Position.DistanceTo(canvasPosition) <= PresentationSettings.DoubleClickSlopPx);
            lastPress = second ? null : new Press(Now, canvasPosition, key); // a third press starts a new pair
            lastWorldPress = (Now, canvasPosition);
            if (second)
            {
                SkipWalk();
                return;
            }
        }
        else ResetDoubleClick();
        Submit(hit, button, canvasPosition);
    }

    /// <summary>Pointer moved: update the hover text from Core's resolver.</summary>
    public void PointerMoved(Vector2 canvasPosition)
    {
        var room = CurrentRoom;
        if (room is null || !AcceptsWorldInput(Game.State)) { HoverPresenter.Hide(); return; }
        var hit = room.HitTest(canvasPosition);
        if (room.TimeNodeTakes(canvasPosition, hit))
        {
            // The painted clock of an anchor node opens the era chooser (DECISIONS, ISSUES PT-F10).
            HoverPresenter.Show(new HoverInfo(Room.TimeNodeName, TextRef.Empty, new Resolution.None()), canvasPosition, false, false);
            return;
        }
        if (hit is Hit.Floor or Hit.Empty) { HoverPresenter.Hide(); return; }
        var info = Game.Session.Hover(hit);
        // Owner control change 6 (2026-10-06): with an item on the cursor only a valid combination gets a label (Core's
        // action sentence for an executable item rule); every other hotspot, NPC or exit shows nothing.
        if (Game.State.SelectedItem is not null && !IsItemUse(info.Resolution)) { HoverPresenter.Hide(); return; }
        HoverPresenter.Show(info, canvasPosition, Game.State.SelectedItem is not null, false);
    }

    /// <summary>
    /// True when a left-click resolution with the selected item is an executable item use on a scene target (Core
    /// <see cref="Resolution.Action"/>; owner control change 6: the only hover label and Tab stop while an item is selected).
    /// </summary>
    public static bool IsItemUse(Resolution resolution) => resolution is Resolution.Action a && !a.ActionDef.IsInventoryAction;

    /// <summary>
    /// Submits a hit with a logical button: the single entry point for world interactions (also used
    /// by the inventory UI with <see cref="Hit.Item"/>).
    /// </summary>
    public void Submit(Hit hit, PointerButton button, Vector2? pointer = null)
    {
        var state = Game.State;
        var room = CurrentRoom;
        if (room is null || !AcceptsWorldInput(state)) return;
        DialoguePresenter.Instance?.HideBark();
        if (hit is Hit.Item) ResetDoubleClick(); // an inventory slot press splits a world press pair

        // Owner control change 6 (2026-10-06): a press into the scene outside the open drawer closes the drawer. With an
        // item picked there, a right click only closes it and keeps the item on the cursor for the scene (a further right
        // click, drawer closed, cancels the selection as before); a left click closes it and then resolves normally (a
        // valid target uses the item, an invalid one stays a complete no-op that keeps the selection).
        if (state.Mode == GameMode.Inventory && hit is not Hit.Item)
        {
            if (button == PointerButton.Right && state.SelectedItem is not null)
            {
                CloseInventory();
                return;
            }
            if (button == PointerButton.Left) CloseInventory();
        }

        // The painted node clock: walk there, then the same era chooser as the HUD clock button (PT-F10).
        if (button == PointerButton.Left && room.TimeNode is { } node &&
            room.TimeNodeTakes(pointer ?? (node.HotspotId is not null ? node.Rect.GetCenter() : new Vector2(-1, -1)), hit))
        {
            CloseInventory();
            pending = null;
            var nodeFace = node.Rect.GetCenter();
            WalkHero(room, node.InteractionPoint, () =>
            {
                if (CurrentRoom != room || room.TimeNode is null || Game.State.Mode != GameMode.World) return;
                room.Hero.FaceTowards(nodeFace);
                UiBus.RequestOpen(UiPanel.Portal);
            });
            return;
        }

        // Left click on non-walkable background walks to the closest walkable point.
        if (hit is Hit.Empty && button == PointerButton.Left && state.SelectedItem is null && pointer is { } p)
        {
            var clamped = room.Walk.Clamp(p);
            hit = new Hit.Floor(clamped.X, clamped.Y);
        }

        var resolution = Game.Session.Resolve(hit, button);
        switch (resolution)
        {
            case Resolution.None:
                return; // complete no-op: no walk, no line, selection kept
            case Resolution.CancelSelection or Resolution.ToggleInventory:
                Game.Session.Apply(resolution);
                return;
            case Resolution.SelectItem:
                // Keep the drawer open so a recipe can be tried; clicking the scene closes it.
                Game.Session.Apply(resolution, combineMode: state.Mode == GameMode.Inventory);
                return;
            case Resolution.Look look when button == PointerButton.Right || hit is Hit.Item:
                ShowLook(look, room, hit);
                return;
            case Resolution.Walk walk:
                CloseInventory();
                pending = null;
                WalkHero(room, new Vector2((float)walk.X, (float)walk.Y), null);
                return;
            case Resolution.Action action when action.ActionDef.IsInventoryAction:
                Execute(room, new Pending(hit, button, resolution, room.Hero.Feet));
                return;
        }

        // Look (left click on an atmospheric prop or a locked exit), Travel, Dialogue, Action: walk first.
        string? targetId = hit switch { Hit.Hotspot h => h.Id, Hit.Exit e => e.Id, _ => null };
        if (targetId is null || !room.TryGetTarget(targetId, out var target)) return;
        CloseInventory();
        var stand = room.ApproachPoint(target, room.Hero.Feet);
        // Beside an NPC the hero turns to the person (side view), not up to the rect centre (back view).
        var face = target.Kind == TargetKind.Npc ? new Vector2(target.Rect.GetCenter().X, stand.Y) : target.Rect.GetCenter();
        var next = new Pending(hit, button, resolution, face);
        pending = next;
        WalkHero(room, stand, () => Arrive(next));
    }

    private void Arrive(Pending arrived)
    {
        if (!ReferenceEquals(pending, arrived)) return;
        pending = null;
        var room = CurrentRoom;
        if (room is null) return;
        // Ask Core again: conditions are re-checked on arrival.
        var again = Game.Session.Resolve(arrived.Hit, arrived.Button);
        if (!SameResolution(arrived.Resolution, again)) return;
        room.Hero.FaceTowards(arrived.FacePoint);
        Execute(room, arrived with { Resolution = again });
    }

    private void Execute(Room room, Pending what)
    {
        switch (what.Resolution)
        {
            case Resolution.Look look:
                ShowLook(look, room, what.Hit);
                break;
            case Resolution.Travel travel:
                WorldStage.Instance?.TravelThrough(travel.ExitId);
                break;
            case Resolution.Dialogue dialogue:
                TalkHotspotId = dialogue.HotspotId;
                if (room.Npcs.TryGetValue(dialogue.HotspotId, out var npc)) npc.FaceTowards(room.Hero.Feet);
                Game.Session.Apply(dialogue);
                break;
            case Resolution.Action action:
                var def = action.ActionDef;
                if (!string.IsNullOrEmpty(def.Animation)) room.Hero.Visual.PlayGesture(def.Animation);
                if (def.Puzzle is not null) Game.OpenPuzzle(def.Id);
                else Game.Commit(def.Id);
                break;
        }
    }

    /// <summary>Same kind and same target/action as resolved before walking.</summary>
    private static bool SameResolution(Resolution before, Resolution after) => (before, after) switch
    {
        (Resolution.Action a, Resolution.Action b) => a.ActionDef.Id == b.ActionDef.Id,
        (Resolution.Travel a, Resolution.Travel b) => a.ExitId == b.ExitId,
        (Resolution.Dialogue a, Resolution.Dialogue b) => a.HotspotId == b.HotspotId,
        (Resolution.Look a, Resolution.Look b) => a.Text.Key == b.Text.Key,
        _ => false,
    };

    private static void ShowLook(Resolution.Look look, Room room, Hit hit)
    {
        string? id = hit switch { Hit.Hotspot h => h.Id, Hit.Exit e => e.Id, _ => null };
        if (id is not null && room.TryGetTarget(id, out var target) && !room.Hero.IsWalking) room.Hero.FaceTowards(target.Rect.GetCenter());
        Game.Session.Apply(look); // records the first look in the journal
        DialoguePresenter.Instance?.ShowBark(look.Text, GameRuntime.HeroId);
    }

    private void WalkHero(Room room, Vector2 destination, System.Action? arrived)
    {
        var hero = room.Hero;
        var path = room.Walk.FindPath(hero.Feet, destination);
        if (path is null)
        {
            pending = null;
            hero.Stop();
            DialoguePresenter.Instance?.ShowBark(LastBell.Core.Text.UiText.PathBlocked, GameRuntime.HeroId); // ui.system.path_blocked (GAME-03)
            return;
        }
        hero.WalkPath(path, arrived);
    }

    private static void CloseInventory()
    {
        if (Game.State.Mode == GameMode.Inventory) Game.Update(GameRules.ToggleInventory);
    }

    private static bool AcceptsWorldInput(GameState state) => state.Mode is GameMode.World or GameMode.Inventory;

    // ------------------------------------------------------------------ keyboard focus (AT19)

    /// <summary>Moves the keyboard focus through the room's accessible order (NPCs, progress props, atmospheric props, exits).</summary>
    public void MoveFocus(int direction)
    {
        var room = CurrentRoom;
        if (room is null || !AcceptsWorldInput(Game.State)) return;
        // With an item selected Tab cycles only the targets where it has an executable use (owner control change 6).
        bool itemSelected = Game.State.SelectedItem is not null;
        var order = room.View.AccessibleOrder
            .Where(id => room.TryGetTarget(id, out var t) && (!itemSelected || IsItemUse(Game.Session.Resolve(t.ToHit(), PointerButton.Left))))
            .ToList();
        if (order.Count == 0)
        {
            if (room.Labels.FocusedId is not null) { ClearFocus(); HoverPresenter.Hide(); }
            return;
        }
        if (focusRoom != room.RoomId) { focusIndex = -1; focusRoom = room.RoomId; }
        ResetDoubleClick();
        int current = room.Labels.FocusedId is { } f ? order.IndexOf(f) : -1;
        focusIndex = current < 0 ? (direction > 0 ? 0 : order.Count - 1) : (current + direction + order.Count) % order.Count;
        room.Labels.FocusedId = order[focusIndex];
        if (room.TryGetTarget(order[focusIndex], out var target))
            HoverPresenter.Show(Game.Session.Hover(target.ToHit()), target.LabelAnchor, Game.State.SelectedItem is not null, true);
    }

    /// <summary>
    /// Enter: left click on the focused target (no focus: nothing). A second Enter on the same focus within the
    /// double-click threshold, or <paramref name="skipWalk"/> (Shift+Enter), skips the walk like a double click.
    /// </summary>
    public void ConfirmFocused(bool skipWalk = false)
    {
        var room = CurrentRoom;
        if (room?.Labels.FocusedId is not { } id || !room.TryGetTarget(id, out var target)) return;
        bool second = lastConfirm is { } last && last.Id == id && Now - last.Time <= PresentationSettings.DoubleClickSeconds;
        lastConfirm = second ? null : (Now, id);
        lastWorldConfirm = Now;
        if (second)
        {
            SkipWalk();
            return;
        }
        Submit(target.ToHit(), PointerButton.Left);
        if (skipWalk) SkipWalk();
    }

    /// <summary>Backspace: right click on the focused target, or on empty floor (inventory / cancel selection).</summary>
    public void BackFocused()
    {
        var room = CurrentRoom;
        if (room is null) return;
        if (room.Labels.FocusedId is { } id && room.TryGetTarget(id, out var target)) Submit(target.ToHit(), PointerButton.Right);
        else Submit(new Hit.Empty(), PointerButton.Right);
    }

    /// <summary>Clears keyboard focus.</summary>
    public void ClearFocus()
    {
        var room = WorldStage.Instance?.Current;
        if (room is not null && room.Labels.FocusedId is not null) room.Labels.FocusedId = null;
        focusIndex = -1;
    }
}
