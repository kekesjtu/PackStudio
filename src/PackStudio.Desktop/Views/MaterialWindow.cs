using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using PackStudio.Core;

namespace PackStudio.Desktop;
public sealed class MaterialWindow : Window
{
    readonly Workspace workspace;
    readonly TreeView list = new() { Name = "MaterialTree" };
    readonly StackPanel editor = new()
    {
        Visibility = Visibility.Collapsed
    };
    readonly TextBlock description = new()
    {
        TextWrapping = TextWrapping.Wrap,
        Margin = new(0, 0, 0, 14)
    };
    readonly Dictionary<string, TextBox> fields = [];
    Material? selected;
    public MaterialWindow(Workspace workspace)
    {
        this.workspace = workspace;
        Title = "材料库 — 当前方案物性";
        Width = 900;
        Height = 620;
        MinWidth = 720;
        FontFamily = new FontFamily("Microsoft YaHei UI");
        FontSize = 12;
        WindowStyle = WindowStyle.ToolWindow;
        ShowInTaskbar = false;
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        var root = new Grid
        {
            Margin = new(18)
        };
        root.ColumnDefinitions.Add(new() { Width = new GridLength(1, GridUnitType.Star) });
        root.ColumnDefinitions.Add(new() { Width = new GridLength(340) });
        Content = root;
        var left = new DockPanel
        {
            Margin = new(0, 0, 22, 0)
        };
        root.Children.Add(left);
        var filter = new TextBox
        {
            Margin = new(0, 0, 0, 10),
            ToolTip = "按材料名称或类别搜索"
        };
        DockPanel.SetDock(filter, Dock.Top);
        left.Children.Add(filter);
        left.Children.Add(list);
        list.Style = (Style)FindResource("ExplorerTree");
        Grid.SetColumn(editor, 1);
        root.Children.Add(editor);
        editor.Children.Add(description);
        foreach (var(key, label)in new[]
        {
            ("kx", "X 导热率 W/(m·K)"),
            ("ky", "Y 导热率 W/(m·K)"),
            ("kz", "Z 导热率 W/(m·K)"),
            ("density", "密度 kg/m³"),
            ("cp", "比热 J/(kg·K)")
        }

        )
        {
            editor.Children.Add(new TextBlock { Text = label, Margin = new(0, 8, 0, 4) });
            var box = new TextBox();
            fields[key] = box;
            editor.Children.Add(box);
        }

        editor.Children.Add(new TextBlock { Text = "修改的物性保存在当前方案中。密度或比热为占位值时，应按实测数据核对。", Foreground = Brushes.DarkGoldenrod, TextWrapping = TextWrapping.Wrap, Margin = new(0, 16, 0, 12) });
        var apply = new Button
        {
            Content = "应用到当前方案",
            HorizontalAlignment = HorizontalAlignment.Right
        };
        apply.Click += Apply;
        editor.Children.Add(apply);
        var available = workspace.Catalog.Materials.Items.Values.ToDictionary(m => m.Id);
        foreach (var m in workspace.Model?.Materials.Values.AsEnumerable() ?? [])
            available[m.Id] = m;
        foreach (var m in workspace.Document.CustomMaterials)
            available[m.Id] = m;
        var materials = available.Values.GroupBy(m => m.Name).Select(g => g.FirstOrDefault(m => workspace.Document.CustomMaterials.Any(c => c.Id == m.Id)) ?? g.FirstOrDefault(m => workspace.Model?.Materials.ContainsKey(m.Id) == true) ?? g.OrderBy(m => m.Id.Length).First()).ToList();
        void Filter()
        {
            var expanded = list.Items.Cast<TreeViewItem>().Where(i => i.IsExpanded).Select(i => i.Tag?.ToString()).ToHashSet();
            list.Items.Clear();
            foreach (var group in materials.Where(m => m.Name.Contains(filter.Text, StringComparison.OrdinalIgnoreCase) || m.Category.Contains(filter.Text, StringComparison.OrdinalIgnoreCase)).GroupBy(m => m.Category).OrderBy(g => g.Key))
            {
                var category = new TreeViewItem
                {
                    Header = new TreeRow(group.Key, true, group.Count().ToString()),
                    Tag = group.Key,
                    Style = (Style)FindResource("ExplorerTreeItem"),
                    IsExpanded = filter.Text.Length > 0 || expanded.Contains(group.Key)
                };
                foreach (var material in group.OrderBy(m => m.Name))
                {
                    var item = new TreeViewItem { Header = new TreeRow(material.Name, false,
                        swatch: (Color)ColorConverter.ConvertFromString(material.Color), warning: MaterialPresentation.NeedsReview(material)), Tag = material,
                        Style = (Style)FindResource("ExplorerTreeItem") };
                    System.Windows.Automation.AutomationProperties.SetName(item, material.Name);
                    category.Items.Add(item);
                }
                System.Windows.Automation.AutomationProperties.SetName(category, $"{group.Key} ({group.Count()})");
                list.Items.Add(category);
            }
        }

        filter.TextChanged += (_, _) => Filter();
        list.SelectedItemChanged += (_, _) => Select();
        list.PreviewMouseLeftButtonDown += (_, e) =>
        {
            var element = e.OriginalSource as DependencyObject;
            bool expander = false;
            while (element != null && element is not TreeViewItem)
            {
                if (element is System.Windows.Controls.Primitives.ToggleButton) expander = true;
                element = VisualTreeHelper.GetParent(element);
            }
            if (!expander && element is TreeViewItem { Tag: string } category)
            {
                category.IsExpanded = !category.IsExpanded;
                e.Handled = true;
                return;
            }
            if (element is TreeViewItem { Tag: Material material } item && selected?.Id == material.Id)
            {
                selected = null;
                item.IsSelected = false;
                editor.Visibility = Visibility.Collapsed;
                e.Handled = true;
            }
        };
        Filter();
    }

    void Select()
    {
        if (list.SelectedItem is not TreeViewItem { Tag: Material m })
            return;
        selected = m;
        editor.Visibility = Visibility.Visible;
        description.Text = m.Name + "\n" + m.Category + (m.ConductivityCoefficient.HasValue ? $"\n温度系数：{m.ConductivityCoefficient:G6}，参考温度：{m.ReferenceTemperature:G6} °C" : "");
        foreach (var(key, value)in new[]
        {
            ("kx", m.Conductivity.X),
            ("ky", m.Conductivity.Y),
            ("kz", m.Conductivity.Z),
            ("density", m.Density),
            ("cp", m.SpecificHeat)
        }

        )
            fields[key].Text = value.ToString("G10", CultureInfo.InvariantCulture);
    }

    void Apply(object sender, RoutedEventArgs e)
    {
        if (selected == null)
            return;
        try
        {
            double N(string key) => double.Parse(fields[key].Text, CultureInfo.InvariantCulture);
            var material = selected with
            {
                Conductivity = new(N("kx"), N("ky"), N("kz")),
                Density = N("density"),
                SpecificHeat = N("cp")
            };
            material.Validate();
            workspace.Document.CustomMaterials.RemoveAll(m => m.Id == material.Id);
            workspace.Document.CustomMaterials.Add(material);
            DialogResult = true;
        }
        catch (Exception ex)
        {
            MessageBox.Show(this, ex.Message, "材料物性无效", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
    }
}
