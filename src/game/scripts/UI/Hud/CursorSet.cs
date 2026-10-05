using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using Godot;

namespace LastBell.Game.UI.Hud;

/// <summary>Contextual cursor kinds (product owner control changes 2026-10-05, item 4).</summary>
public enum CursorKind
{
    /// <summary>Default / walk (floor, empty background, GUI).</summary>
    Pointer,
    /// <summary>Use / take (a prop or NPC whose left click is an action).</summary>
    Hand,
    /// <summary>Talk (an NPC whose left click opens a conversation).</summary>
    Talk,
    /// <summary>Look-only (atmospheric props, locked things whose left click is a look).</summary>
    Look,
    /// <summary>Exit towards the left edge.</summary>
    ExitLeft,
    /// <summary>Exit towards the right edge.</summary>
    ExitRight,
    /// <summary>Exit up / into the picture.</summary>
    ExitUp,
    /// <summary>Exit down / towards the viewer.</summary>
    ExitDown,
    /// <summary>A selected item is on the cursor (the pointer carries its icon).</summary>
    Item,
    /// <summary>Busy / wait (cutscenes, dialogue lines, room transitions).</summary>
    Busy,
}

/// <summary>
/// The painted style-A cursor set (art/tools/cursors.py → res://assets/ui/cursors/<c>&lt;name&gt;_&lt;size&gt;.png</c>
/// + <c>hotspots.json</c>) as hardware cursors through <see cref="Input.SetCustomMouseCursor"/>. The image size follows
/// the window scale (64 / 96 / 128 px; 96 px at 1080p), the hotspot is the tip pixel of pointer-like cursors.
/// The item cursor is composed at runtime: the item's icon with a small pointer at its upper-left corner.
/// When the files are missing or the display has no mouse cursor, the system cursor stays (graceful fallback).
/// </summary>
public static class CursorSet
{
    private const string Folder = "res://assets/ui/cursors/";
    private static readonly int[] Sizes = { 64, 96, 128 };
    private static readonly Dictionary<string, Vector2> Hotspots = new(StringComparer.Ordinal);
    private static readonly Dictionary<string, Image?> Images = new(StringComparer.Ordinal);
    private static bool loaded;
    private static string appliedKey = "";
    private static int handSize;

    /// <summary>The kind currently applied (QA).</summary>
    public static CursorKind Current { get; private set; } = CursorKind.Pointer;

    /// <summary>The cursor image size in window px currently applied (0 = system cursor).</summary>
    public static int CurrentSize { get; private set; }

    /// <summary>True when the painted cursors were found and hardware cursors are available.</summary>
    public static bool Available
    {
        get
        {
            Load();
            return Hotspots.Count > 0 && DisplayServer.GetName() != "headless" && DisplayServer.HasFeature(DisplayServer.Feature.CustomCursorShape);
        }
    }

    /// <summary>File stem of a cursor kind.</summary>
    public static string Name(CursorKind kind) => kind switch
    {
        CursorKind.Hand => "hand",
        CursorKind.Talk => "talk",
        CursorKind.Look => "look",
        CursorKind.ExitLeft => "exit_left",
        CursorKind.ExitRight => "exit_right",
        CursorKind.ExitUp => "exit_up",
        CursorKind.ExitDown => "exit_down",
        CursorKind.Busy => "busy",
        _ => "pointer",
    };

    /// <summary>Cursor image size for a window scale (window height / 1080) and the HUD scale.</summary>
    public static int SizeFor(float windowScale, float hudScale)
    {
        float wanted = 92f * windowScale * Math.Clamp(hudScale, 1f, 1.4f);
        int best = Sizes[0];
        foreach (int s in Sizes) if (Math.Abs(s - wanted) < Math.Abs(best - wanted)) best = s;
        return best;
    }

    private static void Load()
    {
        if (loaded) return;
        loaded = true;
        string path = Folder + "hotspots.json";
        if (!FileAccess.FileExists(path)) { GD.PushWarning("CursorSet: " + path + " missing, system cursor kept"); return; }
        try
        {
            var root = JsonNode.Parse(FileAccess.GetFileAsString(path))?["hotspots"]?.AsObject();
            if (root is null) return;
            foreach (var (name, value) in root)
                if (value is JsonArray { Count: 2 } a) Hotspots[name] = new Vector2((float)a[0]!, (float)a[1]!);
        }
        catch (Exception ex)
        {
            GD.PushWarning("CursorSet: cannot read hotspots.json: " + ex.Message);
            Hotspots.Clear();
        }
    }

