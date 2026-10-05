using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Godot;
using LastBell.Core.Content;
using LastBell.Game.Runtime;
using LastBell.Game.UI.Settings;
using LastBell.Game.UI.Theme;

namespace LastBell.Game.UI.Puzzles;

/// <summary>
/// Base of a puzzle control: edits a JSON draft in the exact answer shape Core expects
/// (LastBell.Core.Rules.PuzzleAnswers) and raises <see cref="Changed"/> after every edit so the
/// modal can store the draft through Core. No timers, no drag precision (AT08): every control is
/// discrete buttons, keyboard focusable.
/// </summary>
public abstract partial class PuzzleControl : VBoxContainer
{
    /// <summary>The puzzle.</summary>
    protected PuzzleDef Puzzle { get; private set; } = null!;

    /// <summary>Raised after the player changed the draft.</summary>
    public event Action? Changed;

    /// <summary>Initialises the control for a puzzle.</summary>
    public void Init(PuzzleDef puzzle)
    {
        Puzzle = puzzle;
        AddThemeConstantOverride("separation", 14);
        Build();
    }

    /// <summary>Builds the widgets.</summary>
    protected abstract void Build();

    /// <summary>Shows a draft (from Core).</summary>
    public abstract void SetDraft(JsonNode? draft);

    /// <summary>The current draft in Core's answer shape.</summary>
    public abstract JsonNode? Draft { get; }

    /// <summary>Adapts the control to the available area (large HUD scale, small windows).</summary>
    public virtual void FitTo(Vector2 available) { }

    /// <summary>Notifies a change.</summary>
    protected void RaiseChanged() => Changed?.Invoke();

    /// <summary>Translated label of an option (puzzle.&lt;id&gt;.left|right.&lt;n&gt;), falling back to the data value.</summary>
    protected string OptionLabel(string side, int index, string value) => TextService.Get($"puzzle.{Puzzle.Id}.{side}.{index + 1}", value);

    /// <summary>Creates the right control for a puzzle's controls.type.</summary>
    public static PuzzleControl Create(PuzzleDef puzzle)
    {
        PuzzleControl control = puzzle.Controls.Type switch
        {
            "matching" => new MatchingControl(),
            "rotate_overlay" => new RotateOverlayControl(),
            "digits" => new DigitsControl(),
            "grid_choice" => new GridChoiceControl(),
            _ => throw new InvalidOperationException($"Unknown puzzle control type '{puzzle.Controls.Type}' ({puzzle.Id})"),
        };
        control.Init(puzzle);
        return control;
    }
}

// ---------------------------------------------------------------------- matching (P01, P04)

/// <summary>
/// matching: pick a slot on the left, then the value on the right that belongs to it (one value per
/// slot; a value moves if it was used elsewhere). Lines show the pairs. Optional shape pictures for
/// the options come from res://assets/ui/puzzle_glyphs.json (presentation only).
/// </summary>
public partial class MatchingControl : PuzzleControl
{
    private readonly List<Button> leftButtons = new();
    private readonly List<Button> rightButtons = new();
    private string?[] values = Array.Empty<string?>();
    private int selected;
    private Dictionary<string, string> glyphs = new(StringComparer.Ordinal);

