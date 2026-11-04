using System.Windows;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void SlugDiagram()
    {
        Rect(Mold, 190, SectionY - 125, 320, 125);
        Section(SectionY, drawMold: false, wireEnd: 265);
        SlugSection();
        Callout("散热块 / Slug", 55, 160, 245, 180);
        Callout("支脚", 530, 190, 480, 218);
        Line(235, 105, 145, 105); Line(235, 125, 145, 125); Line(150, 105, 150, 125);
        Arrow(150, 105, 0, 1, length: 4); Arrow(150, 125, 0, -1, length: 4);
        Text(Dimension("顶部台阶高度\n", "slug.offset"), 140, 98, align: TextAlignment.Right);
        DimV(125, 153, 465, 565, Dimension("厚度\n", "slug.thickness"));
        DimV(224, 230, 490, 600, Dimension("支脚间隙\n", "slug.clearance"));

        Rect(Board, 200, 390, 300, 160);
        Rect(Mold, 210, 400, 280, 140);
        Rect(Metal, 215, 425, 270, 90);
        Rect(Metal, 235, 405, 230, 130);
        Rect(Metal, 235, 410, 230, 120);
        Ellipse(Metal, 350, 470, 35, 35);
        DimH(315, 385, 470, 335, Dimension("顶部直径", "slug.diameter"));
        DimH(215, 485, 405, 365, Dimension("外轮廓长度", "slug.foot_length"));
        DimV(405, 535, 215, 155, Dimension("外轮廓宽度\n", "slug.foot_width"), true);
        DimH(235, 465, 530, 579, Dimension("散热块长度", "slug.length"));
        DimV(410, 530, 465, 550, Dimension("宽度\n", "slug.width"));
        Axes(70, 554);
        Legend((Mold, "塑封"), (Metal, "散热块 / Slug"), (Board, "基板"));
    }
}
