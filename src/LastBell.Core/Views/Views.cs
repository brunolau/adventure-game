using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Text;

namespace LastBell.Core.Views;

/// <summary>A visible hotspot ready to render.</summary>
/// <param name="Id">Hotspot id (pass it back in <see cref="Hit.Hotspot"/>).</param>
/// <param name="Name">Name label (Space labels, hover name).</param>
/// <param name="IsNpc">True for NPC hotspots.</param>
/// <param name="CharacterId">Character id for NPCs.</param>
/// <param name="IsAtmospheric">True when no action ever targets it (look-only prop).</param>
/// <param name="Rect">Hit rectangle [x, y, w, h] in the 1920x1080 canvas.</param>
/// <param name="InteractionPoint">Walk target [x, y].</param>
/// <param name="LabelAnchor">Space label anchor [x, y].</param>
/// <param name="ValidForSelectedItem">True when the selected item has an executable rule on it (subtle outline).</param>
public sealed record HotspotView(string Id, TextRef Name, bool IsNpc, string? CharacterId, bool IsAtmospheric,
    IReadOnlyList<int> Rect, IReadOnlyList<int> InteractionPoint, IReadOnlyList<int> LabelAnchor, bool ValidForSelectedItem);

/// <summary>An exit zone ready to render (always visible and inspectable, even when locked).</summary>
/// <param name="Id">Exit id (pass it back in <see cref="Hit.Exit"/>).</param>
/// <param name="To">Destination room.</param>
/// <param name="Label">Label.</param>
/// <param name="Unlocked">True when the gate is open.</param>
/// <param name="Travel">Travel presentation kind.</param>
/// <param name="Rect">Hit rectangle.</param>
/// <param name="InteractionPoint">Walk target.</param>
public sealed record ExitView(string Id, string To, TextRef Label, bool Unlocked, string Travel, IReadOnlyList<int> Rect, IReadOnlyList<int> InteractionPoint);

/// <summary>Everything the generic Room scene needs to build a room from data in the current state.</summary>
/// <param name="RoomId">Room id.</param>
/// <param name="Name">Room name.</param>
/// <param name="Era">Era.</param>
/// <param name="BackgroundAsset">Background asset path.</param>
/// <param name="Music">Music asset path.</param>
/// <param name="CameraFamily">Camera family.</param>
/// <param name="WalkPolygon">Walkable polygon.</param>
/// <param name="Spawn">Spawn point.</param>
/// <param name="LayerOrder">Layer order (back to front).</param>
/// <param name="Hotspots">Visible hotspots in data order (props and NPCs).</param>
/// <param name="Npcs">The visible NPC hotspots only.</param>
/// <param name="Exits">Exits in data order.</param>
/// <param name="VariantLayers">Visual variant layers (draw those with Visible=true).</param>
/// <param name="CausalEffects">Active causal effects for this room.</param>
/// <param name="HotspotLabels">Space toggle state.</param>
/// <param name="AccessibleOrder">Tab order: NPCs, progress props, atmospheric props, exits.</param>
/// <param name="PortalTargets">Chronometer destinations available here.</param>
public sealed record RoomView(
    string RoomId, TextRef Name, int Era, string BackgroundAsset, string Music, string CameraFamily,
    IReadOnlyList<IReadOnlyList<int>> WalkPolygon, IReadOnlyList<int> Spawn, IReadOnlyList<string> LayerOrder,
    IReadOnlyList<HotspotView> Hotspots, IReadOnlyList<HotspotView> Npcs, IReadOnlyList<ExitView> Exits,
    IReadOnlyList<VariantLayerState> VariantLayers, IReadOnlyList<ActiveCausalEffect> CausalEffects,
    bool HotspotLabels, IReadOnlyList<string> AccessibleOrder, IReadOnlyList<PortalTarget> PortalTargets);

/// <summary>An owned item in the inventory drawer.</summary>
/// <param name="Id">Item id (pass it back in <see cref="Hit.Item"/>).</param>
/// <param name="Name">Name.</param>
/// <param name="Look">Look text.</param>
/// <param name="Purpose">Purpose text.</param>
/// <param name="Icon">Icon asset path.</param>
/// <param name="IsSelected">True when attached to the cursor.</param>
/// <param name="IsArchived">True when it has no remaining use (shown on the archive tab; still owned).</param>
public sealed record InventoryItemView(string Id, TextRef Name, TextRef Look, TextRef Purpose, string Icon, bool IsSelected, bool IsArchived);

