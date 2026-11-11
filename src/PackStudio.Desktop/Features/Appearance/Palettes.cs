using System.Windows.Media;

namespace PackStudio.Desktop;

/// <summary>可选配色方案。默认使用经典配色，保持原有示意图与三维视图的观感。</summary>
public static class Palettes
{
    public static Palette Classic { get; } = new("classic", "经典",
        Die: Rgb(0xFF1744), Substrate: Rgb(0x00C83F), Ceramic: Rgb(0x00A043), SolderMask: Rgb(0x006B32),
        Metal: Rgb(0xFFA000), Mold: Rgb(0x3996FF), Solder: Rgb(0x653FFF), Attach: Rgb(0x7A2400),
        Bump: Rgb(0x9477FF), Wire: Rgb(0xD600C7), Cover: Rgb(0x00B8D9), Accent: Rgb(0x0057D9));

    public static Palette Soft { get; } = new("soft", "柔和",
        Die: Rgb(0xE88098), Substrate: Rgb(0x8CC9A8), Ceramic: Rgb(0x7FBFA0), SolderMask: Rgb(0x5E9B7C),
        Metal: Rgb(0xE7BB74), Mold: Rgb(0x93BAE3), Solder: Rgb(0x9C93DE), Attach: Rgb(0xAC8A6C),
        Bump: Rgb(0xBCAEE7), Wire: Rgb(0xD494CE), Cover: Rgb(0x8DC4D2), Accent: Rgb(0x5F86C0));

    public static Palette Morandi { get; } = new("morandi", "莫兰迪",
        Die: Rgb(0xAC5264), Substrate: Rgb(0x77966B), Ceramic: Rgb(0xA6B584), SolderMask: Rgb(0x36574B),
        Metal: Rgb(0xD6B36A), Mold: Rgb(0xB5C8D5), Solder: Rgb(0x76639E), Attach: Rgb(0x614638),
        Bump: Rgb(0xAB96C5), Wire: Rgb(0x8F416F), Cover: Rgb(0x579595), Accent: Rgb(0x355F7C));

    public static Palette Warm { get; } = new("warm", "暖阳",
        Die: Rgb(0xD64432), Substrate: Rgb(0x6A9140), Ceramic: Rgb(0xB0B96A), SolderMask: Rgb(0x354F2C),
        Metal: Rgb(0xF1B52E), Mold: Rgb(0xF2CEA1), Solder: Rgb(0x7154A6), Attach: Rgb(0x60362A),
        Bump: Rgb(0xAB8DD2), Wire: Rgb(0xA42A6C), Cover: Rgb(0x399C9B), Accent: Rgb(0xB74719));

    public static Palette Cool { get; } = new("cool", "蓝调",
        Die: Rgb(0x2854A0), Substrate: Rgb(0x279D91), Ceramic: Rgb(0x8EC6AD), SolderMask: Rgb(0x174D52),
        Metal: Rgb(0xE4B55F), Mold: Rgb(0xB9DCF0), Solder: Rgb(0x8451B4), Attach: Rgb(0x4B3B51),
        Bump: Rgb(0xB48DDD), Wire: Rgb(0xC23979), Cover: Rgb(0x5494AD), Accent: Rgb(0x173C74));

    public static IReadOnlyList<Palette> All { get; } = [Classic, Soft, Morandi, Warm, Cool];

    static Color Rgb(int value) => Color.FromRgb((byte)(value >> 16), (byte)(value >> 8), (byte)value);
}
