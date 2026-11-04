using System.ComponentModel;
using System.Globalization;
using System.IO;
using System.Windows;
using CommunityToolkit.Mvvm.ComponentModel;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;

public sealed class SummaryField : ObservableObject
{
    readonly Workspace workspace;
    readonly JToken definition;
    readonly ParameterField? parameter;
    public SummaryField(Workspace workspace, ParameterForm form, JToken definition)
    {
        this.workspace = workspace; this.definition = definition;
        if (Source is not ("document.name" or "template.name" or "parameter"))
            throw new InvalidDataException($"未知概要来源 {Source}。");
        if (Editable && Source != "document.name") throw new InvalidDataException($"概要来源 {Source} 不支持编辑。");
        parameter = form.Fields.SingleOrDefault(f => f.Path == definition["parameter"].Text());
        var keys = (definition["visible_when"] as JObject ?? new()).Properties().Select(p => p.Name).ToHashSet();
        if (parameter != null) keys.Add(parameter.Path);
        foreach (var field in form.Fields.Where(f => keys.Contains(f.Path)))
            PropertyChangedEventManager.AddHandler(field, OnParameterChanged, "");
        if (Source == "document.name")
            PropertyChangedEventManager.AddHandler(workspace, OnNameChanged, nameof(Workspace.DesignName));
    }
    string Source => definition["source"].Text();
    string RawText => Source switch
    {
        "document.name" => workspace.DesignName,
        "template.name" => workspace.Template.Info.Name,
        "parameter" => parameter?.Value?.ToString() ?? "",
        _ => throw new InvalidDataException($"未知概要来源 {Source}。")
    };
    public string Label => definition["label"].Text();
    public bool Editable => definition["editable"].Flag();
    public int MaximumLength => (int)definition["maximum_length"].Number();
    public bool Visible => JsonData.Matches(definition["visible_when"] as JObject, workspace.Document.Values) &&
        (!definition["hide_when_empty"].Flag() || RawText.Length > 0);
    public string Symbol => parameter?.Symbol ?? "";
    public string Text
    {
        get => RawText.Length == 0 ? "" : string.Format(CultureInfo.InvariantCulture, definition["format"].Text("{0}"), RawText);
        set { if (Editable && workspace.DesignName != value) workspace.Rename(value); }
    }
    void OnNameChanged(object? sender, PropertyChangedEventArgs e) => OnPropertyChanged(nameof(Text));
    void OnParameterChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (e.PropertyName is not (nameof(ParameterField.Value) or nameof(ParameterField.Symbol))) return;
        OnPropertyChanged(nameof(Text));
        OnPropertyChanged(nameof(Symbol));
        OnPropertyChanged(nameof(Visible));
    }
}
