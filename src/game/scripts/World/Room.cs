using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.Text;
using LastBell.Core.Views;
using LastBell.Game.Hooks;
using LastBell.Game.Runtime;

namespace LastBell.Game.World;

/// <summary>Kind of an interactive target in a room.</summary>
public enum TargetKind
{
    /// <summary>NPC hotspot.</summary>
    Npc,
    /// <summary>Prop hotspot (progress or atmospheric).</summary>
    Prop,
    /// <summary>Exit zone.</summary>
    Exit,
}

/// <summary>Geometry and names of one visible hotspot or exit, with art overrides applied.</summary>
/// <param name="Id">Hotspot or exit id.</param>
/// <param name="Kind">Kind.</param>
/// <param name="Name">Name / label.</param>
/// <param name="Rect">Hit rect (game.json rect plus visual nudge).</param>
/// <param name="InteractionPoint">Walk target (game.json, never nudged).</param>
/// <param name="LabelAnchor">Label anchor (override or game.json; exits: above the rect).</param>
/// <param name="IsAtmospheric">Look-only prop.</param>
/// <param name="ValidForSelectedItem">The selected item has an executable rule on it.</param>
/// <param name="Unlocked">Exits: gate open.</param>
public sealed record TargetInfo(string Id, TargetKind Kind, TextRef Name, Rect2 Rect, Vector2 InteractionPoint, Vector2 LabelAnchor,
    bool IsAtmospheric, bool ValidForSelectedItem, bool Unlocked)
{
    /// <summary>The Core hit for this target.</summary>
    public Hit ToHit() => Kind == TargetKind.Exit ? new Hit.Exit(Id) : new Hit.Hotspot(Id);
}

/// <summary>The painted time-node clock of an anchor node (ISSUES PT-F10).</summary>
/// <param name="Rect">Hit rect.</param>
/// <param name="InteractionPoint">Where the hero walks before the era chooser opens.</param>
/// <param name="HotspotId">The game.json hotspot it doubles as, or null (own presentation rect).</param>
public sealed record TimeNodeInfo(Rect2 Rect, Vector2 InteractionPoint, string? HotspotId);

/// <summary>
/// The one generic room scene (scenes/room/Room.tscn). <see cref="Build"/> creates any room from
/// Core's <see cref="RoomView"/>, with layers in the order of <c>rooms[].layer_order</c>:
/// background (painted art or the dev blockout), state variant layers, ambient host, actor shadows,
/// y-sorted actors, foreground mask, ambient front, hotspot labels and the HUD marker (the HUD
/// itself is the persistent HudHost in Main). The room never decides rules: it renders the view
/// and answers hit tests; <see cref="Refresh"/> applies a new view after a state change.
/// </summary>
public partial class Room : Node2D
{
    /// <summary>Path of the generic room scene.</summary>
    public const string ScenePath = "res://scenes/room/Room.tscn";

    /// <summary>Base canvas size of all rooms.</summary>
    public static readonly Vector2 CanvasSize = new(1920, 1080);

    private readonly Dictionary<string, Actor> npcs = new(StringComparer.Ordinal);
    private readonly List<Actor> guests = new();
    private readonly Dictionary<string, TargetInfo> targets = new(StringComparer.Ordinal);
    private readonly List<string> hitOrder = new();
    private readonly Dictionary<string, Node2D> layers = new(StringComparer.Ordinal);
    private DevBlockout? blockout;
    private DevBlockout? devOverlay;
    private bool devOverlayVisible;
    private string? variantSignature;
    private Texture2D? backgroundTexture;
    private Node2D? npcsBack;
    private Node2D? npcsFront;

    /// <summary>Room id.</summary>
    public string RoomId { get; private set; } = "";

    /// <summary>The view the room currently shows.</summary>
    public RoomView View { get; private set; } = null!;

    /// <summary>Room definition.</summary>
    public RoomDef Definition { get; private set; } = null!;

    /// <summary>Walkable area and pathfinding.</summary>
    public WalkArea Walk { get; private set; } = null!;

