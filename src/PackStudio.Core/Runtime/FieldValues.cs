using System.Globalization;
using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class FieldValues
{
    public static JToken Parse(JToken field, string text)
    {
        if (string.IsNullOrWhiteSpace(text)) return JValue.CreateNull();
        string control = field["control"].Text();
        if (control is "number" or "integer" or "integer_spinbox" && double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out double n) && double.IsFinite(n))
            return control.StartsWith("integer") && n == Math.Truncate(n) && n >= long.MinValue && n < 9223372036854775808d ? new JValue((long)n) : new JValue(n);
        return new JValue(text);
    }

    public static string? Error(JToken field, JToken? value)
    {
        if (value?.Type is null or JTokenType.Null) return null;
        string control = field["control"].Text(), label = field["label"].Text();
        if (control is "number" or "integer" or "integer_spinbox")
        {
            if (value.Type is not (JTokenType.Integer or JTokenType.Float)) return $"{label} 必须是数字。";
            double n = value.Number();
            if (!double.IsFinite(n) || control.StartsWith("integer") && n != Math.Truncate(n) ||
                n < (field["minimum"]?.Type is JTokenType.Integer or JTokenType.Float ? field["minimum"]!.Number() : 0) ||
                field["maximum"]?.Type is JTokenType.Integer or JTokenType.Float && n > field["maximum"]!.Number()) return $"{label} 超出允许范围。";
        }
        if (control == "checkbox" && value.Type != JTokenType.Boolean) return $"{label} 必须是布尔值。";
        if (field["options"] is JArray { Count: > 0 } options && !options.Any(o => JToken.DeepEquals(o, value))) return $"{label} 选项无效。";
        return null;
    }
}
