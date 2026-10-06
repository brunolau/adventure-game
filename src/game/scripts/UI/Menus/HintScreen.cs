using System.Collections.Generic;
using System.Linq;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Text;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Menus;

/// <summary>
/// Progressive hints (H): pick the current main quest or a side quest in progress; each request reveals one more level
/// through <see cref="Hints.RevealNext"/>, as far as the game's difficulty allows (docs/DECISIONS.md "Difficulty
/// settings"): Easy direction, place, exact next step; Standard a nudge and where to look, then a note that the exact
/// step is Easy's; Hard only the nudge, behind a live countdown ("not yet") until three minutes pass without progress,
/// and no help on a puzzle step. The levels belong to the quest's next undone step (<see cref="Hints.CurrentStep"/>,
/// PT-F08): a finished step never comes back. No penalty. On Easy, when the third level of a puzzle's step is revealed
/// the puzzle modal offers "fill in correctly" (hint_can_fill); the player still confirms.
/// </summary>
public partial class HintScreen : ModalScreen
{
    private VBoxContainer questList = null!;
    private VBoxContainer detail = null!;
    private string? selected;
    private Label? waitLabel;
    private Button? waitButton;
    private HintGate? shownGate;

    /// <summary>Quest to show first (e.g. the open puzzle's quest).</summary>
    public string? PreferredQuest { get; set; }

    /// <summary>Godot constructor.</summary>
    public HintScreen() { PreferredSize = new Vector2(1500, 860); }

    /// <inheritdoc />
    protected override void Build()
    {
        SetTitle(Ui.T("ui.hint.title"));
        var row = Ui.HBox(24);
        row.SizeFlagsVertical = SizeFlags.ExpandFill;
        var left = Ui.VBox(8);
        left.CustomMinimumSize = new Vector2(400, 0);
        left.AddChild(Ui.Label(Ui.T("ui.hint.choose_quest"), "CaptionLabel"));
        questList = Ui.VBox(10);
        var leftScroll = Ui.Scroll(questList);
        leftScroll.SizeFlagsHorizontal = SizeFlags.Fill;
        leftScroll.CustomMinimumSize = new Vector2(400, 0);
        left.AddChild(leftScroll);
        row.AddChild(left);
        detail = Ui.VBox(14);
        var rightScroll = Ui.Scroll(detail);
        rightScroll.SizeFlagsStretchRatio = 2;
        row.AddChild(rightScroll);
        Body.AddChild(row);
    }

    private static List<QuestDef> Offered()
    {
        var game = GameRuntime.Instance;
        var content = game.Content;
        var state = game.State;
        var list = new List<QuestDef>();
        if (Quests.CurrentMainQuest(content, state) is { } main) list.Add(main);
        var active = Quests.ActiveSideQuest(content, state);
        if (active is not null) list.Add(active);
        list.AddRange(content.Quests.Where(q => q.IsSide && Quests.StatusOf(q, state) == QuestStatus.InProgress && q != active));
        return list.Where(q => q.Hints.Count > 0).Distinct().ToList();
    }

    /// <inheritdoc />
    protected override void Refresh()
    {
        var offered = Offered();
        var game = GameRuntime.Instance;
        if (PreferredQuest is not null && game.Content.FindQuest(PreferredQuest) is { } pref && !offered.Contains(pref) && !game.State.IsDone(pref.Completion))
            offered.Insert(0, pref);
        if (selected is null || offered.All(q => q.Id != selected)) selected = PreferredQuest is not null && offered.Any(q => q.Id == PreferredQuest) ? PreferredQuest : offered.FirstOrDefault()?.Id;
        if (PreferredQuest is not null && offered.Any(q => q.Id == PreferredQuest)) selected = PreferredQuest;
        PreferredQuest = null;
        Ui.Clear(questList);
        var group = new ButtonGroup();
        foreach (var q in offered)
        {
            string id = q.Id;
            var b = Ui.Tab(TextService.Get(TextKeys.TitleOf(q)), group);
            b.AutowrapMode = TextServer.AutowrapMode.WordSmart;
            b.Alignment = HorizontalAlignment.Left;
            b.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            b.ButtonPressed = id == selected;
            b.Toggled += on => { if (on) { selected = id; BuildDetail(); } };
            var kind = Ui.Label(Ui.T(q.IsMain ? "ui.hint.main_quest" : "ui.hint.side_quest"), "CaptionLabel");
            questList.AddChild(kind);
            questList.AddChild(b);
        }
        BuildDetail();
    }

