using LastBell.Core.Content;
using LastBell.Core.State;
using LastBell.Core.Text;

namespace LastBell.Core.Rules;

/// <summary>Quest status, derived exclusively from action ids.</summary>
public enum QuestStatus
{
    /// <summary>No action of the quest is done.</summary>
    NotStarted,
    /// <summary>Some actions done, completion not done.</summary>
    InProgress,
    /// <summary>The completion action is done.</summary>
    Done,
}

/// <summary>Quest groups, pinning and the next-goal selection.</summary>
public static class Quests
{
    /// <summary>Status of a quest.</summary>
    public static QuestStatus StatusOf(QuestDef quest, GameState state) =>
        state.IsDone(quest.Completion) ? QuestStatus.Done
        : quest.Actions.Any(state.IsDone) ? QuestStatus.InProgress
        : QuestStatus.NotStarted;

    /// <summary>
    /// <c>nextMainQuest</c>: the first (lowest) main quest group that is not complete and has an action
    /// whose guards pass and whose room is reachable (portals included).
    /// </summary>
    public static QuestDef? NextMainQuest(GameContent content, GameState state)
    {
        var reachable = Navigation.ConnectedRooms(content, state, includePortals: true);
        return content.Quests.FirstOrDefault(q => q.IsMain && !state.IsDone(q.Completion) && q.Actions.Any(id =>
        {
            var a = content.GetAction(id);
            return GameRules.GuardsPass(a, state) && (a.IsInventoryAction || reachable.Contains(a.Room));
        }));
    }

    /// <summary>The most recently started side quest that is not complete (shown in its own panel), or null.</summary>
    public static QuestDef? ActiveSideQuest(GameContent content, GameState state)
    {
        for (var i = state.Done.Length - 1; i >= 0; i--)
        {
            var quest = content.GetQuestOf(state.Done[i]);
            if (quest.IsSide && !state.IsDone(quest.Completion)) return quest;
        }
        return null;
    }

    /// <summary>
    /// The main quest the hint system talks about: the pinned main quest while it is incomplete,
    /// otherwise <see cref="NextMainQuest"/>.
    /// </summary>
    public static QuestDef? CurrentMainQuest(GameContent content, GameState state)
    {
        if (state.PinnedMainQuest is not null && content.FindQuest(state.PinnedMainQuest) is { } pinned && !state.IsDone(pinned.Completion))
            return pinned;
        return NextMainQuest(content, state);
    }

    /// <summary>Pins one main or one side quest (replacing the previous pin of that type).</summary>
    public static GameState Pin(GameContent content, GameState state, string questId)
    {
        var quest = content.FindQuest(questId);
        if (quest is null) return state;
        return quest.IsMain ? state with { PinnedMainQuest = quest.Id } : state with { PinnedSideQuest = quest.Id };
    }

    /// <summary>Removes the pin of the quest's type.</summary>
    public static GameState Unpin(GameContent content, GameState state, string questId)
    {
        var quest = content.FindQuest(questId);
        if (quest is null) return state;
        return quest.IsMain ? state with { PinnedMainQuest = null } : state with { PinnedSideQuest = null };
    }

    /// <summary>The latest objective sentence of a done action (contextual, not the only goal source).</summary>
    public static TextRef LatestObjective(GameContent content, GameState state)
    {
        for (var i = state.Done.Length - 1; i >= 0; i--)
        {
            var action = content.GetAction(state.Done[i]);
            if (action.Objective is not null) return TextKeys.ObjectiveOf(action);
        }
        return TextRef.Empty;
    }

    /// <summary>
    /// Reward text of a quest (<c>quest.&lt;id&gt;.reward</c>, fallback the data's <c>reward</c>, empty when the quest
    /// has none); the actual side quest reward is the album entry (epilogue shot) and the visible change.
    /// </summary>
    public static TextRef RewardOf(QuestDef quest) => new(TextKeys.QuestReward(quest.Id), quest.Reward);
}

