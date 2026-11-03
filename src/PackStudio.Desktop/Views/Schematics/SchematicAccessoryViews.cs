using System.Windows.Media;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void TopCover()
    {
        string type = Value("cover.type");
        bool lid = type == "lid", plate = type == "plate", mold = type == "encapsulant";
        string name = lid ? "盖帽 / Lid" : plate ? "盖板 / Plate" : mold ? "塑封体 / Encapsulant" : "裸露芯片 / Bare Die";
        if (mold) Rect(Mold, 195, 160, 310, 100);
        Section(260);
        if (lid || plate)
        {
            Rect(Attach, 285, 200, 130, 12);
            Rect(Cover, 195, 175, 310, 25);
            if (lid)
            {
                bool stiff = Enabled("stiffener.enabled");
                double left = stiff ? 230 : 195, width = stiff ? 24 : 22;
                foreach (double x in new[] { left, 700 - left - width })
                {
                    if (stiff) Rect(Attach, x, 200, width, 6);
                    Rect(stiff ? Metal : Cover, x, stiff ? 206 : 200, width, stiff ? 48 : 54);
                    Rect(Attach, x, 254, width, 6);
                }
                if (stiff) Callout("加强框", 85, 215, 242, 240);
            }
        }
        Callout(name, 330, 123, 350, mold ? 165 : lid || plate ? 182 : 218);
        if (lid || plate || mold)
        {
            string prefix = mold ? "cover" : lid ? "lid" : "plate";
            double top = mold ? 160 : 175, bottom = mold ? 260 : 200;
            DimV(top, bottom, 505, 570, Dimension("顶部厚度\n", prefix + ".thickness"));
            Rect(Board, 190, 420, 320, 140);
            Rect(mold ? Mold : Cover, 215, 432, 270, 116);
            if (lid) Outline(237, 446, 226, 88);
            DimH(215, 485, 548, 589, Dimension("顶部长度", prefix + ".length"));
            DimV(432, 548, 485, 548, Dimension("顶部宽度\n", prefix + ".width"));
            Axes(115, 550);
        }
        else
        {
            Plan();
        }
        if (lid || plate || mold)
            Legend((mold ? Mold : Cover, mold ? "塑封体" : "盖帽 / 盖板"), (Attach, "界面粘接层"), (Board, "基板"));
        else
            Legend((Die, "芯片"), (Solder, "凸点"), (Board, "基板"));
    }

    void Slug()
    {
        Rect(Mold, 190, 145, 320, 125);
        Section(270, drawMold: false, wireEnd: 265);
        Rect(Metal, 300, 145, 100, 28);
        Rect(Metal, 235, 165, 65, 28); Rect(Metal, 400, 165, 65, 28);
        Rect(Metal, 235, 193, 20, 59); Rect(Metal, 445, 193, 20, 59);
        Rect(Metal, 210, 252, 45, 12); Rect(Metal, 445, 252, 45, 12);
        if (Enabled("slug.adhesive_enabled"))
        {
            Rect(Attach, 210, 264, 45, 6); Rect(Attach, 445, 264, 45, 6);
        }
        Callout("散热块", 145, 123, 245, 178);
        Callout("支脚", 520, 131, 465, 258);
        DimH(300, 400, 145, 119, Dimension("顶部直径", "slug.diameter"));
        DimV(165, 193, 465, 565, Dimension("厚度\n", "slug.thickness"));
        DimV(264, 270, 490, 565, Dimension("支脚间隙\n", "slug.clearance"));
        Rect(Mold, 200, 425, 300, 140);
        Rect(Metal, 215, 445, 270, 100);
        Rect(Cover, 240, 430, 220, 130);
        Ellipse(Metal, 350, 495, 42, 42);
        DimH(240, 460, 560, 592, Dimension("散热块长度", "slug.length"));
        DimV(430, 560, 460, 545, Dimension("宽度\n", "slug.width"));
    }

    void Spreader()
    {
        Section(240);
        Rect(Metal, 195, 261, 310, 9);
        Callout("背面扩散片", 110, 310, 205, 266);
        DimV(261, 270, 505, 560, Dimension("厚度\n", "spreader.thickness"));
        Rect(Metal, 210, 443, 280, 120);
        Rect(Brushes.White, 295, 475, 110, 56);
        DimH(295, 405, 475, 420, Dimension("孔长", "spreader.hole_length"));
        DimV(475, 531, 405, 536, Dimension("孔宽\n", "spreader.hole_width"));
        DimH(210, 490, 563, 595, Dimension("扩散片长度", "spreader.length"));
        DimV(443, 563, 210, 162, Dimension("宽度\n", "spreader.width"), true);
    }

}
