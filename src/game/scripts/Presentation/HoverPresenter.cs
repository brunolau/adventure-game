using Godot;
using LastBell.Core.Views;
using LastBell.Game.Hooks;
using LastBell.Game.Presentation.Placeholders;

namespace LastBell.Game.Presentation;

/// <summary>
/// Routes hover text to the registered <see cref="IHoverView"/> or the placeholder. The text comes
/// from Core's shared resolver: the name, plus — only while an item is selected — the action
/// sentence, which Core leaves empty unless the item rule is executable right now.
/// </summary>
public static class HoverPresenter
{
    /// <summary>The placeholder view (set by the placeholder UI layer).</summary>
    internal static PlaceholderHover? Placeholder { get; set; }

    private static IHoverView? View => UiBus.Hover ?? Placeholder;

    /// <summary>Shows hover info at a canvas position.</summary>
    public static void Show(HoverInfo info, Vector2 position, bool itemSelected, bool fromKeyboard)
    {
        if (info.Name.IsEmpty && info.ActionLabel.IsEmpty) { Hide(); return; }
        View?.ShowHover(new HoverPayload(info, position, itemSelected, fromKeyboard));
    }

    /// <summary>Hides the hover text.</summary>
    public static void Hide() => View?.HideHover();
}
