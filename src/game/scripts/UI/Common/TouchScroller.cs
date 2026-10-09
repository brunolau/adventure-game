using Godot;
using LastBell.Game.PlayerInput;
using LastBell.Game.Runtime;

namespace LastBell.Game.UI.Common;

/// <summary>
/// Touch mode (<see cref="TouchMode"/>): a finger that slides over a scroll area scrolls it, wherever it went down.
/// <para>
/// Why the engine does not do it: Godot's own touch scrolling (ScrollContainer, 4.7.2) only starts when the press
/// reaches the scroll container, and a press never passes a button or another control that stops the mouse
/// (Viewport::_gui_call_input). Almost every list of this game is made of buttons (the title menu, save slots,
/// settings rows, topics, hints, the map, the inventory), so on a phone nothing scrolled (owner report 2026-10-09;
/// reproduced on the emulator with the title menu of a game that has a save: "Quit" stayed out of reach).
/// </para>
/// <para>
/// What this node does, from the mouse events Godot makes of the first finger (they come before the GUI sees them):
/// the finger goes down over a scroll area that has more content than room; when it has moved further than
/// <see cref="TouchGestures.SlopPx"/> along an axis the area scrolls on, the slide is a scroll: the buttons under the
/// finger give up their press (NOTIFICATION_SCROLL_BEGIN, as with the engine's own scrolling), the content follows
/// the finger, and lifting lets it coast and slow down. A finger that hardly moves is still a tap. Presses and
/// releases are never taken away from the GUI; only the moves of a slide that scrolls are.
/// </para>
/// <para>
/// Sliders (the volumes): a slider takes its value at the very moment it is touched, so a finger that only wanted to
/// scroll past it changed the volume. Here a touch on a slider is kept from the slider: sliding along it moves the
/// value by that distance, sliding across it scrolls the list, and a tap sets the value at that point. A touch on a
/// scroll bar is left to the scroll bar.
/// </para>
/// Not in a desktop build: the node only exists in touch mode (<see cref="UiRoot"/>), the PC keeps the wheel.
/// </summary>
public partial class TouchScroller : Node
{
    private enum Phase { Idle, Down, Scroll, Slide }

    /// <summary>Coasting slows down by this factor per second (e^-x).</summary>
    private const float Friction = 4.2f;

    /// <summary>Coasting ends below this speed (logical px/s) and never starts above <see cref="MaxFling"/>.</summary>
    private const float MinFling = 60f;

    private const float MaxFling = 5000f;

    private const int Emulated = (int)InputEvent.DeviceIdEmulation;

    /// <summary>The singleton (touch mode only).</summary>
    public static TouchScroller? Instance { get; private set; }

    /// <summary>
    /// True from the moment the slide of the current touch became a scroll until the next finger goes down: a control
    /// that acts on the release by its own code (the inventory slots) must not act then.
    /// </summary>
    public static bool ScrolledThisTouch { get; private set; }

    private Phase phase;
    private ScrollContainer? area;
    private Slider? slider;
    private Vector2 downAt;
    private Vector2 anchorFinger;
    private Vector2 anchorScroll;
    private double sliderStart;
    private Vector2 velocity; // of the finger, logical px/s of the area
    private Vector2 lastMoveAt;
    private double lastMoveTime;
    private ScrollContainer? coasting;
    private Vector2 coastPosition;

    private static double Now => Time.GetTicksMsec() / 1000.0;

    /// <inheritdoc />
    public override void _Ready()
    {
        Instance = this;
        ProcessMode = ProcessModeEnum.Always;
    }

    /// <inheritdoc />
    public override void _ExitTree()
    {
        if (Instance == this) Instance = null;
    }

    /// <inheritdoc />
    public override void _Input(InputEvent e)
    {
        if (e is InputEventMouseButton { ButtonIndex: MouseButton.Left } button && button.Device == Emulated)
        {
            bool keep = button.Pressed ? Down(button.Position) : Up(button.Position);
            if (keep) GetViewport().SetInputAsHandled();
            return;
        }
        if (e is InputEventMouseMotion motion && motion.Device == Emulated && Move(motion.Position))
            GetViewport().SetInputAsHandled();
    }

