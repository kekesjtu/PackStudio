namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    const double SlugSectionTop = SectionY - 125;
    const double SlugShoulderTop = SlugSectionTop + 20;
    const double SlugDrawnThickness = 24;
    const double SlugWallTop = SlugShoulderTop + SlugDrawnThickness;
    const double SlugFootBottom = SectionY - 6;
    const double SlugFootTop = SlugFootBottom - SlugDrawnThickness;
    const double SlugShoulderRight = 465;
    const double SlugRightWallLeft = SlugShoulderRight - SlugDrawnThickness;

    const double EncapsulantTop = SectionY - 100;
    const double StiffenerLeft = 230, StiffenerInnerLeft = 254;
    const double StiffenerTop = 398, StiffenerInnerTop = 420;
    double CapBottom => FlipDieTop(SectionY) - 12;
    double CapTop => CapBottom - 25;

    void CoverSection()
    {
        if (CoverType is not ("lid" or "plate")) return;
        Rect(Attach, 285, CapBottom, 130, 12);
        Rect(Cover, 195, CapTop, 310, 25);
        if (CoverType != "lid") return;
        double left = StiffenedLid ? StiffenerLeft : 195;
        double width = StiffenedLid ? StiffenerInnerLeft - StiffenerLeft : 22;
        foreach (double x in new[] { left, 700 - left - width })
        {
            double top = CapBottom + (StiffenedLid ? 6 : 0);
            if (StiffenedLid) Rect(Attach, x, CapBottom, width, 6);
            Rect(StiffenedLid ? Metal : Cover, x, top, width, SectionY - 6 - top);
            Rect(Attach, x, SectionY - 6, width, 6);
        }
    }

    void SlugSection()
    {
        Rect(Metal, 300, SlugSectionTop, 100, SlugDrawnThickness);
        Rect(Metal, 235, SlugShoulderTop, 65, SlugDrawnThickness);
        Rect(Metal, 400, SlugShoulderTop, SlugShoulderRight - 400, SlugDrawnThickness);
        Rect(Metal, 235, SlugWallTop, SlugDrawnThickness, SlugFootTop - SlugWallTop);
        Rect(Metal, SlugRightWallLeft, SlugWallTop, SlugDrawnThickness, SlugFootTop - SlugWallTop);
        double footWidth = 490 - SlugRightWallLeft;
        Rect(Metal, 210, SlugFootTop, footWidth, SlugDrawnThickness);
        Rect(Metal, SlugRightWallLeft, SlugFootTop, footWidth, SlugDrawnThickness);
        Rect(Attach, 210, SlugFootBottom, footWidth, SectionY - SlugFootBottom);
        Rect(Attach, SlugRightWallLeft, SlugFootBottom, footWidth, SectionY - SlugFootBottom);
    }

    void PlanAccessories()
    {
        if (CoverType is "lid" or "plate" or "encapsulant")
            Rect(CoverType == "encapsulant" ? Mold : Cover, 225, 390, 250, 160);
        if (StiffenedLid)
        {
            Rect(Metal, StiffenerLeft, StiffenerTop, 700 - 2 * StiffenerLeft, 2 * (PlanCenterY - StiffenerTop));
            Rect(Cover, StiffenerInnerLeft, StiffenerInnerTop, 700 - 2 * StiffenerInnerLeft, 2 * (PlanCenterY - StiffenerInnerTop));
        }
        if (ThermalLand) Rect(Metal, 255, 395, 190, 150);
    }
}
