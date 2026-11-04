namespace PackStudio.Core;

public enum IssueSeverity { Warning, Error }
public enum ValidationStage { Input, Generation, Model }

public sealed record ValidationIssue(string Code, IssueSeverity Severity, ValidationStage Stage, string Message,
    IReadOnlyList<string> ParameterPaths, IReadOnlyList<string> EntityIds)
{
    public static ValidationIssue Error(string code, ValidationStage stage, string message, params string[] paths)
        => new(code, IssueSeverity.Error, stage, message, paths, []);
}
