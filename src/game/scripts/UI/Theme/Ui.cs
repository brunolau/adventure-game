using System;
using Godot;
using LastBell.Core.Text;
using LastBell.Game.Runtime;

namespace LastBell.Game.UI.Theme;

/// <summary>Small factory helpers so every screen builds controls the same way (theme variations, minimum hit area).</summary>
public static class Ui
{
    /// <summary>Translated ui.csv text (with {placeholders}).</summary>
    public static string T(string key, params (string Name, string Value)[] args) => TextService.Ui(key, args);

    /// <summary>Translated Core text.</summary>
    public static string T(TextRef text) => TextService.Get(text);

    /// <summary>A label with a theme variation (TitleLabel, HeadingLabel, CaptionLabel ...).</summary>
    public static Label Label(string text, string variation = "", bool wrap = false)
    {
        var label = new Label { Text = text, ThemeTypeVariation = variation, MouseFilter = Control.MouseFilterEnum.Ignore };
        if (wrap)
        {
            label.AutowrapMode = TextServer.AutowrapMode.WordSmart;
            label.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill;
            label.CustomMinimumSize = new Vector2(80, 0);
        }
        return label;
    }

    /// <summary>A wrapped text label that fills the width.</summary>
    public static Label Para(string text, string variation = "") => Label(text, variation, wrap: true);

    /// <summary>A paper button with the minimum hit area.</summary>
    public static Button Button(string text, Action? pressed = null, string variation = "")
    {
        var button = new Button { Text = text, ThemeTypeVariation = variation, CustomMinimumSize = new Vector2(UiTheme.MinHit, UiTheme.MinHit) };
        if (pressed is not null) button.Pressed += pressed;
        button.MouseEntered += LastBell.Game.PlayerInput.WorldInput.ClearHover;
        return button;
    }

    /// <summary>A toggle button for tab rows and segmented choices.</summary>
    public static Button Tab(string text, ButtonGroup? group = null)
    {
        var button = Button(text, null, "TabButton");
        button.ToggleMode = true;
        button.ButtonGroup = group;
        return button;
    }

    /// <summary>A button whose content is a glyph (optional caption under it).</summary>
    public static Button GlyphButton(GlyphKind kind, string tooltip, Action pressed, string variation = "HudButton", float size = 72, string caption = "")
    {
        var button = Button("", pressed, variation);
        button.TooltipText = tooltip;
        button.CustomMinimumSize = new Vector2(Math.Max(UiTheme.MinHit, size), Math.Max(UiTheme.MinHit, size));
        var box = new VBoxContainer { MouseFilter = Control.MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
        box.SetAnchorsAndOffsetsPreset(Control.LayoutPreset.FullRect);
        box.AddThemeConstantOverride("separation", 0);
        bool dark = variation == "HudButton";
        float glyphSize = caption.Length > 0 ? size * 0.52f : size * 0.62f;
        var glyph = new Glyph(kind, glyphSize, dark ? UiTheme.Cream : UiTheme.Ink) { SizeFlagsHorizontal = Control.SizeFlags.ShrinkCenter };
        box.AddChild(glyph);
        if (caption.Length > 0)
        {
            var label = Label(caption, dark ? "OnDarkCaption" : "CaptionLabel");
            label.HorizontalAlignment = HorizontalAlignment.Center;
            label.AddThemeFontSizeOverride("font_size", 19);
            box.AddChild(label);
        }
        button.AddChild(box);
        button.MouseEntered += () => glyph.Color = dark ? UiTheme.BrassLight : UiTheme.Accent;
        button.MouseExited += () => glyph.Color = dark ? UiTheme.Cream : UiTheme.Ink;
        return button;
    }

    /// <summary>The visible close cross of a modal (top-right).</summary>
    public static Button CloseButton(Action pressed)
    {
        var button = GlyphButton(GlyphKind.Close, T("ui.common.close"), pressed, "FlatButton", UiTheme.MinHit);
        return button;
    }

    /// <summary>Margin container helper.</summary>
    public static MarginContainer Margin(Control child, int all)
    {
        var margin = new MarginContainer();
        foreach (var side in new[] { "margin_left", "margin_right", "margin_top", "margin_bottom" }) margin.AddThemeConstantOverride(side, all);
        margin.AddChild(child);
        return margin;
    }

    /// <summary>A vertical box with a given separation.</summary>
    public static VBoxContainer VBox(int separation = 12)
    {
        var box = new VBoxContainer();
        box.AddThemeConstantOverride("separation", separation);
        return box;
    }

    /// <summary>A horizontal box with a given separation.</summary>
    public static HBoxContainer HBox(int separation = 12)
    {
        var box = new HBoxContainer();
        box.AddThemeConstantOverride("separation", separation);
        return box;
    }

    /// <summary>An expanding spacer.</summary>
    public static Control Spacer(bool vertical = false)
    {
        var c = new Control { MouseFilter = Control.MouseFilterEnum.Ignore };
        if (vertical) c.SizeFlagsVertical = Control.SizeFlags.ExpandFill;
        else c.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill;
        return c;
    }

    /// <summary>A vertical scroll area that fills its parent.</summary>
    public static ScrollContainer Scroll(Control content)
    {
        var scroll = new ScrollContainer
        {
            HorizontalScrollMode = ScrollContainer.ScrollMode.Disabled,
            SizeFlagsVertical = Control.SizeFlags.ExpandFill,
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
            FollowFocus = true,
        };
        content.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill;
        scroll.AddChild(content);
        return scroll;
    }

    /// <summary>A thin horizontal rule.</summary>
    public static Control Rule()
    {
        var rule = new ColorRect { Color = new Color(UiTheme.PaperEdge, 0.45f), CustomMinimumSize = new Vector2(0, 2), MouseFilter = Control.MouseFilterEnum.Ignore };
        return rule;
    }

    /// <summary>Gives keyboard focus at the end of the frame, if the control is still shown by then.</summary>
    public static void FocusLater(Control? control)
    {
        if (control is null) return;
        Callable.From(() =>
        {
            if (GodotObject.IsInstanceValid(control) && control.IsInsideTree() && control.IsVisibleInTree()) control.GrabFocus();
        }).CallDeferred();
    }

    /// <summary>Removes and frees every child.</summary>
    public static void Clear(Node node)
    {
        foreach (var child in node.GetChildren())
        {
            node.RemoveChild(child);
            child.QueueFree();
        }
    }

    /// <summary>Splits a fallback "SPEAKER: text" into the speaker id (if the id is known) and the text (TEXT-04).</summary>
    public static (string? SpeakerId, string Text) SplitSpeaker(TextRef text)
    {
        string shown = TextService.Get(text);
        string fallback = text.Fallback ?? "";
        int colon = fallback.IndexOf(':');
        if (colon <= 0) return (null, shown);
        string speaker = fallback[..colon].Trim();
        var content = GameRuntime.Instance.Content;
        bool known = content.FindCharacter(speaker) is not null || content.Data.NonActorSpeakers.ContainsKey(speaker);
        if (!known) return (null, shown);
        // The table text has no prefix (TEXT-04); the fallback still carries it.
        if (shown == fallback) shown = fallback[(colon + 1)..].Trim();
        return (speaker, shown);
    }

    /// <summary>Display name of a speaker id (actors and non-actor speakers).</summary>
    public static string SpeakerName(string speakerId) => TextService.Get(GameRuntime.Instance.Content.SpeakerName(speakerId));
}
