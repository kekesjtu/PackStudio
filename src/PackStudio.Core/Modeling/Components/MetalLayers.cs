namespace PackStudio.Core;
public static class MetalLayers
{
    internal static void Append(BuildContext c, IEnumerable<MetalLayer> layers, double lx, double ly, double top, Material metal, Material matrix, string prefix = "trace")
    {
        foreach (var layer in layers)
        {
            string id = $"{prefix}-{layer.Index}";
            c.Derived(MaterialMixer.Mix(id, metal, matrix, layer.Row["coverage"].Number() / 100));
            c.Center(id, "trace", lx, ly, layer.Thickness, top - layer.End, id, "traces", derived: true);
        }
    }
}
