using Godot;
using LastBell.Core.Rules;
using LastBell.Core.Text;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Menus;

/// <summary>
/// Pause menu (Core mode Pause): resume, save, load, settings, help, main menu, quit — with the
/// current goal as a reminder. Esc resumes (routed through Core's Escape). Nothing here is timed:
/// the story has no clock (AT23).
/// </summary>
public partial class PauseScreen : ModalScreen
{
    private Button resume = null!;
    private Label goal = null!;

    /// <summary>Godot constructor.</summary>
    public PauseScreen() { PreferredSize = new Vector2(820, 900); FitHeight = true; }

    /// <inheritdoc />
    protected override void Build()
    {
        SetTitle(Ui.T("ui.pause.title"));
        var card = new PanelContainer { ThemeTypeVariation = "CardPanel" };
        var cbox = Ui.VBox(4);
        cbox.AddChild(Ui.Label(Ui.T("ui.hud.current_goal"), "CaptionLabel"));
        goal = Ui.Para("");
        cbox.AddChild(goal);
        card.AddChild(cbox);
        var content = Ui.VBox(14);
        content.AddChild(card);
        var list = Ui.VBox(10);
        content.AddChild(list);
        resume = Add(list, "ui.pause.resume", () => GameRuntime.Instance.Update(GameRules.CloseOverlay));
        resume.AddThemeFontOverride("font", UiTheme.BodyBold);
        Add(list, "ui.pause.save", () => UiRoot.Instance?.OpenSaveLoad(true));
        Add(list, "ui.pause.load", () => UiRoot.Instance?.OpenSaveLoad(false));
        Add(list, "ui.pause.settings", () => UiRoot.Instance?.OpenSettings());
        Add(list, "ui.pause.help", () => UiRoot.Instance?.OpenHelp());
        Add(list, "ui.pause.main_menu", () => UiRoot.Instance?.Confirm(Ui.T("ui.pause.main_menu_confirm"), Ui.T("ui.pause.main_menu"), () => UiRoot.Instance?.ShowMainMenu()));
        Add(list, "ui.pause.quit", () => UiRoot.Instance?.Confirm(Ui.T("ui.pause.quit_confirm"), Ui.T("ui.pause.quit"), () => GetTree().Quit()));
        Body.AddChild(Ui.Scroll(content));
        FitTarget = content;
    }

    private static Button Add(VBoxContainer list, string key, System.Action pressed)
    {
        var b = Ui.Button(Ui.T(key), pressed);
        b.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        list.AddChild(b);
        return b;
    }

    /// <inheritdoc />
    protected override void Refresh()
    {
        var game = GameRuntime.Instance;
        var quest = Quests.CurrentMainQuest(game.Content, game.State);
        var objective = LastBell.Game.UI.Journal.JournalScreen.CurrentObjective(game.Content, game.State, Quests.LatestObjective(game.Content, game.State));
        goal.Text = !objective.IsEmpty ? TextService.Get(objective) : quest is null ? Ui.T("ui.hint.all_done") : TextService.Get(TextKeys.GoalOf(quest));
    }

    /// <inheritdoc />
    protected override Control? InitialFocus() => resume;

    /// <inheritdoc />
    public override void Back() => GameRuntime.Instance.Update(GameRules.CloseOverlay);
}
