using System.Collections.Immutable;
using System.Text.Json.Nodes;
using LastBell.Core.Content;
using LastBell.Core.State;
using LastBell.Core.Text;

namespace LastBell.Core.Rules;

/// <summary>
/// Faithful C# port of every exported function of design-doc/runtime_contract.ts, plus the small
/// state helpers the presentation needs to apply a <see cref="Resolution"/>. All functions are pure.
/// </summary>
public static class GameRules
{
    // ------------------------------------------------------------------ runtime_contract.ts ports

    /// <summary>
    /// <c>isVisible</c>: every <c>visible_after</c> is done and no <c>hide_after</c> is done.
    /// Visibility is shared by hit test, Space labels, interactions and accessible names.
    /// </summary>
    public static bool IsVisible(HotspotDef hotspot, GameState state) =>
        state.AllDone(hotspot.VisibleAfter) && !state.AnyDone(hotspot.HideAfter);

    /// <summary><c>lookAt</c>: the last look variant whose action is done, else the base look.</summary>
    public static TextRef LookAt(HotspotDef hotspot, GameState state)
    {
        for (var i = hotspot.LookVariants.Count - 1; i >= 0; i--)
        {
            if (state.IsDone(hotspot.LookVariants[i].After)) return TextKeys.LookVariantOf(hotspot, i);
        }
        return TextKeys.BaseLookOf(hotspot);
    }

    /// <summary>
    /// <c>guardsPass</c>: not yet done, nothing excluding it is done, all prerequisites done and all
    /// required items owned (active or archived).
    /// </summary>
    public static bool GuardsPass(ActionDef action, GameState state) =>
        !state.IsDone(action.Id) && !state.AnyDone(action.ExcludedDone) &&
        state.AllDone(action.RequiresDone) && state.HasAll(action.RequiresItems);

    /// <summary>
    /// <c>validAction</c>: guards pass, the hero is in the action's room (inventory actions work
    /// anywhere) and the target hotspot is visible.
    /// </summary>
    public static bool ValidAction(GameContent content, GameState state, ActionDef action)
    {
        if (!GuardsPass(action, state)) return false;
        if (action.IsInventoryAction) return true;
        if (action.Room != state.Room) return false;
        var target = content.FindHotspot(action.Target);
        return target is not null && target.Room.Id == action.Room && IsVisible(target.Hotspot, state);
    }

    /// <summary>
    /// <c>resolveInteraction</c>: the single resolver used for hover preview and click.
    /// Right button: cancel selection first; else look at item/hotspot/exit; else toggle inventory.
    /// Left button with a selected item: only an executable item rule resolves to an action (its commit
    /// clears the selection); anything else is a complete no-op that keeps the selection (no walk, no
    /// text, no state).
    /// Left button without selection: select item, open NPC topics, run the single default action,
    /// look at props, travel through unlocked exits, read locked exits, walk on the floor.
    /// Only <see cref="GameMode.World"/> and <see cref="GameMode.Inventory"/> accept interactions.
    /// </summary>
    /// <exception cref="InvalidOperationException">Two default actions on one target (forbidden by the data).</exception>
    public static Resolution ResolveInteraction(GameContent content, GameState state, Hit hit, PointerButton button)
    {
        if (state.Mode is not (GameMode.World or GameMode.Inventory)) return Resolution.Nothing;
        var room = content.GetRoom(state.Room);
        var hotspot = hit is Hit.Hotspot hh ? room.Hotspots.FirstOrDefault(x => x.Id == hh.Id && IsVisible(x, state)) : null;
        var item = hit is Hit.Item hi && state.Has(hi.Id) ? content.FindItem(hi.Id) : null;

        if (button == PointerButton.Right)
        {
            if (state.SelectedItem is not null) return new Resolution.CancelSelection();
            if (item is not null)
            {
                var look = TextKeys.LookOf(item);
                return new Resolution.Look(look, look.Key);
            }
            if (hotspot is not null)
            {
                var look = LookAt(hotspot, state);
                return new Resolution.Look(look, look.Key);
            }
            if (hit is Hit.Exit he)
            {
                var exit = room.Exits.FirstOrDefault(x => x.Id == he.Id);
                if (exit is null) return Resolution.Nothing;
                return new Resolution.Look(state.AllDone(exit.RequiresDone) ? TextKeys.LabelOf(exit) : TextKeys.LockedOf(exit), null);
            }
            return new Resolution.ToggleInventory();
        }

        if (state.SelectedItem is not null)
        {
            var selected = state.SelectedItem;
            var match = content.Actions.FirstOrDefault(x =>
            {
                if (!ValidAction(content, state, x)) return false;
                if (hit is Hit.Item target && x.IsCombine)
                {
                    return (x.Target == target.Id && x.SelectedItem == selected) ||
                           (x.Symmetric && x.Target == selected && x.SelectedItem == target.Id);
                }
                return hotspot is not null && x.IsClick && x.Target == hotspot.Id && x.SelectedItem == selected;
            });
            return match is not null ? new Resolution.Action(match) : Resolution.Nothing;
        }

        if (item is not null) return new Resolution.SelectItem(item.Id);

        if (hotspot is not null && hotspot.IsNpc)
        {
            return new Resolution.Dialogue(hotspot.CharacterId ?? "", hotspot.Id, Dialogue.TopicsFor(content, state, hotspot));
        }

        if (hotspot is not null)
        {
            var candidates = content.Actions
                .Where(a => a.IsClick && a.SelectedItem is null && a.Target == hotspot.Id && ValidAction(content, state, a))
                .Take(2).ToList();
            if (candidates.Count > 1) throw new InvalidOperationException("Ambiguous action target: " + hotspot.Id);
            if (candidates.Count == 1) return new Resolution.Action(candidates[0]);
            var look = LookAt(hotspot, state);
            return new Resolution.Look(look, look.Key);
        }

        if (hit is Hit.Exit hx)
        {
            var exit = room.Exits.FirstOrDefault(x => x.Id == hx.Id);
            if (exit is null) return Resolution.Nothing;
            return state.AllDone(exit.RequiresDone)
                ? new Resolution.Travel(exit.Id, exit.To)
                : new Resolution.Look(TextKeys.LockedOf(exit), null);
        }

        if (hit is Hit.Floor floor) return new Resolution.Walk(floor.X, floor.Y);
        return Resolution.Nothing;
    }

