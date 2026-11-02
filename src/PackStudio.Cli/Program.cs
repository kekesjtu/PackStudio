using PackStudio.Core;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

try
{
    string root = Directory.GetCurrentDirectory();
    var catalog = new PackageCatalog(Path.Combine(root, "runtime_data"));
    if (args.Length == 0)
        throw new ArgumentException("用法：catalog | values request.json | generate request.json output.floxml");
    if (args[0] == "catalog")
    {
        Console.WriteLine(JsonConvert.SerializeObject(PackageCatalog.Families.Select(f => new { id = f.Id, name = f.Name, presets = catalog.Load(f.Id).Presets.Select(p => p.Id) })));
        return 0;
    }

    var input = JsonData.Read(args[1]);
    ProjectDocument document;
    document = input["template_id"] != null ? RequestDocument.Parse(input, catalog) : ProjectDocument.Load(args[1]);
    if (args[0] == "values")
    {
        Console.WriteLine(document.Values.ToString(Formatting.None));
        return 0;
    }

    if (args[0] != "generate" || args.Length < 3)
        throw new ArgumentException("generate 需要请求文件和输出文件路径。");
    var model = new ModelBuilder(catalog).Generate(document);
    FloXml.Save(model, args[2], Path.Combine(root, "output_format/floxml/xmlSchema.xsd"));
    Console.WriteLine(JsonConvert.SerializeObject(new { blocks = model.Blocks.Count, power_w = model.Sources.Sum(s => s.Power), warnings = model.Warnings }));
    return 0;
}
catch (Exception ex)
{
    Console.Error.WriteLine(ex.Message);
    return 1;
}
