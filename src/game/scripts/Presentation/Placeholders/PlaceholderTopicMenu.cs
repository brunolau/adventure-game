using Godot;
using LastBell.Core.Text;
using LastBell.Game.Hooks;
using LastBell.Game.Runtime;

namespace LastBell.Game.Presentation.Placeholders;

/// <summary>Placeholder topic menu: one keyboard-focusable button per Core topic, plus "end conversation".</summary>
public partial class PlaceholderTopicMenu : Control, ITopicMenuView
{
    private PanelContainer panel = null!;
    private VBoxContainer list = null!;

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
        panel = PlaceholderStyle.Panel();
        list = new VBoxContainer();
        list.AddThemeConstantOverride("separation", 8);
        panel.AddChild(list);
        AddChild(panel);
        panel.Visible = false;
    }

    /// <inheritdoc />
    public void Open(TopicMenuRequest request)
    {
        foreach (var child in list.GetChildren()) child.QueueFree();
        var game = GameRuntime.Instance;
        var character = game.Content.FindCharacter(request.CharacterId);
        list.AddChild(PlaceholderStyle.Label(character is null ? TextService.Ui("ui.dialogue.topics") : TextService.Get(TextKeys.NameOf(character)), 26, new Color(1f, 0.83f, 0.45f)));
        Button? first = null;
        foreach (var topic in request.Topics)
        {
            var option = topic;
            var button = PlaceholderStyle.Button(TextService.Get(option.Label));
            button.Alignment = HorizontalAlignment.Left;
            button.Pressed += () => request.Choose(option);
            list.AddChild(button);
            first ??= button;
        }
        var end = PlaceholderStyle.Button(TextService.Ui("ui.dialogue.end"));
        end.Alignment = HorizontalAlignment.Left;
        end.Pressed += request.Close;
        list.AddChild(end);
        first ??= end;
        panel.Visible = true;
        panel.ResetSize();
        panel.Position = new Vector2(1920 - 760, 1080 - 120 - panel.GetCombinedMinimumSize().Y);
        panel.CustomMinimumSize = new Vector2(700, 0);
        first.CallDeferred(Control.MethodName.GrabFocus);
    }

    /// <inheritdoc />
    public void Close() => panel.Visible = false;
}
