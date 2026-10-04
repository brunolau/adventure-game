using LastBell.Core.Content;
using LastBell.Core.State;

namespace LastBell.Core.Rules;

/// <summary>Life stage of the single physical object of the cache contract.</summary>
public enum CacheStage
{
    /// <summary>Not yet built (raw parts may be owned).</summary>
    NotCreated,
    /// <summary>Built by <c>created_by</c>, carried by the hero.</summary>
    Created,
    /// <summary>Sealed by <c>sealed_by</c>, carried by the hero.</summary>
    Sealed,
    /// <summary>Stored in the 1982 niche by <c>stored_by</c>; the niche is reserved and ages 38 years.</summary>
    Stored,
    /// <summary>Retrieved in 2020 by <c>retrieved_by</c> (the aged version).</summary>
    Retrieved,
    /// <summary>Opened by <c>opened_by</c>.</summary>
    Opened,
    /// <summary>Consumed by <c>used_by</c>.</summary>
    Used,
}

/// <summary>Status of the temporal cache.</summary>
/// <param name="Stage">Current stage.</param>
/// <param name="CarriedItem">The lineage item currently owned, or null (stored or not created or used).</param>
/// <param name="OwnedLineageItems">How many lineage items are owned (the invariant is at most one).</param>
/// <param name="NicheReserved">True while the object lies in the niche (stored, not yet retrieved).</param>
/// <param name="PreservationComplete">True when every <c>preserved_by</c> action is done (retrieval possible).</param>
/// <param name="RetrievalAvailable">True when the retrieval action is currently valid by its guards.</param>
public sealed record CacheStatus(CacheStage Stage, string? CarriedItem, int OwnedLineageItems, bool NicheReserved,
    bool PreservationComplete, bool RetrievalAvailable);

/// <summary>
/// The cache contract: the same physical object is stored in 1982 and retrieved at the same place in
/// 2020. It is derived purely from action ids; the uniqueness is guaranteed by the once-only actions
/// (the young version can never be picked again, the source never refills, D05 gives the aged one once).
/// </summary>
public static class TemporalCache
{
    /// <summary>Current status.</summary>
    public static CacheStatus StatusOf(GameContent content, GameState state)
    {
        var c = content.Data.CacheContract;
        var stage = state.IsDone(c.UsedBy) ? CacheStage.Used
            : state.IsDone(c.OpenedBy) ? CacheStage.Opened
            : state.IsDone(c.RetrievedBy) ? CacheStage.Retrieved
            : state.IsDone(c.StoredBy) ? CacheStage.Stored
            : state.IsDone(c.SealedBy) ? CacheStage.Sealed
            : state.IsDone(c.CreatedBy) ? CacheStage.Created
            : CacheStage.NotCreated;
        // The first lineage entry is the raw material; the object exists from created_by on.
        var objectStages = c.PhysicalItemLineage.Skip(1).ToList();
        var owned = objectStages.Where(state.Has).ToList();
        var retrieval = content.FindAction(c.RetrievedBy);
        return new CacheStatus(stage, owned.FirstOrDefault(), owned.Count,
            state.IsDone(c.StoredBy) && !state.IsDone(c.RetrievedBy),
            state.AllDone(c.PreservedBy),
            retrieval is not null && GameRules.GuardsPass(retrieval, state));
    }

    /// <summary>True when the object (in any stage) exists at most once: never two lineage items owned, never owned while stored.</summary>
    public static bool InvariantHolds(GameContent content, GameState state)
    {
        var status = StatusOf(content, state);
        if (status.OwnedLineageItems > 1) return false;
        if (status.NicheReserved && status.OwnedLineageItems > 0) return false;
        if (status.Stage == CacheStage.Used && status.OwnedLineageItems > 0) return false;
        return true;
    }
}
