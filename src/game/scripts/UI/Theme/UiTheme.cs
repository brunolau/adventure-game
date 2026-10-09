using Godot;

namespace LastBell.Game.UI.Theme;

/// <summary>
/// The UI look of the game: a warm, readable "paper and ink" theme for a hand-painted adventure.
/// Paper cards with dark ink text for menus and modals, dark translucent wood for the HUD strip and
/// subtitles, brass accents and a teal focus ring (keyboard focus is always clearly visible).
/// Built in code as a Godot <see cref="Godot.Theme"/> resource and assigned to the UI root; every
/// UI control inherits it. Fonts: Alegreya and Alegreya Sans (SIL OFL 1.1, assets/ui/fonts).
/// All sizes are logical canvas pixels at 1920x1080; the HUD scale setting scales the whole UI.
/// </summary>
public static class UiTheme
{
    /// <summary>Minimum hit area in canvas px (66 = 44 physical px at 1280x720).</summary>
    public const int MinHit = 66;

    /// <summary>Body text size.</summary>
    public const int BodySize = 28;

    /// <summary>Small caption size.</summary>
    public const int CaptionSize = 23;

    /// <summary>Section heading size.</summary>
    public const int HeadingSize = 38;

    /// <summary>Screen title size.</summary>
    public const int TitleSize = 52;

    // ------------------------------------------------------------------ palette

    /// <summary>Dark ink (text on paper).</summary>
    public static readonly Color Ink = new("2e2118");
    /// <summary>Softer ink for secondary text.</summary>
    public static readonly Color InkSoft = new("6a5541");
    /// <summary>Paper (panels).</summary>
    public static readonly Color Paper = new("f4e9d2");
    /// <summary>Deeper paper (buttons, cards).</summary>
    public static readonly Color PaperDeep = new("e7d5b1");
    /// <summary>Paper edge / border.</summary>
    public static readonly Color PaperEdge = new("a9834f");
    /// <summary>Dark wood (HUD, subtitles).</summary>
    public static readonly Color Wood = new("1f1712");
    /// <summary>Cream text on dark surfaces.</summary>
    public static readonly Color Cream = new("f7eedc");
    /// <summary>Brass accent.</summary>
    public static readonly Color Brass = new("c9973a");
    /// <summary>Light brass (hover borders, speaker names).</summary>
    public static readonly Color BrassLight = new("e9c46f");
    /// <summary>Brick red accent (titles, current markers).</summary>
    public static readonly Color Accent = new("a5432b");
    /// <summary>Teal keyboard-focus ring.</summary>
    public static readonly Color Focus = new("1f7f7a");
    /// <summary>Muted text (disabled, unvisited).</summary>
    public static readonly Color Muted = new("9e8e78");
    /// <summary>Success green.</summary>
    public static readonly Color Good = new("4f7a3a");

    // ------------------------------------------------------------------ fonts

    private static Font? body;
    private static Font? bodyMedium;
    private static Font? bodyBold;
    private static Font? bodyItalic;
    private static Font? heading;

    /// <summary>Body font (Alegreya Sans Regular).</summary>
    public static Font Body => body ??= LoadFont("AlegreyaSans-Regular.ttf");

    /// <summary>Button font (Alegreya Sans Medium).</summary>
    public static Font BodyMedium => bodyMedium ??= LoadFont("AlegreyaSans-Medium.ttf");

    /// <summary>Bold body font (Alegreya Sans Bold).</summary>
    public static Font BodyBold => bodyBold ??= LoadFont("AlegreyaSans-Bold.ttf");

    /// <summary>Italic body font (look texts, quotes).</summary>
    public static Font BodyItalic => bodyItalic ??= LoadFont("AlegreyaSans-Italic.ttf");

    /// <summary>Heading font (Alegreya, weight 700).</summary>
    public static Font Heading => heading ??= MakeHeading();

    /// <summary>Heading font with lining figures (OpenType lnum): Alegreya's default old-style 0 reads as the letter O
    /// on number dials (playtest PT-F04).</summary>
    public static Font HeadingLining => headingLining ??= new FontVariation
    {
        BaseFont = Heading,
        OpentypeFeatures = new Godot.Collections.Dictionary { { "lnum", 1 } },
    };

    private static Font? headingLining;

    private static Font LoadFont(string file)
    {
        string path = "res://assets/ui/fonts/" + file;
        if (ResourceLoader.Exists(path) && GD.Load<Font>(path) is { } font) return font;
        GD.PushWarning("UiTheme: missing font " + path + " (using the engine default)");
        return ThemeDB.FallbackFont;
    }

