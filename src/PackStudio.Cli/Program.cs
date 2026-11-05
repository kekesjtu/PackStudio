using PackStudio.Cli;
using PackStudio.Core;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

try
{
    string root = Directory.GetCurrentDirectory();
    var catalog = new RuntimeDataCatalog(Path.Combine(root, "runtime_data"));
    if (args.Length == 0)
        throw new ArgumentException("用法：catalog | values request.json | generate request.json output.packstudio.xml");
    if (args[0] == "catalog")
    {
        Console.WriteLine(JsonConvert.SerializeObject(catalog.Families.Select(f => new { id = f.Id, name = f.Name, presets = catalog.Load(f.Id).Presets.Select(p => p.Name) })));
        return 0;
    }

    if (args.Length < 2) throw new ArgumentException("需要请求或方案文件路径。");
    var input = JsonData.Read(args[1]);
    ProjectDocument document;
    document = input["template_id"] != null ? RequestDocument.Parse(input, catalog) : ProjectStore.Load(args[1], catalog);
    if (args[0] == "values")
    {
        Console.WriteLine(document.Values.ToString(Formatting.None));
        return 0;
    }

    if (args[0] != "generate" || args.Length < 3)
        throw new ArgumentException("generate 需要请求文件和输出文件路径。");
    var result = ModelBuilder.Generate(document, catalog.Load(document.TemplateId), catalog.Materials, catalog.LoadValidation(document.TemplateId), catalog.Groups);
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
