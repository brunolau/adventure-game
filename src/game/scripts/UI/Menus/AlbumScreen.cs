using Godot;
using LastBell.Core.State;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Menus;

/// <summary>Read-only album of a saved game (main menu "Album"): completed side quests with their epilogue shot and line.</summary>
public partial class AlbumScreen : ModalScreen
{
    private VBoxContainer list = null!;

    /// <summary>The state to show (the newest valid save).</summary>
    public GameState? Source { get; set; }

    /// <summary>Godot constructor.</summary>
    public AlbumScreen() { PreferredSize = new Vector2(1300, 860); }

    /// <inheritdoc />
    protected override void Build()
    {
        SetTitle(Ui.T("ui.journal.tab_album"));
        list = Ui.VBox(12);
        Body.AddChild(Ui.Scroll(list));
    }

    /// <inheritdoc />
    protected override void Refresh()
    {
        Ui.Clear(list);
        if (Source is null) return;
        var view = LastBell.Core.Rules.Journal.Build(GameRuntime.Instance.Content, Source);
        if (view.Album.Count == 0) list.AddChild(Ui.Para(Ui.T("ui.journal.album_empty"), "CaptionLabel"));
        foreach (var entry in view.Album)
        {
            var card = new PanelContainer { ThemeTypeVariation = "CardPanel" };
            var box = Ui.VBox(6);
            box.AddChild(Ui.Label(Ui.T(entry.Title), "SubheadingLabel", wrap: true));
            if (!entry.Shot.IsEmpty) box.AddChild(Ui.Para(Ui.T(entry.Shot)));
            if (!entry.Line.IsEmpty)
            {
                var (speaker, text) = Ui.SplitSpeaker(entry.Line);
                box.AddChild(Ui.Para((speaker is null ? "" : Ui.SpeakerName(speaker) + ": ") + "„" + text + "“", "ItalicLabel"));
            }
            card.AddChild(box);
            list.AddChild(card);
        }
    }
}
