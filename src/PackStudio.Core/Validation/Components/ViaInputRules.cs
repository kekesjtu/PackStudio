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
        if (c.Values["vias.configuration"] is not JObject config || !config["removal_enabled"].Flag()) return;
        double rows = c.N("vias.rows"), columns = c.N("vias.columns");
        double removedRows = InputChecks.Number(config["removal_rows"]), removedColumns = InputChecks.Number(config["removal_columns"]);
        foreach (string dimension in new[] { "rows", "columns" })
            c.Check(!double.IsFinite(InputChecks.Number(config["removal_" + dimension])), "input.via.removal.required", "通孔去除需要行数和列数。", "vias.configuration.removal_" + dimension);
        c.Check(removedRows < 0 || removedRows > rows || removedColumns < 0 || removedColumns > columns ||
            double.IsFinite(removedRows) && double.IsFinite(removedColumns) && (removedRows == 0) != (removedColumns == 0),
            "input.via.removal", "通孔去除区域无效。", "vias.configuration.removal_rows", "vias.configuration.removal_columns", "vias.rows", "vias.columns");
        ArrayInputRules.ValidateCells(c, "vias.configuration.omitted_cells", config["omitted_cells"] as JArray, rows, columns);
    }
}