    /// <summary>Perspective scale by feet y.</summary>
    public Perspective Perspective { get; private set; }

    /// <summary>Visual overrides of this room.</summary>
    public RoomOverride Overrides { get; private set; } = new();

    /// <summary>Natural re-blocking applied to this room (null = game.json template geometry; see <see cref="RoomBlocking"/>).</summary>
    public RoomBlocking? Blocking { get; private set; }

    /// <summary>The hero actor.</summary>
    public Actor Hero { get; private set; } = null!;

    /// <summary>NPC actors by hotspot id.</summary>
    public IReadOnlyDictionary<string, Actor> Npcs => npcs;

    /// <summary>Guest speakers walking in or standing in the room for one action (World/GuestStage.cs; never Core NPCs).</summary>
    public IReadOnlyList<Actor> Guests => guests;

    /// <summary>The painted time-node clock while Core lists portal targets here, else null (ISSUES PT-F10).</summary>
    public TimeNodeInfo? TimeNode { get; private set; }

    /// <summary>Ambient host (living-world agent fills it).</summary>
    public AmbientHost Ambient { get; private set; } = null!;

    /// <summary>The y-sorted actor layer.</summary>
    public Node2D ActorsLayer { get; private set; } = null!;

    /// <summary>The hotspot label / outline layer.</summary>
    public HotspotLabelLayer Labels { get; private set; } = null!;

    /// <summary>True when painted background art exists for the room.</summary>
    public bool HasBackgroundArt { get; private set; }

    /// <summary>All visible targets (hotspots, then exits) in data order.</summary>
    public IEnumerable<TargetInfo> Targets => targets.Values;

    /// <summary>Named layer node (layer_order names plus "ambient" and "ambient_front").</summary>
    public Node2D? Layer(string name) => layers.TryGetValue(name, out var n) ? n : null;

    /// <summary>Instantiates the generic room scene.</summary>
    public static Room Instantiate() => GD.Load<PackedScene>(ScenePath).Instantiate<Room>();

    /// <summary>Shows or hides the dev overlay (rects, walk polygon) above painted art (F3 / --dev).</summary>
    public bool DevOverlayVisible
    {
        get => devOverlayVisible;
        set
        {
            devOverlayVisible = value;
            if (devOverlay is not null) devOverlay.Visible = value;
        }
    }

    /// <summary>
    /// Builds the room. <paramref name="arrivedFrom"/> places the hero at the exit leading back to
    /// that room (else the room spawn).
    /// </summary>
    public void Build(GameContent content, RoomView view, ArtOverrides art, string? arrivedFrom)
    {
        RoomId = view.RoomId;
        Name = "Room_" + RoomId;
        View = view;
        Definition = content.GetRoom(RoomId);
        Blocking = RoomBlocking.For(RoomId);
        Overrides = Blocking?.ToOverride() ?? art.For(RoomId);
        Walk = new WalkArea(Blocking?.WalkPolygon ?? view.WalkPolygon);
        var band = Overrides.WalkBand ?? new Vector2(Walk.Top, Walk.Bottom);
        var scale = Overrides.ActorScale ?? art.DefaultActorScale;
        Perspective = new Perspective(band.X, band.Y, scale.X, scale.Y);

        var order = view.LayerOrder.Count > 0 ? view.LayerOrder : DefaultLayerOrder;
        foreach (var layerName in order)
        {
            var node = CreateLayer(layerName);
            node.Name = layerName;
            layers[layerName] = node;
            AddChild(node);
            if (layerName == "prop_state_variants") AddAmbientHost();
            if (layerName == "foreground_mask") AddAmbientFront();
        }
        // Layers the data did not list still exist so extensions can rely on them.
        if (!layers.ContainsKey("prop_state_variants")) AddAmbientHost();
        if (!layers.ContainsKey("foreground_mask")) AddAmbientFront();
        if (ActorsLayer is null)
        {
            ActorsLayer = new Node2D { Name = "npcs_and_adam_sorted_by_feet_y", YSortEnabled = true };
            AddChild(ActorsLayer);
        }
        Ambient.Actors = ActorsLayer;
        if (Blocking is not null) AddNaturalStaging(Blocking);
        if (Labels is null)
        {
            Labels = new HotspotLabelLayer { Name = "hotspot_labels" };
            AddChild(Labels);
        }

        devOverlay = new DevBlockout { Name = "DevOverlay", OverlayOnly = true, Visible = devOverlayVisible };
        AddChild(devOverlay);

        Hero = new Actor();
        ActorsLayer.AddChild(Hero);
        Hero.Setup(new ActorContext(GameRuntime.HeroId, true, RoomId, view.Era, null, null), Perspective, HeroSpawn(arrivedFrom));
        Hero.WalkingChanged += walking => WorldHooks.RaiseHeroWalking(Hero, walking);

        ApplyView(view, content);
        ActorVisualRegistry.Changed += OnVisualFactoriesChanged;
    }

