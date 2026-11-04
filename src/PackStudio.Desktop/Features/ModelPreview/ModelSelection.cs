using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Media3D;

namespace PackStudio.Desktop;

public sealed partial class ModelPresenter
{
    bool updatingModelTree;

    void Tree_MouseDown(object sender, MouseButtonEventArgs e)
    {
        var element = e.OriginalSource as DependencyObject;
        while (element != null && element is not TreeViewItem)
        {
            if (element is ToggleButton or ScrollBar or Thumb) return;
            element = VisualTreeHelper.GetParent(element);
        }
        if (element is TreeViewItem { Tag: ModelNode node })
            SelectTreeNode(node, Keyboard.Modifiers);
        else
            ClearModelSelection();
        e.Handled = true;
    }

    void ModelTree_SelectionChanged(object sender, RoutedPropertyChangedEventArgs<object> e)
    {
        if (updatingModelTree || e.NewValue is not TreeViewItem { Tag: ModelNode node }) return;
        workspace.SelectNode(node, toggle: false);
    }

    public void SelectTreeNode(ModelNode node, ModifierKeys modifiers)
    {
        var visible = TreeItems().Where(i => i.Tag is ModelNode { Block: not null } && AncestorsExpanded(i)).Select(i => ((ModelNode)i.Tag).Id).ToList();
        workspace.SelectNode(node, modifiers.HasFlag(ModifierKeys.Control), modifiers.HasFlag(ModifierKeys.Shift), visible);
    }

    void ClearModelSelection() => workspace.ClearSelection();

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
        if (id == null) workspace.ClearSelection();
        else
        {
            var block = workspace.Model!.Blocks.Single(b => b.Id == id);
            workspace.SelectNode(new(block.Id, block.Name, [block], block), toggle: false);
        }
    }
}
