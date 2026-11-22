using System.Globalization;
using System.Xml.Linq;
using PackStudio.Core;
using static TestSuite;

static class PtaExportChecks
{
    static readonly XNamespace M = "http://schemas.datacontract.org/2004/07/ThermalSim.Models";
    static readonly XNamespace A = "http://schemas.microsoft.com/2003/10/Serialization/Arrays";

    public static void Run(TestSuite tests)
    {
        foreach (var family in tests.Catalog.Families)
            tests.Case("export", family.Id + " PTA independent blocks", () =>
            {
                var result = tests.GenerateResult(tests.CreateForGeneration(tests.Catalog.Load(family.Id)));
                var root = PtaProjectExporter.Export(result).Root!;
                var model = result.Model!;
                Assert(root.Name == M + "Structure" && (bool)root.Element(M + "UseBlockBuildMode")!, "independent block mode");
                Assert((string?)root.Element(M + "LengthUnit") == "Mm", "PTA project units");
                foreach (string node in new[] { "Layer", "GeneratedMesh", "Results", "LayerPBResults", "ThermalMaskResults" })
                    Assert(!root.Descendants(M + node).Any(), "unexpected " + node);
                var materials = root.Element(M + "Materials")!.Elements(A + "KeyValueOfstringMaterialGyu7GfTz")
                    .ToDictionary(e => e.Element(A + "Key")!.Value, e => e.Element(A + "Value")!);
                Assert(!root.Element(M + "Functions")!.HasElements, "unexpected PTA material functions");
                var sources = root.Element(M + "HeatSources")!.Elements(M + "HeatSource").ToDictionary(e => e.Element(M + "Id")!.Value);
                var blocks = root.Element(M + "Blocks")!.Elements(M + "Block").ToDictionary(e => e.Element(M + "Id")!.Value);
                var solid = new List<Prism>();
                var originals = model.Blocks.ToDictionary(b => b.Id);
                foreach (var (id, xml) in blocks)
                {
                    var owner = originals.TryGetValue(id, out var direct) ? direct : originals[id[..id.LastIndexOf("-pta-", StringComparison.Ordinal)]];
                    var rects = xml.Element(M + "AllRects")!.Elements().ToArray();
                    var array = rects.SingleOrDefault(r => (bool?)r.Element(M + "ArrayDisguise") == true);
                    if (array != null)
                    {
                        int nx = (int)array.Element(M + "XSizeExpression")!, ny = (int)array.Element(M + "YSizeExpression")!;
                        Assert(rects.Length == nx * ny + 1, "incomplete array");
                        var members = rects.Where(r => r != array).ToArray();
                        for (int i = 0; i < members.Length; i++)
                        {
                            Near(Number(members[i], "XExpression"), i / ny * Number(array, "XIntervalExpression"), "array x");
                            Near(Number(members[i], "YExpression"), i % ny * Number(array, "YIntervalExpression"), "array y");
                        }
                    }
                    double z = Number(xml, "ZOffsetExpression");
                    foreach (var r in rects.Where(r => r != array))
                    {
                        double x = Number(xml, "XOffsetExpression") + Number(r, "XExpression");
                        double y = Number(xml, "YOffsetExpression") + Number(r, "YExpression");
                        solid.Add(new(id, x, x + Number(r, "WidthExpression"), y, y + Number(r, "HeightExpression"),
                            z, z + Number(xml, "ThicknessExpression"), (bool)r.Element(M + "Add_sub")!));
                    }
                    var material = model.Materials[owner.MaterialId];
                    var definition = materials[xml.Element(M + "MaterialName")!.Value];
                    Near(Number(definition, "Density"), material.Density, "density");
                    Near(Number(definition, "SpecificHeatCapacity"), material.SpecificHeat, "specific heat");
                    string k = definition.Element(M + "ThermalConductivity")!.Value;
                    var components = k.Split(',').Select(v => double.Parse(v, CultureInfo.InvariantCulture)).ToArray();
                    double[] expected = material.ConductType == 2 ? [.. material.Conductivity.Components] : [material.Conductivity.X];
                    Assert(components.Length == expected.Length, "conductivity component count");
                    for (int i = 0; i < expected.Length; i++) Near(components[i], expected[i], "conductivity component");
                }
                VerifyOccupancy(model, solid, blocks, sources);
            });

        tests.Case("export", "PTA cuts leave the overlapping source model intact and conserve power", () =>
        {
            var original = tests.Generate(tests.Create(tests.Catalog.Load("bare_die")));
            var seed = original.Blocks.Single();
            var host = seed with { Id = "host", StructureType = "encapsulant", Origin = new(0,0,0), Size = new(4,4,3) };
            var cutter = seed with { Id = "insert", Origin = new(1,1,1), Size = new(2,2,1) };
            var model = new PackageModel(original.TemplateId, original.Name, original.Metadata, original.Groups,
                [host, cutter], original.Materials, [new(host.Id, 22)]);
            var result = tests.Result(model);
            var before = ModelXmlExporter.Export(result);
            var root = PtaProjectExporter.Export(result).Root!;
            Assert(result.Issues.Any(i => i.Code == "model.overlap") && model.Blocks[0] == host &&
                model.Blocks.Count == 2 && XNode.DeepEquals(before, ModelXmlExporter.Export(result)), "PTA clipping leaked into PackStudio");
            var blocks = root.Element(M + "Blocks")!.Elements().ToArray();
            Assert(blocks.Length == 4 && blocks.Count(b => b.Element(M + "HeatSourceId") != null) == 3, "only the host needs three Z slices");
            Assert(blocks.SelectMany(b => b.Descendants(M + "Add_sub")).Count(e => !(bool)e) == 1, "middle slice needs one hole");
            Near(Number(root.Descendants(M + "HeatSource").Single(), "PowerDensity"), 22 / (44e-9), "source volume after boolean cut");
            var covered = cutter with { Origin = host.Origin, Size = host.Size };
            var hiddenSource = new PackageModel(original.TemplateId, original.Name, original.Metadata, original.Groups,
                [host, covered], original.Materials, [new(host.Id, 22)]);
            Reject(() => PtaProjectExporter.Export(tests.Result(hiddenSource)));
        });

        tests.Case("export", "PTA preserves material identity and sums heat contributions", () =>
        {
            var original = tests.Generate(tests.Create(tests.Catalog.Load("bare_die")));
            var first = original.Blocks.Single();
            var material = original.Materials[first.MaterialId];
            var other = material with { Id = "other", Density = 1234 };
            var second = first with { Id = "second", MaterialId = other.Id, Origin = first.Maximum };
            PackageModel WithBlocks(params Block[] blocks) => new(original.TemplateId, original.Name, original.Metadata, original.Groups,
                blocks, new Dictionary<string, Material> { [material.Id] = material, [other.Id] = other }, [new(first.Id, 1), new(first.Id, 2)]);
            var root = PtaProjectExporter.Export(tests.Result(WithBlocks(first, second))).Root!;
            var densities = root.Element(M + "Materials")!.Elements().ToDictionary(e => e.Element(A + "Key")!.Value, e => Number(e.Element(A + "Value")!, "Density"));
            var blocks = root.Element(M + "Blocks")!.Elements().ToDictionary(e => e.Element(M + "Id")!.Value);
            Near(densities[blocks[first.Id].Element(M + "MaterialName")!.Value], material.Density, "first material");
            Near(densities[blocks[second.Id].Element(M + "MaterialName")!.Value], other.Density, "second material");
            var source = root.Element(M + "HeatSources")!.Elements().Single();
            Near(Number(source, "PowerDensity") * first.Size.Volume * 1e-9, 3, "summed power");
            Reject(() => PtaProjectExporter.Export(tests.Result(WithBlocks(first, first))));
        });
    }

