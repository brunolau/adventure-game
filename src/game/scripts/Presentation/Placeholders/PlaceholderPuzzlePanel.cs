using Godot;
using LastBell.Core.Content;
using LastBell.Core.Text;
using LastBell.Game.Hooks;
using LastBell.Game.Runtime;

namespace LastBell.Game.Presentation.Placeholders;

/// <summary>
/// Temporary puzzle modal (until the UI agent registers an <see cref="IPuzzleView"/>): title, clue
/// and Close. Debug builds add a "solve" button that submits the data solution through the normal
/// GameRuntime.SubmitPuzzle path (dev only; the real controls come with the UI agent).
/// Also forwards puzzle open/close events to a registered view.
/// </summary>
public partial class PlaceholderPuzzlePanel : Control, IPuzzleView
{
    private PanelContainer panel = null!;
    private Label title = null!;
    private Label clue = null!;
    private Label feedback = null!;
    private Button close = null!;
    private PuzzleDef? puzzle;

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
        panel = PlaceholderStyle.Panel(0.95f);
        panel.Position = new Vector2(460, 260);
        panel.CustomMinimumSize = new Vector2(1000, 0);
        var box = new VBoxContainer();
        box.AddThemeConstantOverride("separation", 12);
        title = PlaceholderStyle.Label("", 32, new Color(1f, 0.83f, 0.45f));
        clue = PlaceholderStyle.Label("", 24);
        clue.AutowrapMode = TextServer.AutowrapMode.WordSmart;
        clue.CustomMinimumSize = new Vector2(960, 0);
        feedback = PlaceholderStyle.Label("", 22, new Color(0.7f, 0.95f, 1f));
        feedback.AutowrapMode = TextServer.AutowrapMode.WordSmart;
        feedback.CustomMinimumSize = new Vector2(960, 0);
        var buttons = new HBoxContainer();
        close = PlaceholderStyle.Button(TextService.Ui("ui.puzzle.close"));
        close.Pressed += () => GameRuntime.Instance.ClosePuzzle();
        buttons.AddChild(close);
        if (OS.IsDebugBuild())
        {
            var solve = PlaceholderStyle.Button(TextService.Ui("ui.dev.solve"));
            solve.Pressed += Solve;
            buttons.AddChild(solve);
        }
        box.AddChild(title);
        box.AddChild(PlaceholderStyle.Label(TextService.Ui("ui.puzzle.clue"), 20, new Color(1, 1, 1, 0.6f)));
        box.AddChild(clue);
        box.AddChild(feedback);
        box.AddChild(buttons);
        panel.AddChild(box);
        AddChild(panel);
        panel.Visible = false;
        var game = GameRuntime.Instance;
        game.PuzzleOpened += (actionId, p) =>
        {
            if (UiBus.Puzzle is { } custom) custom.Open(actionId, p);
            else Open(actionId, p);
        };
        game.PuzzleClosed += () =>
        {
            if (UiBus.Puzzle is { } custom) custom.Close();
            else Close();
        };
        game.SessionReplaced += Close;
    }

    /// <inheritdoc />
    public void Open(string actionId, PuzzleDef def)
    {
        puzzle = def;
        title.Text = TextService.Get(TextKeys.TitleOf(def));
        clue.Text = TextService.Get(TextKeys.ClueOf(def));
        feedback.Text = "";
        panel.Visible = true;
        close.CallDeferred(Control.MethodName.GrabFocus);
    }

    /// <inheritdoc />
    public void Close()
    {
        panel.Visible = false;
        puzzle = null;
    }

    private void Solve()
    {
        if (puzzle is null) return;
        var result = GameRuntime.Instance.SubmitPuzzle(puzzle.Solution?.DeepClone());
        if (result is not null) feedback.Text = TextService.Get(result.Feedback);
    }
}
