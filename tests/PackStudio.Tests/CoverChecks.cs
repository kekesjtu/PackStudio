using PackStudio.Core;
using static TestSuite;

static class CoverChecks
{
    public static void Run(TestSuite tests)
    {
        foreach (string family in new[] { "pbga_fc", "cbga_fc" })
        {
            var definition = tests.Catalog.Load(family);
            tests.Case("cover", family + " plate rests on the chip attach", () =>
            {
                var document = tests.Create(definition);
                document.Values["cover.type"] = "plate";
                document.Values["plate.die_attach"] = 0.12;
                CheckCap(Generate(tests, document), "thermal-plate", "plate-die-attach", 0.12);
            });

            tests.Case("cover", family + " default small lids clear the die and rest on the adhesive", () =>
            {
                string prefix = family.Replace("_", "").ToUpperInvariant();
                foreach (string footprint in new[] { "49_6X6mm", "64_7X7mm" })
                {
                    var document = tests.Create(definition, prefix + "_" + footprint);
                    document.Values["cover.type"] = "lid";
                    var model = Generate(tests, document);
                    CheckCap(model, "lid", "lid-die-attach", 0.05);
                    foreach (string side in new[] { "left", "right", "lower", "upper" })
                    {
                        var adhesive = Part(model, "lid-adhesive-" + side);
                        var wall = Part(model, "lid-wall-" + side);
                        Near(adhesive.Origin.Z, Part(model, "substrate").Maximum.Z, "adhesive rests on substrate");
                        Near(wall.Origin.Z, adhesive.Maximum.Z, "wall rests on adhesive");
                        Near(wall.Maximum.Z, Part(model, "lid").Origin.Z, "wall meets lid");
                    }
                }
            });

            tests.Case("cover", family + " stiffener sits between the two adhesive layers", () =>
            {
                var document = tests.Create(definition);
                document.Values["cover.type"] = "lid";
                EnableStiffener(document);
                var model = Generate(tests, document);
                CheckCap(model, "lid", "lid-die-attach", 0.05);
                foreach (string side in new[] { "left", "right", "lower", "upper" })
                {
                    var bottomAdhesive = Part(model, "stiffener-adhesive-" + side);
                    var stiffener = Part(model, "stiffener-" + side);
                    var topAdhesive = Part(model, "lid-adhesive-" + side);
                    Near(bottomAdhesive.Origin.Z, Part(model, "substrate").Maximum.Z, "adhesive rests on substrate");
                    Near(stiffener.Origin.Z, bottomAdhesive.Maximum.Z, "stiffener rests on adhesive");
                    Near(topAdhesive.Origin.Z, stiffener.Maximum.Z, "top adhesive rests on stiffener");
                    Near(topAdhesive.Maximum.Z, Part(model, "lid").Origin.Z, "top adhesive meets lid");
                }
            });

            tests.Case("cover", family + " validates lid openings and support heights", () =>
            {
                var document = tests.Create(definition);
                document.Values["cover.type"] = "lid";
                document.Values["lid.base_thickness"] = 2.5;
                Expect(tests, document, "input.lid.die", "die.length", "lid.base_thickness");

                document.Values["lid.base_thickness"] = 2.1;
                Generate(tests, document);
                document.Values["lid.adhesive"] = 0.8;
                Expect(tests, document, "input.lid.height", "lid.adhesive", "bumps.height", "die.thickness", "lid.die_attach");

                EnableStiffener(document);
                document.Values["lid.adhesive"] = 0.7;
                Expect(tests, document, "input.lid.height", "lid.adhesive", "stiffener.adhesive");
                document.Values["lid.adhesive"] = 0.2;
                document.Values["stiffener.cavity_width"] = 1.5;
                Expect(tests, document, "input.lid.die", "die.width", "stiffener.cavity_width");
            });
        }
    }

    static void EnableStiffener(ProjectDocument document)
    {
        document.Values["stiffener.enabled"] = true;
        document.Values["stiffener.length"] = document.Values["stiffener.width"] = 6;
        document.Values["stiffener.cavity_length"] = document.Values["stiffener.cavity_width"] = 3;
        document.Values["stiffener.adhesive"] = 0.1;
    }

    static PackageModel Generate(TestSuite tests, ProjectDocument document)
    {
        var result = tests.GenerateResult(document);
        Assert(result.CanExport && result.Issues.All(i => i.Code != "model.overlap"),
            string.Join(" ", result.Issues.Select(i => i.Message + " " + string.Join("/", i.EntityIds))));
        return result.Model!;
    }

    static void Expect(TestSuite tests, ProjectDocument document, string code, params string[] paths)
    {
        var result = tests.GenerateResult(document);
        Assert(result.Model == null && result.Issues.Any(i => i.Code == code && paths.All(i.ParameterPaths.Contains)),
            $"{code} did not block generation and identify the linked fields");
    }

    static Block Part(PackageModel model, string name) => model.Blocks.Single(b => b.Id == name + "-part-1");

    static void CheckCap(PackageModel model, string capId, string attachId, double thickness)
    {
        var attach = Part(model, attachId);
        Near(attach.Size.Z, thickness, "chip attach thickness");
        Near(attach.Origin.Z, Part(model, "die").Maximum.Z, "chip attach rests on die");
        Near(Part(model, capId).Origin.Z, attach.Maximum.Z, "cap rests on chip attach");
    }
}
