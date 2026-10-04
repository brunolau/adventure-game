using LastBell.Core.Content;
using LastBell.Core.State;
using LastBell.Core.Text;

namespace LastBell.Core.Rules;

/// <summary>A heard conversation entry for the transcript ("People" journal tab).</summary>
/// <param name="SourceId">Action id or ambient topic id.</param>
/// <param name="Label">Topic label.</param>
/// <param name="Lines">The lines (speaker id + text).</param>
public sealed record TranscriptEntry(string SourceId, TextRef Label, IReadOnlyList<(string SpeakerId, TextRef Text)> Lines);

/// <summary>
/// NPC conversations. Clicking an NPC without an item lists story topics (valid <c>topic</c> actions on
/// that NPC hotspot) followed by ambient topics whose <c>requires_done</c> are met. Item actions on NPCs
/// are not topics. Done story topics move to the transcript; ambient topics repeat without state change.
/// </summary>
public static class Dialogue
{
    /// <summary>Journal marker for an ambient topic that has been heard.</summary>
    public static string TopicEntryKey(string topicId) => "topic." + topicId;

    /// <summary>The topic menu of an NPC hotspot (same list the resolver returns).</summary>
    public static IReadOnlyList<TopicOption> TopicsFor(GameContent content, GameState state, HotspotDef npcHotspot)
    {
        var options = new List<TopicOption>();
        foreach (var action in content.Actions)
        {
            if (action.IsTopic && action.Target == npcHotspot.Id && GameRules.ValidAction(content, state, action))
                options.Add(new TopicOption(action.Id, TextKeys.LabelOf(action), action, null));
        }
        var character = npcHotspot.CharacterId is null ? null : content.FindCharacter(npcHotspot.CharacterId);
        if (character is not null)
        {
            foreach (var topic in character.AmbientTopics)
            {
                if (!state.AllDone(topic.RequiresDone)) continue;
                if (!topic.Repeatable && state.JournalSeen.Contains(TopicEntryKey(topic.Id))) continue;
                options.Add(new TopicOption(topic.Id, TextKeys.LabelOf(topic), null, topic));
            }
        }
        return options;
    }

    /// <summary>Opens the topic menu (dialogue mode without an active line).</summary>
    public static GameState OpenMenu(GameState state) =>
        state.Mode is GameMode.World or GameMode.Inventory ? state with { Mode = GameMode.Dialogue, ActiveLineId = null } : state;

    /// <summary>Closes the topic menu back to the world.</summary>
    public static GameState CloseMenu(GameState state) =>
        state.Mode == GameMode.Dialogue && state.ActiveLineId is null ? state with { Mode = GameMode.World } : state;

    /// <summary>
    /// Starts an ambient topic: plays its lines and records it as heard. Ambient topics never change
    /// progression state. Returns the state unchanged if the topic is unknown or not offered.
    /// </summary>
    public static GameState StartTopic(GameContent content, GameState state, string topicId)
    {
        if (state.Mode is not (GameMode.World or GameMode.Inventory or GameMode.Dialogue) || state.ActiveLineId is not null) return state;
        var found = content.FindTopic(topicId);
        if (found is null) return state;
        var (character, topic) = found.Value;
        var present = content.GetRoom(state.Room).Hotspots.Any(h => h.IsNpc && h.CharacterId == character.Id && GameRules.IsVisible(h, state));
        if (!present || !state.AllDone(topic.RequiresDone)) return state;
        if (!topic.Repeatable && state.JournalSeen.Contains(TopicEntryKey(topic.Id))) return state;
        var next = state with { JournalSeen = IdList.AddUnique(state.JournalSeen, TopicEntryKey(topic.Id)) };
        return Playback.Start(content, next, topic.Lines.Select(l => l.LineId ?? "").Where(id => id.Length > 0).ToList());
    }

    /// <summary>Transcript of everything heard from a character: done story actions targeting them, then heard ambient topics.</summary>
    public static IReadOnlyList<TranscriptEntry> Transcript(GameContent content, GameState state, string characterId)
    {
        var npcHotspots = new HashSet<string>(content.Rooms.SelectMany(r => r.Hotspots)
            .Where(h => h.IsNpc && h.CharacterId == characterId).Select(h => h.Id), StringComparer.Ordinal);
        var entries = new List<TranscriptEntry>();
        foreach (var id in state.Done)
        {
            var action = content.GetAction(id);
            if (!npcHotspots.Contains(action.Target)) continue;
            entries.Add(new TranscriptEntry(action.Id, TextKeys.LabelOf(action), action.Lines.Select(l => (l.Speaker, TextKeys.Of(l))).ToList()));
        }
        var character = content.FindCharacter(characterId);
        if (character is not null)
        {
            foreach (var topic in character.AmbientTopics)
            {
                if (state.JournalSeen.Contains(TopicEntryKey(topic.Id)))
                    entries.Add(new TranscriptEntry(topic.Id, TextKeys.LabelOf(topic), topic.Lines.Select(l => (l.Speaker, TextKeys.Of(l))).ToList()));
            }
        }
        return entries;
    }

    /// <summary>Characters the hero has talked to or acted with (story actions on their hotspots or heard topics).</summary>
    public static IReadOnlyList<CharacterDef> MetCharacters(GameContent content, GameState state) =>
        content.Data.Characters.Where(c => Transcript(content, state, c.Id).Count > 0).ToList();
}
