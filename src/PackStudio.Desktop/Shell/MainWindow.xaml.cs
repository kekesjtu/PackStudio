using System.Windows;
using System.Windows.Controls;
using Microsoft.Win32;
using PackStudio.Core;

namespace PackStudio.Desktop;
public partial class MainWindow : Window
{
    readonly Workspace workspace = new();
    readonly ParameterPanel parameters;
    readonly ModelPresenter models;
    bool loading;
    string? projectPath;
    MaterialWindow? materialWindow;
    public MainWindow()
    {
        InitializeComponent();
        models = new(workspace, ModelTree, Viewport, Inspector);
        parameters = new(workspace, FieldsPanel);
        _ = new IssuePresenter(workspace, IssuesList, WarningsText);
        workspace.ParameterRequested += path =>
        {
            if (path.StartsWith("CustomMaterials."))
            {
                Materials_Click(this, new RoutedEventArgs());
                materialWindow?.SelectMaterial(path["CustomMaterials.".Length..]);
                return;
            }
            if (parameters.StepFor(path) is not { } step) return;
            StepList.SelectedValue = step;
            parameters.Focus(path);
        };
        parameters.Changed += UpdateSchematic;
        workspace.PropertyChanged += (_, e) => { if (e.PropertyName == nameof(Workspace.DesignName)) Title = workspace.DesignName + " — PackStudio"; };
        InitializeViewportScale();
        DataContext = workspace;
        workspace.DocumentChanged += RefreshDocument;
        workspace.ModelChanged += models.RefreshModel;
        RefreshDocument();
        Loaded += async (_, _) => await workspace.GenerateAsync();
    }

    void RefreshDocument()
    {
        materialWindow?.Close();
        loading = true;
        parameters.Reset();
        var choice = workspace.Template.Info;
        PackageTitle.Text = choice.Name;
        PackageSubtitle.Text = choice.Description;
        PackagePreview.Content = new PackageIcon
        {
            Profile = choice.Icon
        };
        Title = workspace.Document.Name + " — PackStudio";
        StepList.ItemsSource = workspace.Template.Ui.Steps.Select(s => new WizardStep(s["key"].Text(), s["label"].Text())).ToList();
        StepList.SelectedIndex = 0;
        loading = false;
        RefreshFields();
    }

    void Step_Changed(object sender, SelectionChangedEventArgs e)
    {
        if (!loading)
            RefreshFields();
    }

    void RefreshFields()
    {
        if (StepList.SelectedValue is not string step) return;
        SectionTitle.Text = workspace.Template.Ui.Steps.Single(s => s["key"].Text() == step)["label"].Text();
        parameters.Show(step);
        UpdateSchematic();
    }

    void UpdateSchematic()
    {
        if (StepList.SelectedValue is string step)
            Schematic.Update(workspace.Template, workspace.Document, step, SectionTitle.Text);
    }

    void New_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new NewPackageWindow(workspace.Catalog, workspace.Document.TemplateId)
        {
            Owner = this
        };
        if (dialog.ShowDialog() != true || dialog.CreatedDocument == null)
            return;
        workspace.Load(dialog.CreatedDocument);
        projectPath = null;
    }

    void Open_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog
        {
            Filter = "PackStudio 方案|*.packstudio.json|JSON|*.json"
        };
        if (dialog.ShowDialog(this) != true)
            return;
        try
        {
            var doc = ProjectStore.Load(dialog.FileName, workspace.Catalog);
            workspace.Load(doc);
            projectPath = dialog.FileName;
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
            ProjectStore.Save(workspace.Document, dialog.FileName);
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
        if (!workspace.CanExport || workspace.Result == null)
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
            FloXmlExporter.Save(workspace.Result, dialog.FileName, System.IO.Path.Combine(AppContext.BaseDirectory, "schemas", "xmlSchema.xsd"));
            workspace.Status = "FloXML 已导出：" + dialog.FileName;
        }
        catch (Exception ex)
        {
            Error(ex);
        }
    }

    void Materials_Click(object sender, RoutedEventArgs e)
    {
        if (materialWindow != null)
        {
            materialWindow.Activate();
            return;
        }
        var dialog = new MaterialWindow(workspace)
        {
            Owner = this
        };
        materialWindow = dialog;
        dialog.Closed += (_, _) => materialWindow = null;
        dialog.MaterialApplied += () =>
        {
            workspace.Dirty();
            RefreshFields();
        };
        dialog.Show();
    }

    static string SafeName(string value) => string.Concat(value.Select(c => System.IO.Path.GetInvalidFileNameChars().Contains(c) ? '_' : c));
    void Error(Exception e)
    {
        workspace.Status = e.Message;
        MessageBox.Show(this, e.Message, "PackStudio", MessageBoxButton.OK, MessageBoxImage.Warning);
    }

    void Fit_Click(object sender, RoutedEventArgs e) => Viewport.ZoomExtents();
    void Expand_Click(object sender, RoutedEventArgs e) => models.ExpandTree(true);
    void Collapse_Click(object sender, RoutedEventArgs e) => models.ExpandTree(false);
}
