namespace PackStudio.Core;
public static class AuxiliaryGeometry
{
    public static IReadOnlyList<Auxiliary> Build(string templateId, IReadOnlyList<Block> blocks, PackageGeometry geometry)
    {
        var auxiliary = new List<Auxiliary>();
        var die = blocks.First(b => b.StructureType == "die");
        auxiliary.Add(new("monitor_point", "DieJunction_Temp", new(0, 0, die.Origin.Z + die.Size.Z * (geometry.FlippedDie ? 0.005 : 0.995))));
        if (templateId == "bare_die") return auxiliary;
        auxiliary.Add(new("monitor_point", "CaseTemp", new(0, 0, 0.99 * geometry.Height)));
        Region("z_bottom", geometry.Bottom, 0);
        Region("z_top", geometry.Top, geometry.Height);
        return auxiliary;
        void Region(string name, Footprint size, double z) => auxiliary.Add(new("region", name,
            new(-size.Length / 2, -size.Width / 2, z), new(size.Length, size.Width, 1)));
    }
}
