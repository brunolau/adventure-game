using System;
using System.Globalization;
using Godot;

namespace LastBell.Game.Runtime;

/// <summary>
/// Touch presentation of the phone and tablet ports (docs/PORTS.md "Touch controls"): presentation only, Core never
/// knows. On when the build runs on a mobile OS (feature tag <c>mobile</c>: Android, iOS); a desktop build never
/// turns it on by itself, so the PC controls stay exactly as they are (a touch screen on a PC keeps the old gestures:
/// tap = left click, long press = right click). QA on the desktop: the harness flag <c>--touch</c> emulates a 6.3 inch
/// phone (<c>--touch-mm &lt;mm per canvas px&gt;</c> another screen, e.g. 0.118 for a 10.5 inch tablet) and
/// <c>--safe-area l,t,r,b</c> (canvas px) a display cutout; touch events come from <c>--input tap:x,y</c> etc.
/// <para>
/// What changes in touch mode: the hover label shows at the finger while it is down and stays for a moment after the
/// tap (<see cref="LastBell.Game.PlayerInput.InputRouter"/>, <c>UI/Hud/HoverLabel</c>); the HUD has finger-sized buttons
/// with captions and an eye that latches (<c>UI/Hud/HudView</c>); first-start tips and the help list the touch
/// gestures; a first start picks the HUD scale and the subtitle size from the physical screen size
/// (<see cref="DeviceDefaults"/>); the UI keeps inside the display's safe area (<see cref="SafeInsets"/>); the system
/// Back button is Esc and the game saves and pauses when the app goes to the background (<c>UI/Common/MobileLifecycle</c>).
/// </para>
/// </summary>
public static class TouchMode
{
    /// <summary>Canvas size the game is laid out for.</summary>
    public static readonly Vector2 Canvas = new(1920, 1080);

    /// <summary>Size of a HUD button in touch mode in logical px (before the HUD scale).</summary>
    public const float HudButton = 74f;

    /// <summary>Smallest comfortable touch target (Android: 48 dp = 7.6 mm; this game asks for about 9 mm on the HUD).</summary>
    public const float TargetMm = 9f;

    /// <summary>Smallest subtitle text height that reads well at arm's length (about 16 sp).</summary>
    public const float SubtitleMm = 2.6f;

    /// <summary>mm per canvas px of the QA phone preset: 6.3 inch, 20:9, 1080 px high (a Pixel 7).</summary>
    public const float QaPhoneMmPerPx = 0.0608f;

    private static bool? enabled;
    private static float? qaMm;
    private static Vector4? qaSafe;
    private static bool qaRead;

    /// <summary>True on phones and tablets (and in a QA run with <c>--touch</c>).</summary>
    public static bool Enabled => enabled ??= IsMobile || QaFlag("--touch") || QaValue("--touch-mm") is not null;

    /// <summary>True when the build runs on Android or iOS.</summary>
    public static bool IsMobile { get; } = OS.HasFeature("mobile");

    private static bool QaFlag(string flag) => Array.IndexOf(LaunchArgs.User, flag) >= 0;

    private static string? QaValue(string flag)
    {
        var user = LaunchArgs.User;
        string prefix = flag + "=";
        for (int i = 0; i < user.Length; i++)
        {
            if (user[i] == flag && i + 1 < user.Length) return user[i + 1];
            if (user[i].StartsWith(prefix, StringComparison.Ordinal)) return user[i][prefix.Length..];
        }
        return null;
    }

    private static void ReadQa()
    {
        if (qaRead) return;
        qaRead = true;
        if (QaValue("--touch-mm") is { } mm && float.TryParse(mm, NumberStyles.Float, CultureInfo.InvariantCulture, out float value) && value > 0)
            qaMm = value;
        else if (QaFlag("--touch")) qaMm = QaPhoneMmPerPx;
        if (QaValue("--safe-area") is { } area)
        {
            var parts = area.Split(',');
            if (parts.Length == 4 && float.TryParse(parts[0], NumberStyles.Float, CultureInfo.InvariantCulture, out float l)
                && float.TryParse(parts[1], NumberStyles.Float, CultureInfo.InvariantCulture, out float t)
                && float.TryParse(parts[2], NumberStyles.Float, CultureInfo.InvariantCulture, out float r)
                && float.TryParse(parts[3], NumberStyles.Float, CultureInfo.InvariantCulture, out float b))
                qaSafe = new Vector4(l, t, r, b);
        }
    }

    /// <summary>Window px per canvas px of the letterboxed 16:9 canvas (stretch aspect "keep").</summary>
    public static float WindowScale(Vector2 window) => Mathf.Max(0.01f, Mathf.Min(window.X / Canvas.X, window.Y / Canvas.Y));

