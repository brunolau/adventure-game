using System;
using System.Collections.Generic;
using Godot;
using LastBell.Core.State;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Menus;

/// <summary>
/// The short difficulty step of New Game (docs/DECISIONS.md "Difficulty settings"): three choices with a one-line
/// description each, Standard preselected, then "Start game". Esc / Cancel goes back to the title screen. The choice is
/// stored in the new game's state (saved per save file) and can be changed any time in Settings (tab "Hra").
/// </summary>
public partial class DifficultyPicker : ModalScreen
{
    private readonly List<Button> choices = new();
    private readonly List<Label[]> texts = new();
    private Button start = null!;
    private Difficulty selected = Difficulty.Standard;

    /// <summary>Called with the chosen difficulty when the player starts the game.</summary>
    public Action<Difficulty>? Chosen { get; set; }

    /// <summary>Godot constructor.</summary>
    public DifficultyPicker()
    {
        PreferredSize = new Vector2(1100, 760);
        FitHeight = true;
        Dim = 0.5f;
    }

    /// <inheritdoc />
    protected override void Build()
    {
        SetTitle(Ui.T(DifficultyText.PickTitle));
        Body.AddChild(Ui.Para(Ui.T(DifficultyText.PickIntro)));
        Body.AddChild(Ui.Label(Ui.T(DifficultyText.Title), "SubheadingLabel"));
        var group = new ButtonGroup();
        var list = Ui.VBox(12);
        foreach (var d in DifficultyText.All)
        {
            var difficulty = d;
            var button = Ui.Tab("", group);
            button.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            button.CustomMinimumSize = new Vector2(0, 104);
            button.Toggled += on =>
            {
                if (on) selected = difficulty;
                Recolor();
            };
            var box = Ui.VBox(2);
            box.MouseFilter = MouseFilterEnum.Ignore;
            box.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
            box.OffsetLeft = 22;
            box.OffsetRight = -22;
            box.OffsetTop = 12;
            box.OffsetBottom = -12;
            box.Alignment = BoxContainer.AlignmentMode.Center;
            string name = Ui.T(DifficultyText.Name(d));
            if (d == Difficulty.Standard) name += "  ·  " + Ui.T(DifficultyText.Recommended);
            var title = Ui.Label(name, "HeadingLabel");
            title.MouseFilter = MouseFilterEnum.Ignore;
            box.AddChild(title);
            var desc = Ui.Para(Ui.T(DifficultyText.Description(d)), "CaptionLabel");
            desc.MouseFilter = MouseFilterEnum.Ignore;
            box.AddChild(desc);
            button.AddChild(box);
            button.TooltipText = Ui.T(DifficultyText.Description(d));
            choices.Add(button);
            texts.Add(new[] { title, desc });
            list.AddChild(button);
        }
        Body.AddChild(list);
        Body.AddChild(new Control { CustomMinimumSize = new Vector2(0, 8) });
        var row = Ui.HBox(16);
        row.Alignment = BoxContainer.AlignmentMode.End;
        row.AddChild(Ui.Button(Ui.T("ui.common.cancel"), Back));
        start = Ui.Button(Ui.T(DifficultyText.Start), () =>
        {
            var choice = selected;
            Back();
            Chosen?.Invoke(choice);
        });
        start.AddThemeFontOverride("font", UiTheme.BodyBold);
        row.AddChild(start);
        Body.AddChild(row);
    }

    /// <inheritdoc />
    protected override void Refresh()
    {
        selected = Difficulty.Standard;
        for (int i = 0; i < choices.Count; i++) choices[i].SetPressedNoSignal(DifficultyText.All[i] == selected);
        Recolor();
    }

    /// <summary>The card texts take the button's own font colour (the chosen card is dark with light text).</summary>
    private void Recolor()
    {
        for (int i = 0; i < choices.Count; i++)
        {
            bool on = choices[i].ButtonPressed;
            foreach (var label in texts[i])
            {
                if (on) label.AddThemeColorOverride("font_color", choices[i].GetThemeColor("font_pressed_color"));
                else label.RemoveThemeColorOverride("font_color");
            }
        }
    }

    /// <inheritdoc />
    protected override Control? InitialFocus() => choices[Array.IndexOf(DifficultyText.All, Difficulty.Standard)];

    /// <summary>QA: selects a difficulty as a click on its card would.</summary>
    public void Select(Difficulty difficulty)
    {
        int index = Array.IndexOf(DifficultyText.All, difficulty);
        if (index >= 0) choices[index].ButtonPressed = true;
    }

    /// <inheritdoc />
    public override void Open()
    {
        base.Open();
        Panel.ResetSize();
    }
}
