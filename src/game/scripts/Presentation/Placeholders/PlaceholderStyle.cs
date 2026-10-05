using Godot;

namespace LastBell.Game.Presentation.Placeholders;

/// <summary>Shared look of the temporary placeholder UI (replaced by the UI agent's screens).</summary>
internal static class PlaceholderStyle
{
    /// <summary>A dark rounded panel.</summary>
    public static PanelContainer Panel(float alpha = 0.88f)
    {
        var p = new PanelContainer();
        var style = new StyleBoxFlat { BgColor = new Color(0.06f, 0.07f, 0.1f, alpha) };
        style.SetCornerRadiusAll(10);
        style.SetContentMarginAll(14);
        style.BorderColor = new Color(1f, 0.83f, 0.45f, 0.5f);
        style.SetBorderWidthAll(2);
        p.AddThemeStyleboxOverride("panel", style);
        return p;
    }

    /// <summary>A label.</summary>
    public static Label Label(string text, int size = 24, Color? color = null)
    {
        var l = new Label { Text = text, MouseFilter = Control.MouseFilterEnum.Ignore };
        l.AddThemeFontSizeOverride("font_size", size);
        l.AddThemeColorOverride("font_color", color ?? Colors.White);
        return l;
    }

    /// <summary>A keyboard-focusable button.</summary>
    public static Button Button(string text, int size = 24)
    {
        var b = new Button { Text = text, FocusMode = Control.FocusModeEnum.All };
        b.AddThemeFontSizeOverride("font_size", size);
        return b;
    }
}
