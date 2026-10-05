using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Godot;

namespace LastBell.Game.Living.Actors;

/// <summary>One horizontal-strip sprite sheet (frame i at x = i * cell width).</summary>
public sealed class SpriteSheet
{
    /// <summary>Sheet texture.</summary>
    public required Texture2D Texture { get; init; }

    /// <summary>Cell size in px.</summary>
    public required Vector2I Cell { get; init; }

    /// <summary>Feet centre (or sill line centre for window busts) inside a cell.</summary>
    public required Vector2 Pivot { get; init; }

    /// <summary>Number of cells.</summary>
    public required int Frames { get; init; }

    /// <summary>Authored playback rate.</summary>
    public float Fps { get; init; } = 8f;

    /// <summary>Ground speed of a walk sheet in px/s at scale 1 (null if not a side walk).</summary>
    public float? StridePxPerSecond { get; init; }

    /// <summary>Optional frame names (NPC still sheets: idle, blink, talk_a, talk_b, gesture).</summary>
    public IReadOnlyList<string> FrameNames { get; init; } = Array.Empty<string>();

    /// <summary>Frames that show a blink inside an idle loop (hero idle sheets).</summary>
    public IReadOnlyList<int> BlinkFrames { get; init; } = Array.Empty<int>();

    /// <summary>Indices of "rest" mouth frames in a talk sheet.</summary>
    public IReadOnlyList<int> RestFrames { get; init; } = Array.Empty<int>();

    /// <summary>True when the pivot is a window sill line rather than the feet.</summary>
    public bool PivotIsSillLine { get; init; }

    /// <summary>Region of a frame in the texture.</summary>
    public Rect2 Region(int frame) => new(Math.Clamp(frame, 0, Frames - 1) * Cell.X, 0, Cell.X, Cell.Y);

    private static readonly Dictionary<string, SpriteSheet?> Cache = new(StringComparer.Ordinal);

    /// <summary>Loads (cached) a sheet from its JSON sidecar and image path; null if either is missing.</summary>
    public static SpriteSheet? Load(string imagePath, string jsonPath)
    {
        string key = imagePath + "|" + jsonPath;
        if (Cache.TryGetValue(key, out var cached)) return cached;
        SpriteSheet? sheet = null;
        var meta = Json.Load(jsonPath, warnIfMissing: false);
        if (meta is not null && ResourceLoader.Exists(imagePath) && GD.Load<Texture2D>(imagePath) is { } texture)
        {
            var cell = meta.Vec("cell");
            int frames = Math.Max(1, meta.Int("frames", 1));
            if (cell.X <= 0 || cell.Y <= 0) cell = new Vector2(texture.GetWidth() / (float)frames, texture.GetHeight());
            var names = meta.Strings("frame_names");
            var rest = new List<int>();
            var mouth = meta.Strings("mouth_sequence");
            for (int i = 0; i < mouth.Count; i++)
                if (mouth[i] == "rest") rest.Add(i);
            sheet = new SpriteSheet
            {
                Texture = texture,
                Cell = new Vector2I((int)cell.X, (int)cell.Y),
                Pivot = meta.Vec("pivot", new Vector2(cell.X / 2, cell.Y)),
                Frames = frames,
                Fps = meta.Num("playback_fps", 8f),
                StridePxPerSecond = meta.NumOrNull("stride_px_per_s"),
                FrameNames = names,
                BlinkFrames = meta.Ints("blink_frames"),
                RestFrames = rest,
                PivotIsSillLine = meta.Bool("pivot_is_sill_line"),
            };
        }
        Cache[key] = sheet;
        return sheet;
    }
}

/// <summary>A playable animation: frames of one sheet with timing.</summary>
public sealed class Clip
{
    /// <summary>Clip name (idle_right, talk, gesture ...).</summary>
    public required string Name { get; init; }

    /// <summary>Source sheet.</summary>
    public required SpriteSheet Sheet { get; init; }

    /// <summary>Cell indices in playback order.</summary>
    public required int[] Frames { get; init; }