    /// <inheritdoc />
    public override void _ExitTree() => ActorVisualRegistry.Changed -= OnVisualFactoriesChanged;

    /// <summary>Applies a new view of the same room after a state change.</summary>
    public void Refresh(GameContent content, RoomView view)
    {
        View = view;
        ApplyView(view, content);
        WorldHooks.RaiseRoomRefreshed(this);
    }

    /// <summary>Target info by hotspot/exit id (visible targets only).</summary>
    public bool TryGetTarget(string id, out TargetInfo info) => targets.TryGetValue(id, out info!);

    /// <summary>
    /// Hit test at a canvas point: NPC rects first, then props (later data entries on top), then
    /// exits, then the walk polygon (floor), else empty background.
    /// </summary>
    public Hit HitTest(Vector2 point)
    {
        foreach (var id in hitOrder)
            if (targets[id].Rect.HasPoint(point)) return targets[id].ToHit();
        return Walk.Contains(point) ? new Hit.Floor(point.X, point.Y) : new Hit.Empty();
    }

    /// <summary>Gap in px between an NPC's hotspot rect and the hero's feet when he stands beside the NPC.</summary>
    public const float NpcApproachGap = 95f;

    /// <summary>
    /// Where the hero walks to for a target. Props and exits: the game.json interaction point.
    /// NPCs: every interaction point in the data sits straight below the NPC, so a hero standing
    /// there would hide the person he talks to (ISSUES LIVING-02). The hero stands beside the NPC
    /// instead, on the side he comes from (the other side if that is not walkable), at the
    /// interaction point's depth. Presentation only: Core never reads positions, and the action is
    /// still re-resolved on arrival.
    /// </summary>
    public Vector2 ApproachPoint(TargetInfo target, Vector2 heroFeet)
    {
        var point = target.InteractionPoint;
        if (target.Kind != TargetKind.Npc) return point;
        var rect = target.Rect;
        // A child NPC gets a wider gap (blocking "approach_gap"), so show_item does not reach into the face (PT-S24).
        float gap = Blocking is not null && Blocking.Npcs.TryGetValue(target.Id, out var staged) && staged.ApproachGap is { } g ? g : NpcApproachGap;
        if (point.X < rect.Position.X - gap * 0.5f || point.X > rect.End.X + gap * 0.5f) return point; // already beside
        var left = new Vector2(rect.Position.X - gap, point.Y);
        var right = new Vector2(rect.End.X + gap, point.Y);
        bool preferLeft = heroFeet.X < rect.GetCenter().X;
        foreach (var candidate in preferLeft ? new[] { left, right } : new[] { right, left })
            if (Walk.Contains(candidate)) return candidate;
        return point;
    }

    /// <summary>The actor speaking as <paramref name="characterId"/> (hero or a present NPC), or null.</summary>
    public Actor? FindActor(string characterId)
    {
        if (characterId == Hero.CharacterId) return Hero;
        return npcs.Values.FirstOrDefault(a => a.CharacterId == characterId) ??
               guests.FirstOrDefault(a => a.CharacterId == characterId && IsInstanceValid(a) && !a.IsQueuedForDeletion());
    }

