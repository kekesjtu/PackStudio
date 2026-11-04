namespace PackStudio.Core;

public sealed class GenerationResult(PackageModel? model, IEnumerable<ValidationIssue> issues)
{
    public PackageModel? Model { get; } = model;
    public IReadOnlyList<ValidationIssue> Issues { get; } = Array.AsReadOnly(issues.ToArray());
    public bool HasErrors => Issues.Any(i => i.Severity == IssueSeverity.Error);
    public bool CanPreview => Model is { Blocks.Count: > 0 } && Model.Blocks.All(b =>
        b.Origin.Components.All(double.IsFinite) && b.Size.Components.All(v => double.IsFinite(v) && v > 0) &&
        b.Maximum.Components.All(double.IsFinite) && Model.Materials.ContainsKey(b.MaterialId) && Model.Groups.ContainsKey(b.GroupId));
    public bool CanExport => Model != null && CanPreview && !HasErrors;
}
