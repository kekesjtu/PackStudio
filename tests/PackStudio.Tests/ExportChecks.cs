using PackStudio.Core;
using static TestSuite;

static class ExportChecks
{
    public static void Run(TestSuite tests)
    {
        foreach (var family in tests.Catalog.Families)
            tests.Case("export", family.Id + " self-contained XML", () =>
            {
                var document = tests.Create(tests.Catalog.Load(family.Id));
                var model = tests.Generate(document);
                var root = tests.Export(model).Root!;
                Assert(root.Name == "model" && (string?)root.Attribute("version") == "1", "missing format version");
                Assert(root.Elements().Take(2).Select(e => e.Name.LocalName).SequenceEqual(new[] { "materials", "sources" }), "top-level order");
                var allowed = new HashSet<string> { "model", "materials", "material", "density", "specific_heat", "conductivity", "coefficient", "reference_temperature", "sources", "source", "group", "block" };
                Assert(root.DescendantsAndSelf().All(e => allowed.Contains(e.Name.LocalName)), "nonphysical or native-only field leaked");
                var definitions = root.Element("materials")!.Elements("material").ToDictionary(e => (string)e.Attribute("id")!);
                Assert(definitions.Count == model.Blocks.Select(b => b.MaterialId).Distinct().Count(), "unused material exported or definition missing");
                Assert(!definitions.Keys.Intersect(model.Materials.Keys).Any(), "runtime material IDs leaked");
                var blocks = root.Descendants("block").ToDictionary(e => (string)e.Attribute("id")!);
                Assert(blocks.Count == model.Blocks.Count, "block count changed");
                foreach (var block in model.Blocks)
                {
                    var xml = blocks[block.Id];
                    Assert(xml.Attributes().Select(a => a.Name.LocalName).ToHashSet().SetEquals(new[] { "id", "name", "x", "y", "z", "dx", "dy", "dz" }) && !xml.HasElements, "block field scope");
                    Near((double)xml.Attribute("x")!, block.Origin.X * 0.001, "global x");
                    Near((double)xml.Attribute("y")!, block.Origin.Y * 0.001, "global y");
                    Near((double)xml.Attribute("z")!, block.Origin.Z * 0.001, "global z");
                    Near((double)xml.Attribute("dx")!, block.Size.X * 0.001, "size x");
                    Near((double)xml.Attribute("dy")!, block.Size.Y * 0.001, "size y");
                    Near((double)xml.Attribute("dz")!, block.Size.Z * 0.001, "size z");
                    var material = model.Materials[block.MaterialId];
                    var definition = definitions[xml.Parent!.Element("material")!.Value];
                    Near((double)definition.Element("density")!, material.Density, "density");
                    Near((double)definition.Element("specific_heat")!, material.SpecificHeat, "specific heat");
                    var conductivity = definition.Element("conductivity")!;
                    Near((double)conductivity.Attribute("x")!, material.EffectiveConductivity.X, "kx");
                    Near((double)conductivity.Attribute("y")!, material.EffectiveConductivity.Y, "ky");
                    Near((double)conductivity.Attribute("z")!, material.EffectiveConductivity.Z, "kz");
                }
                var sources = root.Element("sources")!.Elements("source").ToDictionary(e => (string)e.Attribute("block")!);
                Assert(sources.Count == model.Sources.Select(s => s.BlockId).Distinct().Count(), "source count changed");
                foreach (var source in model.Sources.GroupBy(s => s.BlockId))
                    Near((double)sources[source.Key].Attribute("power")!, source.Sum(s => s.Power), "block power");
                Assert(document.Values.Property("grid.enabled") != null && document.Values.Property("grid.density") != null, "internal grid fields removed");
            });

        tests.Case("export", "multiple heat contributions share one block source", () =>
        {
            var model = tests.Generate(tests.Create(tests.Catalog.Load("bare_die")));
            var block = model.Blocks.Single();
            model = new(model.TemplateId, model.Name, model.Metadata, model.Groups, model.Blocks, model.Materials,
                [new(block.Id, 0.75), new(block.Id, 1.25)]);
            var source = tests.Export(model).Root!.Element("sources")!.Elements("source").Single();
            Assert((string?)source.Attribute("block") == block.Id, "source block reference");
            Near((double)source.Attribute("power")!, 2, "source sum");
        });
    }
}
