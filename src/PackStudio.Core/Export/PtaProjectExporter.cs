using System.Globalization;
using System.Xml.Linq;
using static PackStudio.Core.XmlExport;

namespace PackStudio.Core;

public static class PtaProjectExporter
{
    static readonly XNamespace Model = "http://schemas.datacontract.org/2004/07/ThermalSim.Models";
    static readonly XNamespace Arrays = "http://schemas.microsoft.com/2003/10/Serialization/Arrays";
    static readonly XNamespace Media = "http://schemas.datacontract.org/2004/07/System.Windows.Media";
    static readonly XNamespace Instance = "http://www.w3.org/2001/XMLSchema-instance";

    public static void Save(GenerationResult result, string path) => XmlExport.Save(Export(result), path);

    public static XDocument Export(GenerationResult result)
    {
        if (!result.CanExport) throw new ArgumentException("生成结果包含阻断问题，不能导出。");
        var model = result.Model!;
        var slices = PtaGeometry.Partition(model).ToLookup(s => s.Owner.Id);
        var materials = new XElement(Model + "Materials");
        var materialNames = new Dictionary<string, string>();
        var usedNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var id in model.Blocks.Where(b => slices.Contains(b.Id)).Select(b => b.MaterialId).Distinct().Order(StringComparer.Ordinal))
        {
            var material = model.Materials[id];
            string name = string.IsNullOrWhiteSpace(material.Name) ? id : material.Name;
            string key = name;
            for (int suffix = 2; !usedNames.Add(key); suffix++)
                key = FormattableString.Invariant($"{name} ({suffix})");
            materialNames.Add(id, key);
            materials.Add(new XElement(Arrays + "KeyValueOfstringMaterialGyu7GfTz",
                new XElement(Arrays + "Key", key),
                new XElement(Arrays + "Value",
                    new XElement(Model + "Density", Format(material.Density)),
                    new XElement(Model + "FluidMaterial", false),
                    new XElement(Model + "SpecificHeatCapacity", Format(material.SpecificHeat)),
                    new XElement(Model + "ThermalConductivity", Conductivity(material)))));
        }

        var blocks = new XElement(Model + "Blocks");
        var sources = new XElement(Model + "HeatSources");
        var powerByBlock = model.Sources.GroupBy(s => s.BlockId).ToDictionary(g => g.Key, g => g.Sum(s => s.Power));
        var candidates = new List<PtaSlice>();
        var allocated = model.Blocks.Select(b => b.Id).ToHashSet(StringComparer.Ordinal);
        foreach (var block in model.Blocks)
        {
            var parts = slices[block.Id].ToArray();
            if (parts.Length == 0)
            {
                if (powerByBlock.GetValueOrDefault(block.Id) > 0)
                    throw new ArgumentException($"热源块 {block.Id} 被完全覆盖，无法保留其功率。");
                continue;
            }
            string? sourceId = null;
            if (powerByBlock.TryGetValue(block.Id, out double power))
            {
                sourceId = "heat-" + block.Id;
                double volumeM3 = parts.Sum(p => p.Volume) * 1e-9;
                sources.Add(new XElement(Model + "HeatSource",
                    new XElement(Model + "Id", sourceId),
                    new XElement(Model + "Name", block.Name),
                    new XElement(Model + "PowerDensity", Format(power / volumeM3))));
            }
            if (sourceId == null && parts.Length == 1 && parts[0].Holes.Length == 0)
                candidates.Add(parts[0]);
            else
            {
                int suffix = 2;
                foreach (var part in parts)
                {
                    string id = block.Id;
                    if (part != parts[0])
                        do { id = FormattableString.Invariant($"{block.Id}-pta-{suffix++}"); } while (!allocated.Add(id));
                    blocks.Add(WriteBlock(part, id, materialNames[block.MaterialId], model.Materials[block.MaterialId].Color, sourceId));
                }
            }
        }
        foreach (var array in PtaArrays.Layout(candidates))
        {
            var seed = array.Members[0];
            var owner = seed.Owner;
            var block = WriteBlock(seed, owner.Id, materialNames[owner.MaterialId], model.Materials[owner.MaterialId].Color, null);
            if (array.Members.Length > 1)
            {
                var rects = block.Element(Model + "AllRects")!;
                rects.Elements().First().Element(Model + "NotOccupiedByArray")!.Value = "false";
                rects.Add(new XElement(Model + "Rect", new XElement(Model + "ArrayDisguise", true),
                    new XElement(Model + "Name", "阵列"), new XElement(Model + "NotOccupiedByArray", true),
                    new XElement(Model + "XIntervalExpression", array.PitchX), new XElement(Model + "XSizeExpression", array.Columns),
                    new XElement(Model + "YIntervalExpression", array.PitchY), new XElement(Model + "YSizeExpression", array.Rows)));
                foreach (var member in array.Members.Skip(1))
                    rects.Add(Rect(member.Face, seed.Face, member.Owner.Name, true, true));
            }
            blocks.Add(block);
        }

