using System.Globalization;
using System.Xml.Linq;
using PackStudio.Core;
using static TestSuite;

static class PtaExportChecks
{
    static readonly XNamespace M = "http://schemas.datacontract.org/2004/07/ThermalSim.Models";
    static readonly XNamespace A = "http://schemas.microsoft.com/2003/10/Serialization/Arrays";
    static readonly XNamespace F = M.NamespaceName + ".Functions";

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
                var functions = root.Element(M + "Functions")!.Elements(A + "KeyValueOfstringFunctionAdzryM2O")
                    .ToDictionary(e => e.Element(A + "Key")!.Value + "(T)", e => e.Element(A + "Value")!);
                var sources = root.Element(M + "HeatSources")!.Elements(M + "HeatSource").ToDictionary(e => e.Element(M + "Id")!.Value);
                var blocks = root.Element(M + "Blocks")!.Elements(M + "Block").ToDictionary(e => e.Element(M + "Id")!.Value);
                var powers = model.Sources.ToLookup(s => s.BlockId, s => s.Power);
                Assert(blocks.Count == model.Blocks.Count && sources.Count == powers.Count, "blocks or sources lost");
                foreach (var block in model.Blocks)
                {
                    var xml = blocks[block.Id];
                    var rect = xml.Element(M + "AllRects")!.Elements(M + "Rect").Single();
                    Assert((bool)rect.Element(M + "Add_sub")! && (bool)xml.Element(M + "IsVisible")!, "block invisible or subtracted");
                    foreach (string field in new[] { "XSizeExpression", "YSizeExpression", "XIntervalExpression", "YIntervalExpression" })
                        Assert(rect.Element(M + field) == null, "array setter overwrites ordinary rectangle geometry");
                    Near(Number(xml, "XOffsetExpression") + Number(rect, "XExpression"), block.Origin.X, "x");
                    Near(Number(xml, "YOffsetExpression") + Number(rect, "YExpression"), block.Origin.Y, "y");
                    Near(Number(xml, "ZOffsetExpression"), block.Origin.Z, "z");
                    double dx = Number(rect, "WidthExpression"), dy = Number(rect, "HeightExpression"), dz = Number(xml, "ThicknessExpression");
                    Near(dx, block.Size.X, "width");
                    Near(dy, block.Size.Y, "height");
                    Near(dz, block.Size.Z, "thickness");
                    var sourceId = (string?)xml.Element(M + "HeatSourceId");
                    Assert((sourceId != null) == powers.Contains(block.Id), "wrong source assignment");
                    if (sourceId != null)
                        Near(Number(sources[sourceId], "PowerDensity") * dx * dy * dz * 1e-9, powers[block.Id].Sum(), "power in watts");

                    var material = model.Materials[block.MaterialId];
                    var definition = materials[xml.Element(M + "MaterialName")!.Value];
                    Near(Number(definition, "Density"), material.Density, "density");
                    Near(Number(definition, "SpecificHeatCapacity"), material.SpecificHeat, "specific heat");
                    string k = definition.Element(M + "ThermalConductivity")!.Value;
                    if (material.ConductType == 1)
                    {
                        var function = functions[k];
                        Assert((string?)function.Element(F + "ArgumentKind") == "Temperature", "temperature function argument");
                        double slope = (double)function.Element(F + "A1")!, intercept = (double)function.Element(F + "A0")!;
                        Near(slope, material.ConductivityCoefficient!.Value, "temperature slope");
                        Near(intercept + slope * (material.ReferenceTemperature!.Value + 273.15), material.Conductivity.X, "reference conductivity");
                    }
                    else
                    {
                        var components = k.Split(',').Select(v => double.Parse(v, CultureInfo.InvariantCulture)).ToArray();
                        double[] expected = material.ConductType == 2 ? [.. material.Conductivity.Components] : [material.Conductivity.X];
                        Assert(components.Length == expected.Length, "conductivity component count");
                        for (int i = 0; i < expected.Length; i++) Near(components[i], expected[i], "conductivity component");
                    }
                }
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

    static double Number(XElement parent, string field) => (double)parent.Element(M + field)!;
}