    private void BuildDetail()
    {
        Ui.Clear(detail);
        waitLabel = null;
        waitButton = null;
        shownGate = null;
        var game = GameRuntime.Instance;
        var quest = selected is null ? null : game.Content.FindQuest(selected);
        if (quest is null)
        {
            bool done = game.State.IsDone(game.Content.Data.Postgame.Unlock);
            detail.AddChild(Ui.Para(Ui.T(done ? "ui.hint.all_done" : "ui.hint.none")));
            return;
        }
        var difficulty = game.State.Difficulty;
        detail.AddChild(Ui.Label(TextService.Get(TextKeys.TitleOf(quest)), "HeadingLabel", wrap: true));
        detail.AddChild(Ui.Para(TextService.Get(TextKeys.GoalOf(quest)), "ItalicLabel"));
        var level = Ui.Label(Ui.T(DifficultyText.HintDifficulty, ("difficulty", Ui.T(DifficultyText.Name(difficulty)))), "CaptionLabel");
        level.TooltipText = Ui.T(DifficultyText.Description(difficulty));
        level.MouseFilter = MouseFilterEnum.Pass;
        detail.AddChild(level);
        detail.AddChild(Ui.Rule());
        var revealed = Hints.Revealed(game.Content, game.State, quest.Id);
        for (int i = 0; i < revealed.Count; i++)
        {
            var card = new PanelContainer { ThemeTypeVariation = i == revealed.Count - 1 ? "HighlightCard" : "CardPanel" };
            var box = Ui.VBox(4);
            box.AddChild(Ui.Label(LevelLabel(revealed[i]), "CaptionLabel"));
            box.AddChild(Ui.Para(Render(revealed[i])));
            card.AddChild(box);
            detail.AddChild(card);
        }
        var available = Hints.Availability(game.Content, game.State, quest.Id, game.SecondsWithoutProgress);
        shownGate = available.Gate;
        string id = quest.Id;
        switch (available.Gate)
        {
            case HintGate.Open:
                var next = Ui.Button(Ui.T(available.NextIsExactStep ? "ui.hint.show_solution" : "ui.hint.next"), () =>
                {
                    game.Update(s => Hints.RevealNext(game.Content, s, id, game.SecondsWithoutProgress));
                    BuildDetail();
                    FocusDefault();
                });
                next.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
                detail.AddChild(next);
                break;
            case HintGate.Waiting:
                // Hard: a visible "not yet" state with the countdown; the screen rebuilds itself when the wait is over.
                string time = DifficultyText.Countdown(available.WaitSeconds);
                waitButton = Ui.Button(Ui.T(DifficultyText.HardWaitButton, ("time", time)));
                waitButton.Disabled = true;
                waitButton.FocusMode = FocusModeEnum.None;
                waitButton.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
                detail.AddChild(waitButton);
                waitLabel = Ui.Para(Ui.T(DifficultyText.HardWait, ("time", time)));
                detail.AddChild(waitLabel);
                detail.AddChild(Ui.Para(Ui.T(DifficultyText.HardWaitNote), "CaptionLabel"));
                break;
            case HintGate.NoPuzzleHelp:
                detail.AddChild(Ui.Para(Ui.T(DifficultyText.HardNoPuzzle), "CaptionLabel"));
                break;
            case HintGate.AllShown when difficulty == Difficulty.Standard:
                detail.AddChild(Ui.Para(Ui.T(DifficultyText.StandardEnd), "CaptionLabel"));
                break;
            case HintGate.AllShown when difficulty == Difficulty.Hard:
                detail.AddChild(Ui.Para(Ui.T(DifficultyText.HardEnd), "CaptionLabel"));
                break;
        }
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        base._Process(delta);
        if (!Visible || selected is null || shownGate != HintGate.Waiting) return;
        var game = GameRuntime.Instance;
        var available = Hints.Availability(game.Content, game.State, selected, game.SecondsWithoutProgress);
        if (available.Gate != HintGate.Waiting)
        {
            BuildDetail();
            FocusDefault();
            return;
        }
        string time = DifficultyText.Countdown(available.WaitSeconds);
        if (waitLabel is not null) waitLabel.Text = Ui.T(DifficultyText.HardWait, ("time", time));
        if (waitButton is not null) waitButton.Text = Ui.T(DifficultyText.HardWaitButton, ("time", time));
    }

    /// <summary>The caption of a revealed level: Easy keeps "Smer / Postup / Riešenie", Standard and Hard name what the level is.</summary>
    private static string LevelLabel(HintText hint) => hint.Kind switch
    {
        HintKind.Nudge => Ui.T(DifficultyText.LevelNudge),
        HintKind.Where => Ui.T(DifficultyText.LevelWhere),
        HintKind.Place => Ui.T("ui.hint.level_2"),
        HintKind.Step => Ui.T("ui.hint.level_3"),
        _ => Ui.T("ui.hint.level_1"),
    };

    /// <summary>
    /// A hint's text: the step's own text (<c>hint.nudge.&lt;id&gt;</c> / <c>hint.where.&lt;id&gt;</c>) once the table has
    /// it, else the fallback text with its placeholders ({room}, {target}) filled in after translation.
    /// </summary>
    private static string Render(HintText hint)
    {
        if (hint.OwnKey is { } own && TextService.Get(own, "") is { Length: > 0 } written) return written;
        return TextService.Format(TextService.Get(hint.Text), hint.Args.Select(a => (a.Name, TextService.Get(a.Value))).ToArray());
    }

    /// <inheritdoc />
    protected override Control? InitialFocus() => FirstFocusable(detail) ?? FirstFocusable(questList);
}
