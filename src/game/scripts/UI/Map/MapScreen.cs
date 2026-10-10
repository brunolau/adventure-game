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
using LastBell.Game.World;

namespace LastBell.Game.UI.Map;

/// <summary>
/// The topological map (Core mode Map): one sheet per unlocked era (Core's <see cref="ViewBuilder.Map"/>). A sheet shows
/// ALL its regions at once (travel overlay regions, e.g. 2020 Chorvátsky Grob and Dúbravka): one section per region with
/// its name, "Tu si" or the transport into it, the visited count and the stop, and its rooms as nodes laid out by walking
/// distance from the stop (solid = on foot, dashed = transport, faint = still closed), each captioned with its district
/// (<c>region.&lt;district&gt;.name</c>). Only discovered (visited) rooms are drawn, the header counts the rest; a region
/// without a visited room is one grey "Neznáma oblasť" card. ONE click on a node that Core marks <c>CanFastTravel</c> travels there
/// (<see cref="Navigation.FastTravel"/>: visited, same era, reachable over open connections — a locked gate is never
/// bypassed, AT12) in any region, with the transport card of the ride into another region (owner override 2026-10-06,
/// docs/DECISIONS.md control change 8; it replaced the regions-first view and the hub-only rule of item 7).
/// </summary>
public partial class MapScreen : ModalScreen
{
    private HFlowContainer tabRow = null!;
    private ScrollContainer scroll = null!;
    private HFlowContainer sections = null!;
    private Label status = null!;
    private readonly List<MapGraph> graphs = new();
    private readonly Dictionary<string, Control> sectionOf = new(StringComparer.Ordinal);
    private int year;

    /// <summary>Godot constructor.</summary>
    public MapScreen() { PreferredSize = new Vector2(1760, 960); }

    /// <summary>The year of the sheet on screen.</summary>
    public int SheetYear => year;

    /// <summary>The room graphs of the regions on screen (one per visited region, data order).</summary>
    public IReadOnlyList<MapGraph> Graphs => graphs;

    /// <summary>Region ids with a section on screen (data order).</summary>
    public IReadOnlyCollection<string> RegionIds => sectionOf.Keys;

    /// <summary>The node button of a room on the sheet on screen, or null.</summary>
    public Button? RoomNode(string roomId) => graphs.Select(g => g.Nodes.GetValueOrDefault(roomId)).FirstOrDefault(b => b is not null);

    /// <summary>The section (panel) of a region on the sheet on screen, or null.</summary>
    public Control? Section(string regionId) => sectionOf.GetValueOrDefault(regionId);

    /// <inheritdoc />
    protected override void Build()
    {
        SetTitle(Ui.T("ui.map.title"));
        graphs.Clear(); // Build runs again after a change of the language (ModalScreen.Relocalize)
        sectionOf.Clear();
        tabRow = new HFlowContainer();
        tabRow.AddThemeConstantOverride("h_separation", 10);
        Body.AddChild(tabRow);
        sections = new HFlowContainer { SizeFlagsHorizontal = SizeFlags.ExpandFill };
        sections.AddThemeConstantOverride("h_separation", 22);
        sections.AddThemeConstantOverride("v_separation", 14);
        var margin = Ui.Margin(sections, 12);
        margin.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        scroll = new ScrollContainer
        {
            SizeFlagsVertical = SizeFlags.ExpandFill, SizeFlagsHorizontal = SizeFlags.ExpandFill, FollowFocus = true,
            HorizontalScrollMode = ScrollContainer.ScrollMode.Disabled,
        };
        scroll.AddChild(margin);
        var frame = new PanelContainer { ThemeTypeVariation = "CardPanel", SizeFlagsVertical = SizeFlags.ExpandFill };
        frame.AddThemeStyleboxOverride("panel", UiTheme.Box(new Color("efe2c6"), new Color(UiTheme.PaperEdge, 0.6f), 2, 12, 6));
        frame.AddChild(scroll);
        Body.AddChild(frame);
        status = Ui.Para(Ui.T("ui.map.fast_travel_rule"), "CaptionLabel");
        Body.AddChild(status);
        // The room cards are arranged to the visible width of the scroll view (shrink, then wrap): re-arrange when it
        // changes (window size, HUD scale, first layout of the panel).
        scroll.Resized += () =>
        {
            bool changed = false;
            foreach (var g in graphs) changed |= g.SetViewport(GraphViewport(), 0);
            if (changed) EnsureVisibleNextFrame();
        };
    }

