using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class ModelBuilder
{
    public static GenerationResult Generate(ProjectDocument document, PackageDefinition definition, MaterialCatalog materials,
        ValidationRules rules, IReadOnlyDictionary<string, ModelGroup> groups)
    {
        var snapshot = document.Clone();
        var issues = InputValidator.Validate(snapshot, definition, materials, rules).ToList();
        if (issues.Any(i => i.Severity == IssueSeverity.Error)) return new(null, issues);
        PackageModel model;
        try
        {
            var context = new BuildContext(definition, snapshot.Values, snapshot.Name, materials, groups, snapshot.MaterialAssignments, snapshot.CustomMaterials);
            var geometry = snapshot.TemplateId switch
            {
                "bare_die" => BareDieGenerator.Generate(context),
                "cbga_fc" => CbgaFcGenerator.Generate(context),
                "pbga_fc" => PbgaFcGenerator.Generate(context),
                "pbga_wb" => PbgaWbGenerator.Generate(context),
                "chip_array" => ChipArrayGenerator.Generate(context),
                "qfn" => QfnGenerator.Generate(context),
                "pqfp" => PqfpGenerator.Generate(context),
                "sop" => SopGenerator.Generate(context),
                _ => throw new ArgumentException($"未知封装类型 {snapshot.TemplateId}。")
            };
            model = context.Complete(geometry);
        }
        catch (ArgumentException error)
        {
            issues.Add(ValidationIssue.Error("generation.prerequisite", ValidationStage.Generation, error.Message));
            return new(null, issues);
        }
        issues.AddRange(ModelValidator.Validate(model, rules, snapshot.Values["die.power"]!.Value<double>()));
        return new(model, issues);
    }
}
