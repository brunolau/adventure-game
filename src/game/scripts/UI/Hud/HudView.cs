using System;
using System.Linq;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Text;
using LastBell.Game.Hooks;
using LastBell.Game.PlayerInput;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;
using LastBell.Game.World;

namespace LastBell.Game.UI.Hud;

/// <summary>
/// The HUD: a thin translucent bottom strip (PRIBEH_A_PRAVIDLA: bag left, action text in the middle,
/// journal and map right). Buttons are placed so they never cover the template exit zones at the
/// left/right screen edges (x 50–105 and 1870–1925, y 975–1045); the strip background is
/// mouse-transparent. The selected item is announced in a chip with a cancel cross (an alternative to
/// the right click, AT19). HUD buttons only send logical commands through <see cref="WorldInput"/>
/// and never take keyboard focus (Tab stays with the scene's target list).
/// Also implements <see cref="IHoverView"/>: the hover name and the action sentence (only when
/// Core says the item rule is executable) are shown in the strip centre.
/// </summary>
public partial class HudView : Control, IHoverView
{
    /// <summary>Height of the strip in logical px.</summary>
    public const float StripHeight = 82;

    private Control strip = null!;
    private Label hoverName = null!;
    private Label hoverAction = null!;
    private Label keyHint = null!;
    private VBoxContainer centre = null!;
    private bool? narrowLayout;
    private PanelContainer chip = null!;
    private ItemIcon chipIcon = null!;
    private Label chipLabel = null!;
    private Button portalButton = null!;
    private Button eyeButton = null!;
    private bool? labelsShown;
    private string? chipItem;
    private bool portalAvailable;

    /// <summary>The latest hover payload (null when hidden); the inventory drawer shows it too.</summary>
    public HoverPayload? CurrentHover { get; private set; }

    /// <summary>Raised when the hover payload changed.</summary>
    public event Action? HoverChanged;

    /// <summary>Raised when the portal (era chooser) button is pressed.</summary>
    public event Action? PortalPressed;

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;

        strip = new Control { MouseFilter = MouseFilterEnum.Ignore };
        strip.SetAnchorsAndOffsetsPreset(LayoutPreset.BottomWide);
        strip.OffsetTop = -StripHeight;
        AddChild(strip);
        var band = new Panel { MouseFilter = MouseFilterEnum.Ignore };
        var bandStyle = new StyleBoxFlat { BgColor = new Color(UiTheme.Wood, 0.62f), BorderColor = new Color(UiTheme.Brass, 0.45f), BorderWidthTop = 2 };
        band.AddThemeStyleboxOverride("panel", bandStyle);
        band.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        strip.AddChild(band);

        // Left group (starts right of the left exit zone).
        var left = Ui.HBox(10);
        left.MouseFilter = MouseFilterEnum.Ignore;
        left.SetAnchorsAndOffsetsPreset(LayoutPreset.LeftWide);
        left.OffsetLeft = 120;
        left.OffsetTop = 8;
        left.OffsetBottom = -8;
        strip.AddChild(left);
        left.AddChild(HudButton(GlyphKind.Bag, "ui.hud.inventory", "I", () => WorldInput.Dispatch(LogicalCommand.Inventory)));
        eyeButton = HudButton(GlyphKind.Eye, "ui.hud.show_hotspots", "Space", () => WorldInput.Dispatch(LogicalCommand.ToggleLabels));
        left.AddChild(eyeButton);

        chip = new PanelContainer { ThemeTypeVariation = "DarkPanel", MouseFilter = MouseFilterEnum.Ignore };
        chip.AddThemeStyleboxOverride("panel", UiTheme.DarkPanel(0.9f, 6, 12));
        var chipRow = Ui.HBox(8);
        chipRow.MouseFilter = MouseFilterEnum.Ignore;
        chipIcon = new ItemIcon(52);
        chipLabel = Ui.Label("", "OnDarkLabel");
        chipLabel.VerticalAlignment = VerticalAlignment.Center;
        chipLabel.AddThemeFontSizeOverride("font_size", 24);
        var cancel = Ui.GlyphButton(GlyphKind.Close, Ui.T("ui.inventory.selection_cleared"), () => WorldInput.Submit(new Hit.Empty(), PointerButton.Right), "HudButton", UiTheme.MinHit);
        cancel.FocusMode = FocusModeEnum.None;
        chipRow.AddChild(chipIcon);
        chipRow.AddChild(chipLabel);
        chipRow.AddChild(cancel);
        chip.AddChild(chipRow);
        left.AddChild(chip);
        chip.Visible = false;

        // Centre: hover text / key hint.
        centre = Ui.VBox(0);
        centre.MouseFilter = MouseFilterEnum.Ignore;
        centre.Alignment = BoxContainer.AlignmentMode.Center;
        centre.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        centre.OffsetLeft = 560;
        centre.OffsetRight = -560;
        strip.AddChild(centre);
        hoverName = Ui.Label("", "OnDarkLabel");
        hoverName.HorizontalAlignment = HorizontalAlignment.Center;
        hoverName.AddThemeFontOverride("font", UiTheme.BodyBold);
        hoverName.TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis;
        hoverAction = Ui.Label("", "SpeakerLabel");
        hoverAction.HorizontalAlignment = HorizontalAlignment.Center;
        hoverAction.TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis;
        hoverAction.AddThemeFontSizeOverride("font_size", 25);
        keyHint = Ui.Label(Ui.T("ui.hud.hotspot_key_hint"), "OnDarkCaption");
        keyHint.HorizontalAlignment = HorizontalAlignment.Center;
        foreach (var l in new[] { hoverName, hoverAction, keyHint })
        {
            l.AddThemeColorOverride("font_outline_color", new Color(0, 0, 0, 0.85f));
            l.AddThemeConstantOverride("outline_size", 6);
        }
        centre.AddChild(hoverName);
        centre.AddChild(hoverAction);
        centre.AddChild(keyHint);

