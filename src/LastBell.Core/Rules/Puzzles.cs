using System.Text.Json.Nodes;
using LastBell.Core.Content;
using LastBell.Core.State;
using LastBell.Core.Text;

namespace LastBell.Core.Rules;

/// <summary>Outcome of confirming a puzzle answer.</summary>
/// <param name="Solved">True when the answer was correct and the action committed.</param>
/// <param name="State">New state (on a wrong answer only the draft changes; nothing is consumed).</param>
/// <param name="Feedback">Wrong line or success line to show.</param>
public sealed record PuzzleSubmitResult(bool Solved, GameState State, TextRef Feedback);

/// <summary>Typed builders for puzzle answers (the JSON shape of each control type).</summary>
public static class PuzzleAnswers
{
    /// <summary>matching (P01, P04): for each left slot the chosen right value (null = empty).</summary>
    public static JsonNode Matching(params string?[] chosen) => new JsonArray(chosen.Select(c => c is null ? null : (JsonNode)JsonValue.Create(c)).ToArray());

    /// <summary>rotate_overlay (P02): orientation in degrees.</summary>
    public static JsonNode Rotation(int degrees) => JsonValue.Create(degrees);

    /// <summary>digits (P03): the digit values.</summary>
    public static JsonNode Digits(params int[] digits) => new JsonArray(digits.Select(d => (JsonNode?)JsonValue.Create(d)).ToArray());

    /// <summary>grid_choice (P05): 1-based row (from the top) and column (from the left).</summary>
    public static JsonNode Grid(int row, int column) => new JsonObject { ["row"] = row, ["column"] = column };
}

/// <summary>
/// Puzzle modals P01..P05: no timer, no penalty, resettable drafts, wrong answers consume nothing, and
/// the third hint level may fill in the solution (the player still confirms the same normal action).
/// </summary>
public static class Puzzles
{
    /// <summary>True when the answer equals the solution (deep equality).</summary>
    public static bool IsCorrect(PuzzleDef puzzle, JsonNode? answer) => JsonDeep.Equals(answer, puzzle.Solution);

    /// <summary>The action that opens a puzzle.</summary>
    public static ActionDef? ActionFor(GameContent content, string puzzleId) => content.Actions.FirstOrDefault(a => a.Puzzle == puzzleId);

    /// <summary>
    /// Opens the puzzle modal of a valid puzzle action (after the hero arrived and the action was
    /// re-resolved). Creates the draft from <c>initial</c> when there is none.
    /// </summary>
    public static GameState Open(GameContent content, GameState state, string actionId)
    {
        var action = content.FindAction(actionId);
        if (action?.Puzzle is null || !GameRules.ValidAction(content, state, action)) return state;
        if (state.Mode is not (GameMode.World or GameMode.Inventory)) return state;
        var puzzle = content.GetPuzzle(action.Puzzle);
        var drafts = state.PuzzleDrafts.ContainsKey(puzzle.Id)
            ? state.PuzzleDrafts
            : state.PuzzleDrafts.SetItem(puzzle.Id, JsonDeep.ToCanonicalText(puzzle.Initial));
        return state with { Mode = GameMode.Puzzle, PuzzleDrafts = drafts };
    }

    /// <summary>The current draft (or the initial value when no draft exists). A fresh copy every call.</summary>
    public static JsonNode? Draft(GameContent content, GameState state, string puzzleId) =>
        state.PuzzleDrafts.TryGetValue(puzzleId, out var text) ? JsonDeep.Parse(text) : content.GetPuzzle(puzzleId).Initial?.DeepClone();

    /// <summary>Stores a draft (e.g. on every control change or when closing the modal). Never marks the puzzle solved.</summary>
    public static GameState UpdateDraft(GameContent content, GameState state, string puzzleId, JsonNode? draft)
    {
        if (content.FindPuzzle(puzzleId) is null) return state;
        return state with { PuzzleDrafts = state.PuzzleDrafts.SetItem(puzzleId, JsonDeep.ToCanonicalText(draft)) };
    }

    /// <summary>Resets the draft to the puzzle's initial value (when <c>reset_allowed</c>).</summary>
    public static GameState Reset(GameContent content, GameState state, string puzzleId)
    {
        var puzzle = content.FindPuzzle(puzzleId);
        if (puzzle is null || !puzzle.ResetAllowed) return state;
        return state with { PuzzleDrafts = state.PuzzleDrafts.SetItem(puzzleId, JsonDeep.ToCanonicalText(puzzle.Initial)) };
    }

    /// <summary>Closes the modal without solving it; the draft is kept.</summary>
    public static GameState Close(GameState state) => state.Mode == GameMode.Puzzle ? state with { Mode = GameMode.World } : state;

    /// <summary>
    /// Confirms an answer. Correct: the action is committed atomically (lines follow). Wrong: only the
    /// draft is stored, the modal stays open, nothing is consumed and nothing is written to the story.
    /// </summary>
    public static PuzzleSubmitResult Submit(GameContent content, GameState state, string actionId, JsonNode? answer)
    {
        var action = content.GetAction(actionId);
        var puzzle = content.GetPuzzle(action.Puzzle ?? throw new ArgumentException("Action has no puzzle: " + actionId, nameof(actionId)));
        if (!IsCorrect(puzzle, answer))
        {
            return new PuzzleSubmitResult(false, UpdateDraft(content, state, puzzle.Id, answer), TextKeys.WrongOf(puzzle));
        }
        var committed = GameRules.TryCommitAction(content, state, actionId, answer);
        return committed.Success
            ? new PuzzleSubmitResult(true, committed.State, TextKeys.SuccessOf(puzzle))
            : new PuzzleSubmitResult(false, state, TextKeys.WrongOf(puzzle));
    }

    /// <summary>True when the "fill in correctly" button may be shown: <c>hint_can_fill</c> and the third hint level of the owning quest revealed.</summary>
    public static bool CanFill(GameContent content, GameState state, string puzzleId)
    {
        var puzzle = content.FindPuzzle(puzzleId);
        var action = ActionFor(content, puzzleId);
        if (puzzle is null || action is null || !puzzle.HintCanFill) return false;
        var quest = content.GetQuestOf(action.Id);
        return Hints.RevealedLevel(state, quest.Id) >= quest.Hints.Count && quest.Hints.Count > 0;
    }

    /// <summary>Fills the draft with the solution (only when <see cref="CanFill"/>); the player must still confirm.</summary>
    public static GameState Fill(GameContent content, GameState state, string puzzleId) =>
        CanFill(content, state, puzzleId) ? UpdateDraft(content, state, puzzleId, content.GetPuzzle(puzzleId).Solution) : state;

    /// <summary>The readable clue (also listed in the journal).</summary>
    public static TextRef Clue(GameContent content, string puzzleId) => TextKeys.ClueOf(content.GetPuzzle(puzzleId));
}