    /// <inheritdoc />
    public override void Back() => GameRuntime.Instance.Update(GameRules.CloseOverlay);

    /// <inheritdoc />
    protected override void Refresh()
    {
        var game = GameRuntime.Instance;
        year = game.State.Era;
        Ui.Clear(tabRow);
        var group = new ButtonGroup();
        // Chronological tabs (game.json lists the eras in story order: 2020, 1995, 1960, 2035, 1982; playtest PT-S15).
        foreach (var era in ViewBuilder.Map(game.Content, game.State).Where(e => e.Unlocked).OrderBy(e => e.Year))
        {
            int y = era.Year;
            var b = Ui.Tab(Ui.T("ui.map.sheet_year", ("year", TextService.EraYear(y))), group);
            b.ButtonPressed = y == year;
            b.Toggled += on => { if (on) { year = y; ShowSheet(); Ui.FocusLater(PreferredNode()); } };
            tabRow.AddChild(b);
        }
        ShowSheet();
    }

    /// <inheritdoc />
    protected override Control? InitialFocus() => PreferredNode();

    /// <summary>Where keyboard focus starts: the current room, else the first room that can be travelled to, else the first room.</summary>
    private Button? PreferredNode() =>
        graphs.Select(g => g.CurrentNode).FirstOrDefault(n => n is not null)
        ?? graphs.SelectMany(g => g.TravelNodes).FirstOrDefault()
        ?? graphs.Select(g => g.FirstNode).FirstOrDefault(n => n is not null);

    /// <summary>The room graphs' layout space: the visible width of the scroll view minus the scroll bar and the section frame.</summary>
    private Vector2 GraphViewport()
    {
        float bar = Math.Max(12f, scroll.GetVScrollBar().GetCombinedMinimumSize().X);
        float width = scroll.Size.X > 1 ? scroll.Size.X : 1690;
        return new Vector2(width - bar - 2 * 12 - 2 * SectionMargin - 8, 100000);
    }

    private const int SectionMargin = 10;

    private void ShowSheet()
    {
        var game = GameRuntime.Instance;
        var sheet = ViewBuilder.Map(game.Content, game.State).FirstOrDefault(e => e.Year == year);
        if (sheet is null) return;
        foreach (var g in graphs) { g.Travel -= OnTravel; }
        graphs.Clear();
        sectionOf.Clear();
        Ui.Clear(sections);
        foreach (var region in sheet.Regions) AddSection(sheet, region);
        status.Text = Ui.T("ui.map.fast_travel_rule");
        EnsureVisibleNextFrame();
    }

