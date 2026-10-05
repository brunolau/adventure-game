using System.Collections.Generic;
using Godot;

namespace LastBell.Game.Audio;

/// <summary>Loads (and caches) audio streams from res://assets/ paths; missing files return null.</summary>
public static class AudioStreams
{
    private static readonly Dictionary<string, AudioStream?> Cache = new();

    /// <summary>res:// path of an asset path ("music/1960.ogg" → "res://assets/music/1960.ogg").</summary>
    public static string ResPath(string assetPath) =>
        assetPath.StartsWith("res://", System.StringComparison.Ordinal) ? assetPath : "res://assets/" + assetPath;

    /// <summary>True when the file exists in the project (imported or not yet).</summary>
    public static bool Exists(string assetPath) => ResourceLoader.Exists(ResPath(assetPath));

    /// <summary>The stream, or null when the file is missing or cannot be loaded.</summary>
    public static AudioStream? Get(string assetPath)
    {
        if (string.IsNullOrEmpty(assetPath)) return null;
        string path = ResPath(assetPath);
        if (Cache.TryGetValue(path, out var cached)) return cached;
        AudioStream? stream = ResourceLoader.Exists(path) ? ResourceLoader.Load<AudioStream>(path) : null;
        Cache[path] = stream;
        return stream;
    }

    /// <summary>A looping stream: OGG Vorbis loops from <paramref name="loopOffset"/> to the end of the file.</summary>
    public static AudioStream? GetLooping(string assetPath, double loopOffset)
    {
        var stream = Get(assetPath);
        switch (stream)
        {
            case AudioStreamOggVorbis ogg:
                ogg.Loop = true;
                ogg.LoopOffset = loopOffset;
                break;
            case AudioStreamMP3 mp3:
                mp3.Loop = true;
                mp3.LoopOffset = loopOffset;
                break;
        }
        return stream;
    }

    /// <summary>Drops the cache (at exit, so no resource stays referenced by a static).</summary>
    public static void Clear()
    {
        foreach (var stream in Cache.Values) stream?.Dispose(); // release the managed references (no GC at exit)
        Cache.Clear();
    }

    /// <summary>A one-shot stream (loop off).</summary>
    public static AudioStream? GetOneShot(string assetPath)
    {
        var stream = Get(assetPath);
        if (stream is AudioStreamOggVorbis ogg) ogg.Loop = false;
        else if (stream is AudioStreamMP3 mp3) mp3.Loop = false;
        return stream;
    }
}
