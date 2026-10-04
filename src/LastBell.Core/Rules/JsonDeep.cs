using System.Text.Json;
using System.Text.Json.Nodes;

namespace LastBell.Core.Rules;

/// <summary>Deep structural equality of JSON values (port of <c>deepEqual</c> in runtime_contract.ts).</summary>
public static class JsonDeep
{
    /// <summary>
    /// True when both values are structurally equal: same kind, numbers equal by value
    /// (3 equals 3.0), strings by ordinal comparison, arrays element-wise, objects by key set and values.
    /// A missing value (null reference) equals only JSON null.
    /// </summary>
    public static bool Equals(JsonNode? a, JsonNode? b)
    {
        if (a is null || b is null) return IsNull(a) && IsNull(b);
        switch (a)
        {
            case JsonArray aa:
                if (b is not JsonArray ba || aa.Count != ba.Count) return false;
                for (var i = 0; i < aa.Count; i++)
                    if (!Equals(aa[i], ba[i])) return false;
                return true;
            case JsonObject ao:
                if (b is not JsonObject bo || ao.Count != bo.Count) return false;
                foreach (var (key, value) in ao)
                {
                    if (!bo.TryGetPropertyValue(key, out var other) || !Equals(value, other)) return false;
                }
                return true;
            case JsonValue av:
                if (b is not JsonValue bv) return false;
                return ValueEquals(av, bv);
            default:
                return false;
        }
    }

    /// <summary>Canonical compact JSON text of a value ("null" for a missing value).</summary>
    public static string ToCanonicalText(JsonNode? node) => node is null ? "null" : node.ToJsonString();

    /// <summary>Parses JSON text into a node (null for JSON null).</summary>
    public static JsonNode? Parse(string json) => JsonNode.Parse(json);

    // Works for element-backed and CLR-backed values alike (avoids GetValue<T> type restrictions).
    private static decimal? NumberOf(JsonValue value) =>
        decimal.TryParse(value.ToJsonString(), System.Globalization.NumberStyles.Float,
            System.Globalization.CultureInfo.InvariantCulture, out var d) ? d : null;

    private static bool IsNull(JsonNode? node) => node is null || (node is JsonValue v && v.GetValueKind() == JsonValueKind.Null);

    private static bool ValueEquals(JsonValue a, JsonValue b)
    {
        var ka = a.GetValueKind();
        var kb = b.GetValueKind();
        if (ka != kb) return false;
        return ka switch
        {
            JsonValueKind.Number => NumberOf(a) == NumberOf(b),
            JsonValueKind.String => string.Equals(a.GetValue<string>(), b.GetValue<string>(), StringComparison.Ordinal),
            JsonValueKind.True or JsonValueKind.False or JsonValueKind.Null => true,
            _ => a.ToJsonString() == b.ToJsonString(),
        };
    }
}
