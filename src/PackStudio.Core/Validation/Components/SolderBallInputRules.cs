using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

internal static class SolderBallInputRules
{
    const double FitTolerance = 1e-10;

    public static void Validate(InputChecks c, string board)
    {
        double pitch = c.N("bga.pitch"), diameter = c.N("bga.diameter");
        c.Check(diameter > pitch, "input.bga.pitch", "焊球直径不能大于节距。", "bga.diameter", "bga.pitch");
        bool discrete = c.T("bga.representation") == "discrete";
        if (c.B("bga.ball_map_enabled") || c.B("bga.explicit_removal_enabled"))
            c.Check(!discrete, "input.bga.layout", "启用显式去球或焊球坐标表时，焊球建模方式必须为 Discrete Cuboids（离散建模）。",
                "bga.representation", c.B("bga.ball_map_enabled") ? "bga.ball_map_enabled" : "bga.explicit_removal_enabled");
        if (c.B("bga.ball_map_enabled"))
        {
            ValidateMap(c, board, SolderBalls.BlockSide(diameter));
            return;
        }

        double rows = c.N("bga.rows"), columns = c.N("bga.columns");
        double populatedRows = rows, populatedColumns = columns;
        var omissions = c.B("bga.explicit_removal_enabled") ? c.Values["bga.omitted_cells"] as JArray : null;
        bool explicitCells = omissions is { Count: > 0 };
        bool validCells = !explicitCells || ArrayInputRules.ValidateCells(c, "bga.omitted_cells", omissions, rows, columns);
        if (!explicitCells && c.B("bga.solder_removal_enabled"))
        {
            populatedRows = ReadPopulated(c, "rows", rows);
            populatedColumns = ReadPopulated(c, "columns", columns);
            if (!discrete && populatedRows != rows && populatedColumns != columns)
            {
                double lx = SolderBalls.Span(columns, pitch, diameter), ly = SolderBalls.Span(rows, pitch, diameter);
                double tx = SolderBalls.Span(populatedColumns / 2, pitch, diameter), ty = SolderBalls.Span(populatedRows / 2, pitch, diameter);
                c.Check(Math.Min(Math.Min(tx, ty), Math.Min(lx - 2 * tx, ly - 2 * ty)) <= 0,
                    "input.bga.border", "等效焊球边框尺寸必须为正。",
                    "bga.rows", "bga.columns", "bga.pitch", "bga.diameter",
                    "bga.removal_rows", "bga.removal_columns", "bga.populated_rows", "bga.populated_columns");
            }
        }

        if (validCells && (!explicitCells || discrete))
            ValidateRegion(c, board, "bga.", rows, columns, populatedRows, populatedColumns, discrete, "bga.staggered", omissions);
        if (!c.B("bga.center_solder_enabled")) return;
        double centerRows = c.N("bga.center_solder_rows"), centerColumns = c.N("bga.center_solder_columns");
        foreach (string dimension in new[] { "rows", "columns" })
            c.Check(c.N("bga.center_solder_" + dimension) < 1, "input.bga.center", "中央焊球行列数必须为正整数。", "bga.center_solder_" + dimension);
        ValidateRegion(c, board, "bga.center_solder_", centerRows, centerColumns, centerRows, centerColumns, discrete, "bga.center_staggered");
    }

    static double ReadPopulated(InputChecks c, string axis, double total)
    {
        string populated = "bga.populated_" + axis, removed = "bga.removal_" + axis;
        if (c.Invalid(populated) || c.Invalid(removed)) return double.NaN;
        double count = SolderBalls.PopulatedCount(total, c.N(populated), c.N(removed));
        c.Check(double.IsNaN(count) && double.IsFinite(total), "input.bga.removal.required",
            "请填写外围满布数量或去球数量。", populated, removed);
        c.Check(count < 0 || count > total, "input.bga.removal", "外围满布数量超出阵列。", "bga." + axis, populated, removed);
        return count >= 0 && count <= total ? count : double.NaN;
    }

    static void ValidateMap(InputChecks c, string board, double side)
    {
        if (c.Values["bga.ball_map"] is not JArray map) return;
        var ids = new HashSet<string>();
        for (int i = 0; i < map.Count; i++)
        {
            string path = $"bga.ball_map[{i}]";
            if (map[i] is not JObject point) continue;
            if (!c.Invalid(path + ".id"))
                c.Check(!ids.Add(point["id"].Text()), "input.bga.map.id", "Ball Map ID 必须唯一。", path + ".id");
            foreach (var (axis, dimension) in new[] { ("x", "length"), ("y", "width") })
            {
                string limit = board + "." + dimension;
                double position = InputChecks.Number(point[axis]);
                c.Check(2 * Math.Abs(position) + side > c.N(limit) + FitTolerance, "input.bga.fit",
                    "焊球外缘必须位于基板内。", path + "." + axis, "bga.diameter", limit);
            }
        }
    }

    static void ValidateRegion(InputChecks c, string board, string prefix, double rows, double columns,
        double populatedRows, double populatedColumns, bool discrete, string staggered, JArray? omissions = null)
    {
        double pitch = c.N("bga.pitch"), diameter = c.N("bga.diameter");
        double side = discrete ? SolderBalls.BlockSide(diameter) : diameter;
        string lengthKey = board + ".length", widthKey = board + ".width";
        double length = c.N(lengthKey) + FitTolerance, width = c.N(widthKey) + FitTolerance;
        bool outsideX = columns > 0 && SolderBalls.Span(columns, pitch, side) > length;
        bool outsideY = rows > 0 && SolderBalls.Span(rows, pitch, side) > width;
        if (!outsideX && !outsideY) return;

        if (discrete)
        {
            if (!double.IsFinite(populatedRows) || !double.IsFinite(populatedColumns) || rows < 1 || columns < 1 || c.Invalid(staggered))
                return;
            bool canExceedX = outsideX, canExceedY = outsideY;
            outsideX = outsideY = false;
            foreach (var (row, column) in SolderBalls.Cells((int)rows, (int)columns, (int)populatedRows, (int)populatedColumns, c.B(staggered), omissions))
            {
                outsideX |= canExceedX && 2 * Math.Abs(SolderBalls.Position(column, (int)columns, pitch)) + side > length;
                outsideY |= canExceedY && 2 * Math.Abs(SolderBalls.Position(row, (int)rows, pitch)) + side > width;
                if (outsideX == canExceedX && outsideY == canExceedY) break;
            }
        }

        c.Check(outsideX, "input.bga.fit", "焊球外缘必须位于基板内。", prefix + "columns", "bga.pitch", "bga.diameter", lengthKey);
        c.Check(outsideY, "input.bga.fit", "焊球外缘必须位于基板内。", prefix + "rows", "bga.pitch", "bga.diameter", widthKey);
    }
}
