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
/// car S02 -&gt; S51 is gone, and the map shows regions first, then the rooms of a region; another region is reached
/// only through its hub. Real Godot input only (RealInputDriver.cs). With <c>--travel-shots DIR</c> (windowed run
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

        // ---------------------------------------------------------------- TR03: map: regions first, another region only through its hub
        await KeyReal(Godot.Key.M);
        bool mapOpen = await WaitUntil(() => game.State.Mode == GameMode.Map, 5);
        await Frames(8);
        var map = Descendants<MapScreen>(UiRoot.Instance!).FirstOrDefault();
        var graph = map is null ? null : Descendants<MapGraph>(map).FirstOrDefault();
        bool regionsFirst = map is not null && map.OpenRegionId is null && graph is { ShowsRegions: true } && graph.Nodes.ContainsKey("Chorvátsky Grob") && graph.Nodes.ContainsKey("Dúbravka");
        await TravelShot("map_regions_2020", 0.3);
        bool openedGrob = graph is not null && graph.Nodes.TryGetValue("Chorvátsky Grob", out var grobCard) && await ClickControl(grobCard, "map region Chorvátsky Grob");
        await Frames(6);
        bool roomsShown = map?.OpenRegionId == "Chorvátsky Grob" && graph is { ShowsRegions: false } && graph.Nodes.ContainsKey("S07") && !graph.Nodes.ContainsKey("S51");
        await TravelShot("map_region_Chorvatsky_Grob", 0.3);
        var sheet = LastBell.Core.Views.ViewBuilder.Map(content, game.State).Single(e => e.Year == 2020);
        bool hubOnly = sheet.Rooms.Where(r => r.RegionId == "Chorvátsky Grob" && r.Visited).All(r => r.CanFastTravel == r.IsHub);
        string here = game.State.Room;
        bool nonHubStays = true;
        if (graph is not null && graph.Nodes.TryGetValue("S03", out var s03)) { await ClickControl(s03, "map node S03 (not a hub)"); await Frames(6); nonHubStays = game.State.Room == here && game.State.Mode == GameMode.Map; }
        bool viaHub = graph is not null && graph.Nodes.TryGetValue("S07", out var s07) && await ClickControl(s07, "map node S07 (hub)") &&
                      await WaitUntil(() => game.State.Room == "S07" && WorldStage.Instance!.IsSettled && WorldStage.Instance.IsFadedIn, 30);
        string cardBack = WorldStage.Instance!.LastTransportCard;
        await WaitLinesReal(30);
        Check("TR03_map_regions_first_hub_only_fast_travel", mapOpen && regionsFirst && openedGrob && roomsShown && hubOnly && nonHubStays && viaHub && cardBack.Contains("Grob"),
              $"open={mapOpen} regions_first={regionsFirst} rooms_view={roomsShown} hub_only={hubOnly} non_hub_stays={nonHubStays} via_hub={viaHub} card='{cardBack}'");
        if (DialoguePresenter.Instance is { } p2) p2.LineShown -= OnLine;

        // Evidence only (windowed --travel-shots): the 1995 sheet, its regions and the rooms of one region.
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
                await TravelShot("map_regions_1995", 0.3);
                if (Descendants<MapGraph>(screen).FirstOrDefault()?.Nodes.TryGetValue("Staré Mesto", out var sm) == true)
                {
                    await ClickControl(sm, "map region Staré Mesto");
                    await Frames(6);
                    await TravelShot("map_region_Stare_Mesto_1995", 0.3);
                }
            }
        }
        if (game.State.Mode == GameMode.Map) await KeyReal(Godot.Key.Escape);
    }
}
