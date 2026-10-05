using System;
using System.Linq;
using Godot;
using LastBell.Game.World;

namespace LastBell.Game.Living.Actors;

/// <summary>
/// Sprite-sheet look of an actor (hero and NPCs) from <c>res://assets/actors/&lt;ID&gt;/</c>.
/// <list type="bullet">
/// <item>Walk: the cycle is chosen from the movement vector (side cycle mirrored for left; toward /
/// away cycles when the motion is mostly vertical, with hysteresis). Ground speed follows the sheet's
/// <c>stride_px_per_s</c> (the Actor multiplies it by the perspective scale), and the side cycle's
/// playback rate follows the horizontal part of the motion so planted feet never slide.</item>
/// <item>Idle: the facing's idle loop; the hero's built-in blink is kept or skipped per loop at
/// random; still NPC idles blink at random intervals and breathe procedurally; video idles may
/// play an occasional fidget loop (<c>idle_fidget</c>).</item>
/// <item>Talk: lip-flap loop while the line is revealed; it stops on the next rest mouth frame.</item>
/// <item>One-shot actions from <c>actions[].animation</c>: forward, hold, reversed back to idle.</item>
/// <item>Variants: the hero's 2020 face mask where <see cref="ActorStaging"/> says so; NPC window
/// busts (pivot on the sill line) from <c>data/ambient/actors.json</c>.</item>
/// <item>Clip switches cross-fade for 80 ms (video and still cells do not match exactly).</item>
/// </list>
/// Origin = feet centre = sheet pivot (window busts: the node shifts its sprite to the sill line).
/// </summary>
public partial class SpriteActorVisual : Node2D, IActorVisual
{
    private enum Facing { Side, Front, Back }
    private enum ActionPhase { None, Forward, Hold, Reverse }

    private const float CrossFadeSeconds = 0.08f;
    private const float VerticalEnter = 0.76f;
    private const float VerticalExit = 0.66f;
    private const float MaxTalkTail = 0.45f;

    private readonly ActorAnimationSet set;
    private readonly ActorPlacement? placement;
    private readonly RandomNumberGenerator rng = new();
    private Sprite2D sprite = null!;
    private Sprite2D ghost = null!;
    private float ghostLeft;
    private ActorContext? context;

    private bool walking;
    private bool talking;
    private float talkTail;
    private float talkOwed; // talk time that came while a one-shot action played (lines start with the commit)
    private bool verticalWalk;
    private Vector2 direction = Vector2.Right;
    private int side = 1;
    private Facing facing = Facing.Side;
    private float walkRate = 1f;

    private Clip? current;
    private float clipTime;
    private int loopCount;
    private bool blinkThisLoop = true;

    private Clip? action;
    private string actionName = "";
    private ActionPhase phase;
    private float phaseTime;

    private float blinkTimer;
    private float blinkLeft;
    private float fidgetTimer;
    private bool fidgeting;
    private float breathTime;

    /// <summary>Creates the visual for a loaded animation set.</summary>
    public SpriteActorVisual(ActorAnimationSet set, ActorPlacement? placement)
    {
        this.set = set;
        this.placement = placement;
    }

    /// <summary>Parameterless constructor required by Godot for script instancing (unused).</summary>
    public SpriteActorVisual() : this(null!, null) { }

    /// <inheritdoc />
    public Node2D Node => this;

    /// <inheritdoc />
    public bool CastsShadow => placement?.SillY is null; // window busts stand on a sill, not on the floor

    /// <inheritdoc />
    public float HeightPx
    {
        get
        {
            if (placement?.SillY is not { } sill || GetParent() is not Node2D actor) return set.HeightPx * VisualScale;
            float actorScale = Math.Max(0.01f, actor.Scale.X);
            float bust = (current?.Sheet.Pivot.Y ?? set.HeightPx * 0.5f) * AbsoluteScale;
            return (actor.Position.Y - sill + bust) / actorScale;
        }
    }

    /// <inheritdoc />
    public float WalkSpeedPxPerSecond
    {
        get
        {
            float stride = SideStride;
            if (!walking) return stride;
            if (verticalWalk) return stride * ActorStaging.DepthSpeedFactor / Math.Max(0.5f, Math.Abs(direction.Y));
            return Math.Min(stride / Math.Max(0.05f, Math.Abs(direction.X)), stride * 1.15f);
        }
    }

