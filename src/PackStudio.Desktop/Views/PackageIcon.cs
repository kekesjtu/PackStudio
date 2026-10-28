using System.Windows;
using System.Windows.Media;

namespace PackStudio.Desktop;
public sealed class PackageIcon : FrameworkElement
{
    public static readonly DependencyProperty TemplateIdProperty = DependencyProperty.Register(nameof(TemplateId), typeof(string), typeof(PackageIcon), new FrameworkPropertyMetadata("bare_die", FrameworkPropertyMetadataOptions.AffectsRender));
    public string TemplateId { get => (string)GetValue(TemplateIdProperty); set => SetValue(TemplateIdProperty, value); }

    protected override void OnRender(DrawingContext dc)
    {
        base.OnRender(dc);
        double scale = Math.Min(ActualWidth / 120, ActualHeight / 54);
        dc.PushTransform(new TranslateTransform((ActualWidth - 120 * scale) / 2, (ActualHeight - 54 * scale) / 2));
        dc.PushTransform(new ScaleTransform(scale, scale));
        var edge = new Pen(Brushes.DimGray, 0.8);
        void Rect(Brush fill, double x, double y, double w, double h) => dc.DrawRectangle(fill, edge, new(x, y, w, h));
        if (TemplateId == "bare_die")
            Rect(Brushes.Crimson, 26, 22, 68, 10);
        else
        {
            bool bga = TemplateId is "chip_array" or "cbga_fc" or "pbga_fc" or "pbga_wb";
            bool flip = TemplateId is "cbga_fc" or "pbga_fc";
            if (bga)
            {
                Rect(Brushes.SeaGreen, 8, 31, 104, 6);
                for (int i = 0; i < 9; i++)
                    dc.DrawEllipse(Brushes.SlateBlue, edge, new(14 + i * 11.5, 43), 3, 3);
                if (!flip)
                    Rect(Brushes.LightSteelBlue, 17, 15, 86, 16);
                Rect(Brushes.Crimson, 36, flip ? 19 : 25, 48, 5);
                if (flip)
                    for (int i = 0; i < 6; i++)
                        Rect(Brushes.Goldenrod, 38 + i * 8, 25, 3, 5);
            }
            else
            {
                Rect(Brushes.LightSteelBlue, 22, 15, 76, 22);
                Rect(Brushes.Goldenrod, 30, 29, 60, 4);
                Rect(Brushes.Crimson, 39, 23, 42, 6);
                foreach (int sign in new[]
                {
                    -1,
                    1
                }

                )
                {
                    double x = sign < 0 ? 7 : 98;
                    Rect(Brushes.DarkGoldenrod, x, 29, 15, 4);
                    if (TemplateId != "qfn")
                    {
                        Rect(Brushes.DarkGoldenrod, sign < 0 ? 7 : 110, 33, 3, 8);
                        Rect(Brushes.DarkGoldenrod, sign < 0 ? 1 : 110, 40, 9, 3);
                    }
                }
            }
        }

        dc.Pop();
        dc.Pop();
    }
}
