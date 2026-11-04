using PackStudio.Core;
using static TestSuite;

static class SlugChecks
{
    public static void Run(TestSuite tests)
    {
        foreach (string family in new[] { "cbga_fc", "pbga_fc" })
        {
            foreach (bool flush in new[] { false, true })
            foreach (bool adhesive in new[] { false, true })
                tests.Case("slug", $"{family} contact flush={flush} adhesive={adhesive}", () =>
                {
                    var document = Create(tests, family);
                    document.Values["cover.flush"] = flush;
                    document.Values["slug.adhesive_enabled"] = adhesive;
                    foreach (double bumpHeight in new[] { 0.07, 0.2 })
                    {
                        document.Values["bumps.height"] = bumpHeight;
                        var model = tests.Generate(document);
                        var substrate = Part(model, "substrate");
                        Near(substrate.Maximum.Z, 1.55, "substrate top");
                        double top = flush ? substrate.Maximum.Z + bumpHeight + 0.8 : 2.75;
                        CheckContact(model, substrate.Maximum.Z, 0.1, top, adhesive);
                        Near(Part(model, "die").Origin.Z, substrate.Maximum.Z + bumpHeight, "die follows bumps");
                    }
                });

            tests.Case("slug", family + " clearance controls adhesive thickness and foot position", () =>
            {
                var document = Create(tests, family);
                foreach (double clearance in new[] { 0.09, 0.18 })
                {
                    document.Values["slug.clearance"] = clearance;
                    CheckContact(tests.Generate(document), 1.55, clearance, 2.75, true);
                }
            });

            tests.Case("slug", family + " FloXML substrate-to-foot contact", () =>
            {
                var xml = tests.Export(tests.Generate(Create(tests, family)));
                var blocks = xml.Descendants("cuboid").ToDictionary(b => (string)b.Element("name")!);
                foreach (string side in new[] { "left", "right", "upper", "lower" })
                {
                    var glue = blocks[$"slug-adhesive-{side}-part-1"];
                    var foot = blocks[$"slug-foot-{side}-part-1"];
                    var wall = blocks[$"slug-v-{side}-part-1"];
                    double bottom = (double)glue.Element("position")!.Element("z")! * 1000;
                    double height = (double)glue.Element("size")!.Element("z")! * 1000;
                    Near(bottom, 1.55, "exported adhesive bottom");
                    Near(height, 0.1, "exported adhesive thickness");
                    Near((double)foot.Element("position")!.Element("z")! * 1000, bottom + height, "exported foot contact");
                    Near((double)wall.Element("position")!.Element("z")! * 1000, bottom + height, "exported wall bottom");
                    Near((double)wall.Element("size")!.Element("z")! * 1000, 0.6, "exported wall height");
                }
            });
        }

        tests.Case("slug", "wirebond retains solder-mask offset", () =>
        {
            var document = Create(tests, "pbga_wb");
            document.Values["encapsulant.thickness"] = 1.2;
            foreach (double mask in new[] { 0.02, 0.06 })
            {
                document.Values["solder_mask.thickness"] = mask;
                var model = tests.Generate(document);
                double substrateTop = Part(model, "dielectric").Maximum.Z;
                CheckContact(model, substrateTop + mask, 0.1, substrateTop + 1.2, true);
            }
        });
    }

    static ProjectDocument Create(TestSuite tests, string family)
    {
        var document = tests.Create(tests.Catalog.Load(family));
        var values = document.Values;
        values["slug.enabled"] = values["slug.adhesive_enabled"] = true;
        values["slug.length"] = values["slug.width"] = 4;
        values["slug.foot_length"] = values["slug.foot_width"] = 4.5;
        values["slug.thickness"] = 0.4;
        values["slug.diameter"] = 2;
        values["slug.offset"] = values["slug.clearance"] = 0.1;
        if (family != "pbga_wb")
        {
            values["cover.type"] = "encapsulant";
            values["cover.flush"] = false;
            values["cover.length"] = values["cover.width"] = 4;
            values["cover.thickness"] = 1.2;
            values["substrate.thickness"] = 1.15;
            values["bga.height"] = 0.4;
            values["bumps.height"] = 0.1;
            values["die.thickness"] = 0.8;
        }
        return document;
    }

    static Block Part(PackageModel model, string name) => model.Blocks.Single(b => b.Id == name + "-part-1");

    static void CheckContact(PackageModel model, double surface, double clearance, double top, bool adhesive)
    {
        Near(Part(model, "slug-top").Maximum.Z, top, "slug top follows encapsulant");
        Near(Part(model, "slug-top").Size.Z, 0.4, "central plate thickness");
        Assert(model.Blocks.Count(b => b.GroupId == "group-slug-adhesive") == (adhesive ? 4 : 0), "adhesive switch");
        foreach (string side in new[] { "left", "right", "upper", "lower" })
        {
            var foot = Part(model, "slug-foot-" + side);
            var wall = Part(model, "slug-v-" + side);
            var horizontal = Part(model, "slug-h-" + side);
            Near(foot.Origin.Z, surface + clearance, "foot clearance");
            Near(foot.Size.Z, 0.4, "foot thickness");
            Near(wall.Origin.Z, foot.Origin.Z, "wall joins foot bottom");
            Near(wall.Maximum.Z, horizontal.Origin.Z, "wall joins horizontal plate");
            Near(horizontal.Origin.Z, top - 0.4 - 0.1, "horizontal plate offset");
            Near(horizontal.Size.Z, 0.4, "horizontal plate thickness");
            if (!adhesive) continue;
            var glue = Part(model, "slug-adhesive-" + side);
            Near(glue.Origin.Z, surface, "adhesive touches supporting surface");
            Near(glue.Maximum.Z, foot.Origin.Z, "adhesive touches foot");
            Near(glue.Size.Z, clearance, "adhesive fills clearance");
            Assert(Math.Min(glue.Maximum.X, foot.Maximum.X) > Math.Max(glue.Origin.X, foot.Origin.X)
                && Math.Min(glue.Maximum.Y, foot.Maximum.Y) > Math.Max(glue.Origin.Y, foot.Origin.Y), "adhesive overlaps foot in XY");
        }
    }
}
