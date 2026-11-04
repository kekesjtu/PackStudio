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
            var document = ProjectDocument.Create(tests.Catalog.Load("cbga_fc"));
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
                var document = ProjectDocument.Create(tests.Catalog.Load("cbga_fc"), name: "中文方案");
                document.MaterialAssignments["group-substrate"] = "copper";
                document.Values["bga.center_solder_enabled"] = false;
                document.Values["bga.center_solder_rows"] = JValue.CreateNull();
                document.CustomMaterials.Add(new Material("custom", "自定义材料", new(1, 2, 3), 1000, 500));
                document.Save(path);
                var saved = JsonData.Read(path);
                Assert(saved["PresetId"] == null && saved["Values"]?["footprint.size"] == null, "preset fields leaked into saved document");
                var loaded = ProjectDocument.Load(path, tests.Catalog);
                Assert(loaded.Name == document.Name && loaded.MaterialAssignments["group-substrate"] == "copper", "current project roundtrip");
                Assert(!loaded.Values["bga.center_solder_enabled"].Flag() && loaded.Values["bga.center_solder_rows"]!.Type == JTokenType.Null, "layout false/null roundtrip");
                Near(loaded.CustomMaterials.Single().Conductivity.Y, 2, "custom material roundtrip");
                var input = JsonData.Read(path);
                input["extra"] = true;
                File.WriteAllText(path, input.ToString());
                bool rejected = false;
                try { ProjectDocument.Load(path, tests.Catalog); }
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
                var imported = ProjectDocument.Load(path, tests.Catalog);
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
                var document = ProjectDocument.Create(template, options: new JObject { ["substrate.layers"] = "4-Layer" });
                document.Values["metal.layers"]![0]!["thickness"] = 0.025;
                document.MaterialAssignments["group-encapsulant"] = "copper";
                document.Save(path);
                var loaded = ProjectDocument.Load(path, tests.Catalog);
                Near(loaded.Values["metal.layers"]![0]!["thickness"].Number(), 0.025, "import reran layer initialization");
                var model = tests.Builder.Generate(loaded);
                Assert(model.Blocks.Single(b => b.StructureType == "encapsulant").MaterialId == "copper", "saved material choice lost");
                loaded.MaterialAssignments.Remove("group-encapsulant");
                Reject(() => tests.Builder.Generate(loaded));
            }
            finally { File.Delete(path); }
        });
    }
}
