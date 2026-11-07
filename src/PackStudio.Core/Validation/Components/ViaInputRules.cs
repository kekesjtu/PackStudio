using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

internal static class ViaInputRules
{
    public static void Validate(InputChecks c, bool filled = false)
    {
        if (!c.B("vias.enabled")) return;
        c.Check(c.N("vias.diameter") > c.N("vias.pitch"), "input.via.pitch", "通孔直径不能大于节距。", "vias.diameter", "vias.pitch");
        if (!filled)
            c.Check(c.N("vias.plating") <= 0 || c.N("vias.plating") > c.N("vias.diameter") / 2,
                "input.via.plating", "通孔镀层厚度不超过孔半径。", "vias.plating", "vias.diameter");
        if (!c.B("vias.removal_enabled")) return;
        double rows = c.N("vias.rows"), columns = c.N("vias.columns");
        double removedRows = c.N("vias.removal_rows"), removedColumns = c.N("vias.removal_columns");
        c.Check(removedRows > rows || removedColumns > columns || (removedRows == 0) != (removedColumns == 0),
            "input.via.removal", "通孔去除区域无效。", "vias.removal_rows", "vias.removal_columns", "vias.rows", "vias.columns");
        ArrayInputRules.ValidateCells(c, "vias.omitted_cells", c.Values["vias.omitted_cells"] as JArray, rows, columns);
    }
}
