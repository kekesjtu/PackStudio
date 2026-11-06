namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    bool SlugVisible => Enabled("slug.enabled") && (Wirebond || Flip && Value("cover.type") == "encapsulant");
    double CapBottom => FlipDieTop(SectionY) - 12;
    double CapTop => CapBottom - 25;

    void CoverSection()
    {
        if (!Flip || Value("cover.type") is not ("lid" or "plate")) return;
        Rect(Attach, 285, CapBottom, 130, 12);
        Rect(Cover, 195, CapTop, 310, 25);
        if (Value("cover.type") != "lid") return;
        bool stiff = Enabled("stiffener.enabled");
        double left = stiff ? 230 : 195, width = stiff ? 24 : 22;
        foreach (double x in new[] { left, 700 - left - width })
        {
            double top = CapBottom + (stiff ? 6 : 0);
            if (stiff) Rect(Attach, x, CapBottom, width, 6);
            Rect(stiff ? Metal : Cover, x, top, width, SectionY - 6 - top);
            Rect(Attach, x, SectionY - 6, width, 6);
        }
    }

    void SlugSection(bool includeAdhesive = false)
    {
        double y = SectionY;
        Rect(Metal, 300, y - 125, 100, 28);
        Rect(Metal, 235, y - 105, 65, 28); Rect(Metal, 400, y - 105, 65, 28);
        Rect(Metal, 235, y - 77, 20, 59); Rect(Metal, 445, y - 77, 20, 59);
        Rect(Metal, 210, y - 18, 45, 12); Rect(Metal, 445, y - 18, 45, 12);
        if (includeAdhesive || Enabled("slug.adhesive_enabled"))
        {
            Rect(Attach, 210, y - 6, 45, 6); Rect(Attach, 445, y - 6, 45, 6);
        }
    }

    void PlanAccessories()
    {
        if (Flip && Value("cover.type") is "lid" or "plate" or "encapsulant")
            Rect(Value("cover.type") == "encapsulant" ? Mold : Cover, 225, 390, 250, 160);
        if (SlugVisible)
        {
            Rect(Metal, 235, 395, 230, 150);
            Ellipse(Metal, 350, PlanCenterY, 45, 45);
        }
        if (Wirebond && Enabled("spreader.enabled")) Rect(Metal, 240, 402, 220, 136);
        if (!Bga && Enabled("thermal_land.enabled")) Rect(Solder, 255, 395, 190, 150);
    }
}
