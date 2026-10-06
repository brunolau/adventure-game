using LastBell.Core.Content;
using LastBell.Core.State;
using LastBell.Core.Text;

namespace LastBell.Core.Rules;

/// <summary>A named value for a placeholder of a hint text (<c>{room}</c>, <c>{target}</c>).</summary>
/// <param name="Name">Placeholder name without braces.</param>
/// <param name="Value">Text to put in.</param>
public readonly record struct HintArg(string Name, TextRef Value);

/// <summary>What a revealed hint level is (the hint screen labels it).</summary>
public enum HintKind
{
    /// <summary>Easy level 1: the direction (objective that leads to the step, else a quest hint).</summary>
    Direction,
    /// <summary>Easy level 2: room and hotspot of the step, or "in the bag".</summary>
    Place,
    /// <summary>Easy level 3: the exact step.</summary>
    Step,
    /// <summary>Standard / Hard level 1: a nudge in Adam's voice (<c>hint.nudge.&lt;action id&gt;</c>).</summary>
    Nudge,
    /// <summary>Standard level 2: where to look, place or person, never the action (<c>hint.where.&lt;action id&gt;</c>).</summary>
    Where,
}

/// <summary>One revealed hint: a text and the values of its placeholders (empty for plain texts).</summary>
/// <param name="Level">Hint level, 1..3.</param>
/// <param name="Text">The text (the fallback when <see cref="OwnKey"/> has a table entry); ui texts may contain <c>{name}</c> placeholders.</param>
/// <param name="Args">Placeholder values of <see cref="Text"/>; the presentation translates each value and replaces <c>{name}</c>.</param>
public sealed record HintText(int Level, TextRef Text, IReadOnlyList<HintArg> Args)
{
    /// <summary>What this level is.</summary>
    public HintKind Kind { get; init; } = Level switch { 1 => HintKind.Direction, 2 => HintKind.Place, _ => HintKind.Step };

    /// <summary>
    /// The step's own text key on Standard and Hard (<c>hint.nudge.&lt;id&gt;</c> or <c>hint.where.&lt;id&gt;</c>), or null.
    /// Show <c>Tr(OwnKey)</c> when the table has it (a plain text, no placeholders); otherwise show <see cref="Text"/>
    /// with <see cref="Args"/>. Until the writers' texts are approved the tables have no such keys.
    /// </summary>
    public string? OwnKey { get; init; }
}

/// <summary>Why the next hint level of a step can or cannot be revealed now.</summary>
public enum HintGate
{
    /// <summary>The next level can be revealed.</summary>
    Open,
    /// <summary>The quest is complete or unknown: no step.</summary>
    NoStep,
    /// <summary>Every level this difficulty offers for the step is revealed.</summary>
    AllShown,
    /// <summary>Hard: the nudge opens after <see cref="Hints.HardWaitSeconds"/> without progress (<see cref="HintAvailability.WaitSeconds"/> left).</summary>
    Waiting,
    /// <summary>Hard: a puzzle step gets no help at all.</summary>
    NoPuzzleHelp,
}

/// <summary>Hint state of a quest's current step under the game's difficulty.</summary>
/// <param name="Step">The current step (null when <see cref="Gate"/> is <see cref="HintGate.NoStep"/>).</param>
/// <param name="Revealed">Levels shown now (0..<paramref name="Max"/>).</param>
/// <param name="Max">Levels this difficulty offers for the step (Easy 3, Standard 2, Hard 1, Hard puzzle 0).</param>
/// <param name="Gate">Whether the next level can be revealed.</param>
/// <param name="WaitSeconds">Hard while <see cref="HintGate.Waiting"/>: seconds until the nudge opens, else 0.</param>
public sealed record HintAvailability(ActionDef? Step, int Revealed, int Max, HintGate Gate, double WaitSeconds)
{
    /// <summary>True when <see cref="Hints.RevealNext"/> would reveal a level now.</summary>
    public bool CanReveal => Gate == HintGate.Open;

    /// <summary>True when the next level is the exact step (Easy level 3: the hint screen labels its button "show the solution").</summary>
    public bool NextIsExactStep => CanReveal && Revealed + 1 == Hints.Levels;
}

/// <summary>
/// Hints that follow the step (orchestrator decision after the playtests, ISSUES PT-F08 / PT-S26) and the game's
/// difficulty (docs/DECISIONS.md "Difficulty settings", <see cref="GameState.Difficulty"/>). Every level refers to the
/// next undone action of the quest (<see cref="CurrentStep"/>), and a higher level is revealed only on an explicit
/// request.
/// <list type="bullet">
/// <item>Easy: three levels. 1 the direction (the objective that leads to the step, else the quest's first or second
/// hint), 2 the place (room and hotspot, or "in the bag"), 3 only the next step itself
/// (<c>ui.hint_step.&lt;action id&gt;</c>, never the whole chain); level 3 of a puzzle's step offers "fill in".</item>
/// <item>Standard (default): two levels. 1 a nudge (<c>hint.nudge.&lt;id&gt;</c>, until written the Easy level-1 text),
/// 2 where to look (<c>hint.where.&lt;id&gt;</c>, until written the Easy level-2 text; for a puzzle step the rule of
/// the puzzle). Never the exact step, never a fill-in.</item>
/// <item>Hard: only the nudge, and only after <see cref="HardWaitSeconds"/> without progress (the presentation counts
/// the time and passes it in; Core has no clock). A puzzle step gets no help.</item>
/// </list>
/// Revealed levels are kept per step (<see cref="GameState.HintLevels"/> keyed by the step's action id), so a new step
/// starts at level 0 again; a level revealed on an easier difficulty stays stored but is shown only up to the current
/// difficulty's maximum. Hints never change progress and have no penalty.
/// </summary>
public static class Hints
{
    /// <summary>Highest number of hint levels per step (Easy).</summary>
    public const int Levels = 3;

