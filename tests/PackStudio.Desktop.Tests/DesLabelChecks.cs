using System.IO;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop.Tests;
static class DesLabelChecks
{
    public static void Run()
    {
        string root = Path.GetFullPath("runtime_data");
        var labels = JsonData.Read(Path.Combine(root, "des_field_labels.json"));
        var missing = new List<string>();
        foreach (var family in PackageCatalog.Families)
        {
            var template = JsonData.Read(Path.Combine(root, "templates", family.Id + ".json"));
            foreach (var field in ((JArray)template["fields"]!).OfType<JObject>().Where(f => f["control"].Text() is "number" or "integer" or "integer_spinbox"))
            {
                var entry = labels[family.Id]?[field["key"].Text()];
                bool covered = entry is JObject choices ? choices.Properties().All(p => p.Value.Text().Length > 0) : entry.Text().Length > 0;
                if (!covered)
                    missing.Add(family.Id + "." + field["key"].Text());
            }
        }

        if (missing.Count > 0)
            throw new Exception("DES 符号缺失：" + string.Join("、", missing));
        Console.WriteLine("PASS DES symbols cover every numeric wizard field");
    }
}
