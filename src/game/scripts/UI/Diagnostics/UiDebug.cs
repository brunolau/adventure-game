using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Game.Hooks;
using LastBell.Game.PlayerInput;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Settings;
using LastBell.Game.World;

namespace LastBell.Game.UI.Diagnostics;

/// <summary>
/// QA helper for UI screenshots, active only with debug-harness arguments (after "--"). It waits
/// until the harness has prepared the state and the room is settled, then opens a screen:
/// <c>--ui main_menu|pause|settings[:tab]|save|load|load_corrupt|journal[:tab]|map|hints|inventory|
/// puzzle:&lt;actionId&gt;|credits|ending|help|portal|talk|cutscene:&lt;CS&gt;|era:&lt;year&gt;|tips|select:&lt;ITEM&gt;|
/// difficulty:&lt;easy|standard|hard&gt;|idle:&lt;seconds&gt;|new_game|pick:&lt;difficulty&gt;</c>
/// (repeatable, applied in order, 0.4 s apart), <c>--ui-scale &lt;100..200&gt;</c> (HUD scale for this run,
/// not saved), <c>--ui-reduced-motion</c>, <c>--ui-contrast</c>. Opens screens the way a player would
/// (logical commands, Core overlay functions); dev-only shortcuts are marked.
/// </summary>
public partial class UiDebug : Node
{
    private readonly List<string> steps = new();
    private double settleTime;
    private double gap;
    private bool started;

    /// <inheritdoc />
    public override void _Ready()
    {
        ProcessMode = ProcessModeEnum.Always;
        var args = LaunchArgs.User;
        for (int i = 0; i < args.Length; i++)
        {
            string a = args[i];
            string? Next() => i + 1 < args.Length && !args[i + 1].StartsWith("--") ? args[++i] : null;
            if (a == "--ui" && Next() is { } step) steps.Add(step);
            else if (a.StartsWith("--ui=")) steps.Add(a[5..]);
            else if (a == "--ui-scale" && Next() is { } scale && int.TryParse(scale, NumberStyles.Integer, CultureInfo.InvariantCulture, out var pct))
            {
                UiSettings.HudScalePercent = Math.Clamp(pct, 100, 200);
                UiSettings.Apply(keepTextTiming: true, applyWindow: false);
            }
            else if (a == "--ui-reduced-motion") { UiSettings.ReducedMotion = true; UiSettings.Apply(true, false); }
            else if (a == "--ui-contrast") { UiSettings.HighContrastLabels = true; UiSettings.Apply(true, false); }
        }
        if (steps.Count == 0) SetProcess(false);
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        var game = GameRuntime.Instance;
        var stage = WorldStage.Instance;
        if (!started)
        {
            bool calm = stage is { IsSettled: true, IsFadedIn: true } && game.State.Mode is GameMode.World or GameMode.Inventory && game.State.ActiveLineId is null &&
                        !(InteractionController.Instance?.HasPending ?? false);
            settleTime = calm ? settleTime + delta : 0;
            if (settleTime < 0.6) return;
            started = true;
        }
        gap -= delta;
        if (gap > 0 || steps.Count == 0) return;
        string step = steps[0];
        steps.RemoveAt(0);
        gap = 0.4;
        if (step.StartsWith("wait:") && double.TryParse(step[5..], NumberStyles.Float, CultureInfo.InvariantCulture, out var ms))
        {
            gap = ms / 1000.0;
            return;
        }
        try
        {
            Apply(step);
            GD.Print("UIDEBUG " + step);
        }
        catch (Exception ex)
        {
            GD.Print("UIDEBUG ERROR " + step + ": " + ex.Message);
        }
        if (steps.Count == 0) SetProcess(false);
    }

