using Newtonsoft.Json.Linq;
using PackStudio.Core;
using System.ComponentModel;
using System.Windows;

namespace PackStudio.Desktop;

public sealed class ParameterForm
{
    const string DiscreteNotice = "显式去球或焊球坐标表需要离散建模，BGA 焊球建模方式已自动切换为 Discrete Cuboids（discrete）。";
    readonly Func<JObject> values;
    readonly Func<string, JToken, IReadOnlySet<string>> update;
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
        var target = workspace.Document.Values;
        if (path == "bga.representation" && value.Text() != "discrete" && SolderBalls.RequiresDiscrete(target))
        {
            workspace.Status = "请先关闭显式去球和焊球坐标表，再选择其他 BGA 焊球建模方式。";
            return new HashSet<string>();
        }
        if (JToken.DeepEquals(target[path], value)) return new HashSet<string>();
        bool clearSlug = path == "cover.type" && target["cover.type"].Text() == "encapsulant" &&
            value.Text() != "encapsulant" && target["slug.enabled"].Flag();
        target[path] = value.DeepClone();
        HashSet<string> changed = [path];
        if (clearSlug)
        {
            target["slug.enabled"] = false;
            changed.Add("slug.enabled");
        }
        bool forceDiscrete = SolderBalls.RequiresDiscrete(target) && target["bga.representation"].Text() != "discrete";
        if (forceDiscrete)
        {
            target["bga.representation"] = "discrete";
            changed.Add("bga.representation");
        }
        workspace.Dirty();
        if (forceDiscrete) workspace.Status = DiscreteNotice;
        return changed;
    })
    {
        issues = () => workspace.Issues;
        previousIssuePaths = issues().SelectMany(i => i.ParameterPaths).ToHashSet();
        PropertyChangedEventManager.AddHandler(workspace, OnIssuesChanged, nameof(Workspace.Issues));
        if (SolderBalls.RequiresDiscrete(Values) && Values["bga.representation"].Text() != "discrete")
        {
            Set("bga.representation", new JValue("discrete"));
            workspace.Status = DiscreteNotice;
        }
    }

    public ParameterForm(NewPackageViewModel draft) : this(draft.Template, () => draft.Values, draft.Set, forCreation: true) { }

    void RefreshIssues()
    {
        var current = issues().SelectMany(i => i.ParameterPaths).ToHashSet();
        var affected = previousIssuePaths.Union(current).ToList();
        previousIssuePaths = current;
        foreach (var field in Fields.Where(f => affected.Any(fieldPath => f.ContainsPath(fieldPath))))
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
        this.values = values;
        this.update = update;
        var definitions = forCreation ? template.CreationFields : template.DisplayFields.Where(f => !f["creation_only"].Flag());
        Fields = definitions.Select(f => new ParameterField(this, f)).ToList();
        Materials = template.MaterialSelections.Select(s =>
        {
            var definition = (JObject)s.DeepClone();
            definition["key"] = "$material:" + s["key"].Text();
            definition["type"] = "combobox";
            return new ParameterField(this, definition);
        }).ToList();
        foreach (var field in Fields.Concat(Materials))
        {
            Watch(field, nameof(ParameterField.Value), [field.Key]);
            Watch(field, nameof(ParameterField.Visible), field.RuleDependencies("visible_when"));
            Watch(field, nameof(ParameterField.Enabled), field.RuleDependencies("enabled_when"));
            Watch(field, nameof(ParameterField.Symbol), TemplateSymbols.Dependencies(field.Definition));
            Watch(field, nameof(ParameterField.MatrixRows), [field.Definition["rows_key"].Text()]);
            Watch(field, nameof(ParameterField.MatrixColumns), [field.Definition["columns_key"].Text()]);
            Watch(field, nameof(ParameterField.MatrixEnabled), [field.Definition["enabled_key"].Text()]);
            if (field.Key is "bga.omitted_cells" or "bga.ball_map_enabled" or "bga.representation")
                Watch(field, nameof(ParameterField.Notice), ["bga.explicit_removal_enabled", "bga.ball_map_enabled"]);
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

    public void Set(string key, JToken value)
    {
        var changed = update(key, value);
        if (changed.Count == 0)
        {
            Fields.FirstOrDefault(field => field.Key == key)?.Notify(nameof(ParameterField.Value));
            return;
        }
        var affected = changed.Where(dependencies.ContainsKey).SelectMany(key => dependencies[key]).Distinct().ToList();
        foreach (var (target, property) in affected) target.Notify(property);
        Changed?.Invoke();
    }
}