    /// <summary>Playback rate.</summary>
    public float Fps { get; init; } = 8f;

    /// <summary>Loops (else plays once and holds the last frame).</summary>
    public bool Loop { get; init; } = true;

    /// <summary>For single-frame clips: how long the frame is held (blink, gesture).</summary>
    public float HoldSeconds { get; init; }

    /// <summary>Random interval for occasional clips (blink, fidget), else null.</summary>
    public Vector2? EverySeconds { get; init; }

    /// <summary>Sheet faces right and is mirrored for left (three-quarter NPC views, hero side sheets).</summary>
    public bool MirrorForLeft { get; init; } = true;

    /// <summary>Duration of one pass.</summary>
    public float Length => Frames.Length / Math.Max(0.01f, Fps);

    /// <summary>Cell index at a playback position (frames, may exceed the length for loops).</summary>
    public int CellAt(int index) => Frames.Length == 0 ? 0 : Frames[Loop ? ((index % Frames.Length) + Frames.Length) % Frames.Length : Math.Clamp(index, 0, Frames.Length - 1)];
}

/// <summary>
/// The animations of one character, loaded from <c>res://assets/actors/&lt;ID&gt;/</c>. Two manifest
/// formats are read: the hero's <c>animations.json</c> (one sheet per animation, <c>*_mask2020</c>
/// variants) and the NPCs' <c>actor.json</c> (named sheets, frame-name sequences, optional
/// window variants). Clip names are the manifest's names.
/// </summary>
public sealed class ActorAnimationSet
{
    private readonly Dictionary<string, Clip> clips = new(StringComparer.Ordinal);

    /// <summary>Character id.</summary>
    public string CharacterId { get; }

    /// <summary>Standing figure height at scale 1.</summary>
    public float HeightPx { get; private set; } = 512f;

    /// <summary>True for the hero format (directional sheets).</summary>
    public bool IsDirectional { get; private set; }

    /// <summary>Variant this set was built for (null = default).</summary>
    public string? Variant { get; }

    private ActorAnimationSet(string characterId, string? variant)
    {
        CharacterId = characterId;
        Variant = variant;
    }

    /// <summary>Clip by name, or null.</summary>
    public Clip? Get(string name) => clips.TryGetValue(name, out var c) ? c : null;

    /// <summary>All clip names.</summary>
    public IEnumerable<string> Names => clips.Keys;

    /// <summary>Folder of a character's sheets.</summary>
    public static string FolderOf(string characterId) => $"res://assets/actors/{characterId}";

    /// <summary>True when sprite data exists for the character.</summary>
    public static bool Exists(string characterId) =>
        Godot.FileAccess.FileExists(FolderOf(characterId) + "/animations.json") || Godot.FileAccess.FileExists(FolderOf(characterId) + "/actor.json");

    private static readonly Dictionary<string, ActorAnimationSet?> Cache = new(StringComparer.Ordinal);

    /// <summary>
    /// Loads the set. <paramref name="variant"/>: hero "mask2020" (falls back per clip to the default
    /// sheet), NPC variant names from actor.json ("window_glass", "window"); null = the manifest default.
    /// </summary>
    public static ActorAnimationSet? Load(string characterId, string? variant)
    {
        string key = characterId + "|" + (variant ?? "");
        if (Cache.TryGetValue(key, out var cached)) return cached;
        ActorAnimationSet? set = null;
        string folder = FolderOf(characterId);
        try
        {
            if (Json.Load(folder + "/animations.json", warnIfMissing: false) is { } hero) set = LoadDirectional(characterId, folder, hero, variant);
            else if (Json.Load(folder + "/actor.json", warnIfMissing: false) is { } npc) set = LoadNpc(characterId, folder, npc, variant);
        }
        catch (Exception ex)
        {
            GD.PushError($"Living: actor sheets of {characterId} failed to load: {ex.Message}");
            set = null;
        }
        if (set is not null && set.clips.Count == 0) set = null;
        Cache[key] = set;
        return set;
    }

