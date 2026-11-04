using System.Globalization;
using System.Text;
using System.Xml;
using System.Xml.Linq;
using System.Xml.Schema;
using Newtonsoft.Json;

namespace PackStudio.Core;
public static class FloXml
{
    static XElement E(string key, object value) => new(key, value);
    static string F(double n) => double.IsFinite(n) ? n.ToString("G17", CultureInfo.InvariantCulture) : throw new ArgumentException("FloXML 需要有限数值。");
    static XElement Number(string key, double n) => E(key, F(n));
    static XElement Vec(string key, Vector v, double scale = 1) => new(key, Number("x", v.X * scale), Number("y", v.Y * scale), Number("z", v.Z * scale));
    public static XDocument Export(PackageModel model)
    {
        model.Validate();
        var attributes = new XElement("attributes");
        Grid(attributes, model);
        var materials = new XElement("materials");
        attributes.Add(materials);
        foreach (var m in model.Materials.Values.OrderBy(m => m.Id, StringComparer.Ordinal))
        {
            bool iso = m.Conductivity.X == m.Conductivity.Y && m.Conductivity.Y == m.Conductivity.Z, temp = iso && m.ConductivityCoefficient.HasValue;
            var item = new XElement(temp ? "temperature_dependant_material_att" : iso ? "isotropic_material_att" : "orthotropic_material_att", E("name", m.Id), Number("density", m.Density), Number("specific_heat", m.SpecificHeat));
            if (iso)
            {
                item.Add(Number("conductivity", m.Conductivity.X));
                if (temp)
                {
                    item.Add(Number("coeff", m.ConductivityCoefficient!.Value));
                    item.Add(Number("tref", (m.ReferenceTemperature ?? 0) + 273.15));
                }
            }
            else
            {
                item.Add(Number("x_conductivity", m.Conductivity.X), Number("y_conductivity", m.Conductivity.Y), Number("z_conductivity", m.Conductivity.Z));
            }

            item.Add(E("notes", m.Name));
            materials.Add(item);
        }

        var sources = new XElement("sources");
        attributes.Add(sources);
        foreach (var s in model.Sources)
            sources.Add(new XElement("source_att", E("name", "power-" + s.BlockId), E("type", "total"), Number("power", s.Power)));
        bool surface = model.TemplateId is "chip_array" or "cbga_fc" or "pbga_fc";
        if (surface)
        {
            attributes.Add(new XElement("surfaces", new XElement("surface_att", E("name", model.Name), Number("emissivity", 0.8))));
            attributes.Add(new XElement("radiations", new XElement("radiation_att", E("name", model.TemplateId), E("surface", "subdivided_radiating"), Number("subdivided_surface_tolerance", model.Geometry.Grid.Length * 0.0001))));
        }

        var root = new XElement("xml_case", E("name", model.Name), attributes);
        var geometry = new XElement("geometry");
        root.Add(geometry);
        var package = new XElement("assembly", E("name", "package"), Vec("position", new(0, 0, 0)));
        var contents = new XElement("geometry");
        package.Add(contents);
        geometry.Add(package);
        foreach (var group in model.Blocks.GroupBy(b => b.GroupId))
        {
            var assembly = new XElement("assembly", E("name", group.Key), Vec("position", new(0, 0, 0)));
            var members = new XElement("geometry");
            assembly.Add(members);
            foreach (var b in group)
            {
                var item = new XElement("cuboid", E("name", b.Id), Vec("size", b.Size, 0.001), Vec("position", b.Origin, 0.001), E("material", b.MaterialId));
                if (surface && (b.Id.StartsWith("encapsulant-", StringComparison.Ordinal) || b.Id is "substrate-part-1" or "lid-part-1" or "thermal-plate-part-1"))
                    item.Add(E("all_surface", model.Name), E("all_radiation", model.TemplateId));
                item.Add(E("notes", JsonConvert.SerializeObject(new { name = b.Name, structure_type = b.StructureType })));
                members.Add(item);
                foreach (var s in model.Sources.Where(s => s.BlockId == b.Id))
                    members.Add(new XElement("source", E("name", "heat-" + b.Id), Vec("size", b.Size, 0.001), Vec("position", b.Origin, 0.001), E("source", "power-" + b.Id)));
            }

            assembly.Add(E("notes", group.First().GroupName));
            contents.Add(assembly);
        }

        package.Add(E("notes", model.Name));
        foreach (var auxiliary in model.Auxiliary)
        {
            var element = new XElement(auxiliary.Kind, E("name", auxiliary.Name));
            if (auxiliary.Size != null)
                element.Add(Vec("size", auxiliary.Size, 0.001));
            element.Add(Vec("position", auxiliary.Origin, 0.001));
            if (auxiliary.Kind == "region")
                element.Add(new XElement("collapse", E("direction", "z_direction"), E("type", "low_face")));
            geometry.Add(element);
        }

        foreach (string axis in new[]
        {
            "x",
            "y",
            "z"
        }

        )
            root.Add(E(axis + "_grid_constraint", axis == "z" ? "keypoint_z" : "keypoint"));
        root.Add(E("localized_grid", model.Metadata.GridEnabled.ToString().ToLowerInvariant()));
        root.Add(E("notes", JsonConvert.SerializeObject(new { exporter = "PackStudio", profile = "FloXML / FloTHERM 2504", units = "m, W, kg/m3, J/(kg*K), W/(m*K)", metadata = model.Metadata, warnings = model.Warnings })));
        return new(new XDeclaration("1.0", "utf-8", null), root);
    }

