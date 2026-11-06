using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

internal static class ChipArrayInputRules
{
    public static void Validate(InputChecks c)
    {
        SolderBallInputRules.Validate(c, "package");
        c.Check(c.T("bga.representation") != "discrete", "input.bga.representation", "当前封装不支持所选焊球建模方式。", "bga.representation");
        ViaInputRules.Validate(c, c.B("vias.filled"));
        if (c.T("vias.modeling") == "approximate")
            c.Check(c.N("vias.diameter") > c.N("bga.diameter"), "input.chip_array.via", "近似通孔直径不能大于焊球直径。", "vias.diameter", "bga.diameter", "vias.modeling");
        MetalLayerInputRules.Validate(c, checkSurfaces: true);
        c.Fits("die.length", "package.length");
        c.Fits("die.width", "package.width");
        if (c.B("bond_wire.include")) WireInputRules.ValidateExtent(c, accountForDiameter: true);
        WireInputRules.Equivalent(c, WireCount(c), "bond_wire.total", "bond_wire.auto_count");
    }

    // 自动线数由焊球阵列派生，阵列未就绪时返回 NaN 以跳过等效检查。
    static double WireCount(InputChecks c)
    {
        if (!c.B("bond_wire.auto_count")) return c.N("bond_wire.total");
        if (c.B("bga.ball_map_enabled")) return c.Values["bga.ball_map"] is JArray map ? map.Count : double.NaN;
        if (!double.IsFinite(c.N("bga.rows")) || !double.IsFinite(c.N("bga.columns"))) return double.NaN;
        if (!c.B("bga.solder_removal_enabled")) return c.N("bga.rows") * c.N("bga.columns");
        if (c.Values["bga.omitted_cells"] is JArray { Count: > 0 }) return SolderBalls.Count(c.Values);
        if (new[] { "bga.populated_rows", "bga.populated_columns", "bga.removal_rows", "bga.removal_columns" }.Any(c.Invalid))
            return double.NaN;
        if (!double.IsFinite(c.N("bga.populated_rows")) && !double.IsFinite(c.N("bga.removal_rows"))) return double.NaN;
        if (!double.IsFinite(c.N("bga.populated_columns")) && !double.IsFinite(c.N("bga.removal_columns"))) return double.NaN;
        return SolderBalls.Count(c.Values);
    }
}