        // PTA's data contract reads fields in declaration order, including dictionary entries.
        var root = new XElement(Model + "Structure",
            new XAttribute(XNamespace.Xmlns + "a", Arrays),
            new XAttribute(XNamespace.Xmlns + "i", Instance), new XAttribute(XNamespace.Xmlns + "w", Media),
            new XElement(Model + "AmbientTemperature", "300"), new XElement(Model + "BasicGeometries"),
            blocks, new XElement(Model + "Boundaries"),
            new XElement(Model + "Dimension", "Dimension3D"), new XElement(Model + "EnabledPhysics", "HeatTransfer"),
            new XElement(Model + "Functions"), sources, new XElement(Model + "InitialTemperature", 300),
            new XElement(Model + "Layers"), new XElement(Model + "LengthUnit", "Mm"), materials,
            new XElement(Model + "MeshSettings"), new XElement(Model + "ObservePoints2D"), new XElement(Model + "ObservePoints3D"),
            new XElement(Model + "SoftwareMode", "PTA"), new XElement(Model + "SolverType", "FDM"),
            new XElement(Model + "StudyType", "Steady"), new XElement(Model + "TopoGeometries"), new XElement(Model + "TopoLayers"),
            new XElement(Model + "TransientStudyTimeStep", 1), new XElement(Model + "TransientTimeUnit", "S"),
            new XElement(Model + "UseBlockBuildMode", true),
            new XElement(Model + "Variables"));
        return new(new XDeclaration("1.0", "utf-8", null), root);
    }

    static string Conductivity(Material material) => material.ConductType == 2
        ? string.Join(",", material.Conductivity.Components.Select(Format))
        : Format(material.Conductivity.X);

    static XElement Rect(PtaRect face, PtaRect origin, string name, bool add, bool arrayMember = false) =>
        new(Model + "Rect", new XElement(Model + "Add_sub", add),
            arrayMember ? new XElement(Model + "CreatedByArray", true) : null,
            new XElement(Model + "HeightExpression", face.Height), new XElement(Model + "Name", name),
            new XElement(Model + "NotOccupiedByArray", true), new XElement(Model + "WidthExpression", face.Width),
            new XElement(Model + "XExpression", face.Left - origin.Left),
            new XElement(Model + "YExpression", face.Bottom - origin.Bottom));

    static XElement WriteBlock(PtaSlice slice, string id, string material, string color, string? sourceId)
    {
        var block = slice.Owner;
        string name = id == block.Id ? block.Name : id;
        var rects = new XElement(Model + "AllRects", Rect(slice.Face, slice.Face, block.Name, true),
            slice.Holes.Select(h => Rect(h, slice.Face, "扣除矩形", false)));
        return new XElement(Model + "Block", rects,
            new XElement(Model + "CanCreateArray", true), BlockColor(color),
            sourceId == null ? null : new XElement(Model + "HeatSourceId", sourceId),
            new XElement(Model + "Id", id), new XElement(Model + "InitialName", name),
            new XElement(Model + "IsVisible", true), new XElement(Model + "MaterialName", material),
            new XElement(Model + "Name", name), new XElement(Model + "ThicknessExpression", slice.Top - slice.Bottom),
            new XElement(Model + "XOffsetExpression", slice.Face.Left),
            new XElement(Model + "YOffsetExpression", slice.Face.Bottom),
            new XElement(Model + "ZOffsetExpression", slice.Bottom));
    }

    static XElement BlockColor(string color)
    {
        if (color is not { Length: 7 } || color[0] != '#' ||
            !int.TryParse(color.AsSpan(1), NumberStyles.AllowHexSpecifier, CultureInfo.InvariantCulture, out int rgb))
            rgb = 0xAEB7BF;
        return new XElement(Model + "Color", new XElement(Media + "A", 255),
            new XElement(Media + "B", rgb & 255), new XElement(Media + "G", rgb >> 8 & 255),
            new XElement(Media + "R", rgb >> 16));
    }
}
