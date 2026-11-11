using System.Globalization;
using System.Windows;
using System.Windows.Media;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing(PackageDefinition template, ProjectDocument document, string step)
{
    internal const double Width = 700, Height = 580;
    const double SectionY = 230;
    const double PlanTop = 370, PlanBottom = 570, PlanCenterY = (PlanTop + PlanBottom) / 2;
    const double PlanLengthDimensionY = PlanBottom + 29;
    const double PlanLeadSpacing = 30, PlanLeadInner = 20, PlanLeadOuter = 20;
    const double FlipBumpRadius = 7.5;
    static readonly Brush Ink = Brushes.Black, Muted = Brush(Color.FromRgb(85, 85, 85));
    static readonly Brush Die = Brush(PackageColors.Die), Substrate = Brush(PackageColors.Substrate), Metal = Brush(PackageColors.Metal);
    static readonly Brush Mold = Brush(PackageColors.Mold), Solder = Brush(PackageColors.Solder), Attach = Brush(PackageColors.Attach);
    static readonly Brush Bump = Brush(PackageColors.Bump), Ceramic = Brush(PackageColors.Ceramic);
    static readonly Brush WireColor = Brush(PackageColors.Wire);
    static readonly Brush Cover = Brush(PackageColors.Cover), Accent = Brush(PackageColors.Accent);
    DrawingContext dc = null!;
    SchematicProfile Profile => template.Info.Schematic;
    bool Bga => Profile.Bga;
    bool Flip => Profile.Flip;
    bool Bare => Profile.Bare;
    bool Qfn => Profile.Qfn;
    bool Sop => Profile.Sop;
    bool ChipArray => Profile.ChipArray;

    bool CeramicBoard => Profile.Ceramic;
    const int IllustratedLayers = 3;
    Brush Board => CeramicBoard ? Ceramic : Substrate;
    static double FlipDieTop(double substrateTop) => substrateTop - 2 * FlipBumpRadius - 23;
    static double Centered(int index, int count, double pitch, double center = 350) =>
        center + (index - (count - 1) / 2.0) * pitch;
    bool BumpedDie => step == "bumped_die";
    bool ThermalLand => step is "thermal_land" or "thermal_land_solder";
    bool SpreaderSection => step == "backside_spreader";
    bool StiffenedLid => step == "top_cover" && CoverType == "lid" && document.Values["stiffener.enabled"].Flag();
    internal bool HasLocalPackageScene => BumpedDie || ThermalLand || SpreaderSection || StiffenedLid;
    internal string CoverType => Flip ? document.Values["cover.type"].Text() : "";
    JToken? Field(string key) => template.DisplayFields.FirstOrDefault(f =>
        f["key"].Text() == key && f["step"].Text() == step && !f["creation_only"].Flag());

    string? Dimension(string key, string? name = null, string separator = "  ")
    {
        if (Field(key) is not { } field) return null;
        string symbol = TemplateSymbols.Resolve(field, document.Values);
        return (name ?? field["label"].Text()) + (symbol.Length == 0 ? "" : separator + symbol);
    }

    internal DrawingGroup CreatePackageScene()
    {
        var scene = new DrawingGroup();
        using (dc = scene.Open())
        {
            PackageSection();
            Plan();
            Axes(70, PlanBottom + 4);
            PackageLegend();
        }
        scene.Freeze();
        return scene;
    }

    internal DrawingGroup Create(string diagram, DrawingGroup? scene = null)
    {
        var group = new DrawingGroup();
        using (dc = group.Open())
        {
            Rect(Brushes.White, 0, 0, Width, Height, false);
            dc.PushTransform(new TranslateTransform(0, -95));
            switch (diagram)
            {
                case "package": dc.DrawDrawing(scene!); Package(); break;
                case "substrate": SubstrateDetail(); break;
                case "balls": BallArray(); break;
                case "chip_vias": ChipArrayVias(); break;
                case "chip_metal": ChipArrayMetal(); break;
                case "slug": SlugDiagram(); break;
            }
            dc.Pop();
        }
        group.Freeze();
        return group;
    }

    static SolidColorBrush Brush(Color color)
    {
        var result = new SolidColorBrush(color);
        result.Freeze();
        return result;
    }
    void Rect(Brush? fill, double x, double y, double w, double h, bool edge = true) =>
        dc.DrawRectangle(fill, edge ? new Pen(Ink, 1.1) : null, new(x, y, w, h));
    void Line(double x1, double y1, double x2, double y2, Brush? color = null, double thickness = 1) =>
        dc.DrawLine(new Pen(color ?? Ink, thickness), new(x1, y1), new(x2, y2));
    void Ellipse(Brush? fill, double x, double y, double rx, double ry) =>
        dc.DrawEllipse(fill, new Pen(Ink, 1), new(x, y), rx, ry);
    void Text(string text, double x, double y, double size = 13, Brush? color = null,
        TextAlignment align = TextAlignment.Left, bool bold = false)
    {
        var formatted = FormatText(text, size, color ?? Ink, bold);
        dc.DrawText(formatted, new(x - (align == TextAlignment.Center ? formatted.Width / 2 :
            align == TextAlignment.Right ? formatted.Width : 0), y));
    }
    static FormattedText FormatText(string text, double size, Brush color, bool bold = false) =>
        new(text, CultureInfo.GetCultureInfo("zh-CN"), FlowDirection.LeftToRight,
            new Typeface(new FontFamily("Microsoft YaHei UI"), FontStyles.Normal,
                bold ? FontWeights.SemiBold : FontWeights.Normal, FontStretches.Normal), size, color, 1);
    void Arrow(double x, double y, double dx, double dy, Brush? color = null, double length = 7)
    {
        double n = Math.Sqrt(dx * dx + dy * dy);
        dx /= n; dy /= n;
        var geometry = new StreamGeometry();
        using (var c = geometry.Open())
        {
            c.BeginFigure(new(x, y), true, true);
            double halfWidth = length * 3 / 7;
            c.LineTo(new(x + dx * length - dy * halfWidth, y + dy * length + dx * halfWidth), true, false);
            c.LineTo(new(x + dx * length + dy * halfWidth, y + dy * length - dx * halfWidth), true, false);
        }
        dc.DrawGeometry(color ?? Ink, null, geometry);
    }
    void DimH(double x1, double x2, double objectY, double y, string key, string? name = null)
    {
        if (Dimension(key, name) is { } label) DrawDimH(x1, x2, objectY, y, label);
    }
    void DrawDimH(double x1, double x2, double objectY, double y, string label)
    {
        double end = y + (y > objectY ? 5 : -5);
        Line(x1, objectY, x1, end); Line(x2, objectY, x2, end);
        bool narrow = x2 - x1 < 22;
        Line(x1 - (narrow ? 12 : 0), y, x2 + (narrow ? 12 : 0), y);
        Arrow(x1, y, narrow ? -1 : 1, 0); Arrow(x2, y, narrow ? 1 : -1, 0);
        Text(label, (x1 + x2) / 2, y + (y > objectY ? 10 : -25), align: TextAlignment.Center);
    }
    void DimV(double y1, double y2, double objectX, double x, string key, bool left = false, string? name = null,
        double labelOffsetY = 0)
    {
        if (Dimension(key, name, "\n") is { } label) DrawDimV(y1, y2, objectX, x, label, left, labelOffsetY);
    }
    void DrawDimV(double y1, double y2, double objectX, double x, string label, bool left = false, double labelOffsetY = 0)
    {
        double end = x + (x > objectX ? 5 : -5);
        Line(objectX, y1, end, y1); Line(objectX, y2, end, y2);
        bool narrow = y2 - y1 < 22;
        Line(x, y1 - (narrow ? 12 : 0), x, y2 + (narrow ? 12 : 0));
        Arrow(x, y1, 0, narrow ? -1 : 1); Arrow(x, y2, 0, narrow ? 1 : -1);
        Text(label, x + (left ? -10 : 10), (y1 + y2) / 2 - (label.Contains('\n') ? 17 : 9) + labelOffsetY, 13,
            align: left ? TextAlignment.Right : TextAlignment.Left);
    }
    void Callout(string label, double x, double y, double targetX, double targetY, bool arrow = false)
    {
        var text = FormatText(label, 13, Ink);
        dc.DrawText(text, new(x, y));
        const double gap = 7;
        double right = x + text.Width, bottom = y + text.Height;
        double startX = Math.Clamp(targetX, x, right);
        double startY = targetY < y ? y - gap : bottom + gap;
        if (targetY >= y && targetY <= bottom)
        {
            startX = targetX < x ? x - gap : right + gap;
            startY = y + text.Height / 2;
        }
        Line(startX, startY, targetX, targetY);
        if (arrow) Arrow(targetX, targetY, startX - targetX, startY - targetY);
        else dc.DrawEllipse(Ink, null, new(targetX, targetY), 2, 2);
    }
    void DimensionCallout(string key, double x, double y, double targetX, double targetY, bool arrow = false)
    {
        if (Dimension(key) is { } label) Callout(label, x, y, targetX, targetY, arrow);
    }

    void DetailLink(double x, double y, double radius, double detailX, double detailY, string label)
    {
        Ellipse(null, x, y, radius, radius);
        var pen = new Pen(Muted, 1) { DashStyle = DashStyles.Dash };
        double elbowY = (y + radius + detailY) / 2;
        dc.DrawLine(pen, new(x, y + radius), new(x, elbowY));
        dc.DrawLine(pen, new(x, elbowY), new(detailX, elbowY));
        dc.DrawLine(pen, new(detailX, elbowY), new(detailX, detailY));
        Text(label, detailX, detailY + 7, color: Muted, align: TextAlignment.Center);
    }
    void DimensionText(string key, double x, double y, TextAlignment align = TextAlignment.Left, string separator = "  ")
    {
        if (Dimension(key, separator: separator) is { } label) Text(label, x, y, align: align);
    }
    void BracketH(double x1, double x2, double y, string key)
    {
        if (Dimension(key) is not { } label) return;
        Line(x1, y, x2, y);
        Line(x1, y - 5, x1, y + 5); Line(x2, y - 5, x2, y + 5);
        Text(label, (x1 + x2) / 2, y + 8, 13, align: TextAlignment.Center);
    }
    void BracketV(double x, double y1, double y2, string key, double labelY)
    {
        if (Dimension(key) is not { } label) return;
        Line(x, y1, x, y2);
        Line(x - 5, y1, x + 5, y1); Line(x - 5, y2, x + 5, y2);
        Text(label, x - 8, labelY, 13, align: TextAlignment.Right);
    }
    void Axes(double x, double y, string vertical = "Y")
    {
        Line(x, y, x + 34, y, Muted); Arrow(x + 34, y, -1, 0, Muted);
        Line(x, y, x, y - 32, Muted); Arrow(x, y - 32, 0, 1, Muted);
        Text("X", x + 40, y - 10, 11, Muted); Text(vertical, x - 5, y - 51, 11, Muted);
    }
    void Legend(params (Brush Color, string Label)[] entries)
    {
        const double swatchWidth = 14, labelGap = 8, itemGap = 32;
        for (int start = 0; start < entries.Length; start += 3)
        {
            var row = entries.Skip(start).Take(3).ToArray();
            var labels = row.Select(e => FormatText(e.Label, 12, Muted)).ToArray();
            double total = labels.Sum(label => swatchWidth + labelGap + label.Width) + itemGap * (row.Length - 1);
            double x = (Width - total) / 2, y = 630 + start / 3 * 22;
            for (int i = 0; i < row.Length; i++)
            {
                Rect(row[i].Color, x, y + (labels[i].Height - 10) / 2, swatchWidth, 10, false);
                dc.DrawText(labels[i], new(x + swatchWidth + labelGap, y));
                x += swatchWidth + labelGap + labels[i].Width + itemGap;
            }
        }
    }
    void Wire(double x1, double y1, double x2, double y2, double rise = 50)
    {
        var path = new StreamGeometry();
        using (var c = path.Open())
        {
            c.BeginFigure(new(x1, y1), false, false);
            c.BezierTo(new(x1, y1 - rise), new(x2, y2 - rise), new(x2, y2), true, false);
        }
        dc.DrawGeometry(null, new Pen(WireColor, 2.5), path);
    }
}
