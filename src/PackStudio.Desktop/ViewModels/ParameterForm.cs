using System.IO;
using System.Globalization;
using CommunityToolkit.Mvvm.ComponentModel;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;

public sealed class ParameterForm : ObservableObject
{
    readonly Workspace workspace;
    public IReadOnlyList<ParameterField> Fields { get; }
    public event Action? Changed;

    public ParameterForm(Workspace workspace)
    {
        this.workspace = workspace;
        Fields = Expand(workspace.Template.Fields, workspace.Document.Values, null).ToList();
    }

    IEnumerable<ParameterField> Expand(JArray definitions, JObject values, ParameterField? parent)
    {
        foreach (var definition in definitions)
        {
            var field = new ParameterField(this, definition, values, parent);
            if (field.Control == "object")
            {
                if (field.Value is not JObject nested)
                    throw new InvalidDataException($"{field.Key} 缺少模板初始化的对象值。");
                foreach (var child in Expand((JArray)definition["fields"]!, nested, field)) yield return child;
            }
            else yield return field;
        }
    }

    public JObject Values => workspace.Document.Values;
    public void NotifyViewChanged() => Changed?.Invoke();
    public void Set(ParameterField field, JToken value)
    {
        if (JToken.DeepEquals(field.Value, value)) return;
        field.Store(value);
        workspace.Dirty();
        foreach (var item in Fields) item.Refresh(item == field);
        Changed?.Invoke();
    }
}

public sealed class ParameterField(ParameterForm form, JToken definition, JObject values, ParameterField? parent) : ObservableObject
{
    bool? expanded;
    public JToken Definition { get; } = definition;
    public string Key => Definition["key"].Text();
    public string Label => Definition["label"].Text();
    public string Control => Definition["control"].Text();
    public string Step => parent?.Step ?? Definition["step"].Text();
    public JToken? Value => values[Key];
    public bool Visible => (parent?.Visible ?? true) && JsonData.Matches(Definition["visible_when"] as JObject, values);
    public bool Enabled => (parent?.Enabled ?? true) && JsonData.Matches(Definition["enabled_when"] as JObject, values);
    public bool Expanded
    {
        get => expanded ?? (Value is JArray { Count: > 0 });
        set { expanded = value; OnPropertyChanged(); form.NotifyViewChanged(); }
    }
    public int MatrixRows => Count(Definition["rows_key"].Text());
    public int MatrixColumns => Count(Definition["columns_key"].Text());
    int Count(string key) => form.Values[key]?.Type is JTokenType.Integer or JTokenType.Float &&
        double.IsFinite(form.Values[key]!.Number()) && form.Values[key]!.Number() is >= 0 and <= 1000
        ? (int)form.Values[key]!.Number() : 0;
    public bool BooleanValue { get => Value.Flag(); set => form.Set(this, new JValue(value)); }
    public JToken? ChoiceValue { get => Value; set { if (value != null) form.Set(this, value); } }
    public string TextValue
    {
        get => Value?.Type is null or JTokenType.Null ? "" : Value.ToString();
        set
        {
            if (string.IsNullOrWhiteSpace(value)) form.Set(this, JValue.CreateNull());
            else if (Control is "number" or "integer" or "integer_spinbox" && double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out double n) && double.IsFinite(n))
                form.Set(this, Control.StartsWith("integer") && n == Math.Truncate(n) && n >= long.MinValue && n < 9223372036854775808d ? new JValue((long)n) : new JValue(n));
            else form.Set(this, new JValue(value));
        }
    }
    public string DerivedValue
    {
        get
        {
            if (Control != "derived") return "";
            double n = ParameterRules.Derived(Definition["calculation"].Text(), form.Values);
            return double.IsFinite(n) ? n.ToString("G9", CultureInfo.InvariantCulture) : "";
        }
    }
    internal void Store(JToken value) => values[Key] = value.DeepClone();
    public void Set(JToken value) => form.Set(this, value);
    internal void Refresh(bool editing)
    {
        OnPropertyChanged(nameof(Visible));
        OnPropertyChanged(nameof(Enabled));
        OnPropertyChanged(nameof(DerivedValue));
        OnPropertyChanged(nameof(MatrixRows));
        OnPropertyChanged(nameof(MatrixColumns));
        if (editing) return;
        OnPropertyChanged(nameof(Value));
        OnPropertyChanged(nameof(TextValue));
        OnPropertyChanged(nameof(BooleanValue));
        OnPropertyChanged(nameof(ChoiceValue));
    }
}
