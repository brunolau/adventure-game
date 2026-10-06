namespace LastBell.Core.Tests.Support;

/// <summary>Minimal reader of a Godot translation CSV (header "keys,sk,en", RFC 4180 quoting).</summary>
public static class CsvTable
{
    /// <summary>Key to sk text of a table fixture (e.g. "dialogue.csv").</summary>
    public static Dictionary<string, string> Read(string fixtureName)
    {
        var result = new Dictionary<string, string>(StringComparer.Ordinal);
        var text = File.ReadAllText(TestData.FixturePath(fixtureName));
        var row = new List<string>();
        var field = new System.Text.StringBuilder();
        bool quoted = false, header = true;
        void EndRow()
        {
            row.Add(field.ToString());
            field.Clear();
            if (!header && row.Count >= 2 && row[0].Length > 0) result[row[0]] = row[1];
            header = false;
            row.Clear();
        }
        for (var i = 0; i < text.Length; i++)
        {
            var c = text[i];
            if (quoted)
            {
                if (c == '"' && i + 1 < text.Length && text[i + 1] == '"') { field.Append('"'); i++; }
                else if (c == '"') quoted = false;
                else field.Append(c);
            }
            else if (c == '"') quoted = true;
            else if (c == ',') { row.Add(field.ToString()); field.Clear(); }
            else if (c == '\n') EndRow();
            else if (c != '\r') field.Append(c);
        }
        if (field.Length > 0 || row.Count > 0) EndRow();
        return result;
    }
}
