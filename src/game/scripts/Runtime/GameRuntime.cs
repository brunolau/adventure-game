using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Godot;
using LastBell.Core;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Text;

namespace LastBell.Game.Runtime;

/// <summary>
/// Autoload "Game" (<c>/root/Game</c>). Loads <c>res://data/game.json</c> into LastBell.Core content
/// once, owns the <see cref="GameSession"/>, turns state changes into fine-grained C# events (and a
/// few Godot signals with plain types), and saves/loads through Core's SaveCodec under
/// <c>user://saves/</c>. It decides no rules: everything is forwarded to Core.
/// Access it from C# as <see cref="Instance"/>.
/// </summary>
public partial class GameRuntime : Node
{
    /// <summary>Path of the canonical game data inside the project.</summary>
    public const string GameDataPath = "res://data/game.json";

    /// <summary>
    /// Folder of the content overlays applied on top of game.json (world_ext.json, dialogue_ext.json, travel_ext.json;
    /// Core README section 13). A missing file means no overlay of that kind; an invalid one fails the load like a broken
    /// game.json. QA runs may read them from another folder (<see cref="LaunchArgs.ContentExtDirectory"/>).
    /// </summary>
    public const string ContentExtDirectory = "res://data/content_ext";

    /// <summary>Folder of the save files.</summary>
    public const string SaveDirectory = "user://saves";

    /// <summary>Slot name of the automatic save.</summary>
    public const string AutosaveSlot = "autosave";

    /// <summary>The id of the hero character (the player's actor).</summary>
    public const string HeroId = "ADAM";

    /// <summary>Godot signal: the state changed (any field).</summary>
    [Signal] public delegate void StateChangedSignalEventHandler();

    /// <summary>Godot signal: the current room changed.</summary>
    [Signal] public delegate void RoomChangedSignalEventHandler(string roomId);

    /// <summary>Godot signal: the top mode changed (GameMode name, e.g. "Inventory").</summary>
    [Signal] public delegate void ModeChangedSignalEventHandler(string mode);

    /// <summary>The singleton (set when the autoload enters the tree).</summary>
    public static GameRuntime Instance { get; private set; } = null!;

    /// <summary>The loaded, immutable content (null only if loading failed).</summary>
    public GameContent Content { get; private set; } = null!;

    /// <summary>The current session (replaced on new game / load).</summary>
    public GameSession Session { get; private set; } = null!;

    /// <summary>The current immutable state.</summary>
    public GameState State => Session.State;

    /// <summary>True when content loaded without errors.</summary>
    public bool IsReady { get; private set; }

    /// <summary>Content load errors (empty when <see cref="IsReady"/>).</summary>
    public IReadOnlyList<string> LoadErrors { get; private set; } = Array.Empty<string>();

    /// <summary>Autosave after commits and room arrivals (the debug harness turns it off).</summary>
    public bool AutosaveEnabled { get; set; } = true;

    /// <summary>
    /// Action id of the puzzle modal that is open right now (GameState only stores the mode and the
    /// drafts, ISSUES.md GAME-02), or null.
    /// </summary>
    public string? OpenPuzzleActionId { get; private set; }

    /// <summary>Raised after every state change (old, new).</summary>
    public event Action<GameState, GameState>? StateChanged;

    /// <summary>Raised when the current room changed (new room id, previous room id).</summary>
    public event Action<string, string>? RoomChanged;

    /// <summary>Raised when the era changed (new year, previous year).</summary>
    public event Action<int, int>? EraChanged;

    /// <summary>Raised when the top mode changed (new, previous).</summary>
    public event Action<GameMode, GameMode>? ModeChanged;

    /// <summary>Raised when owned items changed (added ids, removed ids).</summary>
    public event Action<IReadOnlyList<string>, IReadOnlyList<string>>? InventoryChanged;

    /// <summary>Raised when the cursor item changed (new selection or null).</summary>
    public event Action<string?>? SelectionChanged;

    /// <summary>Raised when the Space label toggle changed.</summary>
    public event Action<bool>? HotspotLabelsChanged;

    /// <summary>Raised after an action was committed (action id). Lines/cutscene follow through playback.</summary>
    public event Action<ActionDef>? ActionCommitted;

    /// <summary>Raised when the playback cursor moved (active line id or null).</summary>
    public event Action<string?>? ActiveLineChanged;

    /// <summary>Raised when a puzzle modal opened (action id, puzzle).</summary>
    public event Action<string, PuzzleDef>? PuzzleOpened;

    /// <summary>Raised when the puzzle modal closed (solved or not).</summary>
    public event Action? PuzzleClosed;

    /// <summary>Raised after every answer submitted to the open puzzle (action id, result; audio feedback).</summary>
    public event Action<string, PuzzleSubmitResult>? PuzzleSubmitted;

    /// <summary>Raised when the whole session was replaced (new game, load): rebuild everything.</summary>
    public event Action? SessionReplaced;

    /// <summary>Raised after a save was written (slot).</summary>
    public event Action<string>? Saved;

    /// <summary>Raised when a load failed (slot, player-facing error text reference).</summary>
    public event Action<string, TextRef>? LoadFailed;

