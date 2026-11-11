using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Newtonsoft.Json.Linq;
using PackStudio.Core;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;
static class FieldLayoutChecks
{
    static int hinted;
    static int matrices;
    static int checkboxes;
    // 数值输入框（含整数上下调节按钮）与下拉框高度一致，避免同列控件参差不齐。
    public static void Run(MainWindow window, ListBox steps, StackPanel fields, Workspace workspace)
    {
        string family = workspace.Document.TemplateId;
        bool compared = false;
        foreach (var step in steps.Items.Cast<WizardStep>())
        {
            steps.SelectedValue = step.Key;
            window.UpdateLayout();
            CheckRows(fields, family + "/" + step.Key);
            CheckBoxes(fields);
            CheckMatrices(window, fields, workspace);
            if (family == "pbga_fc" && step.Key is "central_solder_balls" or "solder_removal")
                NewPackageChecks.Capture(window, "field-layout-" + step.Key + ".png");
            var numbers = Descendants<Border>(fields).Where(b => b.BorderThickness.Top > 0 && b.Child is DockPanel).Select(b => b.ActualHeight).ToList();
            var combos = Descendants<ComboBox>(fields).Select(c => c.ActualHeight).ToList();
            if (numbers.Count == 0 || combos.Count == 0)
                continue;
            double expected = combos[0];
            if (numbers.Any(height => Math.Abs(height - expected) > 0.6))
                throw new Exception($"{family}/{step.Key}: 数值输入框高度 {string.Join("、", numbers.Select(h => h.ToString("F1")))} 与下拉框 {expected:F1} 不一致");
            compared = true;
        }

        if (!compared)
            throw new Exception(family + ": 未找到同时包含数值输入框与下拉框的栏目");

        // 定义中的取值范围显示在输入框右侧；整数框以箭头区分类型，不再重复标注“整数”。
        foreach (var step in steps.Items.Cast<WizardStep>())
        {
            steps.SelectedValue = step.Key;
            window.UpdateLayout();
            foreach (var row in fields.Children.OfType<Grid>().Where(row => row.Visibility == Visibility.Visible))
            {
                if (row.DataContext is not ParameterField { Type: "number" or "integer" } field) continue;
                var hint = row.Children.OfType<TextBlock>().SingleOrDefault(text => Grid.GetColumn(text) == 2)
                    ?? throw new Exception($"{family}/{field.Key}: 数值框右侧缺少范围提示");
                if (hint.Text != field.Range)
                    throw new Exception($"{family}/{field.Key}: 范围提示“{hint.Text}”与定义“{field.Range}”不一致");
                if (hint.Text.Contains("整数"))
                    throw new Exception($"{family}/{field.Key}: 整数框不再标注整数");
                if (hint.Text.Length > 0) hinted++;
            }
        }
    }

    public static void Verify()
    {
        if (hinted == 0)
            throw new Exception("没有任何字段显示定义中的取值范围");
        if (matrices == 0 || checkboxes == 0)
            throw new Exception("没有覆盖矩阵头部或正方形勾选框");
        Console.WriteLine("PASS field spacing, square checkboxes and matrix expansion with discrete switching");
    }

    static void CheckRows(StackPanel fields, string context)
    {
        var visible = fields.Children.OfType<FrameworkElement>().Where(row => row.Visibility == Visibility.Visible).ToList();
        var lines = visible.OfType<Grid>().Where(row => row.DataContext is ParameterField field &&
            field.Type is not ("table" or "removal_matrix") && field.Definition["help_text"] == null).ToList();
        if (lines.Any(row => row.ActualHeight < 25.5) ||
            lines.Count > 1 && lines.Max(row => row.ActualHeight) - lines.Min(row => row.ActualHeight) > 0.6)
            throw new Exception(context + ": 单行字段高度不统一: " + string.Join(", ", lines.Select(row => $"{((ParameterField)row.DataContext).Key}={row.ActualHeight:F1}")));
        for (int i = 1; i < visible.Count; i++)
        {
            if (visible[i - 1] is not Grid { DataContext: ParameterField } previous ||
                visible[i] is not Grid { DataContext: ParameterField } next) continue;
            double bottom = previous.TranslatePoint(new Point(0, previous.ActualHeight), fields).Y;
            double gap = next.TranslatePoint(new Point(), fields).Y - bottom;
            if (Math.Abs(gap - 7) > 0.6)
                throw new Exception($"{context}: 字段间距 {gap:F1} 不等于 7 DIP");
        }
    }