    private static void Apply(string step)
    {
        var game = GameRuntime.Instance;
        var root = UiRoot.Instance!;
        var parts = step.Split(':', 2);
        string arg = parts.Length > 1 ? parts[1] : "";
        switch (parts[0])
        {
            case "main_menu": root.ShowMainMenu(); break;
            case "pause": game.Update(s => GameRules.OpenOverlay(s, GameMode.Pause)); break;
            case "settings":
                if (arg.Length > 0) LastBell.Game.UI.Menus.SettingsScreen.LastTab = int.Parse(arg, CultureInfo.InvariantCulture);
                root.OpenSettings();
                break;
            case "save": root.OpenSaveLoad(true); break;
            case "load": root.OpenSaveLoad(false); break;
            case "load_corrupt":
                // Dev: writes a damaged file into slot 8, then opens the load screen (AT18).
                DirAccess.MakeDirRecursiveAbsolute(GameRuntime.SaveDirectory);
                using (var f = Godot.FileAccess.Open(GameRuntime.SlotPath("slot8"), Godot.FileAccess.ModeFlags.Write)) f?.StoreString("{\"schema_version\":1,\"room\":\"S01\",\"inventory\":[\"NOPE\"]}");
                root.OpenSaveLoad(false);
                break;
            case "try_load_corrupt": game.Load("slot8"); break;
            case "journal":
                if (arg.Length > 0) LastBell.Game.UI.Journal.JournalScreen.LastTab = int.Parse(arg, CultureInfo.InvariantCulture);
                WorldInput.Dispatch(LogicalCommand.Journal);
                break;
            case "map": WorldInput.Dispatch(LogicalCommand.Map); break;
            case "hints":
                // Over an open puzzle: the modal's own hint button (the H key does not reach the world there).
                if (game.State.Mode == GameMode.Puzzle && game.OpenPuzzleActionId is { } pz) root.OpenHints(game.Content.GetQuestOf(pz).Id);
                else WorldInput.Dispatch(LogicalCommand.Hint);
                break;
            case "reveal_hint":
                if (Quests.CurrentMainQuest(game.Content, game.State) is { } q) game.Update(s => Hints.RevealNext(game.Content, s, q.Id, game.SecondsWithoutProgress));
                break;
            case "difficulty":
                // The running game's difficulty, as the settings row sets it (easy|standard|hard).
                game.SetDifficulty(LastBell.Core.Save.SaveCodec.ParseDifficulty(arg) ?? throw new InvalidOperationException("unknown difficulty " + arg));
                break;
            case "idle":
                // Dev: seconds of play without progress (Hard's hint wait), e.g. idle:170 or idle:200.
                game.SecondsWithoutProgress = double.Parse(arg, CultureInfo.InvariantCulture);
                break;
            case "new_game": root.OpenNewGame(); break; // the difficulty picker of New Game
            case "pick":
                root.DifficultyPickerView.Select(LastBell.Core.Save.SaveCodec.ParseDifficulty(arg) ?? throw new InvalidOperationException("unknown difficulty " + arg));
                break;
            case "inventory": WorldInput.Dispatch(LogicalCommand.Inventory); break;
            case "select": WorldInput.Submit(new Hit.Item(arg), PointerButton.Left); break;
            case "puzzle":
                if (!game.OpenPuzzle(arg)) GD.Print("UIDEBUG puzzle " + arg + " is not valid here");
                break;
            case "credits": root.OpenCredits(rolling: arg == "roll"); break;
            case "ending": root.PlayEnding(replay: true); break;
            case "help": root.OpenHelp(); break;
            case "portal": root.OpenPortal(); break;
            case "tips":
                UiSettings.TipsShown = false;
                root.GetNode<LastBell.Game.UI.Common.TipsOverlay>("Scaled/Tips").Start();
                break;
            case "talk":
                var room = WorldStage.Instance?.Current;
                var npc = room?.View.Npcs.FirstOrDefault();
                if (npc is not null) WorldInput.Submit(new Hit.Hotspot(npc.Id), PointerButton.Left);
                break;
            case "cutscene":
                // A replay of a watched cutscene (Core's postgame replay; its action must be done, e.g. after --replay).
                game.Update(s => Postgame.ReplayCutscene(game.Content, s, arg));
                break;
            case "era":
                var era = game.Content.FindEra(int.Parse(arg, CultureInfo.InvariantCulture));
                if (era is not null) UiBus.EraCard?.Show(era, LastBell.Core.Text.TextKeys.CardOf(era), LastBell.Core.Text.TextKeys.DateOf(era), () => { });
                break;
            case "draft":
                // Writes a draft for the open puzzle through Core (as the controls do), then shows it.
                if (root.PuzzleView.PuzzleId is { } pid)
                {
                    var node = System.Text.Json.Nodes.JsonNode.Parse(arg);
                    game.Update(s => LastBell.Core.Rules.Puzzles.UpdateDraft(game.Content, s, pid, node));
                    root.PuzzleView.ReloadDraft();
                }
                break;
            case "submit": root.PuzzleView.Confirm(); break;
            case "reveal_all":
                if (root.PuzzleView.PuzzleId is { } rp && LastBell.Core.Rules.Puzzles.ActionFor(game.Content, rp) is { } pa)
                {
                    var quest = game.Content.GetQuestOf(pa.Id);
                    for (int i = 0; i < 3; i++) game.Update(s => Hints.RevealNext(game.Content, s, quest.Id));
                }
                break;
            case "postgame_all":
                // Dev: commits walkthrough.json postgame_optional_route through Core rules (like --replay does for the main route).
                ReplayPostgame(game);
                break;
            case "savegame":
                // Writes a save as the save screen does (world state + thumbnail).
                if (game.Save(arg)) UiRoot.SaveThumbnail(arg, root.CaptureFrame());
                break;
            case "beat":
                // View-only check of a cutscene beat (no playback): beat:<CS>:<index>.
                var bits = arg.Split(':');
                if (game.Content.FindCutscene(bits[0]) is { } beatCs && UiBus.Cutscene is { } view)
                {
                    view.Begin(beatCs);
                    view.Beat(beatCs, int.Parse(bits[1], CultureInfo.InvariantCulture));
                }
                break;
            case "press":
                // A GUI action as the keyboard sends it (ui_accept, ui_cancel, ui_focus_next ...).
                Input.ParseInputEvent(new InputEventAction { Action = arg, Pressed = true });
                Input.ParseInputEvent(new InputEventAction { Action = arg, Pressed = false });
                break;
            case "key":
                if (Enum.TryParse<Key>(arg, true, out var key))
                {
                    Input.ParseInputEvent(new InputEventKey { Keycode = key, PhysicalKeycode = key, Pressed = true });
                    Input.ParseInputEvent(new InputEventKey { Keycode = key, PhysicalKeycode = key, Pressed = false });
                }
                break;
            case "report":
                var focus = root.GetViewport().GuiGetFocusOwner();
                GD.Print($"UIDEBUG report mode={game.State.Mode} room={game.State.Room} done={game.State.Done.Length} modal={root.TopModal?.Name ?? "-"} focus={(focus is Button fb ? fb.Text : focus?.Name ?? "-")} menu={root.MainMenuOpen}");
                break;
            case "notice": UiBus.PostNotice("ui.save.saved"); break;
            default: throw new InvalidOperationException("unknown --ui step");
        }
    }

    private static void ReplayPostgame(GameRuntime game)
    {
        var content = game.Content;
        var root = System.Text.Json.Nodes.JsonNode.Parse(Godot.FileAccess.GetFileAsString(LastBell.Game.Diagnostics.WalkthroughReplayer.Path));
        var s = game.State;
        foreach (var node in root?["postgame_optional_route"]?.AsArray() ?? new System.Text.Json.Nodes.JsonArray())
        {
            string id = node is System.Text.Json.Nodes.JsonObject o ? (string?)o["action"] ?? "" : (string?)node ?? "";
            var action = content.FindAction(id);
            if (action is null) continue;
            if (!action.IsInventoryAction && action.Room != s.Room && Navigation.FindRoute(content, s, action.Room) is { } route)
                foreach (var step in route) s = Playback.FinishAll(content, Navigation.ApplyStep(content, s, step));
            var result = GameRules.TryCommitAction(content, s, id);
            if (result.Success) s = Playback.FinishAll(content, result.State);
            else GD.Print("UIDEBUG postgame " + id + " rejected");
        }
        game.ReplaceState(s with { Mode = GameMode.World });
    }
}