    /// <inheritdoc />
    public override void _EnterTree()
    {
        Instance = this;
        ProcessMode = ProcessModeEnum.Always;
        LastBell.Game.Diagnostics.QaWindow.ApplyBackgroundMode(); // QA runs: off-screen, no focus (owner request)
        if (TranslationServer.GetLocale() is var locale && !locale.StartsWith("sk")) TranslationServer.SetLocale("sk");
        LoadContent();
    }

    /// <inheritdoc />
    public override void _Ready()
    {
        // Window title from the localization key game.title (project name is the key itself).
        if (IsReady) GetWindow().Title = TextService.Get("game.title", Content.Data.Title);
    }

    // ------------------------------------------------------------------ content and session

    private void LoadContent()
    {
        try
        {
            if (!Godot.FileAccess.FileExists(GameDataPath)) throw new InvalidOperationException("missing " + GameDataPath);
            string json = Godot.FileAccess.GetFileAsString(GameDataPath);
            Content = GameContent.Load(json, LoadOverlays());
            AttachSession(new GameSession(Content));
            IsReady = true;
        }
        catch (ContentLoadException ex)
        {
            LoadErrors = ex.Errors.ToList();
            foreach (var error in ex.Errors.Take(20)) GD.PushError("game.json: " + error);
        }
        catch (Exception ex)
        {
            LoadErrors = new[] { ex.Message };
            GD.PushError("GameRuntime: cannot load game data: " + ex);
        }
    }

    private static ContentOverlays LoadOverlays()
    {
        string? qa = LaunchArgs.ContentExtDirectory;
        string? Read(string name)
        {
            if (qa is not null)
            {
                string other = System.IO.Path.Combine(qa, name);
                if (System.IO.File.Exists(other))
                {
                    GD.Print($"LastBell: content overlay {name} from {other} (--content-ext)");
                    return System.IO.File.ReadAllText(other);
                }
            }
            string path = ContentExtDirectory + "/" + name;
            return Godot.FileAccess.FileExists(path) ? Godot.FileAccess.GetFileAsString(path) : null;
        }
        return new ContentOverlays(Read(ContentOverlays.DialogueExtFile), Read(ContentOverlays.TravelExtFile), Read(ContentOverlays.WorldExtFile));
    }

    private void AttachSession(GameSession session)
    {
        if (Session is not null) Session.StateChanged -= OnSessionStateChanged;
        Session = session;
        Session.StateChanged += OnSessionStateChanged;
    }

    /// <summary>Starts a new game from <c>initial_state</c> and queues the start room's first-entry lines.</summary>
    public void NewGame()
    {
        OpenPuzzleActionId = null;
        AttachSession(new GameSession(Content));
        SessionReplaced?.Invoke();
        Session.Update(s => Navigation.BeginNewGame(Content, s));
    }

    /// <summary>
    /// Replaces the session with an arbitrary state (debug harness only: room jumps, replays).
    /// Raises <see cref="SessionReplaced"/>.
    /// </summary>
    public void ReplaceState(GameState state)
    {
        OpenPuzzleActionId = null;
        AttachSession(new GameSession(Content, state));
        SessionReplaced?.Invoke();
    }

    /// <summary>Applies a pure Core rule function to the state.</summary>
    public void Update(Func<GameState, GameState> change) => Session.Update(change);

    // ------------------------------------------------------------------ actions, puzzles

    /// <summary>
    /// Commits an action through Core (atomic). Returns false and changes nothing when it is no
    /// longer valid. Autosaves on success.
    /// </summary>
    public bool Commit(string actionId, JsonNode? answer = null)
    {
        if (!Session.Commit(actionId, answer)) return false;
        ActionCommitted?.Invoke(Content.GetAction(actionId));
        Autosave();
        return true;
    }

    /// <summary>Opens the puzzle modal of a valid puzzle action (after the hero arrived).</summary>
    public bool OpenPuzzle(string actionId)
    {
        var before = State;
        Session.Update(s => Puzzles.Open(Content, s, actionId));
        if (ReferenceEquals(before, State) || State.Mode != GameMode.Puzzle) return false;
        OpenPuzzleActionId = actionId;
        PuzzleOpened?.Invoke(actionId, Content.GetPuzzle(Content.GetAction(actionId).Puzzle!));
        return true;
    }

    /// <summary>Confirms an answer of the open puzzle. A correct answer commits the action atomically.</summary>
    public PuzzleSubmitResult? SubmitPuzzle(JsonNode? answer)
    {
        if (OpenPuzzleActionId is null) return null;
        var actionId = OpenPuzzleActionId;
        var result = Session.SubmitPuzzle(actionId, answer);
        PuzzleSubmitted?.Invoke(actionId, result);
        if (result.Solved)
        {
            OpenPuzzleActionId = null;
            PuzzleClosed?.Invoke();
            ActionCommitted?.Invoke(Content.GetAction(actionId));
            Autosave();
        }
        return result;
    }

    /// <summary>Closes the open puzzle without solving it (draft kept).</summary>
    public void ClosePuzzle()
    {
        Session.Update(Puzzles.Close);
        if (OpenPuzzleActionId is null) return;
        OpenPuzzleActionId = null;
        PuzzleClosed?.Invoke();
    }