    private void AddSection(MapEraView sheet, MapRegionView region)
    {
        var game = GameRuntime.Instance;
        var rooms = sheet.Rooms.Where(r => region.Rooms.Contains(r.RoomId)).ToList();
        int visited = rooms.Count(r => r.Visited);
        var panel = new PanelContainer { Name = "Region_" + region.Id.Replace(' ', '_'), MouseFilter = MouseFilterEnum.Ignore };
        Color bg = region.Visited ? new Color("f3e7cd") : new Color("ddd1b9");
        Color border = region.IsCurrent ? UiTheme.Accent : new Color(UiTheme.PaperEdge, 0.7f);
        panel.AddThemeStyleboxOverride("panel", UiTheme.Box(bg, border, region.IsCurrent ? 4 : 2, 14, SectionMargin));
        var box = Ui.VBox(2);
        box.MouseFilter = MouseFilterEnum.Ignore;
        panel.AddChild(box);
        var header = Ui.HBox(12);
        header.MouseFilter = MouseFilterEnum.Ignore;
        string name = region.Visited ? Ui.T(region.Name) : Ui.T("ui.map.region_unvisited");
        var title = Ui.Label(name.ToUpperInvariant(), "HeadingLabel");
        title.AddThemeFontSizeOverride("font_size", 24);
        title.AddThemeFontOverride("font", UiTheme.BodyBold);
        if (!region.Visited) title.AddThemeColorOverride("font_color", UiTheme.InkSoft);
        header.AddChild(title);
        if (region.IsCurrent) header.AddChild(Pill(Ui.T("ui.map.you_are_here"), UiTheme.Accent));
        else if (region.Visited && sheet.Year == game.State.Era && rooms.Any(r => r.CanFastTravel) &&
                 rooms.Where(r => r.CanFastTravel).Select(r => WorldStage.FastTravelCardStyle(game.Content, game.State, game.State.Room, r.RoomId))
                     .FirstOrDefault(s => s is not null) is { } style)
            header.AddChild(Pill(TextService.Get(new TextRef("ui.travel." + style, style)), UiTheme.Brass));
        // One header line (the sheet should fit one screen): the stop is tagged on its node ("Zastávka").
        var sub = Ui.Label(Ui.T("ui.map.region_rooms", ("visited", visited.ToString()), ("total", rooms.Count.ToString())), "CaptionLabel");
        sub.AddThemeFontSizeOverride("font_size", 18);
        sub.MouseFilter = MouseFilterEnum.Ignore;
        sub.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        header.AddChild(sub);
        box.AddChild(header);
        if (region.Visited)
        {
            var graph = new MapGraph { Name = "Graph_" + region.Id.Replace(' ', '_') };
            graph.SetViewport(GraphViewport(), 0, arrange: false);
            box.AddChild(graph);
            graph.BuildRooms(sheet, region);
            graph.Travel += OnTravel;
            graph.Inspect += text => status.Text = text;
            graphs.Add(graph);
        }
        sections.AddChild(panel);
        sectionOf[region.Id] = panel;
    }

    /// <summary>A small coloured tag (the region header's "Tu si" / transport).</summary>
    private static Control Pill(string text, Color color)
    {
        var label = Ui.Label(text, "CaptionLabel");
        label.AddThemeColorOverride("font_color", UiTheme.Cream);
        label.AddThemeFontSizeOverride("font_size", 19);
        var tag = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore, SizeFlagsVertical = SizeFlags.ShrinkCenter };
        tag.AddThemeStyleboxOverride("panel", UiTheme.Box(color, color, 0, 8, 4));
        tag.AddChild(label);
        return tag;
    }

    private void EnsureCurrentVisible()
    {
        // The focused card (keyboard / pad), else the current room: after a re-arrangement it may have moved.
        var focus = GetViewport()?.GuiGetFocusOwner();
        var node = focus is not null && sections.IsAncestorOf(focus) ? focus : PreferredNode();
        if (node is not null) scroll.EnsureControlVisible(node);
    }

    /// <summary>After the scroll view has taken the new minimum size (its scroll range updates in a later sort).</summary>
    private async void EnsureVisibleNextFrame()
    {
        await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
        if (IsInsideTree() && Visible) EnsureCurrentVisible();
    }

    private void OnTravel(string roomId)
    {
        var game = GameRuntime.Instance;
        var before = game.State;
        WorldStage.Instance?.MarkFastTravel(true);
        game.Update(s => Navigation.FastTravel(game.Content, s, roomId));
        if (ReferenceEquals(before, game.State) || game.State.Room == before.Room)
        {
            WorldStage.Instance?.MarkFastTravel(false);
            if (ReferenceEquals(before, game.State)) status.Text = Ui.T("ui.map.unreachable");
        }
    }
}

