using System.Linq;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
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
/// </summary>
public partial class InteractionController : Node
{
    private sealed record Pending(Hit Hit, PointerButton Button, Resolution Resolution, Vector2 FacePoint);

    private Pending? pending;
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
        GameRuntime.Instance.SessionReplaced += () => { pending = null; ClearFocus(); HoverPresenter.Hide(); };
        GameRuntime.Instance.RoomChanged += (_, _) => { pending = null; ClearFocus(); HoverPresenter.Hide(); };
        GameRuntime.Instance.ModeChanged += (mode, _) => { if (mode is not (GameMode.World or GameMode.Inventory)) HoverPresenter.Hide(); };
    }

    private static GameRuntime Game => GameRuntime.Instance;

    private static Room? CurrentRoom => WorldStage.Instance is { IsSettled: true } s ? s.Current : null;

    // ------------------------------------------------------------------ pointer

    /// <summary>A pointer press at a canvas position (mouse, touch tap, or injected).</summary>
    public void PointerAt(Vector2 canvasPosition, PointerButton button)
    {
        var room = CurrentRoom;
        if (room is null) return;
        ClearFocus();
        Submit(room.HitTest(canvasPosition), button, canvasPosition);
    }

    /// <summary>Pointer moved: update the hover text from Core's resolver.</summary>
    public void PointerMoved(Vector2 canvasPosition)
    {
        var room = CurrentRoom;
        if (room is null || !AcceptsWorldInput(Game.State)) { HoverPresenter.Hide(); return; }
        var hit = room.HitTest(canvasPosition);
        if (hit is Hit.Floor or Hit.Empty) { HoverPresenter.Hide(); return; }
        HoverPresenter.Show(Game.Session.Hover(hit), canvasPosition, Game.State.SelectedItem is not null, false);
    }

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
            DialoguePresenter.Instance?.ShowBark(new LastBell.Core.Text.TextRef("ui.system.path_blocked", LastBell.Core.Text.UiText.PathBlocked.Fallback), GameRuntime.HeroId);
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
        var order = room.View.AccessibleOrder.Where(id => room.TryGetTarget(id, out _)).ToList();
        if (order.Count == 0) return;
        if (focusRoom != room.RoomId) { focusIndex = -1; focusRoom = room.RoomId; }
        int current = room.Labels.FocusedId is { } f ? order.IndexOf(f) : -1;
        focusIndex = current < 0 ? (direction > 0 ? 0 : order.Count - 1) : (current + direction + order.Count) % order.Count;
        room.Labels.FocusedId = order[focusIndex];
        if (room.TryGetTarget(order[focusIndex], out var target))
            HoverPresenter.Show(Game.Session.Hover(target.ToHit()), target.LabelAnchor + new Vector2(0, 40), Game.State.SelectedItem is not null, true);
    }

    /// <summary>Enter: left click on the focused target (no focus: nothing).</summary>
    public void ConfirmFocused()
    {
        var room = CurrentRoom;
        if (room?.Labels.FocusedId is not { } id || !room.TryGetTarget(id, out var target)) return;
        Submit(target.ToHit(), PointerButton.Left);
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
