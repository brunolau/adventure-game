using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Godot;

namespace LastBell.Game.Audio;

/// <summary>Loop points of one music file (seconds; the file plays once from 0, then loops LoopStart..end).</summary>
/// <param name="Path">Asset path relative to res://assets/ (as in game.json rooms[].music).</param>
/// <param name="LoopStart">Loop offset in seconds.</param>
public sealed record MusicTrack(string Path, double LoopStart);

/// <summary>A presentation-only music override for a room (e.g. the tension cue in the S49 confrontation).</summary>
/// <param name="Cue">Cue name (see <see cref="AudioCatalog.Cues"/>) or an asset path.</param>
/// <param name="After">Only after this action id is done (null = always).</param>
/// <param name="Until">Only until this action id is done (null = always).</param>
public sealed record RoomMusicOverride(string Cue, string? After, string? Until);

/// <summary>One ambience layer of a room.</summary>
/// <param name="Sound">Library id.</param>
/// <param name="VolumeDb">Gain relative to the normalised library file.</param>
/// <param name="EveryMin">Spots: minimum seconds between two plays.</param>
/// <param name="EveryMax">Spots: maximum seconds between two plays.</param>
/// <param name="XMin">Spots: left end of the canvas x range the sound comes from (stereo position).</param>
/// <param name="XMax">Spots: right end of that range.</param>
/// <param name="PitchJitter">Spots: random pitch scale +- this value.</param>
/// <param name="After">Layer only after this action id is done.</param>
/// <param name="Until">Layer only until this action id is done.</param>
public sealed record AmbienceLayer(string Sound, float VolumeDb, float EveryMin, float EveryMax, float XMin, float XMax,
    float PitchJitter, string? After, string? Until);

/// <summary>A library entry of the ambience set: a seamless bed loop or a one-shot spot (several takes).</summary>
/// <param name="Id">Library id.</param>
/// <param name="Kind">"loop" or "spot".</param>
/// <param name="Files">Asset paths relative to res://assets/.</param>
public sealed record AmbienceSound(string Id, string Kind, IReadOnlyList<string> Files)
{
    /// <summary>True for a looping bed.</summary>
    public bool IsLoop => Kind == "loop";
}

/// <summary>A sound effect id (actions[].sfx or a UI event) with its takes and mix settings.</summary>
/// <param name="Id">Sound id.</param>
/// <param name="Files">Asset paths relative to res://assets/ (one is picked at random, never the same twice in a row).</param>
/// <param name="VolumeDb">Gain.</param>
/// <param name="PitchJitter">Random pitch scale +- this value.</param>
/// <param name="Bus">Audio bus (SFX by default).</param>
/// <param name="CooldownSeconds">Minimum time between two plays of this id.</param>
public sealed record SfxDef(string Id, IReadOnlyList<string> Files, float VolumeDb, float PitchJitter, string Bus, float CooldownSeconds);

/// <summary>
/// Data of the audio service: <c>data/audio/music.json</c> (loop points, cues, overrides),
/// <c>data/audio/ambience.json</c> (library + per-room layers) and <c>data/audio/sfx.json</c>
/// (sound ids, UI event mapping). Missing files or entries simply mean silence.
/// </summary>
public sealed class AudioCatalog
{
    /// <summary>Data folder.</summary>
    public const string DataDir = "res://data/audio";

    /// <summary>Loop points by asset path (e.g. "music/1960.ogg").</summary>
    public Dictionary<string, MusicTrack> Tracks { get; } = new(StringComparer.Ordinal);

    /// <summary>Named cues ("menu", "puzzle", "tension", "epilogue") to asset paths.</summary>
    public Dictionary<string, string> Cues { get; } = new(StringComparer.Ordinal);

    /// <summary>Cutscene id to cue name or asset path (music while that cutscene plays).</summary>
    public Dictionary<string, string> CutsceneMusic { get; } = new(StringComparer.Ordinal);

    /// <summary>Room id to presentation-only music overrides (first match wins).</summary>
    public Dictionary<string, List<RoomMusicOverride>> RoomMusic { get; } = new(StringComparer.Ordinal);

    /// <summary>Default music crossfade in seconds.</summary>
    public float CrossfadeSeconds { get; private set; } = 2.0f;

    /// <summary>Ambience library by id.</summary>
    public Dictionary<string, AmbienceSound> AmbienceLibrary { get; } = new(StringComparer.Ordinal);

    /// <summary>Ambience layers by room id.</summary>
    public Dictionary<string, List<AmbienceLayer>> RoomAmbience { get; } = new(StringComparer.Ordinal);

    /// <summary>Sound effects by id.</summary>
    public Dictionary<string, SfxDef> Sfx { get; } = new(StringComparer.Ordinal);

    /// <summary>UI / game event name (e.g. "button_click", "inventory_open") to sound id.</summary>
    public Dictionary<string, string> Events { get; } = new(StringComparer.Ordinal);

    /// <summary>Problems found while loading (reported by the audio report).</summary>
    public List<string> Warnings { get; } = new();

