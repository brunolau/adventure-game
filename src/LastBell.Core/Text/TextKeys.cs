using LastBell.Core.Content;

namespace LastBell.Core.Text;

/// <summary>
/// A reference to player-visible text: a stable localization key plus the Slovak fallback from game.json.
/// Core never formats display text; the presentation layer shows <c>Tr(Key)</c> and falls back to
/// <see cref="Fallback"/> when the translation table has no entry.
/// </summary>
/// <param name="Key">Localization key (see <see cref="TextKeys"/>).</param>
/// <param name="Fallback">Slovak text from the content data.</param>
public readonly record struct TextRef(string Key, string Fallback)
{
    /// <summary>The empty text (no key, no fallback), e.g. an empty action line.</summary>
    public static TextRef Empty => new("", "");

    /// <summary>True when there is nothing to show.</summary>
    public bool IsEmpty => string.IsNullOrEmpty(Key) && string.IsNullOrEmpty(Fallback);

    /// <inheritdoc />
    public override string ToString() => IsEmpty ? "" : $"{Key} \"{Fallback}\"";
}

/// <summary>
/// Builds localization keys exactly as specified by the key scheme table in design-doc/ARCHITECTURE.md.
/// Spaces inside ids are kept as-is. Both Core and the presentation layer use this class so keys match.
/// </summary>
public static class TextKeys
{
    // ---- raw key builders (one per row of the ARCHITECTURE.md table) ----

    /// <summary>Any line with a <c>line_id</c>: the line id itself.</summary>
    public static string Line(string lineId) => lineId;

    /// <summary><c>room.&lt;roomId&gt;.name</c>.</summary>
    public static string RoomName(string roomId) => $"room.{roomId}.name";

    /// <summary><c>hotspot.&lt;hotspotId&gt;.name</c>.</summary>
    public static string HotspotName(string hotspotId) => $"hotspot.{hotspotId}.name";

    /// <summary><c>hotspot.&lt;hotspotId&gt;.look</c> (used only when the look has no line id).</summary>
    public static string HotspotLook(string hotspotId) => $"hotspot.{hotspotId}.look";

    /// <summary><c>hotspot.&lt;hotspotId&gt;.look.&lt;n&gt;</c>, n from 1 (used only when the variant has no line id).</summary>
    public static string HotspotLookVariant(string hotspotId, int n) => $"hotspot.{hotspotId}.look.{n}";

    /// <summary><c>exit.&lt;exitId&gt;.label</c>.</summary>
    public static string ExitLabel(string exitId) => $"exit.{exitId}.label";

    /// <summary><c>exit.&lt;exitId&gt;.locked</c>.</summary>
    public static string ExitLocked(string exitId) => $"exit.{exitId}.locked";

    /// <summary><c>conn.&lt;from&gt;.&lt;to&gt;.label</c>.</summary>
    public static string ConnectionLabel(string from, string to) => $"conn.{from}.{to}.label";

    /// <summary><c>conn.&lt;from&gt;.&lt;to&gt;.locked</c>.</summary>
    public static string ConnectionLocked(string from, string to) => $"conn.{from}.{to}.locked";

    /// <summary><c>item.&lt;id&gt;.name</c>.</summary>
    public static string ItemName(string itemId) => $"item.{itemId}.name";

    /// <summary><c>item.&lt;id&gt;.look</c>, or the item's <c>look_line_id</c> when present.</summary>
    public static string ItemLook(string itemId, string? lookLineId = null) =>
        string.IsNullOrEmpty(lookLineId) ? $"item.{itemId}.look" : lookLineId;

    /// <summary><c>item.&lt;id&gt;.purpose</c>.</summary>
    public static string ItemPurpose(string itemId) => $"item.{itemId}.purpose";

    /// <summary><c>action.&lt;id&gt;.label</c>.</summary>
    public static string ActionLabel(string actionId) => $"action.{actionId}.label";

    /// <summary><c>action.&lt;id&gt;.journal</c>.</summary>
    public static string ActionJournal(string actionId) => $"action.{actionId}.journal";

    /// <summary><c>action.&lt;id&gt;.objective</c>.</summary>
    public static string ActionObjective(string actionId) => $"action.{actionId}.objective";

    /// <summary><c>char.&lt;id&gt;.name</c> (actors and non-actor speakers).</summary>
    public static string CharacterName(string characterId) => $"char.{characterId}.name";

    /// <summary><c>topic.&lt;topicId&gt;.label</c>.</summary>
    public static string TopicLabel(string topicId) => $"topic.{topicId}.label";

    /// <summary><c>quest.&lt;id&gt;.title</c>.</summary>
    public static string QuestTitle(string questId) => $"quest.{questId}.title";

