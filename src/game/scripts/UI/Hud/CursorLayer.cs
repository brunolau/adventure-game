using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Text;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;
using LastBell.Game.World;

namespace LastBell.Game.UI.Hud;

/// <summary>
/// Top-most, mouse-transparent layer (CanvasLayer 70) that owns the contextual cursor (owner control changes
/// 2026-10-05): every frame it decides the <see cref="CursorKind"/> from what is under the pointer — Core's left-click
/// resolution of the hit (talk / use / look / walk), exits with their direction, the selected item, busy while lines,
/// cutscenes or transitions play — and applies it as a hardware cursor (<see cref="CursorSet"/>, sized to the window).
/// Fallbacks: without hardware cursors the selected item's icon follows the pointer in software (as before); the QA
/// flag <c>--soft-cursor</c> also draws the cursor itself so screenshots show it. Optional highlight ring (setting).
/// </summary>
public partial class CursorLayer : Control
{
    private ItemIcon icon = null!;
    private string? shownItem;
    private Hit? lastHit;
    private GameState? lastState;
    private CursorKind worldKind = CursorKind.Pointer;

    /// <summary>When true the item icon is hidden (e.g. a full-screen menu is open).</summary>
    public bool Suppressed { get; set; }

    /// <summary>QA (harness <c>--soft-cursor</c>): draw the cursor image in software so viewport screenshots contain it.</summary>
    public static bool SoftwareCursor { get; set; }

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
        icon = new ItemIcon(84);
        icon.Size = new Vector2(84, 84);
        AddChild(icon);
        icon.Visible = false;
    }

    /// <inheritdoc />
    public override void _ExitTree() => CursorSet.Reset();

    /// <summary>Window px per canvas px (window height / 1080, letterbox aware).</summary>
    public float WindowScale => GetTree().Root.GetFinalTransform().Scale.Y;

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        var game = GameRuntime.Instance;
        if (!game.IsReady) return;
        var state = game.State;
        string? item = !Suppressed && state.Mode is GameMode.World or GameMode.Inventory ? state.SelectedItem : null;
        Texture2D? itemTexture = null;
        if (item is not null && game.Content.FindItem(item) is { } def)
        {
            itemTexture = ItemIcon.Load(def.Icon);
            if (item != shownItem) icon.SetItem(def.Icon, TextService.Get(TextKeys.NameOf(def)));
        }
        shownItem = item;

        var kind = Decide(state, item);
        int size = CursorSet.SizeFor(WindowScale, UiSettings.HudScale);
        bool hardware = CursorSet.Apply(kind, size, itemTexture, item ?? "");
        icon.Visible = item is not null && !hardware && !SoftwareCursor;
        var mouse = GetLocalMousePosition();
        if (icon.Visible) icon.Position = mouse + new Vector2(18, 18);
        if (UiSettings.CursorHighlight || SoftwareCursor || icon.Visible) QueueRedraw();
    }

    private CursorKind Decide(GameState state, string? item)
    {
        var stage = WorldStage.Instance;
        bool lines = state.ActiveLineId is not null || state.Mode == GameMode.Cutscene;
        if (lines || stage is null || stage.Transitioning) return CursorKind.Busy;
        if (state.Mode is not (GameMode.World or GameMode.Inventory) || Suppressed) return CursorKind.Pointer;
        if (item is not null) return CursorKind.Item;
        if (GetViewport().GuiGetHoveredControl() is not null || stage.Current is not { } room || !stage.IsSettled) return CursorKind.Pointer;
        var hit = room.HitTest(stage.GetGlobalMousePosition());
        if (Equals(hit, lastHit) && ReferenceEquals(state, lastState)) return worldKind;
        lastHit = hit;
        lastState = state;
        worldKind = KindFor(room, hit);
        return worldKind;
    }

    /// <summary>The cursor for a world hit: exits by direction, else by Core's left-click resolution.</summary>
    public static CursorKind KindFor(Room room, Hit hit)
    {
        if (hit is Hit.Exit exit && room.TryGetTarget(exit.Id, out var target)) return ExitKind(target.Rect);
        if (hit is not Hit.Hotspot) return CursorKind.Pointer;
        return GameRuntime.Instance.Session.Resolve(hit, PointerButton.Left) switch
        {
            Resolution.Dialogue => CursorKind.Talk,
            Resolution.Action => CursorKind.Hand,
            Resolution.Look => CursorKind.Look,
            Resolution.Travel => CursorKind.ExitUp,
            _ => CursorKind.Pointer,
        };
    }

    /// <summary>
    /// Direction of an exit zone: zones near the left / right picture edge point there; zones in the middle point
    /// up (into the picture, a door or a path) above the lower third and down (towards the viewer) below it.
    /// </summary>
    public static CursorKind ExitKind(Rect2 rect)
    {
        var c = rect.GetCenter();
        float w = Room.CanvasSize.X, h = Room.CanvasSize.Y;
        if (c.X < w * 0.16f) return CursorKind.ExitLeft;
        if (c.X > w * 0.84f) return CursorKind.ExitRight;
        return c.Y > h * 0.80f ? CursorKind.ExitDown : CursorKind.ExitUp;
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        var p = GetLocalMousePosition();
        if (UiSettings.CursorHighlight)
        {
            DrawCircle(p, 30, new Color(UiTheme.BrassLight, 0.22f));
            DrawArc(p, 30, 0, Mathf.Tau, 40, new Color(UiTheme.BrassLight, 0.95f), 4, true);
            DrawArc(p, 34, 0, Mathf.Tau, 40, new Color(0, 0, 0, 0.6f), 2, true);
        }
        if (!SoftwareCursor) return;
        int size = CursorSet.SizeFor(WindowScale, UiSettings.HudScale);
        var game = GameRuntime.Instance;
        Texture2D? itemTexture = shownItem is not null && game.Content.FindItem(shownItem) is { } def ? ItemIcon.Load(def.Icon) : null;
        if (CursorSet.Build(CursorSet.Current, size, itemTexture, shownItem ?? "") is not { } built) return;
        float k = 1f / Mathf.Max(0.01f, WindowScale); // window px -> canvas px
        var texture = ImageTexture.CreateFromImage(built.Image);
        DrawTextureRect(texture, new Rect2(p - built.Hotspot * k, new Vector2(size, size) * k), false);
    }
}
