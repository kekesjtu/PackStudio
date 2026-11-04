using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;

public sealed class ParameterForm
{
    readonly Func<JObject> values;
    readonly Func<string, JToken, IReadOnlySet<string>> update;
    readonly bool forCreation;
    readonly Dictionary<string, HashSet<(ParameterField Field, string Property)>> dependencies = [];
    public IReadOnlyList<ParameterField> Fields { get; }
    public IReadOnlyList<ParameterField> Materials { get; }
    public Template Template { get; }
    public JObject Values => values();
    public event Action? Changed;

    public ParameterForm(Workspace workspace) : this(workspace.Template, () => workspace.Document.Values, (path, value) =>
    {
        var keys = path.Split('/');
        var target = workspace.Document.Values;
        foreach (string key in keys[..^1]) target = (JObject)target[key]!;
        if (JToken.DeepEquals(target[keys[^1]], value)) return new HashSet<string>();
        target[keys[^1]] = value.DeepClone();
        workspace.Dirty();
        return new HashSet<string> { path };
    }) { }

    public ParameterForm(CreationDraft draft) : this(draft.Template, () => draft.Values, draft.Set, forCreation: true) { }

    ParameterForm(Template template, Func<JObject> values, Func<string, JToken, IReadOnlySet<string>> update, bool forCreation = false)
    {
        Template = template;
        this.forCreation = forCreation;
        this.values = values;
        this.update = update;
        Fields = Expand(template.Fields, null).ToList();
        Materials = template.MaterialSelections.Select(s =>
        {
            var definition = (JObject)s.DeepClone();
            definition["key"] = "$material:" + s["group_id"].Text();
            definition["control"] = "material";
            return new ParameterField(this, definition, null);
        }).ToList();
        foreach (var field in Fields.Concat(Materials))
        {
            Watch(field, nameof(ParameterField.Value), [field.Path]);
            Watch(field, nameof(ParameterField.Visible), field.RuleDependencies("visible_when"));
            Watch(field, nameof(ParameterField.Enabled), field.RuleDependencies("enabled_when"));
            Watch(field, nameof(ParameterField.Symbol), TemplateSymbols.Dependencies(field.Definition));
            Watch(field, nameof(ParameterField.DerivedValue), (field.Definition["depends_on"] as JArray ?? []).Select(k => k.Text()));
            Watch(field, nameof(ParameterField.MatrixRows), [field.Definition["rows_key"].Text()]);
            Watch(field, nameof(ParameterField.MatrixColumns), [field.Definition["columns_key"].Text()]);
        }
    }

    IEnumerable<ParameterField> Expand(JArray definitions, ParameterField? parent)
    {
        foreach (var definition in definitions)
        {
            if (!forCreation && definition["creation_only"].Flag()) continue;
            var field = new ParameterField(this, definition, parent);
            if (field.Control == "object")
                foreach (var child in Expand((JArray)definition["fields"]!, field)) yield return child;
            else yield return field;
        }
    }

    void Watch(ParameterField field, string property, IEnumerable<string> keys)
    {
        foreach (string key in keys.Where(k => k.Length > 0).Distinct())
        {
            if (!dependencies.TryGetValue(key, out var targets)) dependencies[key] = targets = [];
            targets.Add((field, property));
        }
    }

    internal JToken? Get(string path)
    {
        JToken? token = Values;
        foreach (string key in path.Split('/')) token = token?[key];
        return token;
    }

    public void Set(ParameterField field, JToken value)
    {
        var changed = update(field.Path, value);
        if (changed.Count == 0) return;
        var affected = changed.Where(dependencies.ContainsKey).SelectMany(key => dependencies[key]).Distinct().ToList();
        foreach (var (target, property) in affected) target.Notify(property);
        Changed?.Invoke();
    }
}
