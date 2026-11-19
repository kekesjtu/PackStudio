namespace PackStudio.Core;

internal sealed record QfnLeadLayout(string RowAxis, string RadialAxis, string RowDimension, string RadialDimension,
    int Count, double Pitch, double Extent, double Body, double Die, double TransverseDie, double End)
{
    public double WireSpan => End - Die / 2;

    public static IEnumerable<QfnLeadLayout> Rows(Func<string, double> number)
    {
        foreach (var (row, radial, along, across) in new[] { ("x", "y", "length", "width"), ("y", "x", "width", "length") })
        {
            double count = number("leads.count_" + row);
            if (!(count > 0)) continue;
            double pitch = number("leads.pitch_" + row), body = number("package." + across);
            yield return new(row, radial, along, across, (int)count, pitch,
                (count - 1) * pitch + number("leads.width"), body, number("die." + across), number("die." + along),
                body / 2 - number("leads.length") - number("leads.etch"));
        }
    }
}
