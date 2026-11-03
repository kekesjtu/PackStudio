using System.Windows;
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
                Rect(Cover, 195, 200, 22, 54); Rect(Cover, 483, 200, 22, 54);
                Rect(Attach, 195, 254, 22, 6); Rect(Attach, 483, 254, 22, 6);
            }
            if (Enabled("stiffener.enabled"))
            {
                Rect(Metal, 230, 220, 24, 40); Rect(Metal, 446, 220, 24, 40);
                Callout("加强框", 130, 318, 242, 240);
            }
        }
        Callout(name, 330, 123, 350, mold ? 165 : lid || plate ? 182 : 218);
        if (lid || plate || mold)
        {
            string prefix = mold ? "cover" : lid ? "lid" : "plate";
            double top = mold ? 160 : 175, bottom = mold ? 260 : 200;
            DimV(top, bottom, 505, 570, Dimension("顶部厚度\n", prefix + ".thickness"));
            Rect(family == "cbga_fc" ? Cover : Substrate, 190, 420, 320, 140);
            Rect(mold ? Mold : Cover, 215, 432, 270, 116);
            if (lid) Outline(237, 446, 226, 88);
            DimH(215, 485, 548, 589, Dimension("顶部长度", prefix + ".length"));
            DimV(432, 548, 485, 548, Dimension("顶部宽度\n", prefix + ".width"));
            Axes(115, 550);
        }
        else
        {
            Plan();
            Text("当前顶部结构为裸露芯片。", 350, 585, 13, Muted, TextAlignment.Center);
        }
        Legend((Cover, "盖帽 / 盖板"), (Attach, "界面粘接层"), (Substrate, "基板"));
    }

    void Slug()
    {
        Rect(Mold, 190, 174, 320, 100);
        Section(274);
        Rect(Metal, 235, 160, 230, 28);
        Rect(Metal, 235, 188, 25, 80); Rect(Metal, 440, 188, 25, 80);
        Rect(Attach, 285, 188, 130, Flip ? 38 : 53);
        Rect(Die, 285, Flip ? 226 : 241, 130, 23);
        Callout("散热块", 320, 119, 350, 170);
        Callout("支脚", 520, 131, 452, 233);
        Callout("芯片接触界面", 100, 153, 305, 207);
        DimV(160, 188, 465, 565, Dimension("厚度\n", "slug.thickness"));
        DimH(415, 440, 245, 342, Dimension("芯片至支脚间隙", "slug.clearance"));
        Rect(Mold, 200, 425, 300, 140);
        Rect(Metal, 230, 439, 240, 110);
        Outline(280, 457, 140, 73);
        Rect(Attach, 232, 441, 24, 106); Rect(Attach, 444, 441, 24, 106);
        DimH(230, 470, 549, 592, Dimension("散热块长度", "slug.length"));
        DimV(439, 549, 470, 545, Dimension("宽度\n", "slug.width"));
        Text(Enabled("slug.enabled") ? "实色：散热块及支脚；虚线：芯片投影。" : "可选组件示意：当前未启用嵌入式散热块。", 350, 632, 12, Muted, TextAlignment.Center);
    }

    void Spreader()
    {
        Section(240);
        Rect(Metal, 195, 270, 310, 9);
        Callout("背面扩散片", 350, 329, 350, 274);
        DimV(270, 279, 505, 560, Dimension("厚度\n", "spreader.thickness"));
        Rect(Metal, 210, 443, 280, 120);
        Rect(Brushes.White, 295, 475, 110, 56);
        DimH(295, 405, 475, 420, Dimension("孔长", "spreader.hole_length"));
        DimV(475, 531, 405, 536, Dimension("孔宽\n", "spreader.hole_width"));
        DimH(210, 490, 563, 595, Dimension("扩散片长度", "spreader.length"));
        DimV(443, 563, 210, 162, Dimension("宽度\n", "spreader.width"), true);
        Text(Enabled("spreader.enabled") ? "背面金属层通过平面扩散增强导热。" : "可选组件示意：当前未启用背面扩散片。", 350, 635, 12, Muted, TextAlignment.Center);
    }

}
