using System;
using Godot;

namespace LastBell.Game.UI.Theme;

/// <summary>Simple vector icons drawn in code (no icon font, no licensed icon set).</summary>
public enum GlyphKind
{
    /// <summary>Service bag (inventory).</summary>
    Bag,
    /// <summary>Notebook (journal).</summary>
    Journal,
    /// <summary>Folded map.</summary>
    Map,
    /// <summary>Light bulb (hints).</summary>
    Hint,
    /// <summary>Three bars (menu).</summary>
    Menu,
    /// <summary>Eye (show hotspots).</summary>
    Eye,
    /// <summary>Chronometer (era travel).</summary>
    Clock,
    /// <summary>Cross (close / cancel).</summary>
    Close,
    /// <summary>Counter-clockwise arrow.</summary>
    RotateLeft,
    /// <summary>Clockwise arrow.</summary>
    RotateRight,
    /// <summary>Triangle up.</summary>
    Up,
    /// <summary>Triangle down.</summary>
    Down,
    /// <summary>Tick.</summary>
    Check,
    /// <summary>Pin.</summary>
    Pin,
    /// <summary>Play triangle.</summary>
    Play,
    /// <summary>Speech bubble.</summary>
    Talk,
}

/// <summary>A control that draws one <see cref="GlyphKind"/> centred in its rect.</summary>
public partial class Glyph : Control
{
    private GlyphKind kind;
    private Color color = UiTheme.Cream;

    /// <summary>Which icon.</summary>
    public GlyphKind Kind { get => kind; set { kind = value; QueueRedraw(); } }

    /// <summary>Stroke colour.</summary>
    public Color Color { get => color; set { color = value; QueueRedraw(); } }

    /// <summary>Creates a glyph of a given size.</summary>
    public Glyph(GlyphKind kind, float size, Color? color = null)
    {
        this.kind = kind;
        if (color is { } c) this.color = c;
        CustomMinimumSize = new Vector2(size, size);
        MouseFilter = MouseFilterEnum.Ignore;
    }

    /// <summary>Parameterless constructor required by Godot.</summary>
    public Glyph() { }

    /// <inheritdoc />
    public override void _Draw() => Paint(this, kind, new Rect2(Vector2.Zero, Size), color);

