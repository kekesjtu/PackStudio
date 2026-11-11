using System.Windows.Media;

namespace PackStudio.Desktop;

/// <summary>按组件语义定义的一整套配色，三维视图与示意图共用同一套映射。</summary>
public sealed record Palette(string Id, string Name, Color Die, Color Substrate, Color Ceramic, Color SolderMask,
    Color Metal, Color Mold, Color Solder, Color Attach, Color Bump, Color Wire, Color Cover, Color Accent)
{
    public IReadOnlyList<Color> Sample => [Die, Substrate, Metal, Solder, Mold, Attach];

    public Color ForGroup(string groupId, bool ceramicBoard) => groupId switch
    {
        "group-die" => Die,
        "group-encapsulant" => Mold,
        "group-substrate" or "group-upper" or "group-lower" =>
            ceramicBoard ? Ceramic : Substrate,
        "group-solder-mask" => SolderMask,
        "group-die-attach" or "group-lid-adhesive" or "group-stiffener-adhesive" or
            "group-slug-adhesive" or "group-plate-die-attach" or "group-lid-die-attach" => Attach,
        "group-solder-ball" or "group-thermal-solder" or "group-solder" => Solder,
        "group-flip-chip-bumps" => Bump,
        "group-bond-wires" => Wire,
        "group-lid" or "group-plate" => Cover,
        "group-center-solder-ball" or "group-lead-frame" or "group-die-flag" or "group-tie-bars" or
            "group-vias" or "group-traces" or "group-stiffener" or "group-backside-spreader" or
            "group-slug" or "group-exposed-pad" or "group-thermal-land" => Metal,
        "group-via-disconnect" => Colors.White,
        _ => Colors.LightSlateGray
    };
}
