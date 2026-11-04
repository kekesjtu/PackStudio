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
                var input = new JObject { ["substrate.layers"] = "4-Layer" };
                input["bga.center_solder_enabled"] = true;
                input["bga.center_solder_rows"] = 2;
                var result = template.Defaults(template.DefaultPreset, input);
                Assert(((JArray)result["metal.layers"]!).Count == 4, "four-layer stack not initialized");
                Assert(input["metal.layers"] == null, "overrides mutated");
                Assert(result["bga.center_solder_enabled"].Flag() && result["bga.center_solder_rows"].Number() == 2, "layout overwritten by substrate branch");
                foreach (JToken explicitValue in new JToken[] { JValue.CreateNull(), new JValue(0), new JValue(0.75), template.Defaults(template.DefaultPreset)["substrate.thickness"]! })
                {
                    input["substrate.thickness"] = explicitValue;
                    result = template.Defaults(template.DefaultPreset, input);
                    Assert(JToken.DeepEquals(result["substrate.thickness"], explicitValue), "explicit null/zero/value overwritten");
                }
            });
            tests.Case("parameters", family + " inner copper thickness", () =>
            {
                var template = tests.Catalog.Load(family);
                var input = new JObject { ["substrate.layers"] = "4-Layer" };
                input["trace.solid_thickness"] = 0.05;
                var result = ParameterRules.Prepare(template, template.Defaults(template.DefaultPreset, input));
                var rows = (JArray)result["metal.layers"]!;
                Near(rows[1]!["thickness"].Number(), 0.05, "first inner layer");
                Near(rows[2]!["thickness"].Number(), 0.05, "second inner layer");
            });
            tests.Case("parameters", family + " explicit values and tables survive creation and generation", () =>
            {
                var template = tests.Catalog.Load(family);
                double original = template.Defaults(template.DefaultPreset)["substrate.thickness"].Number();
                var options = new JObject { ["substrate.layers"] = "4-Layer", ["substrate.thickness"] = original };
                var document = ProjectDocument.Create(template, options: options);
                Near(document.Values["substrate.thickness"].Number(), original, "explicit value equal to default lost");
                var table = (JArray)document.Values["metal.layers"]!.DeepClone();
                table[0]!["thickness"] = 0.03;
                options["metal.layers"] = table;
                document = ProjectDocument.Create(template, options: options);
                Near(document.Values["metal.layers"]![0]!["thickness"].Number(), 0.03, "explicit layer overwritten during creation");
                var model = tests.Builder.Generate(document);
                Assert(model.Blocks.Any(b => b.GroupId == "group-traces" && Math.Abs(b.Size.Z - 0.03) < 1e-10), "edited table ignored by generation");
                Near(document.Values["metal.layers"]![0]!["thickness"].Number(), 0.03, "generation mutated saved layer");
            });
            tests.Case("parameters", family + " invalid inner thickness rejected by core", () =>
            {
                var template = tests.Catalog.Load(family);
                foreach (JToken thickness in new JToken[] { JValue.CreateNull(), new JValue(0), new JValue("invalid"), new JValue(10) })
                    Reject(() => ProjectDocument.Create(template, options: new JObject { ["substrate.layers"] = "4-Layer", ["trace.solid_thickness"] = thickness }));
            });
        }
        foreach (string family in new[] { "sop", "pqfp" })
            tests.Case("parameters", family + " exposed pad creation", () =>
            {
                var document = ProjectDocument.Create(tests.Catalog.Load(family), options: new JObject { ["package.exposed_pad"] = true });
                Near(document.Values["flag.downset"].Number(), document.Values["leads.height"].Number(), "exposed flag position");
                Assert(tests.Builder.Generate(document).Blocks.Any(b => b.GroupId == "group-thermal-land"), "exposed thermal land missing");
            });
        tests.Case("parameters", "SOP derived display agrees with modeled wire path", () =>
        {
            var document = ProjectDocument.Create(tests.Catalog.Load("sop"));
            var model = tests.Builder.Generate(document);
            var horizontal = model.Blocks.Single(b => b.Id == "bond-wire-h-right-part-1");
            var lead = model.Blocks.Single(b => b.Id == "sop-inner-right-part-1");
            var die = model.Blocks.Single(b => b.StructureType == "die");
            Near(ParameterRules.Derived("sop_wire_path_x", document.Values), horizontal.Size.X + Math.Abs(die.Maximum.Z - lead.Maximum.Z), "display path differs from geometry");
        });
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
            var context = new BuildContext(tests.Catalog, template, values, "layers", MaterialSelection.Defaults(template));
            MetalLayers.Parse(context, "metal.layers")[0]!["depth"] = 0.3;
            Near(values["metal.layers"]![0]!["depth"].Number(), 0.1, "table input mutated");
            context.Values["metal.layers"] = "[]";
            Reject(() => MetalLayers.Parse(context, "metal.layers"));
        });
    }
}
