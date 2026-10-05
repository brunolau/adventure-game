using System;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Text;
using LastBell.Game.Hooks;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Puzzles;

/// <summary>
/// Puzzle modal framework (<see cref="IPuzzleView"/>) for every puzzle in game.json: the control
/// built from <c>controls.type</c> (matching, rotate_overlay, digits, grid_choice), the clue, the
/// feedback line, and the buttons Confirm (the data's confirm label), Start over (reset_allowed),
/// Hint, Fill in correctly (only when Core's <see cref="Puzzles.CanFill"/>: hint_can_fill and the third
/// hint level revealed) and the close cross. No timer, no penalty: a wrong answer only stores the
/// draft and shows the wrong line; drafts are kept through Core on every change and on close.
/// A correct answer commits the action atomically (GameRuntime.SubmitPuzzle) and the modal closes.
/// </summary>
public partial class PuzzleModal : ModalScreen, IPuzzleView
{
    private BoxContainer layout = null!;
    private ScrollContainer scroll = null!;
    private int scrollResetFrames;
    private VBoxContainer controlHost = null!;
    private Label clue = null!;
    private Label feedback = null!;
    private Button confirm = null!;
    private Button reset = null!;
    private Button fill = null!;
    private PuzzleControl? control;
    private PuzzleDef? puzzle;
    private string? actionId;

    /// <summary>Godot constructor.</summary>
    public PuzzleModal() { PreferredSize = new Vector2(1640, 960); FitHeight = true; }

    /// <inheritdoc />
    protected override void Build()
    {
        layout = new BoxContainer { SizeFlagsHorizontal = SizeFlags.ExpandFill };
        layout.AddThemeConstantOverride("separation", 28);
        controlHost = Ui.VBox(10);
        controlHost.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        controlHost.SizeFlagsStretchRatio = 1.6f;
        layout.AddChild(controlHost);

        var side = Ui.VBox(14);
        side.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var clueCard = new PanelContainer { ThemeTypeVariation = "CardPanel" };
        var clueBox = Ui.VBox(6);
        clueBox.AddChild(Ui.Label(Ui.T("ui.puzzle.clue"), "CaptionLabel"));
        clue = Ui.Para("", "ItalicLabel");
        clueBox.AddChild(clue);
        clueCard.AddChild(clueBox);
        side.AddChild(clueCard);
        feedback = Ui.Para("");
        feedback.AddThemeColorOverride("font_color", UiTheme.Accent);
        side.AddChild(feedback);
        confirm = Ui.Button("", Submit);
        confirm.AddThemeFontOverride("font", UiTheme.BodyBold);
        confirm.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        side.AddChild(confirm);
        var row = new HFlowContainer();
        row.AddThemeConstantOverride("h_separation", 10);
        row.AddThemeConstantOverride("v_separation", 10);
        reset = Ui.Button(Ui.T("ui.puzzle.reset"), ResetDraft);
        row.AddChild(reset);
        row.AddChild(Ui.Button(Ui.T("ui.hud.hint"), OpenHints));
        fill = Ui.Button(Ui.T("ui.puzzle.hint_fill"), Fill);
        row.AddChild(fill);
        side.AddChild(row);
        side.AddChild(Ui.Spacer(vertical: true));
        var close = Ui.Button(Ui.T("ui.puzzle.close"), Back, "FlatButton");
        close.SizeFlagsHorizontal = SizeFlags.ShrinkEnd;
        side.AddChild(close);
        layout.AddChild(side);
        scroll = Ui.Scroll(layout);
        Body.AddChild(scroll);
        FitTarget = layout;
    }

    /// <inheritdoc />
    public void Open(string action, PuzzleDef def)
    {
        actionId = action;
        puzzle = def;
        SetTitle(TextService.Get(TextKeys.TitleOf(def)));
        clue.Text = TextService.Get(TextKeys.ClueOf(def));
        feedback.Text = "";
        var confirmText = TextKeys.ConfirmOf(def);
        confirm.Text = confirmText.IsEmpty ? Ui.T("ui.puzzle.confirm") : TextService.Get(confirmText);
        reset.Visible = def.ResetAllowed;
        Ui.Clear(controlHost);
        try
        {
            control = PuzzleControl.Create(def);
        }
        catch (Exception ex)
        {
            GD.PushError(ex.Message);
            control = null;
        }
        if (control is not null)
        {
            controlHost.AddChild(control);
            control.Changed += StoreDraft;
            LoadDraft();
        }
        base.Open();
        scrollResetFrames = 8; // the control fits itself in the first frames; start at the top
    }

