using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.Views;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Map;

/// <summary>
/// The topological map (Core mode Map): one sheet per unlocked era (Core's <see cref="ViewBuilder.Map"/>),
/// rooms as nodes laid out by walking distance from the era's time node, connections as lines
/// (solid = open on foot, dashed = transport, faint = still closed), each room captioned with its
/// region (<c>region.&lt;district&gt;.name</c>). Unvisited rooms are grey and unnamed. A node that Core
/// marks <c>CanFastTravel</c> travels there (<see cref="Navigation.FastTravel"/>: visited, same era,
/// reachable over open connections — a locked gate is never bypassed, AT12).
/// </summary>
public partial class MapScreen : ModalScreen
{
    private HFlowContainer tabRow = null!;
    private ScrollContainer scroll = null!;
    private MapGraph graph = null!;
    private Label status = null!;
    private int year;

    /// <summary>Godot constructor.</summary>
    public MapScreen() { PreferredSize = new Vector2(1760, 960); }

    /// <inheritdoc />
    protected override void Build()
    {
        SetTitle(Ui.T("ui.map.title"));
        tabRow = new HFlowContainer();
        tabRow.AddThemeConstantOverride("h_separation", 10);
        Body.AddChild(tabRow);
        graph = new MapGraph();
        scroll = new ScrollContainer { SizeFlagsVertical = SizeFlags.ExpandFill, SizeFlagsHorizontal = SizeFlags.ExpandFill, FollowFocus = true };
        scroll.AddChild(graph);
        var frame = new PanelContainer { ThemeTypeVariation = "CardPanel", SizeFlagsVertical = SizeFlags.ExpandFill };
        frame.AddThemeStyleboxOverride("panel", UiTheme.Box(new Color("efe2c6"), new Color(UiTheme.PaperEdge, 0.6f), 2, 12, 6));
        frame.AddChild(scroll);
        Body.AddChild(frame);
        status = Ui.Para(Ui.T("ui.map.fast_travel_rule"), "CaptionLabel");
        Body.AddChild(status);
        graph.Travel += OnTravel;
        graph.Inspect += text => status.Text = text;
    }

    /// <inheritdoc />
    public override void Back() => GameRuntime.Instance.Update(GameRules.CloseOverlay);

    /// <inheritdoc />
    protected override void Refresh()
    {
        var game = GameRuntime.Instance;
        year = game.State.Era;
        status.Text = Ui.T("ui.map.fast_travel_rule");
        Ui.Clear(tabRow);
        var group = new ButtonGroup();
        foreach (var era in ViewBuilder.Map(game.Content, game.State).Where(e => e.Unlocked))
        {
            int y = era.Year;
            var b = Ui.Tab(Ui.T("ui.map.sheet_year", ("year", y.ToString())), group);
            b.ButtonPressed = y == year;
            b.Toggled += on => { if (on) { year = y; ShowSheet(); } };
            tabRow.AddChild(b);
        }
        ShowSheet();
    }

    /// <inheritdoc />
    protected override Control? InitialFocus() => graph.CurrentNode ?? graph.FirstNode;

    private void ShowSheet()
    {
        var game = GameRuntime.Instance;
        var sheet = ViewBuilder.Map(game.Content, game.State).FirstOrDefault(e => e.Year == year);
        if (sheet is null) return;
        graph.Build(sheet);
        CallDeferred(MethodName.EnsureCurrentVisible);
    }

    private void EnsureCurrentVisible()
    {
        if (graph.CurrentNode is { } node) scroll.EnsureControlVisible(node);
    }

    private void OnTravel(string roomId)
    {
        var game = GameRuntime.Instance;
        var before = game.State;
        game.Update(s => Navigation.FastTravel(game.Content, s, roomId));
        if (ReferenceEquals(before, game.State)) status.Text = Ui.T("ui.map.unreachable");
    }
}

