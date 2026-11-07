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
                var document = tests.Create(tests.Catalog.Load(family));
                var values = document.Values;
                values["bga.rows"] = values["bga.columns"] = 5;
                values["bga.representation"] = "discrete";
                values["bga.staggered"] = false;
                values["bga.solder_removal_enabled"] = true;
                values["bga.populated_rows"] = values["bga.populated_columns"] = 5;
                values["bga.center_solder_enabled"] = false;
                values["bga.omitted_cells"] = new JArray(new JObject { ["row"] = 0, ["column"] = 0 });
                var model = tests.Generate(document);
                Assert(model.Blocks.Count(b => b.StructureType == "solder_ball") == 24, "explicit removal not applied");
                Assert(model.Blocks.All(b => b.Id != "solder-ball-r5-c1-part-1"), "removal row orientation changed");
                values["bga.center_solder_enabled"] = true;
                values["bga.center_solder_rows"] = values["bga.center_solder_columns"] = 2;
                values["bga.center_staggered"] = false;
                Assert(tests.Generate(document).Blocks.Count(b => b.StructureType == "solder_ball") == 28, "central array missing");
            });
            tests.Case("layout", family + " coordinate map", () =>
            {
                var document = tests.Create(tests.Catalog.Load(family));
                document.Values["bga.representation"] = "discrete";
                document.Values["bga.ball_map_enabled"] = true;
                document.Values["bga.ball_map"] = new JArray(new JObject { ["id"] = "A1", ["x"] = -0.1, ["y"] = 0.2 });
                var ball = tests.Generate(document).Blocks.Single(b => b.StructureType == "solder_ball");
                Near(ball.Origin.X + ball.Size.X / 2, -0.1, "map x");
                Near(ball.Origin.Y + ball.Size.Y / 2, 0.2, "map y");
            });
        }
        tests.Case("layout", "integral JSON floats work as populated row and column counts", () =>
        {
            var document = tests.Create(tests.Catalog.Load("cbga_fc"));
            var values = document.Values;
            values["bga.solder_removal_enabled"] = true;
            values["bga.populated_rows"] = values["bga.populated_columns"] = 4.0;
            values["bga.removal_rows"] = values["bga.removal_columns"] = JValue.CreateNull();
            var model = tests.Generate(document);
            Assert(model.Blocks.Count(b => b.StructureType == "solder_ball") == 4, "equivalent border was not generated");
            values["bga.representation"] = "discrete";
            Assert(tests.Generate(document).Metadata.SolderBallCount == 40, "discrete border did not use the same counts");
        });

        tests.Case("layout", "BGA bounds follow equivalent regions, retained cells and Ball Map edges", () =>
        {
            var document = tests.Create(tests.Catalog.Load("cbga_fc"));
            var values = document.Values;
            values["bga.columns"] = 9;
            CheckFit("bga.columns");
            values["bga.representation"] = "discrete";
            values["bga.solder_removal_enabled"] = true;
            var omitted = new JArray();
            values["bga.omitted_cells"] = omitted;
            for (int row = 0; row < 7; row++)
            foreach (int column in new[] { 0, 8 })
                omitted.Add(new JObject { ["row"] = row, ["column"] = column });
            tests.Generate(document);

            values["bga.center_solder_enabled"] = true;
            values["bga.center_solder_rows"] = 1;
            values["bga.center_solder_columns"] = 9;
            CheckFit("bga.center_solder_columns");

            values["bga.ball_map_enabled"] = true;
            double edge = values["substrate.length"]!.Value<double>() / 2 - Math.Sqrt(Math.PI) * values["bga.diameter"]!.Value<double>() / 4;
            var point = new JObject { ["id"] = "A1", ["x"] = -edge, ["y"] = 0 };
            values["bga.ball_map"] = new JArray(point);
            tests.Generate(document);
            point["x"] = -edge - 0.01;
            CheckFit("bga.ball_map[0].x");

            void CheckFit(string path)
            {
                var result = tests.GenerateResult(document);
                Assert(result.Model == null && result.Issues.Any(i => i.Stage == ValidationStage.Input &&
                    i.Code == "input.bga.fit" && i.ParameterPaths.Contains(path)), "missing solder ball footprint issue for " + path);
            }
        });

        tests.Case("layout", "via removal combines central and explicit cells", () =>
        {
            var template = tests.Catalog.Load("pbga_wb");
            var document = tests.Create(template);
            var values = document.Values;
            values["vias.removal_enabled"] = true;
            values["vias.removal_rows"] = 2;
            values["vias.removal_columns"] = 2;
            values["vias.omitted_cells"] = new JArray(
                new JObject { ["row"] = 0, ["column"] = 0 },
                new JObject { ["row"] = 1, ["column"] = 1 });
            var context = new BuildContext(template, values, "vias", tests.Catalog.Materials, tests.Catalog.Groups, document.MaterialAssignments);
            Assert(Vias.Omissions(context, 5, 5).SetEquals([(0, 0), (1, 1), (1, 2), (2, 1), (2, 2)]), "via removal did not use the union");
        });
    }
}
