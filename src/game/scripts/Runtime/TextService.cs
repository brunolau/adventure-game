using System;
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
    /// <summary>Suffix of the less revealing Standard/Hard version of a text (localization/overrides/guidance_std.csv).</summary>
    public const string StdSuffix = ".std";

    /// <summary>
    /// True when the game shows the less revealing <c>&lt;key&gt;.std</c> texts: on Standard and Hard difficulty (owner
    /// 2026-10-08, "the game is hinting way too much in the texts and dialogues"). Set by GameRuntime; Easy keeps the base texts.
    /// </summary>
    public static Func<bool>? ReducedGuidance { get; set; }

    /// <summary>
    /// The key actually shown for <paramref name="key"/>: its <c>.std</c> variant when <see cref="ReducedGuidance"/> is on and
    /// the variant exists in the tables, else the key itself. The voice-over uses the same key for its file name.
    /// </summary>
    public static string VariantKey(string key)
    {
        if (string.IsNullOrEmpty(key) || key.EndsWith(StdSuffix) || ReducedGuidance?.Invoke() != true) return key;
        string variant = key + StdSuffix;
        string translated = TranslationServer.Translate(variant).ToString();
        return string.IsNullOrEmpty(translated) || translated == variant ? key : variant;
    }

    /// <summary>Translated text of <paramref name="key"/> (its Standard/Hard variant when shown), else <paramref name="fallback"/>.</summary>
    public static string Get(string key, string fallback = "")
    {
        if (string.IsNullOrEmpty(key)) return fallback ?? "";
        key = VariantKey(key);
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

    /// <summary>
    /// Translated <c>ui.*</c> text with a Slovak fallback from code, for UI strings that are drafts waiting for the owner's
    /// approval (docs/writing/out_v3/ui_difficulty.csv): until the row is in ui.csv the fallback shows, without a warning.
    /// </summary>
    public static string UiOr(string key, string fallback, params (string Name, string Value)[] args) => Format(Get(key, fallback), args);

    /// <summary>Replaces <c>{name}</c> placeholders (applied after Tr, see ui.csv convention).</summary>
    public static string Format(string text, params (string Name, string Value)[] args)
    {
        foreach (var (name, value) in args) text = text.Replace("{" + name + "}", value);
        return text;
    }

    /// <summary>The active locale (default "sk").</summary>
    public static string Locale => TranslationServer.GetLocale();

    /// <summary>Switches the locale (e.g. "sk", "en"); missing entries still fall back to Slovak.</summary>
    public static void SetLocale(string locale)
    {
        TranslationServer.SetLocale(locale);
        // The window title follows the language ("Posledný zvonec" / "The Last Bell").
        if (Engine.GetMainLoop() is SceneTree tree && tree.Root is { } root)
            root.Title = Get("game.title", root.Title);
    }

    private static readonly HashSet<string> WarnedKeys = new();
}
