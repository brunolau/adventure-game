using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using Godot;

namespace LastBell.Game.Living.Ambient;

/// <summary>
/// Type <c>particles</c>: falling leaves, dust motes in a sunbeam, snow, rain, steam. A preset
/// gives the motion model and defaults; every number can be overridden in the data.
/// <code>
/// { "type": "particles", "preset": "leaves", "emit_rect": [x, y, w, h], "rate": 0.4,
///   "textures": ["common/leaf_00.webp", ...], "size": [16, 26], "land_y": [600, 760], "rest_s": [2, 5] }
/// </code>
/// Fields: preset (leaves | dust | snow | rain | steam), emit_rect, emit_points (+ emit_jitter),
/// rate (per second) or count (kept alive), lifetime, size (px of the longer side), speed_y, speed_x
/// (ranges), wind (sideways sway amplitude px), sway_freq, gravity, spin (deg/s), tumble (fake 3D
/// flip), grow (size factor at the end of life), fade_in, fade_out, land_y (leaves rest on the ground
/// there), rest_s, twinkle (dust), color / colors, alpha_range, max.
/// Breath (winter Jasna 2035): <c>pulse_s</c> [min, max] seconds between breaths and <c>pulse_on_s</c> (how long
/// each exhale emits) make the emission come in puffs; <c>follow: "hero"</c> emits at the hero's mouth instead of
/// the emit rect / points (<c>follow: "npc:&lt;hotspot id&gt;"</c>: at that NPC's mouth): <c>follow_offset</c> [x, y] as
/// fractions of the drawn figure height (x toward the side the figure faces, y down from the top of the figure),
/// sizes, jitter and <c>follow_push</c> (px/s forward) scale with the actor's perspective scale; nothing is emitted
/// while the actor is missing or hidden.
/// </summary>
public partial class ParticleLayer : AmbientLayer
{
    private struct Particle
    {
        public Vector2 Pos;
        public Vector2 Vel;
        public float Age;
        public float Life;
        public float Size;
        public float Rot;
        public float Spin;
        public float Phase;
        public float Tumble;
        public int Tex;
        public float Alpha;
        public Color Color;
        public bool Landed;
        public float LandY;
        public float RestLeft;
    }

    private readonly List<Particle> particles = new();
    private readonly List<SpriteSource> textures = new();
    private readonly List<Color> palette = new();
    private string preset = "leaves";
    private Rect2 emitRect;
    private List<Vector2> emitPoints = new();
    private Vector2 emitJitter;
    private float rate;
    private int keepCount;
    private int max;
    private float accumulator;
    private Vector2 life, size, speedX, speedY, spin, alphaRange, landY, rest;
    private float wind, swayFreq, gravity, grow, fadeIn, fadeOut, twinkle;
    private bool tumble, land;
    private bool followActor;
    private string? followNpc;
    private Vector2 followOffset;
    private float followPush;
    private float actorFacing = 1f;
    private float followSide = 1f;
    private float lastActorX = float.NaN;
    private Vector2 pulse;
    private float pulseOn, pulseClock, pulseNext;

    /// <inheritdoc />
    protected override float DefaultPrewarm => preset is "rain" ? 1f : preset is "steam" ? 4f : 12f;

    /// <inheritdoc />
    protected override bool DefaultAdditive => preset is "dust";

