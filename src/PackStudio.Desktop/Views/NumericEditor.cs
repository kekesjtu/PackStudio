using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Media;
using PackStudio.Core;

namespace PackStudio.Desktop;

public sealed class NumericEditor : Border
{
    public static readonly DependencyProperty TextProperty = DependencyProperty.Register(nameof(Text), typeof(string), typeof(NumericEditor),
        new FrameworkPropertyMetadata("", FrameworkPropertyMetadataOptions.BindsTwoWayByDefault));
    public string Text { get => (string)GetValue(TextProperty); set => SetCurrentValue(TextProperty, value); }

    public NumericEditor(ParameterField field)
    {
        DataContext = field;
        BorderThickness = new(1); BorderBrush = Brushes.LightSlateGray; CornerRadius = new(2); Background = Brushes.White;
        var dock = new DockPanel(); Child = dock;
        var text = new TextBox { BorderThickness = new(0), Padding = new(6, 3, 6, 3), MinWidth = 60 };
        text.SetBinding(TextBox.TextProperty, new Binding(nameof(Text)) { Source = this, Mode = BindingMode.TwoWay, UpdateSourceTrigger = UpdateSourceTrigger.PropertyChanged });
        var style = new Style(typeof(TextBox));
        style.Setters.Add(new Setter(TextBox.ForegroundProperty, Brushes.Black));
        style.Triggers.Add(new DataTrigger { Binding = new Binding(nameof(ParameterField.HasError)) { Source = field }, Value = true,
            Setters = { new Setter(TextBox.ForegroundProperty, Brushes.Firebrick) } });
        text.Style = style;
        text.SetBinding(ToolTipProperty, new Binding(nameof(ParameterField.Error)) { Source = field });
        text.GotKeyboardFocus += (_, _) => text.SelectAll();
        if (field.Control.StartsWith("integer"))
        {
            var arrows = new Grid { Width = 22 };
            arrows.RowDefinitions.Add(new()); arrows.RowDefinitions.Add(new());
            arrows.SetBinding(HeightProperty, new Binding(nameof(ActualHeight)) { Source = text });
            DockPanel.SetDock(arrows, Dock.Right); dock.Children.Add(arrows);
            foreach (int direction in new[] { 1, -1 })
            {
                var button = new Button { Content = new System.Windows.Shapes.Path
                {
                    Data = Geometry.Parse(direction == 1 ? "M0,3 L5,3 L2.5,0 Z" : "M0,0 L5,0 L2.5,3 Z"), Fill = Brushes.SlateGray,
                    HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center
                }, Padding = new(0), Margin = new(0), MinHeight = 0, Focusable = false };
                button.Click += (_, _) =>
                {
                    if (!double.TryParse(Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double n)) return;
                    double minimum = field.Definition["minimum"]?.Number() ?? 0;
                    double maximum = field.Definition["maximum"]?.Number(long.MaxValue) ?? long.MaxValue;
                    Text = Math.Clamp(Math.Truncate(n) + direction, minimum, maximum).ToString(CultureInfo.InvariantCulture);
                };
                Grid.SetRow(button, arrows.Children.Count); arrows.Children.Add(button);
            }
        }
        else if (field.Definition["unit"].Text() is string unit && unit.Length > 0)
        {
            var label = new TextBlock { Text = unit, Margin = new(5, 0, 7, 0), Foreground = Brushes.SlateGray, VerticalAlignment = VerticalAlignment.Center };
            DockPanel.SetDock(label, Dock.Right); dock.Children.Add(label);
        }
        dock.Children.Add(text);
        SetBinding(TextProperty, new Binding(nameof(ParameterField.TextValue)) { Source = field, Mode = BindingMode.TwoWay, UpdateSourceTrigger = UpdateSourceTrigger.PropertyChanged });
    }
}
