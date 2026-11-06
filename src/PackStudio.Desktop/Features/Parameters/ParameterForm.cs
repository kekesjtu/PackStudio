using Newtonsoft.Json.Linq;
using PackStudio.Core;
using System.ComponentModel;
using System.Windows;

namespace PackStudio.Desktop;

public sealed class ParameterForm
{
    readonly Func<JObject> values;
    readonly Func<string, JToken, IReadOnlySet<string>> update;
    readonly bool forCreation;
    Func<IReadOnlyList<ValidationIssue>> issues = () => [];
    HashSet<string> previousIssuePaths = [];
    readonly Dictionary<string, HashSet<(ParameterField Field, string Property)>> dependencies = [];
    public IReadOnlyList<ParameterField> Fields { get; }
    public IReadOnlyList<ParameterField> Materials { get; }
    public PackageDefinition Template { get; }
    public JObject Values => values();
    public event Action? Changed;

    public ParameterForm(Workspace workspace) : this(workspace.Template, () => workspace.Document.Values, (path, value) =>
    {
        var keys = path.Split('/');
        var target = workspace.Document.Values;
        foreach (string key in keys[..^1])
        {
            if (target[key] is not JObject nested) target[key] = nested = new();
            target = nested;
        }
        if (JToken.DeepEquals(target[keys[^1]], value)) return new HashSet<string>();
        bool clearSlug = path == "cover.type" && target["cover.type"].Text() == "encapsulant" &&
            value.Text() != "encapsulant" && target["slug.enabled"].Flag();
        target[keys[^1]] = value.DeepClone();
        HashSet<string> changed = [path];
        if (clearSlug)
        {
            target["slug.enabled"] = false;
            changed.Add("slug.enabled");
        }
        workspace.Dirty();
        return changed;
    })
    {
        issues = () => workspace.Issues;
        previousIssuePaths = issues().SelectMany(i => i.ParameterPaths).ToHashSet();
        PropertyChangedEventManager.AddHandler(workspace, OnIssuesChanged, nameof(Workspace.Issues));
    }

    public ParameterForm(NewPackageViewModel draft) : this(draft.Template, () => draft.Values, draft.Set, forCreation: true) { }

    void RefreshIssues()
    {
        var current = issues().SelectMany(i => i.ParameterPaths).ToHashSet();
        var affected = previousIssuePaths.Union(current).ToList();
        previousIssuePaths = current;
        foreach (var field in Fields.Where(f => affected.Any(p => ParameterField.MatchesPath(f.Path, p))))
        {
            field.Notify(nameof(ParameterField.Error));
            field.Notify(nameof(ParameterField.HasError));
        }
    }
    void OnIssuesChanged(object? sender, PropertyChangedEventArgs e) => RefreshIssues();

    internal string? Error(string path) => issues().FirstOrDefault(i => i.Severity == IssueSeverity.Error && i.ParameterPaths.Any(p => ParameterField.MatchesPath(path, p)))?.Message;

    ParameterForm(PackageDefinition template, Func<JObject> values, Func<string, JToken, IReadOnlySet<string>> update, bool forCreation = false)
    {
        Template = template;
        this.forCreation = forCreation;
        this.values = values;
        this.update = update;
        Fields = Expand(forCreation ? new JArray(template.CreationFields) : template.DisplayFields, null).ToList();
        Materials = template.MaterialSelections.Select(s =>
        {
            var definition = (JObject)s.DeepClone();
            definition["key"] = "$material:" + s["key"].Text();
            definition["type"] = "combobox";
            return new ParameterField(this, definition, null);
        }).ToList();
        foreach (var field in Fields.Concat(Materials))
        {
            Watch(field, nameof(ParameterField.Value), [field.Path]);
            Watch(field, nameof(ParameterField.Visible), field.RuleDependencies("visible_when"));
            Watch(field, nameof(ParameterField.Enabled), field.RuleDependencies("enabled_when"));
            Watch(field, nameof(ParameterField.Symbol), TemplateSymbols.Dependencies(field.Definition));
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
            if (field.Type == "object")
                foreach (var child in Expand((JArray)definition["keys"]!, field)) yield return child;
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
        foreach (string key in path.Split('/')) token = token is JObject scope ? scope[key] : null;
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
