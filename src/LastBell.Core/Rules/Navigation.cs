using LastBell.Core.Content;
using LastBell.Core.State;
using LastBell.Core.Text;

namespace LastBell.Core.Rules;

/// <summary>Kind of a route step.</summary>
public enum RouteStepKind
{
    /// <summary>Walk through an exit (one side of a connection).</summary>
    Exit,
    /// <summary>Chronometer portal from an anchor node to an era anchor.</summary>
    Portal,
}

/// <summary>One hop of a route.</summary>
/// <param name="Kind">Exit or portal.</param>
/// <param name="From">Room left.</param>
/// <param name="To">Room entered.</param>
/// <param name="ExitId">Exit id for <see cref="RouteStepKind.Exit"/>.</param>
/// <param name="Year">Target year for <see cref="RouteStepKind.Portal"/>.</param>
public sealed record RouteStep(RouteStepKind Kind, string From, string To, string? ExitId, int? Year);

/// <summary>A portal destination offered at an anchor node.</summary>
/// <param name="Year">Target era.</param>
/// <param name="Anchor">Arrival room.</param>
/// <param name="Date">Era date text.</param>
/// <param name="Card">Era title card text.</param>
public sealed record PortalTarget(int Year, string Anchor, TextRef Date, TextRef Card);

/// <summary>
/// Room graph, exits, chronometer portals, era unlocks and map fast travel (travel_contract).
/// Gates are evaluated on every edge; the map can never bypass a locked door.
/// </summary>
public static class Navigation
{
    /// <summary>True when the era is unlocked (<c>unlocked_by</c> null or done).</summary>
    public static bool IsEraUnlocked(GameContent content, GameState state, int year)
    {
        var era = content.FindEra(year);
        return era is not null && (era.UnlockedBy is null || state.IsDone(era.UnlockedBy));
    }

    /// <summary>All unlocked eras in data order.</summary>
    public static IReadOnlyList<EraDef> UnlockedEras(GameContent content, GameState state) =>
        content.Eras.Where(e => e.UnlockedBy is null || state.IsDone(e.UnlockedBy)).ToList();

    /// <summary>
    /// <c>connectedRooms</c>: rooms reachable from the current room over connections whose gates are
    /// open, optionally including chronometer portals (CHRONO owned, source anchor node open, target
    /// era unlocked and different from the source year). Includes the current room.
    /// </summary>
    public static IReadOnlySet<string> ConnectedRooms(GameContent content, GameState state, bool includePortals)
    {
        var graph = BuildGraph(content, state, includePortals);
        var seen = new HashSet<string>(StringComparer.Ordinal) { state.Room };
        var todo = new Queue<string>();
        todo.Enqueue(state.Room);
        while (todo.Count > 0)
        {
            var from = todo.Dequeue();
            if (!graph.TryGetValue(from, out var edges)) continue;
            foreach (var step in edges)
                if (seen.Add(step.To)) todo.Enqueue(step.To);
        }
        return seen;
    }

    /// <summary>
    /// <c>canFastTravel</c>: only from the map, only to a visited room of the current era that is
    /// currently reachable over open same-era connections (no portals). Any such room is one click away,
    /// in any map region (owner override 2026-10-06, DECISIONS "Control changes" item 8: direct fast travel
    /// to every discovered place, no stop at the region's hub). The first trip into a region still happens
    /// physically (bus, tram, cable car), because its rooms are not visited before. A locked gate on every
    /// route keeps the room unavailable.
    /// </summary>
    public static bool CanFastTravel(GameContent content, GameState state, string to) =>
        state.Mode == GameMode.Map && state.Visited.Contains(to) && content.FindRoom(to)?.Era == state.Era &&
        ConnectedRooms(content, state, includePortals: false).Contains(to);

    /// <summary>
    /// The transport used between two rooms of the same era that lie in different map regions: the travel style
    /// (<c>bus</c>, <c>tram</c>, <c>cable_A6</c>, ...) of the first connection on the shortest open route that
    /// leaves the region of <paramref name="from"/>. Null when both rooms are in the same region, in different
    /// eras, or no open route exists. The presentation uses it for the transport card of a map fast travel.
    /// </summary>
    public static string? TransportBetween(GameContent content, GameState state, string from, string to)
    {
        var a = content.FindRoom(from);
        var b = content.FindRoom(to);
        if (a is null || b is null || a.Era != b.Era || ReferenceEquals(content.RegionOf(from), content.RegionOf(to))) return null;
        var route = Route(content, state, from, to, includePortals: false);
        if (route is null) return null;
        var region = content.RegionOf(from);
        foreach (var step in route)
        {
            if (ReferenceEquals(content.RegionOf(step.To), region)) continue;
            var c = content.Data.Connections.FirstOrDefault(x => (x.From == step.From && x.To == step.To) || (x.Bidirectional && x.From == step.To && x.To == step.From));
            return c?.Travel ?? content.FindExit(step.ExitId ?? "")?.Exit.Travel;
        }
        return null;
    }