/// <summary>The drawn graph of one era sheet (nodes are focusable buttons with a region caption; edges are drawn).</summary>
public partial class MapGraph : Control
{
    private const float NodeW = 250, NodeH = 100, ColGap = 300, RowGap = 124, Pad = 50;
    private readonly Dictionary<string, Button> nodes = new(StringComparer.Ordinal);
    private readonly List<(string From, string To, bool Open, string Travel)> edges = new();
    private MapEraView? sheet;

    /// <summary>Raised when a fast-travel node is chosen.</summary>
    public event Action<string>? Travel;

    /// <summary>Raised with a status text for a node that cannot be travelled to.</summary>
    public event Action<string>? Inspect;

    /// <summary>The current room's node (if on this sheet).</summary>
    public Button? CurrentNode { get; private set; }

    /// <summary>The first node.</summary>
    public Button? FirstNode => nodes.Values.FirstOrDefault();

    /// <summary>Builds the sheet.</summary>
    public void Build(MapEraView era)
    {
        sheet = era;
        foreach (var b in nodes.Values) b.QueueFree();
        nodes.Clear();
        edges.Clear();
        CurrentNode = null;
        var game = GameRuntime.Instance;
        var content = game.Content;
        var state = game.State;
        var roomIds = era.Rooms.Select(r => r.RoomId).ToHashSet();
        var connections = content.Data.Connections.Where(c => roomIds.Contains(c.From) && roomIds.Contains(c.To)).ToList();
        foreach (var c in connections) edges.Add((c.From, c.To, state.AllDone(c.RequiresDone), c.Travel));

        // Layered layout: column = distance from the era's time node.
        var anchor = era.Rooms.FirstOrDefault(r => r.IsAnchor)?.RoomId ?? era.Rooms.First().RoomId;
        var neighbours = era.Rooms.ToDictionary(r => r.RoomId, _ => new List<string>());
        foreach (var c in connections) { neighbours[c.From].Add(c.To); neighbours[c.To].Add(c.From); }
        var depth = new Dictionary<string, int> { [anchor] = 0 };
        var queue = new Queue<string>();
        queue.Enqueue(anchor);
        while (queue.Count > 0)
        {
            var id = queue.Dequeue();
            foreach (var n in neighbours[id])
                if (!depth.ContainsKey(n)) { depth[n] = depth[id] + 1; queue.Enqueue(n); }
        }
        int maxDepth = depth.Values.DefaultIfEmpty(0).Max();
        foreach (var r in era.Rooms) if (!depth.ContainsKey(r.RoomId)) depth[r.RoomId] = maxDepth + 1;
        var columns = era.Rooms.GroupBy(r => depth[r.RoomId]).OrderBy(g => g.Key).Select(g => g.Select(r => r.RoomId).ToList()).ToList();
        var row = new Dictionary<string, float>();
        for (int c = 0; c < columns.Count; c++)
        {
            var col = columns[c];
            if (c > 0)
            {
                // Barycentre of the already placed neighbours keeps lines short; ties by district then data order.
                col = col.OrderBy(id => neighbours[id].Where(row.ContainsKey).Select(n => row[n]).DefaultIfEmpty(99).Average())
                    .ThenBy(id => content.GetRoom(id).District, StringComparer.Ordinal).ToList();
                columns[c] = col;
            }
            for (int i = 0; i < col.Count; i++) row[col[i]] = i;
        }
        int maxRows = columns.Max(c => c.Count);
        var positions = new Dictionary<string, Vector2>();
        for (int c = 0; c < columns.Count; c++)
        {
            var col = columns[c];
            float offset = (maxRows - col.Count) * RowGap / 2f;
            for (int i = 0; i < col.Count; i++) positions[col[i]] = new Vector2(Pad + c * ColGap, Pad + 40 + offset + i * RowGap);
        }
        CustomMinimumSize = new Vector2(Pad * 2 + (columns.Count - 1) * ColGap + NodeW, Pad * 2 + 40 + (maxRows - 1) * RowGap + NodeH);

        foreach (var room in era.Rooms) AddNode(room, positions[room.RoomId], era.Year == state.Era);

        QueueRedraw();
    }

