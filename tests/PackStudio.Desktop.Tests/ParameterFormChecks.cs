using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Data;
using System.Windows.Media;
using PackStudio.Core;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;

static class ParameterFormChecks
{
    public static void Run(MainWindow window, Workspace workspace, ListBox steps, StackPanel panel)
    {
        steps.SelectedValue = "modeling";
        window.UpdateLayout();
        var grid = Descendants<CheckBox>(panel).Single(b => b.Content?.ToString() == "局部网格");
        var density = Descendants<ComboBox>(panel).Single(b => BindingOperations.GetBindingExpression(b, Selector.SelectedValueProperty)?.ParentBinding.Source is ParameterField { Key: "grid.density" });
        bool original = grid.IsChecked == true;
        grid.IsChecked = false;
        window.UpdateLayout();
        if (workspace.Document.Values["grid.enabled"].Flag() || Descendants<ComboBox>(panel).Contains(density))
            throw new Exception("field binding did not hide disabled grid settings");
        grid.IsChecked = true;
        window.UpdateLayout();
        if (!workspace.Document.Values["grid.enabled"].Flag() || !Descendants<ComboBox>(panel).Contains(density) ||
            !ReferenceEquals(grid, Descendants<CheckBox>(panel).Single(b => b.Content?.ToString() == "局部网格")))
            throw new Exception("parameter change rebuilt existing controls");
        grid.IsChecked = original;
    }

    static IEnumerable<T> Descendants<T>(DependencyObject root) where T : DependencyObject
    {
        for (int i = 0; i < VisualTreeHelper.GetChildrenCount(root); i++)
        {
            var child = VisualTreeHelper.GetChild(root, i);
            if (child is T match) yield return match;
            foreach (var nested in Descendants<T>(child)) yield return nested;
        }
    }
}
