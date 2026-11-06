using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public static class MetalLayers
{
    public static JArray Parse(BuildContext c, string key) => c.Values[key] is JArray rows ? (JArray)rows.DeepClone() : [];

    public static void Append(BuildContext c, JArray rows, double lx, double ly, double top, Material metal, Material matrix, string prefix = "trace", bool skipZero = false)
    {
        for (int i = 0; i < rows.Count; i++)
        {
            var r = rows[i];
            if (skipZero && r["depth"].Number() == 0)
                continue;
            string id = $"{prefix}-{i}";
            c.Derived(MaterialMixer.Mix(id, metal, matrix, r["coverage"].Number() / 100));
            c.Center(id, "trace", lx, ly, r["thickness"].Number(), top - r["depth"].Number() - r["thickness"].Number(), id, "traces", derived: true);
        }
    }
}
