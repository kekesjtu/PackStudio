using PackStudio.Core;

namespace PackStudio.Desktop;
public sealed record PackageChoice(string Id, string Name, string Group, string Description);
public sealed record WizardStep(string Key, string Label);
public static class PackagePresentation
{
    public static readonly PackageChoice[] Choices = [new("cbga_fc", "Flip Chip CBGA", "球栅阵列封装", "陶瓷基板倒装芯片封装"), new("pbga_fc", "Flip Chip PBGA", "球栅阵列封装", "塑料基板倒装芯片封装"), new("pbga_wb", "Wirebond PBGA", "球栅阵列封装", "键合线塑料球栅阵列封装"), new("chip_array", "Chip Array", "芯片级封装", "Fine Pitch BGA（FBGA）、FSBGA"), new("qfn", "QFN", "芯片级封装", "Quad Flat No-Lead（QFN）"), new("pqfp", "PQFP", "周边引脚封装", "PQFP、LQFP、MQFP、TQFP"), new("sop", "SOP", "周边引脚封装", "SOIC、SOP、TSOP、TSSOP"), new("bare_die", "Bare Die", "其他器件", "裸芯片与凸点芯片")];
    static readonly Dictionary<string, string[]> StepOrder = new()
    {
        ["chip_array"] = ["overall_package", "die", "encapsulant", "bond_wires", "thermal_vias", "metal_layers", "solder_balls", "modeling"],
        ["bare_die"] = ["die", "bumped_die", "modeling"],
        ["cbga_fc"] = ["package_substrate", "die", "flip_chip_bumps", "solder_balls", "top_cover", "slug", "modeling"],
        ["pbga_fc"] = ["package_substrate", "die", "flip_chip_bumps", "thermal_vias", "metal_layers", "upper_built_up", "lower_built_up", "solder_balls", "top_cover", "slug", "modeling"],
        ["pbga_wb"] = ["package_substrate", "encapsulant", "die_flag_solder_mask", "die", "thermal_vias", "metal_layers", "solder_balls", "slug", "backside_spreader", "modeling"],
        ["qfn"] = ["overall_package", "die", "lead_solder_interconnect", "dap", "bond_wires", "thermal_land", "thermal_vias", "modeling"],
        ["pqfp"] = ["overall_package", "encapsulant", "die", "die_flag_tie_bars", "leadframe", "bond_wires", "thermal_land_solder", "modeling"],
        ["sop"] = ["overall_package", "encapsulant", "die", "die_flag_tie_bars", "leadframe", "bond_wires", "thermal_land_solder", "modeling"]
    };
    public static bool IsCreationOption(string key) => key is "substrate.layers" or "trace.top_thickness" or "trace.bottom_thickness" or "cover.type" or "package.exposed_pad";
    public static IEnumerable<string> StepKeys(Template template)
    {
        var available = template.Fields.Where(f => f["control"].Text() != "configuration")
            .Select(f => f["step"].Text()).Concat(template.MaterialSelections.Select(s => s["step"].Text()))
            .Where(key => key != "package_setup").Distinct().ToList();
        return new[]
        {
            "summary"
        }.Concat(StepOrder[template.Info.Id].Where(available.Contains).SelectMany(key => key == "solder_balls" ? new[] { key, "central_solder_balls", "solder_removal" } : new[] { key })).Concat(available.Where(key => !StepOrder[template.Info.Id].Contains(key) && key is not ("central_solder_balls" or "solder_removal")));
    }
}
