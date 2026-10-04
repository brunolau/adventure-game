using System.Text.Json.Nodes;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.Save;
using LastBell.Core.State;
using LastBell.Core.Views;

namespace LastBell.Core;

/// <summary>
/// Optional mutable holder for the presentation layer: keeps the content and the current immutable
/// state, forwards to the pure rule functions and raises <see cref="StateChanged"/> after every
/// change. It adds no rules of its own. The "pending interaction" while the hero walks lives in the
/// presentation; on arrival call <see cref="Resolve"/> again with the same hit and only proceed
/// when the result is still the same.
/// </summary>
public sealed class GameSession
{
    /// <summary>Creates a session on a given state (default: the content's initial state).</summary>
    public GameSession(GameContent content, GameState? state = null)
    {
        Content = content;
        State = state ?? content.InitialState;
    }

    /// <summary>The loaded content.</summary>
    public GameContent Content { get; }

    /// <summary>The current state.</summary>
    public GameState State { get; private set; }

    /// <summary>Raised after the state changed (old, new).</summary>
    public event Action<GameState, GameState>? StateChanged;

    /// <summary>Shared hover/click resolver.</summary>
    public Resolution Resolve(Hit hit, PointerButton button) => GameRules.ResolveInteraction(Content, State, hit, button);

    /// <summary>Hover preview (name + action sentence).</summary>
    public HoverInfo Hover(Hit hit) => ViewBuilder.Hover(Content, State, hit);

    /// <summary>View of the current room.</summary>
    public RoomView Room() => ViewBuilder.Room(Content, State);

    /// <summary>
    /// Applies a resolution that needs no walking or that the hero already walked to: cancel selection,
    /// toggle inventory, select item, look (records the observation), travel, open the topic menu,
    /// commit an action without a puzzle, or open the puzzle modal. Walk and None change nothing.
    /// With <paramref name="combineMode"/> a selected item keeps the drawer open for a recipe.
    /// </summary>
    public void Apply(Resolution resolution, bool combineMode = false)
    {
        switch (resolution)
        {
            case Resolution.CancelSelection: Set(GameRules.CancelSelection(State)); break;
            case Resolution.ToggleInventory: Set(GameRules.ToggleInventory(State)); break;
            case Resolution.SelectItem s: Set(GameRules.SelectItem(State, s.ItemId, keepInventoryOpen: combineMode)); break;
            case Resolution.Look l: Set(Journal.ApplyLook(Content, State, l)); break;
            case Resolution.Travel t: Set(Navigation.Travel(Content, State, t.ExitId)); break;
            case Resolution.Dialogue: Set(Dialogue.OpenMenu(State)); break;
            case Resolution.Action a when a.ActionDef.Puzzle is not null: Set(Puzzles.Open(Content, State, a.ActionDef.Id)); break;
            case Resolution.Action a: Commit(a.ActionDef.Id); break;
        }
    }

    /// <summary>Commits an action; returns false (state unchanged) when it is no longer valid.</summary>
    public bool Commit(string actionId, JsonNode? answer = null)
    {
        var result = GameRules.TryCommitAction(Content, State, actionId, answer);
        if (result.Success) Set(result.State);
        return result.Success;
    }

    /// <summary>Confirms a puzzle answer.</summary>
    public PuzzleSubmitResult SubmitPuzzle(string actionId, JsonNode? answer)
    {
        var result = Puzzles.Submit(Content, State, actionId, answer);
        Set(result.State);
        return result;
    }

    /// <summary>Replaces the state through any pure rule function, e.g. <c>session.Update(s =&gt; Playback.Advance(content, s))</c>.</summary>
    public void Update(Func<GameState, GameState> change) => Set(change(State));

    /// <summary>Serializes the current state.</summary>
    public string Save() => SaveCodec.Serialize(State);

    /// <summary>Loads a save; on failure the current game stays untouched and false is returned.</summary>
    public bool TryLoad(string json, out Text.TextRef error)
    {
        if (SaveCodec.TryLoad(Content, json, out var loaded, out error, out _) && loaded is not null)
        {
            Set(loaded);
            return true;
        }
        return false;
    }

    private void Set(GameState next)
    {
        if (ReferenceEquals(next, State) || next.Equals(State)) return;
        var old = State;
        State = next;
        StateChanged?.Invoke(old, next);
    }
}