        // Right group (ends left of the right exit zone).
        var right = Ui.HBox(10);
        right.MouseFilter = MouseFilterEnum.Ignore;
        right.Alignment = BoxContainer.AlignmentMode.End;
        right.SetAnchorsAndOffsetsPreset(LayoutPreset.RightWide);
        right.GrowHorizontal = GrowDirection.Begin;
        right.OffsetRight = -76;
        right.OffsetLeft = -560;
        right.OffsetTop = 8;
        right.OffsetBottom = -8;
        strip.AddChild(right);
        portalButton = HudButton(GlyphKind.Clock, "ui.travel.choose_era", "T", () => PortalPressed?.Invoke());
        portalButton.Visible = false;
        right.AddChild(portalButton);
        right.AddChild(HudButton(GlyphKind.Hint, "ui.hud.hint", "H", () => WorldInput.Dispatch(LogicalCommand.Hint)));
        right.AddChild(HudButton(GlyphKind.Journal, "ui.hud.journal", "J", () => WorldInput.Dispatch(LogicalCommand.Journal)));
        right.AddChild(HudButton(GlyphKind.Map, "ui.hud.map", "M", () => WorldInput.Dispatch(LogicalCommand.Map)));
        right.AddChild(HudButton(GlyphKind.Menu, "ui.hud.menu", "Esc", OpenPause));

        UpdateHoverLabels();
    }

    private static Button HudButton(GlyphKind glyph, string key, string hotkey, Action pressed)
    {
        var button = Ui.GlyphButton(glyph, Ui.T(key) + " (" + hotkey + ")", pressed, "HudButton", UiTheme.MinHit);
        button.FocusMode = FocusModeEnum.None;
        return button;
    }

    private static void OpenPause()
    {
        var game = GameRuntime.Instance;
        if (game.State.Mode is GameMode.World or GameMode.Inventory) game.Update(s => GameRules.OpenOverlay(s, GameMode.Pause));
    }

    /// <summary>True when the strip should be shown (world / inventory, stage settled).</summary>
    public bool StripWanted { get; set; } = true;

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        var game = GameRuntime.Instance;
        if (!game.IsReady) return;
        var state = game.State;
        bool show = StripWanted && state.Mode is GameMode.World or GameMode.Inventory && WorldStage.Instance?.Current is not null;
        strip.Visible = show && state.Mode == GameMode.World;
        if (!show) return;

        // Selected item chip (accessible announcement of the cursor item).
        if (state.SelectedItem != chipItem)
        {
            chipItem = state.SelectedItem;
            chip.Visible = chipItem is not null;
            if (chipItem is not null && game.Content.FindItem(chipItem) is { } item)
            {
                string name = TextService.Get(TextKeys.NameOf(item));
                chipIcon.SetItem(item.Icon, name);
                chipLabel.Text = Ui.T("ui.inventory.selected", ("item", name));
            }
        }
        bool settled = WorldStage.Instance?.IsSettled ?? false;
        bool portal = settled && state.Mode == GameMode.World && Navigation.PortalTargets(game.Content, state).Count > 0;
        if (portal != portalAvailable)
        {
            portalAvailable = portal;
            portalButton.Visible = portal;
        }
        if (labelsShown != state.HotspotLabels)
        {
            labelsShown = state.HotspotLabels;
            // The eye shows its state (not by colour alone: the border gets thicker as well).
            if (state.HotspotLabels) eyeButton.AddThemeStyleboxOverride("normal", UiTheme.Box(new Color("5a4126", 0.95f), UiTheme.BrassLight, 4, 16, 8));
            else eyeButton.RemoveThemeStyleboxOverride("normal");
        }
        // Narrow logical width (large HUD scale): the hover text floats above the strip, the chip shows only the icon.
        bool narrow = Size.X < 1500;
        if (narrow != narrowLayout)
        {
            narrowLayout = narrow;
            chipLabel.Visible = !narrow;
            if (narrow)
            {
                centre.SetAnchorsAndOffsetsPreset(LayoutPreset.TopWide);
                centre.OffsetTop = -70;
                centre.OffsetBottom = -4;
                centre.OffsetLeft = 16;
                centre.OffsetRight = -16;
            }
            else
            {
                centre.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
                centre.OffsetLeft = 560;
                centre.OffsetRight = -560;
            }
        }
        keyHint.Visible = !narrow && UiSettings.HotspotKeyHint && !hoverName.Visible && !hoverAction.Visible && !state.HotspotLabels;
    }

    // ------------------------------------------------------------------ IHoverView

    /// <inheritdoc />
    public void ShowHover(HoverPayload payload)
    {
        CurrentHover = payload;
        UpdateHoverLabels();
        HoverChanged?.Invoke();
    }

    /// <inheritdoc />
    public void HideHover()
    {
        if (CurrentHover is null) return;
        CurrentHover = null;
        UpdateHoverLabels();
        HoverChanged?.Invoke();
    }

    /// <summary>Hover name and action sentence as display strings (action empty unless Core returned one).</summary>
    public static (string Name, string Action) Texts(HoverPayload? payload)
    {
        if (payload is null) return ("", "");
        string name = TextService.Get(payload.Info.Name);
        string action = payload.ShowAction ? TextService.Get(payload.Info.ActionLabel) : "";
        return (name, action);
    }

    private void UpdateHoverLabels()
    {
        if (hoverName is null) return;
        var (name, action) = Texts(CurrentHover);
        hoverName.Text = name;
        hoverName.Visible = name.Length > 0;
        hoverAction.Text = action;
        hoverAction.Visible = action.Length > 0;
    }
}
