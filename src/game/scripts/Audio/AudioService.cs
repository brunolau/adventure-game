using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Game.Hooks;
using LastBell.Game.Presentation;
using LastBell.Game.Runtime;
using LastBell.Game.UI;
using LastBell.Game.UI.Cutscenes;
using LastBell.Game.UI.Menus;
using LastBell.Game.UI.Settings;

namespace LastBell.Game.Audio;

/// <summary>
/// The game's audio (node "AudioService" under Main): music per room/era with crossfades and cues
/// (main menu, puzzle, cutscene and room overrides, epilogue), ambience per room, sound effects by
/// id for <c>actions[].sfx</c> and UI/game events, and the voice bus for future voice lines
/// (<c>res://assets/voice/&lt;line_id&gt;.ogg</c> when present). Buses: Master, Music, Ambience, SFX,
/// Voice (default_bus_layout.tres); their volumes are set by the settings UI (UiSettings.Apply), the
/// service only routes players to them. Data: data/audio/{music,ambience,sfx}.json.
/// Presentation only: never changes game state.
/// </summary>
public partial class AudioService : Node
{
    private static bool logEnabled;
    private static bool logVerbose;

    private readonly HashSet<ulong> hooked = new();
    private MusicDirector music = null!;
    private AmbiencePlayer ambience = null!;
    private SfxPlayer sfx = null!;
    private AudioStreamPlayer voice = null!;
    private string displayedRoom = "";
    private int displayedEra;
    private string? cutsceneId;
    private string? voiceLine;
    private ulong lastHoverMs;
    private GameMode lastMode = GameMode.World;
    private DialoguePresenter? dialogue;

    /// <summary>The service (null before Main built it).</summary>
    public static AudioService? Instance { get; private set; }

    /// <summary>Loaded audio data.</summary>
    public AudioCatalog Catalog { get; private set; } = new();

    /// <summary>Music decks.</summary>
    public MusicDirector Music => music;

    /// <summary>Room ambience.</summary>
    public AmbiencePlayer Ambience => ambience;

    /// <summary>A forced music cue (cue name or asset path) that wins over everything but the menu; null = automatic.</summary>
    public string? ForcedMusic { get; set; }

    /// <summary>Bus name if it exists, else "Master".</summary>
    public static string BusOrMaster(string bus) => AudioServer.GetBusIndex(bus) >= 0 ? bus : "Master";

    /// <summary>Prints "AUDIO ..." lines in harness runs (any user args) or with <c>--audio-log</c>.</summary>
    public static void Log(string message)
    {
        if (logEnabled) GD.Print("AUDIO " + message);
    }

    /// <summary>Like <see cref="Log"/>, only with <c>--audio-log</c> (every sound effect played).</summary>
    public static void LogVerbose(string message)
    {
        if (logVerbose) GD.Print("AUDIO " + message);
    }

    /// <summary>Plays a sound effect id from data/audio/sfx.json.</summary>
    public static void PlaySfx(string id, float extraDb = 0f) => Instance?.sfx.Play(id, extraDb);

    /// <summary>True while a voice-over line is playing; the dialogue presenter waits for it before auto-advancing.</summary>
    public static bool VoicePlaying => Instance?.voice is { } v && v.Playing;

    /// <summary>Plays the sound mapped to a UI/game event name (sfx.json "events").</summary>
    public static void PlayEvent(string eventName)
    {
        if (Instance is { } s && s.Catalog.Events.TryGetValue(eventName, out var id)) s.sfx.Play(id);
    }

    /// <inheritdoc />
    public override void _Ready()
    {
        Instance = this;
        var args = LaunchArgs.User;
        logEnabled = args.Length > 0;
        logVerbose = args.Contains("--audio-log");
        ProcessMode = ProcessModeEnum.Always; // keep fading while the tree is paused
        Catalog = AudioCatalog.Load();
        foreach (var w in Catalog.Warnings) GD.PushWarning("AudioService: " + w);

        music = new MusicDirector { Name = "Music", Catalog = Catalog };
        ambience = new AmbiencePlayer { Name = "Ambience", Catalog = Catalog };
        sfx = new SfxPlayer { Name = "Sfx", Catalog = Catalog };
        voice = new AudioStreamPlayer { Name = "Voice", Bus = BusOrMaster("Voice") };
        AddChild(music);
        AddChild(ambience);
        AddChild(sfx);
        AddChild(voice);

        var game = GameRuntime.Instance;
        game.SessionReplaced += OnSessionReplaced;
        game.StateChanged += OnStateChanged;
        game.ActionCommitted += OnActionCommitted;
        game.InventoryChanged += OnInventoryChanged;
        game.SelectionChanged += OnSelectionChanged;
        game.ModeChanged += OnModeChanged;
        game.PuzzleOpened += OnPuzzleOpened;
        game.PuzzleSubmitted += OnPuzzleSubmitted;
        game.ActiveLineChanged += OnActiveLineChanged;
        game.Saved += OnSaved;
        WorldHooks.RoomBuilt += OnRoomBuilt;
        WorldHooks.RoomRefreshed += OnRoomRefreshed;
        GetTree().NodeAdded += OnNodeAdded;
        UiSettings.Changed += OnSettingsChanged;
        CallDeferred(MethodName.LateInit);
        Log($"ready: {Catalog.Tracks.Count} music tracks, {Catalog.AmbienceLibrary.Count} ambience sounds in {Catalog.RoomAmbience.Count} rooms, {Catalog.Sfx.Count} sfx ids");
    }

