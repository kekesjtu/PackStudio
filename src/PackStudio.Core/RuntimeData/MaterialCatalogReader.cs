using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public sealed class MaterialCatalogReader
{
    public MaterialCatalog Read(string root)
    {
        string directory = Path.Combine(root, "materials");
        var runtime = JsonData.Read(Path.Combine(directory, "runtime.json"));
        var index = (JObject)JsonData.Read(Path.Combine(directory, "index.json"))["materials"]!;
        var items = new Dictionary<string, Material>();
        foreach (var entry in index.Properties())
        {
            var material = ParseRecord(Path.GetFileNameWithoutExtension(entry.Value["file"]!.ToString()), JsonData.CatalogEntry(directory, entry.Value));
            items.Add(material.Id, Checked(material));
        }
        foreach (var alias in ((JObject)runtime["aliases"]!).Properties())
        {
            var original = items.Values.FirstOrDefault(m => m.Name == alias.Value["name"].Text())
                ?? throw new InvalidDataException($"材料别名 {alias.Name} 引用未知材料。");
            items.Add(alias.Name, original with { Id = alias.Name, Color = alias.Value["color"].Text("#AEB7BF") });
        }
        foreach (var item in (JArray)runtime["project_materials"]!)
        {
            var material = Checked(Parse(item));
            items.Add(material.Id, material);
        }
        return new(items.Values);
    }

    static Material Checked(Material material)
    {
        string[] errors = FieldRules.MaterialErrors(material).ToArray();
        if (errors.Length > 0) throw new InvalidDataException($"材料 {material.Name}：{string.Join(" ", errors)}");
        return material;
    }

    // Legacy internal records use a tensor. Their format mapping is confined to this boundary.
    public static Material Parse(JToken value)
    {
        double Number(string key) => value[key]?.Type is JTokenType.Integer or JTokenType.Float
            ? value[key]!.Value<double>() : throw new InvalidDataException($"材料字段 {key} 需要数值。");
        int type = ConductType(value);
        var conductivity = value["conductivity"] as JObject ?? throw new InvalidDataException("内部材料记录缺少导热率对象。");
        double x = Optional(conductivity, "x") ?? throw new InvalidDataException("内部材料记录缺少导热率 x。");
        double Axis(string key) => Optional(conductivity, key) ?? (type == 2 ? throw new InvalidDataException($"内部材料记录缺少导热率 {key}。") : x);
        var vector = new Vector(x, Axis("y"), Axis("z"));
        double? coefficient = Optional(value, "conductivity_coefficient"), reference = Optional(value, "conductivity_reference_temperature_c");
        return new(value["id"].Text(), value["name"].Text(), vector, Number("density"), Number("specific_heat"),
            value["color"].Text("#AEB7BF"), value["category"].Text("Derived"), coefficient, reference, value["source"].Text(), type);
    }

    static Material ParseRecord(string id, JObject record)
    {
        double Required(string key) => Optional(record, key) ?? throw new InvalidDataException($"材料 {id} 缺少数值字段 {key}。");
        int type = ConductType(record);
        double? scalar = Optional(record, "conductivity_w_m_k");
        var directional = new Vector(Optional(record, "kx_w_m_k") ?? double.NaN, Optional(record, "ky_w_m_k") ?? double.NaN, Optional(record, "kz_w_m_k") ?? double.NaN);
        var active = type switch
        {
            0 or 1 => new Vector(Required("conductivity_w_m_k"), Required("conductivity_w_m_k"), Required("conductivity_w_m_k")),
            2 => directional,
            _ => throw new InvalidDataException($"材料 {id} 的导热类型 {type} 不受支持。")
        };
        return new(id, record["name"].Text(), active, Required("density_kg_m3"), Required("specific_heat_j_kg_k"),
            Category: record["group"].Text(), ConductivityCoefficient: Optional(record, "conductivity_coefficient"),
            ReferenceTemperature: Optional(record, "conductivity_reference_temperature"), Source: record["source"]?.ToString() ?? "",
            ConductType: type, StoredScalarConductivity: scalar, StoredDirectionalConductivity: directional);
    }

    static double? Optional(JToken value, string key) => value[key]?.Type switch
    {
        null or JTokenType.Null => null,
        JTokenType.Integer or JTokenType.Float => value[key]!.Value<double>(),
        _ => throw new InvalidDataException($"材料字段 {key} 需要数值。")
    };

    static int ConductType(JToken value) => value["conduct_type"] is { Type: JTokenType.Integer } type
        ? type.Value<int>() : throw new InvalidDataException("材料 conduct_type 必须为整数。");
}
