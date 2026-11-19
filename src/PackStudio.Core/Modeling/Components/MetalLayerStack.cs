using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

internal sealed record MetalLayer(string Table, int Index, double Depth, double Thickness, JObject Row, bool FixedDepth)
{
    public double End => Depth + Thickness;
    public string Path => $"{Table}[{Index}]";
}

internal static class MetalLayerStack
{
    public static List<MetalLayer> Read(JObject values, string table, double board, bool surfaceLayers)
    {
        var result = new List<MetalLayer>();
        if (values[table] is not JArray rows) return result;
        for (int i = 0; i < rows.Count; i++)
        {
            if (rows[i] is not JObject row) continue;
            double thickness = Numeric(row["thickness"]), depth = Numeric(row["depth"]);
            bool fixedDepth = surfaceLayers && (i == 0 || i == rows.Count - 1);
            if (fixedDepth) depth = i == 0 ? 0 : board - thickness;
            else if (!surfaceLayers && depth == 0) continue;
            result.Add(new(table, i, depth, thickness, row, fixedDepth));
        }
        return result;
    }

    static double Numeric(JToken? value) => value?.Type is JTokenType.Float or JTokenType.Integer
        ? value.Value<double>() : double.NaN;
}

internal readonly record struct BuildUpStack(double Board, double Upper, double Lower)
{
    public double CoreThickness => Board - (Upper + Lower);
    public double Thickness(string region) => region == "upper" ? Upper : Lower;
    public double StartDepth(string region) => region == "upper" ? 0 : Board - Lower;

    public static BuildUpStack Read(Func<string, bool> enabled, Func<string, double> number)
        => new(number("substrate.thickness"), enabled("upper.enabled") ? number("upper.thickness") : 0,
            enabled("lower.enabled") ? number("lower.thickness") : 0);
}
