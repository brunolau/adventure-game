using System;
using Godot;
using LastBell.Core.Text;
using LastBell.Game.Runtime;

namespace LastBell.Game.World;

/// <summary>
/// Development stand-in for a character: a coloured capsule figure with head, facing nose, walk
/// bob, talk mouth and a small gesture pop, plus the character name under the feet. Origin = feet.
/// Replaced by the sprite visual of the living-world agent.
/// </summary>
public partial class PlaceholderActorVisual : Node2D, IActorVisual
{
    private ActorContext? context;
    private bool walking;
    private bool talking;
    private Vector2 direction = Vector2.Right;
    private float time;
    private float gestureTime;
    private Color body = Colors.SlateGray;
    private string label = "";

    /// <inheritdoc />
    public Node2D Node => this;

    /// <inheritdoc />
    public float HeightPx => 400f;

    /// <inheritdoc />
    public float WalkSpeedPxPerSecond => 300f;

    /// <inheritdoc />
    public void Bind(ActorContext ctx)
    {
        context = ctx;
        // Stable colour per character id (not random, so screenshots are reproducible).
        uint hash = 2166136261;
        foreach (char c in ctx.CharacterId) hash = (hash ^ c) * 16777619;
        body = ctx.IsHero ? new Color(0.20f, 0.42f, 0.78f) : Color.FromHsv((hash % 360) / 360f, 0.45f, 0.78f);
        var game = GameRuntime.Instance;
        var character = game?.Content?.FindCharacter(ctx.CharacterId);
        label = character is null ? "" : TextService.Get(TextKeys.NameOf(character));
        QueueRedraw();
    }

    /// <inheritdoc />
    public void SetLocomotion(bool isWalking, Vector2 dir)
    {
        walking = isWalking;
        if (dir.LengthSquared() > 0.0001f) direction = dir.Normalized();
    }

    /// <inheritdoc />
    public void SetTalking(bool isTalking) => talking = isTalking;

    /// <inheritdoc />
    public void PlayGesture(string animation)
    {
        if (!string.IsNullOrEmpty(animation)) gestureTime = 0.6f;
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        time += (float)delta * (walking && GetParent() is Actor actor ? actor.WalkFactor : 1f);
        if (gestureTime > 0) gestureTime = MathF.Max(0, gestureTime - (float)delta);
        QueueRedraw();
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        float h = HeightPx;
        float bob = walking ? MathF.Abs(MathF.Sin(time * 9f)) * 10f : MathF.Sin(time * 2f) * 2f;
        float w = h * 0.26f;
        var outline = new Color(0.08f, 0.08f, 0.1f, 0.9f);
        // Legs
        float stride = walking ? MathF.Sin(time * 9f) * w * 0.35f : 0f;
        DrawLine(new Vector2(-w * 0.18f, -h * 0.42f), new Vector2(-w * 0.18f + stride, 0), outline, 10f);
        DrawLine(new Vector2(w * 0.18f, -h * 0.42f), new Vector2(w * 0.18f - stride, 0), outline, 10f);
        // Torso
        var torso = new Rect2(-w / 2, -h * 0.78f - bob, w, h * 0.40f);
        DrawRect(torso, body);
        DrawRect(torso, outline, false, 3f);
        // Arm (raised during a gesture)
        float raise = gestureTime > 0 ? 0.6f : 0f;
        var shoulder = new Vector2(direction.X >= 0 ? w * 0.45f : -w * 0.45f, -h * 0.72f - bob);
        var hand = shoulder + new Vector2(direction.X >= 0 ? w * 0.35f : -w * 0.35f, h * (0.28f - raise * 0.45f));
        DrawLine(shoulder, hand, body.Darkened(0.3f), 9f);
        // Head
        float r = h * 0.10f;
        var head = new Vector2(0, -h * 0.78f - r - bob);
        DrawCircle(head, r, new Color(0.93f, 0.80f, 0.68f));
        DrawArc(head, r, 0, MathF.Tau, 32, outline, 3f);
        // Nose shows the facing direction
        float face = direction.X >= 0 ? 1f : -1f;
        DrawCircle(head + new Vector2(face * r * 0.95f, r * 0.05f), r * 0.18f, new Color(0.85f, 0.65f, 0.55f));
        // Eye and mouth
        DrawCircle(head + new Vector2(face * r * 0.4f, -r * 0.2f), r * 0.1f, outline);
        float mouth = talking ? (MathF.Sin(time * 18f) > 0 ? r * 0.25f : r * 0.06f) : r * 0.04f;
        DrawRect(new Rect2(head + new Vector2(face * r * 0.25f - r * 0.2f, r * 0.35f), new Vector2(r * 0.4f, mouth + 2f)), outline);
        // Name tag under the feet (dev aid)
        if (label.Length > 0)
        {
            var font = ThemeDB.FallbackFont;
            const int size = 22;
            var textSize = font.GetStringSize(label, HorizontalAlignment.Left, -1, size);
            DrawString(font, new Vector2(-textSize.X / 2, 28), label, HorizontalAlignment.Left, -1, size, new Color(1, 1, 1, 0.85f));
        }
    }
}
