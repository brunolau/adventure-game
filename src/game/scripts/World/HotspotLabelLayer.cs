using System.Linq;
using Godot;
using LastBell.Game.Runtime;

namespace LastBell.Game.World;

/// <summary>Draws actor shadows (layer "npc_shadows", below every actor).</summary>
public partial class ShadowLayer : Node2D
{
    /// <summary>Owner room.</summary>
    public Room Room { get; set; } = null!;

    /// <inheritdoc />
    public override void _Process(double delta) => QueueRedraw();

    /// <inheritdoc />
    public override void _Draw()
    {
        if (Room?.ActorsLayer is null) return;
        foreach (var actor in Room.ActorsLayer.GetChildren().OfType<Actor>())
        {
            if (actor.Visual is { CastsShadow: false }) continue;
            float s = actor.CurrentScale;
            DrawSetTransform(actor.Position, 0, new Vector2(1f, 0.28f));
            DrawCircle(Vector2.Zero, 70f * s, new Color(0, 0, 0, 0.28f));
            DrawSetTransform(Vector2.Zero, 0, Vector2.One);
        }
    }
}

/// <summary>
/// Layer "hotspot_labels": the Space labels of every visible hotspot (NPCs, progress and purely
/// atmospheric props) and exit, the subtle outline of targets valid for the selected item, and the
/// keyboard focus highlight. It only draws what the room's current view says is visible.
/// </summary>
public partial class HotspotLabelLayer : Node2D
{
    private string? focusedId;

    /// <summary>Owner room.</summary>
    public Room Room { get; set; } = null!;

    /// <summary>Keyboard-focused target id (always labelled and outlined), or null.</summary>
    public string? FocusedId
    {
        get => focusedId;
        set
        {
            focusedId = value;
            QueueRedraw();
        }
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        if (Room?.View is null) return;
        var font = ThemeDB.FallbackFont;
        bool all = Room.View.HotspotLabels;
        bool contrast = PresentationSettings.HighContrastLabels;
        foreach (var t in Room.Targets)
        {
            bool focused = t.Id == focusedId;
            if (t.ValidForSelectedItem) DrawRect(t.Rect.Grow(4), new Color(1f, 0.95f, 0.6f, 0.55f), false, 2f);
            if (focused) DrawRect(t.Rect.Grow(6), new Color(1f, 1f, 1f, 0.95f), false, 4f);
            if (!all && !focused) continue;
            string text = TextService.Get(t.Name);
            if (text.Length == 0) continue;
            int size = contrast ? 26 : 22;
            var textSize = font.GetStringSize(text, HorizontalAlignment.Left, -1, size);
            var pos = t.LabelAnchor - new Vector2(textSize.X / 2, 0);
            pos.X = Mathf.Clamp(pos.X, 8, Room.CanvasSize.X - textSize.X - 8);
            pos.Y = Mathf.Clamp(pos.Y, textSize.Y + 8, Room.CanvasSize.Y - 8);
            var box = new Rect2(pos + new Vector2(-10, -textSize.Y - 2), textSize + new Vector2(20, 12));
            var bg = contrast ? new Color(0, 0, 0, 0.92f) : new Color(0.06f, 0.07f, 0.1f, 0.72f);
            var border = t.Kind switch
            {
                TargetKind.Exit => new Color(0.65f, 0.9f, 1f),
                TargetKind.Npc => new Color(1f, 0.85f, 0.55f),
                _ => t.IsAtmospheric ? new Color(0.8f, 0.8f, 0.8f) : new Color(1f, 1f, 1f),
            };
            DrawRect(box, bg);
            DrawRect(box, focused ? Colors.White : new Color(border, 0.8f), false, focused ? 3f : 1.5f);
            if (t.Kind == TargetKind.Exit)
            {
                // Small arrow towards the exit side.
                float dir = t.Rect.GetCenter().X < Room.CanvasSize.X / 2 ? -1 : 1;
                var tip = new Vector2(dir < 0 ? box.Position.X - 14 : box.End.X + 14, box.GetCenter().Y);
                DrawColoredPolygon(new[] { tip, tip + new Vector2(-dir * 12, -8), tip + new Vector2(-dir * 12, 8) }, border);
            }
            DrawString(font, pos, text, HorizontalAlignment.Left, -1, size, contrast ? Colors.Yellow : Colors.White);
        }
    }
}
