using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using Godot;

namespace LastBell.Game.Living.Ambient;

/// <summary>
/// Type <c>sway</c>: wind on a cut-out of the background (tree crown, grass, vine, curtain,
/// washing line). The cut-out is drawn over the painting at its own place and displaced by the sway
/// shader; displacement is zero at the anchor and grows away from it.
/// <code>
/// { "type": "sway", "texture": "S02/birch_crown.webp", "pos": [x, y], "anchor": 0.95,
///   "amp_px": 3, "freq": 0.3, "wavelength_px": 200, "flutter_px": 0.6, "hang": false }
/// </code>
/// anchor: texture-relative y (0 top .. 1 bottom) that stays still; hang: true for things hanging
/// from the anchor (curtains, washing, a hanging basket), so they swing below it.
/// </summary>
public partial class SwayLayer : AmbientLayer
{
    private SpriteSource? source;
    private Vector2 pos;

    /// <inheritdoc />
    protected override AmbientEffect Effect => AmbientEffect.Sway;

    /// <inheritdoc />
    protected override void Configure(JsonObject def)
    {
        source = AmbientContext.Sprite(def.Str("texture"), Vector2.Zero);
        pos = AmbientContext.CutPos(def);
    }

    /// <inheritdoc />
    protected override void ConfigureShader(JsonObject def, ShaderMaterial m)
    {
        if (source is null) return;
        m.SetShaderParameter("tex_size", source.Cell);
        m.SetShaderParameter("amp", def.Num("amp_px", 3f));
        m.SetShaderParameter("freq", def.Num("freq", 0.3f));
        m.SetShaderParameter("wavelength", def.Num("wavelength_px", 220f));
        m.SetShaderParameter("anchor", def.Num("anchor", 1f));
        m.SetShaderParameter("hang", def.Bool("hang"));
        m.SetShaderParameter("flutter", def.Num("flutter_px", 0.6f));
        m.SetShaderParameter("gust", def.Num("gust", 0.35f));
        m.SetShaderParameter("phase", Rng.RandfRange(0, MathF.Tau));
    }

    /// <inheritdoc />
    protected override void Step(float dt) { }

    /// <inheritdoc />
    public override void _Draw()
    {
        if (source is not null) DrawQuad(source, 0, pos, Vector2.One, 0, Colors.White);
    }
}

/// <summary>
/// Type <c>water</c>: ripples and moving glints on a cut-out of the water surface.
/// <code>{ "type": "water", "texture": "S08/water.webp", "pos": [x, y], "amp_px": 1.5, "glint": 0.35 }</code>
/// </summary>
public partial class WaterLayer : AmbientLayer
{
    private SpriteSource? source;
    private Vector2 pos;

    /// <inheritdoc />
    protected override AmbientEffect Effect => AmbientEffect.Water;

    /// <inheritdoc />
    protected override void Configure(JsonObject def)
    {
        source = AmbientContext.Sprite(def.Str("texture"), Vector2.Zero);
        pos = AmbientContext.CutPos(def);
    }

    /// <inheritdoc />
    protected override void ConfigureShader(JsonObject def, ShaderMaterial m)
    {
        if (source is null) return;
        m.SetShaderParameter("tex_size", source.Cell);
        m.SetShaderParameter("amp", def.Num("amp_px", 1.5f));
        m.SetShaderParameter("speed", def.Num("speed", 1f));
        m.SetShaderParameter("glint", def.Num("glint", 0.35f));
        m.SetShaderParameter("glint_color", def.Col("glint_color", new Color(1f, 0.96f, 0.85f)));
    }

    /// <inheritdoc />
    protected override void Step(float dt) { }

    /// <inheritdoc />
    public override void _Draw()
    {
        if (source is not null) DrawQuad(source, 0, pos, Vector2.One, 0, Colors.White);
    }
}

/// <summary>
/// Type <c>sprite_loop</c> (frames of a sheet at a fixed place) and <c>cutout</c> (one static
/// image, e.g. an occluder piece of the background).
/// <code>
/// { "type": "sprite_loop", "sheet": "common/cat_walk_sheet", "pos": [x, y], "scale": 0.4, "fps": 12,
///   "frames": [0, 1, 2], "ping_pong": false, "pause_s": [3, 8], "flip": false }
/// </code>
/// pos is where the sheet pivot lands; pause_s holds the first frame between passes.
/// </summary>
public partial class SpriteLoopLayer : AmbientLayer
{
    private SpriteSource? source;
    private Vector2 pos;
    private float scale = 1;
    private float fps;
    private int[] frames = Array.Empty<int>();
    private bool pingPong;
    private Vector2 pause;
    private float pauseLeft;
    private float clock;
    private bool flip;
    private bool isStatic;