    /// <summary>The finger goes down. True when the GUI must not see the press (it is on a slider).</summary>
    private bool Down(Vector2 point)
    {
        if (coasting is { } gliding && IsInstanceValid(gliding)) EndScroll(gliding); // a touch stops the coasting list
        coasting = null;
        ScrolledThisTouch = false;
        velocity = Vector2.Zero;
        (area, slider) = Find(point);
        phase = area is null && slider is null ? Phase.Idle : Phase.Down;
        downAt = anchorFinger = lastMoveAt = point;
        lastMoveTime = Now;
        if (slider is not null) sliderStart = slider.Value;
        return slider is not null;
    }

    /// <summary>The finger moves. True when the GUI must not see the move.</summary>
    private bool Move(Vector2 point)
    {
        if (phase == Phase.Idle) return false;
        if (slider is not null && (!IsInstanceValid(slider) || !slider.IsVisibleInTree())) { phase = Phase.Idle; return true; }
        if (area is not null && (!IsInstanceValid(area) || !area.IsVisibleInTree()))
        {
            area = null;
            if (phase == Phase.Scroll || slider is null) phase = Phase.Idle;
        }
        bool withheld = slider is not null; // the slider never saw the press: nothing of this touch reaches the GUI
        if (phase == Phase.Down)
        {
            var d = point - downAt;
            float ax = Mathf.Abs(d.X), ay = Mathf.Abs(d.Y);
            if (slider is not null && ax > TouchGestures.SlopPx && ax >= ay) phase = Phase.Slide;
            else if (area is not null && WantsScroll(area, ax, ay)) BeginScroll(area, point);
            else return withheld;
        }
        if (phase == Phase.Slide && slider is not null)
        {
            float along = slider.GetGlobalTransformWithCanvas().AffineInverse().BasisXform(point - downAt).X;
            slider.Value = sliderStart + along / Track(slider) * (slider.MaxValue - slider.MinValue);
            return true;
        }
        if (phase == Phase.Scroll && area is not null)
        {
            var inverse = area.GetGlobalTransformWithCanvas().AffineInverse();
            Place(area, anchorScroll - inverse.BasisXform(point - anchorFinger));
            double now = Now;
            if (now - lastMoveTime > 0.004)
            {
                var speed = inverse.BasisXform(point - lastMoveAt) / (float)(now - lastMoveTime);
                velocity = velocity.Lerp(speed, 0.6f);
                lastMoveAt = point;
                lastMoveTime = now;
            }
            return true;
        }
        return withheld;
    }

    /// <summary>The finger is lifted. True when the GUI must not see the release (its press was on a slider).</summary>
    private bool Up(Vector2 point)
    {
        bool withheld = slider is not null;
        if (phase == Phase.Scroll && area is not null && IsInstanceValid(area))
        {
            velocity = velocity.LimitLength(MaxFling);
            if (Now - lastMoveTime < 0.1 && velocity.Length() > MinFling)
            {
                coasting = area;
                coastPosition = new Vector2(area.ScrollHorizontal, area.ScrollVertical);
            }
            else EndScroll(area);
        }
        else if (phase == Phase.Down && slider is not null && IsInstanceValid(slider) && point.DistanceTo(downAt) <= TouchGestures.SlopPx)
        {
            // A tap on the slider: the value at that point.
            float at = (slider.GetGlobalTransformWithCanvas().AffineInverse() * point).X - (slider.Size.X - Track(slider)) / 2;
            slider.Value = slider.MinValue + Mathf.Clamp(at / Track(slider), 0f, 1f) * (slider.MaxValue - slider.MinValue);
        }
        phase = Phase.Idle;
        area = null;
        slider = null;
        return withheld;
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        if (coasting is not { } list) return;
        if (!IsInstanceValid(list) || !list.IsVisibleInTree()) { coasting = null; return; }
        coastPosition -= velocity * (float)delta;
        velocity *= Mathf.Exp(-Friction * (float)delta);
        Place(list, coastPosition);
        // An axis that has reached its end stops there.
        if (Mathf.Abs(list.ScrollHorizontal - coastPosition.X) > 1f) { coastPosition.X = list.ScrollHorizontal; velocity.X = 0; }
        if (Mathf.Abs(list.ScrollVertical - coastPosition.Y) > 1f) { coastPosition.Y = list.ScrollVertical; velocity.Y = 0; }
        if (velocity.Length() >= MinFling) return;
        coasting = null;
        EndScroll(list);
    }