    private static Font MakeHeading()
    {
        string path = "res://assets/ui/fonts/Alegreya-Variable.ttf";
        if (!ResourceLoader.Exists(path) || GD.Load<Font>(path) is not { } baseFont) return BodyBold;
        var variation = new FontVariation { BaseFont = baseFont };
        variation.VariationOpentype = new Godot.Collections.Dictionary { { "wght", 700 } };
        return variation;
    }

    // ------------------------------------------------------------------ style boxes

    /// <summary>A rounded flat style box.</summary>
    public static StyleBoxFlat Box(Color bg, Color border, int borderWidth = 2, int radius = 12, float margin = 16)
    {
        var box = new StyleBoxFlat { BgColor = bg, BorderColor = border, AntiAliasing = true };
        box.SetBorderWidthAll(borderWidth);
        box.SetCornerRadiusAll(radius);
        box.SetContentMarginAll(margin);
        return box;
    }

    /// <summary>Paper panel with a soft drop shadow (modals, menus).</summary>
    public static StyleBoxFlat PaperPanel(float margin = 30)
    {
        var box = Box(Paper, PaperEdge, 3, 18, margin);
        box.ShadowColor = new Color(0, 0, 0, 0.38f);
        box.ShadowSize = 18;
        box.ShadowOffset = new Vector2(0, 8);
        return box;
    }

    /// <summary>Dark translucent wood surface (HUD strip, subtitle panel, tags).</summary>
    public static StyleBoxFlat DarkPanel(float alpha = 0.84f, float margin = 18, int radius = 14)
    {
        var box = Box(new Color(Wood, alpha), new Color(Brass, 0.55f), 2, radius, margin);
        return box;
    }

    /// <summary>Card inside a paper panel (list rows, slots).</summary>
    public static StyleBoxFlat Card(bool highlighted = false) =>
        Box(highlighted ? new Color("fbf3e2") : new Color("efe0c2"), highlighted ? Brass : new Color(PaperEdge, 0.6f), highlighted ? 3 : 2, 12, 16);

    private static StyleBoxFlat FocusRing(int radius = 14)
    {
        var box = new StyleBoxFlat { DrawCenter = false, BorderColor = Focus, AntiAliasing = true };
        box.SetBorderWidthAll(4);
        box.SetCornerRadiusAll(radius);
        box.SetExpandMarginAll(4);
        return box;
    }

    // ------------------------------------------------------------------ the theme

    private static Godot.Theme? theme;

    /// <summary>The shared theme (built once).</summary>
    public static Godot.Theme Theme => theme ??= Build();

