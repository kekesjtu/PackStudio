using PackStudio.Core;

namespace PackStudio.Desktop;
public sealed record PackageChoice(string Id, string Name, string Group, string Description);
public sealed record WizardStep(string Key, string Label);
public static class PackagePresentation
{
    public static readonly PackageChoice[] Choices = [new("cbga_fc", "Flip Chip CBGA", "球栅阵列封装", "陶瓷基板倒装芯片封装"), new("pbga_fc", "Flip Chip PBGA", "球栅阵列封装", "塑料基板倒装芯片封装"), new("pbga_wb", "Wirebond PBGA", "球栅阵列封装", "键合线塑料球栅阵列封装"), new("chip_array", "Chip Array", "芯片级封装", "Fine Pitch BGA（FBGA）、FSBGA"), new("qfn", "QFN", "芯片级封装", "Quad Flat No-Lead（QFN）"), new("pqfp", "PQFP", "周边引脚封装", "PQFP、LQFP、MQFP、TQFP"), new("sop", "SOP", "周边引脚封装", "SOIC、SOP、TSOP、TSSOP"), new("bare_die", "Bare Die", "其他器件", "裸芯片与凸点芯片")];
    public static IEnumerable<string> StepKeys(Template template) => template.Steps.Select(step => step["key"].Text());
}