    /// <summary>The permanent NPC actor of a character in this room (Core's view), or null.</summary>
    public Actor? FindNpc(string characterId) => npcs.Values.FirstOrDefault(a => a.CharacterId == characterId);

    /// <summary>Adds a guest speaker actor (y-sorted with the hero) at <paramref name="feet"/>.</summary>
    public Actor AddGuest(string characterId, Vector2 feet)
    {
        var actor = new Actor();
        ActorsLayer.AddChild(actor);
        actor.Setup(new ActorContext(characterId, false, RoomId, View.Era, GuestStage.HotspotPrefix + characterId, null), Perspective, feet);
        actor.Name = "Guest_" + characterId;
        guests.Add(actor);
        return actor;
    }

    /// <summary>Removes and frees a guest actor.</summary>
    public void RemoveGuest(Actor actor)
    {
        guests.Remove(actor);
        if (IsInstanceValid(actor)) actor.QueueFree();
    }

    // ------------------------------------------------------------------ building blocks

    private static readonly string[] DefaultLayerOrder =
    {
        "background", "prop_state_variants", "npc_shadows", "npcs_and_adam_sorted_by_feet_y", "foreground_mask", "hotspot_labels", "hud",
    };

    private Node2D CreateLayer(string layerName)
    {
        switch (layerName)
        {
            case "background":
                return CreateBackground();
            case "npc_shadows":
                return new ShadowLayer { Room = this };
            case "npcs_and_adam_sorted_by_feet_y":
                ActorsLayer = new Node2D { YSortEnabled = true };
                return ActorsLayer;
            case "foreground_mask":
                return CreateForeground();
            case "hotspot_labels":
                Labels = new HotspotLabelLayer();
                return Labels;
            case "prop_state_variants":
            case "hud":
                return new Node2D();
            default:
                GD.PushWarning($"Room {RoomId}: unknown layer '{layerName}' in layer_order (empty layer created)");
                return new Node2D();
        }
    }

    private Node2D CreateBackground()
    {
        var root = new Node2D();
        string asset = Blocking?.Background ?? View.BackgroundAsset;
        string path = "res://assets/" + asset;
        if (!string.IsNullOrEmpty(asset) && ResourceLoader.Exists(path) && GD.Load<Texture2D>(path) is { } texture)
        {
            HasBackgroundArt = true;
            backgroundTexture = texture;
            root.AddChild(FitSprite(texture, "Art"));
        }
        else
        {
            blockout = new DevBlockout { Name = "DevBlockout" };
            root.AddChild(blockout);
        }
        return root;
    }

    private Node2D CreateForeground()
    {
        var root = new Node2D();
        string asset = Overrides.ForegroundMask ?? $"fg/{View.RoomId}.webp";
        string path = "res://assets/" + asset;
        if (ResourceLoader.Exists(path) && GD.Load<Texture2D>(path) is { } texture) root.AddChild(FitSprite(texture, "Mask"));
        return root;
    }

