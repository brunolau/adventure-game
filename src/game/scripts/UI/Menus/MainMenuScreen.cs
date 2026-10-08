using System;
using Godot;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Menus;

/// <summary>
/// Title screen (claims UiPanel.MainMenu, so Main does not auto-start): POSLEDNÝ ZVONEC with the
/// brass ring of four symbols, then Continue (hidden without a valid save), New game (then the difficulty picker), Load,
/// Settings, Album, Credits, Quit. The background is a painted room (dimmed) until the dedicated
/// "closed bag on a table" painting exists. Phones and tablets (<see cref="TouchMode"/>) get two columns, the emblem
/// and the title beside the buttons, and the buttons scroll if they must: at the 200 % HUD scale of a phone the
/// logical screen is 960x540, less than the one-column screen is high.
/// </summary>
public partial class MainMenuScreen : ModalScreen
{
    private Button continueButton = null!;
    private Button newGame = null!;
    private Button album = null!;
    private TextureRect backdrop = null!;
    private SlotInfo? newest;

    /// <summary>Godot constructor.</summary>
    public MainMenuScreen()
    {
        PreferredSize = TouchMode.Enabled ? new Vector2(1500, 900) : new Vector2(760, 1000);
        Closable = false;
        Dim = 0.35f;
    }

    /// <inheritdoc />
    protected override void Build()
    {
        backdrop = new TextureRect
        {
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize,
            StretchMode = TextureRect.StretchModeEnum.KeepAspectCovered,
            MouseFilter = MouseFilterEnum.Ignore,
            Modulate = new Color(0.75f, 0.68f, 0.6f),
        };
        backdrop.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        // The natural S01 painting (release exports do not ship the template paintings in assets/bg, docs/BUILD.md).
        string natural = "res://assets/" + (LastBell.Game.World.RoomBlocking.For("S01")?.Background ?? "bg_natural/S01.webp");
        foreach (var path in new[] { "res://assets/ui/menu_background.webp", natural, "res://assets/bg_natural/S01.webp", "res://assets/bg/S01.webp", "res://assets/bg/S05.webp" })
        {
            if (ResourceLoader.Exists(path)) { backdrop.Texture = GD.Load<Texture2D>(path); break; }
        }
        var fill = new ColorRect { Color = new Color("2a1f18"), MouseFilter = MouseFilterEnum.Ignore };
        fill.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        AddChild(fill);
        MoveChild(fill, 0);
        AddChild(backdrop);
        MoveChild(backdrop, 1);

        Panel.AddThemeStyleboxOverride("panel", UiTheme.Box(new Color(UiTheme.Wood, 0.72f), new Color(UiTheme.Brass, 0.6f), 2, 22, 34));
        bool columns = TouchMode.Enabled;
        var emblem = new Emblem { CustomMinimumSize = new Vector2(0, columns ? 140 : 170) };
        var title = Ui.Label(TextService.Get("game.title", GameRuntime.Instance.Content?.Data.Title ?? ""), "TitleLabel");
        title.HorizontalAlignment = HorizontalAlignment.Center;
        title.AddThemeFontSizeOverride("font_size", columns ? 50 : 64);
        title.AddThemeColorOverride("font_color", UiTheme.BrassLight);
        title.Text = title.Text.ToUpperInvariant();
        var head = columns ? Ui.VBox(10) : Body;
        head.AddChild(emblem);
        head.AddChild(title);
        if (!columns) Body.AddChild(Ui.Spacer(vertical: true));
        var list = Ui.VBox(12);
        continueButton = Add(list, "ui.menu.continue", Continue);
        continueButton.AddThemeFontOverride("font", UiTheme.BodyBold);
        newGame = Add(list, "ui.menu.new_game", NewGame);
        Add(list, "ui.menu.load", () => UiRoot.Instance?.OpenSaveLoad(false));
        Add(list, "ui.menu.settings", () => UiRoot.Instance?.OpenSettings());
        album = Add(list, "ui.menu.album", OpenAlbum);
        Add(list, "ui.menu.credits", () => UiRoot.Instance?.OpenCredits(rolling: false));
        Add(list, "ui.menu.quit", () => UiRoot.Instance?.Confirm(Ui.T("ui.menu.quit_confirm"), Ui.T("ui.menu.quit"), () => GetTree().Quit()));
        if (columns)
        {
            // Left: emblem, title on two lines, version. Right: the buttons in a scroll area. The title breaks at its
            // last space by hand: an autowrapped label reports a huge minimum height while it is still narrow, and the
            // panel would keep that height.
            emblem.SizeFlagsVertical = SizeFlags.ExpandFill;
            TitleRow.Visible = false; // the empty title row of the base screen: its height belongs to the buttons here
            int space = title.Text.LastIndexOf(' ');
            if (space > 0) title.Text = title.Text[..space] + '\n' + title.Text[(space + 1)..];
            head.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            head.SizeFlagsStretchRatio = 0.8f;
            var row = Ui.HBox(28);
            row.SizeFlagsVertical = SizeFlags.ExpandFill;
            row.AddChild(head);
            var scroll = Ui.Scroll(list);
            list.SizeFlagsVertical = SizeFlags.ExpandFill;
            list.Alignment = BoxContainer.AlignmentMode.Center;
            row.AddChild(scroll);
            Body.AddChild(row);
        }
        else
        {
            Body.AddChild(list);
            Body.AddChild(Ui.Spacer(vertical: true));
        }
        // The game (release) version (ISSUES M5-03): project.godot application/config/version is the single source; the
        // export presets leave their version fields empty, so the exe takes the same number. game.json's version is the
        // content data version and stays internal.
        var version = Ui.Label(Ui.T("ui.menu.version", ("version", GameVersion)), "OnDarkCaption");
        version.HorizontalAlignment = HorizontalAlignment.Center;
        head.AddChild(version);
    }

