using PackStudio.Core;

namespace PackStudio.Desktop;

public sealed partial class ModelPresenter
{
    void UpdateInspector()
    {
        if (workspace.Model is not PackageModel model) return;
        if (workspace.InspectedGroup is ModelNode group)
        {
            var blocks = group.Blocks;
            var ids = blocks.Select(b => b.Id).ToHashSet();
            var materialIds = blocks.Select(b => b.MaterialId).Distinct().ToList();
            bool package = group.Id == "package";
            string heading = package ? $"封装概览\n{model.Name}" : $"组件分组\n{group.Name}";
            string detail = package
                ? $"封装类型：{workspace.Catalog.Families.Single(c => c.Id == model.TemplateId).Name}\n组件分组：{blocks.Select(b => b.GroupId).Distinct().Count()}\n材料种类：{materialIds.Count}"
                : $"所属封装：{model.Name}\n材料：{string.Join("、", materialIds.Select(id => model.Materials[id].Name))}";
            Inspector.Text = $"{heading}\n\n{detail}\n矩形块数：{blocks.Count}\n可见块数：{blocks.Count(b => !workspace.Hidden.Contains(b.Id))}\n" +
                $"包围尺寸：{Bounds(blocks)} mm\n总功率：{model.Sources.Where(s => ids.Contains(s.BlockId)).Sum(s => s.Power):G6} W";
            return;
        }

        var selected = model.Blocks.Where(b => workspace.Selected.Contains(b.Id)).ToList();
        if (selected.Count == 0)
        {
            Inspector.Text = "点击根节点查看封装概览，点击分组查看组件统计。\n\n点击实体块查看物性，再次点击取消选择。\nCtrl 多选，Shift 连选。\n右键菜单可显示、隐藏或隔离组件。";
            return;
        }
        if (selected.Count > 1)
        {
            Inspector.Text = $"已选择 {selected.Count} 个矩形块\n总体积：{selected.Sum(b => b.Size.Volume):G6} mm³";
            return;
        }

        var b = selected[0];
        var m = model.Materials[b.MaterialId];
        Inspector.Text = $"{b.Name}\n\n类型：{b.StructureType}\n位置：{b.Origin.X:G6}, {b.Origin.Y:G6}, {b.Origin.Z:G6} mm\n尺寸：{b.Size.X:G6} × {b.Size.Y:G6} × {b.Size.Z:G6} mm\n\n材料：{m.Name}\nkx / ky / kz：\n{m.Conductivity.X:G6} / {m.Conductivity.Y:G6} / {m.Conductivity.Z:G6} W/(m·K)\n密度：{m.Density:G6} kg/m³\n比热：{m.SpecificHeat:G6} J/(kg·K)\n功率：{model.Sources.Where(s => s.BlockId == b.Id).Sum(s => s.Power):G6} W";
    }

    static string Bounds(List<Block> blocks)
    {
        if (blocks.Count == 0) return "0 × 0 × 0";
        double x = blocks.Max(b => b.Maximum.X) - blocks.Min(b => b.Origin.X);
        double y = blocks.Max(b => b.Maximum.Y) - blocks.Min(b => b.Origin.Y);
        double z = blocks.Max(b => b.Maximum.Z) - blocks.Min(b => b.Origin.Z);
        return $"{x:G6} × {y:G6} × {z:G6}";
    }
}
