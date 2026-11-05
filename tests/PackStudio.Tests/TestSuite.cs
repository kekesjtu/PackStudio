using PackStudio.Core;
using Newtonsoft.Json.Linq;
using System.Xml.Linq;

sealed class TestSuite(string root, HashSet<string> suites)
{
    public string Root { get; } = root;
    public RuntimeDataCatalog Catalog { get; } = new(Path.Combine(root, "runtime_data"));
    int passed, failed;

    public ProjectDocument Create(PackageDefinition definition, string? presetId = null, string? name = null, JObject? options = null)
    {
        string preset = presetId ?? definition.DefaultPreset;
        var selection = definition.DisplayDefaults(preset);
        string layers = options?.Property("substrate.layers") is { } submitted ? submitted.Value.Text() : selection["substrate.layers"].Text();
        var fourLayer = definition.Info.Id is "chip_array" or "pbga_wb" && layers == "4-Layer" ? Catalog.LoadFourLayer(definition.Info.Id) : null;
        var padSelection = options?["package.exposed_pad"] ?? selection["package.exposed_pad"];
        var exposedPad = definition.Info.Id is "sop" or "pqfp" && padSelection.Flag() ? Catalog.LoadExposedPad(definition.Info.Id) : null;
        return PackageInitializer.Create(definition, preset, name, options, fourLayer, exposedPad);
    }

    public GenerationResult GenerateResult(ProjectDocument document) => ModelBuilder.Generate(document,
        Catalog.Load(document.TemplateId), Catalog.Materials, Catalog.Groups);

    public PackageModel Generate(ProjectDocument document)
    {
        var result = GenerateResult(document);
        if (result.HasErrors || result.Model == null)
            throw new ArgumentException(string.Join(" ", result.Issues.Select(i => i.Message)));
        return result.Model;
    }

    public GenerationResult Result(PackageModel model) => new(model, ModelValidator.Validate(model));
    public XDocument Export(PackageModel model) => ModelXmlExporter.Export(Result(model));

    public void Case(string suite, string name, Action run)
    {
        if (suites.Count > 0 && !suites.Contains(suite)) return;
        try { run(); passed++; }
        catch (Exception error) { failed++; Console.WriteLine($"FAIL {suite}/{name}: {error.Message}"); }
    }

    public int Finish()
    {
        Console.WriteLine($"{passed} passed, {failed} failed");
        return failed == 0 && passed > 0 ? 0 : 1;
    }

    public static void Assert(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
    }

    public static void Near(double actual, double expected, string message)
        => Assert(double.IsFinite(actual) && Math.Abs(actual - expected) <= 1e-8 * Math.Max(1, Math.Abs(expected)), $"{message}: {actual} != {expected}");

    public static void Reject(Action run)
    {
        try { run(); }
        catch (ArgumentException) { return; }
        throw new Exception("invalid input was accepted");
    }
}
