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
        if (Room?.ActorsLayer is null || Room.Hero is null) return;
        foreach (var actor in Room.AllActors) // NPCs may sit in the fixed-depth layers (natural blocking "z")
        {
            if (!actor.IsInsideTree() || actor.IsQueuedForDeletion()) continue;
            if (actor.Visual is { CastsShadow: false }) continue;
            float s = actor.CurrentScale;
            DrawSetTransform(actor.Position, 0, new Vector2(1f, 0.28f));
            DrawCircle(Vector2.Zero, 70f * s, new Color(0, 0, 0, 0.28f * actor.Modulate.A)); // guests fade in and out
            DrawSetTransform(Vector2.Zero, 0, Vector2.One);
        }
    }
}

/// <summary>
/// Layer "hotspot_labels": while Space is held (Core <c>HotspotLabels</c>, owner override 2026-10-05, ISSUES INT-08) a
/// small painted round marker on every visible hotspot (NPCs, progress and purely atmospheric props) and exit (exits
/// get the arrow badge) — markers only, no text; a subtle pulse unless reduced motion is on. While an item is selected
/// only the targets where it has an executable use get a marker (owner control change 6, 2026-10-06). With an item selected
/// nothing is drawn on the valid targets otherwise: no permanent outline (owner 2026-10-06, control change 11); the hover
/// label at the cursor and the Space markers are the only hints. Also the keyboard focus outline of the Tab-focused target
/// (its label is the hover label, drawn at the target by the UI). The QA flag <c>--labels</c> (<see cref="PresentationSettings.QaTextLabels"/>) draws the
/// old text labels of all targets instead, for art review. It only draws what the room's current view says is visible.
/// </summary>
public partial class HotspotLabelLayer : Node2D
{
    /// <summary>Canvas px kept free at the bottom for the HUD strip (markers sit above it).</summary>
    public const float BottomReserve = 86f;

    /// <summary>Drawn marker diameter in canvas px (1920x1080).</summary>
    public const float MarkerSize = 54f;

    private const string MarkerPath = "res://assets/ui/cursors/marker_96.png";
    private const string ExitMarkerPath = "res://assets/ui/cursors/marker_exit_96.png";
    private static Texture2D? marker, exitMarker;
    private static bool texturesLoaded;
    private string? focusedId;
    private float time;
    private bool drawnMarkers;

    /// <summary>Owner room.</summary>
    public Room Room { get; set; } = null!;

    /// <summary>Keyboard-focused target id (outlined), or null.</summary>
    public string? FocusedId
    {
        get => focusedId;
        set
        {
            focusedId = value;
            QueueRedraw();
        }
    }

    /// <summary>Rect outlines drawn in the last frame (QA: only the Tab focus outline, never one per valid item target).</summary>
    public int OutlinesDrawn { get; private set; }

    /// <summary>Target ids that get a marker now (QA; empty while Space is not held).</summary>
    public System.Collections.Generic.IReadOnlyList<string> MarkedIds =>
        MarkersVisible ? Room.Targets.Where(IsMarkable).Select(t => t.Id).ToList() : System.Array.Empty<string>();

    /// <summary>
    /// Whether a target gets a Space marker (owner control change 6, 2026-10-06): without a selected item every visible
    /// target; with one only the targets where Core says the item has an executable use (<see cref="TargetInfo.ValidForSelectedItem"/>).
    /// </summary>
    public static bool IsMarkable(TargetInfo t) =>
        GameRuntime.Instance.State.SelectedItem is null || t.ValidForSelectedItem;

    /// <summary>Number of text labels drawn now (QA: 0 unless <c>--labels</c>).</summary>
    public int TextLabelsDrawn =>
        Room?.View is { HotspotLabels: true } && PresentationSettings.QaTextLabels ? Room.Targets.Count(t => TextService.Get(t.Name).Length > 0) : 0;

    /// <summary>True when markers are wanted now (Space held, world mode, not the QA text labels).</summary>
    public bool MarkersVisible =>
        Room?.View is { HotspotLabels: true } && !PresentationSettings.QaTextLabels &&
        GameRuntime.Instance.IsReady && GameRuntime.Instance.State.Mode == LastBell.Core.State.GameMode.World;