    /// <inheritdoc />
    protected override void Configure(JsonObject def)
    {
        preset = def.Str("preset", "leaves")!;
        emitRect = def.Rect("emit_rect") ?? new Rect2(0, -40, 1920, 20);
        emitPoints = def.Points("emit_points");
        emitJitter = def.Vec("emit_jitter", new Vector2(6, 2));
        textures.AddRange(AmbientContext.Sprites(def));
        if (textures.Count == 0)
        {
            string fallback = preset switch { "rain" => "builtin:streak", "steam" => "builtin:puff", _ => "builtin:dot" };
            if (AmbientContext.Sprite(fallback) is { } s) textures.Add(s);
        }
        foreach (var c in def.Strings("colors"))
            if (Color.HtmlIsValid(c)) palette.Add(Color.FromHtml(c));
        if (palette.Count == 0) palette.Add(def.Col("color", preset switch
        {
            "dust" => new Color(1f, 0.93f, 0.75f),
            "steam" => new Color(1f, 1f, 1f),
            "rain" => new Color(0.8f, 0.85f, 0.95f),
            _ => Colors.White,
        }));
        // preset defaults: (life, size, speedX, speedY, wind, gravity, spin)
        switch (preset)
        {
            case "dust":
                Defaults(def, life: new(6, 12), size: new(2, 5), sx: new(-4, 4), sy: new(-3, 3), wind: 6, swayF: 0.15f, grav: 0, spinR: new(0, 0), alpha: new(0.25f, 0.8f));
                fadeIn = def.Num("fade_in", 1.5f); fadeOut = def.Num("fade_out", 2f); twinkle = def.Num("twinkle", 0.6f);
                break;
            case "snow":
                Defaults(def, life: new(8, 14), size: new(3, 7), sx: new(-8, 8), sy: new(35, 70), wind: 14, swayF: 0.4f, grav: 0, spinR: new(0, 0), alpha: new(0.6f, 0.95f));
                fadeIn = def.Num("fade_in", 0.5f); fadeOut = def.Num("fade_out", 1f);
                break;
            case "rain":
                Defaults(def, life: new(1.2f, 1.6f), size: new(28, 46), sx: new(-90, -60), sy: new(900, 1150), wind: 0, swayF: 0, grav: 0, spinR: new(0, 0), alpha: new(0.2f, 0.4f));
                fadeIn = def.Num("fade_in", 0.05f); fadeOut = def.Num("fade_out", 0.1f);
                break;
            case "steam":
                Defaults(def, life: new(2.5f, 4f), size: new(18, 30), sx: new(-3, 3), sy: new(-28, -16), wind: 6, swayF: 0.5f, grav: 0, spinR: new(-20, 20), alpha: new(0.18f, 0.32f));
                fadeIn = def.Num("fade_in", 0.6f); fadeOut = def.Num("fade_out", 1.8f); grow = def.Num("grow", 2.6f);
                break;
            default: // leaves
                Defaults(def, life: new(9, 16), size: new(16, 26), sx: new(8, 30), sy: new(38, 70), wind: 28, swayF: 0.55f, grav: 0, spinR: new(-90, 90), alpha: new(1, 1));
                fadeIn = def.Num("fade_in", 0.6f); fadeOut = def.Num("fade_out", 1.2f);
                tumble = def.Bool("tumble", true);
                break;
        }
        if (preset != "steam") grow = def.Num("grow", 1f);
        land = def.Has("land_y");
        landY = def.Range("land_y", new Vector2(2000, 2000));
        rest = def.Range("rest_s", new Vector2(2, 5));
        rate = def.Num("rate", preset == "dust" ? 0 : 0.4f);
        keepCount = def.Int("count", preset == "dust" ? 30 : 0);
        max = def.Int("max", 120);
        string follow = def.Str("follow") ?? "";
        followNpc = follow.StartsWith("npc:", StringComparison.Ordinal) ? follow[4..] : null;
        followActor = follow == "hero" || followNpc is not null;
        followOffset = def.Vec("follow_offset", new Vector2(0.035f, 0.115f));
        followPush = def.Num("follow_push", 6f);
        pulse = def.Range("pulse_s", Vector2.Zero);
        pulseOn = def.Num("pulse_on_s", 0.5f);
        if (pulse.Y > 0)
        {
            pulseNext = Pick(pulse);
            pulseClock = Rng.RandfRange(0, pulseNext);
        }
    }

    /// <summary>The followed actor's mouth in canvas px and its perspective scale (false when it is missing).</summary>
    private bool ActorMouth(out Vector2 mouth, out float scale)
    {
        mouth = default;
        scale = 1f;
        World.Actor? actor = Context.Room.Hero;
        if (followNpc is not null && !Context.Room.Npcs.TryGetValue(followNpc, out actor)) return false;
        if (actor is null || !GodotObject.IsInstanceValid(actor) || !actor.IsVisibleInTree() || actor.Visual is null) return false;
        var feet = actor.Feet;
        followSide = 1f;
        if (actor.Visual is Actors.SpriteActorVisual sprite)
        {
            actorFacing = sprite.FacingSign;
            followSide = sprite.FacingAlongView ? 0f : 1f;
        }
        else if (!float.IsNaN(lastActorX) && MathF.Abs(feet.X - lastActorX) > 0.5f) actorFacing = MathF.Sign(feet.X - lastActorX);
        lastActorX = feet.X;
        scale = actor.CurrentScale;
        float h = actor.Visual.HeightPx * scale;
        mouth = feet + new Vector2(followSide * actorFacing * followOffset.X * h, -(1f - followOffset.Y) * h);
        return true;
    }

    private void Defaults(JsonObject def, Vector2 life, Vector2 size, Vector2 sx, Vector2 sy, float wind, float swayF, float grav, Vector2 spinR, Vector2 alpha)
    {
        this.life = def.Range("lifetime", life);
        this.size = def.Range("size", size);
        speedX = def.Range("speed_x", sx);
        speedY = def.Range("speed_y", sy);
        this.wind = def.Num("wind", wind);
        swayFreq = def.Num("sway_freq", swayF);
        gravity = def.Num("gravity", grav);
        spin = def.Range("spin", spinR);
        alphaRange = def.Range("alpha_range", alpha);
    }

