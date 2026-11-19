namespace PackStudio.Core;

internal static class MetalLayerInputRules
{
    public static void Validate(InputChecks c, bool checkSurfaces = false)
    {
        double board = c.N("substrate.thickness");
        var layers = MetalLayerStack.Read(c.Values, "metal.layers", board, checkSurfaces);
        if (!checkSurfaces)
        {
            var stack = BuildUpStack.Read(c.B, c.N);
            foreach (string region in new[] { "upper", "lower" })
            {
                if (!c.B(region + ".enabled")) continue;
                string thickness = region + ".thickness";
                c.Fits(thickness, "substrate.thickness");
                double start = stack.StartDepth(region), end = start + stack.Thickness(region);
                var regionLayers = MetalLayerStack.Read(c.Values, region + ".layers", board, false);
                foreach (var layer in regionLayers)
                    c.Check(layer.Depth < start - 1e-10 || layer.End > end + 1e-10, "input.metal.build_up",
                        "金属层必须位于对应的增层内。", layer.Path + ".depth", layer.Path + ".thickness", thickness, "substrate.thickness");
                layers.AddRange(regionLayers);
            }
        }

        if (checkSurfaces && layers.Count >= 2)
            c.Check(layers[0].Thickness + layers[^1].Thickness >= board, "input.layer.surfaces",
                "表面金属层总厚度必须小于基板厚度。", layers[0].Path + ".thickness", layers[^1].Path + ".thickness", "substrate.thickness");

        for (int i = 0; i < layers.Count; i++)
        {
            var layer = layers[i];
            c.Check(layer.Depth < -1e-10 || layer.End > board + 1e-10, "input.metal.layers",
                "金属层必须位于基板内。", [.. Coordinates(layer), "substrate.thickness"]);
            foreach (var other in layers.Take(i))
                c.Check(Math.Min(layer.End, other.End) - Math.Max(layer.Depth, other.Depth) > 1e-10,
                    "input.metal.overlap", "两层金属的厚度区间重叠。", [.. Coordinates(other), .. Coordinates(layer)]);
        }
    }

    static string[] Coordinates(MetalLayer layer) => layer.FixedDepth ? [layer.Path + ".thickness"]
        : [layer.Path + ".depth", layer.Path + ".thickness"];
}
