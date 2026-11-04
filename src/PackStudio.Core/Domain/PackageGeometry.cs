namespace PackStudio.Core;

public sealed record Footprint(double Length, double Width);
public sealed record PackageGeometry(Footprint Outline, Footprint Grid, Footprint Bottom, Footprint Top, double Height, bool FlippedDie)
{
    public static PackageGeometry Evaluate(BuildContext c)
    {
        string id = c.Template.Info.Id;
        var die = c.Model.Blocks.First(b => b.StructureType == "die");
        Footprint Size(string prefix) => new(c.N(prefix + ".length"), c.N(prefix + ".width"));
        var outline = id switch
        {
            "bare_die" => Size("die"),
            "sop" => new(c.N("body.length"), c.N("package.width")),
            "cbga_fc" or "pbga_fc" => Size("substrate"),
            _ => Size("package")
        };
        var grid = id is "pqfp" or "sop" or "qfn" or "pbga_wb"
            ? new Footprint(Math.Max(outline.Length, outline.Width), Math.Max(outline.Length, outline.Width)) : outline;
        var bottom = c.Values["bga.rows"] != null
            ? new Footprint((c.I("bga.columns") - 1) * c.N("bga.pitch") + c.N("bga.diameter"),
                (c.I("bga.rows") - 1) * c.N("bga.pitch") + c.N("bga.diameter")) : outline;
        var top = id switch
        {
            "chip_array" or "qfn" => outline,
            "pqfp" or "sop" => Size("body"),
            "pbga_wb" => Size("encapsulant"),
            _ => c.T("cover.type") switch
            {
                "lid" => Size("lid"), "plate" => Size("plate"), "encapsulant" => Size("cover"),
                _ => new Footprint(die.Size.X, die.Size.Y)
            }
        };
        return new(outline, grid, bottom, top,
            id == "bare_die" ? c.N("die.thickness") : c.Model.Blocks.Max(b => b.Maximum.Z),
            id is "cbga_fc" or "pbga_fc" || id == "bare_die" && (c.B("die.flipped") || c.B("bumps.enabled")));
    }
}

public sealed record ModelMetadata
{
    [Newtonsoft.Json.JsonIgnore]
    public PackageGeometry Geometry { get; init; } = null!;
    [Newtonsoft.Json.JsonProperty("native_grid_length_mm")]
    public double GridLength => Geometry.Grid.Length;
    [Newtonsoft.Json.JsonProperty("native_grid_width_mm")]
    public double GridWidth => Geometry.Grid.Width;
    [Newtonsoft.Json.JsonProperty("native_grid_height_mm")]
    public double GridHeight => Geometry.Height;
    [Newtonsoft.Json.JsonProperty("flipped_die")]
    public bool FlippedDie => Geometry.FlippedDie;
    [Newtonsoft.Json.JsonProperty("implementation")]
    public string Implementation => "PackStudio C# / .NET 10";
    [Newtonsoft.Json.JsonProperty("outline_type")]
    public string OutlineType => "standard_outline";
    [Newtonsoft.Json.JsonProperty("die_type")]
    public string DieType => "actual_type";
    [Newtonsoft.Json.JsonProperty("native_grid_enabled")]
    public bool GridEnabled { get; init; }
    [Newtonsoft.Json.JsonProperty("native_grid_density")]
    public string GridDensity { get; init; } = "fine";
    [Newtonsoft.Json.JsonProperty("solder_ball_count")]
    public int SolderBallCount { get; set; }
    [Newtonsoft.Json.JsonProperty("solder_ball_representation")]
    public string SolderBallRepresentation { get; set; } = "";
    [Newtonsoft.Json.JsonProperty("flip_chip_bump_count")]
    public int FlipChipBumpCount { get; set; }
}
