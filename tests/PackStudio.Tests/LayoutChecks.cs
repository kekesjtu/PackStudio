using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static TestSuite;

static class LayoutChecks
{
    public static void Run(TestSuite tests)
    {
        foreach (string family in new[] { "chip_array", "cbga_fc", "pbga_fc", "pbga_wb" })
        {
            tests.Case("layout", family + " explicit removals and central balls", () =>
            {
                var document = ProjectDocument.Create(tests.Catalog.Load(family));
                var values = document.Values;
                values["bga.rows"] = values["bga.columns"] = 5;
                values["bga.representation"] = "discrete";
                values["bga.staggered"] = false;
                values["bga.solder_removal_enabled"] = true;
                values["bga.populated_rows"] = values["bga.populated_columns"] = 5;
                values["bga.center_solder_enabled"] = false;
                values["bga.omitted_cells"] = new JArray(new JObject { ["row"] = 0, ["column"] = 0 });
                var model = tests.Builder.Generate(document);
                Assert(model.Blocks.Count(b => b.StructureType == "solder_ball") == 24, "explicit removal not applied");
                Assert(model.Blocks.All(b => b.Id != "solder-ball-r5-c1-part-1"), "removal row orientation changed");
                values["bga.center_solder_enabled"] = true;
                values["bga.center_solder_rows"] = values["bga.center_solder_columns"] = 2;
                values["bga.center_staggered"] = false;
                Assert(tests.Builder.Generate(document).Blocks.Count(b => b.StructureType == "solder_ball") == 28, "central array missing");
            });
            tests.Case("layout", family + " coordinate map", () =>
            {
                var document = ProjectDocument.Create(tests.Catalog.Load(family));
                document.Values["bga.representation"] = "discrete";
                document.Values["bga.ball_map_enabled"] = true;
                document.Values["bga.ball_map"] = new JArray(new JObject { ["id"] = "A1", ["x"] = 0.1, ["y"] = 0.2 });
                var ball = tests.Builder.Generate(document).Blocks.Single(b => b.StructureType == "solder_ball");
                Near(ball.Origin.X + ball.Size.X / 2, 0.1, "map x");
                Near(ball.Origin.Y + ball.Size.Y / 2, 0.2, "map y");
            });
        }
        tests.Case("layout", "flat request overrides", () =>
        {
            var request = new JObject { ["template_id"] = "pbga_wb", ["overrides"] = new JObject { ["pbga_wb.bga.center_solder_enabled"] = false, ["pbga_wb.bga.center_solder_rows"] = null } };
            var parsed = RequestDocument.Parse(request, tests.Catalog);
            Assert(!parsed.Values["bga.center_solder_enabled"].Flag(), "false override lost");
            Assert(parsed.Values["bga.center_solder_rows"]!.Type == JTokenType.Null, "null override lost");
        });
        tests.Case("layout", "via removal in unified values", () =>
        {
            var template = tests.Catalog.Load("pbga_wb");
            var values = template.Defaults(template.DefaultPreset);
            values["vias.configuration"] = new JObject { ["removal_enabled"] = true, ["removal_rows"] = 2, ["removal_columns"] = 2 };
            var context = new BuildContext(tests.Catalog, template, values, template.DefaultPreset, "vias");
            Assert(Vias.Omissions(context, 5, 5).Count == 4, "central via removal");
        });
    }
}