    // ------------------------------------------------------------------ save / load

    /// <summary>Absolute res path of a slot file.</summary>
    public static string SlotPath(string slot) => $"{SaveDirectory}/{slot}.json";

    /// <summary>Writes the current state to a slot. Returns false on an I/O error.</summary>
    public bool Save(string slot)
    {
        DirAccess.MakeDirRecursiveAbsolute(SaveDirectory);
        using var file = Godot.FileAccess.Open(SlotPath(slot), Godot.FileAccess.ModeFlags.Write);
        if (file is null)
        {
            GD.PushError($"Save failed ({slot}): {Godot.FileAccess.GetOpenError()}");
            return false;
        }
        file.StoreString(Session.Save());
        file.Close();
        Saved?.Invoke(slot);
        return true;
    }

    /// <summary>
    /// Loads a slot. On any failure the current game stays untouched, <see cref="LoadFailed"/> is
    /// raised with Core's readable error and false is returned.
    /// </summary>
    public bool Load(string slot)
    {
        string path = SlotPath(slot);
        if (!Godot.FileAccess.FileExists(path))
        {
            LoadFailed?.Invoke(slot, UiText.SaveCorrupt);
            return false;
        }
        return LoadFromJson(Godot.FileAccess.GetFileAsString(path), slot);
    }

    /// <summary>Loads a save from its JSON text (import). Same guarantees as <see cref="Load"/>.</summary>
    public bool LoadFromJson(string json, string label = "import")
    {
        var candidate = new GameSession(Content, State);
        if (!candidate.TryLoad(json, out var error))
        {
            LoadFailed?.Invoke(label, error);
            return false;
        }
        // Overlays close; a puzzle modal reopens when the save names a still valid puzzle action (open_puzzle),
        // otherwise it closes with its draft kept (ISSUES GAME-02, UI-05).
        var loaded = GameRules.ResumeAfterLoad(Content, candidate.State);
        ReplaceState(loaded);
        if (Puzzles.OpenAction(Content, loaded) is { } open)
        {
            OpenPuzzleActionId = open.Id;
            PuzzleOpened?.Invoke(open.Id, Content.GetPuzzle(open.Puzzle!));
        }
        return true;
    }

    /// <summary>True when the slot file exists.</summary>
    public static bool SlotExists(string slot) => Godot.FileAccess.FileExists(SlotPath(slot));

    /// <summary>Slot names present on disk with their modification time (unix seconds).</summary>
    public static IReadOnlyList<(string Slot, ulong ModifiedUnix)> ListSlots()
    {
        var result = new List<(string, ulong)>();
        using var dir = DirAccess.Open(SaveDirectory);
        if (dir is null) return result;
        foreach (var file in dir.GetFiles())
        {
            if (!file.EndsWith(".json")) continue;
            result.Add((file[..^5], Godot.FileAccess.GetModifiedTime($"{SaveDirectory}/{file}")));
        }
        return result;
    }

    /// <summary>Deletes a slot file.</summary>
    public static void DeleteSlot(string slot)
    {
        if (SlotExists(slot)) DirAccess.RemoveAbsolute(SlotPath(slot));
    }

    /// <summary>
    /// Writes the autosave when allowed: never while the hero walks (the caller only calls it after
    /// a commit or a room arrival) and never in the debug harness.
    /// </summary>
    public void Autosave()
    {
        if (AutosaveEnabled && IsReady) Save(AutosaveSlot);
    }

    // ------------------------------------------------------------------ change fan-out

    private void OnSessionStateChanged(GameState old, GameState next)
    {
        StateChanged?.Invoke(old, next);
        EmitSignal(SignalName.StateChangedSignal);

        if (old.Mode != next.Mode)
        {
            if (old.Mode == GameMode.Puzzle && OpenPuzzleActionId is not null)
            {
                OpenPuzzleActionId = null;
                PuzzleClosed?.Invoke();
            }
            ModeChanged?.Invoke(next.Mode, old.Mode);
            EmitSignal(SignalName.ModeChangedSignal, next.Mode.ToString());
        }
        if (old.Room != next.Room)
        {
            RoomChanged?.Invoke(next.Room, old.Room);
            EmitSignal(SignalName.RoomChangedSignal, next.Room);
        }
        if (old.Era != next.Era) EraChanged?.Invoke(next.Era, old.Era);
        if (!old.Inventory.SequenceEqual(next.Inventory))
        {
            var added = next.Inventory.Where(i => !old.Has(i)).ToList();
            var removed = old.Inventory.Where(i => !next.Has(i)).ToList();
            InventoryChanged?.Invoke(added, removed);
        }
        if (old.SelectedItem != next.SelectedItem) SelectionChanged?.Invoke(next.SelectedItem);
        if (old.HotspotLabels != next.HotspotLabels) HotspotLabelsChanged?.Invoke(next.HotspotLabels);
        if (old.ActiveLineId != next.ActiveLineId) ActiveLineChanged?.Invoke(next.ActiveLineId);
    }
}
