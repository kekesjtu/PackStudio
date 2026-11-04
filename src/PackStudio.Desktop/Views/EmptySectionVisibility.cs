using System.Globalization;
using System.Windows;
using System.Windows.Data;

namespace PackStudio.Desktop;

public sealed class EmptySectionVisibility : IMultiValueConverter
{
    public object Convert(object[] values, Type targetType, object parameter, CultureInfo culture) =>
        values.OfType<bool>().Any(value => value) ? Visibility.Collapsed : Visibility.Visible;
    public object[] ConvertBack(object value, Type[] targetTypes, object parameter, CultureInfo culture) => throw new NotSupportedException();
}
