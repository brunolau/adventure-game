using System;
using System.Linq;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Theme;
using LastBell.Game.World;

namespace LastBell.Game.UI.Menus;

/// <summary>
/// Save and load screens. Save: eight manual slots (overwrite needs a confirmation). Load: the
/// autosave, the quick save and the manual slots. Every file is validated by Core before it is
/// listed as loadable; a corrupt file shows Core's readable message and the open game is never
/// touched (AT18). Each slot shows place · year, the time and a thumbnail of the scene.
/// </summary>
public partial class SaveLoadScreen : ModalScreen
{
    private GridContainer grid = null!;
    private Label note = null!;

    /// <summary>True = save screen, false = load screen.</summary>
    public bool SaveMode { get; set; }

    /// <summary>Godot constructor.</summary>
    public SaveLoadScreen() { PreferredSize = new Vector2(1640, 940); }

    /// <inheritdoc />
    protected override void Build()
    {
        note = Ui.Para("", "CaptionLabel");
        Body.AddChild(note);
        grid = new GridContainer { Columns = 2 };
        grid.AddThemeConstantOverride("h_separation", 16);
        grid.AddThemeConstantOverride("v_separation", 16);
        Body.AddChild(Ui.Scroll(grid));
    }

    /// <inheritdoc />
    protected override void Refresh()
    {
        SetTitle(Ui.T(SaveMode ? "ui.save.title_save" : "ui.save.title_load"));
        grid.Columns = Size.X < 1500 ? 1 : 2;
        Ui.Clear(grid);
        var slots = SaveMode ? SaveSlots.Manual.Select(SaveSlots.Inspect).ToList() : SaveSlots.All().Where(s => s.Exists).ToList();
        note.Text = SaveMode ? "" : slots.Count == 0 ? Ui.T("ui.save.no_saves") : "";
        note.Visible = note.Text.Length > 0;
        foreach (var slot in slots) grid.AddChild(SlotCard(slot));
    }

    private Control SlotCard(SlotInfo info)
    {
        var card = new PanelContainer { ThemeTypeVariation = info.Corrupt ? "CardPanel" : "CardPanel", SizeFlagsHorizontal = SizeFlags.ExpandFill };
        var row = Ui.HBox(16);
        var thumb = new TextureRect
        {
            CustomMinimumSize = new Vector2(256, 144),
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize,
            StretchMode = TextureRect.StretchModeEnum.KeepAspectCovered,
            Texture = info.Valid ? SaveSlots.Thumbnail(info.Slot) : null,
            MouseFilter = MouseFilterEnum.Ignore,
        };
        var thumbFrame = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore };
        thumbFrame.AddThemeStyleboxOverride("panel", UiTheme.Box(new Color("3a2c22"), new Color(UiTheme.PaperEdge, 0.8f), 2, 8, 2));
        thumbFrame.AddChild(thumb);
        row.AddChild(thumbFrame);
        var text = Ui.VBox(4);
        text.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        text.AddChild(Ui.Label(SaveSlots.Title(info.Slot), "SubheadingLabel"));
        if (info.Valid)
        {
            text.AddChild(Ui.Para(SaveSlots.Summary(info.State!)));
            text.AddChild(Ui.Label(Ui.T("ui.save.saved_at", ("datetime", SaveSlots.LocalTime(info.ModifiedUnix))), "CaptionLabel"));
        }
        else if (info.Corrupt)
        {
            var bad = Ui.Para(Ui.T("ui.save.corrupted_slot"));
            bad.AddThemeColorOverride("font_color", UiTheme.Accent);
            text.AddChild(bad);
            text.AddChild(Ui.Para(TextService.Get(info.Error), "CaptionLabel"));
        }
        else text.AddChild(Ui.Para(Ui.T("ui.save.slot_empty"), "CaptionLabel"));
        var buttons = Ui.HBox(10);
        string slot = info.Slot;
        if (SaveMode)
        {
            var save = Ui.Button(Ui.T(info.Exists ? "ui.save.overwrite" : "ui.menu.save"), () => RequestSave(info));
            buttons.AddChild(save);
        }
        else
        {
            var load = Ui.Button(Ui.T("ui.menu.load"), () => RequestLoad(info));
            buttons.AddChild(load);
        }
        if (info.Exists && slot != GameRuntime.AutosaveSlot)
        {
            var delete = Ui.Button(Ui.T("ui.save.delete"), () => UiRoot.Instance?.Confirm(
                Ui.T("ui.save.delete_confirm", ("n", SaveSlots.Number(slot))), Ui.T("ui.save.delete"), () =>
                {
                    GameRuntime.DeleteSlot(slot);
                    string png = $"{GameRuntime.SaveDirectory}/{slot}.png";
                    if (Godot.FileAccess.FileExists(png)) DirAccess.RemoveAbsolute(png);
                    Refresh();
                }), "FlatButton");
            buttons.AddChild(delete);
        }
        text.AddChild(buttons);
        row.AddChild(text);
        card.AddChild(row);
        return card;
    }

    private void RequestSave(SlotInfo info)
    {
        if (!CanSaveNow())
        {
            UiRoot.Instance?.Message(Ui.T("ui.save.cannot_save_now"));
            return;
        }
        if (info.Exists) UiRoot.Instance?.Confirm(Ui.T("ui.save.overwrite_confirm", ("n", SaveSlots.Number(info.Slot))), Ui.T("ui.save.overwrite"), () => DoSave(info.Slot));
        else DoSave(info.Slot);
    }

    private static bool CanSaveNow()
    {
        var game = GameRuntime.Instance;
        var stage = WorldStage.Instance;
        bool busy = stage is null || stage.Transitioning || (InteractionController.Instance?.HasPending ?? false) || (stage.Current?.Hero.IsWalking ?? false);
        return !busy && game.State.Mode is GameMode.World or GameMode.Inventory or GameMode.Pause && game.State.ActiveLineId is null;
    }

    private void DoSave(string slot)
    {
        var game = GameRuntime.Instance;
        var shot = UiRoot.Instance?.WorldShot;
        // Save the world state, not the pause overlay: a load resumes in the scene.
        bool paused = game.State.Mode == GameMode.Pause;
        if (paused) game.Update(GameRules.CloseOverlay);
        bool ok = game.Save(slot);
        if (paused) game.Update(s => GameRules.OpenOverlay(s, GameMode.Pause));
        if (ok)
        {
            UiRoot.SaveThumbnail(slot, shot);
            ShowStatus(Ui.T("ui.save.saved"));
            Refresh();
            FocusDefault();
        }
        else UiRoot.Instance?.Message(Ui.T("ui.save.save_failed"));
    }

    private void RequestLoad(SlotInfo info)
    {
        var root = UiRoot.Instance;
        if (root is null) return;
        if (root.MainMenuOpen) GameRuntime.Instance.Load(info.Slot);
        else root.Confirm(Ui.T("ui.save.load_confirm"), Ui.T("ui.menu.load"), () => GameRuntime.Instance.Load(info.Slot));
    }
}
