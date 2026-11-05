namespace PackStudio.Core;

public sealed record Footprint(double Length, double Width);
public sealed record PackageGeometry(Footprint Outline, Footprint Grid, Footprint Bottom, Footprint Top, double Height, bool FlippedDie);

public sealed record ModelMetadata([property: Newtonsoft.Json.JsonIgnore] PackageGeometry Geometry)
{
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
    public int SolderBallCount { get; init; }
    [Newtonsoft.Json.JsonProperty("solder_ball_representation")]
    public string SolderBallRepresentation { get; init; } = "";
    [Newtonsoft.Json.JsonProperty("flip_chip_bump_count")]
    public int FlipChipBumpCount { get; init; }
}
