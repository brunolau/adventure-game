using System;
using System.Collections.Generic;
using Godot;

namespace LastBell.Game.Audio;

/// <summary>
/// One-shot sound effects by id (data/audio/sfx.json): a small pool of players per bus, a random
/// take (never the same one twice in a row), a little random pitch, and a per-id cooldown so a
/// burst of identical events (hovering along a row of buttons) does not stack.
/// </summary>
public partial class SfxPlayer : Node
{
    private const int PoolSize = 10;
    private readonly List<AudioStreamPlayer> pool = new();
    private readonly Dictionary<string, ulong> lastPlayed = new(StringComparer.Ordinal);
    private readonly Dictionary<string, int> lastTake = new(StringComparer.Ordinal);
    private readonly HashSet<string> warned = new(StringComparer.Ordinal);
    private readonly RandomNumberGenerator rng = new();
    private int next;

    /// <summary>Catalog with the sound ids.</summary>
    public AudioCatalog Catalog { get; set; } = new();

    /// <inheritdoc />
    public override void _Ready()
    {
        rng.Randomize();
        for (int i = 0; i < PoolSize; i++)
        {
            var player = new AudioStreamPlayer { Name = "Sfx" + i, Bus = AudioService.BusOrMaster("SFX") };
            AddChild(player);
            pool.Add(player);
        }
    }

    /// <summary>True when the id exists in the catalog.</summary>
    public bool Has(string id) => Catalog.Sfx.ContainsKey(id);

    /// <summary>Plays a sound id; unknown ids are ignored (logged once). Returns true if something started.</summary>
    public bool Play(string id, float extraDb = 0f)
    {
        if (string.IsNullOrEmpty(id)) return false;
        if (!Catalog.Sfx.TryGetValue(id, out var def) || def.Files.Count == 0)
        {
            if (warned.Add(id)) AudioService.Log($"sfx '{id}' has no sound (data/audio/sfx.json)");
            return false;
        }
        ulong now = Time.GetTicksMsec();
        if (lastPlayed.TryGetValue(id, out var at) && now - at < (ulong)(def.CooldownSeconds * 1000f)) return false;
        lastPlayed[id] = now;
        int take = def.Files.Count == 1 ? 0 : rng.RandiRange(0, def.Files.Count - 1);
        if (def.Files.Count > 1 && lastTake.TryGetValue(id, out var prev) && prev == take) take = (take + 1) % def.Files.Count;
        lastTake[id] = take;
        var stream = AudioStreams.GetOneShot(def.Files[take]);
        if (stream is null)
        {
            if (warned.Add(id + "#" + take)) AudioService.Log($"sfx '{id}': missing file {def.Files[take]}");
            return false;
        }
        var player = FreePlayer();
        player.Bus = AudioService.BusOrMaster(def.Bus);
        player.Stream = stream;
        player.VolumeDb = def.VolumeDb + extraDb;
        player.PitchScale = 1f + rng.RandfRange(-def.PitchJitter, def.PitchJitter);
        player.Play();
        AudioService.LogVerbose($"sfx {id} ({def.Files[take]})");
        return true;
    }

    private AudioStreamPlayer FreePlayer()
    {
        foreach (var p in pool)
            if (!p.Playing) return p;
        next = (next + 1) % pool.Count; // all busy: steal the oldest-ish one
        return pool[next];
    }
}
