using System.IO;
using System.Text.RegularExpressions;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop.Tests;
static partial class DesLabelChecks
{
    // 数值字段的标签只写中文名，DES 符号由符号列单独显示，避免标签内重复标注。
    [GeneratedRegex(@"\s+[A-Za-z][A-Za-z0-9_]*$")]
    private static partial Regex TrailingSymbol();

    public static void Run()
    {
        string root = Path.GetFullPath("runtime_data");
        var labels = JsonData.Read(Path.Combine(root, "des_field_labels.json"));
        var missing = new List<string>();
        var duplicated = new List<string>();
        foreach (var family in PackageCatalog.Families)
        {
            var template = JsonData.Read(Path.Combine(root, "templates", family.Id + ".json"));
            foreach (var field in ((JArray)template["fields"]!).OfType<JObject>().Where(f => f["control"].Text() is "number" or "integer" or "integer_spinbox"))
            {
                var entry = labels[family.Id]?[field["key"].Text()];
                bool covered = entry is JObject choices ? choices.Properties().All(p => p.Value.Text().Length > 0) : entry.Text().Length > 0;
                if (!covered)
                    missing.Add(family.Id + "." + field["key"].Text());
                if (TrailingSymbol().IsMatch(field["label"].Text()))
                    duplicated.Add(family.Id + "." + field["key"].Text() + "=" + field["label"].Text());
            }
        }

        if (missing.Count > 0)
            throw new Exception("DES 符号缺失：" + string.Join("、", missing));
        if (duplicated.Count > 0)
            throw new Exception("标签内重复标注 DES 符号：" + string.Join("、", duplicated));
        Console.WriteLine("PASS DES symbols cover every numeric wizard field and labels carry no duplicated symbol");
    }
}
