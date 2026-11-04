using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public sealed class BuildContext
{
    public Template Template { get; }
    public JObject Values { get; }
    public ModelAssembly Model { get; }

    readonly IReadOnlyDictionary<string, ModelGroup> catalogGroups;
    readonly Dictionary<string, string> assignments;
    readonly Dictionary<string, Material> customOverrides = [];
    public BuildContext(PackageCatalog catalog, Template template, JObject values, string name, Dictionary<string, string> materialAssignments, IEnumerable<Material>? custom = null)
    {
        Template = template;
        catalogGroups = catalog.Groups;
        Values = (JObject)values.DeepClone();
        template.Validate(Values);
        Model = new(template.Info.Id, name);
        foreach (var m in catalog.Materials.Items.Values)
            Model.Materials[m.Id] = m;
        foreach (var m in (JArray)template.Data["baseline_materials"]!)
        {
            var item = MaterialLibrary.Parse(m);
            Model.Materials[item.Id] = item;
        }

        assignments = MaterialSelection.Resolve(template, materialAssignments);

        foreach (var m in custom ?? [])
        {
            m.Validate();
            Model.Materials[m.Id] = m;
            customOverrides[m.Id] = m;
        }
    }

    public double N(string key) => Values[key]?.Type is JTokenType.Integer or JTokenType.Float ? Values[key]!.Value<double>() : throw new ArgumentException($"{key} 需要数值。");
    public double N(string key, double fallback) => Values[key] == null || Values[key]!.Type == JTokenType.Null ? fallback : N(key);
    public int I(string key)
    {
        double n = N(key);
        if (n != Math.Truncate(n))
            throw new ArgumentException($"{key} 必须为整数。");
        return checked((int)n);
    }

    public bool B(string key) => Values[key].Flag();
    public string T(string key) => Values[key].Text();
    public Material M(string id) => Model.Materials.TryGetValue(id, out var m) ? m : throw new ArgumentException($"未知材料 {id}");
    public Material Component(string group, string fallback) => M(assignments.GetValueOrDefault(group, fallback));
    public void Derived(Material m) => Model.Materials[m.Id] = customOverrides.GetValueOrDefault(m.Id, m);
    public void Add(string id, string type, double x, double y, double z, double sx, double sy, double sz, string material, string group, string? label = null, bool derived = false, bool exposedSurface = false)
    {
        string g = group.StartsWith("group-") ? group : "group-" + group;
        string assigned = derived ? material : assignments.GetValueOrDefault(g, material);
        Model.Blocks.Add(new(id + "-part-1", label ?? id, type, new(x, y, z), new(sx, sy, sz), assigned, g, catalogGroups.TryGetValue(g, out var groupInfo) ? groupInfo.Name : throw new InvalidDataException($"缺少模型分组名称 {g}。"), exposedSurface));
    }

    public void Center(string id, string type, double sx, double sy, double sz, double z, string material, string group, string? label = null, bool derived = false, double cx = 0, double cy = 0, bool exposedSurface = false) => Add(id, type, cx - sx / 2, cy - sy / 2, z, sx, sy, sz, material, group, label, derived, exposedSurface);
    public void Ring(string id, string type, double lx, double ly, double ix, double iy, double z, double h, string mat, string group, bool derived = false)
    {
        if (ix >= lx || iy >= ly || ix < 0 || iy < 0)
            throw new ArgumentException($"{id} 内孔必须位于外轮廓内。");
        double a = (lx - ix) / 2, b = (ly - iy) / 2;
        Add(id + "-left", type, -lx / 2, -ly / 2, z, a, ly, h, mat, group, derived: derived);
        Add(id + "-right", type, ix / 2, -ly / 2, z, a, ly, h, mat, group, derived: derived);
        Add(id + "-lower", type, -ix / 2, -ly / 2, z, ix, b, h, mat, group, derived: derived);
        Add(id + "-upper", type, -ix / 2, iy / 2, z, ix, b, h, mat, group, derived: derived);
    }

    public PackageModel Complete()
    {
        var dies = Model.Blocks.Where(b => b.StructureType == "die").ToList();
        double volume = dies.Sum(b => b.Size.Volume), power = N("die.power");
        if (volume <= 0)
            throw new ArgumentException("模型必须包含芯片。");
        foreach (var die in dies)
            Model.Sources.Add(new(die.Id, power * die.Size.Volume / volume));
        var used = Model.Blocks.Select(b => b.MaterialId).ToHashSet();
        foreach (var id in Model.Materials.Keys.Where(k => !used.Contains(k)).ToList())
            Model.Materials.Remove(id);
        var metadata = new ModelMetadata(PackageGeometry.Evaluate(this))
        {
            GridEnabled = B("grid.enabled"), GridDensity = T("grid.density"), SurfaceRadiation = Template.Info.SurfaceRadiation,
            SolderBallCount = Model.SolderBallCount, SolderBallRepresentation = Model.SolderBallRepresentation, FlipChipBumpCount = Model.FlipChipBumpCount
        };
        var model = new PackageModel(Model.TemplateId, Model.Name, metadata, catalogGroups);
        model.Blocks.AddRange(Model.Blocks);
        foreach (var material in Model.Materials) model.Materials.Add(material.Key, material.Value);
        model.Sources.AddRange(Model.Sources);
        AuxiliaryGeometry.Build(model);
        model.Validate();
        return model;
    }
}
