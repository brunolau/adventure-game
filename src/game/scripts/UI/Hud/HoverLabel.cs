using Godot;
using LastBell.Core.State;
using LastBell.Game.Hooks;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;
using LastBell.Game.World;

namespace LastBell.Game.UI.Hud;

/// <summary>
/// The contextual hover label next to the cursor (owner control changes 2026-10-05, item 3; it replaced the hover text
/// in the bottom HUD strip). Large outlined text in the game font, readable on any background: the target's name and,
/// only while an item is selected and Core says the rule is executable, the action sentence below it (same texts as
/// <see cref="HudView.Texts"/>). Mouse hover: the label sits right of the cursor image, flips to the left near the
/// right edge and above the cursor near the bottom (HUD strip), and never leaves the screen; it hides while the pointer
/// is over a GUI control, over the open bag (bar and detail card) and while any screen is open (hints, menus, journal
/// ..., <see cref="UiRoot.ScreenCovers"/>, PT-S23). Keyboard focus (Tab): the label is centred at the focused target. Inventory slots keep their
/// own hover line in the drawer. Lives in the cursor layer (CanvasLayer 70, canvas px), mouse-transparent.
/// Touch mode (<see cref="TouchMode"/>): there is no cursor, the label belongs to the finger. It is centred above the
/// touch point (<see cref="FingerLiftMm"/> higher, so the finger does not cover it), anchored at the position the
/// input router reports (not at Godot's mouse position) and not hidden by a stale "hovered control".
/// </summary>
public partial class HoverLabel : Control
{
    private const int NameSize = 40;
    private const int ActionSize = 32;
    private const int Outline = 12;

    /// <summary>Touch mode: how far above the touch point the label's bottom edge sits (a fingertip is about 8 mm).</summary>
    public const float FingerLiftMm = 8f;
    private HudView? hud;
    private string nameText = "";
    private string actionText = "";
    private Vector2 origin;
    private bool shown;

    /// <summary>The shown name ("" when hidden; QA).</summary>
    public string ShownName => shown ? nameText : "";

    /// <summary>The shown action sentence ("" when hidden or none; QA).</summary>
    public string ShownAction => shown ? actionText : "";

    /// <summary>Top-left of the text block in canvas px while shown (QA).</summary>
    public Rect2 ShownRect { get; private set; }

