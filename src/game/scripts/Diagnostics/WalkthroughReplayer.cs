using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;

namespace LastBell.Game.Diagnostics;

/// <summary>One main_route row of walkthrough.json.</summary>
/// <param name="Step">1-based step.</param>
/// <param name="Action">Action id.</param>
/// <param name="TravelPath">Rooms to walk through first.</param>
/// <param name="Target">Target hotspot or item.</param>
/// <param name="Select">Item to select first, or null.</param>
/// <param name="PuzzleSolution">Puzzle answer, or null.</param>
/// <param name="InventoryAfter">Expected inventory (sorted ids).</param>
/// <param name="RoomAfter">Expected room.</param>
public sealed record WalkthroughStep(int Step, string Action, IReadOnlyList<string> TravelPath, string Target, string? Select,
    JsonNode? PuzzleSolution, IReadOnlyList<string> InventoryAfter, string RoomAfter);

/// <summary>
/// Replays the first n steps of <c>res://data/debug/walkthrough.json</c> (a copy of
/// design-doc/walkthrough.json) through Core exactly like the presentation would: exits/portals,
/// item selection from the drawer, the shared resolver, puzzles with their solution, commit, and
/// playback to the end. No item is ever granted directly. Throws on any mismatch.
/// </summary>
public static class WalkthroughReplayer
{
    /// <summary>Path of the walkthrough copy.</summary>
    public const string Path = "res://data/debug/walkthrough.json";

    /// <summary>Loads the main route.</summary>
    public static IReadOnlyList<WalkthroughStep> LoadMainRoute()
    {
        var root = JsonNode.Parse(Godot.FileAccess.GetFileAsString(Path))!;
        return root["main_route"]!.AsArray().Select(n => new WalkthroughStep(
            n!["step"]!.GetValue<int>(),
            n["action"]!.GetValue<string>(),
            n["travel_path"]!.AsArray().Select(x => x!.GetValue<string>()).ToList(),
            n["target"]?.GetValue<string>() ?? "",
            n["select"]?.GetValue<string>(),
            n["puzzle_solution"]?.DeepClone(),
            n["inventory_after"]!.AsArray().Select(x => x!.GetValue<string>()).ToList(),
            n["room_after"]!.GetValue<string>())).ToList();
    }

    /// <summary>Replays steps 1..<paramref name="count"/> from <paramref name="start"/>.</summary>
    public static GameState Replay(GameContent content, GameState start, int count, Action<string>? log = null)
    {
        var steps = LoadMainRoute();
        var s = start;
        foreach (var step in steps.Take(Math.Clamp(count, 0, steps.Count)))
        {
            s = FollowTravelPath(content, s, step);
            // The world overlay may have relocated the step's action to another room of the same era.
            var action = content.GetAction(step.Action);
            if (!action.IsInventoryAction && s.Room != action.Room) s = Walk(content, s, action.Room, step);
            s = Interact(content, s, step);
            var inventory = s.Inventory.OrderBy(x => x, StringComparer.Ordinal).ToList();
            var expected = step.InventoryAfter.OrderBy(x => x, StringComparer.Ordinal).ToList();
            if (!inventory.SequenceEqual(expected))
                throw new InvalidOperationException($"step {step.Step} {step.Action}: inventory [{string.Join(",", inventory)}] != expected [{string.Join(",", expected)}]");
            var roomAfter = content.FindRelocation(step.Action) is { } moved && step.RoomAfter == moved.FromRoom ? moved.ToRoom : step.RoomAfter;
            if (s.Room != roomAfter)
                throw new InvalidOperationException($"step {step.Step} {step.Action}: room {s.Room} != expected {roomAfter}");
            log?.Invoke($"replay step {step.Step,2} {step.Action,-4} ok -> {s.Room} [{string.Join(",", s.Inventory)}]");
        }
        return s;
    }

