using System.Windows.Media;

namespace PackStudio.Desktop;

internal static class PackageColors
{
    internal static readonly Color Die = Color.FromRgb(0xFF, 0x17, 0x44);
    internal static readonly Color Substrate = Color.FromRgb(0x00, 0xC8, 0x3F);
    internal static readonly Color SolderMask = Color.FromRgb(0x00, 0x6B, 0x32);
    internal static readonly Color Metal = Color.FromRgb(0xFF, 0xA0, 0x00);
    internal static readonly Color Mold = Color.FromRgb(0x39, 0x96, 0xFF);
    internal static readonly Color Solder = Color.FromRgb(0x65, 0x3F, 0xFF);
    internal static readonly Color Attach = Color.FromRgb(0x7A, 0x24, 0x00);
    internal static readonly Color Bump = Color.FromRgb(0x94, 0x77, 0xFF);
    internal static readonly Color Ceramic = Color.FromRgb(0x00, 0xA0, 0x43);
    internal static readonly Color Wire = Color.FromRgb(0xD6, 0x00, 0xC7);
    internal static readonly Color Cover = Color.FromRgb(0x00, 0xB8, 0xD9);
    internal static readonly Color Accent = Color.FromRgb(0x00, 0x57, 0xD9);

    internal static Color ForGroup(string groupId, bool ceramicBoard) => groupId switch
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
