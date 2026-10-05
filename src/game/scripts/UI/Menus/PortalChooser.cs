using System.Linq;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.Text;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Menus;

/// <summary>
/// The chronometer's era chooser at an open time node (key T or the clock in the HUD): Core's
/// <see cref="Navigation.PortalTargets"/> as buttons (year, place, date); the current era and the
/// still closed ones are shown but disabled. Choosing calls <see cref="Navigation.UsePortal"/>; the
/// world runtime runs the transition and the era card. Travel is free and always reversible.
/// </summary>
public partial class PortalChooser : ModalScreen
{
    private VBoxContainer list = null!;

    /// <summary>Godot constructor.</summary>
    public PortalChooser() { PreferredSize = new Vector2(980, 820); FitHeight = true; }

    /// <inheritdoc />
    protected override void Build()
    {
        SetTitle(Ui.T("ui.travel.choose_era"));
        list = Ui.VBox(12);
        Body.AddChild(Ui.Scroll(list));
        // FitHeight measures the list, not the scroll area (whose minimum height is 0): without this the
        // panel shrank to the title row and no era button was visible (docs/MILESTONE2.md, bug M2-01).
        FitTarget = list;
    }

    /// <inheritdoc />
    protected override void Refresh()
    {
        Ui.Clear(list);
        var game = GameRuntime.Instance;
        var targets = Navigation.PortalTargets(game.Content, game.State);
        foreach (var era in game.Content.Eras.OrderBy(e => e.Year))
        {
            var target = targets.FirstOrDefault(t => t.Year == era.Year);
            bool current = era.Year == game.State.Era;
            bool unlocked = Navigation.IsEraUnlocked(game.Content, game.State, era.Year);
            string text = era.Year + " · " + TextService.Get(TextKeys.CardOf(era)) + " · " + TextService.Get(TextKeys.DateOf(era));
            string note = current ? Ui.T("ui.travel.era_current") : target is null ? Ui.T(unlocked ? "ui.map.unreachable" : "ui.travel.era_locked") : "";
            if (!unlocked && !current) text = era.Year + " · " + Ui.T("ui.travel.era_locked");
            int year = era.Year;
            var b = Ui.Button(text + (note.Length > 0 && unlocked ? "  (" + note + ")" : ""), () =>
            {
                Back();
                game.Update(s => Navigation.UsePortal(game.Content, s, year));
            });
            b.Alignment = HorizontalAlignment.Left;
            b.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            b.Disabled = target is null;
            if (target is not null) b.AddThemeFontOverride("font", UiTheme.BodyBold);
            list.AddChild(b);
        }
    }
}
