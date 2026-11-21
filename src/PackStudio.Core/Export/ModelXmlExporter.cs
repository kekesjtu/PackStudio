using System.Globalization;
using System.Xml.Linq;
using static PackStudio.Core.XmlExport;

namespace PackStudio.Core;

public static class ModelXmlExporter
{
    static XAttribute Number(string name, double value) => new(name, Format(value));

    public static XDocument Export(GenerationResult result)
    {
        if (!result.CanExport) throw new ArgumentException("生成结果包含阻断问题，不能导出。");
        var model = result.Model!;
        var used = model.Blocks.Select(b => b.MaterialId).ToHashSet(StringComparer.Ordinal);
        var materials = model.Materials.Values.Where(m => used.Contains(m.Id)).OrderBy(m => m.Id, StringComparer.Ordinal).ToArray();
        var references = materials.Select((m, i) => (m.Id, Reference: "m" + (i + 1).ToString(CultureInfo.InvariantCulture)))
            .ToDictionary(p => p.Id, p => p.Reference, StringComparer.Ordinal);
        var definitions = new XElement("materials");
        foreach (var material in materials)
        {
            var k = material.EffectiveConductivity;
            var definition = new XElement("material", new XAttribute("id", references[material.Id]), new XAttribute("name", material.Name),
                new XAttribute("type", material.ConductType switch { 0 => "isotropic", 1 => "temperature_dependent", 2 => "orthotropic", _ => throw new ArgumentException("未知导热类型。") }),
                new XElement("density", Format(material.Density)), new XElement("specific_heat", Format(material.SpecificHeat)),
                new XElement("conductivity", Number("x", k.X), Number("y", k.Y), Number("z", k.Z)));
            if (material.ConductType == 1)
                definition.Add(new XElement("coefficient", Format(material.ConductivityCoefficient!.Value)),
                    new XElement("reference_temperature", Format((material.ReferenceTemperature ?? 0) + 273.15)));
            definitions.Add(definition);
        }

        var sources = new XElement("sources");
        foreach (var source in model.Sources.GroupBy(s => s.BlockId))
            sources.Add(new XElement("source", new XAttribute("block", source.Key), Number("power", source.Sum(s => s.Power))));
        var root = new XElement("model", new XAttribute("version", "1"), new XAttribute("name", model.Name), definitions, sources);
        int groupNumber = 0;
        foreach (var group in model.Blocks.GroupBy(b => (b.GroupId, b.MaterialId)))
        {
            var element = new XElement("group", new XAttribute("id", "g" + (++groupNumber).ToString(CultureInfo.InvariantCulture)),
                new XAttribute("name", group.First().GroupName));
            foreach (var block in group)
                element.Add(new XElement("block", new XAttribute("id", block.Id), new XAttribute("name", block.Name),
                    Number("x", block.Origin.X * 0.001), Number("y", block.Origin.Y * 0.001), Number("z", block.Origin.Z * 0.001),
                    Number("dx", block.Size.X * 0.001), Number("dy", block.Size.Y * 0.001), Number("dz", block.Size.Z * 0.001)));
            element.Add(new XElement("material", references[group.Key.MaterialId]));
            root.Add(element);
        }
        return new(new XDeclaration("1.0", "utf-8", null), root);
    }

    public static void Save(GenerationResult result, string path) => XmlExport.Save(Export(result), path);
}