    /// <summary>Binds the HUD whose hover payload the label shows.</summary>
    public void Init(HudView view)
    {
        hud = view;
        hud.HoverChanged += Refresh;
    }

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
    }

    private void Refresh()
    {
        var payload = hud?.CurrentHover;
        var (name, action) = HudView.Texts(payload);
        nameText = payload is { FromInventory: false } ? name : "";
        actionText = payload is { FromInventory: false } ? action : "";
        QueueRedraw();
    }

    private float TextScale => Mathf.Clamp(UiSettings.HudScale, 1f, 1.5f) * (UiSettings.HighContrastLabels ? 1.12f : 1f);

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        var payload = hud?.CurrentHover;
        var state = GameRuntime.Instance.IsReady ? GameRuntime.Instance.State : null;
        var mouse = LastBell.Game.Diagnostics.QaWindow.ViewportPointer(GetViewport()); // Godot's mouse position (QA: last event)
        bool finger = TouchMode.Enabled && payload is { FromKeyboard: false };
        var next = payload is { FromKeyboard: true } ? payload.ScreenPosition
            : finger ? payload!.ScreenPosition - new Vector2(0, Mathf.Clamp(TouchMode.MmToCanvasPx(FingerLiftMm, 90f), 60f, 150f))
            : LastBell.Game.Diagnostics.QaWindow.UseEventPointer ? GetGlobalTransformWithCanvas().AffineInverse() * mouse : GetLocalMousePosition();
        bool want = payload is { FromInventory: false } && (nameText.Length > 0 || actionText.Length > 0) &&
                    state?.Mode is GameMode.World or GameMode.Inventory && state.ActiveLineId is null &&
                    (payload.FromKeyboard || finger || GetViewport().GuiGetHoveredControl() is null) &&
                    !(UiRoot.Instance?.ScreenCovers(finger ? payload.ScreenPosition : mouse) ?? false);
        if (want != shown || (want && next != origin))
        {
            shown = want;
            origin = next;
            QueueRedraw();
        }
    }

    /// <summary>
    /// Where the text block goes: right of the cursor image, flipped left / up near the edges, clamped on screen.
    /// <paramref name="cursorPx"/> is the cursor image size in canvas px, <paramref name="side"/> the share of it right of the hotspot.
    /// </summary>
    public static Rect2 Place(Vector2 pointer, Vector2 block, float cursorPx, bool atTarget, float bottomReserve, float side = 0.62f)
    {
        var screen = Room.CanvasSize;
        const float margin = 12f;
        Vector2 pos;
        if (atTarget)
        {
            pos = new Vector2(pointer.X - block.X / 2, pointer.Y - block.Y);
        }
        else
        {
            pos = new Vector2(pointer.X + cursorPx * side, pointer.Y + cursorPx * 0.42f - block.Y / 2);
            if (pos.X + block.X > screen.X - margin) pos.X = pointer.X - cursorPx * 0.12f - block.X; // flip left
            if (pos.Y + block.Y > screen.Y - bottomReserve) pos.Y = pointer.Y - cursorPx * 0.2f - block.Y; // flip up
        }
        pos.X = Mathf.Clamp(pos.X, margin, Mathf.Max(margin, screen.X - margin - block.X));
        pos.Y = Mathf.Clamp(pos.Y, margin, Mathf.Max(margin, screen.Y - margin - block.Y));
        return new Rect2(pos, block);
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        ShownRect = new Rect2();
        if (!shown) return;
        var font = UiTheme.Heading;
        float k = TextScale;
        int nameSize = (int)(NameSize * k), actionSize = (int)(ActionSize * k), outline = (int)(Outline * k);
        var nameDim = nameText.Length > 0 ? font.GetStringSize(nameText, HorizontalAlignment.Left, -1, nameSize) : Vector2.Zero;
        var actionFont = UiTheme.BodyBold;
        var actionDim = actionText.Length > 0 ? actionFont.GetStringSize(actionText, HorizontalAlignment.Left, -1, actionSize) : Vector2.Zero;
        var block = new Vector2(Mathf.Max(nameDim.X, actionDim.X), nameDim.Y + actionDim.Y);
        var payload = hud?.CurrentHover;
        bool atTarget = payload?.FromKeyboard == true || TouchMode.Enabled; // touch: centred above the finger
        float windowScale = Mathf.Max(0.01f, GetTree().Root.GetFinalTransform().Scale.Y);
        float cursorPx = (CursorSet.CurrentSize > 0 ? CursorSet.CurrentSize : 48) / windowScale;
        float bottomReserve = HudView.StripHeight * UiSettings.HudScale + 8;
        // The item cursor carries the icon across its whole square: the label starts right of it.
        float side = CursorSet.Current switch { CursorKind.Item => 1.0f, CursorKind.Hand => 0.8f, _ => 0.62f };
        var rect = Place(origin, block, cursorPx, atTarget, bottomReserve, side);
        ShownRect = rect;
        if (UiSettings.HighContrastLabels)
            DrawStyleBox(UiTheme.Box(new Color(0, 0, 0, 0.82f), new Color(UiTheme.BrassLight, 0.9f), 2, 10, 0), rect.Grow(10));
        float y = rect.Position.Y;
        var ink = new Color(0.07f, 0.05f, 0.03f, 0.92f);
        if (nameText.Length > 0)
        {
            var at = new Vector2(rect.Position.X + (block.X - nameDim.X) / 2, y + font.GetAscent(nameSize));
            DrawStringOutline(font, at + new Vector2(0, 3), nameText, HorizontalAlignment.Left, -1, nameSize, outline + 4, new Color(0, 0, 0, 0.35f));
            DrawStringOutline(font, at, nameText, HorizontalAlignment.Left, -1, nameSize, outline, ink);
            DrawString(font, at, nameText, HorizontalAlignment.Left, -1, nameSize, UiSettings.HighContrastLabels ? Colors.Yellow : new Color("fff6e0"));
            y += nameDim.Y;
        }
        if (actionText.Length > 0)
        {
            var at = new Vector2(rect.Position.X + (block.X - actionDim.X) / 2, y + actionFont.GetAscent(actionSize));
            DrawStringOutline(actionFont, at, actionText, HorizontalAlignment.Left, -1, actionSize, outline, ink);
            DrawString(actionFont, at, actionText, HorizontalAlignment.Left, -1, actionSize, UiTheme.BrassLight);
        }
    }
}