    /// <summary>Draws a glyph into any canvas item.</summary>
    public static void Paint(CanvasItem ci, GlyphKind kind, Rect2 rect, Color color)
    {
        float s = Math.Min(rect.Size.X, rect.Size.Y);
        var o = rect.Position + (rect.Size - new Vector2(s, s)) / 2;
        Vector2 P(float x, float y) => o + new Vector2(x * s, y * s);
        float w = Math.Max(2f, s * 0.08f);
        switch (kind)
        {
            case GlyphKind.Bag:
                ci.DrawPolyline(new[] { P(0.36f, 0.32f), P(0.36f, 0.2f), P(0.64f, 0.2f), P(0.64f, 0.32f) }, color, w, true);
                Rounded(ci, new Rect2(P(0.14f, 0.32f), new Vector2(0.72f * s, 0.5f * s)), color, w);
                ci.DrawLine(P(0.14f, 0.5f), P(0.86f, 0.5f), color, w * 0.8f, true);
                ci.DrawRect(new Rect2(P(0.45f, 0.46f), new Vector2(0.1f * s, 0.1f * s)), color);
                break;
            case GlyphKind.Journal:
                Rounded(ci, new Rect2(P(0.2f, 0.14f), new Vector2(0.6f * s, 0.72f * s)), color, w);
                ci.DrawLine(P(0.32f, 0.14f), P(0.32f, 0.86f), color, w, true);
                for (int i = 0; i < 3; i++) ci.DrawLine(P(0.42f, 0.34f + i * 0.14f), P(0.7f, 0.34f + i * 0.14f), color, w * 0.7f, true);
                break;
            case GlyphKind.Map:
                ci.DrawPolyline(new[] { P(0.12f, 0.24f), P(0.37f, 0.14f), P(0.63f, 0.24f), P(0.88f, 0.14f), P(0.88f, 0.76f), P(0.63f, 0.86f), P(0.37f, 0.76f), P(0.12f, 0.86f), P(0.12f, 0.24f) }, color, w, true);
                ci.DrawLine(P(0.37f, 0.14f), P(0.37f, 0.76f), color, w * 0.7f, true);
                ci.DrawLine(P(0.63f, 0.24f), P(0.63f, 0.86f), color, w * 0.7f, true);
                break;
            case GlyphKind.Hint:
                ci.DrawArc(P(0.5f, 0.4f), 0.24f * s, Mathf.Pi * 0.8f, Mathf.Pi * 2.2f, 24, color, w, true);
                ci.DrawLine(P(0.4f, 0.6f), P(0.4f, 0.7f), color, w, true);
                ci.DrawLine(P(0.6f, 0.6f), P(0.6f, 0.7f), color, w, true);
                ci.DrawLine(P(0.38f, 0.72f), P(0.62f, 0.72f), color, w, true);
                ci.DrawLine(P(0.42f, 0.82f), P(0.58f, 0.82f), color, w, true);
                break;
            case GlyphKind.Menu:
                for (int i = 0; i < 3; i++) ci.DrawLine(P(0.2f, 0.3f + i * 0.2f), P(0.8f, 0.3f + i * 0.2f), color, w * 1.2f, true);
                break;
            case GlyphKind.Eye:
                ci.DrawPolyline(Arc(P(0.5f, 0.86f), 0.5f * s, -2.36f, -0.78f), color, w, true);
                ci.DrawPolyline(Arc(P(0.5f, 0.14f), 0.5f * s, 0.78f, 2.36f), color, w, true);
                ci.DrawCircle(P(0.5f, 0.5f), 0.12f * s, color);
                break;
            case GlyphKind.Clock:
                ci.DrawArc(P(0.5f, 0.54f), 0.32f * s, 0, Mathf.Tau, 32, color, w, true);
                ci.DrawLine(P(0.5f, 0.54f), P(0.5f, 0.36f), color, w, true);
                ci.DrawLine(P(0.5f, 0.54f), P(0.64f, 0.62f), color, w, true);
                ci.DrawLine(P(0.44f, 0.12f), P(0.56f, 0.12f), color, w, true);
                ci.DrawLine(P(0.5f, 0.12f), P(0.5f, 0.22f), color, w, true);
                break;
            case GlyphKind.Close:
                ci.DrawLine(P(0.24f, 0.24f), P(0.76f, 0.76f), color, w * 1.3f, true);
                ci.DrawLine(P(0.76f, 0.24f), P(0.24f, 0.76f), color, w * 1.3f, true);
                break;
            case GlyphKind.RotateLeft:
            case GlyphKind.RotateRight:
            {
                bool right = kind == GlyphKind.RotateLeft; // arrow geometry below is drawn for the counter-clockwise case when true
                ci.DrawArc(P(0.5f, 0.52f), 0.28f * s, right ? -Mathf.Pi * 0.75f : -Mathf.Pi * 0.25f, right ? Mathf.Pi * 0.75f : Mathf.Pi * 1.25f, 24, color, w * 1.1f, true);
                var tip = right ? P(0.3f, 0.3f) : P(0.7f, 0.3f);
                var a = right ? P(0.32f, 0.12f) : P(0.68f, 0.12f);
                var b = right ? P(0.14f, 0.34f) : P(0.86f, 0.34f);
                ci.DrawColoredPolygon(new[] { tip + (tip - (a + b) / 2) * 0.6f, a, b }, color);
                break;
            }
            case GlyphKind.Up:
                ci.DrawColoredPolygon(new[] { P(0.5f, 0.24f), P(0.82f, 0.72f), P(0.18f, 0.72f) }, color);
                break;
            case GlyphKind.Down:
                ci.DrawColoredPolygon(new[] { P(0.18f, 0.28f), P(0.82f, 0.28f), P(0.5f, 0.76f) }, color);
                break;
            case GlyphKind.Check:
                ci.DrawPolyline(new[] { P(0.2f, 0.52f), P(0.42f, 0.74f), P(0.8f, 0.28f) }, color, w * 1.3f, true);
                break;
            case GlyphKind.Pin:
                ci.DrawCircle(P(0.5f, 0.32f), 0.17f * s, color);
                ci.DrawLine(P(0.5f, 0.45f), P(0.5f, 0.88f), color, w, true);
                break;
            case GlyphKind.Play:
                ci.DrawColoredPolygon(new[] { P(0.3f, 0.2f), P(0.8f, 0.5f), P(0.3f, 0.8f) }, color);
                break;
            case GlyphKind.Talk:
                Rounded(ci, new Rect2(P(0.12f, 0.18f), new Vector2(0.76f * s, 0.5f * s)), color, w);
                ci.DrawPolyline(new[] { P(0.32f, 0.68f), P(0.26f, 0.86f), P(0.48f, 0.68f) }, color, w, true);
                break;
        }
    }

    private static Vector2[] Arc(Vector2 center, float radius, float from, float to)
    {
        const int n = 16;
        var points = new Vector2[n + 1];
        for (int i = 0; i <= n; i++)
        {
            float a = from + (to - from) * i / n;
            points[i] = center + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * radius;
        }
        return points;
    }

    private static void Rounded(CanvasItem ci, Rect2 r, Color color, float w)
    {
        var box = new StyleBoxFlat { DrawCenter = false, BorderColor = color, AntiAliasing = true };
        box.SetBorderWidthAll((int)Math.Round(w));
        box.SetCornerRadiusAll((int)(Math.Min(r.Size.X, r.Size.Y) * 0.18f));
        box.Draw(ci.GetCanvasItem(), r);
    }
}
