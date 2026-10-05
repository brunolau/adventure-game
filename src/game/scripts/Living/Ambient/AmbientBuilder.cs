using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using Godot;
using LastBell.Game.Hooks;
using LastBell.Game.World;

namespace LastBell.Game.Living.Ambient;

/// <summary>
/// Fills a room's <see cref="AmbientHost"/> from <c>res://data/ambient/&lt;room&gt;.json</c>:
/// <code>{ "room": "S02", "layers": [ { "id": "birch", "type": "sway", "plane": "back", ... }, ... ] }</code>
/// Layers are created in file order. plane: back (default; behind actors, above the background and
/// variant layers), front (above the foreground mask) or actors (y-sorted with the hero by
/// <c>sort_y</c>). Optional <c>"era"</c> / <c>"unless_done"</c> / <c>"if_done"</c> (action ids) limit a
/// layer to a state; the room is rebuilt on refresh only when that selection changes.
/// </summary>
public static class AmbientBuilder
{
    private static readonly Dictionary<string, Func<AmbientLayer>> Types = new(StringComparer.Ordinal)
    {
        ["particles"] = () => new ParticleLayer(),
        ["sway"] = () => new SwayLayer(),
        ["water"] = () => new WaterLayer(),
        ["sprite_loop"] = () => new SpriteLoopLayer(),
        ["cutout"] = () => new SpriteLoopLayer(),
        ["tween_path"] = () => new TweenPathLayer(),
        ["flicker"] = () => new FlickerLayer(),
        ["clouds"] = () => new CloudLayer(),
        ["rotor"] = () => new RotorLayer(),
        ["critters"] = () => new CritterLayer(),
    };

    /// <summary>Known layer type names.</summary>
    public static IEnumerable<string> TypeNames => Types.Keys;

    /// <summary>Builds every layer of the room; returns the created layers.</summary>
    public static List<AmbientLayer> Build(Room room, bool reducedMotion)
    {
        var created = new List<AmbientLayer>();
        var host = room.Ambient;
        if (host is null) return created;
        var data = Json.Load(host.DataPath, warnIfMissing: false);
        if (data?.Arr("layers") is not { } layers) return created;
        var context = new AmbientContext { Room = room };
        int index = 0;
        foreach (var node in layers)
        {
            index++;
            if (node is not JsonObject def || def.Bool("disabled")) continue;
            if (!Applies(def, room)) continue;
            string type = def.Str("type", "")!;
            string id = def.Str("id", $"{type}_{index}")!;
            if (!Types.TryGetValue(type, out var factory))
            {
                GD.PushWarning($"Living: {host.DataPath}: unknown layer type '{type}' ({id})");
                continue;
            }
            try
            {
                var layer = factory();
                layer.Setup(def, context, id, type);
                Node2D parent = def.Str("plane", "back") switch
                {
                    "front" => host.Front ?? host,
                    "actors" => host.Actors ?? host,
                    _ => host,
                };
                if (def.Str("plane") == "actors")
                {
                    // y-sorted with the hero: the node's position is its sort y; drawing stays in canvas coords
                    float sortY = def.Num("sort_y", 0);
                    var holder = new Node2D { Name = "AmbientSort_" + id, Position = new Vector2(0, sortY) };
                    layer.Position = new Vector2(0, -sortY);
                    holder.AddChild(layer);
                    parent.AddChild(holder);
                }
                else parent.AddChild(layer);
                layer.SetReducedMotion(reducedMotion);
                created.Add(layer);
            }
            catch (Exception ex)
            {
                GD.PushError($"Living: {host.DataPath}: layer {id} failed: {ex.Message}");
            }
        }
        return created;
    }

    /// <summary>State conditions of a layer (visual only; Core decides nothing here).</summary>
    public static bool Applies(JsonObject def, Room room)
    {
        if (def.Has("era") && def.Int("era") != room.View.Era) return false;
        var state = Runtime.GameRuntime.Instance?.State;
        if (state is null) return true;
        foreach (var id in def.Strings("if_done"))
            if (!state.IsDone(id)) return false;
        foreach (var id in def.Strings("unless_done"))
            if (state.IsDone(id)) return false;
        return true;
    }

    /// <summary>A signature of which conditional layers apply now (to detect a needed rebuild).</summary>
    public static string Signature(Room room)
    {
        var data = Json.Load(room.Ambient.DataPath, warnIfMissing: false);
        if (data?.Arr("layers") is not { } layers) return "";
        var chars = new System.Text.StringBuilder();
        foreach (var node in layers)
            if (node is JsonObject def && (def.Has("if_done") || def.Has("unless_done")))
                chars.Append(Applies(def, room) ? '1' : '0');
        return chars.ToString();
    }
}
