using System.Collections.Generic;
using System.Linq;
using Godot;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Menus;

/// <summary>Help: the controls (mouse and keyboard; every action has a keyboard alternative, AT19) and the first-start tips.</summary>
public partial class HelpScreen : ModalScreen
{
    /// <summary>The control lines (ui.csv), shared with the settings' controls tab.</summary>
    public static readonly string[] ControlKeys =
    {
        "ui.controls.left_click", "ui.controls.right_click", "ui.controls.right_click_selected", "ui.controls.space", "ui.controls.double_click",
        "ui.controls.inventory", "ui.controls.journal", "ui.controls.map", "ui.controls.hint", "ui.controls.travel",
        "ui.controls.escape", "ui.controls.enter", "ui.controls.shift_enter", "ui.controls.tab", "ui.controls.back",
    };

    /// <summary>
    /// The controls of a phone or tablet (<see cref="TouchMode"/>): key, Slovak and English text. The rows wait in
    /// docs/writing/out_v6/ui_touch.csv for the text owner; until they are in ui.csv the text comes from here.
    /// </summary>
    public static readonly (string Key, string Sk, string En)[] TouchControls =
    {
        ("ui.controls.touch_tap", "Ťuknutie – akcia, chôdza, rozhovor", "Tap – action, walk, talk"),
        ("ui.controls.touch_hold", "Podržanie prsta – prezrieť objekt, na voľnom mieste otvoriť inventár",
            "Hold your finger down – look at an object; on an empty spot, open the Inventory"),
        ("ui.controls.touch_hold_selected", "Podržanie prsta s vybratým predmetom – zrušiť výber",
            "Hold with an item selected – cancel the selection"),
        ("ui.controls.touch_slide", "Prst položený na obraze – názov miesta pod ním; po posunutí prsta sa pri zdvihnutí nič nevykoná",
            "A finger resting on the picture – the name of the place under it; lifting after a slide does nothing"),
        ("ui.controls.touch_eye", "Tlačidlo Oko alebo dva prsty na obraze – značky na všetkých miestach, na ktoré sa dá ťuknúť",
            "The Eye button or two fingers on the picture – markers on every place you can tap"),
        ("ui.controls.touch_double_tap", "Dvojité ťuknutie – preskočiť chôdzu (Adam je hneď na mieste)",
            "Double tap – skip walking (Adam is there at once)"),
        ("ui.controls.touch_item", "Predmet – ťukni naň v inventári, potom na miesto v scéne; podržaním prsta na predmete si ho prezrieš",
            "Items – tap one in the Inventory, then a place in the scene; hold your finger on an item to look at it"),
        ("ui.controls.touch_line", "Ťuknutie počas rozhovoru – ďalší titulok", "Tap during a conversation – next subtitle"),
        ("ui.controls.touch_back", "Tlačidlo Späť – preskočiť titulok, zavrieť panel alebo pozastaviť hru",
            "Back button – skip a subtitle, close a panel or pause the game"),
    };

    /// <summary>The control lines of this device as display text: mouse and keyboard, or touch.</summary>
    public static IEnumerable<string> ControlLines() => TouchMode.Enabled
        ? TouchControls.Select(t => TouchMode.Text(t.Key, t.Sk, t.En))
        : ControlKeys.Select(key => Ui.T(key));

    /// <summary>Godot constructor.</summary>
    public HelpScreen() { PreferredSize = new Vector2(1300, 900); }

    /// <inheritdoc />
    protected override void Build()
    {
        SetTitle(Ui.T("ui.controls.title"));
        var list = Ui.VBox(10);
        foreach (var line in ControlLines()) list.AddChild(Ui.Para("• " + line));
        list.AddChild(Ui.Rule());
        foreach (var key in TipsOverlay.Keys.Where(k => k != "ui.tutorial.help_menu"))
            list.AddChild(Ui.Para(Ui.T(key), "ItalicLabel"));
        Body.AddChild(Ui.Scroll(list));
        var ok = Ui.Button(Ui.T("ui.common.close"), Back);
        ok.SizeFlagsHorizontal = SizeFlags.ShrinkEnd;
        Body.AddChild(ok);
    }
}
