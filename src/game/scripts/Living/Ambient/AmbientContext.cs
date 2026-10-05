using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using Godot;
using LastBell.Game.Living.Actors;
using LastBell.Game.World;

namespace LastBell.Game.Living.Ambient;

/// <summary>
/// A drawable image for an ambient layer: a whole texture (one frame) or the cells of a sprite
/// sheet (<c>name.webp</c> + <c>name.json</c>, same format as the actor sheets).
/// </summary>
public sealed class SpriteSource
{
    /// <summary>Texture.</summary>
    public required Texture2D Texture { get; init; }

    /// <summary>Cell size in px.</summary>
    public required Vector2 Cell { get; init; }

    /// <summary>Anchor inside a cell (feet / centre).</summary>
    public required Vector2 Pivot { get; init; }

    /// <summary>Cell count.</summary>
    public int Frames { get; init; } = 1;

    /// <summary>Authored playback rate.</summary>
    public float Fps { get; init; } = 8;

    /// <summary>Optional frame names.</summary>
    public IReadOnlyList<string> FrameNames { get; init; } = Array.Empty<string>();

    /// <summary>Cells per row (sheets may be row-major grids, see <see cref="SpriteSheet"/>).</summary>
    public int Columns { get; init; } = int.MaxValue;

    /// <summary>Texture region of a cell (strip or row-major grid).</summary>
    public Rect2 Region(int frame) => Frames <= 1 ? new Rect2(Vector2.Zero, Cell) : SpriteSheet.GridRegion(frame, Frames, Columns, Cell);

    /// <summary>Cells whose names start with a prefix (e.g. "fly" → fly_0..fly_3), in sheet order.</summary>
    public int[] Named(string prefix)
    {
        var list = new List<int>();
        for (int i = 0; i < FrameNames.Count; i++)
            if (FrameNames[i] == prefix || FrameNames[i].StartsWith(prefix + "_", StringComparison.Ordinal)) list.Add(i);
        return list.ToArray();
    }
}

/// <summary>
/// What a layer may use while it is built: the room, deterministic randomness, texture loading
/// (<c>res://assets/ambient/…</c> or <c>builtin:*</c> procedural textures) and the hero position.
/// </summary>
public sealed class AmbientContext
{
    /// <summary>Folder of the shipped ambient art.</summary>
    public const string AssetRoot = "res://assets/ambient/";

    private static readonly Dictionary<string, SpriteSource?> Cache = new(StringComparer.Ordinal);

    /// <summary>The room being decorated.</summary>
    public required Room Room { get; init; }

    /// <summary>Room id.</summary>
    public string RoomId => Room.RoomId;

    /// <summary>Hero feet in canvas px (or far away when there is no hero).</summary>
    public Vector2 HeroFeet => Room.Hero is { } hero && GodotObject.IsInstanceValid(hero) ? hero.Feet : new Vector2(-10000, -10000);

    /// <summary>Stable seed for a layer: the same room and layer id always start the same way.</summary>
    public ulong SeedFor(string layerId)
    {
        ulong h = 1469598103934665603UL;
        foreach (char c in RoomId + "/" + layerId) h = (h ^ c) * 1099511628211UL;
        return h;
    }

