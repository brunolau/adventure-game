using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.Json.Nodes;
using Godot;

namespace LastBell.Game.UI.Cutscenes;

/// <summary>
/// Optional pan / zoom per cutscene beat (presentation only), read from <c>res://data/cutscene_camera.json</c>
/// (written by <c>art/tools/cutscenes.py camera</c>). Key = <c>&lt;CS&gt;_&lt;n&gt;</c> (n from 1, as the beat picture).
/// Each move gives the part of the 1920x1080 picture that fills the view at the start (<c>from</c>) and at the
/// end (<c>to</c>) as [x, y, w, h]; the rect is cover-fitted to the screen. A rect may reach up to 10 % of its
/// height above or below the picture (that strip is black and lies under the letterbox bars).
/// <c>seconds</c> defaults to the beat's duration_min_s; <c>ease</c> is in_out (default), out or linear.
/// </summary>
public static class CutsceneCamera
{
    /// <summary>Data file of the camera moves.</summary>
    public const string DataPath = "res://data/cutscene_camera.json";

    /// <summary>The picture frame all rects refer to.</summary>
    public static readonly Vector2 Frame = new(1920, 1080);

    /// <summary>The whole picture (no move).</summary>
    public static readonly Rect2 Full = new(Vector2.Zero, Frame);

    /// <summary>One camera move.</summary>
    /// <param name="From">Visible rect at the start.</param>
    /// <param name="To">Visible rect at the end (and afterwards).</param>
    /// <param name="Seconds">Duration, or null for the beat's minimum duration.</param>
    /// <param name="Ease">in_out, out or linear.</param>
    public sealed record Move(Rect2 From, Rect2 To, double? Seconds, string Ease);

    private static Dictionary<string, Move>? moves;

    /// <summary>The move of a beat (beatIndex from 0), or null when the beat has none.</summary>
    public static Move? For(string cutsceneId, int beatIndex)
    {
        moves ??= Load();
        return moves.TryGetValue($"{cutsceneId}_{beatIndex + 1}", out var move) ? move : null;
    }

    /// <summary>The visible rect after <paramref name="seconds"/> of a move lasting <paramref name="duration"/>.</summary>
    public static Rect2 At(Move move, double seconds, double duration)
    {
        double t = duration <= 0 ? 1 : Math.Clamp(seconds / duration, 0, 1);
        float k = (float)(move.Ease switch
        {
            "linear" => t,
            "out" => 1 - Math.Pow(1 - t, 3),
            _ => t < 0.5 ? 4 * t * t * t : 1 - Math.Pow(-2 * t + 2, 3) / 2,
        });
        return new Rect2(move.From.Position.Lerp(move.To.Position, k), move.From.Size.Lerp(move.To.Size, k));
    }

    /// <summary>
    /// Position and size of the picture control (the whole 1920x1080 picture, stretched) so that
    /// <paramref name="visible"/> covers a view of <paramref name="view"/> pixels, centred.
    /// </summary>
    public static Rect2 Layout(Vector2 view, Rect2 visible)
    {
        float scale = Math.Max(view.X / visible.Size.X, view.Y / visible.Size.Y);
        Vector2 centre = visible.Position + visible.Size / 2;
        return new Rect2(view / 2 - centre * scale, Frame * scale);
    }

    private static Dictionary<string, Move> Load()
    {
        var result = new Dictionary<string, Move>();
        if (!FileAccess.FileExists(DataPath)) return result;
        try
        {
            if (JsonNode.Parse(FileAccess.GetFileAsString(DataPath)) is not JsonObject root) return result;
            foreach (var (key, node) in root)
            {
                if (key.StartsWith('_') || node is not JsonObject entry) continue;
                var from = ReadRect(entry["from"]);
                var to = ReadRect(entry["to"]);
                if (from is null || to is null) { GD.PushWarning($"{DataPath}: {key} needs 'from' and 'to' rects"); continue; }
                double? seconds = entry["seconds"] is JsonValue s ? s.GetValue<double>() : null;
                string ease = entry["ease"] is JsonValue e ? e.GetValue<string>() : "in_out";
                result[key] = new Move(from.Value, to.Value, seconds, ease);
            }
        }
        catch (Exception error)
        {
            GD.PushWarning($"{DataPath}: {error.Message}");
        }
        return result;
    }

    private static Rect2? ReadRect(JsonNode? node)
    {
        if (node is not JsonArray a || a.Count != 4) return null;
        float V(int i) => float.Parse(a[i]!.ToString(), CultureInfo.InvariantCulture);
        var rect = new Rect2(V(0), V(1), V(2), V(3));
        return rect.Size.X > 0 && rect.Size.Y > 0 ? rect : null;
    }
}