    /// <summary>Name of the clip on screen (QA / debug).</summary>
    public string CurrentClip => current?.Name ?? "";

    private float SideStride => set.Get("walk_right")?.Sheet.StridePxPerSecond is { } s && s > 1 ? s : 272f;

    private float AbsoluteScale => placement?.Scale ?? (GetParent() as Node2D)?.Scale.X ?? 1f;

    private float VisualScale => placement?.Scale is { } s && GetParent() is Node2D actor ? s / Math.Max(0.01f, actor.Scale.X) : 1f;

    /// <inheritdoc />
    public void Bind(ActorContext ctx)
    {
        context = ctx;
        uint seed = 2166136261;
        foreach (char c in ctx.CharacterId + ctx.RoomId) seed = (seed ^ c) * 16777619;
        rng.Seed = seed;
        ghost = new Sprite2D { Name = "CrossFade", Centered = false, Visible = false, RegionEnabled = true };
        sprite = new Sprite2D { Name = "Sprite", Centered = false, RegionEnabled = true };
        AddChild(ghost);
        AddChild(sprite);
        if (placement?.Facing == "left") side = -1;
        blinkTimer = NextInterval(set.Get("blink")?.EverySeconds ?? new Vector2(2.5f, 6f));
        fidgetTimer = NextInterval(set.Get("idle_fidget")?.EverySeconds ?? new Vector2(12f, 25f));
        breathTime = rng.RandfRange(0, 4);
        Switch(PickBaseClip(), crossFade: false);
        clipTime = rng.RandfRange(0, current?.Length ?? 0);
        Apply();
    }

    /// <inheritdoc />
    public void SetLocomotion(bool isWalking, Vector2 dir)
    {
        if (dir.LengthSquared() > 0.0001f) direction = dir.Normalized();
        if (isWalking && !walking && action is not null) action = null; // walking cancels an action
        walking = isWalking;
        if (walking)
        {
            float ay = Math.Abs(direction.Y);
            verticalWalk = set.IsDirectional && (verticalWalk ? ay > VerticalExit : ay > VerticalEnter);
            if (!verticalWalk && Math.Abs(direction.X) > 0.05f) side = Math.Sign(direction.X);
            facing = verticalWalk ? (direction.Y > 0 ? Facing.Front : Facing.Back) : Facing.Side;
            walkRate = verticalWalk ? 1f : Math.Clamp(WalkSpeedPxPerSecond * Math.Abs(direction.X) / SideStride, 0.4f, 1.15f);
        }
        else
        {
            if (placement?.Facing is "left" or "right") { side = placement.Facing == "left" ? -1 : 1; facing = Facing.Side; return; }
            if (set.IsDirectional && Math.Abs(direction.Y) > 0.85f) facing = direction.Y > 0 ? Facing.Front : Facing.Back;
            else
            {
                facing = Facing.Side;
                if (Math.Abs(direction.X) > 0.05f) side = Math.Sign(direction.X);
            }
        }
    }

    /// <inheritdoc />
    public void SetTalking(bool isTalking)
    {
        if (isTalking && !talking) talkTail = 0;
        talking = isTalking;
    }