    private void LateInit()
    {
        dialogue = GetParent()?.GetNodeOrNull<DialoguePresenter>("DialoguePresenter");
        if (dialogue is not null) dialogue.LineShown += OnLineShown;
        HookTree(GetTree().Root);
        if (LaunchArgs.User.Contains("--audio-report")) Report();
    }

    /// <inheritdoc />
    public override void _ExitTree()
    {
        if (Instance == this) Instance = null;
        UiSettings.Changed -= OnSettingsChanged;
        foreach (var player in FindChildren("*", "AudioStreamPlayer", true, false).Concat(FindChildren("*", "AudioStreamPlayer2D", true, false)))
        {
            if (player is AudioStreamPlayer p) { p.Stop(); p.Stream = null; }
            else if (player is AudioStreamPlayer2D p2) { p2.Stop(); p2.Stream = null; }
        }
        AudioStreams.Clear();
        // the audio thread drops stopped playbacks on its next mix step; give it one before the engine's leak check
        OS.DelayMsec(60);
        var game = GameRuntime.Instance;
        if (game is null) return;
        game.SessionReplaced -= OnSessionReplaced;
        game.StateChanged -= OnStateChanged;
        game.ActionCommitted -= OnActionCommitted;
        game.InventoryChanged -= OnInventoryChanged;
        game.SelectionChanged -= OnSelectionChanged;
        game.ModeChanged -= OnModeChanged;
        game.PuzzleOpened -= OnPuzzleOpened;
        game.PuzzleSubmitted -= OnPuzzleSubmitted;
        game.ActiveLineChanged -= OnActiveLineChanged;
        game.Saved -= OnSaved;
        WorldHooks.RoomBuilt -= OnRoomBuilt;
        WorldHooks.RoomRefreshed -= OnRoomRefreshed;
        if (dialogue is not null) dialogue.LineShown -= OnLineShown;
    }

    // ------------------------------------------------------------------ music and ambience choice

    /// <summary>The music asset path the current situation asks for ("" = silence).</summary>
    public string DesiredMusic()
    {
        var ui = UiRoot.Instance;
        if (ui?.TopModal is EndingSequence or CreditsScreen) return Catalog.ResolveCue("epilogue");
        if (ui?.MainMenuOpen == true) return Catalog.ResolveCue("menu");
        if (ForcedMusic is { } forced) return Catalog.ResolveCue(forced);
        var game = GameRuntime.Instance;
        if (!game.IsReady) return "";
        var state = game.State;
        if (state.Mode == GameMode.Puzzle) return Catalog.ResolveCue("puzzle");
        if (state.Mode == GameMode.Cutscene && cutsceneId is { } cs && Catalog.CutsceneMusic.TryGetValue(cs, out var cue))
            return Catalog.ResolveCue(cue);
        string roomId = displayedRoom.Length > 0 ? displayedRoom : state.Room;
        return MusicForRoom(roomId, state);
    }

    /// <summary>Room music in a state: a matching override from music.json, else rooms[].music.</summary>
    public string MusicForRoom(string roomId, GameState? state)
    {
        if (Catalog.RoomMusic.TryGetValue(roomId, out var overrides))
        {
            foreach (var o in overrides)
            {
                bool afterOk = o.After is null || (state?.IsDone(o.After) ?? false);
                bool untilOk = o.Until is null || !(state?.IsDone(o.Until) ?? false);
                if (afterOk && untilOk) return Catalog.ResolveCue(o.Cue);
            }
        }
        // A natural blocking may replace the room's music (presentation only; World/RoomBlocking.cs audio.music).
        if (LastBell.Game.World.RoomBlocking.For(roomId)?.Audio?.Music is { Length: > 0 } natural) return Catalog.ResolveCue(natural);
        var room = GameRuntime.Instance.Content.FindRoom(roomId);
        return room?.Music ?? "";
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        if (GameRuntime.Instance is null) return;
        music.Request(DesiredMusic());
        var ui = UiRoot.Instance;
        bool menu = ui?.MainMenuOpen == true || ui?.TopModal is EndingSequence or CreditsScreen;
        var mode = GameRuntime.Instance.IsReady ? GameRuntime.Instance.State.Mode : GameMode.World;
        ambience.SetLevel(menu ? -80f : mode is GameMode.Pause or GameMode.Journal or GameMode.Map ? -8f : mode == GameMode.Puzzle ? -6f : 0f);
        if (!voice.Playing) music.SetDuck(0f);
    }

