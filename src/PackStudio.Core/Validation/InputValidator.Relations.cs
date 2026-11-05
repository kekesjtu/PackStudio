using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static partial class InputValidator
{
    static IReadOnlyList<ValidationIssue> ValidatePackageRelations(ProjectDocument document, ValidationRules rules, IReadOnlyList<ValidationIssue> precedingIssues)
    {
        var values = document.Values;
        var issues = new List<ValidationIssue>();
        bool Invalid(string key) => precedingIssues.Any(i => i.Severity == IssueSeverity.Error &&
            i.ParameterPaths.Any(p => p == key || p.StartsWith(key + "[") || p.StartsWith(key + ".") || key.StartsWith(p + ".")));
        double Number(JToken? value) => value?.Type is JTokenType.Float or JTokenType.Integer && double.IsFinite(value.Value<double>()) ? value.Value<double>() : double.NaN;
        double N(string key) => Invalid(key) ? double.NaN : Number(values[key]);
        bool B(string key) => !Invalid(key) && values[key].Flag();
        string T(string key) => Invalid(key) ? "" : values[key].Text();
        void Check(bool failed, string code, params string[] paths)
        {
            if (failed && !paths.Any(Invalid) && rules.Contains(code))
                issues.Add(rules.Create(code, ValidationStage.Input, paths));
        }
        void Fits(string inner, string outer) => Check(N(inner) > N(outer), "input.package.fit", inner, outer);
        void Ring(string outerX, string outerY, string innerX, string innerY) =>
            Check(N(innerX) >= N(outerX) || N(innerY) >= N(outerY), "input.cavity", outerX, outerY, innerX, innerY);

        bool bga = document.TemplateId is "cbga_fc" or "pbga_fc" or "pbga_wb" or "chip_array";
        if (bga)
        {
            double rows = N("bga.rows"), columns = N("bga.columns");
            if (B("bga.ball_map_enabled") && !Invalid("bga.ball_map") && values["bga.ball_map"] is JArray map)
            {
                var ids = new HashSet<string>();
                for (int i = 0; i < map.Count; i++)
                {
                    string path = $"bga.ball_map[{i}]";
                    if (map[i] is not JObject point)
                    { Check(true, "input.bga.map", path); continue; }
                    Check(!ids.Add(point["id"].Text()), "input.bga.map.id", path + ".id");
                    foreach (string axis in new[] { "x", "y" })
                        Check(!double.IsFinite(Number(point[axis])), "input.bga.map.coordinate", path + "." + axis);
                }
            }
            if (!B("bga.ball_map_enabled"))
            {
                Cells("bga.omitted_cells", values["bga.omitted_cells"] as JArray, rows, columns);
                if (B("bga.solder_removal_enabled") && values["bga.omitted_cells"] is not JArray { Count: > 0 })
                {
                    foreach (string dimension in new[] { "rows", "columns" })
                        if (!double.IsFinite(N("bga.populated_" + dimension)) && !Invalid("bga.populated_" + dimension))
                            Check(!double.IsFinite(N("bga.removal_" + dimension)), "input.bga.removal.required", "bga.removal_" + dimension);
                    double populatedRows = double.IsFinite(N("bga.populated_rows")) ? N("bga.populated_rows") : rows - N("bga.removal_rows");
                    double populatedColumns = double.IsFinite(N("bga.populated_columns")) ? N("bga.populated_columns") : columns - N("bga.removal_columns");
                    Check(populatedRows < 0 || populatedRows > rows || populatedColumns < 0 || populatedColumns > columns,
                        "input.bga.removal", "bga.rows", "bga.columns", "bga.populated_rows", "bga.populated_columns", "bga.removal_rows", "bga.removal_columns");
                }
            }
            if (!B("bga.ball_map_enabled") && B("bga.center_solder_enabled"))
                foreach (string dimension in new[] { "rows", "columns" })
                    Check(N("bga.center_solder_" + dimension) < 1, "input.bga.center", "bga.center_solder_" + dimension);
            Check(document.TemplateId == "chip_array" && T("bga.representation") != "discrete" ||
                document.TemplateId != "pbga_wb" && T("bga.representation") == "isotropic",
                "input.bga.representation", "bga.representation");
        }

        if (B("vias.enabled") && values["vias.configuration"] is JObject config && config["removal_enabled"].Flag())
        {
            double rows = N("vias.rows"), columns = N("vias.columns");
            double removedRows = Number(config["removal_rows"]), removedColumns = Number(config["removal_columns"]);
            foreach (string dimension in new[] { "rows", "columns" })
                Check(!double.IsFinite(Number(config["removal_" + dimension])), "input.via.removal.required", "vias.configuration.removal_" + dimension);
            Check(removedRows < 0 || removedRows > rows || removedColumns < 0 || removedColumns > columns ||
                double.IsFinite(removedRows) && double.IsFinite(removedColumns) && (removedRows == 0) != (removedColumns == 0),
                "input.via.removal", "vias.configuration.removal_rows", "vias.configuration.removal_columns", "vias.rows", "vias.columns");
            Cells("vias.configuration.omitted_cells", config["omitted_cells"] as JArray, rows, columns);
        }

        if (document.TemplateId == "bare_die" && B("bumps.enabled") || document.TemplateId is "cbga_fc" or "pbga_fc")
        {
            double count = T("bumps.array_type") == "regular" ? N("bumps.columns") * N("bumps.rows") : N("bumps.total");
            double fraction = count * Math.PI * Math.Pow(N("bumps.diameter"), 2) / (4 * N("die.length") * N("die.width"));
            Check(fraction > 1, "input.bumps.fraction", "bumps.diameter", "bumps.total", "bumps.columns", "bumps.rows", "die.length", "die.width");
        }

        switch (document.TemplateId)
        {
            case "cbga_fc":
            case "pbga_fc":
                Fits("die.length", "substrate.length"); Fits("die.width", "substrate.width");
                if (T("cover.type") == "lid")
                {
                    if (B("stiffener.enabled")) Ring("stiffener.length", "stiffener.width", "stiffener.cavity_length", "stiffener.cavity_width");
                    else Check(2 * N("lid.base_thickness") >= N("lid.length") || 2 * N("lid.base_thickness") >= N("lid.width"),
                        "input.lid.wall", "lid.base_thickness", "lid.length", "lid.width");
                }
                if (document.TemplateId == "pbga_fc")
                    Check((B("upper.enabled") ? N("upper.thickness") : 0) + (B("lower.enabled") ? N("lower.thickness") : 0) >= N("substrate.thickness") && B("vias.enabled"),
                        "input.substrate.core", "upper.thickness", "lower.thickness", "substrate.thickness");
                break;
            case "chip_array":
            case "pbga_wb":
                bool chip = document.TemplateId == "chip_array";
                string outer = chip ? "package" : "encapsulant";
                Fits("die.length", outer + ".length"); Fits("die.width", outer + ".width");
                if (!chip)
                {
                    Fits("encapsulant.length", "package.length"); Fits("encapsulant.width", "package.width");
                    Fits("flag.length", "encapsulant.length"); Fits("flag.width", "encapsulant.width");
                    if (B("spreader.enabled"))
                    {
                        Fits("spreader.length", "package.length"); Fits("spreader.width", "package.width"); Fits("spreader.thickness", "substrate.thickness");
                        Ring("package.length", "package.width", "spreader.hole_length", "spreader.hole_width");
                    }
                }
                if (!Invalid("metal.layers") && values["metal.layers"] is JArray metal)
                {
                    if (metal.Count >= 2)
                        Check(Number(metal[0]["thickness"]) + Number(metal[metal.Count - 1]["thickness"]) >= N("substrate.thickness"),
                            "input.layer.surfaces", "metal.layers[0].thickness", $"metal.layers[{metal.Count - 1}].thickness", "substrate.thickness");
                }
                if (!chip || B("bond_wire.include"))
                    foreach (var (dimension, extent) in new[] { ("length", "extent_length"), ("width", "extent_width") })
                        Check(N("bond_wire." + extent) - (chip ? 2 * N("bond_wire.diameter") : 0) <= N("die." + dimension),
                            "input.wire.endpoint", "bond_wire." + extent, "bond_wire.diameter", "die." + dimension);
                break;
            case "sop":
            case "pqfp":
                bool sop = document.TemplateId == "sop";
                Fits("body.width", "package.width");
                Fits("body.length", "package.length");
                foreach (string dimension in new[] { "length", "width" })
                { Fits("flag." + dimension, "body." + dimension); Fits("die." + dimension, "body." + dimension); }
                double flagHeight = N(sop ? "flag.thickness" : "leads.thickness");
                Check(N("leads.height") - N("flag.downset") + flagHeight + N("die.attach") + N("die.thickness") > N("body.thickness"),
                    "input.leadframe.stack", "leads.height", "flag.downset", sop ? "flag.thickness" : "leads.thickness", "die.attach", "die.thickness", "body.thickness");
                if (!sop) Check(N("leads.foot_length") <= N("leads.thickness"), "input.pqfp.foot", "leads.foot_length", "leads.thickness");
                if (B("thermal_land.enabled")) Check(N("package.standoff") <= 0, "input.thermal_land", "package.standoff");
                foreach (var (dimension, axis) in new[] { ("length", "x"), ("width", "y") })
                    Check(N("flag." + dimension) + 2 * N(sop ? "leads.gap" : "leads.gap_" + axis) <= N("die." + dimension),
                        "input.wire.endpoint", "flag." + dimension, sop ? "leads.gap" : "leads.gap_" + axis, "die." + dimension);
                break;
            case "qfn":
                Fits("die.length", "package.length"); Fits("die.width", "package.width"); Fits("pad.length", "package.length"); Fits("pad.width", "package.width");
                Check(N("leads.exposed_thickness") >= N("leads.thickness"), "input.qfn.lead_height", "leads.exposed_thickness", "leads.thickness");
                Check(N("leads.count_x") + (double.IsFinite(N("leads.count_y")) ? N("leads.count_y") : 0) == 0, "input.qfn.lead_count", "leads.count_x", "leads.count_y");
                foreach (var (axis, dimension) in new[] { ("x", "length"), ("y", "width") })
                {
                    if (axis == "y" && !(N("leads.count_y") > 0)) continue;
                    Check((N("leads.count_" + axis) - 1) * N("leads.pitch_" + axis) + N("leads.width") > N("package." + dimension),
                        "input.qfn.lead_span", "leads.count_" + axis, "leads.pitch_" + axis, "leads.width", "package." + dimension);
                    string radial = axis == "x" ? "width" : "length";
                    Check(N("package." + radial) - 2 * N("leads.length") - 2 * N("leads.etch") <= N("die." + radial),
                        "input.qfn.wire_endpoint", "package." + radial, "leads.length", "leads.etch", "die." + radial);
                }
                if (B("vias.enabled"))
                    foreach (var (dimension, count) in new[] { ("length", "columns"), ("width", "rows") })
                        Check((N("vias." + count) - 1) * N("vias.pitch") + N("vias.diameter") > N("pad.exposed_" + dimension),
                            "input.qfn.via_span", "vias." + count, "vias.pitch", "vias.diameter", "pad.exposed_" + dimension);
                break;
        }
        return issues.AsReadOnly();

        void Cells(string path, JArray? cells, double rows, double columns)
        {
            if (cells == null || Invalid(path) || !double.IsFinite(rows) || !double.IsFinite(columns)) return;
            for (int i = 0; i < cells.Count; i++)
            {
                if (cells[i] is not JObject cell)
                { Check(true, "input.array.cell", $"{path}[{i}]"); continue; }
                double row = Number(cell["row"]), column = Number(cell["column"]);
                Check(!double.IsFinite(row) || !double.IsFinite(column) || row != Math.Truncate(row) || column != Math.Truncate(column) || row < 0 || row >= rows || column < 0 || column >= columns,
                    "input.array.bounds", $"{path}[{i}].row", $"{path}[{i}].column");
            }
        }
    }
}
