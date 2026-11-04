namespace PackStudio.Core;

public static class ModelValidator
{
    public static IReadOnlyList<ValidationIssue> Validate(PackageModel model, ValidationRules rules, double? expectedPower = null)
    {
        var issues = new List<ValidationIssue>();
        void Error(string code, string message, params string[] entities) => issues.Add(new(code, IssueSeverity.Error, ValidationStage.Model, message, [], entities));
        if (model.Blocks.Count == 0) Error("model.empty", "模型不包含几何块。");
        foreach (var duplicate in model.Blocks.GroupBy(b => b.Id).Where(g => g.Count() > 1))
            Error("model.id", $"重复几何 ID {duplicate.Key}。", duplicate.Key);
        foreach (var block in model.Blocks)
        {
            if (block.Size.Components.Any(v => !double.IsFinite(v) || v <= 0) || block.Origin.Components.Any(v => !double.IsFinite(v)) || block.Maximum.Components.Any(v => !double.IsFinite(v)))
                Error("model.geometry", $"{block.Name} 的位置或尺寸无效。", block.Id);
            if (!model.Materials.ContainsKey(block.MaterialId)) Error("model.material.reference", $"未知材料 {block.MaterialId}。", block.Id);
            if (!model.Groups.ContainsKey(block.GroupId)) Error("model.group.reference", $"未知模型组 {block.GroupId}。", block.Id);
        }
        foreach (var material in model.Materials.Values)
            foreach (string message in FieldRules.MaterialErrors(material))
                issues.Add(new("model.material", IssueSeverity.Error, ValidationStage.Model, $"材料 {material.Name}：{message}", [],
                    model.Blocks.Where(b => b.MaterialId == material.Id).Select(b => b.Id).ToArray()));
        var geometry = model.Geometry;
        if (new[] { geometry.Outline, geometry.Grid, geometry.Bottom, geometry.Top }.Any(f => !double.IsFinite(f.Length) || f.Length <= 0 || !double.IsFinite(f.Width) || f.Width <= 0) || !double.IsFinite(geometry.Height) || geometry.Height <= 0)
            Error("model.metadata", "模型包围尺寸和总高必须为有限正数。");
        var ids = model.Blocks.Select(b => b.Id).ToHashSet();
        foreach (var source in model.Sources)
            if (!FieldRules.NonNegative(source.Power) || !ids.Contains(source.BlockId))
                Error("model.source", "热源功率或目标无效。", source.BlockId);
        if (expectedPower.HasValue && Math.Abs(model.Sources.Sum(s => s.Power) - expectedPower.Value) > 1e-8 * Math.Max(1, Math.Abs(expectedPower.Value)))
            Error("model.power", "模型总功率与输入功率不一致。");
        foreach (var auxiliary in model.Auxiliary)
            if (auxiliary.Origin.Components.Any(v => !double.IsFinite(v)) || auxiliary.Size?.Components.Any(v => !double.IsFinite(v) || v <= 0) == true)
                Error("model.auxiliary", $"辅助实体 {auxiliary.Name} 的位置或尺寸无效。");
        if (!issues.Any(i => i.Code is "model.geometry" or "model.id" or "model.empty"))
        {
            var overlapRule = rules.Checks.FirstOrDefault(c => c["stage"].Text() == "model" && c["check"].Text() == "overlap");
            if (overlapRule != null)
                foreach (var (a, b) in OverlapDetector.Find(model.Blocks))
                    issues.Add(rules.Issue(overlapRule, ValidationStage.Model, "矩形块存在正体积重叠。", [], [a.Id, b.Id]) with { Severity = IssueSeverity.Warning });
        }
        return issues.AsReadOnly();
    }
}