    private void AddNode(MapRoomView room, Vector2 position, bool sameEra)
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
        };
        b.AddThemeFontSizeOverride("font_size", 23);
        Color bg = room.Visited ? UiTheme.PaperDeep : new Color("d8ccb4");
        Color border = room.IsCurrent ? UiTheme.Accent : room.CanFastTravel ? UiTheme.Brass : new Color(UiTheme.PaperEdge, 0.6f);
        int width = room.IsCurrent ? 5 : room.CanFastTravel ? 3 : 2;
        StyleBoxFlat Style(Color c, Color e, int w)
        {
            var box = UiTheme.Box(c, e, w, 12, 10);
            box.ContentMarginTop = 30; // room for the region caption
            return box;
        }
        b.AddThemeStyleboxOverride("normal", Style(bg, border, width));
        b.AddThemeStyleboxOverride("hover", Style(new Color("fbf2df"), room.CanFastTravel ? UiTheme.BrassLight : border, width + 1));
        b.AddThemeStyleboxOverride("pressed", Style(new Color("d9c194"), border, width + 1));
        b.AddThemeStyleboxOverride("focus", UiTheme.Box(new Color(0, 0, 0, 0), UiTheme.Focus, 4, 14, 0));
        if (!room.Visited) b.AddThemeColorOverride("font_color", UiTheme.InkSoft);
        string tip = room.IsCurrent ? Ui.T("ui.map.you_are_here")
            : room.CanFastTravel ? Ui.T("ui.map.travel_to", ("place", name))
            : !room.Visited ? Ui.T("ui.map.unvisited") : Ui.T("ui.map.unreachable");
        if (room.IsAnchor) tip += " · " + Ui.T("ui.map.node_tooltip");
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
        // Region (district) caption: region.<district>.name (ISSUES TEXT-02 / UI-02).
        string district = GameRuntime.Instance.Content.GetRoom(room.RoomId).District;
        var region = Ui.Label(TextService.Get("region." + district + ".name", district).ToUpperInvariant(), "CaptionLabel");
        region.AddThemeFontSizeOverride("font_size", 16);
        region.AddThemeFontOverride("font", UiTheme.BodyBold);
        region.Position = new Vector2(14, 6);
        region.Size = new Vector2(NodeW - 60, 22);
        region.ClipText = true;
        b.AddChild(region);
        if (room.IsAnchor)
        {
            var clock = new Glyph(GlyphKind.Clock, 34, UiTheme.Accent) { Position = new Vector2(NodeW - 40, 4) };
            b.AddChild(clock);
        }
        if (room.IsCurrent)
        {
            var here = Ui.Label(Ui.T("ui.map.you_are_here"), "CaptionLabel");
            here.AddThemeColorOverride("font_color", UiTheme.Cream);
            var tag = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore };
            tag.AddThemeStyleboxOverride("panel", UiTheme.Box(UiTheme.Accent, UiTheme.Accent, 0, 8, 4));
            here.AddThemeFontSizeOverride("font_size", 19);
            tag.AddChild(here);
            tag.Position = new Vector2(NodeW - 84, NodeH - 16);
            b.AddChild(tag);
            CurrentNode = b;
        }
        nodes[id] = b;
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        if (sheet is null) return;
        var game = GameRuntime.Instance;
        foreach (var (from, to, open, travel) in edges)
        {
            if (!nodes.TryGetValue(from, out var a) || !nodes.TryGetValue(to, out var b)) continue;
            var pa = a.Position + a.Size / 2;
            var pb = b.Position + b.Size / 2;
            var color = open ? new Color(UiTheme.Ink, 0.75f) : new Color(UiTheme.Muted, 0.6f);
            float width = open ? 4 : 3;
            if (travel == "walk") DrawLine(pa, pb, color, width, true);
            else DrawDashedLine(pa, pb, open ? UiTheme.Accent : color, width, 14, true);
        }
    }
}