    /// <summary>
    /// Natural blocking extras around the y-sorted actor layer: the occluders (polygons of the painting, y-sorted
    /// with the actors at their baseline) and, only when an NPC asks for it, the fixed-depth NPC layers right
    /// below ("npcs_back") and above ("npcs_front") the actor layer (both still below the foreground mask).
    /// </summary>
    private void AddNaturalStaging(RoomBlocking blocking)
    {
        foreach (var occluder in blocking.Occluders)
        {
            var texture = backgroundTexture;
            if (occluder.Texture is { } asset)
            {
                string path = "res://assets/" + asset;
                texture = ResourceLoader.Exists(path) ? GD.Load<Texture2D>(path) : null;
                if (texture is null) GD.PushWarning($"Room {RoomId}: occluder texture {asset} not found");
            }
            if (texture is null) continue; // blockout room: nothing to cut
            var size = texture.GetSize();
            var sx = size.X / CanvasSize.X;
            var sy = size.Y / CanvasSize.Y;
            var node = new Polygon2D
            {
                Name = "Occluder_" + occluder.Id,
                Position = new Vector2(0, occluder.BaselineY), // y-sort key; the polygon stays in canvas coordinates
                Texture = texture,
                Polygon = occluder.Polygon.Select(p => new Vector2(p.X, p.Y - occluder.BaselineY)).ToArray(),
                UV = occluder.Polygon.Select(p => new Vector2(p.X * sx, p.Y * sy)).ToArray(),
            };
            ActorsLayer.AddChild(node);
        }
        bool back = blocking.Npcs.Values.Any(n => n.Depth == NpcDepth.Back);
        bool front = blocking.Npcs.Values.Any(n => n.Depth == NpcDepth.Front);
        if (!back && !front) return;
        var parent = ActorsLayer.GetParent();
        if (back)
        {
            npcsBack = new Node2D { Name = "npcs_back" };
            parent.AddChild(npcsBack);
            parent.MoveChild(npcsBack, ActorsLayer.GetIndex());
        }
        if (front)
        {
            npcsFront = new Node2D { Name = "npcs_front" };
            parent.AddChild(npcsFront);
            parent.MoveChild(npcsFront, ActorsLayer.GetIndex() + 1);
        }
    }

    /// <summary>The hero and every NPC actor, wherever their depth layer is.</summary>
    public IEnumerable<Actor> AllActors => npcs.Values.Prepend(Hero).Concat(guests.Where(g => IsInstanceValid(g)));

    private void AddAmbientHost()
    {
        Ambient = new AmbientHost { Name = "AmbientHost", RoomId = View.RoomId, Era = View.Era, Room = this };
        // A natural blocking has its own painting: the template's ambient layers are cut from the old one.
        if (Blocking is not null) Ambient.DataPathOverride = Blocking.AmbientDataPath;
        AddChild(Ambient);
    }

    private void AddAmbientFront()
    {
        var front = new Node2D { Name = "ambient_front" };
        AddChild(front);
        layers["ambient_front"] = front;
        if (Ambient is null) AddAmbientHost();
        Ambient!.Front = front;
    }

    private static Sprite2D FitSprite(Texture2D texture, string name)
    {
        var sprite = new Sprite2D { Name = name, Texture = texture, Centered = false };
        var size = texture.GetSize();
        if (size.X > 0 && size.Y > 0 && (size.X != CanvasSize.X || size.Y != CanvasSize.Y))
            sprite.Scale = new Vector2(CanvasSize.X / size.X, CanvasSize.Y / size.Y);
        return sprite;
    }

    private Vector2 HeroSpawn(string? arrivedFrom)
    {
        if (arrivedFrom is not null)
        {
            var back = View.Exits.FirstOrDefault(e => e.To == arrivedFrom);
            if (back is not null && Blocking?.Target(back.Id)?.InteractionPoint is { } natural) return Walk.Clamp(natural);
            if (back is not null && back.InteractionPoint.Count >= 2)
                return Walk.Clamp(new Vector2(back.InteractionPoint[0], back.InteractionPoint[1]));
        }
        if (Blocking?.Spawn is { } spawn) return Walk.Clamp(spawn);
        return Walk.Clamp(View.Spawn.Count >= 2 ? new Vector2(View.Spawn[0], View.Spawn[1]) : new Vector2(960, (Walk.Top + Walk.Bottom) / 2));
    }