    /// <inheritdoc />
    protected override void Build()
    {
        glyphs = PuzzleGlyphs.For(Puzzle.Id);
        var left = Puzzle.Controls.Left ?? Array.Empty<string>();
        var right = Puzzle.Controls.Right ?? Array.Empty<string>();
        values = new string?[left.Count];
        AddChild(Ui.Para(Ui.T("ui.puzzle.match_instruction"), "CaptionLabel"));
        var row = Ui.HBox(0);
        row.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var leftCol = Ui.VBox(14);
        leftCol.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var rightCol = Ui.VBox(14);
        rightCol.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        for (int i = 0; i < left.Count; i++)
        {
            int index = i;
            var b = Ui.Button("", () => SelectLeft(index));
            b.ToggleMode = true;
            b.Alignment = HorizontalAlignment.Left;
            b.CustomMinimumSize = new Vector2(300, 84);
            b.ThemeTypeVariation = "TabButton";
            AttachGlyph(b, left[i], false, i);
            leftButtons.Add(b);
            leftCol.AddChild(b);
        }
        for (int j = 0; j < right.Count; j++)
        {
            int index = j;
            var b = Ui.Button(OptionLabel("right", j, right[j]), () => Assign(index));
            b.Alignment = HorizontalAlignment.Left;
            b.CustomMinimumSize = new Vector2(260, 84);
            AttachGlyph(b, right[j], true, j);
            rightButtons.Add(b);
            rightCol.AddChild(b);
        }
        row.AddChild(leftCol);
        var gap = new Control { CustomMinimumSize = new Vector2(140, 0), MouseFilter = MouseFilterEnum.Ignore };
        row.AddChild(gap);
        row.AddChild(rightCol);
        AddChild(row);
        var clear = Ui.Button(Ui.T("ui.puzzle.match_clear"), () =>
        {
            if (selected < 0 || selected >= values.Length) return;
            values[selected] = null;
            Refresh();
            RaiseChanged();
        }, "FlatButton");
        clear.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
        AddChild(clear);
    }

    private void AttachGlyph(Button button, string value, bool rightSide, int index)
    {
        if (!glyphs.TryGetValue(value, out var shape)) return;
        // Colours vary on purpose on the right side ("colours do not matter"); shapes carry the meaning.
        Color[] palette = { new("2f6f9f"), new("a5432b"), new("4f7a3a"), new("8a5a9e") };
        var glyph = new ShapeGlyph(shape, rightSide ? palette[index % palette.Length] : UiTheme.Ink) { CustomMinimumSize = new Vector2(56, 56), MouseFilter = MouseFilterEnum.Ignore };
        glyph.SetAnchorsAndOffsetsPreset(LayoutPreset.CenterRight);
        glyph.Position = new Vector2(0, 0);
        button.AddChild(glyph);
        button.Resized += () => glyph.Position = new Vector2(button.Size.X - 70, (button.Size.Y - 56) / 2);
    }

    private void SelectLeft(int index)
    {
        selected = index;
        Refresh();
    }

    private void Assign(int rightIndex)
    {
        var right = Puzzle.Controls.Right ?? Array.Empty<string>();
        if (rightIndex < 0 || rightIndex >= right.Count) return;
        if (selected < 0 || selected >= values.Length) selected = Array.FindIndex(values, v => v is null);
        if (selected < 0) selected = 0;
        string value = right[rightIndex];
        for (int i = 0; i < values.Length; i++) if (values[i] == value) values[i] = null;
        values[selected] = value;
        // Move on to the next empty slot (keyboard friendly).
        int next = Array.FindIndex(values, v => v is null);
        if (next >= 0) selected = next;
        Refresh();
        RaiseChanged();
        leftButtons[Math.Clamp(selected, 0, leftButtons.Count - 1)].GrabFocus();
    }

    private void Refresh()
    {
        var left = Puzzle.Controls.Left ?? Array.Empty<string>();
        var right = Puzzle.Controls.Right ?? Array.Empty<string>();
        for (int i = 0; i < leftButtons.Count; i++)
        {
            string assigned = values[i] is { } v ? OptionLabel("right", right.ToList().IndexOf(v), v) : "?";
            leftButtons[i].Text = OptionLabel("left", i, left[i]) + "   →   " + assigned;
            leftButtons[i].SetPressedNoSignal(i == selected);
        }
        for (int j = 0; j < rightButtons.Count; j++)
        {
            bool used = values.Contains(right[j]);
            rightButtons[j].Modulate = used ? new Color(1, 1, 1, 0.7f) : Colors.White;
        }
        QueueRedraw();
    }

    /// <inheritdoc />
    public override void SetDraft(JsonNode? draft)
    {
        var left = Puzzle.Controls.Left ?? Array.Empty<string>();
        values = new string?[left.Count];
        if (draft is JsonArray array)
            for (int i = 0; i < Math.Min(array.Count, values.Length); i++)
                values[i] = array[i] is JsonValue v && v.TryGetValue<string>(out var s) ? s : null;
        selected = Math.Max(0, Array.FindIndex(values, v => v is null));
        Refresh();
    }

