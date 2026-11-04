using Newtonsoft.Json;

namespace PackStudio.Core;

public sealed record SchematicProfile(bool Bga, bool Flip, bool Bare, bool Qfn, bool Sop,
    [property: JsonProperty("chip_array")] bool ChipArray, bool Wirebond, bool Ceramic);
public sealed record TemplateInfo(string Id, string Name, string Group, string Description, string Icon,
    SchematicProfile Schematic, [property: JsonProperty("surface_radiation")] bool SurfaceRadiation,
    [property: JsonProperty("default")] bool IsDefault = false);
public sealed record ModelGroup(string Name, string? Parent = null);
