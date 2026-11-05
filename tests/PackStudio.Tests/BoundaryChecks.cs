using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static TestSuite;

static class BoundaryChecks
{
    public static void Run(TestSuite tests)
    {
        tests.Case("parameters", "creation preserves explicit tables and nested input", () =>
        {
            var template = tests.Catalog.Load("chip_array");
            double explicitHeight = template.DisplayDefaults(template.DefaultPreset)["substrate.thickness"].Number();
            var options = new JObject { ["substrate.thickness"] = explicitHeight, ["substrate.layers"] = "4-Layer" };
            var baseline = tests.Create(template, options: options);
            Near(baseline.Values["substrate.thickness"].Number(), explicitHeight, "equal-to-default user input lost during branch selection");
            var table = (JArray)baseline.Values["metal.layers"]!.DeepClone();
            table[0]!["thickness"] = 0.03;
            options["metal.layers"] = table;
            options["trace.solid_thickness"] = 0.05;
            options["vias.configuration/removal_enabled"] = false;
            var document = tests.Create(template, name: "explicit table", options: options);
            Near(document.Values["metal.layers"]![0]!["thickness"].Number(), 0.03, "finalization replaced explicit table");
            Near(document.Values["metal.layers"]![1]!["thickness"].Number(), table[1]!["thickness"].Number(), "finalization recomputed explicit inner layers");
            Assert(document.Values["vias.configuration"]!["removal_enabled"]?.Type == JTokenType.Boolean, "nested override path was not applied");
            tests.Generate(document);
        });
        tests.Case("materials", "all material views use the same representative", () =>
        {
            var template = tests.Catalog.Load("cbga_fc");
            var document = tests.Create(template);
            document.MaterialAssignments["group-substrate"] = "copper";
            var model = tests.Generate(document);
            var custom = tests.Catalog.Materials.Items["copper"] with { Density = 1234 };
            document.CustomMaterials.Add(custom with { Id = "custom-copper", Density = 2345 });
            document.CustomMaterials.Add(custom);
            var selection = template.MaterialSelections.Single(s => s["key"].Text() == "group-substrate");
            var dropdown = MaterialSelection.Choices(tests.Catalog.Materials, template, document, selection, model);
            var library = MaterialSelection.Available(tests.Catalog.Materials, template, document, model);
            Assert(dropdown.SelectedId == custom.Id, "assigned material representative did not win");
            Near(dropdown.Items.Single(m => m.Name == custom.Name).Density, 1234, "custom properties did not override model/library");
            Assert(dropdown.Items.Single(m => m.Name == custom.Name) == library.Single(m => m.Name == custom.Name), "dropdown and library disagree");
        });
        tests.Case("catalog", "surface annotation survives block rename", () =>
        {
            var model = tests.Generate(tests.Create(tests.Catalog.Load("cbga_fc")));
            var blocks = model.Blocks.Select(b => b.GroupId == "group-substrate" ? b with { Id = "renamed-board", Name = "Board" } : b);
            model = new(model.TemplateId, model.Name, model.Metadata, model.Groups, blocks, model.Materials, model.Sources, model.Auxiliary);
            var cuboid = tests.Export(model).Descendants("cuboid").Single(b => (string?)b.Element("name") == "renamed-board");
            Assert(cuboid.Element("all_surface") != null && cuboid.Element("all_radiation") != null, "surface depended on ID text");
        });
        tests.Case("projects", "v2 migration stays at file boundary and preserves saved geometry", () =>
        {
            string directory = Path.Combine(tests.Root, "tmp", DateTime.Now.ToString("yyyy-MM-dd") + "-core-tests");
            Directory.CreateDirectory(directory);
            string path = Path.Combine(directory, "legacy-project.packstudio.json");
            try
            {
                var template = tests.Catalog.Load("pbga_wb");
                var document = tests.Create(template);
                document.Values["metal.layers"]![0]!["thickness"] = 0.03;
                var data = JObject.FromObject(document);
                data["SchemaVersion"] = "packstudio.project/v2";
                data["PresetId"] = template.DefaultPreset;
                data["MaterialAssignments"] = new JObject { ["group-encapsulant"] = "copper" };
                var values = (JObject)data["Values"]!;
                values["footprint.size"] = template.DefaultPreset;
                values["bga.via_configuration"] = new JObject { ["removal_enabled"] = true, ["removal_rows"] = 1, ["removal_columns"] = 1 };
                values.Property("vias.configuration")!.Remove();
                File.WriteAllText(path, data.ToString());
                var migrated = ProjectStore.Load(path, tests.Catalog);
                Assert(migrated.SchemaVersion == ProjectDocument.CurrentVersion && migrated.Values["bga.via_configuration"] == null, "legacy format leaked into current document");
                Assert(migrated.Values["vias.configuration"]!["removal_enabled"].Flag(), "legacy via configuration lost");
                Near(migrated.Values["metal.layers"]![0]!["thickness"].Number(), 0.03, "migration reinitialized saved geometry");
                Assert(migrated.MaterialAssignments.Count == template.MaterialSelections.Count && migrated.MaterialAssignments["group-encapsulant"] == "copper", "legacy material choices not materialized");
            }
            finally { if (File.Exists(path)) File.Delete(path); }
        });
    }
}
