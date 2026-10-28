using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Microsoft.Win32;
using PackStudio.Core;

namespace PackStudio.Desktop;
public partial class MainWindow : Window
{
    readonly Workspace workspace = new();
    bool loading;
    string? projectPath;
    public MainWindow()
    {
        InitializeComponent();
        DataContext = workspace;
        workspace.DocumentChanged += RefreshDocument;
        workspace.ModelChanged += RefreshModel;
        FamilyBox.ItemsSource = PackageCatalog.Families;
        RefreshDocument();
        Loaded += async (_, _) => await workspace.GenerateAsync();
    }

    void RefreshDocument()
    {
        loading = true;
        FamilyBox.SelectedValue = workspace.Document.TemplateId;
        PresetBox.ItemsSource = workspace.Template.Presets;
        PresetBox.SelectedValue = workspace.Document.PresetId;
        PresetBox.IsEnabled = workspace.Template.Presets.Count > 0;
        NameBox.Text = workspace.Document.Name;
        var steps = workspace.Template.Fields.Select(f => f["step"]!.ToString()).Concat(workspace.Template.MaterialSelections.Select(s => s["step"]!.ToString())).Distinct().Select(key => new { Key = key, Label = StepLabel(key) }).ToList();
        StepBox.ItemsSource = steps;
        StepBox.SelectedIndex = 0;
        loading = false;
        RefreshFields();
    }

    void Family_Changed(object sender, SelectionChangedEventArgs e)
    {
        if (!loading && FamilyBox.SelectedValue is string id)
        {
            workspace.Select(id);
            projectPath = null;
        }
    }

    void Preset_Changed(object sender, SelectionChangedEventArgs e)
    {
        if (!loading && PresetBox.SelectedValue is string id)
            workspace.Select(workspace.Document.TemplateId, id);
    }

    void Step_Changed(object sender, SelectionChangedEventArgs e)
    {
        if (!loading)
            RefreshFields();
    }

    void Name_Changed(object sender, TextChangedEventArgs e)
    {
        if (!loading)
        {
            workspace.Document.Name = NameBox.Text;
            workspace.Dirty();
        }
    }

    void Previous_Click(object sender, RoutedEventArgs e)
    {
        if (StepBox.SelectedIndex > 0)
            StepBox.SelectedIndex--;
    }

    void Next_Click(object sender, RoutedEventArgs e)
    {
        if (StepBox.SelectedIndex < StepBox.Items.Count - 1)
            StepBox.SelectedIndex++;
    }

    async void New_Click(object sender, RoutedEventArgs e)
    {
        workspace.Select("bare_die", "");
        projectPath = null;
        await workspace.GenerateAsync();
    }

    async void Open_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog
        {
            Filter = "PackStudio 方案|*.packstudio.json|JSON|*.json"
        };
        if (dialog.ShowDialog(this) != true)
            return;
        try
        {
            var doc = ProjectDocument.Load(dialog.FileName);
            workspace.Load(doc);
            projectPath = dialog.FileName;
            await workspace.GenerateAsync();
        }
        catch (Exception ex)
        {
            Error(ex);
        }
    }

    void Save_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new SaveFileDialog
        {
            Filter = "PackStudio 方案|*.packstudio.json",
            FileName = projectPath ?? SafeName(workspace.Document.Name) + ".packstudio.json"
        };
        if (dialog.ShowDialog(this) != true)
            return;
        try
        {
            workspace.Document.Save(dialog.FileName);
            projectPath = dialog.FileName;
            workspace.Status = "方案已保存：" + dialog.FileName;
        }
        catch (Exception ex)
        {
            Error(ex);
        }
    }

    void Export_Click(object sender, RoutedEventArgs e)
    {
        if (!workspace.IsCurrent || workspace.Model == null)
            return;
        var dialog = new SaveFileDialog
        {
            Filter = "FloTHERM FloXML|*.floxml",
            FileName = SafeName(workspace.Document.Name) + ".floxml"
        };
        if (dialog.ShowDialog(this) != true)
            return;
        try
        {
            FloXml.Save(workspace.Model, dialog.FileName, System.IO.Path.Combine(AppContext.BaseDirectory, "schemas", "xmlSchema.xsd"));
            workspace.Status = "FloXML 已导出：" + dialog.FileName;
        }
        catch (Exception ex)
        {
            Error(ex);
        }
    }

    async void Materials_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new MaterialWindow(workspace)
        {
            Owner = this
        };
        if (dialog.ShowDialog() == true)
        {
            workspace.Dirty();
            await workspace.GenerateAsync();
        }
    }

    static string SafeName(string value) => string.Concat(value.Select(c => System.IO.Path.GetInvalidFileNameChars().Contains(c) ? '_' : c));
    void Error(Exception e)
    {
        workspace.Status = e.Message;
        MessageBox.Show(this, e.Message, "PackStudio", MessageBoxButton.OK, MessageBoxImage.Warning);
    }

    void Fit_Click(object sender, RoutedEventArgs e) => Viewport.ZoomExtents();
    void ShowAll_Click(object sender, RoutedEventArgs e) => workspace.ChangeVisibility(workspace.Model?.Blocks.Select(b => b.Id) ?? [], true);
    void HideAll_Click(object sender, RoutedEventArgs e) => workspace.ChangeVisibility(workspace.Model?.Blocks.Select(b => b.Id) ?? [], false);
    void Expand_Click(object sender, RoutedEventArgs e) => ExpandTree(true);
    void Collapse_Click(object sender, RoutedEventArgs e) => ExpandTree(false);
}