    /// <summary>Where a target's marker goes: the middle of the drawn NPC figure, a prop's rect centre, an exit's rect centre kept on screen.</summary>
    public Vector2 MarkerPoint(TargetInfo t)
    {
        if (t.Kind == TargetKind.Npc && Room.Npcs.TryGetValue(t.Id, out var actor))
        {
            var p = actor.Position - new Vector2(0, actor.Visual.HeightPx * actor.CurrentScale * 0.55f);
            // Busts and laptops (S54 Jana 2020) are cut at a sill: the middle of the full figure falls below the
            // drawn part and outside the clickable rect, so keep the marker inside the rect (playtest PT-S05).
            var rect = t.Rect.Grow(-8);
            if (!t.Rect.HasPoint(p) && rect.Size.X > 0 && rect.Size.Y > 0)
                p = new Vector2(Mathf.Clamp(p.X, rect.Position.X, rect.End.X), Mathf.Clamp(p.Y, rect.Position.Y, rect.End.Y));
            return p;
        }
        var c = t.Rect.GetCenter();
        float r = MarkerSize * 0.7f;
        // Above the HUD strip (82 px at the bottom): the template exit zones sit at the very bottom edge.
        return new Vector2(Mathf.Clamp(c.X, r, Room.CanvasSize.X - r), Mathf.Clamp(c.Y, r, Room.CanvasSize.Y - BottomReserve - r));
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        bool visible = MarkersVisible;
        if (visible || drawnMarkers)
        {
            time += (float)delta;
            QueueRedraw();
        }
    }

    private static void LoadTextures()
    {
        if (texturesLoaded) return;
        texturesLoaded = true;
        marker = ResourceLoader.Exists(MarkerPath) ? GD.Load<Texture2D>(MarkerPath) : null;
        exitMarker = ResourceLoader.Exists(ExitMarkerPath) ? GD.Load<Texture2D>(ExitMarkerPath) : null;
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        drawnMarkers = false;
        OutlinesDrawn = 0;
        if (Room?.View is null) return;
        bool markers = MarkersVisible;
        drawnMarkers = markers;
        bool qaText = PresentationSettings.QaTextLabels && Room.View.HotspotLabels;
        foreach (var t in Room.Targets)
        {
            // No outline on the targets valid for the selected item (owner 2026-10-06): only hover and Space show them.
            if (t.Id == focusedId) { DrawRect(t.Rect.Grow(6), new Color(1f, 1f, 1f, 0.95f), false, 4f); OutlinesDrawn++; }
            if (markers) { if (IsMarkable(t)) DrawMarker(t); }
            else if (qaText) DrawTextLabel(t);
        }
        // The painted node clock without a game.json hotspot (PT-F10) gets a marker too (not in MarkedIds: Core targets only).
        // Not while an item is selected: the clock is never an item target.
        if (Room.TimeNode is { HotspotId: null } node && GameRuntime.Instance.State.SelectedItem is null)
        {
            var info = new TargetInfo("time_node", TargetKind.Prop, Room.TimeNodeName, node.Rect, node.InteractionPoint,
                new Vector2(node.Rect.GetCenter().X, node.Rect.Position.Y - 10), false, false, true);
            if (markers) DrawMarker(info);
            else if (qaText) DrawTextLabel(info);
        }
    }

    private void DrawMarker(TargetInfo t)
    {
        LoadTextures();
        var p = MarkerPoint(t);
        bool still = PresentationSettings.ReducedMotion;
        // Subtle pulse, phase-shifted per target so the room does not blink in unison.
        float phase = (t.Id.GetHashCode() & 0xff) / 255f * Mathf.Tau;
        float pulse = still ? 1f : 1f + 0.07f * Mathf.Sin(time * Mathf.Tau / 1.3f + phase);
        float size = MarkerSize * pulse;
        var rect = new Rect2(p - new Vector2(size, size) / 2, new Vector2(size, size));
        var texture = t.Kind == TargetKind.Exit ? exitMarker ?? marker : marker;
        DrawCircle(p + new Vector2(0, 3), MarkerSize * 0.5f, new Color(0, 0, 0, 0.28f));
        if (texture is not null)
        {
            if (t.Kind == TargetKind.Exit)
            {
                // The badge's arrow points right; turn it towards the exit side.
                float angle = Room is { } r ? ExitSides.Angle(r.ExitSideOf(t)) : ExitAngle(t.Rect);
                DrawSetTransform(p, angle, Vector2.One);
                DrawTextureRect(texture, new Rect2(-new Vector2(size, size) / 2, new Vector2(size, size)), false);
                DrawSetTransform(Vector2.Zero, 0, Vector2.One);
            }
            else DrawTextureRect(texture, rect, false);
        }
        else
        {
            // Fallback when the painted badge is missing: brass ring, teal disc, cream dot.
            DrawCircle(p, size / 2, new Color("c9973a"));
            DrawCircle(p, size * 0.4f, new Color("1f5a5a"));
            DrawCircle(p, size * 0.1f, new Color("f4e9d2"));
        }
    }

    /// <summary>Rotation of the exit badge's arrow (pointing right at 0) towards the exit's side of the picture.</summary>
    public static float ExitAngle(Rect2 rect) => ExitSides.Angle(ExitSides.FromRect(rect));

    private void DrawTextLabel(TargetInfo t)
    {
        var font = ThemeDB.FallbackFont;
        bool contrast = PresentationSettings.HighContrastLabels;
        string text = TextService.Get(t.Name);
        if (text.Length == 0) return;
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
        DrawRect(box, new Color(border, 0.8f), false, 1.5f);
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
