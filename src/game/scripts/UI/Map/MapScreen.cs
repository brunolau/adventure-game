using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.Text;
using LastBell.Core.Views;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Map;

/// <summary>
/// The topological map (Core mode Map): one sheet per unlocked era (Core's <see cref="ViewBuilder.Map"/>). Each sheet
/// shows its REGIONS first (owner request 2026-10-06, travel overlay regions: e.g. 2020 Chorvátsky Grob and
/// Dúbravka), drawn as cards joined by their transport links (dashed = bus, tram, cable car); choosing a region shows
/// its rooms as nodes laid out by walking distance (solid = on foot, dashed = transport, faint = still closed), each
/// captioned with its district (<c>region.&lt;district&gt;.name</c>), hubs marked. Unvisited rooms are grey and
/// unnamed. A node that Core marks <c>CanFastTravel</c> travels there (<see cref="Navigation.FastTravel"/>: visited,
/// same era, reachable over open connections — a locked gate is never bypassed, AT12 — and inside the current region
/// or a hub of another region: far places are reached through their transport hub).
/// </summary>
public partial class MapScreen : ModalScreen
{
    private HFlowContainer tabRow = null!;
    private HBoxContainer navRow = null!;
    private Button backButton = null!;
    private Label crumb = null!;
    private ScrollContainer scroll = null!;
    private MapGraph graph = null!;
    private Label status = null!;
    private int year;
    private string? regionId;

    /// <summary>Godot constructor.</summary>
    public MapScreen() { PreferredSize = new Vector2(1760, 960); }

    /// <summary>The region whose rooms are shown, or null while the region overview is shown.</summary>
    public string? OpenRegionId => regionId;

    /// <summary>The year of the sheet on screen.</summary>
    public int SheetYear => year;

    /// <inheritdoc />
    protected override void Build()
    {
        SetTitle(Ui.T("ui.map.title"));
        tabRow = new HFlowContainer();
        tabRow.AddThemeConstantOverride("h_separation", 10);
        Body.AddChild(tabRow);
        navRow = Ui.HBox(16);
        backButton = Ui.Button("← " + Ui.T("ui.map.back_to_regions"), () => ShowRegion(null));
        backButton.Name = "BackToRegions";
        navRow.AddChild(backButton);
        crumb = Ui.Label("", "HeadingLabel");
        navRow.AddChild(crumb);
        Body.AddChild(navRow);
        graph = new MapGraph();
        scroll = new ScrollContainer { SizeFlagsVertical = SizeFlags.ExpandFill, SizeFlagsHorizontal = SizeFlags.ExpandFill, FollowFocus = true };
        scroll.AddChild(graph);
        var frame = new PanelContainer { ThemeTypeVariation = "CardPanel", SizeFlagsVertical = SizeFlags.ExpandFill };
        frame.AddThemeStyleboxOverride("panel", UiTheme.Box(new Color("efe2c6"), new Color(UiTheme.PaperEdge, 0.6f), 2, 12, 6));
        frame.AddChild(scroll);
        Body.AddChild(frame);
        status = Ui.Para(Ui.T("ui.map.region_rule"), "CaptionLabel");
        Body.AddChild(status);
        graph.Travel += OnTravel;
        graph.Inspect += text => status.Text = text;
        graph.OpenRegion += id => ShowRegion(id);
    }

    /// <inheritdoc />
    public override void Back() => GameRuntime.Instance.Update(GameRules.CloseOverlay);

    /// <inheritdoc />
    protected override void Refresh()
    {
        var game = GameRuntime.Instance;
        year = game.State.Era;
        regionId = null; // regions first
        Ui.Clear(tabRow);
        var group = new ButtonGroup();
        // Chronological tabs (game.json lists the eras in story order: 2020, 1995, 1960, 2035, 1982; playtest PT-S15).
        foreach (var era in ViewBuilder.Map(game.Content, game.State).Where(e => e.Unlocked).OrderBy(e => e.Year))
        {
            int y = era.Year;
            var b = Ui.Tab(Ui.T("ui.map.sheet_year", ("year", TextService.EraYear(y))), group);
            b.ButtonPressed = y == year;
            b.Toggled += on => { if (on) { year = y; regionId = null; ShowSheet(); } };
            tabRow.AddChild(b);
        }
        ShowSheet();
    }

