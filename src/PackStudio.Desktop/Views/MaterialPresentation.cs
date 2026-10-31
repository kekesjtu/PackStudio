using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Media;
using PackStudio.Core;

namespace PackStudio.Desktop;

internal static class MaterialPresentation
{
    internal static bool NeedsReview(Material material) => material.Density == 1 || material.SpecificHeat == 1;
    internal sealed record Option(Material Material)
    {
        public string Id => Material.Id;
        public string Name => Material.Name;
        public bool NeedsReview => MaterialPresentation.NeedsReview(Material);
    }

    internal static DataTemplate Template()
    {
        var panel = new FrameworkElementFactory(typeof(DockPanel));
        var badge = new FrameworkElementFactory(typeof(TextBlock));
        badge.SetValue(TextBlock.TextProperty, "物性待核实");
        badge.SetValue(TextBlock.ForegroundProperty, Brushes.DarkGoldenrod);
        badge.SetValue(TextBlock.FontSizeProperty, 10.0);
        badge.SetValue(TextBlock.MarginProperty, new Thickness(6, 0, 0, 0));
        badge.SetValue(DockPanel.DockProperty, Dock.Right);
        badge.SetBinding(UIElement.VisibilityProperty, new Binding(nameof(Option.NeedsReview)) { Converter = new BooleanToVisibilityConverter() });
        panel.AppendChild(badge);
        var name = new FrameworkElementFactory(typeof(TextBlock));
        name.SetBinding(TextBlock.TextProperty, new Binding(nameof(Option.Name)));
        name.SetValue(TextBlock.TextTrimmingProperty, TextTrimming.CharacterEllipsis);
        name.SetBinding(FrameworkElement.ToolTipProperty, new Binding(nameof(Option.Name)));
        panel.AppendChild(name);
        return new DataTemplate { VisualTree = panel };
    }
}