/// <summary>
/// The drawn room graph of one region of an era sheet (nodes are focusable buttons; edges are drawn). Columns are the
/// walking / travel distance from the region's stop. The columns are fitted to the width given by
/// <see cref="SetViewport"/>: at the standard spacing when they fit (the graph is then only as wide as its columns, so
/// small regions sit side by side on the sheet); else the room cards and their gaps shrink together down to
/// <c>NodeMinW</c>; when even that is too wide, the columns wrap into bands that run left to right and right to left in
/// turn, so the next band starts under the last column of the previous one and a link between two bands is routed around
/// the side of that shared column. Every place stays visible without horizontal scrolling from 1280x720 to 3840x2160 and
/// at larger HUD scales (owner report 2026-10-06: the last card of Chorvátsky Grob 2020 was cut off).
/// </summary>
public partial class MapGraph : Control
{
    private const float NodeW = 190, NodeMinW = 150, NodeH = 74, NodeGap = 32, RowGap = 84, PadX = 20, PadY = 10, BandGap = 44;
    private const float TagInset = 24;
    private readonly Dictionary<string, Button> nodes = new(StringComparer.Ordinal);
    private readonly Dictionary<string, int> bandOf = new(StringComparer.Ordinal);
    private readonly List<(string From, string To, bool Open, string Travel)> edges = new();
    private readonly List<Button> travelNodes = new();
    private List<List<string>> columns = new();
    private MapEraView? sheet;
    private Vector2 viewport = new(1600, 100000);
    private int slots = 1;
    private float cardW = NodeW, pitch = NodeW + NodeGap;

    /// <summary>Raised when a fast-travel node is chosen.</summary>
    public event Action<string>? Travel;

    /// <summary>Raised with a status text for a node that cannot be travelled to.</summary>
    public event Action<string>? Inspect;

    /// <summary>The current room's node (if in this region).</summary>
    public Button? CurrentNode { get; private set; }

    /// <summary>The first node.</summary>
    public Button? FirstNode => nodes.Values.FirstOrDefault();

    /// <summary>The nodes that fast-travel on a click (data order).</summary>
    public IReadOnlyList<Button> TravelNodes => travelNodes;

    /// <summary>Node buttons by room id.</summary>
    public IReadOnlyDictionary<string, Button> Nodes => nodes;

    /// <summary>Number of bands the columns wrap into (1: one row of columns).</summary>
    public int Bands { get; private set; } = 1;

    /// <summary>
    /// The width available to the graph (and the scroll bar width, kept for callers; 0 when the caller already took it
    /// off); re-arranges the cards when the size changed (unless <paramref name="arrange"/> is false: the next build uses
    /// it). True when the cards were re-arranged.
    /// </summary>
    public bool SetViewport(Vector2 size, float scrollbar, bool arrange = true)
    {
        size = new Vector2(size.X - scrollbar, size.Y);
        if (size.X < 1 || size.Y < 1) return false;
        bool changed = Math.Abs(size.X - viewport.X) > 0.5f;
        viewport = size;
        if (!arrange || !changed || columns.Count == 0) return false;
        Arrange();
        return true;
    }

