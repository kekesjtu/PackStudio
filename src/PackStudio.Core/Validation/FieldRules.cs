namespace PackStudio.Core;

public static class FieldRules
{
    public static bool NonNegative(double value) => double.IsFinite(value) && value >= 0;

    public static IEnumerable<string> MaterialErrors(Material material)
    {
        if (material.ConductType is < 0 or > 2) yield return "导热类型必须为 0、1 或 2。";
        var conductivity = material.ConductType == 2 ? material.Conductivity.Components : [material.Conductivity.X];
        if (conductivity.Any(v => !NonNegative(v))) yield return "生效导热率必须为有限非负数。";
        if (!NonNegative(material.Density)) yield return "密度必须为有限非负数。";
        if (!NonNegative(material.SpecificHeat)) yield return "比热必须为有限非负数。";
        if (material.ConductType == 1)
        {
            if (material.ConductivityCoefficient is not double coefficient || !double.IsFinite(coefficient))
                yield return "温度系数必须为有限数值。";
            if (material.ReferenceTemperature is not double temperature || !double.IsFinite(temperature))
                yield return "参考温度必须为有限数值。";
        }
    }
}