    /// <inheritdoc />
    public void PlayGesture(string animation)
    {
        if (string.IsNullOrEmpty(animation) || animation == "talk") return;
        Clip? clip = set.IsDirectional
            ? set.Get(animation + "_right") ?? set.Get(animation + "_front") ?? set.Get(animation)
            : set.Get(animation) ?? set.Get("gesture");
        if (clip is null) return;
        if (set.IsDirectional && clip.Name.EndsWith("_front", StringComparison.Ordinal)) facing = Facing.Front;
        else facing = Facing.Side;
        action = clip;
        actionName = animation;
        phase = ActionPhase.Forward;
        phaseTime = 0;
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        if (sprite is null || current is null) return;
        float dt = (float)delta;
        breathTime += dt;
        if (ghostLeft > 0)
        {
            ghostLeft -= dt;
            ghost.Modulate = new Color(1, 1, 1, Math.Clamp(ghostLeft / CrossFadeSeconds, 0, 1));
            if (ghostLeft <= 0) ghost.Visible = false;
        }

        if (talking && action is not null) talkOwed = Math.Min(4f, talkOwed + dt);
        if (action is not null && !walking) StepAction(dt);
        else
        {
            var wanted = PickBaseClip();
            if (wanted != current) Switch(wanted, crossFade: true);
            float rate = current.Name.StartsWith("walk", StringComparison.Ordinal) ? walkRate : 1f;
            float before = clipTime;
            clipTime += dt * rate;
            if (current.Loop && current.Length > 0 && (int)(clipTime / current.Length) != (int)(before / current.Length)) OnLoopWrapped();
            if (!current.Loop && clipTime >= current.Length && fidgeting) { fidgeting = false; Switch(PickBaseClip(), crossFade: true); }
            StepIdleExtras(dt);
        }
        Apply();
    }

    // ------------------------------------------------------------------ state

    private Clip PickBaseClip()
    {
        if (walking && set.IsDirectional)
        {
            var walk = facing switch
            {
                Facing.Front => set.Get("walk_toward"),
                Facing.Back => set.Get("walk_away"),
                _ => set.Get("walk_right"),
            };
            if (walk is not null) return walk;
        }
        if (talking || talkOwed > 0 || (current is not null && IsTalkClip(current) && !AtRestFrame() && talkTail < MaxTalkTail))
        {
            // No talk sheet for the back view: turn side-on (last side) while speaking, as adventure heroes do.
            var talk = set.IsDirectional
                ? facing switch { Facing.Front => set.Get("talk_front"), _ => set.Get("talk_right") }
                : set.Get("talk");
            if (talk is not null) return talk;
        }
        if (fidgeting && set.Get("idle_fidget") is { } fidget) return fidget;
        Clip? idle = set.IsDirectional
            ? facing switch { Facing.Front => set.Get("idle_front"), Facing.Back => set.Get("idle_back"), _ => set.Get("idle_right") }
            : set.Get("idle");
        return idle ?? set.Get("idle_still") ?? set.Get("idle_right") ?? set.Get(set.Names.First())!;
    }

    private static bool IsTalkClip(Clip clip) => clip.Name.StartsWith("talk", StringComparison.Ordinal);

    private bool AtRestFrame()
    {
        if (current is null) return true;
        int cell = CurrentCell();
        var sheet = current.Sheet;
        if (sheet.RestFrames.Count > 0) return sheet.RestFrames.Contains(cell);
        if (sheet.FrameNames.Count > cell && cell >= 0) return sheet.FrameNames[cell] == "idle";
        return true;
    }

    private void Switch(Clip clip, bool crossFade)
    {
        if (crossFade && current is not null && clip.Sheet != current.Sheet && sprite.Texture is not null)
        {
            ghost.Texture = sprite.Texture;
            ghost.RegionRect = sprite.RegionRect;
            ghost.Offset = sprite.Offset;
            ghost.FlipH = sprite.FlipH;
            ghost.Position = sprite.Position;
            ghost.Scale = sprite.Scale;
            ghost.Visible = true;
            ghost.Modulate = Colors.White;
            ghostLeft = CrossFadeSeconds;
        }
        bool wasTalk = current is not null && IsTalkClip(current);
        current = clip;
        clipTime = 0;
        loopCount = 0;
        blinkThisLoop = rng.Randf() < ActorStaging.HeroBlinkChance;
        if (IsTalkClip(clip) && !wasTalk) talkTail = 0;
    }

    private void OnLoopWrapped()
    {
        loopCount++;
        blinkThisLoop = rng.Randf() < ActorStaging.HeroBlinkChance;
        if (!walking && !talking && current is not null && current.Name == "idle" && current.Frames.Length > 1 && fidgetTimer <= 0
            && set.Get("idle_fidget") is not null)
        {
            fidgeting = true;
            fidgetTimer = NextInterval(set.Get("idle_fidget")!.EverySeconds ?? new Vector2(12f, 25f));
            Switch(set.Get("idle_fidget")!, crossFade: false); // fidget cell 0 matches the idle loop boundary
        }
    }

