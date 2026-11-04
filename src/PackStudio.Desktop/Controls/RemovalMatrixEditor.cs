using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using Newtonsoft.Json.Linq;

namespace PackStudio.Desktop;

public sealed class RemovalMatrixEditor : ContentControl
{
    public static readonly DependencyProperty RowsProperty = DependencyProperty.Register(nameof(Rows), typeof(int), typeof(RemovalMatrixEditor), new PropertyMetadata(0, Refresh));
    public static readonly DependencyProperty ColumnsProperty = DependencyProperty.Register(nameof(Columns), typeof(int), typeof(RemovalMatrixEditor), new PropertyMetadata(0, Refresh));
    public static readonly DependencyProperty CellsProperty = DependencyProperty.Register(nameof(Cells), typeof(JArray), typeof(RemovalMatrixEditor), new PropertyMetadata(null, Refresh));
    public int Rows { get => (int)GetValue(RowsProperty); set => SetValue(RowsProperty, value); }
    public int Columns { get => (int)GetValue(ColumnsProperty); set => SetValue(ColumnsProperty, value); }
    public JArray? Cells { get => (JArray?)GetValue(CellsProperty); set => SetValue(CellsProperty, value); }
    readonly ParameterField field;
    int builtRows = -1, builtColumns = -1;
    public RemovalMatrixEditor(ParameterField field)
    {
        this.field = field;
        IsVisibleChanged += (_, _) => Rebuild();
        SetBinding(RowsProperty, new Binding(nameof(ParameterField.MatrixRows)) { Source = field });
        SetBinding(ColumnsProperty, new Binding(nameof(ParameterField.MatrixColumns)) { Source = field });
        SetBinding(CellsProperty, new Binding(nameof(ParameterField.Value)) { Source = field });
    }
    static void Refresh(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        var editor = (RemovalMatrixEditor)d;
        editor.Rebuild();
    }
    void Rebuild()
    {
        if (!IsVisible) return;
        if (Content is RemovalMatrixView view && Rows == builtRows && Columns == builtColumns) view.UpdateCells(Cells ?? []);
        else
        {
            Content = RemovalMatrix.Build(Cells ?? [], Rows, Columns, field.Set);
            builtRows = Rows; builtColumns = Columns;
        }
    }
}
