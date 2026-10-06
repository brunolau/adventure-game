using System;
using System.Linq;
using System.Threading.Tasks;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Game.Presentation;
using LastBell.Game.Runtime;
using LastBell.Game.UI;
using LastBell.Game.UI.Hud;
using LastBell.Game.UI.Map;
using LastBell.Game.World;

namespace LastBell.Game.Diagnostics;

/// <summary>
/// Acceptance checks of the travel overlay (owner request 2026-10-06, DECISIONS "Control changes" item 7): Dúbravka
/// 2020 is reached by bus from the Čierna Voda bus stop (S07 &lt;-&gt; S51, first-ride lines, transport card), the old
/// car S02 -&gt; S51 is gone, and the map shows every region of the era on one screen: one click on any visited room
/// travels there, with the transport card of the ride into another region (owner override 2026-10-06, control change 8).
/// NAV04: the inventory is "Inventár" and a selected item draws no outline on its valid targets (control changes 10, 11). Real Godot input only (RealInputDriver.cs). With <c>--travel-shots DIR</c> (windowed run
/// through tools/qa_godot.py) it saves the evidence frames (build/screens/travel/).
/// </summary>
public partial class DebugHarness
{
    /// <summary>A real mouse motion to a canvas point (hover label and cursor shape), no click.</summary>
    private async Task MoveMouseReal(Vector2 canvasPoint)
    {
        var vp = GetTree().Root.GetFinalTransform() * canvasPoint;
        QaWindow.WarpMouse(vp);
        Godot.Input.ParseInputEvent(new InputEventMouseMotion { Position = vp, GlobalPosition = vp });
        await Frames(2);
    }

    private int travelShots;

    /// <summary>Saves an evidence frame to <c>--travel-shots DIR</c> (windowed runs only).</summary>
    private async Task TravelShot(string name, double delay = 0.25)
    {
        string? dirArg = Get("travel-shots");
        if (dirArg is null || DisplayServer.GetName() == "headless") return;
        await Seconds(delay);
        await ToSignal(RenderingServer.Singleton, RenderingServerInstance.SignalName.FramePostDraw);
        var image = GetViewport().GetTexture()?.GetImage();
        if (image is null || image.IsEmpty()) return;
        if (image.GetWidth() != 1920 || image.GetHeight() != 1080) image.Resize(1920, 1080, Image.Interpolation.Lanczos);
        string repoRoot = System.IO.Path.GetFullPath(System.IO.Path.Combine(ProjectSettings.GlobalizePath("res://"), "..", ".."));
        string dir = System.IO.Path.IsPathRooted(dirArg) ? dirArg : System.IO.Path.Combine(repoRoot, dirArg);
        System.IO.Directory.CreateDirectory(dir);
        image.SavePng(System.IO.Path.Combine(dir, $"{++travelShots:D2}_{name}.png"));
    }

