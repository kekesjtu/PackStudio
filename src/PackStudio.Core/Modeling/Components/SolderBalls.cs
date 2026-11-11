using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public static class SolderBalls
{
    public static bool RequiresDiscrete(JObject values) => values["bga.explicit_removal_enabled"].Flag() || values["bga.ball_map_enabled"].Flag();

    public static Footprint Footprint(BuildContext c) => new(
        Span(c.I("bga.columns"), c.N("bga.pitch"), c.N("bga.diameter")),
        Span(c.I("bga.rows"), c.N("bga.pitch"), c.N("bga.diameter")));

    internal static double Span(double count, double pitch, double ballWidth) => (count - 1) * pitch + ballWidth;
    internal static double BlockSide(double diameter) => Math.Sqrt(Math.PI) * diameter / 2;
    internal static double Position(int index, int count, double pitch) => (index - (count - 1) / 2.0) * pitch;

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
            yield return ($"solder-ball-r{row + 1}-c{column + 1}", Position(column, columns, pitch), Position(row, rows, pitch));
    }

    public static int WireCount(BuildContext c) => Count(c.Values);

    internal static int Count(JObject values)
    {
        if (values["bga.ball_map_enabled"].Flag())
            return ((JArray)values["bga.ball_map"]!).Count;
        int nr = values["bga.rows"]!.Value<int>(), nc = values["bga.columns"]!.Value<int>();
        if (values["bga.explicit_removal_enabled"].Flag() && values["bga.omitted_cells"] is JArray { Count: > 0 } omitted)
            return nr * nc - omitted.Count;
        if (!values["bga.solder_removal_enabled"].Flag())
            return nr * nc;
        var(rp, cp) = Populated(values, nr, nc);
        return nr * nc - (nr - rp) * (nc - cp);
    }

    internal static double PopulatedCount(double total, double populated, double removed) =>
        double.IsNaN(populated) ? total - removed : populated;

    static (int Rows, int Columns) Populated(JObject values, int nr, int nc)
    {
        double Count(string axis, int total) => PopulatedCount(total, values["bga.populated_" + axis].Number(double.NaN),
            values["bga.removal_" + axis].Number(double.NaN));
        return ((int)Count("rows", nr), (int)Count("columns", nc));
    }

    static IEnumerable<(int Row, int Column)> Cells(BuildContext c, int nr, int nc)
    {
        bool removal = c.B("bga.solder_removal_enabled");
        var omissions = c.B("bga.explicit_removal_enabled") ? c.Values["bga.omitted_cells"] as JArray : null;
        var (rp, cp) = removal && omissions is not { Count: > 0 } ? Populated(c.Values, nr, nc) : (nr, nc);
        return Cells(nr, nc, rp, cp, c.B("bga.staggered"), omissions);
    }

    internal static IEnumerable<(int Row, int Column)> Cells(int nr, int nc, int rp, int cp, bool staggered, JArray? omissions = null)
    {
        var omitted = (omissions ?? []).Select(x => (x["row"]!.Value<int>(), x["column"]!.Value<int>())).ToHashSet();
        for (int r = 0; r < nr; r++)
            for (int col = 0; col < nc; col++)
                if (omitted.Count > 0 ? !omitted.Contains((nr - 1 - r, col)) :
                    (!staggered || (r + col) % 2 == 0) && (rp == nr || cp == nc || r < rp / 2 || r >= nr - rp / 2 || col < cp / 2 || col >= nc - cp / 2))
                    yield return (r, col);
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
            double lx = Span(nc, pitch, diameter), ly = Span(nr, pitch, diameter);
            var cells = (center ? Cells(nr, nc, nr, nc, staggered) : Cells(c, nr, nc)).ToList();
            count += cells.Count;
            if (!equivalent)
            {
                double side = BlockSide(diameter);
                foreach (var(r, col)in cells)
                    Block($"{id}-r{r + 1}-c{col + 1}", Position(col, nc, pitch), Position(r, nr, pitch), side, side, solder.Id, center);
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
            double side = BlockSide(diameter);
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
