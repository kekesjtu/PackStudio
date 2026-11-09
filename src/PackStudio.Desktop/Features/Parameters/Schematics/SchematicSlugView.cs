using System.Windows;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void SlugDiagram()
    {
        Rect(Mold, 190, SlugSectionTop, 320, SectionY - SlugSectionTop);
        Section(SectionY, drawMold: false, wireEnd: 265);
        SlugSection(includeAdhesive: true);
        Callout("散热块 / Slug", 55, 160, 245, 180);
        Callout("支脚粘接层", 55, 205, 225, 227);
        Line(190, SlugSectionTop, 145, SlugSectionTop);
        Line(150, SlugSectionTop, 150, SlugShoulderTop);
        Arrow(150, SlugSectionTop, 0, 1);
        Arrow(150, SlugShoulderTop, 0, -1);
        Text(Dimension("顶部台阶高度", "slug.offset"), 140, 106, align: TextAlignment.Right);
        DimV(SlugShoulderTop, SlugWallTop, 235, 150, Dimension("台肩厚度", "slug.thickness"), true);
        DimV(SlugSectionTop, SlugSectionTop + SlugDrawnThickness, 400, 560, Dimension("顶部厚度", "slug.thickness"));

        const double wallDimensionY = 176;
        Line(SlugRightWallLeft, wallDimensionY, 535, wallDimensionY);
        Arrow(SlugRightWallLeft, wallDimensionY, 1, 0);
        Arrow(SlugShoulderRight, wallDimensionY, -1, 0);
        Text(Dimension("侧壁厚度", "slug.thickness"), 545, wallDimensionY - 9);
        DimV(SlugFootTop, SlugFootBottom, 490, 530, Dimension("支脚厚度", "slug.thickness"));
        DimV(SlugFootBottom, SectionY, 490, 632, Dimension("支脚间隙\n", "slug.clearance"));

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
        DimH(315, 385, PlanCenterY, 325, Dimension("顶部直径", "slug.diameter"));
        DimH(outerLeft, outerRight, outerTop, 355, Dimension("外轮廓长度", "slug.foot_length"));
        DimV(outerTop, outerBottom, outerLeft, 155, Dimension("外轮廓宽度\n", "slug.foot_width"), true);
        DimH(slugLeft, slugRight, slugBottom, PlanLengthDimensionY, Dimension("散热块长度", "slug.length"));
        DimV(slugTop, slugBottom, slugRight, 550, Dimension("宽度\n", "slug.width"));
        Axes(70, PlanBottom + 4);
        Legend((Mold, "塑封"), (Metal, "散热块 / Slug"), (Board, "基板"), (Attach, "支脚粘接层"));
    }
}
