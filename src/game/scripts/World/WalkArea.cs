using System;
using System.Collections.Generic;
using System.Linq;
using Godot;

namespace LastBell.Game.World;

/// <summary>
/// Walkable area of a room built from <c>rooms[].walk_polygon</c> with deterministic polygon
/// pathfinding: a straight line when it stays inside, otherwise the shortest path over a
/// visibility graph of the polygon's reflex vertices (A*). Pure geometry, no NavigationServer
/// (deterministic in headless runs and on every platform).
/// </summary>
public sealed class WalkArea
{
    private const float Inset = 2f;
    private readonly Vector2[] polygon;
    private readonly Vector2[] nodes;

    /// <summary>Creates the area from game.json points.</summary>
    public WalkArea(IEnumerable<IReadOnlyList<int>> points)
    {
        polygon = points.Where(p => p.Count >= 2).Select(p => new Vector2(p[0], p[1])).ToArray();
        if (polygon.Length >= 3 && SignedArea(polygon) < 0) Array.Reverse(polygon); // counter-clockwise in y-down = clockwise visually
        nodes = BuildNodes();
        if (polygon.Length > 0)
        {
            Top = polygon.Min(p => p.Y);
            Bottom = polygon.Max(p => p.Y);
        }
    }

    /// <summary>Polygon points.</summary>
    public IReadOnlyList<Vector2> Polygon => polygon;

    /// <summary>Smallest y of the polygon (back of the walk band).</summary>
    public float Top { get; }

    /// <summary>Largest y of the polygon (front of the walk band).</summary>
    public float Bottom { get; }

    /// <summary>True when the point lies inside (or on the edge of) the polygon.</summary>
    public bool Contains(Vector2 p) => polygon.Length >= 3 && (Geometry2D.IsPointInPolygon(p, polygon) || DistanceToEdges(p) < 0.01f);

    /// <summary>The point itself when inside, else the closest point slightly inside the polygon.</summary>
    public Vector2 Clamp(Vector2 p)
    {
        if (polygon.Length < 3 || Contains(p)) return p;
        Vector2 best = polygon[0];
        float bestDist = float.MaxValue;
        for (int i = 0; i < polygon.Length; i++)
        {
            var c = Geometry2D.GetClosestPointToSegment(p, polygon[i], polygon[(i + 1) % polygon.Length]);
            float d = c.DistanceSquaredTo(p);
            if (d < bestDist) { bestDist = d; best = c; }
        }
        var centroid = Centroid();
        var inward = (centroid - best).Normalized() * Inset;
        return Contains(best + inward) ? best + inward : best;
    }

    /// <summary>
    /// Path from <paramref name="from"/> to <paramref name="to"/> (both clamped into the area), as
    /// waypoints excluding the start. Returns null when no path exists.
    /// </summary>
    public List<Vector2>? FindPath(Vector2 from, Vector2 to)
    {
        from = Clamp(from);
        to = Clamp(to);
        if (SegmentInside(from, to)) return new List<Vector2> { to };
        // A* over start, goal and the reflex vertices.
        var all = new List<Vector2>(nodes.Length + 2) { from, to };
        all.AddRange(nodes);
        int n = all.Count;
        var g = Enumerable.Repeat(float.MaxValue, n).ToArray();
        var prev = Enumerable.Repeat(-1, n).ToArray();
        var closed = new bool[n];
        g[0] = 0;
        var open = new PriorityQueue<int, float>();
        open.Enqueue(0, all[0].DistanceTo(to));
        while (open.Count > 0)
        {
            int cur = open.Dequeue();
            if (closed[cur]) continue;
            closed[cur] = true;
            if (cur == 1) break;
            for (int next = 0; next < n; next++)
            {
                if (next == cur || closed[next] || !SegmentInside(all[cur], all[next])) continue;
                float cost = g[cur] + all[cur].DistanceTo(all[next]);
                if (cost >= g[next]) continue;
                g[next] = cost;
                prev[next] = cur;
                open.Enqueue(next, cost + all[next].DistanceTo(to));
            }
        }
        if (prev[1] < 0) return null;
        var path = new List<Vector2>();
        for (int i = 1; i != 0; i = prev[i]) path.Add(all[i]);
        path.Reverse();
        return path;
    }

