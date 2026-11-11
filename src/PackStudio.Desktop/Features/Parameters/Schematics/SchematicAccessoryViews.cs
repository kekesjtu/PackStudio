using System.Windows;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void TopCover()
    {
        string type = CoverType;
        if (type is not ("lid" or "plate" or "encapsulant")) return;
        bool encapsulant = type == "encapsulant";
        string prefix = encapsulant ? "cover" : type;
        DimV(encapsulant ? EncapsulantTop : CapTop, encapsulant ? SectionY : CapBottom, 505, 545, prefix + ".thickness");
        DimH(225, 475, 390, 345, prefix + ".length");
        DimV(390, 550, 475, 548, prefix + ".width");
        if (encapsulant) return;
        DimV(CapBottom, CapBottom + 12, 415, 590, prefix + ".die_attach", name: "芯片连接层厚度");
        if (type != "lid") return;
        if (StiffenedLid)
        {
            DimH(StiffenerLeft, 700 - StiffenerLeft, 2 * PlanCenterY - StiffenerTop, PlanLengthDimensionY, "stiffener.length");
            DimV(StiffenerTop, 2 * PlanCenterY - StiffenerTop, StiffenerLeft, 152, "stiffener.width", left: true);
            DimH(StiffenerInnerLeft, 700 - StiffenerInnerLeft, StiffenerInnerTop, 375, "stiffener.cavity_length");
            DimV(StiffenerInnerTop, 2 * PlanCenterY - StiffenerInnerTop, 700 - StiffenerInnerLeft, 635, "stiffener.cavity_width");
            DimV(CapBottom, CapBottom + 6, StiffenerLeft, 125, "lid.adhesive", left: true, name: "顶盖粘接厚度");
            DimV(SectionY - 6, SectionY, 470, 545, "stiffener.adhesive");
        }
        else
        {
            DimH(483, 505, CapTop, 120, "lid.base_thickness");
            DimV(SectionY - 6, SectionY, 505, 545, "lid.adhesive");
        }
    }

    void Spreader()
    {
        Text("底视图", 350, 295, align: TextAlignment.Center);
        DimV(SectionY + 21, SectionY + 30, 430, 560, "spreader.thickness");
        DimH(270, 430, 422, 345, "spreader.length");
        DimV(422, 518, 430, 548, "spreader.width", name: "扩散片宽度");
        DimH(240, 460, 538, PlanLengthDimensionY, "spreader.hole_length");
        DimV(402, 538, 240, 152, "spreader.hole_width", left: true);
    }
}