/// <summary>A named value for a placeholder of a hint text (<c>{room}</c>, <c>{target}</c>).</summary>
/// <param name="Name">Placeholder name without braces.</param>
/// <param name="Value">Text to put in.</param>
public readonly record struct HintArg(string Name, TextRef Value);

/// <summary>One revealed hint: a text and the values of its placeholders (empty for plain texts).</summary>
/// <param name="Level">Hint level, 1 (direction), 2 (place) or 3 (exact step).</param>
/// <param name="Text">The text; ui texts may contain <c>{name}</c> placeholders.</param>
/// <param name="Args">Placeholder values; the presentation translates each value and replaces <c>{name}</c>.</param>
public sealed record HintText(int Level, TextRef Text, IReadOnlyList<HintArg> Args);

/// <summary>
/// Three-level hints that follow the step (orchestrator decision after the playtests, ISSUES PT-F08 / PT-S26): every
/// level refers to the next undone action of the quest (<see cref="CurrentStep"/>), and a higher level is revealed
/// only on an explicit request. Level 1 gives the direction (the objective that leads to the step, else the quest's
/// first or second hint), level 2 the place (room and hotspot, or "in the bag"), level 3 only the next step itself
/// (<c>ui.hint_step.&lt;action id&gt;</c>, never the whole chain). Revealed levels are kept per step
/// (<see cref="GameState.HintLevels"/> keyed by the step's action id), so a new step starts at level 0 again.
/// Hints never change progress and have no penalty.
/// </summary>
public static class Hints
{
    /// <summary>Number of hint levels per step.</summary>
    public const int Levels = 3;

    /// <summary>ui key of the level-2 text for a step in a room (<c>{room}</c>, <c>{target}</c>).</summary>
    public const string PlaceKey = "ui.hint.step_place";

    /// <summary>ui key of the level-2 text for a step in the bag (combining two items).</summary>
    public const string BagKey = "ui.hint.step_bag";

    /// <summary>Slovak fallback of <see cref="PlaceKey"/> (same text as ui.csv).</summary>
    public const string PlaceFallback = "{room}. Zameraj sa na: {target}.";

    /// <summary>Slovak fallback of <see cref="BagKey"/> (same text as ui.csv).</summary>
    public const string BagFallback = "Tento krok urobíš v inventári: spoj dva predmety, ktoré už máš.";

    /// <summary>ui key of the exact level-3 text of a step: <c>ui.hint_step.&lt;action id&gt;</c>.</summary>
    public static string StepKey(string actionId) => "ui.hint_step." + actionId;

    /// <summary>
    /// The next undone action of a quest: the open puzzle's action when it belongs to the quest, otherwise the first
    /// action in quest order that is not done and whose guards pass, otherwise the first action that is not done
    /// (a step that waits for another quest). Null when the quest is complete or unknown.
    /// </summary>
    public static ActionDef? CurrentStep(GameContent content, GameState state, string questId)
    {
        var quest = content.FindQuest(questId);
        if (quest is null || state.IsDone(quest.Completion)) return null;
        if (state.Mode == GameMode.Puzzle && state.OpenPuzzleAction is { } open && quest.Actions.Contains(open) && !state.IsDone(open))
            return content.GetAction(open);
        ActionDef? waiting = null;
        foreach (var id in quest.Actions)
        {
            if (state.IsDone(id)) continue;
            var action = content.GetAction(id);
            if (GameRules.GuardsPass(action, state)) return action;
            waiting ??= action;
        }
        return waiting;
    }

    /// <summary>How many hint levels of a step (action id) are revealed (0..3).</summary>
    public static int StepLevel(GameState state, string actionId) => Math.Clamp(state.HintLevels.GetValueOrDefault(actionId), 0, Levels);

    /// <summary>How many hint levels of the quest's current step are revealed (0..3; 0 for a complete quest).</summary>
    public static int RevealedLevel(GameContent content, GameState state, string questId) =>
        CurrentStep(content, state, questId) is { } step ? StepLevel(state, step.Id) : 0;

