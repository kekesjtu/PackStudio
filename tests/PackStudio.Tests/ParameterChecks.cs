using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static TestSuite;

static class ParameterChecks
{
    public static void Run(TestSuite tests)
    {
        foreach (string family in new[] { "chip_array", "pbga_wb" })
        {
            tests.Case("parameters", family + " creation preserves a malformed branch selection", () =>
            {
                var definition = tests.Catalog.Load(family);
                var selection = new JArray("invalid");
                var document = PackageInitializer.Create(definition, overrides: new JObject { ["substrate.layers"] = selection });
                Assert(JToken.DeepEquals(document.Values["substrate.layers"], selection), "creation rejected or replaced branch input");
                var result = tests.GenerateResult(document);
                Assert(result.Model == null && result.Issues.Any(i => i.Stage == ValidationStage.Input && i.ParameterPaths.Contains("substrate.layers")), "branch type did not reach generation validation");
            });
            tests.Case("parameters", family + " four-layer initialization", () =>
            {
                var template = tests.Catalog.Load(family);
                var input = new JObject { ["substrate.layers"] = "4-Layer" };
                input["bga.center_solder_enabled"] = true;
                input["bga.center_solder_rows"] = 2;
                var result = tests.Create(template, options: input).Values;
                Assert(((JArray)result["metal.layers"]!).Count == 4, "four-layer stack not initialized");
                Assert(input["metal.layers"] == null, "overrides mutated");
                Assert(result["bga.center_solder_enabled"].Flag() && result["bga.center_solder_rows"].Number() == 2, "layout overwritten by substrate branch");
                foreach (JToken explicitValue in new JToken[] { JValue.CreateNull(), new JValue(0), new JValue(0.75), tests.Create(template).Values["substrate.thickness"]! })
                {
                    input["substrate.thickness"] = explicitValue;
                    result = tests.Create(template, options: input).Values;
                    Assert(JToken.DeepEquals(result["substrate.thickness"], explicitValue), "explicit null/zero/value overwritten");
                }
            });
            tests.Case("parameters", family + " inner copper thickness", () =>
            {
                var template = tests.Catalog.Load(family);
                var input = new JObject { ["substrate.layers"] = "4-Layer" };
                input["trace.solid_thickness"] = 0.05;
                var result = tests.Create(template, options: input).Values;
                var rows = (JArray)result["metal.layers"]!;
                Near(rows[1]!["thickness"].Number(), 0.05, "first inner layer");
                Near(rows[2]!["thickness"].Number(), 0.05, "second inner layer");
            });
            tests.Case("parameters", family + " explicit values and tables survive creation and generation", () =>
            {
                var template = tests.Catalog.Load(family);
                double original = tests.Create(template).Values["substrate.thickness"].Number();
                var options = new JObject { ["substrate.layers"] = "4-Layer", ["substrate.thickness"] = original };
                var document = tests.Create(template, options: options);
                Near(document.Values["substrate.thickness"].Number(), original, "explicit value equal to default lost");
                var table = (JArray)document.Values["metal.layers"]!.DeepClone();
                table[0]!["thickness"] = 0.03;
                options["metal.layers"] = table;
                document = tests.Create(template, options: options);
                Near(document.Values["metal.layers"]![0]!["thickness"].Number(), 0.03, "explicit layer overwritten during creation");
                var model = tests.Generate(document);
                Assert(model.Blocks.Any(b => b.GroupId == "group-traces" && Math.Abs(b.Size.Z - 0.03) < 1e-10), "edited table ignored by generation");
                Near(document.Values["metal.layers"]![0]!["thickness"].Number(), 0.03, "generation mutated saved layer");
            });
            tests.Case("parameters", family + " invalid creation thickness is preserved until generation", () =>
            {
                var template = tests.Catalog.Load(family);
                foreach (JToken thickness in new JToken[] { JValue.CreateNull(), new JValue(0), new JValue("invalid"), new JValue(10) })
                {
                    var document = tests.Create(template, options: new JObject { ["substrate.layers"] = "4-Layer", ["trace.solid_thickness"] = thickness });
                    Assert(JToken.DeepEquals(document.Values["trace.solid_thickness"], thickness), "creation changed submitted thickness");
                    var result = tests.GenerateResult(document);
                    Assert(result.Model == null && result.HasErrors && result.Issues.Any(i => i.Stage == ValidationStage.Input), "invalid layer stack entered modeling");
                }
            });
        }
        foreach (string family in new[] { "sop", "pqfp" })
        {
            tests.Case("parameters", family + " exposed pad creation", () =>
            {
                var document = tests.Create(tests.Catalog.Load(family), options: new JObject { ["package.exposed_pad"] = true });
                Near(document.Values["flag.downset"].Number(), document.Values["leads.height"].Number(), "exposed flag position");
                Assert(tests.Generate(document).Blocks.Any(b => b.GroupId == "group-thermal-land"), "exposed thermal land missing");
                var configuration = (JObject)tests.Catalog.LoadExposedPad(family).DeepClone();
                configuration["flag_downset_source"] = "leads.thickness";
                var alternate = PackageInitializer.Create(tests.Catalog.Load(family),
                    overrides: new JObject { ["package.exposed_pad"] = true }, exposedPad: configuration);
                Near(alternate.Values["flag.downset"].Number(), alternate.Values["leads.thickness"].Number(), "downset source ignored the small contract");
            });
            tests.Case("parameters", family + " exposed pad configuration is required only for the final selected branch", () =>
            {
                var definition = tests.Catalog.Load(family);
                var options = new JObject { ["package.exposed_pad"] = false };
                PackageInitializer.Create(definition, overrides: options);
                options["package.exposed_pad"] = true;
                bool missingConfiguration = false;
                try { PackageInitializer.Create(definition, overrides: options); }
                catch (InvalidDataException) { missingConfiguration = true; }
                Assert(missingConfiguration, "exposed pad creation silently skipped its configuration");
                options["flag.downset"] = 0;
                options["thermal_land.thickness"] = -0.12;
                var document = tests.Create(definition, options: options);
                Near(document.Values["flag.downset"].Number(), 0, "explicit downset overwritten by exposed pad initialization");
                Near(document.Values["thermal_land.thickness"].Number(), -0.12, "creation validated or replaced explicit pad thickness");
                var result = tests.GenerateResult(document);
                Assert(result.Model == null && result.Issues.Any(i => i.ParameterPaths.Contains("thermal_land.thickness")), "invalid pad thickness bypassed generation validation");
                Near(document.Values["thermal_land.thickness"].Number(), -0.12, "generation reapplied exposed pad initialization");
            });
        }
        tests.Case("parameters", "power edit and invalid geometry", () =>
        {
            var document = tests.Create(tests.Catalog.Load("bare_die"));
            document.Values["die.power"] = 7.25;
            Near(tests.Generate(document).Sources.Sum(s => s.Power), 7.25, "edited power");
            document.Values["die.length"] = -1;
            Reject(() => tests.Generate(document));
        });
        tests.Case("parameters", "metal layer edits do not mutate document", () =>
        {
            var template = tests.Catalog.Load("pbga_fc");
            var values = tests.Create(template).Values;
            values["metal.layers"] = new JArray(new JObject { ["depth"] = 0.1, ["thickness"] = 0.018, ["coverage"] = 30 });
            var context = new BuildContext(template, values, "layers", tests.Catalog.Materials, tests.Catalog.Groups, MaterialSelection.Defaults(template));
            MetalLayers.Parse(context, "metal.layers")[0]!["depth"] = 0.3;
            Near(values["metal.layers"]![0]!["depth"].Number(), 0.1, "table input mutated");
        });
    }
}
