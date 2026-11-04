namespace PackStudio.Core;

public record Material(string Id, string Name, Vector Conductivity, double Density, double SpecificHeat,
    string Color = "#AEB7BF", string Category = "Derived", double? ConductivityCoefficient = null,
    double? ReferenceTemperature = null, string Source = "", int ConductType = 2,
    double? StoredScalarConductivity = null, Vector? StoredDirectionalConductivity = null, double? Emissivity = null)
{
    [Newtonsoft.Json.JsonIgnore]
    public Vector EffectiveConductivity => ConductType == 2 ? Conductivity : new(Conductivity.X, Conductivity.X, Conductivity.X);
}
