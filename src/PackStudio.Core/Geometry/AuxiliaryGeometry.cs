namespace PackStudio.Core;
public sealed record Auxiliary(string Kind, string Name, Vector Origin, Vector? Size = null);
public static class AuxiliaryGeometry
{
    public static void Build(BuildContext c)
    {
        var model = c.Model;
        string id = model.TemplateId;
        var die = model.Blocks.First(b => b.StructureType == "die");
        bool flipped = (bool)model.Metadata["flipped_die"];
        model.Auxiliary.Add(new("monitor_point", "DieJunction_Temp", new(0, 0, die.Origin.Z + die.Size.Z * (flipped ? 0.005 : 0.995))));
        if (id == "bare_die")
            return;
        double height = Convert.ToDouble(model.Metadata["native_grid_height_mm"]);
        model.Auxiliary.Add(new("monitor_point", "CaseTemp", new(0, 0, 0.99 * height)));
        double l = Convert.ToDouble(model.Metadata["native_grid_length_mm"]), w = Convert.ToDouble(model.Metadata["native_grid_width_mm"]);
        if (c.Values["bga.rows"] != null)
        {
            l = (c.I("bga.columns") - 1) * c.N("bga.pitch") + c.N("bga.diameter");
            w = (c.I("bga.rows") - 1) * c.N("bga.pitch") + c.N("bga.diameter");
        }

        if (id is "pqfp" or "sop" or "qfn")
        {
            l = c.N(id == "sop" ? "body.length" : "package.length");
            w = c.N("package.width");
        }

        model.Auxiliary.Add(new("region", "z_bottom", new(-l / 2, -w / 2, 0), new(l, w, 1)));
        l = die.Size.X;
        w = die.Size.Y;
        if (id is "chip_array" or "qfn")
        {
            l = c.N("package.length");
            w = c.N("package.width");
        }
        else if (id is "pqfp" or "sop" or "pbga_wb")
        {
            string prefix = id == "pbga_wb" ? "encapsulant" : "body";
            l = c.N(prefix + ".length");
            w = c.N(prefix + ".width");
        }
        else
        {
            string prefix = c.T("cover.type") switch
            {
                "lid" => "lid",
                "plate" => "plate",
                "encapsulant" => "cover",
                _ => ""
            };
            if (prefix.Length > 0)
            {
                l = c.N(prefix + ".length");
                w = c.N(prefix + ".width");
            }
        }

        model.Auxiliary.Add(new("region", "z_top", new(-l / 2, -w / 2, height), new(l, w, 1)));
    }
}
