using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Godot;
using LastBell.Core.Rules;
using LastBell.Core.State;
using LastBell.Game.PlayerInput;
using LastBell.Game.Runtime;
using LastBell.Game.UI;
using LastBell.Game.UI.Common;
using LastBell.Game.UI.Hud;
using LastBell.Game.UI.Inventory;
using LastBell.Game.UI.Settings;

namespace LastBell.Game.Diagnostics;

/// <summary>
/// Acceptance checks of the language switch (ISSUES UI-07; run with <c>-- --acceptance language</c>, also with
/// <c>--touch</c>): the language is changed in the settings by a real click or tap, once from the pause menu of a
/// running game and once from the title screen, and then every label, button and tooltip of the HUD and of every
/// screen is searched for texts of the old language.
/// "A text of the old language" is found with the game's own tables (ui.csv, world.csv, dialogue.csv): every text
/// that differs between the two columns and does not occur as a whole phrase in any text of the other column. So a
/// label that still says "Nastavenia" after the switch to English is found, and "Slovenčina", a name or a key name
/// that both languages share is not. Texts with placeholders are left out, and so are the credits entries (photo
/// titles and names from credits.json). Nothing is written to the settings file.
/// </summary>
public partial class DebugHarness
{
    /// <summary>The texts that only one of the two languages has.</summary>
    private sealed class LanguageProbe
    {
        private readonly Dictionary<string, Dictionary<string, List<string>>> byFirstWord = new();
        private readonly Dictionary<string, (string Sk, string En)> rows = new(StringComparer.Ordinal);

        public LanguageProbe()
        {
            foreach (var table in new[] { "ui", "world", "dialogue" })
            {
                using var file = FileAccess.Open($"res://localization/{table}.csv", FileAccess.ModeFlags.Read);
                if (file is null) continue;
                file.GetCsvLine(); // keys,sk,en
                while (!file.EofReached())
                {
                    var row = file.GetCsvLine();
                    if (row.Length >= 3 && row[0].Length > 0) rows[row[0]] = (row[1], row[2]);
                }
            }
            Index("sk", rows.Values.Select(r => (r.Sk, r.En)));
            Index("en", rows.Values.Select(r => (r.En, r.Sk)));
        }

        /// <summary>Rows read from the tables.</summary>
        public int Count => rows.Count;

        /// <summary>Phrases only this language has.</summary>
        public int PhraseCount(string language) => byFirstWord[language].Values.Sum(l => l.Count);

        /// <summary>The table text of a key in one language.</summary>
        public string Text(string key, string language) => rows.TryGetValue(key, out var row) ? (language == "sk" ? row.Sk : row.En) : "";

        private static string Norm(string text) => text.Trim().ToLowerInvariant();

        private void Index(string language, IEnumerable<(string Own, string Other)> pairs)
        {
            var list = pairs.ToList();
            string others = string.Join("\n", list.Select(p => Norm(p.Other)));
            var index = new Dictionary<string, List<string>>(StringComparer.Ordinal);
            foreach (string phrase in list.Where(p => Norm(p.Own) != Norm(p.Other)).Select(p => Norm(p.Own)).Distinct())
            {
                if (phrase.Length < 3 || phrase.Contains('{') || phrase.Contains('[') || !phrase.Any(char.IsLetter)) continue;
                if (HasPhrase(others, phrase)) continue; // the other language says this too (a name, "Menu", a key)
                string first = Words(phrase).FirstOrDefault() ?? "";
                if (first.Length == 0) continue;
                if (!index.TryGetValue(first, out var same)) index[first] = same = new List<string>();
                same.Add(phrase);
            }
            byFirstWord[language] = index;
        }

        private static IEnumerable<string> Words(string text)
        {
            int start = -1;
            for (int i = 0; i <= text.Length; i++)
            {
                bool letter = i < text.Length && char.IsLetterOrDigit(text[i]);
                if (letter && start < 0) start = i;
                else if (!letter && start >= 0)
                {
                    yield return text[start..i];
                    start = -1;
                }
            }
        }

        /// <summary>True when the phrase stands in the text as whole words.</summary>
        public static bool HasPhrase(string text, string phrase)
        {
            int at = 0;
            while ((at = text.IndexOf(phrase, at, StringComparison.Ordinal)) >= 0)
            {
                int end = at + phrase.Length;
                bool left = at == 0 || !char.IsLetterOrDigit(text[at - 1]) || !char.IsLetterOrDigit(phrase[0]);
                bool right = end == text.Length || !char.IsLetterOrDigit(text[end]) || !char.IsLetterOrDigit(phrase[^1]);
                if (left && right) return true;
                at++;
            }
            return false;
        }

