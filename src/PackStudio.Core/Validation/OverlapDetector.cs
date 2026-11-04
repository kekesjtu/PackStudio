namespace PackStudio.Core;

public static class OverlapDetector
{
    public static IEnumerable<(Block First, Block Second)> Find(IReadOnlyList<Block> blocks)
    {
        for (int i = 0; i < blocks.Count; i++)
            for (int j = i + 1; j < blocks.Count; j++)
            {
                var a = blocks[i];
                var b = blocks[j];
                if (Math.Min(a.Maximum.X, b.Maximum.X) - Math.Max(a.Origin.X, b.Origin.X) > 1e-9 &&
                    Math.Min(a.Maximum.Y, b.Maximum.Y) - Math.Max(a.Origin.Y, b.Origin.Y) > 1e-9 &&
                    Math.Min(a.Maximum.Z, b.Maximum.Z) - Math.Max(a.Origin.Z, b.Origin.Z) > 1e-9)
                    yield return (a, b);
            }
    }
}
