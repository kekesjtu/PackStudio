using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static TestSuite;

static class ParameterChecks
{
    public static void Run(TestSuite tests)
    {
        foreach (string family in new[] { "chip_array", "pbga_wb" })
        {
            tests.Case("parameters", family + " four-layer initialization", () =>
            {
                var template = tests.Catalog.Load(family);
                var input = template.Defaults(template.DefaultPreset);
                input["substrate.layers"] = "4-Layer";
                input["bga.center_solder_enabled"] = true;
                input["bga.center_solder_rows"] = 2;
                var result = tests.Catalog.Initialize(template, input, template.DefaultPreset);
                Assert(((JArray)result["metal.layers"]!).Count == 4, "four-layer stack not initialized");
                Assert(((JArray)input["metal.layers"]!).Count == 2, "input stack mutated");
                Assert(result["bga.center_solder_enabled"].Flag() && result["bga.center_solder_rows"].Number() == 2, "layout overwritten by substrate branch");
                foreach (JToken explicitValue in new JToken[] { JValue.CreateNull(), new JValue(0), new JValue(0.75) })
                {
                    input["substrate.thickness"] = explicitValue;
                    result = tests.Catalog.Initialize(template, input, template.DefaultPreset);
                    Assert(JToken.DeepEquals(result["substrate.thickness"], explicitValue), "explicit null/zero/value overwritten");
                }
            });
            tests.Case("parameters", family + " inner copper thickness", () =>
            {
                var template = tests.Catalog.Load(family);
                var input = template.Defaults(template.DefaultPreset);
                input["substrate.layers"] = "4-Layer";
                input["trace.solid_thickness"] = 0.05;
                var result = tests.Catalog.Initialize(template, input, template.DefaultPreset);
                var rows = (JArray)result["metal.layers"]!;
                Near(rows[1]!["thickness"].Number(), 0.05, "first inner layer");
                Near(rows[2]!["thickness"].Number(), 0.05, "second inner layer");
            });
        }
        tests.Case("parameters", "power edit and invalid geometry", () =>
        {
            var document = ProjectDocument.Create(tests.Catalog.Load("bare_die"));
            document.Values["die.power"] = 7.25;
            Near(tests.Builder.Generate(document).Sources.Sum(s => s.Power), 7.25, "edited power");
            document.Values["die.length"] = -1;
            Reject(() => tests.Builder.Generate(document));
        });
        tests.Case("parameters", "metal layer edits do not mutate document", () =>
        {
            var template = tests.Catalog.Load("pbga_fc");
            var values = template.Defaults(template.DefaultPreset);
            values["metal.layers"] = new JArray(new JObject { ["depth"] = 0.1, ["thickness"] = 0.018, ["coverage"] = 30 });
            var context = new BuildContext(tests.Catalog, template, values, template.DefaultPreset, "layers");
            MetalLayers.Parse(context, "metal.layers")[0]!["depth"] = 0.3;
            Near(values["metal.layers"]![0]!["depth"].Number(), 0.1, "table input mutated");
            context.Values["metal.layers"] = "[]";
            Reject(() => MetalLayers.Parse(context, "metal.layers"));
        });
    }
}