        /// <summary>A phrase only <paramref name="language"/> has that stands in the text, or null.</summary>
        public string? PhraseIn(string text, string language)
        {
            string norm = Norm(text);
            var index = byFirstWord[language];
            foreach (string word in Words(norm).Distinct())
                if (index.TryGetValue(word, out var phrases))
                    foreach (string phrase in phrases)
                        if (HasPhrase(norm, phrase)) return phrase;
            return null;
        }
    }

    private static string OtherLanguage(string language) => language == "sk" ? "en" : "sk";

    private static string Short(string text) => text.Length <= 44 ? text.Replace("\n", " ") : text[..44].Replace("\n", " ") + "…";

    private static bool Under<T>(Node node) where T : Node
    {
        for (Node? p = node; p is not null; p = p.GetParent())
            if (p is T) return true;
        return false;
    }

    /// <summary>
    /// Texts of the labels, buttons and tooltips under the roots: how many carry a phrase of <paramref name="language"/>
    /// and which carry one of the other language. Passing lines, notices and the era card are not looked at.
    /// </summary>
    private (int Live, List<string> Stale) LanguageScan(LanguageProbe probe, string language, bool visibleOnly, params Node[] roots)
    {
        int live = 0;
        var stale = new List<string>();
        foreach (var root in roots)
        {
            foreach (var c in (root is Control self ? new[] { self } : Array.Empty<Control>()).Concat(Descendants<Control>(root)))
            {
                if (c is RichTextLabel || Under<SubtitleView>(c) || Under<ToastLayer>(c) || Under<LastBell.Game.UI.Cutscenes.EraCardView>(c)) continue;
                if (visibleOnly && !c.IsVisibleInTree()) continue;
                foreach (string text in new[] { c is Label l ? l.Text : c is Button b ? b.Text : "", c.TooltipText })
                {
                    if (text.Length == 0) continue;
                    if (probe.PhraseIn(text, language) is not null) live++;
                    if (probe.PhraseIn(text, OtherLanguage(language)) is { } old) stale.Add($"{PathOf(c)} '{Short(text)}' <- '{Short(old)}'");
                }
            }
        }
        return (live, stale);
    }

    /// <summary>What the rebuild after a language change covers: the HUD, the inventory and every screen, open or not.</summary>
    private static Node[] BuiltOnceRoots(UiRoot ui) =>
        Descendants<ModalScreen>(ui).Cast<Node>().Concat(Descendants<InventoryPanel>(ui)).Append(ui.Hud).ToArray();

    private static string StaleReport(List<string> stale) =>
        stale.Count == 0 ? "none" : stale.Count + ": " + string.Join(" | ", stale.Take(4));

    private async Task Press(Control control, string what)
    {
        for (Node? p = control.GetParent(); p is not null; p = p.GetParent())
            if (p is ScrollContainer scroll) scroll.EnsureControlVisible(control);
        await Frames(3);
        if (TouchMode.Enabled) await RawTouch(CanvasCenter(control), "tap");
        else await ClickControl(control, what);
        await Frames(8);
    }

    private static Button? ChoiceButton(Node? root, string text) => root is null ? null
        : Descendants<Button>(root).FirstOrDefault(b => b.IsVisibleInTree() && b.ToggleMode && b.Text == text);

    /// <summary>Changes the language in the open settings screen like a player: tab "Text", then the language button.</summary>
    private async Task<(bool Pressed, string Focus)> ChooseLanguage(LanguageProbe probe, string from, string to)
    {
        var ui = UiRoot.Instance!;
        var tab = ChoiceButton(ui.TopModal, probe.Text("ui.settings.tab_text", from));
        if (tab is not null) await Press(tab, "settings tab");
        var choice = ChoiceButton(ui.TopModal, probe.Text("ui.settings.language_" + to, from));
        if (choice is null) return (false, "-");
        await Press(choice, "language " + to);
        await Frames(6);
        var focus = GetViewport().GuiGetFocusOwner();
        return (true, focus is Button b ? $"{b.Text}{(b.ButtonPressed ? " (pressed)" : "")}" : focus?.Name.ToString() ?? "-");
    }

