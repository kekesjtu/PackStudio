using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PackStudio.Core;

namespace PackStudio.Desktop;
public sealed partial class Workspace : ObservableObject
{
    public RuntimeDataCatalog Catalog { get; } = new(App.DataRoot);
    public ProjectDocument Document { get; private set; } = new();
    public PackageDefinition Template { get; private set; } = null!;

    [ObservableProperty]
    string status = "选择封装，编辑参数，然后生成模型。";
    [ObservableProperty]
    bool isBusy;
    [ObservableProperty]
    bool isCurrent;
    public GenerationResult? Result { get; private set; }
    public PackageModel? Model => Result is { CanPreview: true } ? Result.Model : null;
    public bool CanExport => IsCurrent && Result is { CanExport: true };
    public IReadOnlyList<ValidationIssue> Issues => IsCurrent ? Result?.Issues ?? [] : [];
    public long Revision { get; private set; }
    public HashSet<string> Hidden { get; } = [];
    public HashSet<string> Selected { get; } = [];

    public string DesignName => Document.Name;
    public void Rename(string value) { Document.Name = value; OnPropertyChanged(nameof(DesignName)); Dirty(); }

    public event Action? ModelChanged;
    public event Action? DocumentChanged;
    public event Action? IssuesChanged;
    public event Action<string>? ParameterRequested;
    public Workspace() => Select(Catalog.DefaultFamily.Id, null);
    public void Select(string id, string? presetId = null)
    {
        Template = Catalog.Load(id);
        string preset = presetId ?? Template.DefaultPreset;
        var exposedPad = id is "sop" or "pqfp" && Template.DisplayDefaults(preset)["package.exposed_pad"].Flag()
            ? Catalog.LoadExposedPad(id) : null;
        Document = PackageInitializer.Create(Template, preset, exposedPad: exposedPad);
        Result = null;
        Dirty();
        DocumentChanged?.Invoke();
        ModelChanged?.Invoke();
    }

    public void Load(ProjectDocument document)
    {
        Template = Catalog.Load(document.TemplateId);
        Document = document;
        Result = null;
        Dirty();
        DocumentChanged?.Invoke();
        ModelChanged?.Invoke();
    }

    public void Dirty()
    {
        Revision++;
        IsCurrent = false;
        OnPropertyChanged(nameof(CanExport));
        OnPropertyChanged(nameof(Issues));
        IssuesChanged?.Invoke();
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
            var definition = Template;
            var rules = Catalog.LoadValidation(snapshot.TemplateId);
            var result = await Task.Run(() => ModelBuilder.Generate(snapshot, definition, Catalog.Materials, rules, Catalog.Groups));
            if (revision != Revision)
            {
                Status = "生成期间参数有修改，请重新生成。";
                return;
            }

            Result = result;
            IsCurrent = true;
            OnPropertyChanged(nameof(CanExport));
            OnPropertyChanged(nameof(Issues));
            Hidden.Clear();
            Selected.Clear();
            InspectedGroup = null;
            RangeAnchor = null;
            Status = result.HasErrors ? $"生成检查发现 {result.Issues.Count(i => i.Severity == IssueSeverity.Error)} 个错误，请在问题列表中定位。"
                : result.Model is { } model ? $"{model.Name} · {model.Blocks.Count} 个矩形块 · {model.Materials.Count} 种材料 · {model.Sources.Sum(s => s.Power):G6} W" : "模型未生成。";
            IssuesChanged?.Invoke();
            ModelChanged?.Invoke();
        }
        catch (Exception ex)
        {
            IsCurrent = false;
            OnPropertyChanged(nameof(CanExport));
            OnPropertyChanged(nameof(Issues));
            IssuesChanged?.Invoke();
            Status = ex.Message;
            NLog.LogManager.GetCurrentClassLogger().Warn(ex, "生成失败");
        }
        finally
        {
            IsBusy = false;
        }
    }

    public void LocateIssue(ValidationIssue issue)
    {
        Selected.Clear();
        Selected.UnionWith(issue.EntityIds);
        Hidden.ExceptWith(issue.EntityIds);
        InspectedGroup = null;
        RangeAnchor = null;
        ModelChanged?.Invoke();
        if (issue.ParameterPaths.FirstOrDefault() is { } path) ParameterRequested?.Invoke(path);
        Status = issue.Message;
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
