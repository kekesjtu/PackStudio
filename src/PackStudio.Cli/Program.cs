using PackStudio.Cli;
using PackStudio.Core;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

const string Usage = "用法：catalog | --presets <template_id> | --help [template_id] | values request.json | generate request.json output.packstudio.xml";

try
{
    if (args is ["--help"])
    {
        Console.WriteLine(Usage);
        return 0;
    }

    string root = Directory.GetCurrentDirectory();
    var catalog = new RuntimeDataCatalog(Path.Combine(root, "runtime_data"));
    switch (args)
    {
        case ["catalog"]:
            Console.WriteLine(JsonConvert.SerializeObject(catalog.Families.Select(f => f.Id)));
            return 0;
        case ["--presets", var presetFamily]:
            Console.WriteLine(JsonConvert.SerializeObject(catalog.Load(presetFamily).Presets.Select(p => p.Name)));
            return 0;
        case ["--help", var helpFamily]:
            Console.WriteLine(ParameterHelp.Describe(catalog.Load(helpFamily).Fields).ToString(Formatting.Indented));
            return 0;
        case ["values", _, ..]:
        case ["generate", _, _, ..]:
            break;
        default:
            throw new ArgumentException(Usage);
    }

    var input = JsonData.Read(args[1]);
    ProjectDocument document;
    document = input["template_id"] != null ? RequestDocument.Parse(input, catalog) : ProjectStore.Load(args[1], catalog);
    if (args[0] == "values")
    {
        Console.WriteLine(document.Values.ToString(Formatting.None));
        return 0;
    }

    var result = ModelBuilder.Generate(document, catalog.Load(document.TemplateId), catalog.Materials, catalog.Groups);
    Console.WriteLine(JsonConvert.SerializeObject(new { blocks = result.Model?.Blocks.Count ?? 0, power_w = result.Model?.Sources.Sum(s => s.Power), issues = result.Issues,
        warnings = result.Issues.Where(i => i.Severity == IssueSeverity.Warning).Select(i => i.Message), can_preview = result.CanPreview, can_export = result.CanExport },
        new Newtonsoft.Json.Converters.StringEnumConverter()));
    if (!result.CanExport) return 2;
    ModelXmlExporter.Save(result, args[2]);
    return 0;
}
catch (Exception ex)
{
    Console.Error.WriteLine(ex);
    return 1;
}
