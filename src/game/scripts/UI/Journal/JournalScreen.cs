using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Text;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Journal;

/// <summary>
/// The journal (Core mode Journal), built from Core's <see cref="Journal.Build"/>. Tabs follow
/// journal_contract.tabs: Goals (main and side quests, statuses derived from action ids, one main
/// and one side pin), Findings (progress transcripts with objectives, first looks, puzzle clues),
/// People (transcripts of everyone met), Time map (unlocked eras and visited places) and Album
/// (completed side quests, ending replay, cutscene replays). J / Esc / the close cross close it.
/// </summary>
public partial class JournalScreen : ModalScreen
{
    /// <summary>The tab shown on the next open (UI-only memory).</summary>
    public static int LastTab { get; set; }
    private readonly List<Button> tabs = new();
    private VBoxContainer content = null!;
    private ScrollContainer scroll = null!;
    private int tab;
    private string? selectedPerson;
    private string signature = "";

    /// <summary>Godot constructor.</summary>
    public JournalScreen() { PreferredSize = new Vector2(1560, 920); }

    /// <inheritdoc />
    protected override void Build()
    {
        SetTitle(Ui.T("ui.journal.title"));
        tabs.Clear(); // Build runs again after a change of the language (ModalScreen.Relocalize)
        var group = new ButtonGroup();
        var row = new HFlowContainer();
        row.AddThemeConstantOverride("h_separation", 10);
        string[] keys = { "ui.journal.tab_goals", "ui.journal.tab_findings", "ui.journal.tab_people", "ui.journal.tab_time_map", "ui.journal.tab_album" };
        for (int i = 0; i < keys.Length; i++)
        {
            int index = i;
            var b = Ui.Tab(Ui.T(keys[i]), group);
            b.Toggled += on => { if (on) SelectTab(index); };
            tabs.Add(b);
            row.AddChild(b);
        }
        Body.AddChild(row);
        content = Ui.VBox(14);
        scroll = Ui.Scroll(content);
        Body.AddChild(scroll);
    }

    /// <inheritdoc />
    public override void Back() => GameRuntime.Instance.Update(GameRules.CloseOverlay);

    /// <inheritdoc />
    protected override void Refresh()
    {
        tab = LastTab;
        tabs[tab].SetPressedNoSignal(true);
        Rebuild();
    }

    /// <inheritdoc />
    protected override Control? InitialFocus() => tabs[tab];

    private void SelectTab(int index)
    {
        tab = LastTab = index;
        Rebuild();
        scroll.ScrollVertical = 0;
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        base._Process(delta);
        if (!Visible) return;
        var s = GameRuntime.Instance.State;
        string sig = s.Done.Length + "|" + s.PinnedMainQuest + "|" + s.PinnedSideQuest + "|" + s.JournalSeen.Length;
        if (sig != signature) Rebuild();
    }

    private void Rebuild()
    {
        var game = GameRuntime.Instance;
        var s = game.State;
        signature = s.Done.Length + "|" + s.PinnedMainQuest + "|" + s.PinnedSideQuest + "|" + s.JournalSeen.Length;
        var focusedText = (GetViewport()?.GuiGetFocusOwner() as Button)?.Text;
        Ui.Clear(content);
        var view = LastBell.Core.Rules.Journal.Build(game.Content, s);
        switch (tab)
        {
            case 0: BuildGoals(view); break;
            case 1: BuildFindings(view); break;
            case 2: BuildPeople(view); break;
            case 3: BuildTimeMap(view); break;
            default: BuildAlbum(view); break;
        }
        if (focusedText is not null) RefocusButton(content, focusedText);
    }

    private static bool RefocusButton(Node root, string text)
    {
        foreach (var child in root.GetChildren())
        {
            if (child is Button b && b.Text == text) { Ui.FocusLater(b); return true; }
            if (RefocusButton(child, text)) return true;
        }
        return false;
    }

    // ------------------------------------------------------------------ goals

    /// <summary>
    /// The objective line of the "current goal" card: the latest objective of a done main-story action. Core's
    /// <see cref="Quests.LatestObjective"/> takes any action, so a side step (Q9C "Voliteľne sa s Janou porozprávaj …")
    /// stood under the main quest title for the whole E03-E07 stretch (playtest PT-S01). Falls back to Core's
    /// sentence when no main action has an objective yet. Presentation only.
    /// </summary>
    internal static TextRef CurrentObjective(LastBell.Core.Content.GameContent content, GameState state, TextRef latest)
    {
        for (int i = state.Done.Length - 1; i >= 0; i--)
        {
            var action = content.FindAction(state.Done[i]);
            if (action is null || !action.IsMain) continue;
            if (action.Objective is not null) return TextKeys.ObjectiveOf(action);
        }
        return latest;
    }

