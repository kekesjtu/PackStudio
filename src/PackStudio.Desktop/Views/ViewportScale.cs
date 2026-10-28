using System.ComponentModel;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media.Media3D;
using System.Windows.Threading;
using HelixToolkit.Wpf;

namespace PackStudio.Desktop;

public partial class MainWindow
{
    DispatcherOperation? scaleUpdate;
    ProjectionCamera? scaleCamera;

    void InitializeViewportScale()
    {
        var cameraProperty = DependencyPropertyDescriptor.FromProperty(Viewport3D.CameraProperty, typeof(Viewport3D));
        cameraProperty.AddValueChanged(Viewport.Viewport, ScaleCameraReplaced);
        ScaleCameraReplaced(Viewport, EventArgs.Empty);
        Closed += (_, _) =>
        {
            cameraProperty.RemoveValueChanged(Viewport.Viewport, ScaleCameraReplaced);
            if (scaleCamera != null) scaleCamera.Changed -= UpdateViewportScale;
            scaleUpdate?.Abort();
        };
    }

    void ScaleCameraReplaced(object? sender, EventArgs e)
    {
        if (scaleCamera != null) scaleCamera.Changed -= UpdateViewportScale;
        scaleCamera = Viewport.Viewport.Camera as ProjectionCamera;
        if (scaleCamera != null) scaleCamera.Changed += UpdateViewportScale;
        UpdateViewportScale(sender, e);
    }

    void UpdateViewportScale(object? sender, EventArgs e)
    {
        if (scaleUpdate != null) return;
        // Read projection data after WPF has applied camera bindings and layout.
        scaleUpdate = Dispatcher.InvokeAsync(() =>
        {
            scaleUpdate = null;
            RefreshViewportScale();
        }, DispatcherPriority.Render);
    }

    void RefreshViewportScale()
    {
        if (ViewportScaleOverlay == null || Viewport?.Viewport == null) return;
        var view = Viewport.Viewport;
        if (view.Camera is not ProjectionCamera camera || view.ActualWidth <= 0 || view.ActualHeight <= 0 ||
            camera.LookDirection.LengthSquared <= 0)
        {
            ViewportScaleOverlay.Visibility = Visibility.Collapsed;
            return;
        }

        // The reference plane passes through the camera target and is parallel to the screen.
        var target = camera.Position + camera.LookDirection;
        var start = view.UnProject(new Point(0, 0), target, camera.LookDirection);
        var end = view.UnProject(new Point(ScaleBarLine.Width, 0), target, camera.LookDirection);
        double length = start is Point3D a && end is Point3D b ? (b - a).Length : double.NaN;
        bool valid = double.IsFinite(length) && length > 0;
        ViewportScaleOverlay.Visibility = valid ? Visibility.Visible : Visibility.Collapsed;
        if (valid) ScaleLabel.Text = $"{length:G3} mm";
    }
}
