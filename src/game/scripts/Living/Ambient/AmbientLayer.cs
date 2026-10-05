using System;
using System.Text.Json.Nodes;
using Godot;

namespace LastBell.Game.Living.Ambient;

/// <summary>What a layer does when reduced motion is on (ART_DIRECTION section 5).</summary>
public enum ReducedMotionMode
{
    /// <summary>Stop where it is (default for loops, particles, sway, clouds).</summary>
    Freeze,
    /// <summary>Hide (default for things crossing the screen: cars, birds, passers-by).</summary>
    Hide,
    /// <summary>Keep moving at a quarter of the speed.</summary>
    Slow,
}

/// <summary>
/// Base of every ambient layer: one Node2D at the room origin that draws all of its elements itself
/// in room canvas coordinates (quads through <see cref="DrawQuad"/>), so one material can clip or
/// mask it. Handles time, deterministic randomness, reduced motion, optional clip rect / mask, blend
/// mode and prewarming. Subclasses read their own JSON fields in <see cref="Configure"/>.
/// </summary>
public abstract partial class AmbientLayer : Node2D
{
    private static readonly Vector2[] QuadUv = { new(0, 0), new(1, 0), new(1, 1), new(0, 1) };
    private readonly Vector2[] quad = new Vector2[4];
    private readonly Vector2[] uv = new Vector2[4];
    private readonly Color[] colors = new Color[4];
    private bool reduced;

    /// <summary>Layer id from the data (unique per room).</summary>
    public string LayerId { get; private set; } = "";

    /// <summary>Layer type name from the data.</summary>
    public string LayerType { get; private set; } = "";

    /// <summary>Deterministic randomness (seeded from room + layer id).</summary>
    protected RandomNumberGenerator Rng { get; } = new();

    /// <summary>Build context.</summary>
    protected AmbientContext Context { get; private set; } = null!;

    /// <summary>Layer time in seconds (frozen with reduced motion).</summary>
    protected float Time { get; private set; }

    /// <summary>Behaviour under reduced motion.</summary>
    protected ReducedMotionMode ReducedMode { get; set; } = ReducedMotionMode.Freeze;

    /// <summary>The layer's shader material (null when it needs none).</summary>
    protected ShaderMaterial? Shader { get; private set; }

    /// <summary>Global speed multiplier of the layer (data "speed_scale").</summary>
    protected float SpeedScale { get; private set; } = 1f;

    /// <summary>True while reduced motion is active.</summary>
    public bool Reduced => reduced;

    /// <summary>Effect the layer's shader needs.</summary>
    protected virtual AmbientEffect Effect => AmbientEffect.None;

    /// <summary>Default for additive blending (glows).</summary>
    protected virtual bool DefaultAdditive => false;

    /// <summary>Default reduced-motion mode of the layer type.</summary>
    protected virtual ReducedMotionMode DefaultReducedMode => ReducedMotionMode.Freeze;

    /// <summary>Reads the shared fields, then the subclass fields.</summary>
    public void Setup(JsonObject def, AmbientContext context, string id, string type)
    {
        Context = context;
        LayerId = id;
        LayerType = type;
        Name = "Ambient_" + id;
        Rng.Seed = context.SeedFor(id);
        SpeedScale = def.Num("speed_scale", 1f);
        ReducedMode = def.Str("reduced_motion") switch
        {
            "hide" => ReducedMotionMode.Hide,
            "slow" => ReducedMotionMode.Slow,
            "freeze" => ReducedMotionMode.Freeze,
            _ => DefaultReducedMode,
        };
        Modulate = new Color(1, 1, 1, def.Num("alpha", 1f));
        if (def.Has("modulate")) SelfModulate = def.Col("modulate", Colors.White);
        ZIndex = def.Int("z", 0);
        Configure(def);
        BuildMaterial(def);
        if (Shader is not null) ConfigureShader(def, Shader);
        float prewarm = def.Num("prewarm_s", DefaultPrewarm);
        for (float s = 0; s < prewarm; s += 1f / 20f) Advance(1f / 20f);
    }

    /// <summary>Seconds simulated at build time so the room never starts empty.</summary>
    protected virtual float DefaultPrewarm => 0f;

