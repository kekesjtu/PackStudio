using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static TestSuite;

static class BoundaryChecks
{
    public static void Run(TestSuite tests)
    {
        tests.Case("parameters", "creation preserves explicit tables", () =>
        {
            var template = tests.Catalog.Load("chip_array");
            double explicitHeight = template.DisplayDefaults(template.DefaultPreset)["substrate.thickness"].Number();
            var options = new JObject { ["substrate.thickness"] = explicitHeight, ["substrate.layers"] = "4-Layer" };
            var baseline = tests.Create(template, options: options);
            Near(baseline.Values["substrate.thickness"].Number(), explicitHeight, "equal-to-default user input lost during branch selection");
            var table = (JArray)baseline.Values["metal.layers"]!.DeepClone();
            table[0]!["thickness"] = 0.03;
            options["metal.layers"] = table;
            options["trace.solid_thickness"] = 0.05;
            var document = tests.Create(template, name: "explicit table", options: options);
            Near(document.Values["metal.layers"]![0]!["thickness"].Number(), 0.03, "finalization replaced explicit table");
            Near(document.Values["metal.layers"]![1]!["thickness"].Number(), table[1]!["thickness"].Number(), "finalization recomputed explicit inner layers");
            tests.Generate(document);
        });
        tests.Case("materials", "all material views use the same representative", () =>
        {
            var template = tests.Catalog.Load("cbga_fc");
            var document = tests.Create(template);
            document.MaterialAssignments["group-substrate"] = "copper";
            var model = tests.Generate(document);
            var custom = tests.Catalog.Materials.Items["copper"] with { Density = 1234 };
            document.CustomMaterials.Add(custom with { Id = "custom-copper", Density = 2345 });
            document.CustomMaterials.Add(custom);
            var selection = template.MaterialSelections.Single(s => s["key"].Text() == "group-substrate");
            var dropdown = MaterialSelection.Choices(tests.Catalog.Materials, template, document, selection, model);
            var library = MaterialSelection.Available(tests.Catalog.Materials, template, document, model);
            Assert(dropdown.SelectedId == custom.Id, "assigned material representative did not win");
            Near(dropdown.Items.Single(m => m.Name == custom.Name).Density, 1234, "custom properties did not override model/library");
            Assert(dropdown.Items.Single(m => m.Name == custom.Name) == library.Single(m => m.Name == custom.Name), "dropdown and library disagree");
        });
    }
}
