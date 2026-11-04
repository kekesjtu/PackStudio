using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static TestSuite;

static class FourLayerChecks
{
    public static void Run(TestSuite tests)
    {
        foreach (string family in new[] { "chip_array", "pbga_wb" })
            tests.Case("parameters", family + " loads four-layer settings only on explicit selection", () =>
            {
                var source = tests.Catalog.Load(family);
                int reads = 0;
                var template = new Template(source.Info, source.Data, source.Presets, () =>
                {
                    reads++;
                    return FourLayerConfiguration.Load(Path.Combine(tests.Root, "runtime_data", "presets", family, "four_layer.json"), family);
                });
                var draft = new CreationDraft(template, template.DefaultPreset);
                draft.Set("die.power", new JValue(3));
                draft.Complete("two-layer");
                Assert(reads == 0, "four-layer settings eagerly read");
                draft.Set("substrate.layers", new JValue("4-Layer"));
                Assert(reads == 1 && ((JArray)draft.Values["metal.layers"]!).Count == 4, "explicit selection did not load four-layer settings");
                draft.Set("substrate.layers", new JValue("2-Layer"));
                Assert(((JArray)draft.Values["metal.layers"]!).Count == 2, "two-layer selection retained four-layer defaults");
                draft.Set("substrate.layers", new JValue("4-Layer"));
                draft.Complete("four-layer");
                Assert(reads == 1, "four-layer settings were repeatedly read");
            });
        tests.Case("parameters", "Wirebond four-layer settings retain component-specific behavior", () =>
        {
            var template = tests.Catalog.Load("pbga_wb");
            var draft = new CreationDraft(template, "PBGA_208_23X23mm");
            draft.Set("substrate.layers", new JValue("4-Layer"));
            Near(draft.Values["vias.rows"].Number(), 3, "four-layer via rows");
            Near(draft.Values["vias.columns"].Number(), 3, "four-layer via columns");
            Near(draft.Values["spreader.length"].Number(), 11.22, "four-layer spreader length");
            Near(draft.Values["spreader.width"].Number(), 11.22, "four-layer spreader width");
            draft.Set("spreader.length", new JValue(12));
            Near(draft.Complete("explicit spreader").Values["spreader.length"].Number(), 12, "explicit component value overwritten");
        });
    }
}
