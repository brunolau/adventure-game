using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using Godot;

namespace LastBell.Game.Living.Ambient;

/// <summary>
/// Type <c>critters</c>: ground birds (pigeons) that stand, peck, look around and take small steps
/// on a strip of ground, take off when the hero comes near, and fly back in after a while.
/// <code>
/// { "type": "critters", "sheet": "common/pigeon_sheet", "count": 2, "ground": [[x0, y], [x1, y]],
///   "scale": 0.16, "flee_radius": 320, "return_s": [10, 20], "exit": [[-100, 120], [2020, 80]] }
/// </code>
/// The sheet needs frame names stand, peck, look, walk and fly_0..fly_3. ground is a segment the
/// birds stay on (feet points).
/// </summary>
public partial class CritterLayer : AmbientLayer
{
    private enum Mode { Stand, Peck, Look, Walk, FlyAway, Away, FlyIn }

    private sealed class Bird
    {
        public Vector2 Pos;
        public Vector2 Target;
        public Mode Mode;
        public float Left;
        public bool FacesLeft;
        public float Clock;
        public Vector2 Velocity;
        public int Pecks;
    }

    private SpriteSource? source;
    private int stand, peck, look, walk;
    private int[] fly = Array.Empty<int>();
    private Vector2 groundA, groundB;
    private float scale;
    private float fleeRadius;
    private Vector2 returnS;
    private List<Vector2> exits = new();
    private readonly List<Bird> birds = new();

    /// <inheritdoc />
    protected override float DefaultPrewarm => 3f;

    /// <inheritdoc />
    protected override void Configure(JsonObject def)
    {
        source = AmbientContext.Sprite(def.Str("sheet"));
        if (source is null) return;
        stand = First("stand", 0);
        peck = First("peck", stand);
        look = First("look", stand);
        walk = First("walk", stand);
        fly = source.Named("fly");
        if (fly.Length == 0) fly = new[] { stand };
        var ground = def.Points("ground");
        groundA = ground.Count > 0 ? ground[0] : new Vector2(800, 700);
        groundB = ground.Count > 1 ? ground[1] : groundA + new Vector2(200, 0);
        scale = def.Num("scale", 0.16f);
        fleeRadius = def.Num("flee_radius", 300);
        returnS = def.Range("return_s", new Vector2(10, 22));
        exits = def.Points("exit");
        if (exits.Count == 0) exits.AddRange(new[] { new Vector2(-120, 80), new Vector2(2040, 60) });
        int count = Math.Max(1, def.Int("count", 2));
        for (int i = 0; i < count; i++)
        {
            var b = new Bird { Pos = OnGround(Rng.Randf()), FacesLeft = Rng.Randf() < 0.5f };
            NextGroundAction(b);
            birds.Add(b);
        }
    }

    private int First(string name, int fallback) => source!.Named(name) is { Length: > 0 } a ? a[0] : fallback;

    private Vector2 OnGround(float f) => groundA.Lerp(groundB, Math.Clamp(f, 0, 1));

    private void NextGroundAction(Bird b)
    {
        float r = Rng.Randf();
        if (r < 0.35f) { b.Mode = Mode.Peck; b.Pecks = Rng.RandiRange(2, 5); b.Left = 0.22f; }
        else if (r < 0.55f) { b.Mode = Mode.Look; b.Left = Rng.RandfRange(0.8f, 2.2f); if (Rng.Randf() < 0.4f) b.FacesLeft = !b.FacesLeft; }
        else if (r < 0.8f)
        {
            b.Mode = Mode.Walk;
            float along = (b.Pos - groundA).Dot((groundB - groundA).Normalized()) / Math.Max(1, groundA.DistanceTo(groundB));
            float step = Rng.RandfRange(0.04f, 0.12f) * (Rng.Randf() < 0.5f ? -1 : 1);
            b.Target = OnGround(along + step);
            b.FacesLeft = b.Target.X < b.Pos.X;
            b.Left = 3;
        }
        else { b.Mode = Mode.Stand; b.Left = Rng.RandfRange(0.6f, 2f); }
    }

    /// <inheritdoc />
    protected override void Step(float dt)
    {
        if (source is null) return;
        var hero = Context.HeroFeet;
        foreach (var b in birds)
        {
            b.Clock += dt;
            switch (b.Mode)
            {
                case Mode.FlyAway:
                case Mode.FlyIn:
                    b.Pos += b.Velocity * dt;
                    if (b.Mode == Mode.FlyIn && b.Pos.DistanceTo(b.Target) < b.Velocity.Length() * dt * 1.5f + 2)
                    {
                        b.Pos = b.Target;
                        b.Mode = Mode.Stand;
                        b.Left = Rng.RandfRange(0.8f, 1.6f);
                    }
                    else if (b.Mode == Mode.FlyAway && (b.Pos.X < -150 || b.Pos.X > 2070 || b.Pos.Y < -150))
                    {
                        b.Mode = Mode.Away;
                        b.Left = Pick(returnS);
                    }
                    continue;
                case Mode.Away:
                    b.Left -= dt;
                    if (b.Left <= 0 && hero.DistanceTo(groundA.Lerp(groundB, 0.5f)) > fleeRadius * 1.2f)
                    {
                        b.Target = OnGround(Rng.Randf());
                        b.Pos = exits[Rng.RandiRange(0, exits.Count - 1)];
                        b.Velocity = (b.Target - b.Pos).Normalized() * 330f;
                        b.FacesLeft = b.Velocity.X < 0;
                        b.Mode = Mode.FlyIn;
                    }
                    continue;
            }
            if (hero.DistanceTo(b.Pos) < fleeRadius)
            {
                var exit = exits[0];
                foreach (var e in exits)
                    if ((e - hero).Length() > (exit - hero).Length()) exit = e;
                b.Velocity = (exit - b.Pos).Normalized() * Rng.RandfRange(320, 420);
                b.FacesLeft = b.Velocity.X < 0;
                b.Mode = Mode.FlyAway;
                b.Clock = Rng.RandfRange(0, 1);
                continue;
            }
            b.Left -= dt;
            if (b.Mode == Mode.Walk)
            {
                var to = b.Target - b.Pos;
                float stepLen = 34f * dt;
                if (to.Length() <= stepLen) { b.Pos = b.Target; b.Left = 0; }
                else b.Pos += to.Normalized() * stepLen;
            }
            if (b.Left <= 0)
            {
                if (b.Mode == Mode.Peck && --b.Pecks > 0) b.Left = 0.22f;
                else NextGroundAction(b);
            }
        }
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        if (source is null) return;
        foreach (var b in birds)
        {
            int frame = b.Mode switch
            {
                Mode.Away => -1,
                Mode.FlyAway or Mode.FlyIn => fly[(int)(b.Clock * 12f) % fly.Length],
                Mode.Peck => b.Left > 0.11f ? peck : stand,
                Mode.Look => look,
                Mode.Walk => ((int)(b.Clock * 6f) % 2 == 0) ? walk : stand,
                _ => stand,
            };
            if (frame < 0) continue;
            // the sheet faces right
            DrawQuad(source, frame, b.Pos, new Vector2(b.FacesLeft ? -scale : scale, scale), 0, Colors.White);
        }
    }
}