    private void BuildGoals(JournalView view)
    {
        var current = new PanelContainer { ThemeTypeVariation = "HighlightCard" };
        var cbox = Ui.VBox(6);
        cbox.AddChild(Ui.Label(Ui.T("ui.hud.current_goal"), "SubheadingLabel"));
        if (view.CurrentMainQuest is { } cm)
        {
            cbox.AddChild(Ui.Label(Ui.T(cm.Title), "HeadingLabel", wrap: true));
            cbox.AddChild(Ui.Para(Ui.T(cm.Goal)));
        }
        var objective = CurrentObjective(GameRuntime.Instance.Content, GameRuntime.Instance.State, view.LatestObjective);
        if (!objective.IsEmpty) cbox.AddChild(Ui.Para(Ui.T(objective), "ItalicLabel"));
        if (view.CurrentMainQuest is null && objective.IsEmpty) cbox.AddChild(Ui.Para(Ui.T("ui.hint.all_done")));
        current.AddChild(cbox);
        content.AddChild(current);

        content.AddChild(Ui.Label(Ui.T("ui.journal.main_story"), "HeadingLabel"));
        foreach (var q in view.MainQuests.Reverse()) content.AddChild(QuestCard(q, isMain: true));
        content.AddChild(Ui.Label(Ui.T("ui.journal.side_quests"), "HeadingLabel"));
        if (view.SideQuests.Count == 0) content.AddChild(Ui.Para(Ui.T("ui.journal.empty"), "CaptionLabel"));
        foreach (var q in view.SideQuests.OrderBy(q => q.Status == QuestStatus.Done)) content.AddChild(QuestCard(q, isMain: false));
    }

    private Control QuestCard(JournalQuest q, bool isMain)
    {
        var card = new PanelContainer { ThemeTypeVariation = q.IsPinned ? "HighlightCard" : "CardPanel" };
        var row = Ui.HBox(16);
        var text = Ui.VBox(4);
        text.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var titleRow = Ui.HBox(10);
        if (q.IsPinned) titleRow.AddChild(new Glyph(GlyphKind.Pin, 30, UiTheme.Accent));
        var title = Ui.Label(Ui.T(q.Title), "SubheadingLabel", wrap: true);
        title.AddThemeColorOverride("font_color", q.Status == QuestStatus.Done ? UiTheme.Muted : UiTheme.Ink);
        titleRow.AddChild(title);
        text.AddChild(titleRow);
        if (q.Status != QuestStatus.Done) text.AddChild(Ui.Para(Ui.T(q.Goal), "CaptionLabel"));
        row.AddChild(text);
        var status = Ui.Label(StatusText(q.Status), "CaptionLabel");
        status.VerticalAlignment = VerticalAlignment.Center;
        status.AddThemeColorOverride("font_color", q.Status switch { QuestStatus.Done => UiTheme.Good, QuestStatus.InProgress => UiTheme.Accent, _ => UiTheme.InkSoft });
        if (q.Status == QuestStatus.Done) row.AddChild(new Glyph(GlyphKind.Check, 34, UiTheme.Good) { SizeFlagsVertical = SizeFlags.ShrinkCenter });
        row.AddChild(status);
        if (q.Status != QuestStatus.Done)
        {
            string id = q.QuestId;
            var pin = Ui.Button(Ui.T(q.IsPinned ? "ui.journal.unpin" : "ui.journal.pin"), () =>
            {
                var game = GameRuntime.Instance;
                game.Update(s => q.IsPinned ? Quests.Unpin(game.Content, s, id) : Quests.Pin(game.Content, s, id));
            });
            pin.TooltipText = Ui.T(isMain ? "ui.journal.pinned_main" : "ui.journal.pinned_side");
            pin.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            row.AddChild(pin);
        }
        card.AddChild(row);
        return card;
    }

    private static string StatusText(QuestStatus status) => Ui.T(status switch
    {
        QuestStatus.Done => "ui.journal.state_done",
        QuestStatus.InProgress => "ui.journal.state_in_progress",
        _ => "ui.journal.state_open",
    });

    // ------------------------------------------------------------------ findings

