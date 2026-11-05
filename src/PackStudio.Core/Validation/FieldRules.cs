namespace PackStudio.Core;

public static class FieldRules
{
    public static bool NonNegative(double value) => double.IsFinite(value) && value >= 0;

    public static IEnumerable<string> MaterialErrors(Material material, ValidationRules rules)
    {
        if (material.ConductType is < 0 or > 2) yield return rules.MaterialMessage("type");
        var conductivity = material.ConductType == 2 ? material.Conductivity.Components : [material.Conductivity.X];
        if (conductivity.Any(v => !NonNegative(v))) yield return rules.MaterialMessage("conductivity");
        if (!NonNegative(material.Density)) yield return rules.MaterialMessage("density");
        if (!NonNegative(material.SpecificHeat)) yield return rules.MaterialMessage("specific_heat");
        if (material.ConductType == 1)
        {
            if (material.ConductivityCoefficient is not double coefficient || !double.IsFinite(coefficient))
                yield return rules.MaterialMessage("coefficient");
            if (material.ReferenceTemperature is not double temperature || !double.IsFinite(temperature))
                yield return rules.MaterialMessage("temperature");
        }
    }
}
