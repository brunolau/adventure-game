using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using Godot;

namespace LastBell.Game.Living.Ambient;

/// <summary>
/// Type <c>flicker</c>: light that changes over time: fluorescent tubes, screens, LEDs, hazard
/// lights, a pulsing portal glow, a candle. Draws a glow texture (default <c>builtin:glow</c>, or
/// <c>builtin:softrect</c> for tubes) stretched over <c>rect</c>, additive by default.
/// <code>
/// { "type": "flicker", "rect": [x, y, w, h], "texture": "builtin:softrect", "color": "#fff6d8",
///   "mode": "fluorescent", "min": 0.15, "max": 0.35, "period_s": 1.0, "duty": 0.5, "every_s": [6, 18] }
/// </code>
/// Modes: fluorescent (steady hum, now and then a burst of rapid flicker), pulse (sine between min
/// and max over period_s), blink (on/off, duty = on fraction, soft edges), noise (smooth random:
/// candle, TV), sweep (a band of light crossing the rect every period_s, e.g. headlights on a ceiling).
/// Reduced motion holds the mean brightness.
/// </summary>
public partial class FlickerLayer : AmbientLayer
{
    private SpriteSource? source;
    private Rect2 rect;
    private Color color;
    private string mode = "pulse";
    private float min, max, period, duty;
    private Vector2 every;
    private float nextBurst;
    private float burstLeft;
    private float noiseA, noiseB, noiseT;
    private float level;

    /// <inheritdoc />
    protected override bool DefaultAdditive => true;

    /// <inheritdoc />
    protected override void Configure(JsonObject def)
    {
        mode = def.Str("mode", "pulse")!;
        source = AmbientContext.Sprite(def.Str("texture", mode == "fluorescent" ? "builtin:softrect" : "builtin:glow"));
        rect = def.Rect("rect") ?? new Rect2(def.Vec("pos") - def.Vec("size", new Vector2(64, 64)) / 2, def.Vec("size", new Vector2(64, 64)));
        color = def.Col("color", new Color(1f, 0.95f, 0.8f));
        min = def.Num("min", 0.2f);
        max = def.Num("max", 0.5f);
        period = Math.Max(0.05f, def.Num("period_s", 2f));
        duty = def.Num("duty", 0.5f);
        every = def.Range("every_s", new Vector2(6, 18));
        nextBurst = Pick(every);
        noiseA = Rng.Randf();
        noiseB = Rng.Randf();
        level = (min + max) / 2;
    }

    /// <inheritdoc />
    public override void SetReducedMotion(bool on)
    {
        base.SetReducedMotion(on);
        if (on) level = mode == "blink" ? max * duty + min * (1 - duty) : (min + max) / 2;
        if (on && mode == "fluorescent") level = max;
        QueueRedraw();
    }