    private static Godot.Theme Build()
    {
        var t = new Godot.Theme { DefaultFont = Body, DefaultFontSize = BodySize };

        // Labels
        t.SetColor("font_color", "Label", Ink);
        t.SetFontSize("font_size", "Label", BodySize);
        t.SetConstant("line_spacing", "Label", 2);
        Variation(t, "TitleLabel", "Label", Heading, TitleSize, Accent);
        Variation(t, "HeadingLabel", "Label", Heading, HeadingSize, Ink);
        Variation(t, "SubheadingLabel", "Label", BodyBold, 30, InkSoft);
        Variation(t, "CaptionLabel", "Label", Body, CaptionSize, InkSoft);
        Variation(t, "ItalicLabel", "Label", BodyItalic, BodySize, Ink);
        Variation(t, "OnDarkLabel", "Label", Body, BodySize, Cream);
        Variation(t, "OnDarkCaption", "Label", Body, CaptionSize, new Color(Cream, 0.8f));
        Variation(t, "SpeakerLabel", "Label", BodyBold, 28, BrassLight);

        // RichTextLabel
        t.SetColor("default_color", "RichTextLabel", Ink);
        t.SetFont("normal_font", "RichTextLabel", Body);
        t.SetFont("bold_font", "RichTextLabel", BodyBold);
        t.SetFont("italics_font", "RichTextLabel", BodyItalic);
        t.SetFontSize("normal_font_size", "RichTextLabel", BodySize);
        t.SetFontSize("bold_font_size", "RichTextLabel", BodySize);
        t.SetFontSize("italics_font_size", "RichTextLabel", BodySize);

        // Buttons (paper)
        t.SetFont("font", "Button", BodyMedium);
        t.SetFontSize("font_size", "Button", BodySize);
        t.SetColor("font_color", "Button", Ink);
        t.SetColor("font_hover_color", "Button", Ink);
        t.SetColor("font_pressed_color", "Button", Ink);
        t.SetColor("font_focus_color", "Button", Ink);
        t.SetColor("font_hover_pressed_color", "Button", Ink);
        t.SetColor("font_disabled_color", "Button", Muted);
        t.SetColor("icon_normal_color", "Button", Ink);
        t.SetColor("icon_hover_color", "Button", Ink);
        t.SetColor("icon_pressed_color", "Button", Ink);
        t.SetColor("icon_focus_color", "Button", Ink);
        t.SetConstant("h_separation", "Button", 12);
        var normal = Box(PaperDeep, new Color(PaperEdge, 0.85f), 2, 12, 14);
        normal.ContentMarginLeft = normal.ContentMarginRight = 22;
        var hover = Box(new Color("fbf2df"), BrassLight, 3, 12, 14);
        hover.ContentMarginLeft = hover.ContentMarginRight = 22;
        var pressed = Box(new Color("d9c194"), Brass, 3, 12, 14);
        pressed.ContentMarginLeft = pressed.ContentMarginRight = 22;
        var disabled = Box(new Color(PaperDeep, 0.55f), new Color(PaperEdge, 0.35f), 2, 12, 14);
        disabled.ContentMarginLeft = disabled.ContentMarginRight = 22;
        t.SetStylebox("normal", "Button", normal);
        t.SetStylebox("hover", "Button", hover);
        t.SetStylebox("pressed", "Button", pressed);
        t.SetStylebox("hover_pressed", "Button", pressed);
        t.SetStylebox("disabled", "Button", disabled);
        t.SetStylebox("focus", "Button", FocusRing());

        // Toggle / tab / segment buttons: pressed = selected (brick accent)
        t.SetTypeVariation("TabButton", "Button");
        var tabNormal = Box(new Color(PaperDeep, 0.6f), new Color(PaperEdge, 0.5f), 2, 12, 12);
        tabNormal.ContentMarginLeft = tabNormal.ContentMarginRight = 22;
        var tabSelected = Box(Accent, new Color("7a2e1c"), 2, 12, 12);
        tabSelected.ContentMarginLeft = tabSelected.ContentMarginRight = 22;
        var tabHover = Box(new Color("fbf2df"), BrassLight, 3, 12, 12);
        tabHover.ContentMarginLeft = tabHover.ContentMarginRight = 22;
        t.SetStylebox("normal", "TabButton", tabNormal);
        t.SetStylebox("hover", "TabButton", tabHover);
        t.SetStylebox("pressed", "TabButton", tabSelected);
        t.SetStylebox("hover_pressed", "TabButton", tabSelected);
        t.SetColor("font_pressed_color", "TabButton", Cream);
        t.SetColor("font_hover_pressed_color", "TabButton", Cream);
        t.SetColor("icon_pressed_color", "TabButton", Cream);

        // Dark HUD buttons
        t.SetTypeVariation("HudButton", "Button");
        var hudNormal = Box(new Color(Wood, 0.78f), new Color(Brass, 0.6f), 2, 16, 8);
        var hudHover = Box(new Color("3a2b1f", 0.92f), BrassLight, 3, 16, 8);
        var hudPressed = Box(new Color("5a4126", 0.95f), BrassLight, 3, 16, 8);
        t.SetStylebox("normal", "HudButton", hudNormal);
        t.SetStylebox("hover", "HudButton", hudHover);
        t.SetStylebox("pressed", "HudButton", hudPressed);
        t.SetStylebox("hover_pressed", "HudButton", hudPressed);
        t.SetStylebox("disabled", "HudButton", Box(new Color(Wood, 0.4f), new Color(Brass, 0.25f), 2, 16, 8));
        t.SetColor("font_color", "HudButton", Cream);
        t.SetColor("font_hover_color", "HudButton", Cream);
        t.SetColor("font_pressed_color", "HudButton", Cream);
        t.SetColor("font_focus_color", "HudButton", Cream);
        t.SetColor("font_hover_pressed_color", "HudButton", Cream);
        t.SetColor("icon_normal_color", "HudButton", Cream);
        t.SetColor("icon_hover_color", "HudButton", BrassLight);
        t.SetColor("icon_pressed_color", "HudButton", BrassLight);
        t.SetFontSize("font_size", "HudButton", 22);

        // Flat link-like buttons (close crosses, small actions)
        t.SetTypeVariation("FlatButton", "Button");
        var flat = Box(new Color(0, 0, 0, 0), new Color(0, 0, 0, 0), 0, 12, 10);
        t.SetStylebox("normal", "FlatButton", flat);
        t.SetStylebox("hover", "FlatButton", Box(new Color(Brass, 0.18f), new Color(Brass, 0.6f), 2, 12, 10));
        t.SetStylebox("pressed", "FlatButton", Box(new Color(Brass, 0.3f), Brass, 2, 12, 10));
        t.SetStylebox("hover_pressed", "FlatButton", Box(new Color(Brass, 0.3f), Brass, 2, 12, 10));

        // Panels
        t.SetStylebox("panel", "PanelContainer", PaperPanel());
        t.SetTypeVariation("DarkPanel", "PanelContainer");
        t.SetStylebox("panel", "DarkPanel", DarkPanel());
        t.SetTypeVariation("CardPanel", "PanelContainer");
        t.SetStylebox("panel", "CardPanel", Card());
        t.SetTypeVariation("HighlightCard", "PanelContainer");
        t.SetStylebox("panel", "HighlightCard", Card(true));
        t.SetStylebox("panel", "Panel", PaperPanel());

        // Containers
        t.SetConstant("separation", "VBoxContainer", 12);
        t.SetConstant("separation", "HBoxContainer", 12);
        t.SetConstant("h_separation", "GridContainer", 12);
        t.SetConstant("v_separation", "GridContainer", 12);
        t.SetConstant("h_separation", "HFlowContainer", 12);
        t.SetConstant("v_separation", "HFlowContainer", 12);

        // Scroll bars: thick and easy to grab
        foreach (var bar in new[] { "VScrollBar", "HScrollBar" })
        {
            t.SetStylebox("scroll", bar, Box(new Color(PaperEdge, 0.18f), new Color(0, 0, 0, 0), 0, 8, 6));
            t.SetStylebox("grabber", bar, Box(new Color(PaperEdge, 0.75f), new Color(0, 0, 0, 0), 0, 8, 6));
            t.SetStylebox("grabber_highlight", bar, Box(Brass, new Color(0, 0, 0, 0), 0, 8, 6));
            t.SetStylebox("grabber_pressed", bar, Box(Accent, new Color(0, 0, 0, 0), 0, 8, 6));
        }

        // Slider: thick track, big round grabber
        var track = Box(new Color(PaperEdge, 0.35f), new Color(0, 0, 0, 0), 0, 8, 0);
        track.ContentMarginTop = track.ContentMarginBottom = 7;
        var fill = Box(Brass, new Color(0, 0, 0, 0), 0, 8, 0);
        fill.ContentMarginTop = fill.ContentMarginBottom = 7;
        t.SetStylebox("slider", "HSlider", track);
        t.SetStylebox("grabber_area", "HSlider", fill);
        t.SetStylebox("grabber_area_highlight", "HSlider", fill);
        t.SetStylebox("focus", "HSlider", FocusRing(10));
        t.SetIcon("grabber", "HSlider", Disc(40, Accent, Paper));
        t.SetIcon("grabber_highlight", "HSlider", Disc(40, new Color("c4553a"), Paper));

        // Tooltips
        t.SetStylebox("panel", "TooltipPanel", DarkPanel(0.95f, 12, 10));
        t.SetColor("font_color", "TooltipLabel", Cream);
        t.SetFontSize("font_size", "TooltipLabel", 24);
        // Touch mode: a finger leaves no pointer behind, but Godot keeps the last button it touched "hovered" (the mouse
        // it makes of the finger stays there), and the hover look reads as a selection. Hover looks like normal there.
        if (LastBell.Game.Runtime.TouchMode.Enabled)
        {
            foreach (var type in new[] { "Button", "TabButton", "HudButton", "FlatButton" })
                t.SetStylebox("hover", type, t.GetStylebox("normal", type));
            t.SetColor("icon_hover_color", "HudButton", Cream);
        }
        return t;
    }

    private static void Variation(Godot.Theme t, string name, string baseType, Font font, int size, Color color)
    {
        t.SetTypeVariation(name, baseType);
        t.SetFont("font", name, font);
        t.SetFontSize("font_size", name, size);
        t.SetColor("font_color", name, color);
    }

    /// <summary>A filled disc texture with a ring (slider grabbers, markers).</summary>
    public static Texture2D Disc(int size, Color fill, Color ring)
    {
        var image = Image.CreateEmpty(size, size, false, Image.Format.Rgba8);
        float r = size / 2f;
        for (int y = 0; y < size; y++)
        for (int x = 0; x < size; x++)
        {
            float d = new Vector2(x + 0.5f - r, y + 0.5f - r).Length();
            Color c = d <= r - 5 ? fill : d <= r - 1 ? ring : new Color(0, 0, 0, 0);
            if (d > r - 1 && d <= r) c = new Color(ring, r - d);
            image.SetPixel(x, y, c);
        }
        return ImageTexture.CreateFromImage(image);
    }
}