    private void SyncAmbience()
    {
        var game = GameRuntime.Instance;
        if (!game.IsReady) return;
        string roomId = displayedRoom.Length > 0 ? displayedRoom : game.State.Room;
        ambience.Sync(roomId, game.State);
    }

    private void OnRoomBuilt(LastBell.Game.World.Room room)
    {
        displayedRoom = room.RoomId;
        int era = GameRuntime.Instance.Content.FindRoom(room.RoomId)?.Era ?? 0;
        // the whoosh belongs to the era card, which follows the build of the first room of the new era
        if (displayedEra != 0 && era != 0 && era != displayedEra) PlayEvent("era_transition");
        displayedEra = era;
        SyncAmbience();
    }

    private void OnRoomRefreshed(LastBell.Game.World.Room room)
    {
        if (room.RoomId == displayedRoom) SyncAmbience();
    }

    private void OnSessionReplaced()
    {
        cutsceneId = null;
        StopVoice();
        displayedRoom = "";
        displayedEra = 0;
        SyncAmbience();
    }

    private void OnStateChanged(GameState before, GameState after)
    {
        if (before.Done.Length != after.Done.Length) SyncAmbience(); // after/until layers
    }

    // ------------------------------------------------------------------ game events → sounds

    private void OnActionCommitted(ActionDef action)
    {
        if (!string.IsNullOrEmpty(action.Sfx)) sfx.Play(action.Sfx);
        if (!string.IsNullOrEmpty(action.Objective)) PlayEventDelayed("new_goal", 0.6f);
    }

    private void OnInventoryChanged(IReadOnlyList<string> added, IReadOnlyList<string> removed)
    {
        if (added.Count > 0) PlayEventDelayed("item_added", 0.25f);
    }

    private void OnSelectionChanged(string? item) => PlayEvent(item is null ? "item_deselect" : "item_select");


    private void OnModeChanged(GameMode now, GameMode before)
    {
        lastMode = now;
        string? ev = now switch
        {
            GameMode.Inventory => "inventory_open",
            GameMode.Journal => "journal_open",
            GameMode.Map => "map_open",
            GameMode.Pause => "pause_open",
            GameMode.Cutscene => "cutscene_start",
            _ => null,
        };
        if (ev is null)
        {
            ev = before switch
            {
                GameMode.Inventory => "inventory_close",
                GameMode.Journal => "journal_close",
                GameMode.Map => "map_close",
                GameMode.Pause => "pause_close",
                _ => null,
            };
        }
        if (before == GameMode.Cutscene) cutsceneId = null;
        if (ev is not null) PlayEvent(ev);
    }

    private void OnPuzzleOpened(string actionId, PuzzleDef puzzle) => PlayEvent("puzzle_open");

    private void OnPuzzleSubmitted(string actionId, PuzzleSubmitResult result) =>
        PlayEvent(result.Solved ? "puzzle_success" : "puzzle_fail");

    private void OnSaved(string slot) => PlayEvent("saved");

    private void PlayEventDelayed(string eventName, float seconds)
    {
        var timer = GetTree().CreateTimer(seconds, processAlways: true);
        timer.Timeout += () => PlayEvent(eventName);
    }

    // ------------------------------------------------------------------ voice

    private void OnLineShown(SubtitleLine line)
    {
        if (line.Line.IsCutscene) cutsceneId = line.Line.SourceId;
        PlayVoiceLine(line.Line.LineId);
    }

    /// <summary>
    /// Plays <c>assets/voice/&lt;lineId&gt;.ogg</c> on the Voice bus (null or a missing file stops the voice). Used by the
    /// dialogue presenter's lines and by screens that show a line themselves (the epilogue shots). Nothing plays while
    /// the voice-over setting is off (<see cref="UiSettings.VoiceOver"/>).
    /// </summary>
    public static void PlayVoice(string? lineId) => Instance?.PlayVoiceLine(lineId);

    private void PlayVoiceLine(string? lineId)
    {
        voiceLine = lineId;
        string path = $"voice/{lineId}.ogg";
        if (UiSettings.VoiceOver && !string.IsNullOrEmpty(lineId) && AudioStreams.Exists(path) && AudioStreams.GetOneShot(path) is { } stream)
        {
            voice.Stream = stream;
            voice.Play();
            music.SetDuck(-5f);
            Log($"voice {lineId}");
        }
        else
        {
            if (!UiSettings.VoiceOver && !string.IsNullOrEmpty(lineId) && AudioStreams.Exists(path)) Log($"voice off {lineId}");
            StopVoice();
        }
    }