    private void ApplyView(RoomView view, GameContent content)
    {
        // Targets with visual overrides.
        targets.Clear();
        hitOrder.Clear();
        foreach (var h in view.Hotspots)
        {
            var o = Overrides.Targets.TryGetValue(h.Id, out var ov) ? ov : null;
            var rect = ToRect(h.Rect, o);
            var anchor = (o?.LabelAnchor ?? ToVec(h.LabelAnchor, rect.Position + new Vector2(rect.Size.X / 2, -10))) + (o?.LabelOffset ?? Vector2.Zero);
            var point = ToVec(h.InteractionPoint, rect.GetCenter());
            if (Blocking?.Target(h.Id) is { } b) (rect, point, anchor) = ApplyBlocking(b, rect, point, anchor);
            targets[h.Id] = new TargetInfo(h.Id, h.IsNpc ? TargetKind.Npc : TargetKind.Prop, h.Name, rect,
                point, anchor, h.IsAtmospheric, h.ValidForSelectedItem, true);
        }
        foreach (var e in view.Exits)
        {
            var o = Overrides.Targets.TryGetValue(e.Id, out var ov) ? ov : null;
            var rect = ToRect(e.Rect, o);
            var defaultAnchor = new Vector2(Mathf.Clamp(rect.GetCenter().X, 80, CanvasSize.X - 80), rect.Position.Y - 12);
            var anchor = (o?.LabelAnchor ?? defaultAnchor) + (o?.LabelOffset ?? Vector2.Zero);
            var point = ToVec(e.InteractionPoint, rect.GetCenter());
            if (Blocking?.Target(e.Id) is { } b)
            {
                (rect, point, anchor) = ApplyBlocking(b, rect, point, anchor);
                if (b.LabelAnchor is null && b.Rect is not null)
                    anchor = new Vector2(Mathf.Clamp(rect.GetCenter().X, 80, CanvasSize.X - 80), rect.Position.Y - 12);
            }
            targets[e.Id] = new TargetInfo(e.Id, TargetKind.Exit, e.Label, rect, point, anchor,
                false, false, e.Unlocked);
        }
        hitOrder.AddRange(view.Hotspots.Where(h => h.IsNpc).Select(h => h.Id));
        hitOrder.AddRange(view.Hotspots.Where(h => !h.IsNpc).Reverse().Select(h => h.Id));
        hitOrder.AddRange(view.Exits.Select(e => e.Id));

        SyncNpcs(view);
        PlaceNpcLabels();
        TimeNode = BuildTimeNode(view);
        SyncVariantLayers(view);
        blockout?.Setup(this, false);
        devOverlay?.Setup(this, true);
        Labels.Room = this;
        if (Labels.FocusedId is { } focused && !targets.ContainsKey(focused)) Labels.FocusedId = null;
        Labels.QueueRedraw();
    }

    private void SyncNpcs(RoomView view)
    {
        var present = view.Npcs.Select(n => n.Id).ToHashSet(StringComparer.Ordinal);
        foreach (var gone in npcs.Keys.Where(id => !present.Contains(id)).ToList())
        {
            npcs[gone].QueueFree();
            npcs.Remove(gone);
        }
        foreach (var npc in view.Npcs)
        {
            if (npcs.ContainsKey(npc.Id) || npc.CharacterId is null) continue;
            var rect = targets[npc.Id].Rect;
            var feet = new Vector2(rect.Position.X + rect.Size.X / 2, rect.End.Y);
            if (Overrides.NpcFeet.TryGetValue(npc.Id, out var nudge)) feet += nudge;
            var staging = Blocking is not null && Blocking.Npcs.TryGetValue(npc.Id, out var st) ? st : null;
            if (staging?.Feet is { } stagedFeet) feet = stagedFeet;
            var actor = new Actor { ScaleOverride = staging?.Scale };
            var parent = staging?.Depth switch
            {
                NpcDepth.Back => npcsBack,
                NpcDepth.Front => npcsFront,
                _ => null,
            } ?? ActorsLayer;
            parent.AddChild(actor);
            actor.Setup(new ActorContext(npc.CharacterId, false, RoomId, view.Era, npc.Id, rect), Perspective, feet);
            actor.FaceTowards(new Vector2(CanvasSize.X / 2, feet.Y));
            npcs[npc.Id] = actor;
        }
    }