    /// <inheritdoc />
    protected override Control? InitialFocus() => graph.PreferredNode;

    /// <summary>Shows the rooms of a region of the current sheet (null: the region overview).</summary>
    public void ShowRegion(string? id)
    {
        regionId = id;
        ShowSheet();
        Ui.FocusLater(graph.PreferredNode);
    }

    private void ShowSheet()
    {
        var game = GameRuntime.Instance;
        var sheet = ViewBuilder.Map(game.Content, game.State).FirstOrDefault(e => e.Year == year);
        if (sheet is null) return;
        var region = regionId is null ? null : sheet.Regions.FirstOrDefault(r => r.Id == regionId);
        if (region is null)
        {
            regionId = null;
            graph.BuildRegions(sheet);
            status.Text = Ui.T("ui.map.region_rule");
            crumb.Text = Ui.T("ui.map.regions_title");
            backButton.Visible = false;
        }
        else
        {
            graph.BuildRooms(sheet, region);
            status.Text = region.IsCurrent ? Ui.T("ui.map.fast_travel_rule") : Ui.T("ui.map.region_rule");
            crumb.Text = Ui.T(region.Name);
            backButton.Visible = true;
        }
        CallDeferred(MethodName.EnsureCurrentVisible);
    }

    private void EnsureCurrentVisible()
    {
        if (graph.PreferredNode is { } node) scroll.EnsureControlVisible(node);
    }

    private void OnTravel(string roomId)
    {
        var game = GameRuntime.Instance;
        var before = game.State;
        game.Update(s => Navigation.FastTravel(game.Content, s, roomId));
        if (ReferenceEquals(before, game.State)) status.Text = Ui.T("ui.map.unreachable");
    }
}

/// <summary>The drawn graph of one era sheet: region cards (overview) or the rooms of one region (nodes are focusable buttons; edges are drawn).</summary>
public partial class MapGraph : Control
{
    private const float NodeW = 250, NodeH = 100, ColGap = 300, RowGap = 124, Pad = 50;
    private const float RegionW = 330, RegionH = 150, RegionColGap = 420, RegionRowGap = 190;
    private readonly Dictionary<string, Button> nodes = new(StringComparer.Ordinal);
    private readonly List<(string From, string To, bool Open, string Travel)> edges = new();
    private MapEraView? sheet;

    /// <summary>Raised when a fast-travel node is chosen.</summary>
    public event Action<string>? Travel;

    /// <summary>Raised with a status text for a node that cannot be travelled to.</summary>
    public event Action<string>? Inspect;

    /// <summary>Raised when a region card is chosen (region id).</summary>
    public event Action<string>? OpenRegion;

    /// <summary>The current room's node, or the current region's card (if on this sheet).</summary>
    public Button? CurrentNode { get; private set; }

    /// <summary>The first node.</summary>
    public Button? FirstNode => nodes.Values.FirstOrDefault();

    /// <summary>Where keyboard focus starts: the current room / region, else the region's hub, else the first node.</summary>
    public Button? PreferredNode => CurrentNode ?? HubNode ?? FirstNode;

    /// <summary>The first hub node of the shown region (rooms view), or null.</summary>
    public Button? HubNode { get; private set; }

    /// <summary>True while the region overview is shown.</summary>
    public bool ShowsRegions { get; private set; }

    /// <summary>Node buttons by room id (rooms view) or region id (overview).</summary>
    public IReadOnlyDictionary<string, Button> Nodes => nodes;

    private void Reset(MapEraView era, bool regions)
    {
        sheet = era;
        ShowsRegions = regions;
        foreach (var b in nodes.Values) b.QueueFree();
        nodes.Clear();
        edges.Clear();
        CurrentNode = null;
        HubNode = null;
    }

