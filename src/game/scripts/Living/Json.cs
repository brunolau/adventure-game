using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Nodes;
using Godot;

namespace LastBell.Game.Living;

/// <summary>
/// Small tolerant readers over <see cref="JsonNode"/> for the living-world data files
/// (data/ambient/*.json, assets/actors/*/actor.json). Missing or malformed values fall back to the
/// given default so one bad entry never breaks a room.
/// </summary>
internal static class Json
{
    /// <summary>Reads a res:// or user:// JSON file; null (with a warning) when missing or invalid.</summary>
    public static JsonObject? Load(string path, bool warnIfMissing = true)
    {
        if (!Godot.FileAccess.FileExists(path))
        {
            if (warnIfMissing) GD.PushWarning($"Living: {path} not found");
            return null;
        }
        try
        {
            return JsonNode.Parse(Godot.FileAccess.GetFileAsString(path), documentOptions: new JsonDocumentOptions
            {
                CommentHandling = JsonCommentHandling.Skip,
                AllowTrailingCommas = true,
            }) as JsonObject;
        }
        catch (Exception ex)
        {
            GD.PushError($"Living: {path} is not valid JSON: {ex.Message}");
            return null;
        }
    }

    public static string? Str(this JsonObject? o, string key, string? fallback = null)
    {
        if (o is null || !o.TryGetPropertyValue(key, out var n) || n is null) return fallback;
        return n.GetValueKind() == JsonValueKind.String ? n.GetValue<string>() : n.ToJsonString();
    }

    public static float Num(this JsonObject? o, string key, float fallback = 0f)
    {
        if (o is null || !o.TryGetPropertyValue(key, out var n) || n is null) return fallback;
        return AsFloat(n, fallback);
    }

    public static float? NumOrNull(this JsonObject? o, string key)
    {
        if (o is null || !o.TryGetPropertyValue(key, out var n) || n is null) return null;
        return n.GetValueKind() == JsonValueKind.Number ? AsFloat(n, 0) : null;
    }

    public static int Int(this JsonObject? o, string key, int fallback = 0) => (int)MathF.Round(o.Num(key, fallback));

    public static bool Bool(this JsonObject? o, string key, bool fallback = false)
    {
        if (o is null || !o.TryGetPropertyValue(key, out var n) || n is null) return fallback;
        return n.GetValueKind() switch
        {
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            _ => fallback,
        };
    }

    public static JsonObject? Obj(this JsonObject? o, string key) =>
        o is not null && o.TryGetPropertyValue(key, out var n) ? n as JsonObject : null;

    public static JsonArray? Arr(this JsonObject? o, string key) =>
        o is not null && o.TryGetPropertyValue(key, out var n) ? n as JsonArray : null;

    public static bool Has(this JsonObject? o, string key) => o is not null && o.ContainsKey(key) && o[key] is not null;

    /// <summary>[x, y] as a vector.</summary>
    public static Vector2 Vec(this JsonObject? o, string key, Vector2 fallback = default)
    {
        var a = o.Arr(key);
        return a is { Count: >= 2 } ? new Vector2(AsFloat(a[0], fallback.X), AsFloat(a[1], fallback.Y)) : fallback;
    }

    /// <summary>A number or a [min, max] range; a single number gives (n, n).</summary>
    public static Vector2 Range(this JsonObject? o, string key, Vector2 fallback)
    {
        if (o is null || !o.TryGetPropertyValue(key, out var n) || n is null) return fallback;
        if (n is JsonArray a && a.Count >= 2) return new Vector2(AsFloat(a[0], fallback.X), AsFloat(a[1], fallback.Y));
        if (n.GetValueKind() == JsonValueKind.Number) { float v = AsFloat(n, fallback.X); return new Vector2(v, v); }
        return fallback;
    }

    /// <summary>[x, y, w, h] as a rect.</summary>
    public static Rect2? Rect(this JsonObject? o, string key)
    {
        var a = o.Arr(key);
        if (a is not { Count: >= 4 }) return null;
        return new Rect2(AsFloat(a[0], 0), AsFloat(a[1], 0), AsFloat(a[2], 0), AsFloat(a[3], 0));
    }

    /// <summary>"#rrggbb", "#rrggbbaa" or [r, g, b(, a)] in 0..1.</summary>
    public static Color Col(this JsonObject? o, string key, Color fallback)
    {
        if (o is null || !o.TryGetPropertyValue(key, out var n) || n is null) return fallback;
        if (n.GetValueKind() == JsonValueKind.String)
        {
            string s = n.GetValue<string>();
            return Color.HtmlIsValid(s) ? Color.FromHtml(s) : fallback;
        }
        if (n is JsonArray a && a.Count >= 3)
            return new Color(AsFloat(a[0], 1), AsFloat(a[1], 1), AsFloat(a[2], 1), a.Count >= 4 ? AsFloat(a[3], 1) : 1);
        return fallback;
    }

    /// <summary>[[x, y], ...] as a point list.</summary>
    public static List<Vector2> Points(this JsonObject? o, string key)
    {
        var list = new List<Vector2>();
        if (o.Arr(key) is { } a)
            foreach (var p in a)
                if (p is JsonArray pa && pa.Count >= 2) list.Add(new Vector2(AsFloat(pa[0], 0), AsFloat(pa[1], 0)));
        return list;
    }

    /// <summary>A string or a list of strings.</summary>
    public static List<string> Strings(this JsonObject? o, string key)
    {
        var list = new List<string>();
        if (o is null || !o.TryGetPropertyValue(key, out var n) || n is null) return list;
        if (n is JsonArray a)
        {
            foreach (var s in a)
                if (s is not null && s.GetValueKind() == JsonValueKind.String) list.Add(s.GetValue<string>());
        }
        else if (n.GetValueKind() == JsonValueKind.String) list.Add(n.GetValue<string>());
        return list;
    }

    /// <summary>A list of integers (frame indices).</summary>
    public static List<int> Ints(this JsonObject? o, string key)
    {
        var list = new List<int>();
        if (o.Arr(key) is { } a)
            foreach (var v in a)
                if (v is not null && v.GetValueKind() == JsonValueKind.Number) list.Add((int)AsFloat(v, 0));
        return list;
    }

    public static float AsFloat(JsonNode? n, float fallback)
    {
        if (n is null) return fallback;
        try
        {
            return n.GetValueKind() switch
            {
                JsonValueKind.Number => (float)n.GetValue<double>(),
                JsonValueKind.String when float.TryParse(n.GetValue<string>(), NumberStyles.Float, CultureInfo.InvariantCulture, out var f) => f,
                _ => fallback,
            };
        }
        catch (Exception)
        {
            return fallback;
        }
    }
}
