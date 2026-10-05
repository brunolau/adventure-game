using Godot;
using LastBell.Core.Content;
using LastBell.Game.Hooks;
using LastBell.Game.Runtime;

namespace LastBell.Game.Presentation.Placeholders;

/// <summary>
/// Placeholder cutscene framing: letterbox bars and the skip hint. Beat shots are stage directions
/// (not player text, ISSUES TEXT-03) and are not shown.
/// </summary>
public partial class PlaceholderCutsceneFrame : Control, ICutsceneView
{
    private ColorRect top = null!;
    private ColorRect bottom = null!;
    private Label hint = null!;

    /// <inheritdoc />
    public override void _Ready()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        SetAnchorsPreset(LayoutPreset.FullRect);
        top = new ColorRect { Color = Colors.Black, Position = Vector2.Zero, Size = new Vector2(1920, 110), MouseFilter = MouseFilterEnum.Ignore };
        bottom = new ColorRect { Color = Colors.Black, Position = new Vector2(0, 970), Size = new Vector2(1920, 110), MouseFilter = MouseFilterEnum.Ignore };
        hint = PlaceholderStyle.Label("", 20, new Color(1, 1, 1, 0.6f));
        hint.Position = new Vector2(1500, 40);
        AddChild(top);
        AddChild(bottom);
        AddChild(hint);
        Visible = false;
    }

    /// <inheritdoc />
    public void Begin(CutsceneDef cutscene)
    {
        if (UiBus.Cutscene is not null) return;
        hint.Text = cutscene.Skippable ? TextService.Ui("ui.cutscene.skip_prompt") : "";
        Visible = true;
    }

    /// <inheritdoc />
    public void Beat(CutsceneDef cutscene, int beatIndex) { }

    /// <inheritdoc />
    public void End(CutsceneDef cutscene) => Visible = false;
}
