using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static TestSuite;

static class GenerationChecks
{
    public static void Run(TestSuite tests)
    {
        ValidationRules Rules(string family) => new(
            JsonData.Read(Path.Combine(tests.Root, "runtime_data", "validation", "common.json")),
            JsonData.Read(Path.Combine(tests.Root, "runtime_data", "validation", family + ".json")));

        tests.Case("generation", "family relation severity and message come from declarations", () =>
        {
            var definition = tests.Catalog.Load("qfn");
            var document = tests.Create(definition);
            document.Values["die.length"] = document.Values["package.length"]!.Value<double>() + 0.01;
            var rules = Rules("qfn");
            var rule = rules.Checks.Single(r => r["id"].Text() == "input.package.fit");
            rule["severity"] = "warning";
            rule["message"] = "请检查 {path}";
            var issues = InputValidator.Validate(document, definition, tests.Catalog.Materials, rules);
            var fit = issues.Single(i => i.Code == "input.package.fit");
            Assert(fit.Severity == IssueSeverity.Warning && fit.Message == "请检查 die.length", "family relation ignored configured severity or message");
            rule.Remove();
            Assert(!InputValidator.Validate(document, definition, tests.Catalog.Materials, rules).Any(i => i.Code == "input.package.fit"), "undeclared family relation still executed");
        });

        tests.Case("generation", "field diagnostics use configured severity and message", () =>
        {
            var definition = tests.Catalog.Load("bare_die");
            var document = tests.Create(definition);
            document.Values["die.power"] = -1;
            var rules = Rules("bare_die");
            var field = rules.Fields.Single(f => f["key"].Text() == "die.power");
            field["severity"] = "warning";
            field["messages"] = new JObject { ["input.range"] = "功率范围提示：{path}" };
            var issue = InputValidator.Validate(document, definition, tests.Catalog.Materials, rules).Single(i => i.Code == "input.range");
            Assert(issue.Severity == IssueSeverity.Warning && issue.Message == "功率范围提示：die.power", "field rule ignored configured diagnostics");
        });

        tests.Case("generation", "SOP odd lead count is reported once before modeling", () =>
        {
            var document = tests.Create(tests.Catalog.Load("sop"));
            document.Values["leads.total"] = 21;
            var result = tests.GenerateResult(document);
            Assert(result.Model == null && result.Issues.Count(i => i.ParameterPaths.Contains("leads.total")) == 1, "lead count was validated more than once");
            Assert(result.Issues.Single(i => i.ParameterPaths.Contains("leads.total")).Code == "input.sop.leads", "lead count bypassed the declared rule");
        });

        tests.Case("generation", "model diagnostics use configured severity and message", () =>
        {
            var rules = Rules("bare_die");
            var rule = rules.Checks.Single(r => r["id"].Text() == "model.source");
            rule["severity"] = "warning";
            rule["message"] = "检查热源 {entity}";
            var issue = ModelValidator.Validate(Model(tests, sources: [new("a", -1)]), rules).Single(i => i.Code == "model.source");
            Assert(issue.Severity == IssueSeverity.Warning && issue.Message == "检查热源 a", "model check ignored configured diagnostics");
        });

        tests.Case("generation", "independent input errors retain paths without changing submitted values", () =>
        {
            var definition = tests.Catalog.Load("bare_die");
            var document = tests.Create(definition);
            document.Values["die.length"] = "invalid";
            document.Values["die.power"] = -1;
            document.MaterialAssignments["group-die"] = "";
            var submitted = document.Values.DeepClone();
            InputValidator.Validate(document, definition, tests.Catalog.Materials, tests.Catalog.LoadValidation(document.TemplateId));
            Assert(JToken.DeepEquals(submitted, document.Values), "input validator changed submitted values");
            var result = tests.GenerateResult(document);
            Assert(result.Model == null && !result.CanPreview && !result.CanExport, "invalid input published a model");
            Assert(result.Issues.Any(i => i.Stage == ValidationStage.Input && i.ParameterPaths.Contains("die.length")), "missing type error path");
            Assert(result.Issues.Any(i => i.Stage == ValidationStage.Input && i.ParameterPaths.Contains("die.power")), "independent power error was not reported");
            Assert(result.Issues.Any(i => i.Stage == ValidationStage.Input && i.ParameterPaths.Contains("MaterialAssignments.group-die")), "empty required material did not produce an input issue");
            Assert(JToken.DeepEquals(submitted, document.Values), "validation or generation changed submitted input");
        });

        tests.Case("generation", "malformed enum and ball map cells return input issues", () =>
        {
            foreach (var (key, value, expectedPath) in new (string, JToken, string)[]
            {
                ("vias.modeling", new JArray(), "vias.modeling"),
                ("bga.representation", new JArray(), "bga.representation"),
                ("bga.ball_map", new JArray(new JObject { ["id"] = new JArray(), ["x"] = 0, ["y"] = 0 }), "bga.ball_map[0].id")
            })
            {
                var document = tests.Create(tests.Catalog.Load("chip_array"));
                document.Values["vias.enabled"] = true;
                document.Values["bga.ball_map_enabled"] = true;
                document.Values[key] = value;
                var result = tests.GenerateResult(document);
                Assert(result.Model == null && result.Issues.Any(i => i.Stage == ValidationStage.Input && i.ParameterPaths.Contains(expectedPath)), "malformed field escaped structured validation: " + key);
            }
        });

        tests.Case("generation", "post validation errors allow safe problem preview and block export", () =>
        {
            var model = Model(tests, sources: [new("a", -1)]);
            var result = tests.Result(model);
            Assert(result.HasErrors && result.CanPreview && !result.CanExport, "source error did not preserve safe geometry preview");
            Assert(result.Issues.Any(i => i.Code == "model.source" && i.EntityIds.Contains("a")), "source issue has no entity target");
            Reject(() => FloXmlExporter.Export(result));
            Assert(model.Sources.Single().Power == -1, "model validation repaired a source");
        });

        tests.Case("generation", "filled vias ignore plating and missing removal counts are input issues", () =>
        {
            var document = tests.Create(tests.Catalog.Load("chip_array"));
            document.Values["vias.enabled"] = true;
            document.Values["vias.filled"] = true;
            foreach (JToken plating in new JToken[] { new JValue(-1), new JArray() })
            {
                document.Values["vias.plating"] = plating;
                Assert(tests.GenerateResult(document).CanExport, "inactive plating blocked filled vias");
            }
            document.Values["bga.solder_removal_enabled"] = true;
            document.Values["bga.omitted_cells"] = new JArray();
            document.Values["bga.populated_rows"] = document.Values["bga.populated_columns"] = JValue.CreateNull();
            document.Values["bga.removal_rows"] = document.Values["bga.removal_columns"] = JValue.CreateNull();
            var result = tests.GenerateResult(document);
            Assert(result.Model == null && result.Issues.Any(i => i.Stage == ValidationStage.Input && i.ParameterPaths.Contains("bga.removal_rows")), "missing removal counts reached the generator");
        });

        tests.Case("generation", "invalid geometry is withheld from preview", () =>
        {
            var model = Model(tests, [Cube("a", new(double.NaN, 0, 0))]);
            var result = tests.Result(model);
            Assert(result.HasErrors && !result.CanPreview && !result.CanExport, "nonfinite coordinates reached the preview");
            Assert(result.Issues.Any(i => i.Code == "model.geometry" && i.EntityIds.Contains("a")), "geometry issue has no entity target");
        });

        tests.Case("generation", "overlap warnings identify both entities and remain exportable", () =>
        {
            var blocks = new List<Block> { Cube("a", new(0, 0, 0)), Cube("b", new(0.5, 0, 0)) };
            var model = Model(tests, blocks);
            var first = tests.Result(model);
            var second = tests.Result(model);
            var overlap = first.Issues.Single(i => i.EntityIds.Count == 2);
            Assert(overlap.Stage == ValidationStage.Model && overlap.Severity == IssueSeverity.Warning &&
                overlap.EntityIds.ToHashSet().SetEquals(new[] { "a", "b" }), "overlap did not identify the block pair");
            Assert(first.CanPreview && first.CanExport && !first.HasErrors, "overlap warning blocked output");
            Assert(FloXmlExporter.Export(first).Descendants("cuboid").Count() == 2, "warning model did not export");
            Assert(second.Issues.Count == first.Issues.Count && model.Blocks.SequenceEqual(blocks), "validation changed model state or accumulated issues");
            blocks.Clear();
            Assert(model.Blocks.Count == 2, "published model retained a mutable construction collection");
        });

        tests.Case("generation", "coplanar contact has no positive volume overlap", () =>
        {
            var model = Model(tests, [Cube("a", new(0, 0, 0)), Cube("b", new(1, 0, 0))]);
            Assert(!tests.Result(model).Issues.Any(i => i.EntityIds.Count == 2), "coplanar contact counted as an overlap");
        });

        tests.Case("generation", "explicit orthotropic type remains orthotropic for equal axes", () =>
        {
            var document = tests.Create(tests.Catalog.Load("bare_die"));
            document.CustomMaterials.Add(new("silicon", "Custom silicon", new(12, 12, 12), 2000, 700,
                ConductivityCoefficient: double.PositiveInfinity, ReferenceTemperature: double.NaN, ConductType: 2));
            var result = tests.GenerateResult(document);
            Assert(result.CanExport, string.Join(" ", result.Issues.Select(i => i.Message)));
            var xml = FloXmlExporter.Export(result);
            Assert(xml.Descendants("orthotropic_material_att").Single().Element("name")!.Value == "silicon", "equal axes overrode the explicit orthotropic type");
            Assert(!xml.Descendants("isotropic_material_att").Any(), "orthotropic material was inferred as isotropic");
        });

        tests.Case("generation", "isotropic modeling ignores inactive directional storage", () =>
        {
            foreach (int type in new[] { 0, 1 })
            {
                var document = tests.Create(tests.Catalog.Load("bare_die"));
                document.Values["bumps.enabled"] = true;
                var material = new Material("underfill", "Custom underfill", new(0.7, double.NaN, double.PositiveInfinity), 1200, 800,
                    ConductivityCoefficient: type == 1 ? -0.42 : double.NaN, ReferenceTemperature: type == 1 ? -20 : double.PositiveInfinity, ConductType: type);
                document.CustomMaterials.Add(material);
                var result = tests.GenerateResult(document);
                Assert(result.CanExport, string.Join(" ", result.Issues.Select(i => i.Message)));
                var equivalent = result.Model!.Materials["flip-chip-bumps-equivalent"];
                Assert(equivalent.EffectiveConductivity.Components.All(double.IsFinite), "inactive directions entered the material calculation");
                document.CustomMaterials[0] = material with { Conductivity = new(0.7, 0.7, 0.7) };
                var reference = tests.Generate(document).Materials[equivalent.Id];
                Near(equivalent.Conductivity.X, reference.Conductivity.X, "effective isotropic conductivity");
                Assert(double.IsNaN(material.Conductivity.Y), "generation changed inactive submitted storage");
            }
        });
    }

    static Block Cube(string id, Vector origin) => new(id, id, "die", origin, new(1, 1, 1), "silicon", "group-die", "Die");

    static PackageModel Model(TestSuite tests, IEnumerable<Block>? blocks = null, IEnumerable<HeatSource>? sources = null)
        => new("bare_die", "validation", new(new(new(2, 2), new(2, 2), new(2, 2), new(2, 2), 1, false)), tests.Catalog.Groups,
            blocks ?? [Cube("a", new(0, 0, 0))], new Dictionary<string, Material> { ["silicon"] = tests.Catalog.Materials.Items["silicon"] }, sources ?? [], []);
}
