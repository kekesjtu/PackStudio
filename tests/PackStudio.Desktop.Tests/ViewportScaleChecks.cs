using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media.Media3D;
using System.Windows.Threading;
using HelixToolkit.Wpf;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;

static class ViewportScaleChecks
{
    static void Require(bool success, string message)
    {
        if (!success) throw new Exception(message);
    }

    public static async Task Run(MainWindow window)
    {
        var viewport = (HelixViewport3D)window.FindName("Viewport");
        var overlay = (Border)window.FindName("ViewportScaleOverlay");
        var line = (Canvas)window.FindName("ScaleBarLine");
        var label = (TextBlock)window.FindName("ScaleLabel");
        var grid = (Grid)window.FindName("WorkspaceGrid");
        await window.Dispatcher.InvokeAsync(() => { }, DispatcherPriority.ContextIdle);
        viewport.ZoomExtents(0);
        var savedCamera = viewport.Camera;
        var savedWidth = grid.ColumnDefinitions[0].Width;
        async Task Check(Func<double> expected)
        {
            await window.Dispatcher.InvokeAsync(() => { }, DispatcherPriority.ContextIdle);
            window.UpdateLayout();
            double worldLength = expected();
            Require(overlay.Visibility == Visibility.Visible && line.ActualWidth == 120 && !overlay.IsHitTestVisible,
                "fixed scale bar is missing, resized or intercepting input");
            double length = double.Parse(label.Text.Split(' ')[0], CultureInfo.CurrentCulture);
            Require(label.Text.EndsWith(" mm") && Math.Abs(length - worldLength) <= worldLength * 0.005,
                $"incorrect scale: {label.Text}, expected {worldLength:G6} mm; sameCamera={ReferenceEquals(viewport.Camera, viewport.Viewport.Camera)}, innerFov={(viewport.Viewport.Camera as PerspectiveCamera)?.FieldOfView}, innerDepth={(viewport.Viewport.Camera as ProjectionCamera)?.LookDirection.Length}");
        }
        try
        {
            var camera = new PerspectiveCamera(new(0, 0, 20), new(0, 0, -20), new(0, 1, 0), 60);
            viewport.Camera = camera;
            double Expected() => 2 * camera.LookDirection.Length * Math.Tan(camera.FieldOfView * Math.PI / 360) * 120 / viewport.Viewport.ActualWidth;
            await Check(Expected);
            camera.LookDirection = new(0, 0, -40);
            await Check(Expected);
            camera.FieldOfView = 30;
            await Check(Expected);
            camera.Position += new Vector3D(5, 2, 1);
            await Check(Expected);
            camera.LookDirection = new(24, 0, -32);
            await Check(Expected);
            grid.ColumnDefinitions[0].Width = new GridLength(savedWidth.Value + 40);
            window.UpdateLayout();
            await Check(Expected);
            var orthographic = new OrthographicCamera(new(0, 0, 20), new(0, 0, -20), new(0, 1, 0), 20);
            viewport.Camera = orthographic;
            await Check(() => orthographic.Width * 120 / viewport.Viewport.ActualWidth);
            orthographic.Width = 10;
            await Check(() => orthographic.Width * 120 / viewport.Viewport.ActualWidth);
        }
        finally
        {
            grid.ColumnDefinitions[0].Width = savedWidth;
            viewport.Camera = savedCamera;
            window.UpdateLayout();
            await window.Dispatcher.InvokeAsync(() => { }, DispatcherPriority.ContextIdle);
        }
        Require(overlay.VerticalAlignment == VerticalAlignment.Bottom, "scale is not at bottom of viewport");
        NewPackageChecks.Capture(window, "viewport-fixed-scale.png");
        Console.WriteLine("PASS fixed scale updates with zoom, FOV, pan, rotation, viewport width and orthographic camera");
    }
}