    /// <summary>Layered order: column = graph distance from <paramref name="root"/>; rows by barycentre of placed neighbours.</summary>
    private static List<List<string>> Columns(IReadOnlyList<string> ids, string root, Dictionary<string, List<string>> neighbours,
        Func<string, string> tieBreak)
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
        return columns;
    }

    private readonly record struct Plan(int Slots, float CardW, float Gap);

    /// <summary>The fewest bands whose columns fit <paramref name="width"/> (standard spacing, else shrunk), else one column per band.</summary>
    private Plan MakePlan(float width)
    {
        float inner = width - 2 * PadX;
        int n = columns.Count;
        for (int bands = 1; bands <= n; bands++)
        {
            int c = (n + bands - 1) / bands;
            if (bands > 1 && c == (n + bands - 2) / (bands - 1)) continue; // the same band width as one band fewer
            float w = NodeW, gap = NodeGap;
            float need = c * w + (c - 1) * gap;
            if (need > inner)
            {
                float f = inner / need;
                w = NodeW * f;
                gap = NodeGap * f;
                if (w < NodeMinW) continue;
            }
            return new Plan(c, w, gap);
        }
        return new Plan(1, NodeMinW, 0); // not even one card fits: the scroll view scrolls
    }

    /// <summary>Positions and sizes the cards for the current viewport.</summary>
    private void Arrange()
    {
        if (columns.Count == 0) return;
        var plan = MakePlan(viewport.X);
        slots = plan.Slots;
        cardW = plan.CardW;
        pitch = plan.CardW + plan.Gap;
        bandOf.Clear();
        Bands = (columns.Count + slots - 1) / slots;
        float y = PadY;
        for (int band = 0; band < Bands; band++)
        {
            var bandColumns = columns.Skip(band * slots).Take(slots).ToList();
            int rows = bandColumns.Max(c => c.Count);
            for (int j = 0; j < bandColumns.Count; j++)
            {
                int slot = band % 2 == 0 ? j : slots - 1 - j;
                var col = bandColumns[j];
                float offset = (rows - col.Count) * RowGap / 2f;
                for (int i = 0; i < col.Count; i++)
                {
                    bandOf[col[i]] = band;
                    if (!nodes.TryGetValue(col[i], out var node)) continue;
                    node.CustomMinimumSize = new Vector2(cardW, NodeH);
                    node.Size = new Vector2(cardW, NodeH);
                    node.Position = new Vector2(PadX + slot * pitch, y + offset + i * RowGap);
                }
            }
            y += (rows - 1) * RowGap + NodeH + (band < Bands - 1 ? BandGap : 0);
        }
        CustomMinimumSize = new Vector2(2 * PadX + slots * cardW + (slots - 1) * plan.Gap, y + PadY);
        QueueRedraw();
    }

    /// <summary>A small coloured tag on the bottom edge of a card, anchored to its left or right side (follows the card's width).
    /// The anchor calls push the opposite anchor along: without that Godot clamps a left anchor of 1 back to the right anchor 0.</summary>
    private static void AddTag(Control parent, string text, Color color, bool right, float above)
    {
        var label = Ui.Label(text, "CaptionLabel");
        label.AddThemeColorOverride("font_color", UiTheme.Cream);
        label.AddThemeFontSizeOverride("font_size", 15);
        var tag = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore };
        tag.AddThemeStyleboxOverride("panel", UiTheme.Box(color, color, 0, 7, 2));
        tag.AddChild(label);
        float anchor = right ? 1 : 0, x = right ? -TagInset : 10;
        tag.GrowHorizontal = right ? GrowDirection.Begin : GrowDirection.End;
        tag.GrowVertical = GrowDirection.End;
        tag.SetAnchorAndOffset(Side.Left, anchor, x, pushOppositeAnchor: true);
        tag.SetAnchorAndOffset(Side.Right, anchor, x, pushOppositeAnchor: true);
        tag.SetAnchorAndOffset(Side.Top, 1, -above, pushOppositeAnchor: true);
        tag.SetAnchorAndOffset(Side.Bottom, 1, -above, pushOppositeAnchor: true);
        parent.AddChild(tag);
    }

    /// <summary>Builds the room graph of one region of a sheet.</summary>
    public void BuildRooms(MapEraView era, MapRegionView region)
    {
        sheet = era;
        foreach (var b in nodes.Values) b.QueueFree();
        nodes.Clear();
        bandOf.Clear();
        edges.Clear();
        travelNodes.Clear();
        CurrentNode = null;
        var game = GameRuntime.Instance;
        var content = game.Content;
        var state = game.State;
        // Only discovered rooms are drawn (owner 2026-10-06: one screen; the header counts the rest, "Miesta: 8 z 9").
        var rooms = era.Rooms.Where(r => region.Rooms.Contains(r.RoomId) && r.Visited).ToList();
        if (rooms.Count == 0) { columns = new List<List<string>>(); CustomMinimumSize = Vector2.Zero; return; }
        var roomIds = rooms.Select(r => r.RoomId).ToHashSet();
        var connections = content.Data.Connections.Where(c => roomIds.Contains(c.From) && roomIds.Contains(c.To)).ToList();
        foreach (var c in connections) edges.Add((c.From, c.To, state.AllDone(c.RequiresDone), c.Travel));
        var neighbours = rooms.ToDictionary(r => r.RoomId, _ => new List<string>(), StringComparer.Ordinal);
        foreach (var c in connections) { neighbours[c.From].Add(c.To); neighbours[c.To].Add(c.From); }
        string root = rooms.FirstOrDefault(r => r.IsCurrent)?.RoomId ?? rooms.FirstOrDefault(r => r.IsHub)?.RoomId ?? rooms[0].RoomId;
        if (rooms.FirstOrDefault(r => r.IsAnchor) is { } anchor && !rooms.Any(r => r.IsCurrent)) root = anchor.RoomId;
        columns = Columns(rooms.Select(r => r.RoomId).ToList(), region.Hubs.FirstOrDefault(roomIds.Contains) ?? root, neighbours,
            id => content.GetRoom(id).District);
        foreach (var room in rooms) AddNode(room, region, era.Year == state.Era);
        Arrange();
    }

    private void AddNode(MapRoomView room, MapRegionView region, bool sameEra)
    {
        var game = GameRuntime.Instance;
        string name = room.Visited ? Ui.T(room.Name) : Ui.T("ui.map.unvisited");
        var b = new Button
        {
            Text = name,
            AutowrapMode = TextServer.AutowrapMode.WordSmart,
            Size = new Vector2(NodeW, NodeH),
            CustomMinimumSize = new Vector2(NodeW, NodeH),
            ClipText = true,
            Name = "Room_" + room.RoomId,
        };
        b.AddThemeFontSizeOverride("font_size", 19);
        bool canTravel = room.CanFastTravel && sameEra;
        Color bg = room.Visited ? UiTheme.PaperDeep : new Color("d8ccb4");
        Color border = room.IsCurrent ? UiTheme.Accent : canTravel ? UiTheme.Brass : new Color(UiTheme.PaperEdge, 0.6f);
        int width = room.IsCurrent ? 5 : canTravel ? 3 : 2;
        StyleBoxFlat Style(Color c, Color e, int w)
        {
            var box = UiTheme.Box(c, e, w, 12, 8);
            box.ContentMarginTop = 22; // room for the district caption
            return box;
        }
        b.AddThemeStyleboxOverride("normal", Style(bg, border, width));
        b.AddThemeStyleboxOverride("hover", Style(new Color("fbf2df"), canTravel ? UiTheme.BrassLight : border, width + 1));
        b.AddThemeStyleboxOverride("pressed", Style(new Color("d9c194"), border, width + 1));
        b.AddThemeStyleboxOverride("focus", UiTheme.Box(new Color(0, 0, 0, 0), UiTheme.Focus, 4, 14, 0));
        if (!room.Visited) b.AddThemeColorOverride("font_color", UiTheme.InkSoft);
        string? style = canTravel ? WorldStage.FastTravelCardStyle(game.Content, game.State, game.State.Room, room.RoomId) : null;
        string transport = style is null ? "" : TextService.Get(new TextRef("ui.travel." + style, style));
        string tip = room.IsCurrent ? Ui.T("ui.map.you_are_here")
            : canTravel ? (transport.Length > 0 ? Ui.T("ui.map.travel_by", ("place", name), ("transport", transport)) : Ui.T("ui.map.travel_to", ("place", name)))
            : !room.Visited ? Ui.T("ui.map.unvisited")
            : Ui.T("ui.map.unreachable");
        if (room.IsAnchor) tip += " · " + Ui.T("ui.map.node_tooltip");
        b.TooltipText = tip;
        string id = room.RoomId;
        b.Pressed += () =>
        {
            if (canTravel) Travel?.Invoke(id);
            else Inspect?.Invoke(tip);
        };
        b.FocusEntered += () => Inspect?.Invoke(name + " — " + tip);
        AddChild(b);
        // District caption: region.<district>.name (ISSUES TEXT-02 / UI-02); anchored to both sides, it follows the card width.
        var district = Ui.Label(TextService.Get(TextKeys.RegionOf(game.Content.GetRoom(room.RoomId))).ToUpperInvariant(), "CaptionLabel");
        district.AddThemeFontSizeOverride("font_size", 13);
        district.AddThemeFontOverride("font", UiTheme.BodyBold);
        district.SetAnchorAndOffset(Side.Left, 0, 11, pushOppositeAnchor: true);
        const float captionTop = 5; // below the borders and the focus ring (they hid the háček of ČIERNA VODA)
        district.SetAnchorAndOffset(Side.Top, 0, captionTop, pushOppositeAnchor: true);
        district.SetAnchorAndOffset(Side.Right, 1, room.IsAnchor ? -36 : -11, pushOppositeAnchor: true);
        district.SetAnchorAndOffset(Side.Bottom, 0, captionTop + 20, pushOppositeAnchor: true);
        // Not ClipText: it cut the accents of the capitals (DÚBRAVKA, STARÉ MESTO; playtest PT-F03); trim the width only.
        district.ClipText = false;
        district.TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis;
        b.AddChild(district);
        if (room.IsAnchor)
        {
            var clock = new Glyph(GlyphKind.Clock, 26, UiTheme.Accent);
            clock.SetAnchorAndOffset(Side.Left, 1, -32, pushOppositeAnchor: true);
            clock.SetAnchorAndOffset(Side.Top, 0, 3, pushOppositeAnchor: true);
            clock.SetAnchorAndOffset(Side.Right, 1, -5, pushOppositeAnchor: true);
            clock.SetAnchorAndOffset(Side.Bottom, 0, 29, pushOppositeAnchor: true);
            b.AddChild(clock);
        }
        if (room.IsCurrent)
        {
            AddTag(b, Ui.T("ui.map.you_are_here"), UiTheme.Accent, right: true, 12);
            CurrentNode = b;
        }
        else if (room.IsHub && region.Hubs.Count < region.Rooms.Count)
        {
            AddTag(b, Ui.T("ui.map.hub"), UiTheme.Brass, right: false, 12);
        }
        if (canTravel) travelNodes.Add(b);
        nodes[id] = b;
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        if (sheet is null) return;
        var lanes = new Dictionary<(int Band, string A, string B), int>();
        var used = new Dictionary<int, int>();
        foreach (var (from, to, open, travel) in edges)
        {
            if (!nodes.TryGetValue(from, out var a) || !nodes.TryGetValue(to, out var b)) continue;
            var color = open ? new Color(UiTheme.Ink, 0.75f) : new Color(UiTheme.Muted, 0.6f);
            float width = open ? 4 : 3;
            void Segment(Vector2 p, Vector2 q)
            {
                if (travel == "walk") DrawLine(p, q, color, width, true);
                else DrawDashedLine(p, q, open ? UiTheme.Accent : color, width, 14, true);
            }
            int bandA = bandOf.GetValueOrDefault(from), bandB = bandOf.GetValueOrDefault(to);
            if (bandA == bandB)
            {
                Segment(a.Position + a.Size / 2, b.Position + b.Size / 2);
                continue;
            }
            // Between two bands both ends sit in the shared column at the turn of the serpentine (right end after an even
            // band, left end after an odd one): go around that column's side instead of through its other cards.
            int upper = Math.Min(bandA, bandB);
            bool right = upper % 2 == 0;
            bool ordered = string.CompareOrdinal(from, to) < 0;
            var key = (upper, ordered ? from : to, ordered ? to : from);
            if (!lanes.TryGetValue(key, out int lane))
            {
                lane = used.GetValueOrDefault(upper);
                used[upper] = lane + 1;
                lanes[key] = lane;
            }
            float shift = Math.Min(lane, 3) * 6;
            float gutter = right ? PadX + (slots - 1) * pitch + cardW + PadX * 0.45f + shift : PadX * 0.55f - shift;
            Vector2 SideOf(Button n) => new(right ? n.Position.X + n.Size.X : n.Position.X, n.Position.Y + n.Size.Y / 2);
            Vector2 pa = SideOf(a), pb = SideOf(b);
            Segment(pa, new Vector2(gutter, pa.Y));
            Segment(new Vector2(gutter, pa.Y), new Vector2(gutter, pb.Y));
            Segment(new Vector2(gutter, pb.Y), pb);
        }
    }
}
