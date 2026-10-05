using System;
using Godot;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Common;

/// <summary>A small confirmation (or message, when there is no "no" button) dialog. Esc = no / OK.</summary>
public partial class ConfirmDialog : ModalScreen
{
    private readonly string text = "";
    private readonly string yes = "";
    private readonly string? no;
    private readonly Action? onYes;
    private Button? yesButton;
    private Button? noButton;

    /// <summary>Godot constructor.</summary>
    public ConfirmDialog() { }

    /// <summary>Creates the dialog.</summary>
    public ConfirmDialog(string text, string yes, string? no, Action? onYes)
    {
        this.text = text;
        this.yes = yes;
        this.no = no;
        this.onYes = onYes;
        PreferredSize = new Vector2(980, 440);
        Closable = false;
        FitHeight = true;
        Dim = 0.45f;
    }

    /// <inheritdoc />
    protected override void Build()
    {
        Body.AddChild(Ui.Para(text));
        Body.AddChild(new Control { CustomMinimumSize = new Vector2(0, 16) });
        var row = Ui.HBox(16);
        row.Alignment = BoxContainer.AlignmentMode.End;
        if (no is not null)
        {
            noButton = Ui.Button(no, Back);
            row.AddChild(noButton);
        }
        yesButton = Ui.Button(yes, () =>
        {
            Back();
            onYes?.Invoke();
        });
        yesButton.AddThemeFontOverride("font", UiTheme.BodyBold);
        row.AddChild(yesButton);
        Body.AddChild(row);
    }

    /// <inheritdoc />
    protected override Control? InitialFocus() => noButton ?? yesButton;

    /// <inheritdoc />
    public override void Open()
    {
        base.Open();
        Panel.ResetSize();
    }
}
