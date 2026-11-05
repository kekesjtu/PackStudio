using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public static class SolderBalls
{
    public static Footprint Footprint(BuildContext c) => new(
        (c.I("bga.columns") - 1) * c.N("bga.pitch") + c.N("bga.diameter"),
        (c.I("bga.rows") - 1) * c.N("bga.pitch") + c.N("bga.diameter"));

    internal static IEnumerable<(string Id, double X, double Y)> MainPositions(BuildContext c)
    {
        if (c.B("bga.ball_map_enabled"))
        {
            var points = (JArray)c.Values["bga.ball_map"]!;
            for (int i = 0; i < points.Count; i++)
                yield return ($"solder-map-{i + 1}", points[i]["x"].Number(), points[i]["y"].Number());
            yield break;
        }
        int rows = c.I("bga.rows"), columns = c.I("bga.columns");
        double pitch = c.N("bga.pitch");
        foreach (var (row, column) in Cells(c.Values, rows, columns))
            yield return ($"solder-ball-r{row + 1}-c{column + 1}", (column - (columns - 1) / 2.0) * pitch, (row - (rows - 1) / 2.0) * pitch);
    }

    public static int WireCount(BuildContext c)
    {
        if (c.Values["bga.ball_map_enabled"].Flag())
            return ((JArray)c.Values["bga.ball_map"]!).Count;
        int nr = c.I("bga.rows"), nc = c.I("bga.columns");
        if (!c.Values["bga.solder_removal_enabled"].Flag())
            return nr * nc;
        var(rp, cp) = Populated(c.Values, nr, nc);
        return nr * nc - (nr - rp) * (nc - cp);
    }

    static int Required(JObject b, string key) => b[key]?.Type is JTokenType.Integer ? b[key]!.Value<int>() : throw new ModelGenerationException("generation.bga.required", $"焊球阵列缺少 {key}。");
    static (int, int) Populated(JObject b, int nr, int nc)
    {
        int rp = b["bga.populated_rows"]?.Type is JTokenType.Integer ? Required(b, "bga.populated_rows") : nr - Required(b, "bga.removal_rows");
        int cp = b["bga.populated_columns"]?.Type is JTokenType.Integer ? Required(b, "bga.populated_columns") : nc - Required(b, "bga.removal_columns");
        return (rp, cp);
    }

    static List<(int r, int col)> Cells(JObject b, int nr, int nc)
    {
        var omitted = (b["bga.omitted_cells"] as JArray ?? []).Select(x => (r: Required((JObject)x, "row"), col: Required((JObject)x, "column"))).ToHashSet();
        bool removal = b["bga.solder_removal_enabled"].Flag(), explicitCells = removal && omitted.Count > 0;
        var(rp, cp) = removal && !explicitCells ? Populated(b, nr, nc) : (nr, nc);
        var list = new List<(int, int)>();
        for (int r = 0; r < nr; r++)
            for (int col = 0; col < nc; col++)
                if (explicitCells ? !omitted.Contains((nr - 1 - r, col)) : (!b["bga.staggered"].Flag() || (r + col) % 2 == 0) && (rp == nr || cp == nc || r < rp / 2 || r >= nr - rp / 2 || col < cp / 2 || col >= nc - cp / 2))
                    list.Add((r, col));
        return list;
    }

    public static void Build(BuildContext c)
    {
        var b = c.Values;
        string representation = b["bga.representation"].Text("discrete");
        double pitch = c.N("bga.pitch"), diameter = c.N("bga.diameter"), h = c.N("bga.height");
        var solder = c.Component("group-bga-solder", "solder-sn63");
        var air = c.M("static-air");
        bool equivalent = representation != "discrete";
        int count = 0;
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

            bool depop = b["bga.solder_removal_enabled"].Flag() && !center;
            var(rp, cp) = depop ? Populated(b, nr, nc) : (nr, nc);
            double tx = (cp / 2.0 - 1) * pitch + diameter, ty = (rp / 2.0 - 1) * pitch + diameter;
            double area = depop ? lx * ly - (lx - 2 * tx) * (ly - 2 * ty) : lx * ly;
            double n = depop ? nr * nc - (nr - rp) * (nc - cp) : nr * nc;
            double fraction = n * Math.PI * diameter * diameter / (4 * area) * (staggered ? 0.5 : 1);
            var mat = MaterialMixer.Mix(center ? "solder-ball-center-equivalent" : "solder-ball-equivalent", solder, air, fraction, representation == "isotropic" ? "xyz" : "z", allowOverfilled: true);
            c.Derived(mat);
            if (!depop || rp == nr || cp == nc)
                Block(id, 0, 0, lx, ly, mat.Id, center);
            else
            {
                if (Math.Min(Math.Min(tx, ty), Math.Min(lx - 2 * tx, ly - 2 * ty)) <= 0)
                    throw new ModelGenerationException("generation.bga.border", "等效焊球边框尺寸必须为正。");
                Block(id + "-left", -(lx - tx) / 2, 0, tx, ly, mat.Id, center);
                Block(id + "-right", (lx - tx) / 2, 0, tx, ly, mat.Id, center);
                Block(id + "-lower", 0, -(ly - ty) / 2, lx - 2 * tx, ty, mat.Id, center);
                Block(id + "-upper", 0, (ly - ty) / 2, lx - 2 * tx, ty, mat.Id, center);
            }
        }

        if (b["bga.ball_map_enabled"].Flag())
        {
            double side = Math.Sqrt(Math.PI) * diameter / 2;
            foreach (var position in MainPositions(c))
            {
                Block(position.Id, position.X, position.Y, side, side, solder.Id);
                count++;
            }
        }
        else
        {
            Region("solder-ball", c.I("bga.rows"), c.I("bga.columns"), b["bga.staggered"].Flag());
            if (b["bga.center_solder_enabled"].Flag())
                Region("center-solder-ball", Required(b, "bga.center_solder_rows"), Required(b, "bga.center_solder_columns"), b["bga.center_staggered"].Flag(), true);
        }

        c.SolderBallCount = count;
        c.SolderBallRepresentation = representation;
    }
}