    private void BeginScroll(ScrollContainer list, Vector2 point)
    {
        phase = Phase.Scroll;
        ScrolledThisTouch = true;
        anchorFinger = lastMoveAt = point; // from here on the content follows the finger: no jump by the slop
        anchorScroll = new Vector2(list.ScrollHorizontal, list.ScrollVertical);
        lastMoveTime = Now;
        velocity = Vector2.Zero;
        list.PropagateNotification((int)Control.NotificationScrollBegin); // buttons under the finger give up their press
    }

    private static void EndScroll(ScrollContainer list)
    {
        list.PropagateNotification((int)Control.NotificationScrollEnd);
        GD.Print($"LastBell: touch scroll of {list.GetParent()?.Name}/{list.Name} ended at {list.ScrollHorizontal},{list.ScrollVertical}");
    }

    private static void Place(ScrollContainer list, Vector2 position)
    {
        if (Scrolls(list.GetHScrollBar(), list.HorizontalScrollMode)) list.ScrollHorizontal = Mathf.RoundToInt(position.X);
        if (Scrolls(list.GetVScrollBar(), list.VerticalScrollMode)) list.ScrollVertical = Mathf.RoundToInt(position.Y);
    }

    /// <summary>True when the area has more content than room on that axis.</summary>
    private static bool Scrolls(ScrollBar bar, ScrollContainer.ScrollMode mode) =>
        mode != ScrollContainer.ScrollMode.Disabled && bar.MaxValue - bar.MinValue > bar.Page + 0.5;

    /// <summary>
    /// A slide of <paramref name="ax"/> / <paramref name="ay"/> canvas px starts a scroll when it is past the slop on an
    /// axis the area scrolls on; an area that scrolls on one axis only wants the slide to go mostly along that axis
    /// (a sideways slide over a vertical list is not a scroll).
    /// </summary>
    private static bool WantsScroll(ScrollContainer list, float ax, float ay)
    {
        bool h = Scrolls(list.GetHScrollBar(), list.HorizontalScrollMode), v = Scrolls(list.GetVScrollBar(), list.VerticalScrollMode);
        return (v && ay > TouchGestures.SlopPx && (h || ay >= ax)) || (h && ax > TouchGestures.SlopPx && (v || ax >= ay));
    }

    /// <summary>The length the grabber of a slider travels, in the slider's own px.</summary>
    private static float Track(Slider s)
    {
        float grabber = s.HasThemeIcon("grabber") ? s.GetThemeIcon("grabber").GetWidth() : 0;
        return Mathf.Max(1f, s.Size.X - grabber);
    }

    private static bool Has(Control control, Vector2 point) =>
        new Rect2(Vector2.Zero, control.Size).HasPoint(control.GetGlobalTransformWithCanvas().AffineInverse() * point);

    /// <summary>
    /// What is under a point of the viewport: the innermost scroll area that can scroll and the slider, both of the top
    /// screen when one is open. Nothing when the point is on a scroll bar of that area. Parts that a clipping parent
    /// hides (rows scrolled out of a list) do not count.
    /// </summary>
    private (ScrollContainer?, Slider?) Find(Vector2 point)
    {
        ScrollContainer? list = null;
        Slider? knob = null;
        bool onBar = false;
        Node scope = UiRoot.Instance?.TopModal is { } top ? top : GetTree().Root;
        Visit(scope);
        return onBar ? (null, null) : (list, knob);

        void Visit(Node node)
        {
            if (node is CanvasItem { Visible: false } or CanvasLayer { Visible: false }) return;
            if (node is Control { ClipContents: true } clip && !Has(clip, point)) return;
            if (node is ScrollContainer sc && Has(sc, point) &&
                (Scrolls(sc.GetHScrollBar(), sc.HorizontalScrollMode) || Scrolls(sc.GetVScrollBar(), sc.VerticalScrollMode)))
            {
                list = sc;
                onBar = (sc.GetVScrollBar().Visible && Has(sc.GetVScrollBar(), point)) || (sc.GetHScrollBar().Visible && Has(sc.GetHScrollBar(), point));
            }
            else if (node is Slider { Editable: true } s && Has(s, point)) knob = s;
            foreach (var child in node.GetChildren()) Visit(child);
        }
    }
}