    /// <inheritdoc />
    public override JsonNode? Draft => LastBell.Core.Rules.PuzzleAnswers.Matching(values);

    /// <inheritdoc />
    public override void _Draw()
    {
        var right = Puzzle?.Controls.Right ?? Array.Empty<string>();
        for (int i = 0; i < leftButtons.Count && i < values.Length; i++)
        {
            if (values[i] is not { } v) continue;
            int j = right.ToList().IndexOf(v);
            if (j < 0 || j >= rightButtons.Count) continue;
            var a = leftButtons[i].GetGlobalRect();
            var b = rightButtons[j].GetGlobalRect();
            var inv = GetGlobalTransform().AffineInverse();
            var pa = inv * new Vector2(a.End.X, a.GetCenter().Y);
            var pb = inv * new Vector2(b.Position.X, b.GetCenter().Y);
            DrawLine(pa, pb, new Color(UiTheme.Accent, 0.85f), 5, true);
            DrawCircle(pa, 8, UiTheme.Accent);
            DrawCircle(pb, 8, UiTheme.Accent);
        }
    }

    /// <inheritdoc />
    public override void _Process(double delta) => QueueRedraw();
}

/// <summary>Draws a simple shape (circle, triangle, square, star) for puzzle options.</summary>
public partial class ShapeGlyph : Control
{
    private readonly string shape = "";
    private readonly Color color;

    /// <summary>Godot constructor.</summary>
    public ShapeGlyph() { }

    /// <summary>Creates the glyph.</summary>
    public ShapeGlyph(string shape, Color color)
    {
        this.shape = shape;
        this.color = color;
    }

    /// <inheritdoc />
    public override void _Draw()
    {
        float s = Math.Min(Size.X, Size.Y);
        var c = Size / 2;
        float r = s * 0.4f;
        switch (shape)
        {
            case "circle":
                DrawCircle(c, r, color);
                break;
            case "triangle":
                DrawColoredPolygon(new[] { c + new Vector2(0, -r), c + new Vector2(r * 0.95f, r * 0.75f), c + new Vector2(-r * 0.95f, r * 0.75f) }, color);
                break;
            case "square":
                DrawRect(new Rect2(c - new Vector2(r * 0.85f, r * 0.85f), new Vector2(r * 1.7f, r * 1.7f)), color);
                break;
            default:
                DrawCircle(c, r * 0.4f, color);
                break;
        }
    }
}

/// <summary>Optional presentation data for puzzle options (res://assets/ui/puzzle_glyphs.json: { "P01": { "kruh": "circle" } }).</summary>
public static class PuzzleGlyphs
{
    private static JsonNode? data;

    /// <summary>The value → shape map of a puzzle (empty when none).</summary>
    public static Dictionary<string, string> For(string puzzleId)
    {
        const string path = "res://assets/ui/puzzle_glyphs.json";
        if (data is null && Godot.FileAccess.FileExists(path))
        {
            try { data = JsonNode.Parse(Godot.FileAccess.GetFileAsString(path)); } catch (Exception) { data = new JsonObject(); }
        }
        var map = new Dictionary<string, string>(StringComparer.Ordinal);
        if (data?[puzzleId] is JsonObject obj)
            foreach (var (k, v) in obj) if (v is JsonValue jv && jv.TryGetValue<string>(out var s)) map[k] = s;
        return map;
    }
}

// ---------------------------------------------------------------------- rotate overlay (P02)

/// <summary>
/// rotate_overlay: the base sheet with three registration marks (hole, double cross, square) and the
/// transparent foil with the same marks, rotated in the data's discrete steps (buttons, no drag).
/// The marks are large, distinguished by shape (not colour) and stay readable at 200 % HUD scale.
/// </summary>
public partial class RotateOverlayControl : PuzzleControl
{
    private int orientation;
    private float shownAngle;
    private Label value = null!;
    private OverlayCanvas canvas = null!;
    private int[] steps = { 0, 90, 180, 270 };