    static void Grid(XElement attributes, PackageModel model)
    {
        double l = Math.Min(model.Geometry.Grid.Length, model.Geometry.Grid.Width) * 0.001, h = model.Geometry.Height * 0.001;
        string density = model.Metadata.GridDensity;
        bool coarse = density == "coarse", fine = density == "fine";
        var constraints = new XElement("grid_constraints");
        attributes.Add(constraints);
        foreach (var(name, spacing)in new[]
        {
            ("keypoint", l / (fine ? 20 : 10)),
            ("keypoint_z", h / (fine ? 10 : 6))
        }

        )
        {
            void Control(XElement e)
            {
                e.Add(E("number_cells_control", coarse ? "min_number" : "max_size"), Number(coarse ? "min_number" : "max_size", coarse ? 1 : spacing));
            }

            var c = new XElement("grid_constraint_att", E("name", name), E("enable_min_cell_size", "true"), Number("min_cell_size", 0.000002));
            Control(c);
            foreach (var(side, size)in new[]
            {
                ("low", 0.0016),
                ("high", h * 2)
            }

            )
            {
                var e = new XElement(side + "_inflation", E("inflation_type", name == "keypoint" ? "percent" : "size"), Number(name == "keypoint" ? "inflation_percent" : "inflation_size", name == "keypoint" ? 25 : size));
                Control(e);
                c.Add(e);
            }

            constraints.Add(c);
        }
    }

    public static void Save(PackageModel model, string path, string? schemaPath = null)
    {
        var doc = Export(model);
        if (schemaPath != null)
            Validate(doc, schemaPath);
        string absolute = Path.GetFullPath(path), temp = absolute + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            using (var writer = XmlWriter.Create(temp, new XmlWriterSettings { Indent = true, Encoding = new UTF8Encoding(false) }))
                doc.Save(writer);
            File.Move(temp, absolute, true);
        }
        finally
        {
            if (File.Exists(temp))
                File.Delete(temp);
        }
    }

    public static void Validate(XDocument doc, string schemaPath)
    {
        var schemas = new XmlSchemaSet
        {
            XmlResolver = new XmlUrlResolver()
        };
        schemas.Add(null, schemaPath);
        doc.Validate(schemas, (_, e) => throw new InvalidDataException(e.Message));
    }
}