    private static ActorAnimationSet LoadDirectional(string id, string folder, JsonObject manifest, string? variant)
    {
        var set = new ActorAnimationSet(id, variant) { IsDirectional = true, HeightPx = manifest.Num("standing_height_px", 512) };
        if (manifest.Obj("animations") is not { } anims) return set;
        // Default sheets first, then the variant overrides the same base names.
        foreach (var pass in new[] { "default", variant })
        {
            if (pass is null) continue;
            foreach (var (name, node) in anims)
            {
                if (node is not JsonObject a) continue;
                string v = a.Str("variant", "default")!;
                if (v != pass) continue;
                string baseName = v == "default" ? name : name.EndsWith("_" + v, StringComparison.Ordinal) ? name[..^(v.Length + 1)] : name;
                string image = a.Str("image", name + ".webp")!;
                string json = System.IO.Path.ChangeExtension(image, ".json");
                var sheet = SpriteSheet.Load($"{folder}/{image}", $"{folder}/{json}");
                if (sheet is null) continue;
                set.clips[baseName] = new Clip
                {
                    Name = baseName,
                    Sheet = sheet,
                    Frames = Enumerable.Range(0, sheet.Frames).ToArray(),
                    Fps = a.Num("playback_fps", sheet.Fps),
                    Loop = !a.Bool("oneshot"),
                    MirrorForLeft = a.Bool("mirror_for_left"),
                };
            }
        }
        return set;
    }

    private static ActorAnimationSet LoadNpc(string id, string folder, JsonObject manifest, string? variant)
    {
        var set = new ActorAnimationSet(id, variant) { IsDirectional = false, HeightPx = manifest.Num("height_px", 512) };
        var sheets = new Dictionary<string, SpriteSheet>(StringComparer.Ordinal);
        if (manifest.Obj("sheets") is { } sheetDefs)
        {
            foreach (var (name, node) in sheetDefs)
            {
                if (node is not JsonObject s) continue;
                string file = s.Str("file", name + "_sheet.webp")!;
                string json = s.Str("json", System.IO.Path.ChangeExtension(file, ".json"))!;
                if (SpriteSheet.Load($"{folder}/{file}", $"{folder}/{json}") is { } sheet) sheets[name] = sheet;
            }
        }
        string? chosen = variant ?? manifest.Str("default_variant");
        var anims = manifest.Obj("animations");
        if (chosen is not null && manifest.Obj("variants").Obj(chosen).Obj("animations") is { } overrides)
        {
            // Variant animations replace the base ones of the same name.
            var merged = new JsonObject();
            if (anims is not null) foreach (var (k, v) in anims) merged[k] = v?.DeepClone();
            foreach (var (k, v) in overrides) merged[k] = v?.DeepClone();
            anims = merged;
        }
        if (anims is null) return set;
        foreach (var (name, node) in anims)
        {
            if (node is not JsonObject a) continue;
            if (!sheets.TryGetValue(a.Str("sheet", "")!, out var sheet)) continue;
            int[] frames;
            var named = a.Strings("frames");
            if (named.Count > 0)
            {
                frames = named.Select(n => IndexOf(sheet, n)).Where(i => i >= 0).ToArray();
                if (frames.Length == 0) continue;
            }
            else frames = Enumerable.Range(0, sheet.Frames).ToArray();
            var every = a.Range("every_s", new Vector2(-1, -1));
            set.clips[name] = new Clip
            {
                Name = name,
                Sheet = sheet,
                Frames = frames,
                Fps = a.Num("fps", sheet.Fps),
                Loop = a.Bool("loop", !a.Bool("oneshot")) && frames.Length > 1,
                HoldSeconds = a.Num("hold_ms", 0) / 1000f,
                EverySeconds = every.X >= 0 ? every : null,
                MirrorForLeft = true,
            };
        }
        return set;
    }

    private static int IndexOf(SpriteSheet sheet, string frameName)
    {
        for (int i = 0; i < sheet.FrameNames.Count; i++)
            if (sheet.FrameNames[i] == frameName) return i;
        return int.TryParse(frameName, out int n) && n >= 0 && n < sheet.Frames ? n : -1;
    }
}
