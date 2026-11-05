namespace PackStudio.Core;

public static class ModelValidator
{
    public static IReadOnlyList<ValidationIssue> Validate(PackageModel model, ValidationRules rules, double? expectedPower = null)
    {
        var issues = new List<ValidationIssue>();
        void Error(string code, params string[] entities) => issues.Add(rules.Create(code, ValidationStage.Model, [], entities));
        if (model.Blocks.Count == 0) Error("model.empty");
        foreach (var duplicate in model.Blocks.GroupBy(b => b.Id).Where(g => g.Count() > 1))
            Error("model.id", duplicate.Key);
        foreach (var block in model.Blocks)
        {
            if (block.Size.Components.Any(v => !double.IsFinite(v) || v <= 0) || block.Origin.Components.Any(v => !double.IsFinite(v)) || block.Maximum.Components.Any(v => !double.IsFinite(v)))
                Error("model.geometry", block.Id);
            if (!model.Materials.ContainsKey(block.MaterialId)) Error("model.material.reference", block.Id);
            if (!model.Groups.ContainsKey(block.GroupId)) Error("model.group.reference", block.Id);
        }
        foreach (var material in model.Materials.Values)
            foreach (string message in FieldRules.MaterialErrors(material, rules))
                issues.Add(rules.Create("model.material", ValidationStage.Model, [],
                    model.Blocks.Where(b => b.MaterialId == material.Id).Select(b => b.Id).ToArray(), detail: material.Name, reason: message));
        var geometry = model.Geometry;
        if (new[] { geometry.Outline, geometry.Grid, geometry.Bottom, geometry.Top }.Any(f => !double.IsFinite(f.Length) || f.Length <= 0 || !double.IsFinite(f.Width) || f.Width <= 0) || !double.IsFinite(geometry.Height) || geometry.Height <= 0)
            Error("model.metadata");
        var ids = model.Blocks.Select(b => b.Id).ToHashSet();
        foreach (var source in model.Sources)
            if (!FieldRules.NonNegative(source.Power) || !ids.Contains(source.BlockId))
                Error("model.source", source.BlockId);
        if (expectedPower.HasValue && Math.Abs(model.Sources.Sum(s => s.Power) - expectedPower.Value) > 1e-8 * Math.Max(1, Math.Abs(expectedPower.Value)))
            Error("model.power");
        foreach (var auxiliary in model.Auxiliary)
            if (auxiliary.Origin.Components.Any(v => !double.IsFinite(v)) || auxiliary.Size?.Components.Any(v => !double.IsFinite(v) || v <= 0) == true)
                Error("model.auxiliary", auxiliary.Name);
        if (!issues.Any(i => i.Code is "model.geometry" or "model.id" or "model.empty"))
        {
            var overlapRule = rules.Checks.FirstOrDefault(c => c["stage"].Text() == "model" && c["check"].Text() == "overlap");
            if (overlapRule != null)
                foreach (var (a, b) in OverlapDetector.Find(model.Blocks))
                    issues.Add(rules.Create(overlapRule["id"].Text(), ValidationStage.Model, [], [a.Id, b.Id]));
        }
        return issues.AsReadOnly();
    }
}