    /// <summary>True when the segment does not leave the polygon.</summary>
    public bool SegmentInside(Vector2 a, Vector2 b)
    {
        if (polygon.Length < 3) return true;
        if (!Contains(a) || !Contains(b) || !Contains((a + b) * 0.5f)) return false;
        for (int i = 0; i < polygon.Length; i++)
        {
            var p = polygon[i];
            var q = polygon[(i + 1) % polygon.Length];
            var crossing = Geometry2D.SegmentIntersectsSegment(a, b, p, q);
            if (crossing.VariantType != Variant.Type.Vector2) continue;
            var hit = crossing.AsVector2();
            if (hit.DistanceTo(a) > 0.5f && hit.DistanceTo(b) > 0.5f && hit.DistanceTo(p) > 0.5f && hit.DistanceTo(q) > 0.5f)
                return false;
        }
        // Sample points so a segment grazing a reflex corner from outside is rejected.
        for (int s = 1; s < 8; s++)
            if (!Contains(a.Lerp(b, s / 8f))) return false;
        return true;
    }

    private Vector2[] BuildNodes()
    {
        var result = new List<Vector2>();
        int n = polygon.Length;
        if (n < 4) return result.ToArray();
        var centroid = Centroid();
        for (int i = 0; i < n; i++)
        {
            var prev = polygon[(i + n - 1) % n];
            var cur = polygon[i];
            var next = polygon[(i + 1) % n];
            float cross = (cur - prev).Cross(next - cur);
            if (cross >= 0) continue; // convex corner (orientation normalised in the constructor)
            // Reflex corner: offset slightly into the polygon along the bisector.
            var bisector = ((prev - cur).Normalized() + (next - cur).Normalized()).Normalized();
            var candidate = cur - bisector * Inset * 2f;
            if (!Contains(candidate)) candidate = cur + bisector * Inset * 2f;
            if (!Contains(candidate)) candidate = cur.Lerp(centroid, 0.01f);
            result.Add(candidate);
        }
        return result.ToArray();
    }

    private Vector2 Centroid()
    {
        var sum = Vector2.Zero;
        foreach (var p in polygon) sum += p;
        return polygon.Length == 0 ? sum : sum / polygon.Length;
    }

    private float DistanceToEdges(Vector2 p)
    {
        float best = float.MaxValue;
        for (int i = 0; i < polygon.Length; i++)
            best = Mathf.Min(best, Geometry2D.GetClosestPointToSegment(p, polygon[i], polygon[(i + 1) % polygon.Length]).DistanceTo(p));
        return best;
    }

    private static float SignedArea(Vector2[] pts)
    {
        float a = 0;
        for (int i = 0; i < pts.Length; i++) a += pts[i].Cross(pts[(i + 1) % pts.Length]);
        return a * 0.5f;
    }
}

/// <summary>Perspective scale by feet y: linear between the top and the bottom of the walk band, clamped.</summary>
/// <param name="Top">Back edge y of the walk band.</param>
/// <param name="Bottom">Front edge y of the walk band.</param>
/// <param name="ScaleTop">Scale at <paramref name="Top"/> (default 0.80).</param>
/// <param name="ScaleBottom">Scale at <paramref name="Bottom"/> (default 1.00).</param>
public readonly record struct Perspective(float Top, float Bottom, float ScaleTop, float ScaleBottom)
{
    /// <summary>Scale for feet at <paramref name="y"/>.</summary>
    public float ScaleAt(float y)
    {
        if (Bottom - Top < 1f) return ScaleBottom;
        float t = Mathf.Clamp((y - Top) / (Bottom - Top), 0f, 1f);
        return Mathf.Lerp(ScaleTop, ScaleBottom, t);
    }
}
