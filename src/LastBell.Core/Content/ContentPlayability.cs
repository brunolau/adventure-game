using LastBell.Core.Rules;
using LastBell.Core.State;

namespace LastBell.Core.Content;

/// <summary>
/// The softlock check of loaded content: plays the whole game (main story, ending and every side quest) through the
/// real rules in several orders and reports any order that gets stuck. A step is any action whose guards pass, whose
/// room is reachable over the open exits and portals (the hero is then put into that room, as if he had walked there)
/// and whose target is visible; puzzle actions are committed with their solution. An order is stuck when no step is
/// possible but an action is neither done nor excluded by a done action: a player following that order could never
/// finish. <see cref="GameContent.Load(string, ContentOverlays?)"/> runs it whenever the world overlay adds or moves
/// anything; the tests also run it on the handoff.
/// </summary>
public static class ContentPlayability
{
    /// <summary>The orders tried: data order, side quests first, overlay additions first / last, and seeded random orders.</summary>
    public static IReadOnlyList<string> Strategies(int randomOrders) =>
        new[] { "data order", "side quests first", "world overlay first", "world overlay last" }
            .Concat(Enumerable.Range(1, randomOrders).Select(n => $"random order {n}")).ToList();

    /// <summary>Runs every strategy; returns the errors (<c>$playability(&lt;strategy&gt;): ...</c>), empty when the game can always be finished.</summary>
    public static IReadOnlyList<string> Check(GameContent content, int randomOrders = 4)
    {
        // Orders that get stuck the same way are reported once ("$playability(data order, random order 2): ...").
        var stuck = new List<(string Strategy, string Error)>();
        foreach (var strategy in Strategies(randomOrders))
        {
            var error = Play(content, strategy, out _);
            if (error is not null) stuck.Add((strategy, error));
        }
        static string What(string error) => error.Contains(NeverDone, StringComparison.Ordinal) ? error[error.IndexOf(NeverDone, StringComparison.Ordinal)..] : error;
        return stuck.GroupBy(x => What(x.Error), StringComparer.Ordinal)
            .Select(g => $"$playability({string.Join(", ", g.Select(x => x.Strategy))}): {g.First().Error}").ToList();
    }

    /// <summary>Plays one order to the end. Returns null when every action is done or excluded, else what got stuck.</summary>
    /// <param name="content">The content.</param>
    /// <param name="strategy">One of <see cref="Strategies"/>.</param>
    /// <param name="order">The actions in the order they were done.</param>
    public static string? Play(GameContent content, string strategy, out IReadOnlyList<string> order)
    {
        var world = new HashSet<string>(content.Overlay.AddedActions.Concat(content.Overlay.Relocations.Select(r => r.Action)), StringComparer.Ordinal);
        var random = strategy.StartsWith("random order ", StringComparison.Ordinal)
            ? new Random(int.Parse(strategy["random order ".Length..], System.Globalization.CultureInfo.InvariantCulture) * 7919)
            : null;
        int Rank(ActionDef a) => strategy switch
        {
            "side quests first" => a.IsMain ? 1 : 0,
            "world overlay first" => world.Contains(a.Id) ? 0 : 1,
            "world overlay last" => world.Contains(a.Id) ? 1 : 0,
            _ => 0,
        };

        var done = new List<string>();
        order = done;
        var s = Playback.FinishAll(content, Navigation.BeginNewGame(content, content.InitialState));
        for (var guard = 0; guard < content.Actions.Count + 1; guard++)
        {
            var reachable = Navigation.ConnectedRooms(content, s, includePortals: true);
            var enabled = content.Actions.Where(a => Possible(content, s, a, reachable)).ToList();
            if (enabled.Count == 0) break;
            var next = random is not null ? enabled[random.Next(enabled.Count)] : enabled.OrderBy(Rank).First();
            try
            {
                s = Perform(content, s, next);
            }
            catch (ActionRejectedException ex)
            {
                return $"after {string.Join(" ", done)}: '{next.Id}' looked possible but was rejected ({ex.Message})";
            }
            done.Add(next.Id);
        }

        var stuck = content.Actions.Where(a => !s.IsDone(a.Id) && !s.AnyDone(a.ExcludedDone)).ToList();
        if (stuck.Count == 0) return null;
        var reachableAtEnd = Navigation.ConnectedRooms(content, s, includePortals: true);
        var why = stuck.Take(6).Select(a => $"{a.Id} ({Reason(content, s, a, reachableAtEnd)})");
        return $"softlock after {done.Count} actions (last: {string.Join(" ", done.TakeLast(5))}): " +
               $"{stuck.Count} action(s){NeverDone}{string.Join("; ", why)}{(stuck.Count > 6 ? "; ..." : "")}";
    }

    private const string NeverDone = " can never be done: ";

    private static bool Possible(GameContent content, GameState s, ActionDef a, IReadOnlySet<string> reachable)
    {
        if (!GameRules.GuardsPass(a, s) || !s.HasAll(a.Consumes)) return false;
        if (a.Gives.Any(s.Has)) return false;
        if (a.SelectedItem is not null && !s.Has(a.SelectedItem)) return false;
        if (a.IsInventoryAction) return !a.IsCombine || s.Has(a.Target);
        if (!reachable.Contains(a.Room)) return false;
        var target = content.FindHotspot(a.Target);
        return target is not null && target.Room.Id == a.Room && GameRules.IsVisible(target.Hotspot, s);
    }

    private static GameState Perform(GameContent content, GameState s, ActionDef a)
    {
        if (!a.IsInventoryAction && s.Room != a.Room) s = Navigation.EnterRoom(content, s, a.Room);
        s = s with { Mode = GameMode.World, SelectedItem = a.SelectedItem };
        var answer = a.Puzzle is null ? null : content.GetPuzzle(a.Puzzle).Solution?.DeepClone();
        s = GameRules.CommitAction(content, s, a.Id, answer);
        s = Playback.FinishAll(content, s);
        return GameRules.CancelSelection(s) with { Mode = GameMode.World };
    }

    private static string Reason(GameContent content, GameState s, ActionDef a, IReadOnlySet<string> reachable)
    {
        var missing = a.RequiresDone.Where(r => !s.IsDone(r)).ToList();
        if (missing.Count > 0) return "waits for " + string.Join(", ", missing);
        var items = a.RequiresItems.Where(i => !s.Has(i)).ToList();
        if (items.Count > 0) return "item " + string.Join(", ", items) + " is gone or never obtained";
        if (!a.IsInventoryAction && !reachable.Contains(a.Room)) return $"room {a.Room} cannot be reached";
        if (!a.IsInventoryAction && content.FindHotspot(a.Target) is { } h && !GameRules.IsVisible(h.Hotspot, s)) return $"target {a.Target} is hidden";
        return "not possible";
    }
}
