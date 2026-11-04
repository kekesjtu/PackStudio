using System.Windows;
using System.Windows.Input;

namespace PackStudio.Desktop;

public sealed partial class ModelPresenter
{
    Point? pointerOrigin;
    bool pointerDragged;

    void Viewport_PointerDown(object sender, MouseButtonEventArgs e)
    {
        pointerOrigin = e.GetPosition(Viewport.Viewport);
        pointerDragged = false;
    }

    void Viewport_PointerMove(object sender, MouseEventArgs e)
    {
        if (pointerOrigin is not Point origin || e.LeftButton != MouseButtonState.Pressed) return;
        var delta = e.GetPosition(Viewport.Viewport) - origin;
        pointerDragged |= Math.Abs(delta.X) >= SystemParameters.MinimumHorizontalDragDistance ||
            Math.Abs(delta.Y) >= SystemParameters.MinimumVerticalDragDistance;
    }

    void Viewport_PointerUp(object sender, MouseButtonEventArgs e)
    {
        if (pointerOrigin is not Point origin) return;
        var point = e.GetPosition(Viewport.Viewport);
        var delta = point - origin;
        bool clicked = !pointerDragged && Math.Abs(delta.X) < SystemParameters.MinimumHorizontalDragDistance &&
            Math.Abs(delta.Y) < SystemParameters.MinimumVerticalDragDistance;
        pointerOrigin = null;
        if (clicked) SelectViewportBlock(point);
    }
}
