using System.Windows;
using System.Windows.Controls;

namespace PackStudio.Desktop;

public sealed class ModelRootItem : TreeViewItem
{
    static ModelRootItem()
    {
        IsExpandedProperty.OverrideMetadata(typeof(ModelRootItem),
            new FrameworkPropertyMetadata(true, null, (_, _) => true));
    }
}
