namespace PackStudio.Core;
public sealed record Auxiliary(string Kind, string Name, Vector Origin, Vector? Size = null);
public static class AuxiliaryGeometry
{
    public static void Build(BuildContext c)
    {
        var model = c.Model;
        var geometry = model.Geometry;
        var die = model.Blocks.First(b => b.StructureType == "die");
        model.Auxiliary.Add(new("monitor_point", "DieJunction_Temp", new(0, 0, die.Origin.Z + die.Size.Z * (geometry.FlippedDie ? 0.005 : 0.995))));
        if (model.TemplateId == "bare_die") return;
        model.Auxiliary.Add(new("monitor_point", "CaseTemp", new(0, 0, 0.99 * geometry.Height)));
        Region("z_bottom", geometry.Bottom, 0);
        Region("z_top", geometry.Top, geometry.Height);
        void Region(string name, Footprint size, double z) => model.Auxiliary.Add(new("region", name,
            new(-size.Length / 2, -size.Width / 2, z), new(size.Length, size.Width, 1)));
    }
}
