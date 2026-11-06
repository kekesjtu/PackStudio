using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

internal static class SolderBallInputRules
{
    public static void Validate(InputChecks c)
    {
        c.Check(c.N("bga.diameter") > c.N("bga.pitch"), "input.bga.pitch", "焊球直径不能大于节距。", "bga.diameter", "bga.pitch");
        if (c.T("bga.representation") != "discrete" &&
            (c.B("bga.ball_map_enabled") || c.Values["bga.omitted_cells"] is JArray { Count: > 0 }))
            c.Check(true, "input.bga.layout", "显式去球及 Ball Map 需要离散建模。", "bga.representation", "bga.omitted_cells", "bga.ball_map");
        double rows = c.N("bga.rows"), columns = c.N("bga.columns");
        if (c.B("bga.ball_map_enabled") && !c.Invalid("bga.ball_map") && c.Values["bga.ball_map"] is JArray map)
        {
            var ids = new HashSet<string>();
            for (int i = 0; i < map.Count; i++)
            {
                string path = $"bga.ball_map[{i}]";
                if (map[i] is not JObject point)
                { c.Check(true, "input.bga.map", "Ball Map 行必须为对象。", path); continue; }
                c.Check(!ids.Add(point["id"].Text()), "input.bga.map.id", "Ball Map ID 必须唯一。", path + ".id");
                foreach (string axis in new[] { "x", "y" })
                    c.Check(!double.IsFinite(InputChecks.Number(point[axis])), "input.bga.map.coordinate", "Ball Map 坐标必须为有限数值。", path + "." + axis);
            }
        }
        if (!c.B("bga.ball_map_enabled"))
        {
            ArrayInputRules.ValidateCells(c, "bga.omitted_cells", c.Values["bga.omitted_cells"] as JArray, rows, columns);
            if (c.B("bga.solder_removal_enabled") && c.Values["bga.omitted_cells"] is not JArray { Count: > 0 })
            {
                foreach (string dimension in new[] { "rows", "columns" })
                    if (!double.IsFinite(c.N("bga.populated_" + dimension)) && !c.Invalid("bga.populated_" + dimension))
                        c.Check(!double.IsFinite(c.N("bga.removal_" + dimension)), "input.bga.removal.required", "请填写外围满布数量或去球数量。", "bga.removal_" + dimension);
                double populatedRows = double.IsFinite(c.N("bga.populated_rows")) ? c.N("bga.populated_rows") : rows - c.N("bga.removal_rows");
                double populatedColumns = double.IsFinite(c.N("bga.populated_columns")) ? c.N("bga.populated_columns") : columns - c.N("bga.removal_columns");
                c.Check(populatedRows < 0 || populatedRows > rows || populatedColumns < 0 || populatedColumns > columns,
                    "input.bga.removal", "外围满布行列数超出阵列。", "bga.rows", "bga.columns", "bga.populated_rows", "bga.populated_columns", "bga.removal_rows", "bga.removal_columns");
            }
        }
        if (!c.B("bga.ball_map_enabled") && c.B("bga.center_solder_enabled"))
            foreach (string dimension in new[] { "rows", "columns" })
                c.Check(c.N("bga.center_solder_" + dimension) < 1, "input.bga.center", "中央焊球行列数必须为正整数。", "bga.center_solder_" + dimension);
        if (c.T("bga.representation") != "discrete" && c.B("bga.solder_removal_enabled") && !c.B("bga.ball_map_enabled") &&
            c.Values["bga.omitted_cells"] is not JArray { Count: > 0 } &&
            double.IsFinite(c.N("bga.rows")) && double.IsFinite(c.N("bga.columns")) &&
            (double.IsFinite(c.N("bga.populated_rows")) || double.IsFinite(c.N("bga.removal_rows"))) &&
            (double.IsFinite(c.N("bga.populated_columns")) || double.IsFinite(c.N("bga.removal_columns"))))
        {
            var(rp, cp) = SolderBalls.Populated(c.Values, (int)rows, (int)columns);
            if (rp != rows && cp != columns)
            {
                double pitch = c.N("bga.pitch"), diameter = c.N("bga.diameter");
                double lx = (columns - 1) * pitch + diameter, ly = (rows - 1) * pitch + diameter;
                double tx = (cp / 2.0 - 1) * pitch + diameter, ty = (rp / 2.0 - 1) * pitch + diameter;
                c.Check(Math.Min(Math.Min(tx, ty), Math.Min(lx - 2 * tx, ly - 2 * ty)) <= 0,
                    "input.bga.border", "等效焊球边框尺寸必须为正。",
                    "bga.rows", "bga.columns", "bga.pitch", "bga.diameter",
                    "bga.removal_rows", "bga.removal_columns", "bga.populated_rows", "bga.populated_columns");
            }
        }
    }
}
