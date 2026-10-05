using System;
using System.Linq;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Core.Text;
using LastBell.Core.Views;
using LastBell.Game.Hooks;
using LastBell.Game.Runtime;

namespace LastBell.Game.Presentation.Placeholders;

/// <summary>
/// Temporary panels for Core's overlay modes Pause, Journal and Map (each until the UI agent claims
/// it), so the game never gets stuck in a mode without UI. Pause: resume, quick save/load, settings
/// request, quit. Journal: the current goal. Map: fast travel to the rooms Core allows.
/// </summary>
public partial class PlaceholderOverlayPanel : Control
{
    private PanelContainer panel = null!;
    private VBoxContainer box = null!;
    private GameMode shownMode = GameMode.World;

    /// <inheritdoc />
    public override void _Ready()
    {
        SetAnchorsPreset(LayoutPreset.FullRect);
        MouseFilter = MouseFilterEnum.Ignore;
        panel = PlaceholderStyle.Panel(0.95f);
        box = new VBoxContainer();
        box.AddThemeConstantOverride("separation", 10);
        panel.AddChild(box);
        AddChild(panel);
        panel.Visible = false;
    }

    /// <inheritdoc />
    public override void _Process(double delta)
    {
        var game = GameRuntime.Instance;
        if (!game.IsReady) return;
        var mode = game.State.Mode;
        UiPanel? kind = mode switch
        {
            GameMode.Pause => UiPanel.Pause,
            GameMode.Journal => UiPanel.Journal,
            GameMode.Map => UiPanel.Map,
            _ => null,
        };
        bool show = kind is { } k && !UiBus.IsClaimed(k);
        if (!show)
        {
            if (panel.Visible) panel.Visible = false;
            shownMode = GameMode.World;
            return;
        }
        if (shownMode == mode && panel.Visible) return;
        shownMode = mode;
        Build(mode);
    }

    private void Build(GameMode mode)
    {
        var game = GameRuntime.Instance;
        foreach (var child in box.GetChildren()) child.QueueFree();
        Button? first = null;
        void Add(string text, Action onPressed)
        {
            var b = PlaceholderStyle.Button(text);
            b.Pressed += onPressed;
            box.AddChild(b);
            first ??= b;
        }
        var gold = new Color(1f, 0.83f, 0.45f);
        switch (mode)
        {
            case GameMode.Pause:
                box.AddChild(PlaceholderStyle.Label(TextService.Ui("ui.pause.title"), 34, gold));
                Add(TextService.Ui("ui.pause.resume"), () => game.Update(GameRules.CloseOverlay));
                Add(TextService.Ui("ui.pause.save"), () =>
                {
                    game.Update(GameRules.CloseOverlay);
                    if (game.Save("quick")) UiBus.PostNotice("ui.save.saved");
                });
                Add(TextService.Ui("ui.pause.load"), () =>
                {
                    if (GameRuntime.SlotExists("quick")) game.Load("quick");
                    else if (GameRuntime.SlotExists(GameRuntime.AutosaveSlot)) game.Load(GameRuntime.AutosaveSlot);
                    else UiBus.PostNotice("ui.dev.no_save");
                });
                Add(TextService.Ui("ui.pause.settings"), () => UiBus.RequestOpen(UiPanel.Settings));
                Add(TextService.Ui("ui.pause.quit"), () => GetTree().Quit());
                break;
            case GameMode.Journal:
                box.AddChild(PlaceholderStyle.Label(TextService.Ui("ui.journal.title"), 34, gold));
                box.AddChild(PlaceholderStyle.Label(TextService.Ui("ui.hud.current_goal"), 22, new Color(1, 1, 1, 0.6f)));
                var quest = Quests.CurrentMainQuest(game.Content, game.State);
                var goal = PlaceholderStyle.Label(quest is null ? "" : TextService.Get(TextKeys.GoalOf(quest)), 26);
                goal.AutowrapMode = TextServer.AutowrapMode.WordSmart;
                goal.CustomMinimumSize = new Vector2(900, 0);
                box.AddChild(goal);
                Add(TextService.Ui("ui.common.close"), () => game.Update(GameRules.CloseOverlay));
                break;
            case GameMode.Map:
                box.AddChild(PlaceholderStyle.Label(TextService.Ui("ui.map.title"), 34, gold));
                var era = ViewBuilder.Map(game.Content, game.State).FirstOrDefault(e => e.Year == game.State.Era);
                foreach (var room in era?.Rooms.Where(r => r.CanFastTravel) ?? Enumerable.Empty<MapRoomView>())
                {
                    string target = room.RoomId;
                    Add(TextService.Ui("ui.map.travel_to", ("place", TextService.Get(room.Name))),
                        () => game.Update(s => Navigation.FastTravel(game.Content, s, target)));
                }
                Add(TextService.Ui("ui.common.close"), () => game.Update(GameRules.CloseOverlay));
                break;
        }
        panel.Visible = true;
        panel.ResetSize();
        var size = panel.GetCombinedMinimumSize();
        panel.Position = new Vector2((1920 - size.X) / 2, (1080 - size.Y) / 2);
        first?.CallDeferred(Control.MethodName.GrabFocus);
    }
}
