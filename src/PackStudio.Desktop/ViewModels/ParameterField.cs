using System.Globalization;
using CommunityToolkit.Mvvm.ComponentModel;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;

public sealed class ParameterField : ObservableObject
{
    readonly ParameterForm form;
    readonly ParameterField? parent;
    bool expanded;
    string text;
    public JToken Definition { get; }
    public ParameterField(ParameterForm form, JToken definition, ParameterField? parent)
    {
        this.form = form; this.parent = parent; Definition = definition;
        text = Display(Value);
        expanded = Value is JArray { Count: > 0 };
    }
    public string Key => Definition["key"].Text();
    public string Path => parent == null ? Key : parent.Path + "/" + Key;
    public string Label => Definition["label"].Text();
    public string Control => Definition["control"].Text();
    public string Step => parent?.Step ?? Definition["step"].Text();
    public JToken? Value => form.Get(Path);
    JObject Scope => parent?.Value as JObject ?? form.Values;
    public bool Visible => (parent?.Visible ?? true) && JsonData.Matches(Definition["visible_when"] as JObject, Scope);
    public bool Enabled => (parent?.Enabled ?? true) && JsonData.Matches(Definition["enabled_when"] as JObject, Scope);
    public string Symbol => TemplateSymbols.Resolve(Definition, form.Values);
    public JArray Options => form.Template.OptionsFor(Definition);
    public string? Error => FieldValues.Error(Definition, Value, Options);
    public bool HasError => Error != null;
    public bool Expanded { get => expanded; set => SetProperty(ref expanded, value); }
    public int MatrixRows => Count(Definition["rows_key"].Text());
    public int MatrixColumns => Count(Definition["columns_key"].Text());
    int Count(string key) => form.Values[key]?.Type is JTokenType.Integer or JTokenType.Float &&
        double.IsFinite(form.Values[key]!.Number()) && form.Values[key]!.Number() is >= 0 and <= 1000 ? (int)form.Values[key]!.Number() : 0;
    public bool BooleanValue { get => Value.Flag(); set => Set(new JValue(value)); }
    public JToken? ChoiceValue { get => Value; set { if (value != null) Set(value); } }
    public string TextValue
    {
        get => text;
        set { SetProperty(ref text, value); Set(FieldValues.Parse(Definition, value)); }
    }
    public string DerivedValue
    {
        get
        {
            double n = ParameterRules.Derived(Definition["calculation"].Text(), form.Values);
            return double.IsFinite(n) ? n.ToString("G9", CultureInfo.InvariantCulture) : "";
        }
    }
    public void Set(JToken value) => form.Set(this, value);
    internal IEnumerable<string> RuleDependencies(string rule) =>
        (parent?.RuleDependencies(rule) ?? []).Concat((Definition[rule] as JObject ?? new()).Properties()
            .Select(p => parent == null ? p.Name : parent.Path + "/" + p.Name));
    internal void Notify(string property)
    {
        OnPropertyChanged(property);
        if (property != nameof(Value)) return;
        OnPropertyChanged(nameof(BooleanValue));
        OnPropertyChanged(nameof(ChoiceValue));
        OnPropertyChanged(nameof(Error));
        OnPropertyChanged(nameof(HasError));
        if (!JToken.DeepEquals(FieldValues.Parse(Definition, text), Value))
            SetProperty(ref text, Display(Value), nameof(TextValue));
    }
    static string Display(JToken? value) => value?.Type is null or JTokenType.Null ? "" : value.ToString();
}
