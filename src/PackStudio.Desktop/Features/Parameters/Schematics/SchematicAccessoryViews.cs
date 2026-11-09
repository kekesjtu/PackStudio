namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void TopCover()
    {
        string type = Value("cover.type");
        if (type is not ("lid" or "plate" or "encapsulant")) return;
        string prefix = type == "encapsulant" ? "cover" : type;
        DimV(type == "encapsulant" ? SectionY - 100 : CapTop, type == "encapsulant" ? SectionY : CapBottom,
            505, 545, Dimension("顶部厚度", prefix + ".thickness"));
        DimH(225, 475, 390, 345, Dimension("顶部长度", prefix + ".length"));
        DimV(390, 550, 475, 548, Dimension("顶部宽度\n", prefix + ".width"));
        if (type == "encapsulant") return;
        bool stiff = type == "lid" && Enabled("stiffener.enabled");
        if (!stiff)
            DimV(CapBottom, CapBottom + 12, 415, 545, Dimension("连接层厚度", prefix + ".die_attach"));
        if (type != "lid") return;
        double wall = stiff ? 458 : 494;
        if (stiff) DimV(CapBottom, CapBottom + 6, wall, 545, Dimension("顶盖粘接厚度", "lid.adhesive"));
        else DimH(483, 505, CapTop, 120, Dimension("侧壁宽度", "lid.base_thickness"));
        DimV(SectionY - 6, SectionY, wall, 545,
            Dimension(stiff ? "加强环粘接厚度" : "侧壁粘接厚度", stiff ? "stiffener.adhesive" : "lid.adhesive"));
    }

    void Spreader()
    {
        if (!Enabled("spreader.enabled")) return;
        DimV(SectionY + 21, SectionY + 30, 505, 560, Dimension("扩散片厚度\n", "spreader.thickness"));
        DimH(240, 460, 402, 345, Dimension("扩散片长度", "spreader.length"));
        DimV(402, 538, 460, 548, Dimension("宽度\n", "spreader.width"));
    }
}
