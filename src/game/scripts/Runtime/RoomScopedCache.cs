using System;
using System.Collections.Generic;
using System.Linq;

namespace LastBell.Game.Runtime;

/// <summary>
/// A by-key cache whose entries are dropped when no room build used them for <see cref="RoomScopedCaches.KeepRooms"/>
/// rooms. Used for the sprite sheets and ambient sprites (each NPC sheet is up to 16 MB decoded): before
/// these caches were trimmed, every visited room's NPC textures stayed in memory for the whole session
/// (about 450 MB more video memory after 20 rooms). Dropping an entry only drops this reference: nodes that
/// still draw the texture keep it alive, and Godot's resource cache hands the same texture out again on reload.
/// </summary>
public sealed class RoomScopedCache<T>
{
    private readonly Dictionary<string, (T Value, int Epoch)> entries;
    private readonly Func<string, bool>? pinned;

    /// <summary>Creates the cache and registers it for <see cref="RoomScopedCaches.Trim"/>.</summary>
    /// <param name="pinned">Keys that are never dropped (e.g. the hero's sheets, needed in every room).</param>
    public RoomScopedCache(Func<string, bool>? pinned = null)
    {
        entries = new Dictionary<string, (T, int)>(StringComparer.Ordinal);
        this.pinned = pinned;
        RoomScopedCaches.Register(TrimOlderThan);
    }

    /// <summary>Number of entries (QA).</summary>
    public int Count => entries.Count;

    /// <summary>Looks a key up and marks it as used by the current room.</summary>
    public bool TryGetValue(string key, out T value)
    {
        if (entries.TryGetValue(key, out var entry))
        {
            if (entry.Epoch != RoomScopedCaches.Epoch) entries[key] = (entry.Value, RoomScopedCaches.Epoch);
            value = entry.Value;
            return true;
        }
        value = default!;
        return false;
    }

    /// <summary>Stores a value for the current room.</summary>
    public T this[string key]
    {
        set => entries[key] = (value, RoomScopedCaches.Epoch);
    }

    private int TrimOlderThan(int epoch)
    {
        var old = entries.Where(e => e.Value.Epoch < epoch && pinned?.Invoke(e.Key) != true).Select(e => e.Key).ToList();
        foreach (var key in old) entries.Remove(key);
        return old.Count;
    }
}

/// <summary>Room epochs of all <see cref="RoomScopedCache{T}"/> instances (advanced by the world stage per room build).</summary>
public static class RoomScopedCaches
{
    private static readonly List<Func<int, int>> Trimmers = new();

    /// <summary>Rooms an unused entry survives (2: the current room and the one before, so walking back is instant).</summary>
    public static int KeepRooms { get; set; } = 2;

    /// <summary>Current room epoch (number of room builds started).</summary>
    public static int Epoch { get; private set; }

    internal static void Register(Func<int, int> trimmer) => Trimmers.Add(trimmer);

    /// <summary>Starts a new room epoch (call before a room build).</summary>
    public static void NextRoom() => Epoch++;

    /// <summary>Drops entries no room build used in the last <see cref="KeepRooms"/> rooms; returns how many.</summary>
    public static int Trim()
    {
        int removed = 0;
        foreach (var trim in Trimmers) removed += trim(Epoch - KeepRooms + 1);
        if (removed > 0) GC.Collect(); // release the managed texture wrappers now, while the screen is faded out
        return removed;
    }
}
