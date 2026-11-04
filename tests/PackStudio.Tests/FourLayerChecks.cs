using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static TestSuite;

static class FourLayerChecks
{
    public static void Run(TestSuite tests)
    {
        foreach (string family in new[] { "chip_array", "pbga_wb" })
            tests.Case("parameters", family + " four-layer data is supplied only when completing creation", () =>
            {
                var definition = tests.Catalog.Load(family);
                var display = definition.DisplayDefaults(definition.DefaultPreset);
                var request = new JObject { ["substrate.layers"] = "4-Layer" };
                Assert(((JArray)display["metal.layers"]!).Count == 2, "display initialized a layer stack");
                request["substrate.layers"] = "2-Layer";
                var ordinary = PackageInitializer.Create(definition, overrides: request);
                Assert(((JArray)ordinary.Values["metal.layers"]!).Count == 2, "two-layer creation needs four-layer data");
                request["substrate.layers"] = "4-Layer";
                var fourLayer = tests.Catalog.LoadFourLayer(family);
                var document = PackageInitializer.Create(definition, overrides: request, fourLayer: fourLayer);
                Assert(((JArray)document.Values["metal.layers"]!).Count == 4, "final selection did not initialize four layers");
                Assert(ReferenceEquals(fourLayer, tests.Catalog.LoadFourLayer(family)), "four-layer data was not cached");
                Assert(((JArray)display["metal.layers"]!).Count == 2, "creation mutated display defaults");
            });
        tests.Case("parameters", "Wirebond four-layer settings retain component-specific behavior", () =>
        {
            var definition = tests.Catalog.Load("pbga_wb");
            var options = new JObject { ["substrate.layers"] = "4-Layer" };
            var document = tests.Create(definition, "PBGA_208_23X23mm", options: options);
            Near(document.Values["vias.rows"].Number(), 3, "four-layer via rows");
            Near(document.Values["vias.columns"].Number(), 3, "four-layer via columns");
            Near(document.Values["spreader.length"].Number(), 11.22, "four-layer spreader length");
            Near(document.Values["spreader.width"].Number(), 11.22, "four-layer spreader width");
            options["spreader.length"] = 12;
            Near(tests.Create(definition, "PBGA_208_23X23mm", options: options).Values["spreader.length"].Number(), 12, "explicit component value overwritten");
        });
    }
}