    /// <summary>
    /// Physical size of one canvas px on this screen in mm (the 1920x1080 canvas letterboxed into the window, the
    /// screen's dpi), or 0 when the screen does not tell.
    /// </summary>
    public static float MmPerCanvasPx()
    {
        ReadQa();
        if (qaMm is { } qa) return qa;
        if (!IsMobile || DisplayServer.GetName() == "headless") return 0f;
        int dpi = DisplayServer.ScreenGetDpi();
        var window = DisplayServer.WindowGetSize();
        if (dpi <= 0 || window.X <= 0 || window.Y <= 0) return 0f;
        return WindowScale(window) * 25.4f / dpi;
    }

    /// <summary>A length in mm as canvas px on this screen (<paramref name="fallbackPx"/> when the size is unknown).</summary>
    public static float MmToCanvasPx(float mm, float fallbackPx)
    {
        float per = MmPerCanvasPx();
        return per > 0 ? mm / per : fallbackPx;
    }

    /// <summary>
    /// HUD scale (percent, one of the settings' steps 100-200) and subtitle size (logical px, 34-48) that make the HUD
    /// buttons about <see cref="TargetMm"/> and the subtitles about <see cref="SubtitleMm"/> on a screen where one canvas
    /// px is <paramref name="mmPerCanvasPx"/> mm. A 6.3 inch phone gets 200 % and 42 px, a 10.5 inch tablet 100 % and 34 px.
    /// </summary>
    public static (int HudScalePercent, int SubtitleSize) DeviceDefaults(float mmPerCanvasPx)
    {
        if (mmPerCanvasPx <= 0) return (100, 34);
        float wanted = TargetMm / (HudButton * mmPerCanvasPx);
        // The next settings step (25 %) that reaches the target; 4 % short still counts as reached.
        int hud = (int)Math.Clamp(Math.Ceiling((wanted - 0.04f) * 4) * 25, 100, 200);
        int subtitle = (int)Math.Clamp(Math.Round(SubtitleMm / mmPerCanvasPx / 2) * 2, 34, 48);
        return (hud, subtitle);
    }

    /// <summary>
    /// Insets (canvas px: X left, Y top, Z right, W bottom) of the display's safe area inside the letterboxed canvas:
    /// what a notch, a camera hole or rounded corners take away from the 16:9 picture. Zero on most phones in
    /// landscape, because the black bars beside the picture are wider than the cutout; not zero on 16:9 screens with
    /// a cutout. Zero on the desktop.
    /// </summary>
    public static Vector4 SafeInsets()
    {
        ReadQa();
        if (qaSafe is { } qa) return qa;
        if (!IsMobile || DisplayServer.GetName() == "headless") return Vector4.Zero;
        var window = (Vector2)DisplayServer.WindowGetSize();
        Rect2 safe = DisplayServer.GetDisplaySafeArea();
        if (window.X <= 0 || window.Y <= 0 || safe.Size.X <= 0 || safe.Size.Y <= 0) return Vector4.Zero;
        return SafeInsets(window, safe);
    }

    /// <summary>The insets for a window size and a safe rect, both in window px (pure, see <see cref="SafeInsets()"/>).</summary>
    public static Vector4 SafeInsets(Vector2 window, Rect2 safe)
    {
        float s = WindowScale(window);
        var origin = (window - Canvas * s) / 2;
        float left = Mathf.Max(0, (safe.Position.X - origin.X) / s);
        float top = Mathf.Max(0, (safe.Position.Y - origin.Y) / s);
        float right = Mathf.Max(0, (origin.X + Canvas.X * s - safe.End.X) / s);
        float bottom = Mathf.Max(0, (origin.Y + Canvas.Y * s - safe.End.Y) / s);
        // A broken report must never squeeze the UI away: at most an eighth of the picture per side.
        return new Vector4(Mathf.Min(left, Canvas.X / 8), Mathf.Min(top, Canvas.Y / 8), Mathf.Min(right, Canvas.X / 8), Mathf.Min(bottom, Canvas.Y / 8));
    }

    /// <summary>
    /// A touch-only UI text: the ui.csv row when it exists (the rows of docs/writing/out_v6/ui_touch.csv are in the
    /// table since 2026-10-10), else the fallback of the current language from code.
    /// </summary>
    public static string Text(string key, string slovak, string english) =>
        TextService.UiOr(key, TextService.Locale.StartsWith("en", StringComparison.Ordinal) ? english : slovak);
}
