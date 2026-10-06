using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using LastBell.Core.State;

namespace LastBell.Game.Audio;

/// <summary>
/// Room ambience on the "Ambience" bus, built from data/audio/ambience.json: seamless bed loops
/// (plain stereo players) and one-shot spots fired at random intervals from a random x position on
/// the 1920 px canvas (AudioStreamPlayer2D, so a dog barks from the left or the right). Layers can
/// depend on progress (<c>after</c> / <c>until</c> action ids, e.g. S55 birds after E10). A room
/// change crossfades the old layer set out and the new one in.
/// </summary>
public partial class AmbiencePlayer : Node
{
    private sealed class LayerNode
    {
        public AmbienceLayer Layer = null!;
        public AmbienceSound Sound = null!;
        public AudioStreamPlayer? Bed;
        public AudioStreamPlayer2D? Spot;
        public double NextAt;
        public int LastTake = -1;
    }

    private sealed class LayerSet
    {
        public Node Root = null!;
        public string Key = "";
        public List<LayerNode> Layers = new();
        public float Gain;
        public float Target;
    }

    private readonly List<LayerSet> sets = new();
    private readonly RandomNumberGenerator rng = new();
    private LayerSet? current;
    private string? silentKey;
    private float masterDb;
    private float masterTargetDb;
    private double clock;

    /// <summary>Catalog with the library and the room layers.</summary>
    public AudioCatalog Catalog { get; set; } = new();

    /// <summary>Fade time of a room change, seconds.</summary>
    public float FadeSeconds { get; set; } = 1.2f;

    /// <summary>Room whose layers are playing ("" = none).</summary>
    public string CurrentRoom { get; private set; } = "";

    /// <inheritdoc />
    public override void _Ready() => rng.Randomize();

    /// <summary>Overall level offset (ducking for overlays, silence for the main menu).</summary>
    public void SetLevel(float db) => masterTargetDb = db;

    private readonly Dictionary<string, List<AmbienceLayer>> naturalLayers = new(StringComparer.Ordinal);

    /// <summary>
    /// All layers of a room: ambience.json's, or, for a room with a natural blocking that has an
    /// <c>audio.ambience</c> override (World/RoomBlocking.cs, e.g. the bus at the 1982 stop S57), the override
    /// (<c>ambience_mode</c> "replace", default) or ambience.json's plus the override ("add"). Presentation only.
    /// </summary>
    public IReadOnlyList<AmbienceLayer> LayersOf(string roomId)
    {
        var template = Catalog.RoomAmbience.TryGetValue(roomId, out var l) ? l : new List<AmbienceLayer>();
        if (LastBell.Game.World.RoomBlocking.For(roomId)?.Audio is not { AmbienceLayers: { } entries } audio) return template;
        string key = roomId + (audio.AddToTemplate ? "+" : "=");
        if (!naturalLayers.TryGetValue(key, out var merged))
        {
            var own = Catalog.ParseAmbienceLayers(roomId, entries);
            merged = audio.AddToTemplate ? template.Concat(own).ToList() : own;
            naturalLayers[key] = merged;
        }
        return merged;
    }

    /// <summary>The layers of a room that apply in a state (after/until conditions).</summary>
    public IReadOnlyList<AmbienceLayer> ActiveLayers(string roomId, GameState? state)
    {
        var layers = LayersOf(roomId);
        if (layers.Count == 0) return Array.Empty<AmbienceLayer>();
        return layers.Where(l => (l.After is null || (state?.IsDone(l.After) ?? false)) &&
                                 (l.Until is null || !(state?.IsDone(l.Until) ?? false))).ToList();
    }

