using System.Globalization;
using Newtonsoft.Json.Linq;

using PackStudio.Core;

namespace PackStudio.Desktop;

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

}
