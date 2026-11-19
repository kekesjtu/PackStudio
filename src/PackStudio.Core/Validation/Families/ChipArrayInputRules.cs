using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

internal static class ChipArrayInputRules
{
    public static void Validate(InputChecks c)
    {
        bool ballPositionsValid = SolderBallInputRules.Validate(c, "package");
        c.Check(c.T("bga.representation") != "discrete", "input.bga.representation", "当前封装不支持所选焊球建模方式。", "bga.representation");
        ViaInputRules.Validate(c, c.B("vias.filled"));
        if (c.B("vias.enabled") && c.T("vias.modeling") == "approximate")
            c.Check(c.N("vias.diameter") > c.N("bga.diameter"), "input.chip_array.via", "近似通孔直径不能大于焊球直径。", "vias.diameter", "bga.diameter", "vias.modeling");
        if (ballPositionsValid && c.B("vias.enabled")) ValidateViaBounds(c);
        ValidateTraceHole(c);
        MetalLayerInputRules.Validate(c, checkSurfaces: true);
        c.Fits("die.length", "package.length");
        c.Fits("die.width", "package.width");
        if (c.B("bond_wire.include")) WireInputRules.ValidateExtent(c, accountForDiameter: true);
        WireInputRules.Equivalent(c, WireCount(c), "bond_wire.total", "bond_wire.auto_count");
    }

    static void ValidateViaBounds(InputChecks c)
    {
        if (c.Invalid("vias.modeling")) return;
        bool approximate = c.T("vias.modeling") == "approximate";
        string diameter = approximate ? "bga.diameter" : "vias.diameter";
        double length = 0, width = 0;
        foreach (var p in Vias.ChipArrayPlacements(c.Values, approximate, c.N))
        {
            length = Math.Max(length, 2 * Math.Abs(p.X) + p.Side);
            width = Math.Max(width, 2 * Math.Abs(p.Y) + p.Side);
        }
        foreach (var (extent, axis, dimension) in new[] { (length, "x", "length"), (width, "y", "width") })
        {
            string board = "package." + dimension;
            c.Check(extent > c.N(board) + 1e-10, "input.via.fit", "通孔外缘必须位于基板内。",
                approximate ? [board, diameter] : [board, diameter, "vias.offset_" + axis]);
        }
    }

    static void ValidateTraceHole(InputChecks c)
    {
        double holeLength = c.N("metal.hole_length"), holeWidth = c.N("metal.hole_width");
        c.Check(double.IsFinite(holeLength) != double.IsFinite(holeWidth), "input.metal.hole_pair",
            "顶层开孔长宽必须成对填写。", "metal.hole_length", "metal.hole_width");
        foreach (string dimension in new[] { "length", "width" })
        {
            string hole = "metal.hole_" + dimension;
            c.Check(c.N(hole) <= 0, "input.metal.hole_size", "开孔尺寸必须为正。", hole);
            c.Fits(hole, "package." + dimension);
        }
    }

    // 自动线数由焊球阵列派生，阵列未就绪时返回 NaN 以跳过等效检查。
    static double WireCount(InputChecks c)
    {
        if (!c.B("bond_wire.auto_count")) return c.N("bond_wire.total");
        if (c.B("bga.ball_map_enabled")) return c.Values["bga.ball_map"] is JArray map ? map.Count : double.NaN;
        if (!double.IsFinite(c.N("bga.rows")) || !double.IsFinite(c.N("bga.columns"))) return double.NaN;
        if (c.B("bga.explicit_removal_enabled") && c.Values["bga.omitted_cells"] is JArray { Count: > 0 }) return SolderBalls.Count(c.Values);
        if (!c.B("bga.solder_removal_enabled")) return c.N("bga.rows") * c.N("bga.columns");
        if (new[] { "bga.populated_rows", "bga.populated_columns", "bga.removal_rows", "bga.removal_columns" }.Any(c.Invalid))
            return double.NaN;
        if (!double.IsFinite(c.N("bga.populated_rows")) && !double.IsFinite(c.N("bga.removal_rows"))) return double.NaN;
        if (!double.IsFinite(c.N("bga.populated_columns")) && !double.IsFinite(c.N("bga.removal_columns"))) return double.NaN;
        return SolderBalls.Count(c.Values);
    }
}
