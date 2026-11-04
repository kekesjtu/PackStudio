namespace PackStudio.Core;
public record Vector(double X, double Y, double Z)
{
    public static Vector operator +(Vector a, Vector b) => new(a.X + b.X, a.Y + b.Y, a.Z + b.Z);
    public double Volume => X * Y * Z;
    public IEnumerable<double> Components => [X, Y, Z];
}

public record Material(string Id, string Name, Vector Conductivity, double Density, double SpecificHeat, string Color = "#AEB7BF", string Category = "Derived", double? ConductivityCoefficient = null, double? ReferenceTemperature = null, string Source = "")
{
    public void Validate()
    {
        if (Conductivity.Components.Any(x => !double.IsFinite(x) || x <= 0) || !double.IsFinite(Density) || Density <= 0 || !double.IsFinite(SpecificHeat) || SpecificHeat <= 0)
            throw new ArgumentException($"材料 {Name} 的导热率、密度和比热必须为有限正数。");
    }
}

public record Block(string Id, string Name, string StructureType, Vector Origin, Vector Size, string MaterialId, string GroupId, string GroupName)
{
    public Vector Maximum => Origin + Size;
}

public record HeatSource(string BlockId, double Power);
public sealed class PackageModel(string templateId, string name)
{
    public string TemplateId { get; } = templateId;
    public string Name { get; } = name;
    public List<Block> Blocks { get; } = [];
    public Dictionary<string, Material> Materials { get; } = [];
    public List<HeatSource> Sources { get; } = [];
    public List<Auxiliary> Auxiliary { get; } = [];
    public List<string> Warnings { get; } = [];
    public ModelMetadata Metadata { get; set; } = new();
    public PackageGeometry Geometry => Metadata.Geometry;

    public void Validate()
    {
        ProjectDocument.ValidateName(Name);
        if (Blocks.Count == 0 || Blocks.Select(b => b.Id).Distinct().Count() != Blocks.Count)
            throw new ArgumentException("模型为空或包含重复几何 ID。");
        foreach (var block in Blocks)
        {
            if (block.Size.Components.Any(v => !double.IsFinite(v) || v <= 0) || block.Origin.Components.Any(v => !double.IsFinite(v)))
                throw new ArgumentException($"{block.Name} 的位置或尺寸无效。");
            if (!Materials.TryGetValue(block.MaterialId, out var material))
                throw new ArgumentException($"未知材料 {block.MaterialId}");
            material.Validate();
        }

        foreach (var source in Sources)
            if (!double.IsFinite(source.Power) || source.Power < 0 || !Blocks.Any(b => b.Id == source.BlockId))
                throw new ArgumentException("热源功率或目标无效。");
        Warnings.Clear();
        int overlaps = 0;
        for (int i = 0; i < Blocks.Count; i++)
            for (int j = i + 1; j < Blocks.Count; j++)
            {
                var a = Blocks[i];
                var b = Blocks[j];
                if (Math.Min(a.Maximum.X, b.Maximum.X) - Math.Max(a.Origin.X, b.Origin.X) > 1e-9 && Math.Min(a.Maximum.Y, b.Maximum.Y) - Math.Max(a.Origin.Y, b.Origin.Y) > 1e-9 && Math.Min(a.Maximum.Z, b.Maximum.Z) - Math.Max(a.Origin.Z, b.Origin.Z) > 1e-9)
                    overlaps++;
            }

        if (overlaps > 0)
            Warnings.Add($"模型包含 {overlaps} 对重叠块；FloXML 保留这些矩形块。");
    }
}
