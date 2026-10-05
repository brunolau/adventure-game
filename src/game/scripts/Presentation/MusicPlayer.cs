using Godot;
using LastBell.Game.Runtime;

namespace LastBell.Game.Presentation;

/// <summary>
/// Plays <c>rooms[].music</c> (res://assets/music/...) when the file exists; silent otherwise.
/// Keeps playing across rooms that share the same track. Uses the "Music" audio bus when present.
/// </summary>
public partial class MusicPlayer : AudioStreamPlayer
{
    private string currentPath = "";

    /// <inheritdoc />
    public override void _Ready()
    {
        if (AudioServer.GetBusIndex("Music") >= 0) Bus = "Music";
        var game = GameRuntime.Instance;
        game.RoomChanged += (_, _) => Sync();
        game.SessionReplaced += Sync;
    }

    private void Sync()
    {
        var game = GameRuntime.Instance;
        var room = game.Content.FindRoom(game.State.Room);
        string path = room is null || string.IsNullOrEmpty(room.Music) ? "" : "res://assets/" + room.Music;
        if (path == currentPath) return;
        currentPath = path;
        if (path.Length > 0 && ResourceLoader.Exists(path) && GD.Load<AudioStream>(path) is { } stream)
        {
            Stream = stream;
            Play();
        }
        else Stop();
    }
}