    /// <summary>Reveals the next hint level of the quest's current step (one level per player request).</summary>
    public static GameState RevealNext(GameContent content, GameState state, string questId)
    {
        var step = CurrentStep(content, state, questId);
        if (step is null) return state;
        var level = StepLevel(state, step.Id);
        if (level >= Levels) return state;
        return state with { HintLevels = state.HintLevels.SetItem(step.Id, level + 1) };
    }

    /// <summary>The revealed hints of the quest's current step, in level order.</summary>
    public static IReadOnlyList<HintText> Revealed(GameContent content, GameState state, string questId)
    {
        var quest = content.FindQuest(questId);
        var step = quest is null ? null : CurrentStep(content, state, questId);
        if (quest is null || step is null) return Array.Empty<HintText>();
        return Enumerable.Range(1, StepLevel(state, step.Id)).Select(level => TextFor(content, state, quest, step, level)).ToList();
    }

    /// <summary>The hint of one level (1..3) for a step (see <see cref="Hints"/>).</summary>
    public static HintText TextFor(GameContent content, GameState state, QuestDef quest, ActionDef step, int level) => level switch
    {
        1 => new HintText(1, Direction(content, state, quest, step), Array.Empty<HintArg>()),
        2 => Place(content, step),
        _ => new HintText(3, StepText(step), Array.Empty<HintArg>()),
    };

    /// <summary>
    /// The exact level-3 text of a step: the world overlay's <c>hint_step</c> (key <c>action.&lt;id&gt;.hint_step</c>,
    /// world.csv) for its new and relocated actions, else <c>ui.hint_step.&lt;id&gt;</c> (ui.csv, fallback the label).
    /// </summary>
    public static TextRef StepText(ActionDef step) =>
        step.HintStep is { } text ? new TextRef(TextKeys.ActionHintStep(step.Id), text) : new TextRef(StepKey(step.Id), step.Label);

    /// <summary>
    /// Level 1: the objective of the latest done action that enables the step (one of its required actions, or the
    /// giver of an item it needs); else the latest objective among the quest's done actions; else the quest's first
    /// hint while no action of the quest is done, its second hint afterwards.
    /// </summary>
    private static TextRef Direction(GameContent content, GameState state, QuestDef quest, ActionDef step)
    {
        if (!quest.Actions.Any(state.IsDone)) return HintAt(quest, 0);
        var needed = new HashSet<string>(step.RequiresItems, StringComparer.Ordinal);
        if (step.SelectedItem is not null) needed.Add(step.SelectedItem);
        if (step.IsCombine) needed.Add(step.Target);
        ActionDef? enabler = null, latest = null;
        foreach (var id in state.Done)
        {
            var done = content.GetAction(id);
            if (done.Objective is null) continue;
            if (step.RequiresDone.Contains(id) || done.Gives.Any(needed.Contains)) enabler = done;
            if (quest.Actions.Contains(id)) latest = done;
        }
        var source = enabler ?? latest;
        return source is not null ? TextKeys.ObjectiveOf(source) : HintAt(quest, 1);
    }

    /// <summary>Level 2: where the step happens (room and hotspot), or that it happens in the bag.</summary>
    private static HintText Place(GameContent content, ActionDef step)
    {
        if (step.IsInventoryAction) return new HintText(2, new TextRef(BagKey, BagFallback), Array.Empty<HintArg>());
        var room = content.GetRoom(step.Room);
        var target = content.FindHotspot(step.Target);
        var targetName = target is null ? TextRef.Empty : TextKeys.NameOf(target.Hotspot);
        return new HintText(2, new TextRef(PlaceKey, PlaceFallback),
            new[] { new HintArg("room", TextKeys.NameOf(room)), new HintArg("target", targetName) });
    }

    private static TextRef HintAt(QuestDef quest, int index) =>
        quest.Hints.Count == 0 ? TextRef.Empty : TextKeys.HintOf(quest, Math.Min(index, quest.Hints.Count - 1));
}