    /// <summary>Layered layout: column = graph distance from <paramref name="root"/>; rows by barycentre of placed neighbours.</summary>
    private static Dictionary<string, Vector2> Layout(IReadOnlyList<string> ids, string root, Dictionary<string, List<string>> neighbours,
        float colGap, float rowGap, float nodeW, float nodeH, out Vector2 size, Func<string, string> tieBreak)
    {
        var depth = new Dictionary<string, int> { [root] = 0 };
        var queue = new Queue<string>();
        queue.Enqueue(root);
        while (queue.Count > 0)
        {
            var id = queue.Dequeue();
            foreach (var n in neighbours[id])
                if (!depth.ContainsKey(n)) { depth[n] = depth[id] + 1; queue.Enqueue(n); }
        }
        int maxDepth = depth.Values.DefaultIfEmpty(0).Max();
        foreach (var id in ids) if (!depth.ContainsKey(id)) depth[id] = maxDepth + 1;
        var columns = ids.GroupBy(id => depth[id]).OrderBy(g => g.Key).Select(g => g.ToList()).ToList();
        var row = new Dictionary<string, float>();
        for (int c = 0; c < columns.Count; c++)
        {
            var col = columns[c];
            if (c > 0)
            {
                col = col.OrderBy(id => neighbours[id].Where(row.ContainsKey).Select(n => row[n]).DefaultIfEmpty(99).Average())
                    .ThenBy(tieBreak, StringComparer.Ordinal).ToList();
                columns[c] = col;
            }
            for (int i = 0; i < col.Count; i++) row[col[i]] = i;
        }
        int maxRows = columns.Max(c => c.Count);
        var positions = new Dictionary<string, Vector2>();
        for (int c = 0; c < columns.Count; c++)
        {
            var col = columns[c];
            float offset = (maxRows - col.Count) * rowGap / 2f;
            for (int i = 0; i < col.Count; i++) positions[col[i]] = new Vector2(Pad + c * colGap, Pad + 40 + offset + i * rowGap);
        }
        size = new Vector2(Pad * 2 + (columns.Count - 1) * colGap + nodeW, Pad * 2 + 40 + (maxRows - 1) * rowGap + nodeH);
        return positions;
    }

    // ------------------------------------------------------------------ region overview

    /// <summary>Builds the region overview of a sheet.</summary>
    public void BuildRegions(MapEraView era)
    {
        Reset(era, regions: true);
        var game = GameRuntime.Instance;
        var content = game.Content;
        var state = game.State;
        var regionOfRoom = era.Rooms.ToDictionary(r => r.RoomId, r => r.RegionId, StringComparer.Ordinal);
        var ids = era.Regions.Select(r => r.Id).ToList();
        var neighbours = ids.ToDictionary(id => id, _ => new List<string>(), StringComparer.Ordinal);
        foreach (var c in content.Data.Connections)
        {
            if (!regionOfRoom.TryGetValue(c.From, out var a) || !regionOfRoom.TryGetValue(c.To, out var b) || a == b) continue;
            edges.Add((a, b, state.AllDone(c.RequiresDone), c.Travel));
            neighbours[a].Add(b);
            neighbours[b].Add(a);
        }
        var anchorRoom = era.Rooms.FirstOrDefault(r => r.IsAnchor)?.RoomId;
        string root = era.Regions.FirstOrDefault(r => r.IsCurrent)?.Id ?? (anchorRoom is null ? ids[0] : regionOfRoom[anchorRoom]);
        var positions = Layout(ids, root, neighbours, RegionColGap, RegionRowGap, RegionW, RegionH, out var size, id => id);
        CustomMinimumSize = size;
        foreach (var region in era.Regions) AddRegionNode(era, region, positions[region.Id]);
        QueueRedraw();
    }

