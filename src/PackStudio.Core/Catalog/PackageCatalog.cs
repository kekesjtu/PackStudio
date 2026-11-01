using Newtonsoft.Json.Linq;
using System.Collections.Concurrent;

namespace PackStudio.Core;
public sealed class PackageCatalog
{
    public static readonly TemplateInfo[] Families = [new("chip_array", "Chip Array"), new("bare_die", "Bare Die"), new("cbga_fc", "Flip Chip CBGA"), new("pbga_fc", "Flip Chip PBGA"), new("pqfp", "PQFP"), new("qfn", "QFN"), new("sop", "SOP"), new("pbga_wb", "Wirebond PBGA")];
    readonly string root;
    readonly JObject index;
    readonly ConcurrentDictionary<string, Template> cache = new();
    public MaterialLibrary Materials { get; }

    public PackageCatalog(string root)
    {
        this.root = Path.GetFullPath(root);
        Materials = new(root);
        var data = JsonData.Read(Path.Combine(root, "presets", "index.json"));
        if (data["schema_version"].Text() != "packstudio.preset-index/v2")
            throw new InvalidDataException("预设索引版本不受支持。");
        index = (JObject)data["presets"]!;
    }

    public Template Load(string id)
    {
        if (cache.TryGetValue(id, out var cached))
            return cached;
        var info = Families.Single(f => f.Id == id);
        var data = JsonData.Read(Path.Combine(root, "templates", id + ".json"));
        var fields = (JArray)data["fields"]!;
        var presets = new List<Preset>();
        foreach (var p in index.Properties().Where(p => p.Value["family"].Text() == id))
        {
            var record = JsonData.CatalogEntry(Path.Combine(root, "presets"), p.Value);
            if (record["schema_version"].Text() != "packstudio.preset/v2" || record["id"].Text() != p.Name || record["family"].Text() != id)
                throw new InvalidDataException($"预设标识或版本无效：{p.Name}");
            var branches = (JObject)record["branches"]!;
            var branch = branches[record["default_branch"].Text()]!;
            presets.Add(new(p.Name, (JObject)branch["values"]!, (JObject)branch["assignments"]!, (JObject)branch["bga"]!, branches));
        }
        var footprint = fields.FirstOrDefault(f => f["control"].Text() == "footprint");
        if (footprint != null)
            footprint["options"] = new JArray(presets.Select(p => p.Id));
        return cache[id] = new(info, data, presets);
    }

    public JObject Initialize(Template t, JObject source, string presetId)
    {
        var values = (JObject)source.DeepClone();
        if (t.Info.Id is "chip_array" or "pbga_wb" && values["substrate.layers"].Text() == "4-Layer")
        {
            var preset = t.Presets.Single(p => p.Id == presetId);
            if (preset.Branches["four_layer"]?["values"] is JObject branchValues)
            {
                var baseline = t.Defaults(presetId);
                foreach (var p in branchValues.Properties())
                    if (JToken.DeepEquals(source[p.Name], baseline[p.Name]))
                        values[p.Name] = p.Value.DeepClone();
            }
        }

        if (t.Info.Id is "chip_array" or "pbga_wb" && values["substrate.layers"].Text() == "4-Layer" && source["trace.solid_thickness"] != null)
        {
            var thickness = source["trace.solid_thickness"];
            if (thickness?.Type is not (JTokenType.Integer or JTokenType.Float) || !double.IsFinite(thickness.Number()) || thickness.Number() < 0.001)
                throw new ArgumentException("内层金属厚度必须至少为 0.001 mm。");
            if (values["metal.layers"] is not JArray table)
                throw new ArgumentException("金属层表必须为 JSON 数组。");
            var rows = (JArray)table.DeepClone();
            if (rows.Count != 4) throw new ArgumentException("四层基板需要四个金属层。");
            double solid = thickness.Number(), height = values["substrate.thickness"].Number();
            double top = values["trace.top_thickness"].Number(), bottom = values["trace.bottom_thickness"].Number();
            double gap = (height - top - bottom - 2 * solid) / 3;
            if (gap < 0) throw new ArgumentException("金属层厚度超过基板厚度。");
            rows[0]!["thickness"] = top;
            rows[1]!["depth"] = top + gap;
            rows[2]!["depth"] = top + 2 * gap;
            rows[1]!["thickness"] = rows[2]!["thickness"] = solid;
            rows[3]!["depth"] = height - bottom;
            rows[3]!["thickness"] = bottom;
            values["metal.layers"] = rows;
        }

        if (t.Info.Id is "sop" or "pqfp" && values["package.exposed_pad"].Flag())
        {
            values["flag.downset"] = values["leads.height"]!.DeepClone();
            values["thermal_land.enabled"] = true;
            values["thermal_land.thickness"] = 0.07;
        }

        return values;
    }
}