    /// <inheritdoc />
    protected override void Build()
    {
        steps = (Puzzle.Controls.Orientations ?? new[] { 0, 90, 180, 270 }).ToArray();
        canvas = new OverlayCanvas(this) { CustomMinimumSize = new Vector2(520, 520), SizeFlagsHorizontal = SizeFlags.ShrinkCenter };
        AddChild(canvas);
        var row = Ui.HBox(16);
        row.Alignment = AlignmentMode.Center;
        var left = Ui.GlyphButton(GlyphKind.RotateLeft, Ui.T("ui.puzzle.rotate_left"), () => Rotate(-1), "", 80);
        left.FocusMode = FocusModeEnum.All;
        var right = Ui.GlyphButton(GlyphKind.RotateRight, Ui.T("ui.puzzle.rotate_right"), () => Rotate(+1), "", 80);
        right.FocusMode = FocusModeEnum.All;
        value = Ui.Label("", "HeadingLabel");
        value.CustomMinimumSize = new Vector2(140, 0);
        value.HorizontalAlignment = HorizontalAlignment.Center;
        value.VerticalAlignment = VerticalAlignment.Center;
        row.AddChild(left);
        row.AddChild(value);
        row.AddChild(right);
        AddChild(row);
        var hint = Ui.Label(Ui.T("ui.puzzle.rotate_left") + " / " + Ui.T("ui.puzzle.rotate_right"), "CaptionLabel");
        hint.HorizontalAlignment = HorizontalAlignment.Center;
        AddChild(hint);
    }

    private void Rotate(int direction)
    {
        int i = Array.IndexOf(steps, orientation);
        if (i < 0) i = 0;
        orientation = steps[(i + direction + steps.Length) % steps.Length];
        UpdateValue();
        if (UiSettings.ReducedMotion) shownAngle = orientation;
        else
        {
            // Animate the short way round.
            float target = orientation;
            float delta = Mathf.Wrap(target - shownAngle, -180, 180);
            if (Math.Abs(Math.Abs(delta) - 180) < 0.1f) delta = 180 * direction;
            var tween = CreateTween();
            tween.TweenMethod(Callable.From<float>(a => { shownAngle = a; canvas.QueueRedraw(); }), shownAngle, shownAngle + delta, 0.25f);
        }
        canvas.QueueRedraw();
        RaiseChanged();
    }

    private void UpdateValue() => value.Text = Ui.T("ui.puzzle.rotation_value", ("degrees", orientation.ToString()));

    /// <inheritdoc />
    public override void SetDraft(JsonNode? draft)
    {
        orientation = draft is JsonValue v && v.TryGetValue<int>(out var d) ? d : steps[0];
        shownAngle = orientation;
        UpdateValue();
        canvas.QueueRedraw();
    }

    /// <inheritdoc />
    public override JsonNode? Draft => LastBell.Core.Rules.PuzzleAnswers.Rotation(orientation);

    /// <inheritdoc />
    public override void FitTo(Vector2 available)
    {
        float side = Math.Clamp(Math.Min(available.X, available.Y - 140), 170, 520);
        if (Math.Abs(canvas.CustomMinimumSize.X - side) > 1) canvas.CustomMinimumSize = new Vector2(side, side);
    }

    /// <summary>The angle currently drawn (animated).</summary>
    public float ShownAngle => shownAngle;

}

/// <summary>Draws the P02 base sheet and the rotated foil.</summary>
public partial class OverlayCanvas : Control
{
    private readonly RotateOverlayControl? owner;

    public OverlayCanvas() { }

    public OverlayCanvas(RotateOverlayControl owner)
    {
        this.owner = owner;
        MouseFilter = MouseFilterEnum.Ignore;
    }

    // Mark positions on the base sheet (normalised, centre = 0).
    private static readonly Vector2[] Marks = { new(-0.55f, -0.45f), new(0.5f, -0.3f), new(0.12f, 0.55f) };

