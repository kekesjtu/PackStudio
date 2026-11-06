using System.Windows;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void SlugDiagram()
    {
        Rect(Mold, 190, SectionY - 125, 320, 125);
        Section(SectionY, drawMold: false, wireEnd: 265);
        SlugSection(includeAdhesive: true);
        Callout("散热块 / Slug", 55, 160, 245, 180);
        Callout("支脚", 530, 190, 480, 218);
        Callout("支脚粘接层", 55, 205, 225, 227);
        Line(235, 105, 145, 105); Line(235, 125, 145, 125); Line(150, 105, 150, 125);
        Arrow(150, 105, 0, 1, length: 4); Arrow(150, 125, 0, -1, length: 4);
        Text(Dimension("顶部台阶高度\n", "slug.offset"), 140, 98, align: TextAlignment.Right);
        DimV(125, 153, 465, 565, Dimension("厚度\n", "slug.thickness"));
        DimV(224, 230, 490, 600, Dimension("支脚间隙\n", "slug.clearance"));

        Rect(Board, 200, PlanTop, 300, PlanBottom - PlanTop);
        Rect(Mold, 210, 382, 280, 176);
        Rect(Metal, 215, 414, 270, 112);
        Rect(Metal, 235, 389, 230, 162);
        Rect(Metal, 235, 395, 230, 150);
        Ellipse(Metal, 350, PlanCenterY, 35, 35);
        DimH(315, 385, PlanCenterY, 325, Dimension("顶部直径", "slug.diameter"));
        DimH(215, 485, 389, 355, Dimension("外轮廓长度", "slug.foot_length"));
        DimV(389, 551, 215, 155, Dimension("外轮廓宽度\n", "slug.foot_width"), true);
        DimH(235, 465, 545, PlanLengthDimensionY, Dimension("散热块长度", "slug.length"));
        DimV(395, 545, 465, 550, Dimension("宽度\n", "slug.width"));
        Axes(70, PlanBottom + 4);
        Legend((Mold, "塑封"), (Metal, "散热块 / Slug"), (Board, "基板"), (Attach, "支脚粘接层"));
    }
}
