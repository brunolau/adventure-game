using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Game.PlayerInput;
using LastBell.Game.Presentation;
using LastBell.Game.Runtime;
using LastBell.Game.World;

namespace LastBell.Game.Diagnostics;

/// <summary>
/// Debug / QA harness driven by user command-line arguments after "--" (see src/game/README.md):
/// <c>--room &lt;id&gt;</c>, <c>--replay &lt;n&gt;</c>, <c>--play &lt;n&gt;</c> (walkthrough actions up to step n through the input path),
/// <c>--act &lt;actionId&gt;</c> (repeatable),
/// <c>--screenshot &lt;path.png&gt;</c>, <c>--frames &lt;k&gt;</c>, <c>--interval &lt;ms&gt;</c>, <c>--wait &lt;ms&gt;</c>,
/// <c>--input key:Inventory|select:ITEM|portal:YEAR|click:x,y|rclick:x,y|hover:x,y|wait:ms|mouse:x,y|rmouse:x,y|keyev:Space</c> (repeatable, in order;
/// <c>mouse</c>/<c>rmouse</c>/<c>keyev</c> inject real input events through Godot's pipeline, GUI first),
/// <c>--acceptance</c> (prologue input-rule checks, see PrologueAcceptance.cs), <c>--labels</c>, <c>--dev</c>, <c>--lines</c>, <c>--fast-text</c>, <c>--skip-lines</c>, <c>--quit-after &lt;s&gt;</c>, <c>--autosave</c>.
/// It never grants items: replays go through Core rules and acts through the normal input path
/// (resolver, walking, re-resolve on arrival, commit). Autosave is off unless <c>--autosave</c>.
/// Prints <c>HARNESS ...</c> lines to stdout for scripts.
/// </summary>
public partial class DebugHarness : Node
{
    private readonly Dictionary<string, List<string>> args = new(StringComparer.Ordinal);

    /// <summary>Parses OS.GetCmdlineUserArgs(); null when no harness flag is present.</summary>
    public static DebugHarness? FromCommandLine()
    {
        var raw = OS.GetCmdlineUserArgs();
        if (raw.Length == 0) return null;
        var harness = new DebugHarness { Name = "DebugHarness" };
        string? key = null;
        foreach (var token in raw)
        {
            if (token.StartsWith("--"))
            {
                var parts = token[2..].Split('=', 2);
                key = parts[0];
                if (!harness.args.ContainsKey(key)) harness.args[key] = new List<string>();
                if (parts.Length == 2)
                {
                    harness.args[key].Add(parts[1]);
                    key = null;
                }
                continue;
            }
            if (key is not null) harness.args[key].Add(token);
        }
        return harness.args.Count == 0 ? null : harness;
    }

    private bool Has(string key) => args.ContainsKey(key);

    private string? Get(string key) => args.TryGetValue(key, out var v) && v.Count > 0 ? v[^1] : null;

