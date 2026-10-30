using System.Reflection;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using PackStudio.Core;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;

static class ModelTreeChecks
{
    static void Require(bool success, string message)
    {
        if (!success) throw new Exception(message);
    }

    static void Click(TreeViewItem item)
    {
        item.UpdateLayout();
        var header = (FrameworkElement)item.Header;
        header.RaiseEvent(new MouseButtonEventArgs(Mouse.PrimaryDevice, Environment.TickCount, MouseButton.Left)
            { RoutedEvent = Mouse.PreviewMouseDownEvent });
        item.UpdateLayout();
    }

    static IEnumerable<TreeViewItem> Items(TreeViewItem parent)
    {
        yield return parent;
        foreach (TreeViewItem child in parent.Items)
            foreach (var item in Items(child)) yield return item;
    }

    static string Id(TreeViewItem item) => (string)item.Tag.GetType().GetProperty("Id")!.GetValue(item.Tag)!;

    public static void Run(MainWindow window, Workspace workspace)
    {
        var tree = (TreeView)window.FindName("ModelTree");
        var inspector = (TextBlock)window.FindName("Inspector");
        var root = (TreeViewItem)tree.Items[0];
        var group = (TreeViewItem)root.Items[0];
        var leaves = Items(root).Where(item => item.Items.Count == 0).Take(2).ToList();
        var leaf = leaves[0];
        Click(leaf);
        Require(workspace.Selected.SetEquals([Id(leaf)]) && leaf.IsSelected && TreeRow.GetIsHighlighted(leaf),
            "leaf click did not select matching block and row");
        Require(inspector.Text.Contains("kx / ky / kz"), "leaf properties missing");
        Click(leaf);
        Require(workspace.Selected.Count == 0 && !leaf.IsSelected && !TreeRow.GetIsHighlighted(leaf),
            "clicking selected leaf again must deselect it");
        Require(Items(root).All(item => !item.IsSelected && !TreeRow.GetIsHighlighted(item)), "stale tree highlight");

        Click(leaf);
        Click(root);
        Require(root.IsExpanded && root.IsSelected && TreeRow.GetIsHighlighted(root),
            $"root selection and expansion: expanded={root.IsExpanded}, selected={root.IsSelected}, highlighted={TreeRow.GetIsHighlighted(root)}, inspector={inspector.Text}");
        Require(workspace.Selected.Count == 0 && !leaf.IsSelected && !TreeRow.GetIsHighlighted(leaf),
            "root click retained leaf selection");
        Require(inspector.Text.StartsWith("封装概览\n" + workspace.Model!.Name) &&
            inspector.Text.Contains("矩形块数：" + workspace.Model.Blocks.Count) && inspector.Text.Contains("封装类型："),
            "root must show package summary and full block count");
        if (workspace.Model.TemplateId == "qfn") NewPackageChecks.Capture(window, "model-root-info.png");

        string rootInfo = inspector.Text;
        Click(group);
        Require(group.IsSelected && TreeRow.GetIsHighlighted(group) && !root.IsSelected && !TreeRow.GetIsHighlighted(root),
            "group click retained root selection");
        Require(inspector.Text.StartsWith("组件分组\n") && inspector.Text != rootInfo && inspector.Text.Contains("所属封装："),
            "group must show different information from package root");
        string groupInfo = inspector.Text;
        group.IsExpanded = false;
        Require(inspector.Text == groupInfo && group.IsSelected, "collapsing group changed inspected node");
        group.IsExpanded = true;
        var blocks = (List<Block>)group.Tag.GetType().GetProperty("Blocks")!.GetValue(group.Tag)!;
        workspace.ChangeVisibility([blocks[0].Id], false);
        Require(inspector.Text.Contains("可见块数：" + (blocks.Count - 1)), "group visible count did not update");
        workspace.ChangeVisibility([blocks[0].Id], true);
        if (workspace.Model.TemplateId == "qfn") NewPackageChecks.Capture(window, "model-group-info.png");

        if (leaves.Count > 1)
        {
            var select = typeof(MainWindow).GetMethod("SelectTreeNode", BindingFlags.NonPublic | BindingFlags.Instance)!;
            Click(leaf);
            select.Invoke(window, [leaves[1].Tag, ModifierKeys.Control]);
            Require(workspace.Selected.SetEquals(leaves.Select(Id)), "Ctrl no longer adds a leaf");
            select.Invoke(window, [leaf.Tag, ModifierKeys.Control]);
            Require(workspace.Selected.SetEquals([Id(leaves[1])]) && !TreeRow.GetIsHighlighted(leaf), "Ctrl no longer removes a leaf");
            Click(leaf);
            select.Invoke(window, [leaves[1].Tag, ModifierKeys.Shift]);
            Require(workspace.Selected.SetEquals(leaves.Select(Id)), "Shift no longer selects the visible range");
            Click(root);
            Require(workspace.Selected.Count == 0 && inspector.Text.StartsWith("封装概览"), "root retained multi selection");
        }

        // Native keyboard/accessibility selection must use the same inspector state.
        leaf.IsSelected = true;
        Require(workspace.Selected.SetEquals([Id(leaf)]) && inspector.Text.Contains("kx / ky / kz"),
            "native selection did not update block inspector");
        Click(leaf);
        Require(workspace.Selected.Count == 0 && Items(root).All(item => !TreeRow.GetIsHighlighted(item)),
            "leaf remained highlighted after deselection");
    }
}