    sealed record Prism(string Id, double X0, double X1, double Y0, double Y1, double Z0, double Z1, bool Add);

    // Integrate the actual serialized positives and negatives on open intervals between all faces.
    static void VerifyOccupancy(PackageModel model, List<Prism> solid, Dictionary<string, XElement> blocks, Dictionary<string, XElement> sources)
    {
        var input = model.Blocks.OrderBy(b => b.GroupId == "group-backside-spreader" ? 10 :
                b.StructureType == "encapsulant" || b.Id == "dielectric-part-1" ? 100 : 20)
            .ThenBy(b => b.Size.Volume).ThenBy(b => b.Id, StringComparer.Ordinal)
            .Select(b => new Prism(b.Id, b.Origin.X, b.Maximum.X, b.Origin.Y, b.Maximum.Y, b.Origin.Z, b.Maximum.Z, true)).ToArray();
        var original = model.Blocks.ToDictionary(b => b.Id);
        var watts = new Dictionary<string, double>();
        var names = original.Values.ToLookup(b => (b.Name, b.MaterialId));
        foreach (var (z, dz) in Intervals(input.Concat(solid).SelectMany(p => new[] { p.Z0, p.Z1 })))
        {
            var iz = input.Where(p => p.Z0 < z && z < p.Z1).ToArray();
            var oz = solid.Where(p => p.Z0 < z && z < p.Z1).ToArray();
            foreach (var (y, dy) in Intervals(iz.Concat(oz).SelectMany(p => new[] { p.Y0, p.Y1 })))
            {
                var ir = iz.Where(p => p.Y0 < y && y < p.Y1).ToArray();
                var orow = oz.Where(p => p.Y0 < y && y < p.Y1).ToArray();
                foreach (var (x, dx) in Intervals(ir.Concat(orow).SelectMany(p => new[] { p.X0, p.X1 })))
                {
                    var winner = ir.FirstOrDefault(p => p.X0 < x && x < p.X1);
                    var hits = orow.Where(p => p.X0 < x && x < p.X1).GroupBy(p => p.Id).Where(g => g.All(p => p.Add)).ToArray();
                    Assert(hits.Length == (winner == null ? 0 : 1), $"PTA overlap or gap at {x},{y},{z}");
                    if (winner == null) continue;
                    var xml = blocks[hits[0].Key];
                    var seed = xml.Element(M + "AllRects")!.Elements().First();
                    var name = seed.Element(M + "Name")!.Value;
                    Assert(names.Contains((name, original[winner.Id].MaterialId)), "priority material mismatch");
                    if (xml.Element(M + "HeatSourceId") is { } source)
                    {
                        Assert(source.Value == "heat-" + winner.Id, "heat source on wrong material");
                        watts[winner.Id] = watts.GetValueOrDefault(winner.Id) + dx * dy * dz * 1e-9 * Number(sources[source.Value], "PowerDensity");
                    }
                }
            }
        }
        foreach (var group in model.Sources.GroupBy(s => s.BlockId))
            Near(watts.GetValueOrDefault(group.Key), group.Sum(s => s.Power), "integrated source power");
    }

    static IEnumerable<(double Center, double Width)> Intervals(IEnumerable<double> edges)
    {
        var sorted = edges.Distinct().Order().ToArray();
        for (int i = 1; i < sorted.Length; i++)
            if (sorted[i] - sorted[i-1] > 1e-9)
                yield return ((sorted[i] + sorted[i-1]) / 2, sorted[i] - sorted[i-1]);
    }

    static double Number(XElement parent, string field) => (double)parent.Element(M + field)!;
}