    /// <summary>Hard: seconds without progress (no new done action) before the nudge of a step can be revealed.</summary>
    public const double HardWaitSeconds = 180;

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

    /// <summary>Key of a step's nudge (Standard and Hard level 1): <c>hint.nudge.&lt;action id&gt;</c>.</summary>
    public static string NudgeKey(string actionId) => "hint.nudge." + actionId;

    /// <summary>Key of a step's "where to look" (Standard level 2): <c>hint.where.&lt;action id&gt;</c>.</summary>
    public static string WhereKey(string actionId) => "hint.where." + actionId;

    /// <summary>Levels a difficulty offers for a step: Easy 3, Standard 2, Hard 1 (0 for a puzzle step).</summary>
    public static int MaxLevel(Difficulty difficulty, ActionDef step) => difficulty switch
    {
        Difficulty.Easy => Levels,
        Difficulty.Standard => 2,
        _ => step.Puzzle is null ? 1 : 0,
    };

    /// <summary>True when the difficulty lets a puzzle hint fill in the answer (Easy only).</summary>
    public static bool AllowsPuzzleFill(Difficulty difficulty) => difficulty == Difficulty.Easy;

    /// <summary>The state with another difficulty (the same instance when it does not change). Progress is untouched.</summary>
    public static GameState WithDifficulty(GameState state, Difficulty difficulty) =>
        state.Difficulty == difficulty ? state : state with { Difficulty = difficulty };

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

    /// <summary>How many hint levels of a step (action id) are stored (0..3), whatever the difficulty.</summary>
    public static int StepLevel(GameState state, string actionId) => Math.Clamp(state.HintLevels.GetValueOrDefault(actionId), 0, Levels);

    /// <summary>How many hint levels of the quest's current step are shown under the difficulty (0 for a complete quest).</summary>
    public static int RevealedLevel(GameContent content, GameState state, string questId) =>
        CurrentStep(content, state, questId) is { } step ? Math.Min(StepLevel(state, step.Id), MaxLevel(state.Difficulty, step)) : 0;

    /// <summary>
    /// Whether the next level of the quest's current step can be revealed now. <paramref name="secondsWithoutProgress"/>
    /// is the time since the last new done action as the presentation counts it; it matters only on Hard (the default
    /// treats the wait as over, for callers without a clock).
    /// </summary>
    public static HintAvailability Availability(GameContent content, GameState state, string questId, double secondsWithoutProgress = double.PositiveInfinity)
    {
        var step = CurrentStep(content, state, questId);
        if (step is null) return new HintAvailability(null, 0, 0, HintGate.NoStep, 0);
        var max = MaxLevel(state.Difficulty, step);
        var shown = Math.Min(StepLevel(state, step.Id), max);
        if (max == 0) return new HintAvailability(step, 0, 0, HintGate.NoPuzzleHelp, 0);
        if (shown >= max) return new HintAvailability(step, shown, max, HintGate.AllShown, 0);
        if (state.Difficulty == Difficulty.Hard && secondsWithoutProgress < HardWaitSeconds)
            return new HintAvailability(step, shown, max, HintGate.Waiting, HardWaitSeconds - Math.Max(0, secondsWithoutProgress));
        return new HintAvailability(step, shown, max, HintGate.Open, 0);
    }

    /// <summary>
    /// Reveals the next hint level of the quest's current step (one level per player request) when
    /// <see cref="Availability"/> allows it; otherwise returns the same instance.
    /// </summary>
    public static GameState RevealNext(GameContent content, GameState state, string questId, double secondsWithoutProgress = double.PositiveInfinity)
    {
        var available = Availability(content, state, questId, secondsWithoutProgress);
        if (!available.CanReveal || available.Step is null) return state;
        return state with { HintLevels = state.HintLevels.SetItem(available.Step.Id, available.Revealed + 1) };
    }

    /// <summary>The shown hints of the quest's current step, in level order (at most the difficulty's maximum).</summary>
    public static IReadOnlyList<HintText> Revealed(GameContent content, GameState state, string questId)
    {
        var quest = content.FindQuest(questId);
        var step = quest is null ? null : CurrentStep(content, state, questId);
        if (quest is null || step is null) return Array.Empty<HintText>();
        return Enumerable.Range(1, RevealedLevel(content, state, questId)).Select(level => TextFor(content, state, quest, step, level)).ToList();
    }

    /// <summary>The hint of one level (1..3) for a step under the state's difficulty (see <see cref="Hints"/>).</summary>
    public static HintText TextFor(GameContent content, GameState state, QuestDef quest, ActionDef step, int level)
    {
        if (state.Difficulty == Difficulty.Easy)
        {
            return level switch
            {
                1 => new HintText(1, Direction(content, state, quest, step), Array.Empty<HintArg>()),
                2 => Place(content, step),
                _ => new HintText(3, StepText(step), Array.Empty<HintArg>()),
            };
        }
        return level switch
        {
            1 => new HintText(1, Direction(content, state, quest, step), Array.Empty<HintArg>()) { Kind = HintKind.Nudge, OwnKey = NudgeKey(step.Id) },
            _ => Place(content, step) with { Kind = HintKind.Where, OwnKey = WhereKey(step.Id) },
        };
    }

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