    /// <summary><c>quest.&lt;id&gt;.goal</c>.</summary>
    public static string QuestGoal(string questId) => $"quest.{questId}.goal";

    /// <summary><c>quest.&lt;id&gt;.reward</c>.</summary>
    public static string QuestReward(string questId) => $"quest.{questId}.reward";

    /// <summary><c>quest.&lt;id&gt;.hint.&lt;n&gt;</c>, n from 1.</summary>
    public static string QuestHint(string questId, int n) => $"quest.{questId}.hint.{n}";

    /// <summary><c>puzzle.&lt;id&gt;.title</c>.</summary>
    public static string PuzzleTitle(string puzzleId) => $"puzzle.{puzzleId}.title";

    /// <summary><c>puzzle.&lt;id&gt;.clue</c>.</summary>
    public static string PuzzleClue(string puzzleId) => $"puzzle.{puzzleId}.clue";

    /// <summary><c>puzzle.&lt;id&gt;.wrong</c>.</summary>
    public static string PuzzleWrong(string puzzleId) => $"puzzle.{puzzleId}.wrong";

    /// <summary><c>puzzle.&lt;id&gt;.success</c>.</summary>
    public static string PuzzleSuccess(string puzzleId) => $"puzzle.{puzzleId}.success";

    /// <summary><c>puzzle.&lt;id&gt;.confirm</c>.</summary>
    public static string PuzzleConfirm(string puzzleId) => $"puzzle.{puzzleId}.confirm";

    /// <summary><c>era.&lt;year&gt;.card</c>.</summary>
    public static string EraCard(int year) => $"era.{year}.card";

    /// <summary><c>era.&lt;year&gt;.date</c>.</summary>
    public static string EraDate(int year) => $"era.{year}.date";

    /// <summary><c>epilogue.&lt;n&gt;.shot</c>, n from 1 (data order).</summary>
    public static string EpilogueShot(int n) => $"epilogue.{n}.shot";

    /// <summary><c>epilogue.&lt;n&gt;.line</c>, n from 1 (data order).</summary>
    public static string EpilogueLine(int n) => $"epilogue.{n}.line";

    /// <summary><c>ui.&lt;area&gt;.&lt;name&gt;</c>.</summary>
    public static string Ui(string area, string name) => $"ui.{area}.{name}";

    // ---- TextRef builders from content records ----

    /// <summary>Text of a line (key = line id; falls back to the text itself when the id is missing).</summary>
    public static TextRef Of(LineDef line) => new(line.LineId ?? "", line.Text);

    /// <summary>Room name.</summary>
    public static TextRef NameOf(RoomDef room) => new(RoomName(room.Id), room.Name);

    /// <summary>Hotspot name.</summary>
    public static TextRef NameOf(HotspotDef hotspot) => new(HotspotName(hotspot.Id), hotspot.Name);

    /// <summary>Base hotspot look.</summary>
    public static TextRef BaseLookOf(HotspotDef hotspot) =>
        new(string.IsNullOrEmpty(hotspot.LookLineId) ? HotspotLook(hotspot.Id) : hotspot.LookLineId, hotspot.Look);

    /// <summary>Look variant n (0-based index in data; the key uses n + 1).</summary>
    public static TextRef LookVariantOf(HotspotDef hotspot, int index)
    {
        var variant = hotspot.LookVariants[index];
        return new(string.IsNullOrEmpty(variant.LineId) ? HotspotLookVariant(hotspot.Id, index + 1) : variant.LineId, variant.Text);
    }

    /// <summary>Exit label.</summary>
    public static TextRef LabelOf(ExitDef exit) => new(ExitLabel(exit.Id), exit.Label);

    /// <summary>Exit locked look.</summary>
    public static TextRef LockedOf(ExitDef exit) => new(ExitLocked(exit.Id), exit.LockedLook);

    /// <summary>Connection label.</summary>
    public static TextRef LabelOf(ConnectionDef connection) => new(ConnectionLabel(connection.From, connection.To), connection.Label);

    /// <summary>Connection locked look.</summary>
    public static TextRef LockedOf(ConnectionDef connection) => new(ConnectionLocked(connection.From, connection.To), connection.LockedLook);

    /// <summary>Item name.</summary>
    public static TextRef NameOf(ItemDef item) => new(ItemName(item.Id), item.Name);

    /// <summary>Item look.</summary>
    public static TextRef LookOf(ItemDef item) => new(ItemLook(item.Id, item.LookLineId), item.Look);

    /// <summary>Item purpose.</summary>
    public static TextRef PurposeOf(ItemDef item) => new(ItemPurpose(item.Id), item.Purpose);

