using System.Windows.Controls;
using Newtonsoft.Json.Linq;

namespace PackStudio.Desktop;

public sealed class RemovalMatrixView(Action<JArray> updateCells) : StackPanel
{
    public void UpdateCells(JArray cells) => updateCells(cells);
}
