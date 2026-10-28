using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public sealed class ModelBuilder(PackageCatalog catalog)
{
    public PackageModel Generate(string templateId, JObject values, string presetId = "", string? name = null, JObject? bga = null, Dictionary<string, string>? assignments = null, IEnumerable<Material>? custom = null)
    {
        var template = catalog.Load(templateId);
        if (presetId.Length == 0 && template.Presets.Count > 0)
            presetId = values["footprint.size"].Text(template.DefaultPreset);
        var c = new BuildContext(catalog, template, values, presetId, name ?? template.Info.Name, bga, assignments, custom);
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

        Metadata(c);
        AuxiliaryGeometry.Build(c);
        return c.Complete();
    }

    static void Metadata(BuildContext c)
    {
        string id = c.Template.Info.Id;
        string prefix = id == "bare_die" ? "die" : id == "sop" ? "body" : id is "cbga_fc" or "pbga_fc" ? "substrate" : "package";
        double l = c.N(prefix + ".length"), w = c.N(id == "sop" ? "package.width" : prefix + ".width");
        if (id is "pqfp" or "sop" or "qfn" or "pbga_wb")
            l = w = Math.Max(l, w);
        c.Model.Metadata["native_grid_enabled"] = c.B("grid.enabled");
        c.Model.Metadata["native_grid_density"] = c.T("grid.density");
        c.Model.Metadata["native_grid_length_mm"] = l;
        c.Model.Metadata["native_grid_width_mm"] = w;
        c.Model.Metadata["native_grid_height_mm"] = id == "bare_die" ? c.N("die.thickness") : c.Model.Blocks.Max(b => b.Maximum.Z);
        c.Model.Metadata["flipped_die"] = id is "cbga_fc" or "pbga_fc" || id == "bare_die" && (c.B("die.flipped") || c.B("bumps.enabled"));
    }
}
