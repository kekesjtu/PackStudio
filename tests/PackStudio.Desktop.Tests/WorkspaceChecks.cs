using System.Reflection;
using System.Windows.Automation;
using System.Windows.Automation.Peers;
using System.Windows.Automation.Provider;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Input;
using System.Windows.Media;
using HelixToolkit.Wpf;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;

static class WorkspaceChecks
{
    static T Find<T>(MainWindow window, string name) where T : FrameworkElement => (T)window.FindName(name);
    static void Require(bool success, string message)
    {
        if (!success) throw new Exception(message);
    }

    public static void Run(MainWindow window, Workspace workspace)
    {
        var viewport = Find<HelixViewport3D>(window, "Viewport");
        Require(viewport.PanGesture.MouseAction == MouseAction.LeftClick && viewport.PanGesture.Modifiers == ModifierKeys.None,
            "left drag must pan without modifiers");
        Require(viewport.RotateGesture.MouseAction == MouseAction.RightClick && viewport.RotateGesture.Modifiers == ModifierKeys.None,
            "right drag must rotate without modifiers");
        Require(viewport.IsZoomEnabled && viewport.ShowCoordinateSystem && !viewport.ShowViewCube &&
            viewport.CoordinateSystemHorizontalPosition == HorizontalAlignment.Right &&
            viewport.CoordinateSystemVerticalPosition == VerticalAlignment.Bottom, "viewport controls and orientation");

        var warning = Find<Border>(window, "WarningsPanel");
        var text = Find<TextBlock>(window, "WarningsText");
        Require(warning.HorizontalAlignment == HorizontalAlignment.Right && warning.VerticalAlignment == VerticalAlignment.Top,
            "warnings must be at top right");
        string savedText = text.Text;
        text.Text = "";
        window.UpdateLayout();
        Require(warning.Visibility == Visibility.Collapsed, "empty warning box should disappear");
        text.Text = savedText;
        window.UpdateLayout();
        Require(savedText.Length > 0 && warning.Visibility == Visibility.Visible, "overlap warning disappeared");
        Require(Find<StatusBar>(window, "OperationStatusBar").Items.Count == 1, "units legend remains");

        var grid = Find<Grid>(window, "WorkspaceGrid");
        foreach (string name in new[] { "LeftColumnSplitter", "RightColumnSplitter" })
        {
            var splitter = Find<GridSplitter>(window, name);
            var savedWidths = grid.ColumnDefinitions.Select(c => c.Width).ToArray();
            int left = Grid.GetColumn(splitter) - 1, right = left + 2;
            double beforeLeft = grid.ColumnDefinitions[left].ActualWidth;
            double beforeRight = grid.ColumnDefinitions[right].ActualWidth;
            splitter.RaiseEvent(new DragStartedEventArgs(0, 0) { RoutedEvent = Thumb.DragStartedEvent });
            splitter.RaiseEvent(new DragDeltaEventArgs(24, 0) { RoutedEvent = Thumb.DragDeltaEvent });
            window.UpdateLayout();
            Require(Math.Abs(grid.ColumnDefinitions[left].ActualWidth - beforeLeft - 24) < 1 &&
                Math.Abs(grid.ColumnDefinitions[right].ActualWidth - beforeRight + 24) < 1,
                name + " did not resize both adjacent regions before drag completed");
            NewPackageChecks.Capture(window, name + "-during-drag.png");
            splitter.RaiseEvent(new DragCompletedEventArgs(24, 0, false) { RoutedEvent = Thumb.DragCompletedEvent });
            for (int i = 0; i < savedWidths.Length; i++) grid.ColumnDefinitions[i].Width = savedWidths[i];
            window.UpdateLayout();
        }

        // A moved pointer must preserve selection even when released over another block.
        string selectedId = workspace.Model!.Blocks[0].Id;
        workspace.Selected.Add(selectedId);
        var flags = BindingFlags.NonPublic | BindingFlags.Instance;
        var current = Mouse.GetPosition(viewport.Viewport);
        typeof(MainWindow).GetField("pointerOrigin", flags)!.SetValue(window, new Point(current.X - 100, current.Y));
        typeof(MainWindow).GetField("pointerDragged", flags)!.SetValue(window, false);
        typeof(MainWindow).GetMethod("Viewport_PointerUp", flags)!.Invoke(window,
            [viewport, new MouseButtonEventArgs(Mouse.PrimaryDevice, Environment.TickCount, MouseButton.Left)]);
        Require(workspace.Selected.SetEquals([selectedId]), "pan release changed model selection");
        workspace.Selected.Clear();

        CheckTree(Find<TreeView>(window, "ModelTree"));
        CheckMaterials(workspace);
        NewPackageChecks.Capture(window, "workspace-interactions.png");
        Console.WriteLine("PASS gestures, pan selection, live splitters, warning overlay and tree rows");
    }

