using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using LastBell.Core.Views;
using LastBell.Game.Runtime;

namespace LastBell.Game.World;

/// <summary>
/// Loads the paintings of the rooms next to the displayed one in the background (Godot threaded
/// loading), so walking through an exit finds the background and foreground mask already decoded and
/// the room build does not stall the frame. Other modules add the textures their part of a room build
/// would load through <see cref="PathProviders"/> (the living world: hero and NPC sprite sheets). Keeps references only for the current room's neighbours;
/// textures of rooms that are no longer next door are released (Godot frees them when nothing else
/// holds them). Presentation only; Core is never asked for anything but the room's exits.
/// </summary>
public partial class RoomPreloader : Node
{
    /// <summary>The singleton (child of the world stage).</summary>
    public static RoomPreloader? Instance { get; private set; }

    /// <summary>Off for perf comparisons (QA flag <c>--no-preload</c>).</summary>
    public static bool Enabled { get; set; } = true;

    /// <summary>Most neighbours preloaded at once (each 1920x1080 painting is about 8 MB decoded).</summary>
    public static int MaxRooms { get; set; } = 6;

    /// <summary>Extra texture paths a build of the given (neighbour) room would load; called after the paintings.</summary>
    public static readonly List<Func<RoomView, IEnumerable<string>>> PathProviders = new();

    private readonly Dictionary<string, Texture2D> held = new(StringComparer.Ordinal);
    private readonly HashSet<string> pending = new(StringComparer.Ordinal);

    /// <summary>Paths requested and finished since start (perf QA).</summary>
    public int Loaded { get; private set; }

    /// <inheritdoc />
    public override void _Ready()
    {
        Instance = this;
        ProcessMode = ProcessModeEnum.Always;
    }

    /// <inheritdoc />
    public override void _ExitTree()
    {
        if (Instance == this) Instance = null;
    }

    /// <summary>Starts loading the paintings of the rooms the given room's exits lead to.</summary>
    public void Prefetch(Room room) =>
        PrefetchRooms(room.View.Exits.Select(e => e.To).Where(t => t != room.RoomId));

    /// <summary>
    /// Starts loading what a build of these rooms would load (at most <see cref="MaxRooms"/>), and releases the
    /// textures held for rooms not in the list. Also used while the main menu shows (the start room).
    /// </summary>
    public void PrefetchRooms(IEnumerable<string> roomIds)
    {
        if (!Enabled) return;
        var game = GameRuntime.Instance;
        var rooms = roomIds.Where(t => game.Content.FindRoom(t) is not null).Distinct().Take(MaxRooms).ToList();
        var wanted = new List<string>(); // paintings of every room first, then the providers' sprites
        foreach (var to in rooms) wanted.AddRange(PathsOf(to));
        foreach (var to in rooms)
        {
            RoomView view;
            try { view = ViewBuilder.Room(game.Content, game.State, to); }
            catch (Exception) { continue; } // a room the current state cannot show; nothing to preload
            foreach (var provider in PathProviders) wanted.AddRange(provider(view));
        }
        var ordered = wanted.Distinct(StringComparer.Ordinal).ToList();
        var wantedSet = new HashSet<string>(ordered, StringComparer.Ordinal);
        // Release what is no longer next door (the displayed room holds its own textures).
        foreach (var path in held.Keys.Where(p => !wantedSet.Contains(p)).ToList()) held.Remove(path);
        foreach (var path in ordered)
        {
            if (held.ContainsKey(path) || pending.Contains(path) || !ResourceLoader.Exists(path)) continue;
            if (ResourceLoader.HasCached(path))
            {
                if (ResourceLoader.Load(path) is Texture2D cached) held[path] = cached;
                continue;
            }
            if (ResourceLoader.LoadThreadedRequest(path, "Texture2D", false) == Error.Ok) pending.Add(path);
        }
        SetProcess(pending.Count > 0);
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        foreach (var path in pending.ToList())
        {
            var status = ResourceLoader.LoadThreadedGetStatus(path);
            if (status == ResourceLoader.ThreadLoadStatus.InProgress) continue;
            pending.Remove(path);
            if (status == ResourceLoader.ThreadLoadStatus.Loaded && ResourceLoader.LoadThreadedGet(path) is Texture2D texture)
            {
                held[path] = texture;
                Loaded++;
            }
        }
        if (pending.Count == 0) SetProcess(false);
    }

    /// <summary>The background and foreground mask a room build would load (natural blocking or template).</summary>
    private static IEnumerable<string> PathsOf(string roomId)
    {
        if (RoomBlocking.For(roomId) is { } blocking)
        {
            yield return "res://assets/" + (blocking.Background ?? $"bg_natural/{roomId}.webp");
            yield return "res://assets/" + (blocking.ForegroundMask ?? $"fg_natural/{roomId}.webp");
            foreach (var occluder in blocking.Occluders)
                if (occluder.Texture is { } texture) yield return "res://assets/" + texture;
            yield break;
        }
        if (GameRuntime.Instance.Content.FindRoom(roomId) is { } def && !string.IsNullOrEmpty(def.BackgroundAsset))
            yield return "res://assets/" + def.BackgroundAsset;
    }
}
