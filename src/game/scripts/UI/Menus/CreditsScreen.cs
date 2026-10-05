using System;
using System.Text.Json.Nodes;
using Godot;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Menus;

/// <summary>
/// Credits: the game title, then the attributions compiled by tools/build_credits.py into
/// res://assets/ui/credits.json from art/source/CREDITS.md and art/source/rooms/CREDITS_*.md
/// (reference photos: title, author, licence, source), the fonts and the engine. After the ending it
/// rolls by itself (Esc / click skips); from the menu it is a scrollable list.
/// </summary>
public partial class CreditsScreen : ModalScreen
{
    /// <summary>Path of the compiled data.</summary>
    public const string DataPath = "res://assets/ui/credits.json";

    private VBoxContainer list = null!;
    private ScrollContainer scroll = null!;
    private bool built;
    private double scrollPos;
    private double hold;

    /// <summary>Roll automatically (after the ending).</summary>
    public bool Rolling { get; set; }

    /// <summary>Called when the credits are closed or finished.</summary>
    public Action? Done { get; set; }

    /// <summary>Godot constructor.</summary>
    public CreditsScreen() { PreferredSize = new Vector2(1400, 980); }

    /// <inheritdoc />
    protected override void Build()
    {
        SetTitle(Ui.T("ui.credits.title"));
        list = Ui.VBox(8);
        scroll = Ui.Scroll(list);
        Body.AddChild(scroll);
    }

    /// <inheritdoc />
    protected override void Refresh()
    {
        if (!built) Fill();
        scroll.ScrollVertical = 0;
        scrollPos = 0;
        hold = 2.5;
    }

    private void Fill()
    {
        built = true;
        var title = Ui.Label(TextService.Get("game.title", GameRuntime.Instance.Content.Data.Title).ToUpperInvariant(), "TitleLabel");
        title.HorizontalAlignment = HorizontalAlignment.Center;
        list.AddChild(title);
        var thanks = Ui.Para(Ui.T("ui.credits.thanks"), "ItalicLabel");
        thanks.HorizontalAlignment = HorizontalAlignment.Center;
        list.AddChild(thanks);
        list.AddChild(Ui.Rule());
        JsonNode? data = null;
        if (Godot.FileAccess.FileExists(DataPath))
        {
            try { data = JsonNode.Parse(Godot.FileAccess.GetFileAsString(DataPath)); }
            catch (Exception ex) { GD.PushWarning("credits.json: " + ex.Message); }
        }
        if (data?["sections"] is not JsonArray sections) return;
        foreach (var section in sections)
        {
            if (section is null) continue;
            string key = (string?)section["title_key"] ?? "";
            var heading = Ui.Label(key.Length > 0 ? Ui.T(key) : (string?)section["title"] ?? "", "HeadingLabel");
            heading.HorizontalAlignment = HorizontalAlignment.Center;
            list.AddChild(heading);
            if (section["entries"] is not JsonArray entries) continue;
            foreach (var entry in entries)
            {
                if (entry is null) continue;
                string t = (string?)entry["title"] ?? "";
                string author = (string?)entry["author"] ?? "";
                string license = (string?)entry["license"] ?? "";
                string url = (string?)entry["url"] ?? "";
                var rich = new RichTextLabel { BbcodeEnabled = true, FitContent = true, ScrollActive = false, SizeFlagsHorizontal = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore };
                rich.AddThemeFontSizeOverride("normal_font_size", 23);
                rich.AddThemeFontSizeOverride("bold_font_size", 23);
                rich.AddThemeFontSizeOverride("italics_font_size", 21);
                string line = "[center][b]" + Esc(t) + "[/b]";
                if (author.Length > 0) line += " — " + Esc(author);
                if (license.Length > 0) line += " — " + Esc(license);
                if (url.Length > 0) line += "\n[i][color=#6a5541]" + Esc(url) + "[/color][/i]";
                rich.Text = line + "[/center]";
                list.AddChild(rich);
            }
            list.AddChild(Ui.Rule());
        }
        var end = Ui.Label(Ui.T("ui.credits.thanks"), "HeadingLabel");
        end.HorizontalAlignment = HorizontalAlignment.Center;
        list.AddChild(end);
    }

    private static string Esc(string s) => s.Replace("[", "[lb]");

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        base._Process(delta);
        if (!Visible || !Rolling) return;
        if (hold > 0) { hold -= delta; return; }
        double speed = UiSettings.ReducedMotion ? 45 : 70;
        scrollPos += speed * delta;
        scroll.ScrollVertical = (int)scrollPos;
        var bar = scroll.GetVScrollBar();
        if (scrollPos > bar.MaxValue - bar.Page + 40) Back();
    }

    /// <inheritdoc />
    public override void OnKey(InputEventKey key)
    {
        if (Rolling && key.IsAction("ui_accept")) Back();
    }

    /// <inheritdoc />
    public override void Back()
    {
        base.Back();
        var done = Done;
        Done = null;
        Rolling = false;
        done?.Invoke();
    }
}
