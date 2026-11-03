using System.Globalization;
using System.Windows;
using System.Windows.Media;
using PackStudio.Core;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing(Template template, ProjectDocument document, string step)
{
    internal const double Width = 700, Height = 580;
    static readonly Brush Ink = Brushes.Black, Muted = Brush("#555555");
    static readonly Brush Die = Brush("#FF1744"), Substrate = Brush("#00C83F"), Metal = Brush("#FFA000");
    static readonly Brush Mold = Brush("#3996FF"), Solder = Brush("#653FFF"), Attach = Brush("#FFE000");
    static readonly Brush Cover = Brush("#00B8D9"), Accent = Brush("#0057D9");
    readonly string family = document.TemplateId;
    DrawingContext dc = null!;
    bool Bga => family is "cbga_fc" or "pbga_fc" or "pbga_wb" or "chip_array";
    bool Flip => family is "cbga_fc" or "pbga_fc";
    bool Bare => family == "bare_die";
    bool Qfn => family == "qfn";
    bool Sop => family == "sop";
    bool FlagStep => step is "die_flag_solder_mask" or "die_flag_tie_bars" or "dap";
    Brush Board => family == "cbga_fc" ? Cover : Substrate;
    static double Centered(int index, int count, double pitch, double center = 350) =>
        center + (index - (count - 1) / 2.0) * pitch;
    bool Enabled(string key) => document.Values[key].Flag();
    string Value(string key) => document.Values[key].Text();
    string Symbol(string key, string fallback = "")
    {
        var field = template.Fields.FirstOrDefault(f => f["key"].Text() == key);
        return field == null ? fallback : DesFieldLabels.Symbol(field, Value("substrate.layers"));
    }
    string Dimension(string name, string key, string fallback = "")
    {
        string symbol = Symbol(key, fallback);
        return name + (symbol.Length == 0 ? "" : "  " + symbol);
    }

    internal DrawingGroup Create(string diagram)
    {
        var group = new DrawingGroup();
        using (dc = group.Open())
        {
            Rect(Brushes.White, 0, 0, Width, Height, false);
            dc.PushTransform(new TranslateTransform(0, -95));
            switch (diagram)
            {
                case "package": Package(); break;
                case "substrate": SubstrateDetail(); break;
                case "balls": BallArray(); break;
                case "bumps": Bumps(); break;
                case "leads": Leads(); break;
                case "wires": Wires(); break;
                case "cover": TopCover(); break;
                case "slug": Slug(); break;
                case "spreader": Spreader(); break;
            }
            dc.Pop();
        }
        group.Freeze();
        return group;
    }

    static SolidColorBrush Brush(string color)
    {
        var result = new SolidColorBrush((Color)ColorConverter.ConvertFromString(color));
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
        var formatted = new FormattedText(text, CultureInfo.GetCultureInfo("zh-CN"), FlowDirection.LeftToRight,
            new Typeface(new FontFamily("Microsoft YaHei UI"), FontStyles.Normal,
                bold ? FontWeights.SemiBold : FontWeights.Normal, FontStretches.Normal), size, color ?? Ink, 1);
        dc.DrawText(formatted, new(x - (align == TextAlignment.Center ? formatted.Width / 2 :
            align == TextAlignment.Right ? formatted.Width : 0), y));
    }
    void Arrow(double x, double y, double dx, double dy, Brush? color = null)
    {
        double n = Math.Sqrt(dx * dx + dy * dy);
        dx /= n; dy /= n;
        var geometry = new StreamGeometry();
        using (var c = geometry.Open())
        {
            c.BeginFigure(new(x, y), true, true);
            c.LineTo(new(x + dx * 7 - dy * 3, y + dy * 7 + dx * 3), true, false);
            c.LineTo(new(x + dx * 7 + dy * 3, y + dy * 7 - dx * 3), true, false);
        }
        dc.DrawGeometry(color ?? Ink, null, geometry);
    }
    void DimH(double x1, double x2, double objectY, double y, string label)
    {
        double end = y + (y > objectY ? 5 : -5);
        Line(x1, objectY, x1, end); Line(x2, objectY, x2, end);
        bool narrow = x2 - x1 < 22;
        Line(x1 - (narrow ? 12 : 0), y, x2 + (narrow ? 12 : 0), y);
        Arrow(x1, y, narrow ? -1 : 1, 0); Arrow(x2, y, narrow ? 1 : -1, 0);
        Text(label, (x1 + x2) / 2, y + (y > objectY ? 9 : -23), 13, align: TextAlignment.Center);
    }
    void DimV(double y1, double y2, double objectX, double x, string label, bool left = false)
    {
        double end = x + (x > objectX ? 5 : -5);
        Line(objectX, y1, end, y1); Line(objectX, y2, end, y2);
        bool narrow = y2 - y1 < 22;
        Line(x, y1 - (narrow ? 12 : 0), x, y2 + (narrow ? 12 : 0));
        Arrow(x, y1, 0, narrow ? -1 : 1); Arrow(x, y2, 0, narrow ? 1 : -1);
        Text(label, x + (left ? -10 : 10), (y1 + y2) / 2 - (label.Contains('\n') ? 17 : 9), 13,
            align: left ? TextAlignment.Right : TextAlignment.Left);
    }
    void Callout(string label, double x, double y, double targetX, double targetY, bool right = false)
    {
        Text(label, x, y, 13, align: right ? TextAlignment.Right : TextAlignment.Left);
        Line(x, y + 22, targetX, targetY);
        dc.DrawEllipse(Ink, null, new(targetX, targetY), 2, 2);
    }
    void Outline(double x, double y, double w, double h) =>
        dc.DrawRectangle(null, new Pen(Accent, 2) { DashStyle = DashStyles.Dash }, new(x, y, w, h));
    void Axes(double x, double y, string vertical = "Y")
    {
        Line(x, y, x + 34, y, Muted); Arrow(x + 34, y, -1, 0, Muted);
        Line(x, y, x, y - 32, Muted); Arrow(x, y - 32, 0, 1, Muted);
        Text("X", x + 40, y - 10, 11, Muted); Text(vertical, x - 5, y - 51, 11, Muted);
    }
    void Legend(params (Brush Color, string Label)[] entries)
    {
        for (int i = 0; i < entries.Length; i++)
        {
            double x = 80 + i % 3 * 190, y = 620 + i / 3 * 22;
            Rect(entries[i].Color, x, y + 3, 14, 10, false);
            Text(entries[i].Label, x + 22, y, 12, Muted);
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
        dc.DrawGeometry(null, new Pen(Metal, 2.5), path);
    }
}
