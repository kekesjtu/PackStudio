using PackStudio.Core;
using Newtonsoft.Json.Linq;
using System.Globalization;

string root = Path.GetFullPath(args.FirstOrDefault() ?? ".");
var catalog = new PackageCatalog(Path.Combine(root, "runtime_data"));
var builder = new ModelBuilder(catalog);
int passed = 0, failed = 0;

void Test(string name, Action run)
{
    try
    {
        run();
        passed++;
    }
    catch (Exception e)
    {
        failed++;
        Console.WriteLine($"FAIL {name}: {e.Message}");
    }
}

void Assert(bool condition, string message)
{
    if (!condition)
        throw new Exception(message);
}

void Near(double a, double b, string message)
{
    if (Math.Abs(a - b) > 1e-7 * Math.Max(1, Math.Abs(b)))
        throw new Exception($"{message}: {a:G10} != {b:G10}");
}

string Geometry(string type, Vector o, Vector s) => type + ":" + string.Join(",", o.Components.Concat(s.Components).Select(v => Math.Round(v, 7).ToString("F7", CultureInfo.InvariantCulture)));
foreach (var family in PackageCatalog.Families)
{
    var t = catalog.Load(family.Id);
    Test(family.Id + " default", () =>
    {
        var model = builder.Generate(family.Id, t.Defaults(t.DefaultPreset), t.DefaultPreset);
        Assert(model.Blocks.Any(b => b.StructureType == "die"), "missing die");
        Near(model.Sources.Sum(s => s.Power), t.Defaults(t.DefaultPreset)["die.power"].Number(), "power conservation");
        FloXml.Validate(FloXml.Export(model), Path.Combine(root, "output_format/floxml/xmlSchema.xsd"));
        string fixture = Path.Combine(root, "tests/PackStudio.Tests/Fixtures", family.Id + ".json");
        if (!File.Exists(fixture))
            throw new Exception("missing reference fixture");
        var reference = JsonData.Read(fixture);
        var expected = ((JArray)reference["blocks"]!).Select(b => Geometry(b["structure_type"].Text(), new(b["origin"]!["x"].Number(), b["origin"]!["y"].Number(), b["origin"]!["z"].Number()), new(b["size"]!["x"].Number(), b["size"]!["y"].Number(), b["size"]!["z"].Number()))).Order().ToList();
        var actual = model.Blocks.Select(b => Geometry(b.StructureType, b.Origin, b.Size)).Order().ToList();
        var extra = actual.Except(expected).Take(3).ToList();
        var missing = expected.Except(actual).Take(3).ToList();
        Assert(expected.SequenceEqual(actual), $"geometry {expected.Count}/{actual.Count}; extra {string.Join("; ", extra)}; missing {string.Join("; ", missing)}");
        var refMaterials = ((JArray)reference["materials"]!).ToDictionary(m => m["id"].Text());
        foreach (var mat in model.Materials.Values)
        {
            if (!refMaterials.TryGetValue(mat.Id, out var old))
                continue;
            // The reviewed FC PBGA decision requires nonzero isotropic matrix conductivity.
            if (family.Id == "pbga_fc" && mat.Id == "fc-core-via")
                continue;
            Near(mat.Conductivity.X, old["conductivity"]!["x"].Number(), mat.Id + " kx");
            Near(mat.Conductivity.Y, old["conductivity"]!["y"].Number(), mat.Id + " ky");
            Near(mat.Conductivity.Z, old["conductivity"]!["z"].Number(), mat.Id + " kz");
            Near(mat.Density, old["density"].Number(), mat.Id + " density");
            Near(mat.SpecificHeat, old["specific_heat"].Number(), mat.Id + " cp");
        }
    });
    Test(family.Id + " power edit", () =>
    {
        var v = t.Defaults(t.DefaultPreset);
        v["die.power"] = 7.25;
        var m = builder.Generate(family.Id, v, t.DefaultPreset);
        Near(m.Sources.Sum(s => s.Power), 7.25, "edited power");
    });
    foreach (var preset in t.Presets)
    {
        Test(preset.Id, () =>
        {
            var m = builder.Generate(family.Id, t.Defaults(preset.Id), preset.Id);
            FloXml.Validate(FloXml.Export(m), Path.Combine(root, "output_format/floxml/xmlSchema.xsd"));
            Assert(m.Blocks.Count > 0, "empty model");
        });
    }
}

