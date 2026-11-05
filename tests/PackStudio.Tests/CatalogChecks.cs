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
                var document = tests.Create(template);
                var model = tests.Generate(document);
                var die = model.Blocks.Single(b => b.StructureType == "die");
                Near(die.Size.X, document.Values["die.length"].Number(), "die length");
                Near(die.Size.Y, document.Values["die.width"].Number(), "die width");
                Near(die.Size.Z, document.Values["die.thickness"].Number(), "die thickness");
                Near(model.Sources.Sum(s => s.Power), document.Values["die.power"].Number(), "power conservation");
                var xml = tests.Export(model);
                var attributes = xml.Root!.Element("attributes")!;
                foreach (string name in new[] { "surfaces", "radiations" })
                    Assert(attributes.Elements(name).Single() is { IsEmpty: true, HasAttributes: false }, name + " must be an empty tag");
                Assert(!xml.Descendants().Any(e => e.Name.LocalName is not ("surfaces" or "radiations") &&
                    (e.Name.LocalName.Contains("surface") || e.Name.LocalName.Contains("radiation") || e.Name.LocalName.Contains("emissivity"))),
                    "surface radiation definitions or references leaked into FloXML");
                FloXmlExporter.Validate(xml, Path.Combine(tests.Root, "output_format/floxml/xmlSchema.xsd"));
                foreach (var preset in template.Presets)
                    foreach (var assignment in preset.MaterialAssignments)
                        Assert(tests.Catalog.Materials.Items.ContainsKey(assignment.Value), "unresolved material ID");
            });
        }
        tests.Case("catalog", "unknown preset", () => Reject(() => tests.Create(tests.Catalog.Load("qfn"), "missing")));
    }
}
