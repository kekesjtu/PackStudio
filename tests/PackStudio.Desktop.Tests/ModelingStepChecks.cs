using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Newtonsoft.Json.Linq;
using PackStudio.Core;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;
static class ModelingStepChecks
{
    // 建模与局部网格栏目：几何建模控件在前，局部网格开关与网格密度排在最后。
    public static void Run(MainWindow window, ListBox steps, StackPanel fields, Workspace workspace)
    {
        string family = workspace.Document.TemplateId;
        var template = workspace.Template;
        var modeling = Labels(fields, steps, "modeling", window);
        if (modeling.Count == 0)
            throw new Exception(family + ": 建模栏目为空");

        int grid = modeling.IndexOf("局部网格");
        if (grid < 0)
            throw new Exception(family + ": 建模栏目缺少局部网格开关");
        if (modeling.Skip(grid).Any(text => text is not ("局部网格" or "网格密度")))
            throw new Exception(family + ": 局部网格未排在建模栏目末尾");

        var bumpModeling = template.Fields.FirstOrDefault(f => f["key"].Text() == "bumps.modeling");
        if (bumpModeling != null && JsonData.Matches(bumpModeling["visible_when"] as JObject, workspace.Document.Values))
        {
            bool declared = Descendants<ComboBox>(fields).Any(combo => ComboLabel(combo) == "各向同性等效层" && combo.Items.Count == 1);
            if (!declared)
                throw new Exception(family + ": 建模栏目缺少固定为各向同性等效层的凸点建模下拉");
        }

        if (!template.Fields.Any(f => f["step"].Text() == "solder_balls"))
            return;
        if (!modeling.Contains("焊球建模方式"))
            throw new Exception(family + ": 焊球建模方式不在建模栏目");
        if (!Descendants<ComboBox>(fields).Any(combo => ComboLabel(combo) is "离散矩形块" or "各向异性等效层" or "各向同性等效层"))
            throw new Exception(family + ": 焊球建模方式缺少英文选项");
        if (Labels(fields, steps, "solder_balls", window).Contains("焊球建模方式"))
            throw new Exception(family + ": 焊球建模方式仍留在焊球栏目");
    }

    static string? ComboLabel(ComboBox combo) => combo.SelectedItem?.GetType().GetProperty("Label")?.GetValue(combo.SelectedItem)?.ToString();

    static List<string> Labels(StackPanel fields, ListBox steps, string step, MainWindow window)
    {
        if (steps.Items.Cast<WizardStep>().All(s => s.Key != step))
            return [];
        steps.SelectedValue = step;
        window.UpdateLayout();
        return fields.Children.OfType<object>().Select(Label).Where(text => text != null).Select(text => text!).ToList();
    }

    static string? Label(object child)
    {
        if (child is CheckBox direct)
            return direct.Content?.ToString();
        if (child is not Grid row || row.Children.Count == 0)
            return null;
        object first = row.Children[0];
        if (first is StackPanel editors)
            return editors.Children.OfType<CheckBox>().FirstOrDefault() is CheckBox box ? box.Content?.ToString() : null;
        if (first is TextBlock text)
            return text.Text;
        if (first is DockPanel panel)
            return string.Join(" ", panel.Children.OfType<TextBlock>().Select(t => t.Text.Trim()).Where(t => t.Length > 0));
        return null;
    }

    static IEnumerable<T> Descendants<T>(DependencyObject root)
        where T : DependencyObject
    {
        for (int i = 0; i < VisualTreeHelper.GetChildrenCount(root); i++)
        {
            var child = VisualTreeHelper.GetChild(root, i);
            if (child is T match)
                yield return match;
            foreach (var nested in Descendants<T>(child))
                yield return nested;
        }
    }
}
