using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static TestSuite;

static class ProjectChecks
{
    public static void Run(TestSuite tests)
    {
        tests.Case("projects", "clone isolates editable state", () =>
        {
            var document = tests.Create(tests.Catalog.Load("cbga_fc"));
            document.MaterialAssignments["group-substrate"] = "copper";
            document.Values["bga.omitted_cells"] = new JArray(new JObject { ["row"] = 1, ["column"] = 2 });
            var clone = document.Clone();
            clone.MaterialAssignments["group-substrate"] = "alumina";
            clone.Values["bga.omitted_cells"]![0]!["row"] = 3;
            clone.CustomMaterials.Add(tests.Catalog.Materials.Items["copper"]);
            Assert(document.MaterialAssignments["group-substrate"] == "copper", "material assignments shared by clone");
            Assert(document.Values["bga.omitted_cells"]![0]!["row"].Number() == 1, "layout shared by clone");
            Assert(document.CustomMaterials.Count == 0, "custom material list shared by clone");
        });
        tests.Case("projects", "save and load unified format", () =>
        {
            string directory = Environment.GetEnvironmentVariable("PACKSTUDIO_TEST_DIRECTORY") ?? Path.Combine(tests.Root, "tmp", DateTime.Now.ToString("yyyy-MM-dd") + "-core-tests");
            Directory.CreateDirectory(directory);
            string path = Path.Combine(directory, Guid.NewGuid() + ".packstudio.json");
            try
            {
                var document = tests.Create(tests.Catalog.Load("cbga_fc"), name: "中文方案");
                document.MaterialAssignments["group-substrate"] = "copper";
                document.Values["bga.center_solder_enabled"] = false;
                document.Values["bga.center_solder_rows"] = JValue.CreateNull();
                document.CustomMaterials.Add(new Material("custom", "自定义材料", new(1, 2, 3), 1000, 500));
                ProjectStore.Save(document, path);
                var saved = JsonData.Read(path);
                Assert(saved["PresetId"] == null && saved["Values"]?["footprint.size"] == null, "preset fields leaked into saved document");
                var loaded = ProjectStore.Load(path, tests.Catalog);
                Assert(loaded.Name == document.Name && loaded.MaterialAssignments["group-substrate"] == "copper", "current project roundtrip");
                Assert(!loaded.Values["bga.center_solder_enabled"].Flag() && loaded.Values["bga.center_solder_rows"]!.Type == JTokenType.Null, "layout false/null roundtrip");
                Near(loaded.CustomMaterials.Single().Conductivity.Y, 2, "custom material roundtrip");
                var input = JsonData.Read(path);
                input["extra"] = true;
                File.WriteAllText(path, input.ToString());
                bool rejected = false;
                try { ProjectStore.Load(path, tests.Catalog); }
                catch (JsonSerializationException) { rejected = true; }
                Assert(rejected, "unknown project field was silently ignored");
            }
            finally { File.Delete(path); }
        });
        tests.Case("projects", "every built-in preset is directly importable", () =>
        {
            var index = (JObject)JsonData.Read(Path.Combine(tests.Root, "runtime_data", "presets", "index.json"))["presets"]!;
            foreach (var entry in index.Properties())
            {
                string path = Path.Combine(tests.Root, "runtime_data", "presets", entry.Value["file"].Text());
                var imported = ProjectStore.Load(path, tests.Catalog);
                Assert(imported.Name == entry.Name, "preset name differs from catalog selection");
                var template = tests.Catalog.Load(imported.TemplateId);
                Assert(imported.MaterialAssignments.Count == template.MaterialSelections.Count, "preset materials are incomplete");
            }
        });
        tests.Case("projects", "four-layer roundtrip preserves edited geometry and complete materials", () =>
        {
            string directory = Path.Combine(tests.Root, "tmp", DateTime.Now.ToString("yyyy-MM-dd") + "-core-tests");
            Directory.CreateDirectory(directory);
            string path = Path.Combine(directory, "four-layer-roundtrip.packstudio.json");
            try
            {
                var template = tests.Catalog.Load("pbga_wb");
                var document = tests.Create(template, options: new JObject { ["substrate.layers"] = "4-Layer" });
                document.Values["metal.layers"]![0]!["thickness"] = 0.025;
                document.MaterialAssignments["group-encapsulant"] = "copper";
                ProjectStore.Save(document, path);
                var loaded = ProjectStore.Load(path, tests.Catalog);
                Near(loaded.Values["metal.layers"]![0]!["thickness"].Number(), 0.025, "import reran layer initialization");
                var model = tests.Generate(loaded);
                Assert(model.Blocks.Single(b => b.StructureType == "encapsulant").MaterialId == "copper", "saved material choice lost");
                loaded.MaterialAssignments.Remove("group-encapsulant");
                Reject(() => tests.Generate(loaded));
            }
            finally { File.Delete(path); }
        });
        tests.Case("projects", "import preserves invalid and missing inputs for editing", () =>
        {
            string directory = Path.Combine(tests.Root, "tmp", DateTime.Now.ToString("yyyy-MM-dd") + "-core-tests");
            Directory.CreateDirectory(directory);
            string path = Path.Combine(directory, "incomplete-project.packstudio.json");
            try
            {
                var document = tests.Create(tests.Catalog.Load("pbga_wb"), name: "");
                document.Values["die.length"] = JValue.CreateNull();
                document.Values["die.power"] = 0;
                document.Values["grid.enabled"] = false;
                document.Values.Remove("bga.pitch");
                document.Values["metal.layers"]![0]!["thickness"] = 0.025;
                document.MaterialAssignments.Remove("group-encapsulant");
                ProjectStore.Save(document, path);
                var loaded = ProjectStore.Load(path, tests.Catalog);
                Assert(loaded.Name == "" && loaded.Values["die.length"]!.Type == JTokenType.Null, "import rejected or filled invalid input");
                Assert(loaded.Values["bga.pitch"] == null && !loaded.MaterialAssignments.ContainsKey("group-encapsulant"), "import filled missing values");
                Near(loaded.Values["die.power"].Number(), 0, "zero replaced on import");
                Assert(!loaded.Values["grid.enabled"].Flag(), "false replaced on import");
                Near(loaded.Values["metal.layers"]![0]!["thickness"].Number(), 0.025, "import recomputed layer stack");
                var result = tests.GenerateResult(loaded);
                Assert(result.Model == null && result.Issues.Count(i => i.Severity == IssueSeverity.Error) >= 3, "incomplete import bypassed generation checks");
                var choice = tests.Catalog.Load("pbga_wb").MaterialSelections.Single(s => s["key"].Text() == "group-encapsulant");
                Assert(MaterialSelection.Choices(tests.Catalog.Materials, tests.Catalog.Load("pbga_wb"), loaded, choice).Items.Count > 0, "incomplete selection cannot be edited");
            }
            finally { File.Delete(path); }
        });
        tests.Case("projects", "legacy custom conductivity type is migrated at the read boundary", () =>
        {
            string directory = Path.Combine(tests.Root, "tmp", DateTime.Now.ToString("yyyy-MM-dd") + "-core-tests");
            Directory.CreateDirectory(directory);
            string path = Path.Combine(directory, "legacy-materials.packstudio.json");
            try
            {
                var document = tests.Create(tests.Catalog.Load("bare_die"));
                document.CustomMaterials =
                [
                    new("constant", "constant", new(3, 3, 3), 1, 1),
                    new("temperature", "temperature", new(3, 3, 3), 1, 1, ConductivityCoefficient: 0, ReferenceTemperature: -20),
                    new("directional", "directional", new(1, 2, 3), 1, 1),
                    new("explicit", "explicit", new(3, 3, 3), 1, 1, ConductivityCoefficient: -0.4, ConductType: 0)
                ];
                var data = JObject.FromObject(document);
                foreach (var material in ((JArray)data["CustomMaterials"]!).Take(3).Cast<JObject>()) material.Remove("ConductType");
                File.WriteAllText(path, data.ToString());
                var loaded = ProjectStore.Load(path, tests.Catalog);
                Assert(loaded.CustomMaterials.Select(m => m.ConductType).SequenceEqual(new[] { 0, 1, 2, 0 }), "legacy material mapping or explicit type precedence changed");
                Assert(loaded.CustomMaterials[1].ConductivityCoefficient == 0 && loaded.CustomMaterials[1].ReferenceTemperature == -20, "legacy temperature data lost");
                ProjectStore.Save(loaded, path);
                Assert(((JArray)JsonData.Read(path)["CustomMaterials"]!).All(m => m["ConductType"]?.Type == JTokenType.Integer), "save omitted explicit conductivity types");
                foreach (JToken malformed in new JToken[] { JValue.CreateNull(), new JObject { ["Conductivity"] = JValue.CreateNull() } })
                {
                    data["CustomMaterials"] = new JArray(malformed);
                    File.WriteAllText(path, data.ToString());
                    bool rejected = false;
                    try { ProjectStore.Load(path, tests.Catalog); }
                    catch (InvalidDataException) { rejected = true; }
                    Assert(rejected, "malformed material structure entered the editable document");
                }
            }
            finally { File.Delete(path); }
        });
    }
}
