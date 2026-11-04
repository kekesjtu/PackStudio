namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void TopCover()
    {
        string type = Value("cover.type");
        if (type is not ("lid" or "plate" or "encapsulant")) return;
        string prefix = type == "encapsulant" ? "cover" : type;
        DimV(type == "encapsulant" ? SectionY - 100 : CapTop, type == "encapsulant" ? SectionY : CapBottom,
            505, 570, Dimension("顶部厚度\n", prefix + ".thickness"));
        DimH(225, 475, 405, 365, Dimension("顶部长度", prefix + ".length"));
        DimV(405, 535, 475, 548, Dimension("顶部宽度\n", prefix + ".width"));
    }

    void Slug()
    {
        if (!SlugVisible) return;
        DimH(300, 400, SectionY - 125, SectionY - 145, Dimension("顶部直径", "slug.diameter"));
        DimV(SectionY - 105, SectionY - 77, 465, 565, Dimension("厚度\n", "slug.thickness"));
        DimV(SectionY - 6, SectionY, 490, 565, Dimension("支脚间隙\n", "slug.clearance"));
        DimH(235, 465, 410, 365, Dimension("散热块长度", "slug.length"));
        DimV(410, 530, 465, 545, Dimension("宽度\n", "slug.width"));
    }

    void Spreader()
    {
        if (!Enabled("spreader.enabled")) return;
        DimV(SectionY + 21, SectionY + 30, 505, 560, Dimension("厚度\n", "spreader.thickness"));
        DimH(240, 460, 415, 365, Dimension("扩散片长度", "spreader.length"));
        DimV(415, 525, 460, 548, Dimension("宽度\n", "spreader.width"));
    }
}