    /// <summary>Journal marker of a first ride through a transport exit (its first-ride lines played).</summary>
    public static string FirstRideKey(string exitId) => "travel." + exitId + ".first";

    /// <summary>Fast travel from the map; returns the state unchanged when it is not allowed.</summary>
    public static GameState FastTravel(GameContent content, GameState state, string to)
    {
        if (!CanFastTravel(content, state, to) || to == state.Room) return state.Mode == GameMode.Map && to == state.Room ? state with { Mode = GameMode.World } : state;
        return EnterRoomWithEntryLines(content, state with { Mode = GameMode.World }, to);
    }

    /// <summary>
    /// Travels through an exit of the current room (after the hero arrived at it; the gate is
    /// re-checked). First visits queue the room's first-entry lines. The first use of a transport exit
    /// with first-ride lines (travel overlay) queues those lines before them and records
    /// <see cref="FirstRideKey"/>; the presentation plays them in the room being left, then runs the ride.
    /// Returns the state unchanged when the exit is unknown, locked, or the mode does not accept world input.
    /// </summary>
    public static GameState Travel(GameContent content, GameState state, string exitId)
    {
        if (state.Mode != GameMode.World) return state;
        var exit = content.GetRoom(state.Room).Exits.FirstOrDefault(e => e.Id == exitId);
        if (exit is null || !state.AllDone(exit.RequiresDone)) return state;
        var next = EnterRoomWithEntryLines(content, state, exit.To);
        var ride = content.FirstRideLines(exit.Id);
        if (ride.Count == 0 || state.JournalSeen.Contains(FirstRideKey(exit.Id))) return next;
        var queue = ride.Select(l => l.LineId ?? "").Where(id => id.Length > 0).ToList();
        if (next.ActiveLineId is not null) queue.Add(next.ActiveLineId);
        queue.AddRange(next.PlaybackQueue);
        return Playback.Start(content, next with { JournalSeen = IdList.AddUnique(next.JournalSeen, FirstRideKey(exit.Id)) }, queue);
    }

    /// <summary>Portal destinations available in the current room (empty when it is not an open anchor node or CHRONO is missing).</summary>
    public static IReadOnlyList<PortalTarget> PortalTargets(GameContent content, GameState state)
    {
        if (!state.Has(GameContent.ChronometerItem)) return Array.Empty<PortalTarget>();
        var sources = content.Data.AnchorNodes.Where(n => n.Room == state.Room && state.AllDone(n.RequiresDone)).ToList();
        if (sources.Count == 0) return Array.Empty<PortalTarget>();
        return content.Eras
            .Where(e => sources.Any(s => s.Year != e.Year) && (e.UnlockedBy is null || state.IsDone(e.UnlockedBy)))
            .Select(e => new PortalTarget(e.Year, e.Anchor, TextKeys.DateOf(e), TextKeys.CardOf(e)))
            .ToList();
    }

    /// <summary>Uses the chronometer at an anchor node to jump to an unlocked era's anchor. Free and always reversible.</summary>
    public static GameState UsePortal(GameContent content, GameState state, int year)
    {
        if (state.Mode is not (GameMode.World or GameMode.Map)) return state;
        var target = PortalTargets(content, state).FirstOrDefault(t => t.Year == year);
        if (target is null) return state;
        return EnterRoomWithEntryLines(content, state with { Mode = GameMode.World }, target.Anchor);
    }

    /// <summary>
    /// Shortest route (fewest hops) from the current room to a target room over open connections and
    /// portals, or null when unreachable. An empty list means "already there" (or an inventory action).
    /// </summary>
    public static IReadOnlyList<RouteStep>? FindRoute(GameContent content, GameState state, string targetRoom) =>
        targetRoom == GameContent.InventoryRoom ? Array.Empty<RouteStep>() : Route(content, state, state.Room, targetRoom, includePortals: true);

