using LastBell.Core.Content;
using LastBell.Core.State;
using LastBell.Core.Text;

namespace LastBell.Core.Rules;

/// <summary>One credits shot.</summary>
/// <param name="Index">0-based index in <c>epilogue</c> (key n = Index + 1).</param>
/// <param name="QuestId">Side quest id.</param>
/// <param name="Shot">Shot caption.</param>
/// <param name="Line">Spoken line ("SPEAKER: text" in the fallback).</param>
/// <param name="SpeakerId">Speaker id parsed from the line prefix, or null.</param>
public sealed record EpilogueShot(int Index, string QuestId, TextRef Shot, TextRef Line, string? SpeakerId);

/// <summary>
/// Epilogue selection (epilogue_rules): only completed episodes, in Q1..Q9 order, 5–7 seconds each;
/// Q9 needs only Q9C. Without completed side quests the credits roll directly. After the postgame the
/// ending can be replayed from the album with new episodes.
/// </summary>
public static class Epilogue
{
    /// <summary>Minimum seconds per shot.</summary>
    public const double ShotMinSeconds = 5;

    /// <summary>Maximum seconds per shot.</summary>
    public const double ShotMaxSeconds = 7;

    /// <summary>The shots to play, in data order.</summary>
    public static IReadOnlyList<EpilogueShot> Select(GameContent content, GameState state)
    {
        var shots = new List<EpilogueShot>();
        var entries = content.Data.Epilogue;
        for (var i = 0; i < entries.Count; i++)
        {
            var e = entries[i];
            if (!state.IsDone(e.After)) continue;
            var colon = e.Line.IndexOf(':');
            var speaker = colon > 0 ? e.Line[..colon].Trim() : null;
            if (speaker is not null && content.FindCharacter(speaker) is null && !content.Data.NonActorSpeakers.ContainsKey(speaker)) speaker = null;
            shots.Add(new EpilogueShot(i, e.Quest, TextKeys.ShotOf(e, i), TextKeys.LineOf(e, i), speaker));
        }
        return shots;
    }

    /// <summary>True when no episode is completed and the credits roll directly.</summary>
    public static bool GoesStraightToCredits(GameContent content, GameState state) => Select(content, state).Count == 0;
}

/// <summary>
/// Postgame (after F17): the stabilised windows stay open for side quests, main actions never reset,
/// the evidence was returned to the bag in the F17 transaction, and the finale can only be replayed as
/// a cutscene, never as a transaction.
/// </summary>
public static class Postgame
{
    /// <summary>True after the postgame unlock action.</summary>
    public static bool IsActive(GameContent content, GameState state) => state.IsDone(content.Data.Postgame.Unlock);

    /// <summary>Cutscenes whose actions are done (replay list), in commit order.</summary>
    public static IReadOnlyList<string> ReplayableCutscenes(GameContent content, GameState state) =>
        state.Done.Select(content.GetAction).Where(a => a.Cutscene is not null).Select(a => a.Cutscene!).Distinct().ToList();

    /// <summary>Replays a watched cutscene from the scene list. Pure playback: no rule state changes.</summary>
    public static GameState ReplayCutscene(GameContent content, GameState state, string cutsceneId)
    {
        if (state.Mode is not (GameMode.World or GameMode.Journal or GameMode.Pause)) return state;
        if (!ReplayableCutscenes(content, state).Contains(cutsceneId)) return state;
        var cutscene = content.FindCutscene(cutsceneId);
        return cutscene is null ? state : Playback.Start(content, state, Playback.CutsceneLineIds(cutscene).ToList());
    }
}
