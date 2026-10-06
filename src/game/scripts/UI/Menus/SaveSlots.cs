using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using LastBell.Core.Save;
using LastBell.Core.State;
using LastBell.Core.Text;
using LastBell.Game.Runtime;

namespace LastBell.Game.UI.Menus;

/// <summary>One save slot as the save/load screens show it.</summary>
/// <param name="Slot">Slot name (file name without .json).</param>
/// <param name="Exists">A file exists.</param>
/// <param name="State">The validated state (null when empty or corrupt).</param>
/// <param name="ModifiedUnix">File time (unix seconds, UTC).</param>
/// <param name="Error">Core's readable error for a corrupt file.</param>
public sealed record SlotInfo(string Slot, bool Exists, GameState? State, ulong ModifiedUnix, TextRef Error)
{
    /// <summary>True for a readable save.</summary>
    public bool Valid => State is not null;

    /// <summary>True for a file that Core rejected.</summary>
    public bool Corrupt => Exists && State is null;
}

/// <summary>Slot naming and inspection (every file is validated by Core's SaveCodec, never trusted).</summary>
public static class SaveSlots
{
    /// <summary>Manual slots.</summary>
    public static readonly string[] Manual = { "slot1", "slot2", "slot3", "slot4", "slot5", "slot6", "slot7", "slot8" };

    /// <summary>Quick save slot (F5 / F9).</summary>
    public const string Quick = "quick";

    /// <summary>Reads and validates a slot.</summary>
    public static SlotInfo Inspect(string slot)
    {
        if (!GameRuntime.SlotExists(slot)) return new SlotInfo(slot, false, null, 0, TextRef.Empty);
        var game = GameRuntime.Instance;
        string path = GameRuntime.SlotPath(slot);
        ulong time = Godot.FileAccess.GetModifiedTime(path);
        string json = Godot.FileAccess.GetFileAsString(path);
        try
        {
            if (SaveCodec.TryLoad(game.Content, json, out var state, out TextRef error, out _)) return new SlotInfo(slot, true, state, time, TextRef.Empty);
            return new SlotInfo(slot, true, null, time, error);
        }
        catch (Exception)
        {
            return new SlotInfo(slot, true, null, time, LastBell.Core.Text.UiText.SaveCorrupt);
        }
    }

    /// <summary>Every slot the load screen lists: autosave, quick, manual.</summary>
    public static IReadOnlyList<SlotInfo> All() =>
        new[] { GameRuntime.AutosaveSlot, Quick }.Concat(Manual).Select(Inspect).ToList();

    /// <summary>The newest valid save (Continue), or null.</summary>
    public static SlotInfo? Newest() => All().Where(s => s.Valid).OrderByDescending(s => s.ModifiedUnix).FirstOrDefault();

    /// <summary>True when any readable save exists.</summary>
    public static bool AnyValid() => All().Any(s => s.Valid);

    /// <summary>Display title of a slot.</summary>
    public static string Title(string slot)
    {
        if (slot == GameRuntime.AutosaveSlot) return TextService.Ui("ui.save.autosave", ("n", "")).Trim();
        if (slot == Quick) return TextService.Ui("ui.save.quick");
        int n = Array.IndexOf(Manual, slot) + 1;
        return TextService.Ui("ui.save.slot", ("n", n.ToString()));
    }

    /// <summary>The slot number for "... na pozícii {n}" texts (manual slots), else the slot title.</summary>
    public static string Number(string slot)
    {
        int n = Array.IndexOf(Manual, slot) + 1;
        return n > 0 ? n.ToString() : Title(slot);
    }

    /// <summary>"place · year" of a state.</summary>
    public static string Summary(GameState state)
    {
        var content = GameRuntime.Instance.Content;
        var room = content.FindRoom(state.Room);
        string place = room is null ? state.Room : TextService.Get(TextKeys.NameOf(room));
        return TextService.Ui("ui.save.slot_summary", ("place", place), ("year", TextService.EraYear(state.Era)));
    }

    /// <summary>Local date/time text of a unix time.</summary>
    public static string LocalTime(ulong unix)
    {
        var tz = Time.GetTimeZoneFromSystem();
        long bias = tz.TryGetValue("bias", out var b) ? (long)b : 0;
        var dict = Time.GetDatetimeDictFromUnixTime((long)unix + bias * 60);
        return $"{(int)dict["day"]}. {(int)dict["month"]}. {(int)dict["year"]}  {(int)dict["hour"]:00}:{(int)dict["minute"]:00}";
    }

    /// <summary>The thumbnail texture of a slot, or null.</summary>
    public static Texture2D? Thumbnail(string slot)
    {
        string path = $"{GameRuntime.SaveDirectory}/{slot}.png";
        if (!Godot.FileAccess.FileExists(path)) return null;
        var image = Image.LoadFromFile(path);
        return image is null || image.IsEmpty() ? null : ImageTexture.CreateFromImage(image);
    }
}