    /// <summary>
    /// Loads a sprite: <c>"common/leaf_00.webp"</c> (whole image), <c>"common/pigeon_sheet"</c> or
    /// <c>"…_sheet.webp"</c> with a JSON sidecar (cells), or <c>"builtin:dot|glow|streak|puff|silhouette|softrect"</c>.
    /// </summary>
    public static SpriteSource? Sprite(string? path, Vector2? pivot = null)
    {
        if (string.IsNullOrEmpty(path)) return null;
        string key = path + "|" + pivot;
        if (Cache.TryGetValue(key, out var cached)) return cached;
        SpriteSource? source = null;
        if (path.StartsWith("builtin:", StringComparison.Ordinal))
        {
            var tex = BuiltinTextures.Get(path[8..]);
            if (tex is not null)
            {
                var size = tex.GetSize();
                source = new SpriteSource { Texture = tex, Cell = size, Pivot = pivot ?? size / 2 };
            }
        }
        else
        {
            string full = path.StartsWith("res://", StringComparison.Ordinal) ? path : AssetRoot + path;
            string image = full.EndsWith(".webp", StringComparison.Ordinal) || full.EndsWith(".png", StringComparison.Ordinal) ? full : full + ".webp";
            string json = System.IO.Path.ChangeExtension(image, ".json");
            if (Godot.FileAccess.FileExists(json) && SpriteSheet.Load(image, json) is { } sheet)
            {
                source = new SpriteSource
                {
                    Texture = sheet.Texture,
                    Cell = sheet.Cell,
                    Pivot = pivot ?? sheet.Pivot,
                    Frames = sheet.Frames,
                    Columns = sheet.Columns,
                    Fps = sheet.Fps,
                    FrameNames = sheet.FrameNames,
                };
            }
            else if (ResourceLoader.Exists(image) && GD.Load<Texture2D>(image) is { } tex)
            {
                var size = tex.GetSize();
                source = new SpriteSource { Texture = tex, Cell = size, Pivot = pivot ?? size / 2 };
            }
            else GD.PushWarning($"Living: ambient sprite {image} not found");
        }
        Cache[key] = source;
        return source;
    }

    private static JsonObject? manifest;
    private static bool manifestLoaded;

    /// <summary>
    /// Placement info that art/tools/ambient_cut.py recorded for a cut-out or mask
    /// (<c>assets/ambient/manifest.json</c>): pos, size, mask_rect, patch_pos. Path like "S02/birch.webp".
    /// </summary>
    public static JsonObject? CutInfo(string? path)
    {
        if (string.IsNullOrEmpty(path)) return null;
        if (!manifestLoaded)
        {
            manifestLoaded = true;
            manifest = Json.Load(AssetRoot + "manifest.json", warnIfMissing: false);
        }
        string clean = path.StartsWith(AssetRoot, StringComparison.Ordinal) ? path[AssetRoot.Length..] : path;
        int slash = clean.IndexOf('/');
        if (slash < 0) return null;
        string room = clean[..slash];
        string name = System.IO.Path.GetFileNameWithoutExtension(clean[(slash + 1)..]);
        return manifest.Obj("rooms").Obj(room).Obj("items").Obj(name);
    }

    /// <summary>Position of a cut-out: the data's "pos", else the manifest's.</summary>
    public static Vector2 CutPos(JsonObject def, string key = "texture") =>
        def.Has("pos") ? def.Vec("pos") : CutInfo(def.Str(key)).Vec("pos");

    /// <summary>Loads a plain texture from the ambient folder (masks).</summary>
    public static Texture2D? Texture(string? path)
    {
        if (string.IsNullOrEmpty(path)) return null;
        string full = path.StartsWith("res://", StringComparison.Ordinal) ? path : AssetRoot + path;
        if (ResourceLoader.Exists(full) && GD.Load<Texture2D>(full) is { } tex) return tex;
        GD.PushWarning($"Living: ambient texture {full} not found");
        return null;
    }

    /// <summary>All sprites of a "texture"/"textures" entry (string or list).</summary>
    public static List<SpriteSource> Sprites(JsonObject def, string key = "textures")
    {
        var list = new List<SpriteSource>();
        foreach (var p in def.Strings(key))
            if (Sprite(p) is { } s) list.Add(s);
        if (list.Count == 0 && key == "textures")
            foreach (var p in def.Strings("texture"))
                if (Sprite(p) is { } s) list.Add(s);
        return list;
    }
}

/// <summary>Procedural soft textures for light and air (no painted art needed).</summary>
internal static class BuiltinTextures
{
    private static readonly Dictionary<string, Texture2D?> Cache = new(StringComparer.Ordinal);

    public static Texture2D? Get(string name)
    {
        if (Cache.TryGetValue(name, out var t)) return t;
        Image? img = name switch
        {
            "dot" => Radial(32, 2.2f),
            "glow" => Radial(128, 1.6f),
            "puff" => Puff(96),
            "streak" => Streak(6, 64),
            "silhouette" => Silhouette(140, 360),
            "softrect" => SoftRect(128, 32, 10),
            "white" => Solid(4, 4),
            _ => null,
        };
        t = img is null ? null : ImageTexture.CreateFromImage(img);
        if (img is null) GD.PushWarning($"Living: unknown builtin texture '{name}'");
        Cache[name] = t;
        return t;
    }

