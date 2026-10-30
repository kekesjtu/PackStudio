using Newtonsoft.Json.Linq;
using System.Collections.Concurrent;

namespace PackStudio.Core;
public sealed class PackageCatalog
{
    public static readonly TemplateInfo[] Families = [new("chip_array", "Chip Array"), new("bare_die", "Bare Die"), new("cbga_fc", "Flip Chip CBGA"), new("pbga_fc", "Flip Chip PBGA"), new("pqfp", "PQFP"), new("qfn", "QFN"), new("sop", "SOP"), new("pbga_wb", "Wirebond PBGA")];
    readonly string root;
    readonly JObject bindings, index;
    readonly ConcurrentDictionary<string, Template> cache = new();
    public MaterialLibrary Materials { get; }

    public PackageCatalog(string root)
    {
        this.root = Path.GetFullPath(root);
        Materials = new(root);
        bindings = (JObject)JsonData.Read(Path.Combine(root, "pack_bindings.json"))["families"]!;
        index = (JObject)JsonData.Read(Path.Combine(root, "presets", "index.json"))["presets"]!;
    }

    public Template Load(string id)
    {
        if (cache.TryGetValue(id, out var cached))
            return cached;
        var info = Families.Single(f => f.Id == id);
        var data = JsonData.Read(Path.Combine(root, "templates", id + ".json"));
        var fields = (JArray)data["fields"]!;
        var presets = new List<Preset>();
        if (bindings[id] is JObject binding)
        {
            var keys = fields.Select(f => f["key"].Text()).ToHashSet();
            foreach (var p in index.Properties().Where(p => p.Value["family"].Text() == binding["family"].Text()))
            {
                var record = JsonData.CatalogEntry(Path.Combine(root, "presets"), p.Value);
                var branch = record["branches"]![record["default_branch"]!.ToString()]!;
                var values = AdaptValues(branch, binding, keys, id == "pbga_wb");
                var assignments = new JObject();
                foreach (var m in ((JObject)binding["materials"]!).Properties())
                {
                    var native = JsonData.At(branch, m.Value.Values<string>()!);
                    if (native?["value"]?.Type == JTokenType.String)
                        assignments[m.Name] = Materials.IdForName(native["value"]!.ToString());
                }

                presets.Add(new(p.Name, values, assignments, BallPattern(branch, values), record));
            }
        }

        var footprint = fields.FirstOrDefault(f => f["control"].Text() == "footprint");
        if (footprint != null)
            footprint["options"] = new JArray(presets.Select(p => p.Id));
        return cache[id] = new(info, data, presets);
    }

    public JObject AdaptValues(JToken branch, JObject binding, HashSet<string> keys, bool disconnect)
    {
        var values = new JObject();
        foreach (var p in ((JObject)binding["parameters"]!).Properties().Where(p => keys.Contains(p.Name)))
        {
            var native = JsonData.At(branch, p.Value.Values<string>()!);
            if (native?.Type == JTokenType.Boolean)
                values[p.Name] = native.DeepClone();
            else if (native is JArray rows)
                values[p.Name] = NativeValue(p.Name, rows, disconnect);
            else if (native?["value"] != null)
                values[p.Name] = NativeValue(p.Name, native["value"]!, disconnect);
            else if (native?["status"].Text() == "not_applicable")
                values[p.Name] = null;
            else
                throw new InvalidDataException($"原生预设缺少 {p.Name}");
        }

        return values;
    }

    public JObject Initialize(Template t, JObject source, string presetId)
    {
        var values = (JObject)source.DeepClone();
        if (t.Info.Id is "chip_array" or "pbga_wb" && values["substrate.layers"].Text() == "4-Layer")
        {
            var preset = t.Presets.Single(p => p.Id == presetId);
            var branch = preset.Record["branches"]?["four_layer"];
            if (branch != null)
            {
                var adapted = AdaptValues(branch, (JObject)bindings[t.Info.Id]!, t.Fields.Select(f => f["key"].Text()).ToHashSet(), t.Info.Id == "pbga_wb");
                var baseline = t.Defaults(presetId);
                foreach (var p in adapted.Properties())
                    if (JToken.DeepEquals(source[p.Name], baseline[p.Name]))
                        values[p.Name] = p.Value.DeepClone();
            }
        }

        if (t.Info.Id is "sop" or "pqfp" && values["package.exposed_pad"].Flag())
        {
            values["flag.downset"] = values["leads.height"]!.DeepClone();
            values["thermal_land.enabled"] = true;
            values["thermal_land.thickness"] = 0.07;
        }

        return values;
    }

    static JToken NativeValue(string key, JToken v, bool disconnect)
    {
        if (v is JArray rows)
            return new JArray(rows.Where(r => r["status"].Text() == "specified").Select(r => new JObject { ["depth"] = r["depth_m"].Number() * 1000, ["thickness"] = r["thickness_m"].Number() * 1000, ["coverage"] = r["coverage_percent"]?.DeepClone(), ["disconnect"] = disconnect && r["disconnect_to_vias"]?.Flag() == true })).ToString(Newtonsoft.Json.Formatting.None);
        if (key is "vias.filled" or "bond_wire.auto_count" or "upper.filled" or "lower.filled" or "leads.custom_coverage")
            return v.Text() == "yes";
        if (key == "vias.enabled" && v.Type == JTokenType.String)
            return v.Text() != "ignored";
        if (key == "vias.modeling" && v.Text() == "ignored")
            return "discrete";
        if (key == "bumps.array_type")
            return v.Text() == "regularArray" ? "regular" : "non_regular";
        if (key == "cover.type" && v.Text() == "bareDie")
            return "bare_die";
        return v.DeepClone();
    }

    static JObject BallPattern(JToken branch, JObject values)
    {
        var result = new JObject();
        if (values["bga.rows"] == null)
            return result;
        var groups = branch["groups"]!;
        var depop = groups["solderBallDepopulation"]!["properties"]!;
        var center = groups["centralBalls"]!["properties"]!;
        bool enabled = depop["depopulatedCenter"]?["value"].Flag() == true;
        result["solder_removal_enabled"] = enabled;
        result["center_solder_enabled"] = center["centralBalls"]?["value"].Flag() == true;
        result["populated_rows"] = depop["numberFullyPopulatedRowsMEp"]?["value"]?.DeepClone();
        result["populated_columns"] = depop["numberFullyPopulatedRowsMDp"]?["value"]?.DeepClone();
        result["center_solder_rows"] = center["numberCentralRowsMEp"]?["value"]?.DeepClone();
        result["center_solder_columns"] = center["numberCentralRowsMDp"]?["value"]?.DeepClone();
        result["staggered"] = groups["solderBalls"]?["properties"]?["staggeredMatrix"]?["value"]?.DeepClone();
        result["center_staggered"] = center["staggeredMatrix"]?["value"]?.DeepClone();
        if (enabled && depop["depopulationDialog"]?["value"]?["native_cell_list"] is JArray cells && cells.Count > 0)
        {
            int rows = (int)values["bga.rows"]!, cols = (int)values["bga.columns"]!;
            var present = cells.Select(c => (c["row"]!.Value<int>(), c["column"]!.Value<int>())).ToHashSet();
            result["omitted_cells"] = new JArray(
                from r in Enumerable.Range(0, rows)from c in Enumerable.Range(0, cols)
                where !present.Contains((r, c))select new JObject { ["row"] = r, ["column"] = c });
            result["center_solder_enabled"] = false;
        }

        return result;
    }
}
