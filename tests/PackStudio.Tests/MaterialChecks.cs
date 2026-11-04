using PackStudio.Core;
using static TestSuite;

static class MaterialChecks
{
    public static void Run(TestSuite tests)
    {
        tests.Case("materials", "user material assignment wins", () =>
        {
            var document = ProjectDocument.Create(tests.Catalog.Load("cbga_fc"));
            document.MaterialAssignments["group-substrate"] = "copper";
            var model = tests.Builder.Generate(document);
            Assert(model.Blocks.Single(b => b.StructureType == "substrate").MaterialId == "copper", "material assignment not applied");
        });
        tests.Case("materials", "derived material override wins", () =>
        {
            var document = ProjectDocument.Create(tests.Catalog.Load("bare_die"));
            document.Values["bumps.enabled"] = true;
            var original = tests.Builder.Generate(document).Materials["flip-chip-bumps-equivalent"];
            document.CustomMaterials.Add(original with { Conductivity = new(42, 43, 44) });
            Near(tests.Builder.Generate(document).Materials[original.Id].Conductivity.X, 42, "derived override");
        });
        tests.Case("materials", "invalid material rejected", () => Reject(() => new Material("x", "x", new(1, 1, 1), -1, 2).Validate()));
        tests.Case("materials", "generation does not reread preset material assignments", () =>
        {
            var template = tests.Catalog.Load("pbga_wb");
            var preset = template.Presets.Single(p => p.Name == template.DefaultPreset);
            var document = ProjectDocument.Create(template);
            string original = preset.MaterialAssignments["group-encapsulant"];
            try
            {
                preset.MaterialAssignments["group-encapsulant"] = "copper";
                var model = tests.Builder.Generate(document);
                Assert(model.Blocks.Single(b => b.StructureType == "encapsulant").MaterialId == original, "preset changes altered existing document materials");
            }
            finally { preset.MaterialAssignments["group-encapsulant"] = original; }
        });
        tests.Case("materials", "FC via matrix retains isotropic conductivity", () =>
        {
            var document = ProjectDocument.Create(tests.Catalog.Load("pbga_fc"));
            var values = document.Values;
            values["vias.enabled"] = true;
            values["vias.modeling"] = "equivalent";
            values["vias.rows"] = 4; values["vias.columns"] = 3;
            values["vias.pitch"] = 0.5; values["vias.diameter"] = 0.2; values["vias.plating"] = 0.025;
            var matrix = tests.Builder.Generate(document).Materials["fc-core-via"];
            Assert(matrix.Conductivity.X > 0 && matrix.Conductivity.Y > 0, "matrix conductivity lost");
        });
    }
}
