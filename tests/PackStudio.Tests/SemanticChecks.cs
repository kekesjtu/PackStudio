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
                var document = ProjectDocument.Create(template);
                document.Values["trace.top_thickness"] = "unused";
                document.Values["trace.bottom_thickness"] = -1;
                document.Values["trace.solid_thickness"] = "unused";
                document.Values["metal.layers"]![0]!["thickness"] = 0.03;
                var model = tests.Builder.Generate(document);
                Assert(model.Blocks.Any(b => b.GroupId == "group-traces" && Math.Abs(b.Size.Z - 0.03) < 1e-10), "saved table did not control geometry");
                Reject(() => ProjectDocument.Create(template, options: new JObject { ["trace.top_thickness"] = "invalid" }));
            });
        tests.Case("parameters", "inactive object containers still require structure", () =>
        {
            var template = tests.Catalog.Load("pbga_wb");
            var document = ProjectDocument.Create(template);
            document.Values["vias.enabled"] = false;
            document.Values["vias.configuration"] = JValue.CreateNull();
            Reject(() => template.Validate(document.Values));
            var data = (JObject)template.Data.DeepClone();
            data["fields"]!.Single(f => f["key"].Text() == "vias.configuration")["default"] = JValue.CreateNull();
            bool rejected = false;
            try { _ = new Template(template.Info, data, template.Presets); }
            catch (InvalidDataException) { rejected = true; }
            Assert(rejected, "invalid object definition accepted");
        });
        tests.Case("catalog", "preset options are derived without changing field definitions", () =>
        {
            var source = tests.Catalog.Load("chip_array");
            var definition = new JObject { ["key"] = "preset", ["label"] = "Preset", ["control"] = "combobox", ["options_source"] = "presets", ["options"] = new JArray() };
            var template = new Template(source.Info, new JObject { ["fields"] = new JArray(definition) }, source.Presets);
            var field = template.Fields[0]!;
            var options = template.OptionsFor(field);
            Assert(options.Count == source.Presets.Count && options.Any(o => o.Text() == source.DefaultPreset), "preset options missing");
            Assert(FieldValues.Error(field, new JValue(source.DefaultPreset), options) == null, "valid preset rejected");
            Assert(FieldValues.Error(field, new JValue("missing"), options) != null, "invalid preset accepted");
            Assert(((JArray)field["options"]!).Count == 0, "derived options written into definition");
        });
        tests.Case("parameters", "batch creation retains overrides regardless of their order", () =>
        {
            var template = tests.Catalog.Load("chip_array");
            var options = new JObject { ["trace.solid_thickness"] = 0.05, ["substrate.thickness"] = 0.75, ["substrate.layers"] = "4-Layer" };
            var first = ProjectDocument.Create(template, options: options);
            var second = ProjectDocument.Create(template, options: new JObject(options.Properties().Reverse().Select(p => new JProperty(p.Name, p.Value.DeepClone()))));
            foreach (var document in new[] { first, second })
            {
                Near(document.Values["substrate.thickness"].Number(), 0.75, "batch override lost");
                Near(document.Values["metal.layers"]![1]!["thickness"].Number(), 0.05, "batch layer calculation differs");
                tests.Builder.Generate(document);
            }
        });
    }
}
