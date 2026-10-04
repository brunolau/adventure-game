using System.Text.Json.Nodes;
using LastBell.Core.Content;
using LastBell.Core.State;

namespace LastBell.Core.Tests.Support;

/// <summary>One row of walkthrough.json main_route.</summary>
public sealed record WalkthroughStep(int Step, string Quest, string Action, IReadOnlyList<string> TravelPath, string Target,
    string? Select, JsonNode? PuzzleSolution, IReadOnlyList<string> InventoryAfter, string RoomAfter);

/// <summary>Shared fixtures: the canonical handoff files copied next to the test binaries.</summary>
public static class TestData
{
    private static readonly Lazy<string> GameJsonText = new(() => File.ReadAllText(FixturePath("game.json")));
    private static readonly Lazy<GameContent> LazyContent = new(() => GameContent.Load(GameJsonText.Value));
    private static readonly Lazy<(IReadOnlyList<WalkthroughStep> Main, IReadOnlyList<string> Optional)> LazyWalkthrough = new(LoadWalkthrough);
    private static readonly Lazy<IReadOnlyList<GameState>> LazyMainStates = new(BuildMainStates);

    /// <summary>Loaded content (shared, immutable).</summary>
    public static GameContent Content => LazyContent.Value;

    /// <summary>Raw game.json text.</summary>
    public static string GameJson => GameJsonText.Value;

    /// <summary>Main route rows.</summary>
    public static IReadOnlyList<WalkthroughStep> MainRoute => LazyWalkthrough.Value.Main;

    /// <summary>Postgame optional route (side quest action ids).</summary>
    public static IReadOnlyList<string> OptionalRoute => LazyWalkthrough.Value.Optional;

    /// <summary>
    /// States after each main route step, produced through the public API (index 0 = initial state,
    /// index i = after step i).
    /// </summary>
    public static IReadOnlyList<GameState> MainStates => LazyMainStates.Value;

    /// <summary>Absolute path of a fixture file.</summary>
    public static string FixturePath(string name) => Path.Combine(AppContext.BaseDirectory, "fixtures", name);

    /// <summary>State right before a main route action (through the public API).</summary>
    public static GameState StateBefore(string actionId)
    {
        var index = MainRoute.ToList().FindIndex(r => r.Action == actionId);
        if (index < 0) throw new ArgumentException("Not a main route action: " + actionId);
        return MainStates[index];
    }

    /// <summary>State right before a main route action, already standing in the action's room.</summary>
    public static GameState ReadyFor(string actionId)
    {
        var action = Content.GetAction(actionId);
        var s = StateBefore(actionId);
        return action.IsInventoryAction ? s : Driver.TravelTo(Content, s, action.Room);
    }

    /// <summary>State right after a main route action.</summary>
    public static GameState StateAfter(string actionId)
    {
        var index = MainRoute.ToList().FindIndex(r => r.Action == actionId);
        if (index < 0) throw new ArgumentException("Not a main route action: " + actionId);
        return MainStates[index + 1];
    }

    /// <summary>State at the end of the main route (credits rolled, postgame).</summary>
    public static GameState MainEnd => MainStates[^1];

    private static (IReadOnlyList<WalkthroughStep>, IReadOnlyList<string>) LoadWalkthrough()
    {
        var root = JsonNode.Parse(File.ReadAllText(FixturePath("walkthrough.json")))!.AsObject();
        var rows = root["main_route"]!.AsArray().Select(n =>
        {
            var o = n!.AsObject();
            return new WalkthroughStep(
                o["step"]!.GetValue<int>(), o["quest"]!.GetValue<string>(), o["action"]!.GetValue<string>(),
                o["travel_path"]!.AsArray().Select(x => x!.GetValue<string>()).ToList(), o["target"]!.GetValue<string>(),
                o["select"]?.GetValue<string>(), o["puzzle_solution"]?.DeepClone(),
                o["inventory_after"]!.AsArray().Select(x => x!.GetValue<string>()).ToList(), o["room_after"]!.GetValue<string>());
        }).ToList();
        var optional = root["postgame_optional_route"]!.AsArray().Select(x => x!.GetValue<string>()).ToList();
        return (rows, optional);
    }

    private static IReadOnlyList<GameState> BuildMainStates()
    {
        var states = new List<GameState> { Content.InitialState };
        var s = Content.InitialState;
        foreach (var row in MainRoute)
        {
            s = Driver.FollowTravelPath(Content, s, row.TravelPath);
            s = Driver.Interact(Content, s, Content.GetAction(row.Action), row.PuzzleSolution);
            states.Add(s);
        }
        return states;
    }
}