    /// <summary>Loads the three data files.</summary>
    public static AudioCatalog Load()
    {
        var catalog = new AudioCatalog();
        catalog.LoadMusic(ReadJson("music.json", catalog.Warnings));
        catalog.LoadAmbience(ReadJson("ambience.json", catalog.Warnings));
        catalog.LoadSfx(ReadJson("sfx.json", catalog.Warnings));
        return catalog;
    }

    /// <summary>Resolves a cue name or an asset path to an asset path ("" if unknown).</summary>
    public string ResolveCue(string cueOrPath) =>
        Cues.TryGetValue(cueOrPath, out var path) ? path : cueOrPath.EndsWith(".ogg", StringComparison.Ordinal) ? cueOrPath : "";

    private static JsonObject? ReadJson(string file, List<string> warnings)
    {
        string path = DataDir + "/" + file;
        if (!FileAccess.FileExists(path))
        {
            warnings.Add("missing " + path);
            return null;
        }
        try
        {
            return JsonNode.Parse(FileAccess.GetFileAsString(path)) as JsonObject;
        }
        catch (Exception e)
        {
            warnings.Add($"cannot parse {path}: {e.Message}");
            return null;
        }
    }

    private static string? Str(JsonNode? node) => node is JsonValue v && v.TryGetValue(out string? s) ? s : null;

    private static float Num(JsonNode? node, float fallback) =>
        node is JsonValue v ? (v.TryGetValue(out double d) ? (float)d : v.TryGetValue(out int i) ? i : fallback) : fallback;

    private static (float, float) Range(JsonNode? node, float a, float b) =>
        node is JsonArray arr && arr.Count == 2 ? (Num(arr[0], a), Num(arr[1], b)) : (a, b);

    private void LoadMusic(JsonObject? root)
    {
        if (root is null) return;
        CrossfadeSeconds = Num(root["crossfade_seconds"], CrossfadeSeconds);
        if (root["tracks"] is JsonObject tracks)
        {
            foreach (var (_, node) in tracks)
            {
                if (node is not JsonObject t || Str(t["file"]) is not { } file) continue;
                Tracks[file] = new MusicTrack(file, Num(t["loop_start"], 0f));
            }
        }
        if (root["cues"] is JsonObject cues)
            foreach (var (name, node) in cues)
                if (Str(node) is { } path) Cues[name] = path;
        if (root["cutscenes"] is JsonObject cutscenes)
            foreach (var (id, node) in cutscenes)
                if (Str(node) is { } cue) CutsceneMusic[id] = cue;
        if (root["rooms"] is JsonObject rooms)
        {
            foreach (var (id, node) in rooms)
            {
                var list = new List<RoomMusicOverride>();
                foreach (var entry in node as JsonArray ?? new JsonArray())
                    if (entry is JsonObject o && Str(o["cue"]) is { } cue)
                        list.Add(new RoomMusicOverride(cue, Str(o["after"]), Str(o["until"])));
                RoomMusic[id] = list;
            }
        }
    }

    private void LoadAmbience(JsonObject? root)
    {
        if (root is null) return;
        if (root["library"] is JsonObject library)
        {
            foreach (var (id, node) in library)
            {
                if (node is not JsonObject o) continue;
                var files = (o["files"] as JsonArray)?.Select(Str).Where(f => f is not null).Select(f => f!).ToList() ?? new List<string>();
                AmbienceLibrary[id] = new AmbienceSound(id, Str(o["kind"]) ?? "loop", files);
            }
        }
        if (root["rooms"] is JsonObject rooms)
        {
            foreach (var (roomId, node) in rooms)
            {
                var layers = new List<AmbienceLayer>();
                foreach (var entry in (node as JsonObject)?["layers"] as JsonArray ?? new JsonArray())
                {
                    if (entry is not JsonObject o || Str(o["sound"]) is not { } sound) continue;
                    if (!AmbienceLibrary.ContainsKey(sound)) Warnings.Add($"ambience {roomId}: unknown sound {sound}");
                    var (emin, emax) = Range(o["every"], 8f, 20f);
                    var (xmin, xmax) = Range(o["x"], 200f, 1720f);
                    layers.Add(new AmbienceLayer(sound, Num(o["db"], 0f), emin, emax, xmin, xmax, Num(o["pitch"], 0.04f),
                        Str(o["after"]), Str(o["until"])));
                }
                RoomAmbience[roomId] = layers;
            }
        }
    }

    private void LoadSfx(JsonObject? root)
    {
        if (root is null) return;
        if (root["sounds"] is JsonObject sounds)
        {
            foreach (var (id, node) in sounds)
            {
                if (node is not JsonObject o) continue;
                var files = (o["files"] as JsonArray)?.Select(Str).Where(f => f is not null).Select(f => f!).ToList() ?? new List<string>();
                Sfx[id] = new SfxDef(id, files, Num(o["db"], 0f), Num(o["pitch"], 0.03f), Str(o["bus"]) ?? "SFX", Num(o["cooldown"], 0.05f));
            }
        }
        if (root["events"] is JsonObject events)
            foreach (var (name, node) in events)
                if (Str(node) is { } id) Events[name] = id;
    }
}