    private void BuildFindings(JournalView view)
    {
        if (view.Clues.Count > 0)
        {
            content.AddChild(Ui.Label(Ui.T("ui.journal.clues"), "HeadingLabel"));
            foreach (var clue in view.Clues)
            {
                var card = new PanelContainer { ThemeTypeVariation = "CardPanel" };
                var box = Ui.VBox(4);
                var head = Ui.HBox(10);
                head.AddChild(Ui.Label(Ui.T(clue.Title), "SubheadingLabel", wrap: true));
                if (clue.Solved) head.AddChild(new Glyph(GlyphKind.Check, 30, UiTheme.Good));
                box.AddChild(head);
                box.AddChild(Ui.Para(Ui.T(clue.Clue)));
                card.AddChild(box);
                content.AddChild(card);
            }
        }
        var progress = view.Findings.Where(f => f.Kind == FindingKind.Action).Reverse().ToList();
        content.AddChild(Ui.Label(Ui.T("ui.journal.progress_log"), "HeadingLabel"));
        if (progress.Count == 0) content.AddChild(Ui.Para(Ui.T("ui.journal.empty"), "CaptionLabel"));
        foreach (var f in progress)
        {
            var box = Ui.VBox(2);
            box.AddChild(Ui.Para(Ui.T(f.Text)));
            string objective = Ui.T(f.Objective);
            if (objective.Length > 0 && objective != Ui.T(f.Text)) box.AddChild(Ui.Para(objective, "CaptionLabel"));
            content.AddChild(box);
            content.AddChild(Ui.Rule());
        }
        var observations = view.Findings.Where(f => f.Kind == FindingKind.Observation).Reverse().ToList();
        content.AddChild(Ui.Label(Ui.T("ui.journal.observations"), "HeadingLabel"));
        if (observations.Count == 0) content.AddChild(Ui.Para(Ui.T("ui.journal.empty"), "CaptionLabel"));
        foreach (var f in observations) content.AddChild(Ui.Para("„" + Ui.T(f.Text) + "“", "ItalicLabel"));
    }

    // ------------------------------------------------------------------ people

    private void BuildPeople(JournalView view)
    {
        if (view.People.Count == 0)
        {
            content.AddChild(Ui.Para(Ui.T("ui.journal.people_empty"), "CaptionLabel"));
            return;
        }
        var flow = new HFlowContainer();
        flow.AddThemeConstantOverride("h_separation", 10);
        flow.AddThemeConstantOverride("v_separation", 10);
        if (selectedPerson is null || view.People.All(p => p.CharacterId != selectedPerson)) selectedPerson = view.People[^1].CharacterId;
        var group = new ButtonGroup();
        var nameCounts = view.People.GroupBy(p => Ui.T(p.Name)).ToDictionary(g => g.Key, g => g.Count());
        foreach (var person in view.People)
        {
            string id = person.CharacterId;
            var b = Ui.Tab(PersonLabel(person, nameCounts), group);
            b.ButtonPressed = id == selectedPerson;
            b.Toggled += on => { if (on && selectedPerson != id) { selectedPerson = id; Rebuild(); } };
            flow.AddChild(b);
        }
        content.AddChild(flow);
        content.AddChild(Ui.Rule());
        var selected = view.People.First(p => p.CharacterId == selectedPerson);
        content.AddChild(Ui.Label(PersonLabel(selected, nameCounts), "HeadingLabel"));
        if (selected.Transcript.Count == 0) content.AddChild(Ui.Para(Ui.T("ui.journal.empty"), "CaptionLabel"));
        foreach (var entry in selected.Transcript.Reverse())
        {
            var card = new PanelContainer { ThemeTypeVariation = "CardPanel" };
            var box = Ui.VBox(6);
            string label = Ui.T(entry.Label);
            if (label.Length > 0) box.AddChild(Ui.Label(label, "SubheadingLabel", wrap: true));
            foreach (var (speakerId, text) in entry.Lines)
            {
                var rich = new RichTextLabel { BbcodeEnabled = true, FitContent = true, ScrollActive = false, SizeFlagsHorizontal = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore };
                string speaker = Ui.SpeakerName(speakerId);
                rich.Text = (speaker.Length > 0 ? "[b]" + Escape(speaker) + ":[/b] " : "") + Escape(Ui.T(text));
                box.AddChild(rich);
            }
            card.AddChild(box);
            content.AddChild(card);
        }
    }

    /// <summary>The person's name; the same person met in several eras gets the year (ISSUES UI-03).</summary>
    private static string PersonLabel(JournalPerson person, IReadOnlyDictionary<string, int> nameCounts)
    {
        string name = Ui.T(person.Name);
        if (nameCounts.GetValueOrDefault(name) < 2) return name;
        var content = GameRuntime.Instance.Content;
        var room = content.FindCharacter(person.CharacterId)?.Rooms.Select(content.FindRoom).FirstOrDefault(r => r is not null);
        return room is null ? name : name + " (" + TextService.EraYear(room.Era) + ")";
    }