    /// <summary>Action label (also the hover text of an executable item rule).</summary>
    public static TextRef LabelOf(ActionDef action) => new(ActionLabel(action.Id), action.Label);

    /// <summary>Action journal transcript.</summary>
    public static TextRef JournalOf(ActionDef action) => new(ActionJournal(action.Id), action.JournalText);

    /// <summary>Action objective (empty when the action has none).</summary>
    public static TextRef ObjectiveOf(ActionDef action) =>
        action.Objective is null ? TextRef.Empty : new(ActionObjective(action.Id), action.Objective);

    /// <summary>Character name.</summary>
    public static TextRef NameOf(CharacterDef character) => new(CharacterName(character.Id), character.Name);

    /// <summary>Ambient topic label.</summary>
    public static TextRef LabelOf(TopicDef topic) => new(TopicLabel(topic.Id), topic.Label);

    /// <summary>Quest title.</summary>
    public static TextRef TitleOf(QuestDef quest) => new(QuestTitle(quest.Id), quest.Title);

    /// <summary>Quest goal.</summary>
    public static TextRef GoalOf(QuestDef quest) => new(QuestGoal(quest.Id), quest.Goal);

    /// <summary>Quest hint n (0-based index; the key uses n + 1).</summary>
    public static TextRef HintOf(QuestDef quest, int index) => new(QuestHint(quest.Id, index + 1), quest.Hints[index]);

    /// <summary>Puzzle title.</summary>
    public static TextRef TitleOf(PuzzleDef puzzle) => new(PuzzleTitle(puzzle.Id), puzzle.Title);

    /// <summary>Puzzle clue.</summary>
    public static TextRef ClueOf(PuzzleDef puzzle) => new(PuzzleClue(puzzle.Id), puzzle.Clue);

    /// <summary>Puzzle wrong-answer line ("SPEAKER: text" in the fallback).</summary>
    public static TextRef WrongOf(PuzzleDef puzzle) => new(PuzzleWrong(puzzle.Id), puzzle.WrongLine);

    /// <summary>Puzzle success line ("SPEAKER: text" in the fallback).</summary>
    public static TextRef SuccessOf(PuzzleDef puzzle) => new(PuzzleSuccess(puzzle.Id), puzzle.SuccessLine);

    /// <summary>Puzzle confirm button label (empty when the controls have none).</summary>
    public static TextRef ConfirmOf(PuzzleDef puzzle) =>
        puzzle.Controls.ConfirmLabel is null ? TextRef.Empty : new(PuzzleConfirm(puzzle.Id), puzzle.Controls.ConfirmLabel);

    /// <summary>Era date (fallback: ISO date from data).</summary>
    public static TextRef DateOf(EraDef era) => new(EraDate(era.Year), era.Date);

    /// <summary>Era title card (game.json has no card text; the fallback is the ISO date).</summary>
    public static TextRef CardOf(EraDef era) => new(EraCard(era.Year), era.Date);

    /// <summary>Epilogue shot caption (index is 0-based in data).</summary>
    public static TextRef ShotOf(EpilogueDef entry, int index) => new(EpilogueShot(index + 1), entry.Shot);

    /// <summary>Epilogue line (index is 0-based in data).</summary>
    public static TextRef LineOf(EpilogueDef entry, int index) => new(EpilogueLine(index + 1), entry.Line);
}

/// <summary>System messages that Core itself produces (keys follow <c>ui.&lt;area&gt;.&lt;name&gt;</c>).</summary>
public static class UiText
{
    /// <summary>Corrupt or unknown save import (handoff wording).</summary>
    public static TextRef SaveCorrupt => new(TextKeys.Ui("save", "corrupt"), "Chybný súbor uloženia. Aktuálna hra zostala otvorená.");

    /// <summary>No path to the interaction point (a navmesh bug, never a puzzle).</summary>
    public static TextRef PathBlocked => new(TextKeys.Ui("world", "path_blocked"), "Len o krok bokom, tadiaľto sa nedostanem.");

    /// <summary>First-start help bubble 1.</summary>
    public static TextRef HelpLeftClick => new(TextKeys.Ui("help", "left_click"), "Ľavým klikom vykonáš akciu.");

    /// <summary>First-start help bubble 2.</summary>
    public static TextRef HelpRightClick => new(TextKeys.Ui("help", "right_click"), "Pravým prezrieš objekt; na voľnom mieste otvoríš inventár.");

    /// <summary>First-start help bubble 3.</summary>
    public static TextRef HelpSpace => new(TextKeys.Ui("help", "space"), "Space ukáže všetky miesta, na ktoré môžeš kliknúť.");
}
