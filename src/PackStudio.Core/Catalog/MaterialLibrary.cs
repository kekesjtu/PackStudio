using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public sealed class MaterialLibrary
{
    public Dictionary<string, Material> Items { get; } = [];

    public MaterialLibrary(string root)
    {
        string dir = Path.Combine(root, "materials");
        var runtime = JsonData.Read(Path.Combine(dir, "runtime.json"));
        var index = (JObject)JsonData.Read(Path.Combine(dir, "index.json"))["materials"]!;
        foreach (var p in index.Properties())
        {
            var record = JsonData.CatalogEntry(dir, p.Value);
            var material = ParseRecord(Path.GetFileNameWithoutExtension(p.Value["file"]!.ToString()), record, "#AEB7BF");
            Items[material.Id] = material;
        }

        foreach (var p in ((JObject)runtime["aliases"]!).Properties())
        {
            var original = Items.Values.First(m => m.Name == p.Value["name"].Text());
            Items[p.Name] = original with
            {
                Id = p.Name,
                Color = p.Value["color"].Text("#AEB7BF")
            };
        }

        foreach (var item in (JArray)runtime["project_materials"]!)
        {
            var material = Parse(item);
            Items[material.Id] = material;
        }
    }

    public string IdForName(string name) => Items.Values.Where(m => m.Name == name).OrderBy(m => m.Id.Length).ThenBy(m => m.Id, StringComparer.Ordinal).First().Id;
    public static Material Parse(JToken v) => new(v["id"].Text(), v["name"].Text(), new(v["conductivity"]?["x"].Number() ?? 0, v["conductivity"]?["y"].Number() ?? 0, v["conductivity"]?["z"].Number() ?? 0), v["density"].Number(), v["specific_heat"].Number(), v["color"].Text("#AEB7BF"), v["category"].Text("Derived"), v["conductivity_coefficient"]?.Type == JTokenType.Float ? v["conductivity_coefficient"]!.Value<double>() : null, v["conductivity_reference_temperature_c"]?.Type is JTokenType.Float or JTokenType.Integer ? v["conductivity_reference_temperature_c"]!.Value<double>() : null, v["source"].Text());
    static Material ParseRecord(string id, JObject r, string color)
    {
        var c = r["conductivity"]!;
        bool orth = c["model"].Text() == "orthotropic";
        var tensor = orth ? new Vector(c["x"].Number(), c["y"].Number(), c["z"].Number()) : new Vector(c["value"].Number(), c["value"].Number(), c["value"].Number());
        return new(id, r["name"].Text(), tensor, r["density"]?["value"].Number() ?? 0, r["specific_heat"]?["value"].Number() ?? 0, color, r["category"].Text(), c["coefficient"]?.Value<double>(), c["reference_temperature"]?.Value<double>(), "PACK built-in material");
    }

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
            Conductivity = new(K(metal.Conductivity.X, matrix.Conductivity.X, 'x'), K(metal.Conductivity.Y, matrix.Conductivity.Y, 'y'), K(metal.Conductivity.Z, matrix.Conductivity.Z, 'z')),
            Density = rho,
            SpecificHeat = (f * metal.Density * metal.SpecificHeat + g * matrix.Density * matrix.SpecificHeat) / rho,
            ConductivityCoefficient = null,
            ReferenceTemperature = null,
            Source = $"PACK derived; element={metal.Id}; matrix={matrix.Id}; volume_fraction={f:G17}"};
    }
}
