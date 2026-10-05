using Godot;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Menus;

/// <summary>Help: the controls (mouse and keyboard; every action has a keyboard alternative, AT19) and the first-start tips.</summary>
public partial class HelpScreen : ModalScreen
{
    /// <summary>The control lines (ui.csv), shared with the settings' controls tab.</summary>
    public static readonly string[] ControlKeys =
    {
        "ui.controls.left_click", "ui.controls.right_click", "ui.controls.right_click_selected", "ui.controls.space",
        "ui.controls.inventory", "ui.controls.journal", "ui.controls.map", "ui.controls.hint", "ui.controls.travel",
        "ui.controls.escape", "ui.controls.enter", "ui.controls.tab", "ui.controls.back",
    };

    /// <summary>Godot constructor.</summary>
    public HelpScreen() { PreferredSize = new Vector2(1300, 900); }

    /// <inheritdoc />
    protected override void Build()
    {
        SetTitle(Ui.T("ui.controls.title"));
        var list = Ui.VBox(10);
        foreach (var key in ControlKeys) list.AddChild(Ui.Para("• " + Ui.T(key)));
        list.AddChild(Ui.Rule());
        foreach (var key in new[] { "ui.tutorial.left_click", "ui.tutorial.right_click", "ui.tutorial.space" })
            list.AddChild(Ui.Para(Ui.T(key), "ItalicLabel"));
        Body.AddChild(Ui.Scroll(list));
        var ok = Ui.Button(Ui.T("ui.common.close"), Back);
        ok.SizeFlagsHorizontal = SizeFlags.ShrinkEnd;
        Body.AddChild(ok);
    }
}
