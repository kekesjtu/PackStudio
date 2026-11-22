namespace PackStudio.Core;

internal readonly record struct PtaRect(decimal Left, decimal Bottom, decimal Right, decimal Top)
{
    public decimal Width => Right - Left;
    public decimal Height => Top - Bottom;
    public bool Contains(PtaRect r) => Left <= r.Left && Bottom <= r.Bottom && Right >= r.Right && Top >= r.Top;
}

internal sealed record PtaSlice(Block Owner, PtaRect Face, decimal Bottom, decimal Top, PtaRect[] Holes, double Area)
{
    public double Volume => Area * (double)(Top - Bottom);
}

internal static class PtaGeometry
{
    sealed record Box(PtaRect Rect, decimal Bottom, decimal Top);

    static int Priority(Block b) => b.GroupId == "group-backside-spreader" ? 10 :
        b.StructureType == "encapsulant" || b.Id == "dielectric-part-1" ? 100 : 20;

    public static IEnumerable<PtaSlice> Partition(PackageModel model)
    {
        // Round every absolute face on the same decimal lattice, so writing a local offset
        // and a width reconstructs the exact shared face, even across different blocks.
        double extent = model.Blocks.SelectMany(b => b.Origin.Components.Concat(b.Maximum.Components)).Max(Math.Abs);
        int places = Math.Clamp(13 - (int)Math.Floor(Math.Log10(extent)), 0, 28);
        decimal Face(double value) => Math.Round((decimal)value, places);
        var previous = new List<Box>();
        foreach (var b in model.Blocks.OrderBy(Priority).ThenBy(b => b.Size.Volume).ThenBy(b => b.Id, StringComparer.Ordinal))
        {
            var end = b.Maximum;
            var face = new PtaRect(Face(b.Origin.X), Face(b.Origin.Y), Face(end.X), Face(end.Y));
            var box = new Box(face, Face(b.Origin.Z), Face(end.Z));
            if (face.Width <= 0 || face.Height <= 0 || box.Bottom >= box.Top)
                throw new ArgumentException($"块 {b.Id} 的尺寸小于 PTA 导出精度。");
            var cuts = new List<Box>();
            foreach (var other in previous)
            {
                decimal bottom = Math.Max(box.Bottom, other.Bottom), top = Math.Min(box.Top, other.Top);
                if (top <= bottom) continue;
                var r = other.Rect;
                var clip = new PtaRect(Math.Max(face.Left, r.Left), Math.Max(face.Bottom, r.Bottom),
                    Math.Min(face.Right, r.Right), Math.Min(face.Top, r.Top));
                if (clip.Width > 0 && clip.Height > 0) cuts.Add(new(clip, bottom, top));
            }
            previous.Add(box);
            var levels = cuts.SelectMany(c => new[] { c.Bottom, c.Top }).Append(box.Bottom).Append(box.Top).Distinct().Order().ToArray();
            PtaSlice? pending = null;
            for (int i = 1; i < levels.Length; i++)
            {
                decimal low = levels[i - 1], high = levels[i];
                var holes = cuts.Where(c => c.Bottom <= low && c.Top >= high).Select(c => c.Rect).Distinct().ToArray();
                if (holes.Contains(face)) continue;
                holes = holes.Where(r => !holes.Any(h => h != r && h.Contains(r))).ToArray();
                double area = RemainingArea(face, holes);
                if (area <= 0) continue;
                if (pending != null && pending.Top == low && pending.Holes.SequenceEqual(holes))
                    pending = pending with { Top = high };
                else
                {
                    if (pending != null) yield return pending;
                    pending = new(b, face, low, high, holes, area);
                }
            }
            if (pending != null) yield return pending;
        }
    }

    // Sum uncovered strips, so intersecting cutters never remove volume twice.
    static double RemainingArea(PtaRect face, PtaRect[] holes)
    {
        if (holes.Length == 0) return (double)face.Width * (double)face.Height;
        var edges = holes.SelectMany(h => new[] { h.Left, h.Right }).Append(face.Left).Append(face.Right).Distinct().Order().ToArray();
        double area = 0;
        for (int i = 1; i < edges.Length; i++)
        {
            decimal y = face.Bottom;
            double width = (double)(edges[i] - edges[i - 1]);
            foreach (var h in holes.Where(h => h.Left < edges[i] && h.Right > edges[i - 1]).OrderBy(h => h.Bottom))
            {
                area += width * (double)Math.Max(0, h.Bottom - y);
                y = Math.Max(y, h.Top);
            }
            area += width * (double)(face.Top - y);
        }
        return area;
    }
}