    private static string Escape(string text) => text.Replace("[", "[lb]");

    // ------------------------------------------------------------------ time map

    private void BuildTimeMap(JournalView view)
    {
        var game = GameRuntime.Instance;
        foreach (var era in view.TimeMap)
        {
            var card = new PanelContainer { ThemeTypeVariation = era.Year == game.State.Era ? "HighlightCard" : "CardPanel" };
            var box = Ui.VBox(6);
            var head = Ui.HBox(14);
            head.AddChild(Ui.Label(TextService.EraYear(era.Year), "TitleLabel"));
            var names = Ui.VBox(0);
            var eraDef = game.Content.FindEra(era.Year);
            if (eraDef is not null) names.AddChild(Ui.Label(Ui.T(TextKeys.CardOf(eraDef)), "SubheadingLabel"));
            names.AddChild(Ui.Label(Ui.T(era.Date), "CaptionLabel"));
            head.AddChild(names);
            box.AddChild(head);
            var flow = new HFlowContainer();
            flow.AddThemeConstantOverride("h_separation", 18);
            foreach (var room in era.VisitedRooms)
            {
                bool here = room.RoomId == game.State.Room;
                var l = Ui.Label((here ? "● " : "· ") + Ui.T(room.Name) + (here ? "  (" + Ui.T("ui.journal.time_map_current") + ")" : ""), here ? "SubheadingLabel" : "");
                if (here) l.AddThemeColorOverride("font_color", UiTheme.Accent);
                flow.AddChild(l);
            }
            box.AddChild(flow);
            card.AddChild(box);
            content.AddChild(card);
        }
        int locked = game.Content.Eras.Count - view.TimeMap.Count;
        for (int i = 0; i < locked; i++) content.AddChild(Ui.Para(Ui.T("ui.journal.time_map_locked"), "CaptionLabel"));
    }

    // ------------------------------------------------------------------ album

    private void BuildAlbum(JournalView view)
    {
        var game = GameRuntime.Instance;
        if (Postgame.IsActive(game.Content, game.State))
        {
            var replay = Ui.Button(Ui.T("ui.journal.replay_ending"), () =>
            {
                game.Update(GameRules.CloseOverlay);
                UiRoot.Instance?.PlayEnding(replay: true);
            });
            replay.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
            content.AddChild(replay);
        }
        if (view.Album.Count == 0) content.AddChild(Ui.Para(Ui.T("ui.journal.album_empty"), "CaptionLabel"));
        foreach (var entry in view.Album)
        {
            var card = new PanelContainer { ThemeTypeVariation = "CardPanel" };
            var box = Ui.VBox(6);
            box.AddChild(Ui.Label(Ui.T(entry.Title), "SubheadingLabel", wrap: true));
            if (!entry.Shot.IsEmpty) box.AddChild(Ui.Para(Ui.T(entry.Shot)));
            if (!entry.Line.IsEmpty)
            {
                var (speaker, text) = Ui.SplitSpeaker(entry.Line);
                box.AddChild(Ui.Para((speaker is null ? "" : Ui.SpeakerName(speaker) + ": ") + "„" + text + "“", "ItalicLabel"));
            }
            card.AddChild(box);
            content.AddChild(card);
        }
        if (view.ReplayableCutscenes.Count > 0)
        {
            content.AddChild(Ui.Label(Ui.T("ui.journal.scenes"), "HeadingLabel"));
            var flow = new HFlowContainer();
            flow.AddThemeConstantOverride("h_separation", 10);
            flow.AddThemeConstantOverride("v_separation", 10);
            int n = 0;
            foreach (var cutsceneId in view.ReplayableCutscenes)
            {
                n++;
                string id = cutsceneId;
                var action = game.Content.Actions.FirstOrDefault(a => a.Cutscene == id);
                // A scene title of its own when ui.csv has one: the action label can be a spoken topic line
                // ("Zapíšete lipu aj múrik?" for CS08), which reads oddly as a scene name (playtest PT-S08).
                string titled = TextService.Get("ui.journal.scene_" + id.ToLowerInvariant(), "");
                string label = titled.Length > 0 ? titled
                    : action is null ? Ui.T("ui.journal.scene_n", ("n", n.ToString())) : Ui.T(TextKeys.LabelOf(action));
                var b = Ui.Button(label, () => game.Update(s => Postgame.ReplayCutscene(game.Content, s, id)));
                flow.AddChild(b);
            }
            content.AddChild(flow);
        }
    }
}
