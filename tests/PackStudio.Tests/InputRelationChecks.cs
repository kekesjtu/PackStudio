using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static TestSuite;

static class InputRelationChecks
{
    public static void Run(TestSuite tests)
    {
        ProjectDocument Create(string family) => tests.Create(tests.Catalog.Load(family));
        void Check(ProjectDocument doc, string code, bool expected, params string[] paths)
        {
            var issues = InputValidator.Validate(doc, tests.Catalog.Load(doc.TemplateId), tests.Catalog.Materials);
            Assert(issues.Any(i => i.Code == code && paths.All(i.ParameterPaths.Contains)) == expected,
                $"{doc.TemplateId}: expected {code} ({string.Join(", ", paths)}) = {expected}. {string.Join(" | ", issues.Select(i => i.Message))}");
        }

        tests.Case("relations", "QFN one-sided axes, pitch and die stack", () =>
        {
            var doc = Create("qfn");
            var v = doc.Values;
            v["package.length"] = 12;
            v["package.width"] = 8;
            v["pad.width"] = v["pad.exposed_width"] = 7;
            v["leads.length"] = 1;
            v["leads.etch"] = 0;
            v["die.width"] = 6;
            v["die.length"] = 3;
            v["leads.count_x"] = 2;
            v["leads.count_y"] = 0;
            Check(doc, "input.qfn.wire_endpoint", true, "die.width");
            v["leads.count_x"] = 0;
            v["leads.count_y"] = 2;
            v["leads.pitch_y"] = 0.4;
            Check(doc, "input.qfn.wire_endpoint", false);
            var wires = tests.Generate(doc).Blocks.Where(b => b.StructureType == "bond_wire").ToArray();
            Assert(wires.Length > 0 && wires.All(b => b.Id.StartsWith("qfn-bondwire-x-")), "left and right leads must bond along X");
            v["die.length"] = 10;
            Check(doc, "input.qfn.wire_endpoint", true, "die.length");
            v["leads.width"] = 0.45;
            Check(doc, "input.qfn.pitch", true, "leads.pitch_y");
            v["leads.count_y"] = 1;
            Check(doc, "input.qfn.pitch", false);
            double stack = v["leads.thickness"].Number() + v["die.attach"].Number() + v["die.thickness"].Number();
            v["encapsulant.thickness"] = stack;
            Check(doc, "input.encapsulant.stack", false);
            v["encapsulant.thickness"] = stack - 0.01;
            Check(doc, "input.encapsulant.stack", true, "leads.thickness");
        });

        foreach (string family in new[] { "cbga_fc", "pbga_fc" })
            tests.Case("relations", family + " encapsulant footprint and flush height", () =>
            {
                var doc = Create(family);
                var v = doc.Values;
                v["cover.type"] = "encapsulant";
                v["cover.flush"] = false;
                v["cover.thickness"] = 0.1;
                v["cover.width"] = v["die.width"].Number() - 0.1;
                Check(doc, "input.package.fit", true, "cover.width");
                Check(doc, "input.encapsulant.stack", true, "bumps.height");
                v["cover.width"] = v["die.width"];
                v["cover.flush"] = true;
                var mold = tests.Generate(doc).Blocks.Single(b => b.StructureType == "encapsulant");
                Near(mold.Size.Z, v["bumps.height"].Number() + v["die.thickness"].Number(), "flush height");
            });

        foreach (string family in new[] { "pqfp", "sop" })
            tests.Case("relations", family + " outer lead dimensions", () =>
            {
                var doc = Create(family);
                var v = doc.Values;
                foreach (string dim in family == "pqfp" ? new[] { "length", "width" } : new[] { "width" })
                {
                    string key = "package." + dim;
                    double limit = v["body." + dim].Number() + 2 * (v["leads.foot_length"].Number() - v["leads.thickness"].Number());
                    v[key] = limit;
                    Check(doc, "input.leadframe.outer", true, key);
                    v[key] = limit + 0.02;
                    Check(doc, "input.leadframe.outer", false, key);
                }
                if (family == "sop")
                {
                    v["package.standoff"] = 0;
                    v["leads.height"] = v["leads.thickness"];
                    Check(doc, "input.sop.bend", true, "leads.height");
                    v["leads.height"] = v["leads.thickness"].Number() + 0.01;
                    Check(doc, "input.sop.bend", false);
                }
            });

        tests.Case("relations", "build-ups share the core with active through vias", () =>
        {
            var doc = Create("pbga_fc");
            var v = doc.Values;
            v["substrate.thickness"] = 1;
            v["upper.enabled"] = v["lower.enabled"] = true;
            v["upper.thickness"] = v["lower.thickness"] = 0.5;
            Check(doc, "input.substrate.core", false);
            v["vias.enabled"] = true;
            Check(doc, "input.substrate.core", true);
            v["vias.enabled"] = false;
            v["lower.thickness"] = 0.6;
            Check(doc, "input.substrate.core", true);
            v["upper.enabled"] = false;
            Check(doc, "input.substrate.core", false);
        });

        tests.Case("relations", "unsorted same-table and cross-table metal intervals", () =>
        {
            var doc = Create("pbga_fc");
            var v = doc.Values;
            v["metal.layers"] = new JArray(Layer(0.30, 0.05), Layer(0.10, 0.05));
            v["upper.enabled"] = true;
            v["upper.thickness"] = 0.4;
            var upper = Layer(0.15, 0.1);
            v["upper.layers"] = new JArray(upper);
            tests.Generate(doc);
            upper["depth"] = 0.12;
            Check(doc, "input.metal.overlap", true, "metal.layers[1].depth", "upper.layers[0].thickness");
            v["upper.enabled"] = false;
            Check(doc, "input.metal.overlap", false);
            v["metal.layers"]![0]!["depth"] = 0.11;
            Check(doc, "input.metal.overlap", true, "metal.layers[0].depth", "metal.layers[1].depth");
        });

        foreach (string family in new[] { "pbga_wb", "chip_array" })
            tests.Case("relations", family + " bottom metal follows substrate thickness", () =>
            {
                var doc = Create(family);
                var v = doc.Values;
                v["metal.layers"] = new JArray(Layer(0, 0.02), Layer(0.30, 0.05), Layer(0.7, 0.05));
                v["substrate.thickness"] = 0.40;
                Check(doc, "input.metal.overlap", false);
                v["substrate.thickness"] = 0.38;
                Check(doc, "input.metal.overlap", true, "metal.layers[1].depth", "metal.layers[2].thickness");
            });

        foreach (string family in new[] { "pbga_fc", "pbga_wb" })
            tests.Case("relations", family + " retained discrete via edges and equivalent footprint", () =>
            {
                var doc = Create(family);
                var v = doc.Values;
                string board = family == "pbga_fc" ? "substrate.length" : "package.length";
                v[board] = 6;
                v["vias.enabled"] = true;
                v["vias.columns"] = 7;
                v["vias.rows"] = 1;
                v["vias.pitch"] = 1;
                v["vias.diameter"] = 0.2;
                v["vias.plating"] = 0.02;
                v["vias.modeling"] = family == "pbga_fc" ? "discrete" : "discreteCuboids";
                Check(doc, "input.via.fit", true, board);
                v["vias.removal_enabled"] = true;
                var cells = new JArray(Cell(0), Cell(6));
                v["vias.omitted_cells"] = cells;
                Check(doc, "input.via.fit", false);
                cells.Add(Cell(6));
                Check(doc, "input.array.duplicate", true, "vias.omitted_cells[2].row");
                cells.RemoveAt(2);
                v["vias.modeling"] = family == "pbga_fc" ? "equivalent" : "orthotropicCuboid";
                Check(doc, "input.via.fit", true, board);
            });

        tests.Case("relations", "native 4 mm chip array locates and recovers from outboard vias", () =>
        {
            var doc = tests.Create(tests.Catalog.Load("chip_array"), "ChipArray_24_4X4mm_0_8");
            tests.Generate(doc);
            doc.Values["vias.offset_x"] = doc.Values["vias.offset_y"] = 0.4;
            Check(doc, "input.via.fit", true, "vias.offset_x");
            Check(doc, "input.via.fit", true, "vias.offset_y");
            doc.Values["vias.offset_x"] = doc.Values["vias.offset_y"] = 0.3;
            tests.Generate(doc);
        });

        tests.Case("relations", "chip array via offsets, paired openings and duplicate ball removals", () =>
        {
            var doc = Create("chip_array");
            var v = doc.Values;
            v["vias.enabled"] = true;
            v["vias.modeling"] = "accurate";
            v["bga.ball_map_enabled"] = true;
            v["bga.ball_map"] = new JArray(new JObject { ["id"] = "A1", ["x"] = v["package.length"].Number() / 2 - 0.3, ["y"] = 0 });
            v["vias.offset_x"] = 0.3;
            v["vias.offset_y"] = 0;
            Check(doc, "input.via.fit", true, "vias.offset_x");
            v["vias.modeling"] = "approximate";
            Check(doc, "input.via.fit", false);
            v["metal.hole_length"] = 1;
            Check(doc, "input.metal.hole_pair", true);
            v["metal.hole_width"] = 0;
            Check(doc, "input.metal.hole_size", true, "metal.hole_width");
            v["metal.hole_width"] = v["package.width"].Number() + 1;
            Check(doc, "input.package.fit", true, "metal.hole_width");
            v["metal.hole_width"] = 1;
            Assert(tests.Generate(doc).Blocks.Any(b => b.Id.StartsWith("trace-hole-")), "valid opening missing");
            v["bga.ball_map_enabled"] = false;
            v["bga.explicit_removal_enabled"] = true;
            v["bga.omitted_cells"] = new JArray(Cell(0), Cell(0));
            Check(doc, "input.array.duplicate", true, "bga.omitted_cells[1].column");
        });
    }

    static JObject Layer(double depth, double thickness) => new() { ["depth"] = depth, ["thickness"] = thickness, ["coverage"] = 50, ["disconnect"] = false };
    static JObject Cell(int column) => new() { ["row"] = 0, ["column"] = column };
}
