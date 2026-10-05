using System.Linq;
using Godot;
using LastBell.Game.Runtime;

namespace LastBell.Game.World;

/// <summary>
/// Development aid only (never final art): when a room has no painted background it draws an
/// in-engine blockout from the data — floor/wall split, walk polygon, hotspot rects with their
/// names, NPC rects, exits (green open, red locked), interaction points and the spawn. With
/// <see cref="OverlayOnly"/> it draws just the outlines above painted art (F3 / --dev).
/// </summary>
public partial class DevBlockout : Node2D
{
    private Room? room;

    /// <summary>Outline-only overlay mode (no fills, no backdrop).</summary>
    public bool OverlayOnly { get; set; }

    /// <summary>Binds the room and redraws.</summary>
    public void Setup(Room owner, bool overlayOnly)
    {
        room = owner;
        OverlayOnly = overlayOnly;
        QueueRedraw();
    }

    private static Color EraTint(int era) => era switch
    {
        1960 => new Color(0.55f, 0.50f, 0.40f),
        1982 => new Color(0.48f, 0.47f, 0.52f),
        1995 => new Color(0.42f, 0.52f, 0.50f),
        2020 => new Color(0.45f, 0.50f, 0.58f),
        2035 => new Color(0.40f, 0.48f, 0.62f),
        _ => new Color(0.5f, 0.5f, 0.5f),
    };

    /// <inheritdoc />
    public override void _Draw()
    {
        if (room is null) return;
        var font = ThemeDB.FallbackFont;
        var walk = room.Walk;
        var tint = EraTint(room.View.Era);
        if (!OverlayOnly)
        {
            // Wall and floor backdrop split at the back edge of the walk band.
            DrawRect(new Rect2(0, 0, Room.CanvasSize.X, walk.Top), tint.Darkened(0.35f));
            DrawRect(new Rect2(0, walk.Top, Room.CanvasSize.X, Room.CanvasSize.Y - walk.Top), tint.Darkened(0.1f));
            for (int x = 0; x <= 1920; x += 120) DrawLine(new Vector2(x, 0), new Vector2(x, walk.Top), new Color(1, 1, 1, 0.04f), 2);
            string title = TextService.Ui("ui.dev.blockout", ("room", room.RoomId), ("name", TextService.Get(room.View.Name)), ("era", room.View.Era.ToString()));
            DrawString(font, new Vector2(24, 44), title, HorizontalAlignment.Left, -1, 30, new Color(1, 1, 1, 0.75f));
        }
        // Walk polygon.
        var poly = walk.Polygon.ToArray();
        if (poly.Length >= 3)
        {
            if (!OverlayOnly) DrawColoredPolygon(poly, new Color(0.35f, 0.75f, 0.45f, 0.28f));
            DrawPolyline(poly.Append(poly[0]).ToArray(), new Color(0.4f, 0.95f, 0.5f, 0.9f), 3f);
        }
        foreach (var t in room.Targets)
        {
            Color c = t.Kind switch
            {
                TargetKind.Npc => new Color(0.35f, 0.62f, 1f),
                TargetKind.Exit => t.Unlocked ? new Color(0.3f, 0.95f, 0.45f) : new Color(1f, 0.32f, 0.3f),
                _ => t.IsAtmospheric ? new Color(0.85f, 0.85f, 0.85f) : new Color(1f, 0.76f, 0.2f),
            };
            if (!OverlayOnly && t.Kind != TargetKind.Npc) DrawRect(t.Rect, new Color(c, 0.30f));
            DrawRect(t.Rect, c, false, 3f);
            // Interaction point cross and link.
            var ip = t.InteractionPoint;
            DrawLine(ip + new Vector2(-10, 0), ip + new Vector2(10, 0), c, 3f);
            DrawLine(ip + new Vector2(0, -10), ip + new Vector2(0, 10), c, 3f);
            DrawDashedLine(new Vector2(t.Rect.GetCenter().X, t.Rect.End.Y), ip, new Color(c, 0.45f), 2f, 10f);
            // Names are drawn by the label layer while Space labels are on.
            if (OverlayOnly || room.View.HotspotLabels) continue;
            string name = TextService.Get(t.Name);
            if (t.Kind == TargetKind.Exit)
            {
                // Exit label above its zone, kept on screen.
                var size = font.GetStringSize(name, HorizontalAlignment.Left, -1, 18);
                float x = Mathf.Clamp(t.Rect.GetCenter().X - size.X / 2, 6, Room.CanvasSize.X - size.X - 6);
                DrawString(font, new Vector2(x, t.Rect.Position.Y - 8), name, HorizontalAlignment.Left, -1, 18, c);
                continue;
            }
            // Name inside the rect (props) or under it (NPCs) so the blockout reads without pressing Space.
            float width = Mathf.Max(80, t.Rect.Size.X - 12);
            var pos = t.Kind == TargetKind.Npc ? new Vector2(t.Rect.Position.X + 2, t.Rect.Position.Y - 30) : t.Rect.Position + new Vector2(6, 24);
            DrawMultilineString(font, pos, name, HorizontalAlignment.Left, width, 18, 3, Colors.White);
            DrawString(font, new Vector2(t.Rect.Position.X + 4, t.Rect.End.Y - 6), t.Id, HorizontalAlignment.Left, width + 8, 14, new Color(1, 1, 1, 0.65f));
        }
        if (room.View.Spawn.Count >= 2)
        {
            var s = new Vector2(room.View.Spawn[0], room.View.Spawn[1]);
            DrawArc(s, 14, 0, Mathf.Tau, 24, new Color(1, 0, 1, 0.8f), 3f);
        }
    }
}

/// <summary>Dev marker for a visible state-variant layer whose art does not exist yet.</summary>
public partial class DevVariantMarker : Node2D
{
    /// <summary>Asset path from visual_variant_layers.</summary>
    public string AssetName { get; set; } = "";

    /// <summary>Stack index (markers are listed top-right).</summary>
    public int Index { get; set; }

    /// <inheritdoc />
    public override void _Draw()
    {
        var font = ThemeDB.FallbackFont;
        string text = TextService.Ui("ui.dev.variant_missing", ("asset", AssetName));
        var pos = new Vector2(1900 - 640, 40 + Index * 30);
        DrawRect(new Rect2(pos - new Vector2(8, 22), new Vector2(648, 28)), new Color(0.2f, 0.1f, 0.3f, 0.7f));
        DrawString(font, pos, text, HorizontalAlignment.Left, 630, 18, new Color(1f, 0.85f, 1f));
    }
}
