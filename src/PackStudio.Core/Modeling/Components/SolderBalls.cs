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
        foreach (var (row, column) in Cells(c, rows, columns))
            yield return ($"solder-ball-r{row + 1}-c{column + 1}", (column - (columns - 1) / 2.0) * pitch, (row - (rows - 1) / 2.0) * pitch);
    }

    public static int WireCount(BuildContext c) => Count(c.Values);

    internal static int Count(JObject values)
    {
        if (values["bga.ball_map_enabled"].Flag())
            return ((JArray)values["bga.ball_map"]!).Count;
        int nr = values["bga.rows"]!.Value<int>(), nc = values["bga.columns"]!.Value<int>();
        if (!values["bga.solder_removal_enabled"].Flag())
            return nr * nc;
        if (values["bga.omitted_cells"] is JArray { Count: > 0 } omitted)
            return nr * nc - omitted.Count;
        var(rp, cp) = Populated(values, nr, nc);
        return nr * nc - (nr - rp) * (nc - cp);
    }

    internal static (int Rows, int Columns) Populated(JObject values, int nr, int nc) => (
        values["bga.populated_rows"]?.Type is JTokenType.Integer ? values["bga.populated_rows"]!.Value<int>() : nr - values["bga.removal_rows"]!.Value<int>(),
        values["bga.populated_columns"]?.Type is JTokenType.Integer ? values["bga.populated_columns"]!.Value<int>() : nc - values["bga.removal_columns"]!.Value<int>());

    static List<(int r, int col)> Cells(BuildContext c, int nr, int nc)
    {
        var b = c.Values;
        var omitted = (b["bga.omitted_cells"] as JArray ?? []).Select(x => (r: ((JObject)x)["row"]!.Value<int>(), col: ((JObject)x)["column"]!.Value<int>())).ToHashSet();
        bool removal = b["bga.solder_removal_enabled"].Flag(), explicitCells = removal && omitted.Count > 0;
        var(rp, cp) = removal && !explicitCells ? Populated(c.Values, nr, nc) : (nr, nc);
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
                select (r, col)).ToList() : Cells(c, nr, nc);
            count += cells.Count;
            if (!equivalent)
            {
                double side = Math.Sqrt(Math.PI) * diameter / 2;
                foreach (var(r, col)in cells)
                    Block($"{id}-r{r + 1}-c{col + 1}", (col - (nc - 1) / 2.0) * pitch, (r - (nr - 1) / 2.0) * pitch, side, side, solder.Id, center);
                return;
            }

            bool depop = b["bga.solder_removal_enabled"].Flag() && !center;
            var(rp, cp) = depop ? Populated(c.Values, nr, nc) : (nr, nc);
            double tx = (cp / 2.0 - 1) * pitch + diameter, ty = (rp / 2.0 - 1) * pitch + diameter;
            double area = depop ? lx * ly - (lx - 2 * tx) * (ly - 2 * ty) : lx * ly;
            double n = depop ? nr * nc - (nr - rp) * (nc - cp) : nr * nc;
            double fraction = n * Math.PI * diameter * diameter / (4 * area) * (staggered ? 0.5 : 1);
            var mat = MaterialMixer.Mix(center ? "solder-ball-center-equivalent" : "solder-ball-equivalent", solder, air, fraction, representation == "isotropic" ? "xyz" : "z");
            c.Derived(mat);
            if (!depop || rp == nr || cp == nc)
                Block(id, 0, 0, lx, ly, mat.Id, center);
            else
            {
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
                Region("center-solder-ball", b["bga.center_solder_rows"]!.Value<int>(), b["bga.center_solder_columns"]!.Value<int>(), b["bga.center_staggered"].Flag(), true);
        }

        c.SolderBallCount = count;
        c.SolderBallRepresentation = representation;
    }
}