    /// <inheritdoc />
    protected override void Step(float dt)
    {
        // emission (breath: only during an exhale; hero breath: only while there is a hero)
        bool exhale = true;
        if (pulse.Y > 0)
        {
            pulseClock += dt;
            if (pulseClock >= pulseNext)
            {
                pulseClock -= pulseNext;
                pulseNext = Pick(pulse);
            }
            exhale = pulseClock < pulseOn;
        }
        Vector2 mouth = default;
        float actorScale = 1f;
        if (followActor && !ActorMouth(out mouth, out actorScale)) exhale = false;
        if (exhale && keepCount > 0)
        {
            while (particles.Count < Math.Min(keepCount, max)) Spawn(prewarmAge: true, mouth, actorScale);
        }
        else if (exhale && rate > 0)
        {
            accumulator += dt * rate;
            while (accumulator >= 1f)
            {
                accumulator -= 1f;
                // jitter so leaves do not come at a metronome pace
                if (Rng.Randf() < 0.85f && particles.Count < max) Spawn(prewarmAge: false, mouth, actorScale);
            }
        }
        for (int i = particles.Count - 1; i >= 0; i--)
        {
            var p = particles[i];
            p.Age += dt;
            if (p.Landed)
            {
                p.RestLeft -= dt;
                if (p.RestLeft <= 0) { particles.RemoveAt(i); continue; }
            }
            else
            {
                p.Vel.Y += gravity * dt;
                float sway = wind > 0 ? MathF.Cos(p.Age * swayFreq * MathF.Tau + p.Phase) * wind * swayFreq * MathF.Tau : 0f;
                p.Pos += new Vector2(p.Vel.X + sway, p.Vel.Y) * dt;
                if (preset == "dust")
                {
                    // slow random walk
                    p.Vel += new Vector2(Rng.RandfRange(-6, 6), Rng.RandfRange(-6, 6)) * dt;
                    p.Vel = p.Vel.LimitLength(8);
                }
                p.Rot += p.Spin * dt;
                if (land && p.Pos.Y >= p.LandY)
                {
                    p.Pos.Y = p.LandY;
                    p.Landed = true;
                    p.RestLeft = Pick(rest);
                    // a fallen leaf lies flat-ish: freeze the tumble at a readable width
                    p.Tumble = 0;
                    p.Phase = MathF.PI * 0.15f;
                }
                if (p.Age >= p.Life && !p.Landed) { particles.RemoveAt(i); continue; }
            }
            particles[i] = p;
        }
    }

    private void Spawn(bool prewarmAge, Vector2 mouth = default, float actorScale = 1f)
    {
        Vector2 pos;
        if (followActor)
            pos = mouth + new Vector2(Rng.RandfRange(-emitJitter.X, emitJitter.X), Rng.RandfRange(-emitJitter.Y, emitJitter.Y)) * actorScale;
        else if (emitPoints.Count > 0)
        {
            var basePoint = emitPoints[Rng.RandiRange(0, emitPoints.Count - 1)];
            pos = basePoint + new Vector2(Rng.RandfRange(-emitJitter.X, emitJitter.X), Rng.RandfRange(-emitJitter.Y, emitJitter.Y));
        }
        else pos = emitRect.Position + new Vector2(Rng.Randf() * emitRect.Size.X, Rng.Randf() * emitRect.Size.Y);
        var p = new Particle
        {
            Pos = pos,
            Vel = new Vector2(Pick(speedX), Pick(speedY)),
            Life = Pick(life),
            Size = Pick(size),
            Rot = Rng.RandfRange(0, MathF.Tau),
            Spin = Mathf.DegToRad(Pick(spin)),
            Phase = Rng.RandfRange(0, MathF.Tau),
            Tumble = tumble ? Rng.RandfRange(1.2f, 3.2f) : 0,
            Tex = Rng.RandiRange(0, textures.Count - 1),
            Alpha = Pick(alphaRange),
            Color = palette[Rng.RandiRange(0, palette.Count - 1)],
            LandY = Pick(landY),
        };
        if (followActor)
        {
            p.Size *= actorScale;
            p.Vel = p.Vel * actorScale + new Vector2(followSide * actorFacing * followPush * actorScale, 0);
        }
        if (prewarmAge) p.Age = Rng.RandfRange(0, p.Life * 0.8f);
        particles.Add(p);
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        foreach (var p in particles)
        {
            var tex = textures[p.Tex];
            float t = p.Age / Math.Max(0.01f, p.Life);
            float a = p.Alpha;
            if (fadeIn > 0) a *= Smooth(p.Age / fadeIn);
            if (p.Landed) a *= Smooth(p.RestLeft / Math.Max(0.01f, fadeOut));
            else if (fadeOut > 0) a *= Smooth((p.Life - p.Age) / fadeOut);
            if (twinkle > 0) a *= 1 - twinkle * 0.5f * (1 + MathF.Sin(p.Age * 2.3f + p.Phase * 3));
            if (a <= 0.003f) continue;
            float longest = Math.Max(tex.Cell.X, tex.Cell.Y);
            float s = p.Size / longest * (1 + (grow - 1) * t);
            float sx = s;
            if (p.Tumble > 0) sx *= 0.25f + 0.75f * MathF.Abs(MathF.Cos(p.Age * p.Tumble + p.Phase));
            float rot = p.Rot;
            if (preset == "rain") rot = MathF.Atan2(-p.Vel.X, p.Vel.Y);
            var color = new Color(p.Color.R, p.Color.G, p.Color.B, p.Color.A * a);
            DrawQuad(tex, 0, p.Pos, new Vector2(sx, s), rot, color);
        }
    }
}
