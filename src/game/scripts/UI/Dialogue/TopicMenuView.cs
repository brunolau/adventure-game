using System;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.Text;
using LastBell.Game.Hooks;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Dialogue;

/// <summary>
/// Dialogue topic menu (<see cref="ITopicMenuView"/>): the character's name and one button per
/// topic Core offers (story topics first, then ambient topics whose requires_done are met;
/// non-repeatable ones disappear once heard, repeatable ones carry a "heard" mark), plus "end
/// conversation". Topics are content, never verbs. Fully keyboard focusable; Esc/Backspace leave
/// (routed by the world runtime).
/// </summary>
public partial class TopicMenuView : Control, ITopicMenuView
{
    private PanelContainer panel = null!;
    private Label name = null!;
    private VBoxContainer list = null!;
    private ScrollContainer scroll = null!;
    private TopicMenuRequest? request;

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
        panel = new PanelContainer();
        panel.AddThemeStyleboxOverride("panel", UiTheme.PaperPanel(24));
        var box = Ui.VBox(12);
        var header = Ui.HBox(12);
        header.AddChild(new Glyph(GlyphKind.Talk, 40, UiTheme.Accent));
        name = Ui.Label("", "HeadingLabel");
        name.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        header.AddChild(name);
        box.AddChild(header);
        box.AddChild(Ui.Rule());
        list = Ui.VBox(10);
        scroll = Ui.Scroll(list);
        box.AddChild(scroll);
        panel.AddChild(box);
        AddChild(panel);
        panel.Visible = false;
    }

    /// <inheritdoc />
    public void Open(TopicMenuRequest req)
    {
        request = req;
        Ui.Clear(list);
        var game = GameRuntime.Instance;
        var character = game.Content.FindCharacter(req.CharacterId);
        name.Text = character is null ? Ui.T("ui.dialogue.topics") : TextService.Get(TextKeys.NameOf(character));
        Button? first = null;
        foreach (var topic in req.Topics)
        {
            var option = topic;
            bool heard = !option.IsStoryAction && game.State.JournalSeen.Contains(LastBell.Core.Rules.Dialogue.TopicEntryKey(option.Id));
            var button = Ui.Button(TextService.Get(option.Label), () => Choose(option));
            button.Alignment = HorizontalAlignment.Left;
            button.AutowrapMode = TextServer.AutowrapMode.WordSmart;
            button.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            if (option.IsStoryAction) button.AddThemeFontOverride("font", UiTheme.BodyBold);
            if (heard)
            {
                button.AddThemeColorOverride("font_color", UiTheme.InkSoft);
                button.TooltipText = Ui.T("ui.dialogue.heard");
                button.Text += "  · " + Ui.T("ui.dialogue.heard");
            }
            list.AddChild(button);
            first ??= button;
        }
        var end = Ui.Button(Ui.T("ui.dialogue.end"), () => request?.Close());
        end.Alignment = HorizontalAlignment.Left;
        end.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        end.ThemeTypeVariation = "FlatButton";
        list.AddChild(end);
        first ??= end;
        panel.Visible = true;
        Layout();
        Ui.FocusLater(first);
    }

    private void Choose(TopicOption option)
    {
        var req = request;
        if (req is null) return;
        req.Choose(option);
    }

    /// <inheritdoc />
    public void Close()
    {
        if (!panel.Visible) return;
        var focused = GetViewport()?.GuiGetFocusOwner();
        if (focused is not null && panel.IsAncestorOf(focused)) focused.ReleaseFocus();
        panel.Visible = false;
        request = null;
    }

    private void Layout()
    {
        float width = Math.Min(760, Size.X - 80);
        float rows = list.GetChildCount();
        float wanted = 130 + rows * 82;
        float height = Math.Min(wanted, Size.Y - 200);
        panel.CustomMinimumSize = new Vector2(width, height);
        panel.Size = new Vector2(width, height);
        panel.Position = new Vector2(Size.X - width - 60, Size.Y - height - 150);
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        if (panel.Visible) Layout();
    }
}
