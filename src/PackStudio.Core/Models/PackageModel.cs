using System.Collections.ObjectModel;

namespace PackStudio.Core;

public record Vector(double X, double Y, double Z)
{
    public static Vector operator +(Vector a, Vector b) => new(a.X + b.X, a.Y + b.Y, a.Z + b.Z);
    public double Volume => X * Y * Z;
    public IEnumerable<double> Components => [X, Y, Z];
}

public record Block(string Id, string Name, string StructureType, Vector Origin, Vector Size, string MaterialId, string GroupId, string GroupName, bool ExposedSurface = false)
{
    public Vector Maximum => Origin + Size;
}

public record HeatSource(string BlockId, double Power);

public sealed class PackageModel(string templateId, string name, ModelMetadata metadata,
    IReadOnlyDictionary<string, ModelGroup> groups, IEnumerable<Block> blocks,
    IReadOnlyDictionary<string, Material> materials, IEnumerable<HeatSource> sources, IEnumerable<Auxiliary> auxiliary)
{
    public string TemplateId { get; } = templateId;
    public string Name { get; } = name;
    public IReadOnlyList<Block> Blocks { get; } = Array.AsReadOnly(blocks.ToArray());
    public IReadOnlyDictionary<string, Material> Materials { get; } = new ReadOnlyDictionary<string, Material>(new Dictionary<string, Material>(materials));
    public IReadOnlyList<HeatSource> Sources { get; } = Array.AsReadOnly(sources.ToArray());
    public IReadOnlyList<Auxiliary> Auxiliary { get; } = Array.AsReadOnly(auxiliary.ToArray());
    public ModelMetadata Metadata { get; } = metadata;
    public IReadOnlyDictionary<string, ModelGroup> Groups { get; } = new ReadOnlyDictionary<string, ModelGroup>(new Dictionary<string, ModelGroup>(groups));
    public PackageGeometry Geometry => Metadata.Geometry;
}
