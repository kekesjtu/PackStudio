using System.Globalization;
using System.Xml.Linq;
using static PackStudio.Core.XmlExport;

namespace PackStudio.Core;

public static class PtaProjectExporter
{
    static readonly XNamespace Model = "http://schemas.datacontract.org/2004/07/ThermalSim.Models";
    static readonly XNamespace Functions = Model.NamespaceName + ".Functions";
    static readonly XNamespace Arrays = "http://schemas.microsoft.com/2003/10/Serialization/Arrays";
    static readonly XNamespace Media = "http://schemas.datacontract.org/2004/07/System.Windows.Media";
    static readonly XNamespace Instance = "http://www.w3.org/2001/XMLSchema-instance";

    public static void Save(GenerationResult result, string path) => XmlExport.Save(Export(result), path);

    public static XDocument Export(GenerationResult result)
    {
        if (!result.CanExport) throw new ArgumentException("生成结果包含阻断问题，不能导出。");
        var model = result.Model!;
        var materials = new XElement(Model + "Materials");
        var functions = new XElement(Model + "Functions");
        var materialNames = new Dictionary<string, string>();
        var usedNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var id in model.Blocks.Select(b => b.MaterialId).Distinct().Order(StringComparer.Ordinal))
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
                    new XElement(Model + "ThermalConductivity", Conductivity(material, functions, materialNames.Count)))));
        }

        var blocks = new XElement(Model + "Blocks");
        var sources = new XElement(Model + "HeatSources");
        var powerByBlock = model.Sources.GroupBy(s => s.BlockId).ToDictionary(g => g.Key, g => g.Sum(s => s.Power));
        foreach (var block in model.Blocks)
        {
            string? sourceId = null;
            if (powerByBlock.TryGetValue(block.Id, out double power))
            {
                sourceId = "heat-" + block.Id;
                double volumeM3 = block.Size.Volume * 1e-9;
                sources.Add(new XElement(Model + "HeatSource",
                    new XElement(Model + "Id", sourceId),
                    new XElement(Model + "Name", block.Name),
                    new XElement(Model + "PowerDensity", Format(power / volumeM3))));
            }
            blocks.Add(WriteBlock(block, materialNames[block.MaterialId], model.Materials[block.MaterialId].Color, sourceId));
        }

        // PTA's data contract reads fields in declaration order, including dictionary entries.
        var root = new XElement(Model + "Structure",
            new XAttribute(XNamespace.Xmlns + "a", Arrays), new XAttribute(XNamespace.Xmlns + "f", Functions),
            new XAttribute(XNamespace.Xmlns + "i", Instance), new XAttribute(XNamespace.Xmlns + "w", Media),
            new XElement(Model + "AmbientTemperature", "300"), new XElement(Model + "BasicGeometries"),
            blocks, new XElement(Model + "Boundaries"),
            new XElement(Model + "Dimension", "Dimension3D"), new XElement(Model + "EnabledPhysics", "HeatTransfer"),
            functions, sources, new XElement(Model + "InitialTemperature", 300),
            new XElement(Model + "Layers"), new XElement(Model + "LengthUnit", "Mm"), materials,
            new XElement(Model + "MeshSettings"), new XElement(Model + "ObservePoints2D"), new XElement(Model + "ObservePoints3D"),
            new XElement(Model + "SoftwareMode", "PTA"), new XElement(Model + "SolverType", "FDM"),
            new XElement(Model + "StudyType", "Steady"), new XElement(Model + "TopoGeometries"), new XElement(Model + "TopoLayers"),
            new XElement(Model + "TransientStudyTimeStep", 1), new XElement(Model + "TransientTimeUnit", "S"),
            new XElement(Model + "UseBlockBuildMode", true),
            new XElement(Model + "Variables"));
        return new(new XDeclaration("1.0", "utf-8", null), root);
    }

    static string Conductivity(Material material, XElement functions, int index)
    {
        var k = material.EffectiveConductivity;
        if (material.ConductType == 2) return string.Join(",", k.Components.Select(Format));
        if (material.ConductType == 0) return Format(k.X);

        string name = "k" + index.ToString(CultureInfo.InvariantCulture);
        // k(T) = k_ref + slope * (T - T_ref), with PTA temperatures in kelvin.
        double slope = material.ConductivityCoefficient!.Value;
        double referenceK = material.ReferenceTemperature!.Value + 273.15;
        functions.Add(new XElement(Arrays + "KeyValueOfstringFunctionAdzryM2O", new XElement(Arrays + "Key", name),
            new XElement(Arrays + "Value", new XAttribute(Instance + "type", "f:PolynomialFunction"),
                new XElement(Functions + "ArgumentKind", "Temperature"),
                new XElement(Functions + "DrawMaxX", 500), new XElement(Functions + "DrawMinX", 250),
                new XElement(Functions + "A0", Format(k.X - slope * referenceK)),
                new XElement(Functions + "A1", Format(slope)))));
        return name + "(T)";
    }

    static XElement WriteBlock(Block block, string material, string color, string? sourceId)
    {
        // On ordinary rectangles PTA can alias array size/interval setters to width/position.
        // Only serialize the geometry fields for this single positive rectangle.
        var rect = new XElement(Model + "Rect", new XElement(Model + "Add_sub", true),
            new XElement(Model + "HeightExpression", Format(block.Size.Y)), new XElement(Model + "Name", "正向矩形"),
            new XElement(Model + "NotOccupiedByArray", true), new XElement(Model + "WidthExpression", Format(block.Size.X)),
            new XElement(Model + "XExpression", "0"), new XElement(Model + "YExpression", "0"));
        return new XElement(Model + "Block", new XElement(Model + "AllRects", rect),
            new XElement(Model + "CanCreateArray", true), BlockColor(color),
            sourceId == null ? null : new XElement(Model + "HeatSourceId", sourceId),
            new XElement(Model + "Id", block.Id), new XElement(Model + "InitialName", block.Name),
            new XElement(Model + "IsVisible", true), new XElement(Model + "MaterialName", material),
            new XElement(Model + "Name", block.Name), new XElement(Model + "ThicknessExpression", Format(block.Size.Z)),
            new XElement(Model + "XOffsetExpression", Format(block.Origin.X)),
            new XElement(Model + "YOffsetExpression", Format(block.Origin.Y)),
            new XElement(Model + "ZOffsetExpression", Format(block.Origin.Z)));
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