    /// <inheritdoc />
    protected override void Configure(JsonObject def)
    {
        isStatic = LayerType == "cutout";
        source = AmbientContext.Sprite(def.Str("sheet") ?? def.Str("texture"), def.Has("pivot") ? def.Vec("pivot") : isStatic ? Vector2.Zero : null);
        pos = isStatic ? AmbientContext.CutPos(def) : def.Vec("pos");
        scale = def.Num("scale", 1f);
        flip = def.Bool("flip");
        if (source is null) return;
        fps = def.Num("fps", source.Fps);
        var list = def.Ints("frames");
        if (list.Count == 0) for (int i = 0; i < source.Frames; i++) list.Add(i);
        if (def.Bool("ping_pong") && list.Count > 2)
            for (int i = list.Count - 2; i > 0; i--) list.Add(list[i]);
        frames = list.ToArray();
        pingPong = def.Bool("ping_pong");
        pause = def.Range("pause_s", Vector2.Zero);
        clock = Rng.RandfRange(0, frames.Length / Math.Max(0.1f, fps));
    }

    /// <inheritdoc />
    protected override void Step(float dt)
    {
        if (isStatic || frames.Length <= 1) return;
        if (pauseLeft > 0) { pauseLeft -= dt; return; }
        float before = clock;
        clock += dt;
        float length = frames.Length / Math.Max(0.1f, fps);
        if (pause.Y > 0 && (int)(clock / length) != (int)(before / length))
        {
            clock = 0;
            pauseLeft = Pick(pause);
        }
        _ = pingPong;
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        if (source is null) return;
        int frame = frames.Length == 0 ? 0 : frames[(int)(clock * fps) % frames.Length];
        if (pauseLeft > 0 && frames.Length > 0) frame = frames[0];
        DrawQuad(source, frame, pos, new Vector2(flip ? -scale : scale, scale), 0, Colors.White);
    }
}

/// <summary>
/// Type <c>rotor</c>: a clock hand (or fan blade) drawn as a tapered line around a pivot.
/// <code>{ "type": "rotor", "pivot": [1411, 97], "length": 36, "tail": 8, "width": 2, "color": "#a02a1e", "mode": "tick", "period_s": 60 }</code>
/// mode tick: one step per period/60 with a small overshoot (station clocks); sweep: continuous.
/// </summary>
public partial class RotorLayer : AmbientLayer
{
    private Vector2 pivot;
    private float length, tail, width, period;
    private Color color;
    private bool tick;
    private float startAngle;
    private bool dot;

    /// <inheritdoc />
    protected override void Configure(JsonObject def)
    {
        pivot = def.Vec("pivot");
        length = def.Num("length", 30);
        tail = def.Num("tail", 6);
        width = def.Num("width", 2);
        color = def.Col("color", new Color(0.65f, 0.15f, 0.1f));
        period = Math.Max(1, def.Num("period_s", 60));
        tick = def.Str("mode", "tick") == "tick";
        dot = def.Bool("hub", true);
        startAngle = Rng.RandfRange(0, period);
    }

    /// <inheritdoc />
    protected override void Step(float dt) { }

    /// <inheritdoc />
    public override void _Draw()
    {
        float t = Time + startAngle;
        float steps = 60;
        float turns;
        if (tick)
        {
            float stepLen = period / steps;
            float n = MathF.Floor(t / stepLen);
            float f = (t - n * stepLen) / stepLen;
            // quick move in the first 12 % of the step with a small overshoot, then rest
            float move = f < 0.12f ? Smooth(f / 0.12f) * 1.15f : f < 0.2f ? 1.15f - 0.15f * Smooth((f - 0.12f) / 0.08f) : 1f;
            turns = (n + move) / steps;
        }
        else turns = t / period;
        float angle = turns * MathF.Tau - MathF.PI / 2;
        var dir = new Vector2(MathF.Cos(angle), MathF.Sin(angle));
        DrawLine(pivot - dir * tail, pivot + dir * length, color, width, true);
        if (dot) DrawCircle(pivot, width * 1.4f, color);
    }
}