    static void CheckMaterials(Workspace workspace)
    {
        var window = new MaterialWindow(workspace) { ShowInTaskbar = false, ShowActivated = false, Opacity = 0 };
        window.Show();
        try
        {
            var tree = Descendants(window).OfType<TreeView>().Single();
            foreach (TreeViewItem category in tree.Items) category.IsExpanded = true;
            window.UpdateLayout();
            CheckTree(tree);
            var first = (TreeViewItem)((TreeViewItem)tree.Items[0]).Items[0];
            first.IsSelected = true;
            Require(tree.SelectedItem == first, "material selection broken");
            window.UpdateLayout();
            NewPackageChecks.Capture(window, "material-tree-spacing.png");
        }
        finally { window.Close(); }
    }

    static void CheckTree(TreeView tree)
    {
        tree.UpdateLayout();
        var rows = Descendants(tree).OfType<TreeViewItem>().Where(i => i.IsVisible).ToList();
        Require(rows.Count > 1, "tree rows were not generated");
        foreach (var row in rows)
        {
            var background = (Border)row.Template.FindName("RowBackground", row);
            Require(Math.Abs(background.ActualHeight - 28) < 0.1, "inconsistent tree row height");
            Require(row.Header is TreeRow, "tree row lost structured header");
        }
        var root = (TreeViewItem)tree.Items[0];
        var group = root is ModelRootItem ? (TreeViewItem)root.Items[0] : root;
        bool expanded = group.IsExpanded;
        group.IsExpanded = false;
        tree.UpdateLayout();
        Require(group.ActualHeight == 28, "collapsed group still has excess spacing");
        group.IsExpanded = expanded;
        tree.UpdateLayout();
    }

    public static void CheckModelRoot(MainWindow window)
    {
        var tree = Find<TreeView>(window, "ModelTree");
        var root = (TreeViewItem)tree.Items[0];
        root.IsExpanded = false;
        tree.UpdateLayout();
        Require(root.IsExpanded, "model root collapsed");
        Require(!Descendants(root).OfType<ToggleButton>().Any(button =>
            ReferenceEquals(button.TemplatedParent, root)), "root still has an expander");
        var peer = FrameworkElementAutomationPeer.CreatePeerForElement(root)!;
        var expansion = (IExpandCollapseProvider)peer.GetPattern(PatternInterface.ExpandCollapse);
        expansion.Collapse();
        Require(expansion.ExpandCollapseState == ExpandCollapseState.Expanded, "automation collapsed model root");
        var flags = BindingFlags.NonPublic | BindingFlags.Instance;
        var expand = typeof(MainWindow).GetMethod("ExpandTree", flags)!;
        expand.Invoke(window, [false]);
        Require(root.IsExpanded && root.Items.Cast<TreeViewItem>().All(group => !group.IsExpanded),
            "collapse all must preserve root and collapse subgroups");
        expand.Invoke(window, [true]);
        tree.UpdateLayout();
        Require(root.IsExpanded && root.Items.Cast<TreeViewItem>().All(group => group.IsExpanded), "expand all failed");
    }

    static IEnumerable<DependencyObject> Descendants(DependencyObject parent)
    {
        for (int i = 0; i < VisualTreeHelper.GetChildrenCount(parent); i++)
        {
            var child = VisualTreeHelper.GetChild(parent, i);
            yield return child;
            foreach (var item in Descendants(child)) yield return item;
        }
    }
}