    internal static IReadOnlyList<CheckBox> CheckBoxes(DependencyObject root)
    {
        var boxes = Descendants<CheckBox>(root).ToList();
        foreach (var box in boxes)
        {
            box.ApplyTemplate();
            if (box.Template.FindName("Glyph", box) is not Border glyph || glyph.ActualWidth <= 0 ||
                Math.Abs(glyph.ActualWidth - glyph.ActualHeight) > 0.1 || glyph.CornerRadius != new CornerRadius(0))
                throw new Exception("勾选框未使用正方形外观: " + box.Content);
            var mark = (UIElement)box.Template.FindName("CheckMark", box);
            var mixed = (UIElement)box.Template.FindName("MixedMark", box);
            if ((mark.Visibility == Visibility.Visible) != (box.IsChecked == true) ||
                (mixed.Visibility == Visibility.Visible) != (box.IsChecked == null))
                throw new Exception("勾选框标记与当前状态不符");
            if (box.FocusVisualStyle == null) throw new Exception("勾选框缺少键盘焦点提示");
            checkboxes++;
        }
        return boxes;
    }

    static void CheckMatrices(Window window, StackPanel fields, Workspace workspace)
    {
        foreach (var row in fields.Children.OfType<Grid>().Where(row => row.IsVisible && row.DataContext is ParameterField { Type: "removal_matrix" }).ToList())
        {
            var field = (ParameterField)row.DataContext;
            var box = Descendants<CheckBox>(row).Single();
            var editor = row.Children.OfType<RemovalMatrixEditor>().Single();
            bool original = field.Expanded;
            long revision = workspace.Revision;
            var values = workspace.Document.Values.DeepClone();
            bool switchesRepresentation = field.Key == "bga.omitted_cells" && values["bga.representation"].Text() != "discrete";
            if (switchesRepresentation) values["bga.representation"] = "discrete";
            box.IsChecked = false;
            window.UpdateLayout();
            double collapsedHeight = row.ActualHeight;
            if (field.Expanded || editor.Visibility != Visibility.Collapsed || Math.Abs(collapsedHeight - box.ActualHeight) > 0.6)
                throw new Exception("收起矩阵仍占用附属内容空间");
            box.IsChecked = true;
            window.UpdateLayout();
            if (!field.Expanded || !editor.IsVisible || row.ActualHeight <= collapsedHeight ||
                Math.Abs(editor.TranslatePoint(new Point(), row).Y - box.ActualHeight - 6) > 0.6)
                throw new Exception("矩阵展开后未使用统一的头部与内容间距");
            CheckBoxes(row);
            if (workspace.Document.TemplateId == "pbga_fc" && field.Key == "bga.omitted_cells")
                NewPackageChecks.Capture(window, "field-layout-matrix-expanded.png");
            box.IsChecked = original;
            window.UpdateLayout();
            if (workspace.Revision != revision + (switchesRepresentation ? 1 : 0) || !JToken.DeepEquals(values, workspace.Document.Values))
                throw new Exception("矩阵展开收起未按需切换离散建模，或修改了去除名单");
            matrices++;
        }
    }

    static IEnumerable<T> Descendants<T>(DependencyObject root)
        where T : DependencyObject
    {
        if (root is UIElement { Visibility: not Visibility.Visible }) yield break;
        for (int i = 0; i < VisualTreeHelper.GetChildrenCount(root); i++)
        {
            var child = VisualTreeHelper.GetChild(root, i);
            if (child is UIElement { Visibility: not Visibility.Visible }) continue;
            if (child is T match)
                yield return match;
            foreach (var nested in Descendants<T>(child))
                yield return nested;
        }
    }
}