    /// <summary>
    /// <c>itemActionLabel</c>: the action label for an action resolution, otherwise empty.
    /// With a selected item this is non-empty only for an executable item rule.
    /// </summary>
    public static TextRef ItemActionLabel(Resolution result) =>
        result is Resolution.Action a ? TextKeys.LabelOf(a.ActionDef) : TextRef.Empty;

    /// <summary>
    /// <c>commitAction</c>: one atomic transaction, called after walking and re-resolving the same
    /// action. Validates guards, room and visibility, the puzzle answer (deep equality with the
    /// solution) and the item transaction, then: removes consumes, adds gives, appends the action id
    /// to done, records the journal entry, returns postgame evidence, recomputes side rewards, clears
    /// the selection after an item use (and a consumed selection), applies the special transition, and
    /// queues lines (then cutscene lines).
    /// Nothing depends on the lines or the cutscene being watched. A repeated click or a load can
    /// never duplicate an item, because a done action fails validation.
    /// </summary>
    /// <exception cref="ActionRejectedException">The state is unchanged.</exception>
    public static GameState CommitAction(GameContent content, GameState state, string actionId, JsonNode? answer = null)
    {
        var action = content.FindAction(actionId)
            ?? throw new ActionRejectedException(actionId, ActionRejection.UnknownAction, "Unknown action: " + actionId);
        if (!ValidAction(content, state, action))
            throw new ActionRejectedException(actionId, ActionRejection.NoLongerValid, "Action no longer valid: " + actionId);
        if (action.Puzzle is not null)
        {
            var puzzle = content.FindPuzzle(action.Puzzle);
            if (puzzle is null || !JsonDeep.Equals(answer, puzzle.Solution))
                throw new ActionRejectedException(actionId, ActionRejection.PuzzleNotSolved, "Puzzle not solved; state unchanged: " + action.Puzzle);
        }
        if (!state.HasAll(action.Consumes) || action.Gives.Any(state.Has))
            throw new ActionRejectedException(actionId, ActionRejection.InvalidItemTransaction, "Invalid item transaction: " + actionId);

        var inventory = state.Inventory.Where(x => !action.Consumes.Contains(x)).ToImmutableArray();
        inventory = IdList.AddUnique(inventory, action.Gives);
        var done = state.Done.Add(action.Id);
        if (action.Id == content.Data.Postgame.Unlock) inventory = IdList.AddUnique(inventory, content.Data.Postgame.ReturnItems);

        var next = state with
        {
            Inventory = inventory,
            Done = done,
            JournalSeen = IdList.AddUnique(state.JournalSeen, Journal.ActionEntryKey(action.Id)),
            PuzzleDrafts = action.Puzzle is null ? state.PuzzleDrafts : state.PuzzleDrafts.Remove(action.Puzzle),
        };
        next = next with
        {
            SideRewards = IdList.AddUnique(next.SideRewards,
                content.Quests.Where(q => q.IsSide && next.IsDone(q.Completion)).Select(q => q.Id)),
        };
        // A successful item use clears the cursor item (orchestrator decision after the playtests, PT-F09 / PT-S16);
        // a consumed selection is cleared too. Invalid item clicks never get here: they stay a no-op that keeps it.
        if (next.SelectedItem is not null && (action.SelectedItem is not null || !next.Has(next.SelectedItem))) next = next with { SelectedItem = null };

        var lines = action.Lines.Select(l => l.LineId ?? "").Where(id => id.Length > 0).ToList();
        if (action.Cutscene is not null && content.FindCutscene(action.Cutscene) is { } cutscene)
            lines.AddRange(Playback.CutsceneLineIds(cutscene));

        var transition = content.FindTransition(action.Id);
        if (transition is not null)
        {
            var firstVisit = !next.Visited.Contains(transition.To);
            next = Navigation.EnterRoom(content, next, transition.To);
            if (firstVisit) lines.AddRange(content.GetRoom(transition.To).FirstEntry.Select(l => l.LineId ?? "").Where(id => id.Length > 0));
        }

        // A committed puzzle action closes its modal (GAME-02: no stale open_puzzle after the commit).
        return Playback.Start(content, next with { OpenPuzzleAction = null }, lines);
    }