/// <summary>A room on the topological map.</summary>
/// <param name="RoomId">Room id.</param>
/// <param name="Name">Name.</param>
/// <param name="Visited">Visited rooms show their name; others are grey.</param>
/// <param name="IsCurrent">Current room.</param>
/// <param name="CanFastTravel">Fast travel allowed right now (only meaningful in map mode).</param>
/// <param name="IsAnchor">True for the era's time node.</param>
/// <param name="RegionId">Id of the map region the room belongs to.</param>
/// <param name="IsHub">True when the region is entered from other regions through this room (stop or station).</param>
public sealed record MapRoomView(string RoomId, TextRef Name, bool Visited, bool IsCurrent, bool CanFastTravel, bool IsAnchor,
    string RegionId = "", bool IsHub = true);

/// <summary>
/// A region of one era sheet (the map shows the regions first, then the rooms of the chosen region). Fast travel
/// is free inside the current region; another region is reached only through one of its hubs.
/// </summary>
/// <param name="Id">Region id.</param>
/// <param name="Name">Region name (<c>region.&lt;id&gt;.name</c>).</param>
/// <param name="Rooms">Room ids of the region (data order).</param>
/// <param name="Hubs">Hub room ids.</param>
/// <param name="IsCurrent">The hero is in this region.</param>
/// <param name="Visited">At least one room of the region was visited.</param>
/// <param name="CanTravel">At least one room of the region can be fast-travelled to right now.</param>
/// <param name="Transport">Travel style used to reach the region from the current room (e.g. <c>bus</c>), or null.</param>
public sealed record MapRegionView(string Id, TextRef Name, IReadOnlyList<string> Rooms, IReadOnlyList<string> Hubs, bool IsCurrent,
    bool Visited, bool CanTravel, string? Transport);

/// <summary>One era sheet of the map.</summary>
/// <param name="Year">Year.</param>
/// <param name="Date">Date text.</param>
/// <param name="Unlocked">Era unlocked.</param>
/// <param name="Rooms">Rooms of the era (data order).</param>
/// <param name="Regions">Regions of the era (data order of their first room).</param>
public sealed record MapEraView(int Year, TextRef Date, bool Unlocked, IReadOnlyList<MapRoomView> Rooms, IReadOnlyList<MapRegionView> Regions);

/// <summary>View model builders for the presentation layer. They never change state.</summary>
public static class ViewBuilder
{
    /// <summary>Builds the view of the current room (or another room for preloading).</summary>
    public static RoomView Room(GameContent content, GameState state, string? roomId = null)
    {
        var room = content.GetRoom(roomId ?? state.Room);
        var targeted = new HashSet<string>(content.Actions.Where(a => !a.IsCombine).Select(a => a.Target), StringComparer.Ordinal);
        var validItemTargets = new HashSet<string>(StringComparer.Ordinal);
        if (state.SelectedItem is not null && room.Id == state.Room)
        {
            foreach (var a in content.Actions)
                if (a.IsClick && a.SelectedItem == state.SelectedItem && GameRules.ValidAction(content, state, a)) validItemTargets.Add(a.Target);
        }
        var hotspots = room.Hotspots.Where(h => GameRules.IsVisible(h, state)).Select(h => new HotspotView(
            h.Id, TextKeys.NameOf(h), h.IsNpc, h.CharacterId, !h.IsNpc && !targeted.Contains(h.Id),
            h.Rect, h.InteractionPoint, h.LabelAnchor, validItemTargets.Contains(h.Id))).ToList();
        var exits = room.Exits.Select(e => new ExitView(e.Id, e.To, TextKeys.LabelOf(e), state.AllDone(e.RequiresDone), e.Travel, e.Rect, e.InteractionPoint)).ToList();
        var order = hotspots.Where(h => h.IsNpc).Concat(hotspots.Where(h => !h.IsNpc && !h.IsAtmospheric))
            .Concat(hotspots.Where(h => h.IsAtmospheric)).Select(h => h.Id).Concat(exits.Select(e => e.Id)).ToList();
        return new RoomView(room.Id, TextKeys.NameOf(room), room.Era, room.BackgroundAsset, room.Music, room.CameraFamily,
            room.WalkPolygon, room.Spawn, room.LayerOrder, hotspots, hotspots.Where(h => h.IsNpc).ToList(), exits,
            WorldEffects.VariantLayers(content, state, room.Id), WorldEffects.CausalEffectsAt(content, state, room.Id),
            state.HotspotLabels, order, room.Id == state.Room ? Navigation.PortalTargets(content, state) : Array.Empty<PortalTarget>());
    }

