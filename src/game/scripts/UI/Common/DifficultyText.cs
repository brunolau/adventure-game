using LastBell.Core.State;

namespace LastBell.Game.UI.Common;

/// <summary>A ui.csv key with the Slovak text the code shows until the row exists in ui.csv.</summary>
/// <param name="Key">ui.csv key.</param>
/// <param name="Fallback">Slovak fallback (the draft text).</param>
public readonly record struct UiString(string Key, string Fallback);

/// <summary>
/// UI strings of the difficulty settings (docs/DECISIONS.md "Difficulty settings"). They are DRAFTS waiting for the
/// owner's approval: the same rows are in <c>docs/writing/out_v3/ui_difficulty.csv</c> (keys,sk_new,note). Until the
/// orchestrator adds them to ui.csv, <see cref="Theme.Ui.T(UiString, (string, string)[])"/> shows these fallbacks; after
/// the apply the table wins, so a fallback here never needs to change with an approved wording.
/// </summary>
public static class DifficultyText
{
    /// <summary>"Obťažnosť" (settings row, picker heading).</summary>
    public static readonly UiString Title = new("ui.difficulty.title", "Obťažnosť");

    /// <summary>New-game picker title.</summary>
    public static readonly UiString PickTitle = new("ui.difficulty.pick_title", "Nová hra");

    /// <summary>New-game picker intro.</summary>
    public static readonly UiString PickIntro = new("ui.difficulty.pick_intro",
        "Vyber si, ako veľmi ti má nápoveda pomáhať. Obťažnosť mení iba nápovedu a kedykoľvek ju zmeníš v nastaveniach.");

    /// <summary>New-game picker confirm button.</summary>
    public static readonly UiString Start = new("ui.difficulty.start", "Začať hru");

    /// <summary>Tag on the default choice.</summary>
    public static readonly UiString Recommended = new("ui.difficulty.recommended", "odporúčaná");

    /// <summary>Settings tab "Hra" (the difficulty row lives there).</summary>
    public static readonly UiString SettingsTab = new("ui.settings.tab_game", "Hra");

    /// <summary>Settings: description under the difficulty row during a game.</summary>
    public static readonly UiString SettingsInGame = new("ui.settings.difficulty_desc",
        "Platí pre rozohranú hru a uloží sa spolu s ňou.");

    /// <summary>Settings opened from the title screen (no game running).</summary>
    public static readonly UiString SettingsInMenu = new("ui.settings.difficulty_menu",
        "Obťažnosť si vyberieš pri novej hre. Počas hry ju zmeníš tu a každá uložená hra si pamätá svoju.");

    /// <summary>Hint screen: the current difficulty ({difficulty}).</summary>
    public static readonly UiString HintDifficulty = new("ui.hint.difficulty", "Obťažnosť: {difficulty}");

    /// <summary>Hint card label: Standard / Hard level 1.</summary>
    public static readonly UiString LevelNudge = new("ui.hint.level_nudge", "Postrčenie");

    /// <summary>Hint card label: Standard level 2.</summary>
    public static readonly UiString LevelWhere = new("ui.hint.level_where", "Kde hľadať");

    /// <summary>Hint screen: Standard after both levels.</summary>
    public static readonly UiString StandardEnd = new("ui.hint.standard_end",
        "Viac sa na štandardnej obťažnosti nedozvieš. Presný krok ukáže ľahká obťažnosť – prepneš ju v nastaveniach na karte Hra.");

    /// <summary>Hint screen: Hard while the nudge is not open yet ({time} = m:ss).</summary>
    public static readonly UiString HardWait = new("ui.hint.hard_wait", "Do postrčenia zostáva {time}.");

    /// <summary>Hint screen: the Hard rule, under the countdown.</summary>
    public static readonly UiString HardWaitNote = new("ui.hint.hard_wait_note",
        "Na ťažkej obťažnosti sa nápoveda otvorí po troch minútach bez pokroku.");

    /// <summary>Hint screen: the disabled reveal button on Hard while waiting ({time} = m:ss).</summary>
    public static readonly UiString HardWaitButton = new("ui.hint.hard_wait_button", "Ešte nie ({time})");

    /// <summary>Hint screen: Hard after the nudge.</summary>
    public static readonly UiString HardEnd = new("ui.hint.hard_end", "Na ťažkej obťažnosti je to všetko, čo nápoveda povie.");

    /// <summary>Hint screen: Hard on a puzzle step.</summary>
    public static readonly UiString HardNoPuzzle = new("ui.hint.hard_no_puzzle", "Na ťažkej obťažnosti hádanky riešiš bez pomoci.");

    /// <summary>HUD hint button tooltip on Hard while waiting ({time} = m:ss).</summary>
    public static readonly UiString HudWait = new("ui.hud.hint_wait", "Nápoveda (H): zostáva {time}");

    /// <summary>Name of a difficulty.</summary>
    public static UiString Name(Difficulty d) => d switch
    {
        Difficulty.Easy => new("ui.difficulty.easy", "Ľahká"),
        Difficulty.Hard => new("ui.difficulty.hard", "Ťažká"),
        _ => new("ui.difficulty.standard", "Štandardná"),
    };

    /// <summary>One-line description of a difficulty.</summary>
    public static UiString Description(Difficulty d) => d switch
    {
        Difficulty.Easy => new("ui.difficulty.easy_desc", "Nápoveda ukáže aj presný krok a riešenie hádanky ti na požiadanie vyplní."),
        Difficulty.Hard => new("ui.difficulty.hard_desc", "Iba krátke postrčenie, a to až po troch minútach bez pokroku. Hádanky bez pomoci."),
        _ => new("ui.difficulty.standard_desc", "Nápoveda ťa postrčí a povie, kde hľadať. Riešenie nechá na tebe."),
    };

    /// <summary>All difficulties in picker order.</summary>
    public static readonly Difficulty[] All = { Difficulty.Easy, Difficulty.Standard, Difficulty.Hard };

    /// <summary>A countdown as m:ss (rounded up, so it never shows 0:00 while still waiting).</summary>
    public static string Countdown(double seconds)
    {
        int total = (int)System.Math.Ceiling(System.Math.Max(0, seconds));
        return $"{total / 60}:{total % 60:00}";
    }
}