    private void AddRegionNode(MapEraView era, MapRegionView region, Vector2 position)
    {
        var rooms = era.Rooms.Where(r => region.Rooms.Contains(r.RoomId)).ToList();
        int visited = rooms.Count(r => r.Visited);
        string name = region.Visited ? Ui.T(region.Name) : Ui.T("ui.map.region_unvisited");
        var b = new Button
        {
            Text = "",
            Position = position,
            Size = new Vector2(RegionW, RegionH),
            CustomMinimumSize = new Vector2(RegionW, RegionH),
            Name = "Region_" + region.Id.Replace(' ', '_'),
        };
        Color bg = region.Visited ? UiTheme.PaperDeep : new Color("d8ccb4");
        Color border = region.IsCurrent ? UiTheme.Accent : region.CanTravel ? UiTheme.Brass : new Color(UiTheme.PaperEdge, 0.6f);
        int width = region.IsCurrent ? 5 : region.CanTravel ? 3 : 2;
        b.AddThemeStyleboxOverride("normal", UiTheme.Box(bg, border, width, 14, 10));
        b.AddThemeStyleboxOverride("hover", UiTheme.Box(new Color("fbf2df"), region.CanTravel || region.IsCurrent ? UiTheme.BrassLight : border, width + 1, 14, 10));
        b.AddThemeStyleboxOverride("pressed", UiTheme.Box(new Color("d9c194"), border, width + 1, 14, 10));
        b.AddThemeStyleboxOverride("focus", UiTheme.Box(new Color(0, 0, 0, 0), UiTheme.Focus, 4, 16, 0));
        var box = Ui.VBox(4);
        box.MouseFilter = MouseFilterEnum.Ignore;
        box.Position = new Vector2(16, 12);
        box.Size = new Vector2(RegionW - 32, RegionH - 24);
        var title = Ui.Label(name.ToUpperInvariant(), "HeadingLabel");
        title.AddThemeFontSizeOverride("font_size", 27);
        title.AddThemeFontOverride("font", UiTheme.BodyBold);
        if (!region.Visited) title.AddThemeColorOverride("font_color", UiTheme.InkSoft);
        title.ClipText = false;
        title.TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis;
        box.AddChild(title);
        var count = Ui.Label(Ui.T("ui.map.region_rooms", ("visited", visited.ToString()), ("total", rooms.Count.ToString())), "CaptionLabel");
        count.AddThemeFontSizeOverride("font_size", 19);
        box.AddChild(count);
        var hubNames = region.Hubs.Select(h => era.Rooms.First(r => r.RoomId == h)).Select(r => r.Visited ? Ui.T(r.Name) : Ui.T("ui.map.unvisited"));
        var hub = Ui.Label(Ui.T("ui.map.region_hub", ("hub", string.Join(", ", hubNames))), "CaptionLabel");
        hub.AddThemeFontSizeOverride("font_size", 18);
        hub.TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis;
        hub.ClipText = true;
        hub.CustomMinimumSize = new Vector2(RegionW - 40, 0);
        box.AddChild(hub);
        foreach (var child in box.GetChildren()) if (child is Control c) c.MouseFilter = MouseFilterEnum.Ignore;
        b.AddChild(box);
        if (region.IsCurrent) { AddTag(b, Ui.T("ui.map.you_are_here"), UiTheme.Accent, new Vector2(RegionW - 92, RegionH - 18)); CurrentNode = b; }
        else if (region.Transport is { } transport && region.CanTravel)
            AddTag(b, TextService.Get(new TextRef("ui.travel." + transport, transport)), UiTheme.Brass, new Vector2(RegionW - 130, RegionH - 18));
        string tip = region.IsCurrent ? Ui.T("ui.map.you_are_here")
            : !region.Visited ? Ui.T("ui.map.region_unvisited")
            : region.CanTravel ? Ui.T("ui.map.via_hub", ("hub", string.Join(", ", hubNames))) : Ui.T("ui.map.unreachable");
        b.TooltipText = name + " — " + tip;
        string id = region.Id;
        bool open = region.Visited;
        b.Pressed += () =>
        {
            if (open) OpenRegion?.Invoke(id);
            else Inspect?.Invoke(tip);
        };
        b.FocusEntered += () => Inspect?.Invoke(name + " — " + tip);
        AddChild(b);
        nodes[id] = b;
    }

