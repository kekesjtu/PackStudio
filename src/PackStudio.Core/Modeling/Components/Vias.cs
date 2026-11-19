using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public static class Vias
{
    internal static HashSet<(int row, int col)> Omissions(JObject values)
    {
        if (!values["vias.removal_enabled"].Flag() || values["vias.omitted_cells"] is not JArray cells) return [];
        return cells.Select(p => (p["row"]!.Value<int>(), p["column"]!.Value<int>())).ToHashSet();
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

    internal static IEnumerable<(int Row, int Column, double X, double Y)> DiscretePositions(
        int rows, int columns, double pitch, HashSet<(int, int)> omitted)
    {
        for (int row = 0; row < rows; row++)
            for (int column = 0; column < columns; column++)
                if (!omitted.Contains((row, column)))
                    yield return (row, column, SolderBalls.Position(column, columns, pitch), -SolderBalls.Position(row, rows, pitch));
    }

    internal static Footprint EquivalentFootprint(int rows, int columns, double pitch, double diameter)
        => new(SolderBalls.Span(columns, pitch, diameter), SolderBalls.Span(rows, pitch, diameter));

    internal static IEnumerable<(string Id, double X, double Y, double Side)> ChipArrayPlacements(JObject values, bool approximate, Func<string, double> number)
    {
        double side = SolderBalls.BlockSide(number(approximate ? "bga.diameter" : "vias.diameter"));
        double dx = approximate ? 0 : number("vias.offset_x"), dy = approximate ? 0 : number("vias.offset_y");
        foreach (var p in SolderBalls.MainPositions(values))
            yield return (p.Id.Replace("solder-ball", "thermal-via").Replace("solder-map", "thermal-via-map"), p.X + dx, p.Y + dy, side);
    }

    public static void Build(BuildContext c, Material metal, Material matrix, string id, double z, double height, bool fc = false)
    {
        double diameter = c.N("vias.diameter"), plating = c.N("vias.plating"), pitch = c.N("vias.pitch");
        var via = Hollow(metal, 1 - Math.Pow((diameter - 2 * plating) / diameter, 2), id, fc);
        int nr = c.I("vias.rows"), nc = c.I("vias.columns");
        string mode = c.T("vias.modeling");
        var omitted = c.TemplateId == "qfn" ? [] : Omissions(c.Values);
        if (mode is "discrete" or "discreteCuboids")
        {
            c.Derived(via);
            string prefix = fc ? "core-via" : "thermal-via";
            double side = SolderBalls.BlockSide(diameter);
            foreach (var p in DiscretePositions(nr, nc, pitch, omitted))
                c.Center($"{prefix}-r{p.Row + 1}-c{p.Column + 1}", "via", side, side, height, z, id, "vias", derived: true, cx: p.X, cy: p.Y);
            return;
        }

        var (lx, ly) = EquivalentFootprint(nr, nc, pitch, diameter);
        double f = (nr * nc - omitted.Count) * Math.PI * diameter * diameter / (4 * lx * ly);
        c.Derived(MaterialMixer.Mix(id, via, matrix, f, mode == "isotropicCuboid" ? "xyz" : "z"));
        c.Center(fc ? "core-vias" : "thermal-via-equivalent", "via", lx, ly, height, z, id, "vias", derived: true);
    }

}