    private void OnSettingsChanged()
    {
        if (!UiSettings.VoiceOver && voice.Playing) StopVoice(); // switched off while a line was speaking
    }

    private void OnActiveLineChanged(string? lineId)
    {
        if (lineId != voiceLine) StopVoice();
    }

    private void StopVoice()
    {
        if (voice.Playing) voice.Stop();
        music.SetDuck(0f);
    }

    // ------------------------------------------------------------------ UI sounds (hooked, not rewritten)

    private void HookTree(Node node)
    {
        OnNodeAdded(node);
        foreach (var child in node.GetChildren()) HookTree(child);
    }

    private void OnNodeAdded(Node node)
    {
        if (node is not (BaseButton or Godot.Range)) return;
        if (!hooked.Add(node.GetInstanceId())) return;
        node.TreeExited += () => hooked.Remove(node.GetInstanceId());
        switch (node)
        {
            case BaseButton button:
                button.Pressed += () => PlayEvent(button.ToggleMode ? "ui_toggle" : "ui_click");
                button.MouseEntered += () =>
                {
                    if (button.Disabled) return;
                    ulong now = Time.GetTicksMsec();
                    if (now - lastHoverMs < 70) return;
                    lastHoverMs = now;
                    PlayEvent("ui_hover");
                };
                break;
            case Slider slider:
                slider.DragEnded += _ => PlayEvent("ui_slider");
                break;
        }
    }

    // ------------------------------------------------------------------ QA report

    /// <summary>Prints every room's music and ambience layers and checks that every referenced file loads.</summary>
    public void Report()
    {
        var game = GameRuntime.Instance;
        int missing = 0;
        void Check(string what, string path)
        {
            if (string.IsNullOrEmpty(path)) return;
            if (AudioStreams.Get(path) is null)
            {
                missing++;
                GD.Print($"AUDIO REPORT MISSING {what}: {path}");
            }
        }
        foreach (var room in game.Content.Rooms)
        {
            Check("music " + room.Id, room.Music);
            var layers = ambience.ActiveLayers(room.Id, null).ToList();
            var all = ambience.LayersOf(room.Id).ToList(); // incl. a natural blocking's audio override
            string desc = string.Join(", ", all.Select(x => x.Sound + (x.After is not null ? $"[after {x.After}]" : "") + (x.Until is not null ? $"[until {x.Until}]" : "")));
            string over = Catalog.RoomMusic.TryGetValue(room.Id, out var o) && o.Count > 0
                ? " (+" + string.Join(", ", o.Select(x => $"{x.Cue}{(x.After is not null ? " after " + x.After : "")}{(x.Until is not null ? " until " + x.Until : "")}")) + ")" : "";
            GD.Print($"AUDIO REPORT room {room.Id} era {room.Era} music {room.Music}{over} | ambience {desc}");
            foreach (var layer in all)
            {
                if (!Catalog.AmbienceLibrary.TryGetValue(layer.Sound, out var snd)) { missing++; GD.Print($"AUDIO REPORT MISSING ambience sound id {layer.Sound} ({room.Id})"); continue; }
                foreach (var f in snd.Files) Check("ambience " + snd.Id, f);
            }
            if (all.Count == 0) GD.Print($"AUDIO REPORT WARNING room {room.Id} has no ambience");
        }
        foreach (var (name, path) in Catalog.Cues) Check("cue " + name, path);
        foreach (var def in Catalog.Sfx.Values)
            foreach (var f in def.Files) Check("sfx " + def.Id, f);
        foreach (var id in game.Content.Actions.Select(a => a.Sfx).Where(s => !string.IsNullOrEmpty(s)).Distinct())
            if (!Catalog.Sfx.ContainsKey(id)) { missing++; GD.Print($"AUDIO REPORT MISSING sfx id {id} (actions[].sfx)"); }
        foreach (var (ev, id) in Catalog.Events)
            if (!Catalog.Sfx.ContainsKey(id)) { missing++; GD.Print($"AUDIO REPORT MISSING sfx id {id} for event {ev}"); }
        foreach (var w in Catalog.Warnings) GD.Print("AUDIO REPORT WARNING " + w);
        GD.Print($"AUDIO REPORT buses: {string.Join(", ", Enumerable.Range(0, AudioServer.BusCount).Select(i => $"{AudioServer.GetBusName(i)} {AudioServer.GetBusVolumeDb(i):0.0}dB"))}");
        GD.Print(missing == 0 ? "AUDIO REPORT OK" : $"AUDIO REPORT FAIL {missing} missing");
    }
}
