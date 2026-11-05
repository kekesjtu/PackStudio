using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

internal static class MetalLayerInputRules
{
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