    private void SyncVariantLayers(RoomView view)
    {
        if (!layers.TryGetValue("prop_state_variants", out var layer)) return;
        var state = GameRuntime.Instance.State;
        var patches = Overrides.StatePatches.Where(p => p.After.All(state.IsDone) && !p.Until.Any(state.IsDone)).ToList();
        // Blockout rooms also list their active causal effects (dev aid until the art shows them).
        var causal = HasBackgroundArt ? new List<LastBell.Core.Rules.ActiveCausalEffect>() : view.CausalEffects.Where(c => !c.DeferredUntilReentry).ToList();
        string signature = string.Join("|", view.VariantLayers.Where(v => v.Visible).Select(v => v.Layer.Asset)) + "#" +
                           string.Join("|", patches.Select(p => p.Texture)) + "#" + string.Join("|", causal.Select(c => c.Index));
        if (signature == variantSignature) return;
        variantSignature = signature;
        foreach (var child in layer.GetChildren()) child.QueueFree();
        int index = 0;
        foreach (var variant in view.VariantLayers.Where(v => v.Visible))
        {
            if (Blocking is not null)
            {
                // The template overlay belongs to the template painting; a natural room draws its own (or a dev marker).
                if (Blocking.VariantLayer(variant.Layer.Asset) is not { } natural)
                {
                    GD.PushWarning($"Room {RoomId}: natural blocking maps no overlay for {variant.Layer.Asset}");
                    layer.AddChild(new DevVariantMarker { AssetName = variant.Layer.Asset, Index = index++ });
                    continue;
                }
                if (natural.Texture is null) continue; // the natural painting needs no overlay for this change
                string naturalPath = "res://assets/" + natural.Texture;
                if (!ResourceLoader.Exists(naturalPath) || GD.Load<Texture2D>(naturalPath) is not { } naturalTexture)
                {
                    layer.AddChild(new DevVariantMarker { AssetName = natural.Texture, Index = index++ });
                    continue;
                }
                string name = System.IO.Path.GetFileNameWithoutExtension(natural.Texture);
                layer.AddChild(natural.Position is { } pos
                    ? new Sprite2D { Name = name, Texture = naturalTexture, Centered = false, Position = pos }
                    : FitSprite(naturalTexture, name));
                continue;
            }
            string path = "res://assets/" + variant.Layer.Asset;
            if (ResourceLoader.Exists(path) && GD.Load<Texture2D>(path) is { } texture)
                layer.AddChild(FitSprite(texture, System.IO.Path.GetFileNameWithoutExtension(variant.Layer.Asset)));
            else
                layer.AddChild(new DevVariantMarker { AssetName = variant.Layer.Asset, Index = index++ });
        }
        foreach (var effect in causal)
        {
            layer.AddChild(new DevVariantMarker
            {
                Index = index,
                Text = TextService.Ui("ui.dev.causal_active", ("after", effect.Effect.After), ("change", effect.Effect.Change)),
            });
            index += 2;
        }
        // art_overrides.json state patches (props the hero changed himself, e.g. a bag taken off a shelf).
        foreach (var patch in patches)
        {
            string path = "res://assets/" + patch.Texture;
            if (!ResourceLoader.Exists(path) || GD.Load<Texture2D>(path) is not { } texture)
            {
                GD.PushWarning($"Room {RoomId}: state patch {patch.Texture} not found");
                continue;
            }
            layer.AddChild(new Sprite2D { Name = "Patch_" + System.IO.Path.GetFileNameWithoutExtension(patch.Texture), Texture = texture, Centered = false, Position = patch.Position });
        }
    }

    private void OnVisualFactoriesChanged()
    {
        if (!IsInsideTree()) return;
        Hero.SetVisual(ActorVisualRegistry.Create(Hero.Context));
        foreach (var npc in npcs.Values) npc.SetVisual(ActorVisualRegistry.Create(npc.Context));
        foreach (var guest in guests.Where(g => IsInstanceValid(g))) guest.SetVisual(ActorVisualRegistry.Create(guest.Context));
        PlaceNpcLabels();
        Labels?.QueueRedraw();
    }

    /// <summary>Gap in canvas px between the top of an NPC figure and the label's text baseline.</summary>
    public const float NpcLabelGap = 18f;