    private async Task RunLanguageChecks()
    {
        var game = GameRuntime.Instance;
        var ui = UiRoot.Instance!;
        UiSettings.QaNoSave = true;
        var probe = new LanguageProbe();
        string start = TextService.Locale;
        string target = OtherLanguage(start);
        game.NewGame();
        await Settle();
        await Seconds(0.5);
        ui.Toasts.ClearAll();

        // ---------------------------------------------------------------- before: the detector on an untouched UI
        var before = LanguageScan(probe, start, visibleOnly: false, BuiltOnceRoots(ui));
        Check("LG01_before_the_switch_every_text_is_in_the_starting_language",
            probe.Count > 5000 && probe.PhraseCount("sk") > 3000 && probe.PhraseCount("en") > 3000 && before.Live >= 30 && before.Stale.Count == 0,
            $"start='{start}' rows={probe.Count} phrases sk={probe.PhraseCount("sk")} en={probe.PhraseCount("en")} texts in '{start}'={before.Live} in '{target}': {StaleReport(before.Stale)}");

        // ---------------------------------------------------------------- the switch, from the pause menu of a running game
        game.Update(s => GameRules.OpenOverlay(s, GameMode.Pause));
        await Frames(6);
        ui.OpenSettings();
        await Frames(8);
        var settings = ui.TopModal;
        var (pressed, focus) = await ChooseLanguage(probe, start, target);
        string title = GetTree().Root.Title;
        var afterBuilt = LanguageScan(probe, target, visibleOnly: false, BuiltOnceRoots(ui));
        var afterSeen = LanguageScan(probe, target, visibleOnly: true, ui);
        bool sameScreen = ui.TopModal == settings && settings is { Visible: true } && LastBell.Game.UI.Menus.SettingsScreen.LastTab == 2;
        Check("LG02_the_language_button_changes_the_language_and_the_settings_stay_open_on_their_tab",
            pressed && TextService.Locale == target && UiSettings.Locale == target && sameScreen && title == probe.Text("game.title", target),
            $"pressed={pressed} locale={TextService.Locale} settings on top={ui.TopModal == settings} tab={LastBell.Game.UI.Menus.SettingsScreen.LastTab} window title='{title}'");
        Check("LG03_nothing_built_once_keeps_the_old_language",
            afterBuilt.Stale.Count == 0 && afterBuilt.Live >= 30 && afterSeen.Stale.Count == 0 && afterSeen.Live >= 10,
            $"HUD, inventory and screens: texts in '{target}'={afterBuilt.Live}, in '{start}': {StaleReport(afterBuilt.Stale)}; on screen: {afterSeen.Live}, in '{start}': {StaleReport(afterSeen.Stale)}");
        Check("LG04_the_focus_is_back_on_the_chosen_language",
            focus == probe.Text("ui.settings.language_" + target, target) + " (pressed)", $"focus='{focus}'");

        // ---------------------------------------------------------------- back into the game: pause menu, HUD
        ui.TopModal?.Back();
        await Frames(8);
        var pauseSeen = LanguageScan(probe, target, visibleOnly: true, ui);
        var resume = Descendants<Button>(ui).FirstOrDefault(b => b.IsVisibleInTree() && b.Text == probe.Text("ui.pause.resume", target));
        if (resume is not null) await Press(resume, "resume");
        await Frames(8);
        var hudSeen = LanguageScan(probe, target, visibleOnly: true, ui);
        string bagText = probe.Text("ui.hud.inventory", target);
        var bag = Descendants<Button>(ui.Hud).FirstOrDefault(b => b.IsVisibleInTree() && (b.TooltipText == bagText || b.TooltipText.StartsWith(bagText + " (", StringComparison.Ordinal)));
        if (bag is not null) await Press(bag, "HUD inventory");
        bool bagOpens = game.State.Mode == GameMode.Inventory;
        var bagSeen = LanguageScan(probe, target, visibleOnly: true, ui);
        if (game.State.Mode == GameMode.Inventory) WorldInput.Dispatch(LogicalCommand.Inventory);
        await Frames(6);
        Check("LG05_pause_menu_and_HUD_are_in_the_new_language_and_their_new_buttons_work",
            resume is not null && pauseSeen.Stale.Count == 0 && pauseSeen.Live >= 5 && hudSeen.Stale.Count == 0 && hudSeen.Live >= 4 &&
            bag is not null && bagOpens && bagSeen.Stale.Count == 0 && bagSeen.Live >= 3,
            $"pause: {pauseSeen.Live} texts, old: {StaleReport(pauseSeen.Stale)}; resume button={resume is not null}; HUD: {hudSeen.Live} texts, old: {StaleReport(hudSeen.Stale)}; " +
            $"inventory button={bag is not null} opens={bagOpens}, inventory: {bagSeen.Live} texts, old: {StaleReport(bagSeen.Stale)}");

        // ---------------------------------------------------------------- every screen, opened after the switch
        var problems = new List<string>();
        int screens = 0, texts = 0;
        async Task Look(string name, int least = 2)
        {
            await Frames(8);
            var seen = LanguageScan(probe, target, visibleOnly: true, ui);
            screens++;
            texts += seen.Live;
            if (seen.Stale.Count > 0) problems.Add($"{name}: {StaleReport(seen.Stale)}");
            else if (seen.Live < least) problems.Add($"{name}: only {seen.Live} texts in '{target}'");
        }
        async Task Overlay(GameMode mode, string name, string[]? tabKeys = null)
        {
            game.Update(s => GameRules.OpenOverlay(s, mode));
            await Look(name);
            foreach (string key in tabKeys ?? Array.Empty<string>())
            {
                var tab = Descendants<Button>(ui).FirstOrDefault(b => b.IsVisibleInTree() && b.ToggleMode && b.Text == probe.Text(key, target));
                if (tab is null) { problems.Add($"{name}: no tab '{probe.Text(key, target)}'"); continue; }
                await Press(tab, name + " tab");
                await Look(name + " / " + tab.Text);
            }
            game.Update(GameRules.CloseOverlay);
            await Frames(6);
        }
        async Task Modal(string name, Action open, string[]? tabKeys = null, int least = 2)
        {
            open();
            await Look(name, least);
            foreach (string key in tabKeys ?? Array.Empty<string>())
            {
                var tab = ChoiceButton(ui.TopModal, probe.Text(key, target));
                if (tab is null) { problems.Add($"{name}: no tab '{probe.Text(key, target)}'"); continue; }
                await Press(tab, name + " tab");
                await Look(name + " / " + tab.Text, least: 1);
            }
            if (ui.TopModal is { } top && top is not LastBell.Game.UI.Menus.MainMenuScreen) top.Back();
            await Frames(6);
        }
        string[] settingsTabs = { "ui.settings.tab_audio", "ui.settings.tab_text", "ui.settings.tab_display", "ui.settings.tab_accessibility", "ui.settings.tab_controls" };
        await Overlay(GameMode.Journal, "journal", new[] { "ui.journal.tab_findings", "ui.journal.tab_people", "ui.journal.tab_time_map", "ui.journal.tab_album", "ui.journal.tab_goals" });
        await Overlay(GameMode.Map, "map");
        await Modal("hints", () => ui.OpenHints());
        await Modal("help", ui.OpenHelp);
        await Modal("save", () => ui.OpenSaveLoad(true));
        await Modal("load", () => ui.OpenSaveLoad(false), least: 1);
        await Modal("credits", () => ui.OpenCredits(rolling: false));
        await Modal("confirmation", () => ui.Confirm(TextService.Ui("ui.menu.quit_confirm"), TextService.Ui("ui.menu.quit"), () => { }));
        game.Update(s => GameRules.OpenOverlay(s, GameMode.Pause));
        await Frames(6);
        await Modal("settings in the game", ui.OpenSettings, settingsTabs);
        game.Update(GameRules.CloseOverlay);
        await Frames(6);
        ui.ShowMainMenu();
        await Look("title screen", least: 4);
        await Modal("difficulty step", ui.OpenNewGame, least: 4);
        Check("LG06_every_screen_opened_after_the_switch_is_in_the_new_language", problems.Count == 0 && screens >= 20 && texts >= 150,
            $"{screens} views, {texts} texts in '{target}'" + (problems.Count == 0 ? "" : "; " + string.Join(" || ", problems.Take(5))));

        // ---------------------------------------------------------------- and back, from the title screen
        ui.OpenSettings();
        await Frames(8);
        settings = ui.TopModal;
        (pressed, focus) = await ChooseLanguage(probe, target, start);
        var backBuilt = LanguageScan(probe, start, visibleOnly: false, BuiltOnceRoots(ui));
        var backSeen = LanguageScan(probe, start, visibleOnly: true, ui);
        bool onTop = ui.TopModal == settings && ui.MainMenuOpen;
        ui.TopModal?.Back();
        await Frames(8);
        var menuSeen = LanguageScan(probe, start, visibleOnly: true, ui);
        Check("LG07_the_way_back_from_the_title_screen_leaves_nothing_in_the_other_language",
            pressed && TextService.Locale == start && onTop && backBuilt.Stale.Count == 0 && backBuilt.Live >= 30 && backSeen.Stale.Count == 0 &&
            menuSeen.Stale.Count == 0 && menuSeen.Live >= 4 && GetTree().Root.Title == probe.Text("game.title", start),
            $"pressed={pressed} locale={TextService.Locale} settings over the title screen={onTop} texts in '{start}'={backBuilt.Live}, in '{target}': {StaleReport(backBuilt.Stale)}; " +
            $"on screen: {StaleReport(backSeen.Stale)}; title screen: {menuSeen.Live} texts, old: {StaleReport(menuSeen.Stale)}; window title='{GetTree().Root.Title}'");
        Log($"acceptance language: {acceptanceFailures} failure(s)");
    }
}