    /// <inheritdoc />
    public void Close()
    {
        Dismiss();
        if (control is not null) control.Changed -= StoreDraft;
        control = null;
        puzzle = null;
        actionId = null;
    }

    /// <inheritdoc />
    public override void Back() => GameRuntime.Instance.ClosePuzzle();

    /// <inheritdoc />
    protected override Control? InitialFocus() => control is null ? confirm : FirstFocusable(control) ?? confirm;

    /// <summary>Re-reads the draft from Core (after an external change, e.g. the QA harness).</summary>
    public void ReloadDraft() => LoadDraft();

    /// <summary>Confirms the current draft (same as the confirm button).</summary>
    public void Confirm() => Submit();

    /// <summary>The open puzzle's id, or null.</summary>
    public string? PuzzleId => puzzle?.Id;

    private void LoadDraft()
    {
        if (puzzle is null || control is null) return;
        var game = GameRuntime.Instance;
        control.SetDraft(LastBell.Core.Rules.Puzzles.Draft(game.Content, game.State, puzzle.Id));
    }

    private void StoreDraft()
    {
        if (puzzle is null || control is null) return;
        var game = GameRuntime.Instance;
        string id = puzzle.Id;
        var draft = control.Draft;
        game.Update(s => LastBell.Core.Rules.Puzzles.UpdateDraft(game.Content, s, id, draft));
        feedback.Text = "";
    }

    private void Submit()
    {
        if (puzzle is null || control is null) return;
        var def = puzzle;
        var result = GameRuntime.Instance.SubmitPuzzle(control.Draft?.DeepClone());
        if (result is null) return;
        var (speaker, text) = Ui.SplitSpeaker(result.Feedback);
        string shown = (speaker is null ? "" : Ui.SpeakerName(speaker) + ": ") + text;
        if (result.Solved) UiRoot.Instance?.Toasts.Show(shown, "", 4.5);
        else
        {
            feedback.Text = shown;
            if (!Settings.UiSettings.ReducedMotion)
            {
                feedback.Modulate = new Color(1, 1, 1, 0.2f);
                CreateTween().TweenProperty(feedback, "modulate:a", 1f, 0.25f);
            }
        }
    }

    private void ResetDraft()
    {
        if (puzzle is null) return;
        var game = GameRuntime.Instance;
        string id = puzzle.Id;
        game.Update(s => LastBell.Core.Rules.Puzzles.Reset(game.Content, s, id));
        LoadDraft();
        feedback.Text = "";
    }

    private void Fill()
    {
        if (puzzle is null) return;
        var game = GameRuntime.Instance;
        string id = puzzle.Id;
        game.Update(s => LastBell.Core.Rules.Puzzles.Fill(game.Content, s, id));
        LoadDraft();
        feedback.Text = Ui.T("ui.puzzle.hint_fill_done");
        confirm.GrabFocus();
    }

    private void OpenHints()
    {
        if (actionId is null) return;
        var quest = GameRuntime.Instance.Content.GetQuestOf(actionId);
        UiRoot.Instance?.OpenHints(quest.Id);
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        base._Process(delta);
        if (!Visible || puzzle is null) return;
        var game = GameRuntime.Instance;
        fill.Visible = game.State.Mode == GameMode.Puzzle && LastBell.Core.Rules.Puzzles.CanFill(game.Content, game.State, puzzle.Id);
        bool narrow = Size.X < 760;
        if (layout.Vertical != narrow) layout.Vertical = narrow;
        var panelSize = Panel.Size;
        // Fit the control into the visible part (the scroll area may be smaller than the preferred height).
        float visible = Math.Max(scroll.Size.Y, 200);
        control?.FitTo(narrow ? new Vector2(panelSize.X - 80, visible) : new Vector2((panelSize.X - 120) * 0.58f, Math.Min(visible, 760)));
        if (scrollResetFrames > 0)
        {
            scrollResetFrames--;
            scroll.ScrollVertical = 0;
        }
    }
}
