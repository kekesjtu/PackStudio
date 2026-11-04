using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static TestSuite;

static class BoundaryChecks
{
    public static void Run(TestSuite tests)
    {
        tests.Case("parameters", "creation draft preserves explicit tables through finalization", () =>
        {
            var template = tests.Catalog.Load("chip_array");
            var draft = new CreationDraft(template, template.DefaultPreset);
            draft.Set("substrate.thickness", draft.Values["substrate.thickness"]!);
            double explicitHeight = draft.Values["substrate.thickness"].Number();
            draft.Set("substrate.layers", new JValue("4-Layer"));
            Near(draft.Values["substrate.thickness"].Number(), explicitHeight, "equal-to-default user input lost during branch selection");
            var table = (JArray)draft.Values["metal.layers"]!.DeepClone();
            table[0]!["thickness"] = 0.03;
            draft.Set("metal.layers", table);
            draft.Set("trace.solid_thickness", new JValue(0.05));
            var document = draft.Complete("explicit table");
            Near(document.Values["metal.layers"]![0]!["thickness"].Number(), 0.03, "finalization replaced explicit table");
            Near(document.Values["metal.layers"]![1]!["thickness"].Number(), table[1]!["thickness"].Number(), "finalization recomputed explicit inner layers");
            tests.Builder.Generate(document);
        });
        tests.Case("materials", "all material views use the same representative", () =>
        {
            var template = tests.Catalog.Load("cbga_fc");
            var document = ProjectDocument.Create(template);
            document.MaterialAssignments["group-substrate"] = "copper";
            var model = tests.Builder.Generate(document);
            var custom = tests.Catalog.Materials.Items["copper"] with { Density = 1234 };
            document.CustomMaterials.Add(custom with { Id = "custom-copper", Density = 2345 });
            document.CustomMaterials.Add(custom);
            var selection = template.MaterialSelections.Single(s => s["group_id"].Text() == "group-substrate");
            var dropdown = MaterialSelection.Choices(tests.Catalog, template, document, selection, model);
            var library = MaterialSelection.Available(tests.Catalog, template, document, model);
            Assert(dropdown.SelectedId == custom.Id, "assigned material representative did not win");
            Near(dropdown.Items.Single(m => m.Name == custom.Name).Density, 1234, "custom properties did not override model/library");
            Assert(dropdown.Items.Single(m => m.Name == custom.Name) == library.Single(m => m.Name == custom.Name), "dropdown and library disagree");
        });
        tests.Case("catalog", "surface annotation survives block rename", () =>
        {
            var model = tests.Builder.Generate(ProjectDocument.Create(tests.Catalog.Load("cbga_fc")));
            int index = model.Blocks.FindIndex(b => b.GroupId == "group-substrate");
            model.Blocks[index] = model.Blocks[index] with { Id = "renamed-board", Name = "Board" };
            var cuboid = FloXml.Export(model).Descendants("cuboid").Single(b => (string?)b.Element("name") == "renamed-board");
            Assert(cuboid.Element("all_surface") != null && cuboid.Element("all_radiation") != null, "surface depended on ID text");
        });
        tests.Case("parameters", "symbol mapping declares its selector", () =>
        {
            var field = new JObject { ["des_symbol"] = new JObject { ["selector"] = "variant", ["cases"] = new JObject { ["A"] = "La", ["B"] = "Lb" } } };
            Assert(TemplateSymbols.Resolve(field, new JObject { ["variant"] = "B" }) == "Lb", "symbol selector ignored");
        });
        tests.Case("projects", "v2 migration stays at file boundary and preserves saved geometry", () =>
        {
            string directory = Path.Combine(tests.Root, "tmp", DateTime.Now.ToString("yyyy-MM-dd") + "-core-tests");
            Directory.CreateDirectory(directory);
            string path = Path.Combine(directory, "legacy-project.packstudio.json");
            try
            {
                var template = tests.Catalog.Load("pbga_wb");
                var document = ProjectDocument.Create(template);
                document.Values["metal.layers"]![0]!["thickness"] = 0.03;
                var data = JObject.FromObject(document);
                data["SchemaVersion"] = "packstudio.project/v2";
                var values = (JObject)data["Values"]!;
                values["bga.via_configuration"] = new JObject { ["removal_enabled"] = true, ["removal_rows"] = 1, ["removal_columns"] = 1 };
                values.Property("vias.configuration")!.Remove();
                File.WriteAllText(path, data.ToString());
                var migrated = ProjectDocument.Load(path, tests.Catalog);
                Assert(migrated.SchemaVersion == "packstudio.project/v3" && migrated.Values["bga.via_configuration"] == null, "legacy format leaked into current document");
                Assert(migrated.Values["vias.configuration"]!["removal_enabled"].Flag(), "legacy via configuration lost");
                Near(migrated.Values["metal.layers"]![0]!["thickness"].Number(), 0.03, "migration reinitialized saved geometry");
            }
            finally { if (File.Exists(path)) File.Delete(path); }
        });
    }
}
