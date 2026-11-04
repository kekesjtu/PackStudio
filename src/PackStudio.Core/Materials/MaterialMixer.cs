namespace PackStudio.Core;

public static class MaterialMixer
{
    public static Material Mix(string id, Material metal, Material matrix, double fraction, string parallel = "xyz", bool includeMatrix = true, bool allowOverfilled = false)
    {
        if (!double.IsFinite(fraction) || fraction < 0 || fraction > 1 && !allowOverfilled)
            throw new ArgumentException($"{id} 体积分数 {fraction:G6} 不在 0–1 范围。");
        double f = fraction, g = 1 - f, rho = f * metal.Density + g * matrix.Density;
        double K(double a, double b, char axis) => parallel.Contains(axis) ? f * a + (includeMatrix ? g * b : 0) : b;
        return metal with
        {
            Id = id,
            Name = id,
            Conductivity = new(K(metal.EffectiveConductivity.X, matrix.EffectiveConductivity.X, 'x'), K(metal.EffectiveConductivity.Y, matrix.EffectiveConductivity.Y, 'y'), K(metal.EffectiveConductivity.Z, matrix.EffectiveConductivity.Z, 'z')),
            Density = rho,
            SpecificHeat = (f * metal.Density * metal.SpecificHeat + g * matrix.Density * matrix.SpecificHeat) / rho,
            ConductType = parallel == "xyz" && metal.ConductType != 2 && matrix.ConductType != 2 ? 0 : 2,
            StoredScalarConductivity = null,
            StoredDirectionalConductivity = null,
            ConductivityCoefficient = null,
            ReferenceTemperature = null,
            Source = $"PACK derived; element={metal.Id}; matrix={matrix.Id}; volume_fraction={f:G17}"};
    }
}
