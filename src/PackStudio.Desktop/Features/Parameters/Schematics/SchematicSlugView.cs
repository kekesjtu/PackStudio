namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void SlugDiagram()
    {
        Rect(Mold, 190, SlugSectionTop, 320, SectionY - SlugSectionTop);
        Section(SectionY, drawMold: false, wireEnd: 265);
        SlugSection();
        Callout("散热块 / Slug", 55, 160, 245, 180);
        if (Checked("slug.adhesive_enabled")) Callout("支脚粘接层", 55, 205, 225, 227);
        DimV(SlugSectionTop, SlugShoulderTop, 300, 150, "slug.offset", left: true);
        DimV(SlugShoulderTop, SlugWallTop, 235, 188, "slug.thickness", left: true, name: "台肩厚度");
        DimV(SlugSectionTop, SlugSectionTop + SlugDrawnThickness, 400, 560, "slug.thickness", name: "顶部厚度");
        DimH(SlugRightWallLeft, SlugShoulderRight, 176, 166, "slug.thickness", "侧壁厚度");
        DimV(SlugFootTop, SlugFootBottom, 490, 530, "slug.thickness", name: "支脚厚度");
        DimV(SlugFootBottom, SectionY, 490, 610, "slug.clearance");

        const double slugLength = 230, slugWidth = 150;
        const double footStep = 19, footLength = 6, footWidth = 6;
        double slugLeft = 350 - slugLength / 2, slugTop = PlanCenterY - slugWidth / 2;
        double slugRight = slugLeft + slugLength, slugBottom = slugTop + slugWidth;
        double outerLeft = slugLeft - footLength, outerRight = slugRight + footLength;
        double outerTop = slugTop - footWidth, outerBottom = slugBottom + footWidth;
        Rect(Board, 200, PlanTop, 300, PlanBottom - PlanTop);
        Rect(Mold, 210, 382, 280, 176);
        foreach (var (x, y, w, h) in new[]
        {
            (outerLeft, slugTop + footStep, footLength, slugWidth - 2 * footStep),
            (slugRight, slugTop + footStep, footLength, slugWidth - 2 * footStep),
            (slugLeft + footStep, outerTop, slugLength - 2 * footStep, footWidth),
            (slugLeft + footStep, slugBottom, slugLength - 2 * footStep, footWidth)
        })
            Rect(Metal, x, y, w, h);
        Rect(Metal, slugLeft, slugTop, slugLength, slugWidth);
        Ellipse(Metal, 350, PlanCenterY, 35, 35);
        DimH(315, 385, PlanCenterY, 325, "slug.diameter");
        DimH(outerLeft, outerRight, outerTop, 355, "slug.foot_length");
        DimV(outerTop, outerBottom, outerLeft, 155, "slug.foot_width", left: true);
        DimH(slugLeft, slugRight, slugBottom, PlanLengthDimensionY, "slug.length");
        DimV(slugTop, slugBottom, slugRight, 550, "slug.width");
        Axes(70, PlanBottom + 4);
        if (Checked("slug.adhesive_enabled"))
            Legend((Mold, "塑封"), (Metal, "散热块 / Slug"), (Board, "基板"), (Attach, "支脚粘接层"));
        else Legend((Mold, "塑封"), (Metal, "散热块 / Slug"), (Board, "基板"));
    }
}