    /// <inheritdoc />
    protected override void Step(float dt)
    {
        float t = Time;
        switch (mode)
        {
            case "fluorescent":
                nextBurst -= dt;
                if (nextBurst <= 0 && burstLeft <= 0) { burstLeft = Rng.RandfRange(0.25f, 0.9f); nextBurst = Pick(every); }
                if (burstLeft > 0)
                {
                    burstLeft -= dt;
                    level = Rng.Randf() < 0.45f ? min : max * Rng.RandfRange(0.7f, 1f);
                }
                else level = max * (0.97f + 0.03f * MathF.Sin(t * 47f));
                break;
            case "blink":
            {
                float f = (t % period) / period;
                float edge = 0.04f;
                float on = f < duty ? Smooth(f / edge) * Smooth((duty - f) / edge) : 0f;
                level = Mathf.Lerp(min, max, on);
                break;
            }
            case "noise":
                noiseT += dt / period;
                if (noiseT >= 1) { noiseT -= 1; noiseA = noiseB; noiseB = Rng.Randf(); }
                level = Mathf.Lerp(min, max, Mathf.Lerp(noiseA, noiseB, Smooth(noiseT)));
                break;
            case "sweep":
                level = max;
                break;
            default: // pulse
                level = Mathf.Lerp(min, max, 0.5f + 0.5f * MathF.Sin(t / period * MathF.Tau));
                break;
        }
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        if (source is null) return;
        var c = new Color(color.R, color.G, color.B, color.A * level);
        if (mode == "sweep")
        {
            // a soft band moving across the rect once per period, idle the rest of the time
            float f = (Time % period) / period;
            float active = duty > 0 ? f / duty : f;
            if (active > 1) return;
            float w = rect.Size.X * 0.35f;
            float x = rect.Position.X - w + (rect.Size.X + w) * active;
            var scaleS = new Vector2(w / source.Cell.X, rect.Size.Y / source.Cell.Y);
            DrawQuad(source, 0, new Vector2(x + w / 2, rect.Position.Y + rect.Size.Y / 2), scaleS, 0, c * new Color(1, 1, 1, MathF.Sin(active * MathF.PI)));
            return;
        }
        var scale = new Vector2(rect.Size.X / source.Cell.X, rect.Size.Y / source.Cell.Y);
        DrawQuad(source, 0, rect.GetCenter(), scale, 0, c);
    }
}

/// <summary>
/// Type <c>clouds</c>: painted clouds drifting across the sky band with parallax (bigger = nearer =
/// faster), wrapping around. Use a sky mask (<c>mask</c>) so they pass behind roofs and trees.
/// <code>{ "type": "clouds", "textures": ["common/cloud_00.webp", ...], "band": [10, 120], "count": 3, "speed_px_s": 6, "scale": [0.25, 0.45], "alpha": 0.9 }</code>
/// </summary>
public partial class CloudLayer : AmbientLayer
{
    private struct Cloud
    {
        public Vector2 Pos;
        public float Scale;
        public int Tex;
        public bool Flip;
    }

    private readonly List<SpriteSource> textures = new();
    private readonly List<Cloud> clouds = new();
    private Vector2 band;
    private float speed;
    private Vector2 scale;
    private float minX, maxX;

    /// <inheritdoc />
    protected override void Configure(JsonObject def)
    {
        textures.AddRange(AmbientContext.Sprites(def));
        if (textures.Count == 0) return;
        band = def.Range("band", new Vector2(20, 140));
        speed = def.Num("speed_px_s", 6);
        scale = def.Range("scale", new Vector2(0.3f, 0.5f));
        var span = def.Range("x_span", new Vector2(0, 1920));
        int count = Math.Max(1, def.Int("count", 3));
        float widest = 0;
        foreach (var t in textures) widest = Math.Max(widest, t.Cell.X * scale.Y);
        minX = span.X - widest / 2 - 20;
        maxX = span.Y + widest / 2 + 20;
        for (int i = 0; i < count; i++)
        {
            clouds.Add(new Cloud
            {
                Pos = new Vector2(Mathf.Lerp(minX, maxX, (i + Rng.RandfRange(0.1f, 0.9f)) / count), Pick(band)),
                Scale = Pick(scale),
                Tex = i % textures.Count,
                Flip = Rng.Randf() < 0.5f,
            });
        }
    }

    /// <inheritdoc />
    protected override void Step(float dt)
    {
        for (int i = 0; i < clouds.Count; i++)
        {
            var c = clouds[i];
            float parallax = scale.Y > 0 ? c.Scale / scale.Y : 1;
            c.Pos.X += speed * parallax * dt;
            if (speed > 0 && c.Pos.X > maxX) { c.Pos.X = minX; c.Pos.Y = Pick(band); }
            if (speed < 0 && c.Pos.X < minX) { c.Pos.X = maxX; c.Pos.Y = Pick(band); }
            clouds[i] = c;
        }
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        foreach (var c in clouds)
            DrawQuad(textures[c.Tex], 0, c.Pos, new Vector2(c.Flip ? -c.Scale : c.Scale, c.Scale), 0, Colors.White);
    }
}
