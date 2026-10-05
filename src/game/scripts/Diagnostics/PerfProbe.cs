using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Godot;
using LastBell.Core.State;
using LastBell.Game.Runtime;
using LastBell.Game.World;

namespace LastBell.Game.Diagnostics;

/// <summary>
/// Release-engineering probe (flag <c>--perf [n]</c>, default 20; docs/BUILD.md "Performance"): after the
/// first room is on screen it walks <c>n</c> rooms through their exits (dev jumps to the exit's room, gates
/// not checked; unvisited neighbours first, then unvisited rooms of the era, then of the next era), waits <c>--perf-dwell</c> seconds (default 1.5) in each room like
/// a player would, and logs per hop the synchronous room build time, the longest frame and the whole
/// transition (fade out + build + fade in). At the end it logs the process and Godot memory.
/// <c>--no-preload</c> turns the neighbour preloader (World/RoomPreloader.cs) off for comparison.
/// Output lines start with <c>HARNESS perf</c>.
/// </summary>
public partial class DebugHarness
{
    private async Task RunPerf()
    {
        var game = GameRuntime.Instance;
        var stage = WorldStage.Instance!;
        int count = (int)GetNumber("perf", 20);
        double dwell = GetNumber("perf-dwell", 1.5);
        Log($"perf startup first_room={game.State.Room} settled_ms={Time.GetTicksMsec()} build_ms={stage.LastBuildMs:F1} preload={RoomPreloader.Enabled}");
        Log("perf " + MemoryLine("start"));
        var visited = new HashSet<string>(StringComparer.Ordinal) { game.State.Room };
        var builds = new List<double>();
        var worstFrames = new List<double>();
        var totals = new List<double>();
        var random = new Random(7);
        var dwellWorst = new List<double>();
        for (int i = 0; i < count; i++)
        {
            // In the room: frames while the preloader works in the background (a stutter here would be visible).
            ulong dwellEnd = Time.GetTicksUsec() + (ulong)(dwell * 1e6);
            ulong prev = Time.GetTicksUsec();
            double inRoomWorst = 0;
            while (Time.GetTicksUsec() < dwellEnd)
            {
                await Frames(1);
                ulong now = Time.GetTicksUsec();
                inRoomWorst = Math.Max(inRoomWorst, (now - prev) / 1000.0);
                prev = now;
            }
            dwellWorst.Add(inRoomWorst);
            var current = stage.Current!;
            var exits = current.View.Exits.Select(e => e.To).Where(r => r != current.RoomId && game.Content.FindRoom(r) is not null).Distinct().ToList();
            string? next = exits.FirstOrDefault(r => !visited.Contains(r));
            next ??= game.Content.Rooms.Where(r => r.Era == current.View.Era && !visited.Contains(r.Id)).Select(r => r.Id).FirstOrDefault();
            next ??= game.Content.Rooms.Where(r => !visited.Contains(r.Id)).Select(r => r.Id).FirstOrDefault(); // next era (era card)
            next ??= exits.Count > 0 ? exits[random.Next(exits.Count)] : null;
            if (next is null) break;
            bool neighbour = exits.Contains(next);
            visited.Add(next);
            int builtBefore = stage.RoomsBuilt;
            ulong start = Time.GetTicksUsec();
            ulong last = start;
            double worst = 0;
            JumpTo(game, next);
            var deadline = Time.GetTicksMsec() + 15000;
            while (!(stage.RoomsBuilt > builtBefore && stage.IsSettled && stage.IsFadedIn && stage.Current?.RoomId == next))
            {
                if (Time.GetTicksMsec() > deadline) { Log($"perf ERROR {next} did not settle"); break; }
                await Frames(1);
                ulong now = Time.GetTicksUsec();
                worst = Math.Max(worst, (now - last) / 1000.0);
                last = now;
            }
            double total = (Time.GetTicksUsec() - start) / 1000.0;
            builds.Add(stage.LastBuildMs);
            worstFrames.Add(worst);
            totals.Add(total);
            Log($"perf hop {i + 1:D2} {current.RoomId}->{next} neighbour={neighbour} build_ms={stage.LastBuildMs:F1} worst_frame_ms={worst:F1} transition_ms={total:F0} worst_frame_in_previous_room_ms={inRoomWorst:F1}");
        }
        await Seconds(1);
        if (builds.Count > 0)
        {
            static string Stats(List<double> v) => $"median={Median(v):F1} max={v.Max():F1} mean={v.Average():F1}";
            Log($"perf summary rooms={builds.Count} build_ms {Stats(builds)} | worst_frame_ms {Stats(worstFrames)} | transition_ms {Stats(totals)} | in_room_worst_frame_ms {(dwellWorst.Count > 0 ? Stats(dwellWorst) : "-")} | preloaded={RoomPreloader.Instance?.Loaded ?? 0}");
        }
        Log("perf " + MemoryLine($"after_{builds.Count}_rooms"));
    }

    private static double Median(List<double> values)
    {
        var sorted = values.OrderBy(v => v).ToList();
        int mid = sorted.Count / 2;
        return sorted.Count % 2 == 1 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
    }

    private static string MemoryLine(string label)
    {
        using var process = System.Diagnostics.Process.GetCurrentProcess();
        process.Refresh();
        double mb(double bytes) => bytes / (1024.0 * 1024.0);
        return $"memory {label} working_set_mb={mb(process.WorkingSet64):F0} private_mb={mb(process.PrivateMemorySize64):F0} " +
               $"godot_static_mb={mb(OS.GetStaticMemoryUsage()):F0} texture_mem_mb={mb(Performance.GetMonitor(Performance.Monitor.RenderTextureMemUsed)):F0} " +
               $"video_mem_mb={mb(Performance.GetMonitor(Performance.Monitor.RenderVideoMemUsed)):F0} managed_mb={mb(GC.GetTotalMemory(false)):F0} " +
               $"resources={Performance.GetMonitor(Performance.Monitor.ObjectResourceCount):F0}";
    }

    /// <summary>Dev jump to a room (as <c>--room</c>, no gates checked); the world stage runs the normal transition.</summary>
    private static void JumpTo(GameRuntime game, string roomId)
    {
        var def = game.Content.FindRoom(roomId)!;
        game.Update(state => state with
        {
            Room = def.Id,
            Era = def.Era,
            Visited = state.Visited.Contains(def.Id) ? state.Visited : state.Visited.Add(def.Id),
            Mode = GameMode.World,
            ActiveLineId = null,
            PlaybackQueue = System.Collections.Immutable.ImmutableArray<string>.Empty,
            SelectedItem = null,
            RoomEntryDoneCount = state.Done.Length,
        });
    }
}
