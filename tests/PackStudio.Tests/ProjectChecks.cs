using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static TestSuite;

static class ProjectChecks
{
    public static void Run(TestSuite tests)
    {
        tests.Case("projects", "save and load current and legacy formats", () =>
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
                document.Save(path);
                var loaded = ProjectDocument.Load(path);
                Assert(loaded.Name == document.Name && loaded.MaterialAssignments["group-substrate"] == "copper", "current project roundtrip");
                Assert(!loaded.Values["bga.center_solder_enabled"].Flag() && loaded.Values["bga.center_solder_rows"]!.Type == JTokenType.Null, "layout false/null roundtrip");
                var legacy = new JObject { ["SchemaVersion"] = "packstudio.project/v1", ["TemplateId"] = "bare_die", ["Values"] = new JObject { ["die.length"] = 4.0, ["metal.layers"] = "[]" }, ["Bga"] = new JObject { ["omitted_cells"] = new JArray(new JObject { ["row"] = 1, ["column"] = 2 }) }, ["Assignments"] = new JObject { ["group-die"] = "silicon" } };
                File.WriteAllText(path, legacy.ToString());
                loaded = ProjectDocument.Load(path);
                Assert(loaded.SchemaVersion == "packstudio.project/v2" && loaded.MaterialAssignments["group-die"] == "silicon", "legacy material migration");
                Assert(loaded.Values["metal.layers"] is JArray && loaded.Values["bga.omitted_cells"]![0]!["column"].Number() == 2, "legacy values migration");
            }
            finally { File.Delete(path); }
        });
    }
}
