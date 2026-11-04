using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Media3D;
using HelixToolkit.Wpf;
using PackStudio.Core;

namespace PackStudio.Desktop;
public sealed partial class ModelPresenter
{
    readonly Dictionary<Visual3D, string> hitTargets = [];
    PackageModel? shownModel;
    readonly Workspace workspace;
    readonly TreeView ModelTree;
    readonly HelixViewport3D Viewport;
    readonly TextBlock Inspector;

    public ModelPresenter(Workspace workspace, TreeView tree, HelixViewport3D viewport, TextBlock inspector)
    {
        this.workspace = workspace;
        ModelTree = tree; Viewport = viewport; Inspector = inspector;
        tree.PreviewMouseLeftButtonDown += Tree_MouseDown;
        tree.SelectedItemChanged += ModelTree_SelectionChanged;
        viewport.PreviewMouseLeftButtonDown += Viewport_PointerDown;
        viewport.PreviewMouseMove += Viewport_PointerMove;
        viewport.PreviewMouseLeftButtonUp += Viewport_PointerUp;
    }

    public void RefreshModel()
    {
        if (workspace.Model is not PackageModel model)
        {
            shownModel = null;
            ModelTree.Items.Clear();
            Viewport.Children.Clear();
            Viewport.Children.Add(new DefaultLights());
            hitTargets.Clear();
            Inspector.Text = "请修正问题列表中的参数后重新生成。";
            return;
        }
        bool fresh = !ReferenceEquals(shownModel, model);
        shownModel = model;
        if (fresh)
        {
            ModelTree.Items.Clear();
            var root = TreeItem(new("package", model.Name, model.Blocks.ToList()));
            root.IsExpanded = true;
            ModelTree.Items.Add(root);
            var groups = model.Blocks.GroupBy(b => b.GroupId).OrderByDescending(g => (g.Min(b => b.Origin.Z) + g.Max(b => b.Maximum.Z)) / 2).ToList();
            var items = groups.ToDictionary(g => g.Key, group =>
            {
                var item = TreeItem(new(group.Key, group.First().GroupName, group.ToList()));
                item.IsExpanded = true;
                foreach (var block in group.OrderByDescending(b => b.Origin.Z + b.Size.Z / 2))
                    item.Items.Add(TreeItem(new(block.Id, block.Name, [block], block)));
                return item;
            });
            foreach (var group in groups)
            {
                string? parent = model.Groups[group.Key].Parent;
                var container = parent != null && items.TryGetValue(parent, out var parentItem) ? parentItem : root;
                container.Items.Add(items[group.Key]);
            }
        }

        updatingModelTree = true;
        try
        {
            foreach (var item in TreeItems())
                if (item.Tag is ModelNode n)
                {
                    bool selected = n.Block != null ? workspace.Selected.Contains(n.Id) : workspace.InspectedGroup?.Id == n.Id;
                    bool hidden = n.Block != null && workspace.Hidden.Contains(n.Id);
                    string count = n.Block == null ? $"{n.Blocks.Count(b => !workspace.Hidden.Contains(b.Id))}/{n.Blocks.Count}" : "";
                    item.Header = new TreeRow(n.Name, n.Block == null, count, hidden: hidden, modelGroup: true);
                    item.IsSelected = selected && workspace.Selected.Count <= 1;
                    TreeRow.SetIsHighlighted(item, selected);
                    System.Windows.Automation.AutomationProperties.SetName(item, n.Name + (hidden ? "（隐藏）" : ""));
                }
        }
        finally { updatingModelTree = false; }

        Viewport.Children.Clear();
        hitTargets.Clear();
        Viewport.Children.Add(new DefaultLights());
        foreach (var b in model.Blocks.Where(b => !workspace.Hidden.Contains(b.Id)).OrderBy(b => b.StructureType == "encapsulant" ? 1 : 0))
        {
            var material = model.Materials[b.MaterialId];
            var color = workspace.Selected.Contains(b.Id) ? Color.FromRgb(61, 158, 255) : MaterialPresentation.Swatch(material);
            color.A = b.StructureType == "encapsulant" && !workspace.Selected.Contains(b.Id) ? (byte)65 : (byte)240;
            var brush = new SolidColorBrush(color);
            brush.Freeze();
            var fill = new DiffuseMaterial(brush);
            fill.Freeze();
            var box = new BoxVisual3D
            {
                Center = new(b.Origin.X + b.Size.X / 2, b.Origin.Y + b.Size.Y / 2, b.Origin.Z + b.Size.Z / 2),
                Length = b.Size.X,
                Width = b.Size.Y,
                Height = b.Size.Z,
                Material = fill,
                BackMaterial = fill
            };
            Viewport.Children.Add(box);
            hitTargets[box] = b.Id;
        }

        UpdateInspector();
        if (fresh)
            Viewport.Dispatcher.BeginInvoke(() => Viewport.ZoomExtents());
    }

    TreeViewItem TreeItem(ModelNode node)
    {
        TreeViewItem item = node.Id == "package" ? new ModelRootItem() : new TreeViewItem();
        item.Header = node.Name;
        item.Tag = node;
        item.Style = (Style)ModelTree.FindResource(node.Id == "package" ? "ExplorerModelRootItem" : "ExplorerTreeItem");
        item.ContextMenuOpening += (_, e) =>
        {
            var targets = node.Block != null && workspace.Selected.Contains(node.Id) ? workspace.Model!.Blocks.Where(b => workspace.Selected.Contains(b.Id)).ToList() : node.Blocks;
            var menu = new ContextMenu();
            void Add(string title, Action action)
            {
                var entry = new MenuItem
                {
                    Header = title
                };
                entry.Click += (_, _) => action();
                menu.Items.Add(entry);
            }

            Add("显示", () => workspace.ChangeVisibility(targets.Select(b => b.Id), true));
            Add("隐藏", () => workspace.ChangeVisibility(targets.Select(b => b.Id), false));
            Add("只显示", () => workspace.ChangeVisibility(targets.Select(b => b.Id), true, true));
            menu.Items.Add(new Separator());
            Add("显示全部", () => workspace.ChangeVisibility(workspace.Model!.Blocks.Select(b => b.Id), true));
            Add("隐藏全部", () => workspace.ChangeVisibility(workspace.Model!.Blocks.Select(b => b.Id), false));
            item.ContextMenu = menu;
            e.Handled = false;
        };
        item.ContextMenu = new ContextMenu();
        return item;
    }

    IEnumerable<TreeViewItem> TreeItems()
    {
        IEnumerable<TreeViewItem> Walk(ItemsControl parent)
        {
            foreach (TreeViewItem item in parent.Items)
            {
                yield return item;
                foreach (var child in Walk(item))
                    yield return child;
            }
        }

        return Walk(ModelTree);
    }

    public void ExpandTree(bool expand)
    {
        foreach (var item in TreeItems())
            if (item.Items.Count > 0)
                item.IsExpanded = item.Tag is ModelNode { Id: "package" } || expand;
    }
}