    /// <summary>The inventory drawer (acquisition order).</summary>
    public static IReadOnlyList<InventoryItemView> Inventory(GameContent content, GameState state) =>
        state.Inventory.Select(content.GetItem).Select(i => new InventoryItemView(i.Id, TextKeys.NameOf(i), TextKeys.LookOf(i),
            TextKeys.PurposeOf(i), i.Icon, i.Id == state.SelectedItem, IsArchived(content, state, i.Id))).ToList();

    /// <summary>
    /// True when an owned item has no remaining use: no action that can still happen requires,
    /// consumes, selects or targets it. The chronometer is never archived (portals need it).
    /// Archiving is only a view: the item stays owned for every rule.
    /// </summary>
    public static bool IsArchived(GameContent content, GameState state, string itemId)
    {
        if (!state.Has(itemId) || itemId == GameContent.ChronometerItem) return false;
        foreach (var a in content.Actions)
        {
            if (state.IsDone(a.Id) || state.AnyDone(a.ExcludedDone)) continue;
            if (a.RequiresItems.Contains(itemId) || a.Consumes.Contains(itemId) || a.SelectedItem == itemId || (a.IsCombine && a.Target == itemId))
                return false;
        }
        return true;
    }

    /// <summary>
    /// The topological map: every era sheet with its regions and visited/grey rooms and fast-travel flags
    /// (same rule as <see cref="Navigation.CanFastTravel"/>: visited, current era, reachable, and inside the current
    /// region or a hub of another region).
    /// </summary>
    public static IReadOnlyList<MapEraView> Map(GameContent content, GameState state)
    {
        var reachable = Navigation.ConnectedRooms(content, state, includePortals: false);
        var sheets = new List<MapEraView>();
        foreach (var e in content.Eras)
        {
            var rooms = content.Rooms.Where(r => r.Era == e.Year).Select(r => new MapRoomView(r.Id, TextKeys.NameOf(r), state.Visited.Contains(r.Id),
                r.Id == state.Room,
                state.Visited.Contains(r.Id) && r.Era == state.Era && reachable.Contains(r.Id) && r.Id != state.Room &&
                Navigation.IsRegionTarget(content, state.Room, r.Id),
                r.Id == e.Anchor, content.RegionOf(r.Id).Id, content.IsHub(r.Id))).ToList();
            var byId = rooms.ToDictionary(r => r.RoomId, StringComparer.Ordinal);
            var regions = content.RegionsOf(e.Year)
                .OrderBy(g => content.Rooms.ToList().FindIndex(r => g.Rooms.Contains(r.Id)))
                .Select(g => new MapRegionView(g.Id, TextKeys.NameOf(g), g.Rooms, g.Hubs, g.Rooms.Contains(state.Room),
                    g.Rooms.Any(state.Visited.Contains), g.Rooms.Any(id => byId[id].CanFastTravel),
                    g.Rooms.Contains(state.Room) || e.Year != state.Era ? null
                        : g.Hubs.Select(h => Navigation.TransportBetween(content, state, state.Room, h)).FirstOrDefault(t => t is not null)))
                .ToList();
            sheets.Add(new MapEraView(e.Year, TextKeys.DateOf(e), Navigation.IsEraUnlocked(content, state, e.Year), rooms, regions));
        }
        return sheets;
    }

    /// <summary>
    /// Hover information from the shared resolver: the target name plus the action line. With a
    /// selected item the action line is non-empty only for an executable item rule; an invalid pair
    /// keeps the name and shows an empty action line.
    /// </summary>
    public static HoverInfo Hover(GameContent content, GameState state, Hit hit)
    {
        var resolution = GameRules.ResolveInteraction(content, state, hit, PointerButton.Left);
        var room = content.GetRoom(state.Room);
        var name = hit switch
        {
            Hit.Hotspot h when room.Hotspots.FirstOrDefault(x => x.Id == h.Id) is { } hs && GameRules.IsVisible(hs, state) => TextKeys.NameOf(hs),
            Hit.Exit e when room.Exits.FirstOrDefault(x => x.Id == e.Id) is { } ex => TextKeys.LabelOf(ex),
            Hit.Item i when state.Has(i.Id) => TextKeys.NameOf(content.GetItem(i.Id)),
            _ => TextRef.Empty,
        };
        return new HoverInfo(name, GameRules.ItemActionLabel(resolution), resolution);
    }
}

/// <summary>Hover preview.</summary>
/// <param name="Name">Name of the thing under the cursor (empty for floor/nothing).</param>
/// <param name="ActionLabel">Action sentence (empty unless the resolution is an executable action).</param>
/// <param name="Resolution">The left-click resolution the hover is based on.</param>
public sealed record HoverInfo(TextRef Name, TextRef ActionLabel, Resolution Resolution);