    /// <summary>
    /// NPC labels sit just above the figure that is actually drawn (head, bust, seated figure, robot
    /// pennant), not at the template <c>label_anchor</c> of game.json, which put every label across the
    /// face of a standing NPC and far above the small ROBOT (ISSUES ART-2035-02, INT-07). An explicit
    /// <c>label_anchor</c> in art_overrides.json still wins; <c>label_offset</c> is added as usual.
    /// </summary>
    private void PlaceNpcLabels()
    {
        foreach (var (id, actor) in npcs)
        {
            if (!targets.TryGetValue(id, out var target)) continue;
            var o = Overrides.Targets.TryGetValue(id, out var ov) ? ov : null;
            if (o?.LabelAnchor is not null) continue;
            var head = actor.HeadPosition;
            targets[id] = target with { LabelAnchor = new Vector2(head.X, head.Y - NpcLabelGap) + (o?.LabelOffset ?? Vector2.Zero) };
        }
    }

    /// <summary>
    /// The anchor node's painted clock (blocking <c>time_node</c>) while Core lists portal targets in this room: its own
    /// rect, or a game.json hotspot's rect (that hotspot then opens the chooser on a plain left click that Core
    /// resolves as a look). Presentation only: the chooser is the same UI as the HUD clock button (key T).
    /// </summary>
    private TimeNodeInfo? BuildTimeNode(RoomView view)
    {
        if (Blocking?.TimeNode is not { } node || view.PortalTargets.Count == 0) return null;
        if (node.HotspotId is { } hotspotId)
        {
            if (!targets.TryGetValue(hotspotId, out var bound)) return null;
            return new TimeNodeInfo(bound.Rect, node.InteractionPoint ?? bound.InteractionPoint, hotspotId);
        }
        if (node.Rect is not { } rect) return null;
        return new TimeNodeInfo(rect, Walk.Clamp(node.InteractionPoint ?? new Vector2(rect.GetCenter().X, Walk.Top + 20)), null);
    }

    /// <summary>The time node under a canvas point: its own rect (checked after every Core target) or the bound hotspot.</summary>
    public bool IsTimeNodeAt(Vector2 point, Hit hit) => TimeNode is { } node &&
        (node.HotspotId is { } id ? hit is Hit.Hotspot h && h.Id == id : hit is Hit.Floor or Hit.Empty && node.Rect.HasPoint(point));

    /// <summary>
    /// True when a plain left click at <paramref name="point"/> goes to the time node: no item selected, the point is on
    /// the node, and a bound game.json hotspot would only give its look (its item actions keep working).
    /// </summary>
    public bool TimeNodeTakes(Vector2 point, Hit hit) =>
        GameRuntime.Instance.State.SelectedItem is null && IsTimeNodeAt(point, hit) &&
        (TimeNode!.HotspotId is null || GameRuntime.Instance.Session.Resolve(hit, PointerButton.Left) is Resolution.Look);

    /// <summary>Hover name of the time node (ui.csv).</summary>
    public static TextRef TimeNodeName => new("ui.travel.time_node", "Hodiny časového uzla");

    /// <summary>A natural blocking's geometry replaces the template's field by field; a new rect without its own label anchor keeps the default anchor above it.</summary>
    private static (Rect2 Rect, Vector2 Point, Vector2 Anchor) ApplyBlocking(BlockingTarget b, Rect2 rect, Vector2 point, Vector2 anchor)
    {
        var r = b.Rect ?? rect;
        var a = b.LabelAnchor ?? (b.Rect is not null ? r.Position + new Vector2(r.Size.X / 2, -10) : anchor);
        return (r, b.InteractionPoint ?? point, a);
    }

    private static Rect2 ToRect(IReadOnlyList<int> r, TargetOverride? o)
    {
        if (r.Count < 4) return new Rect2();
        var nudge = o?.RectNudge ?? Vector4.Zero;
        return new Rect2(r[0] + nudge.X, r[1] + nudge.Y, Mathf.Max(4, r[2] + nudge.Z), Mathf.Max(4, r[3] + nudge.W));
    }

    private static Vector2 ToVec(IReadOnlyList<int> p, Vector2 fallback) => p.Count >= 2 ? new Vector2(p[0], p[1]) : fallback;
}
