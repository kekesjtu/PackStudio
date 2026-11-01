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

        var unlabeled = new List<string>();
        foreach (var family in PackageCatalog.Families)
        {
            var template = JsonData.Read(Path.Combine(root, "templates", family.Id + ".json"));
            foreach (var field in ((JArray)template["fields"]!).OfType<JObject>().Where(f => f["options"]!.HasValues && f["key"].Text() != "package.type"))
                foreach (var option in (JArray)field["options"]!)
                {
                    string? text = field["option_labels"]?[option.ToString()].Text("");
                    if (text == null || text.Length == 0 || text.Any(char.IsAsciiLetter))
                        unlabeled.Add(family.Id + "." + field["key"].Text() + "=" + option);
                }
        }

        if (unlabeled.Count > 0)
            throw new Exception("下拉选项缺少中文名：" + string.Join("、", unlabeled));
        Console.WriteLine("PASS DES symbols cover every numeric wizard field and every choice has a Chinese name");
    }
}
