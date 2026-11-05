using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public static class Vias
{
    public static HashSet<(int row, int col)> Omissions(BuildContext c, int rows, int cols)
    {
        var config = c.Values["vias.configuration"] as JObject ?? new();
        var cells = new HashSet<(int, int)>();
        if (!config["removal_enabled"].Flag())
            return cells;
        int nr = (int)config["removal_rows"]!, nc = (int)config["removal_columns"]!;
        foreach (var p in config["omitted_cells"] as JArray ?? [])
            cells.Add(((int)p["row"]!, (int)p["column"]!));
        for (int r = (rows - nr) / 2; r < (rows - nr) / 2 + nr; r++)
            for (int col = (cols - nc) / 2; col < (cols - nc) / 2 + nc; col++)
                cells.Add((r, col));
        return cells;
    }

    public static Material Hollow(Material metal, double shell, string id, bool zAxis = false)
    {
        if (shell <= 0 || shell > 1)
            throw new ArgumentException("generation.via.shell");
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
        if (side > pitch || rows < 1 || cols < 1)
            throw new ArgumentException("generation.via.grid");
        var omitted = Omissions(c, rows, cols);
        for (int r = 0; r < rows; r++)
            for (int col = 0; col < cols; col++)
                if (!omitted.Contains((r, col)))
                    c.Center($"{id}-r{r + 1}-c{col + 1}", "via", side, side, height, z, material, "vias", derived: true, cx: (col - (cols - 1) / 2.0) * pitch, cy: ((rows - 1) / 2.0 - r) * pitch);
    }

    public static void Build(BuildContext c, Material metal, Material matrix, string id, double z, double height, bool fc = false)
    {
        double diameter = c.N("vias.diameter"), plating = c.N("vias.plating"), pitch = c.N("vias.pitch");
        if (plating <= 0 || plating > diameter / 2 || diameter > pitch || height <= 0)
            throw new ArgumentException("generation.via.geometry");
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
        double f = (nr * nc - Omissions(c, nr, nc).Count) * Math.PI * diameter * diameter / (4 * lx * ly);
        c.Derived(MaterialMixer.Mix(id, via, matrix, f, mode == "isotropicCuboid" ? "xyz" : "z"));
        c.Center(fc ? "core-vias" : "thermal-via-equivalent", "via", lx, ly, height, z, id, "vias", derived: true);
    }

}
