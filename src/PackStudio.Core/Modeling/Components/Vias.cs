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
        if (config["removal_rows"] == null || config["removal_columns"] == null)
            throw new ArgumentException("通孔去除需要行数和列数。");
        int nr = (int)config["removal_rows"]!, nc = (int)config["removal_columns"]!;
        if (nr < 0 || nc < 0 || nr > rows || nc > cols || (nr == 0) != (nc == 0))
            throw new ArgumentException("通孔去除区域无效。");
        foreach (var p in config["omitted_cells"] as JArray ?? [])
            cells.Add(((int)p["row"]!, (int)p["column"]!));
        if (cells.Any(p => p.Item1 < 0 || p.Item1 >= rows || p.Item2 < 0 || p.Item2 >= cols))
            throw new ArgumentException("通孔去除单元超出阵列。");
        for (int r = (rows - nr) / 2; r < (rows - nr) / 2 + nr; r++)
            for (int col = (cols - nc) / 2; col < (cols - nc) / 2 + nc; col++)
                cells.Add((r, col));
        return cells;
    }

    public static Material Hollow(Material metal, double shell, string id, bool zAxis = false)
    {
        if (shell <= 0 || shell > 1)
            throw new ArgumentException("通孔镀层厚度必须大于零且不超过孔半径。");
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
            throw new ArgumentException("通孔直径或阵列无效。");
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
            throw new ArgumentException("通孔尺寸或镀层无效。");
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