    public override void _Draw()
    {
        if (owner is null) return;
        float s = Math.Min(Size.X, Size.Y);
        var c = Size / 2;
        float half = s * 0.46f;
        Vector2 P(Vector2 n) => c + n * half;
        // Base sheet: paper with streets.
        DrawRect(new Rect2(c - new Vector2(half, half), new Vector2(half * 2, half * 2)), new Color("f3e6c8"));
        DrawRect(new Rect2(c - new Vector2(half, half), new Vector2(half * 2, half * 2)), UiTheme.PaperEdge, false, 3);
        var street = new Color(UiTheme.InkSoft, 0.35f);
        DrawPolyline(new[] { P(new(-1, -0.1f)), P(new(-0.3f, 0)), P(new(0.2f, 0.2f)), P(new(1, 0.1f)) }, street, 10, true);
        DrawPolyline(new[] { P(new(-0.2f, -1)), P(new(-0.25f, -0.2f)), P(new(-0.1f, 1)) }, street, 8, true);
        DrawPolyline(new[] { P(new(0.35f, -1)), P(new(0.45f, 1)) }, street, 6, true);
        foreach (var (m, i) in Marks.Select((m, i) => (m, i))) DrawMark(i, P(m), s * 0.09f, UiTheme.Ink, filled: true);

        // Foil: the same marks at the 180° positions, rotated by the current orientation.
        float a = Mathf.DegToRad(owner.ShownAngle);
        Vector2 F(Vector2 n) => c + (-n * half).Rotated(a);
        float fh = half * 0.98f;
        var corners = new[] { new Vector2(-1, -1), new Vector2(1, -1), new Vector2(1, 1), new Vector2(-1, 1) }
            .Select(v => c + (v * fh).Rotated(a)).ToArray();
        DrawColoredPolygon(corners, new Color("bfe0e6", 0.35f));
        DrawPolyline(corners.Append(corners[0]).ToArray(), new Color("1f7f7a", 0.9f), 3, true);
        // A tab marks the foil's top edge so the orientation is readable without colour.
        var tab = new[] { new Vector2(-0.15f, -1), new Vector2(0.15f, -1), new Vector2(0.1f, -1.08f), new Vector2(-0.1f, -1.08f) }
            .Select(v => c + (v * fh).Rotated(a)).ToArray();
        DrawColoredPolygon(tab, new Color("1f7f7a", 0.9f));
        var route = new Color("a5432b", 0.75f);
        DrawPolyline(new[] { F(new(-0.55f, -0.45f)), F(new(-0.1f, -0.38f)), F(new(0.5f, -0.3f)) }, route, 5, true);
        DrawPolyline(new[] { F(new(0.5f, -0.3f)), F(new(0.3f, 0.2f)), F(new(0.12f, 0.55f)) }, route, 5, true);
        foreach (var (m, i) in Marks.Select((m, i) => (m, i))) DrawMark(i, F(m), s * 0.09f, new Color("1f7f7a"), filled: false);
    }

    private void DrawMark(int kind, Vector2 p, float r, Color color, bool filled)
    {
        float w = filled ? 6 : 5;
        switch (kind)
        {
            case 0: // hole
                if (filled) DrawCircle(p, r * 0.75f, color);
                else DrawArc(p, r, 0, Mathf.Tau, 32, color, w, true);
                break;
            case 1: // double cross
                for (int k = -1; k <= 1; k += 2)
                {
                    DrawLine(p + new Vector2(k * r * 0.35f, -r), p + new Vector2(k * r * 0.35f, r), color, w, true);
                    DrawLine(p + new Vector2(-r, k * r * 0.35f), p + new Vector2(r, k * r * 0.35f), color, w, true);
                }
                break;
            default: // square
                var rect = new Rect2(p - new Vector2(r * 0.8f, r * 0.8f), new Vector2(r * 1.6f, r * 1.6f));
                if (filled) DrawRect(rect, color);
                else DrawRect(rect.Grow(r * 0.2f), color, false, w);
                break;
        }
    }
}

// ---------------------------------------------------------------------- digits (P03)

