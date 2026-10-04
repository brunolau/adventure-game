using System.Collections.Immutable;

namespace LastBell.Core.State;

/// <summary>Finite runtime modes. Only the top mode receives game clicks.</summary>
public enum GameMode
{
    /// <summary>Scene interaction (walking, hotspots, exits).</summary>
    World,
    /// <summary>Inventory drawer open.</summary>
    Inventory,
    /// <summary>Dialogue lines or the topic menu.</summary>
    Dialogue,
    /// <summary>Puzzle modal open.</summary>
    Puzzle,
    /// <summary>Cutscene playing.</summary>
    Cutscene,
    /// <summary>Map open.</summary>
    Map,
    /// <summary>Journal open.</summary>
    Journal,
    /// <summary>Pause menu.</summary>
    Pause,
}

/// <summary>
/// Complete, immutable game state. Every rule function returns a new instance; nothing mutates in place.
/// Progression is derived exclusively from <see cref="Done"/> (ordered list of action ids).
/// The first eleven properties match the <c>State</c> interface of runtime_contract.ts; the rest are
/// UI helper fields the handoff permits (labels toggle, dialogue cursor, hints, pins, room entry marker).
/// </summary>
public sealed record GameState
{
    /// <summary>The only supported save schema version.</summary>
    public const int CurrentSchemaVersion = 1;

    private ImmutableArray<string> done = ImmutableArray<string>.Empty;
    private ImmutableArray<string> inventory = ImmutableArray<string>.Empty;
    private ImmutableHashSet<string>? doneSet;
    private ImmutableHashSet<string>? inventorySet;

    /// <summary>Save schema version (always 1).</summary>
    public int SchemaVersion { get; init; } = CurrentSchemaVersion;

    /// <summary>Current room id.</summary>
    public string Room { get; init; } = "";

    /// <summary>Era (year) of the current room.</summary>
    public int Era { get; init; }

    /// <summary>Owned items in acquisition order (unique).</summary>
    public ImmutableArray<string> Inventory
    {
        get => inventory;
        init { inventory = value.IsDefault ? ImmutableArray<string>.Empty : value; inventorySet = null; }
    }

    /// <summary>Completed action ids in commit order (unique).</summary>
    public ImmutableArray<string> Done
    {
        get => done;
        init { done = value.IsDefault ? ImmutableArray<string>.Empty : value; doneSet = null; }
    }

    /// <summary>Visited room ids in first-visit order (unique).</summary>
    public ImmutableArray<string> Visited { get; init; } = ImmutableArray<string>.Empty;

    /// <summary>Item attached to the cursor, or null.</summary>
    public string? SelectedItem { get; init; }

    /// <summary>Current top mode.</summary>
    public GameMode Mode { get; init; } = GameMode.World;

    /// <summary>Unsolved puzzle drafts: puzzle id to canonical JSON text of the draft value.</summary>
    public ImmutableSortedDictionary<string, string> PuzzleDrafts { get; init; } = ImmutableSortedDictionary<string, string>.Empty.WithComparers(StringComparer.Ordinal);

    /// <summary>Journal entries already recorded (e.g. <c>action.G01</c>, look keys, <c>topic.&lt;id&gt;</c>).</summary>
    public ImmutableArray<string> JournalSeen { get; init; } = ImmutableArray<string>.Empty;

    /// <summary>Completed side quest ids (album rewards).</summary>
    public ImmutableArray<string> SideRewards { get; init; } = ImmutableArray<string>.Empty;

    /// <summary>Space toggle: all visible hotspot labels shown. Persists across rooms.</summary>
    public bool HotspotLabels { get; init; }

    /// <summary>Line currently displayed (dialogue/cutscene/first entry), or null.</summary>
    public string? ActiveLineId { get; init; }

    /// <summary>Line ids still to be played after <see cref="ActiveLineId"/>.</summary>
    public ImmutableArray<string> PlaybackQueue { get; init; } = ImmutableArray<string>.Empty;

    /// <summary>Number of done actions when the current room was entered (deferred causal effects).</summary>
    public int RoomEntryDoneCount { get; init; }

    /// <summary>Revealed hint levels per quest id (0..3).</summary>
    public ImmutableSortedDictionary<string, int> HintLevels { get; init; } = ImmutableSortedDictionary<string, int>.Empty.WithComparers(StringComparer.Ordinal);

    /// <summary>Pinned main quest id, or null.</summary>
    public string? PinnedMainQuest { get; init; }

    /// <summary>Pinned side quest id, or null.</summary>
    public string? PinnedSideQuest { get; init; }

    /// <summary>True if the action id is in <see cref="Done"/>.</summary>
    public bool IsDone(string actionId) => (doneSet ??= done.ToImmutableHashSet(StringComparer.Ordinal)).Contains(actionId);

    /// <summary>True if every id is in <see cref="Done"/> (an empty list is true).</summary>
    public bool AllDone(IEnumerable<string> actionIds) => actionIds.All(IsDone);

    /// <summary>True if any id is in <see cref="Done"/>.</summary>
    public bool AnyDone(IEnumerable<string> actionIds) => actionIds.Any(IsDone);

    /// <summary>True if the item is owned (active or archived; archiving is only a view).</summary>
    public bool Has(string itemId) => (inventorySet ??= inventory.ToImmutableHashSet(StringComparer.Ordinal)).Contains(itemId);

    /// <summary>True if every item is owned.</summary>
    public bool HasAll(IEnumerable<string> itemIds) => itemIds.All(Has);

    /// <summary>Structural equality over every persisted field.</summary>
    public bool Equals(GameState? other)
    {
        if (other is null) return false;
        if (ReferenceEquals(this, other)) return true;
        return SchemaVersion == other.SchemaVersion && Room == other.Room && Era == other.Era &&
               inventory.SequenceEqual(other.inventory) && done.SequenceEqual(other.done) &&
               Visited.SequenceEqual(other.Visited) && SelectedItem == other.SelectedItem && Mode == other.Mode &&
               PuzzleDrafts.SequenceEqual(other.PuzzleDrafts) && JournalSeen.SequenceEqual(other.JournalSeen) &&
               SideRewards.SequenceEqual(other.SideRewards) && HotspotLabels == other.HotspotLabels &&
               ActiveLineId == other.ActiveLineId && PlaybackQueue.SequenceEqual(other.PlaybackQueue) &&
               RoomEntryDoneCount == other.RoomEntryDoneCount && HintLevels.SequenceEqual(other.HintLevels) &&
               PinnedMainQuest == other.PinnedMainQuest && PinnedSideQuest == other.PinnedSideQuest;
    }

    /// <inheritdoc />
    public override int GetHashCode() => HashCode.Combine(Room, Era, done.Length, inventory.Length, Mode, SelectedItem);
}

/// <summary>Small helpers for ordered unique id lists.</summary>
internal static class IdList
{
    /// <summary>Appends ids that are not yet present, keeping order.</summary>
    public static ImmutableArray<string> AddUnique(ImmutableArray<string> list, IEnumerable<string> ids)
    {
        var builder = list.ToBuilder();
        var seen = new HashSet<string>(list, StringComparer.Ordinal);
        foreach (var id in ids)
        {
            if (seen.Add(id)) builder.Add(id);
        }
        return builder.Count == list.Length ? list : builder.ToImmutable();
    }

    /// <summary>Appends a single id if it is not yet present.</summary>
    public static ImmutableArray<string> AddUnique(ImmutableArray<string> list, string id) =>
        list.Contains(id) ? list : list.Add(id);
}
