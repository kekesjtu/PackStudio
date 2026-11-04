using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PackStudio.Core;

namespace PackStudio.Desktop;

public sealed record ModelNode(string Id, string Name, List<Block> Blocks, Block? Block = null);

public sealed partial class Workspace
{
    [ObservableProperty]
    ModelNode? inspectedGroup;
    public string? RangeAnchor { get; private set; }

    public void SelectNode(ModelNode node, bool control = false, bool shift = false, IReadOnlyList<string>? visible = null, bool toggle = true)
    {
        if (node.Block == null)
        {
            Selected.Clear();
            RangeAnchor = null;
            InspectedGroup = node;
        }
        else
        {
            InspectedGroup = null;
            var ordered = visible?.ToList() ?? [];
            if (shift && RangeAnchor != null && ordered.Contains(RangeAnchor) && ordered.Contains(node.Id))
            {
                if (!control) Selected.Clear();
                int a = ordered.IndexOf(RangeAnchor), b = ordered.IndexOf(node.Id);
                Selected.UnionWith(ordered.Skip(Math.Min(a, b)).Take(Math.Abs(a - b) + 1));
            }
            else
            {
                bool deselect = toggle && Selected.Contains(node.Id) && (control || Selected.Count == 1);
                if (!control) Selected.Clear();
                if (deselect) Selected.Remove(node.Id);
                else Selected.Add(node.Id);
                RangeAnchor = Selected.Count > 0 ? node.Id : null;
            }
        }
        ModelChanged?.Invoke();
    }

    [RelayCommand]
    public void ClearSelection()
    {
        Selected.Clear();
        InspectedGroup = null;
        RangeAnchor = null;
        ModelChanged?.Invoke();
    }

    [RelayCommand]
    void ShowAll() => ChangeVisibility(Model?.Blocks.Select(b => b.Id) ?? [], true);
    [RelayCommand]
    void HideAll() => ChangeVisibility(Model?.Blocks.Select(b => b.Id) ?? [], false);
}
