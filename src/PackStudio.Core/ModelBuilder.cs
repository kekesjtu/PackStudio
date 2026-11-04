using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public sealed class ModelBuilder(PackageCatalog catalog)
{
    public PackageModel Generate(ProjectDocument document) => Generate(document.TemplateId, document.Values, document.PresetId, document.Name, document.MaterialAssignments, document.CustomMaterials);

    public PackageModel Generate(string templateId, JObject values, string presetId = "", string? name = null, Dictionary<string, string>? materialAssignments = null, IEnumerable<Material>? custom = null)
    {
        var template = catalog.Load(templateId);
        if (presetId.Length == 0 && template.Presets.Count > 0)
            presetId = values["footprint.size"].Text(template.DefaultPreset);
        var c = new BuildContext(catalog, template, values, presetId, name ?? template.Info.Name, materialAssignments, custom);
        switch (templateId)
        {
            case "bare_die":
                FlipChip.BareDie(c);
                break;
            case "cbga_fc":
            case "pbga_fc":
                FlipChip.Build(c);
                break;
            case "sop":
            case "pqfp":
                LeadframePackages.Build(c);
                break;
            case "qfn":
                Qfn.Build(c);
                break;
            case "chip_array":
            case "pbga_wb":
                WirebondPackages.Build(c);
                break;
            default:
                throw new ArgumentException("未知封装类型。");
        }

        c.Model.Metadata = c.Model.Metadata with { Geometry = PackageGeometry.Evaluate(c), GridEnabled = c.B("grid.enabled"), GridDensity = c.T("grid.density") };
        AuxiliaryGeometry.Build(c);
        return c.Complete();
    }

}
