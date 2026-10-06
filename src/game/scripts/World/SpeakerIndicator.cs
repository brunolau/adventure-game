using Godot;
using LastBell.Game.Runtime;

namespace LastBell.Game.World;

/// <summary>
/// The "voice without a body" badge of <see cref="GuestStage"/> (ISSUES PT-S18): a brass-ringed cream disc in the style of
/// the Space markers with a small drawn icon of the source (mobile phone, cassette, service-channel speaker, device
/// screen) and sound arcs that pulse while the line is being revealed. Drawn in code (no icon font, no licensed set),
/// above the actors; it fades in when a remote line starts and out when it ends. Respects reduced motion.
/// </summary>
public partial class SpeakerIndicator : Node2D
{
    /// <summary>Disc radius in canvas px.</summary>
    public const float Radius = 30f;

    private static readonly Color Brass = new("c9973a");
    private static readonly Color BrassDark = new("7a5a22");
    private static readonly Color Cream = new("f4e9d2");
    private static readonly Color Ink = new("2b2622");
    private static readonly Color Teal = new("1f5a5a");

    private RemoteSpeakerKind kind;
    private float alpha;
    private bool fadingOut;
    private float time;
    private int arcSide = 1;

    /// <summary>True while the line text is still being revealed (the arcs pulse).</summary>
    public bool Talking { get; set; }

    /// <summary>The source drawn now (QA).</summary>
    public RemoteSpeakerKind Kind => kind;

    /// <summary>Shows the badge for a new line at a canvas point.</summary>
    public void Present(RemoteSpeakerKind what, Vector2 point, bool besideHero)
    {
        kind = what;
        Position = point;
        // Beside the hero the arcs point away from his head; above a device they point up-right.
        arcSide = besideHero && point.X < (WorldStage.Instance?.Current?.Hero.Feet.X ?? point.X) ? -1 : 1;
        fadingOut = false;
        Visible = true;
        QueueRedraw();
    }

    /// <summary>Fades the badge out (it hides itself at zero).</summary>
    public void FadeOut() => fadingOut = true;

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        float dt = (float)delta;
        time += dt;
        bool still = PresentationSettings.ReducedMotion;
        float target = fadingOut ? 0f : 1f;
        alpha = still ? target : Mathf.MoveToward(alpha, target, dt / 0.2f);
        Modulate = new Color(1, 1, 1, alpha);
        if (fadingOut && alpha <= 0.001f) Visible = false;
        if (Visible) QueueRedraw();
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        bool still = PresentationSettings.ReducedMotion;
        float bob = still ? 0f : 1.5f * Mathf.Sin(time * Mathf.Tau / 1.6f);
        var c = new Vector2(0, bob);
        DrawCircle(c + new Vector2(0, 3), Radius + 2, new Color(0, 0, 0, 0.3f));
        DrawCircle(c, Radius + 3, Brass);
        DrawCircle(c, Radius - 1, Cream);
        DrawArc(c, Radius + 3, 0, Mathf.Tau, 48, BrassDark, 1.5f, true);
        switch (kind)
        {
            case RemoteSpeakerKind.Phone: DrawPhone(c); break;
            case RemoteSpeakerKind.Recording: DrawCassette(c); break;
            case RemoteSpeakerKind.Radio: DrawRadio(c); break;
            default: DrawDevice(c); break;
        }
        DrawArcs(c, still);
    }

    private void DrawArcs(Vector2 c, bool still)
    {
        // Three sound arcs outside the disc; while talking they pulse outwards one after another.
        var origin = c + new Vector2(arcSide * (Radius + 4), -4);
        float angle = arcSide > 0 ? 0f : Mathf.Pi;
        for (int i = 0; i < 3; i++)
        {
            float a = 0.9f;
            if (Talking && !still) a = 0.35f + 0.65f * Mathf.Clamp(Mathf.Sin(time * Mathf.Tau * 1.4f - i * 0.9f) * 0.5f + 0.5f, 0, 1);
            else if (!Talking) a = 0.45f;
            float r = 8 + i * 7;
            DrawArc(origin, r, angle - 0.7f, angle + 0.7f, 12, new Color(Cream, a), 4.5f, true);
            DrawArc(origin, r, angle - 0.7f, angle + 0.7f, 12, new Color(Ink, a), 2.5f, true);
        }
    }

    private void DrawRounded(Rect2 r, float radius, Color color)
    {
        DrawRect(new Rect2(r.Position + new Vector2(radius, 0), new Vector2(r.Size.X - 2 * radius, r.Size.Y)), color);
        DrawRect(new Rect2(r.Position + new Vector2(0, radius), new Vector2(r.Size.X, r.Size.Y - 2 * radius)), color);
        DrawCircle(r.Position + new Vector2(radius, radius), radius, color);
        DrawCircle(r.Position + new Vector2(r.Size.X - radius, radius), radius, color);
        DrawCircle(r.Position + new Vector2(radius, r.Size.Y - radius), radius, color);
        DrawCircle(r.End - new Vector2(radius, radius), radius, color);
    }

    private void DrawPhone(Vector2 c)
    {
        var body = new Rect2(c + new Vector2(-10, -17), new Vector2(20, 34));
        DrawRounded(body, 4, Ink);
        DrawRect(new Rect2(c + new Vector2(-7, -12), new Vector2(14, 22)), Teal);
        DrawRect(new Rect2(c + new Vector2(-4, -15), new Vector2(8, 1.5f)), Cream);
        DrawCircle(c + new Vector2(0, 13.5f), 1.8f, Cream);
    }

    private void DrawCassette(Vector2 c)
    {
        var body = new Rect2(c + new Vector2(-18, -12), new Vector2(36, 24));
        DrawRounded(body, 3, Ink);
        DrawRect(new Rect2(c + new Vector2(-13, -8), new Vector2(26, 9)), Cream);
        DrawCircle(c + new Vector2(-6.5f, -3.5f), 3.2f, Ink);
        DrawCircle(c + new Vector2(6.5f, -3.5f), 3.2f, Ink);
        DrawRect(new Rect2(c + new Vector2(-9, 5), new Vector2(18, 4)), Brass);
    }

    private void DrawRadio(Vector2 c)
    {
        DrawLine(c + new Vector2(8, -12), c + new Vector2(12, -21), Ink, 3f, true);
        var body = new Rect2(c + new Vector2(-14, -12), new Vector2(28, 28));
        DrawRounded(body, 4, Ink);
        for (int i = 0; i < 3; i++) DrawRect(new Rect2(c + new Vector2(-9, -6 + i * 6), new Vector2(18, 2.5f)), Cream);
        DrawCircle(c + new Vector2(0, 11), 2.4f, Brass);
    }

    private void DrawDevice(Vector2 c)
    {
        var body = new Rect2(c + new Vector2(-17, -13), new Vector2(34, 24));
        DrawRounded(body, 3, Ink);
        DrawRect(new Rect2(c + new Vector2(-13, -9), new Vector2(26, 16)), Teal);
        // a small waveform on the screen
        var pts = new[] { new Vector2(-11, -1), new Vector2(-6, -1), new Vector2(-3, -6), new Vector2(1, 4), new Vector2(4, -3), new Vector2(7, -1), new Vector2(11, -1) };
        for (int i = 0; i + 1 < pts.Length; i++) DrawLine(c + pts[i], c + pts[i + 1], Cream, 2f, true);
        DrawRect(new Rect2(c + new Vector2(-6, 11), new Vector2(12, 4)), Ink);
    }
}
