using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

internal static class ArrayInputRules
{
    public static void ValidateCells(InputChecks c, string path, JArray? cells, double rows, double columns)
    {
        if (cells == null || c.Invalid(path) || !double.IsFinite(rows) || !double.IsFinite(columns)) return;
        for (int i = 0; i < cells.Count; i++)
        {
            if (cells[i] is not JObject cell)
            { c.Check(true, "input.array.cell", "阵列单元必须为对象。", $"{path}[{i}]"); continue; }
            double row = InputChecks.Number(cell["row"]), column = InputChecks.Number(cell["column"]);
            c.Check(!double.IsFinite(row) || !double.IsFinite(column) || row != Math.Truncate(row) || column != Math.Truncate(column) || row < 0 || row >= rows || column < 0 || column >= columns,
                "input.array.bounds", "去除单元必须为阵列范围内的整数行列。", $"{path}[{i}].row", $"{path}[{i}].column");
        }
    }
}
