using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public sealed class ModelBuilder(PackageCatalog catalog)
{
    public PackageModel Generate(ProjectDocument document) => Generate(document.TemplateId, document.Values, document.Name, document.MaterialAssignments, document.CustomMaterials);

    public PackageModel Generate(string templateId, JObject values, string? name = null, Dictionary<string, string>? materialAssignments = null, IEnumerable<Material>? custom = null)
    {
        var template = catalog.Load(templateId);
        var c = new BuildContext(catalog, template, values, name ?? template.Info.Name, materialAssignments ?? MaterialSelection.Defaults(template), custom);
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

        return c.Complete();
    }

}
