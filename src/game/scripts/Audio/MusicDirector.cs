using System;
using System.Collections.Generic;
using Godot;

namespace LastBell.Game.Audio;

/// <summary>
/// Two music players on the "Music" bus with an equal-power crossfade. <see cref="Request"/> names the
/// wanted track; a change fades the old one out and the new one in. A track that was faded out in
/// the last two minutes resumes where it stopped (era theme → puzzle cue → back), otherwise it starts
/// from 0 (its intro) and then loops from the loop point in data/audio/music.json.
/// </summary>
public partial class MusicDirector : Node
{
    private sealed class Deck
    {
        public AudioStreamPlayer Player = null!;
        public string Path = "";
        public float Gain;      // current linear gain 0..1
        public float Target;    // target linear gain
        public float Rate;      // gain units per second
    }

    private readonly Deck[] decks = new Deck[2];
    private readonly Dictionary<string, (double Position, ulong StoppedMs)> resume = new(StringComparer.Ordinal);
    private int active;
    private float duckDb;
    private float duckTargetDb;

    /// <summary>Catalog with loop points.</summary>
    public AudioCatalog Catalog { get; set; } = new();

    /// <summary>Path of the track that is (or is fading) in, "" for silence.</summary>
    public string Current => decks[active].Path;

    /// <summary>Raised when the requested track changes (path, "" = silence).</summary>
    public event Action<string>? TrackChanged;

    /// <inheritdoc />
    public override void _Ready()
    {
        for (int i = 0; i < decks.Length; i++)
        {
            var player = new AudioStreamPlayer { Name = "MusicDeck" + i, Bus = AudioService.BusOrMaster("Music"), VolumeDb = -80f };
            AddChild(player);
            decks[i] = new Deck { Player = player };
        }
    }

    /// <summary>Ducks the music (e.g. while a voice line plays); 0 = no duck.</summary>
    public void SetDuck(float db) => duckTargetDb = Mathf.Min(0f, db);

    /// <summary>Asks for a track (asset path relative to res://assets/, "" = silence).</summary>
    public void Request(string path, float? fadeSeconds = null)
    {
        path ??= "";
        if (path.Length > 0 && AudioStreams.Get(path) is null) path = ""; // missing file: silence
        if (path == decks[active].Path) return;
        float fade = Mathf.Max(0.05f, fadeSeconds ?? Catalog.CrossfadeSeconds);
        var old = decks[active];
        if (old.Path.Length > 0)
        {
            if (old.Player.Playing) resume[old.Path] = (old.Player.GetPlaybackPosition(), Time.GetTicksMsec());
            old.Target = 0f;
            old.Rate = 1f / fade;
        }
        active = 1 - active;
        var deck = decks[active];
        bool sameStillPlaying = path.Length > 0 && deck.Path == path && deck.Player.Playing;
        if (deck.Path.Length > 0 && deck.Player.Playing && deck.Path != path)
            resume[deck.Path] = (deck.Player.GetPlaybackPosition(), Time.GetTicksMsec());
        deck.Path = path;
        if (sameStillPlaying)
        {
            deck.Target = 1f; // it was still fading out: bring it back without a restart
            deck.Rate = 1f / fade;
        }
        else if (path.Length == 0)
        {
            deck.Player.Stop();
            deck.Gain = deck.Target = 0f;
        }
        else
        {
            double loop = Catalog.Tracks.TryGetValue(path, out var track) ? track.LoopStart : 0.0;
            deck.Player.Stream = AudioStreams.GetLooping(path, loop);
            double from = 0.0;
            if (resume.TryGetValue(path, out var r) && Time.GetTicksMsec() - r.StoppedMs < 120_000) from = r.Position;
            deck.Gain = deck.Player.Playing ? deck.Gain : 0f;
            deck.Player.Play((float)from);
            deck.Target = 1f;
            deck.Rate = 1f / fade;
        }
        AudioService.Log($"music -> {(path.Length > 0 ? path : "(silence)")} fade {fade:0.0}s");
        TrackChanged?.Invoke(path);
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        float dt = (float)delta;
        duckDb = Mathf.MoveToward(duckDb, duckTargetDb, 12f * dt);
        foreach (var deck in decks)
        {
            if (deck.Player is null) continue;
            deck.Gain = Mathf.MoveToward(deck.Gain, deck.Target, deck.Rate * dt);
            if (deck.Gain <= 0.0001f && deck.Target <= 0f)
            {
                if (deck.Player.Playing) deck.Player.Stop();
                if (!ReferenceEquals(deck, decks[active])) deck.Path = "";
                deck.Player.VolumeDb = -80f;
                continue;
            }
            // equal-power curve: perceived loudness stays even through the crossfade
            float g = Mathf.Sin(deck.Gain * Mathf.Pi / 2f);
            deck.Player.VolumeDb = Mathf.LinearToDb(Mathf.Max(g, 0.0001f)) + duckDb;
        }
    }
}
