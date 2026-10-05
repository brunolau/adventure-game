using Godot;
using LastBell.Game.Diagnostics;
using LastBell.Game.Hooks;
using LastBell.Game.PlayerInput;
using LastBell.Game.Presentation;
using LastBell.Game.Presentation.Placeholders;
using LastBell.Game.Runtime;
using LastBell.Game.World;

namespace LastBell.Game;

/// <summary>
/// Root of scenes/Main.tscn. Builds the persistent node tree (world stage, input, presenters,
/// placeholder UI, HUD host, living-world host, music), loads the extension roots of the UI and
/// living-world agents if present, then starts the game (or hands control to the debug harness,
/// or to the UI agent's main menu when it claims <see cref="UiPanel.MainMenu"/>).
/// </summary>
public partial class Main : Node
{
    /// <summary>Scene the UI agent provides (instantiated under the HUD host).</summary>
    public const string UiRootScene = "res://scenes/ui/UiRoot.tscn";

    /// <summary>Script the living-world agent provides (a Node subclass, instantiated under LivingHost).</summary>
    public const string LivingRootScript = "res://scripts/Living/LivingRoot.cs";

    /// <summary>The persistent HUD host (CanvasLayer 40) for the UI agent's screens.</summary>
    public CanvasLayer HudHost { get; private set; } = null!;

    /// <summary>Host node of the living-world bootstrap.</summary>
    public Node LivingHost { get; private set; } = null!;

    /// <summary>The singleton.</summary>
    public static Main? Instance { get; private set; }

    /// <inheritdoc />
    public override void _Ready()
    {
        Instance = this;
        var game = GameRuntime.Instance;
        if (!game.IsReady)
        {
            ShowContentError(game);
            return;
        }

        AddChild(new WorldStage { Name = "WorldStage" });
        AddChild(new InteractionController { Name = "InteractionController" });
        AddChild(new InputRouter { Name = "InputRouter" });
        AddChild(new DialoguePresenter { Name = "DialoguePresenter" });
        var placeholderLayer = new CanvasLayer { Name = "PlaceholderLayer", Layer = 30 };
        AddChild(placeholderLayer);
        placeholderLayer.AddChild(new PlaceholderUi { Name = "PlaceholderUi" });
        HudHost = new CanvasLayer { Name = "HudHost", Layer = 40 };
        AddChild(HudHost);
        LivingHost = new Node { Name = "LivingHost" };
        AddChild(LivingHost);
        AddChild(new MusicPlayer { Name = "MusicPlayer" });

        LoadExtensions();

        var harness = DebugHarness.FromCommandLine();
        if (harness is not null)
        {
            AddChild(harness);
            return; // the harness prepares the state and builds the room
        }
        if (!UiBus.IsClaimed(UiPanel.MainMenu)) game.NewGame();
    }

    private void LoadExtensions()
    {
        if (ResourceLoader.Exists(UiRootScene) && GD.Load<PackedScene>(UiRootScene) is { } ui)
            HudHost.AddChild(ui.Instantiate());
        if (ResourceLoader.Exists(LivingRootScript) && GD.Load<Script>(LivingRootScript) is CSharpScript script)
        {
            var instance = script.New().AsGodotObject();
            if (instance is Node node)
            {
                node.Name = "LivingRoot";
                LivingHost.AddChild(node);
            }
            else GD.PushError(LivingRootScript + " must define a Node subclass");
        }
    }

    private void ShowContentError(GameRuntime game)
    {
        var label = new Label
        {
            Text = TextService.Ui("ui.system.error_title") + "\n" + string.Join("\n", game.LoadErrors),
            Position = new Vector2(60, 60),
            AutowrapMode = TextServer.AutowrapMode.WordSmart,
            Size = new Vector2(1800, 900),
        };
        label.AddThemeFontSizeOverride("font_size", 24);
        AddChild(label);
    }
}
