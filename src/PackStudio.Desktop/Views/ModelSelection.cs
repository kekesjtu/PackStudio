using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Media3D;

namespace PackStudio.Desktop;

public partial class MainWindow
{
    Node? inspectedGroup;
    bool updatingModelTree;

    void Tree_MouseDown(object sender, MouseButtonEventArgs e)
    {
        var element = e.OriginalSource as DependencyObject;
        while (element != null && element is not TreeViewItem)
        {
            if (element is ToggleButton or ScrollBar or Thumb) return;
            element = VisualTreeHelper.GetParent(element);
        }
        if (element is TreeViewItem { Tag: Node node })
            SelectTreeNode(node, Keyboard.Modifiers);
        else
            ClearModelSelection();
        e.Handled = true;
    }

    void ModelTree_SelectionChanged(object sender, RoutedPropertyChangedEventArgs<object> e)
    {
        if (updatingModelTree || e.NewValue is not TreeViewItem { Tag: Node node }) return;
        // Native keyboard and accessibility selection replaces the current selection.
        workspace.Selected.Clear();
        inspectedGroup = node.Block == null ? node : null;
        if (node.Block != null) workspace.Selected.Add(node.Id);
        rangeAnchor = node.Block != null ? node.Id : null;
        RefreshModel();
    }

    void SelectTreeNode(Node node, ModifierKeys modifiers)
    {
        if (node.Block == null)
        {
            workspace.Selected.Clear();
            rangeAnchor = null;
            inspectedGroup = node;
            RefreshModel();
            return;
        }

        inspectedGroup = null;
        bool control = modifiers.HasFlag(ModifierKeys.Control), shift = modifiers.HasFlag(ModifierKeys.Shift);
        var visible = TreeItems().Where(i => i.Tag is Node { Block: not null } && AncestorsExpanded(i)).Select(i => ((Node)i.Tag).Id).ToList();
        if (shift && rangeAnchor != null && visible.Contains(rangeAnchor) && visible.Contains(node.Id))
        {
            if (!control) workspace.Selected.Clear();
            int a = visible.IndexOf(rangeAnchor), b = visible.IndexOf(node.Id);
            workspace.Selected.UnionWith(visible.Skip(Math.Min(a, b)).Take(Math.Abs(a - b) + 1));
        }
        else
        {
            bool deselect = workspace.Selected.Contains(node.Id) && (control || workspace.Selected.Count == 1);
            if (!control) workspace.Selected.Clear();
            if (deselect) workspace.Selected.Remove(node.Id);
            else workspace.Selected.Add(node.Id);
            rangeAnchor = workspace.Selected.Count > 0 ? node.Id : null;
        }
        RefreshModel();
    }

    void ClearModelSelection()
    {
        workspace.Selected.Clear();
        inspectedGroup = null;
        rangeAnchor = null;
        RefreshModel();
    }

    static bool AncestorsExpanded(TreeViewItem item)
    {
        var parent = ItemsControl.ItemsControlFromItemContainer(item);
        while (parent is TreeViewItem node)
        {
            if (!node.IsExpanded) return false;
            parent = ItemsControl.ItemsControlFromItemContainer(node);
        }
        return true;
    }

    void SelectViewportBlock(Point point)
    {
        string? id = null;
        VisualTreeHelper.HitTest(Viewport.Viewport, null, result =>
        {
            if (result is RayMeshGeometry3DHitTestResult mesh && hitTargets.TryGetValue(mesh.VisualHit, out var hit))
            {
                id = hit;
                return HitTestResultBehavior.Stop;
            }
            return HitTestResultBehavior.Continue;
        }, new PointHitTestParameters(point));
        workspace.Selected.Clear();
        inspectedGroup = null;
        if (id != null) workspace.Selected.Add(id);
        rangeAnchor = id;
        RefreshModel();
    }
}