    private static Image Solid(int w, int h)
    {
        var img = Image.CreateEmpty(w, h, false, Image.Format.Rgba8);
        img.Fill(Colors.White);
        return img;
    }

    private static Image Radial(int size, float power)
    {
        var img = Image.CreateEmpty(size, size, false, Image.Format.Rgba8);
        float r = size / 2f;
        for (int y = 0; y < size; y++)
            for (int x = 0; x < size; x++)
            {
                float d = new Vector2(x + 0.5f - r, y + 0.5f - r).Length() / r;
                float a = MathF.Pow(Math.Clamp(1 - d, 0, 1), power);
                img.SetPixel(x, y, new Color(1, 1, 1, a));
            }
        return img;
    }

    private static Image Puff(int size)
    {
        var img = Image.CreateEmpty(size, size, false, Image.Format.Rgba8);
        float r = size / 2f;
        var rng = new RandomNumberGenerator { Seed = 7 };
        var blobs = new List<(Vector2 c, float r)>();
        for (int i = 0; i < 7; i++) blobs.Add((new Vector2(rng.RandfRange(-0.3f, 0.3f), rng.RandfRange(-0.3f, 0.3f)) * r, rng.RandfRange(0.35f, 0.6f) * r));
        for (int y = 0; y < size; y++)
            for (int x = 0; x < size; x++)
            {
                var p = new Vector2(x + 0.5f - r, y + 0.5f - r);
                float a = 0;
                foreach (var (c, br) in blobs) a = Math.Max(a, MathF.Pow(Math.Clamp(1 - (p - c).Length() / br, 0, 1), 1.5f));
                img.SetPixel(x, y, new Color(1, 1, 1, a * 0.8f));
            }
        return img;
    }

    private static Image Streak(int w, int h)
    {
        var img = Image.CreateEmpty(w, h, false, Image.Format.Rgba8);
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                float across = 1 - MathF.Abs((x + 0.5f) / w * 2 - 1);
                float along = (float)y / h;
                img.SetPixel(x, y, new Color(1, 1, 1, across * along));
            }
        return img;
    }

    private static Image SoftRect(int w, int h, int feather)
    {
        var img = Image.CreateEmpty(w, h, false, Image.Format.Rgba8);
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                float dx = Math.Min(x + 0.5f, w - x - 0.5f) / feather;
                float dy = Math.Min(y + 0.5f, h - y - 0.5f) / feather;
                float a = Math.Clamp(Math.Min(dx, dy), 0, 1);
                img.SetPixel(x, y, new Color(1, 1, 1, a * a * (3 - 2 * a)));
            }
        return img;
    }

    /// <summary>A soft human silhouette (head, shoulders, torso) for shadows behind curtains.</summary>
    private static Image Silhouette(int w, int h)
    {
        var img = Image.CreateEmpty(w, h, false, Image.Format.Rgba8);
        var head = new Vector2(w * 0.5f, h * 0.13f);
        float headR = w * 0.17f;
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                var p = new Vector2(x + 0.5f, y + 0.5f);
                float a = Math.Clamp(1.3f - (p - head).Length() / headR, 0, 1);
                if (y > h * 0.22f)
                {
                    // shoulders widen quickly, torso slowly narrows
                    float t = (y - h * 0.22f) / (h * 0.78f);
                    float half = w * (t < 0.12f ? 0.2f + t / 0.12f * 0.25f : 0.45f - (t - 0.12f) * 0.08f);
                    float edge = Math.Clamp((half - MathF.Abs(x + 0.5f - w * 0.5f)) / (w * 0.08f), 0, 1);
                    a = Math.Max(a, edge * Math.Clamp((1 - t) * 3, 0, 1));
                }
                img.SetPixel(x, y, new Color(1, 1, 1, Math.Clamp(a, 0, 1)));
            }
        return img;
    }
}
