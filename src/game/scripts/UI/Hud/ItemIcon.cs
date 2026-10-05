using System;
using System.Collections.Generic;
using Godot;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Hud;

/// <summary>
/// An inventory item picture: the painted icon <c>res://assets/&lt;items[].icon&gt;</c> when it exists,
/// otherwise a drawn paper token with the item's initials (dev placeholder, never a blank slot).
/// </summary>
public partial class ItemIcon : Control
{
    private static readonly Dictionary<string, Texture2D?> Cache = new(StringComparer.Ordinal);
    private Texture2D? texture;
    private string initials = "";
    private bool dimmed;

    /// <summary>Godot constructor.</summary>
    public ItemIcon() { MouseFilter = MouseFilterEnum.Ignore; }

    /// <summary>Creates an icon of a given size.</summary>
    public ItemIcon(float size) : this() => CustomMinimumSize = new Vector2(size, size);

    /// <summary>Shows an item (icon path from Core's view, display name for the placeholder).</summary>
    public void SetItem(string iconPath, string displayName, bool dim = false)
    {
        texture = Load(iconPath);
        initials = Initials(displayName);
        dimmed = dim;
        QueueRedraw();
    }

    /// <summary>Loads (and caches) an item texture, or null.</summary>
    public static Texture2D? Load(string iconPath)
    {
        if (string.IsNullOrEmpty(iconPath)) return null;
        if (Cache.TryGetValue(iconPath, out var cached)) return cached;
        string path = iconPath.StartsWith("res://") ? iconPath : "res://assets/" + iconPath;
        var tex = ResourceLoader.Exists(path) ? GD.Load<Texture2D>(path) : null;
        Cache[iconPath] = tex;
        return tex;
    }

    private static string Initials(string name)
    {
        var parts = name.Split(new[] { ' ', '-' }, StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length == 0) return "?";
        string a = parts[0][..1].ToUpperInvariant();
        string b = parts.Length > 1 && char.IsLetter(parts[1][0]) ? parts[1][..1].ToUpperInvariant() : (parts[0].Length > 1 ? parts[0][1..2] : "");
        return a + b;
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        var rect = new Rect2(Vector2.Zero, Size);
        var tint = dimmed ? new Color(1, 1, 1, 0.5f) : Colors.White;
        if (texture is not null)
        {
            var ts = texture.GetSize();
            float scale = Math.Min(rect.Size.X / ts.X, rect.Size.Y / ts.Y);
            var size = ts * scale;
            DrawTextureRect(texture, new Rect2(rect.Position + (rect.Size - size) / 2, size), false, tint);
            return;
        }
        float s = Math.Min(rect.Size.X, rect.Size.Y) * 0.86f;
        var center = rect.GetCenter();
        DrawCircle(center + new Vector2(0, 3), s / 2, new Color(0, 0, 0, 0.18f * tint.A));
        DrawCircle(center, s / 2, new Color(UiTheme.PaperDeep, tint.A));
        DrawArc(center, s / 2 - 2, 0, Mathf.Tau, 40, new Color(UiTheme.Brass, tint.A), 3, true);
        var font = UiTheme.Heading;
        int fontSize = (int)(s * 0.38f);
        var textSize = font.GetStringSize(initials, HorizontalAlignment.Left, -1, fontSize);
        DrawString(font, center + new Vector2(-textSize.X / 2, fontSize * 0.36f), initials, HorizontalAlignment.Left, -1, fontSize, new Color(UiTheme.Ink, tint.A));
    }
}
