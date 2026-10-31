using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace PackStudio.Desktop;

public sealed class TreeRow : Grid
{
    public static readonly DependencyProperty IsHighlightedProperty = DependencyProperty.RegisterAttached(
        "IsHighlighted", typeof(bool), typeof(TreeRow), new FrameworkPropertyMetadata(false));

    public static bool GetIsHighlighted(DependencyObject element) => (bool)element.GetValue(IsHighlightedProperty);
    public static void SetIsHighlighted(DependencyObject element, bool value) => element.SetValue(IsHighlightedProperty, value);

    public TreeRow(string title, bool group, string count = "", Color? swatch = null, bool hidden = false, bool modelGroup = false, bool warning = false)
    {
        VerticalAlignment = VerticalAlignment.Center;
        Opacity = hidden ? 0.45 : 1;
        ColumnDefinitions.Add(new() { Width = new GridLength(22) });
        ColumnDefinitions.Add(new());
        ColumnDefinitions.Add(new() { Width = GridLength.Auto });
        FrameworkElement icon;
        if (swatch.HasValue)
            icon = new Border { Width = 12, Height = 12, CornerRadius = new(2),
                Background = new SolidColorBrush(swatch.Value), BorderBrush = Brushes.SlateGray, BorderThickness = new(0.7) };
        else
            icon = new System.Windows.Shapes.Path
            {
                Width = 15, Height = 15, Stretch = Stretch.Uniform,
                Data = Geometry.Parse(group
                    ? modelGroup ? "M1,5 L8,1 L15,5 L8,9 Z M1,9 L8,13 L15,9 M1,13 L8,17 L15,13" : "M1,3 L6,3 L8,5 L15,5 L15,14 L1,14 Z"
                    : "M1,4 L8,1 L15,4 L15,12 L8,16 L1,12 Z M1,4 L8,7 L15,4 M8,7 L8,16"),
                Fill = new SolidColorBrush(group && !modelGroup ? Color.FromRgb(237, 210, 140) : Color.FromRgb(169, 198, 231)),
                Stroke = new SolidColorBrush(group && !modelGroup ? Color.FromRgb(161, 128, 63) : Color.FromRgb(76, 115, 159)),
                StrokeThickness = 0.9
            };
        icon.HorizontalAlignment = HorizontalAlignment.Left;
        icon.VerticalAlignment = VerticalAlignment.Center;
        Children.Add(icon);
        var label = new TextBlock { Text = title, ToolTip = title, TextTrimming = TextTrimming.CharacterEllipsis,
            FontSize = 12, Foreground = new SolidColorBrush(Color.FromRgb(48, 61, 77)),
            FontWeight = group ? FontWeights.SemiBold : FontWeights.Normal, VerticalAlignment = VerticalAlignment.Center };
        SetColumn(label, 1);
        Children.Add(label);
        var total = new TextBlock { Text = warning ? "物性待核实" : count, FontSize = 10, Foreground = warning ? Brushes.DarkGoldenrod : Brushes.SlateGray,
            VerticalAlignment = VerticalAlignment.Center, Margin = new(8, 0, 3, 0) };
        SetColumn(total, 2);
        Children.Add(total);
    }
}
