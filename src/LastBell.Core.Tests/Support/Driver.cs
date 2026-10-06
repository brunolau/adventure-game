using System.Text.Json.Nodes;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;

namespace LastBell.Core.Tests.Support;

/// <summary>
/// Plays the game through the public API exactly like the presentation layer would: travel through
/// exits/portals, resolve the click with the shared resolver (selecting items from the inventory
/// first), open puzzles, commit, and play the lines to the end. No item is ever granted directly.
/// </summary>
public static class Driver
{
    /// <summary>
    /// Follows an explicit list of rooms (walkthrough travel_path): exits first, else a portal. A hop that the travel
    /// overlay removed (e.g. the 2020 car S02 -> S51, now the bus from S07) is recomputed: the shortest legal route
    /// under the overlay replaces it (walkthrough.json itself is never edited).
    /// </summary>
    public static GameState FollowTravelPath(GameContent content, GameState s, IReadOnlyList<string> path)
    {
        foreach (var roomId in path)
        {
            if (roomId == s.Room) continue; // a recomputed hop may already have passed through this room
            var exit = content.GetRoom(s.Room).Exits.FirstOrDefault(e => e.To == roomId && s.AllDone(e.RequiresDone));
            GameState next;
            if (exit is not null)
            {
                Assert.IsType<Resolution.Travel>(GameRules.ResolveInteraction(content, s, new Hit.Exit(exit.Id), PointerButton.Left));
                next = Navigation.Travel(content, s, exit.Id);
            }
            else if (Navigation.PortalTargets(content, s).Any(p => p.Anchor == roomId))
            {
                next = Navigation.UsePortal(content, s, content.GetRoom(roomId).Era);
            }
            else
            {
                Assert.True(content.Overlay.RemovedConnections.Any(c => (c.From == s.Room && c.To == roomId) || (c.To == s.Room && c.From == roomId)),
                    $"No exit or portal from {s.Room} to {roomId}");
                s = TravelTo(content, s, roomId); // recomputed under the travel overlay
                continue;
            }
            Assert.Equal(roomId, next.Room);
            s = Playback.FinishAll(content, next);
            Assert.Equal(GameMode.World, s.Mode);
        }
        return s;
    }

    /// <summary>Travels to a room over the shortest legal route.</summary>
    public static GameState TravelTo(GameContent content, GameState s, string roomId)
    {
        var route = Navigation.FindRoute(content, s, roomId);
        Assert.True(route is not null, $"No route from {s.Room} to {roomId}");
        foreach (var step in route!)
        {
            s = Navigation.ApplyStep(content, s, step);
            Assert.Equal(step.To, s.Room);
            s = Playback.FinishAll(content, s);
        }
        return s;
    }

    /// <summary>Travels to the action's room and performs it.</summary>
    public static GameState Perform(GameContent content, GameState s, ActionDef action)
    {
        if (!action.IsInventoryAction) s = TravelTo(content, s, action.Room);
        var solution = action.Puzzle is null ? null : content.GetPuzzle(action.Puzzle).Solution?.DeepClone();
        return Interact(content, s, action, solution);
    }

    /// <summary>Performs an action in the current room through the resolver and commits it.</summary>
    public static GameState Interact(GameContent content, GameState s, ActionDef action, JsonNode? solution)
    {
        Assert.Equal(GameMode.World, s.Mode);
        Assert.Null(s.SelectedItem);
        if (action.SelectedItem is not null)
        {
            s = GameRules.ToggleInventory(s);
            Assert.Equal(GameMode.Inventory, s.Mode);
            var pick = GameRules.ResolveInteraction(content, s, new Hit.Item(action.SelectedItem), PointerButton.Left);
            Assert.Equal(new Resolution.SelectItem(action.SelectedItem), pick);
            s = GameRules.SelectItem(s, action.SelectedItem, keepInventoryOpen: action.IsCombine);
        }

        Hit hit = action.IsCombine ? new Hit.Item(action.Target) : new Hit.Hotspot(action.Target);
        var resolution = GameRules.ResolveInteraction(content, s, hit, PointerButton.Left);
        if (action.IsTopic)
        {
            var dialogue = Assert.IsType<Resolution.Dialogue>(resolution);
            Assert.Contains(dialogue.Topics, t => t.Id == action.Id && t.IsStoryAction);
            s = Dialogue.OpenMenu(s);
        }
        else
        {
            var act = Assert.IsType<Resolution.Action>(resolution);
            Assert.Equal(action.Id, act.ActionDef.Id);
            Assert.Equal(action.Label, GameRules.ItemActionLabel(resolution).Fallback);
            // Re-resolve "after walking": the same resolution must still hold.
            Assert.Equal(resolution, GameRules.ResolveInteraction(content, s, hit, PointerButton.Left));
        }

        if (action.Puzzle is not null)
        {
            s = Puzzles.Open(content, s, action.Id);
            Assert.Equal(GameMode.Puzzle, s.Mode);
            var result = Puzzles.Submit(content, s, action.Id, solution);
            Assert.True(result.Solved, $"Puzzle {action.Puzzle} not solved by {solution?.ToJsonString()}");
            s = result.State;
        }
        else
        {
            s = GameRules.CommitAction(content, s, action.Id);
        }
        Assert.True(s.IsDone(action.Id));
        s = Playback.FinishAll(content, s);
        s = GameRules.CancelSelection(s);
        Assert.Equal(GameMode.World, s.Mode);
        return s;
    }

    /// <summary>Actions the validator would consider enabled: guards, visible target, reachable room.</summary>
    public static IReadOnlyList<ActionDef> Enabled(GameContent content, GameState s)
    {
        var reachable = Navigation.ConnectedRooms(content, s, includePortals: true);
        return content.Actions.Where(a =>
        {
            if (!GameRules.GuardsPass(a, s)) return false;
            if (!a.IsInventoryAction && !reachable.Contains(a.Room)) return false;
            var target = content.FindHotspot(a.Target);
            return target is null || GameRules.IsVisible(target.Hotspot, s);
        }).ToList();
    }

    /// <summary>Asserts invariants that must hold in every reachable state.</summary>
    public static void AssertInvariants(GameContent content, GameState s)
    {
        Assert.Equal(s.Inventory.Length, s.Inventory.Distinct().Count());
        Assert.Equal(s.Done.Length, s.Done.Distinct().Count());
        Assert.True(TemporalCache.InvariantHolds(content, s), "temporal cache lineage duplicated");
        Assert.Equal(content.GetRoom(s.Room).Era, s.Era);
        // Unambiguous default click in the current state (validator check).
        var active = content.Actions.Where(a => a.IsClick && a.SelectedItem is null && GameRules.GuardsPass(a, s) &&
            content.FindHotspot(a.Target) is { } h && GameRules.IsVisible(h.Hotspot, s)).Select(a => (a.Room, a.Target)).ToList();
        Assert.Equal(active.Count, active.Distinct().Count());
    }
}
