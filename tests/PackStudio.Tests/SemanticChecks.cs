using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static TestSuite;

static class SemanticChecks
{
    public static void Run(TestSuite tests)
    {
        foreach (string family in new[] { "chip_array", "pbga_wb" })
            tests.Case("parameters", family + " creation-only input does not invalidate saved geometry", () =>
            {
                var template = tests.Catalog.Load(family);
                var document = tests.Create(template);
                document.Values["trace.top_thickness"] = "unused";
                document.Values["trace.bottom_thickness"] = -1;
                document.Values["trace.solid_thickness"] = "unused";
                document.Values["metal.layers"]![0]!["thickness"] = 0.03;
                var model = tests.Generate(document);
                Assert(model.Blocks.Any(b => b.GroupId == "group-traces" && Math.Abs(b.Size.Z - 0.03) < 1e-10), "saved table did not control geometry");
                var created = tests.Create(template, options: new JObject { ["trace.top_thickness"] = "invalid" });
                Assert(created.Values["trace.top_thickness"].Text() == "invalid", "creation discarded invalid original input");
                Assert(tests.GenerateResult(created).HasErrors, "invalid derived layer input was accepted for modeling");
            });
        tests.Case("parameters", "inactive null is preserved and active null reports its field", () =>
        {
            var template = tests.Catalog.Load("pbga_wb");
            var document = tests.Create(template);
            document.Values["vias.enabled"] = false;
            document.Values["vias.configuration"] = JValue.CreateNull();
            tests.Generate(document);
            Assert(document.Values["vias.configuration"]!.Type == JTokenType.Null, "inactive null was backfilled");
            document.Values["vias.enabled"] = true;
            var result = tests.GenerateResult(document);
            Assert(result.Model == null && result.Issues.Any(i => i.ParameterPaths.Contains("vias.configuration")), "active null was not located");
        });
        tests.Case("catalog", "preset options are derived without changing field definitions", () =>
        {
            var source = tests.Catalog.Load("chip_array");
            var definition = new JObject { ["key"] = "preset", ["label"] = "Preset", ["control"] = "combobox", ["options_source"] = "presets", ["options"] = new JArray() };
            var field = definition;
            var options = source.OptionsFor(field);
            Assert(options.Count == source.Presets.Count && options.Any(o => o.Text() == source.DefaultPreset), "preset options missing");
            Assert(!options.Any(o => o.Text() == "missing"), "unknown preset appeared in choices");
            Assert(((JArray)field["options"]!).Count == 0, "derived options written into definition");
        });
        tests.Case("parameters", "batch creation retains overrides regardless of their order", () =>
        {
            var template = tests.Catalog.Load("chip_array");
            var options = new JObject { ["trace.solid_thickness"] = 0.05, ["substrate.thickness"] = 0.75, ["substrate.layers"] = "4-Layer" };
            var first = tests.Create(template, options: options);
            var second = tests.Create(template, options: new JObject(options.Properties().Reverse().Select(p => new JProperty(p.Name, p.Value.DeepClone()))));
            foreach (var document in new[] { first, second })
            {
                Near(document.Values["substrate.thickness"].Number(), 0.75, "batch override lost");
                Near(document.Values["metal.layers"]![1]!["thickness"].Number(), 0.05, "batch layer calculation differs");
                tests.Generate(document);
            }
        });
    }
}
