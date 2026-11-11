using System.Globalization;
using CommunityToolkit.Mvvm.ComponentModel;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;

public sealed class ParameterField : ObservableObject
{
    readonly ParameterForm form;
    bool expanded;
    string text;
    public JToken Definition { get; }
    public ParameterField(ParameterForm form, JToken definition)
    {
        this.form = form; Definition = definition;
        text = Display(Value);
        expanded = Value is JArray { Count: > 0 };
    }
    public string Key => Definition["key"].Text();
    internal static bool MatchesPath(string field, string issue) => issue == field || issue.StartsWith(field + "[");
    public string Label => Definition["label"].Text();
    public string Type => Definition["type"].Text();
    public string Step => Definition["step"].Text();
    public JToken? Value => form.Values[Key];
    public bool Visible => JsonData.Matches(Definition["visible_when"] as JObject, form.Values);
    public bool Enabled => JsonData.Matches(Definition["enabled_when"] as JObject, form.Values);
    public string Symbol => TemplateSymbols.Resolve(Definition, form.Values);
    public string Range => Bounds(Definition);
    public string RowsRange => Rows(Definition);
    public JArray Options => form.Template.OptionsFor(Definition);
    public string? Error => form.Error(Key);
    public bool HasError => Error != null;
    public bool Expanded
    {
        get => expanded;
        set
        {
            if (SetProperty(ref expanded, value) && value && Key == "bga.omitted_cells")
                form.UseDiscreteBalls();
        }
    }
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
        (Definition[rule] as JObject ?? new()).Properties().Select(p => p.Name);
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
