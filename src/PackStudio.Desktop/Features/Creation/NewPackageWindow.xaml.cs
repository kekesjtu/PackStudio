using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;
public partial class NewPackageWindow : Window
{
    readonly RuntimeDataCatalog catalog;
    PackageDefinition template = null!;
    bool syncing;
    bool customizing;
    bool closed;
    string? preparedFamily;
    public NewPackageViewModel? Draft { get; private set; }
    ParameterForm creationForm = null!;
    public ProjectDocument? CreatedDocument { get; private set; }

    public NewPackageWindow(RuntimeDataCatalog catalog, string? initialFamily = null)
    {
        this.catalog = catalog;
        InitializeComponent();
        DesignNameBox.TextChanged += (_, _) => { if (Draft != null) Draft.Name = DesignNameBox.Text; };
        Closed += (_, _) => closed = true;
        var choices = new ListCollectionView(catalog.Families.ToList());
        choices.GroupDescriptions.Add(new PropertyGroupDescription(nameof(TemplateInfo.Group)));
        TemplateList.ItemsSource = choices;
        TemplateList.SelectedValue = initialFamily ?? catalog.DefaultFamily.Id;
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

    void InitializeTemplate(PackageDefinition loaded)
    {
        template = loaded;
        syncing = true;
        DesignNameBox.Text = template.Info.Name;
        var variants = template.Presets.Select(p => p.Values["package.type"].Text()).Distinct().Where(v => v.Length > 0).ToList();
        VariantLabel.Visibility = VariantBox.Visibility = variants.Count > 0 ? Visibility.Visible : Visibility.Collapsed;
        VariantBox.ItemsSource = variants;
        var selected = template.Presets.FirstOrDefault(p => p.Name == template.DefaultPreset);
        VariantBox.SelectedItem = selected?.Values["package.type"].Text();
        FootprintBox.ItemsSource = PresetsForVariant();
        FootprintBox.SelectedValue = template.DefaultPreset;
        FootprintLabel.Visibility = FootprintBox.Visibility = template.HasFootprint ? Visibility.Visible : Visibility.Collapsed;
        syncing = false;
        ApplyPreset();
    }

    List<ProjectDocument> PresetsForVariant() => template.Presets.Where(p => VariantBox.SelectedItem is not string variant || p.Values["package.type"].Text() == variant).ToList();
    void Variant_Changed(object sender, SelectionChangedEventArgs e)
    {
        if (syncing)
            return;
        syncing = true;
        var presets = PresetsForVariant();
        FootprintBox.ItemsSource = presets;
        FootprintBox.SelectedValue = presets.FirstOrDefault()?.Name;
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
        var draft = new NewPackageViewModel(template, id) { Name = DesignNameBox.Text };
        Draft = draft;
        creationForm = new(draft);
        CreationError.Text = "";
        CreationOptions.Children.Clear();
        Grid.SetIsSharedSizeScope(CreationOptions, true);
        foreach (var field in creationForm.Fields.Where(f => f.Definition["creation_option"].Flag()))
            CreationOptions.Children.Add(FieldView.Create(field));
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
        if (preparedFamily == null || Draft == null) return false;
        try
        {
            var fourLayer = template.Info.Id is "chip_array" or "pbga_wb" && Draft.Values["substrate.layers"] is { Type: JTokenType.String } layers && layers.Value<string>() == "4-Layer"
                ? catalog.LoadFourLayer(template.Info.Id) : null;
            CreatedDocument = PackageInitializer.Create(template, Draft.PresetId, Draft.Name, Draft.Overrides, fourLayer);
            return true;
        }
        catch (Exception ex)
        {
            NLog.LogManager.GetCurrentClassLogger().Warn(ex, "创建方案失败");
            CreationError.Text = ex.Message;
            return false;
        }
    }
}