Test("invalid geometry", () =>
{
    var t = catalog.Load("bare_die");
    var v = t.Defaults("");
    v["die.length"] = -1;
    try
    {
        builder.Generate("bare_die", v);
        throw new Exception("invalid geometry accepted");
    }
    catch (ArgumentException)
    {
    }
});
Test("invalid material", () =>
{
    try
    {
        new Material("x", "x", new(1, 1, 1), -1, 2).Validate();
        throw new Exception("invalid material accepted");
    }
    catch (ArgumentException)
    {
    }
});
foreach (var reference in JArray.Parse(File.ReadAllText(Path.Combine(root, "tests/PackStudio.Tests/Fixtures/cases.json"))).Cast<JObject>())
{
    Test("branch " + reference["id"].Text(), () =>
    {
        var d = RequestDocument.Parse((JObject)reference["request"]!, catalog);
        var m = builder.Generate(d.TemplateId, d.Values, d.PresetId, d.Name, d.Bga, d.Assignments, d.CustomMaterials);
        string Shape(JToken b) => Geometry(b["type"].Text(), new(b["origin"]![0].Number(), b["origin"]![1].Number(), b["origin"]![2].Number()), new(b["size"]![0].Number(), b["size"]![1].Number(), b["size"]![2].Number()));
        var expected = ((JArray)reference["blocks"]!).Select(Shape).Order().ToList();
        var actual = m.Blocks.Select(b => Geometry(b.StructureType, b.Origin, b.Size)).Order().ToList();
        Assert(expected.SequenceEqual(actual), $"geometry {expected.Count}/{actual.Count}; extra {string.Join(";", actual.Except(expected).Take(2))}; missing {string.Join(";", expected.Except(actual).Take(2))}");
        foreach (var mat in m.Materials.Values)
        {
            if (reference["materials"]?[mat.Id] is not JArray properties)
                continue;
            if (d.TemplateId == "pbga_fc" && mat.Id == "fc-core-via")
                continue;
            var values = mat.Conductivity.Components.Concat(new[] { mat.Density, mat.SpecificHeat }).ToList();
            for (int i = 0; i < 5; i++)
                Near(values[i], properties[i].Number(), mat.Id + " property " + i);
        }

        Near(m.Sources.Sum(s => s.Power), reference["power"].Number(), "power");
        Assert(m.Auxiliary.Count == ((JArray)reference["auxiliary"]!).Count, "auxiliary count");
        foreach (var aux in m.Auxiliary)
        {
            var old = ((JArray)reference["auxiliary"]!).Single(x => x["name"].Text() == aux.Name);
            Near(aux.Origin.X, old["origin"]!["x"].Number(), aux.Name + " x");
            Near(aux.Origin.Y, old["origin"]!["y"].Number(), aux.Name + " y");
            Near(aux.Origin.Z, old["origin"]!["z"].Number(), aux.Name + " z");
        }

        FloXml.Validate(FloXml.Export(m), Path.Combine(root, "output_format/floxml/xmlSchema.xsd"));
    });
}

Test("explicit derived material override", () =>
{
    var t = catalog.Load("bare_die");
    var v = t.Defaults("");
    v["bumps.enabled"] = true;
    var model = builder.Generate("bare_die", v);
    var original = model.Materials["flip-chip-bumps-equivalent"];
    var edited = original with
    {
        Conductivity = new(42, 43, 44)
    };
    var changed = builder.Generate("bare_die", v, custom: [edited]);
    Near(changed.Materials[edited.Id].Conductivity.X, 42, "derived override");
});
Test("project persistence", () =>
{
    string dir = Path.Combine(root, "tmp/2026-10-28-pta-rewrite/project-roundtrip");
    Directory.CreateDirectory(dir);
    string path = Path.Combine(dir, "roundtrip.packstudio.json");
    try
    {
        var d = new ProjectDocument
        {
            TemplateId = "bare_die",
            Name = "中文方案",
            Values = catalog.Load("bare_die").Defaults("")
        };
        d.Save(path);
        var loaded = ProjectDocument.Load(path);
        Assert(loaded.Name == d.Name && JToken.DeepEquals(loaded.Values, d.Values), "project roundtrip");
    }
    finally
    {
        if (File.Exists(path))
            File.Delete(path);
    }
});
Test("correct FC PBGA isotropic via matrix", () =>
{
    var t = catalog.Load("pbga_fc");
    var v = t.Defaults(t.DefaultPreset);
    v["vias.enabled"] = true;
    v["vias.modeling"] = "equivalent";
    v["vias.rows"] = 4;
    v["vias.columns"] = 3;
    v["vias.pitch"] = 0.5;
    v["vias.diameter"] = 0.2;
    v["vias.plating"] = 0.025;
    var m = builder.Generate("pbga_fc", v, t.DefaultPreset);
    var core = m.Materials["fc-core-via"];
    Assert(core.Conductivity.X > 0 && core.Conductivity.Y > 0, "isotropic matrix conductivity must be retained");
});
Test("unknown preset rejected", () =>
{
    try
    {
        catalog.Load("qfn").Defaults("missing-preset");
        throw new Exception("unknown preset accepted");
    }
    catch (ArgumentException)
    {
    }
});
Test("embedded heat slug availability", () =>
{
    foreach (var family in new[] { "cbga_fc", "pbga_fc" })
    {
        var field = catalog.Load(family).Fields.Single(f => f["key"].Text() == "slug.enabled");
        Assert(!((JObject)field["visible_when"]!).HasValues, family + " hides the slug checkbox instead of disabling it");
        Assert(field["enabled_when"]?["cover.type"].Text() == "encapsulant", family + " slug checkbox is not gated by the top cover");
        Assert(field["help_text"].Text().Length > 0, family + " slug checkbox lacks an availability hint");
    }
});
Test("normalized preset and field correspondence contract", () => PresetContractChecks.Run(catalog, root));
Test("legacy tables normalize only at input boundaries", () => PresetContractChecks.LegacyTables(catalog));
Console.WriteLine($"{passed} passed, {failed} failed");
return failed == 0 ? 0 : 1;
