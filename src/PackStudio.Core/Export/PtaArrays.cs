namespace PackStudio.Core;

internal sealed record PtaArray(PtaSlice[] Members, int Columns, int Rows, decimal PitchX, decimal PitchY);

internal static class PtaArrays
{
    public static IEnumerable<PtaArray> Layout(IEnumerable<PtaSlice> slices)
    {
        foreach (var group in slices.GroupBy(s => (s.Owner.GroupId, s.Owner.StructureType, s.Owner.MaterialId,
                     s.Face.Width, s.Face.Height, s.Bottom, s.Top)))
        {
            var rows = group.GroupBy(s => s.Face.Bottom).OrderBy(g => g.Key)
                .Select(g => g.OrderBy(s => s.Face.Left).ToArray()).ToArray();
            var xs = rows[0].Select(s => s.Face.Left).ToArray();
            var ys = rows.Select(row => row[0].Face.Bottom).ToArray();
            if (Regular(xs) && Regular(ys) && rows.All(row => row.Select(s => s.Face.Left).SequenceEqual(xs)))
            {
                // PTA enumerates X first, then Y within each column.
                yield return new(rows.SelectMany(row => row).OrderBy(s => s.Face.Left).ThenBy(s => s.Face.Bottom).ToArray(),
                    xs.Length, ys.Length, Pitch(xs), Pitch(ys));
                continue;
            }
            // For sparse or staggered layouts choose the direction needing fewer array operations.
            var horizontal = Runs(group, horizontal: true).ToArray();
            var vertical = Runs(group, horizontal: false).ToArray();
            foreach (var run in horizontal.Length <= vertical.Length ? horizontal : vertical)
                yield return run;
        }
    }

    static IEnumerable<PtaArray> Runs(IEnumerable<PtaSlice> members, bool horizontal)
    {
        decimal Position(PtaSlice s) => horizontal ? s.Face.Left : s.Face.Bottom;
        foreach (var line in members.GroupBy(s => horizontal ? s.Face.Bottom : s.Face.Left).OrderBy(g => g.Key))
        {
            var ordered = line.OrderBy(Position).ToArray();
            int start = 0;
            while (start < ordered.Length)
            {
                int end = Math.Min(start + 2, ordered.Length);
                decimal origin = Position(ordered[start]);
                decimal pitch = end - start == 2 ? Position(ordered[start + 1]) - origin : 0;
                while (end < ordered.Length && Position(ordered[end]) - origin == (end - start) * pitch) end++;
                int count = end - start;
                yield return new(ordered[start..end], horizontal ? count : 1, horizontal ? 1 : count,
                    horizontal ? pitch : 0, horizontal ? 0 : pitch);
                start = end;
            }
        }
    }

    static decimal Pitch(decimal[] values) => values.Length < 2 ? 0 : values[1] - values[0];
    static bool Regular(decimal[] values) => values.Select((v, i) => v - values[0] == i * Pitch(values)).All(v => v);
}
