using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public static class MetalLayers
{
    public static JArray Parse(BuildContext c, string key)
    {
        JArray rows;
        try
        {
            rows = JArray.Parse(c.T(key));
        }
        catch (Newtonsoft.Json.JsonException)
        {
            throw new ArgumentException("金属层表必须为 JSON 数组。");
        }

        if (rows.Count > 10)
            throw new ArgumentException("金属层表最多 10 行。");
        foreach (var row in rows)
        {
            if (row is not JObject obj || obj.Properties().Any(p => p.Name is not ("depth" or "thickness" or "coverage" or "disconnect")))
                throw new ArgumentException("金属层表列无效。");
            foreach (string k in new[]
            {
                "depth",
                "thickness",
                "coverage"
            }

            )
                if (row[k]?.Type is not (JTokenType.Float or JTokenType.Integer) || !double.IsFinite(row[k].Number()))
                    throw new ArgumentException("金属层表需要有限数值。");
            if (row["depth"].Number() < 0 || row["thickness"].Number() <= 0 || row["coverage"].Number() < 0 || row["coverage"].Number() > 100)
                throw new ArgumentException("金属层深度 ≥ 0、厚度 > 0、覆盖率 0–100%。");
        }

        return rows;
    }

    public static void Append(BuildContext c, JArray rows, double lx, double ly, double top, Material metal, Material matrix, string prefix = "trace", bool skipZero = false)
    {
        for (int i = 0; i < rows.Count; i++)
        {
            var r = rows[i];
            if (skipZero && r["depth"].Number() == 0)
                continue;
            string id = $"{prefix}-{i}";
            c.Derived(MaterialLibrary.Mix(id, metal, matrix, r["coverage"].Number() / 100));
            c.Center(id, "trace", lx, ly, r["thickness"].Number(), top - r["depth"].Number() - r["thickness"].Number(), id, "traces", derived: true);
        }
    }
}