    private double GetNumber(string key, double fallback) =>
        Get(key) is { } s && double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out var d) ? d : fallback;

    private static void Log(string message) => GD.Print("HARNESS " + message);

    /// <inheritdoc />
    public override void _Ready()
    {
        ProcessMode = ProcessModeEnum.Always;
        _ = Run();
    }

    private async Task Run()
    {
        var game = GameRuntime.Instance;
        game.AutosaveEnabled = Has("autosave");
        var stage = WorldStage.Instance!;
        if (Has("dev")) stage.DevOverlay = true;
        if (Has("fast-text"))
        {
            PresentationSettings.TextCharsPerSecond = 0;
            PresentationSettings.AutoAdvanceBaseSeconds = 0.25f;
            PresentationSettings.AutoAdvancePerCharSeconds = 0.004f;
            PresentationSettings.CutsceneMinDurationScale = 0f;
        }
        if (Has("lines") && DialoguePresenter.Instance is { } presenter)
            presenter.LineShown += l => Log($"line {l.Line.LineId} [{l.Line.SpeakerId}] {l.Speaker}: {l.Text}");
        try
        {
            PrepareState(game);
            await WaitUntil(() => stage.IsSettled && stage.IsFadedIn, 10);
            if (Has("acceptance"))
            {
                await RunPrologueAcceptance();
                Quit(acceptanceFailures > 0 ? 1 : 0);
                return;
            }
            if (Has("labels") && !game.State.HotspotLabels)
            {
                await SkipLines(5);
                game.Update(GameRules.ToggleHotspots);
            }
            var acts = new List<string>();
            if (Get("play") is not null)
            {
                // The first n walkthrough actions through the normal input path (walk, click, travel).
                int skip = Get("replay") is not null ? (int)GetNumber("replay", 0) : 0;
                acts.AddRange(WalkthroughReplayer.LoadMainRoute().Skip(skip).Take((int)GetNumber("play", 0) - skip).Select(st => st.Action));
            }
            if (args.TryGetValue("act", out var list)) acts.AddRange(list);
            for (int i = 0; i < acts.Count; i++)
            {
                await SkipLines(15);
                await PerformAct(acts[i]);
            }
            if (Has("skip-lines")) await SkipLines(15);
            foreach (var input in args.TryGetValue("input", out var inputs) ? inputs : new List<string>()) await PerformInput(input);
            Log(Summary(game.State));
            if (Get("screenshot") is { } shot) await Screenshots(shot);
            if (Has("screenshot")) { Quit(0); return; }
            if (Get("quit-after") is not null)
            {
                await Seconds(GetNumber("quit-after", 1));
                Log(Summary(game.State));
                Quit(0);
            }
        }
        catch (Exception ex)
        {
            Log("ERROR " + ex.Message);
            GD.PushError(ex.ToString());
            if (Has("screenshot") || Has("quit-after") || Has("acceptance")) Quit(1);
        }
    }

    // ------------------------------------------------------------------ state preparation

    private void PrepareState(GameRuntime game)
    {
        var content = game.Content;
        bool replay = Get("replay") is not null;
        string? room = Get("room");
        if (!replay && room is null)
        {
            game.NewGame();
            Log("new game");
            return;
        }
        var state = content.InitialState;
        if (replay)
        {
            int n = (int)GetNumber("replay", 0);
            state = WalkthroughReplayer.Replay(content, state, n, Log);
            Log($"replayed {n} steps");
        }
        if (room is not null && room != state.Room)
        {
            var def = content.FindRoom(room) ?? throw new InvalidOperationException("unknown room " + room);
            // Dev jump: a state Core would never produce on its own (no travel gates checked).
            state = state with
            {
                Room = def.Id,
                Era = def.Era,
                Visited = state.Visited.Contains(def.Id) ? state.Visited : state.Visited.Add(def.Id),
                Mode = GameMode.World,
                ActiveLineId = null,
                PlaybackQueue = System.Collections.Immutable.ImmutableArray<string>.Empty,
                SelectedItem = null,
                RoomEntryDoneCount = state.Done.Length,
            };
            Log($"jumped to {def.Id}");
        }
        game.ReplaceState(state);
    }

    // ------------------------------------------------------------------ acts through the input path

    private async Task PerformAct(string actionId)
    {
        var game = GameRuntime.Instance;
        var content = game.Content;
        var action = content.FindAction(actionId) ?? throw new InvalidOperationException("unknown action " + actionId);
        if (game.State.IsDone(actionId)) throw new InvalidOperationException($"act {actionId}: already done");
        CancelSelectionLikeAPlayer();
        if (!action.IsInventoryAction && action.Room != game.State.Room) await TravelTo(action.Room);

        var controller = InteractionController.Instance!;
        if (action.SelectedItem is not null)
        {
            if (game.State.Mode != GameMode.Inventory) WorldInput.Dispatch(LogicalCommand.Inventory);
            WorldInput.Submit(new Hit.Item(action.SelectedItem), PointerButton.Left);
            if (game.State.SelectedItem != action.SelectedItem) throw new InvalidOperationException($"act {actionId}: cannot select {action.SelectedItem}");
        }
        Hit hit = action.IsCombine ? new Hit.Item(action.Target) : new Hit.Hotspot(action.Target);
        var expected = game.Session.Resolve(hit, PointerButton.Left);
        Log($"act {actionId}: {hit} resolves to {expected.GetType().Name}");
        WorldInput.Submit(hit, PointerButton.Left);
        if (action.IsTopic)
        {
            if (!await WaitUntil(() => game.State.Mode == GameMode.Dialogue && game.State.ActiveLineId is null, 20))
                throw new InvalidOperationException($"act {actionId}: topic menu did not open");
            await Frames(2);
            game.Commit(actionId); // what the topic menu does on choice
        }
        else if (action.Puzzle is not null)
        {
            if (!await WaitUntil(() => game.State.Mode == GameMode.Puzzle, 20))
                throw new InvalidOperationException($"act {actionId}: puzzle did not open");
            var result = game.SubmitPuzzle(content.GetPuzzle(action.Puzzle).Solution?.DeepClone());
            if (result is null || !result.Solved) throw new InvalidOperationException($"act {actionId}: puzzle not solved");
        }
        if (!await WaitUntil(() => game.State.IsDone(actionId), 20) || controller.HasPending)
            throw new InvalidOperationException($"act {actionId}: not committed (mode {game.State.Mode}, room {game.State.Room})");
        Log($"act {actionId}: committed");
    }

    /// <summary>
    /// One scripted input through the normal input path: <c>key:&lt;LogicalCommand&gt;</c>,
    /// <c>click:x,y</c>, <c>rclick:x,y</c>, <c>hover:x,y</c>, <c>wait:ms</c>.
    /// </summary>
    private async Task PerformInput(string input)
    {
        var parts = input.Split(':', 2);
        string kind = parts[0];
        string value = parts.Length > 1 ? parts[1] : "";
        Vector2 Point()
        {
            var xy = value.Split(',');
            return new Vector2(float.Parse(xy[0], CultureInfo.InvariantCulture), float.Parse(xy[1], CultureInfo.InvariantCulture));
        }
        switch (kind)
        {
            case "key" when Enum.TryParse<LogicalCommand>(value, true, out var command):
                WorldInput.Dispatch(command, GetViewport().GetMousePosition());
                break;
            case "click":
                WorldInput.Dispatch(LogicalCommand.Primary, Point());
                break;
            case "rclick":
                WorldInput.Dispatch(LogicalCommand.Secondary, Point());
                break;
            case "select":
                WorldInput.Submit(new Hit.Item(value), PointerButton.Left); // as the inventory UI does
                break;
            case "portal":
                // What the era chooser does on choice.
                GameRuntime.Instance.Update(st => Navigation.UsePortal(GameRuntime.Instance.Content, st, int.Parse(value, CultureInfo.InvariantCulture)));
                break;
            case "hover":
                Godot.Input.WarpMouse(GetTree().Root.GetFinalTransform() * Point());
                InteractionController.Instance?.PointerMoved(Point());
                break;
            case "wait":
                await Seconds(double.Parse(value, CultureInfo.InvariantCulture) / 1000.0);
                break;
            case "mouse" or "rmouse":
                // A real OS-style mouse event (motion, press, release) through Godot's input pipeline:
                // GUI controls get it first, then the InputRouter (_UnhandledInput).
                await RawMouse(Point(), kind == "mouse" ? MouseButton.Left : MouseButton.Right);
                break;
            case "keyev" when Enum.TryParse<Key>(value, true, out var key):
                // A real key press + release (InputMap actions, GUI shortcuts).
                foreach (bool pressed in new[] { true, false })
                {
                    Godot.Input.ParseInputEvent(new InputEventKey { Keycode = key, PhysicalKeycode = key, Pressed = pressed });
                    await Frames(1);
                }
                break;
            default:
                throw new InvalidOperationException("unknown --input " + input);
        }
        Log($"input {input} -> mode={GameRuntime.Instance.State.Mode} focus={InteractionController.Instance?.FocusedId ?? "-"} gui_focus={GetViewport().GuiGetFocusOwner()?.Name ?? "-"} labels={GameRuntime.Instance.State.HotspotLabels} room={GameRuntime.Instance.State.Room}");
        await Frames(2);
    }

    private async Task RawMouse(Vector2 canvasPoint, MouseButton button)
    {
        // Input events carry window pixels; the root viewport maps them back through its stretch transform.
        var viewportPoint = GetTree().Root.GetFinalTransform() * canvasPoint;
        Godot.Input.WarpMouse(viewportPoint);
        Godot.Input.ParseInputEvent(new InputEventMouseMotion { Position = viewportPoint, GlobalPosition = viewportPoint });
        await Frames(2);
        foreach (bool pressed in new[] { true, false })
        {
            Godot.Input.ParseInputEvent(new InputEventMouseButton
            {
                ButtonIndex = button, Pressed = pressed, Position = viewportPoint, GlobalPosition = viewportPoint,
                ButtonMask = pressed ? (button == MouseButton.Left ? MouseButtonMask.Left : MouseButtonMask.Right) : 0,
            });
            await Frames(1);
        }
    }

    private async Task TravelTo(string roomId)
    {
        var game = GameRuntime.Instance;
        var route = Navigation.FindRoute(game.Content, game.State, roomId) ?? throw new InvalidOperationException($"no route to {roomId}");
        foreach (var step in route)
        {
            await SkipLines(15);
            CancelSelectionLikeAPlayer();
            if (step.Kind == RouteStepKind.Exit) WorldInput.Submit(new Hit.Exit(step.ExitId!), PointerButton.Left);
            else game.Update(s => Navigation.UsePortal(game.Content, s, step.Year!.Value));
            if (!await WaitUntil(() => game.State.Room == step.To && WorldStage.Instance!.IsSettled && WorldStage.Instance.IsFadedIn, 30))
                throw new InvalidOperationException($"travel to {step.To} failed");
            Log($"travelled to {step.To}");
        }
        await SkipLines(15);
    }

    /// <summary>A kept (not consumed) item stays on the cursor after its action; a player right-clicks to drop it.</summary>
    private static void CancelSelectionLikeAPlayer()
    {
        var game = GameRuntime.Instance;
        if (game.State.Mode == GameMode.Inventory) WorldInput.Dispatch(LogicalCommand.Inventory);
        if (game.State.SelectedItem is not null) WorldInput.Submit(new Hit.Empty(), PointerButton.Right);
    }

    private async Task SkipLines(double timeout)
    {
        var game = GameRuntime.Instance;
        var deadline = Time.GetTicksMsec() + timeout * 1000;
        while (Time.GetTicksMsec() < deadline)
        {
            var stage = WorldStage.Instance!;
            bool hasPending = InteractionController.Instance?.HasPending ?? false;
            bool walking = stage.Current?.Hero.IsWalking ?? false;
            if (game.State.ActiveLineId is not null && DialoguePresenter.Instance?.IsShowingLine == true) DialoguePresenter.Instance.Skip();
            if (game.State.ActiveLineId is null && stage.IsSettled && stage.IsFadedIn && !hasPending && !walking && game.State.Mode is GameMode.World or GameMode.Inventory) return;
            await Frames(1);
        }
    }

    // ------------------------------------------------------------------ screenshots

    private async Task Screenshots(string path)
    {
        await Seconds(GetNumber("wait", 400) / 1000.0);
        int frames = Math.Max(1, (int)GetNumber("frames", 1));
        double interval = GetNumber("interval", 200) / 1000.0;
        for (int i = 0; i < frames; i++)
        {
            if (i > 0) await Seconds(interval);
            await ToSignal(RenderingServer.Singleton, RenderingServerInstance.SignalName.FramePostDraw);
            string file = frames == 1 ? path : NumberedPath(path, i);
            SaveViewport(file);
        }
    }

    private static string NumberedPath(string path, int index)
    {
        if (path.Contains("{n}")) return path.Replace("{n}", index.ToString("D2"));
        var dir = System.IO.Path.GetDirectoryName(path) ?? "";
        var name = System.IO.Path.GetFileNameWithoutExtension(path);
        var ext = System.IO.Path.GetExtension(path);
        return System.IO.Path.Combine(dir, $"{name}_{index:D2}{(ext.Length > 0 ? ext : ".png")}");
    }

    private void SaveViewport(string path)
    {
        var image = GetViewport().GetTexture()?.GetImage();
        if (image is null || image.IsEmpty())
        {
            Log("ERROR screenshot needs a rendering driver (do not pass --headless)");
            return;
        }
        if (image.GetWidth() != 1920 || image.GetHeight() != 1080) image.Resize(1920, 1080, Image.Interpolation.Lanczos);
        // Godot runs with the project folder (src/game) as working directory; relative paths are taken
        // from the repository root so README commands like build/screens/x.png land in <repo>/build.
        string repoRoot = System.IO.Path.GetFullPath(System.IO.Path.Combine(ProjectSettings.GlobalizePath("res://"), "..", ".."));
        string full = path.StartsWith("res://") || path.StartsWith("user://") ? path
            : System.IO.Path.IsPathRooted(path) ? System.IO.Path.GetFullPath(path) : System.IO.Path.GetFullPath(System.IO.Path.Combine(repoRoot, path));
        var dir = System.IO.Path.GetDirectoryName(full);
        if (!string.IsNullOrEmpty(dir) && !full.StartsWith("res://") && !full.StartsWith("user://")) System.IO.Directory.CreateDirectory(dir);
        var error = image.SavePng(full);
        Log(error == Error.Ok ? $"screenshot {full}" : $"ERROR screenshot {full}: {error}");
    }

    // ------------------------------------------------------------------ helpers

    private static string Summary(GameState s) =>
        $"state room={s.Room} era={s.Era} mode={s.Mode} done={s.Done.Length} last={(s.Done.Length > 0 ? s.Done[^1] : "-")} " +
        $"inventory=[{string.Join(",", s.Inventory)}] selected={s.SelectedItem ?? "-"} line={s.ActiveLineId ?? "-"} labels={s.HotspotLabels}";

    private async Task<bool> WaitUntil(Func<bool> condition, double timeoutSeconds)
    {
        var deadline = Time.GetTicksMsec() + timeoutSeconds * 1000;
        while (!condition())
        {
            if (Time.GetTicksMsec() > deadline) return false;
            await Frames(1);
        }
        return true;
    }

    private async Task Frames(int count)
    {
        for (int i = 0; i < count; i++) await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
    }

    private async Task Seconds(double seconds)
    {
        if (seconds <= 0) return;
        await ToSignal(GetTree().CreateTimer(seconds, true), SceneTreeTimer.SignalName.Timeout);
    }

    private void Quit(int code) => GetTree().Quit(code);
}
