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
    /// Reward text key of a quest. game.json has no reward field, so the fallback is empty; the
    /// actual side quest reward is the album entry (epilogue shot) and the visible change.
    /// </summary>
    public static TextRef RewardOf(QuestDef quest) => new(TextKeys.QuestReward(quest.Id), "");
}

/// <summary>Three-level hints (direction, concrete steps, exact solution); a higher level only on an explicit request.</summary>
public static class Hints
{
    /// <summary>How many hint levels of a quest are revealed (0..3).</summary>
    public static int RevealedLevel(GameState state, string questId) => state.HintLevels.GetValueOrDefault(questId);

    /// <summary>Reveals the next hint level of a quest (one level per player request). No score penalty exists.</summary>
    public static GameState RevealNext(GameContent content, GameState state, string questId)
    {
        var quest = content.FindQuest(questId);
        if (quest is null) return state;
        var level = RevealedLevel(state, questId);
        if (level >= quest.Hints.Count) return state;
        return state with { HintLevels = state.HintLevels.SetItem(questId, level + 1) };
    }

    /// <summary>The revealed hint texts of a quest, in level order.</summary>
    public static IReadOnlyList<TextRef> Revealed(GameContent content, GameState state, string questId)
    {
        var quest = content.FindQuest(questId);
        if (quest is null) return Array.Empty<TextRef>();
        var level = Math.Min(RevealedLevel(state, questId), quest.Hints.Count);
        return Enumerable.Range(0, level).Select(i => TextKeys.HintOf(quest, i)).ToList();
    }
}
