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
        tests.Case("projects", "unknown request field rejected", () =>
            Reject(() => RequestDocument.Parse(new JObject { ["template_id"] = "bare_die", ["extra"] = true }, tests.Catalog)));
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
    }
}
