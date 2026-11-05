using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

internal sealed class InputChecks(JObject values, List<ValidationIssue> issues)
{
    // Only field errors suppress dependent relations; independent relations still run.
    readonly string[] invalidPaths = issues.Where(i => i.Severity == IssueSeverity.Error).SelectMany(i => i.ParameterPaths).ToArray();
    public JObject Values { get; } = values;

    public bool Invalid(string key) => invalidPaths.Any(p => p == key || p.StartsWith(key + "[") ||
        p.StartsWith(key + ".") || key.StartsWith(p + ".") || key.StartsWith(p + "["));
    public static double Number(JToken? value) => value?.Type is JTokenType.Float or JTokenType.Integer && double.IsFinite(value.Value<double>())
        ? value.Value<double>() : double.NaN;
    public double N(string key) => Invalid(key) ? double.NaN : Number(Values[key]);
    public bool B(string key) => !Invalid(key) && Values[key].Flag();
    public string T(string key) => Invalid(key) ? "" : Values[key].Text();

    public void Check(bool failed, string code, string message, params string[] paths)
    {
        if (failed && !paths.Any(Invalid))
            issues.Add(ValidationIssue.Error(code, ValidationStage.Input, message, paths));
    }

    public void Fits(string inner, string outer) => Check(N(inner) > N(outer), "input.package.fit", "部件尺寸必须位于外轮廓内。", inner, outer);
    public void Ring(string outerX, string outerY, string innerX, string innerY) => Check(N(innerX) >= N(outerX) || N(innerY) >= N(outerY),
        "input.cavity", "内孔必须位于外轮廓内。", outerX, outerY, innerX, innerY);
}
