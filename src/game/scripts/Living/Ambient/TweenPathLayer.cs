using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using Godot;

namespace LastBell.Game.Living.Ambient;

/// <summary>
/// Type <c>tween_path</c>: something crossing the scene now and then along a polyline: birds, a car
/// or bus in the distance, a cat on a fence, a shadow behind a curtain.
/// <code>
/// { "type": "tween_path", "sheet": "common/pigeon_sheet", "frames": "fly", "fps": 10,
///   "path": [[-60, 80], [700, 40], [1980, 70]], "speed_px_s": 220, "every_s": [12, 30],
///   "direction": "random", "faces": "right", "scale": 0.18, "flock": 3, "flock_spread": [90, 40],
///   "bob_px": 4, "bob_hz": 1.2, "fade_px": 0, "start_s": [2, 6] }
/// </code>
/// frames: a list of cell indices or a frame-name prefix ("fly" → fly_0..fly_n). scale may be
/// [start, end] for perspective. Masks / clip rects (base fields) hide it behind hedges or windows.
/// </summary>
public partial class TweenPathLayer : AmbientLayer
{
    private struct Member
    {
        public Vector2 Offset;
        public float Phase;
        public float Lag;
        public float ScaleJitter;
    }

    private SpriteSource? source;
    private int[] frames = { 0 };
    private float fps;
    private readonly List<Vector2> path = new();
    private readonly List<float> cumulative = new();
    private float totalLength;
    private float speed;
    private Vector2 every;
    private string direction = "forward";
    private bool facesRight = true;
    private Vector2 scaleRange;
    private Vector2 speedJitter;
    private float bobPx, bobHz, fadePx;
    private Vector2 yJitter;
    private int flock;
    private Vector2 flockSpread;
    private readonly List<Member> members = new();

    private bool running;
    private float wait;
    private float distance;
    private bool reverse;
    private float runSpeed;
    private float runY;
    private int runs;

    /// <inheritdoc />
    protected override ReducedMotionMode DefaultReducedMode => ReducedMotionMode.Hide;

    /// <inheritdoc />
    protected override void Configure(JsonObject def)
    {
        source = AmbientContext.Sprite(def.Str("sheet") ?? def.Str("texture"), def.Has("pivot") ? def.Vec("pivot") : null);
        path.AddRange(def.Points("path"));
        if (path.Count < 2 || source is null) return;
        cumulative.Add(0);
        for (int i = 1; i < path.Count; i++) cumulative.Add(cumulative[i - 1] + path[i].DistanceTo(path[i - 1]));
        totalLength = cumulative[^1];
        fps = def.Num("fps", source.Fps);
        if (def.Arr("frames") is not null) frames = def.Ints("frames").ToArray();
        else if (def.Str("frames") is { } prefix && source.Named(prefix) is { Length: > 0 } named) frames = named;
        else
        {
            frames = new int[source.Frames];
            for (int i = 0; i < frames.Length; i++) frames[i] = i;
        }
        if (frames.Length == 0) frames = new[] { 0 };
        float duration = def.Num("duration_s", 0);
        speed = duration > 0 ? totalLength / duration : def.Num("speed_px_s", 120);
        speedJitter = def.Range("speed_jitter", new Vector2(0.9f, 1.1f));
        every = def.Range("every_s", new Vector2(15, 30));
        direction = def.Str("direction", "forward")!;
        facesRight = def.Str("faces", "right") != "left";
        scaleRange = def.Range("scale", new Vector2(1, 1));
        bobPx = def.Num("bob_px", 0);
        bobHz = def.Num("bob_hz", 1);
        fadePx = def.Num("fade_px", 0);
        yJitter = def.Range("y_jitter", Vector2.Zero);
        flock = Math.Max(1, def.Int("flock", 1));
        flockSpread = def.Vec("flock_spread", new Vector2(80, 30));
        wait = Pick(def.Range("start_s", new Vector2(1, Math.Max(1, every.Y * 0.5f))));
    }

    /// <inheritdoc />
    protected override void Step(float dt)
    {
        if (source is null || totalLength <= 0) return;
        if (!running)
        {
            wait -= dt;
            if (wait <= 0) StartRun();
            return;
        }
        distance += runSpeed * dt;
        float maxLag = 0;
        foreach (var m in members) maxLag = Math.Max(maxLag, m.Lag);
        if (distance > totalLength + maxLag)
        {
            running = false;
            wait = Pick(every);
        }
    }

    private void StartRun()
    {
        running = true;
        distance = 0;
        runs++;
        reverse = direction switch
        {
            "reverse" => true,
            "random" => Rng.Randf() < 0.5f,
            "alternate" => runs % 2 == 0,
            _ => false,
        };
        runSpeed = speed * Pick(speedJitter);
        runY = Pick(yJitter);
        members.Clear();
        for (int i = 0; i < flock; i++)
        {
            members.Add(new Member
            {
                Offset = i == 0 ? Vector2.Zero : new Vector2(Rng.RandfRange(-flockSpread.X, flockSpread.X), Rng.RandfRange(-flockSpread.Y, flockSpread.Y)),
                Phase = Rng.RandfRange(0, 10),
                Lag = i == 0 ? 0 : Rng.RandfRange(10, flockSpread.X * 1.5f),
                ScaleJitter = i == 0 ? 1 : Rng.RandfRange(0.85f, 1.1f),
            });
        }
    }

    private (Vector2 pos, Vector2 dir, float t) Sample(float d)
    {
        d = Math.Clamp(d, 0, totalLength);
        if (reverse) d = totalLength - d;
        int i = 1;
        while (i < cumulative.Count - 1 && cumulative[i] < d) i++;
        float seg = Math.Max(0.001f, cumulative[i] - cumulative[i - 1]);
        float f = (d - cumulative[i - 1]) / seg;
        var dir = (path[i] - path[i - 1]).Normalized();
        return (path[i - 1].Lerp(path[i], f), reverse ? -dir : dir, d / totalLength);
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        if (!running || source is null) return;
        foreach (var m in members)
        {
            float d = distance - m.Lag;
            if (d < 0 || d > totalLength) continue;
            var (pos, dir, t) = Sample(d);
            float s = Mathf.Lerp(scaleRange.X, scaleRange.Y, t) * m.ScaleJitter;
            float time = Time + m.Phase;
            pos += m.Offset * s / Math.Max(0.01f, scaleRange.X) + new Vector2(0, runY);
            if (bobPx > 0) pos.Y += MathF.Sin(time * bobHz * MathF.Tau) * bobPx * s / Math.Max(0.01f, scaleRange.X);
            int frame = frames[(int)(time * fps) % frames.Length];
            bool movingRight = dir.X >= 0;
            float sx = movingRight == facesRight ? s : -s;
            float a = 1;
            if (fadePx > 0) a = Smooth(Math.Min(d, totalLength - d) / fadePx);
            DrawQuad(source, frame, pos, new Vector2(sx, s), 0, new Color(1, 1, 1, a));
        }
    }
}
