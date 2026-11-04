namespace PackStudio.Core;

/// <summary>Mutable geometry under construction; published models require completed geometry metadata.</summary>
public sealed class ModelAssembly(string templateId, string name)
{
    public string TemplateId { get; } = templateId;
    public string Name { get; } = name;
    public List<Block> Blocks { get; } = [];
    public Dictionary<string, Material> Materials { get; } = [];
    public List<HeatSource> Sources { get; } = [];
    public int SolderBallCount { get; set; }
    public string SolderBallRepresentation { get; set; } = "";
    public int FlipChipBumpCount { get; set; }
}
