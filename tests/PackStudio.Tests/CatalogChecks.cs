using PackStudio.Core;
using static TestSuite;

static class CatalogChecks
{
    public static void Run(TestSuite tests)
    {
        foreach (var info in tests.Catalog.Families)
        {
            tests.Case("catalog", info.Id, () =>
            {
                var template = tests.Catalog.Load(info.Id);
                var document = ProjectDocument.Create(template);
                var model = tests.Builder.Generate(document);
                var die = model.Blocks.Single(b => b.StructureType == "die");
                Near(die.Size.X, document.Values["die.length"].Number(), "die length");
                Near(die.Size.Y, document.Values["die.width"].Number(), "die width");
                Near(die.Size.Z, document.Values["die.thickness"].Number(), "die thickness");
                Near(model.Sources.Sum(s => s.Power), document.Values["die.power"].Number(), "power conservation");
                FloXml.Validate(FloXml.Export(model), Path.Combine(tests.Root, "output_format/floxml/xmlSchema.xsd"));
                foreach (var preset in template.Presets)
                    foreach (var assignment in preset.MaterialAssignments)
                        Assert(tests.Catalog.Materials.Items.ContainsKey(assignment.Value), "unresolved material ID");
            });
        }
        tests.Case("catalog", "unknown preset", () => Reject(() => tests.Catalog.Load("qfn").Defaults("missing")));
    }
}
