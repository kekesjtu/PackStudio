using Newtonsoft.Json.Linq;
using PackStudio.Core;

static class PresetContractChecks
{
    public static void Run(PackageCatalog catalog)
    {
        int presets = 0, branches = 0;
        foreach (var info in PackageCatalog.Families)
        {
            var template = catalog.Load(info.Id);
            var fields = template.Fields.ToDictionary(f => f["key"].Text());
            var groups = template.MaterialSelections.Select(s => s["group_id"].Text()).ToHashSet();
            foreach (var field in fields.Values)
            {
                if (field["control"].Text() == "table" && field["default"] is { Type: not JTokenType.Null } tableDefault)
                    Require(tableDefault is JArray, info.Id + ": " + field["key"].Text() + " table baseline must be an array");
            }
            foreach (var preset in template.Presets)
            {
                presets++;
                foreach (var branch in preset.Branches.Properties())
                {
                    branches++;
                    var data = (JObject)branch.Value;
                    Require(data.Properties().Select(p => p.Name).Order().SequenceEqual(new[] { "assignments", "bga", "values" }), "native wrapper in runtime branch");
                    foreach (var value in ((JObject)data["values"]!).Properties())
                    {
                        Require(fields.ContainsKey(value.Name), "unknown internal field " + value.Name);
                        if (fields[value.Name]["control"].Text() == "table")
                            Require(value.Value is JArray, "preset table must be an array");
                    }
                    foreach (var assignment in ((JObject)data["assignments"]!).Properties())
                    {
                        Require(groups.Contains(assignment.Name), "unknown material group");
                        Require(catalog.Materials.Items.ContainsKey(assignment.Value.Text()), "material must be an internal ID");
                    }
                    if (branch.Name == "four_layer")
                    {
                        var input = template.Defaults(preset.Id);
                        input["substrate.layers"] = "4-Layer";
                        var original = input.DeepClone();
                        var initialized = catalog.Initialize(template, input, preset.Id);
                        Require(((JArray)initialized["metal.layers"]!).Count == 4, "four-layer initialization");
                        Require(JToken.DeepEquals(input, original), "initialization mutated the input");
                        foreach (JToken explicitValue in new JToken[] { JValue.CreateNull(), new JValue(0), new JValue(0.75) })
                        {
                            input["substrate.thickness"] = explicitValue;
                            var edited = catalog.Initialize(template, input, preset.Id);
                            Require(JToken.DeepEquals(edited["substrate.thickness"], explicitValue), "branch overwrote explicit null/zero/value");
                        }
                    }
                }
                var baseline = template.Defaults(preset.Id);
                foreach (var value in preset.Values.Properties())
                    Require(JToken.DeepEquals(baseline[value.Name], value.Value), "template default filled a preset null/value");
            }
        }
        Require(presets == 342 && branches == 416, "preset/branch coverage changed");
        var chip = catalog.Load("chip_array");
        var top = chip.Fields.Single(f => f["key"].Text() == "trace.top_thickness");
        Require(top["des_symbol"]?["2-Layer"].Text() == "tza1" && top["des_symbol"]?["4-Layer"].Text() == "tz1", "conditional DES symbols");
        Require(catalog.Load("bare_die").Presets.Count == 0, "Bare Die must use template baseline");
    }

    public static void LegacyTables(PackageCatalog catalog)
    {
        var request = new JObject { ["template_id"] = "pbga_fc", ["overrides"] = new JObject { ["pbga_fc.metal.layers"] = "[{\"depth\":0.1,\"thickness\":0.018,\"coverage\":30}]" } };
        var parsed = RequestDocument.Parse(request, catalog);
        Require(parsed.Values["metal.layers"] is JArray, "archived request table not normalized");
        var context = new BuildContext(catalog, catalog.Load("pbga_fc"), parsed.Values, parsed.PresetId, "table");
        var rows = MetalLayers.Parse(context, "metal.layers");
        rows[0]!["depth"] = 0.3;
        Require(parsed.Values["metal.layers"]![0]!["depth"].Number() == 0.1, "table parsing mutates the project");
        context.Values["metal.layers"] = "[]";
        try { MetalLayers.Parse(context, "metal.layers"); }
        catch (ArgumentException) { return; }
        throw new Exception("generator accepted a string table");
    }

    static void Require(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
    }
}