    /// <summary>Plays the ambience of a room in a state (no-op when the same layer set already plays).</summary>
    public void Sync(string roomId, GameState? state)
    {
        var layers = ActiveLayers(roomId, state);
        string key = roomId + "|" + string.Join(",", layers.Select(l => l.Sound));
        if (current is not null && current.Key == key) return;
        if (current is null && layers.Count == 0 && silentKey == key) return; // already silent (e.g. a room without ambience data)
        if (current is not null) current.Target = 0f;
        current = null;
        CurrentRoom = roomId;
        silentKey = layers.Count == 0 ? key : null;
        if (layers.Count == 0)
        {
            AudioService.Log($"ambience -> {roomId}: (none)");
            return;
        }
        var set = new LayerSet { Root = new Node { Name = "Ambience_" + roomId }, Key = key, Target = 1f };
        AddChild(set.Root);
        foreach (var layer in layers)
        {
            if (!Catalog.AmbienceLibrary.TryGetValue(layer.Sound, out var sound) || sound.Files.Count == 0) continue;
            var node = new LayerNode { Layer = layer, Sound = sound };
            if (sound.IsLoop)
            {
                var stream = AudioStreams.GetLooping(sound.Files[0], 0.0);
                if (stream is null) continue;
                node.Bed = new AudioStreamPlayer { Bus = AudioService.BusOrMaster("Ambience"), Stream = stream, VolumeDb = -80f };
                set.Root.AddChild(node.Bed);
                // start each bed at a random point so rooms that share a bed do not sound identical
                double length = stream.GetLength();
                node.Bed.Play(length > 4 ? (float)rng.RandfRange(0f, (float)length - 2f) : 0f);
            }
            else
            {
                node.Spot = new AudioStreamPlayer2D
                {
                    Bus = AudioService.BusOrMaster("Ambience"), Attenuation = 0f, MaxDistance = 100000f, PanningStrength = 0.7f,
                };
                set.Root.AddChild(node.Spot);
                node.NextAt = clock + rng.RandfRange(1.5f, Mathf.Max(2f, layer.EveryMin));
            }
            set.Layers.Add(node);
        }
        sets.Add(set);
        current = set;
        AudioService.Log($"ambience -> {roomId}: {string.Join(", ", set.Layers.Select(l => $"{l.Sound.Id}({l.Sound.Kind} {l.Layer.VolumeDb:+0;-0}dB)"))}");
    }

    /// <summary>Fades everything out.</summary>
    public void Stop()
    {
        if (current is not null) current.Target = 0f;
        current = null;
        CurrentRoom = "";
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        float dt = (float)delta;
        clock += delta;
        masterDb = Mathf.MoveToward(masterDb, masterTargetDb, 30f * dt);
        for (int i = sets.Count - 1; i >= 0; i--)
        {
            var set = sets[i];
            set.Gain = Mathf.MoveToward(set.Gain, set.Target, dt / Mathf.Max(0.05f, FadeSeconds));
            if (set.Gain <= 0f && set.Target <= 0f)
            {
                set.Root.QueueFree();
                sets.RemoveAt(i);
                continue;
            }
            float setDb = Mathf.LinearToDb(Mathf.Max(Mathf.Sin(set.Gain * Mathf.Pi / 2f), 0.0001f)) + masterDb;
            foreach (var layer in set.Layers)
            {
                if (layer.Bed is { } bed) bed.VolumeDb = setDb + layer.Layer.VolumeDb;
                else if (layer.Spot is { } spot)
                {
                    spot.VolumeDb = setDb + layer.Layer.VolumeDb;
                    if (ReferenceEquals(set, current) && clock >= layer.NextAt) Fire(layer);
                }
            }
        }
    }

    private void Fire(LayerNode layer)
    {
        var spot = layer.Spot!;
        var files = layer.Sound.Files;
        int take = files.Count == 1 ? 0 : rng.RandiRange(0, files.Count - 1);
        if (files.Count > 1 && take == layer.LastTake) take = (take + 1) % files.Count;
        layer.LastTake = take;
        layer.NextAt = clock + rng.RandfRange(layer.Layer.EveryMin, Mathf.Max(layer.Layer.EveryMin, layer.Layer.EveryMax));
        var stream = AudioStreams.GetOneShot(files[take]);
        if (stream is null) return;
        spot.Stream = stream;
        spot.PitchScale = 1f + rng.RandfRange(-layer.Layer.PitchJitter, layer.Layer.PitchJitter);
        // canvas x (1920 px base): the default 2D listener sits at the viewport centre, so x pans the spot
        float x = rng.RandfRange(layer.Layer.XMin, Mathf.Max(layer.Layer.XMin, layer.Layer.XMax));
        spot.GlobalPosition = new Vector2(x, 540f);
        spot.Play();
    }
}
