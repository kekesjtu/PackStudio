using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Media3D;
using HelixToolkit.Wpf;
using PackStudio.Core;

namespace PackStudio.Desktop;
public partial class MainWindow
{
    sealed record Node(string Id, string Name, List<Block> Blocks, Block? Block = null);
    readonly Dictionary<Visual3D, string> hitTargets = [];
    PackageModel? shownModel;
    string? rangeAnchor;
    static readonly Dictionary<string, string> GroupLabels = new()
    {
        ["die"] = "芯片",
        ["encapsulant"] = "塑封",
        ["substrate"] = "基板",
        ["die-attach"] = "芯片胶",
        ["solder-ball"] = "焊球",
        ["center-solder-ball"] = "中央焊球",
        ["flip-chip-bumps"] = "凸点与底填充",
        ["lead-frame"] = "引线框",
        ["die-flag"] = "芯片承载台",
        ["tie-bars"] = "连接筋",
        ["vias"] = "通孔",
        ["traces"] = "金属层",
        ["bond-wires"] = "键合线",
        ["solder-mask"] = "阻焊层"
    };
    void RefreshModel()
    {
        if (workspace.Model is not PackageModel model)
            return;
        bool fresh = !ReferenceEquals(shownModel, model);
        shownModel = model;
        if (fresh)
        {
            ModelTree.Items.Clear();
            rangeAnchor = null;
            var root = TreeItem(new("package", model.Name, model.Blocks));
            root.IsExpanded = true;
            ModelTree.Items.Add(root);
            var groups = model.Blocks.GroupBy(b => b.GroupId).OrderByDescending(g => (g.Min(b => b.Origin.Z) + g.Max(b => b.Maximum.Z)) / 2).ToList();
            TreeViewItem? solder = null;
            foreach (var group in groups.Where(g => g.Key != "group-center-solder-ball"))
            {
                string key = group.Key[6..];
                var item = TreeItem(new(group.Key, GroupLabels.GetValueOrDefault(key, group.First().GroupName), group.ToList()));
                item.IsExpanded = true;
                foreach (var block in group.OrderByDescending(b => b.Origin.Z + b.Size.Z / 2))
                    item.Items.Add(TreeItem(new(block.Id, block.Name, [block], block)));
                root.Items.Add(item);
                if (group.Key == "group-solder-ball")
                    solder = item;
            }

            var center = groups.FirstOrDefault(g => g.Key == "group-center-solder-ball");
            if (center != null)
            {
                var item = TreeItem(new(center.Key, "中央焊球", center.ToList()));
                item.IsExpanded = true;
                foreach (var block in center.OrderByDescending(b => b.Origin.Z + b.Size.Z / 2))
                    item.Items.Add(TreeItem(new(block.Id, block.Name, [block], block)));
                (solder ?? root).Items.Add(item);
            }
        }

        foreach (var item in TreeItems())
            if (item.Tag is Node n)
            {
                bool selected = n.Block != null && workspace.Selected.Contains(n.Id), hidden = n.Block != null && workspace.Hidden.Contains(n.Id);
                string count = n.Block == null ? $"{n.Blocks.Count(b => !workspace.Hidden.Contains(b.Id))}/{n.Blocks.Count}" : "";
                item.Header = new TreeRow(n.Name, n.Block == null, count, hidden: hidden, modelGroup: true);
                TreeRow.SetIsHighlighted(item, selected);
                System.Windows.Automation.AutomationProperties.SetName(item, n.Name + (hidden ? "（隐藏）" : ""));
            }

        Viewport.Children.Clear();
        hitTargets.Clear();
        Viewport.Children.Add(new DefaultLights());
        foreach (var b in model.Blocks.Where(b => !workspace.Hidden.Contains(b.Id)).OrderBy(b => b.StructureType == "encapsulant" ? 1 : 0))
        {
            var material = model.Materials[b.MaterialId];
            var color = (Color)ColorConverter.ConvertFromString(workspace.Selected.Contains(b.Id) ? "#3D9EFF" : material.Color);
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

        WarningsText.Text = string.Join(Environment.NewLine, model.Warnings);
        UpdateInspector();
        if (fresh)
            Dispatcher.BeginInvoke(() => Viewport.ZoomExtents());
    }

    TreeViewItem TreeItem(Node node)
    {
        var item = new TreeViewItem
        {
            Header = node.Name,
            Tag = node,
            Style = (Style)FindResource("ExplorerTreeItem")
        };
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

    void ExpandTree(bool expand)
    {
        foreach (var item in TreeItems())
            if (item.Items.Count > 0)
                item.IsExpanded = item.Tag is Node { Id: "package" } || expand;
    }

    void Tree_MouseDown(object sender, MouseButtonEventArgs e)
    {
        var element = e.OriginalSource as DependencyObject;
        while (element != null && element is not TreeViewItem)
            element = VisualTreeHelper.GetParent(element);
        if (element is TreeViewItem { Tag: Node { Block: not null } node })
        {
            SelectBlock(node.Id);
            e.Handled = true;
        }
    }

    void SelectBlock(string id)
    {
        bool control = Keyboard.Modifiers.HasFlag(ModifierKeys.Control), shift = Keyboard.Modifiers.HasFlag(ModifierKeys.Shift);
        var visible = TreeItems().Where(i => i.Tag is Node { Block: not null } && AncestorsExpanded(i)).Select(i => ((Node)i.Tag).Id).ToList();
        if (shift && rangeAnchor != null && visible.Contains(rangeAnchor) && visible.Contains(id))
        {
            if (!control)
                workspace.Selected.Clear();
            int a = visible.IndexOf(rangeAnchor), b = visible.IndexOf(id);
            workspace.Selected.UnionWith(visible.Skip(Math.Min(a, b)).Take(Math.Abs(a - b) + 1));
        }
        else
        {
            if (!control)
                workspace.Selected.Clear();
            if (!workspace.Selected.Add(id) && control)
                workspace.Selected.Remove(id);
            rangeAnchor = id;
        }

        RefreshModel();
    }

    static bool AncestorsExpanded(TreeViewItem item)
    {
        var parent = ItemsControl.ItemsControlFromItemContainer(item);
        while (parent is TreeViewItem node)
        {
            if (!node.IsExpanded)
                return false;
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
        if (id != null)
            workspace.Selected.Add(id);
        rangeAnchor = id;
        RefreshModel();
    }

    void UpdateInspector()
    {
        if (workspace.Model is not PackageModel model)
            return;
        var blocks = model.Blocks.Where(b => workspace.Selected.Contains(b.Id)).ToList();
        if (blocks.Count == 0)
        {
            Inspector.Text = "在模型树或三维视图中选择组件。\n\n右键菜单可递归显示、隐藏或隔离组件。\nCtrl 多选，Shift 连选。";
            return;
        }

        if (blocks.Count > 1)
        {
            Inspector.Text = $"已选择 {blocks.Count} 个矩形块\n总体积：{blocks.Sum(b => b.Size.Volume):G6} mm³";
            return;
        }

        var b = blocks[0];
        var m = model.Materials[b.MaterialId];
        Inspector.Text = $"{b.Name}\n\n类型：{b.StructureType}\n位置：{b.Origin.X:G6}, {b.Origin.Y:G6}, {b.Origin.Z:G6} mm\n尺寸：{b.Size.X:G6} × {b.Size.Y:G6} × {b.Size.Z:G6} mm\n\n材料：{m.Name}\nkx / ky / kz：\n{m.Conductivity.X:G6} / {m.Conductivity.Y:G6} / {m.Conductivity.Z:G6} W/(m·K)\n密度：{m.Density:G6} kg/m³\n比热：{m.SpecificHeat:G6} J/(kg·K)\n功率：{model.Sources.Where(s => s.BlockId == b.Id).Sum(s => s.Power):G6} W";
    }
}
