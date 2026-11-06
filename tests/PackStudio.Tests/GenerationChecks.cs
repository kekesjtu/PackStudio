using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static TestSuite;

static class GenerationChecks
{
    public static void Run(TestSuite tests)
    {
        tests.Case("generation", "field diagnostics use DES symbols and preserve internal paths", () =>
        {
            var original = tests.Catalog.Load("bare_die");
            var data = (JObject)original.Data.DeepClone();
            var field = data["keys"]!.Single(f => f["key"].Text() == "die.length");
            field["label"] = "芯片整体长度";
            field["des_symbol"] = "Ld_test";
            var definition = new PackageDefinition(original.Info, data, original.Presets);
            var document = tests.Create(definition);
            foreach (var (value, code) in new (JToken, string)[]
            {
                (new JValue("invalid"), "input.type.number"),
                (JValue.CreateNull(), "input.required"),
                (new JValue(-1), "input.range")
            })
            {
                document.Values["die.length"] = value;
                var issue = InputValidator.Validate(document, definition, tests.Catalog.Materials).Single(i => i.Code == code);
                Assert(issue.Message.StartsWith("Ld_test：") && !issue.Message.Contains("die.length") && !issue.Message.Contains("芯片整体长度"),
                    "diagnostic did not prefer the DES symbol");
                Assert(issue.ParameterPaths.SequenceEqual(new[] { "die.length" }), "display labels changed the navigation path");
            }
        });

        tests.Case("generation", "diagnostics resolve DES symbol branches and fall back without exposing keys", () =>
        {
            var original = tests.Catalog.Load("bare_die");
            var data = (JObject)original.Data.DeepClone();
            var field = data["keys"]!.Single(f => f["key"].Text() == "die.length");
            field["label"] = "芯片长度";
            field["des_symbol"] = new JObject { ["selector"] = "variant", ["cases"] = new JObject { ["A"] = "La", ["B"] = "Lb" } };
            var definition = new PackageDefinition(original.Info, data, original.Presets);
            var document = tests.Create(definition);
            document.Values["die.length"] = -1;
            foreach (var (variant, expected) in new (JToken, string)[] { (new JValue("A"), "La"), (new JValue("B"), "Lb"), (new JArray("B"), "芯片长度") })
            {
                document.Values["variant"] = variant;
                var issue = InputValidator.Validate(document, definition, tests.Catalog.Materials).Single(i => i.Code == "input.range");
                Assert(issue.Message.StartsWith(expected + "：") && !issue.Message.Contains("die.length"), "symbol branch or fallback was incorrect");
            }
        });

        tests.Case("generation", "nested diagnostics use parent context and child DES symbols", () =>
        {
            var original = tests.Catalog.Load("pbga_wb");
            var data = (JObject)original.Data.DeepClone();
            var field = data["keys"]!.Single(f => f["key"].Text() == "vias.configuration");
            field["label"] = "通孔配置";
            var child = field["keys"]!.Single(f => f["key"].Text() == "removal_rows");
            child["label"] = "去除行数";
            child["des_symbol"] = "Rv";
            var definition = new PackageDefinition(original.Info, data, original.Presets);
            var document = tests.Create(definition);
            document.Values["vias.enabled"] = true;
            document.Values["vias.configuration"]!["removal_enabled"] = true;
            document.Values["vias.configuration"]!["removal_rows"] = "invalid";
            var issue = InputValidator.Validate(document, definition, tests.Catalog.Materials)
                .Single(i => i.Code == "input.type.number" && i.ParameterPaths.Contains("vias.configuration.removal_rows"));
            Assert(issue.Message == "通孔配置 · Rv：必须为数值。", "nested diagnostic did not resolve its symbol");
        });

        tests.Case("generation", "table structural diagnostics show labels and human row numbers", () =>
        {
            var definition = tests.Catalog.Load("chip_array");
            var document = tests.Create(definition);
            document.Values["metal.layers"] = new JArray(new JValue(0), new JObject { ["unknown"] = 1 });
            var issues = InputValidator.Validate(document, definition, tests.Catalog.Materials);
            foreach (string code in new[] { "input.row", "input.row.columns" })
            {
                var issue = issues.Single(i => i.Code == code);
                Assert(!issue.Message.Contains("metal.layers") && issue.Message.Contains(code == "input.row" ? "第 1 行" : "第 2 行"),
                    "table structure error exposed a machine path or zero-based row number");
            }
            document.Values["metal.layers"] = new JArray();
            var count = InputValidator.Validate(document, definition, tests.Catalog.Materials).Single(i => i.Code == "input.rows");
            Assert(!count.Message.Contains("metal.layers") && count.Message.Contains("行数"), "table count error exposed its key");
        });

        tests.Case("generation", "family relations are blocking C# checks with field paths", () =>
        {
            var definition = tests.Catalog.Load("qfn");
            var document = tests.Create(definition);
            document.Values["die.length"] = document.Values["package.length"]!.Value<double>() + 0.01;
            var result = tests.GenerateResult(document);
            var fit = result.Issues.Single(i => i.Code == "input.package.fit");
            Assert(result.Model == null && fit.Stage == ValidationStage.Input && fit.Severity == IssueSeverity.Error,
                "invalid family relation entered modeling");
            Assert(fit.ParameterPaths.Contains("die.length") && fit.ParameterPaths.Contains("package.length") && !string.IsNullOrWhiteSpace(fit.Message),
                "family relation lost diagnostics");
            Assert(fit.Message.StartsWith("Ld、D：") && !fit.Message.Contains("die.length") && !fit.Message.Contains("package.length"),
                "relation diagnostics did not identify the participating DES symbols");
        });

        tests.Case("generation", "field bounds are read from the parameter definition", () =>
        {
            var original = tests.Catalog.Load("bare_die");
            var data = (JObject)original.Data.DeepClone();
            var field = data["keys"]!.Single(f => f["key"].Text() == "die.power");
            field["maximum"] = 5;
            var definition = new PackageDefinition(original.Info, data, original.Presets);
            var document = tests.Create(definition);
            document.Values["die.power"] = 6;
            var issue = InputValidator.Validate(document, definition, tests.Catalog.Materials).Single(i => i.Code == "input.range");
            Assert(issue.Severity == IssueSeverity.Error && issue.ParameterPaths.SequenceEqual(new[] { "die.power" }),
                "field bound ignored the definition");
            document.Values["die.power"] = 5;
            Assert(!InputValidator.Validate(document, definition, tests.Catalog.Materials).Any(i => i.Code == "input.range"),
                "inclusive bound rejected its endpoint");
        });

        tests.Case("generation", "SOP odd lead count is reported once before modeling", () =>
        {
            var document = tests.Create(tests.Catalog.Load("sop"));
            document.Values["leads.total"] = 21;
            var result = tests.GenerateResult(document);
            Assert(result.Model == null && result.Issues.Count(i => i.ParameterPaths.Contains("leads.total")) == 1, "lead count was validated more than once");
            Assert(result.Issues.Single(i => i.ParameterPaths.Contains("leads.total")).Code == "input.sop.leads", "lead count bypassed the family check");
        });

        tests.Case("generation", "SOP lead row leaves positive inner lead length", () =>
        {
            var document = tests.Create(tests.Catalog.Load("sop"));
            document.Values["leads.total"] = 2;
            var result = tests.GenerateResult(document);
            Assert(result.Model == null && result.Issues.Any(i => i.Code == "input.sop.lead_span" &&
                i.ParameterPaths.Contains("leads.total")), "short lead row escaped input validation");
        });

        tests.Case("generation", "WB PBGA mold covers the die stack and wire ends", () =>
        {
            var document = tests.Create(tests.Catalog.Load("pbga_wb"));
            var values = document.Values;
            double stack = values["solder_mask.thickness"].Number() + values["die.attach"].Number() + values["die.thickness"].Number();
            values["encapsulant.thickness"] = stack;
            values["encapsulant.length"] = values["bond_wire.extent_length"]!.DeepClone();
            tests.Generate(document);
            values["encapsulant.thickness"] = stack - 0.01;
            values["encapsulant.length"] = values["bond_wire.extent_length"].Number() - 0.01;
            var result = tests.GenerateResult(document);
            Assert(result.Model == null && result.Issues.Any(i => i.Code == "input.encapsulant.stack" && i.ParameterPaths.Contains("die.attach")),
                "short mold escaped vertical input validation");
            Assert(result.Issues.Any(i => i.Code == "input.package.fit" && i.ParameterPaths.Contains("bond_wire.extent_length")),
                "wire ends escaped lateral input validation");
        });

        tests.Case("generation", "FC PBGA metal layers fit their own build-up region", () =>
        {
            var document = tests.Create(tests.Catalog.Load("pbga_fc"));
            var values = document.Values;
            double board = values["substrate.thickness"].Number();
            foreach (string region in new[] { "upper", "lower" })
            {
                values[region + ".enabled"] = true;
                values[region + ".thickness"] = 0.2;
                var row = new JObject { ["depth"] = region == "upper" ? 0.1 : board - 0.2,
                    ["thickness"] = 0.1, ["coverage"] = 50, ["disconnect"] = false };
                values[region + ".layers"] = new JArray(row);
                tests.Generate(document);
                row["thickness"] = -0.01;
                CheckLayer("input.range", "thickness");
                row["thickness"] = 0.1;
                row["depth"] = region == "upper" ? 0.15 : board - 0.25;
                CheckLayer("input.metal.build_up", "depth");
                values[region + ".enabled"] = false;

                void CheckLayer(string code, string column)
                {
                    var result = tests.GenerateResult(document);
                    Assert(result.Model == null && result.Issues.Any(i => i.Code == code && i.Stage == ValidationStage.Input &&
                        i.ParameterPaths.Contains(region + ".layers[0]." + column)), region + " layer issue lost its cell");
                }
            }
        });

        tests.Case("generation", "derived geometry relations are input errors with field paths", () =>
        {
            var pqfp = tests.Create(tests.Catalog.Load("pqfp"));
            pqfp.Values["flag.length"] = pqfp.Values["body.length"]!.DeepClone();
            var tieBar = tests.GenerateResult(pqfp);
            var issue = tieBar.Issues.Single(i => i.Code == "input.leadframe.gap");
            Assert(tieBar.Model == null && issue.Stage == ValidationStage.Input && issue.ParameterPaths.Contains("flag.length") && issue.ParameterPaths.Contains("body.length"),
                "tie bar relation entered modeling");

            var bga = tests.Create(tests.Catalog.Load("cbga_fc"));
            bga.Values["bga.solder_removal_enabled"] = true;
            bga.Values["bga.removal_rows"] = 6;
            bga.Values["bga.removal_columns"] = 6;
            bga.Values["bga.diameter"] = 0.3;
            var border = tests.GenerateResult(bga);
            Assert(border.Model == null && border.Issues.Single(i => i.Code == "input.bga.border").ParameterPaths.Contains("bga.removal_rows"),
                "equivalent solder ball border reached modeling");

            var sop = tests.Create(tests.Catalog.Load("sop"));
            sop.Values["die.length"] = sop.Values["die.width"] = 0.2;
            sop.Values["bond_wire.count"] = 200;
            var wire = tests.GenerateResult(sop);
            Assert(wire.Model == null && wire.Issues.Single(i => i.Code == "input.wire.fraction").ParameterPaths.Contains("bond_wire.count"),
                "bond wire volume fraction reached modeling");

            var array = tests.Create(tests.Catalog.Load("chip_array"));
            array.Values["vias.enabled"] = true;
            array.Values["vias.filled"] = true;
            array.Values["vias.modeling"] = "approximate";
            array.Values["vias.diameter"] = 0.8;
            array.Values["vias.pitch"] = 1.0;
            var via = tests.GenerateResult(array);
            Assert(via.Model == null && via.Issues.Single(i => i.Code == "input.chip_array.via").ParameterPaths.Contains("vias.diameter"),
                "approximate via fraction reached modeling");
        });

        foreach (string family in new[] { "pbga_fc", "pbga_wb", "chip_array" })
            tests.Case("generation", family + " table bounds locate invalid layer thickness before modeling", () =>
            {
                var document = tests.Create(tests.Catalog.Load(family));
                var layers = (JArray)document.Values["metal.layers"]!;
                if (layers.Count == 0)
                    layers.Add(new JObject { ["depth"] = 0, ["thickness"] = 0.018, ["coverage"] = 50, ["disconnect"] = false });
                layers[0]!["thickness"] = 0;
                var result = tests.GenerateResult(document);
                Assert(result.Model == null && result.Issues.Any(i => i.Code == "input.range" &&
                    i.Stage == ValidationStage.Input && i.ParameterPaths.Contains("metal.layers[0].thickness")),
                    "strictly positive table constraint did not locate the invalid cell");
                var issue = result.Issues.Single(i => i.Code == "input.range" && i.ParameterPaths.Contains("metal.layers[0].thickness"));
                Assert(issue.Message.Contains("第 1 行") && issue.Message.Contains("层厚") && !issue.Message.Contains("metal.layers"),
                    "table cell error lost its row/column label");
            });

        tests.Case("generation", "invalid model sources always block export", () =>
        {
            var model = Model(tests, sources: [new("a", -1)]);
            var issue = ModelValidator.Validate(model).Single(i => i.Code == "model.source");
            Assert(issue.Severity == IssueSeverity.Error && issue.Stage == ValidationStage.Model && issue.EntityIds.Contains("a"),
                "invalid source lost its blocking diagnostic");
            Assert(!tests.Result(model).CanExport, "invalid source was exportable");
        });

        tests.Case("generation", "model power must match the submitted power", () =>
        {
            var model = Model(tests, sources: [new("a", 2)]);
            Assert(!ModelValidator.Validate(model, expectedPower: 2).Any(i => i.Code == "model.power"), "matching power was rejected");
            Assert(ModelValidator.Validate(model, expectedPower: 4).Any(i => i.Code == "model.power" && i.Severity == IssueSeverity.Error),
                "lost power was accepted");
        });

        tests.Case("generation", "generated material validation follows the final material source", () =>
        {
            var document = tests.Create(tests.Catalog.Load("cbga_fc"));
            var catalog = tests.Catalog.Materials.Items;
            var solder = catalog[document.MaterialAssignments["group-bga-solder"]];
            document.CustomMaterials.Add(solder with { Density = 0 });
            document.CustomMaterials.Add(catalog["static-air"] with { Density = 0 });
            var invalid = tests.GenerateResult(document);
            Assert(!invalid.CanExport && invalid.Issues.Any(i => i.Code == "model.material" && i.EntityIds.Contains("solder-ball-part-1")),
                "invalid calculated material was not checked");
            document.CustomMaterials.Add(solder with { Id = "solder-ball-equivalent" });
            Assert(tests.GenerateResult(document).CanExport, "valid custom override did not replace the calculated material");
        });

        foreach (string family in new[] { "cbga_fc", "pbga_fc", "pbga_wb", "chip_array" })
            tests.Case("generation", family + " shares solder ball checks", () =>
            {
                var document = tests.Create(tests.Catalog.Load(family));
                document.Values["bga.diameter"] = 0.6;
                document.Values["bga.pitch"] = 0.5;
                var result = tests.GenerateResult(document);
                Assert(result.Model == null && result.Issues.Count(i => i.Code == "input.bga.pitch") == 1,
                    "family did not call its shared solder ball check exactly once");
            });

        tests.Case("generation", "invalid fields suppress dependent relations but preserve independent errors", () =>
        {
            var document = tests.Create(tests.Catalog.Load("sop"));
            document.Values["leads.total"] = "odd";
            document.Values["die.power"] = -1;
            var result = tests.GenerateResult(document);
            Assert(result.Model == null && result.Issues.Any(i => i.ParameterPaths.Contains("leads.total")) &&
                result.Issues.Any(i => i.ParameterPaths.Contains("die.power")), "independent field errors were lost");
            Assert(!result.Issues.Any(i => i.Code == "input.sop.leads"), "invalid field produced a dependent relation error");
        });

        tests.Case("generation", "independent input errors retain paths without changing submitted values", () =>
        {
            var definition = tests.Catalog.Load("bare_die");
            var document = tests.Create(definition);
            document.Values["die.length"] = "invalid";
            document.Values["die.power"] = -1;
            document.MaterialAssignments["group-die"] = "";
            var submitted = document.Values.DeepClone();
            InputValidator.Validate(document, definition, tests.Catalog.Materials);
            Assert(JToken.DeepEquals(submitted, document.Values), "input validator changed submitted values");
            var result = tests.GenerateResult(document);
            Assert(result.Model == null && !result.CanPreview && !result.CanExport, "invalid input published a model");
            Assert(result.Issues.Any(i => i.Stage == ValidationStage.Input && i.ParameterPaths.Contains("die.length")), "missing type error path");
            Assert(result.Issues.Any(i => i.Stage == ValidationStage.Input && i.ParameterPaths.Contains("die.power")), "independent power error was not reported");
            Assert(result.Issues.Any(i => i.Stage == ValidationStage.Input && i.ParameterPaths.Contains("MaterialAssignments.group-die")), "empty required material did not produce an input issue");
            var materialIssue = result.Issues.Single(i => i.ParameterPaths.Contains("MaterialAssignments.group-die"));
            Assert(materialIssue.Message.Contains("芯片材料") && !materialIssue.Message.Contains("group-die") && !materialIssue.Message.Contains("MaterialAssignments"),
                "material choice error exposed its internal path");
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
            Reject(() => ModelXmlExporter.Export(result));
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
            Assert(ModelXmlExporter.Export(first).Descendants("block").Count() == 2, "warning model did not export");
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
            var xml = ModelXmlExporter.Export(result);
            Assert((string?)xml.Root!.Element("materials")!.Element("material")!.Attribute("type") == "orthotropic", "equal axes overrode the explicit orthotropic type");
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
            blocks ?? [Cube("a", new(0, 0, 0))], new Dictionary<string, Material> { ["silicon"] = tests.Catalog.Materials.Items["silicon"] }, sources ?? []);
}
