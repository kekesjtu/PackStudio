using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;
public partial class NewPackageWindow : Window
{
    readonly PackageCatalog catalog;
    Template template = null!;
    bool syncing;
    bool customizing;
    bool closed;
    string? preparedFamily;
    public ProjectDocument Draft { get; private set; } = new();
    public ProjectDocument? CreatedDocument { get; private set; }

    public NewPackageWindow(PackageCatalog catalog, string initialFamily = "bare_die")
    {
        this.catalog = catalog;
        InitializeComponent();
        Closed += (_, _) => closed = true;
        var choices = new ListCollectionView(PackagePresentation.Choices.ToList());
        choices.GroupDescriptions.Add(new PropertyGroupDescription(nameof(PackageChoice.Group)));
        TemplateList.ItemsSource = choices;
        TemplateList.SelectedValue = initialFamily;
    }

    async Task<bool> PrepareTemplateAsync()
    {
        if (TemplateList.SelectedValue is not string id)
            return false;
        if (preparedFamily == id) return true;
        NextButton.IsEnabled = TemplateList.IsEnabled = false;
        NextButton.Content = "正在加载…";
        TemplateError.Visibility = Visibility.Collapsed;
        try
        {
            var loaded = await Task.Run(() => catalog.Load(id));
            if (closed) return false;
            preparedFamily = null;
            InitializeTemplate(loaded);
            preparedFamily = id;
            return true;
        }
        catch (Exception ex)
        {
            if (!closed)
            {
                TemplateError.Text = "无法加载模板：" + ex.Message;
                TemplateError.Visibility = Visibility.Visible;
            }
            return false;
        }
        finally
        {
            if (!closed)
            {
                NextButton.IsEnabled = TemplateList.IsEnabled = true;
                NextButton.Content = "下一步 >";
            }
        }
    }

    void InitializeTemplate(Template loaded)
    {
        template = loaded;
        string id = template.Info.Id;
        syncing = true;
        DesignNameBox.Text = template.Info.Name;
        var variants = template.Presets.Select(p => p.Values["package.type"].Text()).Distinct().Where(v => v.Length > 0).ToList();
        VariantLabel.Visibility = VariantBox.Visibility = variants.Count > 0 ? Visibility.Visible : Visibility.Collapsed;
        VariantBox.ItemsSource = variants;
        var selected = template.Presets.FirstOrDefault(p => p.Id == template.DefaultPreset);
        VariantBox.SelectedItem = selected?.Values["package.type"].Text();
        FootprintBox.ItemsSource = PresetsForVariant();
        FootprintBox.SelectedValue = template.DefaultPreset;
        bool bare = id == "bare_die";
        FootprintLabel.Visibility = FootprintBox.Visibility = bare ? Visibility.Collapsed : Visibility.Visible;
        syncing = false;
        ApplyPreset();
    }

    List<Preset> PresetsForVariant() => template.Presets.Where(p => VariantBox.SelectedItem is not string variant || p.Values["package.type"].Text() == variant).ToList();
    void Variant_Changed(object sender, SelectionChangedEventArgs e)
    {
        if (syncing)
            return;
        syncing = true;
        var presets = PresetsForVariant();
        FootprintBox.ItemsSource = presets;
        FootprintBox.SelectedValue = presets.FirstOrDefault()?.Id;
        syncing = false;
        ApplyPreset();
    }

    void Footprint_Changed(object sender, SelectionChangedEventArgs e)
    {
        if (!syncing)
            ApplyPreset();
    }

    void ApplyPreset()
    {
        string id = FootprintBox.SelectedValue as string ?? "";
        if (template.Presets.Count > 0 && id.Length == 0)
            return;
        Draft = ProjectDocument.Create(template, id, DesignNameBox.Text);
        CreationError.Text = "";
        RefreshCreationOptions();
    }

    async void Next_Click(object sender, RoutedEventArgs e)
    {
        if (!customizing)
        {
            if (!await PrepareTemplateAsync()) return;
            customizing = true;
            TemplateList.Visibility = Visibility.Collapsed;
            CustomizePage.Visibility = Visibility.Visible;
            StageTitle.Text = "自定义模板";
            BackButton.IsEnabled = true;
            NextButton.Content = "完成";
            DesignNameBox.Focus();
            DesignNameBox.SelectAll();
        }
        else if (TryCreate())
            DialogResult = true;
    }

    void Back_Click(object sender, RoutedEventArgs e)
    {
        customizing = false;
        TemplateList.Visibility = Visibility.Visible;
        CustomizePage.Visibility = Visibility.Collapsed;
        StageTitle.Text = "选择起始模板";
        BackButton.IsEnabled = false;
        NextButton.Content = "下一步 >";
    }

    public bool TryCreate()
    {
        CreatedDocument = null;
        if (preparedFamily == null) return false;
        string name = DesignNameBox.Text.Trim();
        if (name.Length == 0 || name.Length > 160)
        {
            CreationError.Text = "请输入 1–160 个字符的设计名称。";
            DesignNameBox.Focus();
            return false;
        }

        try
        {
            var result = Draft.Clone();
            result.Name = name;
            result.Values = catalog.Initialize(template, result.Values, result.PresetId);
            template.Validate(result.Values);
            foreach (var field in CreationFields().Where(f => f["control"].Text()is "number" or "integer" or "integer_spinbox"))
                if (result.Values[field["key"].Text()]?.Type is null or JTokenType.Null)
                    throw new ArgumentException($"请填写{field["label"]}。");
            CreatedDocument = result;
            return true;
        }
        catch (ArgumentException ex)
        {
            CreationError.Text = ex.Message;
            return false;
        }
    }
}
