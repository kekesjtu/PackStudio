using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;

internal static class DesFieldLabels
{
    static readonly IReadOnlyDictionary<string, string> SchematicNames = new Dictionary<string, string>
    {
        ["package.length"] = "封装长度", ["package.width"] = "封装宽度",
        ["substrate.length"] = "封装长度", ["substrate.width"] = "封装宽度",
        ["die.attach"] = "粘接层", ["bumps.height"] = "凸点高度",
        ["bga.columns"] = "X 方向列数", ["bga.rows"] = "Y 方向行数",
        ["bga.pitch"] = "间距", ["bga.diameter"] = "球径", ["bga.height"] = "离板高度",
        ["bond_wire.extent_length"] = "线阵列长度", ["bond_wire.extent_width"] = "线阵列宽度",
        ["bond_wire.length_x"] = "线阵列长度", ["bond_wire.length_y"] = "线阵列宽度",
        ["bond_wire.diameter"] = "线径",
        ["flag.length"] = "承载台长度", ["flag.width"] = "承载台宽度",
        ["pad.length"] = "承载台长度", ["pad.width"] = "承载台宽度",
        ["leads.pitch"] = "节距", ["leads.pitch_x"] = "节距 X", ["leads.pitch_y"] = "节距 Y",
        ["leads.width"] = "线宽", ["leads.thickness"] = "引脚厚度", ["leads.height"] = "引脚高度",
        ["leads.foot_length"] = "引脚足长", ["leads.length"] = "外露长度",
        ["leads.gap"] = "框架间隙", ["leads.gap_x"] = "框架间隙", ["leads.gap_y"] = "框架间隙 Y",
        ["thermal_land.thickness"] = "散热焊料厚度",
        ["vias.diameter"] = "孔径", ["vias.plating"] = "镀层厚度",
        ["vias.offset_x"] = "X 偏移", ["vias.offset_y"] = "Y 偏移",
        ["metal.hole_length"] = "顶层开孔长度", ["metal.hole_width"] = "孔宽",
        ["trace.top_thickness"] = "顶层铜厚度", ["trace.bottom_thickness"] = "底层铜厚度",
        ["cover.length"] = "顶部长度", ["cover.width"] = "顶部宽度", ["cover.thickness"] = "顶部厚度",
        ["lid.length"] = "顶部长度", ["lid.width"] = "顶部宽度", ["lid.thickness"] = "顶部厚度",
        ["plate.length"] = "顶部长度", ["plate.width"] = "顶部宽度", ["plate.thickness"] = "顶部厚度",
        ["slug.width"] = "宽度", ["slug.thickness"] = "厚度", ["slug.diameter"] = "顶部直径",
        ["slug.clearance"] = "支脚间隙", ["spreader.width"] = "宽度", ["spreader.thickness"] = "厚度",
        ["upper.thickness"] = "增层厚度", ["lower.thickness"] = "增层厚度"
    };

    internal static string Name(JToken field, string templateId)
    {
        string key = field["key"].Text();
        if (templateId == "bare_die" && key is "die.width" or "die.thickness")
            return key == "die.width" ? "宽度" : "厚度";
        return SchematicNames.TryGetValue(key, out var name) ? name : field["label"].Text();
    }

    internal static string Symbol(JToken field, string substrateLayers)
    {
        JToken? entry = field["des_symbol"];
        string symbol = entry is JObject choices ? choices[substrateLayers].Text() : entry.Text();
        return symbol.Length > 0 ? symbol : ConfigurationSymbol(field["key"].Text());
    }

    internal static string ConfigurationSymbol(string key) => key switch
    {
        "bga.populated_rows" => "MEp", "bga.populated_columns" => "MDp",
        "bga.center_solder_rows" => "MEc", "bga.center_solder_columns" => "MDc",
        _ => ""
    };
}
