namespace LastBell.Core.Content;

/// <summary>
/// Structural validation of game.json (reference checks of validate_handoff.py plus id uniqueness).
/// Every error names the offending id and its JSON path, so a broken content file never produces
/// a silently empty dialogue.
/// </summary>
public static class ContentValidator
{
    /// <summary>Returns all errors ("$.path: message"); an empty list means the content is valid.</summary>
    public static IReadOnlyList<string> Validate(GameData d)
    {
        var errors = new List<string>();
        void Err(string path, string message) => errors.Add($"{path}: {message}");

        var roomIds = Unique(d.Rooms.Select(r => r.Id), "$.rooms", "room", Err);
        var actionIds = Unique(d.Actions.Select(a => a.Id), "$.actions", "action", Err);
        var itemIds = Unique(d.Items.Select(i => i.Id), "$.items", "item", Err);
        var characterIds = Unique(d.Characters.Select(c => c.Id), "$.characters", "character", Err);
        var puzzleIds = Unique(d.Puzzles.Select(p => p.Id), "$.puzzles", "puzzle", Err);
        var cutsceneIds = Unique(d.Cutscenes.Select(c => c.Id), "$.cutscenes", "cutscene", Err);
        var questIds = Unique(d.Quests.Select(q => q.Id), "$.quests", "quest", Err);
        var hotspotIds = Unique(d.Rooms.SelectMany(r => r.Hotspots).Select(h => h.Id), "$.rooms[*].hotspots", "hotspot", Err);
        Unique(d.Rooms.SelectMany(r => r.Exits).Select(e => e.Id), "$.rooms[*].exits", "exit", Err);
        var speakers = new HashSet<string>(characterIds.Concat(d.NonActorSpeakers.Keys), StringComparer.Ordinal);
        var years = new HashSet<int>(d.Eras.Select(e => e.Year));

        void Actions(string path, IEnumerable<string> ids)
        {
            var i = 0;
            foreach (var id in ids)
            {
                if (!actionIds.Contains(id)) Err($"{path}[{i}]", $"unknown action '{id}'");
                i++;
            }
        }
        void Items(string path, IEnumerable<string> ids)
        {
            var i = 0;
            foreach (var id in ids)
            {
                if (!itemIds.Contains(id)) Err($"{path}[{i}]", $"unknown item '{id}'");
                i++;
            }
        }
        void Lines(string path, IReadOnlyList<LineDef> lines, bool requireNonEmpty)
        {
            if (requireNonEmpty && lines.Count == 0) Err(path, "no lines");
            for (var i = 0; i < lines.Count; i++)
            {
                if (string.IsNullOrWhiteSpace(lines[i].Text)) Err($"{path}[{i}].text", "empty line text");
                if (!speakers.Contains(lines[i].Speaker)) Err($"{path}[{i}].speaker", $"unknown speaker '{lines[i].Speaker}'");
                if (string.IsNullOrEmpty(lines[i].LineId)) Err($"{path}[{i}].line_id", "missing line id");
            }
        }

        // Rooms, hotspots, exits.
        var hotspotRoom = new Dictionary<string, string>(StringComparer.Ordinal);
        for (var r = 0; r < d.Rooms.Count; r++)
        {
            var room = d.Rooms[r];
            var rp = $"$.rooms[{r}]({room.Id})";
            if (!years.Contains(room.Era)) Err($"{rp}.era", $"unknown era {room.Era}");
            Lines($"{rp}.first_entry", room.FirstEntry, requireNonEmpty: false);
            for (var h = 0; h < room.Hotspots.Count; h++)
            {
                var hs = room.Hotspots[h];
                var hp = $"{rp}.hotspots[{h}]({hs.Id})";
                hotspotRoom.TryAdd(hs.Id, room.Id);
                Actions($"{hp}.visible_after", hs.VisibleAfter);
                Actions($"{hp}.hide_after", hs.HideAfter);
                for (var v = 0; v < hs.LookVariants.Count; v++)
                    if (!actionIds.Contains(hs.LookVariants[v].After)) Err($"{hp}.look_variants[{v}].after", $"unknown action '{hs.LookVariants[v].After}'");
                if (hs.Kind != "npc" && hs.Kind != "prop") Err($"{hp}.kind", $"unknown hotspot kind '{hs.Kind}'");
                if (hs.IsNpc && (hs.CharacterId is null || !characterIds.Contains(hs.CharacterId)))
                    Err($"{hp}.character_id", $"unknown character '{hs.CharacterId}'");
                if (hs.Rect.Count != 4) Err($"{hp}.rect", "rect must have 4 numbers");
            }
            for (var e = 0; e < room.Exits.Count; e++)
            {
                var ex = room.Exits[e];
                var ep = $"{rp}.exits[{e}]({ex.Id})";
                if (!roomIds.Contains(ex.To)) Err($"{ep}.to", $"unknown room '{ex.To}'");
                Actions($"{ep}.requires_done", ex.RequiresDone);
            }
            for (var n = 0; n < room.NpcIds.Count; n++)
                if (!characterIds.Contains(room.NpcIds[n])) Err($"{rp}.npc_ids[{n}]", $"unknown character '{room.NpcIds[n]}'");
        }

        // Characters and topics.
        for (var c = 0; c < d.Characters.Count; c++)
        {
            var ch = d.Characters[c];
            var cp = $"$.characters[{c}]({ch.Id})";
            for (var r = 0; r < ch.Rooms.Count; r++)
                if (!roomIds.Contains(ch.Rooms[r])) Err($"{cp}.rooms[{r}]", $"unknown room '{ch.Rooms[r]}'");
            for (var t = 0; t < ch.AmbientTopics.Count; t++)
            {
                var tp = $"{cp}.ambient_topics[{t}]({ch.AmbientTopics[t].Id})";
                Actions($"{tp}.requires_done", ch.AmbientTopics[t].RequiresDone);
                Lines($"{tp}.lines", ch.AmbientTopics[t].Lines, requireNonEmpty: true);
            }
        }

        // Actions.
        for (var a = 0; a < d.Actions.Count; a++)
        {
            var ac = d.Actions[a];
            var ap = $"$.actions[{a}]({ac.Id})";
            if (ac.Kind is not ("click" or "topic" or "combine")) Err($"{ap}.kind", $"unknown action kind '{ac.Kind}'");
            if (ac.Room != GameContent.InventoryRoom && !roomIds.Contains(ac.Room)) Err($"{ap}.room", $"unknown room '{ac.Room}'");
            if (ac.Kind == "combine")
            {
                if (!itemIds.Contains(ac.Target)) Err($"{ap}.target", $"unknown item '{ac.Target}'");
                if (ac.Room != GameContent.InventoryRoom) Err($"{ap}.room", "combine actions must use room 'inventory'");
            }
            else if (!hotspotIds.Contains(ac.Target)) Err($"{ap}.target", $"unknown hotspot '{ac.Target}'");
            else if (ac.Room != GameContent.InventoryRoom && hotspotRoom.GetValueOrDefault(ac.Target) != ac.Room)
                Err($"{ap}.target", $"hotspot '{ac.Target}' is not in room '{ac.Room}'");
            Actions($"{ap}.requires_done", ac.RequiresDone);
            Actions($"{ap}.excluded_done", ac.ExcludedDone);
            Items($"{ap}.requires_items", ac.RequiresItems);
            Items($"{ap}.gives", ac.Gives);
            Items($"{ap}.consumes", ac.Consumes);
            foreach (var c in ac.Consumes)
                if (!ac.RequiresItems.Contains(c)) Err($"{ap}.consumes", $"consumed item '{c}' is not declared in requires_items");
            if (ac.SelectedItem is not null && !ac.RequiresItems.Contains(ac.SelectedItem))
                Err($"{ap}.selected_item", $"selected item '{ac.SelectedItem}' is not declared in requires_items");
            if (ac.Puzzle is not null && !puzzleIds.Contains(ac.Puzzle)) Err($"{ap}.puzzle", $"unknown puzzle '{ac.Puzzle}'");
            if (ac.Cutscene is not null && !cutsceneIds.Contains(ac.Cutscene)) Err($"{ap}.cutscene", $"unknown cutscene '{ac.Cutscene}'");
            Lines($"{ap}.lines", ac.Lines, requireNonEmpty: true);
        }

        // Cutscenes.
        for (var c = 0; c < d.Cutscenes.Count; c++)
            for (var b = 0; b < d.Cutscenes[c].Beats.Count; b++)
                Lines($"$.cutscenes[{c}]({d.Cutscenes[c].Id}).beats[{b}].lines", d.Cutscenes[c].Beats[b].Lines, requireNonEmpty: false);

        // Quests: every action belongs to exactly one quest.
        var owner = new Dictionary<string, string>(StringComparer.Ordinal);
        for (var q = 0; q < d.Quests.Count; q++)
        {
            var qu = d.Quests[q];
            var qp = $"$.quests[{q}]({qu.Id})";
            Actions($"{qp}.actions", qu.Actions);
            if (!qu.Actions.Contains(qu.Completion)) Err($"{qp}.completion", $"completion '{qu.Completion}' is not one of the quest actions");
            if (qu.Type is not ("main" or "side")) Err($"{qp}.type", $"unknown quest type '{qu.Type}'");
            foreach (var id in qu.Actions)
                if (!owner.TryAdd(id, qu.Id)) Err($"{qp}.actions", $"action '{id}' already belongs to quest '{owner[id]}'");
        }
        var questType = d.Quests.GroupBy(q => q.Id).ToDictionary(g => g.Key, g => g.First().Type, StringComparer.Ordinal);
        foreach (var ac in d.Actions)
        {
            if (!owner.TryGetValue(ac.Id, out var questId)) Err("$.quests", $"action '{ac.Id}' belongs to no quest");
            else if (ac.Quest == "main" ? questType[questId] != "main" : ac.Quest != questId)
                Err($"$.actions({ac.Id}).quest", $"quest field '{ac.Quest}' does not match owning quest '{questId}'");
        }

        // Graph, eras, transitions, postgame.
        for (var c = 0; c < d.Connections.Count; c++)
        {
            var co = d.Connections[c];
            var cp = $"$.connections[{c}]({co.From}->{co.To})";
            if (!roomIds.Contains(co.From)) Err($"{cp}.from", $"unknown room '{co.From}'");
            if (!roomIds.Contains(co.To)) Err($"{cp}.to", $"unknown room '{co.To}'");
            Actions($"{cp}.requires_done", co.RequiresDone);
        }
        for (var e = 0; e < d.Eras.Count; e++)
        {
            var era = d.Eras[e];
            if (!roomIds.Contains(era.Anchor)) Err($"$.eras[{e}]({era.Year}).anchor", $"unknown room '{era.Anchor}'");
            if (era.UnlockedBy is not null && !actionIds.Contains(era.UnlockedBy)) Err($"$.eras[{e}]({era.Year}).unlocked_by", $"unknown action '{era.UnlockedBy}'");
        }
        for (var n = 0; n < d.AnchorNodes.Count; n++)
        {
            var node = d.AnchorNodes[n];
            if (!roomIds.Contains(node.Room)) Err($"$.anchor_nodes[{n}].room", $"unknown room '{node.Room}'");
            if (!years.Contains(node.Year)) Err($"$.anchor_nodes[{n}].year", $"unknown era {node.Year}");
            Actions($"$.anchor_nodes[{n}].requires_done", node.RequiresDone);
        }
        for (var t = 0; t < d.SpecialTransitions.Count; t++)
        {
            var tr = d.SpecialTransitions[t];
            if (!actionIds.Contains(tr.After)) Err($"$.special_transitions[{t}].after", $"unknown action '{tr.After}'");
            if (!roomIds.Contains(tr.To)) Err($"$.special_transitions[{t}].to", $"unknown room '{tr.To}'");
        }
        if (!actionIds.Contains(d.Postgame.Unlock)) Err("$.postgame.unlock", $"unknown action '{d.Postgame.Unlock}'");
        Items("$.postgame.return_items", d.Postgame.ReturnItems);

        // Effects, epilogue, variants, cache.
        for (var c = 0; c < d.CausalEffects.Count; c++)
        {
            var ce = d.CausalEffects[c];
            if (!actionIds.Contains(ce.After)) Err($"$.causal_effects[{c}].after", $"unknown action '{ce.After}'");
            for (var r = 0; r < ce.At.Count; r++)
                if (!roomIds.Contains(ce.At[r])) Err($"$.causal_effects[{c}].at[{r}]", $"unknown room '{ce.At[r]}'");
        }
        for (var e = 0; e < d.Epilogue.Count; e++)
        {
            if (!actionIds.Contains(d.Epilogue[e].After)) Err($"$.epilogue[{e}].after", $"unknown action '{d.Epilogue[e].After}'");
            if (!questIds.Contains(d.Epilogue[e].Quest)) Err($"$.epilogue[{e}].quest", $"unknown quest '{d.Epilogue[e].Quest}'");
        }
        for (var v = 0; v < d.VisualVariantLayers.Count; v++)
        {
            var layer = d.VisualVariantLayers[v];
            if (!roomIds.Contains(layer.Room)) Err($"$.visual_variant_layers[{v}].room", $"unknown room '{layer.Room}'");
            if (!actionIds.Contains(layer.After)) Err($"$.visual_variant_layers[{v}].after", $"unknown action '{layer.After}'");
        }
        for (var b = 0; b < d.ButterflyEffects.Count; b++)
        {
            var bf = d.ButterflyEffects[b];
            if (!actionIds.Contains(bf.Trigger)) Err($"$.butterfly_effects[{b}].trigger", $"unknown action '{bf.Trigger}'");
            for (var r = 0; r < bf.VisibleRooms.Count; r++)
                if (!roomIds.Contains(bf.VisibleRooms[r])) Err($"$.butterfly_effects[{b}].visible_rooms[{r}]", $"unknown room '{bf.VisibleRooms[r]}'");
        }
        var cache = d.CacheContract;
        Items("$.cache_contract.physical_item_lineage", cache.PhysicalItemLineage);
        Actions("$.cache_contract", new[] { cache.CreatedBy, cache.SealedBy, cache.StoredBy, cache.RetrievedBy, cache.OpenedBy, cache.UsedBy });
        Actions("$.cache_contract.preserved_by", cache.PreservedBy);
        for (var f = 0; f < d.LocationFamilies.Count; f++)
            foreach (var (year, room) in d.LocationFamilies[f].Versions)
                if (!roomIds.Contains(room)) Err($"$.location_families[{f}].versions.{year}", $"unknown room '{room}'");

        // Line ids are unique across the whole content (they are localization keys).
        var lineIds = new HashSet<string>(StringComparer.Ordinal);
        IEnumerable<(string Path, LineDef Line)> AllLines()
        {
            for (var a = 0; a < d.Actions.Count; a++)
                foreach (var l in d.Actions[a].Lines) yield return ($"$.actions[{a}].lines", l);
            foreach (var c in d.Characters)
                foreach (var t in c.AmbientTopics)
                    foreach (var l in t.Lines) yield return ($"$.characters({c.Id}).ambient_topics({t.Id})", l);
            foreach (var r in d.Rooms)
                foreach (var l in r.FirstEntry) yield return ($"$.rooms({r.Id}).first_entry", l);
            foreach (var c in d.Cutscenes)
                foreach (var b in c.Beats)
                    foreach (var l in b.Lines) yield return ($"$.cutscenes({c.Id}).beats", l);
        }
        foreach (var (path, line) in AllLines())
            if (!string.IsNullOrEmpty(line.LineId) && !lineIds.Add(line.LineId)) Err(path, $"duplicate line id '{line.LineId}'");

        return errors;
    }

    private static HashSet<string> Unique(IEnumerable<string> ids, string path, string what, Action<string, string> err)
    {
        var set = new HashSet<string>(StringComparer.Ordinal);
        foreach (var id in ids)
        {
            if (string.IsNullOrEmpty(id)) err(path, $"{what} with empty id");
            else if (!set.Add(id)) err(path, $"duplicate {what} id '{id}'");
        }
        return set;
    }
}
