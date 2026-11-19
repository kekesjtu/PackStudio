namespace PackStudio.Core;

internal static class OuterLeadGeometry
{
    public static double HorizontalLength(double package, double body, double foot, double thickness)
        => (package - body) / 2 - (foot - thickness);

    public static double SopBendHeight(double leadBottom, double thickness) => leadBottom - thickness;
}
