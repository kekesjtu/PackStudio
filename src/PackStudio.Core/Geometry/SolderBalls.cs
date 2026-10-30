using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public static class SolderBalls
{
    public static int WireCount(BuildContext c)
    {
        if (c.Bga["ball_map_enabled"].Flag())
            return ((JArray)c.Bga["ball_map"]!).Count;
        int nr = c.I("bga.rows"), nc = c.I("bga.columns");
        if (!c.Bga["solder_removal_enabled"].Flag())
            return nr * nc;
        var(rp, cp) = Populated(c.Bga, nr, nc);
        return nr * nc - (nr - rp) * (nc - cp);
    }

    public static int Count(BuildContext c)
    {
        if (c.Bga["ball_map_enabled"].Flag())
            return ((JArray)c.Bga["ball_map"]!).Count;
        int rows = c.I("bga.rows"), cols = c.I("bga.columns");
        int count = Cells(c.Bga, rows, cols).Count;
        if (c.Bga["center_solder_enabled"].Flag())
        {
            int nr = Required(c.Bga, "center_solder_rows"), nc = Required(c.Bga, "center_solder_columns");
            count += c.Bga["center_staggered"].Flag() ? (nr * nc + 1) / 2 : nr * nc;
        }

        return count;
    }

    static int Required(JObject b, string key) => b[key]?.Type is JTokenType.Integer ? b[key]!.Value<int>() : throw new ArgumentException($"焊球阵列缺少 {key}");
    static (int, int) Populated(JObject b, int nr, int nc)
    {
        int rp = b["populated_rows"]?.Type is JTokenType.Integer ? Required(b, "populated_rows") : nr - Required(b, "removal_rows");
        int cp = b["populated_columns"]?.Type is JTokenType.Integer ? Required(b, "populated_columns") : nc - Required(b, "removal_columns");
        if (rp < 0 || rp > nr || cp < 0 || cp > nc)
            throw new ArgumentException("外围满布行列数超出阵列。");
        return (rp, cp);
    }

    static List<(int r, int col)> Cells(JObject b, int nr, int nc)
    {
        if (nr < 1 || nc < 1 || nr > 300 || nc > 300)
            throw new ArgumentException("焊球阵列行列数无效。");
        var omitted = (b["omitted_cells"] as JArray ?? []).Select(x => (r: Required((JObject)x, "row"), col: Required((JObject)x, "column"))).ToHashSet();
        if (omitted.Any(p => p.r < 0 || p.r >= nr || p.col < 0 || p.col >= nc))
            throw new ArgumentException("显式去球单元超出主阵列。");
        bool removal = b["solder_removal_enabled"].Flag(), explicitCells = removal && omitted.Count > 0;
        var(rp, cp) = removal && !explicitCells ? Populated(b, nr, nc) : (nr, nc);
        var list = new List<(int, int)>();
        for (int r = 0; r < nr; r++)
            for (int col = 0; col < nc; col++)
                if (explicitCells ? !omitted.Contains((nr - 1 - r, col)) : (!b["staggered"].Flag() || (r + col) % 2 == 0) && (rp == nr || cp == nc || r < rp / 2 || r >= nr - rp / 2 || col < cp / 2 || col >= nc - cp / 2))
                    list.Add((r, col));
        return list;
    }

    public static void Build(BuildContext c)
    {
        var b = c.Bga;
        string representation = b["representation"].Text("discrete");
        if (representation is not ("discrete" or "equivalent" or "isotropic") || representation == "isotropic" && c.Template.Info.Id != "pbga_wb" || c.Template.Info.Id == "chip_array" && representation != "discrete")
            throw new ArgumentException("当前封装不支持所选焊球建模方式。");
        double pitch = c.N("bga.pitch"), diameter = c.N("bga.diameter"), h = c.N("bga.height");
        if (diameter > pitch)
            throw new ArgumentException("焊球直径不能大于节距。");
        var solder = c.Component("group-bga-solder", "solder-sn63");
        var air = c.M("static-air");
        bool equivalent = representation != "discrete";
        int count = 0;
        if (equivalent && (b["ball_map_enabled"].Flag() || (b["omitted_cells"] as JArray)?.Count > 0))
            throw new ArgumentException("显式去球及 Ball Map 需要离散建模。");
        void Block(string id, double x, double y, double lx, double ly, string mat, bool center = false) => c.Center(id, "solder_ball", lx, ly, h, 0, mat, center ? "center-solder-ball" : "solder-ball", derived: true, cx: x, cy: y);
        void Region(string id, int nr, int nc, bool staggered, bool center = false)
        {
            double lx = (nc - 1) * pitch + diameter, ly = (nr - 1) * pitch + diameter;
            var cells = center ? (
                from r in Enumerable.Range(0, nr)from col in Enumerable.Range(0, nc)
                where !staggered || (r + col) % 2 == 0
                select (r, col)).ToList() : Cells(b, nr, nc);
            count += cells.Count;
            if (!equivalent)
            {
                double side = Math.Sqrt(Math.PI) * diameter / 2;
                foreach (var(r, col)in cells)
                    Block($"{id}-r{r + 1}-c{col + 1}", (col - (nc - 1) / 2.0) * pitch, (r - (nr - 1) / 2.0) * pitch, side, side, solder.Id, center);
                return;
            }

            bool depop = b["solder_removal_enabled"].Flag() && !center;
            var(rp, cp) = depop ? Populated(b, nr, nc) : (nr, nc);
            double tx = (cp / 2.0 - 1) * pitch + diameter, ty = (rp / 2.0 - 1) * pitch + diameter;
            double area = depop ? lx * ly - (lx - 2 * tx) * (ly - 2 * ty) : lx * ly;
            double n = depop ? nr * nc - (nr - rp) * (nc - cp) : nr * nc;
            double fraction = n * Math.PI * diameter * diameter / (4 * area) * (staggered ? 0.5 : 1);
            var mat = MaterialLibrary.Mix(center ? "solder-ball-center-equivalent" : "solder-ball-equivalent", solder, air, fraction, representation == "isotropic" ? "xyz" : "z", allowOverfilled: true);
            c.Derived(mat);
            if (!depop || rp == nr || cp == nc)
                Block(id, 0, 0, lx, ly, mat.Id, center);
            else
            {
                if (Math.Min(Math.Min(tx, ty), Math.Min(lx - 2 * tx, ly - 2 * ty)) <= 0)
                    throw new ArgumentException("等效焊球边框尺寸必须为正。");
                Block(id + "-left", -(lx - tx) / 2, 0, tx, ly, mat.Id, center);
                Block(id + "-right", (lx - tx) / 2, 0, tx, ly, mat.Id, center);
                Block(id + "-lower", 0, -(ly - ty) / 2, lx - 2 * tx, ty, mat.Id, center);
                Block(id + "-upper", 0, (ly - ty) / 2, lx - 2 * tx, ty, mat.Id, center);
            }
        }

        if (b["ball_map_enabled"].Flag())
        {
            var points = (JArray)b["ball_map"]!;
            if (points.Select(p => p["id"].Text()).Distinct().Count() != points.Count)
                throw new ArgumentException("Ball Map ID 必须唯一。");
            double side = Math.Sqrt(Math.PI) * diameter / 2;
            int index = 0;
            foreach (var p in points)
                Block($"solder-map-{++index}", p["x"].Number(), p["y"].Number(), side, side, solder.Id);
            count = points.Count;
        }
        else
        {
            Region("solder-ball", c.I("bga.rows"), c.I("bga.columns"), b["staggered"].Flag());
            if (b["center_solder_enabled"].Flag())
                Region("center-solder-ball", Required(b, "center_solder_rows"), Required(b, "center_solder_columns"), b["center_staggered"].Flag(), true);
        }

        c.Model.Metadata["solder_ball_count"] = count;
        c.Model.Metadata["solder_ball_representation"] = representation;
    }
}
