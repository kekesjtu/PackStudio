using System.Globalization;
using System.Text;
using System.Xml;
using System.Xml.Linq;

namespace PackStudio.Core;

internal static class XmlExport
{
    internal static string Format(double value) => double.IsFinite(value)
        ? value == 0 ? "0" : value.ToString("G12", CultureInfo.InvariantCulture)
        : throw new ArgumentException("模型 XML 需要有限数值。");

    internal static void Save(XDocument document, string path)
    {
        string absolute = Path.GetFullPath(path), temporary = absolute + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            using (var writer = XmlWriter.Create(temporary, new XmlWriterSettings { Indent = true, Encoding = new UTF8Encoding(false) }))
                document.Save(writer);
            File.Move(temporary, absolute, true);
        }
        finally
        {
            if (File.Exists(temporary)) File.Delete(temporary);
        }
    }
}
