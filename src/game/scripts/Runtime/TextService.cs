using System.Collections.Generic;
using Godot;
using LastBell.Core.Text;

namespace LastBell.Game.Runtime;

/// <summary>
/// The only way presentation code turns a text key into player-visible text. It returns
/// <c>Tr(key)</c> from the CSV translation tables, or the Slovak fallback from game.json when the
/// table has no entry (Tr returns the key itself) or the entry is empty. Never hardcode visible
/// strings: build a key (Core <see cref="TextKeys"/> or a <c>ui.*</c> key in ui.csv) and call this.
/// </summary>
public static class TextService
{
    /// <summary>Translated text of <paramref name="key"/>, else <paramref name="fallback"/>.</summary>
    public static string Get(string key, string fallback = "")
    {
        if (string.IsNullOrEmpty(key)) return fallback ?? "";
        string translated = TranslationServer.Translate(key).ToString();
        if (string.IsNullOrEmpty(translated) || translated == key) return fallback ?? "";
        return translated;
    }

    /// <summary>Translated text of a Core text reference.</summary>
    public static string Get(TextRef text) => Get(text.Key, text.Fallback);

    /// <summary>
    /// The year shown for an era (<c>era.&lt;year&gt;.year</c> in ui.csv, else the era id). Use it wherever an era year
    /// is visible: the Ivanka era has the id 1960 but is shown as 1962 (docs/DECISIONS.md).
    /// </summary>
    public static string EraYear(int year) => Get(TextKeys.YearOf(year));

    /// <summary>
    /// Translated <c>ui.*</c> text with <c>{name}</c> placeholders replaced. A missing ui key is a
    /// bug (ui.csv is hand-written); it logs a warning once and shows nothing.
    /// </summary>
    public static string Ui(string key, params (string Name, string Value)[] args)
    {
        string text = Get(key);
        if (text.Length == 0 && WarnedKeys.Add(key)) GD.PushWarning($"TextService: missing ui key '{key}' in ui.csv");
        return Format(text, args);
    }

    /// <summary>Replaces <c>{name}</c> placeholders (applied after Tr, see ui.csv convention).</summary>
    public static string Format(string text, params (string Name, string Value)[] args)
    {
        foreach (var (name, value) in args) text = text.Replace("{" + name + "}", value);
        return text;
    }

    /// <summary>The active locale (default "sk").</summary>
    public static string Locale => TranslationServer.GetLocale();

    /// <summary>Switches the locale (e.g. "sk", "en"); missing entries still fall back to Slovak.</summary>
    public static void SetLocale(string locale) => TranslationServer.SetLocale(locale);

    private static readonly HashSet<string> WarnedKeys = new();
}
