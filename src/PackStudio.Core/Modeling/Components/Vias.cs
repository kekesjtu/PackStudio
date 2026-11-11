using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public static class Vias
{
    public static HashSet<(int row, int col)> Omissions(BuildContext c)
    {
        var cells = new HashSet<(int, int)>();
        if (c.TemplateId is not ("pbga_fc" or "pbga_wb") || !c.B("vias.removal_enabled"))
            return cells;
        foreach (var p in (JArray)c.Values["vias.omitted_cells"]!)
            cells.Add(((int)p["row"]!, (int)p["column"]!));
        return cells;
    }

    public static Material Hollow(Material metal, double shell, string id, bool zAxis = false)
    {
        double k = shell * (zAxis ? metal.EffectiveConductivity.Z : metal.EffectiveConductivity.X);
        return metal with
        {
            Id = id,
            Name = id,
            ConductType = 0,
            StoredScalarConductivity = null,
            StoredDirectionalConductivity = null,
            Conductivity = new(k, k, k),
            Density = shell * metal.Density,
            ConductivityCoefficient = null,
            ReferenceTemperature = null
        };
    }

    public static void Grid(BuildContext c, string id, int rows, int cols, double pitch, double side, double z, double height, string material)
    {
        var omitted = Omissions(c);
        for (int r = 0; r < rows; r++)
            for (int col = 0; col < cols; col++)
                if (!omitted.Contains((r, col)))
                    c.Center($"{id}-r{r + 1}-c{col + 1}", "via", side, side, height, z, material, "vias", derived: true, cx: (col - (cols - 1) / 2.0) * pitch, cy: ((rows - 1) / 2.0 - r) * pitch);
    }

    public static void Build(BuildContext c, Material metal, Material matrix, string id, double z, double height, bool fc = false)
    {
        double diameter = c.N("vias.diameter"), plating = c.N("vias.plating"), pitch = c.N("vias.pitch");
        var via = Hollow(metal, 1 - Math.Pow((diameter - 2 * plating) / diameter, 2), id, fc);
        int nr = c.I("vias.rows"), nc = c.I("vias.columns");
        string mode = c.T("vias.modeling");
        if (mode is "discrete" or "discreteCuboids")
        {
            c.Derived(via);
            Grid(c, fc ? "core-via" : "thermal-via", nr, nc, pitch, Math.Sqrt(Math.PI) * diameter / 2, z, height, id);
            return;
        }

        double lx = (nc - 1) * pitch + diameter, ly = (nr - 1) * pitch + diameter;
        double f = (nr * nc - Omissions(c).Count) * Math.PI * diameter * diameter / (4 * lx * ly);
        c.Derived(MaterialMixer.Mix(id, via, matrix, f, mode == "isotropicCuboid" ? "xyz" : "z"));
        c.Center(fc ? "core-vias" : "thermal-via-equivalent", "via", lx, ly, height, z, id, "vias", derived: true);
    }

}