    /// <summary>Non-throwing variant of <see cref="CommitAction"/> (e.g. for double-click spam).</summary>
    public static CommitResult TryCommitAction(GameContent content, GameState state, string actionId, JsonNode? answer = null)
    {
        try
        {
            return new CommitResult(true, CommitAction(content, state, actionId, answer), null);
        }
        catch (ActionRejectedException ex)
        {
            return new CommitResult(false, state, ex.Reason);
        }
    }

    /// <summary><c>toggleHotspots</c>: toggles the hotspot markers, only in world mode (HUD eye button, QA).</summary>
    public static GameState ToggleHotspots(GameState state) =>
        state.Mode == GameMode.World ? state with { HotspotLabels = !state.HotspotLabels } : state;

    /// <summary>
    /// Hold-to-show hotspot markers (product owner override 2026-10-05, ISSUES INT-08): pressing Space shows them, only
    /// in world mode; releasing Space hides them in every mode (a release must never leave them stuck on).
    /// </summary>
    public static GameState SetHotspots(GameState state, bool shown)
    {
        if (shown) return state.Mode == GameMode.World && !state.HotspotLabels ? state with { HotspotLabels = true } : state;
        return state.HotspotLabels ? state with { HotspotLabels = false } : state;
    }

    /// <summary>
    /// <c>hotspotList</c>: every visible hotspot (NPCs, progress and purely atmospheric props) followed
    /// by every exit of the current room, in data order. Hidden hotspots are never listed.
    /// </summary>
    public static IReadOnlyList<HotspotListEntry> HotspotList(GameContent content, GameState state)
    {
        var room = content.GetRoom(state.Room);
        return room.Hotspots.Where(h => IsVisible(h, state))
            .Select(h => new HotspotListEntry(h.Id, TextKeys.NameOf(h), h.IsNpc ? HotspotListKind.Npc : HotspotListKind.Prop))
            .Concat(room.Exits.Select(e => new HotspotListEntry(e.Id, TextKeys.LabelOf(e), HotspotListKind.Exit)))
            .ToList();
    }

    /// <summary><c>connectedRooms</c>: see <see cref="Navigation.ConnectedRooms"/>.</summary>
    public static IReadOnlySet<string> ConnectedRooms(GameContent content, GameState state, bool includePortals) =>
        Navigation.ConnectedRooms(content, state, includePortals);

    /// <summary><c>canFastTravel</c>: see <see cref="Navigation.CanFastTravel"/>.</summary>
    public static bool CanFastTravel(GameContent content, GameState state, string to) => Navigation.CanFastTravel(content, state, to);

    /// <summary><c>nextMainQuest</c>: see <see cref="Quests.NextMainQuest"/>.</summary>
    public static QuestDef? NextMainQuest(GameContent content, GameState state) => Quests.NextMainQuest(content, state);