    /// <summary>An RGBA8 image of a cursor or marker (cached), or null.</summary>
    public static Image? ImageOf(string name, int size)
    {
        string key = name + "_" + size;
        if (Images.TryGetValue(key, out var cached)) return cached;
        string path = Folder + key + ".png";
        Image? image = null;
        if (ResourceLoader.Exists(path) && GD.Load<Texture2D>(path) is { } texture) image = Rgba(texture.GetImage());
        Images[key] = image;
        return image;
    }

    /// <summary>A texture of a cursor or marker, or null (software drawing, markers).</summary>
    public static Texture2D? TextureOf(string name, int size)
    {
        string path = Folder + name + "_" + size + ".png";
        return ResourceLoader.Exists(path) ? GD.Load<Texture2D>(path) : null;
    }

    /// <summary>Hotspot of a cursor as a fraction of its square.</summary>
    public static Vector2 HotspotOf(string name)
    {
        Load();
        return Hotspots.TryGetValue(name, out var h) ? h : new Vector2(0.5f, 0.5f);
    }

    private static Image? Rgba(Image? image)
    {
        if (image is null) return null;
        var copy = (Image)image.Duplicate();
        if (copy.IsCompressed()) copy.Decompress();
        if (copy.GetFormat() != Image.Format.Rgba8) copy.Convert(Image.Format.Rgba8);
        return copy;
    }

    /// <summary>
    /// The cursor image for a kind and size: the painted cursor, or for <see cref="CursorKind.Item"/> the item icon
    /// with a small pointer at the upper-left (hotspot = that pointer's tip). Null when nothing can be built.
    /// </summary>
    public static (Image Image, Vector2 Hotspot)? Build(CursorKind kind, int size, Texture2D? itemIcon, string itemKey)
    {
        Load();
        if (kind != CursorKind.Item)
        {
            var name = Name(kind);
            var img = ImageOf(name, size);
            if (img is null) return null;
            return (img, HotspotOf(name) * size);
        }
        string key = "item:" + itemKey + ":" + size;
        if (Images.TryGetValue(key, out var composed) && composed is not null)
            return (composed, HotspotOf("pointer") * (size * 0.5f));
        var canvas = Image.CreateEmpty(size, size, false, Image.Format.Rgba8);
        if (Rgba(itemIcon?.GetImage()) is { } icon)
        {
            int side = (int)(size * 0.78f);
            icon.Resize(side, side, Image.Interpolation.Lanczos);
            canvas.BlendRect(icon, new Rect2I(0, 0, side, side), new Vector2I(size - side, size - side));
        }
        if (ImageOf("pointer", size) is { } pointer)
        {
            var small = (Image)pointer.Duplicate();
            small.Resize(size / 2, size / 2, Image.Interpolation.Lanczos);
            canvas.BlendRect(small, new Rect2I(0, 0, size / 2, size / 2), Vector2I.Zero);
        }
        Images[key] = canvas;
        return (canvas, HotspotOf("pointer") * (size * 0.5f));
    }

    /// <summary>
    /// Applies a kind as the hardware arrow cursor (and the pointing-hand shape of GUI links) when it differs from the
    /// current one. Returns false when hardware cursors are unavailable (the system cursor stays).
    /// </summary>
    public static bool Apply(CursorKind kind, int size, Texture2D? itemIcon = null, string itemKey = "")
    {
        Current = kind; // also without hardware cursors (headless QA reads the decision)
        if (!Available) { CurrentSize = 0; return false; }
        string key = kind + ":" + size + ":" + itemKey;
        if (key == appliedKey) return true;
        var built = Build(kind, size, itemIcon, itemKey) ?? Build(CursorKind.Pointer, size, null, "");
        if (built is not { } b) { CurrentSize = 0; return false; }
        Input.SetCustomMouseCursor(ImageTexture.CreateFromImage(b.Image), Input.CursorShape.Arrow, b.Hotspot);
        if (handSize != size && Build(CursorKind.Hand, size, null, "") is { } hand)
        {
            Input.SetCustomMouseCursor(ImageTexture.CreateFromImage(hand.Image), Input.CursorShape.PointingHand, hand.Hotspot);
            handSize = size;
        }
        appliedKey = key;
        CurrentSize = size;
        return true;
    }

    /// <summary>Back to the system cursors (e.g. on exit of the UI).</summary>
    public static void Reset()
    {
        if (appliedKey.Length == 0) return;
        Input.SetCustomMouseCursor(null, Input.CursorShape.Arrow);
        Input.SetCustomMouseCursor(null, Input.CursorShape.PointingHand);
        appliedKey = "";
        handSize = 0;
        CurrentSize = 0;
    }
}
