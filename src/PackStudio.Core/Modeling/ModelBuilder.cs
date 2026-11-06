using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class ModelBuilder
{
    public static GenerationResult Generate(ProjectDocument document, PackageDefinition definition, MaterialCatalog materials,
        IReadOnlyDictionary<string, ModelGroup> groups)
    {
        var snapshot = document.Clone();
        var issues = InputValidator.Validate(snapshot, definition, materials).ToList();
        if (issues.Any(i => i.Severity == IssueSeverity.Error)) return new(null, issues);
        PackageModel model;
        IReadOnlySet<string> derivedMaterialIds;
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
                _ => throw new ModelGenerationException("generation.template", $"未知封装类型 {snapshot.TemplateId}。")
            };
            model = context.Complete(geometry);
            derivedMaterialIds = context.DerivedMaterialIds;
        }
        catch (ModelGenerationException error)
        {
            issues.Add(ValidationIssue.Error(error.Code, ValidationStage.Generation, error.Message));
            return new(null, issues);
        }
        issues.AddRange(ModelValidator.Validate(model, snapshot.Values["die.power"]!.Value<double>(), derivedMaterialIds));
        return new(model, issues);
    }
}
