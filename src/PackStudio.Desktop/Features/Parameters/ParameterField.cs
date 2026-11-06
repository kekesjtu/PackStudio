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
    internal static bool MatchesPath(string field, string issue)
    {
        string dotted = field.Replace('/', '.');
        return issue == field || issue == dotted || issue.StartsWith(field + "/") || issue.StartsWith(dotted + "[") ||
            issue.StartsWith(dotted + ".") || dotted.StartsWith(issue + ".");
    }
    public string Label => Definition["label"].Text();
    public string Type => Definition["type"].Text();
    public string Step => parent?.Step ?? Definition["step"].Text();
    public JToken? Value => form.Get(Path);
    JObject Scope => parent?.Value as JObject ?? form.Values;
    public bool Visible => (parent?.Visible ?? true) && JsonData.Matches(Definition["visible_when"] as JObject, Scope);
    public bool Enabled => (parent?.Enabled ?? true) && JsonData.Matches(Definition["enabled_when"] as JObject, Scope);
    public string Symbol => TemplateSymbols.Resolve(Definition, form.Values);
    public string Range => Bounds(Definition);
    public string RowsRange => Rows(Definition);
    public JArray Options => form.Template.OptionsFor(Definition);
    public string? Error => form.Error(Path);
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
    internal static string Bounds(JToken definition)
    {
        static string? Format(JToken? token) => token?.Type is JTokenType.Integer or JTokenType.Float
            ? token.Value<double>().ToString("0.################", CultureInfo.InvariantCulture) : null;
        string? min = Format(definition["minimum"]), exclusive = Format(definition["exclusive_minimum"]), max = Format(definition["maximum"]);
        if (exclusive != null) return max == null ? ">" + exclusive : ">" + exclusive + "~" + max;
        if (min != null) return max == null ? "≥" + min : min + "~" + max;
        return max == null ? "" : "≤" + max;
    }
    static string Rows(JToken definition)
    {
        static string? Format(JToken? token) => token?.Type is JTokenType.Integer ? token.Value<int>().ToString(CultureInfo.InvariantCulture) : null;
        string? min = Format(definition["min_rows"]), max = Format(definition["max_rows"]);
        if (min == null && max == null) return "";
        if (max == null) return "行数 ≥" + min;
        return min == null ? "行数 ≤" + max : "行数 " + min + "~" + max;
    }
}
