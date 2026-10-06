using System;
using Godot;
using LastBell.Core.Content;
using LastBell.Core.Text;
using LastBell.Game.Hooks;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Cutscenes;

/// <summary>
/// Era title card (<see cref="IEraCardView"/>), shown on its own canvas layer above the world's
/// black transition fade: the year, the place (<c>era.&lt;year&gt;.card</c>) and the date. A short
/// fade with a gentle rise; with reduced motion only a plain fade with the year name
/// (travel_contract.reduced_motion). The transition waits for <c>done()</c>.
/// </summary>
public partial class EraCardView : Control, IEraCardView
{
    private Label year = null!;
    private Label place = null!;
    private Label date = null!;
    private VBoxContainer box = null!;
    private Action? done;
    private double left;
    private int phase;

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
        // Own dark backdrop: normally the world's fade is already black underneath.
        var backdrop = new ColorRect { Color = new Color(0.05f, 0.035f, 0.025f, 0.94f), MouseFilter = MouseFilterEnum.Ignore };
        backdrop.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        AddChild(backdrop);
        box = Ui.VBox(6);
        box.MouseFilter = MouseFilterEnum.Ignore;
        box.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        box.Alignment = BoxContainer.AlignmentMode.Center;
        year = Ui.Label("", "TitleLabel");
        year.AddThemeFontSizeOverride("font_size", 150);
        year.AddThemeColorOverride("font_color", UiTheme.BrassLight);
        place = Ui.Label("", "HeadingLabel");
        place.AddThemeFontSizeOverride("font_size", 58);
        place.AddThemeColorOverride("font_color", UiTheme.Cream);
        date = Ui.Label("", "SubheadingLabel");
        date.AddThemeFontSizeOverride("font_size", 36);
        date.AddThemeColorOverride("font_color", new Color(UiTheme.Cream, 0.8f));
        foreach (var l in new[] { year, place, date })
        {
            l.HorizontalAlignment = HorizontalAlignment.Center;
            box.AddChild(l);
        }
        var rule = new ColorRect { Color = new Color(UiTheme.Brass, 0.8f), CustomMinimumSize = new Vector2(360, 3), SizeFlagsHorizontal = SizeFlags.ShrinkCenter, MouseFilter = MouseFilterEnum.Ignore };
        box.AddChild(rule);
        box.MoveChild(rule, 2);
        AddChild(box);
        Visible = false;
    }

    /// <inheritdoc />
    public void Show(EraDef era, TextRef card, TextRef dateText, Action finished)
    {
        done?.Invoke(); // never leave a transition waiting
        done = finished;
        year.Text = TextService.EraYear(era.Year);
        place.Text = TextService.Get(card);
        date.Text = TextService.Get(dateText);
        place.Visible = !UiSettings.ReducedMotion || place.Text.Length > 0;
        Visible = true;
        Modulate = new Color(1, 1, 1, 0);
        box.Position = new Vector2(0, UiSettings.ReducedMotion ? 0 : 24);
        phase = 0;
        left = UiSettings.ReducedMotion ? 0.3 : 0.6;
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        if (!Visible || done is null) return;
        left -= delta;
        bool reduced = UiSettings.ReducedMotion;
        switch (phase)
        {
            case 0: // fade in
                float t = (float)Math.Clamp(1 - left / (reduced ? 0.3 : 0.6), 0, 1);
                Modulate = new Color(1, 1, 1, t);
                if (!reduced) box.Position = new Vector2(0, 24 * (1 - t));
                if (left <= 0) { phase = 1; left = reduced ? 1.0 : 1.7; }
                break;
            case 1: // hold
                if (left <= 0) { phase = 2; left = 0.35; }
                break;
            default: // fade out
                Modulate = new Color(1, 1, 1, (float)Math.Clamp(left / 0.35, 0, 1));
                if (left <= 0)
                {
                    Visible = false;
                    var callback = done;
                    done = null;
                    callback?.Invoke();
                }
                break;
        }
    }
}
