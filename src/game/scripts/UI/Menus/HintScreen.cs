using System.Collections.Generic;
using System.Linq;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.Text;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Menus;

/// <summary>
/// Progressive hints (H): pick the current main quest or a side quest in progress; each request
/// reveals one more level (direction, place, exact next step) through <see cref="Hints.RevealNext"/>.
/// The levels belong to the quest's next undone step (<see cref="Hints.CurrentStep"/>, PT-F08): a
/// finished step never comes back, and the third level shows only that step, not the whole chain.
/// No penalty. When the third level of a puzzle's step is revealed the puzzle modal offers
/// "fill in correctly" (hint_can_fill); the player still confirms.
/// </summary>
public partial class HintScreen : ModalScreen
{
    private VBoxContainer questList = null!;
    private VBoxContainer detail = null!;
    private string? selected;

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
        var game = GameRuntime.Instance;
        var quest = selected is null ? null : game.Content.FindQuest(selected);
        if (quest is null)
        {
            bool done = game.State.IsDone(game.Content.Data.Postgame.Unlock);
            detail.AddChild(Ui.Para(Ui.T(done ? "ui.hint.all_done" : "ui.hint.none")));
            return;
        }
        detail.AddChild(Ui.Label(TextService.Get(TextKeys.TitleOf(quest)), "HeadingLabel", wrap: true));
        detail.AddChild(Ui.Para(TextService.Get(TextKeys.GoalOf(quest)), "ItalicLabel"));
        detail.AddChild(Ui.Rule());
        var revealed = Hints.Revealed(game.Content, game.State, quest.Id);
        string[] levelKeys = { "ui.hint.level_1", "ui.hint.level_2", "ui.hint.level_3" };
        for (int i = 0; i < revealed.Count; i++)
        {
            var card = new PanelContainer { ThemeTypeVariation = i == revealed.Count - 1 ? "HighlightCard" : "CardPanel" };
            var box = Ui.VBox(4);
            box.AddChild(Ui.Label(Ui.T(levelKeys[System.Math.Clamp(revealed[i].Level - 1, 0, 2)]), "CaptionLabel"));
            box.AddChild(Ui.Para(Render(revealed[i])));
            card.AddChild(box);
            detail.AddChild(card);
        }
        int level = Hints.RevealedLevel(game.Content, game.State, quest.Id);
        if (level < Hints.Levels && Hints.CurrentStep(game.Content, game.State, quest.Id) is not null)
        {
            bool last = level == Hints.Levels - 1;
            string id = quest.Id;
            var next = Ui.Button(Ui.T(last ? "ui.hint.show_solution" : "ui.hint.next"), () =>
            {
                game.Update(s => Hints.RevealNext(game.Content, s, id));
                BuildDetail();
                FocusDefault();
            });
            next.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
            detail.AddChild(next);
        }
    }

    /// <summary>A hint's text with its placeholders ({room}, {target}) filled in after translation.</summary>
    private static string Render(HintText hint) =>
        TextService.Format(TextService.Get(hint.Text), hint.Args.Select(a => (a.Name, TextService.Get(a.Value))).ToArray());

    /// <inheritdoc />
    protected override Control? InitialFocus() => FirstFocusable(detail) ?? FirstFocusable(questList);
}