    private static void AddTag(Control parent, string text, Color color, Vector2 position)
    {
        var label = Ui.Label(text, "CaptionLabel");
        label.AddThemeColorOverride("font_color", UiTheme.Cream);
        label.AddThemeFontSizeOverride("font_size", 19);
        var tag = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore };
        tag.AddThemeStyleboxOverride("panel", UiTheme.Box(color, color, 0, 8, 4));
        tag.AddChild(label);
        tag.Position = position;
        parent.AddChild(tag);
    }

    // ------------------------------------------------------------------ rooms of one region

    /// <summary>Builds the room graph of one region of a sheet.</summary>
    public void BuildRooms(MapEraView era, MapRegionView region)
    {
        Reset(era, regions: false);
        var game = GameRuntime.Instance;
        var content = game.Content;
        var state = game.State;
        var rooms = era.Rooms.Where(r => region.Rooms.Contains(r.RoomId)).ToList();
        var roomIds = rooms.Select(r => r.RoomId).ToHashSet();
        var connections = content.Data.Connections.Where(c => roomIds.Contains(c.From) && roomIds.Contains(c.To)).ToList();
        foreach (var c in connections) edges.Add((c.From, c.To, state.AllDone(c.RequiresDone), c.Travel));
        var neighbours = rooms.ToDictionary(r => r.RoomId, _ => new List<string>(), StringComparer.Ordinal);
        foreach (var c in connections) { neighbours[c.From].Add(c.To); neighbours[c.To].Add(c.From); }
        string root = rooms.FirstOrDefault(r => r.IsCurrent)?.RoomId ?? rooms.FirstOrDefault(r => r.IsHub)?.RoomId ?? rooms[0].RoomId;
        if (rooms.FirstOrDefault(r => r.IsAnchor) is { } anchor && !rooms.Any(r => r.IsCurrent)) root = anchor.RoomId;
        var positions = Layout(rooms.Select(r => r.RoomId).ToList(), region.Hubs.FirstOrDefault(roomIds.Contains) ?? root, neighbours,
            ColGap, RowGap, NodeW, NodeH, out var size, id => content.GetRoom(id).District);
        CustomMinimumSize = size;
        foreach (var room in rooms) AddNode(room, region, positions[room.RoomId], era.Year == state.Era);
        QueueRedraw();
    }

    private void AddNode(MapRoomView room, MapRegionView region, Vector2 position, bool sameEra)
    {
        string name = room.Visited ? Ui.T(room.Name) : Ui.T("ui.map.unvisited");
        var b = new Button
        {
            Text = name,
            AutowrapMode = TextServer.AutowrapMode.WordSmart,
            Position = position,
            Size = new Vector2(NodeW, NodeH),
            CustomMinimumSize = new Vector2(NodeW, NodeH),
            ClipText = true,
            Name = "Room_" + room.RoomId,
        };
        b.AddThemeFontSizeOverride("font_size", 23);
        Color bg = room.Visited ? UiTheme.PaperDeep : new Color("d8ccb4");
        Color border = room.IsCurrent ? UiTheme.Accent : room.CanFastTravel ? UiTheme.Brass : new Color(UiTheme.PaperEdge, 0.6f);
        int width = room.IsCurrent ? 5 : room.CanFastTravel ? 3 : 2;
        StyleBoxFlat Style(Color c, Color e, int w)
        {
            var box = UiTheme.Box(c, e, w, 12, 10);
            box.ContentMarginTop = 30; // room for the district caption
            return box;
        }
        b.AddThemeStyleboxOverride("normal", Style(bg, border, width));
        b.AddThemeStyleboxOverride("hover", Style(new Color("fbf2df"), room.CanFastTravel ? UiTheme.BrassLight : border, width + 1));
        b.AddThemeStyleboxOverride("pressed", Style(new Color("d9c194"), border, width + 1));
        b.AddThemeStyleboxOverride("focus", UiTheme.Box(new Color(0, 0, 0, 0), UiTheme.Focus, 4, 14, 0));
        if (!room.Visited) b.AddThemeColorOverride("font_color", UiTheme.InkSoft);
        string transport = region.Transport is { } t ? TextService.Get(new TextRef("ui.travel." + t, t)) : "";
        string hubs = string.Join(", ", region.Hubs.Select(h => sheet!.Rooms.First(r => r.RoomId == h)).Select(r => r.Visited ? Ui.T(r.Name) : Ui.T("ui.map.unvisited")));
        string tip = room.IsCurrent ? Ui.T("ui.map.you_are_here")
            : room.CanFastTravel ? (transport.Length > 0 && !region.IsCurrent ? Ui.T("ui.map.travel_by", ("place", name), ("transport", transport)) : Ui.T("ui.map.travel_to", ("place", name)))
            : !room.Visited ? Ui.T("ui.map.unvisited")
            : sameEra && !region.IsCurrent && !room.IsHub ? Ui.T("ui.map.via_hub", ("hub", hubs))
            : Ui.T("ui.map.unreachable");
        if (room.IsAnchor) tip += " · " + Ui.T("ui.map.node_tooltip");
        if (room.IsHub && !region.IsCurrent) tip += " · " + Ui.T("ui.map.hub");
        b.TooltipText = tip;
        string id = room.RoomId;
        bool canTravel = room.CanFastTravel && sameEra;
        b.Pressed += () =>
        {
            if (canTravel) Travel?.Invoke(id);
            else Inspect?.Invoke(tip);
        };
        b.FocusEntered += () => Inspect?.Invoke(name + " — " + tip);
        AddChild(b);
        // District caption: region.<district>.name (ISSUES TEXT-02 / UI-02).
        var district = Ui.Label(TextService.Get(TextKeys.RegionOf(GameRuntime.Instance.Content.GetRoom(room.RoomId))).ToUpperInvariant(), "CaptionLabel");
        district.AddThemeFontSizeOverride("font_size", 16);
        district.AddThemeFontOverride("font", UiTheme.BodyBold);
        district.Position = new Vector2(14, 4);
        district.Size = new Vector2(NodeW - 60, 26);
        // Not ClipText: it cut the accents of the capitals (DÚBRAVKA, STARÉ MESTO; playtest PT-F03); trim the width only.
        district.ClipText = false;
        district.TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis;
        b.AddChild(district);
        if (room.IsAnchor)
        {
            var clock = new Glyph(GlyphKind.Clock, 34, UiTheme.Accent) { Position = new Vector2(NodeW - 40, 4) };
            b.AddChild(clock);
        }
        if (room.IsCurrent)
        {
            AddTag(b, Ui.T("ui.map.you_are_here"), UiTheme.Accent, new Vector2(NodeW - 84, NodeH - 16));
            CurrentNode = b;
        }
        else if (room.IsHub && region.Hubs.Count < region.Rooms.Count)
        {
            AddTag(b, Ui.T("ui.map.hub"), UiTheme.Brass, new Vector2(10, NodeH - 16));
        }
        if (room.IsHub) HubNode ??= b;
        nodes[id] = b;
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        if (sheet is null) return;
        foreach (var (from, to, open, travel) in edges)
        {
            if (!nodes.TryGetValue(from, out var a) || !nodes.TryGetValue(to, out var b)) continue;
            var pa = a.Position + a.Size / 2;
            var pb = b.Position + b.Size / 2;
            var color = open ? new Color(UiTheme.Ink, 0.75f) : new Color(UiTheme.Muted, 0.6f);
            float width = ShowsRegions ? (open ? 6 : 4) : (open ? 4 : 3);
            if (travel == "walk") DrawLine(pa, pb, color, width, true);
            else DrawDashedLine(pa, pb, open ? UiTheme.Accent : color, width, ShowsRegions ? 20 : 14, true);
        }
    }
}
