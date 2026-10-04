using LastBell.Core.Content;
using LastBell.Core.Text;

namespace LastBell.Core.Rules;

/// <summary>Mouse (or mapped touch/keyboard) button of a pointer interaction.</summary>
public enum PointerButton
{
    /// <summary>Logical action.</summary>
    Left,
    /// <summary>Look / inventory / cancel selection.</summary>
    Right,
}

/// <summary>What the pointer is over, as determined by the presentation layer's hit test.</summary>
public abstract record Hit
{
    private Hit() { }

    /// <summary>Walkable floor at logical coordinates.</summary>
    public sealed record Floor(double X, double Y) : Hit;

    /// <summary>A hotspot (prop or NPC) by id.</summary>
    public sealed record Hotspot(string Id) : Hit;

    /// <summary>An exit zone by id.</summary>
    public sealed record Exit(string Id) : Hit;

    /// <summary>An inventory item slot by item id.</summary>
    public sealed record Item(string Id) : Hit;

    /// <summary>Nothing interactive (e.g. non-walkable background).</summary>
    public sealed record Empty : Hit;
}

/// <summary>One entry of the dialogue topic menu: either a story topic action or an ambient topic.</summary>
/// <param name="Id">Action id or ambient topic id.</param>
/// <param name="Label">Topic label to show.</param>
/// <param name="Action">The story action (commit it with <see cref="GameRules.CommitAction"/>), or null.</param>
/// <param name="Topic">The ambient topic (start it with <see cref="Dialogue.StartTopic"/>), or null.</param>
public sealed record TopicOption(string Id, TextRef Label, ActionDef? Action, TopicDef? Topic)
{
    /// <summary>True for a one-time story topic action.</summary>
    public bool IsStoryAction => Action is not null;
}

/// <summary>
/// Result of <see cref="GameRules.ResolveInteraction"/>. The same value drives hover preview and click,
/// so a hover can never promise something a click would not do.
/// </summary>
public abstract record Resolution
{
    private Resolution() { }

    /// <summary>Nothing happens (complete no-op; the selection is kept).</summary>
    public sealed record None : Resolution;

    /// <summary>Show a look text. <paramref name="ObservationKey"/> is recorded in the journal on first look.</summary>
    public sealed record Look(TextRef Text, string? ObservationKey) : Resolution;

    /// <summary>Clear the item attached to the cursor (and do nothing else).</summary>
    public sealed record CancelSelection : Resolution;

    /// <summary>Open or close the inventory drawer.</summary>
    public sealed record ToggleInventory : Resolution;

    /// <summary>Attach an item to the cursor.</summary>
    public sealed record SelectItem(string ItemId) : Resolution;

    /// <summary>Walk to a floor point.</summary>
    public sealed record Walk(double X, double Y) : Resolution;

    /// <summary>Walk to an unlocked exit and travel through it.</summary>
    public sealed record Travel(string ExitId, string To) : Resolution;

    /// <summary>Open the topic menu of an NPC.</summary>
    public sealed record Dialogue(string CharacterId, string HotspotId, IReadOnlyList<TopicOption> Topics) : Resolution;

    /// <summary>Walk to the target and commit this action (after re-resolving on arrival).</summary>
    public sealed record Action(ActionDef ActionDef) : Resolution;

    /// <summary>The shared "no-op" instance.</summary>
    public static Resolution Nothing { get; } = new None();
}

/// <summary>Thrown when an action cannot be committed; the state is unchanged.</summary>
public sealed class ActionRejectedException : InvalidOperationException
{
    /// <summary>Creates the exception.</summary>
    public ActionRejectedException(string actionId, ActionRejection reason, string message) : base(message)
    {
        ActionId = actionId;
        Reason = reason;
    }

    /// <summary>The action that was rejected.</summary>
    public string ActionId { get; }

    /// <summary>Why it was rejected.</summary>
    public ActionRejection Reason { get; }
}

/// <summary>Reasons for rejecting a commit.</summary>
public enum ActionRejection
{
    /// <summary>Unknown id.</summary>
    UnknownAction,
    /// <summary>Guards, room or visibility no longer allow it (e.g. already done).</summary>
    NoLongerValid,
    /// <summary>The puzzle answer is missing or wrong.</summary>
    PuzzleNotSolved,
    /// <summary>Consumed item missing or given item already owned.</summary>
    InvalidItemTransaction,
}

/// <summary>Result of <see cref="GameRules.TryCommitAction"/>.</summary>
/// <param name="Success">True when the transaction was committed.</param>
/// <param name="State">The new state, or the unchanged input state on failure.</param>
/// <param name="Rejection">Failure reason, or null.</param>
public sealed record CommitResult(bool Success, State.GameState State, ActionRejection? Rejection);