    private static GameState FollowTravelPath(GameContent content, GameState s, WalkthroughStep step)
    {
        foreach (var roomId in step.TravelPath)
        {
            if (roomId == s.Room) continue; // a recomputed hop may already have passed through this room
            var exit = content.GetRoom(s.Room).Exits.FirstOrDefault(e => e.To == roomId && s.AllDone(e.RequiresDone));
            GameState next;
            if (exit is not null)
            {
                if (GameRules.ResolveInteraction(content, s, new Hit.Exit(exit.Id), PointerButton.Left) is not Resolution.Travel)
                    throw new InvalidOperationException($"step {step.Step}: exit {exit.Id} does not resolve to travel");
                next = Navigation.Travel(content, s, exit.Id);
            }
            else if (Navigation.PortalTargets(content, s).Any(p => p.Anchor == roomId))
            {
                next = Navigation.UsePortal(content, s, content.GetRoom(roomId).Era);
            }
            else
            {
                // A hop the travel overlay removed (2020: the car S02 -> S51 became the bus from S07), or a path that
                // starts where walkthrough.json expects the hero although a relocated action took him elsewhere: recompute it.
                string from = s.Room;
                if (!content.Overlay.RemovedConnections.Any(c => (c.From == from && c.To == roomId) || (c.To == from && c.From == roomId)) &&
                    content.Overlay.Relocations.Count == 0)
                    throw new InvalidOperationException($"step {step.Step}: no exit or portal from {s.Room} to {roomId}");
                s = Walk(content, s, roomId, step);
                continue;
            }
            if (next.Room != roomId) throw new InvalidOperationException($"step {step.Step}: travel to {roomId} failed");
            s = Playback.FinishAll(content, next);
        }
        return s;
    }

    private static GameState Walk(GameContent content, GameState s, string roomId, WalkthroughStep step)
    {
        var route = Navigation.FindRoute(content, s, roomId) ?? throw new InvalidOperationException($"step {step.Step}: no route from {s.Room} to {roomId}");
        foreach (var hop in route) s = Playback.FinishAll(content, Navigation.ApplyStep(content, s, hop));
        if (s.Room != roomId) throw new InvalidOperationException($"step {step.Step}: travel to {roomId} failed");
        return s;
    }

    private static GameState Interact(GameContent content, GameState s, WalkthroughStep step)
    {
        var action = content.GetAction(step.Action);
        if (action.SelectedItem is not null)
        {
            s = GameRules.ToggleInventory(s);
            if (GameRules.ResolveInteraction(content, s, new Hit.Item(action.SelectedItem), PointerButton.Left) is not Resolution.SelectItem)
                throw new InvalidOperationException($"step {step.Step}: cannot select {action.SelectedItem}");
            s = GameRules.SelectItem(s, action.SelectedItem, keepInventoryOpen: action.IsCombine);
        }
        Hit hit = action.IsCombine ? new Hit.Item(action.Target) : new Hit.Hotspot(action.Target);
        var resolution = GameRules.ResolveInteraction(content, s, hit, PointerButton.Left);
        if (action.IsTopic)
        {
            if (resolution is not Resolution.Dialogue d || !d.Topics.Any(t => t.Id == action.Id))
                throw new InvalidOperationException($"step {step.Step}: topic {action.Id} not offered");
            s = Dialogue.OpenMenu(s);
        }
        else if (resolution is not Resolution.Action a || a.ActionDef.Id != action.Id)
            throw new InvalidOperationException($"step {step.Step}: {hit} resolves to {resolution.GetType().Name}, not {action.Id}");

        if (action.Puzzle is not null)
        {
            s = Puzzles.Open(content, s, action.Id);
            var answer = step.PuzzleSolution ?? content.GetPuzzle(action.Puzzle).Solution?.DeepClone();
            var result = Puzzles.Submit(content, s, action.Id, answer);
            if (!result.Solved) throw new InvalidOperationException($"step {step.Step}: puzzle {action.Puzzle} not solved");
            s = result.State;
        }
        else s = GameRules.CommitAction(content, s, action.Id);
        s = Playback.FinishAll(content, s);
        return GameRules.CancelSelection(s);
    }
}
