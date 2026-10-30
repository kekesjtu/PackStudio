using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Newtonsoft.Json.Linq;
using PackStudio.Core;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;
static class NewPackageChecks
{
    static readonly string PreviewDirectory = Path.GetFullPath("tmp/2026-10-29-new-package");
    static T Control<T>(FrameworkElement window, string name)
        where T : FrameworkElement => (T)window.FindName(name);
    static void Click(Button button) => button.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
    internal static async Task OpenCustomize(NewPackageWindow dialog)
    {
        Click(Control<Button>(dialog, "NextButton"));
        long deadline = Environment.TickCount64 + 15000;
        while (Control<FrameworkElement>(dialog, "CustomizePage").Visibility != Visibility.Visible)
        {
            if (Control<FrameworkElement>(dialog, "TemplateError").Visibility == Visibility.Visible)
                throw new Exception(Control<TextBlock>(dialog, "TemplateError").Text);
            if (Environment.TickCount64 > deadline) throw new TimeoutException("template initialization timed out");
            await Task.Delay(10);
        }
    }

    public static async Task<ProjectDocument> CreateDraft(PackageCatalog catalog, string family)
    {
        var dialog = new NewPackageWindow(catalog, family)
        {
            ShowInTaskbar = false,
            ShowActivated = false,
            Opacity = 0
        };
        dialog.Show();
        try
        {
            if (family == "qfn")
                Capture(dialog, "new-package-templates.png");
            await OpenCustomize(dialog);
            if (Control<FrameworkElement>(dialog, "CustomizePage").Visibility != Visibility.Visible)
                throw new Exception("customization page did not open");
            var name = Control<TextBox>(dialog, "DesignNameBox");
            name.Text = " ";
            if (dialog.TryCreate() || dialog.CreatedDocument != null)
                throw new Exception("blank design name accepted");
            name.Text = "测试方案 " + family;
            var variants = Control<ComboBox>(dialog, "VariantBox");
            if (variants.Items.Count > 1)
                variants.SelectedIndex = variants.Items.Count - 1;
            var presets = Control<ComboBox>(dialog, "FootprintBox");
            if (presets.Items.Count > 1)
                presets.SelectedIndex = presets.Items.Count - 1;
            string expectedPreset = presets.SelectedValue as string ?? "";
            if (family == "chip_array")
            {
                var options = Control<StackPanel>(dialog, "CreationOptions");
                var layerChoice = options.Children.OfType<Grid>().SelectMany(g => g.Children.OfType<ComboBox>()).Single(c => c.Tag?.ToString() == "substrate.layers");
                layerChoice.SelectedValue = new JValue("4-Layer");
            }

            var values = dialog.Draft.Values.DeepClone();
            Click(Control<Button>(dialog, "BackButton"));
            await OpenCustomize(dialog);
            if (!JToken.DeepEquals(values, dialog.Draft.Values) || name.Text != "测试方案 " + family)
                throw new Exception("back/next discarded draft inputs");
            if (!dialog.TryCreate() || dialog.CreatedDocument is not ProjectDocument result)
                throw new Exception(family + " could not finish: " + Control<TextBlock>(dialog, "CreationError").Text);
            if (result.TemplateId != family || result.PresetId != expectedPreset || result.Name != name.Text)
                throw new Exception("created project differs from selection");
            if (expectedPreset.Length > 0 && result.Values["footprint.size"].Text() != expectedPreset)
                throw new Exception("preset values were not applied");
            if (family == "chip_array" && result.Values["substrate.layers"].Text() != "4-Layer")
                throw new Exception("substrate initialization was discarded");
            if (family == "qfn")
                Capture(dialog, "new-package-customize.png");
            return result;
        }
        finally
        {
            dialog.Close();
        }
    }

    public static void CancelPreservesProject(MainWindow window, Workspace workspace)
    {
        var document = workspace.Document;
        var model = workspace.Model;
        _ = window.Dispatcher.BeginInvoke(async () =>
        {
            var dialog = window.OwnedWindows.OfType<NewPackageWindow>().Single();
            dialog.Opacity = 0;
            Control<ListBox>(dialog, "TemplateList").SelectedValue = "pqfp";
            await OpenCustomize(dialog);
            Control<TextBox>(dialog, "DesignNameBox").Text = "不应覆盖当前方案";
            dialog.Close();
        });
        Control<Fluent.Button>(window, "NewPackageButton").RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
        if (!ReferenceEquals(document, workspace.Document) || !ReferenceEquals(model, workspace.Model))
            throw new Exception("canceling New Package modified current project");
        Console.WriteLine("PASS cancel New Package preserves current project");
    }

    public static async Task FinishCreatesProject(MainWindow window, Workspace workspace)
    {
        _ = window.Dispatcher.BeginInvoke(async () =>
        {
            var dialog = window.OwnedWindows.OfType<NewPackageWindow>().Single();
            dialog.Opacity = 0;
            Control<ListBox>(dialog, "TemplateList").SelectedValue = "qfn";
            await OpenCustomize(dialog);
            Control<TextBox>(dialog, "DesignNameBox").Text = "QFN — 布局验证";
            Click(Control<Button>(dialog, "NextButton"));
        });
        Control<Fluent.Button>(window, "NewPackageButton").RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
        while (workspace.IsBusy)
            await Task.Delay(20);
        if (workspace.Document.TemplateId != "qfn" || workspace.Document.Name != "QFN — 布局验证" || !workspace.IsCurrent)
            throw new Exception("finishing New Package did not generate the chosen project");
        var steps = Control<ListBox>(window, "StepList");
        Control<HelixToolkit.Wpf.HelixViewport3D>(window, "Viewport").ZoomExtents(0);
        steps.SelectedValue = "overall_package";
        Capture(window, "sidebar-overall-package.png");
        steps.SelectedValue = "summary";
        Capture(window, "sidebar-summary.png");
        Console.WriteLine("PASS finish New Package and visible sidebar navigation");
    }

    internal static void Capture(Window window, string name)
    {
        window.UpdateLayout();
        var content = (FrameworkElement)window.Content;
        var margin = content.Margin;
        double width = content.ActualWidth + margin.Left + margin.Right;
        double height = content.ActualHeight + margin.Top + margin.Bottom;
        var bitmap = new RenderTargetBitmap((int)Math.Ceiling(width), (int)Math.Ceiling(height), 96, 96, PixelFormats.Pbgra32);
        var background = new DrawingVisual();
        using (var dc = background.RenderOpen())
        {
            dc.DrawRectangle(window.Background, null, new Rect(0, 0, width, height));
            dc.DrawRectangle(new VisualBrush(content), null, new Rect(margin.Left, margin.Top, content.ActualWidth, content.ActualHeight));
        }
        bitmap.Render(background);
        var encoder = new PngBitmapEncoder();
        encoder.Frames.Add(BitmapFrame.Create(bitmap));
        Directory.CreateDirectory(PreviewDirectory);
        using var output = File.Create(Path.Combine(PreviewDirectory, name));
        encoder.Save(output);
    }
}