    /// <summary>The game version from project.godot (application/config/version), e.g. "0.1.0".</summary>
    public static string GameVersion => ProjectSettings.GetSetting("application/config/version", "").AsString();

    private static Button Add(VBoxContainer list, string key, Action pressed)
    {
        var b = Ui.Button(Ui.T(key), pressed);
        b.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        list.AddChild(b);
        return b;
    }

    /// <inheritdoc />
    protected override void Refresh()
    {
        newest = SaveSlots.Newest();
        continueButton.Visible = newest is not null;
        album.Visible = newest?.State is { } s && (s.SideRewards.Length > 0 || s.IsDone(GameRuntime.Instance.Content.Data.Postgame.Unlock));
    }

    /// <inheritdoc />
    protected override Control? InitialFocus() => continueButton.Visible ? continueButton : newGame;

    /// <inheritdoc />
    public override void Back() { } // the title screen stays until a game starts

    private void Continue()
    {
        if (newest is null) return;
        GameRuntime.Instance.Load(newest.Slot);
    }

    private void NewGame()
    {
        // Then the short difficulty step (DifficultyPicker); the game starts with the chosen difficulty.
        if (SaveSlots.AnyValid())
            UiRoot.Instance?.Confirm(Ui.T("ui.menu.new_game_confirm"), Ui.T("ui.menu.new_game"), () => UiRoot.Instance?.OpenNewGame());
        else UiRoot.Instance?.OpenNewGame();
    }

    private void OpenAlbum()
    {
        if (newest?.State is { } state) UiRoot.Instance?.OpenAlbum(state);
    }
}

/// <summary>The title emblem: a brass ring carrying four simple symbols (circle, triangle, square, double cross).</summary>
public partial class Emblem : Control
{
    /// <inheritdoc />
    public override void _Draw()
    {
        var c = Size / 2;
        float r = Math.Min(Size.X, Size.Y) * 0.42f;
        DrawCircle(c, r + 6, new Color(0, 0, 0, 0.25f));
        DrawArc(c, r, 0, Mathf.Tau, 64, UiTheme.Brass, 9, true);
        DrawArc(c, r - 12, 0, Mathf.Tau, 64, new Color(UiTheme.BrassLight, 0.7f), 2, true);
        float s = r * 0.26f;
        var col = UiTheme.BrassLight;
        // top: circle
        DrawArc(c + new Vector2(0, -r * 0.55f), s * 0.55f, 0, Mathf.Tau, 32, col, 4, true);
        // right: triangle
        var t = c + new Vector2(r * 0.55f, 0);
        DrawPolyline(new[] { t + new Vector2(0, -s * 0.6f), t + new Vector2(s * 0.6f, s * 0.45f), t + new Vector2(-s * 0.6f, s * 0.45f), t + new Vector2(0, -s * 0.6f) }, col, 4, true);
        // bottom: square
        var q = c + new Vector2(0, r * 0.55f);
        DrawRect(new Rect2(q - new Vector2(s * 0.5f, s * 0.5f), new Vector2(s, s)), col, false, 4);
        // left: double cross
        var x = c + new Vector2(-r * 0.55f, 0);
        DrawLine(x + new Vector2(0, -s * 0.6f), x + new Vector2(0, s * 0.6f), col, 4, true);
        DrawLine(x + new Vector2(-s * 0.45f, -s * 0.2f), x + new Vector2(s * 0.45f, -s * 0.2f), col, 4, true);
        DrawLine(x + new Vector2(-s * 0.45f, s * 0.2f), x + new Vector2(s * 0.45f, s * 0.2f), col, 4, true);
        // centre bell dot
        DrawCircle(c, s * 0.22f, UiTheme.Brass);
    }
}
