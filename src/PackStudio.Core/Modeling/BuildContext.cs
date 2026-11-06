using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public sealed class BuildContext
{
    public PackageDefinition Template { get; }
    public JObject Values { get; }
    public string TemplateId => Template.Info.Id;
    public string Name { get; }
    public List<Block> Blocks { get; } = [];
    public Dictionary<string, Material> Materials { get; } = [];
    public List<HeatSource> Sources { get; } = [];
    public int SolderBallCount { get; set; }
    public string SolderBallRepresentation { get; set; } = "";
    public int FlipChipBumpCount { get; set; }

    readonly IReadOnlyDictionary<string, ModelGroup> catalogGroups;
    readonly Dictionary<string, string> assignments;
    readonly Dictionary<string, Material> customOverrides = [];
    readonly HashSet<string> derivedMaterialIds = [];
    internal IReadOnlySet<string> DerivedMaterialIds => derivedMaterialIds;
    public BuildContext(PackageDefinition template, JObject values, string name, MaterialCatalog materials,
        IReadOnlyDictionary<string, ModelGroup> groups, Dictionary<string, string> materialAssignments, IEnumerable<Material>? custom = null)
    {
        Template = template;
        Name = name;
        catalogGroups = groups;
        Values = (JObject)values.DeepClone();
        foreach (var m in materials.Items.Values) Materials[m.Id] = m;
        assignments = new(materialAssignments);
        foreach (var m in custom ?? [])
        {
            Materials[m.Id] = m;
            customOverrides[m.Id] = m;
        }
    }

    public double N(string key) => Values[key]!.Value<double>();
    public double N(string key, double fallback) => Values[key] == null || Values[key]!.Type == JTokenType.Null ? fallback : N(key);
    public int I(string key) => checked((int)N(key));

    public bool B(string key) => Values[key].Flag();
    public string T(string key) => Values[key].Text();
    public Material M(string id) => Materials[id];
    public Material Component(string group, string fallback) => M(assignments.GetValueOrDefault(group, fallback));
    public void Derived(Material m)
    {
        if (customOverrides.TryGetValue(m.Id, out var custom))
            Materials[m.Id] = custom;
        else
        {
            Materials[m.Id] = m;
            derivedMaterialIds.Add(m.Id);
        }
    }
    public void Add(string id, string type, double x, double y, double z, double sx, double sy, double sz, string material, string group, string? label = null, bool derived = false)
    {
        string g = group.StartsWith("group-") ? group : "group-" + group;
        string assigned = derived ? material : assignments.GetValueOrDefault(g, material);
        Blocks.Add(new(id + "-part-1", label ?? id, type, new(x, y, z), new(sx, sy, sz), assigned, g, catalogGroups.TryGetValue(g, out var groupInfo) ? groupInfo.Name : throw new InvalidDataException($"缺少模型分组名称 {g}。")));
    }

    public void Center(string id, string type, double sx, double sy, double sz, double z, string material, string group, string? label = null, bool derived = false, double cx = 0, double cy = 0) => Add(id, type, cx - sx / 2, cy - sy / 2, z, sx, sy, sz, material, group, label, derived);
    public void Ring(string id, string type, double lx, double ly, double ix, double iy, double z, double h, string mat, string group, bool derived = false)
    {
        double a = (lx - ix) / 2, b = (ly - iy) / 2;
        Add(id + "-left", type, -lx / 2, -ly / 2, z, a, ly, h, mat, group, derived: derived);
        Add(id + "-right", type, ix / 2, -ly / 2, z, a, ly, h, mat, group, derived: derived);
        Add(id + "-lower", type, -ix / 2, -ly / 2, z, ix, b, h, mat, group, derived: derived);
        Add(id + "-upper", type, -ix / 2, iy / 2, z, ix, b, h, mat, group, derived: derived);
    }

    public void DistributeDiePower()
    {
        var dies = Blocks.Where(b => b.StructureType == "die").ToList();
        double volume = dies.Sum(b => b.Size.Volume), power = N("die.power");
        if (volume <= 0) throw new ModelGenerationException("generation.die", "模型必须包含芯片。");
        foreach (var die in dies) Sources.Add(new(die.Id, power * die.Size.Volume / volume));
    }

    public PackageModel Complete(PackageGeometry geometry)
    {
        var used = Blocks.Select(b => b.MaterialId).ToHashSet();
        var materials = Materials.Where(p => used.Contains(p.Key)).ToDictionary(p => p.Key, p => p.Value);
        var metadata = new ModelMetadata(geometry)
        {
            GridEnabled = B("grid.enabled"), GridDensity = T("grid.density"),
            SolderBallCount = SolderBallCount, SolderBallRepresentation = SolderBallRepresentation, FlipChipBumpCount = FlipChipBumpCount
        };
        return new(TemplateId, Name, metadata, catalogGroups, Blocks, materials, Sources);
    }
}
