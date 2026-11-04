using System.IO;
using System.Text.RegularExpressions;
using Newtonsoft.Json.Linq;
using PackStudio.Core;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;
static partial class DesLabelChecks
{
    // 数值字段的标签只写中文名，DES 符号由符号列单独显示，避免标签内重复标注。
    [GeneratedRegex(@"\s+[A-Za-z][A-Za-z0-9_]*$")]
    private static partial Regex TrailingSymbol();

    public static void Run()
    {
        var selector = new JObject { ["des_symbol"] = new JObject { ["selector"] = "variant", ["cases"] = new JObject { ["A"] = "La", ["B"] = "Lb" } } };
        if (TemplateSymbols.Resolve(selector, new JObject { ["variant"] = "B" }) != "Lb")
            throw new Exception("symbol selector ignored");
        if (TemplateSymbols.Resolve(selector, new JObject { ["variant"] = new JArray("B") }) != "")
            throw new Exception("invalid selector cannot remain editable");
        string root = Path.GetFullPath("runtime_data");
        var missing = new List<string>();
        var duplicated = new List<string>();
        var catalog = new RuntimeDataCatalog(root);
        foreach (var family in catalog.Families)
        {
            var template = catalog.Load(family.Id);
            foreach (var field in template.Ui.Fields.OfType<JObject>().Where(f => !f["creation_option"].Flag() && f["control"].Text() is "number" or "integer" or "integer_spinbox"))
            {
                var entry = field["des_symbol"];
                bool covered = entry is JObject choices ? ((JObject)choices["cases"]!).Properties().All(p => p.Value.Text().Length > 0) : entry.Text().Length > 0;
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
