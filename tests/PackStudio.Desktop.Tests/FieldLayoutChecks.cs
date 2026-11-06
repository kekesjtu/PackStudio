using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using PackStudio.Core;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;
static class FieldLayoutChecks
{
    static int hinted;
    // 数值输入框（含整数上下调节按钮）与下拉框高度一致，避免同列控件参差不齐。
    public static void Run(MainWindow window, ListBox steps, StackPanel fields, Workspace workspace)
    {
        string family = workspace.Document.TemplateId;
        bool compared = false;
        foreach (var step in steps.Items.Cast<WizardStep>())
        {
            steps.SelectedValue = step.Key;
            window.UpdateLayout();
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
                    ?? throw new Exception($"{family}/{field.Path}: 数值框右侧缺少范围提示");
                if (hint.Text != field.Range)
                    throw new Exception($"{family}/{field.Path}: 范围提示“{hint.Text}”与定义“{field.Range}”不一致");
                if (hint.Text.Contains("整数"))
                    throw new Exception($"{family}/{field.Path}: 整数框不再标注整数");
                if (hint.Text.Length > 0) hinted++;
            }
        }
    }

    public static void Verify()
    {
        if (hinted == 0)
            throw new Exception("没有任何字段显示定义中的取值范围");
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