    /// <summary>Reads the type-specific fields.</summary>
    protected abstract void Configure(JsonObject def);

    /// <summary>Sets type-specific shader parameters (called after <see cref="Configure"/>).</summary>
    protected virtual void ConfigureShader(JsonObject def, ShaderMaterial material) { }

    /// <summary>Advances the simulation by dt seconds (already scaled for reduced motion).</summary>
    protected abstract void Step(float dt);

    /// <summary>Switches reduced motion on or off.</summary>
    public virtual void SetReducedMotion(bool on)
    {
        reduced = on;
        Visible = !(on && ReducedMode == ReducedMotionMode.Hide);
        QueueRedraw();
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        float dt = (float)delta * SpeedScale;
        if (reduced) dt *= ReducedMode == ReducedMotionMode.Slow ? 0.25f : 0f;
        if (dt <= 0) return;
        Advance(dt);
        QueueRedraw();
    }

    private void Advance(float dt)
    {
        Time += dt;
        Shader?.SetShaderParameter("t", Time);
        Step(dt);
    }

    private void BuildMaterial(JsonObject def)
    {
        var clip = def.Rect("clip");
        string? maskPath = def.Str("mask");
        bool additive = def.Str("blend") switch { "add" => true, "mix" => false, _ => DefaultAdditive };
        var maskTex = AmbientContext.Texture(maskPath);
        if (clip is null && maskTex is null && Effect == AmbientEffect.None && !additive) return;
        Shader = new ShaderMaterial { Shader = AmbientShaders.Get(Effect, additive, clip is not null, maskTex is not null) };
        if (clip is { } c) Shader.SetShaderParameter("clip_rect", new Vector4(c.Position.X, c.Position.Y, c.Size.X, c.Size.Y));
        if (maskTex is not null)
        {
            var r = def.Rect("mask_rect") ?? AmbientContext.CutInfo(maskPath).Rect("mask_rect") ?? new Rect2(0, 0, 1920, 1080);
            Shader.SetShaderParameter("mask_tex", maskTex);
            Shader.SetShaderParameter("mask_rect", new Vector4(r.Position.X, r.Position.Y, r.Size.X, r.Size.Y));
            Shader.SetShaderParameter("mask_invert", def.Bool("mask_invert"));
        }
        Material = Shader;
    }

    /// <summary>
    /// Draws one textured quad centred on <paramref name="at"/> (the sprite's pivot lands there),
    /// rotated and scaled; negative <paramref name="scale"/>.X mirrors it.
    /// </summary>
    protected void DrawQuad(SpriteSource source, int frame, Vector2 at, Vector2 scale, float rotation, Color color)
    {
        var region = source.Region(frame);
        var texSize = source.Texture.GetSize();
        var size = region.Size;
        var pivot = source.Pivot;
        // corners relative to the pivot, before rotation
        Vector2 a = new Vector2(-pivot.X, -pivot.Y) * scale;
        Vector2 b = new Vector2(size.X - pivot.X, -pivot.Y) * scale;
        Vector2 c = new Vector2(size.X - pivot.X, size.Y - pivot.Y) * scale;
        Vector2 d = new Vector2(-pivot.X, size.Y - pivot.Y) * scale;
        if (rotation != 0)
        {
            a = a.Rotated(rotation); b = b.Rotated(rotation); c = c.Rotated(rotation); d = d.Rotated(rotation);
        }
        quad[0] = at + a; quad[1] = at + b; quad[2] = at + c; quad[3] = at + d;
        for (int i = 0; i < 4; i++)
        {
            uv[i] = (region.Position + QuadUv[i] * size) / texSize;
            colors[i] = color;
        }
        DrawPolygon(quad, colors, uv, source.Texture);
    }

    /// <summary>Random float in a [min, max] range vector.</summary>
    protected float Pick(Vector2 range) => range.Y > range.X ? Rng.RandfRange(range.X, range.Y) : range.X;

    /// <summary>Smoothstep.</summary>
    protected static float Smooth(float x)
    {
        x = Math.Clamp(x, 0, 1);
        return x * x * (3 - 2 * x);
    }
}
