using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Godot;

namespace LastBell.Game.Living.Actors;

/// <summary>
/// One sprite sheet: a horizontal strip or a row-major grid of equal cells (frame i at column i % Columns,
/// row i / Columns). Grids keep every sheet at most 4096 px wide for mobile GPUs (ISSUES LIVING-04 / BUILD-01).
/// </summary>
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

    /// <summary>Cells per row (JSON <c>columns</c>, else the texture width / cell width; a strip has Columns == Frames).</summary>
    public int Columns { get; init; } = int.MaxValue;

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
    public Rect2 Region(int frame) => GridRegion(frame, Frames, Columns, Cell);

    /// <summary>Region of cell <paramref name="frame"/> in a row-major grid with <paramref name="columns"/> cells per row.</summary>
    public static Rect2 GridRegion(int frame, int frames, int columns, Vector2 cell)
    {
        int i = Math.Clamp(frame, 0, Math.Max(0, frames - 1));
        int cols = Math.Max(1, columns);
        return new Rect2(i % cols * cell.X, i / cols * cell.Y, cell.X, cell.Y);
    }

    /// <summary>
    /// Cells per row of a sheet: JSON <c>columns</c> (or <c>grid: [columns, rows]</c>), else as many cells as fit
    /// in the texture width (a strip gives frames, a grid its column count).
    /// </summary>
    public static int ColumnsOf(JsonObject meta, Texture2D texture, Vector2 cell, int frames)
    {
        int columns = meta.Int("columns", 0);
        if (columns <= 0 && meta["grid"] is JsonArray grid && grid.Count >= 1 && grid[0] is JsonValue g && g.TryGetValue(out int gc)) columns = gc;
        if (columns <= 0 && cell.X > 0) columns = (int)(texture.GetWidth() / cell.X + 0.01f);
        return Math.Clamp(columns, 1, Math.Max(1, frames));
    }

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
            int columns = ColumnsOf(meta, texture, cell, frames);
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
                Columns = columns,
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

    /// <summary>An NPC manifest's <c>default_variant</c> (e.g. JANA20 "laptop"), or null.</summary>
    public static string? DefaultVariant(string characterId)
    {
        if (DefaultVariants.TryGetValue(characterId, out var cached)) return cached;
        string? result = Json.Load(FolderOf(characterId) + "/actor.json", warnIfMissing: false)?.Str("default_variant");
        DefaultVariants[characterId] = result;
        return result;
    }

    private static readonly Dictionary<string, string?> DefaultVariants = new(StringComparer.Ordinal);

    /// <summary>
    /// Resolves a natural-blocking staging name (data/blocking/&lt;room&gt;.json <c>npcs.*.variant</c>) to an
    /// actor.json variant. Generic names: <c>standing</c> (the <c>full</c> variant, else the default sheets of a
    /// standing figure), <c>seated</c> (a <c>seated</c> variant, else the default sheets of a figure whose manifest
    /// says <c>staging</c>/<c>posture</c> "seated"), <c>behind_counter</c> (<c>counter</c>, else <c>table</c>),
    /// <c>window_bust</c> (<c>window</c>), <c>window_bust_glass</c> (<c>window_glass</c>); any other name must be a
    /// variant of the manifest. <paramref name="variant"/> null = the default sheets. Same rule as
    /// tools/check_blocking.py <c>resolve_staging</c>. Returns false when the actor has no such staging.
    /// </summary>
    public static bool TryResolveStaging(string characterId, string? staging, out string? variant)
    {
        variant = null;
        if (string.IsNullOrEmpty(staging) || staging == "default") return true;
        var manifest = Json.Load(FolderOf(characterId) + "/actor.json", warnIfMissing: false);
        if (manifest is null) return false;
        var variants = manifest.Obj("variants");
        bool Has(string name) => variants.Obj(name) is not null;
        // "posture" may carry a note after a semicolon ("standing; variants: counter").
        string pose = (manifest.Str("posture") ?? manifest.Str("staging") ?? "standing").Split(';')[0].Trim();
        bool plainDefault = manifest.Str("default_variant") is null;
        string? pick = staging switch
        {
            "standing" => Has("full") ? "full" : plainDefault && pose == "standing" ? "" : null,
            "seated" => Has("seated") ? "seated" : plainDefault && pose == "seated" ? "" : null,
            "behind_counter" => Has("counter") ? "counter" : Has("table") ? "table" : null,
            "window_bust" => Has("window") ? "window" : null,
            "window_bust_glass" => Has("window_glass") ? "window_glass" : null,
            _ => Has(staging) ? staging : null,
        };
        if (pick is null) return false;
        variant = pick.Length == 0 ? null : pick;
        return true;
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