    private async Task RunTravelChecks()
    {
        var game = GameRuntime.Instance;
        var content = game.Content;
        var seenLines = new System.Collections.Generic.List<string>();
        void OnLine(LastBell.Game.Hooks.SubtitleLine l) => seenLines.Add(l.Line.LineId);

        // ---------------------------------------------------------------- TR01: no car from the street, a bus at the bus stop
        await Prepare("D01"); // after C01: Mira sends Adam to Dúbravka 2020
        bool noCar = !content.GetRoom("S02").Exits.Any(e => e.To == "S51") && !content.GetRoom("S51").Exits.Any(e => e.To == "S02");
        // Core travel to the bus stop (the walk there is covered by AT11 / --play-all); the ride itself is real input.
        var atStop = game.State;
        foreach (var step in Navigation.FindRoute(content, atStop, "S07")!) atStop = Playback.FinishAll(content, Navigation.ApplyStep(content, atStop, step));
        game.ReplaceState(atStop);
        await Settle();
        await WaitLinesReal(20);
        var bus = content.GetRoom("S07").Exits.Single(e => e.To == "S51");
        bool exitShown = CurrentRoom.TryGetTarget(bus.Id, out var busTarget);
        var cursor = exitShown ? CursorLayer.KindFor(CurrentRoom, new LastBell.Core.Rules.Hit.Exit(bus.Id)) : CursorKind.Pointer;
        string hover = TextService.Get(game.Session.Hover(new LastBell.Core.Rules.Hit.Exit(bus.Id)).Name);
        if (exitShown && await FindClickPoint(bus.Id) is { } point) { await MoveMouseReal(point); await Frames(6); await TravelShot("S07_bus_exit_hover"); }
        Check("TR01_bus_exit_at_the_Cierna_Voda_stop", noCar && exitShown && bus.Travel == "bus" && cursor.ToString().StartsWith("Exit", StringComparison.Ordinal) &&
              hover == TextService.Get("exit." + bus.Id + ".label"),
              $"no_car={noCar} exit_shown={exitShown} travel={bus.Travel} cursor={cursor} label='{hover}'");

        // ---------------------------------------------------------------- TR02: first ride: lines in S07, transport card, arrival in S51
        if (DialoguePresenter.Instance is { } presenter) presenter.LineShown += OnLine;
        bool clicked = await ClickTarget(bus.Id);
        string input = "real";
        if (!await WaitUntil(() => game.State.Room == "S51", 8) && game.State.Room == "S07")
        {
            // Windowed QA runs (hidden window, 2026-10-06) currently miss raw clicks on world targets (also S01 -> S02,
            // outside the travel overlay; the hero walks to a wrong floor point). Take the keyboard path instead:
            // Tab focus on the exit + Enter, still real Godot input.
            Log("WARN TR02: the raw click on the bus exit did not land; using Tab + Enter");
            input = "keyboard";
            if (await FocusByTab(bus.Id)) await KeyReal(Godot.Key.Enter);
        }
        bool rideLines = await WaitUntil(() => seenLines.Any(id => id.StartsWith("travel.S07.to_S51.first.", StringComparison.Ordinal)), 15);
        bool oldRoomDuringRide = WorldStage.Instance!.Current?.RoomId == "S07";
        if (rideLines) await TravelShot("S07_first_ride_line", 0.3);
        bool card = await WaitUntil(() => WorldStage.Instance!.Transitioning && WorldStage.Instance.LastTransportCard.Length > 0, 30);
        if (card) await TravelShot("transport_card_bus", 0.55);
        bool arrived = await WaitUntil(() => game.State.Room == "S51" && WorldStage.Instance!.IsSettled && WorldStage.Instance.IsFadedIn, 30);
        await WaitLinesReal(30);
        if (arrived) await TravelShot("S51_after_bus", 0.3);
        int rides = seenLines.Count(id => id.StartsWith("travel.S07.to_S51.first.", StringComparison.Ordinal));
        Check("TR02_first_ride_lines_then_card_then_S51", clicked && rideLines && oldRoomDuringRide && card && arrived && rides == content.FirstRideLines(bus.Id).Count &&
              game.State.JournalSeen.Contains(Navigation.FirstRideKey(bus.Id)) && WorldStage.Instance!.LastTransportCard.Contains(TextService.Get("ui.travel.bus")),
              $"clicked={clicked} input={input} lines={rides} old_room_during_ride={oldRoomDuringRide} card='{WorldStage.Instance!.LastTransportCard}' arrived={arrived}");

        // ---------------------------------------------------------------- TR03: map: every region on one screen, one click to any visited room
        // Owner override 2026-10-06 (DECISIONS control change 8; replaced the regions-first view and the hub rule of item 7):
        // one click on a discovered room of another region travels there directly, with the transport card of the ride.
        await KeyReal(Godot.Key.M);
        bool mapOpen = await WaitUntil(() => game.State.Mode == GameMode.Map, 5);
        await Frames(8);
        var map = Descendants<MapScreen>(UiRoot.Instance!).FirstOrDefault();
        bool allRegions = map is not null && map.RegionIds.Contains("Chorvátsky Grob") && map.RegionIds.Contains("Dúbravka") &&
                          map.Section("Chorvátsky Grob")?.IsVisibleInTree() == true && map.Section("Dúbravka")?.IsVisibleInTree() == true;
        var s03 = map?.RoomNode("S03");
        bool sameScreen = allRegions && s03 is not null && s03.IsVisibleInTree() && map!.RoomNode("S51") is { } here51 && here51.IsVisibleInTree();
        await TravelShot("map_2020_all_regions_one_screen", 0.3);
        var sheet = LastBell.Core.Views.ViewBuilder.Map(content, game.State).Single(e => e.Year == 2020);
        // Every visited room of the era can be travelled to, hub or not; a room never visited cannot (the first trip is physical).
        bool direct = sheet.Rooms.Where(r => r.Visited && !r.IsCurrent).All(r => r.CanFastTravel) &&
                      sheet.Rooms.Where(r => !r.Visited).All(r => !r.CanFastTravel) && !content.IsHub("S03");
        // Undiscovered rooms are not drawn (the region header counts them): S52 waits for the first walk from the stop.
        bool unvisitedStays = game.State.Visited.Contains("S52") || map?.RoomNode("S52") is null;
        bool clickedS03 = s03 is not null && await ClickControl(s03, "map node S03 (another region, not a hub)");
        bool cardSeen = await WaitUntil(() => WorldStage.Instance!.Transitioning && WorldStage.Instance.LastTransportCard.Contains("Grob"), 20);
        if (cardSeen) await TravelShot("fast_travel_transport_card_bus", 0.55);
        bool oneClick = clickedS03 && await WaitUntil(() => game.State.Room == "S03" && WorldStage.Instance!.IsSettled && WorldStage.Instance.IsFadedIn, 30);
        string cardBack = WorldStage.Instance!.LastTransportCard;
        await WaitLinesReal(30);
        if (oneClick) await TravelShot("S03_after_one_click", 0.3);
        Check("TR03_map_one_screen_one_click_to_any_visited_room", mapOpen && sameScreen && direct && unvisitedStays && oneClick &&
              cardBack.Contains("Grob") && cardBack.Contains(TextService.Get("ui.travel.bus")),
              $"open={mapOpen} one_screen={sameScreen} direct_flags={direct} unvisited_hidden={unvisitedStays} one_click={oneClick} card='{cardBack}'");
        if (DialoguePresenter.Instance is { } p2) p2.LineShown -= OnLine;

        // Evidence only (windowed --travel-shots): the 1995 sheet with all its regions.
        if (Get("travel-shots") is not null && DisplayServer.GetName() != "headless")
        {
            await KeyReal(Godot.Key.M);
            await WaitUntil(() => game.State.Mode == GameMode.Map, 5);
            await Frames(6);
            var screen = Descendants<MapScreen>(UiRoot.Instance!).FirstOrDefault();
            string tab = TextService.Ui("ui.map.sheet_year", ("year", TextService.EraYear(1995)));
            if (screen is not null && Descendants<Button>(screen).FirstOrDefault(b => b.IsVisibleInTree() && b.Text == tab) is { } t1995)
            {
                await ClickControl(t1995, "map tab 1995");
                await Frames(6);
                await TravelShot("map_1995_all_regions", 0.3);
            }
        }
        if (game.State.Mode == GameMode.Map) await KeyReal(Godot.Key.Escape);

        // ---------------------------------------------------------------- NAV04: "Inventár", and no outline on the valid targets of a selected item
        // Owner 2026-10-06 (DECISIONS control changes 10 and 11): the panel is "Inventár" (no "brašna inside the brašna"); with an
        // item selected the valid targets show only on hover (the item-action label at the cursor) and while Space is held.
        await Prepare("B06");
        // Core travel to the radio room (the walk is covered by AT03 / --play-all; hidden-window runs miss raw world clicks).
        var toRadio = game.State;
        foreach (var step in Navigation.FindRoute(content, toRadio, "S16")!) toRadio = Playback.FinishAll(content, Navigation.ApplyStep(content, toRadio, step));
        game.ReplaceState(toRadio);
        await Settle();
        await WaitLinesReal(20);
        await OpenDrawerReal();
        string invTitle = TextService.Ui("ui.inventory.title");
        bool titleShown = Descendants<Label>(UiRoot.Instance!).Any(l => l.IsVisibleInTree() && l.Text == invTitle);
        await TravelShot("inventory_title", 0.3);
        await CloseDrawerReal();
        await SelectItemReal("BELT_NEW", keepDrawerOpen: false);
        var room = CurrentRoom;
        var floor = new Vector2(960, 1000);
        await MoveMouseReal(floor);
        await Frames(4);
        int outlinesIdle = InteractionController.Instance?.FocusedId is null ? room.Labels.OutlinesDrawn : -1;
        await TravelShot("item_selected_no_outline", 0.3);
        string hoverAction = "";
        if (await FindClickPoint("S16.deck") is { } deck)
        {
            await MoveMouseReal(deck);
            await Frames(6);
            hoverAction = UiRoot.Instance!.HoverLabel.ShownAction;
            await TravelShot("item_hover_label_on_valid_target", 0.2);
        }
        int outlinesHover = room.Labels.OutlinesDrawn;
        await MoveMouseReal(floor);
        await KeyEdge(Godot.Key.Space, true);
        await Frames(4);
        var marked = room.Labels.MarkedIds.ToList();
        var valid = room.Targets.Where(t => t.ValidForSelectedItem).Select(t => t.Id).ToList();
        await TravelShot("item_space_markers_valid_only", 0.2);
        await KeyEdge(Godot.Key.Space, false);
        await Frames(2);
        Check("NAV04_inventar_title_and_no_item_outline", titleShown && invTitle == "Inventár" && outlinesIdle == 0 && outlinesHover == 0 && hoverAction.Length > 0 &&
              marked.Count > 0 && marked.OrderBy(x => x, StringComparer.Ordinal).SequenceEqual(valid.OrderBy(x => x, StringComparer.Ordinal)),
              $"title='{invTitle}' shown={titleShown} outlines_idle={outlinesIdle} outlines_hover={outlinesHover} hover_action='{hoverAction}' marked=[{string.Join(",", marked)}] valid=[{string.Join(",", valid)}]");
        await DropSelectionReal();
    }
}
