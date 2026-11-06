using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

internal static class MetalLayerInputRules
{
    public static void ValidateBuildUp(InputChecks c, string region)
    {
        string table = region + ".layers", thickness = region + ".thickness";
        c.Fits(thickness, "substrate.thickness");
        if (c.Values[table] is not JArray layers) return;
        double board = c.N("substrate.thickness"), height = c.N(thickness);
        double start = region == "upper" ? 0 : board - height;
        double end = region == "upper" ? height : board;
        for (int i = 0; i < layers.Count; i++)
        {
            if (layers[i] is not JObject row) continue;
            string path = $"{table}[{i}]";
            double depth = InputChecks.Number(row["depth"]), layerThickness = InputChecks.Number(row["thickness"]);
            c.Check(depth < start - 1e-10 || depth + layerThickness > end + 1e-10, "input.metal.build_up",
                "金属层必须位于对应的增层内。", path + ".depth", path + ".thickness", thickness, "substrate.thickness");
        }
    }

    public static void Validate(InputChecks c, bool checkSurfaces = false)
    {
        if (c.Invalid("metal.layers") || c.Values["metal.layers"] is not JArray layers) return;
        double substrateThickness = c.N("substrate.thickness");
        for (int i = 0; i < layers.Count; i++)
        {
            string path = $"metal.layers[{i}]";
            c.Check(InputChecks.Number(layers[i]["depth"]) + InputChecks.Number(layers[i]["thickness"]) > substrateThickness + 1e-10,
                "input.metal.layers", "金属层必须位于基板内。", path + ".depth", path + ".thickness", "substrate.thickness");
        }
        if (checkSurfaces && layers.Count >= 2)
            c.Check(InputChecks.Number(layers[0]["thickness"]) + InputChecks.Number(layers[layers.Count - 1]["thickness"]) >= substrateThickness,
                "input.layer.surfaces", "表面金属层总厚度必须小于基板厚度。", "metal.layers[0].thickness", $"metal.layers[{layers.Count - 1}].thickness", "substrate.thickness");
    }
}
