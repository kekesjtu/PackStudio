namespace PackStudio.Core;

// 散热块各字段的定义下限为 0；几何自洽关系在这里按本体、顶部圆盘、侧壁与竖向空间统一检查。
internal static class SlugInputRules
{
    public static void Validate(InputChecks c, bool wirebond)
    {
        if (!c.B("slug.enabled")) return;
        double length = c.N("slug.length"), width = c.N("slug.width"), thickness = c.N("slug.thickness"),
            diameter = c.N("slug.diameter"), footLength = c.N("slug.foot_length"), footWidth = c.N("slug.foot_width");
        c.Check(length <= 0 || width <= 0 || thickness <= 0 || diameter <= 0,
            "input.slug.size", "散热块的长度、宽度、厚度与顶部直径必须大于零。",
            "slug.length", "slug.width", "slug.thickness", "slug.diameter");
        c.Check(footLength <= length || footWidth <= width,
            "input.slug.foot", "支脚外轮廓必须大于散热块本体。",
            "slug.foot_length", "slug.foot_width", "slug.length", "slug.width");
        double side = Math.Sqrt(Math.PI) * diameter / 2;
        c.Check(side >= length || side >= width,
            "input.slug.plate", "顶部圆盘的等效边长必须小于散热块本体。",
            "slug.diameter", "slug.length", "slug.width");
        c.Check(2 * thickness >= length || 2 * thickness >= width,
            "input.slug.wall", "散热块侧壁厚度必须为正。",
            "slug.thickness", "slug.length", "slug.width");
        c.Check(c.N("die.length") > length - 2 * thickness || c.N("die.width") > width - 2 * thickness,
            "input.slug.die", "芯片必须位于散热块腔体内。",
            "die.length", "die.width", "slug.length", "slug.width", "slug.thickness");
        string[] height;
        double available;
        if (wirebond)
        {
            height = ["encapsulant.thickness", "solder_mask.thickness"];
            available = c.N("encapsulant.thickness") - c.N("solder_mask.thickness");
        }
        else if (c.B("cover.flush"))
        {
            height = ["bumps.height", "die.thickness"];
            available = c.N("bumps.height") + c.N("die.thickness");
        }
        else
        {
            height = ["cover.thickness"];
            available = c.N("cover.thickness");
        }
        c.Check(thickness + c.N("slug.offset") + c.N("slug.clearance") >= available,
            "input.slug.height", "厚度、顶部台阶与支脚间隙之和必须小于塑封高度。",
            ["slug.thickness", "slug.offset", "slug.clearance", .. height]);
        if (c.B("slug.adhesive_enabled"))
            c.Check(c.N("slug.clearance") <= 0,
                "input.slug.adhesive", "启用支脚粘接层时支脚间隙必须大于零。", "slug.clearance", "slug.adhesive_enabled");
    }
}