/// <summary>digits: N wheels with up/down buttons over the data range (wrapping), keyboard focusable.</summary>
public partial class DigitsControl : PuzzleControl
{
    private int[] digits = Array.Empty<int>();
    private readonly List<Label> labels = new();
    private int min, max = 9;

    /// <inheritdoc />
    protected override void Build()
    {
        int count = Puzzle.Controls.Digits ?? 3;
        var range = Puzzle.Controls.Range ?? new[] { 0, 9 };
        min = range.Count > 0 ? range[0] : 0;
        max = range.Count > 1 ? range[1] : 9;
        digits = Enumerable.Repeat(min, count).ToArray();
        var row = Ui.HBox(28);
        row.Alignment = AlignmentMode.Center;
        for (int i = 0; i < count; i++)
        {
            int index = i;
            var col = Ui.VBox(8);
            var caption = Ui.Label(Ui.T("ui.puzzle.digit", ("n", (i + 1).ToString())), "CaptionLabel");
            caption.HorizontalAlignment = HorizontalAlignment.Center;
            col.AddChild(caption);
            var up = Ui.GlyphButton(GlyphKind.Up, Ui.T("ui.puzzle.digit_up"), () => Step(index, +1), "", 84);
            up.FocusMode = FocusModeEnum.All;
            col.AddChild(up);
            var frame = new PanelContainer();
            frame.AddThemeStyleboxOverride("panel", UiTheme.Box(new Color("2a1f18"), UiTheme.Brass, 3, 12, 8));
            var label = Ui.Label("0", "TitleLabel");
            label.AddThemeFontSizeOverride("font_size", 96);
            label.AddThemeColorOverride("font_color", UiTheme.BrassLight);
            label.HorizontalAlignment = HorizontalAlignment.Center;
            label.CustomMinimumSize = new Vector2(120, 130);
            label.VerticalAlignment = VerticalAlignment.Center;
            frame.AddChild(label);
            labels.Add(label);
            col.AddChild(frame);
            var down = Ui.GlyphButton(GlyphKind.Down, Ui.T("ui.puzzle.digit_down"), () => Step(index, -1), "", 84);
            down.FocusMode = FocusModeEnum.All;
            col.AddChild(down);
            row.AddChild(col);
        }
        AddChild(row);
    }

    private void Step(int index, int delta)
    {
        int span = max - min + 1;
        digits[index] = min + ((digits[index] - min + delta) % span + span) % span;
        Refresh();
        RaiseChanged();
    }

    private void Refresh()
    {
        for (int i = 0; i < labels.Count; i++) labels[i].Text = digits[i].ToString();
    }

    /// <inheritdoc />
    public override void SetDraft(JsonNode? draft)
    {
        for (int i = 0; i < digits.Length; i++) digits[i] = min;
        if (draft is JsonArray array)
            for (int i = 0; i < Math.Min(array.Count, digits.Length); i++)
                if (array[i] is JsonValue v && v.TryGetValue<int>(out var d)) digits[i] = Math.Clamp(d, min, max);
        Refresh();
    }

    /// <inheritdoc />
    public override JsonNode? Draft => LastBell.Core.Rules.PuzzleAnswers.Digits(digits);
}

// ---------------------------------------------------------------------- grid choice (P05)

/// <summary>
/// grid_choice: a wall of rows × columns stones; one stone is chosen. Rows and columns are numbered
/// from the data's origins (row_origin / column_origin), matching the clue's wording.
/// </summary>
public partial class GridChoiceControl : PuzzleControl
{
    private int rows, columns;
    private (int Row, int Column)? choice;
    private readonly Dictionary<(int, int), Button> cells = new();