    private static IReadOnlyList<RouteStep>? Route(GameContent content, GameState state, string from, string targetRoom, bool includePortals)
    {
        if (targetRoom == from) return Array.Empty<RouteStep>();
        var graph = BuildGraph(content, state, includePortals);
        var previous = new Dictionary<string, RouteStep?>(StringComparer.Ordinal) { [from] = null };
        var queue = new Queue<string>();
        queue.Enqueue(from);
        while (queue.Count > 0)
        {
            var room = queue.Dequeue();
            if (room == targetRoom)
            {
                var route = new List<RouteStep>();
                for (var step = previous[room]; step is not null; step = previous[step.From]) route.Add(step);
                route.Reverse();
                return route;
            }
            if (!graph.TryGetValue(room, out var edges)) continue;
            foreach (var step in edges)
            {
                if (previous.ContainsKey(step.To)) continue;
                previous[step.To] = step;
                queue.Enqueue(step.To);
            }
        }
        return null;
    }

    /// <summary>Applies a route step (exit travel or portal). First-entry lines it queues must be played or skipped before the next step.</summary>
    public static GameState ApplyStep(GameContent content, GameState state, RouteStep step) => step.Kind == RouteStepKind.Exit
        ? Travel(content, state, step.ExitId!)
        : UsePortal(content, state, step.Year!.Value);

    /// <summary>
    /// Starts a new game presentation-side: queues the first-entry lines of the start room. The
    /// initial state already lists the start room as visited, so <see cref="Travel"/> never queues
    /// them (ISSUES.md GAME-01). Only acts on a state with no done action, no line playing and world
    /// mode; otherwise returns the same instance. Changes no rules state besides the playback cursor.
    /// </summary>
    public static GameState BeginNewGame(GameContent content, GameState state)
    {
        if (!state.Done.IsEmpty || state.ActiveLineId is not null || state.Mode != GameMode.World) return state;
        var lines = content.GetRoom(state.Room).FirstEntry.Select(l => l.LineId ?? "").Where(id => id.Length > 0).ToList();
        return lines.Count == 0 ? state : Playback.Start(content, state, lines);
    }

    /// <summary>
    /// Moves the hero into a room: sets room and era, marks it visited and records the entry marker
    /// used for deferred causal effects. Does not queue lines.
    /// </summary>
    internal static GameState EnterRoom(GameContent content, GameState state, string roomId)
    {
        var room = content.GetRoom(roomId);
        return state with
        {
            Room = room.Id,
            Era = room.Era,
            Visited = IdList.AddUnique(state.Visited, room.Id),
            RoomEntryDoneCount = state.Done.Length,
        };
    }

    private static GameState EnterRoomWithEntryLines(GameContent content, GameState state, string roomId)
    {
        var firstVisit = !state.Visited.Contains(roomId);
        var next = EnterRoom(content, state, roomId);
        if (!firstVisit) return next;
        var lines = content.GetRoom(roomId).FirstEntry.Select(l => l.LineId ?? "").Where(id => id.Length > 0).ToList();
        return lines.Count == 0 ? next : Playback.Start(content, next, lines);
    }

    private static Dictionary<string, List<RouteStep>> BuildGraph(GameContent content, GameState state, bool includePortals)
    {
        var graph = new Dictionary<string, List<RouteStep>>(StringComparer.Ordinal);
        void Edge(RouteStep step)
        {
            if (!graph.TryGetValue(step.From, out var list)) graph[step.From] = list = new List<RouteStep>();
            list.Add(step);
        }
        foreach (var c in content.Data.Connections)
        {
            if (!state.AllDone(c.RequiresDone)) continue;
            Edge(new RouteStep(RouteStepKind.Exit, c.From, c.To, ExitIdFor(content, c.From, c.To), null));
            if (c.Bidirectional) Edge(new RouteStep(RouteStepKind.Exit, c.To, c.From, ExitIdFor(content, c.To, c.From), null));
        }
        if (includePortals && state.Has(GameContent.ChronometerItem))
        {
            foreach (var source in content.Data.AnchorNodes)
            {
                if (!state.AllDone(source.RequiresDone)) continue;
                foreach (var era in content.Eras)
                {
                    if (era.Year != source.Year && (era.UnlockedBy is null || state.IsDone(era.UnlockedBy)))
                        Edge(new RouteStep(RouteStepKind.Portal, source.Room, era.Anchor, null, era.Year));
                }
            }
        }
        return graph;
    }

    private static string? ExitIdFor(GameContent content, string from, string to) =>
        content.FindRoom(from)?.Exits.FirstOrDefault(e => e.To == to)?.Id;
}
