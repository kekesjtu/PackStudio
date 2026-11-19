using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

internal static class ViaInputRules
{
    public static void Validate(InputChecks c, bool filled = false, string? board = null)
    {
        if (!c.B("vias.enabled")) return;
        c.Check(c.N("vias.diameter") > c.N("vias.pitch"), "input.via.pitch", "通孔直径不能大于节距。", "vias.diameter", "vias.pitch");
        if (!filled)
            c.Check(c.N("vias.plating") <= 0 || c.N("vias.plating") > c.N("vias.diameter") / 2,
                "input.via.plating", "通孔镀层厚度不超过孔半径。", "vias.plating", "vias.diameter");
        if (board == null) return;
        double rows = c.N("vias.rows"), columns = c.N("vias.columns"), pitch = c.N("vias.pitch"), diameter = c.N("vias.diameter");
        if (c.B("vias.removal_enabled") && !ArrayInputRules.ValidateCells(c, "vias.omitted_cells",
            c.Values["vias.omitted_cells"] as JArray, rows, columns)) return;
        if (!double.IsFinite(rows) || !double.IsFinite(columns)) return;
        var (length, width) = Vias.EquivalentFootprint((int)rows, (int)columns, pitch, diameter);
        if (c.T("vias.modeling") is "discrete" or "discreteCuboids")
        {
            length = width = 0;
            double side = SolderBalls.BlockSide(diameter);
            foreach (var p in Vias.DiscretePositions((int)rows, (int)columns, pitch, Vias.Omissions(c.Values)))
            {
                length = Math.Max(length, 2 * Math.Abs(p.X) + side);
                width = Math.Max(width, 2 * Math.Abs(p.Y) + side);
            }
        }
        c.Check(length > c.N(board + ".length") + 1e-10, "input.via.fit", "通孔外缘必须位于基板内。",
            "vias.columns", "vias.pitch", "vias.diameter", board + ".length");
        c.Check(width > c.N(board + ".width") + 1e-10, "input.via.fit", "通孔外缘必须位于基板内。",
            "vias.rows", "vias.pitch", "vias.diameter", board + ".width");
    }
}
