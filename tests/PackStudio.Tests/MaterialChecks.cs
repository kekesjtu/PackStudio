using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static TestSuite;

static class MaterialChecks
{
    public static void Run(TestSuite tests)
    {
        tests.Case("materials", "omitted options offer library and custom materials with matching validation", () =>
        {
            var original = tests.Catalog.Load("bare_die");
            var data = (JObject)original.Data.DeepClone();
            var slot = (JObject)data["materials"]!.Single(s => s["key"].Text() == "group-bump-solder");
            slot.Remove("options");
            var template = new PackageDefinition(original.Info, data, original.Presets);
            var document = tests.Create(template);
            var custom = tests.Catalog.Materials.Items["copper"] with { Id = "custom-test", Name = "Custom test material" };
            document.CustomMaterials.Add(custom);
            bool Rejected() => InputValidator.Validate(document, template, tests.Catalog.Materials, tests.Catalog.LoadValidation("bare_die"))
                .Any(i => i.Code == "input.material.reference" && i.ParameterPaths.Contains("MaterialAssignments.group-bump-solder"));
            foreach (string id in new[] { "copper", custom.Id })
            {
                document.MaterialAssignments["group-bump-solder"] = id;
                var choices = MaterialSelection.Choices(tests.Catalog.Materials, template, document, slot);
                Assert(choices.SelectedId == id && choices.Items.Any(m => m.Id == id) && !Rejected(), "default material candidates disagree with validation");
            }
            foreach (string id in new[] { "", "unknown-material" })
            {
                document.MaterialAssignments["group-bump-solder"] = id;
                Assert(Rejected(), "default candidates accepted an empty or unknown material");
            }
        });
        tests.Case("materials", "explicit options restrict choices and control empty assignments", () =>
        {
            var original = tests.Catalog.Load("bare_die");
            var data = (JObject)original.Data.DeepClone();
            var slot = data["materials"]!.Single(s => s["key"].Text() == "group-bump-solder");
            slot["options"] = new JArray(new JObject { ["value"] = "solder-pb90" });
            var template = new PackageDefinition(original.Info, data, original.Presets);
            var document = tests.Create(template);
            var choices = MaterialSelection.Choices(tests.Catalog.Materials, template, document, slot);
            Assert(choices.Items.Any(m => m.Id == "solder-pb90") && !choices.Items.Any(m => m.Id == "copper"), "explicit options did not restrict choices");
            bool Rejected() => InputValidator.Validate(document, template, tests.Catalog.Materials, tests.Catalog.LoadValidation("bare_die"))
                .Any(i => i.Code == "input.material.reference" && i.ParameterPaths.Contains("MaterialAssignments.group-bump-solder"));
            document.MaterialAssignments["group-bump-solder"] = "copper";
            Assert(Rejected(), "explicit material restrictions were ignored");
            document.MaterialAssignments["group-bump-solder"] = "";
            Assert(Rejected(), "empty material accepted without an explicit option");
            slot["options"] = new JArray(new JObject { ["value"] = "" }, new JObject { ["value"] = "*" });
            Assert(!Rejected(), "explicit empty material option was ignored");
            document.MaterialAssignments["group-bump-solder"] = "copper";
            Assert(!Rejected(), "wildcard did not allow a library material");
            slot["options"] = new JArray();
            Assert(Rejected(), "an empty option list acted like omitted options");
        });
        tests.Case("materials", "user material assignment wins", () =>
        {
            var document = tests.Create(tests.Catalog.Load("cbga_fc"));
            document.MaterialAssignments["group-substrate"] = "copper";
            var model = tests.Generate(document);
            Assert(model.Blocks.Single(b => b.StructureType == "substrate").MaterialId == "copper", "material assignment not applied");
        });
        tests.Case("materials", "derived material override wins", () =>
        {
            var document = tests.Create(tests.Catalog.Load("bare_die"));
            document.Values["bumps.enabled"] = true;
            var original = tests.Generate(document).Materials["flip-chip-bumps-equivalent"];
            document.CustomMaterials.Add(original with { Conductivity = new(42, 43, 44) });
            Near(tests.Generate(document).Materials[original.Id].Conductivity.X, 42, "derived override");
        });
        tests.Case("materials", "invalid material rejected before generation", () =>
        {
            var document = tests.Create(tests.Catalog.Load("bare_die"));
            document.CustomMaterials.Add(new("x", "x", new(1, 1, 1), -1, 2));
            var result = tests.GenerateResult(document);
            Assert(result.Model == null && result.Issues.Any(i => i.Code == "input.material"), "invalid user material entered modeling");
        });
        tests.Case("materials", "zero properties and signed temperature parameters are allowed", () =>
        {
            var document = tests.Create(tests.Catalog.Load("bare_die"));
            document.CustomMaterials.Add(new("zero", "zero", new(0, 0, 0), 0, 0, ConductivityCoefficient: -0.42, ReferenceTemperature: -20, ConductType: 1));
            tests.Generate(document);
            document.CustomMaterials.Add(new("invalid", "invalid", new(double.NaN, 1, 1), 1, 1));
            Reject(() => tests.Generate(document));
            document.CustomMaterials[^1] = new("invalid", "invalid", new(1, 1, 1), 1, 1, ConductivityCoefficient: double.PositiveInfinity, ConductType: 1);
            Reject(() => tests.Generate(document));
        });
        tests.Case("materials", "flat records select active conductivity fields by type", () =>
        {
            string directory = Path.Combine(tests.Root, "tmp", DateTime.Now.ToString("yyyy-MM-dd") + "-core-tests", "material-records-" + Guid.NewGuid().ToString("N"));
            string materials = Path.Combine(directory, "materials");
            Directory.CreateDirectory(materials);
            try
            {
                var index = new JObject();
                foreach (int type in new[] { 0, 1, 2 })
                {
                    string id = "material-" + type;
                    var record = new JObject
                    {
                        ["name"] = id, ["group"] = "Test", ["density_kg_m3"] = 10,
                        ["specific_heat_j_kg_k"] = 20, ["conductivity_w_m_k"] = 78.4,
                        ["conductivity_coefficient"] = -0.42, ["conductivity_reference_temperature"] = -20,
                        ["kx_w_m_k"] = 1, ["ky_w_m_k"] = 2, ["kz_w_m_k"] = 3, ["conduct_type"] = type
                    };
                    File.WriteAllText(Path.Combine(materials, id + ".json"), record.ToString());
                    index[id] = new JObject { ["file"] = id + ".json" };
                }
                File.WriteAllText(Path.Combine(materials, "index.json"), new JObject { ["materials"] = index }.ToString());
                File.WriteAllText(Path.Combine(materials, "runtime.json"), new JObject { ["aliases"] = new JObject(), ["project_materials"] = new JArray() }.ToString());
                var library = new MaterialCatalogReader().Read(directory, tests.Catalog.LoadValidation("bare_die"));
                var constant = library.Items["material-0"];
                var temperature = library.Items["material-1"];
                var orthotropic = library.Items["material-2"];
                Assert(constant.Conductivity == new Vector(78.4, 78.4, 78.4) && constant.ConductType == 0 && constant.ConductivityCoefficient == -0.42, "constant material lost stored inactive fields");
                Assert(temperature.Conductivity == constant.Conductivity && temperature.ConductivityCoefficient == -0.42 && temperature.ReferenceTemperature == -20, "temperature model not preserved");
                Assert(orthotropic.Conductivity == new Vector(1, 2, 3) && orthotropic.ConductType == 2 && orthotropic.StoredScalarConductivity == 78.4, "orthotropic material lost its inactive scalar");
                Assert(orthotropic.Category == "Test", "material group not mapped");
                var blocks = library.Items.Values.Select((material, index) => new Block(material.Id, material.Name, "die", new(index * 2, 0, 0), new(1, 1, 1), material.Id, "group-die", "Die"));
                var model = new PackageModel("bare_die", "test", new ModelMetadata(new PackageGeometry(new(1, 1), new(1, 1), new(1, 1), new(1, 1), 1, false)), tests.Catalog.Groups,
                    blocks, library.Items, [], []);
                var exported = tests.Export(model);
                Assert(exported.Descendants("isotropic_material_att").Single().Element("name")!.Value == constant.Id, "constant material exported as temperature dependent");
                var temperatureXml = exported.Descendants("temperature_dependant_material_att").Single();
                Near(double.Parse(temperatureXml.Element("coeff")!.Value, System.Globalization.CultureInfo.InvariantCulture), -0.42, "signed temperature coefficient");
                Near(double.Parse(temperatureXml.Element("tref")!.Value, System.Globalization.CultureInfo.InvariantCulture), 253.15, "reference temperature conversion");
                Assert(exported.Descendants("orthotropic_material_att").Single().Element("name")!.Value == orthotropic.Id, "orthotropic material export lost");
            }
            finally { Directory.Delete(directory, true); }
        });
        tests.Case("materials", "generation does not reread preset material assignments", () =>
        {
            var template = tests.Catalog.Load("pbga_wb");
            var preset = template.Presets.Single(p => p.Name == template.DefaultPreset);
            var document = tests.Create(template);
            string original = preset.MaterialAssignments["group-encapsulant"];
            try
            {
                preset.MaterialAssignments["group-encapsulant"] = "copper";
                var model = tests.Generate(document);
                Assert(model.Blocks.Single(b => b.StructureType == "encapsulant").MaterialId == original, "preset changes altered existing document materials");
            }
            finally { preset.MaterialAssignments["group-encapsulant"] = original; }
        });
        tests.Case("materials", "FC via matrix retains isotropic conductivity", () =>
        {
            var document = tests.Create(tests.Catalog.Load("pbga_fc"));
            var values = document.Values;
            values["vias.enabled"] = true;
            values["vias.modeling"] = "equivalent";
            values["vias.rows"] = 4; values["vias.columns"] = 3;
            values["vias.pitch"] = 0.5; values["vias.diameter"] = 0.2; values["vias.plating"] = 0.025;
            var matrix = tests.Generate(document).Materials["fc-core-via"];
            Assert(matrix.Conductivity.X > 0 && matrix.Conductivity.Y > 0, "matrix conductivity lost");
        });
    }
}