    /// <summary><c>validateSave</c>: see <see cref="Save.SaveCodec.ValidateSave"/>.</summary>
    public static GameState ValidateSave(GameContent content, JsonNode? raw) => Save.SaveCodec.ValidateSave(content, raw);

    // ------------------------------------------------------------------ applying resolutions

    /// <summary>Attaches an owned item to the cursor. The drawer closes unless <paramref name="keepInventoryOpen"/> (combine mode).</summary>
    public static GameState SelectItem(GameState state, string itemId, bool keepInventoryOpen = false)
    {
        if (!state.Has(itemId) || state.Mode is not (GameMode.World or GameMode.Inventory)) return state;
        return state with
        {
            SelectedItem = itemId,
            Mode = keepInventoryOpen ? state.Mode : GameMode.World,
        };
    }

    /// <summary>Clears the cursor item and does nothing else.</summary>
    public static GameState CancelSelection(GameState state) => state.SelectedItem is null ? state : state with { SelectedItem = null };

    /// <summary>Opens or closes the inventory drawer (world ⇄ inventory).</summary>
    public static GameState ToggleInventory(GameState state) => state.Mode switch
    {
        GameMode.World => state with { Mode = GameMode.Inventory },
        GameMode.Inventory => state with { Mode = GameMode.World },
        _ => state,
    };

    /// <summary>Opens an overlay mode (map, journal, pause) from world or inventory.</summary>
    public static GameState OpenOverlay(GameState state, GameMode overlay)
    {
        if (overlay is not (GameMode.Map or GameMode.Journal or GameMode.Pause)) throw new ArgumentOutOfRangeException(nameof(overlay));
        return state.Mode is GameMode.World or GameMode.Inventory ? state with { Mode = overlay } : state;
    }

    /// <summary>Closes the topmost overlay (map, journal, pause, inventory, topic menu) back to world.</summary>
    public static GameState CloseOverlay(GameState state) => state.Mode switch
    {
        GameMode.Map or GameMode.Journal or GameMode.Pause or GameMode.Inventory => state with { Mode = GameMode.World },
        GameMode.Dialogue when state.ActiveLineId is null => state with { Mode = GameMode.World },
        _ => state,
    };

    /// <summary>
    /// Escape key: cancels the selection first (accessibility rule), otherwise closes the top panel,
    /// otherwise opens the pause menu from the scene.
    /// </summary>
    public static GameState Escape(GameState state)
    {
        if (state.SelectedItem is not null && state.Mode is GameMode.World or GameMode.Inventory) return CancelSelection(state);
        if (state.Mode == GameMode.World) return state with { Mode = GameMode.Pause };
        return CloseOverlay(state);
    }

    /// <summary>
    /// The state a loaded save resumes in: pause, map and journal close to the scene (a save taken from an
    /// overlay never reopens it, ISSUES UI-05); puzzle mode keeps its modal only when the saved
    /// <c>open_puzzle</c> action is still valid (<see cref="Puzzles.OpenAction"/>, ISSUES GAME-02), otherwise the
    /// modal closes and its draft is kept. Every other mode is unchanged.
    /// </summary>
    public static GameState ResumeAfterLoad(GameContent content, GameState state) => state.Mode switch
    {
        GameMode.Pause or GameMode.Map or GameMode.Journal => state with { Mode = GameMode.World },
        GameMode.Puzzle when Puzzles.OpenAction(content, state) is null => Puzzles.Close(state),
        _ => state,
    };

    /// <summary>All actions that are valid right now (debug panel; never shown to players).</summary>
    public static IReadOnlyList<ActionDef> AvailableActions(GameContent content, GameState state) =>
        content.Actions.Where(a => ValidAction(content, state, a)).ToList();
}

/// <summary>Kind of an entry in <see cref="GameRules.HotspotList"/>.</summary>
public enum HotspotListKind
{
    /// <summary>NPC hotspot.</summary>
    Npc,
    /// <summary>Prop hotspot (progress or atmospheric).</summary>
    Prop,
    /// <summary>Exit zone.</summary>
    Exit,
}

/// <summary>Entry of <see cref="GameRules.HotspotList"/>.</summary>
/// <param name="Id">Hotspot or exit id.</param>
/// <param name="Name">Label to show.</param>
/// <param name="Kind">Entry kind.</param>
public sealed record HotspotListEntry(string Id, TextRef Name, HotspotListKind Kind);