    private void StepIdleExtras(float dt)
    {
        if (current is null) return;
        if (!talking && IsTalkClip(current))
        {
            if (talkOwed > 0) talkOwed = Math.Max(0, talkOwed - dt);
            else talkTail += dt;
        }
        if (walking) talkOwed = 0;
        if (fidgetTimer > 0) fidgetTimer -= dt;
        // Random blinks on still idles (the NPC still sheets have a blink cell).
        if (current.Frames.Length == 1 && current.Name is "idle" or "idle_still" && set.Get("blink") is { } blink)
        {
            if (blinkLeft > 0) blinkLeft -= dt;
            else if ((blinkTimer -= dt) <= 0)
            {
                blinkLeft = Math.Max(0.08f, blink.HoldSeconds);
                blinkTimer = NextInterval(blink.EverySeconds ?? new Vector2(2.5f, 6f));
                // occasional double blink
                if (rng.Randf() < 0.15f) blinkTimer = 0.25f;
            }
        }
        else blinkLeft = 0;
    }

    private void StepAction(float dt)
    {
        if (action is null) return;
        if (current != action) Switch(action, crossFade: true);
        phaseTime += dt;
        float length = action.Frames.Length > 1 ? action.Length : 0f;
        switch (phase)
        {
            case ActionPhase.Forward:
                clipTime = Math.Min(phaseTime, length);
                if (phaseTime >= length) { phase = ActionPhase.Hold; phaseTime = 0; }
                break;
            case ActionPhase.Hold:
                clipTime = length;
                float hold = action.Frames.Length > 1 ? ActorStaging.HoldFor(actionName) : Math.Max(0.2f, action.HoldSeconds);
                if (phaseTime >= hold) { phase = action.Frames.Length > 1 ? ActionPhase.Reverse : ActionPhase.None; phaseTime = 0; }
                break;
            case ActionPhase.Reverse:
                clipTime = Math.Max(0, length - phaseTime);
                if (phaseTime >= length) phase = ActionPhase.None;
                break;
        }
        if (phase == ActionPhase.None)
        {
            action = null;
            Switch(PickBaseClip(), crossFade: true);
        }
    }

    // ------------------------------------------------------------------ drawing

    private int CurrentCell()
    {
        if (current is null) return 0;
        int index = (int)MathF.Floor(clipTime * current.Fps + 0.0001f);
        if (action == current) index = Math.Clamp(index, 0, current.Frames.Length - 1);
        int cell = current.CellAt(index);
        // Random blinking: skip the sheet's built-in blink in some loops (hero idles).
        if (!blinkThisLoop && current.Sheet.BlinkFrames.Contains(cell))
            cell = cell > 0 ? cell - 1 : cell + 1;
        return cell;
    }

    private void Apply()
    {
        if (current is null) return;
        var clip = current;
        int cell = CurrentCell();
        if (blinkLeft > 0 && set.Get("blink") is { } blink && blink.Sheet == clip.Sheet) cell = blink.Frames[0];
        sprite.Texture = clip.Sheet.Texture;
        sprite.RegionRect = clip.Sheet.Region(cell);
        sprite.Offset = -clip.Sheet.Pivot;
        sprite.FlipH = clip.MirrorForLeft && side < 0 && !clip.Name.EndsWith("_front", StringComparison.Ordinal)
                       && !clip.Name.EndsWith("_back", StringComparison.Ordinal) && clip.Name is not ("walk_toward" or "walk_away");
        // Procedural breathing for single-frame idles (stills have no motion of their own).
        float breath = clip.Frames.Length == 1 && !walking ? 1f + 0.005f * MathF.Sin(breathTime * MathF.Tau / 3.6f) : 1f;
        float k = VisualScale;
        sprite.Scale = new Vector2(k, k * breath);
        if (placement is not null && GetParent() is Node2D actor)
        {
            float actorScale = Math.Max(0.01f, actor.Scale.X);
            float y = placement.SillY is { } sill ? (sill - actor.Position.Y) / actorScale : 0f;
            sprite.Position = new Vector2(placement.OffsetX / actorScale, y);
        }
    }

    private float NextInterval(Vector2 range) => rng.RandfRange(range.X, Math.Max(range.X, range.Y));
}