    /// <inheritdoc />
    protected override void Build()
    {
        rows = Puzzle.Controls.Rows ?? 3;
        columns = Puzzle.Controls.Columns ?? 4;
        bool fromBottom = Puzzle.Controls.RowOrigin == "bottom";
        bool fromRight = Puzzle.Controls.ColumnOrigin == "right";
        var grid = new GridContainer { Columns = columns + 1, SizeFlagsHorizontal = SizeFlags.ShrinkCenter };
        grid.AddThemeConstantOverride("h_separation", 8);
        grid.AddThemeConstantOverride("v_separation", 8);
        grid.AddChild(new Control { CustomMinimumSize = new Vector2(40, 30) });
        for (int c = 0; c < columns; c++)
        {
            int number = fromRight ? columns - c : c + 1;
            var l = Ui.Label(number.ToString(), "SubheadingLabel");
            l.HorizontalAlignment = HorizontalAlignment.Center;
            grid.AddChild(l);
        }
        for (int r = 0; r < rows; r++)
        {
            int rowNumber = fromBottom ? rows - r : r + 1;
            var rl = Ui.Label(rowNumber.ToString(), "SubheadingLabel");
            rl.VerticalAlignment = VerticalAlignment.Center;
            grid.AddChild(rl);
            for (int c = 0; c < columns; c++)
            {
                int columnNumber = fromRight ? columns - c : c + 1;
                int rr = rowNumber, cc = columnNumber;
                var b = new Button { CustomMinimumSize = new Vector2(150, 96), TooltipText = Ui.T("ui.puzzle.grid_cell", ("row", rr.ToString()), ("column", cc.ToString())) };
                b.Pressed += () => Choose(rr, cc);
                b.MouseEntered += LastBell.Game.PlayerInput.WorldInput.ClearHover;
                cells[(rr, cc)] = b;
                grid.AddChild(b);
            }
        }
        var wall = new PanelContainer { SizeFlagsHorizontal = SizeFlags.ShrinkCenter };
        wall.AddThemeStyleboxOverride("panel", UiTheme.Box(new Color("8c7b68"), new Color("5b4b3b"), 3, 10, 14));
        wall.AddChild(grid);
        AddChild(wall);
        Refresh();
    }

    /// <inheritdoc />
    public override void FitTo(Vector2 available)
    {
        float w = Math.Clamp((available.X - 80) / columns - 8, 70, 150);
        float h = Math.Clamp((available.Y - 80) / rows - 8, 66, 96);
        foreach (var b in cells.Values)
            if (Math.Abs(b.CustomMinimumSize.X - w) > 1 || Math.Abs(b.CustomMinimumSize.Y - h) > 1) b.CustomMinimumSize = new Vector2(w, h);
    }

    private void Choose(int row, int column)
    {
        choice = (row, column);
        Refresh();
        RaiseChanged();
    }

    private void Refresh()
    {
        foreach (var ((r, c), b) in cells)
        {
            bool chosen = choice is { } ch && ch.Row == r && ch.Column == c;
            // Brick-like stones with slight variation (presentation only).
            var stone = new Color("c9b9a3").Darkened(((r * 7 + c * 3) % 5) * 0.035f);
            b.AddThemeStyleboxOverride("normal", UiTheme.Box(chosen ? new Color("e9c46f") : stone, chosen ? UiTheme.Accent : new Color("6e5d4c"), chosen ? 5 : 2, 6, 6));
            b.AddThemeStyleboxOverride("hover", UiTheme.Box(chosen ? new Color("efcf86") : stone.Lightened(0.15f), UiTheme.BrassLight, 4, 6, 6));
            b.AddThemeStyleboxOverride("pressed", UiTheme.Box(new Color("e9c46f"), UiTheme.Accent, 5, 6, 6));
            b.Text = chosen ? Ui.T("ui.puzzle.grid_cell", ("row", r.ToString()), ("column", c.ToString())) : "";
            b.AddThemeFontSizeOverride("font_size", 19);
        }
    }

    /// <inheritdoc />
    public override void SetDraft(JsonNode? draft)
    {
        choice = draft is JsonObject o && o["row"] is JsonValue r && o["column"] is JsonValue c && r.TryGetValue<int>(out var ri) && c.TryGetValue<int>(out var ci)
            ? (ri, ci) : null;
        Refresh();
    }

    /// <inheritdoc />
    public override JsonNode? Draft => choice is { } ch ? LastBell.Core.Rules.PuzzleAnswers.Grid(ch.Row, ch.Column) : null;
}
