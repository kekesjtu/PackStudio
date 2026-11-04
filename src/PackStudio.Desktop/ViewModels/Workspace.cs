using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PackStudio.Core;
using Newtonsoft.Json.Linq;

namespace PackStudio.Desktop;
public sealed partial class Workspace : ObservableObject
{
    public PackageCatalog Catalog { get; } = new(App.DataRoot);
    public ProjectDocument Document { get; private set; } = new();
    public Template Template { get; private set; } = null!;

    [ObservableProperty]
    string status = "选择封装，编辑参数，然后生成模型。";
    [ObservableProperty]
    bool isBusy;
    [ObservableProperty]
    bool isCurrent;
    public PackageModel? Model { get; private set; }
    public long Revision { get; private set; }
    public HashSet<string> Hidden { get; } = [];
    public HashSet<string> Selected { get; } = [];

    public string DesignName => Document.Name;
    public void Rename(string value) { Document.Name = value; OnPropertyChanged(nameof(DesignName)); Dirty(); }

    public event Action? ModelChanged;
    public event Action? DocumentChanged;
    public Workspace() => Select("cbga_fc", null);
    public void Select(string id, string? presetId = null)
    {
        Template = Catalog.Load(id);
        string preset = presetId ?? Template.DefaultPreset;
        Document = ProjectDocument.Create(Template, preset);
        Dirty();
        DocumentChanged?.Invoke();
    }

    public void Load(ProjectDocument document)
    {
        Template = Catalog.Load(document.TemplateId);
        Document = document;
        Document.Values = Template.Restore(document.PresetId, document.Values);
        Dirty();
        DocumentChanged?.Invoke();
    }

    public void Dirty()
    {
        Revision++;
        IsCurrent = false;
        Status = "参数有修改，请生成模型。";
    }

    partial void OnIsBusyChanged(bool value) => GenerateCommand.NotifyCanExecuteChanged();
    bool CanGenerate() => !IsBusy;
    [RelayCommand(CanExecute = nameof(CanGenerate))]
    public async Task GenerateAsync()
    {
        var snapshot = Document.Clone();
        long revision = Revision;
        IsBusy = true;
        Status = "正在生成模型…";
        try
        {
            var model = await Task.Run(() => new ModelBuilder(Catalog).Generate(snapshot));
            if (revision != Revision)
            {
                Status = "生成期间参数有修改，请重新生成。";
                return;
            }

            Model = model;
            IsCurrent = true;
            Hidden.Clear();
            Selected.Clear();
            InspectedGroup = null;
            RangeAnchor = null;
            Status = $"{model.Name} · {model.Blocks.Count} 个矩形块 · {model.Materials.Count} 种材料 · {model.Sources.Sum(s => s.Power):G6} W";
            ModelChanged?.Invoke();
        }
        catch (Exception ex)
        {
            IsCurrent = false;
            Status = ex.Message;
            NLog.LogManager.GetCurrentClassLogger().Warn(ex, "生成失败");
        }
        finally
        {
            IsBusy = false;
        }
    }

    public void ChangeVisibility(IEnumerable<string> ids, bool visible, bool only = false)
    {
        if (Model == null)
            return;
        if (only)
        {
            Hidden.Clear();
            Hidden.UnionWith(Model.Blocks.Select(b => b.Id));
        }

        foreach (string id in ids)
            if (visible)
                Hidden.Remove(id);
            else
                Hidden.Add(id);
        ModelChanged?.Invoke();
    }
}
